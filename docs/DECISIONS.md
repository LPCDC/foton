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

## ADR-0019 — A fotógrafa troca o próprio login e a própria senha
- **Status:** ACCEPTED — em produção
- **Data:** 2026-08-29
- **Decisão:** rota `POST /conta/credenciais` (autosserviço) que troca login e/ou senha,
  exigindo a **senha atual** além da sessão. Renomear a conta migra `event.dono`,
  `session` e a chave `ftp_visto:<login>`. O campo de login do app deixa de exigir
  formato de e-mail.
- **Contexto:** só o admin trocava senha (`/admin/senha`). Quando a senha da cliente
  apareceu em texto puro num repo público, ela **dependia do dono** para se proteger —
  numa madrugada, num fim de semana, no meio de um evento. Isso é falha de produto, não
  só de higiene.
- **Alternativas:** só admin (o que havia — a cliente refém do fornecedor) · e-mail de
  recuperação (exige servidor de e-mail, dependência nova, e ela nem sempre tem o
  e-mail à mão no evento) · **autosserviço com a senha atual** (nada novo no stack).
- **Justificativa:** menor stack que resolve. Não adiciona dependência nenhuma.
- **Consequências:**
  - **Pede a senha atual mesmo com sessão válida.** Celular destravado esquecido na mesa
    da festa não pode virar "troco a senha e tranco a dona fora da própria conta".
  - **Renomear-se para um login de `FOTON_ADMINS` seria virar admin sem senha de admin.**
    Bloqueado com 403 e com teste dedicado — era o buraco real desta rota.
  - O login **é a chave primária** da conta. Sem migrar `event.dono`, os eventos dela
    virariam órfãos: convidado vendo as fotos e a fotógrafa sem ver o evento — exatamente
    a armadilha já paga. A `logo` é coluna de `photographer` e viaja sozinha (com teste).
  - **A senha do FTP muda junto**, porque é derivada do login. O app avisa na tela.
  - A troca **derruba todas as sessões**, inclusive a de quem trocou — a rota devolve um
    token novo para não expulsar a própria dona no meio do evento.
  - O login não precisa mais ser e-mail. O servidor **sempre** aceitou (`cria_conta` só
    normaliza); era o `input type="email"` que barrava.

## ADR-0020 — QR por foto: a amiga que aparece junto leva a foto na hora
- **Status:** ACCEPTED — em produção
- **Data:** 2026-08-29
- **Decisão:** o visualizador de foto do convidado ganha um botão **QR**, ao lado de
  Salvar e Compartilhar. O QR aponta para o **próprio app** com aquela foto aberta
  (`/?ev=CODE&foto=ID`), não para o `.jpg` cru.
- **Contexto:** cena real de festa — a convidada abre a foto e a amiga do lado também
  aparece nela. Hoje a saída é "me manda depois", que quase sempre não acontece. O
  Compartilhar do sistema resolve quando as duas têm WhatsApp aberto e se conhecem; o QR
  resolve **de celular para celular, sem trocar contato**.
- **Alternativas:** só o Compartilhar do sistema (exige app de mensagem e contato) · QR
  apontando direto para o `.jpg` (abre uma imagem solta numa aba, sem botão de salvar e
  sem marca do Fóton) · **QR apontando para o app** com a foto aberta.
- **Justificativa:** reaproveita o que já existe — a rota `/qr` do servidor e o próprio
  visualizador. Zero dependência nova. E quem escaneia **vê o Fóton**, com a marca
  d'água da fotógrafa na foto: cada QR desses é propaganda das duas.
- **Consequências:**
  - **Não abre nada que já não estivesse aberto.** `/img/{evento}/{foto}.jpg` sempre foi
    público; o QR só torna prático o que a convidada quer fazer com a própria foto.
  - **A retenção de 90 dias continua valendo.** Passou disso, o link morre e quem
    escanear vê "esta foto não está mais disponível" — aviso, não erro.
  - Foto de demonstração (`assets/pXX.jpg`) não tem endereço público: o botão **some
    sozinho** em vez de gerar um QR quebrado.
  - Com 3 ações na barra, o contador "1 / 8" se esconde abaixo de 400 px de tela.
  - **Aberto:** se um dia a foto deixar de ser pública (link com escopo/expiração, como
    a §7 do CLAUDE.md prevê), este QR passa a precisar de um token próprio.
    `UNKNOWN — REQUIRES EXPERIMENT` até haver decisão sobre link temporário.

## ADR-0021 — Retenção de biometria POR CONTA (álbum permanente)
- **Status:** ACCEPTED — em produção
- **Data:** 2026-08-29
- **Decisão:** coluna `photographer.ret_bio_dias`. `NULL` = política geral (7 dias);
  `0` = **não expira**; `N` = N dias. Ligado só pelo admin, em `/admin/retencao`.
