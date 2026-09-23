# CAMERA-FILTROS.md — filtros com nome, calibração e o lag da câmera

> **Atualização 2026-09-23 (ADR-0044).** Decisão do dono: **filtro entra depois do
> reconhecimento**, sem experimento — não há filtro conhecido que melhore o ArcFace. O
> reconhecimento passou a rodar na cópia limpa (antes rodava na foto já com look e marca
> d'água). Os filtros com nome **já existem** como looks (`quente`, `frio`, `filme`, `vivo`,
> `pb`). O experimento 4 do §6 está **encerrado sem rodar**; o 2 e o 3 perdem urgência.

> Pesquisa e proposta de 2026-09-22. **Nada implementado.** Pedido do dono: deixar as pessoas
> calibrarem a imagem com **filtros de nome criativo** que resolvam 99% dos ajustes que se
> costuma fazer, **leve para nós** e com o **mínimo possível de lag ao mover a câmera**.

## 1. O ponto de partida que já existe no código

O app **não tem visor próprio**. Ele usa `capture="environment"`, que abre a **câmera nativa**
do celular. O comentário em `app/web/index.html:938` diz o porquê: um visor dentro do app
(`getUserMedia`) entregaria só o fluxo de vídeo, perdendo HDR e a resolução cheia do aparelho.

Isso é a chave do pedido: **enquanto não houver visor nosso, não existe lag de câmera para
resolver — a câmera é a do fabricante, otimizada por ele.** Qualquer filtro ao vivo que a
gente colocar cria o problema que o pedido quer evitar.

## 2. A saída: filtro depois do clique, aproximação antes

Separar duas coisas que costumam ser confundidas:

| Camada | O que faz | Custo de lag |
|---|---|---|
| **Correção real** | aplicada **na foto capturada**, em resolução cheia | **zero na câmera**: acontece depois do clique |
| **Prévia** | como a foto vai ficar | quase zero, se for aproximação barata |

Três formas de mostrar a prévia, da mais barata para a mais cara:

1. **Nenhuma prévia ao vivo.** A pessoa escolhe o filtro por **amostras** (duas fotos do
   próprio evento, antes e depois). Custo zero. **É a recomendação para a v1.**
2. **Prévia com filtro do CSS** (`filter: contrast() saturate() brightness()`), aplicada sobre
   uma foto já tirada ou sobre um visor. É composta pela GPU do navegador e é, de longe, o
   caminho mais barato. Não reproduz uma tabela de cor completa, mas aproxima.
3. **Visor ao vivo com tabela de cor (LUT) em WebGL.** É o que dá lag. Se um dia for preciso:
   `requestVideoFrameCallback` para andar no ritmo do vídeo, `OffscreenCanvas` num *worker*
   para tirar o desenho da thread principal, e resolução/quadros reduzidos no `getUserMedia`
   quando não der conta. Vale registrar: `requestVideoFrameCallback` **não existe no Firefox**,
   e o Safari tem comportamento próprio de `MediaStream` e WebGL.

## 3. Onde a correção roda

| Lugar | A favor | Contra |
|---|---|---|
| **No celular, antes de subir** | não gasta a VM; a foto sobe já corrigida | consome bateria e CPU do aparelho; varia por modelo |
| **Na VM, no caminho da foto** | um só lugar, igual para todos, testável | entra no caminho do SLA de 10 s; a VM é 1/8 de OCPU |
| **Na VM, fora do caminho** (versão corrigida depois) | não atrasa a entrega | o convidado pode receber a versão sem filtro primeiro |

**Recomendação:** medir antes de escolher. O experimento está no §6.

## 4. Os filtros: quais ajustes cobrem "99%"

Os ajustes que aparecem em praticamente toda edição de foto de evento:

1. **Exposição** (clareia/escurece)
2. **Temperatura e matiz** (tira o amarelo de luz quente, o verde de lâmpada fluorescente)
3. **Contraste**
4. **Realce de sombras e contenção de altas luzes** (rosto escuro contra janela clara)
5. **Saturação e vibração** (vibração mexe menos no tom de pele)
6. **Grão** e **nitidez leve**

