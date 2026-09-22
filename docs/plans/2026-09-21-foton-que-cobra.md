# Fóton que cobra — Método do Ateliê + Plano 1 (esteira da pintura)

> Use a skill `executing-plans` para implementar este plano tarefa a tarefa. Os passos usam
> caixas (`- [ ]`) para acompanhar.

**Goal:** chegar a uma versão do Fóton que **impressiona numa demonstração de 60 segundos e
já pode cobrar**, produzida por um método repetível em que cada peça vai para a pintura no
Higgsfield e volta por uma alfândega que não deixa passar erro de código, número sem lastro
nem imagem gerada de pessoa real.

**Architecture:** duas camadas. **(A) O método** — fases com portão de saída e o ciclo do
Ateliê, que vale para toda peça estética. **(B) O Plano 1** — a esteira executável do ciclo:
`infra/pintura.py` (ida e volta), regras do design system extraídas para um módulo que o
teste e a alfândega compartilham, e o teste da própria alfândega com prova do vermelho. As
fases seguintes viram planos próprios (um por subsistema), escritos quando o portão anterior
abrir.

**Tech Stack:** Python 3 só com biblioteca padrão (sem dependência nova), git, o design system
de `app/web/ds/` (ADR-0038), a suíte `tests/todos.sh`, deploy por `git push origin main`
verificado pelo `/health`.

---

## A. O método do Ateliê

### A.1 O ciclo de cada peça

```
  CONSTRUIR ──► IDA ──► PINTURA ──► VOLTA ──► ALFÂNDEGA ──► INTEGRAR ──► PROVAR ──► NO AR ──► APROVO?
  (Claude)    pacote   (Luiz no     pacote    pintura.py    (Claude,     navegador   push +    (Luiz)
              brief +  Higgsfield)  + MANI-   volta:        TDD, suíte   + celular   /health
              consti-               FESTO     aprova /      verde)       + contraste  = SHA
              tuição                          pendente /
                                              reprova
```

As regras vêm da experiência com a GLAMON (memória `higgsfield-arte-finalizacao`) e
viram máquina aqui:

| Regra | Como a esteira aplica |
|---|---|
| **Direção estética do pacote: aceita por padrão** | cor, imagem e texto que respeitam a constituição passam como APROVADO |
| **Patch de código: conferir contra o arquivo antes** | `.patch` nunca é aprovado sozinho: `git apply --check` reprova o que não aplica; o que aplica fica PENDENTE para eu ler |
| **Número só entra com lastro** | todo número em texto (s, %, R$, fotos, convidados) precisa de fonte no manifesto, senão PENDENTE |
| **Imagem gerada de pessoa real não entra, nunca** | `pessoa: real` com origem gerada → REPROVADO; pessoa fictícia passa com aviso de rótulo "ilustrativa" |
| **O Higgsfield entrega pacote, não publica** | no Fóton isso já é estrutural: só o `git push` publica, e só com a suíte verde |

**A constituição** é o que a pintura não pode mudar sem ADR: contraste WCAG AA nos 2 temas
× 3 perfis, só raios 0 e 50%, nenhuma sombra com desfoque, coral nunca como cor de texto,
QR sempre preto sobre branco, movimento reduzido respeitado, nenhuma foto de convidado real.
Se o Higgsfield propuser algo lindo que fere a constituição (uma sombra suave, por exemplo),
a resposta não é descartar em silêncio: é **trazer para o dono com ADR**, e se aprovado, o
teste muda junto.

### A.2 As fases e seus portões

