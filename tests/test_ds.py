"""Design system (ADR-0038): contraste recalculado do próprio CSS, forma, cache e QR.

    python tests/test_ds.py

Não abre navegador: lê app/web/ds/foton.css, resolve os tokens para cada combinação de
tema x perfil e mede o contraste WCAG. Quem mudar uma cor e quebrar a leitura reprova aqui.
Prova do vermelho embutida: cópias estragadas de propósito precisam reprovar.
"""
import os, re, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSS = open(os.path.join(RAIZ, "app", "web", "ds", "foton.css"), encoding="utf-8").read()
VITRINE = open(os.path.join(RAIZ, "app", "web", "ds", "index.html"), encoding="utf-8").read()
SW = open(os.path.join(RAIZ, "app", "web", "sw.js"), encoding="utf-8").read()

FALHAS = []
def checa(nome, obtido, esperado):
    ok = obtido == esperado
    print(("  ok   " if ok else "  FALHA") + f" {nome}: {obtido!r} (esperado {esperado!r})")
    if not ok: FALHAS.append(nome)

# ---------------------------------------------------------------- tokens
def bloco(css, seletor):
    m = re.search(re.escape(seletor) + r"\s*\{([^}]*)\}", css)
    return dict(re.findall(r"--([\w-]+):\s*([^;]+);", m.group(1))) if m else {}

def tokens(css, tema, perfil):
    t = {}
    t.update(bloco(css, ":root"))
    if perfil != "pro":
        t.update(bloco(css, f':root[data-perfil="{perfil}"]'))
    if tema == "noite":
        t.update(bloco(css, ':root[data-tema="noite"]'))
    def resolve(v, n=0):
        v = v.strip()
        m = re.fullmatch(r"var\(--([\w-]+)\)", v)
        return resolve(t[m.group(1)], n + 1) if m and n < 10 else v
    return {k: resolve(v).upper() for k, v in t.items()}

def lum(h):
    c = [int(h.lstrip("#")[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]

def razao(a, b):
    x, y = sorted([lum(a), lum(b)], reverse=True)
    return (x + 0.05) / (y + 0.05)

TEXTO, FORMA = 4.5, 3.0   # WCAG AA: texto normal; componente gráfico

def problemas_de_contraste(css):
    ruins = []
    for tema in ("dia", "noite"):
        for perfil in ("pro", "empresa", "social"):
            t = tokens(css, tema, perfil)
            pares = [
                ("tinta sobre papel", t["tinta"], t["papel"], TEXTO),
                ("texto secundário (fio) sobre papel", t["fio"], t["papel"], TEXTO),
                ("texto sobre a marca", t["sobre-marca"], t["marca"], TEXTO),
                ("marca como forma sobre papel", t["marca"], t["papel"], FORMA),
                ("texto sobre alarme", t["sobre-alarme"], t["alarme"], TEXTO),
                ("alarme como forma sobre papel", t["alarme"], t["papel"], FORMA),
                ("texto preto sobre flash", "#000000", t["flash"], TEXTO),
                ("texto preto sobre coral", "#000000", t["coral"], TEXTO),
            ]
            for nome, a, b, minimo in pares:
                if razao(a, b) < minimo:
                    ruins.append(f"{tema}/{perfil}: {nome} {razao(a, b):.2f}")
    return ruins

print("\n[1] contraste — 2 temas x 3 perfis x 8 pares, recalculado do CSS")
checa("nenhum par abaixo do mínimo WCAG AA", problemas_de_contraste(CSS), [])

print("\n[2] prova do vermelho — o teste enxerga contraste ruim")
estragado = CSS.replace('--sobre-marca: #000000; }', '--sobre-marca: #FFFFFF; }', 1)
checa("branco sobre coral reprova", any("social: texto sobre a marca" in p for p in problemas_de_contraste(estragado)), True)
estragado = CSS.replace("--fio: #6B6B6B;", "--fio: #B0B0B0;", 1)
checa("cinza claro demais como texto reprova", any("fio" in p for p in problemas_de_contraste(estragado)), True)

# ---------------------------------------------------------------- forma
print("\n[3] forma — só dois raios, nenhuma sombra difusa")
raios = sorted(set(v.strip() for v in re.findall(r"border-radius:\s*([^;}]+)", CSS)))
checa("raios usados", raios, ["0", "50%"])
def sombras_com_desfoque(css):
    ruins = []
    for s in re.findall(r"box-shadow:\s*([^;}]+)", css):
        for camada in re.split(r",(?![^(]*\))", s):
            medidas = re.findall(r"-?[\d.]+(?:px|rem)?|var\([^)]*\)", camada.replace("inset", ""))
            if len(medidas) >= 3 and medidas[2] not in ("0", "0px"):
                ruins.append(camada.strip())
    return ruins
checa("sombras com desfoque", sombras_com_desfoque(CSS), [])
checa("prova do vermelho: sombra de cartão genérica reprova",
      len(sombras_com_desfoque(CSS + ".x { box-shadow: 0 4px 12px rgba(0,0,0,.1); }")), 1)
checa("coral nunca como cor de texto", re.findall(r"(?<![-\w])color:\s*var\(--coral\)", CSS), [])
checa("respeita movimento reduzido", "prefers-reduced-motion: reduce" in CSS, True)

# ---------------------------------------------------------------- cache
print("\n[4] cache — o service worker guarda .css sem revalidar")
checa("sw.js trata .css como estático (motivo da regra)", bool(re.search(r"ESTATICO\s*=.*css", SW)), True)
refs = re.findall(r'href="(/ds/foton\.css[^"]*)"', VITRINE)
checa("vitrine referencia o CSS", len(refs), 1)
checa("referência leva versão no endereço", all(re.search(r"\?v=\d+$", r) for r in refs), True)

# ---------------------------------------------------------------- QR e privacidade
print("\n[5] QR sempre preto sobre branco; vitrine sem foto de gente")
qr = re.search(r"\.qr-quadro\s*\{([^}]*)\}", CSS)
checa("QR tem fundo branco fixo (não segue o tema)", bool(qr and "#FFFFFF" in qr.group(1).upper()), True)
checa("módulos do QR em preto fixo", ".qr i { background: #000000; }" in VITRINE, True)
checa("vitrine não carrega imagem nenhuma", re.findall(r"<img\b", VITRINE), [])

print("\n" + ("TODOS OS TESTES PASSARAM" if not FALHAS else f"{len(FALHAS)} FALHA(S): {FALHAS}"))
sys.exit(1 if FALHAS else 0)
