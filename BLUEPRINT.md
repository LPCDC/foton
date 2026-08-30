# FÓTON — Blueprint

> **Leia isto primeiro em qualquer sessão nova.** Resume o que é, onde está, como mexer,
> quanto aguenta e o que vem. Escrito para retomar o trabalho sem reler o histórico.
> Atualizado: 2026-08-31 · Plano de trabalho vivo: `docs/PROMPT-PROXIMA-SESSAO.md`

---

## 1. O que é

**Fóton** — as fotos do evento chegam **sozinhas** no celular de quem aparece nelas,
**durante a festa**. O convidado escaneia um QR, tira 1 selfie, e as fotos em que ele
aparece caem na galeria dele ao vivo.

**Um motor, três portas** (ADR-0030 — perfis em produção):

| Porta | Quem | Pele | Estado |
|---|---|---|---|
| Vou fotografar | **Patrícia** — fotógrafa profissional (Santos) | `pro` · dourado · evento/convidado | no ar |
| Sou empresa | **GLAMON** — salão, álbum permanente | `empresa` · platinado · álbum/equipe | no ar |
| **Foto'n Fiesta!** | **Ana** — cliente sem câmera; ela E os convidados fotografam | `social` · coral · festa/rolê | decidido, não feito (PRODUTO §2) |

- **Usuário final:** o convidado — 2 minutos na vida, sem instalar nada.
- **Diferencial:** entrega **ao vivo**, em português, num preço que os internacionais
  (SpotMyPhotos ~US$142/mês) não alcançam aqui. Reconhecimento facial é commodity;
  **na hora** não é.
- **Nome da terceira porta é decisão do dono (2026-08-31): "Foto'n Fiesta!"** — botão
  e branding. Concorrente gringo (GuestCam) cobra US$25–55/evento só pelo upload de
  convidado que a Fiesta terá de graça.

## 2. Onde está (produção)

| | |
|---|---|
| **App (tudo)** | **https://app.foton.app.br** |
| App (endereço antigo) | https://getfoton.duckdns.org — funciona, mesmo certificado |
| **Site de marca** | `getfoton.netlify.app` — **NO AR** (repo ligado, `git push` publica; verificado 2026-08-30) |
| Servidor | Oracle Cloud Always Free, São Paulo · `152.67.46.113` |
| Máquina | `VM.Standard.E2.1.Micro` — **1/8 OCPU**, 1 GB RAM + 2 GB swap (ver §11: dá para 16× isso de graça) |
| Código | https://github.com/LPCDC/foton (público — ver §7) |
| Repo local | `C:\Users\Pichau\Menir ClickPal` |
| DNS | zona no **registro.br** (`d/e.sec.dns.br`) — só 3 registros A, sem MX/TXT; migração p/ Cloudflare autorizada (plano no PROMPT item 7) |
| Certificado | **um só**, nome `getfoton.duckdns.org`, cobre app+raiz+www+duckdns, expira **2026-11-27**; separação pendente (PROMPT item 7.1) |

**Credenciais:** fora do repo (ele é público), em `C:\Users\Pichau\foton-acessos.md`.
Senha nunca em chat, commit ou log. Admin é quem está em `FOTON_ADMINS` **no servidor**
(ADR-0025); o painel não mostra senha nenhuma (PBKDF2, irreversível de propósito).

## 3. Como funciona (pipeline)

```
FOTÓGRAFA cria evento → sai um QR                    (grátis — crédito cortado, ADR-0024)
CONVIDADO escaneia → 1 selfie → vira vetor facial (a selfie é DESCARTADA)
FOTÓGRAFA fotografa → a foto chega por 3 caminhos:
   (a) app: câmera interna ou galeria do celular (lote, retry, fila em IndexedDB)
   (b) PWA instalado: menu "Compartilhar" do Android entrega o lote (ADR-0018)
   (c) FTP: câmera PROFISSIONAL envia sozinha (não é o caso da Patrícia — R8/T6s
       NÃO têm FTP, verificado presencialmente) → porta 2121
SERVIDOR: reduz p/ 2048px → look da conta (ADR-0028) → marca d'água → SCRFD detecta
          rostos → ArcFace embedding → match com convidados → publica p/ quem casar
          → miniatura 320px em coluna própria (ADR-0022)
CONVIDADO: foto aparece sozinha (poll 2,5 s), animação; baixa/compartilha/QR por foto
           (ADR-0020); segura o dedo para selecionar várias
```

