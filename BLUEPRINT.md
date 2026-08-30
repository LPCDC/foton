# FÓTON — Blueprint

> **Leia isto primeiro em qualquer sessão nova.** Resume o que é, onde está, como mexer
> e o que vem. Escrito para retomar o trabalho sem reler o histórico.
> Atualizado: 2026-08-30

---

## 1. O que é

**Fóton** — as fotos do evento chegam **sozinhas** no celular de quem aparece nelas,
**durante a festa**. O convidado escaneia um QR, tira 1 selfie, e as fotos em que ele
aparece caem na galeria dele ao vivo.

- **Cliente pagante:** fotógrafo de eventos (primeira: **Patrícia Vargas**,
  Santos/Baixada; segunda: **GLAMON**, salão em Santos, usando o Fóton como álbum
  permanente de clientes).
- **Usuário final:** o convidado (usa 2 minutos na vida, sem instalar nada).
- **Diferencial:** entrega **ao vivo**, em português, para um mercado que os
  concorrentes internacionais não atendem no preço.
- **Concorrentes:** FotoOwl, SpotMyPhotos (~US$142/mês), EventHex, SnapSeek.
  Todos entregam "link para depois"; nosso wedge é o **tempo real**.
- **Três portas de entrada na home:** Vou fotografar · Sou convidado · **Sou empresa**
  (conta com galeria permanente, ex.: GLAMON — ver §8).

## 2. Onde está (produção)

| | |
|---|---|
| **App (tudo)** | **https://app.foton.app.br** (domínio próprio, desde 2026-08-29) |
| App (endereço antigo) | https://getfoton.duckdns.org — continua funcionando, mesmo certificado |
| Servidor | Oracle Cloud Always Free, São Paulo · `152.67.46.113` |
| Máquina | `VM.Standard.E2.1.Micro` — 1 vCPU, 1 GB RAM + 2 GB swap |
| Código | https://github.com/LPCDC/foton (público — ver §7) |
| Repo local | `C:\Users\Pichau\Menir ClickPal` |
| Netlify | `getfoton.netlify.app` — só demo antiga; **virará o site de marca** |

**Credenciais:** ficam **fora do repo** (ele é público), em
`C:\Users\Pichau\foton-acessos.md`. Esse arquivo tem a lista completa e o porquê o
painel não mostra senha nenhuma (PBKDF2, irreversível de propósito).

> ⚠️ A senha da Patrícia esteve no repo em texto puro até 2026-08-29 e continua no
> histórico do git — por isso **login e senha foram trocados em produção** naquele dia.
> O que ficou no histórico não abre mais nada. A fotógrafa troca a própria senha em
> **Painel → Minha conta e senha** (ADR-0019).
>
> A conta de administração **não é mais `admin@foton.com`** — foi substituída em
> 2026-08-28 por um login sem esse endereço, para não deixar rastro de e-mail de
> administração num repositório público. Quem é admin é decidido pela lista
> `FOTON_ADMINS` **no servidor**; o cliente só obedece (ADR-0025 — ver a armadilha
> correspondente em §7).

## 3. Como funciona (pipeline)

```
FOTÓGRAFA cria evento → sai um QR                       (sem custo — crédito cortado, §10)
CONVIDADO escaneia → 1 selfie → vira vetor facial (a selfie é DESCARTADA)
FOTÓGRAFA fotografa → a foto chega ao servidor por 3 caminhos:
   (a) app: câmera de dentro do app, ou galeria do celular (lote, com retry)
   (b) app instalado: menu "Compartilhar" do Android entrega o lote direto (ADR-0018)
   (c) FTP: a câmera envia SOZINHA (câmeras PROFISSIONAIS com FTP — não é o caso da
       Patrícia: Canon R8 e T6s NÃO têm FTP, verificado presencialmente) → porta 2121
SERVIDOR: reduz p/ 2048px → marca d'água do fotógrafo → detecta rostos (SCRFD)
          → embedding (ArcFace) → compara com os convidados → publica p/ quem casar
          → gera MINIATURA (320px, coluna própria — ADR-0022)
CONVIDADO: a foto aparece sozinha, com animação; baixa/compartilha/dá QR para quem
           aparece junto (ADR-0020); pode selecionar várias segurando o dedo
```