| Fase | Entrega | Portão de saída (evidência) | Plano |
|---|---|---|---|
| **0 · Proteger** | certificado encolhido para `app` + `getfoton.duckdns.org` | `certbot renew --dry-run` sem erro, saída colada no chat | comando pronto (DNS-MIGRACAO §5) |
| **1 · Esteira** | `infra/pintura.py`, alfândega testada, manual `docs/PINTURA.md` | suíte verde com `test_pintura`, prova do vermelho, deploy pelo SHA | **este documento, parte B** |
| **2 · Vitrine pintada** | 1º ciclo real: a vitrine vai ao Higgsfield e volta | relatório da alfândega sem REPROVADO + "aprovo" do dono | Plano 2 |
| **3 · Os 60 segundos** | jornada do convidado redesenhada (QR → selfie → galeria ao vivo, tema noite) + **demonstração de mesa** | a demo roda do zero em um celular emprestado; P95 da demo medido | Plano 3 |
| **4 · A fotógrafa** | painel redesenhado + **cartaz com QR para imprimir** | Patrícia cria um evento sozinha, sem ajuda, cronometrado | Plano 4 |
| **5 · A prova** | medição com a R8 real: clique → celular | P95 medido no BENCHMARKS; **só então** o número vai para o site | Plano 5 (roteiro R8) |
| **6 · A vitrine de vendas** | site de vendas na nova gramática, hero pintado, demo "Adote um rosto" | Lighthouse e contraste medidos; nenhum número sem lastro | Plano 6 |
| **7 · Cobrar** | **Plano Fundadora**: preço + ativação manual pelo admin (costura de pagamento com provedor "manual") | primeira fotógrafa pagante ativada; recibo emitido | Plano 7 — **exige 3 decisões do dono** |

### A.3 As duas demonstrações — onde o "impressionar" mora

1. **Demonstração de mesa (fase 3), a principal — zero ficção.** Você está com a fotógrafa.
   Ela escaneia o QR e tira a selfie. Você fotografa ela ali, com o seu celular. A foto
   **chega no celular dela** enquanto ela ainda está olhando. Nenhum concorrente entrega
   isso numa conversa de café; é o diferencial do produto (CLAUDE.md §3) virado em gesto.
   Requisito técnico: um evento-demo que se limpa sozinho (retenção curta), para a selfie
   dela não ficar guardada.
2. **"Adote um rosto" (fase 6), para o site — quando não há ninguém na mesa.** O visitante
   escolhe um convidado **fictício, gerado no Higgsfield e rotulado como tal**, e vê as
   fotos daquela pessoa chegando ao vivo. **Experimento antes de construir:** identidades
   geradas com consistência de personagem precisam dar match entre si no buffalo_s acima de
   0,40 e **não** dar match entre pessoas diferentes. Hoje isso é
   `UNKNOWN — REQUIRES EXPERIMENT` (reusa `tests/experimento_limiar.py`).

### A.4 Cobrar "de alguma forma" antes do provedor de pagamento

A costura de pagamento da FIESTA-IMPLEMENTACAO §4.5 já prevê uma interface de provedor. O
caminho mais curto para a primeira receita, **sem integrar PSP**, é um provedor `manual`: a
fotógrafa paga por PIX, você confirma, o admin ativa o plano com registro na auditoria. Três
decisões são **suas** e bloqueiam a fase 7:

1. **Preço** — por evento, por pacote de upload ou mensal (tabela em `docs/PRODUTO.md` §3c).
2. **Quem emite o recibo/nota** — CNPJ, MEI ou pessoa física: `UNKNOWN`, pergunta para o
   contador, não para mim.
3. **O que a Fundadora ganha** — sugestão: preço travado por 12 meses em troca de depoimento
   e de fotos de evento autorizadas para o site.

---

## B. Plano 1 — a esteira da pintura

### Mapa de arquivos

| Arquivo | Responsabilidade |
|---|---|
| Criar `tests/ds_regras.py` | as regras da constituição como funções puras (contraste, raios, sombras) — **uma fonte só**, usada pelo teste e pela alfândega |
| Modificar `tests/test_ds.py` | passa a importar `ds_regras` em vez de definir as funções |
| Criar `infra/pintura.py` | `ida <peça>` monta o pacote de envio; `volta <pasta>` roda a alfândega e escreve `RELATORIO.md` |
| Criar `tests/test_pintura.py` | prova, com pacotes falsos, cada regra da alfândega — vermelho e verde |
| Modificar `tests/todos.sh` | inclui `test_pintura` |
| Modificar `.gitignore` | `_pintura/` fora do git (pacotes com imagens pesadas e rascunhos) |
| Criar `docs/PINTURA.md` | manual do dono: como mandar, o que pedir ao Higgsfield, como devolver |
| Modificar `docs/DECISIONS.md` | ADR-0039 — a esteira |

