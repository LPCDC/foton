# FIESTA-IMPLEMENTACAO.md — Proposta de implementação

> **PROPOSTA — aguardando aprovação do dono. Nenhuma linha de produto foi escrita.**
> Escrita em 2026-09-12 a partir do pedido "transformar o Fóton Fiesta em produto pronto
> para piloto real e arquitetado para monetização futura", seguindo o processo que o dono
> definiu: ler o plano → inspecionar o código → procurar skills → identificar reuso →
> listar conflitos → só então propor.
>
> Fonte das regras: `docs/FIESTA.md` (plano, 14 invariantes, decisões fechadas) e as ADRs
> 0024, 0025, 0029, 0030, 0034, 0035, 0036. **Nada aqui simplifica regra existente.** Onde
> este documento e o plano divergirem, o plano vence até uma ADR dizer o contrário.

---

## 0. Em uma tela

**O que proponho.** A Fiesta vira uma modalidade nova do mesmo motor, com **três
experiências em páginas próprias** (participante, contratante, operação), um **design
system Bauhaus** comum a elas, **fila durável** no servidor, **moderação no caminho**,
**auditoria administrativa** e a **costura de monetização pronta** — com um provedor de
pagamento *falso* no piloto, sem nenhuma cobrança real e sem nenhuma credencial fora do
servidor.

**O que não muda.** O modo fotógrafa e o modo empresa continuam exatamente como estão: o
`/ingest` síncrono, o `index.html`, a fila IndexedDB, a idempotência, a retenção, o
reconhecimento, a autenticação por senha e as 367 checagens atuais.

**O que bloqueia, em ordem:**
1. **Quatro decisões suas** (§3.1) — uma delas é nova e séria: a licença AGPL do modelo de
   moderação.
2. **Os três números** que o plano já exigia antes do piloto (§6).
3. **Parecer jurídico** — agora sem a parte de crianças, mas com três itens que continuam
   valendo para público adulto (§3.3).

**Estado honesto:** com esta proposta aprovada, o projeto passa de *pronto para ADR e
medição* para *pronto para construir em fases* — **não** para *pronto para piloto*. O
piloto só abre com os três números medidos e o parecer em mãos.

---

## 1. O que a inspeção do código mostrou

Fatos lidos no código em 2026-09-12, não suposições.

| Área | O que existe hoje | Onde |
|---|---|---|
| Front | **Uma página só**, `index.html` com **240 KB** e **16 telas** (`section.screen` + `go()`), sem framework (ADR-0016) | `app/web/index.html` |
| Peles | `PERFIL()` / `VOCAB` / `aplicarPerfil()` trocam vocabulário e cor: `pro` dourado, `empresa` platinado, `social` coral (ADR-0030) | `index.html:1703-1727` |
| Admin | É **uma tela dentro da mesma página** (`s-admin`, `abrirAdmin()`), com 18 rotas `/admin/*` no servidor | `index.html:824`, `rig.py` |
| Contrato do front | `test_front.py` lê o `index.html` **como texto**: compila o JS, proíbe função e id duplicados, exige funções essenciais e as regras da fila | `tests/test_front.py` |
| Servir arquivos | `StaticFiles` monta `app/web` na raiz — qualquer `.html` novo ali vira página | `rig.py:1295` |
| Service worker | Cacheia **só a casca** (`CASCA`), nunca API | `app/web/sw.js:19` |
| Conta | Senha PBKDF2 + token em `session` | `store.py`, ADR-0019/0026 |
| **Sessão** | **O token nunca expira no servidor** — `por_token()` não confere idade | `store.py:159` |
| Admin | `FOTON_ADMINS` (env) **ou** coluna `photographer.admin`; se a env faltar, o padrão é o login `admin` | `rig.py:800-812` |
| Convidado | **Sem credencial.** O `guest_id` fica no `localStorage` e vai em query string (`/feed?guest_id=`) | `index.html:2648` |
| Pipeline | `/ingest` **síncrono** no request; feed por **polling** de 2,5 s | `rig.py` |
| Flags | Tabela `config(chave, valor)` já existe e já é usada (`ftp_visto:*`) | `store.py:175-209` |
| Dinheiro | `credits` / `credits_total` **existem e estão desligadas** (ADR-0024) | `store.py` |
| Deploy | `git push`; o auto-update **só puxa código, não instala dependência** | BLUEPRINT §5 |

**Achados de passagem, que valem registro:**
- **`app/web/artifact.html`**: cópia **antiga** do front (98 KB, último commit de agosto,
  diferente do `index.html`), **servida publicamente** em `/artifact.html`. É um app velho
  acessível em produção. Recomendo remover — com nota de ADR, porque aqui remover também é
  mudar (ADR-0027).
