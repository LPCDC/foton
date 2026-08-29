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
os.environ["FOTON_ADMINS"] = "chefe@t.com,reservado@t.com"   # o 2o NAO tem conta: testa escalada

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

print("\n[7] Freio do login (força bruta) — sem travar quem erra a senha de vez em quando")
for i in range(9):
    C.post("/login", data={"email": "dona@t.com", "senha": "errada"})
checa("9 erros ainda deixam entrar", C.post("/login", data={"email": "dona@t.com", "senha": "senha123"}).status_code, 200)
for i in range(10):
    C.post("/login", data={"email": "dona@t.com", "senha": "errada"})
checa("10 erros seguidos -> freia", C.post("/login", data={"email": "dona@t.com", "senha": "senha123"}).status_code, 429)
rig._tentativas.clear()
checa("passada a janela, volta a entrar", C.post("/login", data={"email": "dona@t.com", "senha": "senha123"}).status_code, 200)

print("\n[8] Torre de controle do admin")
checa("fotógrafa comum não vê a saúde", C.get("/admin/saude", headers=h(dona)).status_code, 403)
checa("anônimo não vê", C.get("/admin/saude").status_code, 403)
chefe = C.post("/signup", data={"email": "chefe@t.com", "senha": "senha123"}).json()["token"]
r = C.get("/admin/saude", headers=h(chefe))
checa("admin vê", r.status_code, 200)
s = r.json()
checa("tem as seções que importam", sorted(s.keys()),
      ["alertas", "backup", "disco", "fila", "negocio", "servidor"])
checa("uptime do processo é número", isinstance(s["servidor"]["uptime_processo_h"], float), True)
checa("fila de fotos do FTP responde", isinstance(s["fila"]["fotos_ftp_aguardando"], (int, type(None))), True)
checa("sem backup vira alerta", "SEM BACKUP" in s["alertas"], True)

print("\n[9] A faixa do evento responde 'está chegando?'")
C.post("/event", data={"code": "FESTA9", "brand": "D"}, headers=h(dona))
st = C.get("/stats?event=FESTA9", headers=h(dona)).json()
checa("sem foto ainda -> tempo nulo", st["ultima_foto_s"], None)
checa("dona vê a fila do FTP", "aguardando" in st, True)
C.post("/ingest", data={"event": "FESTA9"}, files={"file": ("f.jpg", jpeg(), "image/jpeg")}, headers=h(dona))
checa("depois da foto, o tempo é pequeno", C.get("/stats?event=FESTA9", headers=h(dona)).json()["ultima_foto_s"] < 5, True)
checa("anônimo NÃO vê a fila", "aguardando" in C.get("/stats?event=FESTA9").json(), False)
checa("outra conta NÃO vê a fila", "aguardando" in C.get("/stats?event=FESTA9", headers=h(outra)).json(), False)
checa("convidado ainda lê o /stats", C.get("/stats?event=FESTA9").status_code, 200)

print("\n[10] Encerrar conta — leva os dados junto, e ninguém encerra a conta de outro")
alvo = C.post("/signup", data={"email": "sai@t.com", "senha": "senha123"}).json()["token"]
C.post("/event", data={"code": "DELE1"}, headers=h(alvo))
C.post("/ingest", data={"event": "DELE1"}, files={"file": ("f.jpg", jpeg(), "image/jpeg")}, headers=h(alvo))
checa("senha errada não encerra", C.post("/conta/excluir", data={"senha": "chutei"}, headers=h(alvo)).status_code, 403)
checa("anônimo não encerra", C.post("/conta/excluir", data={"senha": "senha123"}).status_code, 401)
checa("fotógrafa comum não usa a rota de admin",
      C.post("/admin/conta/excluir", data={"email": "sai@t.com"}, headers=h(dona)).status_code, 403)
checa("o titular encerra", C.post("/conta/excluir", data={"senha": "senha123"}, headers=h(alvo)).status_code, 200)
checa("a conta sumiu", rig.store.conta("sai@t.com"), None)
checa("as fotos dela sumiram", C.get("/photos?event=DELE1").json()["photos"], [])
checa("a sessão morreu junto", C.get("/me", headers=h(alvo)).status_code, 401)
checa("admin não apaga a si mesmo",
      C.post("/admin/conta/excluir", data={"email": "chefe@t.com"}, headers=h(chefe)).status_code, 400)

