"""Esteira da pintura (ADR-0039): a alfândega aprova, segura ou reprova o pacote que volta.

    python tests/test_pintura.py

Três vereditos, e PENDENTE NÃO É APROVADO: só o que sai APROVADO pode ser integrado sem
leitura humana. Saída do comando: 0 = tudo aprovado; 3 = há pendentes; 1 = há reprovado.
"""
import difflib, json, os, sys, tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "infra"))
import pintura

CSS_REL = "app/web/ds/foton.css"
CSS_ATUAL = open(os.path.join(RAIZ, CSS_REL), encoding="utf-8").read()

FALHAS = []
def checa(nome, obtido, esperado):
    ok = obtido == esperado
    print(("  ok   " if ok else "  FALHA") + f" {nome}: {obtido!r} (esperado {esperado!r})")
    if not ok: FALHAS.append(nome)

def pacote(arquivos, manifesto):
    """arquivos: {nome: conteúdo str|bytes}; nome com '/' cria subpasta. manifesto None = sem."""
    d = tempfile.mkdtemp()
    for nome, conteudo in arquivos.items():
        caminho = os.path.join(d, *nome.split("/"))
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        if isinstance(conteudo, bytes):
            open(caminho, "wb").write(conteudo)
        else:
            open(caminho, "w", encoding="utf-8", newline="").write(conteudo)
    if manifesto is not None:
        with open(os.path.join(d, "MANIFESTO.json"), "w", encoding="utf-8") as f:
            json.dump(manifesto, f)
    return d

def veredito(d, nome):
    return {a: v for a, v, _ in pintura.volta(d)[1]}.get(nome)

def limpo(nome):
    return {"arquivos": {nome: {"origem": "higgsfield", "pessoa": "nenhuma"}}}

JPG = b"\xff\xd8\xff\xe0fake"

print("\n[1] sem manifesto, nada entra")
ok, itens = pintura.volta(pacote({"hero.jpg": JPG}, None))
checa("pacote sem MANIFESTO.json reprova", ok, False)

print("\n[2] arquivo fora do manifesto não tem procedência")
d = pacote({"hero.jpg": JPG, "extra.png": JPG}, limpo("hero.jpg"))
checa("arquivo não listado", veredito(d, "extra.png"), "REPROVADO")
checa("arquivo listado e limpo", veredito(d, "hero.jpg"), "APROVADO")

print("\n[3] a pasta de volta é plana na V1: subpasta não passa sem ser vista")
d = pacote({"hero.jpg": JPG, "fotos/escondida.jpg": JPG}, limpo("hero.jpg"))
checa("subpasta reprova", veredito(d, "fotos/"), "REPROVADO")
checa("o resto do pacote segue julgado", veredito(d, "hero.jpg"), "APROVADO")

print("\n[4] imagem gerada de pessoa real nunca entra")
def img(info): return veredito(pacote({"retrato.jpg": JPG}, {"arquivos": {"retrato.jpg": info}}), "retrato.jpg")
checa("pessoa real gerada", img({"origem": "higgsfield", "pessoa": "real"}), "REPROVADO")
checa("foto real de pessoa real espera autorização", img({"origem": "foto-real", "pessoa": "real"}), "PENDENTE")
checa("pessoa fictícia passa (com rótulo)", img({"origem": "higgsfield", "pessoa": "ficticia"}), "APROVADO")
checa("imagem sem origem", img({"pessoa": "nenhuma"}), "REPROVADO")
checa("imagem sem dizer se há pessoa", img({"origem": "higgsfield"}), "REPROVADO")

print("\n[5] CSS passa pela constituição")
def css(nome, conteudo): return veredito(pacote({nome: conteudo}, {"arquivos": {nome: {"origem": "higgsfield"}}}), nome)
checa("CSS atual intacto", css("foton.css", CSS_ATUAL), "APROVADO")
checa("branco sobre coral", css("foton.css", CSS_ATUAL.replace('--sobre-marca: #000000; }', '--sobre-marca: #FFFFFF; }', 1)), "REPROVADO")
checa("sombra difusa e raio de 12px",
      css("extra.css", ".cartao { box-shadow: 0 4px 12px rgba(0,0,0,.1); border-radius: 12px; }"), "REPROVADO")

