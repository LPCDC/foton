# FÓTON — Blueprint

> **Leia isto primeiro em qualquer sessão nova.** Resume o que é, onde está, como mexer
> e o que vem. Escrito para retomar o trabalho sem reler o histórico.
> Atualizado: 2026-08-28

---

## 1. O que é

**Fóton** — as fotos do evento chegam **sozinhas** no celular de quem aparece nelas,
**durante a festa**. O convidado escaneia um QR, tira 1 selfie, e as fotos em que ele
aparece caem na galeria dele ao vivo.

- **Cliente pagante:** fotógrafo de eventos (primeira: **Patrícia Vargas**, Santos/Baixada).
- **Usuário final:** o convidado (usa 2 minutos na vida, sem instalar nada).
- **Diferencial:** entrega **ao vivo**, em português, para um mercado que os
  concorrentes internacionais não atendem no preço.
- **Concorrentes:** FotoOwl, SpotMyPhotos (~US$142/mês), EventHex, SnapSeek.
  Todos entregam "link para depois"; nosso wedge é o **tempo real**.

## 2. Onde está (produção)

| | |
|---|---|
| **App (tudo)** | **https://app.foton.app.br** (dominio proprio, desde 2026-08-29) |
| App (endereco antigo) | https://getfoton.duckdns.org — continua funcionando, mesmo certificado |
| Servidor | Oracle Cloud Always Free, São Paulo · `152.67.46.113` |
| Máquina | `VM.Standard.E2.1.Micro` — 1 vCPU, 1 GB RAM + 2 GB swap |
| Código | https://github.com/LPCDC/foton (público — ver §7) |
| Repo local | `C:\Users\Pichau\Menir ClickPal` |
| Netlify | `getfoton.netlify.app` — só demo antiga; **virará o site de marca** |

**Contas**
```
Fotógrafa (cliente real): patriciavargas       / (senha com o dono — NÃO escrever aqui)
Admin:                    admin@foton.com     / (senha com o dono — NÃO escrever aqui)
```
> ⚠️ **Este repo é público. Nenhuma senha entra neste arquivo.** A senha da Patrícia
> esteve aqui em texto puro até 2026-08-29 e continua no histórico do git — por isso
> **login e senha foram trocados em produção** naquele dia. O que está no histórico
> não abre mais nada. A fotógrafa troca a própria senha em **Painel → Minha conta e
> senha** (ADR-0019); o admin ainda pode, por `/admin/senha`.

## 3. Como funciona (pipeline)

```
FOTÓGRAFA cria evento → sai um QR
CONVIDADO escaneia → 1 selfie → vira vetor facial (a selfie é DESCARTADA)
FOTÓGRAFA fotografa → a foto chega ao servidor por 2 caminhos:
   (a) app: envia do celular (lote, com retry)
   (b) FTP: a câmera envia SOZINHA (Canon R8 e afins) → porta 2121
SERVIDOR: reduz p/ 2048px → marca d'água do fotógrafo → detecta rostos (SCRFD)
          → embedding (ArcFace) → compara com os convidados → publica p/ quem casar
CONVIDADO: a foto aparece sozinha, com animação; baixa/compartilha
```

**Reconhecimento:** InsightFace **buffalo_s** (SCRFD + ArcFace), CPU, `det_size=640`,
limiar cosseno **0.25**. Validado: 99,5% no LFW.
⚠️ `det_size=320` fazia rosto de 90px **não ser detectado** (0/6). Não reduzir.

## 4. Estrutura do código

```
app/test_rig/
  rig.py         FastAPI: rotas, pipeline, admin, LGPD, FTP
  store.py       SQLite: contas, eventos, fotos, rostos, convidados, contatos
  ftp_camera.py  servidor FTP (câmera envia direto)
  models/buffalo_s/  ONNX empacotado (não baixa em runtime)
app/web/
  index.html     TODO o front (uma página, sem framework) — fotógrafa + convidado
  sw.js          service worker (ver §7 — armadilha conhecida)
  assets/        fotos de demonstração
infra/           scripts de VM, HTTPS, FTP, backup
docs/DECISIONS.md   ADRs (leia antes de mudar arquitetura)
```

**Dados (nunca apagar):** `/var/lib/foton/foton.db` + `backup/` (7 cópias diárias).

