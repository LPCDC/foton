# Prompt para a próxima sessão

> Cole isto numa sessão nova, ou diga só: **"continua do PROMPT-PROXIMA-SESSAO.md"**.
> **Versão de 2026-08-30, fim do dia.** A sessão anterior rodou em Opus; esta roda em
> **Sonnet 5**. Escrito para ser executável sem reconstruir contexto.

Fóton — continuação. Antes de tocar em qualquer coisa: `BLUEPRINT.md`, `docs/PRODUTO.md`
§1–§3, `docs/DECISIONS.md` da ADR-0025 em diante, `docs/BACKUP.md` e `docs/IDEIAS-V2.md`.
Onde documento e código divergirem, **o código ganha** e corrigir o documento é parte da
tarefa. Nada é "pronto" sem rodar e ler a saída.

## Como este projeto trabalha (não negociável)

- `bash tests/todos.sh` antes de todo push. Hoje: **263 checagens, 4 suítes**.
- Mudou modelo de dados? Declare ANTES: entidades, migração, LGPD, testes, rollback.
  O padrão daqui é ALTER guardado com **NULL = comportamento idêntico ao de hoje**.
- Deploy é `git push origin main` (~2 min). **Validar sempre pelo SHA exato:**
  `curl -s https://app.foton.app.br/health` → o campo `versao` tem que bater com
  `git rev-parse --short=7 HEAD`. Verificação que não checa o SHA não vale (já deu
  falso positivo nesta sessão).
- Não inventar número nem explicação. Sem medição → `UNKNOWN — REQUIRES EXPERIMENT`.

## Estado em 2026-08-30 (tudo verificado em produção)

- **Domínios SEPARADOS e funcionando:** `foton.app.br` + `www` → site novo no Netlify
  (confirmado: `Server: Netlify`, HTTP 200, TLS ok); `app.foton.app.br` → o app na VM.
  NS na Cloudflare (`ernest`/`kristina`), os 3 registros em **DNS only** (cinza).
- **Feito nesta sessão:** teto de 50 na galeria (~24× menos render) · zoom na foto
  (pinça/arrastar/duplo-toque) · arrastar-para-atualizar · confirmação ao sair · voltar
  sem refazer selfie · idempotência de ingestão (`photo.sha`) · `/health` real com
  `versao` · `/admin/latencias` (P50/95/99) · admin promovível pelo painel · contatos
  mascarados por padrão · pele `social` atribuível · preview da câmera 4K→2560 (dono
  confirmou ganho de FPS) · prova de restauração de backup.

## O que fazer, em ordem de risco

### 1. Backup fora da VM — ÚNICO RISCO IRREVERSÍVEL, faça primeiro
`infra/backup-externo.sh` está escrito e **nunca rodou**. As 7 cópias moram no mesmo
disco da mesma VM: perder a máquina (Oracle Always Free pode recuperar instância) leva o
acervo do GLAMON junto. Precisa: bucket no R2 + chaves + Cloud Shell do dono.
Instruções no topo do script. Depois vira ADR. Ver `docs/BACKUP.md`.

### 2. Certificado — PRAZO DURO: antes de 28/10/2026
Agora que raiz e `www` saíram da VM, o certbot **não consegue mais validá-los** e a
renovação inteira falha — incluindo `app.foton.app.br`, que quebra em **27/11/2026**.
Comando exato em `docs/DNS-MIGRACAO.md` passo 5. O `renew --dry-run` no fim é a prova;
não pule.

### 3. Experimento de limiar → destrava o reencontro por selfie (P1)
Medir selfie↔selfie da mesma pessoa vs pessoas diferentes usando `fotos-teste/`, achar
limiar + margem, registrar em BENCHMARKS. **Só então** codar. Escopo é SEMPRE dentro de
um evento — busca global de rosto é proibida (PRODUTO §3b).

### 4. Foto'n Fiesta — regras já decididas pelo dono (PRODUTO §2)
50 fotos por participante (por sessão, **nunca por IP**) · participante apaga a própria
foto **exceto onde houver mais rostos** (`n_faces > 1` esconde o botão) · corte de
conteúdo é **genitália e mamilo**, não "nudez" genérica (decote e vestido de festa
passam). Falta o mecanismo de moderação — tem tensão real com o "na hora", ver
IDEIAS-V2 §A.1.

### 5. Barato e desbloqueado (fazer quando o dono pedir)
Ordenar galeria por pessoas (`n_faces` já vem do servidor — falta só o seletor) ·
coração/favoritos · `photo.oculta` (pré-cadastro) · rate limiting por rota · feature
flags (a tabela `config` já existe) · auditoria administrativa.

## Sem prova real — não tratar como pronto

- **Idempotência nunca rodou em produção.** Mandar a mesma foto 2× pelo app deve
  devolver `"duplicada": true`.
- **`/admin/latencias` sem amostras de evento real** — o P95 só significa algo depois.
- **Item 0 (saúde do GLAMON)** nunca foi coletado: contagem, bytes, disco. Decide a
  urgência do R2. Precisa do token admin do dono.

## O que NÃO fazer

Login e-mail/senha fica (ADR-0019/0026) · crédito cortado fica (ADR-0024) · FTP quieto ·
nenhuma credencial no repo (é público) · não reprocessar foto entregue (ADR-0028) ·
`ensaio.py` nunca em massa · busca global de rosto NÃO · menores fora de escopo
(ADR-0029) · double-tap NUNCA na grade (só no lightbox) · `infra/dominio.sh` NÃO serve
para encolher certificado (só expande).

## Armadilhas que já custaram caro

- O painel da Cloudflare tem um modal ("Welcome to the new DNS experience") que **come
  todos os cliques** até ser fechado. E o toggle de proxy só existe **dentro do Edit**
  de cada registro, não na lista.
- `prompt()` não funciona em PWA no Android (aparece sem caixa de digitar). Escolha
  precisa ser botão.
- Antes de criar função no `index.html`, **conferir se o nome já existe** — quase houve
  colisão com `aplicarPerfil()`, que teria quebrado o app inteiro. `tests/test_front.py`
  pega isso.

## Comandos

```
bash tests/todos.sh                                          # 263 checagens
git add -A && git commit -m "..." && git push origin main    # deploy (~2 min)
curl -s https://app.foton.app.br/health                      # conferir SHA
bash infra/conferir-dns.sh                                   # estado dos dominios
```
