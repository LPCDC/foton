"""Fóton — servidor do piloto (pipeline real + persistência + contas).

Fluxo: ingest -> watermark(marca do fotógrafo) -> detecção+embedding (ArcFace) ->
match -> feed do convidado. Dados em SQLite (store.py), não mais em memória.

Segurança (ADR-0005): a selfie do convidado NUNCA é armazenada — vira embedding e os
bytes são descartados. Logs sem PII (só id de rastreio, contagem, latência).
"""
import io, os, re, time, uuid, logging
import cv2, numpy as np, qrcode
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageEnhance
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
THUMB_EDGE = 320        # a grade mostra ~110px; 320 cobre tela retina sem exagero
THUMB_Q = 70

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

# ---------------- LOOK por conta (ADR-0028) ----------------
# NAO e editor, nao e "Lightroom na nuvem", nao e IA. E uma curva por canal aplicada
# com Image.point() — UMA passada em C sobre a imagem que o pipeline JA decodificou,
# exatamente o mesmo truque da miniatura (ADR-0022). O que a fotografa quer e "a foto
# sair com a cara dela", nao um editor dentro do Foton.
#
# REGRA DE OURO desta funcao: look vazio/desconhecido = pipeline IDENTICO ao de sempre.
# Nada aqui pode derrubar o ingest — foto sem look e melhor que foto nenhuma.
#
# ganho  = multiplica o canal (vies de cor)
# gamma  = <1 clareia o meio-tom do canal, >1 escurece
# lift   = levanta o preto (aquele cinza de filme; 0 = preto continua preto)
# contra = S-curve suave em torno do meio-tom
# sat    = saturacao (1 = intocada)
LOOKS = {
    "quente": {"rotulo": "Quente",       "ganho": (1.06, 1.01, 0.94), "gamma": (0.98, 1.00, 1.02), "lift": 0.010, "contra": 0.10, "sat": 1.06},
    "frio":   {"rotulo": "Frio",         "ganho": (0.95, 1.00, 1.07), "gamma": (1.02, 1.00, 0.97), "lift": 0.008, "contra": 0.12, "sat": 1.02},
    "filme":  {"rotulo": "Filme",        "ganho": (1.03, 1.00, 0.99), "gamma": (0.97, 0.99, 1.01), "lift": 0.055, "contra": 0.06, "sat": 0.92},
    "vivo":   {"rotulo": "Vivo",         "ganho": (1.00, 1.00, 1.00), "gamma": (1.00, 1.00, 1.00), "lift": 0.000, "contra": 0.22, "sat": 1.18},
    "pb":     {"rotulo": "Preto e branco","ganho": (1.00, 1.00, 1.00), "gamma": (1.00, 1.00, 1.00), "lift": 0.020, "contra": 0.16, "sat": 0.00},
}
_TABELAS = {}          # nome -> lista de 768 valores; a curva e a mesma para toda foto

def _tabela(nome):
    """Monta (uma vez) a tabela de 256 valores por canal que o Image.point() consome."""
    if nome in _TABELAS:
        return _TABELAS[nome]
    p = LOOKS[nome]
    tab = []
    for canal in range(3):
        ganho, gama = p["ganho"][canal], p["gamma"][canal]
        for i in range(256):
            v = i / 255.0
            v = v ** gama                                   # gamma do canal
            v = p["lift"] + v * (1.0 - p["lift"])           # levanta o preto
            v = v + p["contra"] * (v - 0.5) * (1.0 - abs(v - 0.5) * 2) * 0.5 * 2  # S-curve suave
            v = v * ganho
            tab.append(max(0, min(255, round(v * 255))))
    _TABELAS[nome] = tab
    return tab

def aplica_look(img: Image.Image, nome: str):
    """Aplica o look e devolve a imagem. Look vazio/desconhecido -> devolve a MESMA imagem.

    Envolto em try/except pela mesma razao do _thumb: um look com problema nunca pode
    impedir a foto de chegar na convidada.
    """
    if not nome:
        return img
    nome = str(nome).strip().lower()
    if nome not in LOOKS:
        return img
    try:
        p = LOOKS[nome]
        img = img.point(_tabela(nome))
        if p["sat"] == 0.0:
            img = img.convert("L").convert("RGB")           # preto e branco
        elif p["sat"] != 1.0:
            img = ImageEnhance.Color(img).enhance(p["sat"])
        return img
    except Exception:
        return img                                          # nunca derruba o ingest

def process_image(raw: bytes, marca: str = "FÓTON", logo: bytes = None, look: str = None):
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
    # LOOK antes da marca d'agua, de proposito: a curva e para a FOTO, nao para a marca.
    # Aplicar depois tingiria o logo/texto da fotografa junto (ADR-0028).
    img = aplica_look(img, look)
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
    # Miniatura na MESMA passada (ADR-0022): a imagem ja esta decodificada em memoria,
    # entao e um resize, nao uma segunda decodificacao. ~15 KB contra ~400 KB da foto.
    thumb = _thumb(img)
    return out.getvalue(), (fw, fh), (time.perf_counter() - t0) * 1000, thumb

