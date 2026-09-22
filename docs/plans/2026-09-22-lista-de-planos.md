# Lista de planos de execução — Fóton, 2026-09-22

> Método: skill `roadmap-prioritization` (refoundai/lenny-skills). Três coisas dela valem
> aqui: **apetite fixo** em vez de estimativa ("quanto estou disposto a gastar antes de
> entregar algo"), **equilíbrio de portfólio** (melhoria incremental × aposta × base) e
> **separar verdade de hipótese**.
>
> Entradas: auditoria visual do app e da vitrine (2026-09-22), auditoria do site
> (2026-09-21), `docs/CONCORRENCIA.md`, `docs/WHATSAPP.md`, `docs/CAMERA-FILTROS.md`, o
> método do Ateliê em `docs/plans/2026-09-21-foton-que-cobra.md`.

## 0. O que é verdade e o que é hipótese

**Verdade (medida ou verificada):** o produto roda em produção; o limiar 0,40 e a auditoria
de entrega existem; o certificado vale até 21/12; a esteira da pintura funciona; o design
system tem contraste medido e travado; o app público **não** segue o design system; o site
não tem menu no celular, foco visível nem imagem de produto; o WhatsApp tem janela gratuita
de 24 h.

**Hipótese (ainda não medida):** que entregamos em menos de 10 s ponta a ponta; que a VM
aguenta uma festa de 300 pessoas; que seis ajustes de cor cobrem 99% do que a fotógrafa faz;
que o filtro não estraga o reconhecimento; que o preço X é aceito.

**A pergunta que a skill manda fazer e eu devolvo ao dono:** *qual é a proporção entre
melhoria incremental e aposta que você quer neste trimestre?* Minha proposta abaixo é
**70% incremental / 30% aposta**, porque o produto ainda não tem uma venda.

## 1. Temas (três, não dez)

| Tema | Pergunta que ele responde |
|---|---|
| **A · A fotógrafa fecha negócio** | ela vê, entende e quer pagar? |
| **B · A prova existe** | funciona numa festa de verdade, com números? |
| **C · O produto é um só** | a mesma gramática do começo ao fim, sem defeito de acessibilidade |

## 2. A lista, em ordem de execução

Pontuação: **alcance** (quantos afeta), **impacto**, **confiança** e **esforço** — tudo
estimativa declarada, não medição. **Apetite** é o teto: se não couber, o escopo diminui.

| # | Plano | Tema | Alc. | Imp. | Conf. | Esf. | Apetite | Porta de saída |
|---|---|---|---|---|---|---|---|---|
| 1 | **Defeitos de acessibilidade do app e do site** | C | alto | médio | **alta** | baixo | 1 sessão | zoom liberado, foco visível, ícones rotulados, menu no celular; testes |
| 2 | **Jornada do convidado no design system** | A | alto | **alto** | alta | médio | 2 sessões | QR → selfie → galeria ao vivo em 375 px, tema noite, acessibilidade |
| 3 | **Entrada do app por papel, alinhada ao DS** | A+C | alto | alto | alta | baixo | 1 sessão | três caminhos com resultado declarado; funciona sem a mídia de fundo carregar |
| 4 | **Verificação real em Android e iPhone** | C | alto | alto | **média** | baixo | 1 sessão | rodada em 3 aparelhos, com prints por tamanho; defeitos viram lista |
| 5 | **Experimento 4 dos filtros: a cor mexe no reconhecimento?** | B | — | **alto** | baixa | baixo | 1 sessão | número no BENCHMARKS; decide se filtro entra antes ou depois do reconhecimento |
| 6 | **Medição com a R8 e a Patrícia (TTFR)** | B | alto | **alto** | média | médio | 1 dia de campo | P95 do clique ao celular; só então o site pode citar tempo |
| 7 | **WhatsApp v1: aviso e link** | A | **alto** | alto | média | médio | 2 sessões | convidado liga, recebe aviso durante a festa, dentro da janela gratuita |
| 8 | **Filtros com nome, aplicados depois do clique** | A | médio | médio | média | médio | 2 sessões | 6 filtros, calibração automática por evento, sem visor ao vivo |
| 9 | **Matriz "design system → app" e anti-padrões** | C | médio | médio | alta | baixo | 1 sessão | cada componente com estado, toque e onde aparece no app |
| 10 | **Painel da fotógrafa + cartaz de QR para imprimir** | A | médio | alto | alta | médio | 2 sessões | ela cria um evento sozinha, cronometrado |
| 11 | **Teste de carga na VM real** | B | alto | alto | média | médio | 1 sessão | os três números do plano da Fiesta; define o teto de convidados |
| 12 | **Site de vendas redesenhado** | A | alto | alto | alta | alto | 3 sessões | mostra o produto de verdade; nenhum número sem lastro |
| 13 | **Cobrar: preço + ativação manual por PIX** | A | baixo | **alto** | baixa | médio | 2 sessões | primeira fotógrafa pagante |
| 14 | **Fiesta** (convidado fotografa) | — | alto | alto | média | **alto** | a decidir | trilho paralelo, depois do piloto |

**Por que esta ordem, e não a da auditoria.** As duas auditorias pedem, com razão, que o app
vire Bauhaus. Mas o item 1 vem antes de tudo porque **zoom bloqueado e falta de foco visível
não são estética, são exclusão**, e custam pouco. E o item 6 vem antes do 12 porque o site só
pode mostrar o produto **depois** que as telas novas existirem, e só pode citar tempo
**depois** da medição — caso contrário, repetimos a promessa não medida que já está no ar.

## 3. Triagem das auditorias (a regra do relay)

Cada auditoria viu uma versão diferente. Registro o que cada uma viu e o desfecho:

| Ponto | Viu | Desfecho |
|---|---|---|
| Site com fonte manuscrita, gradiente, tudo arredondado | site antigo | **procede** → plano 12 |
| Site sem menu no celular, sem foco, ícones sem rótulo | site antigo | **procede, urgente** → plano 1 |
| Site sem imagem do produto | site antigo | **procede, mas depende** do plano 2 |
| App não segue o design system | app atual | **procede** → planos 2 e 3 |
| App depende de texto claro sobre foto escura | app atual | **procede** → plano 3 |
| `user-scalable=no` no app | app atual | **procede, urgente** → plano 1 |
| Vitrine precisa virar contrato com o app | vitrine | **procede** → plano 9 |
| Vitrine com muita documentação lado a lado | vitrine | **parcial**: a densidade é proposital; entra "anti-padrões" no plano 9 |
| Trocar foto gerada por foto real de fluxo | vitrine | **não procede agora**: foto de convidado real exige autorização, e prova de piloto ainda não existe |
| Mobile não verificado | ambas | **procede** → plano 4 |

## 4. O que eu recomendo fechar com você antes de começar

1. **A proporção 70/30** entre melhoria e aposta.
2. **O apetite do plano 6** (a medição com a R8): sem uma data com a Patrícia, ele não anda, e
   metade da lista depende dele.
3. **Os três "UNKNOWN" que viram trabalho perdido se ficarem abertos:** tempo real de
   entrega, teto da VM e se o filtro mexe no reconhecimento.

---

## 5. Fechamento do dono (2026-09-22) — vale sobre a ordem do §2

**Aprovado:** portfólio 70/30. **Tema do trimestre: A** (a fotógrafa fecha negócio).
**Tema de proteção: C** (produto coerente e acessível). **Tema de prova: B** (evidência antes
de prometer). Quatro ajustes, todos incorporados:

### 5.1 O plano 1 vira dois, com aceites separados

Apetite total continua uma sessão, mas **app e site são produtos diferentes e não se
verificam juntos**:

- **1A · App:** zoom liberado, foco visível, ícones rotulados, contraste do texto sobre foto,
  teclado e toque.
- **1B · Site:** menu no celular, foco visível, ícones rotulados, navegação e chamada.

`user-scalable=no` **sai**, salvo razão operacional específica registrada em ADR. Impedir
zoom é exclusão, e não se usa para segurar layout.

### 5.2 O plano 4 é portão, não tarefa

A verificação em Android e iPhone roda **depois de 1–3**, **antes de dar 2 ou 3 por
encerrados**, e **de novo a cada mudança grande**. Frota mínima: Android Chrome e iPhone
Safari, tela pequena e grande, em pé, teclado aberto, conexão lenta, mídia carregando e mídia
indisponível. O critério de aceite não é estético:

> **O convidado consegue entrar, entender, consentir, enviar a selfie e chegar à galeria sem
> ajuda?**

### 5.3 O plano 6 é portão de decisão, não só medição

Depois do TTFR medido:

| Resultado | O que o site pode dizer |
|---|---|
| P95 bom | comunica velocidade, com o número medido |
| P95 aceitável | comunica "durante o evento", **sem número** |
| P95 ruim | corrige o caminho **antes** de vender a promessa |
| medição não aconteceu | **nenhum número de tempo** no site |

Mesma regra para o teste de carga (plano 11): **não vender capacidade de 300 convidados** até
existir evidência.

### 5.4 O site completo espera; a página de piloto não

O plano 12 encolhe para uma **página mínima de piloto**, depois dos planos 2 e 3: demonstração
real do fluxo, três telas do produto, chamada clara para fotógrafas, privacidade em duas
linhas, convite ao piloto e **nenhum número sem lastro**. O site completo só depois do
primeiro evento e da primeira conversa comercial.

### 5.5 Cobrar sobe: logo depois do primeiro piloto

Mesmo manual, por PIX, com ativação feita por nós. A pergunta que vale mais que um checkout
elegante: **uma fotógrafa aceita pagar por isso?**

### 5.6 A sequência que passa a valer

| Bloco | Ordem |
|---|---|
| **1 · Remover risco barato** | 1A app · 1B site · 3 entrada por papel · 2 jornada do convidado · **4 validação em celular real (portão)** |
| **2 · Provar o produto** | 5 filtro × reconhecimento · 6 TTFR (**portão de decisão**) · 11 carga · 7 WhatsApp v1 |
| **3 · Fazer a fotógrafa operar** | 10 painel + cartaz · 8 filtros pós-clique · 9 matriz DS → app |
| **4 · Converter** | 12-mínimo página de piloto · 13 primeira cobrança por PIX · 12-completo site |
| **Paralelo** | 14 Fiesta, só depois de o piloto provar operação |

### 5.7 O que falta para travar o cronograma

**A data com a Patrícia para o teste de campo.** Sem ela, o plano 6 não anda, e o cronograma
não pode fingir que anda. Enquanto não houver data, os blocos 1 e 2 seguem pelo que não
depende dela.
