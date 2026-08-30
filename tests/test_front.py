"""Trava do front — pega o erro que quebra o app INTEIRO antes de ele subir.

Existe por causa de estragos reais, todos meus, numa mesma sessao:
  1. uma mensagem com \\n virou quebra de linha REAL na passagem pelo shell, cortou uma
     string JavaScript no meio e o arquivo parou de carregar: app em branco;
  2. uma edicao por linha comeu o meio de `registerEvent`;
  3. uma escrita que falhou no meio ZEROU o docs/PILOTO-1.md (144 linhas -> 0);
  4. `ehIOS` acabou definida duas vezes — a segunda vence, em silencio.

Nada disso e pego pelos testes de contrato: o servidor continua respondendo 200 com o
front morto. Este arquivo olha o front como TEXTO e recusa o que nao pode subir.

    python tests/test_front.py
"""
import io, json, os, re, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB = os.path.join(RAIZ, "app", "web")
IDX = os.path.join(WEB, "index.html")

FALHAS = []
def checa(nome, obtido, esperado):
    ok = obtido == esperado
    print(("  ok   " if ok else "  FALHA") + f" {nome}: {obtido} (esperado {esperado})")
    if not ok: FALHAS.append(nome)

html = io.open(IDX, encoding="utf-8", newline="").read()
ini = html.find("<script"); ini = html.find(">", ini) + 1
js = html[ini:html.rfind("</script>")]
linhas = re.split(r"\r?\n", js)

print("[1] O arquivo nao pode ter encolhido (escrita que falhou no meio)")
checa("index.html tem tamanho de gente", len(html) > 120_000, True)
checa("tem bloco de script", len(js) > 60_000, True)
for nome in ("sw.js", "manifest.webmanifest"):
    checa(f"{nome} nao esta vazio", os.path.getsize(os.path.join(WEB, nome)) > 200, True)

print("")
print("[2] Nenhuma string JavaScript cortada no meio (o erro que apagou o app)")

ASPA_DUPLA = '"'
ASPA_SIMPLES = "'"
CRASE = "`"

def limpa(linha):
    """Deixa so o que conta para saber se sobrou aspa aberta."""
    t = re.sub(r"\\.", "", linha)                 # escapes: \\' \\" \\n ...
    t = re.sub(CRASE + "[^" + CRASE + "]*" + CRASE, "", t)   # template que abre e fecha aqui
    t = re.sub(r"'[^']*'", "", t)                 # string simples completa
    t = re.sub(r'"[^"]*"', "", t)                 # string dupla completa
    return t

dentro_de_bloco = False
dentro_de_template = False
suspeitas = []
for n, linha in enumerate(linhas, 1):
    s = linha.strip()
    if "/*" in s and "*/" not in s:
        dentro_de_bloco = True
        continue
    if dentro_de_bloco:
        if "*/" in s: dentro_de_bloco = False
        continue
    if s.startswith("//") or s.startswith("*"):
        continue
    # template literal aberto em varias linhas: o miolo dele nao e codigo
    if linha.count(CRASE) % 2:
        dentro_de_template = not dentro_de_template
        continue
    if dentro_de_template:
        continue
    t = limpa(linha)
    if t.count(ASPA_SIMPLES) or t.count(ASPA_DUPLA):
        suspeitas.append((n, s[:60]))
checa("linhas com aspas abertas", suspeitas, [])

print("")
print("[3] As funcoes que o HTML chama existem de verdade")
chamadas = set(re.findall(r'onclick="([A-Za-z_$][\w$]*)\(', html))
definidas = set(re.findall(r"(?:async\s+)?function\s+([A-Za-z_$][\w$]*)\s*\(", js))
PALAVRAS = {"if", "for", "while", "switch", "return", "typeof", "delete", "new", "event"}
faltando = sorted(c for c in chamadas if c not in definidas and c not in PALAVRAS)
checa("onclick apontando para funcao inexistente", faltando, [])

