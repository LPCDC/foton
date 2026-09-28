# PRODUCT.md | o que o Fóton é, para quem, e o que ainda não sabemos

> Autoridade de produto desde 2026-09-28, ao lado das ADRs (`docs/DECISIONS.md`), do
> design system (ADR-0038) e da esteira de pintura (`docs/PINTURA.md`). Não substitui
> nenhum deles. Curto de propósito. Ideias que ainda não viraram decisão moram em
> `docs/PRODUTO.md`; o experimento do evento real, em `docs/PILOTO-1.md`.
>
> Marcação: **FATO** (medido ou observado) · **DEDUÇÃO** · **HIPÓTESE** · **UNKNOWN**.
> Quando o código ou a produção contradizem este arquivo, eles vencem e ele é corrigido.

## Para quem
A fotógrafa brasileira de evento social (casamento, aniversário, formatura) que fotografa
com Canon sem FTP, usa o celular como ponte, vive no WhatsApp, cobra em PIX e não quer
mais uma coisa para administrar. **HIPÓTESE:** nenhuma fotógrafa usou o Fóton num evento
real até hoje.

Fora deste ciclo: casas noturnas (Fiesta, segundo plano) e empresas (modo retirado).

## Problema
Depois do evento começa um segundo trabalho que ninguém paga: descarregar, separar quem é
quem, mandar link, responder "achou uma minha?". A foto chega fria, dias depois.
**HIPÓTESE:** que isso dói o bastante para ela pagar. Nenhuma fotógrafa foi entrevistada
com método sobre isso.

## Promessa
Quem aparece na foto recebe a foto durante a festa, sem a fotógrafa separar nada e sem o
convidado instalar nada. A fotógrafa sai do evento com o trabalho entregue e com os
contatos de quem gostou.

Tempo **não** é promessa ainda: "~1 s por foto" é o servidor, não o produto. Até medir o
caminho inteiro num evento real, nenhum número de velocidade entra em material de venda.

## Fluxo principal
```
câmera → celular (Camera Connect) → Fóton (menu Compartilhar) → reconhecimento
       → galeria do convidado, ao vivo → [WhatsApp: não existe]
       → fotógrafa vê o resultado → [pagamento: não existe]
```

## Por que pagaria (todas HIPÓTESE, nenhuma testada)
1. Economiza o pós-evento de separar e entregar.
2. "Entregou na festa" vira argumento de venda dela para os próximos clientes.
3. Os contatos que os convidados deixam viram clientes novos.
4. Dado tratado com responsabilidade (LGPD) é argumento para o cliente dela.

Preço: R$ 89,90 por evento é proposta do dono, sem teste. **O que ela faz quando
cobramos** vale mais do que o que ela diz achar do preço.

## Alternativas dela hoje
Galeria depois (Drive, Pixieset, Pic-Time), WhatsApp na mão, ou concorrentes com
reconhecimento (FotoOwl, Kamero, Samaro, TIME&SPACE, Fotop). Parte do que eles anunciam é
alegação de marketing, não benchmark (`docs/CONCORRENCIA.md`). Não competimos por
quantidade de funções.

## O que o Fóton não é
- Não é loja de fotos, CRM, site de fotógrafo nem álbum impresso.
- Não é busca de rosto sem consentimento, nem entre eventos.
- Não é app que o convidado instala.
- Não é "reconhecimento facial": isso, a galeria e a IA são infraestrutura. O produto é
  a cadeia `fotógrafa → foto → entrega → relacionamento → resultado`.

## Como mediremos valor
Por evento real, com o protocolo de `docs/PILOTO-1.md`.

| O que a fotógrafa precisaria ver | Estado do dado |
|---|---|
| Evento funcionando, fotos chegando | **temos** (`photo.criado`, faixa do painel) |
| Fotos processadas, com e sem rosto | **temos** (`photo.n_faces`) |
| Pessoas alcançadas (fizeram selfie) | **temos** (`guest`) |
| Entregas foto × pessoa, com a nota | **temos** (`match`, ADR-0035) |
| Entregas recusadas ("não sou eu") | **temos** (`rejeicao`, ADR-0037) |
| Contatos obtidos | **temos** (`contact`, opt-in) |
| Hora do disparo na câmera | **instrumentar** (EXIF + foto de calibração do relógio) |
| Tempo de envio no celular | **instrumentar** (hora do cliente no envio) |
| O convidado recebeu de fato na tela | **instrumentar** (primeira vez que o feed entregou) |
| Abriu o link e desistiu antes da selfie | **instrumentar** (contagem por evento, sem dado pessoal) |
| Fotos perdidas no caminho | **manual** (contador da câmera × recebidas) |
| Relatório útil para os noivos | **hipótese de valor** (o dado existe; o valor, não se sabe) |
| Resultado financeiro dela | **hipótese de valor** (não há cobrança) |

## FATO
- O motor funciona em produção: selfie → rosto → galeria ao vivo (`app.foton.app.br`).
- Servidor de produção, uma foto por vez: p50 de 916 ms; teto de 35 a 45 fotos/min
  (carga de 2026-09-23, `docs/BENCHMARKS.md`).
- Pronta no servidor, a foto aparece na galeria aberta em ~0,1 s (ADR-0042).
- R8 e T6s não têm FTP (verificado no menu das duas, 2026-08-29).
- O caminho celular → Fóton pelo menu Compartilhar existe em produção (ADR-0018).
- Limiar 0,40: zero entregas erradas numa amostra rotulada de 4 selfies × 43 fotos
  (ADR-0034). A amostra é pequena.
- Nunca houve evento real. Ninguém usa o Fóton hoje.

## DEDUÇÃO
- A seleção das fotos na galeria do celular é humana: nenhuma API web vigia pasta no
  Android (`docs/PILOTO-1.md`).
- Envio em lote forma fila no teto de 35 a 45 fotos/min: o lote chega em sequência.

## UNKNOWN (os que mudam arquitetura, produto ou disposição a pagar)
1. **A ponte câmera → celular → Fóton aguenta um evento?** Gestos, tempo, perdas, e se a
   fotógrafa aceita fazer isso no meio da festa. Se não, a resposta é pasta vigiada ou app
   nativo: um segundo artefato.
2. **Entrega errada em escala.** Com 100 convidados e milhares de rostos, a taxa real de
   foto na pessoa errada é desconhecida. Muda o algoritmo de entrega, e é risco de dano.
3. **Adoção do convidado.** Quantos abrem o QR, quantos fazem a selfie. Sem adoção, não há
   promessa.
4. **Tempo percebido, disparo → galeria**, por trecho. Decide o que otimizar, se algo.
5. **Volume real de um evento** (fotos por hora enviadas). Decide se a máquina basta.
6. **Por que e quanto ela pagaria.** Decide produto e preço.

## Decisões deste ciclo (dono, 2026-09-28)
- Cliente inicial: **fotógrafa**. Fiesta em segundo plano até o fluxo dela ser provado em
  evento real. Modo Empresa retirado do desenho.
- O próximo marco é **um evento real**, não uma função nova.
- WhatsApp: investigar e desenhar antes de construir (`docs/WHATSAPP.md`).
- Câmera: assumir que não tem FTP; achar a melhor ponte sem equipamento novo.
- Oracle A1: não migrar antes de medir o fluxo real.
- Filtros: primeiro o acabamento da fotógrafa, e só depois do evento; filtros do
  convidado, mais tarde.
- Cada modo terá experiência e visual próprios, com um condutor comum; a ADR-0030 é
  revista quando o segundo modo for desenhado, não antes.
