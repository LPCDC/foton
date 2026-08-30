"""Teste de contrato: quem pode mexer no evento — e o caminho feliz continuar inteiro.

Roda o servidor DE VERDADE (FastAPI + SQLite real, em arquivo temporário). Só o motor
facial é dublado, porque ele não muda nada nas regras testadas aqui e pesa 300 MB.

Motivo de existir: o código do evento fica no QR projetado na parede da festa. Antes
disto, qualquer convidado com o código apagava o evento, encerrava a festa, injetava
foto na galeria dos outros e baixava a lista de contatos.

    python tests/test_autorizacao.py
"""
import io, os, sys, tempfile, time, types

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
# apagado e apagado: antes o /photos RECRIAVA o evento e devolvia lista vazia
checa("sumiu mesmo",  C.get("/photos?event=FESTA1").status_code, 404)

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
# o admin NAO nasce por /signup (ver [16]): a conta tem que pre-existir no banco
rig.store.cria_conta("chefe@t.com", "senha123", "Chefe")
chefe = C.post("/login", data={"email": "chefe@t.com", "senha": "senha123"}).json()["token"]
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
checa("as fotos dela sumiram", C.get("/photos?event=DELE1").status_code, 404)
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

print("")
print("[15] Painel do admin: numeros por conta e contatos — e o portao continua fechado")
r = C.get("/admin/resumo", headers=h(chefe))
checa("admin ve o resumo", r.status_code, 200)
_j = r.json()
checa("tem leitura de credito", sorted(_j["credito"].keys()),
      ["creditos_dados", "creditos_livres", "eventos_criados", "eventos_orfaos", "eventos_vazios"])
_umа = _j["fotografos_lista"][0]
checa("cada conta traz os numeros que decidem credito",
      all(k in _umа for k in ("fotos", "convidados", "contatos", "bytes", "ao_vivo", "ultima_foto")), True)
# a lista tem que mostrar ate conta que nunca criou evento (subconsulta, nao JOIN)
C.post("/signup", data={"email": "vazia@t.com", "senha": "senha123"})
checa("conta sem evento nenhum aparece na lista",
      any(f["email"] == "vazia@t.com" for f in C.get("/admin/resumo", headers=h(chefe)).json()["fotografos_lista"]), True)

# contatos sao nome + telefone de convidado: SO admin
checa("admin le os contatos", C.get("/admin/contatos", headers=h(chefe)).status_code, 200)
checa("fotografa comum NAO le os contatos de todos", C.get("/admin/contatos", headers=h(dona)).status_code, 403)
checa("anonimo NAO le", C.get("/admin/contatos").status_code, 403)
# o evento que tinha contato foi apagado la em [6]; cria um agora para ter o que ler
C.post("/event", data={"code": "CONT1", "name": "Festa com contato"}, headers=h(dona))
C.post("/selfie", data={"event": "CONT1", "consent": "true", "nome": "Bia", "contato": "13 98888-0000"},
       files={"file": ("s.jpg", jpeg(), "image/jpeg")})
_cs = C.get("/admin/contatos", headers=h(chefe)).json()["contatos"]
checa("traz o contato com o evento e o dono",
      all(k in (_cs[0] if _cs else {}) for k in ("nome", "contato", "evento", "dono", "ts")), True)


print("")
print("[16] Cadastro NAO pode reivindicar um login de admin")
checa("signup com login de admin JA existente", C.post("/signup", data={"email": "chefe@t.com", "senha": "outra123"}).status_code, 403)
checa("signup com login de admin SEM conta", C.post("/signup", data={"email": "reservado@t.com", "senha": "outra123"}).status_code, 403)
checa("e a conta reservada continua sem existir", rig.store.conta("reservado@t.com"), None)
checa("cadastro normal continua funcionando", C.post("/signup", data={"email": "gente@t.com", "senha": "senha123"}).status_code, 200)
checa("conta nova nasce com 100 creditos", C.post("/login", data={"email": "gente@t.com", "senha": "senha123"}).json()["credits"], 100)

