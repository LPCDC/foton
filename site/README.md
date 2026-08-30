# site/ — site de marca do Fóton

Vitrine de marketing, **separada do app** (`app/web/`). Não roda backend, não fala
com a API — é HTML/CSS/JS autocontido (GSAP + Lenis + ScrollTrigger inline).

- ~~**Ainda não está publicado em lugar nenhum.** `netlify.toml` continua apontando
  para `app/web` (a demo antiga)~~ — **DESATUALIZADO, ver "Estado real do deploy" abaixo.**
- Skill usada: `.claude/skills/build-awwwards-quality-sites/` (instalada de
  https://github.com/MengTo/Skills).
- Honestidade de conteúdo: sem depoimento inventado, sem preço inventado
  (ADR-0012 — preço aguarda EXP-10), sem foto de "cliente" fabricada. A prova
  social é o fato real — primeira parceira piloto, Patrícia Vargas, Santos/SP.

## Estado real do deploy (verificado em 2026-08-30, com `curl`)

Duas coisas que os documentos diziam errado:

1. **`netlify.toml` JÁ publica `site/`**, não `app/web` — mudou no commit `ffc5b1b`
   ("netlify: publica o site de marca (site/), nao mais a demo antiga do app").
   O texto riscado acima ficou para trás e enganou pelo menos uma sessão.
2. **Mesmo assim, `getfoton.netlify.app` ainda serve a demo ANTIGA.** Medido: a
   página no ar tem 42 KB, título "Fóton", contém a palavra `placeholder` 4× e
   **nenhum** marcador do site atual (`Sua foto encontra`, `intro-flash`,
   `entry-card` → 0 ocorrências). Ou seja: o `publish = "site"` está no repo mas
   **o build do Netlify não rodou desde então**.

**Conclusão:** o deploy automático do Netlify a partir deste repo está
`UNKNOWN — REQUIRES EXPERIMENT` — provavelmente nunca foi conectado, ou está
preso num commit antigo. Antes de qualquer conversa sobre apontar `foton.app.br`
para o Netlify, é preciso **confirmar no painel do Netlify** se o site está
ligado a `github.com/LPCDC/foton` e em qual branch. Sem isso, mudar DNS levaria
o domínio raiz para uma página desatualizada.

### Atualização 2026-08-30 (v2)

- **Marca nova:** o wordmark script ("Fóton" cursivo) saiu; entrou o selo real
  em uso em produção (diafragma de 6 lâminas + hexágono + ponto de luz), com
  as mesmas coordenadas de `app/web/index.html` (`_LAMINAS`/`_HEX`), no nav e
  no véu de transição para o app.
- **Abertura com flash de câmera:** ao carregar, o diafragma da marca "fecha"
  como um obturador de verdade; no instante do fecho, um flash radial (não um
  retângulo branco chapado) estoura e decai — aí sim o cabeçalho da hero
  aparece, saindo de dentro da luz. Roda em GSAP, dentro do mesmo gate
  `!reduced` do resto do site: sob `prefers-reduced-motion`, não roda nada — a
  hero já aparece no estado final. Sem JS, `#intro` fica `opacity:0` por CSS
  (nunca bloqueia o conteúdo) e é sempre `pointer-events:none`.
- **Seção "Modelo" corrigida:** o texto antigo ("compra créditos, 1 crédito =
  1 evento") ficou **desatualizado pela ADR-0024** (crédito cortado em
  2026-08-30 — nesta fase é tudo grátis, só com login). Trocado por copy
  honesta: grátis nesta fase de piloto, modelo comercial final ainda em
  aberto — sem inventar preço nem fingir que o crédito continua valendo.

## Para publicar de verdade

1. Ver o rascunho, pedir ajustes.
2. Decidir: `site/index.html` vira o publish do Netlify (troca `netlify.toml`),
   ou fica noutro domínio/serviço.
3. Nesse ponto, também decidir os links de CTA (hoje são `mailto:`) — se
   quiser um link direto para o app, esperar o domínio próprio resolver
   primeiro (`foton.app.br`), para não linkar para uma página com aviso de
   "site perigoso" no duckdns.
