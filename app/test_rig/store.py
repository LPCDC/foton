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
        try: _conn.execute("ALTER TABLE photographer ADD COLUMN logo BLOB")
        except sqlite3.OperationalError: pass   # coluna ja existe (banco de producao antigo)
        # retencao de biometria POR CONTA. NULL = segue a politica geral (7 dias).
        # 0 = nao expira — so para album permanente, onde as MESMAS pessoas voltam
        # toda semana e refazer a selfie a cada 7 dias inviabilizaria o uso.
        try: _conn.execute("ALTER TABLE photographer ADD COLUMN ret_bio_dias INTEGER")
        except sqlite3.OperationalError: pass
        # Conta de EMPRESA: album interno, login compartilhado pela equipe. Quem entra
        # ve e baixa tudo, mas NAO cria nem apaga sem a senha de admin. Sem isto, a
        # senha do salao (que circula entre colaboradoras) apagaria o acervo inteiro.
        try: _conn.execute("ALTER TABLE photographer ADD COLUMN empresa INTEGER DEFAULT 0")
        except sqlite3.OperationalError: pass
        # Miniatura na MESMA linha da foto (ADR-0022). Nao e arquivo novo nem estagio
        # novo do pipeline: e um resize a mais na passada que ja decodificou a imagem.
        # A grade mostra quadradinhos de 110px e baixava a foto de 2048px inteira.
        try: _conn.execute("ALTER TABLE photo ADD COLUMN thumb BLOB")
        except sqlite3.OperationalError: pass
        # LOOK da conta (ADR-0028): curva leve aplicada na mesma passada que ja decodifica
        # a foto. NULL = nenhum look, e o pipeline fica identico ao que sempre foi — e o
        # que as contas existentes tem, entao esta migracao nao muda foto de ninguem.
        # IDEMPOTENCIA DE INGESTAO: impressao digital (SHA-256) dos bytes ORIGINAIS da
        # foto. A mesma foto reenviada (retentativa do FTP da camera, celular com
        # internet ruim que reenvia o lote) reaproveita a linha em vez de criar outra.
        # Linha antiga fica NULL — sem dedupe retroativo, e NULL nunca casa porque a
        # busca sempre passa um sha real. Nao e biometria: e hash do arquivo.
        try: _conn.execute("ALTER TABLE photo ADD COLUMN sha TEXT")
        except sqlite3.OperationalError: pass
        try: _conn.execute("CREATE INDEX IF NOT EXISTS ix_photo_sha ON photo(event_code, sha)")
        except sqlite3.OperationalError: pass
        try: _conn.execute("ALTER TABLE photographer ADD COLUMN look TEXT")
        except sqlite3.OperationalError: pass
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

CREDITOS_INICIAIS = int(os.environ.get("FOTON_CREDITOS_INICIAIS", "100"))

def cria_conta(email, senha, nome="", marca=""):
    email = email.strip().lower()
    if q("SELECT 1 FROM photographer WHERE email=?", (email,), "one"):
        return None
    q("INSERT INTO photographer(email,senha,nome,marca,credits,credits_total,criado) VALUES(?,?,?,?,?,?,?)",
      (email, hash_senha(senha), nome.strip()[:60], marca.strip()[:40], CREDITOS_INICIAIS, CREDITOS_INICIAIS, time.time()))
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

def salva_logo(email, png_bytes):
    q("UPDATE photographer SET logo=? WHERE email=?", (png_bytes, email))

def apaga_logo(email):
    q("UPDATE photographer SET logo=NULL WHERE email=?", (email,))

def pega_logo(email):
    r = q("SELECT logo FROM photographer WHERE email=?", (email,), "one")
    return r["logo"] if r and r["logo"] else None

def salva_look(email, look):
    """look vazio/None = volta a NENHUM look (a foto sai como sempre saiu)."""
    q("UPDATE photographer SET look=? WHERE email=?", ((look or None), email))

def pega_look(email):
    r = q("SELECT look FROM photographer WHERE email=?", (email,), "one")
    return r["look"] if r and r["look"] else None

def marca_ftp_visto(email):
    """Registra que a câmera CONSEGUIU logar no FTP, agora — sem precisar de foto.

    É a diferença entre a fotógrafa digitar a senha errada e só descobrir quando
    nenhuma foto aparece, e ela saber em segundos que funcionou.
    """
    q("INSERT OR REPLACE INTO config(chave,valor) VALUES(?,?)", ("ftp_visto:" + email, str(time.time())))

