"""Esteira da pintura (ADR-0039): ida e volta do Higgsfield, com alfândega.

    python infra/pintura.py ida vitrine
        -> _pintura/AAAA-MM-DD-vitrine/ida/  (BRIEF.md, arquivos/, MANIFESTO.exemplo.json)
    python infra/pintura.py volta _pintura/AAAA-MM-DD-vitrine/volta
        -> RELATORIO.md na própria pasta

A alfândega não publica e não aplica nada. Ela só classifica cada arquivo que voltou:
    APROVADO   pode ser integrado (ainda passa por TDD e pela suíte antes do push)
    PENDENTE   um humano lê antes. PENDENTE NÃO É APROVADO.
    REPROVADO  não entra
Saída: 0 = tudo APROVADO; 3 = há PENDENTE (integrar só os APROVADOS); 1 = há REPROVADO.

Limites conhecidos da V1, aceitos de propósito:
  - A pasta de volta é PLANA. Subpasta é REPROVADA sem ser aberta: nada passa sem ser visto.
  - A checagem de números é LEXICAL e conservadora: pega algarismo com unidade (s, min, %,
    R$, fotos, convidados, pessoas, x). Número por extenso ("dez segundos") escapa; um número
    inofensivo com unidade pode cair em PENDENTE à toa. Errar para o lado do PENDENTE é o certo.
"""
import datetime, json, os, re, shutil, subprocess, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "tests"))
import ds_regras

PECAS = {
    "vitrine": ["app/web/ds/index.html", "app/web/ds/foton.css"],
    "convidado": ["app/web/index.html", "app/web/ds/foton.css"],
}
IMAGEM = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".avif", ".svg", ".mp4", ".webm", ".mov"}
TEXTO = {".md", ".txt", ".html", ".json"}
ORIGENS = {"higgsfield", "banco", "foto-real", "gerado-local"}
PESSOAS = {"nenhuma", "ficticia", "real"}
NUMERO = re.compile(
    r"R\$\s*\d[\d.,]*|\d[\d.,]*\s*(?:%|s\b|segundos?\b|min\b|minutos?\b|fotos?\b|convidados?\b|pessoas?\b|x\b)",
    re.I)
SAIDA = {"APROVADO": 0, "PENDENTE": 3, "REPROVADO": 1}

CONSTITUICAO = """\
## Constituição — o que a pintura não muda sem ADR

1. Contraste WCAG AA em 2 temas (dia, noite) x 3 perfis (fotógrafa, empresa, festa).
   Texto preto sobre coral e sobre flash; branco sobre cobalto (de dia).
2. Só dois raios: 0 e 50%. Nada de cartão arredondado.
3. Nenhuma sombra com desfoque. Estrutura é borda preta de 2 px.
4. Coral nunca como cor de texto sobre fundo claro.
5. QR sempre preto sobre branco, em qualquer tema.
6. Movimento reduzido respeitado; só um movimento automático por tela.
7. Nenhuma foto de convidado real. Pessoa gerada = fictícia e rotulada como ilustrativa.
8. Nenhum número (tempo, preço, quantidade) sem fonte medida. Escreva números com
   algarismos: a conferência é por texto, e "dez segundos" por extenso passa sem ser vista.
"""

MANIFESTO_EXEMPLO = {
    "peca": "vitrine",
    "arquivos": {
        "hero.jpg": {"origem": "higgsfield", "pessoa": "nenhuma", "uso": "fundo da abertura"},
        "convidada-1.jpg": {"origem": "higgsfield", "pessoa": "ficticia", "uso": "demo Adote um rosto"},
        "textos.md": {"origem": "higgsfield", "fontes": {"4 s": "docs/BENCHMARKS.md, medição de AAAA-MM-DD"}},
        "foton.css": {"origem": "higgsfield"},
        "correcao.patch": {"origem": "higgsfield", "motivo": "o que o patch corrige"},
    },
}