print("")
print("[17] Retencao de biometria por conta (album permanente)")
checa("so admin muda retencao", C.post("/admin/retencao", data={"email": "dona@t.com", "dias": "0"}, headers=h(dona)).status_code, 403)
checa("anonimo nao muda", C.post("/admin/retencao", data={"email": "dona@t.com", "dias": "0"}).status_code, 403)
checa("conta inexistente", C.post("/admin/retencao", data={"email": "nao@existe", "dias": "0"}, headers=h(chefe)).status_code, 404)
checa("admin desliga a expiracao", C.post("/admin/retencao", data={"email": "dona@t.com", "dias": "0"}, headers=h(chefe)).json()["ret_bio_dias"], 0)
import numpy as _np
C.post("/event", data={"code": "PERM1"}, headers=h(dona))
C.post("/event", data={"code": "TEMP1"}, headers=h(outra))
rig.store.salva_convidado("gperm", "PERM1", _np.zeros(512, _np.float32))
rig.store.salva_convidado("gtemp", "TEMP1", _np.zeros(512, _np.float32))
rig.store.q("UPDATE guest SET criado=? WHERE id IN (?,?)", (time.time() - 40 * 86400, "gperm", "gtemp"))
rig.store.expirar(7, 90)
_vivos = [r["id"] for r in rig.store.q("SELECT id FROM guest", (), "all")]
checa("biometria da conta isenta SOBREVIVEU", "gperm" in _vivos, True)
checa("biometria da conta normal expirou", "gtemp" in _vivos, False)
checa("admin volta ao padrao", C.post("/admin/retencao", data={"email": "dona@t.com", "dias": ""}, headers=h(chefe)).json()["ret_bio_dias"], None)


print("")
print("[18] Zerar dados e compactar — sem levar as contas junto")
checa("so admin zera", C.post("/admin/zerar", data={"confirmacao": "ZERAR"}, headers=h(dona)).status_code, 403)
checa("anonimo nao zera", C.post("/admin/zerar", data={"confirmacao": "ZERAR"}).status_code, 403)
checa("sem a palavra certa nao zera", C.post("/admin/zerar", data={"confirmacao": "sim"}, headers=h(chefe)).status_code, 400)
# guarda o que NAO pode sumir
_antes = {f["email"]: (f["credits"], f["credits_total"]) for f in C.get("/admin/resumo", headers=h(chefe)).json()["fotografos_lista"]}
_png = io.BytesIO(); Image.new("RGBA", (30, 30), (0, 255, 0, 255)).save(_png, "PNG")
C.post("/conta/logo", files={"file": ("l.png", _png.getvalue(), "image/png")}, headers=h(dona))
C.post("/admin/retencao", data={"email": "dona@t.com", "dias": "0"}, headers=h(chefe))
_r = C.post("/admin/zerar", data={"confirmacao": "zerar"}, headers=h(chefe))
checa("admin zera (aceita minusculo)", _r.status_code, 200)
_z = C.get("/admin/resumo", headers=h(chefe)).json()
checa("nao sobrou foto", _z["fotos"], 0)
checa("nao sobrou convidado", _z["convidados"], 0)
checa("nao sobrou contato", _z["contatos"], 0)
checa("nao sobrou evento", _z["eventos"], 0)
# o que TEM que sobreviver
_dep = {f["email"]: (f["credits"], f["credits_total"]) for f in _z["fotografos_lista"]}
checa("todas as contas continuam existindo", sorted(_dep), sorted(_antes))
checa("creditos intactos", _dep, _antes)
checa("a senha continua valendo", C.post("/login", data={"email": "dona@t.com", "senha": "senha123"}).status_code, 200)
checa("a marca d'agua PNG sobreviveu", C.get("/me", headers=h(dona)).json()["tem_logo"], True)
checa("a retencao por conta sobreviveu",
      [f["ret_bio_dias"] for f in _z["fotografos_lista"] if f["email"] == "dona@t.com"], [0])