**Reconhecimento:** InsightFace **buffalo_s** (SCRFD + ArcFace), CPU, `det_size=640`,
limiar cosseno **0.25** (agrupar fotos — NÃO serve para autenticar, PRODUTO §3).
Validado: 99,5% no LFW. ⚠️ `det_size=320` perdia rosto de 90px (0/6). Não reduzir.

## 4. Estrutura do código

```
app/test_rig/
  rig.py         FastAPI: rotas, pipeline, admin, LGPD, FTP, perfis (_perfil, ADR-0030)
  store.py       SQLite: contas, eventos, fotos, rostos (face), convidados, match,
                 contatos, thumbs — migrações por ALTER TABLE guardado
  ftp_camera.py  servidor FTP (só câmera PROFISSIONAL)
  models/buffalo_s/  ONNX empacotado (não baixa em runtime)
app/web/
  index.html     TODO o front (uma página, sem framework, ~210 KB). Pontos de entrada:
                 badgeSVG()/diafragmaSVG() (marca §8) · PERFIL()/VOCAB/aplicarPerfil()
                 (três peles, ADR-0030) · estadoDaCamera() · armarToqueLongo() ·
                 filaGravar() e cia (fila IndexedDB) · renderGuestGrid() (galeria)
  sw.js          service worker: cache-first SÓ de estáticos, NUNCA resposta com
                 sessão (armadilha paga, §7); Web Share Target (ADR-0018)
  manifest.webmanifest   share_target (campo "fotos")
site/            site de marca (GSAP sem Lenis, ADR-0027) — publicado pelo Netlify
tests/
  test_autorizacao.py   210 checagens — contrato de rotas, LGPD, admin, perfis
  test_front.py         31 checagens — front como TEXTO: node --check, ids, funções
                        essenciais, fila grava ANTES da rede, perfis [6d]
  test_ftp_camera.py    23 · test_logo.py 16 (marca d'água do FOTÓGRAFO, não a do Fóton)
  todos.sh       roda as 4 e FALHA se qualquer uma falhar. SEMPRE antes de push.
  ensaio.py      fotos REAIS em produção — bom senso, NUNCA em massa
infra/           VM, HTTPS (dominio.sh — só EXPANDE cert, não reduz), FTP, backup
docs/
  PROMPT-PROXIMA-SESSAO.md  o plano de trabalho vivo — decisões do dono + ordem
  DECISIONS.md   30 ADRs · PRODUTO.md  o que ainda não virou código
  CONTRATO-ORGANIZADOR.md   minuta LGPD + pesquisa de aceite (clickwrap)
  BENCHMARKS.md · PILOTO-1.md · TESTES.md · ROTEIRO-CAMERAS.md   medições
  ARCHITECTURE.md, ROADMAP.md, GAUNTLET.md (parte antiga)   histórico, aviso no topo
```

**Dados (nunca apagar):** `/var/lib/foton/foton.db` + `backup/` (7 cópias diárias —
cada MB no banco custa **×8** em disco).

## 5. Como fazer deploy

**Basta `git push`.** Auto-update na VM (systemd timer, 2 min) puxa `origin/main` e
reinicia (~25 s de 502).

```bash
bash tests/todos.sh && git add -A && git commit -m "..." && git push origin main
curl -s https://app.foton.app.br/health     # ~2 min depois
```