- **Sessão que não expira**: aceitável para a fotógrafa (derrubar a sessão da Patrícia no
  meio da festa seria pior), **não** para quem tem poder de apagar tudo. Ver §4.6.
- **Licença do modelo de moderação** — o pacote NudeNet se declara MIT, mas o arquivo
  `320n.onnx` declara **AGPL-3.0** nos próprios metadados. O plano estava errado nesse
  ponto e já foi corrigido. Ver §3.1.

---

## 2. O que se reaproveita — e não se reescreve

| Reaproveitado | Como entra na Fiesta |
|---|---|
| Conta com senha, sessão, `_pode()` | **É** o login do contratante. Nenhum sistema de login novo |
| Pele `social` (ADR-0030) | Marca a conta contratante; o poder continua vindo do servidor |
| `_admin()` e as 18 rotas `/admin/*` | Base do painel de operação; nada é removido |
| `detect_embed`, limiar 0,40, maior rosto (ADR-0034) | Motor da entrega, sem mudança |
| Auditoria de entrega (ADR-0035) | Invariante 5 já cumprida; o painel só passa a mostrar |
| Idempotência (`photo.sha`) | Envio repetido do participante não duplica |
| Fila IndexedDB + `reduzir()` (2048 px) | O celular do participante já envia leve e sobrevive a fechar o app |
| Consentimento e `/convidado/excluir` | Saída do titular, mantida como exceção consciente (invariante 3) |
| Retenção e expiração automática | Valem igual; foto da Fiesta segue a retenção do evento |
| Tabela `config` | Feature flags, sem tabela nova |
| `tests/experimento_limiar.py`, `experimento_moderacao.py`, `medir-janela-deploy.sh` | Base dos três números |

---

## 3. Conflitos e decisões para aprovar

### 3.1 Bloqueiam — preciso da sua resposta antes de começar

> **Respostas do dono (2026-09-12):**
> **A — mantém: v1 sem registro de criança.** · **B — login de teste só em
> desenvolvimento.** · **D — costura + provedor falso.**
> **C — ainda aberta:** o dono pediu alternativa com licença permissiva (MIT, Apache 2.0,
> BSD). A pesquisa está no §3.4; falta o experimento que decide.

**A. Crianças: o pedido conflita com a decisão que você fechou.**
O pedido lista "registro de criança conforme as regras do Fiesta" e teste de "regras de
crianças". A regra vigente, fechada por você em 12/09 depois da revisão externa, é **v1 só
para maiores** — o registro foi adiado até haver parecer (ADR-0036). *Proposta:* **não
construir registro de criança na v1**, e testar que ele **não existe** (as invariantes
12–14 ficam dormentes). Não vou reverter uma decisão sua em silêncio pela segunda vez.

**B. "Login universal de teste" para participante.**
Conflita com a invariante 3 (escrita exige token próprio do participante) e com o repo ser
público (credencial compartilhada não pode morar no código). *Proposta:* existe **só em
modo de desenvolvimento**, ligado por variável de ambiente no servidor, **com a rota nem
registrada em produção** — e um teste que prova a ausência dela quando a variável falta.
No piloto real, o participante entra pelo caminho de verdade: QR, selfie e token.

**C. Moderação: o modelo candidato é AGPL-3.0.** *(novo — descoberto nesta inspeção)*
Lido direto do arquivo: `320n.onnx` → `author = Ultralytics`, `license = AGPL-3.0`. A
Ultralytics diz que modelo treinado com o código dela fica sob AGPL, e que serviço acessível
pela rede precisa disponibilizar o código-fonte correspondente da aplicação.
- **Aceitar**, com parecer: o repo já é público, o que pode atender. Custo: **abre mão de
  fechar o repositório** no futuro sem licença comercial ou troca de modelo — e isso pesa
  num produto que vai ser monetizado.
- **Procurar modelo sem AGPL** antes de construir a moderação: atrasa, com resultado
  `UNKNOWN`.
- **API gerenciada** (visão computacional de nuvem): **não recomendo** — a foto da festa
  sai do Fóton para terceiro, contra a postura de LGPD que é argumento de venda.

**D. Pagamento: a costura agora, o provedor depois.**
Um detalhe técnico muda a expectativa: **uma chave PIX, sozinha, recebe o dinheiro mas não
avisa o sistema que ele chegou.** Confirmar pagamento automaticamente exige um provedor
(PSP) com API e webhook — ou a API Pix do banco, que pede certificado. *Proposta:* construir
agora **o domínio** (plano, limites, estados do pagamento, interface de provedor) com um
**provedor falso**, e escolher o PSP real numa ADR quando a monetização for ativada. Sem SDK
novo, sem credencial, sem webhook exposto no piloto. A alternativa — integrar um PSP em
sandbox já — adiciona dependência e superfície sem uso no piloto.

