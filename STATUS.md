# STATUS.md | o que está pronto e o que falta no Fóton

> Checklist vivo (regra global do dono: "fechado" = congelado em arquivo). Cada item
> fechado aponta a prova. Antes de declarar qualquer coisa pronta, este arquivo é a lista.
> **Pronto é quando o dono aprova**, não quando o teste passa: tela se mostra no desktop e
> no celular antes do [x] (dono, 2026-09-28).

## Ciclo atual: prova de produto (orientação do dono, 2026-09-28)

O próximo marco é **um evento real** com uma fotógrafa, não uma função nova. Para quem, o
que se promete e o que não sabemos: `PRODUCT.md`. O experimento: `docs/PILOTO-1.md`.

### Reconciliação (feito em 2026-09-28)
- [x] `PRODUCT.md`: autoridade de produto, curta, com FATO / DEDUÇÃO / HIPÓTESE / UNKNOWN
- [x] `docs/PILOTO-1.md`: o experimento do ciclo, com portões, medidas por trecho e três testes sem construir nada
- [x] `docs/CONCORRENCIA.md`: premissa errada retirada ("reconhecimento + convidado envia + ao vivo" não é diferencial)
- [x] `docs/PRODUTO.md` marcado como cardápio de ideias, não autoridade
- [x] `docs/WHATSAPP.md`: o que precisa acontecer antes de construir
- [x] Site: saíram "com fotógrafa real", "eventos de verdade", o "~1 s" e o modo Empresa; trava no test_site [6]

### Próximo bloco (para chegar ao primeiro evento e ao primeiro pagamento)
- [ ] **P1 · Instrumentar a cadeia por trecho** (Claude): hora do disparo (EXIF + foto de calibração do relógio), hora do envio no celular, primeira entrega na tela do convidado, "abriu o link sem selfie" (contagem sem dado pessoal), e um script que monta a tabela do evento. Mudança de dados declarada antes do código.
- [ ] **P2 · Ensaio de mesa** (dono, roteiro do Claude): celular Android do dono, a câmera que houver, 3 a 5 pessoas. Responde se o Fóton aparece no Compartilhar e se a galeria seleciona por arrasto
- [ ] **P3 · Risco de entrega errada** (dono decide): aceitar no piloto com convidados avisados, ou medir antes numa base maior
- [ ] **Recrutar uma fotógrafa** para um evento nas próximas semanas (dono; convite e briefing de uma página pelo Claude)
- [ ] **Preço do próximo evento pago** e como receber (PIX manual) (dono)

### Parado de propósito neste ciclo
- Redesenho do painel. O que existe é repintura (`6e66a08`); o dono o considera ainda
  ruim, sobretudo no desktop. Antes de redesenhar, o evento diz que informação importa
  (`PRODUCT.md`, "Como mediremos valor").
- Filtros: primeiro o acabamento da fotógrafa, depois do evento. Os do convidado, mais tarde.
- WhatsApp integrado: só depois do teste sem construir (`docs/WHATSAPP.md`).
- Fiesta, casas, créditos para casas (`docs/CASAS.md`): segundo plano até o fluxo da
  fotógrafa ser provado.
- Oracle A1: não migrar antes de medir o fluxo real.
- Ajustes finais pelo Higgsfield, matriz design system → app, apresentação e vídeo.
- Skills PM Skills e Impeccable: autorizadas no texto de orientação; instalação espera o
  "pode instalar" do dono, porque baixa e executa código de terceiros.

## Pronto e no ar (com prova)
- [x] Certificado HTTPS até 2026-12-21 | `docs/DNS-MIGRACAO.md` §5, commit `79ed8b6`
- [x] Design system Bauhaus com contraste testado, ouro como marca | ADR-0038, `7469c74`
- [x] Esteira da pintura (Higgsfield) com alfândega | ADR-0039
- [x] Acessibilidade do app (zoom, foco) e do site (menu no celular) | `a558e30`, `3447194`
- [x] Entrada do app por papel | ADR-0040, `64bd571`
- [x] Jornada do convidado no design system (entrar, selfie, galeria) | `3b2a561`, `80677a6`
- [x] Limites de tamanho e tipo, freio na selfie, fim do `artifact.html` | ADR-0041, `312decd`
- [x] Espera longa: a foto aparece ~0,1 s depois de pronta no servidor | ADR-0042, `52c0b00`
- [x] Cartaz A4 do evento, assinado pela fotógrafa | `fcaa4b4`
- [x] Evento-demonstração de 1 hora que se apaga sozinho | ADR-0043, `3782065`
- [x] Reconhecimento na foto original; look e marca d'água depois | ADR-0044, `2f57018`
- [x] Foto de referência do roteiro da porta | ADR-0045, `ba49d44`
- [x] Medições de servidor: recebida → entregue e carga da VM (35 a 45 fotos/min) | BENCHMARKS
- [x] Sem travessão no app, com trava | `4be85bd`
- [x] Site de vendas no design system, com a história da capa medida no reconhecimento | `cb986f7`
- [~] Painel no design system: **repintado, não resolvido** (`6e66a08`). Consertou três defeitos reais (botão sem fundo, película latente, aba sem marca); a cara profissional continua faltando

## Com o dono, fora do ciclo
- [ ] Apagar pelo painel: conta GLAMON; conta de teste `carga-1790199346@teste.foton`
- [ ] Parecer jurídico antes de qualquer restaurante de família (ECA Digital), quando a Fiesta voltar
- Backup cifrado e região do R2: decisão do dono, depois