# e o app continua servindo depois de zerar
C.post("/event", data={"code": "DEPOIS1"}, headers=h(dona))
_n = C.post("/ingest", data={"event": "DEPOIS1"}, files={"file": ("f.jpg", jpeg(), "image/jpeg")}, headers=h(dona))
checa("da para usar normalmente depois de zerar", _n.status_code, 200)
checa("compactar e so do admin", C.post("/admin/compactar", headers=h(dona)).status_code, 403)
checa("admin compacta", C.post("/admin/compactar", headers=h(chefe)).status_code, 200)


print("")
print("[19] Leitura NAO cria evento (fabrica de orfaos fechada)")
_orf_antes = len(C.get("/admin/orfaos", headers=h(chefe)).json()["orfaos"])
checa("/stats com codigo inexistente -> 404", C.get("/stats?event=NAOEXISTE").status_code, 404)
checa("/photos com codigo inexistente -> 404", C.get("/photos?event=NAOEXISTE").status_code, 404)
checa("/feed com codigo inexistente -> 404", C.get("/feed?event=NAOEXISTE&guest_id=x").status_code, 404)
checa("e NAO nasceu evento nenhum", rig.store.evento("NAOEXISTE"), None)
checa("nenhum orfao novo", len(C.get("/admin/orfaos", headers=h(chefe)).json()["orfaos"]), _orf_antes)
# o caminho de verdade continua inteiro
C.post("/event", data={"code": "LEIT1"}, headers=h(dona))
checa("/stats de evento que existe", C.get("/stats?event=LEIT1").status_code, 200)
checa("/photos de evento que existe", C.get("/photos?event=LEIT1").status_code, 200)
C.post("/ingest", data={"event": "LEIT1"}, files={"file": ("f.jpg", jpeg(), "image/jpeg")}, headers=h(dona))
_s = C.post("/selfie", data={"event": "LEIT1", "consent": "true"}, files={"file": ("s.jpg", jpeg(), "image/jpeg")})
checa("convidado ainda se registra", _s.status_code, 200)
checa("e recebe a foto dele", len(_s.json()["matches"]), 1)
# a cadeia real que ressuscitou um evento apagado em producao:
# celular antigo pede /feed -> servidor recria como orfao -> app da fotografa adota de volta
_gid = _s.json()["guest_id"]
C.post("/event/delete", data={"code": "LEIT1"}, headers=h(dona))
checa("celular antigo pedindo /feed nao ressuscita o evento", C.get("/feed?event=LEIT1&guest_id=" + _gid).status_code, 404)
checa("e o evento continua apagado", rig.store.evento("LEIT1"), None)
C.post("/event/adotar", data={"codes": "LEIT1"}, headers=h(dona))
checa("adotar tambem nao faz nascer evento", rig.store.evento("LEIT1"), None)


print("")
print("[20] Tela do convidado e botoes de envio da fotografa")
_h = open(os.path.join(RAIZ, "app", "web", "index.html"), encoding="utf-8").read()
# a tela mandava escanear o QR e nao dava como escanear
checa("existe botao de escanear", _h.count(chr(39) + "btn-scan" + chr(39)) >= 1 or "id=\"btn-scan\"" in _h, True)
checa("existe o leitor sobreposto", "id=\"scanner\"" in _h, True)
checa("usa BarcodeDetector do navegador (sem lib nova)", "BarcodeDetector" in _h, True)
checa("degrada quando o aparelho nao le QR", "mostrarBotaoScan" in _h, True)
# camera do celular visivel, separada da galeria
checa("botao de abrir a camera", "Abrir câmera" in _h, True)
checa("e o de mandar da galeria", "Enviar foto do celular" in _h, True)
checa("abre a camera NATIVA (capture)", "capture=\"environment\"" in _h, True)
checa("botao separado para a galeria", "id=\"ev-galeria\"" in _h, True)
checa("mostra as formas sem tocar no app", "id=\"ev-semtoque\"" in _h, True)
# o Voltar nao pode sair do app com uma foto aberta na tela
checa("sobreposicao consome o Voltar", "fecharSobreposicao" in _h, True)
checa("o popstate checa a sobreposicao ANTES da tela",
      _h.index("if(fecharSobreposicao())") < _h.index("const t=telaAtiva(), f=VOLTAR_PARA[t];"), True)


