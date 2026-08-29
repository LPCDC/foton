# BENCHMARKS.md — Registro de Medições (SaaS em nuvem)

> Fonte de verdade do SLA. Nada é "otimizado" ou "aceito" sem número aqui.
> **Regra:** valor não medido = `UNKNOWN — REQUIRES EXPERIMENT`. Proibido inventar.
> Alvo global: **end-to-end P95 < 10 000 ms** (disparo → foto no celular do convidado), **medido sobre hotspot 4G/5G real**.

---

## 0. Status — EM PRODUÇÃO (atualizado 2026-08-28)

> ⚠️ A seção original desta parte (S0 "parcial/pausado", de 2026-08-23) descrevia um
> momento pré-produto. Ela fica logo abaixo, sem alterar, como registro histórico —
> os números medidos ali (EXP-04/05/06) continuam corretos como medições **do motor
> antigo (YuNet+SFace)**, hoje substituído por buffalo_s/SCRFD+ArcFace (ADR-0015).

**Estado real de hoje:**
- App em produção, com cliente real (Patrícia). Ver `BLUEPRINT.md`.
- **Caminho celular→app medido em produção** (não mais proxy sintético): 1 foto de câmera
  isolada cabe no SLA de 10s; rajada grande ainda não (ver entradas de 2026-08-28 abaixo).
- **Caminho FTP direto validado ponta a ponta** com cliente de script real (login,
  envio, foto entrando sozinha no evento) — **ainda não testado com uma câmera Canon
  física**. É o próximo passo (`docs/ROTEIRO-CAMERAS.md`).
- O "risco principal" de 2026-08-23 (upload de JPEG grande domina o orçamento) **se
  confirmou** e já tem mitigação medida: reduzir a foto no celular antes de subir
  (2,9× mais rápido) + `Image.draft()` no servidor (2,7× mais rápido) — ver entradas
  de 2026-08-28.

---

## 0-histórico. Status do S0 — como estava em 2026-08-23 (não reflete hoje)

**Provado sem câmera (compute, CPU-only, LAB Ryzen 7800X3D):**
- ✅ EXP-04 processing (watermark+otimização): P95 **533 ms**.
- ✅ EXP-05 facial self-hosted (YuNet+SFace): **97,2%** no LFW, **~6 ms/rosto** P95.
- ✅ EXP-06 match (busca vetorial): **<1 ms** até 100k rostos.
- → Compute total **< 0,6 s/foto**, sem GPU, sem API paga. Facial self-hosted escolhido (confiável, ~R$0).

**Bloqueado — aguarda câmeras R8/T6 + hotspot 4G/5G:**
- ⛔ EXP-01/02 (upload câmera→nuvem) · EXP-03 (throughput rede) · EXP-08 (E2E <10s) · EXP-07 (concorrência) · EXP-09 (resiliência).

**Pendente de credencial do dono (opcional):** comparação com face API gerenciada.

**Risco principal em aberto:** o upload domina o orçamento. JPEG full-res 24MP (~10 MB) num 4G ~10 Mbps ≈ **~8 s** → pode estourar. **Mitigação a testar com a câmera:** disparar JPEG menor (M/S ~3 MB) ou reduzir antes de subir. Sobra de orçamento pós-compute: **~9,4 s**.

**Para retomar:** R8 e T6 fisicamente + um hotspot 4G/5G. Rodar EXP-01→03, depois EXP-08.

---

## 1. Latência por estágio (caminho de nuvem)

| # | Métrica | Estágio | Unid. | P50 | P95 | P99 | Amostras | Condições | Status |
|---|---------|---------|-------|-----|-----|-----|----------|-----------|--------|
| 1 | Upload latency (shutter → arquivo na nuvem) | Uploader | ms | — | — | — | — | — | UNKNOWN — REQUIRES EXPERIMENT |
| 2 | Ingest/validação | (1) | ms | — | — | — | — | — | UNKNOWN — REQUIRES EXPERIMENT |
| 3 | Processing (watermark + otimização) | (2) | ms | 502 | 533 | 542 | 30 | **PROXY** 24MP sintético · CPU-only (Ryzen 7800X3D) · long-edge 2048 · q82 · 1 img | MEASURED (proxy) |
| 4 | Detecção + embedding (por rosto) | (3) | ms | ~5.2 | ~6.2 | ~6.8 | 2000 | YuNet+SFace · **CPU-only** · det ~1.4 + emb ~3.8 (P50) | MEASURED |
| 5 | Match c/ selfies (galeria 100k) | (4) | ms | 0.6 | 0.7 | 0.9 | 200 | brute-force cosine · CPU · 128-d | MEASURED |
| 6 | Entrega / feed no navegador | (6) | ms | — | — | — | — | — | UNKNOWN — REQUIRES EXPERIMENT |
| 7 | **End-to-end (shutter → convidado)** | todos | ms | — | — | — | — | hotspot real | **UNKNOWN — REQUIRES EXPERIMENT** |
| 8 | Selfie → match (detect+embed+busca) | (3)+(4) | ms | ~6 | ~7 | ~8 | — | selfie detect+embed ~5ms + match <1ms · CPU | MEASURED (composto) |

