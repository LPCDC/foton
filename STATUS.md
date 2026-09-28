# STATUS.md | o que está pronto e o que falta no Fóton

> Checklist vivo (regra global do dono: "fechado" = congelado em arquivo). Atualizado em
> 2026-09-27 a partir de `docs/plans/2026-09-22-lista-de-planos.md`, `docs/CASAS.md`, das
> ADRs e dos commits. Cada item fechado aponta a prova. Antes de declarar qualquer coisa
> pronta, este arquivo é a lista.

## Pronto e no ar (com prova)

- [x] Certificado HTTPS até 2026-12-21 | `docs/DNS-MIGRACAO.md` §5, commit `79ed8b6`
- [x] Design system Bauhaus com contraste testado, ouro como marca | ADR-0038, `7469c74`
- [x] Esteira da pintura (Higgsfield) com alfândega | ADR-0039
- [x] Acessibilidade do app (zoom, foco) e do site (menu no celular) | `a558e30`, `3447194`
- [x] Entrada do app por papel | ADR-0040, `64bd571`
- [x] Jornada do convidado no design system (entrar, selfie, galeria) | `3b2a561`, `80677a6`
- [x] Limites de tamanho e tipo, freio na selfie, fim do `artifact.html` | ADR-0041, `312decd`
- [x] Espera longa: a foto aparece ~0,1 s depois de chegar ao servidor | ADR-0042, `52c0b00`
- [x] Cartaz A4 do evento, assinado pela fotógrafa (ou pelo Fóton no modo festa) | `fcaa4b4`
- [x] Evento-demonstração de 1 hora que se apaga sozinho | ADR-0043, `3782065`
- [x] Reconhecimento na foto original; look e marca d'água depois | ADR-0044, `2f57018`
- [x] Foto de referência do roteiro da porta | ADR-0045, `ba49d44`
- [x] Medições: recebida → entregue e carga da VM (35 a 45 fotos/min) | BENCHMARKS

## Falta para o app e o site estarem "terminados"

### Com o Claude (não depende de ninguém)
- [ ] **Painel da fotógrafa no design system** (lista de eventos, criar evento, tela do evento, conta). Hoje só a entrada e a jornada do convidado foram migradas; o resto do app ainda é o visual antigo.
- [ ] **Site de vendas: estrutura e conteúdo** (página mínima de piloto: o produto de verdade, os três passos, privacidade, chamada para piloto). O visual antigo do site continua no ar.
- [ ] **Matriz design system → app** (cada componente, onde aparece, estados) | plano 9
- [ ] **Validação em celular real** (portão 4): o Claude emula 375 px; aparelho de verdade falta

> **Decisão do dono, 2026-09-28:** o Higgsfield fica para os ajustes finais. O Claude
> migra painel e site para o design system e gera as imagens pelo Higgsfield daqui do
> chat, com a skill `build-awwwards-quality-sites`: "surpreender pela beleza, efeitos,
> mas leveza". Direção de arte em `docs/DIRECAO-VISUAL.md`.

### Com o dono
- [ ] **Ajustes finais pelo Higgsfield** (depois do painel e do site no design system)
- [ ] **Preço**: o dono propôs R$ 89,90 (§12 de CASAS.md); falta o preço do crédito para a casa e para a fotógrafa
- [ ] Apagar pelo painel: conta GLAMON; conta de teste `carga-1790199346@teste.foton`

## Falta para vender às casas (CASAS.md, degrau 1)
- [ ] Fiesta: o convidado fotografa, com moderação (cascata aprovada) | FIESTA-IMPLEMENTACAO
- [ ] Conta do tipo casa e "mesa da noite" (reuso do evento com prazo)
- [ ] Créditos religados + cobrança na comanda (PIX manual, ativação pelo admin)
- [ ] Parecer jurídico **antes** de restaurante de família (ECA Digital em vigor)

## Adiado de propósito
- WhatsApp (conta Meta e número do dono) | `docs/WHATSAPP.md`
- Máquina maior (Oracle A1 grátis, a testar em ARM) | só quando a vazão apertar
- Backup cifrado e região do R2 | decisão do dono: depois
- Apresentação e vídeo para as casas | **só depois do app e do site terminados** (dono, 2026-09-27)