## 5. Como fazer deploy

**Basta `git push`.** A VM tem auto-update (systemd timer, 2 min) que puxa `origin/main`,
reinstala dependências se mudaram e reinicia o serviço.

```bash
git add -A && git commit -m "..." && git push origin main
# aguardar ~2 min e validar:
curl -s https://getfoton.duckdns.org/health
```

Mudou algo de **infraestrutura** (systemd, nginx, portas)? Aí sim precisa rodar no
Cloud Shell da Oracle:
```bash
ssh -o StrictHostKeyChecking=no -i ~/.ssh/foton.key ubuntu@152.67.46.113 \
  'curl -sL https://raw.githubusercontent.com/LPCDC/foton/main/infra/instalar-foton.sh | bash'
```

## 6. Regras de trabalho (do CLAUDE.md e da prática)

1. **Nada é "pronto" sem teste real.** Rode o fluxo, leia a saída, mostre o número.
   Nunca dizer "deve funcionar".
2. **Medir antes de otimizar.** Valor não medido = `UNKNOWN — REQUIRES EXPERIMENT`.
3. **Mudou arquitetura/dependência → ADR** em `docs/DECISIONS.md`.
4. **Não quebrar o que funciona.** Testar o caminho inteiro depois de mexer.
5. **Sem segredo no git.** Senhas e tokens só em env/Secrets.
6. **Reportar com honestidade** — falhou é falhou, com a saída.

## 7. Armadilhas já pagas (não repetir)

| Armadilha | O que aconteceu |
|---|---|
| **Service worker cacheando API** | `/me` e `/events` vinham do cache → app mostrava **conta errada**. Hoje o SW só cacheia lista explícita de estáticos. **Nunca cachear resposta com sessão.** |
| **Banco dentro do código** | O instalador faz `rm -rf /opt/foton` e o banco morava lá → **apagava contas e eventos**. Agora em `/var/lib/foton`. |
| **Evento sem dono** | `openEvent` chamava `/photos` antes de registrar; o auto-create gravava sem dono → convidado via as fotos, fotógrafa não via o evento. |
| **`createEvent` colidia com `document.createEvent`** | Handler inline chamava o método nativo → botão não fazia nada. |
| **EXIF ignorado** | Fotos deitadas + rosto não detectado. `ImageOps.exif_transpose` resolve. |
| **ARM sem estoque em SP** | `A1.Flex` dá "out of capacity". O script cai para x86 `E2.1.Micro`. |
| **Firewall em 2 camadas** | Security List (nuvem) **e** iptables (VM). Abrir só um não funciona. |
| **Cloud Shell em FIPS** | Recusa chave ed25519 → usar RSA. |
| **Repo privado quebra deploy** | Auto-update e instalador baixam do GitHub público. Privatizar exige **deploy key na VM antes**. |
| **Rotas destrutivas sem dono** | `/event/delete`, `/event/close`, `/photo/delete`, `/ingest` e `/contatos` eram **abertas**: com o código do QR (projetado na parede) qualquer convidado apagava o evento ou injetava foto. Hoje passam por `_pode()`. **Rota que muda dado precisa de dono.** |
| **FTP engolia foto sem evento** | Sem evento ao vivo o arquivo ficava parado na pasta e nunca era processado — perda silenciosa. Hoje vai para fila de pendentes e entra ao abrir o evento. |
| **Usuário de FTP só no boot** | Conta criada depois não conectava a câmera até reiniciar o serviço. Hoje o login é conferido no banco na hora. |
| **Selfie "invertida"** | O preview mostrava a cena como a lente vê; quem se olha espera espelho. Espelha-se **só o preview** (CSS) — a foto salva fica na orientação real. |
| **`/signup` podia reivindicar um login de admin** | O cadastro é aberto e **não conferia a lista de admins**, que vive no código de um **repo público**. Se um login de admin não tivesse conta, qualquer um se cadastrava com ele e virava admin: lia todos os contatos, apagava contas, trocava senhas. Fechado em 2026-08-29 (403), com teste. **Rota que concede poder precisa conferir quem pode.** |
| **Leitura que escreve** | `GET /stats`, `GET /photos` e `GET /feed` usavam `create=True`: **ler criava evento**. Quem digitava um codigo errado via uma galeria vazia para sempre em vez de "esse codigo nao existe". Pior: celular de convidado com a galeria aberta **ressuscitava evento apagado**, e o app da fotografa adotava o orfao de volta — evento apagado reaparecia vazio no painel dela. Visto ao vivo em 2026-08-29. Hoje as tres devolvem 404. **Rota de leitura nunca escreve.** |
| **SQLite nao devolve espaco** | Apagar evento marcava o espaco como livre **dentro** do arquivo; o arquivo nunca encolhia. Como as fotos moram no banco e o backup guarda **7 copias** dele, cada MB nao recuperado custava **8 MB** de disco. Nunca houve `VACUUM` no projeto — o banco chegou a 136 MB com 10 MB de fotos. Hoje: `/admin/compactar`. E **o checkpoint do WAL nao e opcional**: sem `wal_checkpoint(TRUNCATE)` o VACUUM deixa o resultado no `-wal` e o `.db` continua igual. |
| **Deploy tem ~25 s de 502** | O auto-update reinicia o serviço. **Não fazer deploy durante evento da cliente.** |

