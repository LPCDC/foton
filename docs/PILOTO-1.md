# PILOTO #1 — o próximo marco

> Uma fotógrafa. Uma câmera. Um evento. Convidados reais. Dinheiro real.
> Não é "Fóton v1.1". Enquanto isto não passar, **nada de R2, marca própria,
> freemium ou escala** — seria otimizar uma máquina que ninguém provou que vende.
> Aberto em 2026-08-28.

## O experimento deste ciclo (2026-09-28)

> Reaberto pela orientação do dono de 2026-09-28 (`PRODUCT.md`): o evento real é o
> principal experimento do ciclo. Não é mais a Patrícia (dono, 2026-09-27); é **uma
> fotógrafa** que aceite usar o Fóton num evento nas próximas semanas. O critério de
> aceite de 2026-08-28 (abaixo) continua valendo, com o que este bloco acrescenta.

### O que ele precisa responder
Os UNKNOWNs de `PRODUCT.md`: a ponte câmera → celular → Fóton aguenta a festa? Quantas
fotos vão para a pessoa errada? Quantos convidados aderem? Quanto tempo leva cada trecho?
Qual o volume real? Ela paga pelo próximo?

### Portões antes do evento (sem eles, não se expõe convidado real)
| # | Portão | Quem | Por quê |
|---|---|---|---|
| P1 | **Instrumentação por trecho** no ar e testada: hora do disparo (EXIF + foto de calibração do relógio), hora do envio no celular, primeira vez que a foto chegou à tela do convidado, e "abriu o link sem fazer selfie" (contagem, sem dado pessoal) | Claude | Sem isso o evento produz impressão, não número |
| P2 | **Ensaio de mesa** pelo dono: celular Android dele, a câmera que houver, 3 a 5 pessoas, o roteiro abaixo inteiro | dono | Responde o B2 (o Fóton aparece no Compartilhar? a galeria seleciona por arrasto?) sem gastar a paciência de uma fotógrafa |
| P3 | **Risco de entrega errada decidido**: aceitar o risco do piloto com convidados avisados e o "Não sou eu" à vista, ou medir antes numa base maior | dono decide, Claude mede | A amostra rotulada tem 4 selfies (ADR-0034); foto na pessoa errada é o pior erro |
| P4 | **Fotógrafa e anfitrião de acordo**: ela sabe que é teste; quem contratou a festa autoriza (`docs/CONTRATO-ORGANIZADOR.md`) | dono | O organizador é o controlador dos dados (PRODUTO.md §3b-2) |

### Os horários, com o que cada um é (fechado em 2026-09-28)
| | O que é | Estado |
|---|---|---|
| T0 | disparo, derivado do EXIF + calibração pela foto do relógio | proxy calibrado |
| T1 | **proxy da chegada ao celular** (data do arquivo). "Data do arquivo" e "chegou ao celular" podem não ser a mesma coisa | **a validar no Android real (P2)** |
| T2 | início do envio para o Fóton | celular, levado ao relógio do servidor |
| T3 | recebimento pelo servidor | medido |
| T4 | processamento terminado (salva, entregas decididas, feed acordado) | medido |
| T5 | imagem **efetivamente carregada na galeria** do convidado | observado, ou **não observado** (a galeria não estava visível ou desenhando). Não observado nunca vira atraso nem falha de entrega |

### A pergunta do P2 (não é "o código funciona?")
> Uma fotógrafa consegue fazer 20 fotos com a câmera, receber essas fotos no Android,
> selecionar um lote e mandar para o Fóton **sem pensar no Fóton**?

Se sim, a arquitetura atual ganha uma evidência valiosa e se adia muita engenharia. Se não,
o ensaio mostra onde quebra: seleção, Compartilhar, Camera Connect ou transferência. Por
isso, **nada de app Android nativo nem pasta vigiada antes do P2** (dono, 2026-09-28).

**Hipótese a testar (não é evidência do P1):** o gargalo operacional está na ponte câmera →
celular → Compartilhar e no comportamento da fotógrafa, mais do que no servidor. Apoio que
existe: a seleção na galeria é humana (dedução, acima) e 30 selfies ao mesmo tempo deram P95
de 8,2 s (medição de 2026-08-29, B3). O ensaio do P1 **não** mediu isso: os 36 a 69 s "no
celular até entrar no Fóton" dele eram o tempo do script de simulação.