def _thumb(img: Image.Image) -> bytes:
    """Reduz a imagem JA decodificada. Nunca deixa a falta de miniatura derrubar o
    ingest: se der errado, a foto entra sem thumb e a grade cai na foto inteira."""
    try:
        m = img.copy()
        m.thumbnail((THUMB_EDGE, THUMB_EDGE), Image.LANCZOS)
        b = io.BytesIO(); m.save(b, "JPEG", quality=THUMB_Q, optimize=True)
        return b.getvalue()
    except Exception:
        return None

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

def _senha_de_admin(senha):
    """A senha informada e a de ALGUM login da lista de admins?"""
    if not senha: return False
    return any(store.autentica(a, senha) for a in ADMINS)

def _exige_elevacao(c, senha_admin):
    """Conta de EMPRESA e login compartilhado pela equipe: ve e baixa tudo, mas nao
    cria nem apaga sem a senha de admin. A trava vive no SERVIDOR — esconder o botao
    na tela nao segura ninguem que saiba abrir o console."""
    if not c or not c.get("empresa"): return
    if c["email"].lower() in ADMINS: return
    if not _senha_de_admin(senha_admin):
        raise HTTPException(403, "esta conta é de empresa: peça a senha de administrador")

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
                # Loga SEMPRE, inclusive quando nao havia nada a expirar. Sem isto nao ha
                # como distinguir "rodou e nao tinha nada" de "nunca rodou" — e a segunda
                # e uma falha de conformidade silenciosa.
                log.info('{"stage":"lgpd","acao":"expirou","convidados":%d,"fotos":%d}'
                         % (r["convidados"], r["fotos"]))
            except Exception as e:
                # Antes: `except Exception: pass`. A expiracao de BIOMETRIA falhava em
                # SILENCIO — a retencao da politica de privacidade podia estar parada ha
                # meses sem ninguem saber. Falha de conformidade nao pode ser muda.
                log.error('{"stage":"lgpd","acao":"expirou","status":"FALHOU","erro":"%s"}'
                          % str(e).replace('"', "'")[:200])
            time.sleep(12 * 3600)
    threading.Thread(target=_limpeza, daemon=True).start()

def _versao():
    """Qual codigo esta rodando AGORA na VM.

    Sem isto, 'o push ja subiu?' era fe: um deploy que nao pegou e um deploy que pegou
    respondiam exatamente igual. Le o SHA do .git sem subprocess (so leitura de
    arquivo); se nao houver .git, cai para uma impressao digital do proprio fonte, que
    muda a cada alteracao. Um dos dois sempre responde."""
    import hashlib as _hl
    try:
        d = os.path.dirname(os.path.abspath(__file__))
        for _ in range(4):
            g = os.path.join(d, ".git")
            if os.path.isdir(g):
                with open(os.path.join(g, "HEAD")) as f:
                    h = f.read().strip()
                if not h.startswith("ref:"):
                    return h[:7]
                ref = h[4:].strip()
                alvo = os.path.join(g, ref)
                if os.path.exists(alvo):
                    with open(alvo) as f:
                        return f.read().strip()[:7]
                pr = os.path.join(g, "packed-refs")     # repo com refs empacotadas
                if os.path.exists(pr):
                    with open(pr) as f:
                        for ln in f:
                            if ln.rstrip().endswith(" " + ref):
                                return ln.split()[0][:7]
                break
            d = os.path.dirname(d)
    except Exception:
        pass
    try:
        with open(os.path.abspath(__file__), "rb") as f:
            return "src:" + _hl.sha256(f.read()).hexdigest()[:7]
    except Exception:
        return "desconhecida"

_VERSAO = _versao()

@app.get("/health")
def health():
    """Saude do PIPELINE, nao so 'o processo respondeu'.

    Antes isto devolvia tres constantes: dizia OK com o banco no chao. Agora bate no
    banco de verdade e informa se o motor facial esta carregado.

    `engine_carregado:false` e um ALARME, nao um "ainda vai carregar": o motor e
    aquecido no startup (`_startup` chama `_face()`), e aquela chamada esta dentro de
    um try/except para o servidor subir mesmo se o modelo falhar. Entao false significa
    que o warm-up FALHOU — o app aceita foto e nao reconhece ninguem. Antes disto, esse
    estado era invisivel ate a festa comecar.

    Publico de proposito e por isso SEM numero de negocio (quantas fotos, quantos
    clientes) e sem PII — regra da secao 7. O detalhe fica em /admin/saude."""
    t0 = time.time()
    try:
        store.q("SELECT 1", (), "one")
        db_ok, db_ms = True, int((time.time() - t0) * 1000)
    except Exception:
        db_ok, db_ms = False, None
    return {"ok": db_ok, "versao": _VERSAO, "db": "sqlite", "db_ok": db_ok, "db_ms": db_ms,
            "engine": "InsightFace buffalo_s (SCRFD+ArcFace) CPU",
            "engine_carregado": _fa is not None}