Deploy com evento ao vivo: **liberado nesta fase** (dono, 2026-08-30), com bom senso —
mudança em fila de upload, pipeline ou reconhecimento pede `/admin/saude` antes
(última foto + carga; GLAMON/Carol ficam `ao_vivo` permanente, não é sinal).
**Infraestrutura** (systemd, nginx, portas, certificado) = Cloud Shell da Oracle:
```bash
ssh -o StrictHostKeyChecking=no -i ~/.ssh/foton.key ubuntu@152.67.46.113 '...'
```

## 6. Regras de trabalho

1. **Nada é "pronto" sem rodar e ler a saída.** Cole o número. Nunca "deve funcionar".
2. **Medir antes de otimizar.** Não medido = `UNKNOWN — REQUIRES EXPERIMENT`.
3. **Mudou arquitetura/dependência → ADR antes** (remover também é mudar, ADR-0027).
4. **Não quebrar o que funciona** — há fotógrafa cobrando de cliente com isto.
5. **Sem segredo no git** (repo público). Senha nunca em chat/commit/log.
6. **Reportar com honestidade** — falhou é falhou, com a saída.
7. **Autorização nunca se infere de formato de dado no cliente** (ADR-0025).
8. **Barra invertida não sobrevive a heredoc de shell** — montar com `chr(92)` ou usar
   ferramenta de escrita direta. Já corrompeu o app mais de uma vez.
9. **Doc que afirma estado de deploy se verifica com curl/cat**, não se relê (§7).

## 7. Armadilhas já pagas (não repetir)