## 2. Throughput

| Métrica | Unid. | Valor | Condições | Status |
|---------|-------|-------|-----------|--------|
| Upload em hotspot 4G/5G | MB/s | — | — | UNKNOWN — REQUIRES EXPERIMENT |
| Fotos processadas por minuto | fotos/min | — | — | UNKNOWN — REQUIRES EXPERIMENT |
| Convidados simultâneos (feed ao vivo) | sessões | — | — | UNKNOWN — REQUIRES EXPERIMENT |
| Selfies/matches por segundo | req/s | — | — | UNKNOWN — REQUIRES EXPERIMENT |

## 3. Recursos (amostrados nos testes)

| Recurso | Ocioso | Sob carga (P95) | Pico | Status |
|---------|--------|-----------------|------|--------|
| Backend CPU (%) | — | — | — | UNKNOWN — REQUIRES EXPERIMENT |
| Facial GPU (%) — se self-hosted | — | — | — | UNKNOWN — REQUIRES EXPERIMENT |
| Facial VRAM (GB) — se self-hosted | — | — | — | UNKNOWN — REQUIRES EXPERIMENT |
| Backend RAM (GB) | — | — | — | UNKNOWN — REQUIRES EXPERIMENT |

## 4. Facial: gerenciado vs self-hosted (EXP-05 / ADR-0009)

| Opção | Precisão (LFW) | Latência P95/rosto | Custo | Privacidade | Status |
|-------|----------|-------------------|-----------------|-------------|--------|
| **Self-hosted YuNet+SFace (CPU)** | **97,2%** | **~6 ms** | ~R$0 (só CPU, sem API) | dados sob nosso controle | **MEASURED** |
| API gerenciada (ex.: Rekognition/Azure) | — | — | — | rostos vão a terceiro | UNKNOWN — aguarda credencial do dono |

## 5. Qualidade do match

| Métrica | Unid. | Valor | Status |
|---------|-------|-------|--------|
| Cobertura de detecção (LFW) | % | 100 (0/2000 falhas) | MEASURED — set frontal fácil |
| Acurácia de verificação (LFW @cos 0.363) | % | 97,2 | MEASURED |
| Precisão / recall do match em fotos de evento reais | % | — | UNKNOWN — REQUIRES EXPERIMENT (fotos reais c/ ângulo/blur/multi-face) |

## 6. Custo por evento (economics)

> **Premissa de referência:** 1 evento = ~500 fotos processadas (~400KB cada = ~200MB) · ~150 convidados · egress de entrega ~10-20GB (cada convidado vê/baixa suas fotos). Valores abaixo são **ESTIMATED — de preços públicos 2026** (pesquisa, não medição). EXP-10 confirma com uso real.

| Item | Unid. | Valor | Premissa | Status |
|------|-------|-------|----------|--------|
| Face API (self-hosted, ADR-0009) | R$/evento | **~0** | roda em CPU no nosso worker, sem custo por chamada | ESTIMATED (EXP-05) |
| Storage R2 (ADR-0011) | R$/evento | **~0,02** | 200MB × US$0,015/GB/mês ≈ US$0,003 | ESTIMATED |
| **Egress / entrega (R2)** | R$/evento | **~0** | R2 **não cobra egress** — mesmo servindo 20GB | ESTIMATED |
| Compute (processing) | R$/evento | **~0** (free tier) / marginal desprezível | Render web free 750h/mês; 500 fotos × 0,5s = ~4min de CPU | ESTIMATED |
| Supabase (DB+Auth+Realtime) | R$/evento | **~0** (free tier) | 150 convidados « 50k MAU; « 200 conexões realtime | ESTIMATED |
| **Custo marginal por evento** | R$/evento | **~R$0,05-0,30** | dominado por storage; egress zero é o pulo do gato | **ESTIMATED — confirmar em EXP-10** |
| Custo **fixo** de infra | R$/mês | **~0** (free) → **~R$35** (Render US$7 quando houver clientes) | acordar worker antes do evento evita cold start | ESTIMATED |