- **Contexto:** apareceu um terceiro tipo de uso — **álbum permanente** (GLAMON, salão em
  Santos): as **mesmas pessoas** voltam toda semana. Com os 7 dias globais, cada
  colaboradora refaria a selfie a cada 7 dias, o que inviabiliza o uso.
- **Alternativas:** baixar a retenção global (**recusado** — enfraquece a proteção de todo
  mundo por causa de um caso) · ignorar e deixar refazer a selfie (mata o caso de uso) ·
  **por conta**, que é o que se fez.
- **Justificativa:** a retenção curta é uma proteção de dado sensível, não um detalhe de
  implementação. Afrouxar tem que ser **explícito, restrito e visível** — nunca o padrão.
- **Consequências:**
  - É do **admin**, pede confirmação na tela, e o painel mostra em quais contas está
    ligado. Ninguém liga sem querer.
  - **Só faz sentido com base legal para isso.** Álbum de empresa com colaborador tem
    relação continuada; festa com convidado desconhecido **não tem**. Não ligar por
    conveniência.
  - `docs/TESTES.md` seção [17]: a biometria da conta isenta sobrevive à limpeza e a das
    outras não — as duas metades testadas.
  - Padrão de créditos subiu de 20 para **100** (`FOTON_CREDITOS_INICIAIS`).

## ADR-0022 — Miniatura como COLUNA, não como arquivo
- **Status:** PROPOSED — decisão do dono
- **Data:** 2026-08-30
- **Problema observado:** o álbum GLAMON com 89 fotos rola pesado no celular. A causa é
  medida, não suposta: a grade mostra miniaturas de ~110 px, mas baixa a **foto inteira**
  (`/img/...`, 2048 px, ~400 KB). São **~35 MB e 89 decodificações de 2048 px** para
  desenhar quadradinhos. `loading="lazy"` já existe — ele adia, não emagrece.
- **Decisão proposta:** uma coluna `photo.thumb` (BLOB) com a mesma imagem a **320 px,
  q70 (~15 KB)**, gerada **na mesma passada que já decodifica a foto** no `process_image`,
  e servida por `/img/{event}/{id}.jpg?t=1`.
- **Por que não as alternativas:**
  - *Arquivo separado por foto*: dobra o número de objetos, cria um estágio novo no
    pipeline, e é exatamente o que se quer evitar antes do R2.
  - *Redimensionar a cada requisição*: gasta o único núcleo justamente quando 30
    convidados estão rolando a galeria — competindo com o reconhecimento.
  - *Deixar o navegador encolher*: é o que acontece hoje, e é o problema.
- **Por que a coluna resolve sem custo de pipeline:**
  - **Não é arquivo novo.** É a mesma linha, no mesmo banco, no mesmo backup.
  - **Não é estágio novo.** O `process_image` já tem a imagem decodificada em memória;
    é um `resize` a mais (~10 ms), não uma segunda decodificação.
  - **Custo de disco desprezível:** 15 KB × 8 (as 7 cópias de backup) = 120 KB por foto,
    contra 3,2 MB da foto tratada. Menos de 4% a mais.
  - **Ganho:** a grade de 89 fotos cai de ~35 MB para **~1,3 MB** — 26× menos.
- **Fotos que já existem:** gerar a miniatura **na primeira vez que for pedida** e
  guardar. Espalha o custo em vez de exigir uma migração que trava a VM.
- **Consequências:** `store.salva_foto` ganha um parâmetro; `/img` ganha um modo; o
  front pede `?t=1` na grade e a foto inteira só no visualizador. Reversível: sem a
  coluna preenchida, cai na foto inteira, como hoje.

## ADR-0023 — Vídeo de até 15 s (plano; depende do R2)
- **Status:** PROPOSED — **bloqueado por object storage**
- **Data:** 2026-08-30
- **Decisão proposta:** aceitar clipes de até 15 s, entregues ao convidado pelo mesmo
  reconhecimento facial das fotos. **Só depois do R2** — e essa ordem não é preferência,
  é aritmética.
- **Por que vídeo EXIGE o R2 antes:**
  - Um clipe de 15 s a 1080p pesa **20–40 MB**. Hoje as fotos moram no SQLite e o backup
    guarda **7 cópias do banco inteiro**: cada byte conta **8×**.
  - **Um clipe custaria 160–320 MB de disco.** Com 40 GB livres, ~150 clipes enchem tudo
    — e derrubam a produção da fotógrafa junto, porque é o mesmo disco e o mesmo banco.
  - Com o R2, o banco guarda só a **chave** e os vetores; o arquivo nunca entra no backup.
- **Como o reconhecimento funciona em vídeo:** extrair **1 quadro por segundo** (≈15
  quadros), rodar neles o SCRFD+ArcFace que já existe, e indexar o clipe para todo mundo
  que aparecer em qualquer quadro. Não é motor novo — é o mesmo, aplicado a alguns
  quadros.