### Task 1: Extrair as regras da constituição

**Files:**
- Create: `tests/ds_regras.py`
- Modify: `tests/test_ds.py:22-69` e `:84-91`

- [ ] **Step 1: Criar o módulo com as funções que hoje moram no teste**

```python
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
```

- [ ] **Step 2: Trocar as definições em `tests/test_ds.py` pelo import**

Apagar as funções `bloco`, `tokens`, `lum`, `razao`, `problemas_de_contraste`,
`sombras_com_desfoque` e a constante `TEXTO, FORMA`, e logo depois de `import os, re, sys`
acrescentar:

```python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ds_regras import problemas_de_contraste, sombras_com_desfoque, raios_usados, coral_como_texto
```

E trocar as duas linhas que calculavam direto:

```python
checa("raios usados", raios_usados(CSS), ["0", "50%"])
checa("coral nunca como cor de texto", coral_como_texto(CSS), [])
```

- [ ] **Step 3: Rodar e conferir que nada mudou**

Run: `python tests/test_ds.py`
Expected: `TODOS OS TESTES PASSARAM`, com as mesmas 14 checagens de antes.

- [ ] **Step 4: Commit**

```bash
git add tests/ds_regras.py tests/test_ds.py
git commit -m "refactor(ds): regras da constituicao num modulo compartilhado"
```

### Task 2: O teste da alfândega (vermelho primeiro)

> **HISTÓRICO — não é a versão final.** Este bloco é anterior aos ajustes do revisor (§D):
> não reprova subpasta e sai `0 if ok else 1`. A versão congelada é o arquivo no repo
> (`tests/test_pintura.py`): subpasta → REPROVADO, saída 0 / 3 / 1 com o REPROVADO vencendo.

**Files:**
- Create: `tests/test_pintura.py`

- [ ] **Step 1: Escrever o teste inteiro, antes do código**

