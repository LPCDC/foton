"""Fóton — recebe fotos DIRETO da câmera (FTP/FTPS).

A Canon R8 (e a maioria das profissionais) tem cliente FTP embutido: a cada disparo
ela envia a foto sozinha. Isso elimina o passo manual "câmera → celular → escolher →
enviar" — a fotógrafa só fotografa.

Como funciona: cada fotógrafo tem um usuário FTP e uma pasta. Quando um arquivo
termina de chegar, ele entra no MESMO pipeline do upload pelo app (watermark,
reconhecimento, match) e cai no evento que estiver AO VIVO daquele fotógrafo.
"""
import os, time, threading, logging
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer

import store

log = logging.getLogger("foton.ftp")
RAIZ = os.environ.get("FOTON_FTP_DIR", "/var/lib/foton/ftp")
PORTA = int(os.environ.get("FOTON_FTP_PORT", "2121"))
_ingerir = None          # injetado pelo rig (evita import circular)


def _pasta_do(email):
    p = os.path.join(RAIZ, email.replace("@", "_at_").replace("/", "_"))
    os.makedirs(p, exist_ok=True)
    return p


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
                log.info('{"stage":"ftp","status":"sem_evento_ao_vivo","user":"%s"}' % email)
                return                                   # guarda o arquivo para depois
            with open(arquivo, "rb") as f:
                raw = f.read()
            pid, n = _ingerir(code, raw)
            os.remove(arquivo)                           # já está no banco
            log.info('{"stage":"ftp","photo_id":"%s","event":"%s","n_faces":%d}' % (pid, code, n))
        except Exception as e:
            log.info('{"stage":"ftp","status":"erro","err":"%s"}' % str(e)[:120])

    def on_incomplete_file_received(self, arquivo):
        try: os.remove(arquivo)                          # envio cortado: descarta
        except Exception: pass


def senha_ftp(email):
    """Senha do FTP derivada da conta — a fotógrafa não precisa decorar outra."""
    import hashlib
    seg = os.environ.get("FOTON_FTP_SEED", "foton-ftp")
    return hashlib.sha256((seg + email).encode()).hexdigest()[:12]


def iniciar(ingerir):
    """Sobe o servidor FTP numa thread. `ingerir(code, bytes) -> (photo_id, n_faces)`."""
    global _ingerir
    _ingerir = ingerir
    os.makedirs(RAIZ, exist_ok=True)

    aut = DummyAuthorizer()
    for f in store.todos_fotografos():                   # um usuário por fotógrafo
        aut.add_user(f["email"], senha_ftp(f["email"]), _pasta_do(f["email"]), perm="elw")

    h = _Handler
    h.authorizer = aut
    h.banner = "Foton FTP"
    h.passive_ports = range(30000, 30021)                # faixa fixa (firewall)
    srv = FTPServer(("0.0.0.0", PORTA), h)
    srv.max_cons = 32

    def _run():
        log.info('{"stage":"ftp","status":"ouvindo","porta":%d}' % PORTA)
        srv.serve_forever()
    threading.Thread(target=_run, daemon=True).start()
    return srv