**Reconhecimento:** InsightFace **buffalo_s** (SCRFD + ArcFace), CPU, `det_size=640`,
limiar cosseno **0.25**. Validado: 99,5% no LFW.
⚠️ `det_size=320` fazia rosto de 90px **não ser detectado** (0/6). Não reduzir.

## 4. Estrutura do código

```
app/test_rig/
  rig.py         FastAPI: rotas, pipeline, admin, LGPD, FTP, elevação de conta empresa
  store.py       SQLite: contas, eventos, fotos, rostos, convidados, contatos, thumbs
  ftp_camera.py  servidor FTP (câmera envia direto — só serve câmera PROFISSIONAL)
  models/buffalo_s/  ONNX empacotado (não baixa em runtime)
app/web/
  index.html     TODO o front (uma página, sem framework) — fotógrafa + convidado +
                 empresa + admin. ~205 mil bytes. Pontos de entrada relevantes:
                 badgeSVG()/diafragmaSVG() — a marca (§8) · estadoDaCamera() — cartão
                 do painel · armarToqueLongo() — segurar para selecionar · filaGravar()
                 e companhia — fila de upload persistente em IndexedDB.
  sw.js          service worker: cache-first só de estáticos, NUNCA de resposta com
                 sessão (armadilha paga, §7); atende o Web Share Target (ADR-0018)
  manifest.webmanifest   share_target (campo "fotos")
  assets/        fotos de demonstração
tests/
  test_autorizacao.py   193 checagens — contrato de todas as rotas, LGPD, admin
  test_front.py         24 checagens — o front como TEXTO: sintaxe JS de verdade
                         (node --check), ids duplicados, funções essenciais presentes,
                         fila grava em disco ANTES da rede. Nasceu de estragos reais.
  test_ftp_camera.py    23 checagens — servidor FTP
  test_logo.py          16 checagens — marca d'água do FOTÓGRAFO na foto (não é a
                         marca do Fóton — são duas coisas diferentes com nome parecido)
  todos.sh       roda as 4 suítes e FALHA (exit ≠ 0) se qualquer uma falhar — existe
                 porque um `&&` mal escrito já deixou subir com suíte vermelha. Rodar
                 sempre antes de `git push`.
  ensaio.py      NÃO é suíte automática — ensaio com fotos REAIS do dono, em
                 fotos-teste/ (gitignored, o repo é público), cria e apaga um evento
                 de teste em produção. Rodar com bom senso, não em massa (pedido do
                 dono em 2026-08-30 — cuidado reafirmado para quando o R2 chegar).
infra/           scripts de VM, HTTPS, FTP, backup
docs/
  DECISIONS.md   25 ADRs — leia antes de mudar arquitetura ou dependência
  PRODUTO.md     o que NÃO virou código ainda (Fóton Festa, login por selfie, chat em
                 emoji, pré-cadastro com nome/Instagram, limite de upload) — ler antes
                 de propor algo novo, provavelmente já está lá
  BENCHMARKS.md, PILOTO-1.md, TESTES.md, ROTEIRO-CAMERAS.md   medições reais
  ARCHITECTURE.md, ROADMAP.md, parte antiga de GAUNTLET.md   HISTÓRICO do
                 planejamento original — cada um avisa no topo o que mudou
```

**Dados (nunca apagar):** `/var/lib/foton/foton.db` + `backup/` (7 cópias diárias).

## 5. Como fazer deploy

**Basta `git push`.** A VM tem auto-update (systemd timer, 2 min) que puxa `origin/main`,
reinstala dependências se mudaram e reinicia o serviço (~25 s de 502 no meio).