def ftp_visto_ha_s(email):
    r = q("SELECT valor FROM config WHERE chave=?", ("ftp_visto:" + email,), "one")
    if not r or not r["valor"]:
        return None
    return time.time() - float(r["valor"])

def gasta_credito(email):
    q("UPDATE photographer SET credits=MAX(0,credits-1) WHERE email=?", (email,))

# ---------------- admin ----------------
def todos_fotografos():
    """Uma linha por conta, com o que o operador precisa para decidir credito.

    Tudo por subconsulta em vez de JOIN: sao poucas contas, e assim uma conta sem
    evento nenhum continua aparecendo na lista (com JOIN ela sumiria).
    `bytes` e o que a conta ocupa DE VERDADE no banco — lembrando que o backup
    guarda 7 copias completas, entao no disco isso conta 8x.
    """
    rs = q("""SELECT p.email, p.nome, p.marca, p.credits, p.credits_total, p.criado,
                (SELECT COUNT(*) FROM event WHERE dono=p.email AND auto=0) eventos,
                (SELECT COUNT(*) FROM event WHERE dono=p.email AND status='live') ao_vivo,
                (SELECT COUNT(*) FROM photo WHERE event_code IN
                    (SELECT code FROM event WHERE dono=p.email)) fotos,
                (SELECT COUNT(*) FROM guest WHERE event_code IN
                    (SELECT code FROM event WHERE dono=p.email)) convidados,
                (SELECT COUNT(*) FROM contact WHERE event_code IN
                    (SELECT code FROM event WHERE dono=p.email)) contatos,
                (SELECT COALESCE(SUM(LENGTH(bytes)),0) FROM photo WHERE event_code IN
                    (SELECT code FROM event WHERE dono=p.email)) bytes,
                p.ret_bio_dias,
                p.empresa,
                (SELECT MAX(criado) FROM photo WHERE event_code IN
                    (SELECT code FROM event WHERE dono=p.email)) ultima_foto
              FROM photographer p ORDER BY p.criado DESC""", (), "all")
    return [dict(r) for r in rs]

def define_empresa(email, ligado):
    q("UPDATE photographer SET empresa=? WHERE email=?", (1 if ligado else 0, (email or "").strip().lower()))

def define_retencao_bio(email, dias):
    """dias=0 -> biometria NAO expira nessa conta. dias=None -> volta a politica geral."""
    q("UPDATE photographer SET ret_bio_dias=? WHERE email=?", (dias, (email or "").strip().lower()))

def contatos_todos(limite=300):
    """Todo contato que convidado deixou, em qualquer evento, com o dono do evento.

    E dado pessoal (nome + telefone): esta rota e SO do admin, nunca do convidado.
    Ordenado do mais novo para o mais velho — o que interessa e o de hoje.
    """
    rs = q("""SELECT c.nome, c.contato, c.ts, c.event_code, e.nome AS evento, e.dono
              FROM contact c LEFT JOIN event e ON e.code=c.event_code
              ORDER BY c.ts DESC LIMIT ?""", (limite,), "all")
    return [dict(r) for r in (rs or [])]

def uso_de_credito():
    """Quanto credito ja foi gasto e em que. Um credito sai por evento criado."""
    def n(sql):
        r = q(sql, (), "one"); return (list(r)[0] if r else 0) or 0
    return {
        "creditos_dados":  n("SELECT COALESCE(SUM(credits_total),0) FROM photographer"),
        "creditos_livres": n("SELECT COALESCE(SUM(credits),0) FROM photographer"),
        "eventos_criados": n("SELECT COUNT(*) FROM event WHERE auto=0"),
        "eventos_orfaos":  n("SELECT COUNT(*) FROM event WHERE auto=1 OR dono IS NULL"),
        "eventos_vazios":  n("""SELECT COUNT(*) FROM event WHERE auto=0 AND code NOT IN
                                (SELECT DISTINCT event_code FROM photo)"""),
    }

def da_creditos(email, n):
    q("""UPDATE photographer SET credits=credits+?, credits_total=credits_total+?
         WHERE email=?""", (n, n, email.strip().lower()))
    return conta(email.strip().lower())

