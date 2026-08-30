# Prompt para a próxima sessão

> Cole isto numa sessão nova. Foi escrito para carregar contexto sem gastar
> tokens repetindo o que já está nos documentos, e para forçar o rigor do
> Gauntlet em vez de pedir educadamente por ele.

---

Fóton — continuação. Antes de qualquer coisa, leia nesta ordem: `BLUEPRINT.md`,
`docs/DECISIONS.md` (ADR-0019 e ADR-0025 em especial — são as duas decisões de
autenticação já tomadas) e `docs/PRODUTO.md` §3 (login por selfie — uma ideia de
login alternativa já registrada, para não colidir com ela). Não repita trabalho
que já está lá, e não confie na sua memória de treino sobre este projeto —
confie nos documentos e no código.

**Objetivo desta sessão, e só ele:** decidir se o Fóton deve oferecer "Continuar
com Google" como login para fotógrafas, e produzir essa decisão como uma ADR —
**em qualquer um dos dois sentidos**. Isto NÃO é uma sessão para implementar
OAuth por padrão; é uma sessão para investigar de verdade e decidir com
critério, documentando o porquê.

**Contexto que já existe, para você não redescobrir do zero:** hoje o login é
e-mail/senha com PBKDF2-SHA256 (120k iterações), contas são criadas por
`/signup` ou provisionadas à mão pelo dono. Ninguém jamais pediu recuperação
de senha — as três contas em produção (Patrícia, Carol, GLAMON) foram
cadastradas por ele. O público-alvo é explicitamente **não-técnico** (o
desenho Bauhaus das telas existe por causa disso) e às vezes fotografa com
**celular emprestado** — um detalhe que pesa contra OAuth, porque a sessão do
Google de outra pessoa no aparelho é mais confusa que digitar login e senha.

**As perguntas que a investigação precisa responder, com evidência, não
opinião:**
1. Que problema real o Google login resolveria **hoje**, com 3-4 contas
   provisionadas à mão? Se a resposta for "nenhum ainda, mas ajudaria um canal
   de auto-cadastro futuro", isso é válido — mas diga isso explicitamente, não
   disfarce de urgência.
2. Custo de implementação real: biblioteca (ex.: Authlib com Starlette/FastAPI
   — verificar se já é compatível com o `rig.py` atual), quantas rotas novas,
   o que muda no schema do `store.py` (uma conta pode ter senha OU Google OU
   as duas?).
3. **Onde vive o client secret do Google**, dado que o repositório é público.
   A resposta tem que ser tão rigorosa quanto a que já existe para a semente
   do FTP (`secrets.token_urlsafe`, nunca no código) — variável de ambiente na
   VM, nunca commitada, com o mesmo cuidado do ADR que criou essa disciplina.
4. O que o **dono** precisa fazer fora do código (Google Cloud Console,
   OAuth consent screen, domínio verificado) — a sessão não pode inventar um
   Client ID/Secret; se a investigação concluir que vale a pena, o produto
   desta sessão é uma lista exata de passos para ele fazer, não credenciais
   fabricadas.
5. Como isso convive com a ideia de **login por selfie** já registrada em
   `docs/PRODUTO.md` §3 — são concorrentes ou complementares?

**Critério de aceite (sem isto, não está pronto):**
1. Uma ADR nova em `docs/DECISIONS.md`, com a decisão E o porquê — mesmo que a
   decisão seja "não agora", com o gatilho que reverteria essa decisão escrito
   por extenso (ex.: "quando existir um canal de cadastro aberto ao público").
2. **Se a decisão for implementar:** um plano escrito ANTES de tocar em
   código — biblioteca escolhida e por quê, onde o secret mora, o que muda no
   schema, e como uma conta com senha continua funcionando exatamente igual
   (Google é ADIÇÃO, nunca substituição do login atual).
3. **Se implementar:** as 4 suítes (`tests/todos.sh`) passando antes de
   qualquer deploy, e teste manual em produção do login antigo continuando
   igual — não presuma que não quebrou.
4. **Se NÃO implementar:** a sessão ainda entrega valor — a ADR de rejeição
   documentada é o produto, não uma desculpa para não fazer nada.

**Não faça nesta sessão, mesmo que pareça tentador:** não troque nem remova o
login por e-mail/senha atual. Não mexa no sistema de crédito (foi cortado em
2026-08-30, ADR-0024 — deixe cortado). Não mexa no FTP de câmera. Não invente
um Client ID/Secret do Google só para "mostrar que funciona" — sem credencial
real do Console do dono, o máximo que dá para entregar é o código pronto para
receber a credencial, nunca uma credencial de teste guardada no repo.

**Regras de trabalho (valem sempre):**
- Nada é "pronto" sem rodar e ler a saída. Cole o número/a saída.
- Não quebre o que funciona: teste o caminho inteiro depois de mexer.
- Suposição não medida se escreve `UNKNOWN — REQUIRES EXPERIMENT`.
- Mudou arquitetura ou dependência → ADR em `docs/DECISIONS.md` (esta sessão
  inteira É uma ADR, ver acima).
- Se eu estiver viajando na maionese, me diga, com o motivo.
- Deploy é `git push` (VM se atualiza em ~2 min). Infra exige Cloud Shell.
- Deploy com evento ao vivo está **liberado** nesta fase de teste (decisão do
  dono, 2026-08-30) — use bom senso para o que é "coisa grande" (ver
  `BLUEPRINT.md` §5) e cheque `/admin/saude` antes na dúvida.
- Barra invertida literal em string JS não passa por heredoc de shell — monte
  com `chr(92)` ou use a ferramenta de escrita de arquivo direta.

---

## Por que este prompt é assim

- **O objetivo é "decidir com uma ADR", não "implementar".** A pergunta do
  dono foi genuinamente aberta ("isso nos ajudaria ou atrapalharia?") — dar a
  ele uma implementação sem essa reflexão seria responder a uma pergunta
  diferente da que ele fez.
- **Lista perguntas concretas em vez de um objetivo vago de "avaliar".** Sem
  isso, o agente troca investigação por opinião — exatamente o que eu fiz na
  hora, rápido, sem pesquisa real, na sessão que escreveu este prompt.
- **Proíbe fabricar credencial do Google.** É a mesma lição do FTP: segredo
  nunca inventado, nunca commitado, sempre vindo do dono ou de variável de
  ambiente.
- **Autoriza explicitamente a resposta "não agora".** Uma ADR de rejeição bem
  fundamentada é tão válida quanto código novo — e evita a pior falha de um
  agente: implementar algo só porque foi perguntado, sem checar se deveria.
