# IDEIAS-V2.md — Backlog avaliado para a versão 2

> **Origem:** avaliação externa entregue ao dono em 2026-08-30 (27 ideias + priorização),
> preservada íntegra na Parte B. A Parte A é a **análise de expert do próprio Fóton**,
> feita sobre o código real (schema, rotas, ADRs), **sem viés de confirmação** — o objetivo
> é o dono poder apresentar v2 sem passar vergonha, então onde a avaliação erra a mão,
> está corrigido aqui.
> **Status:** registro para retomar. Nada aqui é decisão nem foi construído. Antes de
> qualquer item virar código: declarar entidades, migração, LGPD, testes e rollback
> (regra do CLAUDE.md), e passar pelo gauntlet.

---

## Parte A — Análise do Fóton (grounded no código)

### A.0 O elefante que a avaliação NÃO viu: armazenamento

As fotos são gravadas como **BLOB dentro do SQLite** (`photo.bytes BLOB`, [store.py:24](../app/test_rig/store.py)).
O GLAMON já despejou ~2000 fotos de 2000×2000 nesse banco. **Isto é o gargalo real, não a
falta de features.** Toda ideia "durante + depois" (galerias que persistem, replay, ZIP com
tudo, memória permanente em escala) empilha em cima de um armazém que não escala e de um
backup que cresce com cada foto.

**Regra de sequência que a avaliação deveria ter dito:** a migração para R2 (object storage,
já sinalizada no plano) é **pré-requisito** de #12 (pós-evento), #25 (Replay), #26 (Memory em
escala) e do ZIP organizado com originais. Apresentar essas ideias sem dizer "dependem do R2"
é overpromise.

### A.1 O que a avaliação SUPERESTIMA em facilidade (risco de vergonha)

