# Fóton — o produto, e o que ainda não foi decidido

> Onde moram as ideias que o dono trouxe e que ainda **não viraram código**.
> Nada aqui está implementado. Cada item tem: o que é, o que muda, o que custa, e o
> que precisa ser decidido. Aberto em 2026-08-30.
>
> `BLUEPRINT.md` = o que existe. `docs/DECISIONS.md` = o que já foi decidido.
> **Este arquivo = o que está na mesa.**

---

## 1. Os três públicos, e as três portas

Descoberta importante desta fase: **não são três produtos — é um motor com três portas.**
O motor (foto → rosto → entrega certa) é o mesmo. O que muda é a casca e o vocabulário.

| Quem | O que é para ela | Vocabulário | Estado |
|---|---|---|---|
| **Patrícia** — fotógrafa profissional | ferramenta de trabalho: evento começa, termina, convidados novos | evento, convidado | **no ar** |
| **GLAMON** — empresa, álbum interno | acervo permanente, mesmas pessoas toda semana, login compartilhado | álbum, equipe | **no ar** (ADR-0021) |
| **Ana** — a pessoa comum no próprio rolê | ela é fotógrafa **e** convidada ao mesmo tempo | festa | **§2, não feito** |

**Por que isso importa:** a porta da Ana é a única que ninguém no Brasil atende. Face
Album, Fotix, Mirino, 4.events e TIME&SPACE são todos ferramenta de fotógrafo ou módulo
de plataforma de evento. Ninguém serve quem fotografa o próprio rolê. É consumo, é
viral, e é o freemium que já estava no BLUEPRINT §9c.

---

## 2. FÓTON FESTA — todo mundo é fotógrafo e convidado

**A ideia:** numa festa, todos estão interligados. Qualquer um fotografa, qualquer um
recebe as fotos em que aparece. **Só o criador (quem contratou) apaga.** Com limite por
IP e por festa.

**Por que é forte:** hoje o app tem um lado que manda e outro que recebe. Numa festa de
amigos essa divisão é artificial — a mesma pessoa faz as duas coisas. E o volume de
fotos multiplica sem custo de aquisição: cada convidado vira uma câmera.

**O que muda de verdade no código:**
- Convidado passa a poder **enviar** (hoje `/ingest` exige conta de fotógrafo).
- Papéis por evento: `dono` (apaga tudo) · `participante` (envia e recebe, não apaga).
- Hoje o modelo é *conta → eventos*. Passaria a ser *evento → participantes*.

**O limite por IP: razoável, com uma ressalva séria.** Limite por IP protege contra
alguém despejar mil fotos. Mas **numa festa todo mundo está no mesmo Wi-Fi, e portanto
no mesmo IP** — um limite por IP puniria a festa inteira por causa de uma pessoa. O
limite tem que ser **por participante** (o id que a selfie já cria), com o IP só como
segunda barreira contra abuso em massa.

**Decidir:** quantas fotos por participante? Participante pode apagar a **própria** foto?
Se alguém sai da festa, as fotos dele ficam? Quem responde por conteúdo impróprio?

---

## 3. Login por selfie ("se você já foi fotografado pelo Fóton")

**A ideia:** a pessoa entra com **o rosto** + uma senha que recebe por e-mail, sem
precisar do código do evento — porque quem criou o evento já mandou fotos das pessoas
que provavelmente estarão lá.

**O que é bom:** mata a fricção do código. A pessoa chega, faz a selfie e já está dentro.

**O que impede hoje, e é grave:**

1. **A biometria é apagada em 7 dias** (ADR-0005, retenção LGPD). Login por rosto exige
   guardar o vetor facial **por tempo indeterminado**, ligado a uma identidade. Isso
   **inverte a promessa central** do produto — hoje a selfie é descartada e o vetor é
   efêmero. É a decisão mais séria desta lista.
2. **Rosto não é senha.** Rosto não se troca quando vaza. Por isso ele **nunca** pode
   ser o único fator — o e-mail + senha que você citou não é detalhe, é o que torna a
   ideia defensável.
3. **Não temos e-mail.** O app não envia e-mail hoje; entra dependência nova (ADR).
4. **Falso positivo tem consequência diferente.** Errar o match hoje entrega uma foto
   errada. Errando no *login*, a pessoa entra **na conta de outra**. O limiar de 0,25
   que serve para agrupar fotos **não serve** para autenticar.

**Versão defensável, se você quiser seguir:** a selfie **sugere** os eventos em que a
pessoa aparece, e o acesso só se confirma com o segundo fator. O rosto encontra; a
senha autoriza. E com consentimento explícito e separado para guardar a biometria além
dos 7 dias.

---

