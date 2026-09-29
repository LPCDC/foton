# HANDOFF | Menir ClickPal

estado: retomado (2026-09-29T06:25:15-03:00)
gerado: 2026-09-28T19:28:29-03:00

## Fatos mecânicos (gerados pelo script)

- quando: 2026-09-28T19:28:29-03:00
- pasta: C:\Users\Pichau\Menir ClickPal
- sessão: ffb86c15-b935-4331-8d82-77ee9508330e.jsonl
- contexto: 208662 tokens · modelo claude-opus-5-5 · zona ROLLOVER (86% do teto 241916: menor auto-compactação vista acima do uso atual)
- handoff: retomado
- git: main @ 77fdb3c
- não commitado:
    M CLAUDE.md
    ?? .claude/launch.json
    ?? foton-handoff-supercomputer-2026-09-10.md
    ?? foton.zip
- últimos commits:
    77fdb3c docs(p2): folha de campo, ensaio simulado e conferencia em producao
    01f7943 chore(handoff): retomado; objetivo P2 (folha de campo, ensaio simulado, conferencia em producao)
    9cd7d05 chore(handoff): skill manda commitar o handoff
    1ebbfdf chore(handoff): handoff e skill rollover no repo (sessao em worktree/nuvem nao via o disco local)
    8b32a63 docs(piloto): P1 fechado como infraestrutura de medicao; criterio #4 pela galeria
- últimos pedidos do dono:
    > Base directory for this skill: C:\Users\Pichau\.claude\skills\rollover  # Rollover: escrever o handoff e retomar
 
 O script `python ~/.claude/rollover/rollover.py` faz a parte mecânica (medir, carimbar,
 validar, marcar estado). **O conteúdo do handoff é seu**: só você sabe o objetivo, as
 decisões e o que não pode se perder. Pergunta que guia tudo:
 
 > Se esta janela fechar agora e outra abrir 
    > TO meio perdido :D

## Objetivo em curso

Fóton, P2 (ensaio de mesa com câmera e Android reais, `docs/PILOTO-1.md`). A preparação do Claude está PRONTA (`77fdb3c`). Agora é a vez do dono: a conferência da véspera e o ensaio. O dono disse "tô meio perdido" no fim desta sessão: a próxima sessão começa explicando o P2 em linguagem simples (o que é, por que, o que ele faz em ordem), sem jargão (T0..T5, lotes, seq).

## Concluído nesta sessão (com prova)

- Handoff anterior retomado (`01f7943`).
- `77fdb3c`: folha de campo `docs/P2-FOLHA-DE-CAMPO.html` (1 página A4, conferida por impressão em PDF no Edge sem janela); `tests/ensaio_simulado_p2.py` (exports no formato do P2 com verdade conhecida, 5 variantes); `tests/relatorio_evento.py` corrigido (T1 suspeito por lote: hora do Compartilhar, EXIF copiado, data do app; perdas com `--disparos` e UNKNOWN sem nome IMG_xxxx; seção de lotes; `--relogio` pelo número do arquivo; `--galeria` confere o T1); `test_relatorio` [5]; BENCHMARKS (seção "Ensaio simulado do P2"); PILOTO-1 ("Preparação do P2" e "Antes do P2: o que o dono confere em produção", 13 itens); STATUS (subitens do P2).
- Produção conferida sem conta: `/health` ok versão 9cd7d05, `/agora`, `relogio.html` 200, manifest com share_target `fotos`, `/medidas` 401.

## Decisões tomadas

- Nenhuma decisão nova de produto. Não houve deploy: app sem mudança desde `8b32a63`; commits só de docs e tests. NÃO foi feito push de `01f7943` e `77fdb3c` (produção roda 9cd7d05, idêntica em app).

## Arquivos tocados

`docs/P2-FOLHA-DE-CAMPO.html` (novo), `tests/ensaio_simulado_p2.py` (novo), `tests/relatorio_evento.py`, `tests/test_relatorio.py`, `docs/PILOTO-1.md`, `docs/BENCHMARKS.md`, `STATUS.md`, `.claude/HANDOFF.md`.

## Testes e verificações executados

- `bash tests/todos.sh`: 8 suítes, 743 verificações verdes (test_relatorio 55).
- `python tests/ensaio_simulado_p2.py`: as 5 variantes sem erro silencioso.

## Erros, bloqueios e riscos

- O dono está perdido: explicar antes de pedir qualquer ação.
- claude-mem sem gravar desde 2026-09-23 (não investigado).
- Aviso de rollover usa teto aprendido de outro modelo (241916); nesta sessão (opus-5-5) disparou em ~208k.

## Hipóteses abertas

- UNKNOWN até a prova do item 4 da lista (evento-demonstração): o Compartilhar do Android passa o nome IMG_xxxx e a data real do arquivo?
- DEDUÇÃO: com envio em lotes, disparo até a galeria > intervalo entre lotes; lotes de 2 min derrubam o critério #4 (30 s). O P2 mede o intervalo real.

## Próximos passos (em ordem)

0. P2 ADIADO pelo dono em 2026-09-28: não cobrar; a explicação simples já foi dada (3 passos). Só retomar se ele pedir.
1. (quando ele retomar o P2) Explicar o P2 ao dono em linguagem simples, em 3 passos: (a) na véspera, 15 min de conferência + mandar 3 fotos pelo Compartilhar para um evento-demonstração e exportar o JSON; (b) o ensaio com a folha impressa; (c) mandar JSON + foto do relógio + foto da folha.
2. Perguntar se ele quer push de `01f7943` e `77fdb3c`.
3. Ao receber o JSON do evento-demonstração: conferir seq, t1_arquivo e via; rodar o relatório.
4. Ao receber o JSON do P2: `python tests/relatorio_evento.py <json> --relogio IMG_xxxx=HH:MM:SS.d --disparos A-B --galeria IMG_xxxx=HH:MM:SS.d` e registrar em BENCHMARKS.

## Não pode se perder

- Deploy = `git push origin main` + `/health` versao == `git rev-parse --short=7 HEAD`; `bash tests/todos.sh` antes.
- Nunca criar conta nem digitar senha em produção. `fotos-teste/` só local.
- Scripts com aspas: escrever com a ferramenta de arquivo, não heredoc no bash.
- No Windows, rodar scripts com saída acentuada exige `sys.stdout.reconfigure(encoding="utf-8")` (já posto no relatório e no simulador).
- Não mexer em CLAUDE.md, .claude/launch.json, foton-handoff-supercomputer-2026-09-10.md, foton.zip sem o dono.

## Próximo objetivo (definido pelo dono)

P2 ADIADO pelo dono (sem data, registrado no STATUS). Próximo objetivo: investigar por que o claude-mem parou de gravar em 2026-09-23 21:37 (274 observações, nenhuma depois). Não mexe no Fóton.
