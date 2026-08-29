"""Fóton — servidor do piloto (pipeline real + persistência + contas).

Fluxo: ingest -> watermark(marca do fotógrafo) -> detecção+embedding (ArcFace) ->
match -> feed do convidado. Dados em SQLite (store.py), não mais em memória.

Segurança (ADR-0005): a selfie do convidado NUNCA é armazenada — vira embedding e os
bytes são descartados. Logs sem PII (só id de rastreio, contagem, latência).
"""
import io, os, time, uuid, logging
import cv2, numpy as np, qrcode
from PIL import Image, ImageDraw, ImageFont, ImageOps
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Header, Request
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

LOGO_MAX = 900          # lado maior guardado no banco — watermark nao precisa de mais que isso
LOGO_LIMITE_BYTES = 3 * 1024 * 1024

def _prepara_logo(raw: bytes) -> bytes:
    """Valida e reduz o PNG antes de guardar — nunca guarda o arquivo do jeito que veio."""
    im = Image.open(io.BytesIO(raw))
    if im.format != "PNG":
        raise HTTPException(400, "envie um PNG (com transparência, se quiser fundo vazado)")
    im = im.convert("RGBA")
    w, h = im.size
    s = LOGO_MAX / max(w, h)
    if s < 1:
        im = im.resize((round(w * s), round(h * s)), Image.LANCZOS)
    out = io.BytesIO(); im.save(out, "PNG", optimize=True)
    return out.getvalue()

def _aplica_logo(img: Image.Image, logo_bytes: bytes, fw: int, fh: int):
    """Cola o logo (com o próprio alfa) no canto — substitui o texto quando existe."""
    try:
        lg = Image.open(io.BytesIO(logo_bytes)).convert("RGBA")
    except Exception:
        return False                      # logo corrompido: a foto segue sem marca, nunca quebra
    alvo_w = max(64, round(fw * 0.20))
    s = alvo_w / lg.width
    lg = lg.resize((alvo_w, max(1, round(lg.height * s))), Image.LANCZOS)
    m = round(fw * 0.02)
    x, y = fw - lg.width - m, fh - lg.height - m
    img.paste(lg, (x, y), lg)
    return True

