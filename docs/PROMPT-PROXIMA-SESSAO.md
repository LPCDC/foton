# Prompt para a próxima sessão

> Cole isto numa sessão nova. Escrito para carregar contexto sem gastar tokens
> repetindo documento, e para forçar o rigor do Gauntlet em vez de pedir por ele.
>
> **Versão de 2026-08-30, fim do dia.** Substitui o prompt anterior (login com
> Google), que foi cumprido e virou a **ADR-0026** (rejeitado por ora, com gatilho
> de reversão escrito).

---

Fóton — continuação. Antes de tocar em qualquer coisa, leia nesta ordem:
`BLUEPRINT.md` (estado geral e as armadilhas do §7 — são cicatrizes reais, cada
uma custou caro), `docs/PRODUTO.md` §1 (a tese dos "três públicos, um motor") e
`docs/DECISIONS.md` da **ADR-0022 em diante** (as recentes: miniatura, crédito
cortado, autorização, login Google rejeitado, remoção do Lenis, look por conta,
LGPD). Não confie na sua memória de treino sobre este projeto — confie nos
documentos e no código. Onde eles divergirem, **o código ganha**, e corrigir o
documento faz parte da tarefa.

## O que este produto é, em três linhas

Fóton entrega ao convidado, **durante o evento**, as fotos em que ele aparece:
escaneia um QR, tira 1 selfie, e a galeria pessoal enche ao vivo. Roda em
produção (`https://app.foton.app.br`), numa VM Oracle de 1 vCPU, com clientes
reais. O diferencial não é reconhecimento facial (commodity) — é **na hora**.

## Estado em 2026-08-30 (verificado, não lembrado)

- **App em produção**, 3 contas reais: Patrícia (fotógrafa, Santos), Carol,
  GLAMON (salão, álbum permanente).
- **Deploy é `git push`** — a VM se atualiza sozinha em ~2 min. Infra (systemd,
  nginx, porta) exige Cloud Shell da Oracle.
- **4 suítes, 280 checagens**, `bash tests/todos.sh`. Verde antes de todo push,
  sem exceção.
- **Crédito cortado** (ADR-0024): criar evento é grátis, com login.
- **Look por conta** recém-entregue (ADR-0028).
- **Site de marca** (`site/`) pronto e **não publicado** — ver "Pendências" abaixo.

## A regra que vale mais que qualquer outra aqui

> **Não quebrar o que funciona.** Há fotógrafa cobrando de cliente com isto.
> Uma foto que não chega no meio de uma festa paga é um dano real, não um bug.

Na prática: mudança no pipeline de foto, na fila de upload ou no reconhecimento
pede cautela extra — checar `/admin/saude` (última foto + carga) antes. Deploy
com evento ao vivo **está liberado** nesta fase (decisão do dono, 2026-08-30),
com bom senso para o que é "coisa grande".

## As três frentes (decidido: adolescente está FORA)

`docs/PRODUTO.md` §1 crava a tese e ela continua valendo: **não são três
produtos — é um motor com três portas.** O dono confirmou em 2026-08-30: **um
motor, três frentes**, e o **público adolescente saiu de escopo** (era LGPD Art.
14, consentimento parental — regime jurídico diferente, decisão antes de tela).

| Quem | O que é para ela | Estado |
|---|---|---|
| **Patrícia** — fotógrafa profissional | ferramenta de trabalho; evento começa e termina | no ar |
| **GLAMON** — empresa | acervo permanente, mesmas pessoas toda semana | no ar (ADR-0021) |
| **Ana** — pessoa no próprio rolê | é fotógrafa **e** convidada ao mesmo tempo | não feito (PRODUTO.md §2) |

**A tarefa provável desta sessão é dar identidade própria a cada frente.** Antes
de escrever CSS, leia o parágrafo seguinte, que é a parte que um agente erra:

> O app é **um arquivo HTML de ~205 mil bytes, sem framework**. Desenhar três
> painéis à mão triplica a superfície de bug num código que já pagou caro por
> armadilhas repetidas (§7). O caminho recomendado é **uma estrutura, três
> peles**: um `perfil` de conta (`pro | social | empresa`) que controla só três
> coisas — (1) **vocabulário** (evento/álbum/rolê), (2) **quais blocos do painel
> aparecem** (marca d'água e FTP são da Patrícia; a Ana não quer ver isso),
> (3) **tokens de cor/tipo**, não CSS novo. Diferenciação real percebida, com
> fração do risco, e reversível — perfil errado é uma coluna, não um rewrite.
> Se você discordar disso depois de ler o código, **diga por quê** e proponha
> outra coisa; o que não vale é ignorar e sair desenhando.

Já existe fundação para isso: `photographer.empresa`, `MODO_EMPRESA_PEDIDO`, e
vocabulário que já troca em alguns lugares (hoje improvisado).

## Pendências concretas, em ordem de valor

**1. O maior risco do piloto não é código** (BLUEPRINT §9, continua verdade):
- **TTFR ponta a ponta nunca foi medido** com relógio nas duas pontas. É *o*
  número que prova a promessa do produto. Só as partes foram medidas
  (`/ingest` P95 1,9 s + poll 2,5 s).
- **Nada foi testado no aparelho da Patrícia:** o Fóton aparece no menu
  "Compartilhar" do Android dela (ADR-0018)? A galeria dela seleciona várias
  fotos por arrasto? Teste de 30 segundos com o celular na mão, que vale mais
  que qualquer código.
- **30 selfies simultâneas: P95 8,2 s** — a entrada de convidados é o gargalo
  real, não o envio de fotos.

**2. Site de marca não está no ar, e o motivo não é o que os documentos diziam.**
`site/index.html` está pronto (marca nova, abertura com flash, GSAP sem Lenis —
ADR-0027). `netlify.toml` já aponta para `site/`. **Mas o projeto no Netlify é
um "Netlify Drop"** — `Current repository: Not linked`, último deploy por upload
em 24/ago. Ele **nunca leu o `netlify.toml`**, porque o Netlify só lê esse
arquivo quando constrói a partir de um repo ligado. Falta o dono terminar o
assistente "Link repository" (GitHub → `LPCDC/foton` → branch `main` → build
vazio → publish `site`). Sem isso, **nenhum `git push` publica o site**.

**3. DNS de `foton.app.br` — não mexer sem ler isto.** Hoje `foton.app.br`,
`www.foton.app.br` e `app.foton.app.br` **compartilham o mesmo certificado** da
VM (`infra/dominio.sh`, `certbot --expand`). Apontar a raiz para o Netlify sem
**separar o certificado antes** pode derrubar o HTTPS do **app** numa renovação
futura, semanas depois, sem ninguém relacionar as coisas. Ordem obrigatória:
(1) separar o cert para cobrir só `app.` + duckdns, (2) **ver uma renovação
passar**, (3) só então mexer no DNS da raiz.

**4. LGPD — o que falta é documento, não código.** A condição nº 1 da decisão do
dono em `docs/PRODUTO.md` §3b-2 — **contrato com o organizador** declarando que
ele tem base legal para os dados que cadastra — **não existe**. Enquanto não
existir, quem responde por um pré-cadastro sem base legal somos nós. As outras
três condições estão cumpridas e agora **testadas** (ADR-0029).

**5. Fila de upload que sobrevive** (PRODUTO.md, "Ordem que eu defenderia" nº 1):
verificar se `filaFalhas` ainda vive em memória. É o único item capaz de custar
as fotos de um cliente.

## Como trabalhar aqui (não é burocracia, é cicatriz)

1. **Nada é "pronto" sem rodar e ler a saída.** Cole o número. Nunca "deve
   funcionar".
2. **Medir antes de otimizar, e antes de afirmar.** Valor não medido se escreve
   `UNKNOWN — REQUIRES EXPERIMENT`. Se disser "isso deixa mais rápido/mais leve",
   mostre os dois números.
3. **Mudou arquitetura ou dependência → ADR** em `docs/DECISIONS.md`, antes.
   Remover dependência também é mudança (ver ADR-0027).
4. **Documento que afirma estado de deploy tem que ser verificado com `curl`/
   `cat`, não relido.** Um `README` desatualizado já enganou uma sessão inteira
   (§7). Desconfie de documento, inclusive deste.
5. **Autorização nunca se infere do formato de um dado no cliente** (ADR-0025).
   Quem decide poder é o servidor; o cliente obedece.
6. **Rota que muda dado precisa de dono. Rota de leitura nunca escreve.** As duas
   já foram violadas e custaram caro (§7).
7. **Barra invertida literal em JS não passa por heredoc de shell.** Monte com
   `chr(92)` ou use a ferramenta de escrita direta. Já corrompeu o app mais de
   uma vez.
8. **Ao remover uma dependência, confira linha a linha o que estava no bloco dela
   por acaso.** `gsap.ticker.lagSmoothing(0)` morava dentro do `if (window.Lenis)`
   sem ser do Lenis, e sumir com ela travou a animação (§7).
9. **Todo overlay que cobre a tela precisa de saída que não dependa da animação
   terminar.** Senão animação quebrada = tela preta (§7).
10. **Reporte com honestidade.** Falhou é falhou, com a saída. Se eu estiver
    viajando na maionese, **me diga, com o motivo** — é para isso que você está
    aqui, e o dono pede isso explicitamente.

## O que NÃO fazer

- Não troque nem remova o login por e-mail/senha (ADR-0019). Google foi avaliado
  e **rejeitado por ora** (ADR-0026) — não reabra sem o gatilho de lá.
- Não religue o sistema de crédito (ADR-0024). Um contador religado pela metade
  bloqueia a fotógrafa **no meio de uma festa**.
- Não mexa no FTP de câmera. R8 e T6s **não têm FTP** (verificado
  presencialmente) — aquilo serve a outro perfil de cliente.
- Não invente credencial de serviço nenhum. Segredo vem do dono ou de variável
  de ambiente na VM, nunca do código — o repositório é **público**.
- Não reprocesse fotos já entregues. Mudar debaixo do pé uma foto que a
  convidada já baixou é pior que não mudar (ADR-0028).
- Não rode `tests/ensaio.py` em massa: ele cria e apaga evento **em produção**.

## Comandos

```bash
bash tests/todos.sh                                    # 4 suítes, 280 checagens
git add -A && git commit -m "..." && git push origin main   # deploy (~2 min)
curl -s https://app.foton.app.br/health                # validar depois
```