print("")
print("[21] Credito DESLIGADO — nesta fase criar evento e de graca")
# Ate 2026-08-30 sair 1 credito por evento novo era o comportamento certo, e este
# teste guardava a regra "8 tentativas do mesmo evento = 1 credito" (bug real: o app
# repete o POST quando a rede esta ruim e o evento queimava 8). O dono cortou o
# credito: tudo gratis, com login. O teste agora guarda o OPOSTO — que nada e gasto —
# porque um contador que volta a descontar em silencio bloquearia a fotografa no meio
# de uma festa. As colunas continuam na base de proposito (historico + painel do admin).
_tk = C.post("/signup", data={"email": "cred@t.com", "senha": "senha123"}).json()["token"]
_c0 = C.get("/me", headers=h(_tk)).json()["credits"]
for _ in range(8): C.post("/event", data={"code": "REPET"}, headers=h(_tk))
C.post("/event", data={"code": "OUTRO1"}, headers=h(_tk))
checa("criar 2 eventos NAO gasta credito", _c0 - C.get("/me", headers=h(_tk)).json()["credits"], 0)
checa("e a criacao continua funcionando",
      C.post("/event", data={"code": "TERCE"}, headers=h(_tk)).status_code, 200)
checa("entrar na conta NAO gasta credito",
      C.post("/login", data={"email": "cred@t.com", "senha": "senha123"}).json()["credits"],
      C.get("/me", headers=h(_tk)).json()["credits"])
checa("o login diz se a conta e admin (o botao do painel depende disso)",
      C.post("/login", data={"email": "cred@t.com", "senha": "senha123"}).json().get("admin"), False)

print("")
print("[22] Conta de EMPRESA: ve e baixa tudo, mas nao cria nem apaga sem senha de admin")
_et = C.post("/signup", data={"email": "salao@t.com", "senha": "senha123"}).json()["token"]
checa("so admin marca conta como empresa", C.post("/admin/empresa", data={"email": "salao@t.com"}, headers=h(dona)).status_code, 403)
checa("admin marca", C.post("/admin/empresa", data={"email": "salao@t.com", "ligado": "1"}, headers=h(chefe)).json()["empresa"], True)
checa("o app fica sabendo pelo /me", C.get("/me", headers=h(_et)).json()["empresa"], True)
checa("e sabe que NAO e admin", C.get("/me", headers=h(_et)).json()["admin"], False)
# a trava vive no SERVIDOR: esconder o botao na tela nao segura ninguem
checa("criar album SEM senha de admin", C.post("/event", data={"code": "ALB1"}, headers=h(_et)).status_code, 403)
checa("criar com senha ERRADA", C.post("/event", data={"code": "ALB1", "senha_admin": "chutei"}, headers=h(_et)).status_code, 403)
checa("criar com a senha do admin", C.post("/event", data={"code": "ALB1", "senha_admin": "senha123"}, headers=h(_et)).status_code, 200)
checa("apagar album SEM senha", C.post("/event/delete", data={"code": "ALB1"}, headers=h(_et)).status_code, 403)
checa("apagar foto SEM senha", C.post("/photo/delete", data={"event": "ALB1", "photo_id": "x"}, headers=h(_et)).status_code, 403)
# o que a EQUIPE pode: ver, e receber foto normalmente
checa("equipe ve os albuns", C.get("/events", headers=h(_et)).status_code, 200)
checa("equipe manda foto para o album", C.post("/ingest", data={"event": "ALB1"},
      files={"file": ("f.jpg", jpeg(), "image/jpeg")}, headers=h(_et)).status_code, 200)
checa("apagar com a senha do admin funciona", C.post("/event/delete", data={"code": "ALB1", "senha_admin": "senha123"}, headers=h(_et)).status_code, 200)
# conta comum nao e afetada por nada disso
checa("conta comum cria sem senha nenhuma", C.post("/event", data={"code": "NORM1"}, headers=h(dona)).status_code, 200)
checa("conta comum apaga sem senha nenhuma", C.post("/event/delete", data={"code": "NORM1"}, headers=h(dona)).status_code, 200)


