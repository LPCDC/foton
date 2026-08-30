# Prompt para a próxima sessão

> Cole isto numa sessão nova (ou diga só: **"continua do PROMPT-PROXIMA-SESSAO.md"**).
> Escrito para carregar contexto sem gastar tokens repetindo documento, e para forçar
> o rigor do Gauntlet em vez de pedir por ele.
>
> **Versão de 2026-08-30, noite.** Substitui o prompt anterior (perfis), que foi
> cumprido e virou a **ADR-0030** (três peles em produção). Esta versão é um **plano
> aprovado pelo dono** — a sessão anterior planejou, esta implementa.

---

Fóton — continuação. Antes de tocar em qualquer coisa, leia nesta ordem:
`BLUEPRINT.md` (estado geral e as armadilhas do §7 — cicatrizes reais), `docs/PRODUTO.md`
§1 e §3 (três públicos; login por selfie e suas linhas vermelhas) e `docs/DECISIONS.md`
da **ADR-0025 em diante**. Não confie na memória de treino — confie nos documentos e no
código; onde divergirem, **o código ganha**, e corrigir o documento faz parte da tarefa.

## Estado em 2026-08-30, noite (verificado com curl, não lembrado)

- App em produção (`https://app.foton.app.br`), 3 contas reais. Deploy = `git push`
  (~2 min). 4 suítes, **280 checagens**, `bash tests/todos.sh` — verde antes de todo push.
- **ADR-0030 no ar:** perfil de conta (`pro`/`empresa`/`social`) declarado pelo servidor;
  vocabulário, blocos e tokens por perfil. `social` ainda não é atribuível (sem coluna).
- **Site de marca NO AR no Netlify** (`getfoton.netlify.app`, 150 KB, site novo — o dono
  ligou o repo em 2026-08-30). DNS: zona no **registro.br** (`d/e.sec.dns.br`); raiz e
  `www` apontam para a VM `152.67.46.113`.
- **Minuta do contrato do organizador existe**: `docs/CONTRATO-ORGANIZADOR.md`
  (condição nº 1 do PRODUTO §3b-2). Falta advogado + decisão de aceite (pergunta P3).
- **Perfis, clarificado pelo dono (2026-08-30):** Patrícia = pro (câmera). **Ana =
  cliente que também contrata, mas fotografa SÓ com celular** — não é "amadora no
  rolê", é um perfil pagante sem câmera. Empresa = GLAMON.
- **O dono vai despejar fotos grandes, várias de uma vez, no álbum fixo da GLAMON**
  antes da próxima sessão. A instrumentação já existe (logs por estágio + `/admin/saude`
  + miniaturas ADR-0022); o que falta é LER os números depois — item 0 abaixo.

## Ordem de trabalho (aprovada; implementar nesta ordem)

### 0. Relatório do despejo GLAMON — ANTES de mexer em qualquer código
O dono despejou fotos no álbum GLAMON. Primeiro ato da sessão, com o token de admin
(o dono fornece — `foton-acessos.md` fora do repo):
- `/admin/saude`: última foto, carga, disco.
- Contagem e bytes do álbum GLAMON (foto cheia + thumb); crescimento do banco e do backup.
- Se o dono der acesso ao Cloud Shell: P95 do `/ingest` no período do despejo, pelos
  logs JSON. Sem acesso: registrar `UNKNOWN — REQUIRES EXPERIMENT` e seguir.
- Colar os números em `docs/BENCHMARKS.md`. **Este relatório decide a urgência do R2.**

### 1. Galeria do convidado: teto de 50 + "Mostrar mais" (pedido do dono)
`renderGuestGrid()` (`app/web/index.html:~2732`) reconstrói a grade INTEIRA a cada foto
nova — 89 fotos = 89 nós + 89 decodificações por render, e o despejo GLAMON vai piorar.
- `guestState.limite = 50` por aba (minhas/todas); render corta em `ordem.slice(0, limite)`;
  botão "Mostrar mais 50" (`grid-column:1/-1`) na base soma 50 e re-renderiza.
- Foto nova continua entrando no topo (não conta contra o limite mostrado — ajustar o
  slice para não EMPURRAR uma foto já vista para fora, senão "sumiu uma foto" vira bug).