## 8. Estado atual (o que funciona hoje)

**Fotógrafa:** conta com senha · criar/encerrar/apagar evento · marca d'água própria ·
QR (tela cheia + imprimível) · upload em lote com barra de progresso e retry ·
**receber fotos pelo menu "Compartilhar" do Android (PWA instalado)** ·
apagar foto · convidados ao vivo · contatos · resumo ao encerrar · **FTP da câmera** ·
créditos · PWA · faixa fixa com código + status "recebendo" ·
**trocar o próprio login e a própria senha** (Painel → Minha conta e senha).

**Convidado:** QR → 1 tela (selfie + consentimento) · galeria ao vivo com abas
(minhas / todas) · **animação de chegada** + "Chegou uma foto sua!" · espera viva
("N fotos já na festa") · saídas quando não reconhece · lightbox com navegação ·
salvar/compartilhar/ZIP · **QR por foto** (a amiga que aparece junto escaneia e leva a
foto no próprio celular, na hora) · sessão persistente (volta sem refazer selfie) · PWA.

**Admin** (`admin@foton.com`): resumo geral · disco · lista de fotógrafos ·
+créditos · trocar senha · **testar foto da câmera** (valida o setup em segundos) ·
adotar eventos órfãos · forçar expiração LGPD.

**LGPD:** política publicada · consentimento destacado · selfie nunca armazenada ·
retenção automática (biometria 7d, fotos 90d) · direito de exclusão funcionando.

