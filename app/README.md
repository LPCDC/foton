# Fóton — o app

> Este arquivo descreve só o código desta pasta. O que é o produto, onde roda,
> como fazer deploy e o que falta: **`BLUEPRINT.md` na raiz do repo é a fonte
> de verdade** — leia-o primeiro em qualquer sessão nova.

## Estrutura real (2026-08-28)

```
app/test_rig/
  rig.py         FastAPI: TODAS as rotas — contas, eventos, pipeline, admin, LGPD, FTP.
  store.py       SQLite: contas, eventos, fotos, rostos, convidados, contatos, config.
  ftp_camera.py  servidor FTP (a câmera envia direto, sem passar pelo celular).
  models/buffalo_s/  modelo ONNX do InsightFace, versionado no repo (não baixa em runtime).
app/web/
  index.html     TODO o front — uma página só, sem framework. Painel do fotógrafo
                 + app do convidado. É o mesmo arquivo que o rig.py serve em produção
                 (StaticFiles) e que o Netlify serve como demo.
  sw.js          service worker (só cacheia estáticos — nunca API, ver BLUEPRINT §7).
  assets/        fotos de demonstração.
```

Não existe `app/api/`, `app/db/`, Supabase, nem Render em produção. Esse desenho
foi abandonado — ver ADR-0015/ADR-0016 em `docs/DECISIONS.md`. O que roda hoje é
**um único processo Python** (rig.py) numa VM própria, servindo API e front juntos.

## Rodar localmente

```bash
cd app/test_rig
pip install -r requirements.txt
uvicorn rig:app --reload --app-dir .
# abra http://localhost:8000
```

Sem internet/câmera real: qualquer JPEG serve para testar `/ingest` e `/selfie`.
Testes automatizados (não exigem o modelo facial carregado): `python ../../tests/test_autorizacao.py`
e `python ../../tests/test_ftp_camera.py`, a partir da raiz do repo.

## Como operar um evento de verdade

Ver `BLUEPRINT.md` §2 (onde está) e §3 (pipeline). Resumo: a fotógrafa cria conta,
cria evento, mostra o QR, fotografa (celular ou FTP direto — `docs/ROTEIRO-CAMERAS.md`).
Créditos são atribuídos manualmente pelo admin (`/admin/creditos`) — não existe
gateway de pagamento ainda (ADR-0012).

## Deploy

`git push` — a VM tem auto-update (ver `BLUEPRINT.md` §5). Não precisa dos passos
de Supabase/R2/Render que apareciam aqui antes; esse desenho não é o que roda.
