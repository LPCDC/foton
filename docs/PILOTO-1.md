# PILOTO #1 — o próximo marco

> Uma fotógrafa. Uma câmera. Um evento. Convidados reais. Dinheiro real.
> Não é "Fóton v1.1". Enquanto isto não passar, **nada de R2, marca própria,
> freemium ou escala** — seria otimizar uma máquina que ninguém provou que vende.
> Aberto em 2026-08-28.

## Por que este marco

O ativo não é o código. É a combinação **foto → reconhecimento → entrega
automática → durante o evento**. Isso se demonstra em 30 segundos e se entende sem
explicação. Se funcionar de forma confiável com uma câmera real, existe produto.
Se não funcionar, tudo o que vier antes disso é desperdício.

## Critério de aceite (go / no-go)

O piloto **passa** se, com evidência medida no evento:

| # | Critério | Por quê |
|---|---|---|
| 1 | **Zero foto entregue à pessoa errada** | É a falha que destrói confiança. Pior que atrasar. |
| 2 | **Zero foto perdida** — toda foto disparada chegou ao servidor | Se some foto, a fotógrafa não pode confiar no sistema. |
| 3 | ≥ 90% dos convidados que fizeram selfie receberam ao menos 1 foto correta | É a promessa do produto. |
| 4 | **P95 do disparo até aparecer no celular ≤ 30 s** | O SLA de projeto é 10 s; num piloto com rajada, 30 s ainda é "na hora". Medir o número real, não o desejado. |
| 5 | A fotógrafa operou **sozinha**, sem o desenvolvedor no ombro | É produto, não demonstração. |
| 6 | O convidado abriu o link **sem aviso de segurança** do navegador | Ver bloqueador B1. |

Falhou qualquer um → **no-go**, conserta e repete. Sem negociar critério depois do fato.

## Bloqueadores (têm que cair ANTES do piloto)

| | Bloqueador | Estado (2026-08-28) |
|---|---|---|
| **B1** | **Chrome mostra "Site perigoso"** no celular do convidado (reputação do domínio `duckdns.org`, não é o certificado). Correção: **domínio próprio**. | **EM ANDAMENTO** — `foton.app.br` registrado no Registro.br; DNS em propagação; script `infra/dominio.sh` pronto e commitado (mantém o duckdns funcionando em paralelo). Falta: propagação terminar + rodar o script no Cloud Shell. |
| **B2** | **Como a foto sai da câmera dela.** A premissa "R8 tem FTP nativo" **estava errada**: nem a R8 nem a T6s têm FTP. | **CAMINHO ENTREGUE, FALTA O ENSAIO.** O elo celular → Fóton foi construído e está em produção: menu "Compartilhar" do Android → Fóton, **zero gesto dentro do app** (ADR-0018, medido em `docs/BENCHMARKS.md`). Falta com hardware real: (a) o Fóton aparece no menu Compartilhar do celular dela? (b) a galeria dela seleciona por arrasto? (c) a T6s tem envio automático após o disparo? Os três são `UNKNOWN — REQUIRES EXPERIMENT` (`docs/ROTEIRO-CAMERAS.md`). |
| **B3** | **Rajada**: 1 vCPU, foto de câmera grande domina o tempo. | **MITIGADO, não eliminado.** Reduzir a foto no celular antes de subir (2,9× mais rápido) + `Image.draft()` no servidor (2,7× mais rápido). Medido: 1 foto isolada agora cabe folgado no SLA de 10s; rajada de 20 ainda não (~46s extrapolado, era ~125s). |
| **B4** | **Disco**: fotos são BLOB no SQLite × 7 backups completos. | **MEDIDO, rebaixado.** 40,5 GB livres de 48,3 GB, banco de 3,3 MB — folga real, não é risco imediato. `/admin/saude` expõe o número e alerta se passar de 80%. |
| **B5** | Monitor externo: sem ele, ninguém sabe que o Fóton caiu. | **RODANDO, ALERTA NÃO PROVADO.** Actions **está habilitado** — 3 execuções agendadas, todas verdes (conferido pela API em 2026-08-29; a afirmação anterior de que a aba não aparecia estava **errada** e foi repetida sem verificar). Corrigidos dois furos: ele vigiava **só o duckdns** — com `app.foton.app.br` fora do ar o monitor ficava verde — e o passo do WhatsApp tinha uma guarda de `env` no `if` que podia pulá-lo **em silêncio**. **Falta:** provar que a mensagem chega. `UNKNOWN — REQUIRES EXPERIMENT`. **Ação do dono (1 clique):** Actions → Monitor do Fóton → Run workflow → marcar **testar_alerta** → conferir se o WhatsApp chegou. |

