# CASAS.md | Fóton nas casas: bares, restaurantes, baladas e grandes eventos

> Proposta de 2026-09-27, a pedido do dono: "pensa grande, mas realista". **Nada implementado.**
> Nenhum preço aqui é medido nem decidido: preço é decisão do dono, e o que falta vira
> `UNKNOWN`. Os números de capacidade vêm de `docs/BENCHMARKS.md` (carga na VM, 2026-09-23).

## 1. A ideia em uma frase

A casa (bar, restaurante, balada) deixa um QR em cada mesa. Quem está na mesa escaneia, tira
a selfie, e **as fotos da noite chegam sozinhas para cada pessoa que aparece nelas**, com a
marca da casa. A casa paga o Fóton e ganha o que nenhuma outra ferramenta dá: **cada foto
compartilhada no Instagram é propaganda dela, feita pelo cliente.**

É o Foto'n Fiesta (o convidado fotografa) com um dono novo: não a aniversariante, mas o
estabelecimento, todos os dias.

## 2. Por que a casa pagaria (o motivo tem que ser dela, não nosso)

| O que a casa ganha | Por quê importa para ela |
|---|---|
| **Divulgação feita pelo cliente** | a foto sai com a marca da casa e vai para o Instagram de quem estava lá |
| **Um motivo para a mesa ficar** | "as fotos da mesa chegam enquanto vocês estão aqui" é experiência, não cardápio |
| **Um produto para vender** | "aniversário na casa, com Fóton" vira item de pacote |
| **O orgulho que você descreveu** | o selo físico "Tem Fóton aqui" e um número mensal: "sua casa gerou N fotos e N compartilhamentos" |

**O que a casa NÃO ganha, nunca:** saber quem são os clientes. O rosto serve para entregar a
foto à própria pessoa e morre com a noite. "Temos Fóton" não pode virar "sabemos quem vem
aqui". Isso é a linha que protege o produto inteiro (LGPD e reputação).

## 3. O que já existe e serve

| Peça | Onde | Como serve às casas |
|---|---|---|
| Evento com prazo que se apaga sozinho | ADR-0043 | **a mesa desta noite**: nasce no QR, some no fechamento |
| Espera longa no feed | ADR-0042 | a foto chega na hora, sem o celular ficar perguntando |
| Marca d'água e logo da conta | ADR-0028 | a foto sai assinada pela casa |
| Cartaz A4 com QR | `cartaz.html` | base do **display de mesa** (versão menor) |
| Créditos | colunas `credits` em `photographer` | existem no banco, **desligados** desde 2026-08-30: base do pacote de créditos |
| Moderação (cascata aprovada) | decisão C, FIESTA-IMPLEMENTACAO §3.4 | **obrigatória** quando o cliente fotografa |
| "Não sou eu" | ADR-0037 | o cliente corrige o reconhecimento |

## 4. Os quatro tipos de casa não são o mesmo produto

| | Barzinho e restaurante | Balada | Aniversário na casa | Grande evento |
|---|---|---|---|---|
| Quem fotografa | a própria mesa | a mesa **e** o fotógrafo da casa | a mesa do aniversário | fotógrafos profissionais |
| Volume por noite (hipótese) | baixo | alto, com pico | médio, concentrado | muito alto |
| Público | **tem criança** | **só maiores** | depende | depende |
| Risco principal | criança na foto | foto íntima, assédio, gente sem consentimento | nenhum específico | capacidade |
| Cabe hoje? | com trava de idade | **sim**, é o melhor encaixe | **sim** | **não** |

**Duas conclusões que vêm da tabela, não do entusiasmo:**

1. **Balada e bar noturno primeiro.** São lugares de maiores, e a v1 da Fiesta é **só para
   maiores** (FIESTA.md §6.2, ADR-0036). Restaurante de família tem criança na mesa, e isso
   trava na decisão que você mesmo fechou. Não é impossível; é para depois do parecer jurídico.
2. **Grande evento não cabe na máquina de hoje.** A VM processa ~35 a 45 fotos por minuto
   (medido). Um evento de 10 mil pessoas tirando 10 fotos cada são 100 mil fotos: na VM atual,
   **mais de 30 horas de fila**. Grande evento exige a máquina maior (Oracle A1 grátis, ainda a
   testar) e processamento em vários núcleos. É o "pensa grande", mas é o **degrau 3**.

## 5. Capacidade, com a conta aberta

Base medida: **~35 a 45 fotos/min** na VM atual (BENCHMARKS, 2026-09-23). Tudo o mais abaixo
é **hipótese de uso**, marcada como tal.

| Cenário (hipótese) | Fotos | Cabe na VM atual? |
|---|---|---|
| Bar com 20 mesas, 20 fotos por mesa na noite | ~400 em 5 h | sim, folgado |
| 10 casas assim na mesma noite | ~4.000 em 5 h (~13/min) | sim, se o pico não concentrar |
| Balada de 800 pessoas, 5 fotos cada | ~4.000 em 4 h | na média sim; **o pico da meia-noite é `UNKNOWN`** |
| Grande evento, 10 mil pessoas, 10 fotos | ~100.000 | **não** |