> ⚠️ **`UNKNOWN — REQUIRES EXPERIMENT`:** dizer que esses seis cobrem 99% é hipótese, não
> medição. A checagem é barata e é com a Patrícia: pedir 10 fotos dela **antes e depois** da
> edição e comparar. Sem isso, "99%" não entra em documento nem em site.

**Nomes com sentido, não enfeite** — cada filtro é uma decisão, e o nome diz o problema que
resolve:

| Nome | Problema que resolve |
|---|---|
| **Salão quente** | luz amarela de festa: esfria a cor e segura o tom de pele |
| **Contraluz** | rosto escuro contra janela ou pista iluminada: levanta sombra |
| **Pista de dança** | luz colorida e pouca luz: contraste e grão, sem estourar cor |
| **Fim de tarde** | luz dourada: mantém o quente sem deixar tudo laranja |
| **Preto Bauhaus** | preto e branco de contraste firme, da gramática da marca |
| **Natural** | só corrige exposição e branco; não inventa estilo |

## 5. Calibração: o que "calibrar a câmera" quer dizer aqui

Três níveis, do mais simples ao mais ambicioso:

1. **Calibração por evento, automática.** As primeiras fotos do evento medem a temperatura de
   cor e a exposição média; o resto do evento é normalizado por essa referência. Barato, e
   resolve o caso "o salão inteiro é amarelo".
2. **Calibração por referência.** A fotógrafa fotografa uma folha branca (ou a folha do QR,
   que já é preta e branca) e o sistema calcula o branco real. Mais preciso, exige um gesto.
3. **Perfil da fotógrafa.** Ela escolhe o filtro padrão dela uma vez; passa a valer em todo
   evento novo. É o que transforma o filtro em "a cara dela".

## 6. Experimentos antes de qualquer linha de produto

| # | Pergunta | Como | Sai em |
|---|---|---|---|
| 1 | Os seis ajustes cobrem o que a Patrícia faz? | 10 pares antes/depois dela, comparados | decide a lista de filtros |
| 2 | Quanto custa aplicar na VM? | aplicar em 50 fotos reais na VM, medir p50/p95 e memória | BENCHMARKS |
| 3 | Quanto custa no celular? | mesma correção no navegador, em 3 aparelhos | BENCHMARKS |
| 4 | Estraga o reconhecimento? | rodar o pareamento antes e depois do filtro e comparar as notas | **crítico**: filtro que muda a cor da pele pode mexer no embedding |
| 5 | A prévia do CSS engana? | comparar prévia e resultado final lado a lado | decide se a v1 tem prévia |

O experimento 4 é o que ninguém lembra e pode inviabilizar tudo: **se o filtro for aplicado
antes da detecção, ele mexe com o reconhecimento.** Regra provável: **reconhecer sempre no
original, aplicar o filtro só na cópia entregue.**

## 7. O que NÃO faremos

- Visor ao vivo com filtro na v1 — é exatamente a fonte do lag que o pedido quer evitar.
- Filtro que altere rosto: suavizar pele, afinar, clarear. Além do risco ético, mexe no
  reconhecimento.
- Dependência nova de biblioteca de imagem sem ADR. O Pillow já está no projeto.

## Fontes (2026-09-22)

- [requestVideoFrameCallback (MDN)](https://developer.mozilla.org/en-US/docs/Web/API/HTMLVideoElement/requestVideoFrameCallback)
- [WebCodecs e Streams para vídeo em tempo real](https://webrtchacks.com/real-time-video-processing-with-webcodecs-and-streams-processing-pipelines-part-1/)
- [OffscreenCanvas e workers para WebGL](https://evilmartians.com/chronicles/faster-webgl-three-js-3d-graphics-with-offscreencanvas-and-web-workers)
- [Filtro por LUT no navegador](https://github.com/lijialiang/lut-filter)