| Armadilha | O que aconteceu |
|---|---|
| **Service worker cacheando API** | `/me` e `/events` vinham do cache → app mostrava **conta errada**. Hoje o SW só cacheia lista explícita de estáticos. **Nunca cachear resposta com sessão.** |
| **Banco dentro do código** | O instalador faz `rm -rf /opt/foton` e o banco morava lá → **apagava contas e eventos**. Agora em `/var/lib/foton`. |
| **Evento sem dono** | `openEvent` chamava `/photos` antes de registrar; o auto-create gravava sem dono → convidado via as fotos, fotógrafa não via o evento. |
| **`createEvent` colidia com `document.createEvent`** | Handler inline chamava o método nativo → botão não fazia nada. |
| **EXIF ignorado** | Fotos deitadas + rosto não detectado. `ImageOps.exif_transpose` resolve. |
| **ARM sem estoque em SP** | `A1.Flex` dá "out of capacity". O script cai para x86 `E2.1.Micro`. (Reabrir: §11 — vale insistir/agendar retry, o prêmio é 16× a CPU.) |
| **Firewall em 2 camadas** | Security List (nuvem) **e** iptables (VM). Abrir só um não funciona. |
| **Cloud Shell em FIPS** | Recusa chave ed25519 → usar RSA. |
| **Repo privado quebra deploy** | Auto-update e instalador baixam do GitHub público. Privatizar exige **deploy key na VM antes**. |
| **Rotas destrutivas sem dono** | `/event/delete`, `/event/close`, `/photo/delete`, `/ingest` e `/contatos` eram **abertas**: com o código do QR qualquer convidado apagava o evento. Hoje passam por `_pode()`. **Rota que muda dado precisa de dono.** |
| **FTP engolia foto sem evento** | Arquivo ficava parado e nunca era processado — perda silenciosa. Hoje: fila de pendentes, entra ao abrir o evento. |
| **Usuário de FTP só no boot** | Conta criada depois não conectava até reiniciar. Hoje o login é conferido no banco na hora. |
| **Selfie "invertida"** | Espelha-se **só o preview** (CSS) — a foto salva fica na orientação real. |
| **`/signup` podia reivindicar login de admin** | Cadastro aberto não conferia `FOTON_ADMINS` (que vive em repo público). Fechado (403), com teste. **Rota que concede poder confere quem pode.** |
| **Leitura que escreve** | `GET /stats`, `/photos` e `/feed` usavam `create=True`: **ler criava evento**. Hoje 404. **Rota de leitura nunca escreve.** |
| **SQLite não devolve espaço** | Apagar não encolhe o arquivo; backup ×7 multiplica o desperdício. `/admin/compactar` (VACUUM + `wal_checkpoint(TRUNCATE)`, nessa ordem). |
| **Deploy tem ~25 s de 502** | O auto-update reinicia o serviço. Ver §5. |
| **Autorização inferida do FORMATO no cliente** | `EH_ADMIN` era `/^admin@/`. Login virou `admin` → botão sumiu em silêncio por um mês. ADR-0025: o servidor informa `admin`/`perfil`; o cliente obedece. |
| **Barra invertida através de heredoc** | `\n` literal virou quebra de linha real dentro de string JS, cortou-a no meio, derrubou `node --check`. Montar com `chr(92)`. |
| **Texto de estado que mentia** | Cartão da câmera dizia "nenhuma foto ainda" para conta com 30 fotos — falava da CÂMERA com vocabulário de FOTOS. **Todo texto de estado se lê ao lado do número que pode contradizê-lo.** |
| **Segurar miniatura abria menu do navegador** | Alvo do toque era o `<img>`. Hoje: `pointer-events:none`, `contextmenu` barrado, 450 ms entra em seleção. |
| **Overflow real = "fundo desliza"** | 146px além da viewport; fundo `absolute` rolava junto. Corrigido medindo (`scrollHeight`), não chutando — a suspeita inicial foi **descartada por teste direto**. **"X parece causar Y": remova X de verdade e meça antes de reescrever CSS.** |
| **Sessão persistente só de um lado** | Convidado com sessão salva caía na home sem o código. Mesmo bug já corrigido para a fotógrafa. **Bug corrigido de um lado é motivo para checar o espelho do outro.** |
| **Documento desatualizado enganou uma sessão inteira** | README dizia uma coisa, `netlify.toml` outra, e o site no ar era uma terceira. **Estado de deploy se verifica com curl/cat.** |
| **Lib de smooth-scroll quebrou a rolagem** | Lenis sequestrava a roda do mouse. Removido (ADR-0027). Ao arrancar, quase foi junto `gsap.ticker.lagSmoothing(0)`, que morava no bloco dela sem ser dela. **Ao remover dependência, conferir linha a linha o que estava no bloco por acaso.** |
| **`scroll-behavior:smooth` ignora `prefers-reduced-motion`** | Precisou de media query explícita. **Nem toda propriedade de movimento se auto-desliga.** |
| **Overlay de tela cheia sem rede de segurança** | Animação de abertura quebrada = tela preta. `setTimeout` de 4 s força a saída. **Todo overlay que cobre a tela sai sem depender da animação terminar.** |
| **Segurar em texto abria "Pesquisar no Google"** | `user-select:none` global, exceção para `input`/`textarea`/`.selecionavel`. Texto de app não é texto de página. |

## 8. Estado atual — o que funciona HOJE (inventário de features)

**Fotógrafa (`pro`):** conta com senha, grátis (ADR-0024) · criar/encerrar/apagar
evento · marca d'água própria (texto ou logo PNG) · **look por conta** — quente/frio/
filme/vivo/pb aplicado a toda foto nova, +2–9 ms (ADR-0028) · QR tela cheia +
imprimível · câmera no app com fallback nativo · upload em lote com barra, retry e
**fila IndexedDB que sobrevive a fechar o app** · receber pelo "Compartilhar" do
Android (ADR-0018) · cartão de status da câmera honesto (verde/âmbar/cinza, nunca
inventa) · seleção múltipla por toque longo · convidados ao vivo + contatos · resumo
ao encerrar · FTP p/ câmera profissional · trocar login/senha (ADR-0019).

**Empresa (`empresa` — GLAMON):** tudo acima, pele platinada, vocabulário
álbum/equipe, sem cartão de câmera; criar/apagar álbum exige senha de admin
(elevação no servidor, ADR-0021); retenção de biometria configurável (permanente no
álbum, com consentimento destacado).