Consequência: o piloto com casas cabe na máquina de hoje **se forem poucas e pequenas**. Para
crescer, a migração para a máquina maior deixa de ser opcional.

## 6. Como a casa paga | três modelos, uma recomendação

| Modelo | Como funciona | A favor | Contra |
|---|---|---|---|
| **A · Créditos da casa** | a casa compra pacotes; cada **mesa ativada numa noite** gasta 1 crédito | simples de explicar; a casa revende em pacote de aniversário; **a infraestrutura de créditos já existe** | a casa precisa lembrar de recarregar |
| **B · Mensalidade da casa** | valor fixo por mês com um teto de mesas/fotos | receita previsível para o Fóton; a casa oferece como cortesia | teto precisa ser medido, senão uma balada grande sai no prejuízo |
| **C · O cliente paga na mesa** | a mesa escolhe desbloquear o álbum da noite por PIX; a casa ganha comissão | a casa não paga nada para começar | exige pagamento automático (provedor de PIX com aviso de pagamento); disposição do cliente de bar pagar é `UNKNOWN` |

**Recomendação: A para começar, B quando houver casas fiéis, C só depois.** A é o que você
consegue vender na semana que vem, com PIX manual e ativação pelo admin, sem integração nova.
Os **valores** de cada modelo são decisão sua e hoje são `UNKNOWN`.

**A unidade que cobra certo é "mesa por noite", não "foto".** A casa entende mesa; foto é
custo nosso, que o teto do plano protege.

## 7. "Temos Fóton" | o sistema de orgulho

1. **Display de mesa** (acrílico A6, versão pequena do cartaz): QR, a frase "as fotos da sua
   mesa chegam aqui", a marca da casa e o selo "Tem Fóton".
2. **Selo na porta e no Instagram da casa** (arte pronta para ela postar).
3. **Número do mês** no painel da casa: fotos da casa, mesas ativadas, **compartilhamentos**.
   É o número que ela mostra para o sócio, e o que justifica a renovação.
4. **Mapa "Onde tem Fóton"** no site: a casa ganha vitrine; o Fóton ganha prova social.
   (Público e sem dado pessoal: só a casa, o bairro e o selo.)

## 8. O que muda no produto (degrau por degrau)

**Degrau 1 | piloto com 1 a 3 bares ou baladas (cabe na máquina de hoje)**
- Conta do tipo **casa**, com marca e logo (a estrutura de perfil já tem três peles).
- **Mesa da noite**: QR fixo da mesa que abre um evento que se apaga no fechamento
  (reuso direto da ADR-0043, com prazo configurável em vez de 1 hora).
- **Fiesta ligada**: a mesa fotografa, com **moderação obrigatória** e limite por pessoa.
- Créditos religados, com recarga por PIX manual.
- Display de mesa para imprimir.

**Degrau 2 | casas fiéis**
- Painel da casa com o número do mês e o selo.
- Mensalidade com teto.
- Mapa "Onde tem Fóton".

**Degrau 3 | grande evento**
- Máquina maior e processamento em paralelo, **medido** antes de vender.
- Telão (já decidido: v2).

## 9. O que nunca faremos (vale para as casas também)

- **Câmera fixa reconhecendo quem entra.** Seria vigilância, não festa. Só tem rosto no
  sistema quem tirou a selfie por vontade própria.
- **Entregar à casa lista de clientes, rostos ou frequência.**
- **Reconhecer alguém entre casas diferentes.** A mesa de uma noite não enxerga outra noite
  nem outra casa (é o mesmo princípio de "nada de busca global").
- Vender a promessa de grande evento antes de a máquina aguentar, medido.

## 10. Riscos, em ordem

1. **Foto de quem não quis.** Na mesa, alguém fotografa a mesa do lado. Mitigação: só recebe
   quem fez selfie; "Não sou eu"; pedido de remoção; moderação. Parecer jurídico continua
   necessário (FIESTA-IMPLEMENTACAO §3.3).
2. **Balada: conteúdo impróprio e assédio.** Moderação obrigatória desde o primeiro dia; a
   casa como responsável por retirar (Marco Civil, art. 21).
3. **Criança em restaurante.** Travado pela v1 só para maiores; por isso a ordem da §4.
4. **Suporte.** O funcionário do bar não é técnico: o display tem que funcionar sem ninguém
   da casa explicar nada.
5. **Pico da balada** acima da vazão da máquina: `UNKNOWN` até medir numa noite real.

## 11. Decisões que são suas

1. **Topa começar por bar noturno e balada** (maiores), deixando restaurante de família para
   depois do parecer?
