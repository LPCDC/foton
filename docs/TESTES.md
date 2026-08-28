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

### 1. Contrato HTTP — `tests/test_autorizacao.py` ✅ existe
Sobe o FastAPI real + SQLite real em arquivo temporário; dubla `cv2` e `insightface`.
Cobre: portão anônimo (5 rotas), portão de outra conta (4 rotas), caminho feliz da
fotógrafa, caminho do convidado, evento nasce com dono, encerrar/apagar.
**21 checagens, 21 passando.** Roda em ~3 s, sem rede.

```bash
python tests/test_autorizacao.py
```

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
| Autorização das rotas | contrato | ✅ 21/21 | toda rota destrutiva com teste de 401 e 403 |
| Detecção + embedding | unidade | ❌ falta | 4 casos de regressão acima |
| Upload em lote / retry | contrato | ❌ falta | rede cai no meio: nenhuma foto perdida |
| FTP da câmera | integração | ❌ falta | foto antes do evento abrir NÃO some |
| LGPD (exclusão, expiração) | contrato | ❌ falta | excluir convidado apaga vetor, match e contato |
| Disco / rajada | carga | ⚠️ parcial | ver BENCHMARKS.md; falta com foto de 13 MB |
| Front (galeria, lightbox) | manual | manual | fica manual por ora — 1 página, sem framework |

**Não testar:** qrcode, PIL, FastAPI (código de terceiros), scripts de infra de uso único.

## Furos conhecidos que ainda não têm teste

1. **FTP sem evento ao vivo engole a foto** — `ftp_camera.py:45`. Sem teste e sem
   correção. É perda silenciosa de foto.
2. **Usuário de FTP só nasce no boot** — `ftp_camera.py:76`. Conta nova não loga na
   câmera até reiniciar o serviço.
3. **Senha do FTP derivável** — `FOTON_FTP_SEED` não é definida em produção.
4. **Disco** — fotos são BLOB no SQLite e o backup guarda 7 cópias do banco inteiro.
   Falta um teste que alerte antes de encher.
5. **Sem rate limit no `/login`**; sessão sem expiração.

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