```python
"""Esteira da pintura (ADR-0039): a alfândega aprova, segura ou reprova o pacote que volta.

    python tests/test_pintura.py
"""
import json, os, shutil, sys, tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "infra"))
import pintura

CSS_ATUAL = open(os.path.join(RAIZ, "app", "web", "ds", "foton.css"), encoding="utf-8").read()

FALHAS = []
def checa(nome, obtido, esperado):
    ok = obtido == esperado
    print(("  ok   " if ok else "  FALHA") + f" {nome}: {obtido!r} (esperado {esperado!r})")
    if not ok: FALHAS.append(nome)

def pacote(arquivos, manifesto):
    """arquivos: {nome: conteúdo str|bytes}. manifesto: dict ou None (sem manifesto)."""
    d = tempfile.mkdtemp()
    for nome, conteudo in arquivos.items():
        modo = "wb" if isinstance(conteudo, bytes) else "w"
        with open(os.path.join(d, nome), modo, **({} if modo == "wb" else {"encoding": "utf-8"})) as f:
            f.write(conteudo)
    if manifesto is not None:
        with open(os.path.join(d, "MANIFESTO.json"), "w", encoding="utf-8") as f:
            json.dump(manifesto, f)
    return d

def veredito(d, nome):
    return {a: v for a, v, _ in pintura.volta(d)[1]}.get(nome)

JPG = b"\xff\xd8\xff\xe0fake"

print("\n[1] sem manifesto, nada entra")
d = pacote({"hero.jpg": JPG}, None)
ok, itens = pintura.volta(d)
checa("pacote sem MANIFESTO.json reprova", ok, False)

print("\n[2] arquivo fora do manifesto não tem procedência")
d = pacote({"hero.jpg": JPG, "extra.png": JPG},
           {"arquivos": {"hero.jpg": {"origem": "higgsfield", "pessoa": "nenhuma"}}})
checa("arquivo não listado", veredito(d, "extra.png"), "REPROVADO")
checa("arquivo listado e limpo", veredito(d, "hero.jpg"), "APROVADO")

print("\n[3] imagem gerada de pessoa real nunca entra")
d = pacote({"retrato.jpg": JPG}, {"arquivos": {"retrato.jpg": {"origem": "higgsfield", "pessoa": "real"}}})
checa("pessoa real gerada", veredito(d, "retrato.jpg"), "REPROVADO")
d = pacote({"retrato.jpg": JPG}, {"arquivos": {"retrato.jpg": {"origem": "foto-real", "pessoa": "real"}}})
checa("foto real de pessoa real espera autorização", veredito(d, "retrato.jpg"), "PENDENTE")
d = pacote({"retrato.jpg": JPG}, {"arquivos": {"retrato.jpg": {"origem": "higgsfield", "pessoa": "ficticia"}}})
checa("pessoa fictícia passa (com rótulo)", veredito(d, "retrato.jpg"), "APROVADO")
d = pacote({"retrato.jpg": JPG}, {"arquivos": {"retrato.jpg": {"pessoa": "nenhuma"}}})
checa("imagem sem origem", veredito(d, "retrato.jpg"), "REPROVADO")

print("\n[4] CSS passa pela constituição")
d = pacote({"foton.css": CSS_ATUAL}, {"arquivos": {"foton.css": {"origem": "higgsfield"}}})
checa("CSS atual intacto", veredito(d, "foton.css"), "APROVADO")
estragado = CSS_ATUAL.replace('--sobre-marca: #000000; }', '--sobre-marca: #FFFFFF; }', 1)
d = pacote({"foton.css": estragado}, {"arquivos": {"foton.css": {"origem": "higgsfield"}}})
checa("branco sobre coral", veredito(d, "foton.css"), "REPROVADO")
d = pacote({"extra.css": ".cartao { box-shadow: 0 4px 12px rgba(0,0,0,.1); border-radius: 12px; }"},
           {"arquivos": {"extra.css": {"origem": "higgsfield"}}})
checa("sombra difusa e raio de 12px", veredito(d, "extra.css"), "REPROVADO")

print("\n[5] patch de código: nunca aprovado sozinho")
ruim = "--- a/app/web/ds/foton.css\n+++ b/app/web/ds/foton.css\n@@ -1,1 +1,1 @@\n-linha que nao existe\n+outra\n"
d = pacote({"correcao.patch": ruim}, {"arquivos": {"correcao.patch": {"origem": "higgsfield"}}})
checa("patch que não aplica", veredito(d, "correcao.patch"), "REPROVADO")

print("\n[6] número só com lastro")
d = pacote({"textos.md": "A foto chega em 4 s no celular do convidado."},
           {"arquivos": {"textos.md": {"origem": "higgsfield"}}})
checa("número sem fonte", veredito(d, "textos.md"), "PENDENTE")
d = pacote({"textos.md": "A foto chega em 4 s no celular do convidado."},
           {"arquivos": {"textos.md": {"origem": "higgsfield", "fontes": {"4 s": "BENCHMARKS 2026-10-01"}}}})
checa("número com fonte", veredito(d, "textos.md"), "APROVADO")
d = pacote({"textos.md": "Receba suas fotos durante a festa."},
           {"arquivos": {"textos.md": {"origem": "higgsfield"}}})
checa("texto sem número", veredito(d, "textos.md"), "APROVADO")

print("\n[7] relatório e código de saída")
d = pacote({"retrato.jpg": JPG}, {"arquivos": {"retrato.jpg": {"origem": "higgsfield", "pessoa": "real"}}})
pintura.volta(d)
checa("RELATORIO.md escrito", os.path.exists(os.path.join(d, "RELATORIO.md")), True)
checa("com REPROVADO, saída 1", pintura.main(["volta", d]), 1)
d = pacote({"hero.jpg": JPG}, {"arquivos": {"hero.jpg": {"origem": "higgsfield", "pessoa": "nenhuma"}}})
checa("tudo limpo, saída 0", pintura.main(["volta", d]), 0)

print("\n[8] ida: o pacote leva brief, constituição e a versão do código")
destino = tempfile.mkdtemp()
pasta = pintura.ida("vitrine", raiz_saida=destino)
brief = open(os.path.join(pasta, "BRIEF.md"), encoding="utf-8").read()
checa("brief traz a constituição", "QR sempre preto sobre branco" in brief, True)
checa("brief traz o SHA", pintura.sha() in brief, True)
checa("arquivos da peça copiados", sorted(os.listdir(os.path.join(pasta, "arquivos"))), ["foton.css", "index.html"])
checa("exemplo de manifesto junto", os.path.exists(os.path.join(pasta, "MANIFESTO.exemplo.json")), True)
checa("peça desconhecida recusa", pintura.main(["ida", "nao-existe"]), 2)

print("\n" + ("TODOS OS TESTES PASSARAM" if not FALHAS else f"{len(FALHAS)} FALHA(S): {FALHAS}"))
sys.exit(1 if FALHAS else 0)
```