### 3.2 Com recomendação padrão — sigo assim se você não objetar

| # | Decisão | Recomendação | Por quê |
|---|---|---|---|
| E | Onde vivem as três experiências | **Páginas próprias:** `/fiesta/` (participante), `/fiesta/painel/` (contratante), `/ops/` (operação), sem framework | O `index.html` já tem 240 KB e contrato de texto próprio; três identidades visuais dentro dele brigariam com as peles `pro`/`empresa` e com o `test_front`. Páginas estáticas mantêm o espírito da ADR-0016 (sem build, sem framework) |
| F | Painel de operação | **Novo, em `/ops/`, para o Fóton inteiro**; a tela antiga de admin fica até o novo cobrir tudo, e só então sai, com ADR | É o painel de quem opera todos os modos, não só a Fiesta |
| G | Admin e foto retida | Admin **não libera** foto retida (decisão 4: só a dona). Admin **retira** conteúdo, com registro | Marco Civil art. 21: provedor notificado que não retira conteúdo íntimo responde subsidiariamente. Publicar ≠ retirar |
| H | Sessão de admin | Ação destrutiva exige **reautenticação recente** (janela curta) + confirmação digitada + registro. **Sessão da fotógrafa não muda** | Hoje o token não expira; derrubar sessão de fotógrafa no meio de festa seria pior que o risco atual |
| I | Quem cria evento Fiesta no piloto | Qualquer conta logada **só se** a flag `fiesta_habilitada` estiver ligada **e** a conta estiver na lista do piloto | Controla o piloto sem código novo depois; `event.modo` continua por evento (revisão externa) |
| J | Nome técnico | Só `fiesta` em rota, tabela, coluna e contrato. "Foto'n Fiesta!" é marca, só na interface | Revisão externa; conferido: "terceira porta" não vazou para código |
| K | Cor-assinatura | **Coral continua a assinatura da Fiesta** dentro do sistema Bauhaus (§5) | Continuidade com a ADR-0030; a Bauhaus entra como gramática, não como troca de marca |
| L | `artifact.html` antigo | Remover | App velho servido em produção, sem dono |
| M | Tamanho do piloto | **Teto definido pelo teste de carga**, não por chute | É o número 1 do §6 |

### 3.4 Moderação com licença permissiva — o que a pesquisa encontrou (2026-09-12)

**A família NudeNet inteira sai.** O **repositório** `notAI-tech/NudeNet` é **AGPL-3.0**
(API do GitHub), apesar de o pacote no PyPI dizer MIT, e os pesos v3 declaram AGPL-3.0 e
autoria Ultralytics nos metadados do ONNX. O fork `ifnude` não serve: **não declara licença**
(sem licença, o padrão legal é todos os direitos reservados) e baixa um modelo de 139 MB de
origem não informada.

**O que existe com licença permissiva é outra coisa: classificador da imagem inteira, não
detector de parte do corpo.** Isso importa porque a regra do dono é por parte do corpo
("decote passa, mamilo não"), e classificador genérico é justamente o que ele disse que
"reprovaria metade de um casamento". **Nenhum** candidato permissivo com detecção por parte
do corpo foi encontrado.

Licença e tamanho lidos da API do Hugging Face:

| Modelo | Licença | Saída | Peso | Por que é candidato | Risco |
|---|---|---|---|---|---|
| `Freepik/nsfw_image_detector` | **MIT** | **4 níveis**: neutro · baixo · médio · alto (explícito) | 172,7 MB | é o único que **separa sugestivo de explícito** — o mais perto da regra do dono | arquitetura EVA02 a 448 px: custo em CPU `UNKNOWN`, provavelmente alto para 1/8 de OCPU |
| `Marqo/nsfw-image-detection-384` | **Apache-2.0** | binário (NSFW / normal) | **22,4 MB** | o único leve o bastante para parecer caber na VM | binário: pode reter decote |
| `AdamCodd/vit-base-nsfw-detector` | **Apache-2.0** | binário | 344 MB; tem **ONNX pronto**, inclusive 4-bit (52,6 MB) | já em ONNX, que é o stack da VM | binário: mesmo risco |
| `Falconsai/nsfw_image_detection` | Apache-2.0 | binário | 343 MB | o mais baixado | o repositório traz também um `yolov9` quantizado, de outra linhagem — conferir antes de usar |