### Roteiro do ensaio de mesa (P2), com a instrumentação do P1
**Regra: não corrigir nada durante o ensaio.** Se uma etapa parecer ruim, registrar o gesto,
o tempo, o erro e o contorno usado. Mudar o produto só depois, com o registro na mão.
1. No painel: criar o evento e abrir **"Ensaio: medir o caminho da foto"**.
2. Abrir o **relógio de calibração** num segundo aparelho e **fotografar a tela com a
   câmera**, nítida. Essa foto entra no Fóton como qualquer outra.
3. 3 a 5 pessoas escaneiam o QR, fazem a selfie e **ficam com a galeria aberta e a tela
   acesa**: o T5 só existe quando a foto carrega com a tela ligada.
4. Fotografar ~20 fotos (rajada e espaçadas), passar pelo Camera Connect e compartilhar
   para o Fóton. Anotar **como** fez (um lote, vários, uma a uma).
5. Anotar o **número do último arquivo** da câmera (perdas = buracos na sequência).
6. No fim: **"Exportar medidas (JSON)"** e mandar o arquivo, a foto do relógio e a folha de
   campo preenchida. O relatório roda com o que a folha anota:
   `python tests/relatorio_evento.py <json> --relogio IMG_0201=HH:MM:SS.d --disparos 201-221 --galeria IMG_0205=HH:MM:SS.d`
7. **Validar o T1:** comparar, em 3 ou 4 fotos, a data do arquivo com a hora em que a foto
   apareceu na galeria do celular (cronômetro ou gravação de tela). Se o relatório marcar T1
   **suspeito**, o Android não passou a data do arquivo pelo
   Compartilhar: o trecho câmera → celular fica UNKNOWN nesse caminho.

### Preparação do P2 (2026-09-28)
- **Folha de campo** de uma página: `docs/P2-FOLHA-DE-CAMPO.html` (imprimir em A4). Cada
  campo alimenta uma pergunta do P2 ou um número que o export não tem.
- **Ensaio simulado** (`tests/ensaio_simulado_p2.py`, resultado em `docs/BENCHMARKS.md`):
  o relatório foi posto contra exports no formato do P2, com verdade conhecida, e errava
  sem avisar em quatro pontos, agora corrigidos e travados no `test_relatorio` [5]: T1 falso
  aceito (três jeitos de o Android datar o arquivo), perda no fim da sequência invisível,
  "0 perdas" quando o nome do arquivo some, lotes ausentes.
- **DEDUÇÃO a olhar no P2 (não é medida):** mandando em lotes, o disparo até a galeria
  fica maior que o intervalo entre um lote e outro. Lotes de 2 em 2 minutos dão um P95 em
  torno de 100 s na simulação, e o critério #4 (30 s) cai. O que o P2 mede é o intervalo
  que a fotógrafa usa de fato; decidir o que fazer com isso só depois do número.

### Antes do P2: o que o dono confere em produção
**Já conferido pelo Claude (2026-09-28, 19:52, sem conta):** `/health` ok, versão `9cd7d05`,
motor carregado · `/agora` responde · `relogio.html` 200 · manifest com o alvo de
compartilhamento (`fotos`, `image/*`) · `/medidas` sem login dá 401.

**Na véspera, no Android do ensaio (uns 15 min):**
1. `app.foton.app.br` abre no Chrome **sem aviso de "site perigoso"** (B1). Repetir num
   segundo celular, de preferência de outra marca ou um iPhone.
2. Fóton **instalado** a partir de `app.foton.app.br`. Se houver um instalado do endereço
   antigo (`getfoton.duckdns.org`), desinstalar antes: o Compartilhar pertence ao endereço
   de onde o app foi instalado.
3. Conta aberta no app instalado (a senha, você mesmo digita).
4. **Prova do Compartilhar num evento-demonstração** (o de 1 hora, que se apaga sozinho):
   abrir o evento-demonstração, compartilhar 3 fotos da câmera pela galeria, conferir que
   entraram, **"Exportar medidas (JSON)"** e me mandar. Esse JSON responde, antes do
   ensaio: o nome `IMG_xxxx` chega? a data do arquivo chega? a via é `compartilhar`?