- [ ] **Step 2: Rodar e ver o vermelho**

Run: `python tests/test_pintura.py`
Expected: FAIL com `ModuleNotFoundError: No module named 'pintura'`.

### Task 3: A esteira (`infra/pintura.py`)

> **HISTÓRICO — não é a versão final.** Este bloco é anterior aos ajustes do revisor (§D):
> não reprova subpasta e sai `0 if ok else 1`. A versão congelada é o arquivo no repo
> (`infra/pintura.py`): subpasta → REPROVADO, saída 0 / 3 / 1 com o REPROVADO vencendo.

**Files:**
- Create: `infra/pintura.py`

- [ ] **Step 1: Implementar ida, volta e main**

```python
"""Esteira da pintura (ADR-0039): ida e volta do Higgsfield, com alfândega.

    python infra/pintura.py ida vitrine
        -> _pintura/AAAA-MM-DD-vitrine/ida/  (BRIEF.md, arquivos/, MANIFESTO.exemplo.json)
    python infra/pintura.py volta _pintura/AAAA-MM-DD-vitrine/volta
        -> RELATORIO.md na própria pasta; sai 1 se houver REPROVADO

A alfândega não publica nada. Ela só diz o que pode seguir para integração (APROVADO),
o que eu preciso ler antes (PENDENTE) e o que não entra (REPROVADO).
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
8. Nenhum número (tempo, preço, quantidade) sem fonte medida.
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
    base = raiz_saida or os.path.join(RAIZ, "_pintura")
    pasta = os.path.join(base, f"{datetime.date.today().isoformat()}-{peca}", "ida")
    os.makedirs(os.path.join(pasta, "arquivos"), exist_ok=True)
    for rel in PECAS[peca]:
        shutil.copy2(os.path.join(RAIZ, rel), os.path.join(pasta, "arquivos", os.path.basename(rel)))
    with open(os.path.join(pasta, "BRIEF.md"), "w", encoding="utf-8") as f:
        f.write(f"# Pintura: {peca}\n\nVersão do código: `{sha()}`. "
                f"Enviado em {datetime.date.today().isoformat()}.\n\n"
                "## O que pedir\n\nArte-finalização: imagem, textura, hierarquia, texto. "
                "A estrutura das telas e o fluxo ficam.\n\n"
                + CONSTITUICAO +
                "\n## Como devolver\n\nUma pasta com os arquivos e um `MANIFESTO.json` dizendo, "
                "para cada arquivo, a origem e se há pessoa na imagem. "
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
        return "PENDENTE", "aplica, mas conferir contra o arquivo antes (nunca aprovado sozinho)"
    if ext in TEXTO:
        fontes = {_norm(k) for k in info.get("fontes", {})}
        sem = [n for n in NUMERO.findall(conteudo) if _norm(n) not in fontes]
        if sem:
            return "PENDENTE", "número sem lastro: " + ", ".join(sorted(set(sem))[:6])
        return "APROVADO", ""
    return "PENDENTE", f"tipo {ext or 'sem extensão'} sem regra: olhar à mão"


def volta(pasta):
    manifesto_p = os.path.join(pasta, "MANIFESTO.json")
    nomes = sorted(n for n in os.listdir(pasta)
                   if n not in ("MANIFESTO.json", "RELATORIO.md") and os.path.isfile(os.path.join(pasta, n)))
    if not os.path.exists(manifesto_p):
        itens = [(n, "REPROVADO", "pacote sem MANIFESTO.json") for n in nomes] \
            or [("MANIFESTO.json", "REPROVADO", "ausente")]
    else:
        arquivos = json.load(open(manifesto_p, encoding="utf-8")).get("arquivos", {})
        itens = [(n, *_julga(os.path.join(pasta, n), n, arquivos.get(n))) for n in nomes]
    ok = not any(v == "REPROVADO" for _, v, _ in itens)
    with open(os.path.join(pasta, "RELATORIO.md"), "w", encoding="utf-8") as f:
        f.write(f"# Alfândega da pintura\n\nCódigo em `{sha()}`. "
                f"Resultado: **{'pode integrar' if ok else 'NÃO integrar'}**.\n\n"
                "| Arquivo | Veredito | Motivo |\n|---|---|---|\n")
        for n, v, m in itens:
            f.write(f"| `{n}` | {v} | {m} |\n")
    return ok, itens


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
    ok, itens = volta(argv[1])
    for n, v, m in itens:
        print(f"  {v:9} {n}  {m}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
```

