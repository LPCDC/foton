# HANDOFF | Menir ClickPal

estado: pendente
gerado: 2026-09-28T18:13:29-03:00

## Fatos mecânicos (gerados pelo script)

- quando: 2026-09-28T18:13:29-03:00
- pasta: C:\Users\Pichau\Menir ClickPal
- sessão: 3896f046-4ba5-4b85-bcfc-2ee7dc4310a9.jsonl
- contexto: 811469 tokens · zona ATENCAO (a auto-compactação desta sessão já disparou em 885591)
- git: main @ 8b32a63 (no ar: `/health` versao 8b32a63)
- não commitado (NÃO são deste trabalho, não mexer sem o dono): M CLAUDE.md · ?? .claude/launch.json · ?? foton-handoff-supercomputer-2026-09-10.md · ?? foton.zip
- últimos commits: 8b32a63 P1 fechado · 571450e P1 instrumentação (ADR-0046) · 5afcdb7 PRODUCT.md · cb986f7 site novo · 4be85bd sem travessão no app

## Objetivo em curso

Dois trilhos, nesta ordem de importância para a próxima sessão:
1. **Fóton, ciclo de prova de produto** (`PRODUCT.md`): o próximo marco é um **evento real**. P1 (instrumentação) está FECHADO. O próximo é o **P2, ensaio de mesa com câmera + Android reais**, que é do DONO executar; o Claude só prepara e depois analisa o JSON exportado.
2. **Sistema de rollover + handoff do Claude Code**: PRONTO e ligado (ver Concluído). Este arquivo é o primeiro handoff real dele; esta sessão entrou em ROLLOVER de verdade (831337 tokens, 94% do teto 885591).

## Concluído nesta sessão (com prova)

- Painel da fotógrafa repintado no design system (`6e66a08`), com 3 defeitos corrigidos; o dono ainda o acha ruim no desktop (redesenho PARADO por decisão).
- App sem travessão (`4be85bd`); site novo no DS com imagens Higgsfield e história medida (`cb986f7`); site sem afirmações falsas (`5afcdb7`).
- `PRODUCT.md` criado (autoridade de produto); `docs/PILOTO-1.md` com o experimento; `docs/CONCORRENCIA.md` corrigido.
- **P1 fechado** (`571450e`, `8b32a63`): instrumentação T0..T5 (ADR-0046), relógio `app/web/relogio.html`, export `/medidas`, relatório `tests/relatorio_evento.py` com critério #4 pela galeria. Ensaio local com câmera simulada: desvio recuperado +83,62 s de 83,6; T0 a 0,03 s do real (docs/BENCHMARKS.md).
- Rollover pronto: `~/.claude/rollover/{rollover.py,README.md,test_rollover.py}`, skill `~/.claude/skills/rollover/SKILL.md`, 4 hooks em `~/.claude/settings.json` (backup `settings.json.bak-antes-do-rollover`), memória `rollover-handoff`. Teto por modelo (menor auto-compactação: opus-4-7 531463, opus-4-8 241916, opus-5 885591). Testes: `test_rollover.py` todos verdes. Provas reais: (1) `claude -p` numa sessão NOVA reconstruiu o estado só por este handoff; (2) o PostToolUse injetou o aviso ROLLOVER ao vivo nesta sessão.

## Decisões tomadas

- Cliente inicial = fotógrafa; Fiesta em segundo plano; modo Empresa fora; A1 não migrar; filtros só o acabamento da fotógrafa, depois do evento; WhatsApp: testar sem construir primeiro (PRODUCT.md, "Decisões deste ciclo").
- Nada de app Android nativo nem pasta vigiada antes do P2.
- P1 = infraestrutura de medição validada em ensaio controlado; P2 = outro portão.
- Critério #4 do piloto: "P95 do disparo até a foto aparecer na GALERIA do convidado ≤ 30 s", só entregas observadas; não observado não é atraso.
- T1 é proxy da chegada ao celular até ser validado no Android real.
- Pronto é quando o dono aprova (STATUS.md, topo). Proibido travessão em qualquer texto gerado (regra global do dono).

## Arquivos tocados

Fóton: `PRODUCT.md`, `STATUS.md`, `docs/{PILOTO-1,DECISIONS,BENCHMARKS,CONCORRENCIA,PRODUTO,WHATSAPP,DIRECAO-VISUAL}.md`, `app/test_rig/{rig,store}.py`, `app/web/{index.html,sw.js,relogio.html,ds/*}`, `site/*`, `tests/{test_front,test_autorizacao,test_site,test_relatorio,relatorio_evento,site_reconhecimento}.py`, `tests/todos.sh`.
Rollover (fora do repo): `~/.claude/rollover/rollover.py`, `~/.claude/rollover/estado.json` (teto aprendido). Aqui: `.claude/HANDOFF.md`, `.claude/handoff-auto/` (se ignora no git).

## Testes e verificações executados

- `bash tests/todos.sh`: 8 suítes, 744 verificações verdes (último rodado antes de `8b32a63`).
- Produção: `/health` versao 8b32a63; `/agora` ok; `relogio.html` 200; `/medidas` sem login 401.
- Rollover: `rollover.py calibrar` achou 10 compactações reais; `status` mediu 811469 tokens nesta sessão.

## Erros, bloqueios e riscos

- **claude-mem parou de gravar em 2026-09-23 21:37** (274 observações, nenhuma depois). Não confiar nele para nada de 24 a 28/09. Causa não investigada.
- Rollover: teto é aprendizado, não garantia (compactações de 241916 a 1000018). O hook `menir-t0` (teste do dono, de 17/09) continua ligado; é removível, mas só se o dono quiser.
- O painel do navegador do app desktop fica escondido e não desenha quadros: rAF e imagens preguiçosas não rodam nele (irrelevante para usuário real; afeta testes).

## Hipóteses abertas

- O gargalo operacional do produto está na ponte câmera → celular → Compartilhar e no comportamento da fotógrafa (HIPÓTESE para o P2, não evidência do P1).
- O Android passa a data real do arquivo pelo Compartilhar (T1)? UNKNOWN até o P2.
- `UserPromptSubmit` e `PostToolUse` aceitam contexto injetado (stdout / additionalContext) nesta versão: o binário 2.1.284 tem os campos; falta prova de ponta a ponta.

## Próximos passos (em ordem)

1. Retomar pelo protocolo da skill `rollover` (git status, resumo curto, confirmar o objetivo com o dono, `rollover.py retomado`).
2. Opcional, se o dono quiser: investigar por que o claude-mem parou em 2026-09-23.
3. Fóton: esperar o P2 do dono; ao receber o JSON exportado e a foto do relógio, rodar `python tests/relatorio_evento.py <json> --relogio FOTO_ID=HH:MM:SS.d` e registrar em BENCHMARKS.

## Não pode se perder

- Deploy = `git push origin main` + conferir `/health` versao == `git rev-parse --short=7 HEAD`. `bash tests/todos.sh` antes de todo push.
- Nunca criar conta nem digitar senha em produção; testes com conta só em localhost (servidor local: `.claude/launch.json` "rig-local", banco descartável no scratchpad).
- `fotos-teste/` tem pessoas reais: só local, nunca web nem git.
- Textos com aspas e crases no bash heredoc quebram: escrever scripts com a ferramenta de arquivo.
- O dono escreve orientações longas coladas (às vezes redigidas com outra IA): tratar como decisão dele só quando ele confirma em palavras próprias.

## Próximo objetivo (definido pelo dono)

(preencher)
