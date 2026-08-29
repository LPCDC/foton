# Estratégia de teste — Fóton

> O que testar, de que jeito, e o que ainda está descoberto.
> Regra da casa: nada é "pronto" sem rodar e ler a saída.

## Pirâmide aplicada ao Fóton

```
        /  ENSAIO REAL  \      1 por marco — câmera + celular + 2 pessoas
       /   FUMAÇA (prod)  \    1 comando, roda a cada deploy
      /  CONTRATO (HTTP)    \  rápido, dubla só o motor facial
     /    UNIDADE (pipeline)  \ imagem entra -> vetor sai
```

O motor facial (SCRFD+ArcFace) **não** é redublado nos testes de unidade do pipeline:
ali ele é o que está sendo testado. Nas camadas acima ele é dublado, porque pesa
300 MB e não muda nenhuma regra de negócio.

## Camadas

### 1. Contrato HTTP — `tests/test_autorizacao.py` e `tests/test_ftp_camera.py` ✅ existem
`test_autorizacao.py` sobe o FastAPI real + SQLite real em arquivo temporário; dubla
`cv2` e `insightface`. Cobre: portão anônimo, portão de outra conta, caminho feliz da
fotógrafa, caminho do convidado, evento nasce com dono, encerrar/apagar, faixa do
evento ("está chegando?"), freio de login, torre de controle do admin, encerrar conta.
**91 checagens, 91 passando.**

A seção [12] cobre a **troca de login e senha pela própria fotógrafa**: senha atual
obrigatória · login inválido/curto/já usado · **não dá para virar admin renomeando a conta**
· credenciais velhas param de funcionar · sessões antigas caem · e o que mais quebraria:
**os eventos e a marca d'água PNG seguem junto com o login novo**.

A seção [11] do `test_autorizacao.py` cobre o **Web Share Target**: o manifest declara
`share_target` com o campo `fotos` dentro do scope · o service worker atende o POST e
responde 303 · o `activate` **não** apaga o cache do lote (apagaria fotos em trânsito) ·
o caminho antigo continua no HTML · e, sem service worker, `POST /compartilhar` devolve
página explicando em vez de 405 **sem virar upload anônimo** (nenhuma foto entra).

`test_ftp_camera.py` testa o servidor FTP isoladamente (sem subir o FastAPI): fila de
pendentes, descarte por idade, login conferido no banco na hora, semente não-derivável,
indicador "câmera conectada" sem precisar de foto de teste. **23 checagens, 23 passando.**
Roda em poucos segundos, sem rede.

```bash
python tests/test_autorizacao.py
python tests/test_ftp_camera.py
```

### 1b. Trava do front — `tests/test_front.py` ✅ 13 checagens
Os testes de contrato provam que o **servidor** está certo. Nenhum deles vê o app
morto: o servidor responde 200 com a tela em branco. Este olha o `index.html` como
texto e recusa o que não pode subir — string JavaScript cortada no meio, `onclick`
apontando para função que não existe, função definida duas vezes, `getElementById`
de id inexistente, arquivo que encolheu, `share_target` quebrado, senha escrita no repo.

Nasceu de erros reais numa única sessão: um `
` que virou quebra de linha e apagou o
app; uma edição que comeu o meio de uma função; uma escrita que zerou um documento;
`ehIOS` definida duas vezes. **Rodar sempre antes do `git push`.**

### 1c. Ensaio com fotos reais — `tests/ensaio.py`
O único teste que responde "vou passar vergonha?". Fotos em `fotos-teste/` (pasta
**ignorada pelo git** — o repo é público). Cria evento de teste em produção, manda as
fotos, registra as selfies como convidados, mede P50/P95, perdas, rostos lidos e
quantos convidados receberam foto — e apaga o evento no fim.
⚠ Ele **não** prova que a foto foi para a pessoa certa. Isso só o seu olho prova; o
script imprime os links para você conferir.

### 2. Fumaça em produção — a fazer (`tests/fumaca.sh`)
Depois de cada `git push`, contra `getfoton.duckdns.org`: cria evento de teste, sobe
foto, faz selfie, confere match, confere que anônimo leva 401, apaga o evento.
Hoje isso está feito à mão; virar script é o próximo passo.

### 3. Unidade do pipeline — a fazer (`tests/test_pipeline.py`)
Com o motor **real**, em imagens fixas versionadas:
- rosto de frente é detectado; foto de costas dá 0 (não é bug — é o esperado)
- foto deitada com EXIF continua sendo reconhecida (regressão do `exif_transpose`)
- `det_size=640` acha rosto de 90 px; a 320 não acha (regressão registrada)
- mesma pessoa em 2 fotos: cosseno ≥ 0,25; pessoas diferentes: < 0,25