- [ ] **Step 2: Rodar o teste até o verde**

Run: `python tests/test_pintura.py`
Expected: `TODOS OS TESTES PASSARAM` (22 checagens).

- [ ] **Step 3: Prova do vermelho de verdade** — comentar temporariamente a linha
  `if pessoa == "real" and origem != "foto-real":` e o `return` dela, rodar, e ver
  `FALHA pessoa real gerada: 'APROVADO' (esperado 'REPROVADO')`. Desfazer.

- [ ] **Step 4: Commit**

```bash
git add infra/pintura.py tests/test_pintura.py
git commit -m "feat(pintura): esteira ida/volta do Higgsfield com alfandega testada"
```

### Task 4: Suíte, gitignore, manual e ADR

**Files:**
- Modify: `tests/todos.sh:7`, `.gitignore`, `docs/DECISIONS.md` (fim)
- Create: `docs/PINTURA.md`

- [ ] **Step 1: Incluir na suíte e ignorar os pacotes**

```bash
sed -i 's/test_logo test_ds; do/test_logo test_ds test_pintura; do/' tests/todos.sh
printf '\n# --- Pacotes da pintura (Higgsfield): imagens pesadas e rascunhos ---\n_pintura/\n' >> .gitignore
```

- [ ] **Step 2: Escrever `docs/PINTURA.md`** — o manual do dono, curto:
  1. `python infra/pintura.py ida <peça>` e a pasta que ele gera;
  2. o que mandar ao Higgsfield: a pasta `ida/` + prints das telas (eu tiro pelo navegador);
  3. o que pedir: arte-finalização dentro da constituição (colar a seção do BRIEF);
  4. como devolver: tudo em `_pintura/<data>-<peça>/volta/` com `MANIFESTO.json`;
  5. o que acontece depois: eu rodo a volta, leio os PENDENTES, integro com TDD, e publico
     só com a suíte verde;
  6. **o Higgsfield nunca publica**, e imagem de convidado real nunca vai no pacote.

- [ ] **Step 3: ADR-0039 no fim de `docs/DECISIONS.md`** — contexto (ciclo do Higgsfield da
  GLAMON, incidentes de 14 e 15/09: patch inferido do DOM e foto gerada de pessoa real),
  decisão (esteira + alfândega, vereditos, constituição como contrato), o que **não** faz
  (não publica, não aplica patch), testes (`test_pintura`, prova do vermelho) e rollback
  (apagar `infra/pintura.py`, `tests/test_pintura.py`, `tests/ds_regras.py` volta para dentro
  de `test_ds.py`).