**O que decide é medir, não o card do modelo:** as mesmas **80 fotos reais de festa, sem
nudez** do experimento anterior → quantas cada modelo reteria (falso positivo contra a
regra "decote passa") e quanto custa por foto num núcleo. O **recall** continua
`UNKNOWN` para todos, pelo mesmo motivo de antes: não vamos coletar imagem de nudez.

**Uma leitura de produto que o experimento vai testar:** como a retenção só **atrasa** (a
dona libera), um classificador que erre um pouco para o lado de reter pode ser aceitável —
**desde que** o número de fotos de festa retidas por engano fique baixo. Se o Freepik
separar bem os níveis, "alto" vira o gatilho de retenção e "médio" publica.

#### Resultado medido (2026-09-12) — detalhe no BENCHMARKS

Nas mesmas 80 fotos de festa, sem nudez, num núcleo:

| Modelo | Retidas por engano | Custo por foto |
|---|---|---|
| Freepik (MIT) | **0/80** | 1.813 ms |
| Marqo (Apache-2.0) | **1/80** — um vestido de festa estampado | **116 ms** |
| AdamCodd 4-bit (Apache-2.0) | **27/80 (34 %)** | 980 ms |
| **Cascata Marqo → Freepik, portão 0,15** | **0/80** | **252 ms** (6 de 80 sobem ao Freepik) |

**Recomendação para a decisão C: cascata Marqo → Freepik**, com duas licenças permissivas
(Apache-2.0 + MIT), o mesmo zero falso positivo do NudeNet nesta amostra, custo na mesma
ordem, e o julgamento **sugestivo × explícito** que a regra do dono pede. O Marqo sozinho
não serve: a única foto que ele reteria é justamente um vestido de festa. O AdamCodd está
descartado.

#### No stack da VM (ONNX), medido em 2026-09-12 — detalhe no BENCHMARKS

**Pendência 1 resolvida: a cascata cabe no stack da VM, com uma condição — o Freepik tem que
ser INT8.** Exportados para ONNX, com pré-processamento reescrito sem PyTorch (**diferença 0**
pixel a pixel) e **decisão idêntica em 80/80** em todas as etapas (PyTorch bf16 → PyTorch fp32
→ ONNX fp32 → ONNX INT8):

| Freepik | Processo inteiro (rosto + Marqo + Freepik) | Freepik por foto | Cascata, média por foto |
|---|---|---|---|
| float32 | 556–826 MB — **não cabe** com folga em 1 GB | 1.936 ms | ~237 ms |
| **INT8** | **308 MB** | **1.098 ms** | **~171 ms** (24 % do rosto) |

**Recomendação atualizada para a decisão C:** **Marqo em ONNX float32 → Freepik em ONNX INT8**,
arena de memória desligada, portão 0,15. Sem PyTorch na VM, sem dependência nova de runtime
(o `onnxruntime` já está lá), duas licenças permissivas.

**Antes da ADR de moderação — o que continua pendente:**
1. ~~Exportar para ONNX e medir memória e tempo~~ — **feito localmente**. Falta a mesma
   medição **na VM real**, com o processo de produção inteiro no mesmo 1 GB (número 2 do plano).
   E o INT8 soma uma incerteza: o erro de quantização foi medido em foto **sem** nudez.
2. **Falso positivo em traje de banho, piscina e pouca luz** — precisa de fotos cedidas
   pelo dono, como as de festa. Imagem de pessoa baixada da internet não entra (sem
   consentimento). **É também onde se descobre se a regra sobrevive à troca de modelo:** o
   NudeNet dizia "peito masculino exposto" e a política mandava publicar; um classificador
   da imagem inteira não tem essa classe, e só a foto de piscina mostra se o Freepik chama
   homem sem camisa de "alto".
3. **Escolher o portão**, que é decisão de risco: 0,15 custa 252 ms; 0,10 custa 547 ms e
   deixa menos coisa escapar do Freepik. O recall continua desconhecido nos dois.
   *(Custos em PyTorch; na cascata ONNX/INT8 o portão 0,15 sai por ~171 ms e o 0,10 por
   ~89 + 19/80 × 1.098 ≈ 350 ms.)*
4. **Como os 125 MB de pesos chegam na VM.** Não cabem bem no git, e o auto-update não baixa
   nada. Caminho provável: um passo de instalação único, no Cloud Shell, que baixa uma revisão
   **fixada** do Hugging Face, confere o **SHA-256**, converte e mantém os avisos de licença
   (MIT e Apache-2.0 exigem isso, inclusive na versão INT8). Entra na ADR.

### 3.3 Continuam dependendo de advogado, mesmo sem crianças