print("")
print("[23] Miniatura como COLUNA (ADR-0022)")
_mt = C.post("/signup", data={"email": "mini@t.com", "senha": "senha123"}).json()["token"]
C.post("/event", data={"code": "MINI1"}, headers=h(_mt))
_pid = C.post("/ingest", data={"event": "MINI1"}, files={"file": ("f.jpg", jpeg(), "image/jpeg")},
                headers=h(_mt)).json()["photo_id"]
_cheia = C.get("/img/MINI1/" + _pid + ".jpg")
_mini  = C.get("/img/MINI1/" + _pid + ".jpg?t=1")
checa("a foto inteira continua servida", _cheia.status_code, 200)
checa("a miniatura tem rota propria", _mini.status_code, 200)
checa("miniatura e MENOR que a foto", len(_mini.content) < len(_cheia.content), True)
checa("as duas sao imagem", _mini.headers["content-type"], "image/jpeg")
# foto ANTERIOR a coluna existir: gera uma vez e guarda, sem migracao que trave a VM
rig.store.q("UPDATE photo SET thumb=NULL WHERE id=?", (_pid,))
checa("foto antiga nasce sem miniatura", rig.store.thumb_bytes("MINI1", _pid), None)
checa("pedir a miniatura funciona mesmo assim", C.get("/img/MINI1/" + _pid + ".jpg?t=1").status_code, 200)
checa("e ela fica guardada para a proxima", rig.store.thumb_bytes("MINI1", _pid) is not None, True)
checa("foto que nao existe continua 404", C.get("/img/MINI1/naoexiste.jpg?t=1").status_code, 404)
# a grade do app tem que pedir a miniatura, nao a foto inteira
_h2 = open(os.path.join(RAIZ, "app", "web", "index.html"), encoding="utf-8").read()
checa("a grade usa mini()", _h2.count(chr(36) + "{mini(p.src)}"), 2)

print("[24] DIREITO DE EXCLUSAO da convidada (LGPD Art. 18) — nao tinha teste nenhum")
# Esta rota e a condicao no.3 da decisao registrada em docs/PRODUTO.md §3b-2: e ela que
# sustenta o argumento "quem registrou foi o dono do evento; reclame com ele". Se quebrar
# num refactor, o alicerce juridico daquela decisao cai junto, em silencio. Por isso existe
# este teste — a rota mais importante para conformidade era a menos protegida do sistema.
_ld = "lgpd@t.com"
rig.store.cria_conta(_ld, "senha123", "Dona LGPD")
_lt = C.post("/login", data={"email": _ld, "senha": "senha123"}).json()["token"]
C.post("/ingest", data={"event": "LGPD1"}, files={"file": ("f.jpg", jpeg(), "image/jpeg")}, headers=h(_lt))
_s = C.post("/selfie", data={"event": "LGPD1", "consent": "true", "nome": "Bia", "contato": "11988"},
            files={"file": ("s.jpg", jpeg(), "image/jpeg")})
_gid = _s.json()["guest_id"]
checa("a convidada existe antes de sair", rig.store.convidado_existe("LGPD1", _gid), True)
checa("e ela aparece nos contatos da dona",
      len(C.get("/contatos?event=LGPD1", headers=h(_lt)).json()["contatos"]), 1)
# a saida NAO pode exigir login: a convidada nao tem conta nenhuma
_x = C.post("/convidado/excluir", data={"event": "LGPD1", "guest_id": _gid})
checa("sair NAO exige login (a convidada nao tem conta)", _x.status_code, 200)
checa("o servidor confirma que removeu", _x.json().get("removido"), True)
checa("a BIOMETRIA dela sumiu de verdade", rig.store.convidado_existe("LGPD1", _gid), False)
checa("o feed dela morre junto", C.get(f"/feed?event=LGPD1&guest_id={_gid}").json().get("photos", []), [])
# apagar de novo nao pode explodir — a convidada pode tocar duas vezes no botao
checa("apagar duas vezes nao quebra",
      C.post("/convidado/excluir", data={"event": "LGPD1", "guest_id": _gid}).status_code, 200)
