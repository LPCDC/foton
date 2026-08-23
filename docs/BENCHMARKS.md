# BENCHMARKS.md — Registro de Medições (SaaS em nuvem)

> Fonte de verdade do SLA. Nada é "otimizado" ou "aceito" sem número aqui.
> **Regra:** valor não medido = `UNKNOWN — REQUIRES EXPERIMENT`. Proibido inventar.
> Alvo global: **end-to-end P95 < 10 000 ms** (disparo → foto no celular do convidado), **medido sobre hotspot 4G/5G real**.

---

## 1. Latência por estágio (caminho de nuvem)

| # | Métrica | Estágio | Unid. | P50 | P95 | P99 | Amostras | Condições | Status |
|---|---------|---------|-------|-----|-----|-----|----------|-----------|--------|
| 1 | Upload latency (shutter → arquivo na nuvem) | Uploader | ms | — | — | — | — | — | UNKNOWN — REQUIRES EXPERIMENT |
| 2 | Ingest/validação | (1) | ms | — | — | — | — | — | UNKNOWN — REQUIRES EXPERIMENT |
| 3 | Processing (watermark + otimização) | (2) | ms | 502 | 533 | 542 | 30 | **PROXY** 24MP sintético · CPU-only (Ryzen 7800X3D) · long-edge 2048 · q82 · 1 img | MEASURED (proxy) |
| 4 | Detecção + embedding | (3) | ms | — | — | — | — | — | UNKNOWN — REQUIRES EXPERIMENT |
| 5 | Match c/ selfies | (4) | ms | — | — | — | — | — | UNKNOWN — REQUIRES EXPERIMENT |
| 6 | Entrega / feed no navegador | (6) | ms | — | — | — | — | — | UNKNOWN — REQUIRES EXPERIMENT |
| 7 | **End-to-end (shutter → convidado)** | todos | ms | — | — | — | — | hotspot real | **UNKNOWN — REQUIRES EXPERIMENT** |
| 8 | Selfie → match (caminho do convidado) | (3)+(4) | ms | — | — | — | — | — | UNKNOWN — REQUIRES EXPERIMENT |

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

| Opção | Precisão | Latência P95 (ms) | Custo / 1k imgs | Privacidade | Status |
|-------|----------|-------------------|-----------------|-------------|--------|
| API gerenciada (ex.: Rekognition/Azure) | — | — | — | rostos vão a terceiro | UNKNOWN — REQUIRES EXPERIMENT |
| Self-hosted (ex.: InsightFace/GPU) | — | — | — | dados sob nosso controle | UNKNOWN — REQUIRES EXPERIMENT |

## 5. Qualidade do match

| Métrica | Unid. | Valor | Status |
|---------|-------|-------|--------|
| Precisão de detecção facial | % | — | UNKNOWN — REQUIRES EXPERIMENT |
| Precisão / recall do match (selfie → fotos) | % | — | UNKNOWN — REQUIRES EXPERIMENT |
| Falsos positivos | % | — | UNKNOWN — REQUIRES EXPERIMENT |

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