### 4. Ensaio real — obrigatório antes do primeiro evento pago
Canon R8 (FTP nativo) e T6s (Camera Connect → celular → app), 2 pessoas, 20 fotos
em rajada. Mede: tempo do clique até a foto no celular (P95), quantas fotos se
perderam, o que a fotógrafa precisou digitar.

## Cobertura por área

| Área | Tipo | Estado | Alvo |
|---|---|---|---|
| Autorização das rotas | contrato | ✅ 46/46 | toda rota destrutiva com teste de 401 e 403 |
| FTP da câmera (pendentes, login, semente) | contrato | ✅ 23/23 | ver `tests/test_ftp_camera.py` |
| Detecção + embedding | unidade | ❌ falta | 4 casos de regressão abaixo |
| Upload em lote / retry | contrato | ❌ falta | rede cai no meio: nenhuma foto perdida |
| LGPD (exclusão, expiração automática) | contrato | ⚠️ parcial | exclusão manual coberta; expiração por tempo (`store.expirar`) sem teste |
| Disco / rajada | carga | ✅ medido em produção | ver BENCHMARKS.md 2026-08-28: 1 foto e rajada de 4, com e sem redução no celular |
| Zerar dados sem levar as contas | contrato | ✅ seção [18] | senha, créditos, marca d'água e retenção sobrevivem |
| Leitura nao cria evento | contrato | ✅ seção [19] | inclui a cadeia /feed → órfão → adoção |
| Cadastro nao vira admin | contrato | ✅ seção [16] | inclui admin que ainda não tem conta |
| Retenção de biometria por conta | contrato | ✅ seção [17] | isenta sobrevive, normal expira |
| Compartilhar (Web Share Target) | contrato + navegador | ✅ 17 checagens + ponta a ponta em produção | ver `docs/BENCHMARKS.md` 2026-08-29 |
| Trocar login/senha (autosserviço) | contrato | ✅ 28 checagens | inclui escalada de privilégio e eventos seguindo o dono |
| QR por foto (convidado) | navegador | ✅ testado local e em produção | link, foto expirada, foto de demo, navegação |
| Fóton no menu Compartilhar de um Android real | ensaio real | ❌ nunca feito | exige o PWA instalado no celular dela |
| Câmera Canon física | ensaio real | ❌ nunca feito | `docs/ROTEIRO-CAMERAS.md` — bloqueador do piloto |
| Front (galeria, lightbox, seleção múltipla) | manual | manual | fica manual por ora — 1 página, sem framework |

**Não testar:** qrcode, PIL, FastAPI (código de terceiros), scripts de infra de uso único.

## Furos corrigidos (2026-08-28) — não repetir

1. ~~FTP sem evento ao vivo engolia a foto~~ — corrigido: fila de pendentes, drena ao
   abrir o evento. `tests/test_ftp_camera.py`.
2. ~~Usuário de FTP só nascia no boot~~ — corrigido: login conferido no banco na hora.
3. ~~Senha do FTP derivável do repo público~~ — corrigido: semente gerada e guardada
   no banco (`store.segredo`).
4. ~~Rotas destrutivas sem dono~~ (`/event/delete`, `/event/close`, `/photo/delete`,
   `/ingest`, `/contatos`) — corrigido: `_pode()` exige sessão + ser dono do evento.
5. ~~Sem rate limit no `/login`~~ — corrigido: 10 falhas/10min por IP → 429.
6. ~~Não existia rota para apagar conta~~ — corrigido: `/conta/excluir` e
   `/admin/conta/excluir`.

## Furos conhecidos que ainda não têm teste nem correção

1. **Disco** — fotos são BLOB no SQLite e o backup guarda 7 cópias do banco inteiro.
   Medido em 2026-08-28: 40,5 GB livres, folgado hoje — mas ainda falta um teste que
   **alerte** antes de encher (`/admin/saude` já expõe o número; falta o teste).
2. **Sessão de login nunca expira** (tabela `session` sem TTL).
3. **`GET /stats` e `GET /photos` ainda criam evento sozinhos** quando o código não
   existe — é a fábrica de "eventos órfãos" (2 encontrados e apagados em 2026-08-28).
   Conserto simples (404 em vez de criar), adiado por mexer no caminho do convidado.
4. **Câmera Canon física nunca testada** — todo o caminho FTP foi validado com cliente
   de script; falta o ensaio real (`docs/ROTEIRO-CAMERAS.md`).

## Medições reais (2026-08-28, produção)

| O quê | Número |
|---|---|
| `/health` | 200 em 0,27 s |
| Rajada de 5 fotos de demonstração (~80 KB, 720×900) | **3,6 s no total** (170–887 ms cada) |
| Foto de câmera (24 MP, 13 MB), isolada | 2,9 s |
| Rajada de 4 fotos de câmera | 19 s (~4,8 s cada) |
| Janela de 502 durante o auto-update | ~25 s por deploy |

⚠️ As fotos de demonstração são pequenas: **não** servem para medir SLA. O número que
vale é o da foto de câmera.
