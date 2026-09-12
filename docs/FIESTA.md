# FIESTA.md — Plano da Foto'n Fiesta!

> **Plano, não código.** Escrito em 2026-09-11 a pedido do dono ("planejar a criação do
> modo Foto'n Fiesta — melhores práticas, tecnologias e funcionalidades"). Regras de
> produto já decididas vivem em `docs/PRODUTO.md` §2; este documento diz **como** fazer,
> **em que ordem**, **o que falta medir** e **o que ainda é decisão do dono**.
> Regra do projeto: nada aqui vira código sem ADR antes (CLAUDE.md §4.3/§4.5).
>
> **Estado em 2026-09-12: pronto para ADR e medição — não pronto para construir.**
> Faltam três números (§7) e um parecer jurídico (§6.4). Revisado por fora em 12/09, com o
> mesmo veredito. **Proposta de implementação** (aguardando aprovação):
> `docs/FIESTA-IMPLEMENTACAO.md`.

---

## 0. Em uma tela

**O que é.** Uma festa em que **todo mundo é fotógrafo e convidado ao mesmo tempo**. A
Ana (conta `social`) cria a festa e projeta o QR. Cada convidado faz a selfie de sempre,
fotografa com o próprio celular, e **cada foto chega sozinha no celular de quem aparece
nela** — de quem quer que a tenha tirado. Durante a festa, não no dia seguinte.

**Por que dá para ganhar.** Os concorrentes de "foto de convidado por QR" (GuestCam,
Kululu, POV, PartyCam e outros — §2) fazem um **álbum coletivo**: todo mundo vê tudo e
cada um procura as próprias fotos. **Nenhum dos 12 comparados entrega a foto certa na
pessoa certa por rosto e de graça, e nenhum tem filtro automático de conteúdo** — todos
moderam com "o anfitrião apaga depois". O Fóton já tem os dois motores.

**O maior risco não é feature, é capacidade.** Uma festa de 100 convidados pode mandar
milhares de fotos, e concentradas nos mesmos minutos (parabéns, primeira dança). A VM de
hoje tem **1/8 de OCPU** e guarda foto **dentro do SQLite**. A Fiesta é o dia em que a
"fila explícita", o ARM gratuito e o R2 deixam de ser opcionais (§5.4).

**Ordem proposta:** fechar os pré-requisitos (limites de upload, flags) → 3 ADRs + 3
experimentos → backend → front → **piloto fechado com uma festa pequena da Ana** → v2
(telão, revelação). §7.

**O que é seu.** Em 2026-09-12 o dono fechou tudo menos uma: peito masculino passa, ânus
bloqueia, **só a dona libera** foto retida, a foto é **assinada** por quem enviou, quem
**sai da festa deixa as fotos**, **telão fica para a v2** — e, depois de decidir que
crianças entrariam, **voltou atrás no mesmo dia: a v1 é só para maiores** (§6.2, e leia lá
o que isso *não* significa). Resta **uma** decisão: o preço. O desenho para crianças fica
guardado, esperando **parecer jurídico** (§6.4).

---

## 1. Regras de produto já decididas (PRODUTO §2 — não reabrir)

| # | Regra | Como vira sistema |
|---|---|---|
| 1 | **50 fotos por participante** ("inicialmente") | contador por **sessão de convidado**, **nunca por IP** (numa festa o Wi-Fi é um só) |
| 2 | Participante **apaga a própria foto**, exceto se tiver **mais de um rosto** | botão só aparece em foto **dele** com `n_faces <= 1`; nas outras, "pedir remoção" ao dono |
| 3 | Conteúdo: **genitália e mamilo não; bunda pode; decote e vestido passam** | classificador por **parte do corpo**, não "nudez" genérica (§5.3) |
| 4 | É a versão da Ana: **ela E os convidados** enviam | papéis por evento: `dono` e `participante` |
| 5 | Interface sem nada de câmera profissional | pele `social` (ADR-0030) — já esconde câmera/FTP |

---

## 2. O mercado em 2026 — o que os outros fazem

Fonte principal: comparação de 12 apps publicada pela PartyCam, que é concorrente — ler
com esse viés ([partycam.app](https://partycam.app/blog/best-qr-code-wedding-photo-apps-2026)).

| Recurso | Quem tem | Como é neles | O que isso diz para nós |
|---|---|---|---|
| Entrar sem instalar (QR → câmera no navegador) | quase todos | padrão de mercado | **já temos** (PWA) — é o mínimo, não diferencial |
| Limite de fotos por convidado ("câmera descartável") | PartyCam, POV, Lense (25), Disposable (10 grátis) | o anfitrião escolhe | nossas **50** estão na faixa; o número pode virar configurável |
| Revelação atrasada ("vê amanhã", efeito filme) | PartyCam, POV, Once, Lense | opcional | é **o oposto** do nosso "na hora" — só como opção de v2, se o dono quiser |
| Telão / slideshow ao vivo | Kululu, PixelParty, Wedbox | forte em casamento | v2, **com moldura de consentimento** (IDEIAS-V2 A.1) |
| Moderação | **todos: só "anfitrião apaga"** | nenhum filtro automático citado | **lacuna aberta** — nós temos como filtrar antes de publicar (§5.3) |
| Achar as próprias fotos por rosto | **só GuestCam, pago à parte (+US$45)** | busca manual por selfie | nós **entregamos sozinho, ao vivo, sem custo extra** — é o motor |
| ZIP com os originais | quase todos | incluso ou pago | v2 (depende do R2, IDEIAS-V2 A.0) |
| Preço | US$ 2–150 por evento | por número de convidados | modelo comercial: decisão do dono (§8) |

Afirmação de mercado que vale registrar como **alegação, não medição**: apps que exigem
instalar perderiam 40–60% dos convidados na tela da loja
([Guesticon](https://guesticon.com/blog/guests-upload-wedding-photos-qr-code-2025)).
Coerente com a nossa decisão de PWA, mas não medido por nós.

---

## 3. O que já existe e a Fiesta reaproveita

- QR → **1 selfie** → galeria que enche ao vivo, com abas **minhas / todas**.
- **Câmera no app** com fallback nativo; **fila IndexedDB** que sobrevive a fechar o app;
  retentativa; **idempotência** (`photo.sha` — foto reenviada não duplica).
- **Redução no celular antes de subir** (`reduzir()`, 2048 px, `index.html:2022`): a foto de
  convidado já chega leve.
- "Compartilhar" do Android direto para o app (ADR-0018).
- `n_faces` por foto — é o que decide o botão de apagar (regra 2).
- Pele `social` reservada e atribuível (ADR-0030) — a "casca" da Fiesta já tem lugar.
- **Limiar de entrega 0,40 e selfie pelo maior rosto (ADR-0034, 2026-09-11).** Crítico aqui:
  a Fiesta multiplica as fotos e os parecidos. No 0,25 antigo, cada foto de grupo era uma
  loteria de estranho parecido — com milhares de fotos de convidado, virava certeza.

---

## 4. Funcionalidades

### 4.1 MVP (Fiesta v1) — o mínimo que prova a ideia sem passar vergonha

**Para o participante (convidado):**
1. Selfie de sempre (consentimento já existe) → vira participante.
2. Botão **Fotografar / Enviar da galeria**, com contador visível **"12 de 50"**, e o
   estado de cada envio — inclusive **"em análise"** quando o filtro reteve (§5.3).
   A selfie da Fiesta pede um **apelido**, porque a foto enviada é assinada (decisão 5).
3. As fotos em que ele aparece chegam sozinhas — de qualquer autor, **assinadas pelo
   apelido de quem enviou** (decisão 5: vira crédito e diversão, e inibe quem pensar em
   mandar bobagem).
4. Aba **Todas**: a festa inteira (só fotos **publicadas**).
5. Apagar a **própria** foto, se ela tiver no máximo 1 rosto. Nas outras, **"Pedir remoção"**.
*(Registrar criança sob responsabilidade **saiu da v1** — decisão do dono, 2026-09-12,
§6.2. O desenho está pronto e espera parecer jurídico.)*

**Para a dona da festa (Ana):**
1. Criar festa → QR (existe).
2. Ver tudo e apagar qualquer foto (existe para a dona).
3. **Fila de retidas**: foto que o filtro segurou só aparece para ela, com "publicar" ou
   "apagar".
4. **Pedidos de remoção** dos participantes.
5. Resumo no fim: fotos enviadas, participantes, retidas, removidas.

**Fora do MVP, de propósito:** telão, revelação atrasada, reações, ZIP, vídeo e número de
fotos configurável (§8). A autoria visível **entrou** no MVP (decisão 5).

### 4.2 v2 — depois de uma festa real

- **Telão / slideshow** do evento, só com quem aceitou aparecer (moldura de consentimento
  antes do brilho — IDEIAS-V2 A.1/A.3).
- **Revelação atrasada** como modo opcional ("modo filme"), se o dono quiser — contraria o
  "na hora" e por isso nunca é o padrão.
- **Coração/favoritos** (PRODUTO §3d) e **ZIP da festa** para a dona (depende do R2).
- Limite de fotos por participante **configurável pela dona**.

---

## 5. Arquitetura e tecnologia

### 5.1 Modelo de dados — declarado ANTES, como manda o projeto

Padrão da casa: `ALTER` guardado, **NULL = comportamento idêntico ao de hoje**.

| Mudança | NULL significa | Para quê |
|---|---|---|
| `event.modo TEXT` (`'fiesta'`) | evento normal (fotógrafa) | liga as regras da Fiesta **por evento**, testável, sem depender de inferir pelo perfil da conta |
| `photo.autor_guest TEXT` | foto da fotógrafa/dona | contar as 50, e saber quem pode apagar |
| `photo.status TEXT` (`'retida'`, `'removida'`) | **publicada** (hoje) | moderação sem apagar dado — a dona decide |
| `photo.moderacao TEXT` (JSON: classes, scores, **versão do modelo e da política**, sem PII) | não passou por filtro | auditar falso positivo, calibrar limiar, e explicar por que a mesma foto passaria hoje e seria retida amanhã (invariante 6) |
| `guest.token TEXT` | convidado só lê (hoje) | **credencial de escrita** separada do `guest_id` (§5.5) |
| `guest.responsavel TEXT` | é um adulto que se cadastrou sozinho | **criança registrada por um responsável** (§6.2): guarda o `guest_id` de quem autorizou. Entrega vai para a galeria dele |
| `guest.apelido TEXT` | sem rótulo | duplo uso: como a criança aparece na galeria do responsável ("fotos da Manu") **e** como o autor assina a foto que enviou (decisão 5). Apelido, nunca nome completo — e na Fiesta ele deixa de ser opcional: sem apelido não há como assinar |
| `guest.consent_resp TEXT` (JSON: quando, versão do texto em destaque) | não se aplica | prova do consentimento do art. 14 §1, que é requisito de forma |
| tabela `pedido_remocao(event, photo_id, guest_id, ts, status)` | — | regra 2 |

- **Migração:** tudo aditivo; nenhuma linha antiga muda de significado.
- **LGPD:** `autor_guest` liga foto a participante — entra na mesma retenção do evento
  (ADR-0029). `moderacao` guarda só classe e score, nunca recorte.
- **Rollback:** colunas NULL são ignoradas pelo código antigo; `git revert` volta ao hoje.
- **Testes:** cada regra do §1 vira checagem de contrato (autorização sempre no servidor —
  BLUEPRINT §6.7).

### 5.2 Rotas novas (esboço — o contrato fecha na ADR)

| Rota | Quem | Regra |
|---|---|---|
| `POST /fiesta/enviar` | participante (token) | evento em modo fiesta; < 50 dele; tipo/tamanho válidos; passa pela moderação |
| `POST /fiesta/apagar` | participante | só foto **dele**, só com `n_faces <= 1` |
| `POST /fiesta/pedir-remocao` | participante | registra pedido para a dona |
| `GET /fiesta/retidas` · `POST /fiesta/moderar` | dona | publicar ou apagar retida |

O `/ingest` da fotógrafa **não muda**. Rota que muda dado exige dono ou token — lição paga
(BLUEPRINT §7, "rotas destrutivas sem dono").

### 5.3 Moderação: filtro por PARTE DO CORPO, antes de publicar

> **ATUALIZAÇÃO 2026-09-12 — o NudeNet saiu.** Repositório e pesos são AGPL-3.0 (correção
> abaixo), e o dono pediu licença permissiva. **Candidato atual: cascata Marqo (Apache-2.0)
> → Freepik (MIT)**, medida nas mesmas 80 fotos: **0 retenções indevidas, 252 ms por foto**
> num núcleo. Os dois julgam a imagem inteira, mas o Freepik separa sugestivo de explícito.
> Pendências antes da ADR: exportar para ONNX e medir memória na VM, e testar traje de
> banho/piscina. Detalhe em `FIESTA-IMPLEMENTACAO.md` §3.4 e no BENCHMARKS. A tabela de
> classes abaixo continua valendo **como regra**; o que muda é o modelo que a aplica.

**Candidato original (substituído): NudeNet 3.4.2** ([PyPI](https://pypi.org/project/nudenet/)) —
detector YOLOv8n de 320 px em **ONNX** (roda no `onnxruntime`, que o projeto já usa),
modelo de **12,2 MB**.

> ⚠️ **CORREÇÃO DE LICENÇA (2026-09-12) — este documento dizia "licença MIT", e está errado
> para o que importa.** O **pacote** Python se declara MIT. Mas o **arquivo do modelo**
> (`320n.onnx`) traz nos próprios metadados, lidos com `onnx.load`:
> `author = Ultralytics` · `version = 8.2.46` · `description = Ultralytics best model trained
> on data.yml` · **`license = AGPL-3.0`**. A Ultralytics declara que modelos treinados com
> o código dela ficam sob AGPL-3.0, cuja exigência para serviço acessível pela rede é
> disponibilizar o código-fonte correspondente da aplicação.
> **Consequência para o Fóton:** o repositório já é público, o que pode atender a exigência
> — mas **fecha a porta de torná-lo privado** (BLUEPRINT §9, item 10) sem licença comercial
> da Ultralytics ou troca de modelo. É decisão de negócio e de advogado, **antes** da ADR de
> moderação. O "conferir a licença dos pesos antes da ADR" abaixo não era formalidade: ele
> pegou isso. O que o torna certo para a regra do dono: ele não diz
"nudez sim/não", ele devolve **partes do corpo, cobertas ou expostas**:

| Regra do dono | Classe | Ação |
|---|---|---|
| mamilo não | `FEMALE_BREAST_EXPOSED` | **retém** |
| genitália não | `FEMALE_GENITALIA_EXPOSED`, `MALE_GENITALIA_EXPOSED` | **retém** |
| ânus não | `ANUS_EXPOSED` | **retém** — decidido pelo dono em 2026-09-12 |
| decote passa | `FEMALE_BREAST_COVERED` | publica |
| bunda pode | `BUTTOCKS_EXPOSED` / `_COVERED` | publica |
| peito masculino (piscina) passa | `MALE_BREAST_EXPOSED` | **publica** — decidido pelo dono em 2026-09-12 |

**Medido em 2026-09-11** (`tests/experimento_moderacao.py`, BENCHMARKS): nas 80 fotos
reais de festa, **0 retenções indevidas** mesmo com confiança ≥ 0,3; o modelo marcou
**90 decotes como `COVERED`**, que é exatamente a distinção pedida. Custo: **181 ms por foto
(p50) contra 702 ms do reconhecimento facial**, num núcleo só — a moderação soma ~26% ao
que o pipeline já gasta com rosto.

**Desenho: publica na hora, ou retém — nunca "publica e apaga depois".** Filtro no
caminho, antes da entrega: foto limpa segue direto (mantém o "na hora"); foto com classe
bloqueada fica `retida`, **invisível para todos menos a dona**, até ela decidir.

**Quem libera é só a dona, quando puder olhar** (decisão do dono, 2026-09-12). Isso tem um
efeito colateral que precisa de tela: numa festa ela **não** vai estar olhando o celular, e
a foto pode ficar retida até o dia seguinte. Então **quem enviou tem que ver "em análise"**,
com o motivo em linguagem humana — senão ele acha que o envio falhou e manda de novo (e a
idempotência vai devolver a mesma foto retida, o que parece um bug e não é). É o
meio-termo da tensão de IDEIAS-V2 A.1: humano **só** no caminho da foto suspeita.
"Publicar e remover depois" foi descartado: numa festa, 10 segundos de foto imprópria na
galeria de 100 pessoas já é o estrago.

**O que ainda não se sabe (e precisa de experimento antes do ADR):**
- **Recall** — se ele *pega* o que deve pegar: `UNKNOWN`. Não coletaremos imagem de nudez
  para testar; o caminho é a avaliação publicada do modelo + monitoramento das retenções
  reais no piloto.
- **Falso positivo em traje de banho, piscina, bebê sem camisa, pouca luz**: não está na
  amostra. **É o próximo teste obrigatório** — festa de piscina é caso comum.
- Tempo **na VM** (1/8 OCPU): `UNKNOWN`; a razão 0,26× vale como estimativa.
- Manutenção: última versão do pacote é de **julho/2024**. Mitigação: carregar o ONNX
  direto no `onnxruntime` (sem depender do pacote). **Conferir a licença dos pesos**
  (treino sobre YOLOv8/Ultralytics) antes do ADR — o repositório é público, mas não se
  presume.

### 5.4 Capacidade — o risco nº 1

Conta de guardanapo, **não medição**: 100 participantes × até 50 fotos = até **5.000 fotos**
numa noite. O reconhecimento facial custou ~0,7 s por foto **num núcleo desta máquina**; a
VM tem **1/8 de OCPU**. Mesmo com uma fração disso, os picos da festa (parabéns: 60 pessoas
fotografando no mesmo minuto) enfileiram muito além dos 10 s de P95. O próprio projeto já
tinha dito: a **fila explícita "vira obrigatória no dia em que a Fiesta fizer N convidados
subirem ao mesmo tempo"** (IDEIAS-V2 A-bis #4).

**Fila não é capacidade — e confundir as duas é o erro caro aqui.** A fila impede que o
envio falhe ou estoure timeout; ela **não** aumenta quantas fotos por minuto a VM
processa. Se no parabéns chegam 60 fotos por minuto e a máquina processa 20, a fila
converte *erro* em *atraso* — e atraso é exatamente o que o "na hora" promete não ter.
Capacidade vem de CPU (a ARM) e de saber o número (teste de carga). Junto com a fila, o
SLA muda de nome: deixa de ser "o `/ingest` respondeu em X" e passa a ser
**P95 de "recebida" → "entregue no celular de quem aparece"**, que é a promessa real.

Pré-requisitos, em ordem:
1. **Fila assíncrona e DURÁVEL**: o envio responde na hora ("recebida"), o processamento
   acontece atrás, e o participante vê o estado. Durável porque **aqui deploy é `git push`
   a qualquer hora e todo deploy reinicia o serviço** (medido: 3 a 10 s de queda) — fila em
   memória perderia, a cada push, as fotos recebidas e ainda não processadas. Uma tabela no
   SQLite com estado (`recebida → processada`) e um worker que retoma depois do restart
   resolve, sem Redis nem Celery (CLAUDE.md §4.3: o menor stack que cumpra). De bônus, o
   estado visível para o participante sai de graça. A fila IndexedDB do celular já existe;
   falta a do servidor.
2. **VM ARM A1** gratuita — ~16× a CPU de hoje (BLUEPRINT §11); A1 em São Paulo costuma
   dar "out of capacity", então tentar com retry agendado. Mudança de infra = ADR.
3. **Fotos fora do SQLite (R2)** — IDEIAS-V2 A.0; milhares de fotos por festa num BLOB
   derrubam banco e backup.
4. **Teto por evento** (IDEIAS-V2 A-bis #7): uma festa gigante não pode travar a
   fotógrafa que está trabalhando ao mesmo tempo.

`UNKNOWN — REQUIRES EXPERIMENT`: quantos envios por minuto a VM atual e a ARM aguentam
dentro do P95 < 10 s. Experimento: teste de carga com N participantes simulados, na
VM de verdade, antes do piloto.

### 5.5 Segurança e abuso

- **Credencial do participante no header**, não na URL. Hoje o `guest_id` vai em query
  string (`/feed?guest_id=`), o que é aceitável para **ler** a própria galeria, mas não
  para **escrever**. Token próprio, escopo do evento, expira com a sessão.
- **Limite por participante = produto (50); limite por IP = abuso** (rajada absurda),
  nunca o contrário (PRODUTO §2).
- Tipo e tamanho no servidor: JPEG/PNG/HEIC, teto de tamanho (item §3.3 do handoff).
- Tudo com teste de contrato, como as rotas atuais.

### 5.6 Invariantes da Fiesta

> Isto não é estilo: **cada linha aqui vira teste de contrato**. É o que impede que a
> próxima sessão (humana ou agente) "simplifique" uma delas sem perceber o que está
> quebrando. Escritas depois de uma revisão externa do plano (2026-09-11), com as
> correções que a leitura do código impôs.

1. **Envio da Fiesta nunca espera o processamento.** O upload termina em `recebida`, não
   em "processada e entregue". (§5.4)
2. **Foto não publicada não participa de nada.** Uma foto `retida` fica fora da entrega,
   da listagem e do byte. Vale no **índice de rostos** (`rostos_de`, senão a próxima
   selfie casa com ela e a foto retida chega no feed), em `GET /photos` e em
   `GET /img/...` — **nunca só na interface**. Hoje as duas rotas são públicas para quem
   tem o código do evento, e o código está no QR projetado na parede.
3. **`guest_id` não é credencial de escrita na Fiesta.** Escrita de participante (enviar,
   apagar, pedir remoção) exige token próprio, no cabeçalho, com escopo do evento.
   **Exceção legada, consciente:** `/convidado/excluir` (`rig.py`) aceita só o `guest_id`
   — é a saída do titular (LGPD Art. 18) e o pior dano possível é alguém apagar o próprio
   cadastro de outra pessoa. Fica como está; quem "consertar" isso sem ler aqui quebra um
   direito do titular.
4. **Toda foto da Fiesta tem exatamente um autor: um participante OU a dona do evento.**
   (A Ana também fotografa — PRODUTO §2. Por isso `autor_guest` é `NULL` quando a autora é
   a conta dona, e não "toda foto tem `autor_guest`".)
5. **Toda entrega é auditável**: score, limiar vigente, modelo e caminho. **Já feito e em
   produção** — ADR-0035, vale para todos os modos.
6. **Toda decisão de moderação é auditável**: versão do modelo **e** da política, junto da
   foto. Sem isso não há como explicar por que a mesma foto passaria hoje e seria retida
   amanhã.
7. **O limite de 50 é por participante e por evento, nunca por IP** — e a checagem é
   **atômica**: com envio simultâneo, dois uploads chegando em 49 não podem virar 51.
8. **A fila é durável**: reiniciar o serviço não perde foto recebida. Todo deploy
   reinicia. (§5.4)
9. **R2 guarda o binário; o SQLite guarda estado e metadado.** E apagar apaga nos dois:
   expiração de retenção e pedido do titular precisam remover **o objeto**, senão sobra
   arquivo órfão — dado que a política de privacidade afirma não existir. O teste de
   restauração (`docs/BACKUP.md`) passa a cobrir os dois lados.
10. **Nada da Fiesta muda o significado de dado legado.** `NULL` continua querendo dizer
    "comportamento de hoje".
11. **Quem aparece na foto tem direito de remoção mesmo sem ser participante.** O art. 18
    não exige ter feito selfie. Precisa de canal (organizadora / Fóton), e ele não pode
    ser o botão do app, que só existe para quem entrou.
12. **Criança nunca tem sessão própria.** Não faz selfie, não tem galeria, não recebe no
    celular dela: quem recebe é o responsável que a registrou (§6.2).
    *(12, 13 e 14 valem trivialmente na v1, que não registra criança — ficam escritas
    porque são a condição de entrada da §6.2 quando ela voltar.)*
13. **Biometria de menor nunca é permanente.** Morre com o evento, e a retenção permanente
    do modo álbum (GLAMON, `ret_bio_dias = 0`) é **proibida** para quem tem responsável
    registrado — é a única regra da Fiesta que precisa de uma trava explícita no código de
    retenção, porque hoje a isenção é por conta, não por pessoa.
14. **Criança nunca vai para o telão** (v2), em nenhuma configuração.

---

## 6. LGPD e conteúdo

### 6.1 Quem responde pelo quê
Na Fiesta, **quem fotografa é o convidado**, não uma profissional contratada. A dona do
evento (Ana) vira a organizadora que responde pela festa — o contrato do organizador
(`docs/CONTRATO-ORGANIZADOR.md`) precisa de um **adendo Fiesta**. E o participante que
envia precisa de um **aceite curto no primeiro envio**: "tenho direito de compartilhar
esta foto; sem nudez; entendo que os rostos serão usados para entregar a foto a quem
aparece nela".

### 6.2 Crianças — ADIADO: a v1 é só para maiores

> ### ⛔ Estado, e ele mudou duas vezes no mesmo dia (2026-09-12)
>
> **De manhã:** *"Crianças na Fiesta pode, e será seguro para elas."* O desenho abaixo foi
> escrito a partir dessa decisão.
> **Depois de ler a revisão externa, o dono voltou atrás:** *"por enquanto vamos deixar o
> Fóton para maiores"*. **A v1 da Fiesta não terá registro de criança.** O desenho abaixo
> fica pronto, e volta à mesa quando houver parecer jurídico (§6.4).
>
> **Foi a decisão certa**, e não é recuo: o art. 14 §1 fala em *pais ou responsável legal*,
> e a regra que tínhamos acabado de aceitar (valer a declaração do adulto acompanhante) é
> uma leitura mais larga que isso. O desenho técnico estava na frente da validação
> jurídica — e o jeito de resolver é a validação vir antes, não o código andar assim.

> ### ⚠️ O que "só para maiores" NÃO quer dizer
>
> Não quer dizer que nenhum dado de criança seja tocado. **Numa festa, criança aparece na
> foto**, e o motor detecta e vetoriza **todo rosto de toda foto** para saber a quem
> entregar — é assim hoje, também no modo fotógrafa. O que a v1 deixa de ter é o
> **registro da criança como destinatária**: ninguém a cadastra, ela não vira convidada, e
> nada é entregue por causa dela.
>
> Ou seja, "só para maiores" é **quem usa**, não **quem aparece**. Vender como "o Fóton não
> processa criança" seria mentira, e é exatamente o tipo de frase que não pode sair daqui.
> A posição honesta para o contrato e para a venda: *o Fóton não cadastra menores; rostos
> de menores que apareçam em fotos são tratados como qualquer outro rosto não cadastrado,
> com a mesma retenção curta, e nunca viram destinatário.*

**O desenho guardado** (para quando houver parecer): a base legal e o que foi verificado
estão na **ADR-0036**, que segue valendo como decisão de desenho — e cuja aplicação na v1
está suspensa por esta decisão.

**O que é verdade na premissa, e o que não é.** Lá fora existe mesmo, e funciona — mas
quem faz isso com criança de forma legítima são as **plataformas de foto escolar**, e o
modelo delas é sempre o mesmo: **o responsável autoriza antes**. A atualização da COPPA de
2025 passou a tratar **molde facial como dado pessoal** de forma explícita. Do outro lado,
quem agrupou rosto sem pedir pagou caro: Google Fotos fechou acordo de **US$ 100 milhões**
em Illinois, a Apple responde ação que cita **justamente menores**, TikTok pagou US$ 92
milhões, e Nova York mantém moratória de reconhecimento facial em escola. **Não existe
caso de sucesso do modelo "processa a criança e depois se vê".**

**No Brasil a régua é mais explícita, não menos.** LGPD **art. 14 §1**: dado de criança
exige **consentimento específico e em destaque, dado por ao menos um dos pais ou
responsável**, e o controlador deve fazer *"todos os esforços razoáveis"* para verificar
que foi o responsável mesmo, considerando as tecnologias disponíveis. O caput manda tratar
sempre no **melhor interesse** da criança. (A lei separa **criança**, até 12, de
**adolescente**, 12 a 18; o consentimento do responsável é exigência escrita para
criança — trataremos os dois de forma conservadora.)

**O desenho que atende os dois lados — a criança não é usuária; o responsável é:**

1. **Ninguém vira destinatário sem alguém autorizar.** A criança **não** faz selfie, não
   tem sessão, não tem galeria e não recebe nada no celular dela.
2. **Quem registra é o adulto que está com a criança**, já participante identificado da
   festa (fez a própria selfie): ele tira a foto dela, marca a **cláusula em destaque,
   separada do resto**, e **declara ser o responsável por ela naquele evento**.
   **Decidido pelo dono em 2026-09-12:** vale a declaração de quem está com a criança — não
   só de pai, mãe ou responsável legal. A razão é a festa real: no Brasil, a criança
   costuma chegar com a tia, a avó ou a madrinha, e um desenho que só aceitasse o
   responsável legal deixaria de fora o caso mais comum.
   **Consequência honesta, e é a mais séria deste documento:** o art. 14 §1 fala em *"pais
   ou responsável legal"*. Aceitar o adulto acompanhante é uma leitura mais larga, e passa
   a ser **o ponto jurídico central** do plano, não um detalhe. O que reduz o risco, e
   precisa estar no desenho: a declaração é explícita e em destaque (não uma caixinha
   escondida), fica **registrada com quem declarou, quando e sob qual texto**, a biometria
   morre com o evento, e o responsável pode apagar tudo a qualquer momento. Confirmar isso
   com advogado é **item 1 do §6.4** e é bloqueio de lançamento.
3. **As fotos da criança chegam na galeria do responsável**, identificadas como dela.
4. **Retenção curta e nunca permanente.** A biometria da criança morre com o evento, e a
   retenção permanente do modo álbum (GLAMON) fica **proibida para menor**.
5. **Criança nunca aparece no telão** (v2), em nenhuma hipótese.
6. **O responsável apaga tudo a qualquer momento**, exercendo o art. 18 em nome dela.
7. **Distinção que precisa ficar clara no contrato:** detectar um rosto numa foto (o que o
   motor faz com todo mundo, para saber a quem entregar) **não é** transformar aquela
   pessoa em destinatária. Para criança, virar destinatária depende do passo 2.

**O que NÃO vamos afirmar, nem vender:**
- O filtro de conteúdo **não detecta idade** e **não é proteção infantil**. Ele separa
  parte do corpo, nada mais.
- Não faremos estimativa de idade por imagem para "proteger": estimar idade **é mais**
  tratamento biométrico, é impreciso, e criaria um problema novo para resolver outro.

### 6.3 Remoção e retenção
- **Quem sai da festa deixa as fotos** (decisão do dono, 2026-09-12): ao apagar a selfie, o
  participante perde a **própria galeria** e a própria biometria, mas as fotos que ele
  enviou **ficam** — são lembrança dos outros também, a mesma lógica da regra de não apagar
  foto com mais gente. **Consequência que precisa de desenho:** a assinatura dele sai
  junto. Quem pediu para sair não continua com o apelido estampado em dezenas de fotos,
  então a autoria daquelas fotos vira **anônima** ("um convidado"). O vínculo interno
  (`autor_guest`) aponta para um convidado que não existe mais, e isso é estado válido, não
  erro — o código precisa tratar, não "consertar".
- Pedido de remoção vai para a dona; retenção igual à do evento (ADR-0029).
- Foto retida pela moderação **não entra** na entrega por rosto até ser publicada.
- Telão só na v2, com consentimento próprio (IDEIAS-V2 A.1).
- Quem aparece na foto **sem ser participante** também tem direito de remoção (art. 18 não
  exige ter feito selfie) — precisa de canal fora do app (invariante 11 da §5.6).

### 6.4 O que precisa de advogado antes de lançar

Não é formalidade: são os pontos em que uma opinião jurídica muda o desenho, e nenhum
deles se resolve escrevendo mais código.

1. **A declaração do adulto acompanhante** (§6.2 passo 2, decisão do dono) satisfaz o
   art. 14 §1, que fala em *pais ou responsável legal*? Se não satisfaz, o que satisfaz
   numa festa — e continua viável em 15 segundos na porta do salão? **É a pergunta nº 1
   desta lista, e a que pode mudar o desenho.**
2. **Adendo Fiesta ao contrato do organizador** (`docs/CONTRATO-ORGANIZADOR.md`), que hoje
   pressupõe fotógrafa contratada, não convidado fotografando convidado.
3. **Texto do aceite do participante** (uma tela, linguagem simples) e da **cláusula em
   destaque do responsável** — o "destaque" do art. 14 §1 é requisito de forma, não de
   estilo.
4. Base legal do rosto **detectado mas não registrado** (a pessoa que aparece na foto e
   nunca fez selfie) — hoje sustentado pelo contrato do organizador; na Fiesta o
   fotógrafo é convidado, e vale confirmar se a construção continua de pé.

---

## 7. Plano em fases (cada fase só começa com a anterior aceita)

| Fase | O quê | Porta de saída (evidência, não afirmação) |
|---|---|---|
| **0. Pré-requisitos** | limite de tamanho/tipo e rate limit no `/ingest` e `/selfie` (handoff §3.3); feature flags na tabela `config`; ~~limiar 0,40~~ (**feito**, ADR-0034) | testes de contrato verdes; deploy verificado por SHA |
| **1. Decidir e medir** | ~~**ADR crianças**~~ (**feita**: ADR-0036); **ADR Fiesta** (papéis, dados, rotas); **ADR moderação** (NudeNet, limiar de retenção, licença dos pesos); **ADR capacidade** (fila + ARM + R2). Experimentos: falso positivo em traje de banho/piscina; tempo do NudeNet **na VM**; teste de carga. Em paralelo, o que é do advogado (§6.4) | 3 ADRs aceitas pelo dono; 3 números em BENCHMARKS; parecer jurídico do §6.4 |
| **2. Backend** | fila assíncrona, rotas §5.2, moderação no caminho, contador de 50, apagar/pedir remoção | testes de contrato para cada regra do §1; prova do vermelho |
| **3. Front** | pele `social` completa; botão enviar + "12 de 50"; retidas e pedidos no painel da dona | `test_front` + (quando existir) E2E Playwright |
| **4. Piloto fechado** | uma festa pequena de verdade da Ana, **de público adulto**, com o dono presente | medir: fotos enviadas, retidas, **retidas por engano**, **entregas erradas reportadas**, P95 do envio à entrega |
| **5. v2** | **telão** com consentimento (decidido: não é v1), revelação opcional, ZIP, limite configurável, e a §6.2 se o parecer permitir | depois de uma v1 sem vergonha |

### Os três números que abrem a porta do piloto

Uma revisão externa do plano (2026-09-12) isolou o que precisa ter número **antes** da
fase 4, e concordo — nenhum deles existe hoje:

1. **Throughput e latência da VM real** sob envio concorrente.
2. **Custo do filtro de conteúdo na VM real** (aqui só temos a razão de 0,26× medida em
   outra máquina).
3. **P95 de "recebida" até "entregue"** sob carga — a promessa percebida pelo convidado,
   não o tempo de resposta do upload.

Enquanto os três forem `UNKNOWN`, o estado do projeto é **pronto para ADR e medição**, não
pronto para construir. É a mesma conclusão da revisão, e é a ordem que este documento já
propunha.

---

## 8. Decisões do dono

### Já decididas (2026-09-12)

| # | Pergunta | Decisão | O que ela puxa junto |
|---|---|---|---|
| 1 | Crianças na Fiesta | **ADIADA no mesmo dia.** De manhã: entram, com o desenho do §6.2. À tarde, depois da revisão externa: **a v1 é só para maiores** | o desenho fica guardado (ADR-0036); volta quando houver parecer jurídico. Cuidado com o que "só para maiores" não significa — §6.2 |
| 2 | Peito masculino (piscina) | **Passa** | classe liberada na política (§5.3) |
| 3 | `ANUS_EXPOSED` | **Bloqueia** | classe retida (§5.3) |
| 4 | Quem libera foto retida | **Só a dona**, quando puder olhar | quem enviou precisa ver **"em análise"**, senão acha que falhou (§5.3) |
| 5 | Mostrar quem tirou a foto | **Sim, com apelido** | a selfie da Fiesta passa a **pedir um apelido** — hoje o nome é opcional (§5.1) |
| 6 | Participante que sai da festa | **As fotos ficam**; ele perde a própria galeria | a autoria vira **anônima** ao sair (§6.3) |
| 7 | Telão | **v2**, não v1 | menos superfície na v1; o telão volta com moldura de consentimento |
| 9 | Criança sem o responsável legal | Valeria a declaração de quem está com ela — **sem efeito na v1**, que não registra criança | continua sendo o ponto jurídico a resolver antes de a §6.2 sair do papel |

| 8 | Preço | **Piloto gratuito**, com a arquitetura já preparada para monetização futura (evento gratuito → pago → pagamento confirmado → limites do plano), sem cobrança real e sem credencial fora do servidor | costura e provedor falso agora; o provedor real (PSP) numa ADR quando a monetização ligar. Ver `FIESTA-IMPLEMENTACAO.md` §4.5 |

**Não há mais decisão de produto aberta neste plano.** As decisões novas — que surgiram ao
propor a implementação — estão em `docs/FIESTA-IMPLEMENTACAO.md` §3.

---

## 9. Riscos, em ordem

1. **Capacidade no pico da festa** — sem fila, ARM e R2, a Fiesta trava justamente no
   parabéns. (§5.4)
2. **Moderação que não pega** — recall desconhecido; uma foto imprópria no telão ou na
   galeria é a vergonha máxima. Mitigação: retenção antes de publicar + dona no controle.
3. **Menores** — a v1 **não registra criança** (§6.2), o que tira o risco maior da mesa por
   ora. O que **sobra** e não some: criança aparece em foto de festa, e todo rosto é
   detectado e vetorizado para a entrega funcionar. Mitigação do que sobra: retenção curta
   igual à de qualquer rosto não cadastrado, nunca vira destinatária, nunca vai ao telão
   (que também saiu da v1), e o contrato do organizador tem que dizer isso com todas as
   letras. O risco grande — "o consentimento do responsável se sustenta?" — volta junto com
   a §6.2, depois do parecer.
4. **Entrega errada em escala** — mitigada pelo 0,40 (ADR-0034); ainda precisa ser medida
   num evento real com gente sem parentesco.
5. **Abuso** (spam de fotos, foto de fora da festa) — limite por participante + rate limit.

---

## Fontes externas (consultadas em 2026-09-11)

- Comparação de 12 apps de foto de convidado — [PartyCam](https://partycam.app/blog/best-qr-code-wedding-photo-apps-2026) (concorrente; ler com viés)
- GuestCam, casamentos — [guestcam.co](https://guestcam.co/photo-sharing/weddings)
- Kululu — [kululu.com](https://www.kululu.com/wedding-photo-sharing-app)
- NudeNet 3.4.2 (licença, classes, modelos) — [PyPI](https://pypi.org/project/nudenet/)
- Alegação de perda na instalação — [Guesticon](https://guesticon.com/blog/guests-upload-wedding-photos-qr-code-2025)