# ---- latencia do ingest: janela em memoria para provar (ou desmentir) o SLA ----
# CLAUDE.md §2: o que importa e P95, nao media. Ate aqui cada ingest logava a propria
# latencia e ninguem somava — para responder "estamos dentro dos 10s?" era preciso ir
# catar log. Esta janela e de MEMORIA (morre no restart) e sem PII: so numeros.
# HONESTO: mede o SERVIDOR (chegada do byte -> foto no banco + match), nao o
# end-to-end do disparo ate o celular. O trecho camera->servidor e celular<-servidor
# continua `UNKNOWN — REQUIRES EXPERIMENT`.
_LATS = []
def _marca_latencia(ms):
    _LATS.append(ms)
    if len(_LATS) > 500:                 # janela deslizante: as 500 ultimas
        del _LATS[:len(_LATS) - 500]

def _pct(vals, p):
    if not vals: return None
    o = sorted(vals)
    return o[min(len(o) - 1, int(round((p / 100.0) * (len(o) - 1))))]

# ============================ CONTAS ============================
def _perfil(c):
    # ADR-0030: o perfil de APRESENTACAO (vocabulario, blocos, tokens) e declarado
    # pelo servidor — o cliente obedece (regra da ADR-0025). Derivado, sem coluna:
    # 'social' e valor reservado para a frente da Ana (PRODUTO §2). Poder continua
    # sendo `empresa` (_exige_elevacao) e a lista FOTON_ADMINS; perfil nao abre porta.
    return "empresa" if c.get("empresa") else "pro"

@app.post("/signup")
def signup(email: str = Form(...), senha: str = Form(...), nome: str = Form(""), marca: str = Form("")):
    if len(senha) < 6: raise HTTPException(400, "senha muito curta (mínimo 6)")
    # Buraco fechado em 2026-08-29: o cadastro e ABERTO e nao conferia ADMINS. Como a
    # lista de admins vive no codigo de um repo PUBLICO, bastava alguem se cadastrar com
    # um login de admin que ainda nao tivesse conta para virar admin — e ler todos os
    # contatos, apagar contas e trocar senhas. Mesma trava que ja existe em
    # /conta/credenciais (renomear-se para admin).
    if email.strip().lower() in ADMINS:
        raise HTTPException(403, "esse login é reservado")
    if not store.cria_conta(email, senha, nome, marca):
        raise HTTPException(409, "já existe uma conta com esse e-mail")
    c = store.autentica(email, senha)
    return {"token": store.novo_token(c["email"]), "nome": c["nome"], "marca": c["marca"],
            "credits": c["credits"], "credits_total": c["credits_total"], "email": c["email"],
            "admin": _eh_admin(c),
            "empresa": bool(c.get("empresa")), "perfil": _perfil(c)}

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
            "credits": c["credits"], "credits_total": c["credits_total"], "email": c["email"],
            "admin": _eh_admin(c),
            "empresa": bool(c.get("empresa")), "perfil": _perfil(c)}

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

@app.get("/conta/look")
def conta_look_ver(authorization: str = Header(None)):
    """Look atual + o cardapio. O front nao inventa a lista: ela vem do servidor."""
    c = _dono(authorization)
    if not c: raise HTTPException(401, "sessão expirada")
    return {"look": store.pega_look(c["email"]) or "",
            "opcoes": [{"id": k, "rotulo": v["rotulo"]} for k, v in LOOKS.items()]}

@app.post("/conta/look")
def conta_look(look: str = Form(""), authorization: str = Header(None)):
    """A fotografa escolhe o look da conta. Vazio = nenhum (a foto sai como sempre saiu).

    Vale so para foto NOVA: nao reprocessa o que ja foi entregue. Reprocessar mudaria
    debaixo do pe uma foto que a convidada ja pode ter baixado.
    """
    c = _dono(authorization)
    if not c: raise HTTPException(401, "sessão expirada")
    v = (look or "").strip().lower()
    if v and v not in LOOKS:
        raise HTTPException(400, "look desconhecido")
    store.salva_look(c["email"], v)
    log.info('{"stage":"conta","acao":"look","valor":"%s"}' % (v or "nenhum"))
    return {"ok": True, "look": v}