**Conclusão de economics:** o custo **marginal** por evento é ~centavos (egress zero + facial self-hosted). O único custo relevante é o **fixo mensal baixo** de hospedagem. → **Pagamento único é sustentável** (ADR-0012): mesmo um pacote de 20 eventos custa <R$6 de infra marginal. Fontes: [Supabase free tier](https://uibakery.io/blog/supabase-pricing), [Cloudflare R2 egress $0](https://egresscost.com/cloudflare/), [Render free tier](https://www.saaspricepulse.com/tools/render).

## 7. Orçamento de latência (a validar contra 10s)

```
shutter→upload + ingest + processing + detect+embed + match + CDN + browser  <  10 000 ms (P95, hotspot real)
   (?)            (?)      (?)          (?)            (?)      (?)     (?)
```
Todos `UNKNOWN` até o S0.

## 8. Como registrar um benchmark

1. Descreva o experimento (objetivo, ambiente, dados, N amostras, **rede: hotspot real**).
2. Relógio monotônico por estágio; colete recursos e, quando aplicável, custo.
3. Calcule P50/P95/P99, throughput e custo.
4. Preencha a linha + anexe script/dados.
5. Falhou o alvo → Gauntlet: REJECT/REFINE + ADR em `docs/DECISIONS.md`.

---

### Histórico de execuções

**2026-08-23 · S0-EXP-04 (processing)** — `experiments/exp04_processing/`
- **Proxy:** imagem sintética 24MP (6000×4000, 15,5MB); câmeras indisponíveis. Mede latência, não qualidade.
- **Ambiente:** LAB, CPU-only (Ryzen 7 7800X3D), Pillow 12.3.0, Python 3.12, 30 iters + 3 warmup.
- **Pipeline:** decode → resize(long-edge 2048, LANCZOS) → watermark → encode JPEG q82 optimize+progressive.
- **Resultado:** total P50 **502ms** / P95 **533ms** / P99 542ms. Saída 2048×1365, ~403KB.
- **Dono do estágio:** resize domina (~282ms) e decode (~186ms); watermark é desprezível (~1,5ms).
- **Conclusão:** processamento de 1 foto cabe folgado nos 10s. Otimização futura possível (paralelizar nos 16 threads, decode mais rápido), mas **não é prioridade** — medir antes upload e facial. `ACCEPT` provisório para o orçamento de latência.

**2026-08-23 · S0-EXP-05 (facial self-hosted)** — `experiments/exp05_facial/`
- **Engine:** OpenCV 5.0.0 · YuNet 2023mar (detecção) + SFace 2021dec (embedding), ONNX, **CPU-only** (wheel sem CUDA).
- **Dataset:** LFW pairs subset=test (1000 pares, 500/500), imagens frontais.
- **Precisão:** acurácia **97,2%** @cos 0,363 (melhor 97,2% @0,344). Cosseno médio iguais 0,64 / diferentes 0,08. Cobertura de detecção 100% (0/2000 falhas).
- **Latência (por rosto, CPU):** detecção P50 1,4 / P95 1,7 ms; embedding P50 3,8 / P95 4,5 ms. Throughput 174 rostos/s (1 thread).
- **Conclusão:** facial **não é o gargalo** — ~6 ms/rosto P95, custo ~R$0, dados sob nosso controle → forte para **confiabilidade** e economics. `ACCEPT` provisório do self-hosted.
- **Ressalvas:** LFW é frontal/limpo; **fotos reais de evento** (ângulo, blur, multi-face, oclusão) darão precisão menor → EXP futuro com fotos reais. GPU não testada (wheel sem CUDA); não é necessária dado o resultado em CPU. Comparação com API gerenciada pendente de credencial do dono.

**2026-08-23 · S0-EXP-06 (selfie→match / busca vetorial)** — `experiments/exp06_match/`
- **Método:** brute-force cosseno em CPU/numpy, embeddings 128-d (dim do SFace), 200 iters/tamanho.
- **Resultado:** galeria 1k = 0,015 ms · 10k = 0,13 ms · **100k = 0,6 ms (P95 0,7)**; memória 100k = 51 MB.
- **Conclusão:** busca vetorial é **desprezível** no orçamento; **não precisa de FAISS/índice** nessa escala. Caminho do convidado (selfie detect+embed ~5ms + match <1ms) ≈ **~6 ms**.

**2026-08-28 · Reduzir a foto NO CELULAR antes de subir** — produção (`getfoton.duckdns.org`, VM 1 vCPU / 1 GB)
- **Hipótese:** o servidor já reduz para 2048 px de lado maior. Reduzir antes de enviar não perde
  qualidade e tira bytes da rede **e** a decodificação de 24 MP do único núcleo.
- **Método:** mesma imagem, 4000×3000. Envio real por HTTPS, de fora. Rajada = 4 envios em paralelo.
- **Cuidado obrigatório:** o canvas descarta o EXIF → sem `imageOrientation:'from-image'` a foto chega
  deitada e o rosto não é detectado. Verificado no navegador (10,5 MB → 1,91 MB, 4000×3000 deitada →
  1536×2048 em pé, 159 ms no aparelho).

| | 11,6 MB (como era) | 2,1 MB (como é agora) | ganho |
|---|---|---|---|
| 1 foto, ponta a ponta | **9,07 s** | **3,17 s** | 2,9× |
| processamento no servidor | 3.701 ms | 993 ms | 3,7× |
| rajada de 4 | **25,1 s** | **9,3 s** | 2,7× |

- **Leitura honesta:** foto isolada passou a caber folgado no SLA de 10 s. Rajada de 4 = 9,3 s;
  extrapolando, 20 fotos ≈ 46 s (antes ~125 s). **Rajada grande ainda não cabe em 10 s.**
- **Assimetria importante:** isto vale para o caminho **celular → app**. A câmera por **FTP manda o
  arquivo original**, sem redução possível no cliente — continua em ~9 s por foto. Hoje o celular é
  o caminho MAIS RÁPIDO, não o contrário.
- **Próximo experimento proposto:** `Image.draft()` do Pillow decodifica o JPEG já em escala reduzida.
  Deve derrubar os 3,7 s de processamento da foto grande e beneficiaria os **dois** caminhos.
  `UNKNOWN — REQUIRES EXPERIMENT`.

**2026-08-28 · `Image.draft()` — decodificar o JPEG já reduzido** — produção (VM 1 vCPU / 1 GB)
- **Método:** MESMA foto nos dois lados (4000×5000, 20 MP, 1,8 MB, com um rosto), 2 envios cada.
- **Alvo do draft = 1024 e não 2048:** pedindo 2048 o PIL escolhe escala 1/1 e não economiza nada.

| | antes | depois | ganho |
|---|---|---|---|
| processamento no servidor | 1.537–1.690 ms | **556–633 ms** | 2,7× |
| total ponta a ponta | 1.920–2.886 ms | **868–926 ms** | ~2,5× |
| rostos detectados | 1 | **1** | sem regressão |
| imagem entregue | 1638×2048 | **1638×2048** | idêntica |

- **Conclusão:** `ACCEPT`. Beneficia os **dois** caminhos — inclusive o FTP da câmera, que manda o
  arquivo original e não pode ser reduzido no cliente.
- **Ressalva medida:** numa origem perto de 4000 px de lado maior a saída fica 2000 px em vez de
  2048 (2,3% menor). Numa foto de câmera de 6000×4000 a saída é **idêntica**.

---

**2026-08-29 · Gestos humanos até a foto entrar no Fóton — Web Share Target** — produção
(`https://app.foton.app.br`), Chrome, service worker ativo e controlando

**Por que medir isto:** a promessa feita à cliente é "clicar e a foto já ir pro Fóton". A
R8 já resolve a primeira metade sozinha (`Envio automático` deposita cada foto no celular).
O que sobrou é gesto humano no celular — e gesto é a unidade que decide se ela usa ou
abandona o produto no meio da festa.

**Método:** contador de cliques instalado na página real (`addEventListener('click', …,
true)` em `button/.evt/label/a`), fluxo disparado com cliques e submissão de formulário
reais, contra produção. O POST de compartilhamento foi reproduzido exatamente como o
Android faz: `<form method=POST action=/compartilhar enctype=multipart/form-data>` com o
campo `fotos`. Reprodutível: as chamadas estão no corpo desta seção.

### Medido — gestos DENTRO do Fóton, por lote

| Caminho | Gestos no Fóton | O que ela toca |
|---|---|---|
| Antigo (`Enviar foto da câmera`) | **2** | toca no evento · toca em "Enviar foto da câmera" |
| Novo (`Compartilhar → Fóton`) | **0** | nada — o lote entra sozinho no evento certo |

Cenário do teste = o cenário real dela: **5 eventos ao vivo na conta** (eventos antigos
nunca foram encerrados). Mesmo assim: 0 gestos, e as fotos foram para o evento certo
(o último que ela abriu), com os outros 4 eventos intactos.

| Verificação em produção | Resultado |
|---|---|
| 5 fotos compartilhadas → publicadas | 5/5, **10,4 s** o lote (≈2,1 s cada) |
| 2 fotos com rosto de verdade pelo share | publicadas, **1 rosto detectado**, marca d'água aplicada |
| Caminho antigo depois de mexer | 2/2 publicadas em **1,9 s** — intacto |
| Evento de destino entre 5 ao vivo | correto; os outros 4 sem nenhuma foto a mais |
| Cache do lote depois do envio | **vazio** — não fica foto de terceiro no celular |
| Sem service worker: `POST /compartilhar` | **200** com página explicando (antes: **405**) |
| Deslogada no meio | lote **espera**, sobe sozinho depois do login — nada perdido |

### Contado, NÃO medido — o fluxo inteiro por 100 fotos

Os gestos do lado do Android (galeria, menu Compartilhar) **não foram medidos**: não há
aparelho Android nesta sessão. A contagem abaixo vem do fluxo documentado do Android.

| Etapa | Antigo | Novo |
|---|---|---|
| abrir o app / a galeria | 1 | 1 |
| navegar até a pasta da Canon | ~2 | 0 |
| entrar em modo de seleção | 0 | 1 |
| **selecionar 100 fotos** | **100** | **99 tocando uma a uma, ou 1 arrastando** |
| confirmar / Compartilhar | 1 | 1 |
| escolher o Fóton no menu | 0 | 1 |
| dentro do Fóton (medido) | 2 | **0** |
| **total por 100 fotos** | **~106** | **~103 tocando · ~5 arrastando** |

### Leitura honesta

- O que este trabalho eliminou de fato: **os 2 gestos dentro do Fóton e a navegação de
  pastas**. Isso está medido e está em produção.
- O que ele **não** eliminou: **a seleção das fotos na galeria continua sendo humana.**
  Nenhuma API web no Android permite um site enxergar a galeria ou uma pasta — o
  `showDirectoryPicker()` só existe no Chrome de desktop. Não há gambiarra possível aqui.
- Portanto o ganho real depende de um fato do aparelho dela:
  **`UNKNOWN — REQUIRES EXPERIMENT`: a galeria da Patrícia seleciona por arrasto
  (segurar a primeira foto e arrastar) ou "selecionar tudo"?**
  - **Se sim:** ~5 gestos por 100 fotos, contra ~106. Promessa cumprida na prática.
  - **Se não:** ~103 contra ~106. A promessa **não** está cumprida e a decisão passa para
    as alternativas de zero gesto (`docs/PILOTO-1.md`).
- **Experimento para fechar isto (5 minutos, no celular dela):** abrir a galeria, segurar
  uma foto e arrastar o dedo sobre as seguintes. Contar quantos toques para marcar 20.
  Depois: Compartilhar → Fóton, e cronometrar até a última foto aparecer no painel.
- **Lotes grandes, não pequenos:** o custo fixo do share (~4 gestos) só compensa se ela
  mandar muitas fotos de uma vez. Compartilhar de 10 em 10 dá ~150 gestos por 100 fotos —
  **pior** que o caminho antigo. Isso precisa entrar no roteiro do dia.
- **Não medido aqui:** se o Fóton de fato aparece no menu Compartilhar do celular dela.
  Isso exige o app instalado como PWA num Android real — `UNKNOWN — REQUIRES EXPERIMENT`.
  Todo o resto da cadeia (POST do Android → service worker → cache → app → `/ingest` →
  reconhecimento) está verificado em produção acima.
