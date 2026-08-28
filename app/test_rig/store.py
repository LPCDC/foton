"""Fóton — persistência real (SQLite).

Substitui o dicionário em memória: eventos, fotos, convidados e contas passam a
sobreviver a reload da página, logout/login e restart do processo.

LIMITE HONESTO: no plano free da Render o disco é efêmero — um *deploy* novo zera o
arquivo. Para persistência total (Fase 1) basta apontar DATABASE_URL para um Postgres
(Supabase); o resto do app não muda, só este módulo.
"""
import os, json, sqlite3, hashlib, secrets, time, threading

DB_PATH = os.environ.get("FOTON_DB", os.path.join(os.path.dirname(os.path.abspath(__file__)), "foton.db"))
_lock = threading.Lock()
_conn = None

SCHEMA = """
CREATE TABLE IF NOT EXISTS photographer(
  email TEXT PRIMARY KEY, senha TEXT NOT NULL, nome TEXT, marca TEXT DEFAULT '',
  credits INTEGER DEFAULT 20, credits_total INTEGER DEFAULT 20, criado REAL);
CREATE TABLE IF NOT EXISTS event(
  code TEXT PRIMARY KEY, dono TEXT, nome TEXT, data TEXT, marca TEXT DEFAULT 'FÓTON',
  status TEXT DEFAULT 'live', auto INTEGER DEFAULT 0, criado REAL);
CREATE TABLE IF NOT EXISTS photo(
  id TEXT PRIMARY KEY, event_code TEXT, bytes BLOB, n_faces INTEGER, criado REAL);
CREATE TABLE IF NOT EXISTS face(
  photo_id TEXT, event_code TEXT, emb BLOB);
CREATE TABLE IF NOT EXISTS guest(
  id TEXT PRIMARY KEY, event_code TEXT, emb BLOB, criado REAL);
CREATE TABLE IF NOT EXISTS match(
  guest_id TEXT, photo_id TEXT, PRIMARY KEY(guest_id, photo_id));
CREATE TABLE IF NOT EXISTS contact(
  event_code TEXT, guest_id TEXT, nome TEXT, contato TEXT, ts REAL);
CREATE TABLE IF NOT EXISTS session(
  token TEXT PRIMARY KEY, email TEXT, criado REAL);
CREATE TABLE IF NOT EXISTS config(
  chave TEXT PRIMARY KEY, valor TEXT);
CREATE INDEX IF NOT EXISTS ix_photo_ev ON photo(event_code);
CREATE INDEX IF NOT EXISTS ix_face_ev ON face(event_code);
CREATE INDEX IF NOT EXISTS ix_guest_ev ON guest(event_code);
CREATE INDEX IF NOT EXISTS ix_event_dono ON event(dono);
"""

def conn():
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _conn.execute("PRAGMA journal_mode=WAL")
        _conn.executescript(SCHEMA)
        _conn.commit()
    return _conn

def q(sql, args=(), fetch=None):
    with _lock:
        c = conn().execute(sql, args)
        if fetch == "one":  r = c.fetchone()
        elif fetch == "all": r = c.fetchall()
        else: r = None; conn().commit()
        return r

# ---------------- contas ----------------
def hash_senha(senha, salt=None):
    salt = salt or secrets.token_hex(8)
    h = hashlib.pbkdf2_hmac("sha256", senha.encode(), salt.encode(), 120_000).hex()
    return f"{salt}${h}"

def confere_senha(senha, guardado):
    try:
        salt, _ = guardado.split("$", 1)
        return secrets.compare_digest(hash_senha(senha, salt), guardado)
    except Exception:
        return False

def cria_conta(email, senha, nome="", marca=""):
    email = email.strip().lower()
    if q("SELECT 1 FROM photographer WHERE email=?", (email,), "one"):
        return None
    q("INSERT INTO photographer(email,senha,nome,marca,credits,credits_total,criado) VALUES(?,?,?,?,?,?,?)",
      (email, hash_senha(senha), nome.strip()[:60], marca.strip()[:40], 20, 20, time.time()))
    return email

def autentica(email, senha):
    r = q("SELECT * FROM photographer WHERE email=?", (email.strip().lower(),), "one")
    if not r or not confere_senha(senha, r["senha"]): return None
    return dict(r)

def novo_token(email):
    t = secrets.token_urlsafe(24)
    q("INSERT INTO session(token,email,criado) VALUES(?,?,?)", (t, email, time.time()))
    return t

def por_token(token):
    r = q("""SELECT p.* FROM session s JOIN photographer p ON p.email=s.email
             WHERE s.token=?""", (token,), "one")
    return dict(r) if r else None