5. Eventos antigos "ao vivo" da conta encerrados: o Compartilhar manda para o **último
   evento aberto**, e evento esquecido aberto é foto no lugar errado.
6. Câmera: **data de hoje** e hora mais ou menos certa (a foto do relógio corrige os
   segundos, não o dia). Camera Connect pareado; anotar se há "envio automático após o
   disparo".
7. Data e hora **automáticas** no celular.

**No dia, antes da primeira foto:**
8. Criar o evento do ensaio e **abri-lo por último** no celular (é para ele que o
   Compartilhar vai mandar).
9. Relógio de calibração aberto no segundo aparelho mostrando "hora do servidor · ± N ms",
   com N abaixo de 150 (acima, recarregar).
10. Celular na rede que o evento teria (4G, Wi-Fi desligado), e anotar na folha.
11. Os 3 a 5 convidados sabem que é teste e que o evento é apagado depois da análise;
    tempo de tela apagada deles em 10 min ou mais.
12. Folha de campo impressa, caneta, cartaz ou QR na tela.
13. Pendente de antes: confirmar que o e-mail de teste do UptimeRobot chegou (B5).

### O que se mede, por trecho (servidor rápido ≠ produto rápido)
| Trecho | Como | Automático? |
|---|---|---|
| câmera → celular | EXIF da foto × hora do envio no celular, corrigido pela foto do relógio | sim, depois do P1 |
| celular → Fóton | hora do envio no celular × chegada ao servidor | sim, depois do P1 |
| processamento | `latency_ms` do `/ingest` (já existe) | sim |
| Fóton → tela do convidado | pronta × primeira entrega pelo feed | sim, depois do P1 |
| perdas | contador de disparos da câmera × fotos recebidas | manual, no fim |
| duplicatas | recusas por `photo.sha` (já existe) | sim |
| entregas e recusas | `match` e `rejeicao` (já existem) | sim |
| adesão do convidado | abriu o link × fez selfie × recebeu ≥ 1 foto | sim, depois do P1 |
| comportamento da fotógrafa | quantos lotes, de quanto em quanto tempo, onde travou, o que perguntou | observação e entrevista de 10 min |
| comportamento do convidado | voltou à galeria? baixou? pediu ajuda? | parcial; o resto, observação |

### Três testes sem construir nada (fazer como se existisse)
1. **Relatório para os noivos:** depois do evento, gerar à mão (script) uma página com o
   que aconteceu e entregar à fotógrafa. **Medida:** ela encaminha aos noivos ou não.
2. **WhatsApp:** quem deixou contato recebe o link da galeria pelo WhatsApp **da própria
   fotógrafa**, depois do evento. **Medida:** quantos voltam à galeria. Nenhuma conta Meta
   para isso.
3. **Pagamento:** ao fim, oferecer o próximo evento pago, por PIX, no preço que o dono
   decidir. **Medida:** paga ou não paga. Opinião sobre preço não conta.

### Sucesso
Os seis critérios de 2026-08-28 (abaixo), mais: a fotógrafa **pagou** ou **marcou** o
próximo evento pago. Falhou qualquer um: registrar onde a cadeia quebrou, consertar só
aquilo e repetir.

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
| 4 | **P95 do disparo até a foto aparecer na galeria do convidado ≤ 30 s** | O SLA de projeto é 10 s; num piloto com rajada, 30 s ainda é "na hora". Medir o número real, não o desejado. **Só conta entrega observada** (houve T5, com a galeria aberta); a não observada é contada à parte e **não é atraso** (redação corrigida em 2026-09-28, ver definições acima). |
| 5 | A fotógrafa operou **sozinha**, sem o desenvolvedor no ombro | É produto, não demonstração. |
| 6 | O convidado abriu o link **sem aviso de segurança** do navegador | Ver bloqueador B1. |

Falhou qualquer um → **no-go**, conserta e repete. Sem negociar critério depois do fato.

## Bloqueadores (têm que cair ANTES do piloto)

