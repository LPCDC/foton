# CONCORRENCIA.md — o que o mundo faz, o que fazemos, o que adiamos e o que nunca faremos

> Pesquisa de 2026-09-22. Fontes no fim. **Regra desta casa:** o que é afirmação de
> concorrente (site, release) está marcado como **alegado**; só é **medido** o que nós
> medimos. Nenhum número de concorrente foi conferido por nós.

## 1. Quem são, em três grupos

| Grupo | Quem | O que vendem |
|---|---|---|
| **Entrega com reconhecimento facial** (nosso território) | **FotoOwl** (o mais próximo), Pic-Time, Lenzeit; no Brasil, TIME&SPACE e Fotop | a foto encontra a pessoa: busca por rosto, entrega no celular |
| **Galeria do fotógrafo** | Pixieset, ShootProof, Pic-Time | galeria bonita, loja de impressão, CRM, site |
| **Convidado que fotografa** (nosso Fiesta) | Kululu, GuestPix, POV, Joy | QR na mesa, convidado envia, telão ao vivo |

**O fato que mais importa nesta pesquisa:** o FotoOwl já junta **reconhecimento facial +
câmera direto para a nuvem + entrega por WhatsApp**, e uma matéria de 2026 o coloca em
primeiro numa lista de galerias com busca por rosto (alegado). É o nosso espelho.

**O dado que mais ajuda a nossa tese:** plataformas que rodam **só no navegador** alcançam,
segundo o levantamento citado, 65–85% de participação dos convidados, contra 30–45% quando
exigem instalar aplicativo (alegado, não medido por nós). O Fóton não pede instalação.

## 2. O que eles têm e nós não

| Função | Quem tem | Vale para nós? |
|---|---|---|
| **Entrega por WhatsApp** | FotoOwl | **Sim, é a maior lacuna.** Pesquisa e caminho já estão em `docs/WHATSAPP.md` |
| **Câmera direto para a nuvem** (upload sem o computador) | FotoOwl ("Beam") | Sim. É o piloto com a R8 |
| **Telão ao vivo** | Kululu, GuestPix | Já decidido: **v2** |
| **Loja de impressão e álbuns** | Pic-Time, Pixieset, ShootProof | Não agora. Receita por venda de foto impressa é outro negócio |
| **Site, CRM e contratos do fotógrafo** | Pixieset, ShootProof | Não. Vira software de gestão, não "a foto na hora" |
| **Seleção automática das melhores fotos e edição por IA** | Aftershoot, Pic-Time | Interessante e caro. Depois do piloto |
| **Busca por palavra além de rosto** ("praia", "bolo") | Pic-Time | Não agora |
| **Vídeo e retrospectiva automática** | FotoOwl (alegado), Kululu | Não agora |

## 3. O que temos e eles não (ou fazem pior)

1. **Entrega durante a festa como promessa central**, não como recurso extra. É a única coisa
   que nos define (CLAUDE.md §3).
2. **"Não sou eu"**: o convidado corrige o reconhecimento e a correção é permanente
   (ADR-0037). Não encontrei equivalente em nenhum concorrente pesquisado.
3. **Auditoria de entrega**: para cada foto entregue sabemos a nota, o limiar e o modelo
   (ADR-0035). Isso permite calibrar com evidência em vez de opinião.
4. **Apagar de verdade**: retenção curta, exclusão por conta e limpeza de dado órfão, com
   teste que prova (ADR-0037). Concorrente nenhum vende isso; no Brasil, com a LGPD, é
   argumento de venda.
5. **Português de gente e sem instalar nada**, com o produto feito para uma fotógrafa que
   às vezes trabalha com celular emprestado.
6. **Um sistema visual próprio** (ADR-0038), com contraste medido e travado por teste.

## 4. O que escolhemos **ainda** não ter (e quando revisamos)

| Adiado | Por quê | Revisar quando |
|---|---|---|
| Telão ao vivo | decisão do dono, v2 | depois do piloto |
| Convidado fotografando (Fiesta) | trilho paralelo; a fotógrafa vem primeiro | quando a fotógrafa tiver piloto |
| Moderação de conteúdo | só faz sentido com convidado enviando | junto com a Fiesta (decisão C, aprovada) |
| Registro de criança | sem parecer jurídico (ADR-0036) | com parecer |
| WhatsApp | conta Meta e número dedicado dependem do dono | assim que ele quiser |
| Pagamento automático | PIX manual resolve o piloto | quando houver fila de clientes |
| Edição e seleção por IA | custo e escopo | depois de vender |

## 5. O que **nunca** teremos

1. **Reconhecer alguém sem consentimento.** Sem selfie voluntária, não há busca por rosto.
2. **Vender, treinar modelo com, ou compartilhar rosto e foto de convidado.** Biometria é
   efêmera e morre com o evento.
3. **Foto guardada para sempre "de graça".** Retenção curta é parte do produto, não falta de
   recurso.
4. **Aplicativo obrigatório para o convidado.** É o que derruba a participação.
5. **Link público permanente do álbum.** Sessão com escopo e validade (CLAUDE.md §7).
6. **Ranking de beleza, estimativa de idade, gênero ou emoção.** Não é o negócio e é risco
   jurídico e ético.
7. **Marca d'água que estraga a foto para forçar compra.** A marca existe para creditar a
   fotógrafa, não para extorquir o convidado.

## 6. O que esta pesquisa muda na ordem do trabalho

1. **WhatsApp sobe de prioridade.** O concorrente global líder já entrega por lá, e no Brasil
   é o canal natural. O caminho grátis (janela de 24 h) cabe numa festa.
2. **"Sem instalar nada" vira argumento de venda explícito**, com o número de participação
   citado como referência de mercado, nunca como medição nossa.
3. **Nada aqui justifica loja de impressão, CRM ou site do fotógrafo.** Seria virar Pixieset
   com dez anos de atraso.

## Fontes (consultadas em 2026-09-22)

- FotoOwl: [galeria com IA](https://fotoowl.ai/ai-gallery) · [face search + WhatsApp](https://www.openpr.com/news/4626823/fotoowl-pairs-face-search-with-whatsapp-delivery-for-event) · [ranking 2026 (alegado)](https://www.openpr.com/news/4616251/fotoowl-ranks-first-for-face-search-client-galleries-in-2026)
- Pic-Time × Pixieset: [comparativo picflow](https://picflow.com/compare/pic-time-vs-pixieset) · [Pic-Time 2.0](https://blog.pic-time.com/features/pic-time-2-0-client-gallery-experience/)
- Convidado que fotografa: [POV](https://pov.camera/blog/the-10-best-wedding-photo-apps) · [Kululu](https://www.kululu.com/wedding-photo-sharing-app) · [GuestPix](https://guestpix.com/weddings/)
- Participação navegador × aplicativo: [comparativo 2026](https://easyweddingalbum.com/blog/wedding-photo-sharing-comparison)