**Infra:** HTTPS (Let's Encrypt, renovação automática) · backup diário ·
auto-update · reinício automático · proteção contra recuperação por ociosidade ·
**monitor externo real (UptimeRobot, desde 2026-08-29)** — 3 monitores, 5 min
de verdade, alerta por e-mail. Dois são **keyword** em `/health` exigindo `"ok":true`,
o que pega servidor de pé com pipeline morto. O GitHub Actions (cadência real medida:
~5 h) fica como rede de segurança. Ver `docs/PILOTO-1.md` B5.

## 9. O que vem (priorizado)

> **`docs/PRODUTO.md` guarda o que ainda NAO virou codigo**: Foton Festa (todo mundo
> fotografa), login por selfie, a porta coletiva com fundo animado, alternativas ao
> modelo de creditos e o que falta de branding. Cada item com o que custa e o que
> precisa ser decidido. Ler antes de propor coisa nova — provavelmente ja esta la.

**Agora**
1. **Site de marca no Netlify** — vitrine, planos, links úteis, botão "Entrar".
2. **Cloudflare R2** para as fotos — tira o peso da VM (1 núcleo entrega tudo hoje);
   conta já criada, falta configurar. Egress zero (ADR-0011).
3. **Repo privado + deploy key** — com cuidado para não quebrar o auto-update.

**Depois**
4. **Segunda VM + failover** — a Oracle dá 2 grátis; DuckDNS troca o IP por API.
   Sai de ~99% para ~99,7%.
5. Login com Google · cobrança (créditos hoje são manuais) · domínio próprio.

### Pedidos do dono ainda não feitos (2026-08-28)

**Feito em 2026-08-28 (com teste real, ver `docs/TESTES.md`):** autorização das rotas ·
fila de pendentes do FTP · login de FTP conferido na hora · espelho da selfie.
**Caminho FTP validado de ponta a ponta em produção** (login de conta recém-criada,
envio, foto entrando sozinha no evento em ~7 s) — mas **com cliente FTP de script,
ainda não com a Canon**.

**Pendências abertas:**
- ✅ ~~Senha da Patrícia em texto puro num repo público~~ — **RESOLVIDO em 2026-08-29**:
  login e senha **trocados em produção** (o login virou `patriciavargas`). As credenciais
  antigas dão 401 — o que ficou no histórico do git não abre mais nada.
  ⚠ **Ela precisa das credenciais novas**: a sessão do celular dela caiu junto (a troca
  derruba todas as sessões, de propósito). E a **senha do FTP mudou** com o login.
  Daqui pra frente ela mesma troca a própria senha em **Painel → Minha conta e senha**
  (ADR-0019), sem depender do dono.
- Fotos são BLOB no SQLite × 7 backups completos (disco) — medido, com folga hoje.

**Já corrigido (não é mais pendência):** ~~semente do FTP derivável do repo público~~ — a
semente é gerada com `secrets.token_urlsafe(24)` na primeira execução e guardada no banco
(`store.segredo`), não no código; `/camera/config` exige sessão (401 para anônimo e para
token inválido) e devolve **só a senha da própria conta**. ~~Sem rate limit no `/login`~~ —
10 falhas/10 min por IP → 429.

**a) ENCONTRO PRESENCIAL FEITO (2026-08-28) — resultado real**

   ✅ **O produto funcionou.** A Patrícia aprovou o protótipo. Tudo que foi enviado
   pelo celular funcionou: 35 fotos, 4 eventos, 19 convidados registrados em produção.
   Nada falhou no pipeline.

   ❌ **As câmeras não conectaram.** É a única frustração do dia, e virou a
   **prioridade nº 1**: o dono prometeu fazer a R8 e a T6s "clicarem e a foto já ir
   pro Fóton".

   **Inventário definitivo (não perguntar de novo):** ela tem **Canon R8 + Canon T6s
   (760D)**. Ela **NÃO tem R6** — hipótese levantada e descartada pelo dono.
   **Nenhuma das duas tem FTP** — verificado no menu das duas, presencialmente.
   Logo, o servidor FTP do Fóton (que funciona) **não serve para esta cliente**.

   **Causa raiz da frustração no encontro: o tutorial do nosso app estava errado.**
   Ele mandava procurar `MENU → (rede) → Configurações de Wi-Fi`, que **não existe
   com esse nome na R8**. O caminho certo (manual oficial Canon, C013) é:
   `MENU → Funções de comunicação → Conectar a smartphone(tablet)`. Corrigido no app.

   **Descoberta que muda o jogo — a R8 TEM envio automático:**
   `Funções de comunicação → Conectar a smartphone(tablet) → Enviar para smartphone
   após o disparo → Envio automático: Ativar`. Com isso **cada foto cai sozinha no
   celular dela**, sem tocar na câmera. Metade do caminho já está resolvida.

   **O elo que faltava — FEITO em 2026-08-29 (ADR-0018):** com o app instalado, o
   **Fóton aparece no menu "Compartilhar" do Android**. Ela seleciona o lote na galeria,
   toca em Compartilhar → Fóton, e **dentro do app não toca em mais nada** — o lote entra
   sozinho no último evento que ela abriu. Medido em produção: 2 gestos no app → **0**.
   **Ressalva honesta:** a seleção das fotos na galeria continua sendo humana, e nenhuma
   API web no Android muda isso. Por 100 fotos: ~106 gestos antes → **~5 se a galeria
   dela selecionar por arrasto, ~103 se não**. Qual dos dois é
   `UNKNOWN — REQUIRES EXPERIMENT` (5 minutos no celular dela). As duas alternativas de
   zero gesto — EOS Utility num notebook, ou app Android nativo — estão orçadas em
   `docs/PILOTO-1.md`, aguardando decisão do dono.

   T6s (760D, 2015): envio automático após disparo provavelmente **não existe**
   (recurso de gerações novas) — `UNKNOWN — REQUIRES EXPERIMENT`.
   - **É o maior risco em aberto.** Fazer um ensaio presencial com as duas câmeras
     antes de qualquer evento pago. Usar o "testar foto" do admin para validar na hora.