Do `FIESTA.md` §6.4, os itens 2 a 4 valem para público adulto:
1. **Adendo Fiesta** ao contrato do organizador (hoje pressupõe fotógrafa contratada).
2. **Texto do aceite do participante** no primeiro envio.
3. **Base legal do rosto detectado e não registrado**, agora com convidado fotografando
   convidado.
4. *(novo)* **Canal de notificação e remoção** do art. 21 do Marco Civil — prazo diligente,
   o que a notificação precisa conter, e como se verifica a legitimidade de quem pede.
5. *(novo)* **Licença do modelo de moderação** (decisão C) — só se o escolhido não for permissivo.

---

## 4. Arquitetura proposta

### 4.1 Três papéis, uma matriz de autorização

Autorização **sempre no servidor** (BLUEPRINT §6.7). Cada célula vira teste.

| Ação | Participante (token Fiesta) | Contratante (sessão, dono do evento) | Operação (admin) |
|---|---|---|---|
| Ver as próprias fotos / a festa publicada | ✅ | ✅ | ✅ (agregado) |
| Enviar foto (até 50) | ✅ | ✅ (sem teto de participante) | ❌ |
| Apagar foto | só a **própria**, com **1 rosto** no máximo | qualquer foto **do evento dele** | só como **retirada** (art. 21), com registro |
| Pedir remoção | ✅ | — | recebe as de **quem não é participante** (invariante 11) |
| Liberar foto retida | ❌ | ✅ **só ele** (decisão 4) | ❌ |
| Criar / encerrar evento Fiesta | ❌ | ✅ (com flag e lista do piloto) | ✅ |
| Flags, filas, erros, capacidade, auditoria | ❌ | ❌ | ✅ |
| Registrar criança | ❌ **(não existe na v1)** | ❌ | ❌ |

**Credencial do participante (invariante 3):** token próprio gerado na selfie de um evento
Fiesta, **no cabeçalho**, com escopo do evento e expiração junto com a retenção.

### 4.2 Modelo de dados — declarado antes

Padrão da casa: `ALTER` guardado, **NULL = comportamento de hoje**, nenhuma linha antiga
muda de significado.

**Do plano (sem alteração):** `event.modo`, `photo.autor_guest`, `photo.status`,
`photo.moderacao`, `guest.token`, `guest.apelido`, tabela `pedido_remocao`.
*(`guest.responsavel` e `guest.consent_resp` ficam **fora** da v1 — decisão A.)*

**Novo nesta proposta:**

| Mudança | NULL / vazio significa | Para quê |
|---|---|---|
| tabela `fila_fiesta(id, event_code, photo_id, autor_guest, estado, tentativas, erro, recebida_ts, iniciada_ts, terminada_ts)` | — | fila durável (§4.3) |
| `event.plano TEXT` | **gratuito do piloto** = hoje | limites vêm do plano, resolvidos no servidor |
| tabela `pagamento(id, event_code, conta, plano, valor_centavos, provedor, ref_provedor, estado, criado, atualizado, expira)` | — | máquina de estados do pagamento (§4.5) |
| tabela `pagamento_webhook(provedor, id_evento UNIQUE, recebido, hash)` | — | webhook **idempotente**: o mesmo aviso duas vezes não confirma duas vezes |
| tabela `admin_auditoria(id, ts, admin, acao, alvo, motivo, resultado)` | — | ação destrutiva deixa rastro (§4.6); **só inserção, nunca edição** |
| tabela `retirada(id, event_code, photo_id, origem, recebida_ts, concluida_ts, admin)` | — | prazo diligente do art. 21 fica mensurável |
| chaves em `config`: `flag:fiesta_habilitada`, `flag:pagamento_ativo`, `piloto:contas` | flag ausente = **desligada** | feature flags sem tabela nova |

- **LGPD:** `autor_guest`, `pedido_remocao` e a fila seguem a retenção do evento;
  `admin_auditoria` guarda **e-mail do admin, ação e alvo**, nunca rosto, selfie ou contato.
- **Rollback:** tudo aditivo; `git revert` volta ao hoje, e as tabelas novas ficam inertes.

### 4.3 Fila durável e os estados que o participante vê

```
enviar ──► RECEBIDA ──► PROCESSANDO ──┬──► PUBLICADA ──► ENTREGUE a quem aparece
 (responde                             ├──► RETIDA  ("em análise" — só a dona libera)
  na hora)                             └──► ERRO    (com motivo; nova tentativa ou aviso)
```

- **Envio termina em RECEBIDA** (invariante 1): os bytes vão para o armazenamento **antes**
  da resposta, então reiniciar o serviço não perde nada (invariante 8).
- **Worker no mesmo processo** (ADR-0016: um processo só), lendo a tabela. Ao subir, itens
  presos em PROCESSANDO voltam para RECEBIDA. **Um worker** por padrão: numa VM de 1/8 de
  OCPU, trabalho de CPU em paralelo não acelera — medir antes de mudar.
