"""Fóton — recebe fotos DIRETO da câmera (FTP/FTPS).

A Canon R8 (e a maioria das profissionais) tem cliente FTP embutido: a cada disparo
ela envia a foto sozinha. Isso elimina o passo manual "câmera → celular → escolher →
enviar" — a fotógrafa só fotografa.

Como funciona: cada fotógrafo tem um usuário FTP e uma pasta. Quando um arquivo
termina de chegar, ele entra no MESMO pipeline do upload pelo app (watermark,
reconhecimento, match) e cai no evento que estiver AO VIVO daquele fotógrafo.
"""
import os, time, threading, logging, secrets
from pyftpdlib.authorizers import DummyAuthorizer, AuthenticationFailed
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer

import store

log = logging.getLogger("foton.ftp")
RAIZ = os.environ.get("FOTON_FTP_DIR", "/var/lib/foton/ftp")
PORTA = int(os.environ.get("FOTON_FTP_PORT", "2121"))
JANELA_H = float(os.environ.get("FOTON_FTP_JANELA_HORAS", "6"))   # foto pendente entra no evento se for desta janela
DESCARTE_H = float(os.environ.get("FOTON_FTP_DESCARTE_HORAS", "24"))  # mais velha que isso: some (a foto segue no cartão)
_ingerir = None          # injetado pelo rig (evita import circular)
_drenando = threading.Lock()


def _pasta_do(email):
    p = os.path.join(RAIZ, email.replace("@", "_at_").replace("/", "_"))
    os.makedirs(p, exist_ok=True)
    return p


def _pendentes_do(email):
    """Fotos que chegaram ANTES de existir evento ao vivo. Ficam aqui esperando —
    antes elas eram deixadas na pasta e nunca mais processadas (foto perdida em
    silêncio, justo no ensaio em que a fotógrafa testa a câmera)."""
    p = os.path.join(RAIZ, "_pendentes", email.replace("@", "_at_").replace("/", "_"))
    os.makedirs(p, exist_ok=True)
    return p


def drenar(email):
    """Manda para o evento ao vivo o que ficou pendente. Chamado quando chega foto
    nova e quando a fotógrafa abre um evento. Roda numa thread para não travar o
    FTP (o servidor é de laço único: ingerir 20 fotos aqui pararia de receber)."""
    def _trabalho():
        if not _drenando.acquire(blocking=False):
            return                                    # já tem um drenando; não empilha
        try:
            pasta = _pendentes_do(email)
            agora = time.time()
            for nome in sorted(os.listdir(pasta)):
                caminho = os.path.join(pasta, nome)
                try:
                    idade_h = (agora - os.path.getmtime(caminho)) / 3600
                    if idade_h > DESCARTE_H:
                        os.remove(caminho)
                        log.info('{"stage":"ftp","status":"pendente_descartada","idade_h":%.1f}' % idade_h)
                        continue
                    if idade_h > JANELA_H:
                        continue                      # velha demais para este evento; espera o descarte
                    code = _evento_ao_vivo(email)
                    if not code:
                        return                        # ainda não há evento: fica pendente
                    with open(caminho, "rb") as f:
                        raw = f.read()
                    pid, n = _ingerir(code, raw)
                    os.remove(caminho)
                    log.info('{"stage":"ftp","status":"pendente_entregue","photo_id":"%s","event":"%s","n_faces":%d}'
                             % (pid, code, n))
                except Exception as e:
                    log.info('{"stage":"ftp","status":"pendente_erro","err":"%s"}' % str(e)[:120])
        finally:
            _drenando.release()
    threading.Thread(target=_trabalho, daemon=True).start()


def _evento_ao_vivo(email):
    """A foto vai para o evento que o fotógrafo tem AO VIVO agora."""
    for e in store.eventos_de(email):
        if e.get("status") == "live":
            return e["code"]
    return None


class _Handler(FTPHandler):
    def on_file_received(self, arquivo):
        """Chamado quando a câmera termina de enviar um arquivo."""
        try:
            email = self.username
            if not arquivo.lower().endswith((".jpg", ".jpeg")):
                os.remove(arquivo); return
            code = _evento_ao_vivo(email)
            if not code:
                # Sem evento ao vivo a foto vai para a fila de pendentes e entra
                # assim que a fotógrafa abrir o evento. Antes ela sumia.
                destino = os.path.join(_pendentes_do(email), "%d_%s" % (time.time() * 1000, os.path.basename(arquivo)))
                os.replace(arquivo, destino)
                log.info('{"stage":"ftp","status":"pendente_guardada","user":"%s"}' % email)
                return
            with open(arquivo, "rb") as f:
                raw = f.read()
            pid, n = _ingerir(code, raw)
            os.remove(arquivo)                           # já está no banco
            log.info('{"stage":"ftp","photo_id":"%s","event":"%s","n_faces":%d}' % (pid, code, n))
            drenar(email)                                # leva junto o que ficou para trás
        except Exception as e:
            log.info('{"stage":"ftp","status":"erro","err":"%s"}' % str(e)[:120])

    def on_incomplete_file_received(self, arquivo):
        try: os.remove(arquivo)                          # envio cortado: descarta
        except Exception: pass


def senha_ftp(email):
    """Senha do FTP derivada da conta — a fotógrafa não precisa decorar outra.

    A semente é um segredo do servidor, gerado sozinho na primeira vez e guardado no
    banco. Antes o padrão era a string "foton-ftp", que está no repositório PÚBLICO:
    quem soubesse o e-mail da fotógrafa calculava a senha da câmera dela e despejava
    foto no evento ao vivo. A senha aparece no painel dela, não precisa decorar.
    """
    import hashlib
    seg = os.environ.get("FOTON_FTP_SEED") or store.segredo("ftp_seed")
    return hashlib.sha256((seg + email).encode()).hexdigest()[:12]


class _Auth(DummyAuthorizer):
    """Confere o login contra o banco NA HORA.

    Antes, os usuários eram cadastrados uma única vez no boot: quem criasse conta
    depois não conseguia conectar a câmera até alguém reiniciar o serviço — e a
    fotógrafa não teria como saber disso no meio do evento.
    """
    def validate_authentication(self, username, password, handler):
        c = store.conta((username or "").strip().lower())
        if not c or not secrets.compare_digest(senha_ftp(c["email"]), password or ""):
            raise AuthenticationFailed("usuario ou senha do FTP incorretos")

    def get_home_dir(self, username):
        return _pasta_do((username or "").strip().lower())

    def has_user(self, username):
        return store.conta((username or "").strip().lower()) is not None

    def has_perm(self, username, perm, path=None):
        return perm in "elw"                             # entrar, listar, escrever

    def get_perms(self, username):
        return "elw"

    def get_msg_login(self, username):
        return "Foton pronto"

    def get_msg_quit(self, username):
        return "ate logo"


def iniciar(ingerir):
    """Sobe o servidor FTP numa thread. `ingerir(code, bytes) -> (photo_id, n_faces)`."""
    global _ingerir
    _ingerir = ingerir
    os.makedirs(RAIZ, exist_ok=True)

    h = _Handler
    h.authorizer = _Auth()
    h.banner = "Foton FTP"
    h.passive_ports = range(30000, 30021)                # faixa fixa (firewall)
    srv = FTPServer(("0.0.0.0", PORTA), h)
    srv.max_cons = 32

    def _run():
        log.info('{"stage":"ftp","status":"ouvindo","porta":%d}' % PORTA)
        srv.serve_forever()
    threading.Thread(target=_run, daemon=True).start()
    return srv
