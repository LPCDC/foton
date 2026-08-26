"""Fóton — TEST-RIG (pipeline REAL mínimo para o teste ao vivo da reunião).

NÃO é a arquitetura de produto (isso é ADR-0010/nuvem). Isto é um rig efêmero para
provar, ao vivo, que uma foto real percorre: ingest -> watermark -> facial -> match ->
feed do convidado. Reusa EXP-04 (watermark), EXP-05 (YuNet+SFace), EXP-06 (match).

Segurança (ADR-0005): a selfie do convidado NUNCA é armazenada nem servida — vira
embedding em memória e é descartada com o /reset ou ao encerrar o processo. Logs sem
PII (só id de rastreio, contagem, latência). Acesso com código de evento.
"""
import io, os, time, uuid, logging
import cv2, numpy as np, qrcode
from PIL import Image, ImageDraw, ImageFont
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Render free = CPU compartilhada: onnxruntime multi-thread trava/crasha (502).
# Forca 1 thread ANTES do insightface criar qualquer sessao.
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
import onnxruntime as _ort
_ort_orig = _ort.InferenceSession
def _ort_1thread(*a, **k):
    so = k.pop("sess_options", None) or _ort.SessionOptions()
    so.intra_op_num_threads = 1
    so.inter_op_num_threads = 1
    return _ort_orig(*a, sess_options=so, **k)
_ort.InferenceSession = _ort_1thread
from insightface.app import FaceAnalysis

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(os.path.dirname(HERE))
THRESH = 0.25           # ArcFace/buffalo_s — validado (iguais ~0.61, diferentes ~0.01; 99.6% LFW)
LONG_EDGE = 2048
JPEG_Q = 82

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("foton")

_fa = None
def _face():
    """InsightFace buffalo_l (SCRFD deteccao + ArcFace r50 reconhecimento), CPU, det+rec.
    Modelos baixam sozinhos (~/.insightface) na 1a chamada."""
    global _fa
    if _fa is None:
        _fa = FaceAnalysis(name="buffalo_s", allowed_modules=["detection", "recognition"],
                           providers=["CPUExecutionProvider"])
        _fa.prepare(ctx_id=-1, det_size=(320, 320))
    return _fa

def _font(sz):
    for p in (r"C:\Windows\Fonts\arialbd.ttf", r"C:\Windows\Fonts\arial.ttf"):
        try: return ImageFont.truetype(p, sz)
        except Exception: pass
    return ImageFont.load_default()