- **O custo de CPU é o segundo bloqueio, e é medido:** hoje uma foto leva ~400 ms de
  processamento. 15 quadros ≈ **6 s de CPU por clipe**, num núcleo só que já é o gargalo
  da avalanche de selfie (P95 de 8,2 s). Vídeo **sem mais CPU** transformaria cada clipe
  numa parada de 6 s para todo mundo.
- **Ordem obrigatória:** (1) R2 · (2) mais CPU · (3) fila com prioridade (selfie na
  frente do vídeo) · (4) só então o vídeo.
- **A decidir quando chegar a hora:** 1 quadro/s é suficiente ou perde quem aparece de
  relance? Guardar o clipe original ou uma versão reduzida? Áudio entra na retenção
  LGPD como dado novo? `UNKNOWN — REQUIRES EXPERIMENT`.


---

## ADR-0024 — Cortar o sistema de créditos: tudo grátis, com login

**Data:** 2026-08-30 · **Estado:** aceita · **Decisão do dono**

**Contexto.** Cada evento novo gastava 1 crédito; a conta nascia com 100. O contador já
tinha causado um incidente real: o app repete o `POST /event` até 8 vezes quando a rede
está ruim, e um único evento chegou a queimar 8 créditos em silêncio (corrigido em
2026-08-29 com `ja_existia`).

**Decisão.** Nesta fase **não se gasta nem se bloqueia crédito**. Login continua
obrigatório — grátis não é anônimo.

**Por que não apagar as colunas.** `credits` e `credits_total` ficam na base. Apagá-las
exigiria migração num banco em produção com cliente real, para ganhar nada. Elas guardam
o histórico e alimentam o painel do admin.

**O risco que isto cria, e como está guardado.** Um contador desligado pela metade é pior
que um contador ligado: se alguém religar o desconto sem religar a recarga, a fotógrafa
é bloqueada **no meio de uma festa**. O teste `[21]` de `tests/test_autorizacao.py`, que
guardava "8 tentativas = 1 crédito", agora guarda o **oposto** — que nada é gasto.

**O substituto planejado** é limite de **upload**, não crédito: mede o que de fato custa
(disco e CPU) e é o único número que a fotógrafa entende sem explicação. Ver
`docs/PRODUTO.md` §3c. **Ainda sem COGS medido** — `UNKNOWN — REQUIRES EXPERIMENT`.

---

## ADR-0025 — O cliente não decide quem é admin

**Data:** 2026-08-30 · **Estado:** aceita

**O que estava errado.** `EH_ADMIN` era `/^admin@/i.test(email)`. Quando o login de
administração virou `admin` (sem arroba), o teste passou a dar **falso**: o painel de
administração existia, o servidor autorizava, e **o botão nunca aparecia**. Um mês de
painel invisível por causa de um regex no cliente.

**Decisão.** Quem sabe quem é admin é o servidor — a lista `FOTON_ADMINS`. `/me` já
informava; `/login` e `/signup` passam a informar também. O cliente **obedece**, não
adivinha. Regra geral: **autorização nunca se infere do formato de um dado no cliente.**

---

## ADR-0026 — Login com Google para fotógrafas: não agora

**Data:** 2026-08-30 · **Estado:** aceita — rejeição fundamentada, não ausência de decisão

**Decisão.** O Fóton **não** oferece "Continuar com Google" nesta fase. Login continua
sendo só e-mail/senha (ADR-0019), com o autosserviço de troca já existente
(`/conta/credenciais`). A rejeição é condicionada a um gatilho explícito (fim desta ADR),
não é "nunca".

### 1. Que problema resolveria hoje — nenhum medido, e o canal que "ajudaria" já existe

Hoje há 3 contas em produção (Patrícia, Carol, GLAMON), todas provisionadas à mão pelo
dono. Ninguém jamais pediu recuperação de senha. Google login não reduziria o trabalho do
dono — ele continuaria criando a conta e vinculando o evento.

A premissa de que Google "ajudaria um canal de auto-cadastro futuro" (BLUEPRINT §9,
antes desta ADR) é parcialmente falsa: **o canal de auto-cadastro já existe e está no
ar** — `POST /signup` (`app/test_rig/rig.py:229`) é uma rota aberta, sem convite, que só
bloqueia quem tenta se registrar com um login da lista `FOTON_ADMINS`. Qualquer pessoa já
pode criar a própria conta com e-mail/senha hoje, sem uma linha de código nova. O que o
Google acrescentaria a isso não é *abrir* um canal — é reduzir o atrito de preencher dois
campos num formulário que já é aberto. É um ganho real, mas pequeno, e sem ninguém hoje
esbarrando nesse atrito.