- [ ] **Step 4: Suíte inteira**

Run: `bash tests/todos.sh`
Expected: 6 suítes, `tudo verde — pode subir`.

- [ ] **Step 5: Commit, deploy e verificação**

```bash
git add tests/todos.sh .gitignore docs/PINTURA.md docs/DECISIONS.md
git commit -m "docs(pintura): manual do dono + ADR-0039"
git push origin main
```

Depois: repetir `curl -s https://app.foton.app.br/health` até `versao` bater com
`git rev-parse --short=7 HEAD`.

### Task 5: Primeira ida de verdade

- [ ] **Step 1:** `python infra/pintura.py ida vitrine`
- [ ] **Step 2:** prints da vitrine em 375 px e 1280 px, temas dia e noite, perfis fotógrafa e
  festa, salvos em `_pintura/<data>-vitrine/ida/prints/`.
- [ ] **Step 3:** entregar ao dono o caminho da pasta e o texto pronto para colar no Higgsfield.

**Portão da fase 1:** suíte verde com `test_pintura`, deploy verificado pelo SHA, e o pacote
de ida da vitrine nas suas mãos.

---

## C. Revisão do plano (feita)

- **Cobertura:** ciclo de ida → Task 3 (`ida`) e 5; alfândega → Tasks 2 e 3; regras da
  GLAMON → tabela A.1, cada uma com teste no [3], [5] e [6]; "impressionar" → A.3; "cobrar"
  → A.2 fase 7 e A.4; regras do repo (TDD, ADR, deploy pelo SHA) → Tasks 2–4.
- **Sem lacunas de nome:** `problemas_de_contraste`, `sombras_com_desfoque`, `raios_usados`,
  `raios_proibidos`, `coral_como_texto` definidos na Task 1 e usados com os mesmos nomes nas
  Tasks 1 e 3; `ida`, `volta`, `main`, `sha` definidos na Task 3 e usados no teste da Task 2.
- **O que não está aqui, de propósito:** as fases 2 a 7 viram planos próprios quando o
  portão anterior abrir. Escrever tudo agora seria planejar sobre respostas que ainda não
  existem (aprovação da vitrine, P95 da R8, preço).

---

## D. Ajustes do revisor antes do primeiro comando (dono, 2026-09-21) — aplicados

O dono aprovou o plano ("eu executaria; não o reescreveria") com quatro ajustes. O código
em `infra/pintura.py` e `tests/test_pintura.py` é a versão final — onde divergir dos blocos
da parte B acima, **vale o arquivo**.

1. **Patch que aplica → PENDENTE, testado.** O teste gera um patch real (via `difflib`)
   contra `app/web/ds/foton.css`, confere que ele aplica e exige PENDENTE.
2. **A volta é plana na V1.** Subpasta sai REPROVADA sem ser aberta, com o motivo "mova os
   arquivos para a raiz"; o resto do pacote continua sendo julgado.
3. **PENDENTE ≠ aprovado.** Saídas **0 / 3 / 1** (tudo aprovado / há pendente / há
   reprovado). O relatório só escreve "pode integrar tudo" no caso 0; com pendente, escreve
   "integrar só os APROVADOS" e quantos aguardam leitura humana.
4. **Números: checagem lexical e conservadora na V1**, escrita no código, no brief, no
   manual e na ADR-0039 — e **travada por teste** ("dez segundos" por extenso passa), para
   que uma melhoria futura mude o teste de propósito.

Estado: Tasks 1–4 feitas (`c7a2099`, `6c611a0` e o commit de docs); 34 checagens no
`test_pintura`, com prova do vermelho. Task 5 (primeira ida da vitrine) em seguida.

**Congelado em 2026-09-21** após a 2ª revisão do dono: subpasta e códigos de saída já
estavam no código (conferido rodando o cenário dele); entrou o teste da precedência
(PENDENTE + REPROVADO → 1) e a regra de pessoa real ficou operacional no manual (o que a
alfândega verifica é o manifesto, não a imagem). **Nada mais entra no Plano 1.**
