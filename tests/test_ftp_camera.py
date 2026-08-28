"""Teste do FTP da câmera: foto que chega antes do evento NÃO pode sumir, e conta
criada depois do boot tem que conseguir logar na câmera.

Os dois furos que este teste tranca:
  1. sem evento ao vivo, o arquivo ficava parado na pasta e nunca era processado —
     perda silenciosa, justo no ensaio em que a fotógrafa testa a câmera;
  2. os usuários de FTP eram cadastrados uma vez no boot: quem criasse conta depois
     não conectava a câmera até alguém reiniciar o serviço.

    python tests/test_ftp_camera.py
"""
import os, sys, time, types, tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "app", "test_rig"))
TMP = tempfile.mkdtemp()
os.environ["FOTON_DB"] = os.path.join(TMP, "teste.db")
os.environ["FOTON_FTP_DIR"] = os.path.join(TMP, "ftp")

import store
import ftp_camera as F
from pyftpdlib.authorizers import AuthenticationFailed

FALHAS = []
def checa(nome, obtido, esperado):
    ok = obtido == esperado
    print(("  ok   " if ok else "  FALHA") + f" {nome}: {obtido!r} (esperado {esperado!r})")
    if not ok: FALHAS.append(nome)

# o pipeline real é caro (300 MB de modelo); aqui só interessa SE a foto foi entregue
entregues = []
F._ingerir = lambda code, raw: (entregues.append((code, len(raw))) or ("id%d" % len(entregues), 1))

def espera_drenar(seg=5):
    fim = time.time() + seg
    while time.time() < fim:
        if F._drenando.acquire(blocking=False):
            F._drenando.release()
            time.sleep(0.05)
            if not os.listdir(F._pendentes_do("p@t.com")): return
        time.sleep(0.05)

def chega_foto(email, nome, conteudo=b"JPEGFALSO"):
    """Simula o fim de um envio da câmera (mesmo caminho do pyftpdlib)."""
    caminho = os.path.join(F._pasta_do(email), nome)
    with open(caminho, "wb") as f: f.write(conteudo)
    F._Handler.on_file_received(types.SimpleNamespace(username=email), caminho)
    return caminho

store.cria_conta("p@t.com", "senha123", "Patricia")

print("\n[1] Foto ANTES de existir evento: fica pendente, não some")
c = chega_foto("p@t.com", "IMG_001.JPG")
checa("saiu da pasta de entrada", os.path.exists(c), False)
checa("está na fila de pendentes", len(os.listdir(F._pendentes_do("p@t.com"))), 1)
checa("nada foi entregue ainda", len(entregues), 0)

print("\n[2] Fotógrafa abre o evento -> a pendente entra sozinha")
store.cria_evento("FESTA1", dono="p@t.com", nome="Festa", auto=0)
F.drenar("p@t.com"); espera_drenar()
checa("foto entregue ao evento", [e[0] for e in entregues], ["FESTA1"])
checa("fila de pendentes vazia", len(os.listdir(F._pendentes_do("p@t.com"))), 0)

print("\n[3] Com evento ao vivo, a foto entra direto")
chega_foto("p@t.com", "IMG_002.JPG"); espera_drenar()
checa("duas fotos no evento", len(entregues), 2)

print("\n[4] Pendente velha demais é descartada (a foto segue no cartão da câmera)")
store.encerra_evento("FESTA1")                      # sem evento ao vivo de novo
velha = chega_foto("p@t.com", "IMG_ANTIGA.JPG")
pend = os.path.join(F._pendentes_do("p@t.com"), os.listdir(F._pendentes_do("p@t.com"))[0])
os.utime(pend, (time.time() - 40 * 3600, time.time() - 40 * 3600))   # 40 h atrás
store.cria_evento("FESTA2", dono="p@t.com", nome="Festa 2", auto=0)
F.drenar("p@t.com"); espera_drenar()
checa("velha não entrou no evento novo", len(entregues), 2)
checa("velha saiu do disco", len(os.listdir(F._pendentes_do("p@t.com"))), 0)

print("\n[5] Login da câmera é conferido no banco NA HORA (sem reiniciar o serviço)")
aut = F._Auth()
checa("conta existente é reconhecida", aut.has_user("p@t.com"), True)
checa("conta inexistente não é", aut.has_user("ninguem@t.com"), False)
try:
    aut.validate_authentication("p@t.com", F.senha_ftp("p@t.com"), None); ok = True
except AuthenticationFailed: ok = False
checa("senha certa entra", ok, True)
try:
    aut.validate_authentication("p@t.com", "errada", None); ok = True
except AuthenticationFailed: ok = False
checa("senha errada é barrada", ok, False)

store.cria_conta("nova@t.com", "senha123", "Nova")   # conta criada DEPOIS do boot
try:
    aut.validate_authentication("nova@t.com", F.senha_ftp("nova@t.com"), None); ok = True
except AuthenticationFailed: ok = False
checa("conta criada agora já conecta", ok, True)
checa("pasta dela é só dela", aut.get_home_dir("nova@t.com").endswith("nova_at_t.com"), True)

print("\n[6] Senha do FTP não pode ser calculável a partir do repositório público")
import hashlib
antiga = hashlib.sha256(("foton-ftp" + "p@t.com").encode()).hexdigest()[:12]
checa("não é mais a senha da semente publica", F.senha_ftp("p@t.com") == antiga, False)
checa("estável entre chamadas", F.senha_ftp("p@t.com"), F.senha_ftp("p@t.com"))
checa("semente sobrevive no banco", store.segredo("ftp_seed"), store.segredo("ftp_seed"))
checa("cada conta tem senha própria", F.senha_ftp("p@t.com") == F.senha_ftp("nova@t.com"), False)

print("\n[7] 'Câmera conectada' — a fotógrafa sabe SEM gastar uma foto de teste")
store.cria_conta("conecta@t.com", "senha123", "Conecta")
checa("antes de logar, nunca conectou", store.ftp_visto_ha_s("conecta@t.com"), None)
checa("via /camera/config (helper)", F.conectada_ha_s("conecta@t.com"), None)
aut = F._Auth()
try: aut.validate_authentication("conecta@t.com", "senha errada de proposito", None)
except AuthenticationFailed: pass
checa("senha ERRADA não marca como conectada", store.ftp_visto_ha_s("conecta@t.com"), None)
aut.validate_authentication("conecta@t.com", F.senha_ftp("conecta@t.com"), None)
ha_s = store.ftp_visto_ha_s("conecta@t.com")
checa("login CERTO marca como conectada agora", ha_s is not None and ha_s < 2, True)
checa("cada fotógrafo tem o próprio relógio", store.ftp_visto_ha_s("p@t.com") != ha_s, True)

print("\n" + ("TODOS OS TESTES PASSARAM" if not FALHAS else f"{len(FALHAS)} FALHA(S): {FALHAS}"))
sys.exit(1 if FALHAS else 0)