```bash
bash tests/todos.sh && git add -A && git commit -m "..." && git push origin main
# aguardar ~2 min e validar:
curl -s https://app.foton.app.br/health
```

**Sobre deploy com evento ao vivo:** a regra original era não fazer deploy nessa
condição. **O dono revisou isso em 2026-08-30**, nesta fase de testes: *"faça deploy
sim nessa fase de teste quando tem evento ao vivo. você saberá quando terá coisa
grande."* Ou seja: **deploy liberado por padrão agora**, com bom senso do agente para
o que é "coisa grande" — mudança na fila de upload, no pipeline de reconhecimento ou
algo que pode deixar a fotógrafa sem receber foto no meio de um evento pago de verdade
ainda pede cautela extra (checar `/admin/saude`: última foto, carga da máquina) e, na
dúvida, perguntar. `/admin/saude` **não serve mais** para detectar "evento ao vivo" por
si só — GLAMON e Carol ficam marcadas `ao_vivo` permanentemente (álbuns de propósito
duradouro); o sinal real é última foto + carga.

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
5. **Sem segredo no git.** Senhas e tokens só em env/Secrets/`foton-acessos.md` (fora
   do repo).
6. **Reportar com honestidade** — falhou é falhou, com a saída.
7. **Autorização nunca se infere do formato de um dado no cliente** (ADR-0025) — quem
   decide poder é sempre o servidor.