# guest_id de outro evento nao pode apagar dado deste
checa("id inexistente nao acha nada",
      C.post("/convidado/excluir", data={"event": "LGPD1", "guest_id": "naoexiste"}).json().get("removido"), False)
# a EXPIRACAO automatica precisa continuar funcionando (a outra metade da retencao)
checa("expirar roda e devolve contagem", set(rig.store.expirar(7, 90).keys()) >= {"convidados", "fotos"}, True)
# o botao de saida tem que estar VISIVEL na galeria dela, nao escondido numa tela de ajuda
_h3 = open(os.path.join(RAIZ, "app", "web", "index.html"), encoding="utf-8").read()
checa("o app chama a rota de exclusao", "/convidado/excluir" in _h3, True)

print("")
print("[25] PERFIL de conta (ADR-0030): o servidor declara, o cliente obedece")
# O perfil e APRESENTACAO (vocabulario, blocos visiveis, tokens de cor) — nunca poder.
# Poder continua nos testes [22] (empresa/_exige_elevacao) e de admin. Aqui se guarda o
# contrato: conta comum e 'pro'; virou empresa, o perfil acompanha nos TRES lugares em
# que o app pode ficar sabendo (/signup, /login e /me — regra da ADR-0025).
_pj = C.post("/signup", data={"email": "perfil@t.com", "senha": "senha123"}).json()
checa("conta nova nasce 'pro' ja no /signup", _pj.get("perfil"), "pro")
checa("e o /signup tambem diz que nao e empresa", _pj.get("empresa"), False)
_pl = C.post("/login", data={"email": "perfil@t.com", "senha": "senha123"}).json()
checa("o /login informa o perfil", _pl.get("perfil"), "pro")
checa("o /me informa o perfil", C.get("/me", headers=h(_pl["token"])).json().get("perfil"), "pro")
C.post("/admin/empresa", data={"email": "perfil@t.com", "ligado": "1"}, headers=h(chefe))
checa("marcada como empresa, o perfil acompanha no /me",
      C.get("/me", headers=h(_pl["token"])).json().get("perfil"), "empresa")
checa("e no /login tambem",
      C.post("/login", data={"email": "perfil@t.com", "senha": "senha123"}).json().get("perfil"), "empresa")
C.post("/admin/empresa", data={"email": "perfil@t.com", "ligado": "0"}, headers=h(chefe))
checa("desligada, volta a 'pro'",
      C.get("/me", headers=h(_pl["token"])).json().get("perfil"), "pro")

print("\n[26] Confiabilidade: idempotencia de ingestao, health do pipeline e latencia")
# Cenario real: a camera reenvia por retentativa, ou o celular com internet ruim manda o
# lote de novo. Antes, a MESMA foto virava duas linhas, dois processamentos e duas copias
# na galeria do convidado. O convidado via a mesma foto duplicada.
C.post("/event", data={"code": "IDEM1", "brand": "DONA"}, headers=h(dona))
_foto = jpeg()
_r1 = C.post("/ingest", data={"event": "IDEM1"}, files={"file": ("a.jpg", _foto, "image/jpeg")}, headers=h(dona)).json()
_r2 = C.post("/ingest", data={"event": "IDEM1"}, files={"file": ("a.jpg", _foto, "image/jpeg")}, headers=h(dona)).json()
checa("foto reenviada devolve a MESMA entrega", _r2["photo_id"], _r1["photo_id"])
checa("e se declara duplicada", _r2.get("duplicada"), True)
checa("a primeira NAO e duplicada", _r1.get("duplicada"), False)
checa("o evento continua com UMA foto", len(C.get("/photos?event=IDEM1").json()["photos"]), 1)
# foto DIFERENTE no mesmo evento continua entrando (o dedupe nao pode comer foto nova)
b = io.BytesIO(); Image.new("RGB", (200, 200), (10, 200, 30)).save(b, "JPEG")
_r3 = C.post("/ingest", data={"event": "IDEM1"}, files={"file": ("b.jpg", b.getvalue(), "image/jpeg")}, headers=h(dona)).json()
checa("foto diferente entra normalmente", _r3.get("duplicada"), False)
checa("agora o evento tem duas fotos", len(C.get("/photos?event=IDEM1").json()["photos"]), 2)
# a MESMA foto em OUTRO evento e outra entrega (marca/dono diferentes), nao duplicata
C.post("/event", data={"code": "IDEM2", "brand": "DONA"}, headers=h(dona))
_r4 = C.post("/ingest", data={"event": "IDEM2"}, files={"file": ("a.jpg", _foto, "image/jpeg")}, headers=h(dona)).json()
checa("mesma foto em OUTRO evento nao e duplicata", _r4.get("duplicada"), False)
checa("e o outro evento tem a sua propria copia", len(C.get("/photos?event=IDEM2").json()["photos"]), 1)
# a duplicata devolve os mesmos convidados da entrega original (cliente nao ve diferenca)
_sf = C.post("/selfie", data={"event": "IDEM1", "consent": "true"},
             files={"file": ("s.jpg", jpeg(), "image/jpeg")}).json()
