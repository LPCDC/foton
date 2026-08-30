# Termo do Organizador — Acordo de Tratamento de Dados e Uso do Fóton

> **Status: MINUTA (2026-08-30).** Redigida com fundamento na LGPD (Lei 13.709/2018),
> no Marco Civil da Internet (Lei 12.965/2014) e na MP 2.200-2/2001 (validade do aceite
> eletrônico). É a condição nº 1 da decisão registrada em `docs/PRODUTO.md` §3b-2.
> **Antes do primeiro uso comercial fora da fase de teste, passar por advogado** —
> especialmente cláusulas 8 e 10. Existe em duas formas de aceite (cláusula 11):
> eletrônico dentro do app (escala) ou assinado (âncora, para GLAMON e contratos maiores).

---

## 1. Partes e definições

**FÓTON** — o serviço operado por [NOME/CPF-CNPJ do dono], doravante **Operador**.
**ORGANIZADOR** — a pessoa física ou jurídica que cria e administra um Evento ou Álbum
no Fóton (a fotógrafa contratada, a empresa dona do álbum, ou o anfitrião), doravante
**Controlador**.
**CONVIDADO** — o titular dos dados: quem escaneia o QR, tira selfie ou aparece nas fotos.
**EVENTO/ÁLBUM** — o espaço criado pelo Organizador, identificado por código próprio.

## 2. Objeto

O Fóton licencia ao Organizador o uso do serviço de entrega de fotos por
reconhecimento facial e, para isso, **trata dados pessoais por conta e ordem do
Organizador**, nos termos deste acordo.

## 3. Papéis na LGPD (Art. 5º, VI e VII)

3.1. O **Organizador é o Controlador**: decide a finalidade (entregar as fotos do seu
evento), possui a relação com os Convidados e responde pela base legal dos dados que
cadastra — exatamente como já responde pela lista de convidados do próprio evento.
3.2. O **Fóton é o Operador**: trata os dados exclusivamente para a finalidade acima,
conforme este acordo, e não usa os dados dos Convidados para nenhum outro fim
(não vende, não perfila, não treina modelos com rostos de Convidados).

## 4. Declarações do Organizador — a cláusula que sustenta tudo

O Organizador **declara e garante**, sob sua exclusiva responsabilidade:

a) que **possui base legal** (LGPD Arts. 7º e 11) para **todo dado pessoal que ele
próprio cadastrar** no Fóton — nomes, contatos, redes sociais e **fotos de referência
de pré-cadastro** — e que **informou os titulares** desse cadastro e da finalidade;
b) que tem o direito de fotografar e publicar as imagens do seu evento no espaço do
Fóton (autorização de uso de imagem dos fotografados, quando exigível);
c) que **não cadastrará dados de menores de 18 anos** nem criará eventos dirigidos a
público menor de idade — tratamento de dado sensível de criança/adolescente
(Art. 14 c/c Art. 11) está **fora do escopo do serviço** nesta fase;
d) que responde pelo conteúdo das fotos que enviar (direito autoral, imagem, licitude);
e) que, ao usar o pré-cadastro com identificação (nome/Instagram), entende que **o
vínculo rosto↔nome é feito por ele** e que a exibição desses dados aos demais
convidados **só ocorre se o próprio Convidado ligar** (padrão: desligado).

## 5. O que o Fóton garante ao Organizador e aos Convidados

a) **Selfie nunca armazenada** — convertida em vetor matemático e descartada;
b) **Biometria efêmera por padrão** — vetores apagados em 7 dias (configurável por
conta; retenção estendida, como em álbum permanente, exige o consentimento destacado
do titular colhido no próprio app); fotos expiram em 90 dias, salvo álbum permanente;
c) **Direito de saída do titular sem intermediário** — botão "Apagar minha selfie e
sair", visível na galeria do Convidado, com efeito imediato (Art. 18);
d) **Consentimento destacado do Convidado** colhido no app antes da selfie (Art. 11, I);
e) **Segurança**: HTTPS, senhas com hash irreversível, sem dado pessoal em logs ou URLs;
f) **Sub-operadores**: Oracle Cloud (infraestrutura, região São Paulo/Brasil). Inclusão
de novo sub-operador (ex.: Cloudflare, para armazenamento de fotos) será comunicada ao
Organizador com antecedência mínima de 15 dias;
g) **Incidente de segurança** com risco aos titulares: comunicação ao Organizador em
até **48 horas** do conhecimento, com o que se sabe e o que foi feito — para que o
Controlador cumpra o dever do Art. 48 junto à ANPD quando cabível.

## 6. Obrigações do Organizador durante o evento

a) Exibir o QR/aviso de que o evento usa reconhecimento facial para entrega de fotos;
b) Não compartilhar o código do evento fora do público do evento;
c) Atender pedidos de titulares que chegarem a ele (o app já dá a saída direta ao
Convidado; o que chegar por outra via é dever do Controlador, com apoio do Fóton).

## 7. Propriedade e licença

As fotos são do Organizador/fotógrafo. O Organizador concede ao Fóton licença
limitada, não exclusiva, apenas para hospedar, processar (redução, marca d'água,
reconhecimento) e entregar as fotos dentro do serviço.

## 8. Responsabilidade

8.1. O Organizador **indeniza e mantém indene** o Fóton por qualquer reclamação de
titular ou autoridade decorrente de dado que **ele** cadastrou sem base legal (cláusula 4).
8.2. O Fóton responde, nos limites da lei, por descumprimento das garantias da
cláusula 5. Fica excluído lucro cessante; a responsabilidade total do Operador
limita-se ao valor pago pelo Organizador nos 12 meses anteriores ao fato.
*(Teto simbólico durante a fase gratuita — revisar com advogado ao definir preço.)*

## 9. Vigência e término

Vale por evento/álbum criado, enquanto a conta existir. Ao término do evento ou
exclusão da conta, os dados seguem as regras de expiração da cláusula 5-b, e o
Organizador pode solicitar eliminação antecipada.

## 10. Foro e lei

Lei brasileira. Foro da comarca de **Santos/SP**, com renúncia a qualquer outro.

## 11. Aceite

**Forma eletrônica (padrão do app):** ao criar o primeiro evento, o Organizador marca
a caixa *"Li e aceito o Termo do Organizador"*, e o Fóton registra **data/hora, conta
e versão do termo aceita** (MP 2.200-2/2001, Art. 10, §2º — validade do aceite
eletrônico entre as partes). O texto integral fica permanentemente acessível no app.
**Forma assinada:** para contas empresa ou contratos de maior porte, este mesmo texto
assinado em duas vias (ou por assinatura eletrônica qualificada).

---

*Versão 1.0-minuta · registrada em `docs/DECISIONS.md` quando aceita pelo dono e
revisada por advogado. O que o app já cumpre por código está testado em
`tests/test_autorizacao.py` [24] (saída do titular) e documentado na ADR-0029.*