print("\n[6] patch de código: nunca aprovado sozinho")
def patch(nome, conteudo): return veredito(pacote({nome: conteudo}, {"arquivos": {nome: {"origem": "higgsfield"}}}), nome)
ruim = f"--- a/{CSS_REL}\n+++ b/{CSS_REL}\n@@ -1,1 +1,1 @@\n-linha que nao existe\n+outra\n"
checa("patch que não aplica", patch("ruim.patch", ruim), "REPROVADO")
atual = open(os.path.join(RAIZ, CSS_REL), encoding="utf-8", newline="").read().splitlines(keepends=True)
novo = list(atual); novo[0] = novo[0].replace("Fóton", "Fóton (pintado)", 1)
bom = "".join(difflib.unified_diff(atual, novo, f"a/{CSS_REL}", f"b/{CSS_REL}"))
checa("patch gerado de fato altera algo", bom.count("\n+") >= 1 and "(pintado)" in bom, True)
checa("patch que APLICA fica PENDENTE (humano lê antes)", patch("bom.patch", bom), "PENDENTE")

print("\n[7] número só com lastro — checagem LEXICAL e conservadora na V1")
def txt(texto, fontes=None):
    info = {"origem": "higgsfield"}
    if fontes: info["fontes"] = fontes
    return veredito(pacote({"textos.md": texto}, {"arquivos": {"textos.md": info}}), "textos.md")
checa("número sem fonte", txt("A foto chega em 4 s no celular."), "PENDENTE")
checa("número com fonte", txt("A foto chega em 4 s no celular.", {"4 s": "BENCHMARKS 2026-10-01"}), "APROVADO")
checa("preço sem fonte", txt("Plano a partir de R$ 49."), "PENDENTE")
checa("texto sem número", txt("Receba suas fotos durante a festa."), "APROVADO")
# Limite conhecido e aceito na V1: número por extenso escapa da checagem lexical.
# Se um dia a checagem ficar semântica, este teste muda de propósito — não por acidente.
checa("limite da V1: número por extenso não é detectado", txt("A foto chega em dez segundos."), "APROVADO")

print("\n[8] PENDENTE não é aprovado: relatório e código de saída")
d = pacote({"retrato.jpg": JPG}, {"arquivos": {"retrato.jpg": {"origem": "higgsfield", "pessoa": "real"}}})
checa("com REPROVADO, saída 1", pintura.main(["volta", d]), 1)
rel = open(os.path.join(d, "RELATORIO.md"), encoding="utf-8").read()
checa("relatório diz NÃO integrar", "NÃO integrar" in rel, True)
d = pacote({"hero.jpg": JPG, "textos.md": "Chega em 4 s."},
           {"arquivos": {"hero.jpg": {"origem": "higgsfield", "pessoa": "nenhuma"}, "textos.md": {"origem": "higgsfield"}}})
checa("com PENDENTE e sem reprovado, saída 3", pintura.main(["volta", d]), 3)
rel = open(os.path.join(d, "RELATORIO.md"), encoding="utf-8").read()
checa("relatório não diz 'pode integrar' com pendente", "pode integrar tudo" in rel, False)
checa("relatório manda integrar só os APROVADOS", "integrar só os APROVADOS" in rel, True)
d = pacote({"textos.md": "Chega em 4 s.", "fotos/segredo.css": ".x{color:red}"},
           {"arquivos": {"textos.md": {"origem": "higgsfield"}}})
checa("PENDENTE + REPROVADO juntos: vence o REPROVADO, saída 1", pintura.main(["volta", d]), 1)
d = pacote({"hero.jpg": JPG}, limpo("hero.jpg"))
checa("tudo aprovado, saída 0", pintura.main(["volta", d]), 0)
checa("só aqui o relatório libera tudo",
      "pode integrar tudo" in open(os.path.join(d, "RELATORIO.md"), encoding="utf-8").read(), True)

print("\n[9] ida: o pacote leva brief, constituição, limites e a versão do código")
pasta = pintura.ida("vitrine", raiz_saida=tempfile.mkdtemp())
brief = open(os.path.join(pasta, "BRIEF.md"), encoding="utf-8").read()
checa("brief traz a constituição", "QR sempre preto sobre branco" in brief, True)
checa("brief avisa que a volta é plana", "sem subpastas" in brief, True)
checa("brief traz o SHA", pintura.sha() in brief, True)
checa("arquivos da peça copiados", sorted(os.listdir(os.path.join(pasta, "arquivos"))), ["foton.css", "index.html"])
checa("exemplo de manifesto junto", os.path.exists(os.path.join(pasta, "MANIFESTO.exemplo.json")), True)
checa("peça desconhecida recusa", pintura.main(["ida", "nao-existe"]), 2)

print("\n" + ("TODOS OS TESTES PASSARAM" if not FALHAS else f"{len(FALHAS)} FALHA(S): {FALHAS}"))
sys.exit(1 if FALHAS else 0)