@app.get("/me")
def me(authorization: str = Header(None)):
    c = _dono(authorization)
    if not c: raise HTTPException(401, "sessão expirada")
    evs = store.eventos_de(c["email"])
    return {"nome": c["nome"], "marca": c["marca"], "email": c["email"],
            "empresa": bool(c.get("empresa")), "perfil": _perfil(c),
            "admin": _eh_admin(c),
            "credits": c["credits"], "credits_total": c["credits_total"],
            "total_fotos": sum(e["fotos"] for e in evs),
            "total_convidados": sum(e["convidados"] for e in evs),
            "tem_logo": bool(c.get("logo"))}

# ============================ EVENTOS ============================
@app.post("/event")
def create_event(code: str = Form(...), brand: str = Form("FÓTON"),
                 name: str = Form(""), date: str = Form(""), senha_admin: str = Form(""),
                 authorization: str = Header(None)):
    c = _dono(authorization)
    _exige_elevacao(c, senha_admin)
    # Credito so sai quando o evento e NOVO. Antes saia em toda chamada, e o app tenta
    # ate 8 vezes quando a rede esta ruim (cold start): um unico evento podia queimar 8
    # creditos. `cria_evento` usa INSERT OR REPLACE, entao reenviar o mesmo codigo nao
    # duplicava o evento — so o credito ia embora, em silencio.
    # CREDITO DESLIGADO (2026-08-30, decisao do dono): nesta fase tudo e gratis, com
    # login. As colunas continuam na base para nao perder historico e para o painel do
    # admin nao quebrar, mas nada e gasto e nada bloqueia. O substituto planejado e
    # limite de UPLOAD, que mede o que de fato custa (disco e CPU) — docs/PRODUTO.md 3c.
    store.cria_evento(code, dono=(c["email"] if c else None), nome=(name or "Evento"),
                      data=date, marca=brand, auto=0)
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
def event_delete(code: str = Form(...), senha_admin: str = Form(""), authorization: str = Header(None)):
    _exige_elevacao(_pode(code, authorization), senha_admin)
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
    # LEITURA NAO CRIA. Antes era create=True: quem digitasse um codigo errado fazia
    # nascer um evento fantasma sem dono, e via uma galeria vazia para sempre em vez de
    # "esse codigo nao existe". Foi assim que apareceu 1 orfao 3 minutos depois de zerar
    # o banco. Fabrica de orfaos fechada aqui e no /photos.
    e = _ev(event, create=False)
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
    _ev(event, create=False)          # leitura nao cria (ver /stats)
    return {"event": event, "photos": [{"id": p["id"], "n_faces": p["n_faces"]} for p in store.fotos_de(event)]}