8. **Barra invertida não passa por heredoc de shell.** Uma string JS delicada
   (`\n` dentro de um `confirm()`, por exemplo) que passa por um heredoc bash já virou
   quebra de linha real e corrompeu o app inteiro, mais de uma vez nesta sessão. Ao
   escrever JS com barra invertida literal via script Python, montar o caractere com
   `chr(92)` em vez de escrevê-lo direto na string do shell — e se o heredoc em si
   falhar (ex.: erro de parsing do shell sem motivo aparente), trocar para a
   ferramenta de escrita de arquivo direta em vez de insistir.

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
| **`/signup` podia reivindicar um login de admin** | O cadastro é aberto e **não conferia a lista de admins**, que vive no código de um **repo público**. Fechado em 2026-08-29 (403), com teste. **Rota que concede poder precisa conferir quem pode.** |
| **Leitura que escreve** | `GET /stats`, `GET /photos` e `GET /feed` usavam `create=True`: **ler criava evento**. Hoje as três devolvem 404. **Rota de leitura nunca escreve.** |
| **SQLite não devolve espaço** | Apagar evento marcava o espaço como livre **dentro** do arquivo; o arquivo nunca encolhia, e como o backup guarda 7 cópias, cada MB não recuperado custava 8 MB de disco. Hoje: `/admin/compactar` (VACUUM + `wal_checkpoint(TRUNCATE)`, nessa ordem — o checkpoint sozinho não basta). |
| **Deploy tem ~25 s de 502** | O auto-update reinicia o serviço. Ver §5 sobre a regra de evento ao vivo, revisada em 2026-08-30. |
| **Autorização de admin inferida do FORMATO de um dado no cliente** | `EH_ADMIN` no front era `/^admin@/.test(email)`. Quando o login de administração deixou de ter arroba (virou `admin`, não mais `admin@foton.com`), o teste passou a dar **falso** silenciosamente: o painel de administração existia, o servidor autorizava, e **o botão nunca aparecia**. Corrigido (ADR-0025): `/login`, `/signup` e `/me` informam `admin: bool`; o cliente obedece o servidor, não adivinha pelo texto do e-mail. |
| **Barra invertida através de heredoc de shell** | Ao escrever uma string JS com `\n` literal (dentro de um `confirm()`) usando um heredoc de shell para gerar o script Python que edita o arquivo, o `\n` virou **quebra de linha real** dentro da string JavaScript, cortando-a no meio e derrubando `node --check`. Pego antes do deploy — era exatamente para isso que o teste de sintaxe existe. Regra: montar barra invertida literal com `chr(92)`, nunca confiar no shell para preservá-la. |
| **Texto de estado que mentia** | O cartão de status da câmera dizia "FTP ligado, nenhuma foto ainda" para uma conta (Carol) que tinha **30 fotos** no painel, uma linha acima. O texto falava da CÂMERA (nenhuma câmera de FTP jamais conectou), mas usava vocabulário de FOTOS. Visto na tela, corrigido no mesmo turno. **Todo texto de estado tem que ser lido ao lado do número que ele poderia contradizer.** |
| **Segurar a miniatura abria o menu do navegador** | Não havia gesto de toque longo — só um botão "Escolher algumas" — e o alvo do toque era o `<img>`, por isso o Android oferecia ações de IMAGEM ("salvar", "abrir em nova aba") em vez de selecionar. Corrigido: a miniatura não recebe toque (`pointer-events:none`), o `contextmenu` é barrado, e segurar 450 ms entra no modo seleção. |
| **Página com mais conteúdo do que a tela = "fundo desliza" ao arrastar** | A home tinha até 146px de conteúdo além da viewport (dois links de rodapé ficavam fora da dobra) — arrastar o dedo rolava a página de verdade uns 20-40px, e o fundo (`position:absolute`, preso ao `.stage` que rolava junto) parecia "deslizar". Não era ilusão nem bug de touch: era overflow real, medido com `document.scrollingElement.scrollHeight`. Corrigido por dois lados — espaçamentos apertados até o overflow zerar em telas comuns, e `.stage-bg`/`.stage-fade` viraram `position:fixed` (nunca mais se movem, mesmo que sobre 1px de rolagem numa tela bem baixa). **Ao investigar "elemento X parece causar Y", meça removendo/escondendo X de verdade antes de reescrever CSS em cima dele** — a suspeita inicial (a barra de progresso `.prog`, fixed com `transform` pra ficar fora da tela) foi **descartada por teste direto** (escondê-la não mudou o `scrollHeight` nem 1px); só a medição salvou de uma correção no lugar errado. |
| **Sessão persistente só restaurava com o código já em mãos** | O convidado já tinha sessão de 24h salva (`saveGuestSession`), mas só era restaurada se o app já soubesse o código do evento (link direto ou digitado) — fechar pelo ícone da tela inicial (sem parâmetro na URL) sempre caía na home pedindo o código de novo. É o **mesmo bug, do outro lado**: já tinha sido corrigido para a fotógrafa (a IIFE de boot que restaura `go('dash')` com o token salvo). Corrigido com o mesmo padrão: um marcador `foton_guest_ultimo_ev` (paralelo a `ultimoEvento`/`lembrarEvento`), checado no boot quando não há link direto na URL nem sessão de fotógrafa para restaurar. **Um bug corrigido de um lado do app é motivo para checar o espelho dele do outro lado.** |
| **Segurar em texto abria "Pesquisar no Google" do Chrome** | Sem `user-select:none` global, segurar o dedo num título ou texto de botão selecionava a palavra e o Android oferecia buscar/compartilhar por cima do app — texto de app não é texto de página. Já existia a proteção nas miniaturas de foto (armadilha acima); faltava no resto. Corrigido: `user-select:none` em `html,body`, com exceção explícita para `input`, `textarea` e uma classe `.selecionavel` para o que precisar no futuro. |

## 8. Estado atual (o que funciona hoje)

**Fotógrafa:** conta com senha, **sem custo** (crédito cortado em 2026-08-30 — ADR-0024,
ver §10) · criar/encerrar/apagar evento · marca d'água própria (upload de logo,
`test_logo.py`) · QR (tela cheia + imprimível) · câmera de dentro do app com fallback
para a câmera nativa · upload em lote com barra de progresso e retry, **fila persistente
em IndexedDB** que sobrevive a fechar o app no meio de um envio · receber fotos pelo
menu "Compartilhar" do Android (PWA instalado, ADR-0018) · **cartão de status da
câmera no painel** — verde (FTP conectou há pouco), âmbar (FTP ligado, sem conexão
recente) ou cinza (sem FTP — R8/T6s, o caminho é o celular); nunca inventa "conectada"
quando não dá para saber · **segurar uma miniatura para selecionar várias e apagar em
lote** · apagar foto individual · convidados ao vivo + contatos · resumo ao encerrar ·
FTP da câmera (para quem tem câmera PROFISSIONAL com FTP) · trocar o próprio
login/senha (ADR-0019) · **conta "empresa"** (ex.: GLAMON) com galeria permanente,
elevação por senha de admin para criar/apagar álbum.

