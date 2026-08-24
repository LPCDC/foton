# Foto na Hora — Plataforma (MVP)

O que a gente vende, em uma frase: **um serviço web** (como assinar um software, mas em
**pagamento único** — ADR-0012). A fotógrafa faz **login e senha**, cria o evento, mostra o QR
e fotografa. O convidado escaneia, tira 1 selfie e recebe as fotos dele **na hora**. Sem
instalar nada, sem hardware no evento.

> **Não vendemos** um programa instalado no PC/câmera dela, nem um equipamento. Vendemos
> **acesso ao pipeline na nuvem**. O equipamento dela vira irrelevante (ADR-0006).

---

## Estrutura

```
app/
  web/index.html   ← front-end (Netlify). Painel do fotógrafo + app do convidado. RODA HOJE em modo demo.
  db/schema.sql    ← banco (Supabase / PostgreSQL)
  api/             ← worker do pipeline (FastAPI): watermark + facial + match
    main.py        ← endpoints /ingest e /guest/selfie
    pipeline.py    ← reusa EXP-04 (watermark) + EXP-05 (YuNet/SFace) + EXP-06 (match)
    requirements.txt
```

## Ver a demo AGORA (sem montar nada)

`app/web/index.html` é autocontido. Abra no navegador:

```bash
# opção simples (a câmera/selfie exige localhost ou https):
cd app/web && python -m http.server 8080
# abra http://localhost:8080  → celular na mesma rede: http://SEU_IP:8080
```

Fluxo da demo: **Sou o fotógrafo** → login (já preenchido) → **Criar evento** → **Simular
disparo** (feed enche) → **Ver como o convidado vê** → selfie → galeria enchendo ao vivo.
Nenhuma foto real sai do aparelho. É a peça pra mostrar pra Patrícia.

---

## Arquitetura de produção (ADR-0010/0011) — 4 serviços, todos com free tier

| Serviço | Papel | Free tier (2026) |
|---|---|---|
| **Netlify** | hospeda `app/web` (front estático) | 100GB banda/mês |
| **Supabase** | Auth (login/senha), PostgreSQL, Realtime (feed ao vivo) | 500MB DB · 50k usuários · 200 conexões |
| **Cloudflare R2** | fotos + CDN (**egress zero** = custo por evento ~R$0) | 10GB storage · egress $0 |
| **Render** (ou Railway) | worker FastAPI (`app/api`) — pipeline pesado | web free 750h/mês |

O front NÃO fala com o worker direto o tempo todo: a câmera manda a foto pro worker
(`/ingest`), o worker trata+reconhece, grava no R2+Supabase, e o **Supabase Realtime** empurra
pro celular do convidado. Cada peça é trocável (contratos explícitos, §4 CLAUDE.md).

---

## Como operar um evento (runbook)

1. **Conta da fotógrafa** — criada no Supabase Auth (login/senha). O operador atribui os
   créditos comprados: `update photographer set credits=20, credits_total=20 where id=...`
   (no MVP o crédito é manual; gateway de pagamento fica pós-validação — ADR-0012).
2. **Antes do evento** — se o worker do Render estiver "dormindo" (free tier dorme após 15min),
   acordar com um ping (`GET /health`) uns minutos antes. Com clientes pagando, subir o worker
   pro plano always-on (~US$7/mês — o único custo fixo relevante).
3. **No evento** — fotógrafa: login → Criar evento → mostra o QR. Câmera configurada 1x para
   enviar por FTP/Wi-Fi ao endpoint `/ingest` (mapeado no S1, quando as câmeras chegarem).
4. **Convidado** — escaneia o QR (`?evento=CODE`) → consente → selfie → feed pessoal ao vivo.
5. **Fim** — encerrar o evento. Selfies/embeddings dos convidados são descartados (ADR-0005).

---

## Deploy (quando for pra valer)

```
1. Supabase: criar projeto → rodar app/db/schema.sql no SQL editor →
   Database > Replication: habilitar realtime em `photo` e `match`.
2. Cloudflare R2: criar bucket `fotonahora` → domínio público de CDN.
3. Render: novo Web Service apontando app/api (uvicorn main:app) → env:
   R2_PUBLIC_BASE, R2_KEY/SECRET, SUPABASE_URL, SUPABASE_SERVICE_KEY.
   Copiar os modelos ONNX de experiments/exp05_facial/models/ para app/api/models/.
4. Netlify: publicar app/web → em produção, criar app/web/config.js com as chaves
   PÚBLICAS do Supabase (anon key) e trocar DEMO=false.
```

> **Segredos nunca no código nem no git** (§7 CLAUDE.md). Chaves de serviço só como env no
> Render/Netlify. Os modelos ONNX e qualquer credencial já estão no `.gitignore`.

## Custo (economics — ver docs/BENCHMARKS.md §6)

Marginal por evento **~R$0,05–0,30** (egress zero no R2 + facial self-hosted em CPU). Único
custo relevante é o **fixo** de hospedagem (~US$7/mês do worker quando houver clientes). É isso
que faz o **pagamento único** fechar: um pacote de 20 eventos custa <R$6 de infra marginal.

## Pendências do S0 (não bloqueiam esta camada)

Upload câmera→nuvem e P95<10s reais (EXP-01/02/03/08) seguem aguardando as câmeras R8/T6s +
hotspot. O `/ingest` já é o ponto onde a câmera vai plugar. Ver `docs/ROADMAP.md`.