_r5 = C.post("/ingest", data={"event": "IDEM1"}, files={"file": ("a.jpg", _foto, "image/jpeg")}, headers=h(dona)).json()
checa("duplicata devolve os convidados ja entregues", _sf["guest_id"] in _r5["matched_guests"], True)

# A PERGUNTA QUE DECIDE O DEDUPE: o convidado que chega DEPOIS ainda casa com a foto?
# Se pular o reprocessamento deixasse o convidado atrasado sem a foto, a idempotencia
# seria uma troca ruim (economiza CPU, perde entrega). Nao deixa: a duplicata nao cria
# foto nova, mas os ROSTOS da original continuam no indice, e a selfie faz backfill
# contra rostos_de(evento). Travado aqui para ninguem "otimizar" isso por engano.
C.post("/event", data={"code": "TARDE1", "brand": "DONA"}, headers=h(dona))
C.post("/ingest", data={"event": "TARDE1"}, files={"file": ("a.jpg", _foto, "image/jpeg")}, headers=h(dona))
_dup = C.post("/ingest", data={"event": "TARDE1"}, files={"file": ("a.jpg", _foto, "image/jpeg")}, headers=h(dona)).json()
checa("(cenario) a 2a foi mesmo tratada como duplicata", _dup.get("duplicada"), True)
_tardio = C.post("/selfie", data={"event": "TARDE1", "consent": "true"},
                 files={"file": ("s.jpg", jpeg(), "image/jpeg")}).json()
checa("convidado que chega DEPOIS casa com a foto deduplicada", len(_tardio["matches"]), 1)
_feed = C.get(f"/feed?event=TARDE1&guest_id={_tardio['guest_id']}").json()
checa("e a foto chega no feed dele", len(_feed["photos"]), 1)

# o caminho da CAMERA (FTP) usa ingerir_bytes, nao /ingest: dedupe vale la tambem
C.post("/event", data={"code": "FTP1", "brand": "DONA"}, headers=h(dona))
_p1, _n1 = rig.ingerir_bytes("FTP1", _foto)
_p2, _n2 = rig.ingerir_bytes("FTP1", _foto)     # retentativa da camera
checa("retentativa do FTP devolve a mesma foto", _p2, _p1)
checa("e nao duplica no evento", len(C.get("/photos?event=FTP1").json()["photos"]), 1)
checa("e devolve o mesmo n_faces", _n2, _n1)

# health deixou de ser tres constantes: bate no banco de verdade
_hj = C.get("/health").json()
checa("health confere o banco", _hj.get("db_ok"), True)
checa("health responde ok", _hj.get("ok"), True)
checa("health nao vaza numero de negocio", any(k in _hj for k in ("photos", "fotos", "contatos", "clientes")), False)

