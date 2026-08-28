# site/ — site de marca do Fóton

Vitrine de marketing, **separada do app** (`app/web/`). Não roda backend, não fala
com a API — é HTML/CSS/JS autocontido (GSAP + Lenis + ScrollTrigger inline).

- **Ainda não está publicado em lugar nenhum.** `netlify.toml` continua apontando
  para `app/web` (a demo antiga) — trocar o alvo do deploy é decisão do dono,
  não foi feito junto com este commit.
- Skill usada: `.claude/skills/build-awwwards-quality-sites/` (instalada de
  https://github.com/MengTo/Skills).
- Honestidade de conteúdo: sem depoimento inventado, sem preço inventado
  (ADR-0012 — preço aguarda EXP-10), sem foto de "cliente" fabricada. A prova
  social é o fato real — primeira parceira piloto, Patrícia Vargas, Santos/SP.

## Para publicar de verdade

1. Ver o rascunho, pedir ajustes.
2. Decidir: `site/index.html` vira o publish do Netlify (troca `netlify.toml`),
   ou fica noutro domínio/serviço.
3. Nesse ponto, também decidir os links de CTA (hoje são `mailto:`) — se
   quiser um link direto para o app, esperar o domínio próprio resolver
   primeiro (`foton.app.br`), para não linkar para uma página com aviso de
   "site perigoso" no duckdns.
