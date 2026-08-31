# DNS — separar o site de venda do app (runbook)

> **Histórico — o site saiu do Netlify em 2026-08-31 (ADR-0032, `docs/DECISIONS.md`).**
> A separação raiz+www / app descrita aqui aconteceu como planejado; o que mudou depois
> foi só o hospedeiro do site (Netlify → Cloudflare Pages, mesmo crédito free do Netlify
> ter esgotado). O raciocínio de DNS/certificado abaixo continua válido para entender
> por que a ordem foi essa — só troque "Netlify" por "Cloudflare Pages" mentalmente.
>
> Estado medido em 2026-08-30, antes de mexer:
>
> | nome | aponta para | o que é |
> |---|---|---|
> | `foton.app.br` | 152.67.46.113 | a VM (o app) |
> | `www.foton.app.br` | 152.67.46.113 | a VM (o app) |
> | `app.foton.app.br` | 152.67.46.113 | a VM (o app) |
>
> Servidores de nome: `d.sec.dns.br` / `e.sec.dns.br` (o DNS do próprio registro.br).
> Certificado da VM cobre os 4 nomes (`app`, raiz, `www`, `getfoton.duckdns.org`),
> **vence em 27/11/2026**.
> Site novo já publicado e no ar em `getfoton.netlify.app` (verificado).
>
> **Objetivo:** `foton.app.br` e `www` passam a servir o SITE (Netlify);
> `app.foton.app.br` continua sendo o APP (VM). Hoje os três são a mesma coisa.

## ⚠️ A armadilha — por que a ordem do plano antigo foi trocada

O certificado da VM cobre **os quatro nomes num único certificado**. O certbot renova
validando **todos** eles: para provar que é dono de `foton.app.br`, ele precisa que
`foton.app.br` **aponte para a VM**.

No dia em que a raiz e o `www` passarem a apontar para o Netlify, essa prova falha — e
**a renovação inteira falha junto, inclusive a de `app.foton.app.br`**. O app não cai na
hora: cai em **27/11/2026**, quando o certificado vencer, com HTTPS quebrado no meio de
qualquer coisa. É a pior classe de defeito: silencioso e com data marcada.

O plano antigo mandava mexer no certificado **primeiro**. Isso resolve a armadilha, mas
cria uma janela em que a raiz e o `www` continuam na VM **sem** cobertura do certificado
— ou seja, **aviso de segurança no navegador de quem visitar**, até o DNS propagar
(horas).

**Ordem correta: DNS primeiro, certificado depois.** Durante a propagação, quem cai na VM
vê o certificado antigo (ainda válido para a raiz) e quem cai no Netlify vê o do Netlify.
**Nenhum aviso, em momento nenhum.** O passo do certificado deixa de ser urgente e passa a
ter prazo: precisa estar feito **antes de 28/10/2026** (quando o certbot começa a tentar
renovar). Anote a data.

---

## Passo 1 — Netlify: declarar o domínio (2 min)

No painel do Netlify, no site do Fóton: **Domain management → Add a domain** →
`foton.app.br`. Ele vai dizer que o DNS ainda não aponta para lá — **isso é esperado**,
siga assim. Adicione também `www.foton.app.br`.

## Passo 2 — Cloudflare: criar a zona (5 min)

Na mesma conta Cloudflare do R2: **Add a site** → `foton.app.br` → plano **Free**.

Ela vai varrer o DNS atual e provavelmente já trazer os três registros A. Deixe **exatamente** assim:

| Tipo | Nome | Valor | Proxy |
|---|---|---|---|
| A | `app` | `152.67.46.113` | **DNS only** (nuvem CINZA) |
| CNAME | `@` (raiz) | `getfoton.netlify.app` | **DNS only** (cinza) |
| CNAME | `www` | `getfoton.netlify.app` | **DNS only** (cinza) |

Apague os registros A antigos da raiz e do `www` (os que apontam para 152.67.46.113).

**Por que tudo cinza:**
- `app` **precisa** ser cinza: com o proxy laranja a Cloudflare fica na frente e o
  certbot da VM não consegue mais renovar (a validação não chega na máquina).
- raiz e `www` cinza para o Netlify emitir o certificado dele sem disputa. Depois de
  tudo funcionando, dá para ligar o laranja neles se quiser cache — **nunca no `app`**.

CNAME na raiz funciona na Cloudflare (ela achata o CNAME sozinha). Se por algum motivo ela
recusar, use `A @ 75.2.60.5` (o balanceador do Netlify).

No fim ela mostra **dois servidores de nome** (algo como `xxx.ns.cloudflare.com`). Copie os dois.

## Passo 3 — registro.br: apontar para a Cloudflare (2 min)

Entre no registro.br → domínio `foton.app.br` → **Alterar servidores DNS**.
Troque `d.sec.dns.br` / `e.sec.dns.br` pelos dois da Cloudflare. Salve.

Propaga em **minutos a algumas horas**. Nada quebra durante — é o ponto da ordem escolhida.

## Passo 4 — conferir (quando propagar)

```bash
bash infra/conferir-dns.sh
```

## Passo 5 — certificado (ANTES DE 28/10/2026, não precisa ser hoje)

Depois que a raiz e o `www` já estiverem no Netlify, encolher o certificado da VM para só
o que ela ainda serve:

```
ssh -o StrictHostKeyChecking=no -i ~/.ssh/foton.key ubuntu@152.67.46.113 \
  'sudo certbot --nginx --cert-name getfoton.duckdns.org \
     -d app.foton.app.br -d getfoton.duckdns.org \
     --non-interactive --agree-tos && sudo certbot renew --dry-run'
```

Se o certbot perguntar se pode **remover** domínios, responda que sim (é o objetivo).
Nesse caso rode sem `--non-interactive`. O `renew --dry-run` no fim é o que prova que a
renovação vai funcionar em novembro — **não pule**.

`infra/dominio.sh` só EXPANDE a lista de domínios. **Não usar aqui.**

## Depois disto

`fotos.foton.app.br` (fotos no R2) fica a um registro de distância, com a zona já na
Cloudflare — e o backup externo passa a usar a mesma conta.