## 4. Entrada coletiva — o botão da festa

**O pedido:** uma terceira forma de entrar, com botão **maior e diferente**, com um GIF
animado de ~10 s de uma festa entre jovens ao fundo.

**A ideia de dar peso visual diferente à porta da festa está certa** — é a porta do
produto de consumo, e ela não deveria parecer irmã das outras duas.

**Sobre o GIF, com honestidade técnica:**
- **GIF de 10 s pesa 3 a 8 MB** e não tem compressão de vídeo. Na landing, num hotspot
  4G de festa, isso é a primeira coisa que a pessoa baixa — e o produto inteiro depende
  daquele 4G. Um **MP4/WebM mudo em loop** faz a mesma coisa com **~300 KB**.
- **Procedência importa.** Não vou pegar um GIF de banco de imagem sem licença clara nem
  gerar gente que não existe e apresentar como festa real. As fotos que já estão no app
  são Openverse/CC-BY, creditadas em `assets/CREDITS.txt` — o mesmo padrão vale aqui.
- **O melhor material seria seu.** Você tem 89 fotos do GLAMON e vai ter as da festa de
  hoje. Um loop curto feito com material próprio é mais verdadeiro que qualquer banco de
  imagem — e resolve a licença.

**Decidir:** MP4 curto em vez de GIF? Material próprio ou licenciado?

---

## 5. Créditos — o modelo que não te agrada

Concordo que incomoda, e dá para nomear o porquê: **crédito é uma unidade que só existe
para nós.** A cliente não pensa "vou gastar um crédito", pensa "vou cobrir um casamento".
E hoje o crédito sai por **evento criado** — então criar um evento por engano custa
dinheiro, e um álbum permanente (GLAMON) consome um crédito para durar um ano.

**A evidência de mercado:** a Face Album usa exatamente créditos sem mensalidade. Isso
valida o ADR-0012. Mas a Patrícia pediu o oposto — aluguel, recorrência — e isso está em
aberto desde o áudio dela.

**Alternativas, com o que cada uma quebra:**

| Modelo | A favor | Contra |
|---|---|---|
| **Por evento** (hoje) | simples, sem mensalidade — é o que a cliente disse querer | crédito por engano custa; álbum permanente não encaixa |
| **Por convidado alcançado** | cobra pelo valor entregue, não pelo esforço | imprevisível para ela; ela quer saber o preço antes |
| **Assinatura mensal** | receita recorrente — o que a Patrícia pediu | contradiz o ADR-0012; fotógrafo de evento tem mês parado |
| **Por foto entregue** | escala com o uso real | pune quem fotografa muito; é o oposto do produto |
| **Grátis com nossa marca / pago com a dela** | a marca é o gatilho de conversão já identificado | precisa de limite de armazenamento definido |

**Minha leitura:** o último é o mais forte, porque a marca d'água já é o gatilho real —
nenhum profissional aceita marca de terceiro no trabalho dele. Mas isso é **decisão de
negócio, não de engenharia**, e depende do preço, que continua sem medição (EXP-10).

---

## 6. Branding — o que está e o que falta

**O que já tem:** selo circular do Fóton (Fóton + pontos de luz), preto e dourado
champagne, tipografia Jost + Instrument Sans, e agora uma **escala tipográfica de 17
degraus** com corpo em 17 px (a disciplina Bauhaus que você pediu: poucos passos,
decisivos).

**O que falta, e por que não fiz sozinho:**
- **Sistema de cor com função.** Bauhaus não é só tamanho — é cor que **significa**.
  Hoje o dourado é decoração; poderia ser o estado "ao vivo", "chegando", "seu".
- **O logo.** Mudar a marca do seu ganha-pão sem referência sua seria chute.
- **As três portas com personalidade própria** — hoje são três cartões iguais.

**O que eu preciso de você:** 2 ou 3 referências de apps que você acha que têm a cara
certa. Com isso eu trabalho com precisão; sem isso eu adivinho.

---

## Ordem que eu defenderia

1. **Fila que sobrevive** — `filaFalhas` vive em memória: foto que não subiu **some se
   recarregar**. Viola o critério #2 do piloto ("zero foto perdida"). É o único item
   desta lista que pode fazer você passar vergonha amanhã.
2. **Miniatura como coluna** (ADR-0022) — 26× menos peso na rolagem, sem arquivo novo.
3. **Fóton Festa** (§2) — o produto que ninguém atende.
4. **Modelo comercial** (§5) — decisão sua; a engenharia é pequena.
5. **Branding e a porta da festa** (§4, §6) — depende das suas referências.
6. **Login por selfie** (§3) — o de maior risco de privacidade. Por último, e só com a
   base legal resolvida.
