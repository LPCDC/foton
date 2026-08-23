# BENCHMARKS.md — Registro de Medições (SaaS em nuvem)

> Fonte de verdade do SLA. Nada é "otimizado" ou "aceito" sem número aqui.
> **Regra:** valor não medido = `UNKNOWN — REQUIRES EXPERIMENT`. Proibido inventar.
> Alvo global: **end-to-end P95 < 10 000 ms** (disparo → foto no celular do convidado), **medido sobre hotspot 4G/5G real**.

---

## 0. Status do S0 — PARCIAL / PAUSADO (2026-08-23)

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

| Item | Unid. | Valor | Premissa | Status |
|------|-------|-------|----------|--------|
| Compute (processing + backend) | R$/evento | — | N fotos, M convidados | UNKNOWN — REQUIRES EXPERIMENT |
| Face API (se gerenciado) | R$/evento | — | — | UNKNOWN — REQUIRES EXPERIMENT |
| Storage + CDN (banda) | R$/evento | — | — | UNKNOWN — REQUIRES EXPERIMENT |
| **Custo total por evento** | R$/evento | — | — | **UNKNOWN — REQUIRES EXPERIMENT** |

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