def troca_senha(email, nova):
    q("UPDATE photographer SET senha=? WHERE email=?", (hash_senha(nova), email.strip().lower()))
    q("DELETE FROM session WHERE email=?", (email.strip().lower(),))   # derruba sessões antigas

def renomeia_conta(antigo, novo):
    """Troca o LOGIN da conta levando junto tudo que aponta para ele.

    O login é PRIMARY KEY de `photographer` e é referenciado por `event.dono`,
    `session.email` e a chave `ftp_visto:<login>` do config. Trocar só a linha do
    fotógrafo deixaria os eventos dele órfãos — a mesma "fábrica de eventos órfãos"
    que já custou caro aqui (a fotógrafa não via o evento, o convidado via as fotos).

    A `logo` é coluna de `photographer`, então viaja sozinha com o UPDATE.
    As sessões antigas caem de propósito: quem estava logado com o login velho
    precisa entrar de novo.
    """
    antigo = (antigo or "").strip().lower()
    novo = (novo or "").strip().lower()
    if not antigo or not novo or antigo == novo:
        return False
    if not conta(antigo) or conta(novo):
        return False
    with _lock:
        cx = conn()
        try:
            cx.execute("BEGIN IMMEDIATE")
            cx.execute("UPDATE photographer SET email=? WHERE email=?", (novo, antigo))
            cx.execute("UPDATE event SET dono=? WHERE dono=?", (novo, antigo))
            cx.execute("DELETE FROM session WHERE email=?", (antigo,))
            cx.execute("UPDATE config SET chave=? WHERE chave=?",
                       ("ftp_visto:" + novo, "ftp_visto:" + antigo))
            cx.commit()
        except Exception:
            cx.rollback()
            raise
    return True

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
    # 1) biometria dos convidados (dado sensível) — vida curta.
    #    Conta com ret_bio_dias definido manda no proprio dado: 0 = nao expira
    #    (album permanente), N = N dias. Sem valor, vale a politica geral.
    isentos = [r["email"] for r in (q(
        "SELECT email FROM photographer WHERE ret_bio_dias IS NOT NULL AND ret_bio_dias=0", (), "all") or [])]
    gs = []
    for g in (q("""SELECT g.id, e.dono, p.ret_bio_dias FROM guest g
                   LEFT JOIN event e ON e.code=g.event_code
                   LEFT JOIN photographer p ON p.email=e.dono
                   WHERE g.criado < ?""", (agora,), "all") or []):
        rd = g["ret_bio_dias"]
        limite = lim_bio if rd is None else (None if rd == 0 else agora - rd * 86400)
        if limite is None:
            continue                      # conta isenta: biometria fica
        if q("SELECT 1 FROM guest WHERE id=? AND criado < ?", (g["id"], limite), "one"):
            gs.append(g)
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

def zerar_dados():
    """Apaga TODO o conteudo (fotos, rostos, convidados, matches, contatos, eventos)
    e mantem as CONTAS: login, senha, nome, marca, logo, creditos e retencao.

    Compacta no fim, e ai esta o ponto: o SQLite NAO devolve espaco ao apagar linha —
    o arquivo so cresce. Sem o VACUUM, "zerar" deixaria o banco do mesmo tamanho e a
    unica coisa que zerar deveria resolver (disco) continuaria igual.
    """
    antes = tamanho_no_disco()
    contagem = {t: (q("SELECT COUNT(*) FROM " + t, (), "one") or [0])[0]
                for t in ("photo", "face", "guest", "match", "contact", "event")}
    for t in ("match", "face", "photo", "guest", "contact", "event"):
        q("DELETE FROM " + t)
    depois = compacta()
    return {**contagem, "bytes_antes": antes, "bytes_depois": depois}

def compacta():
    """VACUUM: reescreve o arquivo sem os buracos das linhas apagadas.

    Nao roda dentro de transacao — por isso o isolation_level vai a None e volta.

    O checkpoint no fim NAO e detalhe: o banco roda em WAL, entao o VACUUM sozinho
    deixa o resultado no arquivo -wal e o .db principal continua do mesmo tamanho.
    Sem o wal_checkpoint(TRUNCATE) a limpeza nao aparece no disco — foi exatamente
    o que aconteceu no primeiro teste (11380 KB antes, 11380 KB depois).

    E caro (reescreve o banco inteiro), entao e acao manual do admin, nao rotina.
    """
    with _lock:
        cx = conn()
        cx.commit()
        antigo = cx.isolation_level
        try:
            cx.isolation_level = None
            cx.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            cx.execute("VACUUM")
            cx.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        finally:
            cx.isolation_level = antigo
    return tamanho_no_disco()