**Convidado:** QR → 1 tela (selfie + consentimento) · galeria ao vivo com abas
(minhas / todas) · animação de chegada + "Chegou uma foto sua!" · espera viva ·
lightbox com navegação · salvar/compartilhar/ZIP · **segurar uma foto para selecionar
várias** (compartilhar as melhores para o grupo, sem precisar de todas nem de uma só) ·
QR por foto (ADR-0020 — quem aparece junto escaneia e leva a foto no próprio celular) ·
**sessão persistente de verdade** — "uma vez logado, sempre": mesmo fechando o app pelo
ícone da tela inicial, sem link nem código na URL, volta direto pra galeria (24h,
testado ponta a ponta contra produção em 2026-08-30) · **"Apagar minha selfie e sair
deste evento"**, visível na própria galeria, sem precisar falar com ninguém — é a
condição da decisão do dono sobre nome/Instagram no pré-cadastro (`docs/PRODUTO.md`
§3b-2) e também o que limpa a sessão persistente acima · PWA.

**Admin** (login `admin`, não mais `admin@foton.com` — ver §2): resumo geral · disco ·
lista de fotógrafos + histórico de crédito (não gasto mais, só histórico) · marcar
conta como empresa · retenção de biometria configurável por conta · zerar dados
(mantém logins, senhas, marca, logo) · compactar banco · trocar senha de outra conta ·
testar foto da câmera (valida o setup em segundos) · adotar eventos órfãos · forçar
expiração LGPD · lista de contatos.

**A marca (2026-08-30):** redesenhada — um **diafragma** construído de verdade (seis
lâminas tangentes ao hexágono da abertura, coordenadas calculadas) com um único
**ponto de luz dentro, fora do centro** de propósito. Ideia: Fóton é uma partícula de
luz; o produto é uma lente que acha *você* no meio de muitos. Funções `badgeSVG()` e
`diafragmaSVG()` em `app/web/index.html`. Na home ela é grande e centralizada, com um
teto de tamanho em `vh` além do de `vw` — sem isso a marca em 300px empurrava a
terceira porta ("Sou empresa") para fora da primeira tela do celular. O fundo por trás
dela (`.stage-bg`/`.stage-fade`) é `position:fixed` — não se move mesmo se a página
rolar um pouco (ver armadilha em §7).

**Toque no app (2026-08-30):** texto do app não é mais selecionável (título, legenda,
botão) — segurar o dedo não seleciona palavra nem abre o popup "Pesquisar no Google"
do Chrome. Campos de digitar (código do evento, senha, etc.) continuam selecionáveis
normalmente.

**LGPD:** política publicada · consentimento destacado · selfie nunca armazenada ·
retenção automática (biometria 7d por padrão, configurável por conta; fotos 90d) ·
**direito de exclusão com botão visível na galeria da convidada** (não mais só numa
tela de privacidade escondida) · **decisão registrada sobre nome/Instagram no
pré-cadastro** (`docs/PRODUTO.md` §3b-2): o organizador do evento é o **controlador**
na LGPD e faz o vínculo rosto↔nome; a convidada escolhe apenas se isso **aparece** para
os outros. Condição para essa decisão continuar válida: contrato com o organizador,
padrão de exibição desligado, e o botão de saída acima — que já existe.

