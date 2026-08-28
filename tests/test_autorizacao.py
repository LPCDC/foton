"""Teste de contrato: quem pode mexer no evento — e o caminho feliz continuar inteiro.

Roda o servidor DE VERDADE (FastAPI + SQLite real, em arquivo temporário). Só o motor
facial é dublado, porque ele não muda nada nas regras testadas aqui e pesa 300 MB.

Motivo de existir: o código do evento fica no QR projetado na parede da festa. Antes
disto, qualquer convidado com o código apagava o evento, encerrava a festa, injetava
foto na galeria dos outros e baixava a lista de contatos.

    python tests/test_autorizacao.py
"""
import io, os, sys, tempfile, types

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "app", "test_rig"))
os.environ["FOTON_DB"] = os.path.join(tempfile.mkdtemp(), "teste.db")

# ---- dublês: cv2 e insightface (o resto do pipeline é o real) ----
import numpy as np

_EMB = np.zeros(512, np.float32); _EMB[0] = 1.0          # vetor fixo: selfie casa com a foto

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
import rig

C = TestClient(rig.app)

def jpeg():
    b = io.BytesIO(); Image.new("RGB", (200, 200), (90, 90, 90)).save(b, "JPEG")
    return b.getvalue()

def h(tok):
    return {"Authorization": "Bearer " + tok}

FALHAS = []
def checa(nome, obtido, esperado):
    ok = obtido == esperado
    print(("  ok   " if ok else "  FALHA") + f" {nome}: {obtido} (esperado {esperado})")
    if not ok: FALHAS.append(nome)

# ---------------- cenário ----------------
dona = C.post("/signup", data={"email": "dona@t.com", "senha": "senha123", "nome": "Dona"}).json()["token"]
outra = C.post("/signup", data={"email": "outra@t.com", "senha": "senha123", "nome": "Outra"}).json()["token"]
C.post("/event", data={"code": "FESTA1", "brand": "DONA"}, headers=h(dona))

print("\n[1] Portão: anônimo com o código do QR não faz nada destrutivo")
checa("delete anônimo",  C.post("/event/delete", data={"code": "FESTA1"}).status_code, 401)
checa("close anônimo",   C.post("/event/close",  data={"code": "FESTA1"}).status_code, 401)
checa("ingest anônimo",  C.post("/ingest", data={"event": "FESTA1"}, files={"file": ("f.jpg", jpeg(), "image/jpeg")}).status_code, 401)
checa("contatos anônimo", C.get("/contatos?event=FESTA1").status_code, 401)
checa("photo/delete anônimo", C.post("/photo/delete", data={"event": "FESTA1", "photo_id": "x"}).status_code, 401)

print("\n[2] Portão: outra fotógrafa logada não mexe em evento alheio")
checa("delete de outra",   C.post("/event/delete", data={"code": "FESTA1"}, headers=h(outra)).status_code, 403)
checa("close de outra",    C.post("/event/close",  data={"code": "FESTA1"}, headers=h(outra)).status_code, 403)
checa("ingest de outra",   C.post("/ingest", data={"event": "FESTA1"}, files={"file": ("f.jpg", jpeg(), "image/jpeg")}, headers=h(outra)).status_code, 403)
checa("contatos de outra", C.get("/contatos?event=FESTA1", headers=h(outra)).status_code, 403)

print("\n[3] Caminho feliz da fotógrafa (não pode ter quebrado)")
r = C.post("/ingest", data={"event": "FESTA1"}, files={"file": ("f.jpg", jpeg(), "image/jpeg")}, headers=h(dona))
checa("dona envia foto", r.status_code, 200)
pid = r.json().get("photo_id", "")
checa("rosto detectado", r.json().get("n_faces"), 1)
checa("evento aparece no painel dela", len(C.get("/events", headers=h(dona)).json()["events"]), 1)

print("\n[4] Caminho do convidado — continua aberto (ele não tem conta)")
s = C.post("/selfie", data={"event": "FESTA1", "consent": "true", "nome": "Ana", "contato": "11999"},
           files={"file": ("s.jpg", jpeg(), "image/jpeg")})
checa("selfie sem login", s.status_code, 200)
gid = s.json().get("guest_id", "")
checa("selfie casou com a foto", len(s.json().get("matches", [])), 1)
checa("feed do convidado", C.get(f"/feed?event=FESTA1&guest_id={gid}").status_code, 200)
checa("galeria 'todas'", C.get("/photos?event=FESTA1").status_code, 200)
checa("baixar a foto", C.get(f"/img/FESTA1/{pid}.jpg").status_code, 200)

print("\n[5] Dona vê os contatos; e evento criado pelo ingest nasce COM DONO")
checa("contatos da dona", len(C.get("/contatos?event=FESTA1", headers=h(dona)).json()["contatos"]), 1)
C.post("/ingest", data={"event": "NOVO9"}, files={"file": ("f.jpg", jpeg(), "image/jpeg")}, headers=h(dona))
checa("evento novo tem dono", rig.store.evento("NOVO9")["dono"], "dona@t.com")

print("\n[6] Dona encerra e apaga o próprio evento")
checa("dona encerra", C.post("/event/close",  data={"code": "FESTA1"}, headers=h(dona)).status_code, 200)
checa("dona apaga",   C.post("/event/delete", data={"code": "FESTA1"}, headers=h(dona)).status_code, 200)
checa("sumiu mesmo",  C.get("/photos?event=FESTA1").json()["photos"], [])

print("\n" + ("TODOS OS TESTES PASSARAM" if not FALHAS else f"{len(FALHAS)} FALHA(S): {FALHAS}"))
sys.exit(1 if FALHAS else 0)
