# Prompt para a próxima sessão

> Cole isto numa sessão nova. Foi escrito para carregar contexto sem gastar
> tokens repetindo o que já está nos documentos, e para forçar o rigor do
> Gauntlet em vez de pedir educadamente por ele.

---

Fóton — continuação. Antes de qualquer coisa, leia nesta ordem: `BLUEPRINT.md`,
`docs/PILOTO-1.md` e `docs/TESTES.md`. Eles têm o produto, o estado real de
produção, o critério de go/no-go do próximo marco e o que já foi medido. Não
repita trabalho que já está lá, e não confie na sua memória de treino sobre este
projeto — confie nos documentos e no código.

**Objetivo desta sessão, e só ele:** fazer a foto sair da câmera da Patrícia
(Canon R8 e T6s — nenhuma tem FTP) e chegar no Fóton com o mínimo de gesto
humano possível. É uma promessa já feita à cliente. Todo o resto é distração
até isto fechar.

**Caminho que eu quero que você ataque primeiro**, salvo se encontrar evidência
contra: Web Share Target no PWA. A R8 já envia cada foto sozinha para o celular
(`Funções de comunicação → Enviar para smartphone após o disparo → Envio
automático`). Falta só o elo celular → Fóton. Se o Fóton aparecer no menu
"Compartilhar" do Android, ela seleciona o lote e manda num gesto.

**Critério de aceite (sem isto, não está pronto):**
1. Número medido de gestos humanos por 100 fotos, antes e depois. Sem o número,
   a tarefa não está concluída.
2. O caminho antigo (escolher arquivo pelo app) continua funcionando — teste-o
   depois de mexer.
3. Funciona com o app instalado como PWA e degrada sem quebrar quando não está.
4. As três suítes passando: `tests/test_autorizacao.py`, `tests/test_ftp_camera.py`,
   `tests/test_logo.py`.
5. Testado em produção (`https://app.foton.app.br`), com a saída colada na
   resposta — não "deve funcionar".

**Se o Web Share Target não resolver**, não invente uma gambiarra: meça, diga
que não resolveu, e apresente as duas alternativas reais (EOS Utility num
notebook, que funciona nas duas câmeras; ou app Android nativo) com custo de
desenvolvimento e o que cada uma exige no dia do evento. A decisão é minha.

**Regras de trabalho (valem sempre):**
- Nada é "pronto" sem rodar e ler a saída. Cole o número.
- Não quebre o que funciona: teste o caminho inteiro depois de mexer.
- Suposição não medida se escreve `UNKNOWN — REQUIRES EXPERIMENT`. Já erramos
  feio assumindo capacidade de câmera sem teste — não repita.
- Mudou arquitetura ou dependência → ADR em `docs/DECISIONS.md`.
- Se eu estiver viajando na maionese, me diga, com o motivo.
- Deploy é `git push` (VM se atualiza em ~2 min). Infra exige Cloud Shell.
- Não faça deploy se houver evento ao vivo (`/admin/saude` mostra).

**Não faça nesta sessão, mesmo que pareça tentador:** sliders de edição,
freemium, R2, redesenho de tela. Se sobrar tempo, o próximo item da fila é
**teste de carga real** (30 selfies simultâneas + rajada de 50 fotos, com P95),
porque o piloto ainda não provou que aguenta um evento de verdade.

---

## Por que este prompt é assim

- **Manda ler os documentos em vez de repetir contexto** — o BLUEPRINT já é o
  contrato; repetir contexto no prompt gera divergência entre os dois.
- **Um objetivo só.** Sessões anteriores tiveram 6 pedidos numa mensagem e o
  resultado foi dispersão: muita coisa boa entregue, e o gargalo intacto.
- **O critério de aceite é numérico** ("gestos por 100 fotos"), não adjetivo
  ("ficar bom"). É o que separa Gauntlet de conversa.
- **Diz explicitamente o que NÃO fazer.** Sem isso, o agente resolve o pedido
  fácil e adia o difícil.
- **Autoriza a falha.** "Se não resolver, diga que não resolveu" evita a pior
  falha de um agente: inventar que funcionou.