| | Bloqueador | Estado (2026-08-28) |
|---|---|---|
| **B1** | **Chrome mostra "Site perigoso"** no celular do convidado (reputação do domínio `duckdns.org`, não é o certificado). Correção: **domínio próprio**. | **RESOLVIDO no domínio (2026-09-28):** `app.foton.app.br` e `foton.app.br` no ar, certificado até 2026-12-21 (`STATUS.md`). Falta só ver, no ensaio de mesa (P2), que o celular de um convidado abre sem aviso. |
| **B2** | **Como a foto sai da câmera dela.** A premissa "R8 tem FTP nativo" **estava errada**: nem a R8 nem a T6s têm FTP. | **CAMINHO ENTREGUE, FALTA O ENSAIO.** O elo celular → Fóton foi construído e está em produção: menu "Compartilhar" do Android → Fóton, **zero gesto dentro do app** (ADR-0018, medido em `docs/BENCHMARKS.md`). Falta com hardware real: (a) o Fóton aparece no menu Compartilhar do celular dela? (b) a galeria dela seleciona por arrasto? (c) a T6s tem envio automático após o disparo? Os três são `UNKNOWN — REQUIRES EXPERIMENT` (`docs/ROTEIRO-CAMERAS.md`). |
| **B3** | **Rajada**: 1 vCPU, foto de câmera grande domina o tempo. | **MEDIDO E RESOLVIDO para o critério do piloto** (2026-08-29). Rajada de **50 fotos de 2,1 MB: 55,6 s, P95 de 1,9 s por foto, zero perdida**. Com o poll do convidado dá ~4,5 s até aparecer no celular — folgado nos 30 s do critério #4. A extrapolação antiga (~46 s para 20 fotos) era **pessimista**: foi feita antes do `reduzir()` e do `Image.draft()`. **O gargalo mudou de lugar:** agora é a **selfie** — 30 convidados escaneando o QR ao mesmo tempo dão **P95 de 8,2 s** para o último. Não quebra, mas é o pior momento da experiência. Ver `docs/BENCHMARKS.md`. |
| **B4** | **Disco**: fotos são BLOB no SQLite × 7 backups completos. | **MEDIDO, rebaixado.** 40,5 GB livres de 48,3 GB, banco de 3,3 MB — folga real, não é risco imediato. `/admin/saude` expõe o número e alerta se passar de 80%. |
| **B5** | Monitor externo: sem ele, ninguem sabe que o Foton caiu. | **RESOLVIDO em 2026-08-29 - UptimeRobot no ar.** Tres monitores, checagem a cada **5 min de verdade** (o GitHub Actions dizia 5 min e entregava ~5 HORAS - medido). Dois deles sao **keyword**, nao HTTP: batem em `/health` e exigem a string `"ok":true` no corpo. Isso pega o caso que um HTTP 200 nao pega - **servidor de pe com o pipeline morto**. Alerta por e-mail para `luizoak@gmail.com`. (1) `app.foton.app.br/health` - o endereco que a convidada usa; (2) `getfoton.duckdns.org/health` - o endereco antigo, que QRs impressos e PWAs ja instalados ainda usam; (3) `foton.app.br` HTTP - o apex. O workflow do GitHub continua como rede de seguranca. **Falta so o dono confirmar** que o e-mail de teste chegou na caixa dele. |

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

`docs/BENCHMARKS.md`: disparadas, recebidas, perdidas, P50/P95 do disparo→galeria do convidado (só entregas observadas),
entregas corretas, entregas erradas, convidados que não foram reconhecidos.

## Decisões do dono

1. ~~Domínio próprio (B1)~~ — **decidido**: `foton.app.br`, registrado 2026-08-28. Em propagação.
2. **Preço do piloto** — ainda em aberto; a proposta é que exista dinheiro real, mesmo simbólico.
3. **Proposta de sociedade da fotógrafa** — ela propôs, por conta própria: 50% do que
   vender com o programa + modelo de aluguel (recorrência) em vez de venda única. Isso
   **contradiz o ADR-0012** (pagamento único). Ver `BLUEPRINT.md` §10 e `docs/DECISIONS.md`.
   Ainda sem decisão — não fechar verbalmente antes do piloto.