def tamanho_no_disco():
    """O banco ocupa .db + -wal + -shm. Olhar so o .db engana durante o WAL."""
    n = 0
    for suf in ("", "-wal", "-shm"):
        try: n += os.path.getsize(DB_PATH + suf)
        except OSError: pass
    return n

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

def apaga_conta(email):
    """Apaga o fotógrafo e TUDO que é dele: eventos, fotos, rostos, convidados,
    contatos e sessões. Não existia rota para isso — conta criada por engano ficava
    para sempre, e o titular não tinha como sair (LGPD Art. 18)."""
    email = (email or "").strip().lower()
    if not conta(email):
        return False
    for e in q("SELECT code FROM event WHERE dono=?", (email,), "all") or []:
        apaga_evento(e["code"])
    q("DELETE FROM session WHERE email=?", (email,))
    q("DELETE FROM photographer WHERE email=?", (email,))
    return True

def apaga_evento(code):
    for t in ("photo", "face", "guest", "contact"):
        q(f"DELETE FROM {t} WHERE event_code=?", (code,))
    q("DELETE FROM match WHERE guest_id IN (SELECT id FROM guest WHERE event_code=?)", (code,))
    q("DELETE FROM event WHERE code=?", (code,))

def encerra_evento(code):
    q("UPDATE event SET status='done' WHERE code=?", (code,))

# ---------------- fotos / rostos ----------------
def sha_de(raw):
    """Impressao digital dos bytes ORIGINAIS (antes do tratamento — o watermark tem
    hora/marca e mudaria o hash da mesma foto)."""
    return hashlib.sha256(raw).hexdigest()

def foto_por_sha(code, sha):
    """Ja existe esta MESMA foto neste evento? Devolve o photo_id, ou None.

    Escopo e o EVENTO de proposito: a mesma foto em dois eventos sao duas entregas
    diferentes (marcas/donos diferentes), nao uma duplicata."""
    if not sha: return None
    r = q("SELECT id FROM photo WHERE event_code=? AND sha=?", (code, sha), "one")
    return r["id"] if r else None

def salva_foto(pid, code, bytes_, embs, thumb=None, sha=None):
    q("INSERT INTO photo(id,event_code,bytes,n_faces,criado,thumb,sha) VALUES(?,?,?,?,?,?,?)",
      (pid, code, bytes_, len(embs), time.time(), thumb, sha))
    for e in embs:
        q("INSERT INTO face(photo_id,event_code,emb) VALUES(?,?,?)", (pid, code, e.tobytes()))

def convidados_da_foto(pid):
    """Quem ja foi entregue nesta foto — para a resposta da duplicata ser igual a da
    entrega original (o cliente que reenviou nao percebe diferenca)."""
    rs = q("SELECT guest_id FROM match WHERE photo_id=?", (pid,), "all")
    return [r["guest_id"] for r in rs]

def n_faces_de(code, pid):
    r = q("SELECT n_faces FROM photo WHERE id=? AND event_code=?", (pid, code), "one")
    return r["n_faces"] if r else 0

def foto_bytes(code, pid):
    r = q("SELECT bytes FROM photo WHERE id=? AND event_code=?", (pid, code), "one")
    return r["bytes"] if r else None

def thumb_bytes(code, pid):
    """Miniatura da foto. None quando a foto e ANTERIOR a coluna existir — nesse caso
    quem chama gera uma vez e guarda (`guarda_thumb`), espalhando o custo em vez de
    exigir uma migracao que travaria a VM."""
    r = q("SELECT thumb FROM photo WHERE id=? AND event_code=?", (pid, code), "one")
    return r["thumb"] if r and r["thumb"] else None

def guarda_thumb(code, pid, dados):
    q("UPDATE photo SET thumb=? WHERE id=? AND event_code=?", (dados, pid, code))

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
