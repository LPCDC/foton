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
- **Status:** SUPERSEDED por ADR-0015 (motor trocado para buffalo_s/SCRFD+ArcFace)
- **Status (histórico):** ACCEPTED (para o MVP) — revisar se aparecer gargalo de precisão em fotos reais
- **Data:** 2026-08-24
- **Decisão:** MVP usa **facial self-hosted** — YuNet (detecção) + SFace (embedding), ONNX/OpenCV, CPU. Sem API gerenciada.
- **Contexto:** EXP-05 mediu **97,2%** no LFW, **~6 ms/rosto** em CPU, **~R$0** de custo, dados sob nosso controle. O critério do dono foi "que fique de uma forma confiável" — self-hosted entrega isso sem enviar rostos a terceiro (melhor p/ LGPD, ADR-0005) e sem custo por chamada.
- **Alternativas:** AWS Rekognition / Azure Face (mais simples, mas custo por chamada, rostos vão a terceiro, dependência externa).
- **Justificativa:** decidido por dado (EXP-05): precisão suficiente, latência desprezível, custo zero, privacidade sob controle.
- **Consequências:** exige hospedar o modelo (37MB) num worker Python. Precisão em **fotos reais de evento** (ângulo/blur/multi-face) ainda é UNKNOWN → EXP futuro com fotos reais pode forçar reavaliação. Comparação com gerenciado fica arquivada como opção de contingência.

## ADR-0010 — Stack do MVP: Netlify + Supabase + Cloudflare R2 + FastAPI
- **Status:** SUPERSEDED por ADR-0014 (infra) e ADR-0016 (app: sem Supabase/R2, monólito FastAPI+SQLite)
- **Status (histórico):** ACCEPTED
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

## Decisões resolvidas (2026-08-24) — histórico, ver ADR-0015/0016 para o que roda hoje
Provider de nuvem, linguagem do backend, storage/CDN e feed ao vivo saíram de "adiadas" e viraram ADR-0010/0011: **Supabase + Netlify + Cloudflare R2 + FastAPI (Python)**, feed via **Supabase Realtime**. Match = brute-force cosine (EXP-06), sem índice dedicado nessa escala. **Esse desenho foi abandonado na prática** — produção roda o monólito da ADR-0016.

## Estado real de hoje (2026-08-28) — ver `BLUEPRINT.md` para o quadro completo
Motor facial: **buffalo_s/SCRFD+ArcFace** (ADR-0015). Stack: **FastAPI + SQLite, um processo só** (ADR-0016). Infra: **Oracle VM própria** (ADR-0014). Domínio: **duckdns + foton.app.br em paralelo** (ADR-0017, em propagação). Modelo comercial: **créditos, pagamento único** (ADR-0012, segue válido — mas ver `BLUEPRINT.md` §10, a própria cliente propôs recorrência, decisão do dono em aberto).

## Ainda adiado (aguarda dado ou decisão)
Preço final (aguarda EXP-10, custo por evento real) · gateway de pagamento (pós-validação) · modelo de recorrência vs. pagamento único (proposta da cliente, ver BLUEPRINT §10) · edge/offline, NFC, edição por IA, estilos artísticos de renderização (pós-piloto — ver `docs/PILOTO-1.md`).

## ADR-0014 — Infraestrutura própria: Oracle Cloud Always Free (São Paulo)
- **Status:** ACCEPTED — em uso
- **Data:** 2026-08-28
- **Decisão:** o Fóton passa a rodar em **VM própria na Oracle Cloud Always Free**, região **sa-saopaulo-1** (baixa latência no Brasil), com SQLite em disco persistente da VM. Render fica como ambiente de teste/backup.
- **Contexto:** o free tier da Render tem **disco efêmero** — um deploy zerava o banco (álbum da fotógrafa sumia). A Oracle Always Free dá VM de verdade, disco persistente, 10 TB de tráfego/mês e **não expira**.
- **Como ficou:** VM `foton-server` (`VM.Standard.E2.1.Micro`, 1 vCPU / 1 GB + **2 GB de swap**), IP `152.67.46.113`. Ubuntu + nginx (80) → uvicorn (127.0.0.1:8000) → SQLite em `/opt/foton/data`. systemd com `Restart=always` e boot automático.
- **Alternativas:** Turso/Neon/Supabase (bancos gerenciados, mas free tier alheio e Supabase pausa em 7 dias) · Litestream+R2 (elegante, peça extra) · Render pago (~R$40/mês).
- **Aprendizados (registrados para não repetir):**
  1. **ARM sem estoque em São Paulo** — `VM.Standard.A1.Flex` deu "out of capacity" em 2/12 e 1/6. O script cai para **x86 E2.1.Micro** automaticamente (2 dessas são Always Free e quase sempre têm estoque).
  2. **Firewall em dois níveis** — Security List (nuvem) **e** iptables (dentro da VM). Abrir só um não funciona; o instalador faz os dois.
  3. **Cloud Shell em modo FIPS** recusa chaves ed25519 → usar **RSA**.