print("")
print("[4] As pecas criticas continuam la (regressao das ultimas sessoes)")
essenciais = [
    "enviarLote", "enviarUma", "reduzir",                    # o caminho da foto
    "openGuest", "entrarNoEvento",                            # o caminho do convidado
    "receberDoCompartilhamento", "entregarCompartilhadas",    # Compartilhar do Android
    "fecharSobreposicao", "armarVoltar",                      # botao Voltar
    "tirarFotoAgora", "abrirScanner",                         # camera e leitor de QR
    "entrarComoEmpresa", "senhaAdminSeNecessario",            # conta de empresa
    "abrirAdmin", "admZerar", "admCompactar",                 # painel do admin
    "salvarCredenciais",                                      # trocar a propria senha
]
checa("funcoes essenciais ausentes", [f for f in essenciais if f not in definidas], [])

print("")
print("[5] Cada funcao so pode ser definida UMA vez")
todas = re.findall(r"(?:async\s+)?function\s+([A-Za-z_$][\w$]*)\s*\(", js)
checa("funcoes definidas em duplicata", sorted({f for f in todas if todas.count(f) > 1}), [])

print("")
print("[5b] Nenhum id repetido no HTML")
# getElementById devolve o PRIMEIRO. Havia dois id="cam-video" (a selfie do convidado,
# escondida, e o visor da camera): a camera ligava no video INVISIVEL — preview preto e
# foto funcionando, porque o ImageCapture usa a trilha, nao o elemento.
_ids = re.findall(r'id="([^"]+)"', html)
_rep = sorted({i for i in _ids if _ids.count(i) > 1})
checa("ids repetidos", _rep, [])

print("")
print("[6] Elementos que o JavaScript procura por id existem no HTML")
ids_no_html = set(re.findall(r'id="([^"]+)"', html))
procurados = set(re.findall(r"getElementById\(['\"]([^'\"]+)['\"]\)", js))
# id criado em tempo de execucao (el.id='x') nao precisa estar no HTML
dinamicos = set(re.findall(r"\.id\s*=\s*['\"]([^'\"]+)['\"]", js))
dinamicos |= {"prog", "prog-t", "prog-c", "prog-i"}
checa("getElementById para id que nao existe",
      sorted(p for p in procurados if p not in ids_no_html and p not in dinamicos), [])

print("")
print("[7] O manifest continua valido (o Compartilhar do Android depende dele)")
m = json.load(open(os.path.join(WEB, "manifest.webmanifest"), encoding="utf-8"))
checa("manifest e JSON valido", isinstance(m, dict), True)
checa("share_target intacto", (m.get("share_target") or {}).get("method"), "POST")
checa("campo dos arquivos continua 'fotos'",
      ((m.get("share_target") or {}).get("params") or {}).get("files", [{}])[0].get("name"), "fotos")

print("")
print("[8] Nenhuma senha vazou para dentro do repo (ele e publico)")
DE_TESTE = {"senha123", "outrasenha", "terceira1", "novasenha", "minhasenha123"}
suspeitos = []
for raiz, dirs, arqs in os.walk(RAIZ):
    dirs[:] = [d for d in dirs if d not in (".git", "__pycache__", "fotos-teste", "node_modules")]
    for a in arqs:
        if not a.endswith((".md", ".py", ".html", ".js", ".sh", ".yml", ".yaml", ".json", ".toml")):
            continue
        if a.startswith("test_"):          # senha de fixture e proposital
            continue
        try:
            txt = io.open(os.path.join(raiz, a), encoding="utf-8", errors="ignore").read()
        except Exception:
            continue
        for achado in re.finditer(r"(?i)senha\s*[=:]\s*['\"]([^'\"]{6,})['\"]", txt):
            v = achado.group(1)
            if v.startswith(("$", "{", "<")) or v in DE_TESTE:
                continue
            suspeitos.append(os.path.relpath(os.path.join(raiz, a), RAIZ) + ": " + v[:3] + "...")
checa("senha escrita em arquivo do repo", suspeitos, [])

print("")
print("TODOS OS TESTES PASSARAM" if not FALHAS else f"{len(FALHAS)} FALHA(S): {FALHAS}")
sys.exit(1 if FALHAS else 0)
