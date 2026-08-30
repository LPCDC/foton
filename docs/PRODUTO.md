# Fóton — o produto, e o que ainda não foi decidido

> Onde moram as ideias trazidas pelo dono que ainda **não viraram código**.
> Cada item tem: o que é, o que muda, o que custa, e o que precisa ser decidido.
> Aberto em 2026-08-30.
>
> `BLUEPRINT.md` = o que existe · `docs/DECISIONS.md` = o que já foi decidido ·
> **este arquivo = o que está na mesa.**

---

## 1. Os três públicos, e as três portas

Descoberta desta fase: **não são três produtos — é um motor com três portas.**
O motor (foto → rosto → entrega certa) é o mesmo. O que muda é a casca e o vocabulário.

| Quem | O que é para ela | Vocabulário | Estado |
|---|---|---|---|
| **Patrícia** — fotógrafa profissional | ferramenta de trabalho: evento começa e termina | evento, convidado | **no ar** |
| **GLAMON** — empresa, álbum interno | acervo permanente, mesmas pessoas toda semana | álbum, equipe | **no ar** (ADR-0021) |
| **Ana** — a pessoa comum no próprio rolê | é fotógrafa **e** convidada ao mesmo tempo | festa | **§2, não feito** |

**Por que importa:** a porta da Ana é a única que ninguém no Brasil atende. Face Album,
Fotix, Mirino, 4.events e TIME&SPACE são todos ferramenta de fotógrafo ou módulo de
plataforma de evento. Ninguém serve quem fotografa o próprio rolê. É consumo, é viral, e
é o freemium que já estava no `BLUEPRINT` §9c.

---

## 2. FÓTON FESTA — todo mundo é fotógrafo e convidado

**A ideia:** numa festa todos estão interligados. Qualquer um fotografa, qualquer um
recebe as fotos em que aparece. **Só o criador apaga.**

**Por que é forte:** hoje o app tem um lado que manda e outro que recebe. Numa festa de
amigos essa divisão é artificial — a mesma pessoa faz as duas coisas. E o volume
multiplica sem custo de aquisição: cada convidado vira uma câmera.

**O que muda no código:**
- Convidado passa a poder **enviar** (hoje `/ingest` exige conta de fotógrafo).
- Papéis por evento: `dono` (apaga tudo) · `participante` (envia e recebe, não apaga).
- O modelo hoje é *conta → eventos*. Passaria a ser *evento → participantes*.

**Sobre o limite por IP — razoável, mas não sozinho.** Numa festa **todo mundo está no
mesmo Wi-Fi, logo no mesmo IP**: um limite por IP puniria a festa inteira por causa de
uma pessoa. O limite tem que ser **por participante** (o id que a selfie já cria), com o
IP como segunda barreira contra abuso em massa.

**Decidir:** quantas fotos por participante? Ele apaga a **própria** foto? Se sai da
festa, as fotos ficam? Quem responde por conteúdo impróprio?

---

## 3. Login por selfie

**A ideia:** entrar com **o rosto** + uma senha recebida por e-mail, sem o código do
evento.

**O que impede:**

1. **A biometria é apagada em 7 dias** (ADR-0005). Login por rosto exige guardar o vetor
   por tempo indeterminado, ligado a uma identidade — **invertendo a promessa central**
   do produto. *(→ §3b: o dono achou a saída para isso.)*
2. **Rosto não é senha.** Rosto não se troca quando vaza. Nunca pode ser o único fator —
   o e-mail + senha não é detalhe, é o que torna a ideia defensável.
3. **Não temos e-mail.** O app não envia e-mail; entra dependência nova (exige ADR).
4. **Falso positivo muda de gravidade.** Errar o match hoje entrega uma foto errada.
   Errando no *login*, a pessoa entra **na conta de outra**. O limiar de 0,25, que serve
   para agrupar fotos, **não serve** para autenticar.

**Versão defensável:** o rosto **encontra**, a senha **autoriza**.

### 3b. Pré-cadastro — a saída do dono, e ela **funciona hoje**

