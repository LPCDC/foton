"""Fóton — servidor do piloto (pipeline real + persistência + contas).

Fluxo: ingest -> watermark(marca do fotógrafo) -> detecção+embedding (ArcFace) ->
match -> feed do convidado. Dados em SQLite (store.py), não mais em memória.

Segurança (ADR-0005): a selfie do convidado NUNCA é armazenada — vira embedding e os
bytes são descartados. Logs sem PII (só id de rastreio, contagem, latência).
"""
import io, os, time, uuid, logging
import cv2, numpy as np, qrcode
from PIL import Image, ImageDraw, ImageFont, ImageOps
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Header
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Render free = CPU compartilhada: limita threads. O modelo carrega no startup (nao no request).
os.environ.setdefault("OMP_NUM_THREADS", "2")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "2")
from insightface.app import FaceAnalysis
import store

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(os.path.dirname(HERE))
THRESH = 0.25           # ArcFace/buffalo_s — validado (iguais ~0.61, diferentes ~0.01)
LONG_EDGE = 2048
JPEG_Q = 82

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("foton")

_fa = None
def _face():
    global _fa
    if _fa is None:
        _fa = FaceAnalysis(name="buffalo_s", root=HERE, allowed_modules=["detection", "recognition"],
                           providers=["CPUExecutionProvider"])
        # det_size=640: rosto de 90px so e detectado a 640 (a 320 = 0/6).
        _fa.prepare(ctx_id=-1, det_size=(640, 640))
    return _fa