**Convidado:** QR → 1 tela (selfie + consentimento) · galeria ao vivo com abas
minhas/todas · animação de chegada + "Chegou uma foto sua!" · espera viva · lightbox ·
salvar/compartilhar/ZIP · seleção múltipla por toque longo · QR por foto (ADR-0020) ·
**sessão persistente 24h de verdade** (volta pra galeria mesmo sem link) · **"Apagar
minha selfie e sair"** visível na galeria (LGPD Art. 18, testado — ADR-0029) · PWA ·
pré-cadastro funciona (criador sobe fotos antes → reconhecido na 1ª selfie).

**Admin:** resumo · disco · contas + histórico de crédito · marcar empresa · retenção
por conta · zerar dados · compactar banco · trocar senha de conta · testar foto de
câmera · adotar órfãos · forçar expiração LGPD · contatos.

**Perfis (ADR-0030):** servidor declara `perfil` em `/signup`/`/login`/`/me`; front
aplica vocabulário/blocos/tokens (`aplicarPerfil()`); `social` reservado à Fiesta.

**LGPD:** política publicada · consentimento destacado · selfie nunca armazenada ·
retenção automática logando SEMPRE (ADR-0029) · saída do titular com teste [24] ·
minuta de contrato do organizador pronta (`docs/CONTRATO-ORGANIZADOR.md`) · menores
fora de escopo (decisão do dono).

**Infra:** HTTPS auto-renovável · backup diário ×7 · auto-update · monitor externo
(UptimeRobot 3×, keyword em `/health`) — alerta nunca visto disparar de verdade:
`UNKNOWN — REQUIRES EXPERIMENT`.

**Números que provam (medidos):** `/ingest` P95 1,9 s · poll 2,5 s · 30 selfies
simultâneas P95 8,2 s (gargalo real) · look +2–9 ms · `/health` 80–150 ms após o
despejo GLAMON de fotos 2000×2000 (2026-08-31). **TTFR fim a fim: nunca medido.**

## 9. Backlog — o que falta, em ordem (detalhe vivo no PROMPT-PROXIMA-SESSAO.md)

1. **Relatório do despejo GLAMON** (números de dentro — comando do dono) → decide R2.
2. **Galeria 50 + "Mostrar mais"** · **sort data/pessoas** (`n_faces` já existe) ·
   **coração no lightbox** (1ª fatia do chat de emoji §3d) · **adicionar rosto manual**
   (GLAMON; linha em `match`, sem biometria nova).
3. **Reencontro por selfie** (limiar por experimento) — GLAMON reencontra histórico.
4. **Câmera sem lag** — preview forçado a 4K localizado (`index.html:2379`); medir e baixar.
5. **DNS/cert** — autorizado; comandos prontos (PROMPT item 7). Mesma sessão: cert →
   Cloudflare → NS. Depois: `fotos.foton.app.br` no R2.
6. **Foto'n Fiesta!** — papéis dono/participante, limite POR participante; perguntas
   do PRODUTO §2 precisam do dono antes do código.
7. **`photo.oculta`** + roteiro de abordagem no painel (material de venda, PRODUTO §3b).
8. **Contrato** — clickwrap + tabela `aceite` (aguarda "ok" do dono à recomendação).
9. **TTFR fim a fim** + testes no aparelho da Patrícia (30 s de teste que valem mais
   que código) — continuam sendo o maior risco do piloto.
10. R2 · repo privado+deploy key · segunda VM/failover · chat emoji completo.

## 10. Modelo comercial

Crédito **cortado** (ADR-0024): grátis com login nesta fase. Substituto planejado:
**limite de upload** (PRODUTO §3c) — COGS real `UNKNOWN`. Em aberto: proposta da
Patrícia (revenda/50%) vs ADR-0012; revisitar ao fim da fase de teste. Upsell
registrado: "conectar DSLR" como **plano plus** futuro (decisão 2026-08-30).

