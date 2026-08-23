# ARCHITECTURE.md — Foto na Hora (SaaS em nuvem)

> Arquitetura **proposta** (não implementada). Validada empiricamente no Sprint S0.
> Toda decisão marcante vira ADR em `docs/DECISIONS.md`.

---

## 1. Ambiente — o LAB de desenvolvimento (≠ produto)

> ⚠️ O PC abaixo é a **bancada de desenvolvimento e benchmark**. **Não** é o equipamento do cliente, nem o alvo de deploy. O produto roda **na nuvem**; a fotógrafa não instala nada pesado.

Inspeção em **2026-08-23**, host `C:\Users\Pichau\Menir ClickPal`.

| Item | Valor |
|------|-------|
| SO | Windows 11 Pro 10.0.26200 (x64) |
| CPU | AMD Ryzen 7 7800X3D — 8C/16T |
| RAM | 31,15 GB total (4,55 GB livres na inspeção) |
| GPU | NVIDIA RTX 4070 Ti — **12 GB** (11,99 confirmado), driver 32.0.15.9571; **`nvidia-smi` fora do PATH → CUDA não verificado** |
| Python | 3.13.2 (miniconda base); envs `menir`, `sdxl` em `E:\Conda\envs` |
| Node/npm | v24.14.0 / 11.9.0 · **Git** 2.51.0 · **Docker** presente |
| Discos livres | C: 73 GB · E: 118 GB · F: 106 GB · G: 62 GB |
| Toolchain ausente | cmake, gcc/g++, MSVC, rustc, ffmpeg, exiftool, ImageMagick |
| Repo git | **Sem repo dedicado** — a pasta está aninhada no repo da home `C:/Users/Pichau` (ADR-0001) |

**Uso do LAB:** desenvolver o backend, prototipar, e **medir o facial self-hosted** (EXP-05) na RTX para comparar com a API gerenciada. Só isso.

## 2. Visão Geral

SaaS: câmera → um serviço na nuvem → app web do convidado. Cada foto carrega um `photo_id` de rastreio por todos os estágios. Nada roda no evento além da câmera + um celular/hotspot.

```
Câmera (JPEG via Wi-Fi/FTP nativo, ou uploader leve em cel/notebook tethered)
        │  (rede: hotspot 4G/5G)
        ▼
┌───────────────────────── SERVIÇO NA NUVEM ─────────────────────────┐
│ (1)Ingest → (2)Watermark+Otimização → (3)Detecção+Embedding         │
│      → (4)Match c/ selfies registradas → (5)Storage(object)+CDN     │
│      → (6)Entrega no feed pessoal do convidado                      │
│  transversais: (7)Config de evento · (8)Observabilidade/custo       │
│               (9)Resiliência (fila de upload, retry, dedup)         │
└───────────────┬─────────────────────────────────┬──────────────────┘
                │ QR do evento                     │ API
   [Convidado] ─┴─► app web (sem instalar) ─selfie─┴─► galeria pessoal AO VIVO → download
   [Fotógrafo] ───► painel: cria evento, mostra QR, vê uploads
```

## 3. Componentes (fronteiras e contratos)

Cada componente é isolado, substituível e mensurável. Comunicação por contrato/evento, nunca por acoplamento direto.

### (0) Uploader (borda, no lado da câmera)
- **Responsabilidade:** levar o JPEG da câmera à nuvem o mais rápido e confiável possível; fila local com retry se a Internet oscilar.
- **Caminho:** `UNKNOWN — REQUIRES EXPERIMENT` (S0). Candidatos: Wi-Fi/FTP nativo da câmera (R8) · app uploader leve em celular/notebook tethered (provável para a T6).
- **Saída (contrato):** `PhotoUploaded{ photo_id, event_id, source_camera, bytes, checksum, t_shutter?, t_received }`.
- **Métrica dona:** *upload latency*, *file completeness*.

### (1) Ingest (nuvem)
- Recebe o upload, valida, cria `photo_id`, enfileira. Idempotente por checksum (dedup).

### (2) Image Processing
- Decode JPEG → resize/derivadas → **watermark** → otimização web. **Sem edição de cor por IA no MVP.**
- **Métrica dona:** *processing latency*.

### (3) Face Detection + Embedding
- Localiza rostos e gera embeddings. **Default MVP: API gerenciada** (ex.: AWS Rekognition / Azure Face). Alternativa a comparar: **self-hosted** (ex.: InsightFace em GPU de nuvem) por custo/privacidade/latência — ADR-0009 / EXP-05.
- **Métrica dona:** *detection+embedding latency*, precisão.

### (4) Match
- Casa os embeddings da foto com as **selfies registradas** do evento; adiciona a foto ao feed de cada convidado correspondente.
- **Métrica dona:** *match latency*, precisão/recall, falsos positivos.

### (5) Storage + CDN
- JPEGs tratados em object storage; entrega via CDN. URLs com escopo/expiração.

### (6) Entrega / Feed do convidado
- **Feed pessoal ao vivo** (web push ou polling — a decidir por dado). A foto aparece "na hora".
- **Métrica dona:** *browser delivery latency*.

### (7) Event Configuration
- Evento, watermark, retenção/privacidade/consentimento, QR, limites. Declarativo, sem hardcode.

### (8) Observability
- Logs estruturados, latência por estágio (P50/P95/P99), throughput, **custo por evento** (compute+storage+banda+face API). Fonte de verdade do SLA.

### (9) Resiliência
- Fila de upload com retry/backoff, dedup por checksum, reprocessamento idempotente, degradação graciosa quando a Internet oscila. Alvo do Roadmap S7.

### (App do convidado) e (Painel do fotógrafo)
- Convidado: web, sem instalar — QR → selfie → feed ao vivo → download.
- Fotógrafo: painel simples — criar evento, obter QR, acompanhar uploads. **Turnkey.**

## 4. Contrato de Rastreio

Todo estágio emite `{ photo_id, stage, t_in, t_out, latency_ms, status }`. O `photo_id` nasce no Uploader e é a chave do **end-to-end** e dos percentis.

## 5. Estágios de Latência mapeados ao SLA

`shutter → upload → ingest → processing → detection+embedding → match → CDN → browser`. A soma governada por P95 tem que ficar **< 10 s** — medida sobre **hotspot real** (`docs/BENCHMARKS.md`).

## 6. Não-decisões (abertas, a decidir por dado no S0)

Provider de nuvem · linguagem do backend · facial gerenciado vs self-hosted · motor de índice/match · formato do feed ao vivo (push vs polling). Todas viram ADR **após** os benchmarks.

## 7. Guardado para pós-MVP

Edge/offline (locais sem sinal) · privacidade-como-argumento · NFC/pulseira · edição de cor por IA · associação por RFID/EXIF (Foolography).
