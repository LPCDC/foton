# PINTURA.md — como uma peça do Fóton vai ao Higgsfield e volta

> Manual do dono. A decisão está na ADR-0039; o método inteiro, em
> `docs/plans/2026-09-21-foton-que-cobra.md`.

```
constituição ─► Claude ─► ida ─► Higgsfield ─► volta ─► alfândega ─► APROVADO ─► integrar ─► TDD ─► push ─► /health
                                                                 ├► PENDENTE ─► humano lê
                                                                 └► REPROVADO ─► não entra
```

A IA tem **liberdade dentro da constituição** e **nenhuma autoridade sobre o produto**: ela
entrega pacote, não publica. No Fóton só o `git push` publica, e só com a suíte verde.

## 1. Mandar (ida)

```bash
python infra/pintura.py ida vitrine
```

Gera `_pintura/AAAA-MM-DD-vitrine/ida/` com:
- `BRIEF.md` — o que pedir, a **constituição** e a versão do código;
- `arquivos/` — as telas e o CSS da peça;
- `MANIFESTO.exemplo.json` — o formato da devolução;
- `prints/` — eu tiro pelo navegador (celular e desktop, dia e noite).

Peças conhecidas hoje: `vitrine`, `convidado`. `_pintura/` fica fora do git.

## 2. O que pedir ao Higgsfield

Cole a seção **Constituição** do `BRIEF.md` junto do pedido. Peça **arte-finalização**:
imagem, textura, hierarquia, texto. A estrutura das telas e o fluxo ficam.

Três coisas que o pacote **não** pode trazer:
1. **Foto ou imagem gerada de pessoa real.** A alfândega verifica o que o manifesto
   declara — ela não avalia a imagem em si:

   | origem | pessoa | veredito |
   |---|---|---|
   | `higgsfield` (ou outra geração) | `real` | **REPROVADO** |
   | `higgsfield` | `ficticia` | APROVADO, rotulada como ilustrativa |
   | `foto-real` | `real` | PENDENTE (falta autorização de uso de imagem) |

   Por isso o manifesto precisa ser honesto: declarar `ficticia` para uma pessoa real é o
   único jeito de a regra falhar.
2. **Número sem fonte** (tempo, preço, quantidade). E número sempre com algarismo.
3. **Mudança na constituição sem conversa.** Se o Higgsfield propuser algo lindo que a fere
   (uma sombra suave, um cartão arredondado), traga assim mesmo: vira decisão sua com ADR,
   e o teste muda junto — nunca em silêncio.

## 3. Devolver (volta)

Tudo numa pasta **plana, sem subpastas**: `_pintura/AAAA-MM-DD-vitrine/volta/`, com um
`MANIFESTO.json` que diz, para cada arquivo:
- `origem`: `higgsfield`, `banco`, `foto-real` ou `gerado-local`;
- `pessoa` (imagens): `nenhuma`, `ficticia` ou `real`;
- `fontes` (textos): de onde vem cada número.

## 4. A alfândega

```bash
python infra/pintura.py volta _pintura/AAAA-MM-DD-vitrine/volta
```

| Veredito | Quer dizer | Exemplos |
|---|---|---|
| **APROVADO** | pode ser integrado — ainda passa por TDD e pela suíte | imagem sem pessoa; pessoa fictícia (rotulada); CSS dentro da constituição |
| **PENDENTE** | **um humano lê antes. PENDENTE não é aprovado.** | todo patch de código que aplica; número sem fonte; foto real de pessoa real (falta autorização de imagem) |
| **REPROVADO** | não entra | imagem gerada de pessoa real; arquivo fora do manifesto; subpasta; patch que não aplica; CSS que fere contraste, raio ou sombra |

Saída do comando: **0** tudo aprovado · **3** há pendente (integrar só os aprovados) ·
**1** há reprovado. O detalhe fica em `RELATORIO.md`, na própria pasta de volta.

## 5. Limites da V1 (conhecidos e aceitos)

- **A volta é plana.** Subpasta é reprovada sem ser aberta — assim nada passa sem ser visto.
- **A checagem de números é lexical e conservadora.** Ela pega algarismo com unidade
  (s, min, %, R$, fotos, convidados, pessoas, x). "Dez segundos" por extenso escapa; um
  número inofensivo pode cair em PENDENTE à toa. Errar para o lado do PENDENTE é o certo.
- **Patch nunca é aprovado sozinho**, mesmo aplicando limpo: na GLAMON, um patch inferido da
  tela reintroduzia o defeito que corrigia.