**b) Deixar explícito que serve para os DOIS públicos** (hoje a comunicação só fala
   de fotógrafo com DSLR):
   - **Fotógrafo profissional** com DSLR/mirrorless (Canon, Nikon, Sony).
   - **Quem fotografa com o celular mesmo** — o app já aceita, mas isso não está
     dito em lugar nenhum. Precisa aparecer na home e no site de marca.

**c) FREEMIUM com nossa marca na foto** (modelo de negócio):
   - Pessoa comum (ex.: alguém numa balada) cria conta grátis e usa o Fóton no
     próprio rolê; as fotos saem com a **marca d'água do Fóton** = propaganda nossa
     circulando nas redes.
   - O **plano pago troca a marca pela do fotógrafo** — é exatamente o gatilho de
     conversão já identificado (nenhum profissional aceita marca de terceiro).
   - Isso transforma cada usuário grátis em canal de aquisição. Definir limites do
     grátis (nº de eventos/fotos, retenção) junto com o preço.

**Riscos conhecidos**
- **1 vCPU / 1 GB** é o gargalo real. Migrar para ARM quando houver estoque, ou VM paga.
- **Always Free não tem SLA.** Expectativa honesta: ~99%.
- **Fotos servidas pela VM** — R2 resolve.

### Carga MEDIDA em produção (2026-08-28)

| Cenário | Resultado |
|---|---|
| 8 selfies simultâneas | **1 s no total** — tranquilo |
| 1 foto de câmera (24 MP, 13 MB) | **2,9 s** (upload + tratamento + reconhecimento) |
| 4 fotos de câmera em rajada | **19 s no total** (~4,8 s cada — enfileiram no único núcleo) |

**⚠ SUPERADO — ver a medição de 2026-08-29 em `docs/BENCHMARKS.md`.** A leitura abaixo
foi feita antes do `reduzir()` no celular e do `Image.draft()` no servidor, e era
**pessimista**. Medido depois: **50 fotos de 2,1 MB em 55,6 s, P95 de 1,9 s, zero
perdida**; e **30 selfies simultâneas em 8,2 s** — a selfie virou o gargalo, não a foto.

**Leitura honesta:** foto isolada cumpre o SLA de 10 s. **Em rajada, não.** 20 fotos de
uma vez levam ~1,5 min; 50 fotos, ~4 min. Selfies de convidados são baratas; **o custo
está no upload de fotos grandes**. Mitigações, em ordem: reduzir a foto no celular antes
de subir · mais núcleos (ARM/VM paga) · fila com prioridade para selfies.

## 10. Modelo comercial

### Proposta da Patrícia (áudio de 2026-08-28) — AGUARDA DECISÃO DO DONO

No áudio ela propõe, por conta própria, duas coisas que mudam o negócio:

1. **Sociedade / revenda:** ela leva o Fóton nos trabalhos dela e repassa **50% de
   tudo que vender** com o programa. Deixa de ser só cliente e vira **canal de
   aquisição** — é a "máquina de aquisição" que o dono quer provar.
2. **Alugar em vez de vender:** *"em vez de você vender o programa, você alugar…
   porque aí você vai ganhar mais. Se você vender, ganha o seu na hora e não ganha
   mais."* — ela está **pedindo recorrência**.

⚠️ Isso **contradiz a premissa do ADR-0012** ("a cliente não quer mensalidade").
A premissa nasceu de conversa anterior e agora a própria cliente propõe o oposto.
**Não decidir sozinho:** revisitar o ADR-0012 com o dono antes de fixar preço.

Ela também se ofereceu para levar **as duas câmeras** ao encontro e fazer um teste
no evento "do dia dois", possivelmente com um ajudante.

### Modelo hoje (registrado)

**Pagamento único / créditos por evento** (ADR-0012 — a cliente não quer mensalidade).
Custo marginal por evento é ~centavos; o custo relevante é o fixo (hoje ~R$0 na Oracle).
Preço final aguarda medição real (EXP-10). Marca própria nas fotos é o gatilho do
plano pago — nenhum profissional aceita marca de terceiro no trabalho dele.