def conta(email):
    r = q("SELECT * FROM photographer WHERE email=?", (email,), "one")
    return dict(r) if r else None

# ---------------- configuração persistente ----------------
def segredo(chave):
    """Segredo do servidor, criado sozinho na primeira vez e guardado no banco.

    Fica no banco de propósito: sobrevive a restart e a `rm -rf /opt/foton`, entra no
    backup diário, e não exige ninguém abrir o Cloud Shell para definir variável.
    """
    r = q("SELECT valor FROM config WHERE chave=?", (chave,), "one")
    if r and r["valor"]:
        return r["valor"]
    v = secrets.token_urlsafe(24)
    q("INSERT OR REPLACE INTO config(chave,valor) VALUES(?,?)", (chave, v))
    return v

def gasta_credito(email):
    q("UPDATE photographer SET credits=MAX(0,credits-1) WHERE email=?", (email,))

# ---------------- admin ----------------
def todos_fotografos():
    rs = q("""SELECT p.email, p.nome, p.marca, p.credits, p.credits_total, p.criado,
                     (SELECT COUNT(*) FROM event WHERE dono=p.email AND auto=0) eventos
              FROM photographer p ORDER BY p.criado DESC""", (), "all")
    return [dict(r) for r in rs]

def da_creditos(email, n):
    q("""UPDATE photographer SET credits=credits+?, credits_total=credits_total+?
         WHERE email=?""", (n, n, email.strip().lower()))
    return conta(email.strip().lower())

def troca_senha(email, nova):
    q("UPDATE photographer SET senha=? WHERE email=?", (hash_senha(nova), email.strip().lower()))
    q("DELETE FROM session WHERE email=?", (email.strip().lower(),))   # derruba sessões antigas

def resumo_geral():
    def n(sql):
        r = q(sql, (), "one"); return list(r)[0] if r else 0
    return {
        "fotografos": n("SELECT COUNT(*) FROM photographer"),
        "eventos":    n("SELECT COUNT(*) FROM event WHERE auto=0"),
        "fotos":      n("SELECT COUNT(*) FROM photo"),
        "convidados": n("SELECT COUNT(*) FROM guest"),
        "contatos":   n("SELECT COUNT(*) FROM contact"),
    }

# ---------------- eventos ----------------
def cria_evento(code, dono=None, nome="Evento", data="", marca="FÓTON", auto=0):
    q("""INSERT OR REPLACE INTO event(code,dono,nome,data,marca,status,auto,criado)
         VALUES(?,?,?,?,?,'live',?,?)""", (code, dono, nome[:60], data[:10], (marca or "FÓTON")[:40], auto, time.time()))

def evento(code):
    r = q("SELECT * FROM event WHERE code=?", (code,), "one")
    return dict(r) if r else None

def eventos_de(dono):
    rs = q("""SELECT e.*, (SELECT COUNT(*) FROM photo WHERE event_code=e.code) fotos,
                     (SELECT COUNT(*) FROM guest WHERE event_code=e.code) convidados
              FROM event e WHERE e.dono=? AND (e.auto=0 OR
                   (SELECT COUNT(*) FROM photo WHERE event_code=e.code)>0)
              ORDER BY e.criado DESC""", (dono,), "all")
    return [dict(r) for r in rs]

def adota_evento(code, dono):
    """Reivindica um evento SEM dono (órfão) para o fotógrafo. Nunca rouba de outro."""
    e = evento(code)
    if not e: return False
    if e["dono"] and e["dono"] != dono: return False        # já tem dono: não mexe
    q("UPDATE event SET dono=?, auto=0 WHERE code=?", (dono, code))
    return True

def expirar(dias_biometria=7, dias_fotos=90):
    """LGPD — minimização e retenção: biometria some rápido; fotos seguem a retenção
    do plano. Roda diariamente. Retorna o que foi apagado (para o log)."""
    import time as _t
    agora = _t.time()
    lim_bio = agora - dias_biometria * 86400
    lim_fot = agora - dias_fotos * 86400
    # 1) biometria dos convidados (dado sensível) — vida curta
    gs = q("SELECT id FROM guest WHERE criado < ?", (lim_bio,), "all")
    for g in gs:
        q("DELETE FROM match WHERE guest_id=?", (g["id"],))
        q("DELETE FROM guest WHERE id=?", (g["id"],))
    # 2) contatos deixados voluntariamente seguem a retenção das fotos
    q("DELETE FROM contact WHERE ts < ?", (lim_fot,))
    # 3) fotos e rostos delas
    ps = q("SELECT id FROM photo WHERE criado < ?", (lim_fot,), "all")
    for p in ps:
        q("DELETE FROM face WHERE photo_id=?", (p["id"],))
        q("DELETE FROM match WHERE photo_id=?", (p["id"],))
        q("DELETE FROM photo WHERE id=?", (p["id"],))
    return {"convidados": len(gs), "fotos": len(ps)}

