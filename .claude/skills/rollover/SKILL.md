---
name: rollover
description: Handoff entre janelas de contexto do Claude Code. Use quando aparecer um aviso "[ROLLOVER]" (zona ATENCAO ou ROLLOVER), quando o dono pedir "handoff", "rollover", "passar o bastão", "preparar a próxima sessão", ou no início de uma sessão que recebeu um HANDOFF pendente. Grava o estado operacional em .claude/HANDOFF.md e conduz a retomada.
---

# Rollover: escrever o handoff e retomar

O script `python ~/.claude/rollover/rollover.py` faz a parte mecânica (medir, carimbar,
validar, marcar estado). **O conteúdo do handoff é seu**: só você sabe o objetivo, as
decisões e o que não pode se perder. Pergunta que guia tudo:

> Se esta janela fechar agora e outra abrir em 10 segundos, o próximo Claude continua daqui
> sem depender da memória do dono?

> Sem o script (sessão na nuvem ou em outra máquina): edite `.claude/HANDOFF.md` à mão;
> `retomado` = trocar a linha `estado: pendente` por `estado: retomado`. O handoff vai no git.

## A. Escrever (zona ROLLOVER, ou quando o dono pedir)

1. **Pare de expandir.** Termine só o passo que está no meio, se for curto. Nada de leitura
   grande nem frente nova.
2. `python ~/.claude/rollover/rollover.py novo` cria `.claude/HANDOFF.md` com os fatos
   mecânicos (git, uso, últimos pedidos). Se já houver um pendente, **atualize-o**.
3. Preencha **todas** as seções com o que é verdade agora, curto e verificável:
   objetivo em curso · concluído (com prova: commit, teste, medida) · decisões (e onde estão
   registradas) · arquivos tocados · testes executados · erros e riscos · hipóteses abertas ·
   próximos passos em ordem · o que não pode se perder. Não é resumo da conversa: é o pacote
   mínimo para continuar. Não copie o que já está em arquivo do projeto; aponte o arquivo.
4. `python ~/.claude/rollover/rollover.py validar` até dar `ok`.
5. Diga ao dono, exatamente:
   > O contexto desta sessão está chegando à zona de rollover. Já preservei o estado.
   > Antes de abrir a próxima sessão, qual é o objetivo que você quer continuar daqui?
6. Com a resposta: `python ~/.claude/rollover/rollover.py objetivo "<o que ele disse>"`,
   e oriente: abrir uma sessão nova nesta pasta (ou `/clear`). O hook de início entrega o
   handoff à próxima sessão.

## B. Retomar (sessão que começou com "[ROLLOVER] Existe um HANDOFF pendente")

1. Parta do handoff; não peça o transcript antigo.
2. Confira o estado real: `git status --short`, `git log --oneline -5`, e abra os arquivos
   que o handoff manda revisitar. Se algo divergir, o que está no disco vence o handoff.
3. Se precisar, consulte a memória (auto-memória; claude-mem só como complemento).
4. Apresente ao dono um resumo de 3 a 5 linhas: onde paramos, o que está pendente.
5. Objetivo: se a seção "Próximo objetivo" estiver preenchida, confirme; se não, pergunte.
6. Confirmado, rode `python ~/.claude/rollover/rollover.py retomado` e siga o trabalho.

## Não fazer
- Não escrever handoff em zona NORMAL sem o dono pedir (sem ritual).
- Não registrar tudo: só o necessário para continuar pensando e trabalhando certo.
- Não apagar handoff antigo: `novo` arquiva em `.claude/handoff-auto/anteriores/`.
