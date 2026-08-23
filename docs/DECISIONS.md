# DECISIONS.md — Architecture Decision Records (ADRs)

> Nenhuma decisão arquitetural importante é tomada em silêncio.
> Cada ADR: **Decisão · Contexto · Alternativas · Justificativa · Consequências · Status**.
> Status: `PROPOSED` · `ACCEPTED` · `REJECTED` · `SUPERSEDED` · `OPEN` (aguarda experimento/decisão).

Formato para copiar:

```
## ADR-XXXX — <título curto>
- **Status:** ...
- **Data:** AAAA-MM-DD
- **Decisão:** ...
- **Contexto:** ...
- **Alternativas:** ...
- **Justificativa:** ...
- **Consequências:** ...
```

---

## ADR-0001 — Repositório git dedicado para o projeto
- **Status:** ACCEPTED
- **Data:** 2026-08-23
- **Decisão:** criar um repo git próprio em `C:\Users\Pichau\Menir ClickPal`, isolado do repo da home. **Aprovado pelo dono em 2026-08-23; `git init` executado + `.gitignore` protegendo biometria/segredos/binários.**
- **Contexto:** a pasta **não** é um repo; está aninhada no repo cuja raiz é `C:/Users/Pichau` (home inteira sob versionamento). Commitar aqui poluiria/arriscaria esse repo.
- **Alternativas:** usar o repo da home (rejeitado: escopo errado/risco) · subpasta ignorada (frágil) · repo dedicado (limpo).
- **Justificativa:** isolamento, histórico próprio, `.gitignore` para dados sensíveis/binários.
- **Consequências:** requer `git init` + `.gitignore` (selfies/embeddings/segredos fora do versionamento). **Nada será commitado até aceite.**

## ADR-0006 — Formato do produto: SaaS em nuvem (não edge)
- **Status:** ACCEPTED
- **Data:** 2026-08-23
- **Decisão:** o produto é um **SaaS em nuvem, sem hardware no evento**. Descartado o caminho edge/appliance para o MVP.
- **Contexto:** o cliente-alvo (fotógrafa) não é técnico e exige **turnkey**. Um appliance é um produto de hardware caro de fabricar/suportar. O mercado prova que dá pra ser "na hora" na nuvem (SpotMyPhotos ~2,5s).
- **Alternativas:** appliance turnkey (complexo, hardware) · software no notebook dela (performance/suporte incertos) · **nuvem (mais simples de construir, vender, suportar)**.
- **Justificativa:** simplicidade e velocidade de chegar a produto; equipamento do cliente vira irrelevante.
- **Consequências:** **depende de Internet no local** (mitigado por hotspot 4G/5G). Custo de nuvem por evento entra na economics. Biometria trafega/processa na nuvem → cuidado de privacidade (ADR-0005). Edge/offline vira tier premium **futuro**.

## ADR-0007 — Matching por selfie + reconhecimento facial
- **Status:** ACCEPTED
- **Data:** 2026-08-23
- **Decisão:** o convidado registra **1 selfie**; o sistema casa as fotos por reconhecimento facial e monta o feed pessoal.
- **Contexto:** entregar "na hora" por foto sem capturar dado do convidado a cada clique exige um registro friccionless. Padrão do mercado e do briefing.
- **Alternativas:** entrega direta por foto (exige identificar cada foto manualmente) · galeria geral (sem privacidade).
- **Justificativa:** remove o atrito; escala em festa grande.
- **Consequências:** exige engine facial + índice; biometria sensível (ADR-0005). Precisão/recall viram alvo de benchmark.

## ADR-0008 — Tratamento = watermark + otimização (sem IA de cor no MVP)
- **Status:** ACCEPTED
- **Data:** 2026-08-23
- **Decisão:** o "tratamento na hora" é **watermark + resize/otimização web**. Sem edição automática de cor/exposição no MVP.
- **Contexto:** edição por IA pesa no pipeline e ameaça o P95<10s.
- **Alternativas:** edição por IA (pós-MVP, benchmark) · edição manual do fotógrafo (deixa de ser "na hora").
- **Justificativa:** cabe folgado nos 10s; entrega valor imediato.
- **Consequências:** cor/exposição saem como da câmera. Edição por IA fica no backlog como diferencial futuro.

## ADR-0009 — Reconhecimento facial: gerenciado vs self-hosted
- **Status:** OPEN
- **Data:** 2026-08-23
- **Decisão:** *(pendente do S0)* escolher entre **API gerenciada** (ex.: AWS Rekognition / Azure Face) e **modelo self-hosted** (ex.: InsightFace em GPU de nuvem).
- **Contexto:** gerenciado = mais simples e rápido de subir; self-hosted = mais controle de custo/privacidade, sem enviar rostos a terceiro.
- **Alternativas:** ver EXP-05 (precisão × latência × custo × privacidade).
- **Justificativa:** decidir por dado, não por preferência.
- **Consequências:** afeta custo por evento, latência e a política de privacidade (ADR-0005).

## ADR-0005 — Privacidade dos dados biométricos
- **Status:** ACCEPTED
- **Data:** 2026-08-23
- **Decisão:** selfies/rostos/embeddings são **efêmeros**, atados à sessão do evento, descartados ao fim, salvo consentimento explícito. Consentimento no fluxo; sem PII em logs/URLs; QR/sessão com expiração.
- **Contexto:** processamento de biometria **na nuvem** exige cuidado reforçado (LGPD).
- **Alternativas:** retenção por padrão (rejeitado) · biometria sem consentimento (rejeitado).
- **Justificativa:** minimização de dados; confiança do convidado.
- **Consequências:** exige TTL de sessão, expiração de link, política de retenção; se facial for gerenciado, avaliar trânsito/armazenamento dos dados. Base legal final vira ADR ao ser definida com o operador.

---

## ADRs aposentadas pelo pivô para nuvem (2026-08-23)
- **ADR-0002** (CUDA/`nvidia-smi` no Edge Server), **ADR-0003** (toolchain CV local), **ADR-0004** (env Python isolado — agora só do LAB), e o desenho de **entrega híbrida / Cloudflare Tunnel / appliance**: `SUPERSEDED` por **ADR-0006**. A GPU do LAB permanece relevante só para medir o facial self-hosted (EXP-05).

## Decisões deliberadamente adiadas (sem ADR, aguardam S0)
Provider de nuvem · linguagem do backend · motor de índice/match · formato do feed ao vivo (push vs polling) · storage/CDN específico. Cada uma vira ADR **após** os benchmarks.