- **Consequências:** 1 GB de RAM é apertado para o ArcFace (~380 MB medidos) — daí o swap; se faltar fôlego, migrar para ARM quando houver estoque (o script já tenta ARM primeiro). **Falta HTTPS** (obrigatório para a câmera do convidado ligar) — próximo passo, com domínio.
- **Atualização (2026-08-28):** HTTPS resolvido (Let's Encrypt, `infra/https.sh`) no dia seguinte a este ADR. O gargalo de hoje não é RAM nem HTTPS — é **reputação do domínio** `duckdns.org` (Chrome mostra "Site perigoso"); ver ADR-0017.

## ADR-0015 — Reconhecimento facial em produção: InsightFace buffalo_s (SCRFD+ArcFace)
- **Status:** ACCEPTED — em uso em produção
- **Data:** 2026-08-24 (nunca documentado formalmente até agora — código e ADR haviam divergido)
- **Decisão:** o motor que roda em produção **não é** o YuNet+SFace da ADR-0009. É o
  **InsightFace `buffalo_s`** (SCRFD para detecção + ArcFace para embedding), ONNX/CPU,
  `det_size=640`, limiar de cosseno **0,25**.
- **Contexto:** o pacote `buffalo_s` do InsightFace embute os dois modelos com uma API
  pronta (`FaceAnalysis`) e pesa pouco (~16 MB), cabendo versionado no repo (ver `.gitignore`,
  que abre exceção só para ele). `det_size=320` deixava rosto de 90px **não detectado**
  (0/6 numa bateria de teste) — `det_size=640` corrigiu.
- **Justificativa:** 99,5% no LFW (medido), mesma família usada por plataformas líderes,
  sem custo por chamada, sem enviar rosto a terceiro (LGPD, ADR-0005).
- **Consequências:** o número de precisão da ADR-0009 (97,2%, YuNet+SFace) está **obsoleto** —
  não descreve o motor que roda hoje. `det_size=640` custa mais CPU que 320; mitigado por
  `Image.draft()` no pré-processamento (ver `docs/BENCHMARKS.md`, 2026-08-28).

## ADR-0016 — Simplificação do stack: um único processo (FastAPI + SQLite + HTML estático)
- **Status:** ACCEPTED — em uso em produção
- **Data:** 2026-08-24 a 2026-08-28 (retroativo — nunca documentado formalmente)
- **Decisão:** abandonado o desenho de 4 serviços da ADR-0010. Produção roda **um único
  processo Python** (`app/test_rig/rig.py`) que serve API **e** front-end (`app/web/index.html`
  via `StaticFiles`), com **SQLite** (`store.py`) no lugar de Supabase/Postgres, autenticação
  própria (PBKDF2 + token de sessão) no lugar de Supabase Auth, e **sem** Cloudflare R2 — as
  fotos ficam como BLOB no próprio SQLite.
- **Contexto:** a ADR-0014 já havia trocado a infra (Render→Oracle VM) por causa do disco
  efêmero. Na prática, ao construir o piloto real, o Supabase/R2/Netlify-para-o-app nunca
  chegaram a ser usados — o caminho mais simples (que cumpria "simplicidade é requisito",
  CLAUDE.md §4.3) foi manter tudo num processo só, com o Netlify sobrando só como **demo
  estática antiga** (não serve o app de produção).
- **Alternativas:** implementar a ADR-0010 como planejada (mais peças para operar sozinho,
  sem ganho medido) · manter o monólito (menos peças, mais fácil de depurar e fazer deploy
  com `git push`).
- **Justificativa:** o dono opera sozinho; menos serviços = menos coisa para quebrar. Cumpre
  o SLA medido (ver BENCHMARKS) sem a complexidade extra.
- **Consequências:** fotos como BLOB no SQLite limita escala (mitigação futura: R2, ver
  BLUEPRINT §9 "Depois") — hoje o disco tem folga (40,5 GB livres, medido). Sem Realtime do
  Supabase, o feed do convidado é **polling** (`/feed`, `/stats`), não push — funciona no
  volume medido, mas não escala para milhares de convidados simultâneos sem revisão.

## ADR-0017 — Domínio próprio para sair da reputação ruim do duckdns.org
- **Status:** ACCEPTED — em execução (DNS em propagação)
- **Data:** 2026-08-28
- **Decisão:** o app passa a responder também em `app.foton.app.br` (domínio próprio,
  registrado no Registro.br), mantendo `getfoton.duckdns.org` funcionando em paralelo.
- **Contexto:** o Chrome mostra **"Site perigoso"** ao abrir `getfoton.duckdns.org` no
  celular do convidado. Não é o certificado (TLS 1.3 válido) — é reputação de domínio:
  `duckdns.org` é muito usado em golpe, e o classificador do Safe Browsing pesa isso mais
  a página pedir câmera + nome + telefone. Isso mataria o piloto sozinho: ninguém escaneia
  um QR que abre alerta vermelho.
- **Alternativas:** pedir para o convidado ignorar o aviso (inaceitável — parece golpe de
  verdade) · trocar de provedor de DNS dinâmico (mesmo problema de reputação, outro domínio
  genérico) · **domínio próprio** (resolve na raiz).
- **Justificativa:** é a única correção real; qualquer outra é gambiarra.
- **Consequências:** certificado precisa cobrir os dois domínios (`infra/dominio.sh`,
  `--expand`); o painel mostra `FOTON_HOST` correto para a configuração de FTP da câmera;
  o duckdns **não é desligado** — QR já impresso, PWA instalado e o monitor externo não
  podem quebrar na troca.

## ADR-0018 — Web Share Target: o menu "Compartilhar" do Android vira entrada de fotos
- **Status:** ACCEPTED — em produção
- **Data:** 2026-08-29
- **Decisão:** o PWA declara `share_target` no manifest e o **service worker** atende o
  `POST /compartilhar` que o Android faz. As fotos são guardadas num cache próprio
  (`foton-compartilhado`), a página reabre em `/?compartilhado=<id>`, lê o lote, escolhe
  o evento e envia pelo caminho de sempre (`reduzir → /ingest → reconhecimento`).
- **Contexto:** a promessa feita à cliente é "clicar e a foto já ir pro Fóton". A Canon R8
  já resolve metade: `Funções de comunicação → Enviar para smartphone após o disparo →
  Envio automático` deposita cada foto no celular sozinha. Faltava o elo celular → Fóton.
  **Nem a R8 nem a T6s têm FTP** (verificado no menu das duas, presencialmente), então o
  servidor FTP do Fóton — que funciona — não serve para esta cliente.
- **Alternativas:**
  - **Só o seletor de arquivos** (o que existia): obriga abrir o app, achar o evento e
    navegar na pasta antes de selecionar. É o caminho longo.
  - **App Android nativo** vigiando a pasta: chega a zero gesto por foto, mas é outro
    artefato para construir, assinar e manter, e ela precisa instalar fora da loja.
  - **EOS Utility num notebook** + pasta vigiada: zero gesto e funciona nas **duas**
    câmeras, mas põe notebook e cabo no evento.
  - **Web Share Target:** nada para instalar além do próprio PWA, roda no que já existe.
- **Justificativa:** é o maior ganho por unidade de risco. Não toca no pipeline, não
  adiciona dependência, não cria rota nova de servidor que aceite foto — reaproveita o
  `/ingest` autenticado. **Não chega a zero gesto**: a seleção das fotos na galeria
  continua sendo humana (ver `docs/BENCHMARKS.md`). As duas alternativas de zero gesto
  ficam registradas acima para decisão do dono.
- **Consequências:**
  - O `activate` do service worker **não pode** apagar `foton-compartilhado` — apagaria um
    lote em trânsito. Está no filtro e tem teste (`tests/test_autorizacao.py`, seção 11).
  - O lote fica no cache só até a página consumi-lo; sobra de mais de 1h é descartada.
    Foto de evento é dado de terceiro, não pode virar entulho no celular.
  - `POST /compartilhar` existe também no servidor, **só para degradar**: devolve página
    explicando, em vez de 405. Ela **não ingere foto** — o POST do Android não carrega o
    token da conta, e aceitar arquivo sem dono abriria upload anônimo (a armadilha das
    "rotas destrutivas sem dono", já paga).
  - Só existe com o app **instalado** como PWA, e só no Android/Chrome. Sem instalar, o
    menu não aparece e o botão "Enviar foto da câmera" continua sendo o caminho.
  - PWA **já instalado** pode precisar ser reinstalado para o Chrome reler o manifest e
    registrar o alvo de compartilhamento.