- **Limite de 50 atômico** (invariante 7): contagem e reserva na mesma transação.
- **O `/ingest` da fotógrafa continua síncrono.** A fila é só da Fiesta; migrar o legado
  seria outra decisão, com outra medição.
- **SLA com nome certo:** P95 de `recebida_ts` até a entrega (o `ts` da ADR-0035). Hoje
  esse número **não existe para produto nenhum**.
- **Armazenamento atrás de uma interface** (`guardar` / `ler` / `apagar`): BLOB no SQLite
  hoje, R2 quando o teste de carga pedir — **sem reescrever a Fiesta**, e com o "apagar
  apaga nos dois lados" (invariante 9) passando por um lugar só.

### 4.4 Moderação no caminho

- Carregar o ONNX **direto no `onnxruntime`** (já instalado na VM), sem o pacote `nudenet`:
  resolve o fato de o auto-update não instalar dependência. Pré e pós-processamento em
  numpy.
- Política como **tabela versionada no código**, com as classes fechadas por você (§5.3 do
  plano). A foto guarda `versão do modelo + versão da política + classes + scores`
  (invariante 6).
- **Retida não participa de nada** — nem do índice de rostos (`rostos_de`), nem de
  `/photos`, nem de `/img` (invariante 2), testado nas três portas.
- **Bloqueado pela decisão C.** Sem ela, a moderação não entra no código.

### 4.5 Monetização: a costura, sem cobrança

```
evento GRATUITO ──► contratante escolhe plano ──► pagamento CRIADO ──► PENDENTE
                                                                        │
            limites do plano valem ◄── CONFIRMADO ◄── webhook validado ◄┘
                                          │
                                          └──► ESTORNADO / EXPIRADO / CANCELADO
```

- **Limites resolvidos no servidor** por uma função só (`limites_do_evento`): as 50 fotos,
  a moderação e a retenção passam a vir do plano. **No piloto todo evento é o plano
  gratuito**, com exatamente as regras de hoje.
- **Interface de provedor** — `criar_cobranca_pix`, `consultar`, `validar_webhook` — com
  **um único provedor agora: o falso**, que não faz rede e confirma sob comando de teste.
- **Chaves e credenciais só em variável de ambiente no servidor.** Nada no front, nada no
  repo. O front recebe no máximo o **texto do PIX copia-e-cola e a imagem do QR**, que são
  públicos por natureza.
- **Três travas contra cobrança acidental:** `flag:pagamento_ativo` desligada; provedor
  configurado = `falso`; e rota de webhook que responde 404 enquanto não houver provedor
  real. Um teste prova que, nesse estado, **nenhuma cobrança real consegue ser criada**.
- **Ligar em produção depois** = escolher o PSP (ADR), escrever o provedor real contra a
  mesma interface, configurar a env na VM e ligar a flag. **Sem mexer em login, evento ou
  fluxo.**

### 4.6 Operação (`/ops`) — o que entra, com a evidência de por que

| Área | O que mostra / faz | Evidência de que precisa |
|---|---|---|
| Agora | eventos ao vivo, fila, P95 recebida→entregue, erros das últimas horas | o SLA recebida→entregue não tem medição hoje |
| Fila | profundidade, idade do item mais antigo, erros, **nova tentativa** | invariantes 1 e 8; "fila não é capacidade" |
| Capacidade | CPU, memória, disco, **minutos para zerar a fila no ritmo atual** | risco nº 1 do plano |
| Erros por rota | contador + últimos erros, sem PII | IDEIAS-V2 A-bis #1: "um 500 some no log" |
| Moderação | retidas **por evento e por idade** (sem liberar), **retiradas** com prazo | decisão 4 + art. 21 |
| Eventos · contas · participantes | o que já existe hoje, reorganizado; participante **só em número**, nunca rosto por rosto | minimização (LGPD) |
| Entregas | a auditoria da ADR-0035, com filtro | já existe na API, falta tela |
| Flags | liga/desliga com registro | `config` já existe |
| Auditoria | toda ação destrutiva, **inclusive as rotas antigas** (`zerar`, `conta/excluir`, `compactar`, `expirar`) | IDEIAS-V2 A-bis #11: "não existe" |
| Diagnóstico | testar foto, saúde, versão no ar | já existe |

**Ação destrutiva:** reautenticação recente + confirmação **digitando o nome do alvo**, num
modal da própria página (não `prompt()` — não funciona em PWA no Android) + linha em
`admin_auditoria`.

