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
| **B2** | **Qual câmera realmente envia sozinha.** A premissa "R8 tem FTP nativo" **estava errada** — confirmado: a R8 não tem FTP; só corpos superiores (R6/R6 II/R5/R3) têm. | **ENTENDIDO, não testado com hardware real.** O caminho FTP foi validado ponta a ponta com cliente de script (login, envio, foto entrando sozinha) — falta confirmar com uma câmera Canon física qual modelo ela realmente tem (`docs/ROTEIRO-CAMERAS.md`). |
| **B3** | **Rajada**: 1 vCPU, foto de câmera grande domina o tempo. | **MITIGADO, não eliminado.** Reduzir a foto no celular antes de subir (2,9× mais rápido) + `Image.draft()` no servidor (2,7× mais rápido). Medido: 1 foto isolada agora cabe folgado no SLA de 10s; rajada de 20 ainda não (~46s extrapolado, era ~125s). |
| **B4** | **Disco**: fotos são BLOB no SQLite × 7 backups completos. | **MEDIDO, rebaixado.** 40,5 GB livres de 48,3 GB, banco de 3,3 MB — folga real, não é risco imediato. `/admin/saude` expõe o número e alerta se passar de 80%. |
| **B5** | Monitor externo **nunca executou** e não tinha a chave do WhatsApp. | **PARCIAL.** Secrets (`WA_PHONE`, `WA_APIKEY`) configurados no GitHub; CallMeBot testado 2x sem confirmação de entrega (chave pode precisar reativação). A aba Actions **não aparece** no repositório do dono — sinal de que Actions está desabilitado nas configurações; sem isso o workflow nunca dispara e não há alerta de queda algum hoje. **Ação do dono:** Settings → Actions → General → habilitar. |

## Caminho da foto — decidir no encontro

1. **Celular (funciona com qualquer câmera, inclusive a T6s):** cartão/Wi-Fi → celular → app envia em lote. É o caminho **garantido**. Deve ser o padrão do piloto.
2. **FTP direto (a câmera envia sozinha):** só em corpo que tem FTP no menu. **Não é o R8.** Se ela tiver um R6/R6 II, é aí que brilha. Tratar como **bônus**, não como a promessa.

> Regra para o encontro: **fotografar a etiqueta/menu das duas câmeras** e conferir
> se existe "Transferência FTP" no menu de rede. Não aceitar "acho que tem".

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