## Caminho da foto — estado em 2026-08-29

Inventário fechado (não perguntar de novo): **Canon R8 + Canon T6s (760D)**, e
**nenhuma das duas tem FTP** — verificado no menu das duas, presencialmente. O servidor
FTP do Fóton funciona, mas **não serve para esta cliente**.

1. **Celular → Fóton pelo menu "Compartilhar"** (feito, em produção — ADR-0018). A R8
   deposita cada foto no celular sozinha (`Funções de comunicação → Enviar para
   smartphone após o disparo → Envio automático`); ela seleciona o lote na galeria e
   toca em Compartilhar → Fóton. **Dentro do Fóton: zero gesto.** É o padrão do piloto.
2. **Celular → Fóton pelo botão "Enviar foto da câmera"** (o caminho antigo, intacto).
   Funciona sem instalar nada e é o degrade quando o app não está instalado como PWA.
3. **FTP direto:** só em corpo que tem FTP no menu. Não é nenhuma das duas dela. Fica
   guardado para outros fotógrafos, não para o piloto.

### O que o "Compartilhar" resolveu e o que NÃO resolveu

**Resolveu:** os gestos dentro do Fóton (2 → 0, medido) e a navegação de pastas.
**Não resolveu:** **a seleção das fotos na galeria continua sendo humana.** Nenhuma API
web no Android deixa um site enxergar a galeria ou vigiar uma pasta (`showDirectoryPicker()`
só existe no Chrome de desktop). Não há gambiarra web possível aqui.

Por 100 fotos, num lote só (ver `docs/BENCHMARKS.md` para o método):
~106 gestos antes · **~5 depois, SE a galeria dela selecionar por arrasto** ·
~103 depois, se ela tiver que tocar foto por foto.

> **`UNKNOWN — REQUIRES EXPERIMENT` — é o número que decide.** Experimento de 5 minutos
> no celular dela: abrir a galeria, segurar uma foto, arrastar o dedo sobre as seguintes,
> e contar os toques para marcar 20. Se arrastar funcionar, a promessa está cumprida e
> nada mais precisa ser construído. Se não, decidir entre as alternativas abaixo.

> Também não medido: se o Fóton **aparece** no menu Compartilhar do aparelho dela. Exige
> o app instalado como PWA num Android real. Se ele já estiver instalado, pode precisar
> ser **reinstalado** para o Chrome reler o manifest.

## As duas alternativas de ZERO gesto por foto — decisão do dono

Custos abaixo são **estimativa de engenharia**, não medição.

### A) EOS Utility num notebook + pasta vigiada

- **Como funciona:** EOS Utility (software oficial da Canon, grátis) recebe cada disparo
  e grava numa pasta do notebook automaticamente. O Fóton vigia essa pasta e sobe cada
  arquivo novo. **Gesto por foto: zero.**
- **Cobre as duas câmeras.** É a única opção que provadamente serve para a T6s também —
  a T6s por USB é caminho certo; por Wi-Fi (modo "EOS Utility") é
  `UNKNOWN — REQUIRES EXPERIMENT`.
