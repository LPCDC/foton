"""Marca d'água em PNG: upload, redução, aplicação na foto (substitui o texto).

    python tests/test_logo.py
"""
import io, os, sys, tempfile, types

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "app", "test_rig"))
os.environ["FOTON_DB"] = os.path.join(tempfile.mkdtemp(), "teste.db")

import numpy as np

_EMB = np.zeros(512, np.float32); _EMB[0] = 1.0

class _FaceFalsa:
    normed_embedding = _EMB

cv2 = types.ModuleType("cv2")
cv2.IMREAD_COLOR = 1
cv2.imdecode = lambda arr, flag: np.zeros((10, 10, 3), np.uint8)
sys.modules["cv2"] = cv2

insightface = types.ModuleType("insightface")
app_mod = types.ModuleType("insightface.app")
class FaceAnalysis:
    def __init__(self, **kw): pass
    def prepare(self, **kw): pass
    def get(self, bgr): return [_FaceFalsa()]
app_mod.FaceAnalysis = FaceAnalysis
insightface.app = app_mod
sys.modules["insightface"] = insightface
sys.modules["insightface.app"] = app_mod

from PIL import Image
from fastapi.testclient import TestClient
import rig, store

C = TestClient(rig.app)

def foto_jpeg(cor=(90, 90, 90)):
    b = io.BytesIO(); Image.new("RGB", (600, 400), cor).save(b, "JPEG")
    return b.getvalue()

def png_com_transparencia():
    im = Image.new("RGBA", (300, 120), (0, 0, 0, 0))       # fundo TOTALMENTE transparente
    for x in range(80, 220):
        for y in range(40, 80):
            im.putpixel((x, y), (232, 217, 176, 255))       # bloco opaco no meio
    b = io.BytesIO(); im.save(b, "PNG")
    return b.getvalue()

def h(tok):
    return {"Authorization": "Bearer " + tok}

FALHAS = []
def checa(nome, obtido, esperado):
    ok = obtido == esperado
    print(("  ok   " if ok else "  FALHA") + f" {nome}: {obtido!r} (esperado {esperado!r})")
    if not ok: FALHAS.append(nome)

tok = C.post("/signup", data={"email": "logo@t.com", "senha": "senha123", "nome": "Logo"}).json()["token"]

print("\n[1] Antes de enviar: sem logo")
checa("me diz que nao tem logo", C.get("/me", headers=h(tok)).json()["tem_logo"], False)
checa("GET /conta/logo -> 404", C.get("/conta/logo", headers=h(tok)).status_code, 404)

print("\n[2] Rejeita arquivo que nao e PNG")
r = C.post("/conta/logo", files={"file": ("f.jpg", foto_jpeg(), "image/jpeg")}, headers=h(tok))
checa("JPEG disfarcado de logo -> 400", r.status_code, 400)

print("\n[3] Upload de PNG valido")
png = png_com_transparencia()
r = C.post("/conta/logo", files={"file": ("logo.png", png, "image/png")}, headers=h(tok))
checa("upload -> 200", r.status_code, 200)
checa("agora tem_logo=True", C.get("/me", headers=h(tok)).json()["tem_logo"], True)
r2 = C.get("/conta/logo", headers=h(tok))
checa("GET devolve PNG", r2.headers.get("content-type"), "image/png")
salvo = Image.open(io.BytesIO(r2.content))
checa("reduzido para <= 900px de lado", max(salvo.size) <= 900, True)
checa("transparencia preservada (modo RGBA)", salvo.mode, "RGBA")
canto = salvo.convert("RGBA").getpixel((5, 5))
checa("fundo do logo continua transparente", canto[3], 0)

print("\n[4] Outra conta nao ve nem apaga a logo da primeira")
outro = C.post("/signup", data={"email": "outro@t.com", "senha": "senha123"}).json()["token"]
checa("outra conta: sem logo propria", C.get("/conta/logo", headers=h(outro)).status_code, 404)

print("\n[5] A logo substitui o texto na foto do evento")
C.post("/event", data={"code": "COMLOGO", "brand": "Texto Que Nao Deveria Aparecer"}, headers=h(tok))
r = C.post("/ingest", data={"event": "COMLOGO"}, files={"file": ("f.jpg", foto_jpeg(), "image/jpeg")}, headers=h(tok))
checa("ingest com logo -> 200", r.status_code, 200)
foto_final = Image.open(io.BytesIO(store.foto_bytes("COMLOGO", r.json()["photo_id"])))
# geometria real de _aplica_logo: alvo_w=20% da largura, margem=2%; o bloco dourado
# ocupa x:80-220/y:40-80 dentro do PNG 300x120 original -> reescalado e posicionado
fw, fh = foto_final.size
s = round(fw * 0.20) / 300
lw, lh = round(300 * s), round(120 * s)
m = round(fw * 0.02)
lx, ly = fw - lw - m, fh - lh - m
alvo = (lx + round(150 * s), ly + round(60 * s))          # centro do bloco dourado
canto_foto = foto_final.convert("RGB").getpixel(alvo)
dourado = abs(canto_foto[0] - 232) < 40 and abs(canto_foto[1] - 217) < 40
checa("cor do logo aparece no canto da foto final", dourado, True)

print("\n[6] Remover logo: volta a usar texto")
checa("apagar -> 200", C.post("/conta/logo/apagar", headers=h(tok)).status_code, 200)
checa("tem_logo volta a False", C.get("/me", headers=h(tok)).json()["tem_logo"], False)
checa("GET volta a 404", C.get("/conta/logo", headers=h(tok)).status_code, 404)

print("\n[7] Logo corrompido nao derruba o pipeline (so nao marca)")
store.salva_logo("logo@t.com", b"isto nao e um PNG de verdade")
r = C.post("/ingest", data={"event": "COMLOGO"}, files={"file": ("f2.jpg", foto_jpeg(), "image/jpeg")}, headers=h(tok))
checa("mesmo com logo quebrado, ingest -> 200", r.status_code, 200)

print("\n" + ("TODOS OS TESTES PASSARAM" if not FALHAS else f"{len(FALHAS)} FALHA(S): {FALHAS}"))
sys.exit(1 if FALHAS else 0)