def process_image(raw: bytes, marca: str = "FÓTON", logo: bytes = None):
    t0 = time.perf_counter()
    img = Image.open(io.BytesIO(raw))
    # draft: manda o decodificador de JPEG ja entregar a imagem reduzida (usa a escala
    # do proprio DCT, 1/2, 1/4...). Decodificar 24 MP inteiros para depois jogar 90%
    # fora era desperdicio puro no unico nucleo da VM.
    # Alvo 1024 e nao 2048 de proposito: com 2048 o PIL escolhe escala 1/1 e nao economiza
    # nada. Numa foto de camera (6000x4000) o draft entrega 3000x2000, que ainda e maior
    # que os 2048 finais — a imagem entregue fica IDENTICA. So numa origem perto de 4000px
    # o resultado fica 2000 em vez de 2048 (2,3% menor, irrelevante para o rosto).
    try: img.draft("RGB", (LONG_EDGE // 2, LONG_EDGE // 2))
    except Exception: pass
    # exif_transpose: celular/camera gravam a rotacao no EXIF. Sem isso a foto sai deitada.
    img = ImageOps.exif_transpose(img).convert("RGB")
    w, h = img.size
    s = LONG_EDGE / max(w, h)
    if s < 1:
        img = img.resize((round(w * s), round(h * s)), Image.LANCZOS)
    fw, fh = img.size
    # logo em PNG substitui o texto quando a fotografa subiu um; senao, marca por texto (como sempre)
    if not (logo and _aplica_logo(img, logo, fw, fh)):
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

def _pode(code, authorization):
    """Portão das ações destrutivas: só o DONO do evento (ou admin) mexe nele.

    O código do evento fica no QR projetado na parede da festa — sem isto, qualquer
    convidado apagava o evento, encerrava a festa ou injetava foto na galeria dos
    outros. Evento órfão (dono=None, do auto-create) aceita qualquer sessão válida,
    porque é assim que a fotógrafa readota o evento dela; anônimo, nunca.
    """
    c = _dono(authorization)
    if not c:
        raise HTTPException(401, "sessão expirada")
    e = store.evento(code)
    if e and e.get("dono") and e["dono"] != c["email"] and c["email"].lower() not in ADMINS:
        log.info('{"stage":"authz","code":"%s","status":"negado"}' % code)
        raise HTTPException(403, "este evento é de outra conta")
    return c

INICIO = time.time()
app = FastAPI(title="Fóton", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.middleware("http")
async def _sem_cache_na_api(request, call_next):
    """Defesa em profundidade: nenhuma resposta de API pode ser cacheada.
    Um cache em /me ou /events mostra os dados de OUTRA conta depois de trocar
    de login — foi exatamente o bug do 'entrei como admin e apareceu a Patrícia'."""
    resp = await call_next(request)
    p = request.url.path
    if not p.startswith("/img/") and ("." not in p.rsplit("/", 1)[-1] or p.endswith((".json",))):
        resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        resp.headers["Pragma"] = "no-cache"
    return resp

@app.on_event("startup")
def _startup():
    store.conn()
    try: _face(); log.info('{"stage":"warm","status":"ready"}')
    except Exception as e: log.info('{"stage":"warm","status":"fail","err":"%s"}' % str(e)[:140])
    # LGPD: expiração roda no boot e a cada 12h, sem depender de ninguém lembrar
    # FTP da câmera (opcional — se a lib não estiver instalada, o resto segue igual)
    try:
        import ftp_camera
        ftp_camera.iniciar(ingerir_bytes)
    except Exception as e:
        log.info('{"stage":"ftp","status":"desligado","motivo":"%s"}' % str(e)[:100])
    import threading
    def _limpeza():
        while True:
            try:
                r = store.expirar(RET_BIO, RET_FOTO)
                if r["convidados"] or r["fotos"]:
                    log.info('{"stage":"lgpd","acao":"expirou","convidados":%d,"fotos":%d}'
                             % (r["convidados"], r["fotos"]))
            except Exception:
                pass
            time.sleep(12 * 3600)
    threading.Thread(target=_limpeza, daemon=True).start()

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

_tentativas = {}          # ip -> [instantes de falha]
LIMITE_FALHAS, JANELA_S = 10, 600

def _freio(ip):
    """Freio contra força bruta no login. Conta só FALHA e por IP.

    10 falhas em 10 min é folgado de propósito: travar a fotógrafa que errou a senha
    no meio do evento seria pior que o ataque que isto evita.
    """
    agora = time.time()
    h = [t for t in _tentativas.get(ip, []) if agora - t < JANELA_S]
    _tentativas[ip] = h
    if len(h) >= LIMITE_FALHAS:
        raise HTTPException(429, "muitas tentativas — espere alguns minutos")

@app.post("/login")
def login(request: Request, email: str = Form(...), senha: str = Form(...)):
    ip = request.client.host if request.client else "?"
    _freio(ip)
    c = store.autentica(email, senha)
    if not c:
        _tentativas.setdefault(ip, []).append(time.time())
        log.info('{"stage":"login","status":"falha","tentativas":%d}' % len(_tentativas[ip]))
        raise HTTPException(401, "e-mail ou senha incorretos")
    _tentativas.pop(ip, None)                     # acertou: zera o histórico
    return {"token": store.novo_token(c["email"]), "nome": c["nome"], "marca": c["marca"],
            "credits": c["credits"], "credits_total": c["credits_total"], "email": c["email"]}

@app.post("/conta/logo")
async def conta_logo(file: UploadFile = File(...), authorization: str = Header(None)):
    """Marca d'água em imagem (PNG com transparência) — substitui o texto nas fotos dela."""
    c = _dono(authorization)
    if not c: raise HTTPException(401, "sessão expirada")
    raw = await file.read()
    if len(raw) > LOGO_LIMITE_BYTES:
        raise HTTPException(400, "arquivo muito grande (máximo 3 MB)")
    png = _prepara_logo(raw)
    store.salva_logo(c["email"], png)
    log.info('{"stage":"conta","acao":"logo_salvo"}')
    return {"ok": True}

@app.get("/conta/logo")
def conta_logo_ver(authorization: str = Header(None)):
    c = _dono(authorization)
    if not c: raise HTTPException(401, "sessão expirada")
    png = store.pega_logo(c["email"])
    if not png: raise HTTPException(404, "sem logo cadastrado")
    return Response(png, media_type="image/png", headers={"Cache-Control": "private, max-age=60"})

@app.post("/conta/logo/apagar")
def conta_logo_apagar(authorization: str = Header(None)):
    c = _dono(authorization)
    if not c: raise HTTPException(401, "sessão expirada")
    store.apaga_logo(c["email"])
    return {"ok": True}

@app.get("/me")
def me(authorization: str = Header(None)):
    c = _dono(authorization)
    if not c: raise HTTPException(401, "sessão expirada")
    evs = store.eventos_de(c["email"])
    return {"nome": c["nome"], "marca": c["marca"], "email": c["email"],
            "credits": c["credits"], "credits_total": c["credits_total"],
            "total_fotos": sum(e["fotos"] for e in evs),
            "total_convidados": sum(e["convidados"] for e in evs),
            "tem_logo": bool(c.get("logo"))}

# ============================ EVENTOS ============================
@app.post("/event")
def create_event(code: str = Form(...), brand: str = Form("FÓTON"),
                 name: str = Form(""), date: str = Form(""), authorization: str = Header(None)):
    c = _dono(authorization)
    store.cria_evento(code, dono=(c["email"] if c else None), nome=(name or "Evento"),
                      data=date, marca=brand, auto=0)
    if c: store.gasta_credito(c["email"])
    log.info('{"stage":"event","code":"%s","status":"created"}' % code)
    if c:
        # Fotos que a câmera mandou ANTES do evento existir entram agora, sozinhas.
        try:
            import ftp_camera; ftp_camera.drenar(c["email"])
        except Exception:
            pass
    return {"event": code, "brand": (brand or "FÓTON")}

@app.get("/events")
def events(authorization: str = Header(None)):
    c = _dono(authorization)
    # 401 explicito: devolver lista vazia com 200 fazia o app achar que o fotografo
    # nao tem eventos e APAGAR a lista local. Sessao invalida tem que ser erro.
    if not c: raise HTTPException(401, "sessão expirada")
    return {"events": [{"code": e["code"], "name": e["nome"], "date": e["data"], "brand": e["marca"],
                        "photos": e["fotos"], "guests": e["convidados"], "status": e["status"]}
                       for e in store.eventos_de(c["email"])]}

@app.post("/event/adotar")
def event_adotar(codes: str = Form(...), authorization: str = Header(None)):
    """O app manda os códigos que ele tem salvos localmente; o servidor devolve os que
    conseguiu vincular a esta conta. Recupera eventos que ficaram sem dono."""
    c = _dono(authorization)
    if not c: raise HTTPException(401, "sessão expirada")
    adotados = [x.strip() for x in codes.split(",") if x.strip() and store.adota_evento(x.strip(), c["email"])]
    if adotados: log.info('{"stage":"event","acao":"adotados","n":%d}' % len(adotados))
    return {"adotados": adotados}

@app.get("/admin/orfaos")
def admin_orfaos(authorization: str = Header(None)):
    _admin(authorization)
    return {"orfaos": store.orfaos()}

@app.post("/admin/adotar-todos")
def admin_adotar_todos(email: str = Form(...), authorization: str = Header(None)):
    """Vincula TODOS os eventos órfãos a um fotógrafo (resgate de suporte)."""
    _admin(authorization)
    if not store.conta(email.strip().lower()): raise HTTPException(404, "fotógrafo não encontrado")
    n = sum(1 for o in store.orfaos() if store.adota_evento(o["code"], email.strip().lower()))
    return {"ok": True, "adotados": n}

@app.post("/event/delete")
def event_delete(code: str = Form(...), authorization: str = Header(None)):
    _pode(code, authorization)
    existed = store.evento(code) is not None
    store.apaga_evento(code)
    log.info('{"stage":"event","code":"%s","status":"deleted"}' % code)
    return {"ok": True, "deleted": existed}

@app.post("/event/close")
def event_close(code: str = Form(...), authorization: str = Header(None)):
    _pode(code, authorization)
    store.encerra_evento(code)
    return {"ok": True}

@app.get("/stats")
def stats(event: str, authorization: str = Header(None)):
    """Alimenta a faixa fixa do painel dela durante o evento.

    `ultima_foto_s` e `aguardando` existem para responder a única pergunta que a
    fotógrafa faz no meio da festa: "está chegando?". Sem isso ela só vê um ponto
    verde que não prova nada.
    """
    e = _ev(event, create=True)
    ult = store.ultima_foto(event)
    out = {"event": event, "photos": len(store.fotos_de(event)),
           "guests": store.conta_convidados(event),
           "ultima_foto_s": (round(time.time() - ult) if ult else None)}
    c = _dono(authorization)
    if c and (not e.get("dono") or e["dono"] == c["email"]):
        try:                          # fila do FTP: foto que a câmera mandou e ainda não entrou
            import ftp_camera, os as _os
            p = ftp_camera._pendentes_do(c["email"])
            out["aguardando"] = len([f for f in _os.listdir(p) if not f.startswith(".")])
        except Exception:
            out["aguardando"] = None
    return out

@app.get("/photos")
def photos(event: str):
    _ev(event, create=True)
    return {"event": event, "photos": [{"id": p["id"], "n_faces": p["n_faces"]} for p in store.fotos_de(event)]}

# ============================ PIPELINE ============================
def ingerir_bytes(event: str, raw: bytes):
    """Coração do pipeline — usado pelo upload do app E pelo FTP da câmera."""
    e = _ev(event, create=True)
    pid = uuid.uuid4().hex[:12]
    logo = store.pega_logo(e["dono"]) if e.get("dono") else None
    treated, dims, pms = process_image(raw, e.get("marca") or "FÓTON", logo)
    faces = detect_embed(treated)
    store.salva_foto(pid, event, treated, faces)
    for gid, gemb in store.convidados_de(event):
        g = _emb(gemb)
        if any(float(g @ f) >= THRESH for f in faces):
            store.salva_match(gid, pid)
    return pid, len(faces)

@app.post("/ingest")
async def ingest(event: str = Form(...), file: UploadFile = File(...),
                 authorization: str = Header(None)):
    # Sem isto, qualquer um com o código do QR injetava imagem na galeria dos convidados.
    c = _pode(event, authorization)
    e = store.evento(event)
    if e is None:                      # primeira foto de um evento novo: já nasce COM DONO
        store.cria_evento(event, dono=c["email"], nome="Evento", auto=1)
        e = store.evento(event)
    raw = await file.read()
    pid = uuid.uuid4().hex[:12]
    t0 = time.time()
    logo = store.pega_logo(e["dono"]) if e.get("dono") else None
    treated, dims, pms = process_image(raw, e.get("marca") or "FÓTON", logo)
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
def contatos(event: str, authorization: str = Header(None)):
    # Nome e telefone de convidado é dado pessoal: só a dona do evento vê.
    # Aberto, bastava o código do QR para baixar a lista inteira (LGPD Art. 46).
    _pode(event, authorization)
    return {"event": event, "contatos": store.contatos_de(event)}

@app.get("/img/{event}/{photo_id}.jpg")
def img(event: str, photo_id: str):
    b = store.foto_bytes(event, photo_id)
    if not b: raise HTTPException(404)
    return Response(b, media_type="image/jpeg", headers={"Cache-Control": "public, max-age=86400"})

@app.post("/photo/delete")
def photo_delete(event: str = Form(...), photo_id: str = Form(...), authorization: str = Header(None)):
    _pode(event, authorization)
    store.apaga_foto(event, photo_id)
    log.info('{"stage":"photo","photo_id":"%s","status":"deleted"}' % photo_id)
    return {"ok": True}

# ============================ ADMIN ============================
ADMINS = {e.strip().lower() for e in os.environ.get("FOTON_ADMINS", "admin@foton.com").split(",")}

def _admin(authorization):
    c = _dono(authorization)
    if not c or c["email"].lower() not in ADMINS:
        raise HTTPException(403, "acesso restrito")
    return c

@app.get("/admin/resumo")
def admin_resumo(authorization: str = Header(None)):
    _admin(authorization)
    import shutil
    du = shutil.disk_usage("/")
    return {**store.resumo_geral(),
            "disco_livre_gb": round(du.free / 1e9, 1), "disco_total_gb": round(du.total / 1e9, 1),
            "fotografos_lista": store.todos_fotografos()}

@app.get("/admin/saude")
def admin_saude(authorization: str = Header(None)):
    """Torre de controle: o que precisa estar verde ANTES e DURANTE um evento.

    Tudo em try/except de propósito — um painel de saúde que quebra quando algo
    está estranho é justamente o que não serve. Campo que não deu para ler vem null.
    """
    _admin(authorization)
    import shutil, glob
    def _tenta(f, padrao=None):
        try: return f()
        except Exception: return padrao

    du = _tenta(lambda: shutil.disk_usage("/"))
    dbp = os.environ.get("FOTON_DB", "")
    dirdb = os.path.dirname(dbp) or "."

    def _mem():
        m = {}
        with open("/proc/meminfo") as f:
            for ln in f:
                p = ln.split()
                if p[0][:-1] in ("MemTotal", "MemAvailable"): m[p[0][:-1]] = int(p[1]) * 1024
        return {"total_mb": round(m["MemTotal"] / 1e6), "livre_mb": round(m["MemAvailable"] / 1e6),
                "uso_pct": round(100 * (1 - m["MemAvailable"] / m["MemTotal"]))}

    def _backup():
        arqs = glob.glob(os.path.join(dirdb, "backup", "*.db"))
        if not arqs: return None
        novo = max(arqs, key=os.path.getmtime)
        return {"horas_atras": round((time.time() - os.path.getmtime(novo)) / 3600, 1),
                "tamanho_mb": round(os.path.getsize(novo) / 1e6, 1), "copias": len(arqs)}

    def _fila():
        raiz = os.environ.get("FOTON_FTP_DIR", "/var/lib/foton/ftp")
        n = sum(len(fs) for _, _, fs in os.walk(os.path.join(raiz, "_pendentes")))
        return n

    banco_mb = _tenta(lambda: round(os.path.getsize(dbp) / 1e6, 1))
    bkp = _tenta(_backup)
    return {
        "servidor": {
            "uptime_processo_h": round((time.time() - INICIO) / 3600, 1),
            "uptime_maquina_h": _tenta(lambda: round(float(open("/proc/uptime").read().split()[0]) / 3600, 1)),
            "carga": _tenta(lambda: open("/proc/loadavg").read().split()[:3]),
            "memoria": _tenta(_mem),
        },
        "disco": {
            "livre_gb": _tenta(lambda: round(du.free / 1e9, 1)),
            "total_gb": _tenta(lambda: round(du.total / 1e9, 1)),
            "uso_pct": _tenta(lambda: round(100 * (du.total - du.free) / du.total)),
            "banco_mb": banco_mb,
            # o backup guarda 7 cópias do banco INTEIRO, e as fotos moram nele
            "backups_ocupam_mb": _tenta(lambda: round(sum(os.path.getsize(a) for a in
                                       glob.glob(os.path.join(dirdb, "backup", "*.db"))) / 1e6, 1)),
        },
        "backup": bkp,
        "fila": {"fotos_ftp_aguardando": _tenta(_fila), "ftp_ligado": _tenta(lambda: __import__("ftp_camera") is not None, False)},
        "negocio": store.resumo_geral(),
        "alertas": [a for a in [
            "DISCO ACIMA DE 80%" if _tenta(lambda: (du.total - du.free) / du.total > .8) else None,
            "BACKUP COM MAIS DE 48H" if (bkp and bkp["horas_atras"] > 48) else ("SEM BACKUP" if not bkp else None),
            "FOTOS PRESAS NA FILA DO FTP" if _tenta(_fila, 0) else None,
        ] if a],
    }

@app.post("/admin/creditos")
def admin_creditos(email: str = Form(...), quantidade: int = Form(...), authorization: str = Header(None)):
    _admin(authorization)
    c = store.da_creditos(email, max(-999, min(999, quantidade)))
    if not c: raise HTTPException(404, "fotógrafo não encontrado")
    log.info('{"stage":"admin","acao":"creditos","alvo":"%s","n":%d}' % (email, quantidade))
    return {"ok": True, "credits": c["credits"], "credits_total": c["credits_total"]}

@app.post("/conta/excluir")
def conta_excluir(senha: str = Form(...), authorization: str = Header(None)):
    """O próprio fotógrafo encerra a conta. Pede a senha de novo de propósito: é
    irreversível e leva junto eventos e fotos (LGPD Art. 18)."""
    c = _dono(authorization)
    if not c: raise HTTPException(401, "sessão expirada")
    if not store.autentica(c["email"], senha): raise HTTPException(403, "senha incorreta")
    store.apaga_conta(c["email"])
    log.info('{"stage":"conta","acao":"excluida_pelo_titular"}')
    return {"ok": True}

@app.post("/admin/conta/excluir")
def admin_conta_excluir(email: str = Form(...), authorization: str = Header(None)):
    """Limpeza de suporte: apagar conta de teste sem precisar da senha dela."""
    a = _admin(authorization)
    alvo = email.strip().lower()
    if alvo == a["email"].lower(): raise HTTPException(400, "não dá para apagar a própria conta de admin")
    if not store.apaga_conta(alvo): raise HTTPException(404, "fotógrafo não encontrado")
    log.info('{"stage":"admin","acao":"conta_excluida","alvo":"%s"}' % alvo)
    return {"ok": True}

@app.post("/admin/senha")
def admin_senha(email: str = Form(...), nova: str = Form(...), authorization: str = Header(None)):
    _admin(authorization)
    if len(nova) < 6: raise HTTPException(400, "senha muito curta (mínimo 6)")
    if not store.conta(email.strip().lower()): raise HTTPException(404, "fotógrafo não encontrado")
    store.troca_senha(email, nova)
    log.info('{"stage":"admin","acao":"senha","alvo":"%s"}' % email)
    return {"ok": True}

@app.post("/admin/testar-foto")
def admin_testar_foto(file: UploadFile = File(...), authorization: str = Header(None)):
    """Canivete suíço da visita presencial: manda uma foto da câmera da fotógrafa e
    diz na hora se o rosto seria reconhecido — valida o setup dela em segundos."""
    _admin(authorization)
    import asyncio
    raw = asyncio.run(file.read()) if False else file.file.read()
    t0 = time.time()
    treated, dims, pms = process_image(raw)
    faces = detect_embed(treated)
    dica = ("Perfeito — rosto reconhecido." if len(faces) == 1 else
            f"{len(faces)} rostos reconhecidos." if faces else
            "Nenhum rosto lido. Aproxime a pessoa, use luz melhor e rosto de frente.")
    return {"n_faces": len(faces), "dims": dims, "processing_ms": round(pms, 1),
            "total_ms": int((time.time() - t0) * 1000), "dica": dica}

# ======================= FTP DA CÂMERA =======================
@app.get("/camera/config")
def camera_config(authorization: str = Header(None)):
    """Dados que a fotógrafa digita na câmera para enviar direto, sem celular."""
    c = _dono(authorization)
    if not c: raise HTTPException(401, "sessão expirada")
    try:
        import ftp_camera
        senha = ftp_camera.senha_ftp(c["email"])
        porta = ftp_camera.PORTA
        ativo = True
        ha_s = ftp_camera.conectada_ha_s(c["email"])
    except Exception:
        senha, porta, ativo, ha_s = None, None, False, None
    ao_vivo = next((e["code"] for e in store.eventos_de(c["email"]) if e["status"] == "live"), None)
    return {"ativo": ativo, "servidor": os.environ.get("FOTON_HOST", "getfoton.duckdns.org"),
            "porta": porta, "usuario": c["email"], "senha": senha, "modo": "FTP passivo",
            "evento_ao_vivo": ao_vivo, "conectada_ha_s": (round(ha_s) if ha_s is not None else None),
            "aviso": None if ao_vivo else "Crie/abra um evento antes de fotografar — as fotos vão para o evento ao vivo."}

# ============================ LGPD ============================
RET_BIO = int(os.environ.get("FOTON_RET_BIOMETRIA_DIAS", "7"))    # biometria: vida curta
RET_FOTO = int(os.environ.get("FOTON_RET_FOTOS_DIAS", "90"))      # fotos: retenção do plano

@app.get("/privacidade")
def privacidade():
    """Transparência (LGPD Art. 9º): o que coletamos, por quê e por quanto tempo."""
    return {
        "controlador": "Fóton — fotos na hora",
        "contato": os.environ.get("FOTON_CONTATO", "luizoak@gmail.com"),
        "dados_do_convidado": {
            "selfie": "usada apenas para gerar o código facial e DESCARTADA em seguida; nunca é armazenada",
            "codigo_facial": "vetor matemático (não permite reconstruir o rosto), usado só para achar suas fotos neste evento",
            "nome_e_contato": "opcionais; só se você preencher",
        },
        "base_legal": "consentimento específico e destacado para dado sensível (LGPD Art. 11, I)",
        "retencao": {"codigo_facial_dias": RET_BIO, "fotos_do_evento_dias": RET_FOTO},
        "compartilhamento": "nenhum. O reconhecimento roda em servidor próprio, sem enviar rostos a terceiros",
        "seus_direitos": "confirmar, acessar, corrigir e EXCLUIR seus dados a qualquer momento (Art. 18)",
        "como_excluir": "POST /convidado/excluir com o seu guest_id, ou peça pelo contato acima",
        "servidores": "Brasil (São Paulo)",
    }

@app.post("/convidado/excluir")
def convidado_excluir(guest_id: str = Form(...)):
    """Direito de exclusão do titular — sem burocracia, o próprio app chama."""
    ok = store.apagar_dados_do_convidado(guest_id)
    log.info('{"stage":"lgpd","acao":"exclusao","achou":%s}' % str(ok).lower())
    return {"ok": True, "removido": ok}

@app.post("/admin/expirar")
def admin_expirar(authorization: str = Header(None)):
    _admin(authorization)
    r = store.expirar(RET_BIO, RET_FOTO)
    return {"ok": True, **r, "politica": {"biometria_dias": RET_BIO, "fotos_dias": RET_FOTO}}

@app.get("/qr")
def qr(data: str):
    img = qrcode.make(data)
    buf = io.BytesIO(); img.save(buf, "PNG")
    return Response(buf.getvalue(), media_type="image/png", headers={"Cache-Control": "public, max-age=3600"})

# front-end (uma URL faz tudo). Rotas de API acima têm precedência.
app.mount("/", StaticFiles(directory=os.path.join(BASE, "app", "web"), html=True), name="web")