**Infra:** HTTPS (Let's Encrypt, renovação automática) · backup diário · auto-update ·
reinício automático · proteção contra recuperação por ociosidade · monitor externo real
(UptimeRobot, desde 2026-08-29) — 3 monitores, 5 min de verdade, alerta por e-mail;
dois são **keyword** em `/health` exigindo `"ok":true`. O GitHub Actions (cadência real
medida: ~5 h) fica como rede de segurança. **O alerta do monitor nunca foi visto
disparar de verdade** — `UNKNOWN — REQUIRES EXPERIMENT` até alguém ver um e-mail/
WhatsApp chegar.

## 9. O que vem (priorizado)

> **`docs/PRODUTO.md` guarda o que ainda NÃO virou código**: Fóton Festa (todo mundo
> fotografa), login por selfie, chat em emoji dentro do evento, limite de upload no
> lugar do crédito, o que falta de branding. Cada item com o que custa e o que precisa
> ser decidido. Ler antes de propor coisa nova — provavelmente já está lá.

**Maior risco do piloto agora, e não é código:**
1. `UNKNOWN — REQUIRES EXPERIMENT`: o Fóton aparece no menu Compartilhar do Android da
   Patrícia? A galeria dela seleciona várias fotos de uma vez, por arrasto? A T6s tem
   algum jeito de mandar foto sozinha? Nenhuma das três foi testada com o aparelho dela
   — o dono ainda não a encontrou pessoalmente para isso.
2. **TTFR (Time to First Relevant Photo) fim a fim nunca foi medido** com relógio nas
   duas pontas — só as partes (`/ingest` P95 1,9s + poll 2,5s). É o número que prova a
   promessa do produto.
3. **30 selfies simultâneas: P95 8,2s** — a entrada de convidados, não o envio de
   fotos, é o gargalo real numa festa (todo mundo escaneia o QR nos mesmos 5 minutos).

**Depois**
4. **Login com Google** para fotógrafas — investigado e **rejeitado por ora** em
   2026-08-30 (ADR-0026): o canal de auto-cadastro que o Google "ajudaria" **já existe**
   (`/signup` é aberto), ninguém pediu recuperação de senha, e o celular emprestado (caso
   real desta fotógrafa) torna o login Google mais confuso, não menos. Gatilho de
   reversão escrito na ADR: canal público de aquisição com volume real, pedido de
   recuperação de senha, ou domínio com reputação suficiente para não disparar o aviso
   "app não verificado" do Google.
5. **Site de marca no Netlify** — vitrine, planos, links úteis, botão "Entrar".
6. **Cloudflare R2** para as fotos — tira o peso da VM (1 núcleo entrega tudo hoje);
   conta já criada, falta configurar. Egress zero (ADR-0011). Bloqueia vídeo (ADR-0023)
   e miniaturas maiores.
7. **Repo privado + deploy key** — com cuidado para não quebrar o auto-update.
8. **Segunda VM + failover** — a Oracle dá 2 grátis; DuckDNS troca o IP por API.
9. **Chat em emoji dentro do evento** (`docs/PRODUTO.md` §3d) — desenhado, sem uma
   linha de código. Barato (o poll de 2,5s já existe), mas depois do piloto.

## 10. Modelo comercial

**Crédito cortado em 2026-08-30 (ADR-0024), decisão do dono.** Nesta fase, criar
evento é **grátis**, com login obrigatório. As colunas `credits`/`credits_total`
continuam no banco (histórico, painel do admin), mas nada é gasto e nada bloqueia. O
substituto planejado é **limite de upload** (`docs/PRODUTO.md` §3c) — mede o que de
fato custa (disco e CPU) — mas o COGS real ainda **não foi medido**:
`UNKNOWN — REQUIRES EXPERIMENT`.

**Em aberto, não decidido:** a proposta da Patrícia de sociedade/revenda (50% do que
ela vender com o programa) ou aluguel em vez de venda avulsa — contradiz a premissa
original do ADR-0012 ("a cliente não quer mensalidade"). Revisitar com o dono antes de
fixar preço, quando a fase de teste terminar e o modelo comercial voltar à mesa.