def process_image(raw: bytes):
    t0 = time.perf_counter()
    img = Image.open(io.BytesIO(raw)).convert("RGB")
    w, h = img.size
    s = LONG_EDGE / max(w, h)
    if s < 1:
        img = img.resize((round(w * s), round(h * s)), Image.LANCZOS)
    fw, fh = img.size
    d = ImageDraw.Draw(img, "RGBA")
    font = _font(max(18, fw // 28))
    txt = "FÓTON"
    bb = d.textbbox((0, 0), txt, font=font); tw, th = bb[2] - bb[0], bb[3] - bb[1]
    m = int(fw * 0.02); x, y = fw - tw - m, fh - th - m * 2
    d.text((x + 2, y + 2), txt, font=font, fill=(0, 0, 0, 120))
    d.text((x, y), txt, font=font, fill=(255, 255, 255, 190))
    out = io.BytesIO(); img.save(out, "JPEG", quality=JPEG_Q, optimize=True, progressive=True)
    return out.getvalue(), (fw, fh), (time.perf_counter() - t0) * 1000

def detect_embed(raw: bytes):
    app = _face()
    arr = np.frombuffer(raw, np.uint8)
    bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if bgr is None:
        return []
    return [f.normed_embedding.astype(np.float32) for f in app.get(bgr)]  # ArcFace, ja L2-normalizado

# ---- store efêmero em memória ----
EVENTS = {}   # code -> {"photos":{pid:{bytes,faces,ts}}, "guests":{gid:emb}, "matches":{gid:set(pid)}}
def _ev(code, create=False):
    e = EVENTS.get(code)
    if e is None:
        if not create:
            raise HTTPException(404, "evento nao encontrado")
        e = EVENTS[code] = {"photos": {}, "guests": {}, "matches": {}}
        log.info('{"stage":"event","code":"%s","status":"auto-created"}' % code)
    return e

app = FastAPI(title="Fóton test-rig", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/health")
def health():
    return {"ok": True, "engine": "InsightFace buffalo_s (SCRFD+ArcFace) CPU", "events": len(EVENTS)}

@app.post("/event")
def create_event(code: str = Form(...)):
    EVENTS[code] = {"photos": {}, "guests": {}, "matches": {}}
    log.info('{"stage":"event","code":"%s","status":"created"}' % code)
    return {"event": code}

@app.post("/ingest")
async def ingest(event: str = Form(...), file: UploadFile = File(...)):
    e = _ev(event, create=True)
    raw = await file.read()
    pid = uuid.uuid4().hex[:12]
    t0 = time.time()
    treated, dims, pms = process_image(raw)
    faces = detect_embed(treated)
    e["photos"][pid] = {"bytes": treated, "faces": faces, "ts": time.time()}
    matched = []
    for gid, gemb in e["guests"].items():
        if any(float(gemb @ f) >= THRESH for f in faces):
            e["matches"].setdefault(gid, set()).add(pid); matched.append(gid)
    lat = int((time.time() - t0) * 1000)
    log.info('{"stage":"ingest","photo_id":"%s","n_faces":%d,"proc_ms":%.0f,"latency_ms":%d,"status":"ok"}'
             % (pid, len(faces), pms, lat))
    return {"photo_id": pid, "n_faces": len(faces), "dims": dims,
            "processing_ms": round(pms, 1), "latency_ms": lat, "matched_guests": matched}

@app.post("/selfie")
async def selfie(event: str = Form(...), consent: bool = Form(...), file: UploadFile = File(...)):
    e = _ev(event, create=True)
    if not consent:
        raise HTTPException(400, "consentimento obrigatorio (LGPD, ADR-0005)")
    raw = await file.read()                 # bytes da selfie: usados e descartados
    faces = detect_embed(raw)
    if not faces:
        raise HTTPException(422, "nenhum rosto detectado na selfie")
    emb = faces[0]
    gid = uuid.uuid4().hex[:12]
    e["guests"][gid] = emb
    matched = [pid for pid, p in e["photos"].items()
               if any(float(emb @ f) >= THRESH for f in p["faces"])]
    e["matches"][gid] = set(matched)
    log.info('{"stage":"selfie","guest_id":"%s","matches":%d,"status":"ok"}' % (gid, len(matched)))
    return {"guest_id": gid, "matches": matched}

@app.get("/feed")
def feed(event: str, guest_id: str):
    e = _ev(event, create=True)
    return {"guest_id": guest_id, "photos": sorted(e["matches"].get(guest_id, set()))}

@app.get("/img/{event}/{photo_id}.jpg")
def img(event: str, photo_id: str):
    e = _ev(event)
    p = e["photos"].get(photo_id)
    if not p:
        raise HTTPException(404)
    return Response(p["bytes"], media_type="image/jpeg",
                    headers={"Cache-Control": "public, max-age=86400"})

@app.get("/photos")
def photos(event: str):
    """Lista as fotos de um evento (p/ o fotografo reabrir e ver o que ja subiu)."""
    e = _ev(event, create=True)
    return {"event": event, "photos": [{"id": pid, "n_faces": len(p["faces"])} for pid, p in e["photos"].items()]}

@app.get("/qr")
def qr(data: str):
    img = qrcode.make(data)
    buf = io.BytesIO(); img.save(buf, "PNG")
    return Response(buf.getvalue(), media_type="image/png",
                    headers={"Cache-Control": "public, max-age=3600"})

@app.post("/reset")
def reset():
    EVENTS.clear()
    return {"ok": True}

# serve o front-end (uma URL só faz tudo). Rotas de API acima têm precedência.
app.mount("/", StaticFiles(directory=os.path.join(BASE, "app", "web"), html=True), name="web")