def apagar_dados_do_convidado(gid):
    """Direito de exclusão (LGPD Art. 18): o titular pede e sai tudo dele."""
    achou = bool(q("SELECT 1 FROM guest WHERE id=?", (gid,), "one"))
    q("DELETE FROM match WHERE guest_id=?", (gid,))
    q("DELETE FROM contact WHERE guest_id=?", (gid,))
    q("DELETE FROM guest WHERE id=?", (gid,))
    return achou

def orfaos():
    rs = q("""SELECT e.code, e.nome, e.criado,
                     (SELECT COUNT(*) FROM photo WHERE event_code=e.code) fotos
              FROM event e WHERE (e.dono IS NULL OR e.dono='')
              ORDER BY e.criado DESC""", (), "all")
    return [dict(r) for r in rs]

def apaga_evento(code):
    for t in ("photo", "face", "guest", "contact"):
        q(f"DELETE FROM {t} WHERE event_code=?", (code,))
    q("DELETE FROM match WHERE guest_id IN (SELECT id FROM guest WHERE event_code=?)", (code,))
    q("DELETE FROM event WHERE code=?", (code,))

def encerra_evento(code):
    q("UPDATE event SET status='done' WHERE code=?", (code,))

# ---------------- fotos / rostos ----------------
def salva_foto(pid, code, bytes_, embs):
    q("INSERT INTO photo(id,event_code,bytes,n_faces,criado) VALUES(?,?,?,?,?)",
      (pid, code, bytes_, len(embs), time.time()))
    for e in embs:
        q("INSERT INTO face(photo_id,event_code,emb) VALUES(?,?,?)", (pid, code, e.tobytes()))

def foto_bytes(code, pid):
    r = q("SELECT bytes FROM photo WHERE id=? AND event_code=?", (pid, code), "one")
    return r["bytes"] if r else None

def fotos_de(code):
    rs = q("SELECT id,n_faces FROM photo WHERE event_code=? ORDER BY criado", (code,), "all")
    return [dict(r) for r in rs]

def apaga_foto(code, pid):
    q("DELETE FROM photo WHERE id=? AND event_code=?", (pid, code))
    q("DELETE FROM face WHERE photo_id=?", (pid,))
    q("DELETE FROM match WHERE photo_id=?", (pid,))

def rostos_de(code):
    rs = q("SELECT photo_id, emb FROM face WHERE event_code=?", (code,), "all")
    return [(r["photo_id"], r["emb"]) for r in rs]

# ---------------- convidados ----------------
def salva_convidado(gid, code, emb):
    q("INSERT INTO guest(id,event_code,emb,criado) VALUES(?,?,?,?)", (gid, code, emb.tobytes(), time.time()))

def convidado_existe(code, gid):
    return bool(q("SELECT 1 FROM guest WHERE id=? AND event_code=?", (gid, code), "one"))

def convidados_de(code):
    rs = q("SELECT id, emb FROM guest WHERE event_code=?", (code,), "all")
    return [(r["id"], r["emb"]) for r in rs]

def conta_convidados(code):
    r = q("SELECT COUNT(*) n FROM guest WHERE event_code=?", (code,), "one")
    return r["n"] if r else 0

def salva_match(gid, pid):
    q("INSERT OR IGNORE INTO match(guest_id,photo_id) VALUES(?,?)", (gid, pid))

def matches_de(gid):
    rs = q("SELECT photo_id FROM match WHERE guest_id=?", (gid,), "all")
    return sorted(r["photo_id"] for r in rs)

# ---------------- contatos ----------------
def salva_contato(code, gid, nome, contato):
    q("INSERT INTO contact(event_code,guest_id,nome,contato,ts) VALUES(?,?,?,?,?)",
      (code, gid, nome[:60], contato[:40], time.time()))

def ultima_foto(code):
    r = q("SELECT MAX(criado) t FROM photo WHERE event_code=?", (code,), "one")
    return r["t"] if r and r["t"] else None

def contatos_de(code):
    rs = q("SELECT nome,contato,ts FROM contact WHERE event_code=? ORDER BY ts DESC", (code,), "all")
    return [dict(r) for r in rs]
