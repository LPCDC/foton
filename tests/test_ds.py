"""Design system (ADR-0038): contraste recalculado do próprio CSS, forma, cache e QR.

    python tests/test_ds.py

Não abre navegador: lê app/web/ds/foton.css, resolve os tokens para cada combinação de
tema x perfil e mede o contraste WCAG. Quem mudar uma cor e quebrar a leitura reprova aqui.
Prova do vermelho embutida: cópias estragadas de propósito precisam reprovar.
As regras moram em tests/ds_regras.py — a alfândega da pintura (ADR-0039) usa as mesmas.
"""
import os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ds_regras import problemas_de_contraste, sombras_com_desfoque, raios_usados, coral_como_texto

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSS = open(os.path.join(RAIZ, "app", "web", "ds", "foton.css"), encoding="utf-8").read()
VITRINE = open(os.path.join(RAIZ, "app", "web", "ds", "index.html"), encoding="utf-8").read()
SW = open(os.path.join(RAIZ, "app", "web", "sw.js"), encoding="utf-8").read()

FALHAS = []
def checa(nome, obtido, esperado):
    ok = obtido == esperado
    print(("  ok   " if ok else "  FALHA") + f" {nome}: {obtido!r} (esperado {esperado!r})")
    if not ok: FALHAS.append(nome)

print("\n[1] contraste — 2 temas x 3 perfis x 8 pares, recalculado do CSS")
checa("nenhum par abaixo do mínimo WCAG AA", problemas_de_contraste(CSS), [])

print("\n[2] prova do vermelho — o teste enxerga contraste ruim")
estragado = CSS.replace('--sobre-marca: #000000; }', '--sobre-marca: #FFFFFF; }', 1)
checa("branco sobre coral reprova", any("social: texto sobre a marca" in p for p in problemas_de_contraste(estragado)), True)
estragado = CSS.replace("--fio: #6B6B6B;", "--fio: #B0B0B0;", 1)
checa("cinza claro demais como texto reprova", any("fio" in p for p in problemas_de_contraste(estragado)), True)

print("\n[3] forma — só dois raios, nenhuma sombra difusa")
checa("raios usados", raios_usados(CSS), ["0", "50%"])
checa("sombras com desfoque", sombras_com_desfoque(CSS), [])
checa("prova do vermelho: sombra de cartão genérica reprova",
      len(sombras_com_desfoque(CSS + ".x { box-shadow: 0 4px 12px rgba(0,0,0,.1); }")), 1)
checa("coral nunca como cor de texto", coral_como_texto(CSS), [])
checa("respeita movimento reduzido", "prefers-reduced-motion: reduce" in CSS, True)

print("\n[4] cache — o service worker guarda .css sem revalidar")
checa("sw.js trata .css como estático (motivo da regra)", bool(re.search(r"ESTATICO\s*=.*css", SW)), True)
refs = re.findall(r'href="(/ds/foton\.css[^"]*)"', VITRINE)
checa("vitrine referencia o CSS", len(refs), 1)
checa("referência leva versão no endereço", all(re.search(r"\?v=\d+$", r) for r in refs), True)

print("\n[5] QR sempre preto sobre branco; vitrine sem foto de gente")
qr = re.search(r"\.qr-quadro\s*\{([^}]*)\}", CSS)
checa("QR tem fundo branco fixo (não segue o tema)", bool(qr and "#FFFFFF" in qr.group(1).upper()), True)
checa("módulos do QR em preto fixo", ".qr i { background: #000000; }" in VITRINE, True)
checa("vitrine não carrega imagem nenhuma", re.findall(r"<img\b", VITRINE), [])

print("\n" + ("TODOS OS TESTES PASSARAM" if not FALHAS else f"{len(FALHAS)} FALHA(S): {FALHAS}"))
sys.exit(1 if FALHAS else 0)
