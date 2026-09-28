# site/ | o site de vendas do Fóton

Vitrine, **separada do app** (`app/web/`). HTML, CSS e um pouco de JavaScript próprio,
sem biblioteca e sem backend. Publicado pelo Cloudflare Pages a partir desta pasta
(ADR-0032): `git push origin main` publica em `https://foton.app.br`.

## Como é feito (2026-09-28)

- **Direção:** `docs/DIRECAO-VISUAL.md`. Skill que guiou: `build-awwwards-quality-sites`.
- **Design system:** `ds/foton.css` é cópia fiel de `app/web/ds/foton.css`. O
  `tests/test_site.py` confere que as duas são iguais. Mudou lá: copie para cá e suba o
  `?v=` no `<link>` do `index.html`.
- **Movimento:** CSS (a abertura roda uma vez; as linhas de rolagem usam
  `animation-timeline: view()` onde existe) e JS próprio só para os títulos palavra por
  palavra e para a galeria ao vivo, que para fora da tela. Com `prefers-reduced-motion`,
  nada anima. Sem JS, a página está completa. Sem motor de rolagem (ADR-0027).
- **Imagens:** `img/`, geradas pelo Higgsfield, **pessoas fictícias**, rotuladas na página.
  Procedência de cada arquivo em `img/PROCEDENCIA.json`.
- **Os números da página saem de medição:** `tests/site_reconhecimento.py` mede a selfie
  contra cada foto publicada no motor e limiar da produção e grava em `PROCEDENCIA.json`;
  o `test_site` confere que o texto da página bate com esse arquivo.

## Honestidade de conteúdo

Sem depoimento inventado, sem logo de cliente, sem número sem fonte. O "10 s" é a meta
do produto (decisão do dono de manter). O tempo do servidor (~1 s por foto) **não** entra
na página: é servidor rápido, não produto rápido, e o caminho inteiro nunca foi medido
num evento real (`PRODUCT.md`, orientação de 2026-09-28).