- **Custo:** o menor dos dois. Não precisa de app novo: o Chrome de desktop tem
  `showDirectoryPicker()`, então a pasta vigiada vira uma tela dentro do próprio Fóton.
  Estimativa: **1 sessão para construir + 1 para endurecer** (arquivo pela metade sendo
  gravado, duplicata, reconexão), mais um ensaio com a câmera de verdade.
- **No dia do evento:** notebook ligado e num lugar seguro · cabo USB até a câmera (limita
  o quanto ela anda) ou Wi-Fi para EOS Utility (sem cabo, mas com alcance e estabilidade
  a verificar) · mais um aparelho para carregar, montar e dar defeito.

### B) App Android nativo vigiando a pasta

- **Como funciona:** a Camera Connect já deposita as fotos da R8 no celular. Um app nosso
  vigia essa pasta e sobe cada arquivo novo. **Gesto por foto: zero, e sem notebook.**
- **Cobre bem a R8.** Para a T6s depende de a câmera ter envio automático após o disparo,
  que é recurso de geração nova — `UNKNOWN — REQUIRES EXPERIMENT`, provavelmente não tem.
- **Custo:** o maior dos dois, e o único que cria um **segundo artefato para manter**.
  Projeto Android de verdade: serviço em primeiro plano com notificação (restrição de
  background do Android 8+), acesso à pasta sob armazenamento com escopo do Android 11+,
  isenção de otimização de bateria, assinatura, e distribuição fora da Play Store
  (instalação lateral) ou uma publicação na loja. Estimativa: **várias sessões**, mais
  manutenção a cada versão do Android.
- **No dia do evento:** instalar uma vez · manter Camera Connect e o app nosso vivos ao
  mesmo tempo · celular acordado e no carregador · sem notebook e sem cabo.

### Recomendação

**Rodar o experimento dos 5 minutos antes de escolher.** Se a galeria dela selecionar por
arrasto, o que já está em produção cumpre a promessa e as duas alternativas viram
pós-piloto. Se não, **A** é a escolha: custa muito menos, cobre as duas câmeras, e não
cria um app para manter — o preço é levar um notebook para o evento.

### Higiene que apareceu na medição

A conta dela tem **5 eventos marcados "ao vivo"** porque eventos antigos nunca foram
encerrados. Para o share não ter que perguntar o destino, o Fóton agora manda para o
**último evento que ela abriu**. Ainda assim, encerrar os eventos velhos antes do piloto
elimina uma classe inteira de confusão.

## Roteiro do dia (ensaio, antes do evento pago)

1. Abrir o painel, criar o evento, mostrar o QR. Cronometrar quanto ela leva **sozinha**.
2. Usar o **"testar foto"** do admin com uma foto da câmera dela — valida o setup em segundos.
3. 2 pessoas fazem selfie. Fotografar 20 disparos em rajada.
4. Anotar: fotos disparadas, fotos chegadas, tempo de cada uma, entregas erradas.
5. Repetir com a segunda câmera.

## O que medir e onde anotar

`docs/BENCHMARKS.md`: disparadas, recebidas, perdidas, P50/P95 do disparo→celular,
entregas corretas, entregas erradas, convidados que não foram reconhecidos.

## Decisões do dono

1. ~~Domínio próprio (B1)~~ — **decidido**: `foton.app.br`, registrado 2026-08-28. Em propagação.
2. **Preço do piloto** — ainda em aberto; a proposta é que exista dinheiro real, mesmo simbólico.
3. **Proposta de sociedade da fotógrafa** — ela propôs, por conta própria: 50% do que
   vender com o programa + modelo de aluguel (recorrência) em vez de venda única. Isso
   **contradiz o ADR-0012** (pagamento único). Ver `BLUEPRINT.md` §10 e `docs/DECISIONS.md`.
   Ainda sem decisão — não fechar verbalmente antes do piloto.