def sha():
    try:
        return subprocess.run(["git", "rev-parse", "--short=7", "HEAD"], cwd=RAIZ,
                              capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        return "sem-git"


def ida(peca, raiz_saida=None):
    if peca not in PECAS:
        raise KeyError(peca)
    hoje = datetime.date.today().isoformat()
    pasta = os.path.join(raiz_saida or os.path.join(RAIZ, "_pintura"), f"{hoje}-{peca}", "ida")
    os.makedirs(os.path.join(pasta, "arquivos"), exist_ok=True)
    for rel in PECAS[peca]:
        shutil.copy2(os.path.join(RAIZ, rel), os.path.join(pasta, "arquivos", os.path.basename(rel)))
    with open(os.path.join(pasta, "BRIEF.md"), "w", encoding="utf-8") as f:
        f.write(f"# Pintura: {peca}\n\nVersão do código: `{sha()}`. Enviado em {hoje}.\n\n"
                "## O que pedir\n\nArte-finalização: imagem, textura, hierarquia, texto. "
                "A estrutura das telas e o fluxo ficam.\n\n"
                + CONSTITUICAO +
                "\n## Como devolver\n\nUma pasta **plana, sem subpastas**, com os arquivos e um "
                "`MANIFESTO.json` dizendo, para cada arquivo, a origem e se há pessoa na imagem "
                "(`nenhuma`, `ficticia` ou `real`). Números no texto levam a fonte em `fontes`. "
                "Veja `MANIFESTO.exemplo.json`.\n")
    with open(os.path.join(pasta, "MANIFESTO.exemplo.json"), "w", encoding="utf-8") as f:
        json.dump(MANIFESTO_EXEMPLO, f, ensure_ascii=False, indent=2)
    return pasta


def _norm(s):
    return re.sub(r"\s+", "", s).lower()


def _julga(caminho, nome, info):
    ext = os.path.splitext(nome)[1].lower()
    if info is None:
        return "REPROVADO", "fora do manifesto: sem procedência"
    if ext in IMAGEM:
        origem, pessoa = info.get("origem"), info.get("pessoa")
        if origem not in ORIGENS:
            return "REPROVADO", f"origem ausente ou desconhecida ({origem!r})"
        if pessoa not in PESSOAS:
            return "REPROVADO", "diga se há pessoa na imagem: nenhuma, ficticia ou real"
        if pessoa == "real" and origem != "foto-real":
            return "REPROVADO", "imagem gerada de pessoa real nunca entra"
        if pessoa == "real":
            return "PENDENTE", "foto de pessoa real: precisa de autorização de uso de imagem"
        if pessoa == "ficticia":
            return "APROVADO", "pessoa fictícia: rotular como ilustrativa onde aparecer"
        return "APROVADO", ""
    conteudo = open(caminho, encoding="utf-8", errors="replace").read()
    if ext == ".css":
        erros = ds_regras.raios_proibidos(conteudo) + ds_regras.sombras_com_desfoque(conteudo) \
            + ds_regras.coral_como_texto(conteudo)
        if ":root" in conteudo:
            try:
                erros += ds_regras.problemas_de_contraste(conteudo)
            except KeyError as e:
                return "PENDENTE", f"tokens incompletos (falta --{e.args[0]}): conferir à mão"
        if erros:
            return "REPROVADO", "fere a constituição: " + "; ".join(erros[:4])
        return "APROVADO", ""
    if ext in (".patch", ".diff"):
        r = subprocess.run(["git", "apply", "--check", caminho], cwd=RAIZ, capture_output=True, text=True)
        if r.returncode != 0:
            return "REPROVADO", "não aplica no código atual (pode ter sido inferido da tela, não do fonte)"
        return "PENDENTE", "aplica, mas conferir contra o arquivo antes (patch nunca é aprovado sozinho)"
    if ext in TEXTO:
        fontes = {_norm(k) for k in info.get("fontes", {})}
        sem = [n for n in NUMERO.findall(conteudo) if _norm(n) not in fontes]
        if sem:
            return "PENDENTE", "número sem lastro: " + ", ".join(sorted(set(sem))[:6])
        return "APROVADO", ""
    return "PENDENTE", f"tipo {ext or 'sem extensão'} sem regra: olhar à mão"


def volta(pasta):
    """Devolve (sem_reprovado, itens). itens = [(nome, veredito, motivo)]."""
    manifesto_p = os.path.join(pasta, "MANIFESTO.json")
    entradas = sorted(n for n in os.listdir(pasta) if n not in ("MANIFESTO.json", "RELATORIO.md"))
    subpastas = [n for n in entradas if os.path.isdir(os.path.join(pasta, n))]
    nomes = [n for n in entradas if n not in subpastas]
    itens = [(n + "/", "REPROVADO", "a volta é plana na V1: mova os arquivos para a raiz da pasta")
             for n in subpastas]
    if not os.path.exists(manifesto_p):
        itens += [(n, "REPROVADO", "pacote sem MANIFESTO.json") for n in nomes] \
            or [("MANIFESTO.json", "REPROVADO", "ausente")]
    else:
        arquivos = json.load(open(manifesto_p, encoding="utf-8")).get("arquivos", {})
        itens += [(n, *_julga(os.path.join(pasta, n), n, arquivos.get(n))) for n in nomes]
    _relatorio(pasta, itens)
    return not any(v == "REPROVADO" for _, v, _ in itens), itens


def _pior(itens):
    vs = {v for _, v, _ in itens}
    return "REPROVADO" if "REPROVADO" in vs else "PENDENTE" if "PENDENTE" in vs else "APROVADO"


def _relatorio(pasta, itens):
    pior = _pior(itens)
    pend = sum(1 for _, v, _ in itens if v == "PENDENTE")
    resultado = {
        "APROVADO": "**pode integrar tudo** (e ainda passa por TDD e pela suíte antes do push).",
        "PENDENTE": f"**integrar só os APROVADOS.** {pend} PENDENTE(S) aguardam leitura humana — "
                    "PENDENTE não é aprovado.",
        "REPROVADO": "**NÃO integrar** até resolver os REPROVADOS.",
    }[pior]
    with open(os.path.join(pasta, "RELATORIO.md"), "w", encoding="utf-8") as f:
        f.write(f"# Alfândega da pintura\n\nCódigo em `{sha()}`. Resultado: {resultado}\n\n"
                "| Arquivo | Veredito | Motivo |\n|---|---|---|\n")
        for n, v, m in itens:
            f.write(f"| `{n}` | {v} | {m} |\n")


def main(argv):
    if len(argv) != 2 or argv[0] not in ("ida", "volta"):
        print(__doc__)
        return 2
    if argv[0] == "ida":
        try:
            print(ida(argv[1]))
            return 0
        except KeyError:
            print(f"peça desconhecida: {argv[1]}. Conhecidas: {', '.join(PECAS)}")
            return 2
    _, itens = volta(argv[1])
    for n, v, m in itens:
        print(f"  {v:9} {n}  {m}")
    return SAIDA[_pior(itens)]


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
