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

## ADR-0009 — Reconhecimento facial: self-hosted (YuNet+SFace) para o MVP
- **Status:** ACCEPTED (para o MVP) — revisar se aparecer gargalo de precisão em fotos reais
- **Data:** 2026-08-24
- **Decisão:** MVP usa **facial self-hosted** — YuNet (detecção) + SFace (embedding), ONNX/OpenCV, CPU. Sem API gerenciada.
- **Contexto:** EXP-05 mediu **97,2%** no LFW, **~6 ms/rosto** em CPU, **~R$0** de custo, dados sob nosso controle. O critério do dono foi "que fique de uma forma confiável" — self-hosted entrega isso sem enviar rostos a terceiro (melhor p/ LGPD, ADR-0005) e sem custo por chamada.
- **Alternativas:** AWS Rekognition / Azure Face (mais simples, mas custo por chamada, rostos vão a terceiro, dependência externa).
- **Justificativa:** decidido por dado (EXP-05): precisão suficiente, latência desprezível, custo zero, privacidade sob controle.
- **Consequências:** exige hospedar o modelo (37MB) num worker Python. Precisão em **fotos reais de evento** (ângulo/blur/multi-face) ainda é UNKNOWN → EXP futuro com fotos reais pode forçar reavaliação. Comparação com gerenciado fica arquivada como opção de contingência.

## ADR-0010 — Stack do MVP: Netlify + Supabase + Cloudflare R2 + FastAPI
- **Status:** ACCEPTED
- **Data:** 2026-08-24
- **Decisão:** o MVP roda em quatro serviços, todos com free tier:
  - **Netlify (free)** — hospeda o front-end estático (painel da fotógrafa + app do convidado / PWA).
  - **Supabase (free)** — Auth (login/senha), PostgreSQL (usuários, eventos, fotos, embeddings), Realtime (feed ao vivo).
  - **Cloudflare R2** — storage + CDN das fotos (**egress zero**).
  - **FastAPI** num worker Python (Render/Railway) — pipeline: watermark + otimização + YuNet/SFace + match (ADR-0008/0009).
- **Contexto:** o dono perguntou se "Netlify grátis aguenta". Netlify grátis serve **só** front-end estático — não roda OpenCV, não tem banco/auth/storage. O pipeline pesado (modelo 37MB, deps nativas) precisa de um host Python real.
- **Alternativas:** tudo na AWS (mais poderoso, mais caro/complexo, não-turnkey p/ operar) · tudo em serverless (timeout de 10s mata o processamento + cold start do modelo) · Firebase (lock-in, egress caro). Números de free tier pesquisados (2026): Supabase 500MB DB / 1GB storage / 50k MAU / 200 conexões realtime; R2 10GB grátis + egress $0; Render web free 750h/mês (dorme após 15min).
- **Justificativa:** menor stack que cumpre o SLA, com custo ~R$0 no MVP; cada peça é substituível (§4 do CLAUDE.md) e tem free tier real.
- **Consequências:** 4 serviços a orquestrar (runbook em `app/README.md`). Render free dorme após 15min → **cold start ~30-60s**: acordar o worker antes do evento (ping) ou subir p/ plano pago (~US$7/mês) quando houver clientes. Provider trocável sem tocar no front-end (contratos explícitos).

## ADR-0011 — Storage/CDN das fotos: Cloudflare R2 (egress zero)
- **Status:** ACCEPTED
- **Data:** 2026-08-24
- **Decisão:** fotos processadas ficam no **Cloudflare R2**, servidas ao convidado pela CDN do R2.
- **Contexto:** servir foto ao convidado é o item que **mais consome banda** (egress). No S3 o egress é ~US$0,09/GB; no R2 é **US$0** (só paga storage US$0,015/GB/mês). Isso domina a economics por evento.
- **Alternativas:** AWS S3+CloudFront (egress caro) · Supabase Storage (só 1GB free, egress limitado) · Backblaze B2 (bom, mas R2 integra melhor com CDN e egress zero).
- **Justificativa:** egress zero derruba o custo marginal por evento para ~centavos → **viabiliza o one-time payment** (ADR-0012).
- **Consequências:** conta Cloudflare + bucket R2. Front-end aponta pra URL do R2. TTL/expiração das fotos do evento seguem ADR-0005.

## ADR-0012 — Modelo comercial do MVP: pagamento único / créditos por evento
- **Status:** ACCEPTED
- **Data:** 2026-08-24
- **Decisão:** vender **pagamento único** (não assinatura). A fotógrafa compra um **pacote de N eventos** (créditos) e usa quando quiser, sem vencimento mensal. Login/senha dá acesso ao painel; consumir um evento debita um crédito.
- **Contexto:** a primeira cliente (Patrícia) **não quer mensalidade**. O custo marginal por evento é ~R$0 (ADR-0011 + facial self-hosted ADR-0009), então o único custo real é o fixo de hospedagem (baixo) → pagamento único é sustentável.
- **Alternativas:** assinatura mensal (rejeitada pela cliente) · por-foto (atrito de cobrança) · lifetime ilimitado (risco de custo se usar muito — reservado como oferta de early-adopter negociada caso a caso).
- **Justificativa:** casa com o desejo da cliente e com a estrutura de custo (marginal ~zero).
- **Consequências:** preço final aguarda EXP-10 (custo por evento medido). Enquanto isso, a plataforma já implementa **contador de créditos por conta**. Cobrança/checkout de verdade (gateway) fica pós-validação — no MVP os créditos são atribuídos manualmente pelo operador.

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

## ADR-0013 — Nome/marca do produto: "Fóton" (tagline "fotos na hora")
- **Status:** ACCEPTED — **pendente clearance final** (INPI + domínio + @Instagram)
- **Data:** 2026-08-24
- **Decisão:** a marca é **Fóton**; "fotos na hora" vira **tagline** descritiva. Logo = o próprio fóton (ponto de luz + lampejo), **sem ícone de câmera**.
- **Contexto:** "Foto na Hora" é termo **genérico/descritivo**, amplamente usado no mercado BR (Fuzuê Fotos na Hora, "foto impressa na hora", Media Pix, etc.) → não registrável no INPI, domínio/Instagram saturados, invisível na busca.
- **Alternativas:** Faísca, Lampejo, Confete (todas apresentadas). Dono escolheu **Fóton** — premium, moderno, raiz "foto" (fóton = partícula de luz), *ownable*.
- **Justificativa:** marca distintiva e protegível; separa **marca** (Fóton) de **categoria** (fotos na hora).
- **Consequências:** antes de investir pesado, **clearance obrigatório**: busca INPI + registrar domínio (ex.: foton.com.br / getfoton) + @ no Instagram. Propagar o nome nos docs/README (ainda citam "Foto na Hora"). Watermark e UI já atualizados.

## Decisões resolvidas (2026-08-24)
Provider de nuvem, linguagem do backend, storage/CDN e feed ao vivo saíram de "adiadas" e viraram ADR-0010/0011: **Supabase + Netlify + Cloudflare R2 + FastAPI (Python)**, feed via **Supabase Realtime**. Match = brute-force cosine (EXP-06), sem índice dedicado nessa escala.

## Ainda adiado (aguarda dado)
Preço final (aguarda EXP-10, custo por evento real) · gateway de pagamento (pós-validação) · edge/offline, NFC, edição por IA (pós-MVP).