# latencia: numero do SLA atras de admin
checa("latencias: anonimo nao ve", C.get("/admin/latencias").status_code, 403)
checa("latencias nega fotografa comum", C.get("/admin/latencias", headers=h(dona)).status_code, 403)
_lj = C.get("/admin/latencias", headers=h(chefe)).json()
checa("admin ve amostras de latencia", _lj["amostras"] >= 1, True)
checa("e o alvo declarado do SLA", _lj["alvo_ms"], 10000)
# a duplicata nao processa: se entrasse na janela, entraria como ~0ms e maquiaria o P95
_antes = C.get("/admin/latencias", headers=h(chefe)).json()["amostras"]
C.post("/ingest", data={"event": "IDEM1"}, files={"file": ("a.jpg", _foto, "image/jpeg")}, headers=h(dona))
_depois = C.get("/admin/latencias", headers=h(chefe)).json()["amostras"]
checa("duplicata NAO entra na conta (nao maquia o P95)", _depois, _antes)

print("\n[27] ADMIN promovido pelo painel + contatos mascarados")
# Caso real: dar admin a alguem para ele conhecer o sistema. Antes so dava editando a
# variavel de ambiente da VM e reiniciando.
C.post("/signup", data={"email": "danilo@t.com", "senha": "senha123", "nome": "Danilo"})
_dn = C.post("/login", data={"email": "danilo@t.com", "senha": "senha123"}).json()
checa("conta nova NAO nasce admin", _dn.get("admin"), False)
checa("e nao entra no painel", C.get("/admin/resumo", headers=h(_dn["token"])).status_code, 403)
checa("fotografa comum NAO promove ninguem",
      C.post("/admin/promover", data={"email": "danilo@t.com", "ligado": "1"}, headers=h(dona)).status_code, 403)
checa("anonimo NAO promove", C.post("/admin/promover", data={"email": "danilo@t.com", "ligado": "1"}).status_code, 403)
checa("admin promove", C.post("/admin/promover", data={"email": "danilo@t.com", "ligado": "1"},
                              headers=h(chefe)).status_code, 200)
checa("promovido, ele ENTRA no painel", C.get("/admin/resumo", headers=h(_dn["token"])).status_code, 200)
checa("e o /me ja informa o cracha", C.get("/me", headers=h(_dn["token"])).json().get("admin"), True)
checa("promover conta inexistente da 404",
      C.post("/admin/promover", data={"email": "ninguem@t.com", "ligado": "1"}, headers=h(chefe)).status_code, 404)
# trava anti-lockout: quem e admin pela CONFIGURACAO do servidor nao cai pelo app
checa("admin da configuracao NAO pode ser rebaixado",
      C.post("/admin/promover", data={"email": "chefe@t.com", "ligado": "0"}, headers=h(chefe)).status_code, 400)
checa("e ele continua admin", C.get("/admin/resumo", headers=h(chefe)).status_code, 200)
C.post("/admin/promover", data={"email": "danilo@t.com", "ligado": "0"}, headers=h(chefe))
checa("rebaixado, perde o painel", C.get("/admin/resumo", headers=h(_dn["token"])).status_code, 403)

# contatos: mascarado por padrao (ver o FORMATO do dado nao exige ver a pessoa)
C.post("/event", data={"code": "MASC1", "brand": "DONA"}, headers=h(dona))
C.post("/selfie", data={"event": "MASC1", "consent": "true", "nome": "Ana Carolina Souza",
                        "contato": "13991234567"}, files={"file": ("s.jpg", jpeg(), "image/jpeg")})
_mc = C.get("/admin/contatos", headers=h(chefe)).json()
_a = [x for x in _mc["contatos"] if x["event_code"] == "MASC1"][0]
checa("vem marcado como mascarado", _mc.get("mascarado"), True)
checa("nome vira iniciais", _a["nome"], "Ana C. S.")
checa("telefone esconde tudo menos os 2 ultimos", _a["contato"].endswith("67") and "9123" not in _a["contato"], True)
_rv = C.get("/admin/contatos?revelar=1", headers=h(chefe)).json()
_b = [x for x in _rv["contatos"] if x["event_code"] == "MASC1"][0]
checa("revelar=1 mostra o numero real", _b["contato"], "13991234567")
checa("e se declara NAO mascarado", _rv.get("mascarado"), False)

print("\n" + ("TODOS OS TESTES PASSARAM" if not FALHAS else f"{len(FALHAS)} FALHA(S): {FALHAS}"))
sys.exit(1 if FALHAS else 0)