| Ideia | Nota dela | Realidade no código | Correção honesta |
|---|---|---|---|
| **Telão / Live Wall (#1, #27)** | "Baixa" / aposta #1 | O feed existe; render é trivial | **Não é problema técnico, é de LGPD (§7).** Jogar rostos de todo mundo numa TV — ainda mais "permanente no GLAMON" — é dado biométrico sensível fora do escopo de consentimento efêmero que é a espinha do produto. Baixa em código, **NÃO baixa em consentimento/retenção**. É também a maior superfície de vergonha: um telão que trava na frente da festa. Precisa de: feed do EVENTO (não o pessoal), moldura de consentimento, e um modo "só quem aceitou aparecer no telão". |
| **Analytics (#3)** | "Baixa" | Metade é grátis: convidados (`guest`), fotos (`photo`), fotos por convidado (`match`), taxa de identificação (`n_faces>0` vs `match`). **A outra metade NÃO existe:** downloads, compartilhamentos, favoritos, horário de pico — **não há tabela de eventos/telemetria de produto.** Os logs (§6) são de ops (latência), e §7 proíbe PII neles. | Metade "baixa", metade exige **nova instrumentação** (uma tabela `evento_uso`). Dizer "Analytics é barato" inteiro é errado. |
| **Álbuns dentro do evento (#4)** | "Média" | `photo` não tem `album_id`. E o fluxo é **câmera → sobe sozinho**: a câmera não sabe em qual álbum a foto entra. | Roteamento no ingest é o problema real, não o schema. "Cerimônia/Recepção" pode ser por **horário** (barato); "GLAMON: Clientes/Equipe/Campanhas" é mais **tag/categoria** que álbum de captura. Média é otimista para o caso câmera. |
| **Moderação Fiesta (#6)** | "Baixa/média" | `photo` não tem `status`. | Adicionar `pending\|published\|rejected` **coloca um humano no caminho crítico** e briga com a promessa "na hora" (P95<10s). É decisão de PRODUTO, não `photo.status = simples`. Necessário para uploads de convidado, mas precisa de um desenho que não mate o "ao vivo" (ex.: auto-publica + remove depois, ou fila só para o Festa). |
| **WhatsApp (#10)** | "Média" ⭐⭐⭐⭐⭐ | O telefone **já é coletado** (`contact.contato`). | Entrega por WhatsApp = **WhatsApp Business API (Meta) + BSP + templates aprovados + opt-in + custo por mensagem + base legal de outreach ativo (LGPD).** Isso é **alta** operação/dependência, não "média". A própria avaliação diz "depois do piloto" — instinto certo, nota errada. |

### A.2 O que JÁ EXISTE ou JÁ foi decidido (não apresentar como novo)

- **#2 Favoritos** — o coração já está desenhado (PRODUTO §3d, item 3 do plano atual, ainda
  não construído). Favoritos = coleção persistente = **1 tabela nova `guest↔photo`**. Aqui a
  avaliação acerta: baixo de verdade. É a extensão natural do coração.
- **#5 Reencontro por selfie** — **CONFIRMADO** (P1), desenhado, falta o experimento de
  limiar. Já está no plano.
- **#13 Busca por pessoa** — **já É a tabela `match`** (`matches_de(gid)`). Para o convidado
  é "minhas fotos". Para o fotógrafo, "fotos da Ana" é uma consulta sobre dado que já existe.
- **#14 Busca por nº de pessoas** — `n_faces` **já vem em `/photos`** ([rig.py:524](../app/test_rig/rig.py)).
  É o item 2 do plano, quase pronto (falta o seletor client-side).
- **#26 Fóton Memory (histórico GLAMON)** — o schema **já suporta retenção permanente**
  (`photographer.ret_bio_dias = 0`, [store.py:55](../app/test_rig/store.py)). A fundação de dados existe. É P1 com biometria permanente.
- **#11 Pré-evento** — item 9-b do plano (falta `photo.oculta`). Já mapeado.
- **#17 White-label** — a base existe: `event.marca` e `photographer.logo`. Falta o "tirar o
  Fóton da frente" completo (domínio próprio etc.), mas branding por conta já roda.
- **#5/#7 Colaboradores** — existe uma versão **crua**: conta **EMPRESA = login compartilhado
  pela equipe** ([store.py:57](../app/test_rig/store.py)). Não é RBAC (é senha compartilhada). Formalizar papéis é o upgrade.
- **Vídeo (o que ela NÃO colocaria)** — concordo e o ROADMAP/DECISIONS já colocam vídeo em
  pós-MVP. Ponto para a avaliação.

### A.3 Onde eu DISCORDO da priorização dela (sem viés)

1. **Live Wall como aposta nº1 — discordo da ordem, não do valor.** O argumento ("o produto
   vira propaganda no evento") é real e forte para viralização. Mas: (a) é **a feature mais
   copiável** — GuestCam já tem; (b) o risco de LGPD e o risco de vergonha (travar na frente
   de gente) são máximos; (c) o valor concentra-se em eventos com tela e plateia (GLAMON na
   TV, casamento com telão) — fraco para a fotógrafa solo. Faria como **centro do v2**, depois
   de uma v1.1 estável, e **com a moldura de consentimento antes do brilho.**

2. **Fóton Memory está subvalorizado (ela põe #10; eu poria no topo estratégico).** Não é o
   mais vistoso, é o mais **defensável**: reconhecimento facial é commodity (o próprio
   Blueprint diz isso), telão é copiável — mas **memória facial permanente atada à relação do
   salão** (a cliente volta, tira selfie, reencontra o histórico) é recorrência e retenção, e
   o schema já está pronto para isso. É a única ideia da lista que pode virar **categoria
   própria** em vez de mais uma opção no painel.

3. **Estabilidade antes de espetáculo.** "Não posso passar vergonha" empurra para: fechar
   primeiro o que já está 80% pronto (n_faces sort, coração, reencontro, teto da galeria — já
   feito) e o Analytics-grátis, entregando uma **v1.1 sólida**; só então a vitrine (Live Wall).

### A.4 Consolidação — sequência honesta

- **v1.1 (estabilizar e fechar o que existe), risco baixo, sem R2:**
  teto da galeria (✅ feito), sort por data/pessoas (#14, quase pronto), coração/favoritos
  (#2), reencontro por selfie (#5), Analytics-grátis (metade de #3), link curto + página do
  evento (#7, #8 — baixo e sem biometria), `photo.oculta` para pré-cadastro (#11).
- **v2 (vitrine e vendabilidade), exige desenho de consentimento e/ou R2:**
  Live Wall com moldura de consentimento (#1/#27), álbuns por horário/tag (#4), moderação do
  Festa sem matar o "na hora" (#6), colaboradores/RBAC formal (#5/#7), white-label completo
  (#17).
- **v2+ (dependem de R2 e/ou custo externo):**
  pós-evento automático (#12), Replay (#25), Memory em escala (#26 além do que o schema já
  dá), WhatsApp (#10).
- **Fora por ora (concordo com a avaliação):** vídeo; "momentos" por IA de visão (#24);
  ranking obrigatório (#22, cuidado com gamificação forçada).

---

## Parte A-bis — A lista do DONO (infra/confiabilidade) — e por que ela vem primeiro

> O dono respondeu à avaliação externa com 12 itens de **confiabilidade**, não de feature.
> **Concordo, e essa lista tem precedência.** Razão: a lista de features aumenta
> *superfície*; esta aumenta *confiança*. O critério declarado dele é "não posso passar
> vergonha" — e vergonha não vem de faltar telão, vem de travar na festa sem saber por quê.

| # | Item do dono | Estado real no código | Veredito |
|---|---|---|---|
| 1 | Observabilidade real (erros/rota, latência, fila, CPU, memória) | logs JSON por foto existem; **nada agrega**. `/admin/saude` já lê mem/disco | Parcial → **fazer** |
| 2 | Métricas de TTFR (provar os <10 s) | latência era logada e **ninguém somava** | ✅ **FEITO** (`/admin/latencias`, P50/P95/P99) |
| 3 | Health específico do pipeline | `/health` devolvia **3 constantes**; dizia ok com o banco no chão | ✅ **FEITO** (bate no banco + estado do motor) |
| 4 | Fila explícita (recebido→processando→identificado→entregue) | não existe; o ingest é síncrono | **Adiar** — hoje é síncrono e simples; fila é complexidade que só se paga quando houver concorrência real. Ver crítica abaixo |
| 5 | Idempotência de ingestão | **ausente** (`uuid` novo a cada upload) — mesma foto virava 2 linhas, 2 processamentos, 2 cópias na galeria | ✅ **FEITO** (`photo.sha`) |
| 6 | Retentativa inteligente (celular ruim) | o app tem retry? **a idempotência era o pré-requisito** — sem ela, retry duplica | **Próximo** — agora é seguro |
| 7 | Capacidade por evento (GLAMON gigante não mata os outros) | não existe limite por evento | **Fazer** (depois do R2) |
| 8 | Storage fora do SQLite (R2) | fotos são `photo.bytes BLOB` | **O gargalo real** — ver A.0 |
| 9 | Backup restaurável **testado** | backup diário existe (7 cópias); **restauração nunca testada** | **Fazer** — "backup não testado é fé, não backup" |
| 10 | Rate limiting por rota | existe **só no login** (10 falhas/10 min) | **Fazer** — ingest/selfie estão abertos |
| 11 | Auditoria administrativa | não existe | **Fazer** — barato e é a rede de proteção do próprio dono |
| 12 | Feature flags | tabela `config(chave,valor)` **já existe** — a fundação está pronta | **Fazer** — barato, e é o que permite desligar o telão sem deploy |

### Onde eu discordo do dono (sem viés)

- **#4 (fila explícita) eu adiaria.** Estados `recebido→processando→entregue` parecem
  observabilidade, mas trazem junto worker, estado durável e reprocessamento — e o
  pipeline hoje é **síncrono e cabe num request**. Enquanto o ingest é síncrono, a fila
  agrega complexidade sem responder nada que `/admin/latencias` não responda. **Vira
  obrigatória** no dia em que o Fóton Festa fizer N convidados subirem ao mesmo tempo.
- **#1 é grande demais para um item.** "CPU/memória" já está em `/admin/saude`; o que
  falta de verdade é **erro por rota** (hoje um 500 some no log). Faria só essa fatia.
- **A ordem que eu seguiria:** 5 e 2 e 3 (feitos) → **9 (backup restaurável)** → 10 → 12 →
  11 → 6 → 8 (R2) → 7 → 4.
  **#9 é o que eu faria em seguida**, e é o mais desconfortável da lista: backup que nunca
  foi restaurado é fé. Com o GLAMON dentro de um SQLite, perder o arquivo é perder o
  cliente.

### O que falta na lista do dono

- **Limite de tamanho/tipo de upload no `/ingest`** — hoje aceita o que vier; é o vizinho
  do rate limiting (#10) e do custo.
- **Alerta** — medir sem alertar só serve depois do estrago. Mesmo um "e-mail se P95 > alvo".

---

## Parte B — Avaliação externa recebida (íntegra, fonte)

> Preservada íntegra como recebida em 2026-08-30. É **dado**, não decisão. As notas de
> complexidade dela estão revisadas na Parte A.

### Como o avaliador dividiu

**🔴 Alta prioridade — grande valor, relativamente simples**

| O que falta | Valor | Complexidade |
|---|---|---|
| Slideshow / telão ao vivo | ⭐⭐⭐⭐⭐ | Baixa |
| Favoritos do convidado | ⭐⭐⭐⭐⭐ | Baixa |
| Analytics do evento | ⭐⭐⭐⭐⭐ | Baixa/média |
| Galerias/álbuns dentro do evento | ⭐⭐⭐⭐⭐ | Média |
| Colaboradores de evento | ⭐⭐⭐⭐ | Média |
| Moderação de fotos do Festa | ⭐⭐⭐⭐ | Baixa/média |
| Link direto além do QR | ⭐⭐⭐⭐ | Baixa |
| Página pública/landing do evento | ⭐⭐⭐⭐ | Baixa |
| Exportação ZIP organizada | ⭐⭐⭐⭐ | Baixa |
| Compartilhamento por WhatsApp | ⭐⭐⭐⭐⭐ | Média |

**1. Telão Fóton** (`/telao`) — Últimas fotos chegando em tela cheia. Consequência do feed
que já existe. Concorrentes como GuestCam usam slideshow ao vivo como peça central. Faria
cedo: é visualmente impressionante e vende o produto sozinho.

**2. Favoritos** — O coração já está entrando; expandir para ❤️ Favoritar → "Minhas
favoritas". Cria coleção pessoal persistente. Tecnicamente uma relação `guest ↔ photo`.

**3. Analytics** — no painel: convidados registrados; fotos processadas; fotos entregues;
fotos por convidado; downloads; compartilhamentos; favoritos; horário de maior movimento;
taxa de identificação. Concorrentes tratam analytics como recurso comercial.

**4. Álbuns dentro de um evento** — ex. CASAMENTO → Cerimônia / Recepção / Festa / Making of;
ou GLAMON → Clientes / Equipe / Eventos / Campanhas. GuestCam usa hierarquia de
galerias/subgalerias. O modelo já tem `evento`; criar `album` embaixo é extensão natural.

**5. Colaboradores** — hoje só "dono do evento". Poderia virar Patrícia → assistente / editor;
ou GLAMON → proprietário → gerente / equipe. RBAC simples sem compartilhar senha. Feature B2B.

**6. Moderação** — especialmente Fiesta. Antes de a foto do convidado aparecer para todos:
Automática / Aprovar antes. GuestCam oferece esse controle. `photo.status = pending |
published | rejected`.

**7. QR + URL curta** — não obrigar a escanear. Ex. `foton.app.br/festa/ana`. QR = interface
física; URL = interface digital.

**8. Página do evento** — landing simples: "Ana & João / 12/09/2026" → [Entrar na galeria] /
[Enviar minhas fotos] / [Encontrar minhas fotos]. Ótimo para Fiesta.

**9. ZIP realmente organizado** — `Festa_Ana/ Todas/ Minhas_fotos/ Favoritas/ 2026-09-12/`.
Baixo custo, sensação de produto acabado.

**10. WhatsApp** — potencial comercial enorme no Brasil. "Suas fotos chegaram." / "Você
apareceu em 37 fotos." → WhatsApp. SpotMyPhotos já distribui por WhatsApp/SMS/email/AirDrop.
Deixaria depois do piloto (custo operacional + dependência externa).

**🟠 Segunda camada — muito interessante**

**11. Pré-evento** — "O Fóton estará no evento sábado. Cadastre-se agora." Selfie antes, chega
pronto. SpotMyPhotos trabalha com registro pré e pós-evento. Ótimo para casamento.

**12. Pós-evento automático** — "Você apareceu em 47 fotos." Link → galeria pessoal.
Transforma o Fóton de ferramenta durante em durante + depois.

**13. Busca por pessoa** — já haverá `guest → match → photos`; "Mostrar fotos de Ana" é
consulta sobre dado existente.

**14. Busca por quantidade de pessoas** — já implementando `n_faces`: 1 / 2 / 3+ pessoas.
Excelente para GLAMON.

**15. Filtros inteligentes** — data; pessoas; favoritas; minhas; equipe; álbum; mais recentes.
Pouco esforço depois que o modelo amadurecer.

**16. Download seletivo para fotógrafo** — selecionar 34 fotos → ZIP; ou "todas as fotos com
Ana". Comercialmente útil.

**17. Marca branca / white-label** — hoje existe a pele do Fóton; depois "Patrícia Vargas
Fotografia" sem Fóton em primeiro plano. Fóton como infraestrutura invisível.

**🟡 Terceira camada — boas ideias, mas não agora**

**18. QR por álbum** — QR Cerimônia / QR Festa / QR Making of.
**19. Convite digital integrado** — "Encontre suas fotos no Fóton." Ótimo para aquisição.
**20. Cartões QR prontos para impressão** — fotógrafo escolhe tipo (casamento/aniversário/
corporativo/festa); Fóton gera QR + instrução + logo + layout de impressão.
**21. Tela de espera personalizada** — "As próximas fotos podem ser suas." com animação/branding.
**22. Ranking / estatísticas da festa** — 📸 Ana 83 / João 51 / Maria 37. Cuidado com
competição obrigatória; como estatística divertida funciona.
**23. Timeline do evento** — 19:00 → 22:00 com fotos aparecendo; visualização do feed.
**24. "Momentos" automáticos** — agrupar Pessoas / Grupos / Pista / Mesa / Cerimônia. IA de
visão além do facial. Só depois.

**🟣 Três que ele acha particularmente interessantes**

**25. Fóton Replay** — "Veja como foi sua festa." Timeline automática com as melhores fotos.
Experiência pós-evento, não só galeria.
**26. Fóton Memory** — para GLAMON: "Você voltou." Nova selfie → histórico → fotos antigas.
Transforma a galeria permanente em produto de relacionamento. Uma das que ele mais exploraria.
**27. Fóton Live Wall** — não só slideshow: uma tela viva do evento (grade de fotos + "142
fotos / 38 pessoas / AO VIVO"), cada foto nova entra. Poderia ficar na TV do GLAMON
permanentemente.

**O que ele NÃO colocaria:** Vídeo. Concorrentes suportam (GuestCam aceita foto+vídeo e
slideshow de ambos), mas vídeo = armazenamento + processamento + thumbnails + streaming +
reconhecimento + R2 + custos + UX. Não é preciso para provar a tese.

**Se tivesse que escolher só 10 (ordem dele):**
1. Fóton Live Wall / Telão · 2. Favoritos · 3. Analytics · 4. Álbuns · 5. Reencontro por
selfie · 6. Moderação Fiesta · 7. Colaboradores · 8. Pós-evento automático · 9. WhatsApp ·
10. Fóton Memory / histórico GLAMON.

Lógica dele: 1–4 aumentam o valor do produto atual; 5 cria capacidade proprietária; 6–7
tornam o Fiesta vendável; 8–9 aumentam retenção/distribuição; 10 pode criar categoria própria.

**Aposta mais forte dele:** Fóton Live Wall — "o próprio produto vira propaganda durante o
evento" (convidado vê a foto chegar → alguém pergunta → aponta para o QR → distribui sozinho).