## 11. Capacidade e teto GRÁTIS (lido da doc oficial Oracle, 2026-08-31)

O que o Always Free ainda dá, além do que usamos — **estamos usando a fatia menor**:

| Recurso | Hoje | Teto grátis | Salto |
|---|---|---|---|
| CPU/RAM | E2.1.Micro: **1/8 OCPU**, 1 GB | **ARM A1: 2 OCPUs + 12 GB** (1.500 OCPU-h/mês) | ~16× CPU, 12× RAM — atacaria direto o P95 de 8,2 s da avalanche de selfies |
| VMs | 1 | **2 AMD + ARM** | segunda VM/failover do §9 é grátis |
| Block storage | boot 50 GB | **200 GB total** | +150 GB para fotos ANTES de precisar do R2 |
| Object storage | — | **20 GB** (50k req/mês) | pequeno; R2 continua o plano para TB |
| Load balancer | — | 1 flexível (10 Mbps) | frente para 2 VMs |
| Saída de dados | — | **10 TB/mês** | egress nunca será o problema da VM |
| **E-mail** | — (bloqueio do login por selfie: "não temos e-mail") | **3.000/mês grátis** (Email Delivery) + 1.000 notificações | destrava recuperação de senha e 2º fator SEM custo — remove o item 3 dos impedimentos do PRODUTO §3 |
| Monitoring | UptimeRobot | 500M pontos + alarmes | alarme de disco/carga nativo |

Armadilha conhecida: **A1 "out of capacity" em SP** (§7) — insistir/agendar retry;
migração de x86→ARM exige reinstalar (ONNX aarch64 existe) e é mudança de infra = ADR
+ Cloud Shell. **Custo pago que cabe no bolso do dono (R$100–200/mês):** R2 com 1 TB ≈
US$15/mês (egress zero, ADR-0011); WhatsApp Business API para entrega (centavos por
conversa) — os dois juntos ainda ficam abaixo do teto.

## 12. Concorrência internacional — o que copiar barato (pesquisa 2026-08-31)

Levantado de FotoOwl, SpotMyPhotos, Memzo, GuestCam, Honcho, VaultPic, FindMe.
Filtro: implementável a custo ~zero ou ≤ R$200/mês. **Ninguém no Brasil junta isso
com entrega ao vivo em português.**

| Feature deles | Quem tem | Custo p/ nós | Nota |
|---|---|---|---|
| **Slideshow ao vivo no telão** | Honcho | ~zero | rota `/telao` ciclando as últimas fotos; ouro para festa E para a TV do salão GLAMON |
| **Venda de foto extra / impressão** | Memzo (0% comissão), Honcho | ~zero + taxa Pix | fotógrafa vende pelo app; Pix via Mercado Pago, sem mensalidade — vira RECEITA |
| **Subdomínio da fotógrafa** (`patricia.foton.app.br`) | FindMe | ~zero | wildcard na Cloudflare pós-migração; branding que fideliza a cliente pagante |
| **Entrega/upload por WhatsApp** | FotoOwl (carro-chefe) | centavos/conversa | o canal que o brasileiro usa; depois do piloto |
| **Rastreio de visualização/download** | FindMe | ~zero | a fotógrafa vê o engajamento — argumento de venda dela |
| **Sync com Google Drive** (backup da fotógrafa) | FindMe | ~zero | exporta o evento para o Drive DELA; conforto de posse |
| **Upload de convidado por QR** | GuestCam (US$25–55/evento!) | já planejado | é a Foto'n Fiesta — eles COBRAM pelo que teremos grátis |
| Reels automáticos personalizados | FotoOwl | CPU cara | só depois de ARM/R2 — anotado, não agora |

**Direção validada pela pesquisa:** o mercado 2026 está indo para consent-first
(SpotMyPhotos: "a era do aviso na porta acabou") — exatamente o desenho LGPD que já
temos por código e contrato. Isso é vantagem, não burocracia.