# ============================ PIPELINE ============================
def ingerir_bytes(event: str, raw: bytes):
    """Coração do pipeline — usado pelo upload do app E pelo FTP da câmera."""
    e = _ev(event, create=True)
    t0 = time.time()
    sha = store.sha_de(raw)
    ja = store.foto_por_sha(event, sha)      # retentativa do FTP nao vira foto repetida
    if ja:
        return ja, store.n_faces_de(event, ja)
    pid = uuid.uuid4().hex[:12]
    logo = store.pega_logo(e["dono"]) if e.get("dono") else None
    look = store.pega_look(e["dono"]) if e.get("dono") else None
    treated, dims, pms, thumb = process_image(raw, e.get("marca") or "FÓTON", logo, look)
    faces = detect_embed(treated)
    store.salva_foto(pid, event, treated, faces, thumb, sha)
    for gid, gemb in store.convidados_de(event):
        g = _emb(gemb)
        if any(float(g @ f) >= THRESH for f in faces):
            store.salva_match(gid, pid)
    # A CAMERA passa por aqui (o /ingest e o caminho do celular). Sem esta linha o P95
    # ficava cego justamente para o caminho principal do piloto — e o numero do SLA
    # mediria so o celular da fotografa, nao a R8.
    _marca_latencia(int((time.time() - t0) * 1000))
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
    t0 = time.time()
    # IDEMPOTENCIA (antes de qualquer processamento — o objetivo e justamente NAO gastar
    # ~1s de CPU de novo): a mesma foto reenviada devolve a entrega original.
    sha = store.sha_de(raw)
    ja = store.foto_por_sha(event, sha)
    if ja:
        lat = int((time.time() - t0) * 1000)
        log.info('{"stage":"ingest","photo_id":"%s","latency_ms":%d,"status":"duplicada"}' % (ja, lat))
        return {"photo_id": ja, "n_faces": store.n_faces_de(event, ja), "duplicada": True,
                "latency_ms": lat, "matched_guests": store.convidados_da_foto(ja)}
    pid = uuid.uuid4().hex[:12]
    logo = store.pega_logo(e["dono"]) if e.get("dono") else None
    look = store.pega_look(e["dono"]) if e.get("dono") else None
    treated, dims, pms, thumb = process_image(raw, e.get("marca") or "FÓTON", logo, look)
    faces = detect_embed(treated)
    store.salva_foto(pid, event, treated, faces, thumb, sha)
    matched = []
    for gid, gemb in store.convidados_de(event):
        g = _emb(gemb)
        if any(float(g @ f) >= THRESH for f in faces):
            store.salva_match(gid, pid); matched.append(gid)
    lat = int((time.time() - t0) * 1000)
    _marca_latencia(lat)
    log.info('{"stage":"ingest","photo_id":"%s","n_faces":%d,"proc_ms":%.0f,"latency_ms":%d,"status":"ok"}'
             % (pid, len(faces), pms, lat))
    return {"photo_id": pid, "n_faces": len(faces), "dims": dims, "duplicada": False,
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
    # Leitura nao cria (como /stats e /photos). Esta era a ultima da cadeia: o celular
    # de um convidado com a galeria aberta continuava pedindo /feed de um evento ja
    # apagado, o servidor RECRIAVA o evento como orfao, e o app da fotografa (ainda
    # aberto) adotava o orfao de volta para a conta dela. Resultado: evento apagado
    # reaparecia no painel, vazio e com nome generico. Foi visto acontecer.
    _ev(event, create=False)
    return {"guest_id": guest_id, "known": store.convidado_existe(event, guest_id),
            "photos": store.matches_de(guest_id)}

@app.get("/contatos")
def contatos(event: str, authorization: str = Header(None)):
    # Nome e telefone de convidado é dado pessoal: só a dona do evento vê.
    # Aberto, bastava o código do QR para baixar a lista inteira (LGPD Art. 46).
    _pode(event, authorization)
    return {"event": event, "contatos": store.contatos_de(event)}

@app.get("/img/{event}/{photo_id}.jpg")
def img(event: str, photo_id: str, t: str = ""):
    """`?t=1` devolve a MINIATURA. A grade mostra quadradinhos e baixava a foto de
    2048px inteira: 89 fotos eram ~35 MB e 89 decodificacoes so para desenhar
    miniatura (ADR-0022).

    Foto anterior a coluna existir nao tem miniatura: gera UMA vez, guarda, e das
    proximas vezes ja sai pronta. Espalha o custo em vez de exigir uma migracao que
    travaria o unico nucleo da VM."""
    if t:
        m = store.thumb_bytes(event, photo_id)
        if not m:
            cheia = store.foto_bytes(event, photo_id)
            if not cheia: raise HTTPException(404)
            try:
                m = _thumb(Image.open(io.BytesIO(cheia)).convert("RGB"))
                if m: store.guarda_thumb(event, photo_id, m)
            except Exception:
                m = None
            if not m: m = cheia          # nunca deixa a grade sem imagem
        return Response(m, media_type="image/jpeg",
                        headers={"Cache-Control": "public, max-age=86400"})
    b = store.foto_bytes(event, photo_id)
    if not b: raise HTTPException(404)
    return Response(b, media_type="image/jpeg", headers={"Cache-Control": "public, max-age=86400"})

@app.post("/photo/delete")
def photo_delete(event: str = Form(...), photo_id: str = Form(...), senha_admin: str = Form(""),
                 authorization: str = Header(None)):
    _exige_elevacao(_pode(event, authorization), senha_admin)
    store.apaga_foto(event, photo_id)
    log.info('{"stage":"photo","photo_id":"%s","status":"deleted"}' % photo_id)
    return {"ok": True}

# ============================ ADMIN ============================
# Logins com poder de admin. Vem do ambiente quando definido; o padrao existe para o
# dono nao ficar trancado fora do proprio painel. Nao ha segredo aqui — o login e
# publico, a senha nao. E o /signup agora recusa qualquer login desta lista, entao
# ninguem reivindica um admin que ainda nao tenha conta.
ADMINS = {e.strip().lower() for e in os.environ.get("FOTON_ADMINS", "admin").split(",")}

def _eh_admin(c):
    """Admin por VARIAVEL (raiz de confianca, nao rebaixavel pelo app) OU por COLUNA
    (promovido no painel por outro admin)."""
    if not c: return False
    return c["email"].lower() in ADMINS or bool(c.get("admin"))

def _admin(authorization):
    c = _dono(authorization)
    if not _eh_admin(c):
        raise HTTPException(403, "acesso restrito")
    return c

@app.post("/admin/promover")
def admin_promover(email: str = Form(...), ligado: str = Form(...), authorization: str = Header(None)):
    """Da ou tira o crachá de administrador. So admin promove admin.

    Quem esta em FOTON_ADMINS nao pode ser rebaixado aqui: e a raiz de confianca, e sem
    essa trava o ultimo admin conseguiria se remover e ninguem mais entraria no painel.

    Peso do que se esta dando: o admin le o NOME e o TELEFONE de convidados reais de
    TODOS os eventos, apaga contas e troca senhas. Nao e um cracha de visitante."""
    _admin(authorization)
    alvo = (email or "").strip().lower()
    if not store.conta(alvo):
        raise HTTPException(404, "conta não encontrada")
    lig = str(ligado) in ("1", "true", "True")
    if not lig and alvo in ADMINS:
        raise HTTPException(400, "esta conta é administradora pela configuração do servidor e não pode ser rebaixada aqui")
    store.marca_admin(alvo, lig)
    log.info('{"stage":"admin","acao":"promover","ligado":%s}' % ("true" if lig else "false"))
    return {"email": alvo, "admin": lig}

@app.get("/admin/resumo")
def admin_resumo(authorization: str = Header(None)):
    _admin(authorization)
    import shutil
    du = shutil.disk_usage("/")
    return {**store.resumo_geral(),
            "disco_livre_gb": round(du.free / 1e9, 1), "disco_total_gb": round(du.total / 1e9, 1),
            "credito": store.uso_de_credito(), "admins": sorted(ADMINS),
            # `admin` = cracha efetivo (variavel OU coluna); `admin_fixo` = veio da
            # configuracao do servidor, entao o painel nao oferece o botao de rebaixar.
            "fotografos_lista": [dict(f, admin=(f["email"].lower() in ADMINS or bool(f.get("admin"))),
                                      admin_fixo=(f["email"].lower() in ADMINS))
                                 for f in store.todos_fotografos()]}

@app.get("/admin/latencias")
def admin_latencias(authorization: str = Header(None)):
    """P50/P95/P99 do ingest desde o ultimo restart — o numero do SLA (CLAUDE.md §2).

    Janela em memoria (500 ultimas). Zera no restart de proposito: e um termometro de
    'como esta AGORA', nao um historico — historico medido vive em docs/BENCHMARKS.md.
    Duplicata nao entra na conta: ela nao processa, e entraria como latencia falsamente
    baixa, maquiando o P95.

    Cobre os DOIS caminhos: /ingest (celular) e ingerir_bytes (FTP da camera). Ficaram
    na mesma janela porque a pergunta do SLA e "a foto chega em quanto tempo", nao "por
    onde ela entrou"; separar por origem so vale a pena quando houver numero que mostre
    que os dois caminhos tem custos diferentes."""
    _admin(authorization)
    return {"amostras": len(_LATS),
            "p50_ms": _pct(_LATS, 50), "p95_ms": _pct(_LATS, 95), "p99_ms": _pct(_LATS, 99),
            "max_ms": max(_LATS) if _LATS else None,
            "alvo_ms": 10000, "escopo": "servidor (ingest->banco+match), NAO end-to-end"}

def _mascara_nome(n):
    """"Ana Carolina Souza" -> "Ana C. S." — da para reconhecer o formato, nao a pessoa."""
    ps = [p for p in str(n or "").split() if p]
    if not ps: return ""
    return " ".join([ps[0]] + [p[0].upper() + "." for p in ps[1:]])

def _mascara_contato(v):
    """Guarda os 2 ultimos digitos (suficiente para conferir "e este mesmo?" no suporte)."""
    v = str(v or "")
    if "@" in v:                                  # e-mail: a@b.com -> a***@b.com
        u, _, d = v.partition("@")
        return (u[:1] + "***@" + d) if u else ("***@" + d)
    dig = [ch for ch in v if ch.isdigit()]
    if not dig: return "•••"
    return "•" * max(0, len(dig) - 2) + "".join(dig[-2:])

@app.get("/admin/contatos")
def admin_contatos(revelar: str = "0", authorization: str = Header(None)):
    """Todo contato deixado por convidado, de todos os eventos.

    Dado pessoal (nome + telefone). Fica atras de _admin de proposito: o convidado
    entregou isso para a fotografa dele, nao para o publico. Nunca chega ao app do
    convidado, e nao entra em log (regra da secao 7 do CLAUDE.md).

    MASCARADO POR PADRAO (`?revelar=1` mostra por inteiro). O caso que motivou isto:
    dar admin a alguem para ele CONHECER o sistema — ver que guardamos nome e telefone
    e um requisito legitimo; ler o telefone da convidada de um casamento real nao e.
    Minimizacao de dado (LGPD): mostra-se o formato, nao o conteudo. Quem precisa do
    numero de verdade (suporte) pede explicitamente e isso fica no log."""
    c = _admin(authorization)
    revelar = str(revelar) in ("1", "true", "True")
    cs = store.contatos_todos()
    if revelar:
        log.info('{"stage":"admin","acao":"contatos_revelados","n":%d}' % len(cs))
        return {"contatos": cs, "mascarado": False}
    return {"contatos": [dict(x, nome=_mascara_nome(x.get("nome")),
                              contato=_mascara_contato(x.get("contato"))) for x in cs],
            "mascarado": True}

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

_LOGIN_OK = re.compile(r"^[a-z0-9][a-z0-9._%+-]{2,59}(@[a-z0-9.-]+\.[a-z]{2,})?$")

@app.post("/conta/credenciais")
def conta_credenciais(atual: str = Form(...), novo_login: str = Form(""), nova_senha: str = Form(""),
                      authorization: str = Header(None)):
    """A própria fotógrafa troca o login e/ou a senha.

    Existia um buraco: SÓ o admin trocava senha (`/admin/senha`). Se a senha dela
    vazasse — e vazou: esteve em texto puro num repo público — ela dependia do dono
    para se proteger. Agora não depende.

    Pede a senha ATUAL mesmo já tendo sessão: sessão roubada não deve conseguir
    trocar a senha e expulsar a dona da própria conta.
    """
    c = _dono(authorization)
    if not c: raise HTTPException(401, "sessão expirada")
    if not store.autentica(c["email"], atual): raise HTTPException(403, "senha atual incorreta")

    login = (novo_login or c["email"]).strip().lower()
    senha = nova_senha or atual
    if len(senha) < 6: raise HTTPException(400, "senha muito curta (mínimo 6)")

    if login != c["email"].strip().lower():
        if not _LOGIN_OK.match(login):
            raise HTTPException(400, "login inválido — use letras, números, ponto ou hífen (sem espaço)")
        # renomear-se para um login de admin seria virar admin sem senha de admin
        if login in ADMINS:
            raise HTTPException(403, "esse login é reservado")
        if store.conta(login):
            raise HTTPException(409, "já existe uma conta com esse login")
        if not store.renomeia_conta(c["email"], login):
            raise HTTPException(400, "não consegui trocar o login")
        log.info('{"stage":"conta","acao":"login_trocado"}')

    store.troca_senha(login, senha)          # já derruba TODAS as sessões
    log.info('{"stage":"conta","acao":"senha_trocada"}')
    d = store.conta(login)
    # a senha do FTP é derivada do login: trocou o login, trocou a senha da câmera
    return {"ok": True, "email": login, "token": store.novo_token(login),
            "nome": d["nome"], "marca": d["marca"],
            "credits": d["credits"], "credits_total": d["credits_total"],
            "ftp_mudou": login != c["email"].strip().lower()}

@app.post("/admin/conta/excluir")
def admin_conta_excluir(email: str = Form(...), authorization: str = Header(None)):
    """Limpeza de suporte: apagar conta de teste sem precisar da senha dela."""
    a = _admin(authorization)
    alvo = email.strip().lower()
    if alvo == a["email"].lower(): raise HTTPException(400, "não dá para apagar a própria conta de admin")
    if not store.apaga_conta(alvo): raise HTTPException(404, "fotógrafo não encontrado")
    log.info('{"stage":"admin","acao":"conta_excluida","alvo":"%s"}' % alvo)
    return {"ok": True}

@app.post("/admin/compactar")
def admin_compactar(authorization: str = Header(None)):
    """Devolve ao disco o espaco das linhas apagadas.

    O SQLite NAO encolhe sozinho: apagar evento marca o espaco como livre dentro do
    arquivo, e o arquivo continua do mesmo tamanho. Como as fotos moram no banco e o
    backup guarda 7 copias dele, cada MB nao recuperado custa 8 MB de disco."""
    _admin(authorization)
    antes = store.tamanho_no_disco()
    depois = store.compacta()
    log.info('{"stage":"admin","acao":"compactar","liberou_mb":%.1f}' % ((antes - depois) / 1e6))
    return {"ok": True, "antes_mb": round(antes / 1e6, 1), "depois_mb": round(depois / 1e6, 1),
            "liberou_mb": round((antes - depois) / 1e6, 1)}

@app.post("/admin/zerar")
def admin_zerar(confirmacao: str = Form(...), authorization: str = Header(None)):
    """Apaga TODO o conteudo e mantem as contas. Irreversivel pelo app.

    Exige a palavra ZERAR digitada: e a unica rota que destroi dado de cliente de uma
    vez so, e um toque errado num celular nao pode disparar isso. A rede de seguranca
    real e o backup diario (7 copias) — conferir /admin/saude ANTES de usar."""
    _admin(authorization)
    if (confirmacao or "").strip().upper() != "ZERAR":
        raise HTTPException(400, "digite ZERAR para confirmar")
    r = store.zerar_dados()
    log.info('{"stage":"admin","acao":"zerar","fotos":%d,"convidados":%d}' % (r["photo"], r["guest"]))
    return {"ok": True, **{k: v for k, v in r.items() if not k.startswith("bytes")},
            "antes_mb": round(r["bytes_antes"] / 1e6, 1), "depois_mb": round(r["bytes_depois"] / 1e6, 1)}

@app.post("/admin/empresa")
def admin_empresa(email: str = Form(...), ligado: str = Form("1"), authorization: str = Header(None)):
    """Marca a conta como de EMPRESA (album interno, login compartilhado)."""
    _admin(authorization)
    alvo = email.strip().lower()
    if not store.conta(alvo): raise HTTPException(404, "conta não encontrada")
    lig = str(ligado).strip() not in ("0", "", "false", "False")
    store.define_empresa(alvo, lig)
    log.info('{"stage":"admin","acao":"empresa","ligado":%s}' % ("true" if lig else "false"))
    return {"ok": True, "email": alvo, "empresa": lig}

@app.post("/admin/retencao")
def admin_retencao(email: str = Form(...), dias: str = Form(""), authorization: str = Header(None)):
    """Retencao de biometria por conta. dias=0 -> NAO expira; vazio -> politica geral.

    Existe por um caso real: album permanente (GLAMON) onde as MESMAS pessoas voltam
    toda semana. Com os 7 dias globais elas refariam a selfie a cada semana.
    Isto AFROUXA uma protecao de dado sensivel — por isso e do admin, e por isso o
    painel mostra em quais contas esta ligado."""
    _admin(authorization)
    alvo = email.strip().lower()
    if not store.conta(alvo): raise HTTPException(404, "conta não encontrada")
    d = None if dias.strip() == "" else int(dias)
    if d is not None and (d < 0 or d > 3650): raise HTTPException(400, "dias fora do intervalo")
    store.define_retencao_bio(alvo, d)
    log.info('{"stage":"admin","acao":"retencao_bio","dias":"%s"}' % dias)
    return {"ok": True, "email": alvo, "ret_bio_dias": d}

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
    treated, dims, pms, thumb = process_image(raw)
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

# ==================== COMPARTILHAR (Web Share Target) ====================
# Com o app instalado, o Fóton aparece no menu "Compartilhar" do Android e o
# sistema faz POST /compartilhar com as fotos. Esse POST é atendido pelo SERVICE
# WORKER (app/web/sw.js) e normalmente não chega aqui.
#
# Chega aqui quando o service worker não está no ar (foi desregistrado, dados do
# site limpos, primeira abertura ainda sem controlar a página). Sem esta rota o
# servidor devolvia 405 e a fotógrafa via uma tela de erro crua — as fotos se
# perdiam sem explicação. Aqui não dá para ingerir: o POST do Android não carrega
# o token da conta (ele mora no localStorage do navegador) e aceitar arquivo sem
# dono abriria uma rota de upload anônima. Então a resposta honesta é: explicar,
# reinstalar o service worker e mandar para o caminho que funciona.
_PAGINA_COMPARTILHAR = """<!doctype html><html lang="pt-BR"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Fóton — compartilhar</title>
<style>body{margin:0;background:#0b0a0d;color:#f4f2f7;font:16px/1.55 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;
display:flex;align-items:center;justify-content:center;min-height:100vh;padding:24px}
.c{max-width:420px}h1{font-size:22px;margin:0 0 12px}p{color:#b9b4c4;margin:0 0 14px}
a{display:block;text-align:center;background:#7c5cff;color:#fff;text-decoration:none;
padding:14px;border-radius:12px;font-weight:600;margin-top:20px}</style>
<div class="c"><h1>Não consegui receber as fotos por aqui</h1>
<p>O Fóton precisa estar aberto pelo menos uma vez neste celular para receber fotos
pelo menu <b>Compartilhar</b>. Acabei de reativar isso — da próxima vez funciona.</p>
<p>Agora, para não perder essas fotos: abra o evento e toque em
<b>Enviar foto da câmera</b>.</p>
<a href="/">Abrir o Fóton</a></div>
<script>if('serviceWorker' in navigator)navigator.serviceWorker.register('/sw.js').catch(function(){});</script>
"""

@app.get("/compartilhar")
@app.post("/compartilhar")
def compartilhar_sem_sw():
    # sem parâmetro de corpo declarado: o multipart é ignorado, não carregamos as fotos na RAM
    return Response(_PAGINA_COMPARTILHAR, media_type="text/html; charset=utf-8",
                    headers={"Cache-Control": "no-store"})

@app.get("/qr")
def qr(data: str):
    img = qrcode.make(data)
    buf = io.BytesIO(); img.save(buf, "PNG")
    return Response(buf.getvalue(), media_type="image/png", headers={"Cache-Control": "public, max-age=3600"})

# front-end (uma URL faz tudo). Rotas de API acima têm precedência.
app.mount("/", StaticFiles(directory=os.path.join(BASE, "app", "web"), html=True), name="web")