**A ideia dele:** o criador usa os 7 dias antes do evento para registrar as pessoas,
subindo fotos delas. A biometria continua sumindo em 7 dias — a retenção não muda.

**Medido em produção (2026-08-30):**

```
criador sobe 2 fotos ANTES do evento  ->  2 rostos indexados
pessoa chega e faz a 1a selfie        ->  reconhecida na hora
```

Nenhum motor novo: o `/selfie` já compara contra **todos os rostos que estiverem no
evento**, tenham chegado quando tiverem. O que muda é só *quando* o criador sobe.

**O que isso resolve, e é muito:** a convidada deixa de esperar a primeira foto da festa
para ver alguma coisa. Ela faz a selfie e a galeria **já nasce cheia**. É o momento em
que o produto se prova — adiantado para o segundo zero.

**A aresta:** a foto usada para registrar aparece no álbum. **Refinamento pequeno:** uma
coluna `photo.oculta` — o rosto entra no índice, a foto não entra na galeria. "Foto de
referência".

**O que o pré-cadastro NÃO resolve:** entrar **sem o código**. Para isso o Fóton teria
que procurar o rosto em *todos* os eventos — e descobrir em que festas alguém aparece é,
por si só, um vazamento. Pré-cadastro é dentro de **um** evento; busca global é outra
coisa, e precisa do segundo fator e de base legal própria.

### 3b-2. Nome e Instagram no pré-cadastro — e a linha que não pode ser cruzada

**A ideia do dono:** ao pré-cadastrar, o criador informa **nome e Instagram** da pessoa.
Quando ela chega e faz a selfie, **ela escolhe** se compartilha esses dados com os outros.

**O que isso ganha, e é muito:** o reconhecimento deixa de ser anônimo. Em vez de
"achamos você em 8 fotos", vira **"Oi, Carol — achei 8 fotos suas"**. É outro produto
emocionalmente. E o Instagram cria a camada social: as pessoas se acham depois da festa,
que é exatamente o laço viral que falta.

**O opt-in que ele propôs está certo** — é a mesma resposta que já tínhamos dado para
"mostrar o nome na foto": a pessoa decide, e não o organizador.

**A linha, e ela é real:**

Hoje o criador já sobe fotos de pessoas antes de elas consentirem — e tudo bem, porque
esses vetores são **anônimos**: são "um rosto", não "a Carol". No instante em que se
escreve *este rosto = Carol, @carol*, cria-se um **perfil biométrico identificado de
alguém que nunca concordou com nada**. Biometria é dado **sensível** (LGPD Art. 5º, II) e
exige consentimento **específico e destacado do titular** (Art. 11, I). O organizador
não consente pela convidada.

**DECIDIDO PELO DONO (2026-08-30), depois de eu levantar a objeção acima:**
o criador registra nome e Instagram e o vínculo rosto↔nome é feito por ele, não pela
convidada. A convidada escolhe apenas se esses dados **aparecem** para os outros.
Argumento dele, e ele se sustenta: *"quem registrou foi o dono do evento onde ela está
indo; a pessoa que reclame com o dono."*

**Por que isso fecha juridicamente** (e por isso deixei de discutir): na LGPD o
**organizador do evento é o controlador** — é ele quem decide a finalidade e possui a
relação com os convidados. O Fóton é **operador**: trata os dados por conta dele. A base
legal e o ônus de ter obtido consentimento são **do organizador**, exatamente como já
acontece com a lista de convidados de qualquer casamento. Isso não é uma brecha, é o
desenho normal de um SaaS B2B.

**O que continua sendo obrigação nossa** — e isto não é opinião, é o que nos protege:

1. **Contrato com o organizador** dizendo, por escrito, que ele declara ter base legal
   para os dados que cadastrar. Sem isso, quem responde somos nós.
2. **Padrão desligado** para exibição: registrar ≠ mostrar. A convidada liga.
3. **Caminho de saída visível para a convidada**, dentro do app, sem falar com ninguém:
   apagar a própria biometria e sair do evento. Se ela não tem esse botão, o argumento
   "reclame com o dono" deixa de valer.
