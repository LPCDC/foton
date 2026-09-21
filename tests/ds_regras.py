"""Regras da constituição do design system (ADR-0038) como funções puras.

Uma fonte só: tests/test_ds.py e infra/pintura.py (alfândega, ADR-0039) importam daqui.
"""
import re

TEXTO, FORMA = 4.5, 3.0   # WCAG AA: texto normal; componente gráfico
TEMAS = ("dia", "noite")
PERFIS = ("pro", "empresa", "social")


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


def problemas_de_contraste(css):
    """Lista vazia = passa. KeyError = o CSS não traz o conjunto completo de tokens."""
    ruins = []
    for tema in TEMAS:
        for perfil in PERFIS:
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


def raios_usados(css):
    return sorted(set(v.strip() for v in re.findall(r"border-radius:\s*([^;}]+)", css)))


def raios_proibidos(css):
    return [r for r in raios_usados(css) if r not in ("0", "50%")]


def sombras_com_desfoque(css):
    ruins = []
    for s in re.findall(r"box-shadow:\s*([^;}]+)", css):
        for camada in re.split(r",(?![^(]*\))", s):
            medidas = re.findall(r"-?[\d.]+(?:px|rem)?|var\([^)]*\)", camada.replace("inset", ""))
            if len(medidas) >= 3 and medidas[2] not in ("0", "0px"):
                ruins.append(camada.strip())
    return ruins


def coral_como_texto(css):
    return re.findall(r"(?<![-\w])color:\s*var\(--coral\)", css)