2. **Modelo A (créditos por mesa-noite)** para o piloto?
3. **Quanto custa uma mesa-noite** e o pacote de créditos? (`UNKNOWN` até você decidir.)
4. **Qual casa seria a primeira?** Uma casa real muda mais o desenho do que qualquer documento.

## 12. Rodada de 2026-09-27 | preço, restaurantes e LGPD

### 12.1 A proposta do dono: R$ 89,90 por 2 horas, pago pelo cliente

**Contra a concorrência (preços públicos, consultados em 2026-09-27):**

| Referência | Preço | O que é |
|---|---|---|
| GuestPix | a partir de **US$ 19,99** por evento | convidados sobem fotos; sem reconhecimento facial |
| Kululu | **US$ 39** (500 envios) a **US$ 99** (ilimitado, com marca e moderação) por evento | idem |
| Cabine de fotos no Brasil | **R$ 500 a R$ 3.000**; R$ 800 a R$ 1.500 por 4 h na tradicional | aluguel com equipamento e operador |

**Leitura:** R$ 89,90 fica **abaixo até do plano mais barato do GuestPix** em qualquer câmbio
acima de R$ 4,50 por dólar, e o GuestPix não reconhece rosto nem entrega na hora. Contra a
cabine, é uma fração. Ou seja: **o preço não é o risco.** O risco é outro, e é `UNKNOWN`: se o
cliente de bar compra, por impulso, um serviço de foto que ele não sabia que existia.

**Dois ajustes que eu faria antes de testar:**
1. **"A noite da mesa", não "2 horas".** Cortar no meio do aniversário (a foto para de chegar
   com a festa ainda rolando) é a pior experiência possível. Se o custo preocupar, o teto
   deve ser de **fotos**, não de relógio.
2. **O cliente paga na comanda, não no Fóton.** A casa cobra os R$ 89,90 junto da conta e gasta
   um crédito comprado de nós por menos. Isso dispensa integração de pagamento, dá margem à
   casa (o motivo dela empurrar o produto) e usa os créditos que já existem. O preço do crédito
   para a casa é decisão do dono (`UNKNOWN`).

### 12.2 Restaurantes: o dono quer incluir

Possível, mas é o segmento com a regra mais dura, porque **tem criança na mesa**:

- **LGPD, art. 14:** dado de criança e adolescente só no **melhor interesse** deles; quando a
  base for consentimento, ele precisa ser **específico e em destaque**, dado por pelo menos um
  dos pais ou responsável.
- **ANPD, Enunciado CD/ANPD nº 1/2023 (vinculante):** o tratamento pode usar **qualquer base
  legal dos arts. 7º e 11**, não só o consentimento, **desde que o melhor interesse prevaleça**.
- **Biometria é dado sensível** (art. 5º, II): base legal do art. 11.
- **ECA Digital (Lei 15.211/2025), em vigor desde 17/03/2026:** vale para serviço digital
  "direcionado ou de acesso provável" por criança e adolescente, com deveres de prevenção,
  proteção, informação e segurança, **proporcionais ao porte** do fornecedor. Um Fóton em
  restaurante de família entra, com boa chance, no "acesso provável".

**Como o restaurante pode entrar sem cruzar a linha** (desenho já aceito na ADR-0036, aplicação
adiada): **a criança não é usuária, o responsável é.** Ela nunca tira selfie sozinha; o
responsável cadastra do celular dele e recebe as fotos dela. Retenção da **noite**, não de dias.
E, com o ECA Digital em vigor, o **parecer jurídico deixa de ser recomendação e passa a ser
porta**: restaurante de família só entra depois dele. Isto não é aconselhamento jurídico.

### 12.3 Fontes (2026-09-27)

- GuestPix, Kululu: [comparativo de preços](https://www.wedibox.com/compare/pricing) · [Kululu, página de preços](https://www.kululu.com/pricing) · [Kululu × GuestPix](https://oureventalbum.com/vs/kululu-vs-guestpix)
- Cabine de fotos: [GetNinjas](https://www.getninjas.com.br/eventos/equipamentos-para-festas/preco/cabine-de-fotos) · [CBL Connect](https://cblconnect.app/blog/quanto-custa-cabine-de-fotos)
- ANPD: [Enunciado CD/ANPD nº 1/2023](https://www.gov.br/anpd/pt-br/assuntos/noticias/anpd-divulga-enunciado-sobre-o-tratamento-de-dados-pessoais-de-criancas-e-adolescentes)
- ECA Digital: [Machado Meyer](https://www.machadomeyer.com.br/pt/inteligencia-juridica/publicacoes-ij/direito-digital/estatuto-digital-da-crianca-e-do-adolescente-lei-n-15-211-2025-entra-em-vigor-em-17-de-marco-de-2026) · [Data Privacy Brasil](https://www.dataprivacybr.org/eca-digital-entra-em-vigor-o-que-a-lei-preve-e-o-que-ainda-falta-regulamentar/)