4. **A biometria continua expirando** (7 dias por padrão, configurável por conta), como já está.

Registrado aqui porque a decisão é dele e é defensável; os quatro itens acima são a
condição para ela continuar sendo.

**Sobre compartilhar "com geral", uma ressalva de segurança, não de conformidade:**
numa festa, deixar o Instagram visível para qualquer um que escaneie o QR expõe uma
convidada a estranhos. O padrão tem que ser **desligado**, e a escolha **separada**:
mostrar meu nome ≠ mostrar meu Instagram. Uma coisa é ser reconhecida na foto; outra é
ser encontrada depois.

**Decidir:** a lista de esperados fica visível para os outros convidados antes de cada um
se apontar? (Eu diria **não** — senão vira uma lista de quem vai à festa, aberta a
qualquer um com o QR.)

### 3d. Chat ao vivo dentro do evento — e por que ele deve ser SÓ emoji

**Ideia do dono:** um chat em tempo real dentro de cada evento, em emoji, com link para
a pessoa que está falando e para as fotos onde ela aparece.

**Dá, e é barato.** Não precisa de WebSocket nem de dependência nova: o app do convidado
**já faz poll a cada 2,5 s** para buscar fotos novas. As reações pegam carona nesse
mesmo pedido. Custo real: uma tabela (`evento, guest_id, emoji, foto_id, ts`), um POST e
um campo a mais na resposta do `/feed`. Nada de infraestrutura nova, nada de ADR de
dependência.

**A parte forte da ideia não é o chat — é o link.** Tocar em quem reagiu e cair no álbum
daquela pessoa transforma a conversa num **diretório de gente da festa**. É a camada
social do Fóton Festa entrando por uma porta pequena, sem construir o Fóton Festa
inteiro. Esse é o motivo para fazer.

**Só emoji é a decisão certa, e não por preguiça:**

1. **Sem texto não há moderação.** Chat com texto numa festa vira, no primeiro
   incidente, cantada, número de telefone, briga ou spam — e o dono do problema passa a
   ser o Fóton, não o organizador. Emoji não carrega assédio nem número de telefone.
2. **Ninguém digita numa festa.** Uma fileira de emojis é um toque; texto é dez.
3. **Emoji funciona sem idioma e sem alfabetização digital** — o mesmo público idoso que
   motivou o desenho Bauhaus das telas.

**A linha, que é a mesma da lista de convidados:** o link para o álbum de alguém só pode
existir se **aquela pessoa** ligou a exibição do nome (§3b-2). Reação de quem está com o
nome desligado aparece **sem link e sem nome** — o emoji some na multidão, que é o certo.

**Quando fazer:** depois do piloto. O piloto responde "a foto chega?"; isto responde
"a festa conversa?". Inverter a ordem é resolver o problema errado.

### 3c. Limite de UPLOAD — a métrica que substitui o crédito

**Dá, e é melhor que crédito.** Crédito conta uma coisa que só existe para nós. Limite de
upload conta **exatamente o que nos custa**: disco e CPU. E é o único número que a
fotógrafa entende sem explicação — "este pacote dá 500 fotos".

**Forma:** coluna `event.limite_fotos` (NULL = sem limite). O `/ingest` recusa com **409**
ao bater o teto, e o app avisa antes de a pessoa gastar a viagem. Na Fóton Festa o teto
vale **por participante** — senão o primeiro a chegar consome a cota de todos.

**É também a barreira de abuso certa:** limite por IP não serve numa festa; por
participante serve, e ainda vira produto.

**Agora fica tudo em NULL — sem limite.** Atrapalhar teste é pior que gastar disco, e
ainda não há preço definido.

---

## 4. Entrada coletiva — o botão da festa

**O pedido:** terceira forma de entrar, botão **maior e diferente**, com um GIF animado
de ~10 s de festa entre jovens ao fundo.

**Dar peso visual diferente à porta da festa está certo** — é a porta do produto de
consumo e não deveria parecer irmã das outras duas.