def _font(sz):
    for p in (r"C:\Windows\Fonts\arialbd.ttf", r"C:\Windows\Fonts\arial.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        try: return ImageFont.truetype(p, sz)
        except Exception: pass
    return ImageFont.load_default()

def process_image(raw: bytes, marca: str = "FÓTON"):
    t0 = time.perf_counter()
    # exif_transpose: celular/camera gravam a rotacao no EXIF. Sem isso a foto sai deitada.
    img = ImageOps.exif_transpose(Image.open(io.BytesIO(raw))).convert("RGB")
    w, h = img.size
    s = LONG_EDGE / max(w, h)
    if s < 1:
        img = img.resize((round(w * s), round(h * s)), Image.LANCZOS)
    fw, fh = img.size
    d = ImageDraw.Draw(img, "RGBA")
    font = _font(max(18, fw // 28))
    txt = (marca or "FÓTON").strip()[:40]
    bb = d.textbbox((0, 0), txt, font=font); tw, th = bb[2] - bb[0], bb[3] - bb[1]
    m = int(fw * 0.02); x, y = fw - tw - m, fh - th - m * 2
    d.text((x + 2, y + 2), txt, font=font, fill=(0, 0, 0, 120))
    d.text((x, y), txt, font=font, fill=(255, 255, 255, 190))
    out = io.BytesIO(); img.save(out, "JPEG", quality=JPEG_Q, optimize=True, progressive=True)
    return out.getvalue(), (fw, fh), (time.perf_counter() - t0) * 1000

def detect_embed(raw: bytes):
    arr = np.frombuffer(raw, np.uint8)
    bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if bgr is None:
        return []
    return [f.normed_embedding.astype(np.float32) for f in _face().get(bgr)]

def _emb(b):  # bytes -> vetor
    return np.frombuffer(b, np.float32)

def _ev(code, create=False):
    e = store.evento(code)
    if e is None:
        if not create:
            raise HTTPException(404, "evento nao encontrado")
        store.cria_evento(code, dono=None, nome="Evento", auto=1)
        log.info('{"stage":"event","code":"%s","status":"auto-created"}' % code)
        e = store.evento(code)
    return e

def _dono(token):
    """Identifica a fotógrafa pelo token de sessão (header Authorization: Bearer ...)."""
    if not token: return None
    t = token.replace("Bearer ", "").strip()
    return store.por_token(t)

app = FastAPI(title="Fóton", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.on_event("startup")
def _startup():
    store.conn()
    try: _face(); log.info('{"stage":"warm","status":"ready"}')
    except Exception as e: log.info('{"stage":"warm","status":"fail","err":"%s"}' % str(e)[:140])

@app.get("/health")
def health():
    return {"ok": True, "engine": "InsightFace buffalo_s (SCRFD+ArcFace) CPU", "db": "sqlite"}

# ============================ CONTAS ============================
@app.post("/signup")
def signup(email: str = Form(...), senha: str = Form(...), nome: str = Form(""), marca: str = Form("")):
    if len(senha) < 6: raise HTTPException(400, "senha muito curta (mínimo 6)")
    if not store.cria_conta(email, senha, nome, marca):
        raise HTTPException(409, "já existe uma conta com esse e-mail")
    c = store.autentica(email, senha)
    return {"token": store.novo_token(c["email"]), "nome": c["nome"], "marca": c["marca"],
            "credits": c["credits"], "credits_total": c["credits_total"], "email": c["email"]}

@app.post("/login")
def login(email: str = Form(...), senha: str = Form(...)):
    c = store.autentica(email, senha)
    if not c: raise HTTPException(401, "e-mail ou senha incorretos")
    return {"token": store.novo_token(c["email"]), "nome": c["nome"], "marca": c["marca"],
            "credits": c["credits"], "credits_total": c["credits_total"], "email": c["email"]}

@app.get("/me")
def me(authorization: str = Header(None)):
    c = _dono(authorization)
    if not c: raise HTTPException(401, "sessão expirada")
    evs = store.eventos_de(c["email"])
    return {"nome": c["nome"], "marca": c["marca"], "email": c["email"],
            "credits": c["credits"], "credits_total": c["credits_total"],
            "total_fotos": sum(e["fotos"] for e in evs),
            "total_convidados": sum(e["convidados"] for e in evs)}

# ============================ EVENTOS ============================
@app.post("/event")
def create_event(code: str = Form(...), brand: str = Form("FÓTON"),
                 name: str = Form(""), date: str = Form(""), authorization: str = Header(None)):
    c = _dono(authorization)
    store.cria_evento(code, dono=(c["email"] if c else None), nome=(name or "Evento"),
                      data=date, marca=brand, auto=0)
    if c: store.gasta_credito(c["email"])
    log.info('{"stage":"event","code":"%s","status":"created"}' % code)
    return {"event": code, "brand": (brand or "FÓTON")}

@app.get("/events")
def events(authorization: str = Header(None)):
    c = _dono(authorization)
    if not c: return {"events": []}          # sem login, nenhum evento (nao vaza de outros)
    return {"events": [{"code": e["code"], "name": e["nome"], "date": e["data"], "brand": e["marca"],
                        "photos": e["fotos"], "guests": e["convidados"], "status": e["status"]}
                       for e in store.eventos_de(c["email"])]}

@app.post("/event/delete")
def event_delete(code: str = Form(...)):
    existed = store.evento(code) is not None
    store.apaga_evento(code)
    log.info('{"stage":"event","code":"%s","status":"deleted"}' % code)
    return {"ok": True, "deleted": existed}

@app.post("/event/close")
def event_close(code: str = Form(...)):
    store.encerra_evento(code)
    return {"ok": True}

@app.get("/stats")
def stats(event: str):
    _ev(event, create=True)
    return {"event": event, "photos": len(store.fotos_de(event)), "guests": store.conta_convidados(event)}

@app.get("/photos")
def photos(event: str):
    _ev(event, create=True)
    return {"event": event, "photos": [{"id": p["id"], "n_faces": p["n_faces"]} for p in store.fotos_de(event)]}

# ============================ PIPELINE ============================
@app.post("/ingest")
async def ingest(event: str = Form(...), file: UploadFile = File(...)):
    e = _ev(event, create=True)
    raw = await file.read()
    pid = uuid.uuid4().hex[:12]
    t0 = time.time()
    treated, dims, pms = process_image(raw, e.get("marca") or "FÓTON")
    faces = detect_embed(treated)
    store.salva_foto(pid, event, treated, faces)
    matched = []
    for gid, gemb in store.convidados_de(event):
        g = _emb(gemb)
        if any(float(g @ f) >= THRESH for f in faces):
            store.salva_match(gid, pid); matched.append(gid)
    lat = int((time.time() - t0) * 1000)
    log.info('{"stage":"ingest","photo_id":"%s","n_faces":%d,"proc_ms":%.0f,"latency_ms":%d,"status":"ok"}'
             % (pid, len(faces), pms, lat))
    return {"photo_id": pid, "n_faces": len(faces), "dims": dims,
            "processing_ms": round(pms, 1), "latency_ms": lat, "matched_guests": matched}

@app.post("/selfie")
async def selfie(event: str = Form(...), consent: bool = Form(...), file: UploadFile = File(...),
                 nome: str = Form(""), contato: str = Form("")):
    _ev(event, create=True)
    if not consent:
        raise HTTPException(400, "consentimento obrigatorio (LGPD, ADR-0005)")
    raw = await file.read()                 # bytes da selfie: usados e descartados
    faces = detect_embed(raw)
    if not faces:
        raise HTTPException(422, "nenhum rosto detectado na selfie")
    emb = faces[0]
    gid = uuid.uuid4().hex[:12]
    store.salva_convidado(gid, event, emb)
    matched = []
    for pid, femb in store.rostos_de(event):
        if float(emb @ _emb(femb)) >= THRESH:
            store.salva_match(gid, pid)
            if pid not in matched: matched.append(pid)
    if (nome or "").strip() or (contato or "").strip():
        store.salva_contato(event, gid, (nome or "").strip(), (contato or "").strip())
    log.info('{"stage":"selfie","guest_id":"%s","matches":%d,"status":"ok"}' % (gid, len(matched)))
    return {"guest_id": gid, "matches": matched}

@app.get("/feed")
def feed(event: str, guest_id: str):
    _ev(event, create=True)
    return {"guest_id": guest_id, "known": store.convidado_existe(event, guest_id),
            "photos": store.matches_de(guest_id)}

@app.get("/contatos")
def contatos(event: str):
    _ev(event, create=True)
    return {"event": event, "contatos": store.contatos_de(event)}

@app.get("/img/{event}/{photo_id}.jpg")
def img(event: str, photo_id: str):
    b = store.foto_bytes(event, photo_id)
    if not b: raise HTTPException(404)
    return Response(b, media_type="image/jpeg", headers={"Cache-Control": "public, max-age=86400"})

@app.post("/photo/delete")
def photo_delete(event: str = Form(...), photo_id: str = Form(...)):
    store.apaga_foto(event, photo_id)
    log.info('{"stage":"photo","photo_id":"%s","status":"deleted"}' % photo_id)
    return {"ok": True}

@app.get("/qr")
def qr(data: str):
    img = qrcode.make(data)
    buf = io.BytesIO(); img.save(buf, "PNG")
    return Response(buf.getvalue(), media_type="image/png", headers={"Cache-Control": "public, max-age=3600"})

# front-end (uma URL faz tudo). Rotas de API acima têm precedência.
app.mount("/", StaticFiles(directory=os.path.join(BASE, "app", "web"), html=True), name="web")