- **Cuidado:** ZIP, seleção por toque longo e contagem usam a LISTA CHEIA, não a
  mostrada — conferir cada consumidor de `guestState.photos/todas` antes de cortar.
- Benchmark de aceite: com o álbum GLAMON real, bytes e tempo do primeiro render antes
  vs depois (esperado ~750 KB vs ~1,3 MB em 89; mais após o despejo). Colar números.

### 2. Perfil `social` atribuível + coluna (completa a ADR-0030)
- `store.py`: `ALTER TABLE photographer ADD COLUMN perfil TEXT` (guardado por try, como
  as outras). `rig.py _perfil()`: coluna explícita vence; senão deriva como hoje.
- Admin: no painel de contas, seletor pro/social/empresa (reusar o fluxo de "marcar
  empresa"). `social` NÃO mexe em poder — só apresentação (regra da ADR-0030).
- Signup: adiar oferta pública de escolha de perfil até a resposta da pergunta P2.
- Testes: estender [25] (social atribuível e revogável; front cai em pro se valor
  desconhecido — já testado no navegador em 2026-08-30).

### 3. Reencontro por selfie (o "login com selfie" do dono, na versão defensável)
O que o dono pediu: *"se o rosto se registrou, você pode tentar logar com sua selfie"*,
com interface blindada pela LGPD. O desenho que cabe nas linhas do PRODUTO §3:
- **Dentro de UM evento, sempre.** Busca global de rosto continua proibida (§3b: é
  vazamento por si só). O convidado chega pelo QR/código como hoje.
- Hoje `/selfie` sempre cria guest novo → selfie repetida = identidade duplicada e
  histórico perdido. O reencontro: comparar a selfie nova contra os convidados JÁ
  registrados do evento; se casar com **limiar de reencontro** (mais duro que os 0,25
  de agrupar fotos — 0,25 NÃO autentica, PRODUTO §3 item 4) **e margem** sobre o
  segundo colocado, reatar ao guest_id existente (galeria volta). Senão: guest novo,
  como hoje — falha silenciosa e inofensiva, nunca "você é a Carol?".
- **Limiar: `UNKNOWN — REQUIRES EXPERIMENT`.** Experimento antes do código de produção:
  com `fotos-teste/` (ensaio.py com bom senso, NUNCA em massa), medir a distância
  selfie↔selfie da mesma pessoa vs pessoas diferentes; escolher limiar com margem e
  registrar em BENCHMARKS. Sem esse número, o item não entra.
- **Onde brilha: GLAMON** (biometria não expira — a cliente volta na outra semana,
  selfie nova, histórico inteiro). Na Patrícia vale dentro da janela de retenção (7d).
  Depende da resposta do dono à pergunta P1.
- Copy LGPD na tela (ajustar com a P1): *"Já esteve aqui? Tire uma selfie nova — ela é
  comparada com quem já se registrou neste evento e descartada. Nada novo é guardado."*
- Servidor decide tudo (ADR-0025); rota `/selfie` ganha o caminho de reencontro com
  dono claro; testes de contrato: reencontro certo, abaixo do limiar cria novo,
  evento errado nunca reata.

### 4. Contrato do organizador — de minuta a produto
`docs/CONTRATO-ORGANIZADOR.md` existe. Conforme a resposta à P3:
- aceite eletrônico: checkbox ao criar o 1º evento + registro (conta, data/hora, versão)
  numa tabela `aceite` — rota com dono, teste de contrato; texto integral em `/termo`.
- Vira ADR quando o dono aceitar a minuta (com ou sem ajuste de advogado).

### 5. DNS — plano pronto, executar na ordem, NADA em paralelo
Estado real: zona no registro.br; raiz+www+app no MESMO certificado da VM. Objetivo:
raiz/www → Netlify (site), app → VM, e **preparar o R2** (que vai exigir a zona na
Cloudflare para domínio próprio de fotos, ex.: `fotos.foton.app.br`).
1. **Cert primeiro** (Cloud Shell): re-emitir cobrindo só `app.foton.app.br` +
   `getfoton.duckdns.org`; rodar `certbot renew --dry-run` para PROVAR a renovação
   (encurta a espera de "ver uma renovação passar").
2. **Zona → Cloudflare** (grátis): importar registros, `app` = A 152.67.46.113
   **DNS-only (nuvem cinza)** — proxy laranja quebraria o certbot da VM; raiz e `www` →
   Netlify (CNAME flattening / apex). Só então trocar os NS no registro.br.
3. **Validar tudo com curl** (app, raiz, www, HTTPS dos três) e registrar em BENCHMARKS.
4. R2 depois do "primeiro sucesso em evento médio" (palavra do dono): a conta já
   existe; zona na Cloudflare deixa o domínio de fotos a um passo. Egress zero
   (ADR-0011); destrava vídeo (ADR-0023) e tira as fotos do ciclo de backup ×8.
   O passo 1 é executável já; 2–3 dependem dos acessos da pergunta P4.

## O que o dono precisa dar a esta sessão (comando e permissões)

- **Comando:** "continua do PROMPT-PROXIMA-SESSAO.md" + as respostas às 5 perguntas
  abaixo (as que tiver).
- **Token/admin:** autorizar a leitura de `C:\Users\Pichau\foton-acessos.md` (fica fora
  do repo) para o item 0; ou colar só o token de admin.
- **Cloud Shell** (item 5 passo 1 e logs do item 0): rodar os comandos que a sessão
  preparar, ou dar a chave.
- **Registro.br + Cloudflare** (item 5 passo 2): criar conta Cloudflare grátis e
  autorizar a troca de NS — a sessão prepara tudo, o clique é do dono.
- **Permissões do Claude Code:** aprovar edição de arquivos e os comandos
  `bash tests/todos.sh`, `git add/commit/push`, `curl`. Deploy segue liberado com bom
  senso (regra de 2026-08-30); itens 1 e 3 tocam galeria e `/selfie` — checar
  `/admin/saude` antes do push desses dois.

## As 5 perguntas (respostas do dono moldam os itens acima)

- **P1 — Reencontro por selfie, alcance:** na GLAMON (biometria permanente), a cliente
  que volta semanas depois DEVE reencontrar todo o histórico com uma selfie nova?
  E na Patrícia, reencontro só dentro da janela de 7 dias do evento — confirma?
- **P2 — Ana:** o evento dela é (a) só ela envia fotos (perfil social = pro sem câmera,
  barato, sai já) ou (b) os convidados também enviam (Fóton Festa, PRODUTO §2 — muda o
  modelo para evento→participantes, mais caro)? Qual das duas na primeira versão? E a
  Ana se auto-cadastra escolhendo "fotografo com celular" ou o dono atribui à mão?
- **P3 — Contrato:** quem assina como organizador no casamento da Patrícia — ela ou os
  noivos? Aceite eletrônico no app (checkbox, escala) ou assinado fora (mais forte,
  ex.: GLAMON)? Pode ser os dois — qual o padrão?
- **P4 — DNS/R2:** você tem a senha do registro.br do `foton.app.br` e autoriza mover a
  zona para a Cloudflare (necessária para domínio próprio no R2 depois)? Feito na ordem
  do item 5, sem downtime.
- **P5 — Despejo GLAMON, número esperado:** quantas fotos e de que tamanho médio, de uma
  vez? Referência medida: ~530 ms de CPU por foto (200 fotos ≈ 2 min de fila) e cada MB
  no banco custa ×8 em backup. Acima de ~1.000 fotos grandes, o R2 sobe na fila.

## O que NÃO fazer (continua valendo)

Login e-mail/senha fica (ADR-0019/0026) · crédito fica cortado (ADR-0024) · FTP de
câmera quieto · nenhuma credencial no repo (público) · não reprocessar foto entregue
(ADR-0028) · `tests/ensaio.py` nunca em massa · busca global de rosto NÃO (PRODUTO §3b)
· menores de idade fora de escopo (ADR-0029).

## Comandos

```
bash tests/todos.sh                                         # 4 suítes, 280 checagens
git add -A && git commit -m "..." && git push origin main   # deploy (~2 min)
curl -s https://app.foton.app.br/health                     # validar depois
```