**Sobre o GIF:**
- **GIF de 10 s pesa 3 a 8 MB** e não tem compressão de vídeo. Na landing, num hotspot 4G
  de festa, é a primeira coisa que a pessoa baixa — e o produto inteiro depende daquele
  4G. Um **MP4/WebM mudo em loop** faz o mesmo com **~300 KB**.
- **Procedência importa.** Nada de banco de imagem sem licença clara, nem gente gerada
  apresentada como festa real. O padrão do projeto é `assets/CREDITS.txt`.
- **O melhor material é o seu.** 89 fotos do GLAMON e as da festa de hoje. Loop curto com
  material próprio é mais verdadeiro que qualquer banco — e resolve a licença.

---

## 5. Créditos — o modelo que não agrada

O incômodo tem nome: **crédito é uma unidade que só existe para nós.** A cliente não
pensa "vou gastar um crédito", pensa "vou cobrir um casamento". E o crédito sai por
*evento criado* — então criar por engano custa, e um álbum permanente consome um crédito
para durar um ano.

**Evidência de mercado:** a Face Album usa exatamente créditos sem mensalidade — valida o
ADR-0012. Mas a Patrícia pediu o oposto (aluguel, recorrência), e isso segue em aberto.

| Modelo | A favor | Contra |
|---|---|---|
| Por evento (hoje) | simples, sem mensalidade | engano custa; álbum permanente não encaixa |
| Por convidado alcançado | cobra pelo valor entregue | imprevisível; ela quer o preço antes |
| Assinatura mensal | recorrência — o que ela pediu | contradiz o ADR-0012; há mês parado |
| Por foto entregue | escala com o uso | pune quem fotografa muito |
| **Limite de upload por pacote** (§3c) | conta o que custa; ela entende sem explicação | precisa de preço |
| **Grátis com nossa marca / pago com a dela** | a marca já é o gatilho de conversão | precisa de limite definido |

**Leitura:** os dois últimos combinam — o pacote é medido em fotos enviadas, e a marca
própria é o que faz virar pago. Nenhum profissional aceita marca de terceiro no trabalho
dele.

---

## 6. Branding

**O que já existe:** selo circular (Fóton + pontos de luz), preto e dourado champagne,
Jost + Instrument Sans, e uma escala tipográfica de 17 degraus com corpo em 17 px.

**A tensão real, e é ela que trava a decisão:** a Patrícia quer **discrição e elegância**
(casamento); a festa da Ana quer **energia**. Um sistema visual não grita as duas coisas.

**Direção que eu defendo:** a base é a da Patrícia — sóbria, escura, dourada, porque é
ela que paga hoje e é a que exige seriedade. A porta da festa **não muda o sistema**:
ganha movimento (o loop de vídeo) e escala maior. Energia por **movimento e tamanho**,
não por cor nova. Assim o produto não se parte em dois.

**O que falta:** cor com função (hoje o dourado é decoração; poderia significar "ao
vivo", "chegando", "sua"), e o logo.

---

## Ordem que eu defenderia

1. **Fila que sobrevive** — `filaFalhas` vive em memória: foto que não subiu **some se
   recarregar**. Viola o critério #2 do piloto. É o único item aqui que pode custar as
   fotos de um cliente.
2. **Miniatura como coluna** (ADR-0022) — 26× menos peso na rolagem, sem arquivo novo.
3. **Pré-cadastro com foto de referência** (§3b) — barato e muda o primeiro minuto do
   convidado.
4. **Fóton Festa** (§2) — o produto que ninguém atende.
5. **Chat em emoji** (§3d) — pequeno, e é a camada social entrando por uma porta
   pequena. Depois do piloto.
6. **Limite de upload** (§3c) — o crédito foi CORTADO em 2026-08-30 (ADR-0024): nesta
   fase tudo é grátis, com login. Antes de pôr limite, medir o COGS.
6. **Branding e a porta da festa** (§4/§6).
7. **Login por selfie global** (§3) — maior risco de privacidade. Por último.