print("\n[11] Compartilhar (Web Share Target) — o caminho da foto pelo menu do Android")
import json as _json
_WEB = os.path.join(RAIZ, "app", "web")
_mani = _json.load(open(os.path.join(_WEB, "manifest.webmanifest"), encoding="utf-8"))
_st = _mani.get("share_target", {})
checa("o manifest declara share_target", bool(_st), True)
checa("o Android manda por POST", _st.get("method"), "POST")
checa("multipart (é o único enctype que carrega arquivo)", _st.get("enctype"), "multipart/form-data")
_arq = (_st.get("params") or {}).get("files") or [{}]
checa("o campo dos arquivos se chama 'fotos' (o sw.js lê esse nome)", _arq[0].get("name"), "fotos")
checa("aceita imagem", "image/*" in (_arq[0].get("accept") or []), True)
# a action tem que cair dentro do scope, senão o Chrome ignora o share_target inteiro
_acao = _st.get("action", "")
checa("a action fica dentro do scope", _acao.lstrip("./").startswith("compartilhar"), True)

_sw = open(os.path.join(_WEB, "sw.js"), encoding="utf-8").read()
checa("o service worker atende o POST do compartilhamento", "'POST'" in _sw and "compartilhar" in _sw, True)
checa("responde com 303 (POST vira GET na página)", "303" in _sw, True)
checa("o cache do lote NÃO é apagado no activate", "k !== CACHE_SHARE" in _sw, True)
_idx = open(os.path.join(_WEB, "index.html"), encoding="utf-8").read()
checa("a página lê o lote e o consome", "receberDoCompartilhamento" in _idx, True)
checa("o caminho antigo continua existindo", "onchange=\"uploadPhoto(event)\"" in _idx, True)

# degrade sem service worker: o POST cai no servidor e não pode virar 405 na cara dela
_antes = len(C.get("/photos?event=FESTA9").json()["photos"])
r = C.post("/compartilhar", files={"fotos": ("f.jpg", jpeg(), "image/jpeg")}, data={"event": "FESTA9"})
checa("sem service worker, o POST responde página (não 405)", r.status_code, 200)
checa("é HTML legível", r.headers["content-type"].startswith("text/html"), True)
checa("explica o que fazer", "Enviar foto da câmera" in r.text, True)
checa("reinstala o service worker", "serviceWorker" in r.text, True)
checa("abrir /compartilhar no navegador não quebra", C.get("/compartilhar").status_code, 200)
# a rota é anônima de propósito (o Android não manda token) — então ela NÃO pode publicar foto
checa("a rota NÃO virou upload anônimo: nada entrou no evento",
      len(C.get("/photos?event=FESTA9").json()["photos"]), _antes)

print("")
print("[12] Trocar o proprio login e a propria senha - sem depender do admin")
tk = C.post("/signup", data={"email": "muda@t.com", "senha": "senha123", "nome": "Muda"}).json()["token"]
C.post("/event", data={"code": "MUD1", "name": "Festa da Muda"}, headers=h(tk))
C.post("/ingest", data={"event": "MUD1"}, files={"file": ("f.jpg", jpeg(), "image/jpeg")}, headers=h(tk))

checa("anonimo nao troca credencial", C.post("/conta/credenciais", data={"atual": "senha123"}).status_code, 401)
checa("senha atual errada nao passa",
      C.post("/conta/credenciais", data={"atual": "chutei", "nova_senha": "novasenha"}, headers=h(tk)).status_code, 403)
checa("senha nova curta demais",
      C.post("/conta/credenciais", data={"atual": "senha123", "nova_senha": "123"}, headers=h(tk)).status_code, 400)
checa("login com espaco nao passa",
      C.post("/conta/credenciais", data={"atual": "senha123", "novo_login": "no me"}, headers=h(tk)).status_code, 400)
checa("login curto demais nao passa",
      C.post("/conta/credenciais", data={"atual": "senha123", "novo_login": "ab"}, headers=h(tk)).status_code, 400)
checa("login ja usado por outra conta",
      C.post("/conta/credenciais", data={"atual": "senha123", "novo_login": "dona@t.com"}, headers=h(tk)).status_code, 409)
checa("NAO da para virar admin renomeando a conta",
      C.post("/conta/credenciais", data={"atual": "senha123", "novo_login": "reservado@t.com"}, headers=h(tk)).status_code, 403)
checa("e continua sem ser admin", C.get("/admin/saude", headers=h(tk)).status_code, 403)