**O que fica fora, de propósito:** navegar rosto por rosto de participante, entrar como
outro usuário, gráfico que não responde pergunta nenhuma de operação.

---

## 5. Design system da Fiesta

> Direção pedida: *Bauhaus + fotografia + tecnologia + festa + excelente UX* — sem
> caricatura histórica e sem carnaval visual. A proposta abaixo é a **gramática**; valores
> finais saem da fase de design system (§7), revisados por contraste e com as telas reais.

### 5.1 O princípio que evita a caricatura

**Cor e forma são sintaxe, não enfeite.** Na Bauhaus caricata, círculo amarelo e quadrado
vermelho decoram. Aqui cada forma **diz alguma coisa**, sempre a mesma coisa, nas três
experiências — e a cor viva de verdade vem das **fotos**, que são o conteúdo.

| Forma | Vem de | Significa |
|---|---|---|
| **Círculo** | a lente, o diafragma | pessoa, rosto, **estado de uma foto** |
| **Retângulo** | o quadro, a folha de contato | foto, evento, bloco de conteúdo |
| **Linha** | a linha do tempo, o filme | fila, progresso, sequência |

### 5.2 Estados como forma (e não só como cor)

Acessível por construção: quem não distingue cor distingue forma.

| Estado | Forma | Cor | Texto |
|---|---|---|---|
| Recebida | círculo **vazado** | tinta | "Recebida" |
| Em análise | **meio círculo** | amarelo-flash | "Em análise — a anfitriã revisa quando puder" |
| Entregue | círculo **cheio** | cobalto | "Entregue a 3 pessoas" |
| Erro | **quadrado** | vermelho-alarme (≠ coral) | o que houve + o que fazer |
| Carregando | diafragma que **abre** | tinta | nenhum — a forma basta; respeita movimento reduzido |
| Vazio | um círculo vazado e uma ação | — | "Tire a primeira foto da festa" |

### 5.3 Tokens (proposta)

| Nome | Valor | Papel |
|---|---|---|
| `papel` | `#FFFFFF` | fundo: folha branca, não creme |
| `tinta` | `#000000` | texto e estrutura: preto de verdade, não quase-preto |
| `coral` | `#F2542D` | **assinatura da Fiesta** e ação principal (texto preto sobre ele — contraste ≈ 6,4:1) |
| `flash` | `#FFC400` | em análise, destaque |
| `cobalto` | `#2346D8` | entregue, confiança, links (texto branco — ≈ 7,5:1) |
| `alarme` | `#C8102E` | erro — **separado do coral**, para a marca nunca ler como erro |

**Tipografia — duas famílias, papéis claramente distintos:**
- **Jost** (display): sans geométrica da linhagem da Futura, que é contemporânea da
  Bauhaus. Pesos altos, poucas palavras.
- **Archivo** (interface e dados): grotesca com **eixo de largura** — expandida nos
  títulos do contratante, **condensada nas tabelas densas da operação**, com números
  tabulares.

**Formas de borda:** só dois raios — **zero** (retângulo, foto, bloco) e **50 %** (círculo).
Estrutura com borda preta de 2 px; dado denso com fio de 1 px. Sem sombra difusa e sem
cartão arredondado em tudo.

**Grid e espaço:** base 8 px. Participante em 4 colunas no celular; contratante e operação
em 12. Composição **assimétrica controlada**: o bloco de cor fica sempre ancorado num lado,
nunca centralizado por padrão.

### 5.4 As três experiências — mesma gramática, três temperamentos

| | Participante | Contratante | Operação |
|---|---|---|---|
| Temperamento | rápido, divertido, uma mão só | premium, calmo, controle | denso, técnico, diagnóstico |
| Tela-mãe | celular, 360 px | desktop e celular | desktop |
| Gesto central | **botão-lente**: círculo coral grande, ancorado embaixo à direita | **revisar retidas**: uma foto por vez, publicar ou apagar pelo teclado | **ler o estado**: fila, erros e capacidade numa só tela |
| Cor | coral e flash com generosidade | cobalto e tinta; coral só na ação | tinta e fio; cor **só** para estado |
| Tipo | Jost grande, pouco texto | Archivo expandida, respiro | Archivo condensada, tabular |
| Detalhe do assunto | contador como **rolo de filme**: "12 / 50 poses" | a festa como **cartaz**: nome, data e QR num bloco | a fila como **linha do tempo** de formas |
| Movimento | foto chegando "revela" (uma vez, com propósito) | confirmação de ação | nenhum decorativo |

---

## 6. Testes — a tarefa não termina quando a tela aparece

