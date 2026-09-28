# Direção visual | painel e site no design system

> Decisão do dono (2026-09-28): "surpreender pela beleza, efeitos, mas leveza". O Claude
> faz a migração e gera as imagens pelo Higgsfield daqui do chat; o Higgsfield entra de
> novo só nos ajustes finais. Skill que guia: `build-awwwards-quality-sites`.

## Tese

**A luz chega.** Fóton é partícula de luz: o flash da câmera congela a cena e, logo
depois, a foto aterrissa no celular de quem estava nela. Tudo no site conta essa frase,
com a gramática que já existe no design system (ADR-0038):

| forma | significa | no site |
|---|---|---|
| círculo | pessoa, rosto | a selfie do convidado |
| linha | entrega, sequência | o fio de ouro que liga a selfie à foto |
| retângulo | foto, evento | a foto da festa |

A cor viva vem das fotos. O resto é preto, branco e um único ouro.

## Peças

- **Primeira tela:** uma foto grande da festa (retângulo), congelada pelo flash. Sobre
  ela, o círculo da selfie da mesma pessoa, ligado por uma linha de ouro. O título e o
  botão estão legíveis desde o primeiro quadro; a animação só acrescenta.
- **Tipos:** Jost para títulos, Archivo para interface (os tokens `--f-display` e
  `--f-ui` do sistema). Nada de fonte cursiva.
- **Cor:** tema noite do sistema (papel preto, tinta branca, ouro `#E8D9B0`). Uma seção
  clara no meio (tema dia, ouro `#B08C3A`) para dar ritmo.
- **Sequência:** primeira tela | três passos (círculo, linha, retângulo) | a galeria
  enchendo ao vivo num celular | para quem (fotógrafa, empresa, festa) | privacidade |
  o que existe hoje, sem exagero | chamada final | rodapé com a procedência das imagens.

## Movimento

Um movimento por ideia, e todos contam a mesma frase:

1. **Flash:** a tela estoura em branco por um instante e revela a foto (só uma vez).
2. **Linha:** o fio de ouro se desenha da selfie até a foto.
3. **Chegada:** na seção "ao vivo", as fotos entram na galeria com a revelação em íris
   que o sistema já tem (`.foto`), só enquanto a seção está na tela.

Pilha: **CSS e JavaScript próprio**, sem biblioteca. A skill sugere GSAP e um motor de
rolagem suave; aqui valem as regras do repo, que vêm antes: dependência nova exige ADR
(AGENTS.md §4.3) e a ADR-0027 tirou o motor de rolagem porque ele quebrava a roda do
mouse. Three.js: **não**, nenhuma ideia do site precisa de profundidade 3D.

Com `prefers-reduced-motion`, nada anima: tudo aparece no estado final. Sem JavaScript,
a página está completa.

## Leveza (meta, não medição)

Meta para a primeira tela no celular: no máximo **250 KB** transferidos, fontes à parte.
O número real entra aqui depois de medido; até lá, `UNKNOWN | REQUIRES EXPERIMENT`.
Imagens em WebP com largura certa para cada tela, as de baixo da dobra com
`loading="lazy"`, nenhuma animação rodando fora da tela.

## Imagens

- Geradas pelo Higgsfield (`seedream_v5_pro`, o mesmo da vitrine). **Pessoas fictícias**,
  nunca pessoa real; rotuladas na página como "Fotos ilustrativas, geradas por IA".
- Cada arquivo tem registro em `PROCEDENCIA.json` (modelo, job, uso), como na vitrine.
- Nada de depoimento, logo de cliente ou número inventado.

## Painel da fotógrafa

Sem imagem nova: o painel é ferramenta. A migração troca os tokens antigos pelos do
sistema (cor, raio, fonte, sombra) numa ponte única e depois corrige, tela a tela, o que
estava pintado à mão. IDs e funções ficam intactos.