r = C.post("/conta/credenciais", data={"atual": "senha123", "novo_login": "MudaNova", "nova_senha": "outrasenha"}, headers=h(tk))
checa("troca login + senha de uma vez", r.status_code, 200)
j = r.json()
checa("login virou minusculo", j["email"], "mudanova")
checa("avisa que a senha do FTP mudou junto", j["ftp_mudou"], True)
checa("o login velho nao entra mais", C.post("/login", data={"email": "muda@t.com", "senha": "outrasenha"}).status_code, 401)
checa("a senha velha nao entra mais", C.post("/login", data={"email": "mudanova", "senha": "senha123"}).status_code, 401)
checa("o login NOVO entra", C.post("/login", data={"email": "mudanova", "senha": "outrasenha"}).status_code, 200)
checa("a sessao antiga caiu", C.get("/me", headers=h(tk)).status_code, 401)
novo = j["token"]
checa("o token devolvido ja vale", C.get("/me", headers=h(novo)).status_code, 200)
evs = C.get("/events", headers=h(novo)).json()["events"]
checa("o evento veio junto com o login novo", [e["code"] for e in evs], ["MUD1"])
checa("a foto continua no evento", len(C.get("/photos?event=MUD1").json()["photos"]), 1)
checa("e ela ainda manda no evento", C.post("/event/close", data={"code": "MUD1"}, headers=h(novo)).status_code, 200)
checa("a conta velha sumiu de vez", rig.store.conta("muda@t.com"), None)
# a marca d'agua em PNG e coluna de photographer: nao pode sumir na renomeacao
_png = io.BytesIO(); Image.new("RGBA", (40, 40), (255, 0, 0, 255)).save(_png, "PNG")
tk2 = C.post("/signup", data={"email": "comlogo@t.com", "senha": "senha123"}).json()["token"]
C.post("/conta/logo", files={"file": ("l.png", _png.getvalue(), "image/png")}, headers=h(tk2))
checa("tem logo antes de renomear", C.get("/me", headers=h(tk2)).json()["tem_logo"], True)
r3 = C.post("/conta/credenciais", data={"atual": "senha123", "novo_login": "semarroba"}, headers=h(tk2))
checa("renomeou", r3.status_code, 200)
checa("o logo sobreviveu a renomeacao", C.get("/me", headers=h(r3.json()["token"])).json()["tem_logo"], True)
checa("e o PNG ainda e servido", C.get("/conta/logo", headers=h(r3.json()["token"])).status_code, 200)

r2 = C.post("/conta/credenciais", data={"atual": "outrasenha", "nova_senha": "terceira1"}, headers=h(novo))
checa("troca so a senha", r2.status_code, 200)
checa("e o login fica igual", r2.json()["email"], "mudanova")
checa("nao avisa FTP a toa", r2.json()["ftp_mudou"], False)
checa("entra com a senha nova", C.post("/login", data={"email": "mudanova", "senha": "terceira1"}).status_code, 200)

print("")
print("[13] Instalar o app: e o que destrava o menu Compartilhar - nao pode ficar atras do login")
_idx2 = open(os.path.join(RAIZ, "app", "web", "index.html"), encoding="utf-8").read()
checa("tem tela propria de instalar", _idx2.count('id="s-instalar"'), 1)
checa("o link aparece NA TELA DE LOGIN", "abrirInstalar('login')" in _idx2, True)
checa("e continua no painel", "abrirInstalar('dash')" in _idx2, True)
checa("explica que e isso que liga o Compartilhar", 'aparece no menu' in _idx2, True)
checa("ensina o caminho manual quando o navegador nao oferece", "Adicionar a Tela de Inicio" in _idx2 or "Adicionar à Tela de Início" in _idx2, True)
# regressao de CSS: `.tips b` pegava tambem o <b> aninhado e jogava frase inteira em caixa alta
checa("o titulo de .tips so pega o filho direto", ".tips > b{" in _idx2, True)
checa("e a versao que quebrava o texto sumiu", (chr(10) + ".tips b{") in _idx2, False)

print("")
print("[14] Botao Voltar do celular: nao pode SAIR DO APP de qualquer tela")
_i = _idx2
checa("existe mapa de para-onde-voltar", "VOLTAR_PARA" in _i, True)
checa("o popstate e tratado", "addEventListener('popstate'" in _i, True)
checa("a sentinela do historico e armada no boot", "armarVoltar();" in _i, True)
checa("tela raiz avisa antes de sair", "voltar de novo para sair" in _i, True)
# um Voltar sem querer NAO pode encerrar o evento dela
checa("voltar do evento nao chama stopEvent", "'event':       ()=>{ clearInterval(state.liveTimer); go('dash'); }" in _i, True)
# a acao mais repetida da festa tem que vir ANTES do QR no HTML (acima da dobra)
checa("enviar fotos vem antes do QR", _i.find('id="ev-shoot"') < _i.find('class="ticket"'), True)
checa("o seletor de arquivo veio junto", _i.find('id="live-upload"') < _i.find('class="ticket"'), True)
checa("rotulo nao exclui quem usa o celular", "da câmera':'Simular" in _i, False)
checa("a landing fala com quem usa o celular", "Com câmera ou com o celular mesmo" in _i, True)

print("\n" + ("TODOS OS TESTES PASSARAM" if not FALHAS else f"{len(FALHAS)} FALHA(S): {FALHAS}"))
sys.exit(1 if FALHAS else 0)