Contra esse ganho pequeno pesa um negativo concreto e específico deste público: a
fotógrafa às vezes fotografa com **celular emprestado** (registrado no contexto desta
sessão). Numa tela de "Continuar com Google", o Android tende a sugerir a conta Google
**de quem é o dono do aparelho**, não da fotógrafa — mais confuso que digitar login e
senha, não menos. É o tipo de fricção que o desenho Bauhaus das telas existe para evitar.

### 2. Custo de implementação — não é trivial, e esbarra na ADR-0019

- **Biblioteca:** nenhuma dependência OAuth existe no projeto hoje (`requirements.txt`
  não tem `authlib`, `httpx` nem `requests`). A opção natural para Starlette/FastAPI é
  **Authlib** (`authlib.integrations.starlette_client.OAuth`) — mas é uma dependência
  nova, e o CLAUDE.md §4.3 exige justificativa para cada uma ("menor stack que cumpra o
  SLA"). Ainda não há justificativa medida (ver item 1).
- **Rotas novas:** no mínimo duas — `GET /auth/google/login` (redireciona para o Google)
  e `GET /auth/google/callback` (troca o código, busca o e-mail verificado, cria ou casa
  a conta, emite token de sessão pelo mesmo `store.novo_token` de hoje). O front, que é
  uma página só (`app/web/index.html`), precisaria tratar o retorno do redirect como já
  trata outros estados via querystring (padrão existente em `/?ev=&foto=` da ADR-0020).
- **Schema — o ponto que a investigação revelou e o prompt não previa:** `photographer`
  tem `email TEXT PRIMARY KEY, senha TEXT NOT NULL` (`store.py:17-19`). A ideia óbvia —
  "casar a conta pelo e-mail que o Google devolve" — **esbarra na ADR-0019**: aquela
  decisão tirou a exigência de formato de e-mail do campo de login exatamente para não
  prender a fotógrafa a um endereço real. Isso significa que **o login de uma conta em
  produção pode não ser um e-mail válido**, e casar automaticamente por igualdade de
  string com o e-mail do Google seria voltar a assumir algo que a própria ADR-0019
  removeu. Pior: casar uma conta existente pelo e-mail só porque bateu string abre uma
  superfície de sequestro de conta — nada hoje verifica que o dono do login "sabe" aquele
  e-mail, então um Google account com e-mail igual a um login por coincidência **não
  prova** ser a mesma pessoa.
  A forma correta exigiria uma coluna nova e estável — `google_id` (o `sub` do token,
  imutável, nunca o e-mail) — casando **só** por esse id, nunca por igualdade de texto
  com o login existente. Contas criadas via Google e sem senha escolhida receberiam um
  hash de senha aleatório e inutilizável (não uma coluna `senha` opcional — mantém o
  `NOT NULL` de hoje sem migração de nulidade). Isso é código novo real, não uma
  configuração.
- Nada disso é "não dá para fazer" — é "não é barato", e o custo cai justamente na área
  (identidade da conta) que a ADR-0019 acabou de deixar mais flexível.

### 3. Onde vive o client secret — mesmo rigor da semente do FTP, mas não o mesmo mecanismo

A semente do FTP (`ftp_camera.py:124`) é **autogerada** e vive no banco
(`store.segredo`, com fallback a env var) — não serve de modelo direto aqui, porque o
client secret do Google **não é gerado por nós**, é emitido pelo Console do Google e
tem que ser guardado tal como veio.

A única opção correta, com o repositório público: variável de ambiente na VM, nunca no
git — o mesmo princípio do CLAUDE.md §7 ("credenciais nunca no código").

Achado operacional relevante: `infra/instalar-foton.sh` **reescreve o arquivo do
systemd** inteiro (`/etc/systemd/system/foton.service`, linhas 47-61) toda vez que roda.
O auto-update de 2 min (`foton-update.timer`) **não** toca nesse arquivo — só faz
`git reset --hard` + `systemctl restart` — mas um reinstall completo (o script inteiro,
rodado via Cloud Shell para mudança de infra, ex.: migração para ARM cogitada na
ADR-0014) apagaria qualquer `Environment=` adicionado à mão para o secret, porque o
heredoc é fixo e commitado. Se um dia isto for implementado, o secret **não pode** ser um
`Environment=` colado à mão no unit — tem que ser `EnvironmentFile=/etc/foton.env`
referenciado (por **caminho**, não por valor) dentro do heredoc committed, apontando para
um arquivo que existe só na VM, criado uma vez à mão e nunca versionado. Sem isso, a
primeira reinstalação de infra depois de configurar o Google quebraria o login Google em
produção silenciosamente — a mesma classe de armadilha já paga com `FOTON_ADMINS`.

### 4. O que o dono precisaria fazer fora do código (não inventado aqui)

Sem credencial real, o máximo responsável é listar os passos, não fabricar valores:
1. Criar um projeto no **Google Cloud Console**.
2. Configurar a **tela de consentimento OAuth** (nome do app, e-mail de suporte, logo).
3. Registrar o **URI de redirecionamento** exato (`https://app.foton.app.br/auth/google/callback`
   — e provavelmente também o domínio antigo `getfoton.duckdns.org`, no mesmo espírito de
   "não quebrar o que já está impresso/instalado" da ADR-0017).
4. Gerar **Client ID + Client Secret**, e colocar o secret na VM como descrito no item 3
   — nunca no repo, nunca colado numa mensagem que vire commit.
5. **Ponto que pesa contra, e ecoa a ADR-0017:** enquanto o app OAuth não passa pela
   verificação do Google (exige política de privacidade publicada, prova de propriedade
   do domínio, e para "External" pode levar dias), a tela de login mostra o aviso
   **"O Google não verificou este app"** — para o mesmo público não-técnico que a
   ADR-0017 protegeu do aviso "Site perigoso" do Chrome. Trocar um aviso assustador por
   outro não é o ganho que se está buscando.

### 5. Convivência com "login por selfie" (`docs/PRODUTO.md` §3)

Não competem — são mecanismos diferentes e resolvem problemas diferentes. O bloqueio
central do login por selfie é a falta de e-mail para o segundo fator ("Rosto não é
senha… Não temos e-mail", PRODUTO.md §3, itens 2-3) mais a severidade de um falso
positivo virando login em conta errada. O Google **entrega um e-mail verificado**, o que
tecnicamente atenua o item 3 daquela lista — mas não entrega capacidade de **enviar**
e-mail (recuperação de senha continua sem infra própria) nem muda o limiar de 0,25 usado
para casar fotos, que a própria PRODUTO.md já registra como impróprio para autenticação.
Se um dia o login por selfie avançar, o Google pode virar a fonte do "e-mail" que falta
no fator 2 — mas isso é otimização de uma ideia hoje parada por decisão do dono, não uma
razão para adiantar o Google agora.

### Gatilho de reversão (escrito por extenso)

Revisitar quando **qualquer um** destes acontecer:
- existir um **canal de aquisição público de verdade** direcionando estranhos para
  `/signup` (ex.: o "site de marca" do BLUEPRINT §9 item 5 rodando com tráfego pago ou
  orgânico) — aí o atrito de dois campos passa a ter volume que justifica o custo do
  item 2 e o aviso do item 4;
- alguém pedir **recuperação de senha** de verdade (ainda não aconteceu);
- o domínio `foton.app.br` tiver reputação/verificação suficiente para não disparar o
  aviso "app não verificado" do item 4 (paralelo direto à condição que resolveu a
  ADR-0017).

### Consequências
- Nenhuma mudança de código nesta sessão. `/signup`, `/login`, `/conta/credenciais`
  seguem exatamente como estão.
- Se o gatilho disparar no futuro: exige plano escrito antes de código (biblioteca,
  coluna `google_id`, onde mora o secret via `EnvironmentFile`, como a conta com senha
  continua funcionando idêntica), as 4 suítes de `tests/todos.sh` passando, e teste
  manual em produção confirmando que o login antigo não regrediu — os mesmos critérios
  já deixados em `docs/PROMPT-PROXIMA-SESSAO.md`.

---

## ADR-0027 — Site de marca sem biblioteca de smooth-scroll (Lenis removido)

**Data:** 2026-08-30 · **Estado:** aceita

**Decisão.** O site de marca (`site/index.html`) deixa de usar **Lenis**. A rolagem
passa a ser a **nativa do navegador**, com `scroll-behavior:smooth` só para os links
âncora. GSAP + ScrollTrigger continuam — a animação não dependia do Lenis.

**Contexto.** O dono relatou, testando no navegador dele: *"a rolagem do botão do mouse
não funciona"*. O Lenis sequestra o evento de roda para interpolar a rolagem; quando essa
interpolação briga com o ambiente (roda de mouse com passo grande, aceleração do SO,
janela sem foco), o resultado é rolagem travada ou que não responde. É o modo de falha
clássico dessa classe de biblioteca.

**Alternativas.** Ajustar parâmetros do Lenis (`duration`, `smoothWheel`) — tentaria
adivinhar o hardware do usuário, e o benefício é puramente estético · trocar por
Locomotive Scroll — mesma classe de problema, outra dependência · **remover** e usar
rolagem nativa.

**Justificativa.** A rolagem funcionar é requisito; rolagem *interpolada* é enfeite. Uma
dependência que quebra a interação mais básica da página não paga o próprio custo
(CLAUDE.md §4.3: menor stack que cumpre o objetivo). ScrollTrigger funciona igual sem
engine de smooth-scroll nenhuma — nada de animação foi perdido.

**Consequências.**
- Uma dependência a menos vendorizada no HTML (~10 KB de JS removidos).
- `gsap.ticker.lagSmoothing(0)` **precisou ser mantida**: ela morava dentro do bloco do
  Lenis, mas não é dele. Sem ela o GSAP "absorve" travadas do navegador em vez de tocar
  a timeline, e a animação de abertura ficou presa no meio. Achado ao remover o Lenis —
  ver armadilha em `BLUEPRINT.md` §7.
- `scroll-behavior:smooth` **não respeita `prefers-reduced-motion` sozinho**; foi preciso
  desligá-lo explicitamente por media query. O resto do arquivo já respeitava.
- Regra que fica: **efeito de rolagem não pode custar a rolagem.** Antes de adicionar
  qualquer biblioteca que intercepte roda/toque, testar com mouse de verdade.

---

## ADR-0028 — Look por conta: curva leve na passada que já existe (não é editor)

**Data:** 2026-08-30 · **Estado:** aceita — em produção

**Decisão.** Cada conta pode escolher **um look** (`quente`, `frio`, `filme`, `vivo`,
`pb`) aplicado a **toda foto nova** no `process_image`. É uma **curva por canal** via
`Image.point()` — uma passada em C sobre a imagem que o pipeline **já decodificou**.
Coluna `photographer.look`; `NULL` = nenhum look, e o pipeline fica **idêntico** ao que
sempre foi.

**Contexto.** A Patrícia quer "tratar as fotos antes de irem pro Fóton" (presets). Ao
destrinchar o pedido, havia duas leituras muito diferentes:
- **Ela trata no Lightroom e depois sobe:** funciona hoje, custo zero de código — mas
  **mata a promessa do produto**, porque tratar leva minutos e o Fóton se vende como
  "durante o evento".
- **O Fóton vira editor:** colide com a **ADR-0008** (tratamento = watermark +
  otimização, sem edição de cor no MVP) e com a aritmética — 1 vCPU que já é o gargalo
  medido (P95 de 8,2 s na avalanche de selfies).

**Justificativa.** O que a fotógrafa quer é **a foto sair com a cara dela**, não rodar
Lightroom na nuvem. Um look fixo por conta entrega isso pelo mesmo truque que a
ADR-0022 usou na miniatura: aproveitar a decodificação que já aconteceu, em vez de
criar um estágio novo no pipeline.

**Medido** (máquina de desenvolvimento, imagem sintética 1200×800 com pele, céu e preto):

| look | efeito verificado | custo |
|---|---|---|
| (nenhum) | referência | 20,1 ms |
| quente | pele 222→**240** no vermelho, azul 141→128 | 29,4 ms |
| frio | vermelho 222→213, azul 141→**156** | 22,0 ms |
| filme | preto 12→**24** (o cinza de filme) | 21,9 ms |
| vivo | saturação acima, contraste em S | 22,1 ms |
| pb | cinzas neutros | 17,4 ms |

**+2 a 9 ms** sobre os ~530 ms do processamento — **menos de 2%**. Número da VM ainda
não medido: `UNKNOWN — REQUIRES EXPERIMENT`, mas a ordem de grandeza se mantém porque
`point()` é uma passada linear em C.

**Regra de ouro, verificada por teste.** Look vazio **ou** desconhecido devolve bytes
**idênticos** aos de hoje. `aplica_look` é envolta em `try/except` pela mesma razão do
`_thumb`: **foto sem look é melhor que foto nenhuma** — nada aqui pode derrubar o ingest.

**Consequências.**
- Vale só para foto **nova**. Não reprocessa o passado: mudaria debaixo do pé uma foto
  que a convidada já pode ter baixado.
- O look entra **antes** da marca d'água, de propósito — a curva é para a foto, não para
  a marca. Aplicar depois tingiria o logo da fotógrafa junto.
- O **cardápio vem do servidor** (`GET /conta/look`), não de uma lista no cliente. É a
  regra da ADR-0025 aplicada: o cliente obedece, não adivinha.
- A tela mostra uma **amostra visual** de cada look, não só o nome — "Quente" não
  significa nada sozinho para quem escolhe com o olho.
- **Não fecha a porta do editor de verdade.** Se um dia houver CPU sobrando e demanda
  medida, isto vira o padrão e o editor é outra ADR.

---

## ADR-0029 — Buracos de LGPD tapados: a rota mais crítica não tinha teste

**Data:** 2026-08-30 · **Estado:** aceita — em produção

**Contexto.** Auditoria de conformidade feita lendo o código, não os documentos. O que
existe e funciona: política publicada (`GET /privacidade`), consentimento no fluxo (24
pontos no front), **selfie nunca armazenada** (nenhum `INSERT` de selfie existe),
retenção **automática de verdade** (thread daemon a cada 12 h, `RET_BIO`=7 d,
`RET_FOTO`=90 d), retenção por conta (ADR-0021), sem PII em log. Dois furos, porém:

**1. `POST /convidado/excluir` não tinha um único teste.** É a rota do **direito de
exclusão** (LGPD Art. 18) e é a **condição nº 3** da decisão registrada em
`docs/PRODUTO.md` §3b-2 — é ela que sustenta o argumento *"quem registrou foi o dono do
evento; reclame com ele"*. Num refactor, ela podia quebrar em silêncio e derrubar junto
o alicerce jurídico daquela decisão. **A rota mais importante para conformidade era a
menos protegida do sistema.**

**2. A limpeza engolia os próprios erros.** `except Exception: pass` na thread de
expiração: se a expiração de **biometria** falhasse, ninguém ficaria sabendo — podia
estar parada há meses. Conformidade falhando muda.

**Decisão.**
- Seção `[24]` em `tests/test_autorizacao.py`, com 10 checagens: a saída **não exige
  login** (a convidada não tem conta), a biometria **some de verdade**, o feed morre
  junto, apagar duas vezes não quebra, id inexistente não apaga nada, a expiração
  automática continua devolvendo contagem, e o app **de fato** chama a rota.
- A thread de limpeza passa a logar **sempre** — inclusive quando não havia nada a
  expirar, porque sem isso não se distingue "rodou e não tinha nada" de "nunca rodou" —
  e loga `status:"FALHOU"` com o erro em vez de engolir.

**Consequência / o que fica em aberto.** A condição nº 1 daquela mesma decisão —
**contrato com o organizador** declarando que ele tem base legal para os dados que
cadastra — **continua não existindo**. É documento, não código, e segue pendente.
**Público de menores de idade está fora do escopo por decisão do dono (2026-08-30)**:
seria LGPD **Art. 14** (consentimento específico de um dos pais) somado ao Art. 11
(dado sensível) — regime jurídico diferente, que exige decisão antes de qualquer tela.

---

## ADR-0030 — Perfil de conta: uma estrutura, três peles (não são três apps)

> **Atualização 2026-08-30 — a ADR foi completada.** Até aqui `_perfil()` era *derivado*
> (`empresa` se a coluna empresa, senão `pro`), então a pele **`social` nunca saía do
> servidor**: ela existia no app e era código inalcançável. Agora existe
> `photographer.perfil` (ALTER guardado; **NULL = deriva como antes**, então nenhuma
> conta existente mudou de tela — medido: migração de 15,8 ms num banco antigo com
> dados, `perfil` NULL e créditos preservados) e `/admin/perfil` com seletor no painel.
> **A regra "perfil não abre porta" continua valendo e agora está travada por teste:**
> marcar alguém como pele `empresa` NÃO concede os poderes de empresa — quem manda
> segue sendo a coluna `empresa` (`_exige_elevacao`) e `FOTON_ADMINS`.
> Isto é o **pré-requisito do Fóton Festa** (PRODUTO §2): sem pele `social` atribuível,
> não havia como uma conta ser "rolê" em vez de "evento".

**Data:** 2026-08-30 · **Estado:** aceita — decisão de direção do dono

**Contexto.** `docs/PRODUTO.md` §1: não são três produtos — é um motor com três portas
(Patrícia/pro · GLAMON/empresa · Ana/social). O dono confirmou a tese em 2026-08-30 e
pediu identidade própria para cada frente. O front é um HTML de ~205 KB sem framework;
desenhar três painéis à mão triplicaria a superfície de bug num código que já pagou
caro por armadilhas repetidas (BLUEPRINT §7).

**Decisão.** Cada conta tem um **perfil de apresentação** — `pro` | `empresa` |
`social` — **declarado pelo servidor** em `/signup`, `/login` e `/me` (regra da
ADR-0025: o cliente obedece, não adivinha). O perfil controla exatamente **três
coisas**, todas de apresentação:

1. **Vocabulário** — evento / álbum / rolê, numa tabela única (`VOCAB`) aplicada por
   `aplicarPerfil()` sobre elementos marcados com `data-voc`/`data-voc-ph`. Mata as
   trocas improvisadas que existiam espalhadas.
2. **Quais blocos aparecem** — elementos com `data-so="pro,..."`: o cartão de câmera
   /FTP e o link "Conectar câmera" são ferramenta de fotógrafa profissional; a conta
   de empresa (fotografa de celular) e a social não os veem. Marca d'água fica para
   pro **e** empresa (uma empresa tem logo), some para social.
3. **Tokens de cor** — uma classe `perfil-*` no `body` troca `--accent`/`--accent-2`/
   `--accent-soft`. Nenhum CSS de layout novo.

**O que o perfil NÃO controla: fluxo e poder.** Autorização continua sendo `empresa`
no servidor (`_exige_elevacao`) e `admin` na lista `FOTON_ADMINS`. Perfil errado
mostra a palavra errada — nunca abre nem fecha porta.

**Derivação, sem migração.** Nesta fase o servidor **deriva** o perfil:
`empresa=1 → 'empresa'`, senão `'pro'`. `'social'` é valor reservado — só passa a ser
atribuível quando a frente da Ana (PRODUTO §2) existir; criar coluna/rota agora seria
construir à frente da demanda (mesmo raciocínio da ADR-0026). O front tem fallback
(`SESSAO.perfil` ausente → deriva de `empresa`) para sessão em cache de antes do deploy.

**Por que não as alternativas.** *Três HTMLs/painéis*: triplica bug e manutenção num
arquivo que é um só de propósito. *Detectar no cliente* (ex.: pelo nome da conta):
viola ADR-0025. *Coluna `perfil` no banco já*: não há quem a use — YAGNI medido.

**Reversível.** Sem a classe no body e sem `data-voc` preenchido, o app fica idêntico
ao de hoje; `social` inexistente cai em `pro`.

**Consequências.** `/signup` e `/login` passam a devolver também `empresa` (antes só o
`/me` devolvia) e `perfil`; testes novos nas seções [25] de `test_autorizacao.py` e
`test_front.py` guardam o contrato.

---

## ADR-0031 — Backup fora da VM: instalado, rodou, provou

**Data:** 2026-08-31 · **Estado:** aceita — em produção

**Decisão.** `infra/backup-externo.sh` foi executado (Cloud Shell da Oracle, com o dono
logado) e instalado como serviço permanente na VM. O banco de produção agora tem uma
**terceira cópia**, fora do disco da VM: Cloudflare R2, bucket `foton-backup`, conta
gratuita até 10 GB/mês.

**Contexto.** Era o único risco irreversível do sistema (`docs/BACKUP.md` item 1): as 7
cópias diárias moravam no mesmo disco da mesma VM que o banco — perder a máquina (Always
Free pode ser recuperada por inatividade) levava o acervo do GLAMON junto com elas.

**Como foi feito.** Sessão conduzida por agente com acesso ao Chrome já autenticado do
dono (extensão `claude-in-chrome`), dirigindo o navegador real dele:
1. Bucket R2 `foton-backup` criado no painel Cloudflare (conta `Luizoak@gmail.com`,
   mesma conta da zona DNS de `foton.app.br`), região automática, storage Standard,
   privado.
2. Token de API criado com escopo **restrito ao bucket** (`Object Read & Write`,
   não "todos os buckets"), tipo **Account API Token** (sobrevive independente da
   sessão pessoal — é o recomendado da própria Cloudflare para sistema de produção).
3. **Regra seguida à risca:** o agente nunca digitou a chave nem o segredo em campo
   nenhum — só o dono copiou do painel Cloudflare e colou no Cloud Shell
   (`export R2_CHAVE=...` / `export R2_SEGREDO=...`). O agente só preparou as variáveis
   não sensíveis (`R2_CONTA`, `R2_BALDE`) e disparou o comando final via SSH.
4. Script instalou `rclone`, gravou as credenciais em `/root/.config/rclone` (modo 600,
   só root lê), criou o timer diário (`foton-backup-externo.timer`, depois do backup
   local) e **provou na hora**: enviou o backup mais recente e listou o bucket.

**Prova real (2026-08-31):**
```
enviado: foton-2026-08-31.db (54M)
-- o que existe no R2 hoje --
 55709696 foton-2026-08-31.db
PRONTO. O acervo agora sobrevive a perda da VM.
```

**O que isso muda em `docs/BACKUP.md`.** O item 1 ("Perder a máquina") deixa de ser
`SCRIPT PRONTO, FALTA RODAR` — está resolvido. Os itens 2 (`restaurar-teste.sh` no
timer, recusando sobrescrever quando reprovar) e 3 (tirar o `cp` de emergência) continuam
abertos, mas já não são o risco catastrófico — agora é "perco um dia", não "perco tudo".

**O que ainda falta, registrado para não perder de vista:**
- O tamanho real do banco em produção nunca tinha sido medido antes: **54 MB** (era
  `UNKNOWN — REQUIRES EXPERIMENT` em `docs/BACKUP.md`). Cabe folgado no teto grátis do
  R2 (10 GB) por muito tempo.
- Retenção no R2 é 30 dias (script já cuida disso); local continua 7 cópias rotativas.
- `restaurar-teste.sh` prova que um backup *local* restaura — ainda não foi rodado
  puxando a cópia *do R2* de volta. Prova de restauração completa a partir da nuvem
  segue como `UNKNOWN — REQUIRES EXPERIMENT`.

**Consequências.** Nenhuma mudança de código nesta sessão — é infraestrutura pura. O
segredo do R2 nunca passou pelo repositório, pelo chat ou por este documento (CLAUDE.md
§7). O timer roda diariamente, sem intervenção manual daqui pra frente.