| Camada | O que prova | Como |
|---|---|---|
| **Contrato** (estilo de hoje, Python) | cada invariante; a matriz de papéis (§4.1) célula a célula; limite de 50 com **envios concorrentes**; estados da fila; retida fora de `rostos_de`/`/photos`/`/img`; pedido de remoção; **registro de criança inexistente**; auditoria; máquina de pagamento; webhook idempotente e com assinatura; **login de teste ausente em produção**; **nenhuma cobrança real possível com as travas** | `tests/`, dentro do `todos.sh`, **com prova do vermelho** |
| **Fila durável** | reiniciar no meio do processamento não perde nem duplica | teste que derruba o worker e sobe de novo |
| **Regressão** | modo fotógrafa e empresa intactos | as 367 checagens atuais continuam verdes a cada passo |
| **Modelo real** | o caminho completo com buffalo_s e a moderação reais | smoke com uvicorn, como os de 11 e 12/09 |
| **Navegador** | participante no celular (375 px), contratante no desktop, operação | Playwright — **ADR primeiro** (dependência nova, ~300 MB de navegador, roda fora do `todos.sh`) |
| **Acessibilidade** | contraste, foco visível, teclado, leitor de tela, movimento reduzido | axe-core no Playwright (dependência nova, na mesma ADR) + revisão manual |
| **Performance da página** | peso da página do participante, tempo até a galeria em 4G simulado | Playwright com rede limitada; **orçamento definido por medição**, não chutado |
| **Carga — os três números** | (1) throughput e latência da VM real; (2) custo da moderação na VM real; (3) P95 recebida→entregue sob carga | script Python com `httpx` assíncrono (já é dependência de teste), **na VM de verdade** |
| **Moderação** | falso positivo em **traje de banho, piscina e pouca luz** | continuação do `experimento_moderacao.py` |

---

## 7. Ordem de implementação — cada fase com porta de saída

| Fase | Entrega | Porta de saída (evidência) |
|---|---|---|
| **0 · Decidir** | suas respostas às decisões A–D; ADRs: Fiesta (dados + papéis + fila), moderação, front e design system, pagamento, operação e auditoria, testes de navegador | ADRs aceitas por você |
| **1 · Pré-requisitos** | limite de tamanho e tipo + rate limit em `/ingest` e `/selfie`; flags em `config`; auditoria administrativa ligada nas rotas antigas; remoção do `artifact.html` | contrato verde + deploy verificado pelo SHA |
| **2 · Motor da Fiesta** | dados, token do participante, fila durável, rotas, limite atômico, remoção, retirada, pagamento com provedor falso | um teste por regra, com prova do vermelho; regressão verde |
| **3 · Medir** | teste de carga na VM real com a fila de verdade; moderação na VM | **os três números no BENCHMARKS**, e o teto do piloto (decisão M) |
| **4 · Design system** | tokens, tipografia, estados, componentes, página-vitrine dos componentes | contraste e foco conferidos; revisão sua da vitrine **antes** das telas |
| **5 · Participante** | QR → selfie + apelido → enviar → estados → minhas / todas → remover | E2E no celular + acessibilidade |
| **6 · Contratante** | festa, QR, galeria, retidas, pedidos, resumo, área de plano (só leitura no piloto) | E2E desktop e celular |
| **7 · Operação** | `/ops` com as áreas do §4.6 | E2E + auditoria conferida |
| **8 · Piloto fechado** | uma festa adulta pequena, com você presente | fotos enviadas, retidas, retidas por engano, entregas erradas reportadas, P95 recebida→entregue |

A moderação (dentro das fases 2 e 3) **só entra se a decisão C estiver fechada**. Sem ela, o
piloto não abre: foto imprópria na galeria é a vergonha máxima do plano.

---

## 8. O que eu não vou fazer

- Reverter decisão fechada sem perguntar (crianças, telão, só a dona libera).
- Tocar o `/ingest` síncrono, o `index.html` do modo fotógrafa ou a fila IndexedDB existente.
- Instalar dependência nova sem ADR — nem Playwright, nem axe-core, nem SDK de pagamento.
- Colocar chave, token ou credencial no front ou no repositório.
- Ligar qualquer cobrança real.
- Criar funcionalidade de operação que não responda a uma pergunta de operação.
- Declarar "pronto" porque a tela apareceu.

---

## Fontes externas (consultadas em 2026-09-12)

- Licença de modelos treinados com YOLO — [Ultralytics License](https://www.ultralytics.com/license) · [issue #2129](https://github.com/ultralytics/ultralytics/issues/2129)
- Metadados do `320n.onnx` — lidos localmente com `onnx.load` (NudeNet 3.4.2)
- Marco Civil da Internet, art. 21 — [texto comentado](https://modeloinicial.com.br/lei/L-12965-2014/marco-civil-internet/art-21)
