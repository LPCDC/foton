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
| **App (tudo)** | **https://getfoton.duckdns.org** |
| Servidor | Oracle Cloud Always Free, São Paulo · `152.67.46.113` |
| Máquina | `VM.Standard.E2.1.Micro` — 1 vCPU, 1 GB RAM + 2 GB swap |
| Código | https://github.com/LPCDC/foton (público — ver §7) |
| Repo local | `C:\Users\Pichau\Menir ClickPal` |
| Netlify | `getfoton.netlify.app` — só demo antiga; **virará o site de marca** |

**Contas de teste**
```
Fotógrafa: patricia@vargas.com / minhasenha123
Admin:     admin@foton.com / (senha trocada — ver com o dono)
```

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

## 8. Estado atual (o que funciona hoje)

**Fotógrafa:** conta com senha · criar/encerrar/apagar evento · marca d'água própria ·
QR (tela cheia + imprimível) · upload em lote com barra de progresso e retry ·
apagar foto · convidados ao vivo · contatos · resumo ao encerrar · **FTP da câmera** ·
créditos · PWA · faixa fixa com código + status "recebendo".

**Convidado:** QR → 1 tela (selfie + consentimento) · galeria ao vivo com abas
(minhas / todas) · **animação de chegada** + "Chegou uma foto sua!" · espera viva
("N fotos já na festa") · saídas quando não reconhece · lightbox com navegação ·
salvar/compartilhar/ZIP · sessão persistente (volta sem refazer selfie) · PWA.

**Admin** (`admin@foton.com`): resumo geral · disco · lista de fotógrafos ·
+créditos · trocar senha · **testar foto da câmera** (valida o setup em segundos) ·
adotar eventos órfãos · forçar expiração LGPD.

**LGPD:** política publicada · consentimento destacado · selfie nunca armazenada ·
retenção automática (biometria 7d, fotos 90d) · direito de exclusão funcionando.

**Infra:** HTTPS (Let's Encrypt, renovação automática) · backup diário ·
auto-update · reinício automático · proteção contra recuperação por ociosidade ·
monitor externo (GitHub Actions) — **falta só a chave do WhatsApp**.

## 9. O que vem (priorizado)

**Agora**
1. **Site de marca no Netlify** — vitrine, planos, links úteis, botão "Entrar".
2. **Cloudflare R2** para as fotos — tira o peso da VM (1 núcleo entrega tudo hoje);
   conta já criada, falta configurar. Egress zero (ADR-0011).
3. **Repo privado + deploy key** — com cuidado para não quebrar o auto-update.

**Depois**
4. **Segunda VM + failover** — a Oracle dá 2 grátis; DuckDNS troca o IP por API.
   Sai de ~99% para ~99,7%.
5. Login com Google · cobrança (créditos hoje são manuais) · domínio próprio.

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

**Leitura honesta:** foto isolada cumpre o SLA de 10 s. **Em rajada, não.** 20 fotos de
uma vez levam ~1,5 min; 50 fotos, ~4 min. Selfies de convidados são baratas; **o custo
está no upload de fotos grandes**. Mitigações, em ordem: reduzir a foto no celular antes
de subir · mais núcleos (ARM/VM paga) · fila com prioridade para selfies.

## 10. Modelo comercial

**Pagamento único / créditos por evento** (ADR-0012 — a cliente não quer mensalidade).
Custo marginal por evento é ~centavos; o custo relevante é o fixo (hoje ~R$0 na Oracle).
Preço final aguarda medição real (EXP-10). Marca própria nas fotos é o gatilho do
plano pago — nenhum profissional aceita marca de terceiro no trabalho dele.
