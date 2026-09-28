# WHATSAPP.md — entregar a foto no WhatsApp do convidado

> Pesquisa de 2026-09-22 na documentação da Meta. **Nada implementado.** Fontes no fim.

## A descoberta que muda a conta

A Meta cobra **por mensagem desde 01/07/2025**, e a regra que nos interessa é esta:

- Quando **o convidado manda a primeira mensagem**, abre uma **janela de atendimento de 24 h**.
- Dentro dela, **mensagem comum (inclusive imagem) é gratuita**. Só modelo de mensagem
  ("template") entregue é cobrado.
- **Limite de envio não se aplica dentro da janela.** O limite de 250 destinatários por dia de
  uma conta nova vale para mensagens que a empresa inicia.
- Imagem: JPEG ou PNG, **até 5 MB**.

Uma festa dura menos de 24 h. Então **o evento inteiro cabe na janela gratuita**.

## Desenho proposto

1. Depois da selfie, o convidado vê **"Receber minhas fotos no WhatsApp"**.
2. O botão abre o WhatsApp dele com uma mensagem pronta para o número do Fóton, contendo um
   **código aleatório** (nunca nome, telefone ou id do convidado no texto visível).
3. O envio dele **é o consentimento** e **abre a janela**.
4. Durante a festa, cada entrega vai para o WhatsApp, sem custo.
5. Passadas 24 h, no máximo **uma** mensagem paga com o link da galeria.

## A decisão de formato, que é do dono

**Foto enviada não volta.** O "Não sou eu" (ADR-0037) não apaga nada do celular de ninguém.
Como a regra da casa é "foto errada é pior que foto perdida":

| Modo | O que manda | Risco |
|---|---|---|
| **Aviso e link** (recomendado para a v1) | "chegaram 3 fotos suas" + link | erro ainda é reversível: a foto sai da galeria |
| **Foto no WhatsApp** | a imagem | irreversível; só depois de medir entrega errada em evento real |

## O que falta, e de quem é

| Item | Quem |
|---|---|
| Conta empresarial na Meta, conta WhatsApp Business, aceitar termos | **dono** (criar conta e aceitar termos não é tarefa do agente) |
| Número dedicado | **dono** |
| Rota que recebe a mensagem (webhook), fila de envio com repetição, testes, ADR | agente. `httpx` já é dependência; **nenhuma dependência nova** |
| HTTPS válido | já resolvido em 2026-09-22 (certificado até 21/12) |
| Tempo do servidor até o celular pelo WhatsApp | `UNKNOWN — REQUIRES EXPERIMENT` |
| Custo por mensagem em reais, e se o CNPJ se enquadra | `UNKNOWN` |

## Antes de construir (orientação do dono, 2026-09-28)

Nada de código até estes itens terem resposta. A ordem importa:

1. **Testar sem construir, no evento real** (`docs/PILOTO-1.md`): quem deixou contato
   recebe o link da galeria pelo WhatsApp **da própria fotógrafa**. Se ninguém volta pela
   mensagem, a integração com a Meta não é a próxima coisa a fazer.
2. **O que só o dono pode fazer:** conta empresarial na Meta, número dedicado, aceitar os
   termos, dizer se o CNPJ serve. Sem isso, não há o que integrar.
3. **Custo em reais:** dentro da janela de 24 h, mensagem comum é grátis; fora dela, só
   modelo pago. O valor por mensagem para o nosso caso é `UNKNOWN` até a conta existir.
4. **Formato:** aviso com link (reversível) ou a foto (irreversível). Recomendação
   mantida: aviso com link na v1.
5. **Só então** a rota que recebe mensagens e a fila de envio, sem abstração para "outros
   canais" que ninguém pediu.

## LGPD

As fotos passam por servidores da Meta: **transferência internacional**, como o backup no R2.
Entra na política de privacidade e na ADR de privacidade. O consentimento é o gesto do
convidado, e precisa ser registrado com data e hora, junto do código usado.

## Fontes (2026-09-22)

- [Preços da plataforma](https://developers.facebook.com/docs/whatsapp/pricing)
- [Mensagens com imagem](https://developers.facebook.com/docs/whatsapp/cloud-api/messages/image-messages)
- [Limites de envio](https://developers.facebook.com/docs/whatsapp/messaging-limits)
- [Visão geral da Cloud API](https://developers.facebook.com/docs/whatsapp/cloud-api/overview)
