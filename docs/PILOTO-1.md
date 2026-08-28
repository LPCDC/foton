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

| | Bloqueador | Estado |
|---|---|---|
| **B1** | **Chrome mostra "Site perigoso"** no celular do convidado. O certificado está válido (TLS 1.3) — é reputação do domínio `duckdns.org`, que é muito usado em golpe. **Mata o piloto sozinho:** ninguém escaneia um QR que abre um alerta vermelho. Correção: **domínio próprio** + certificado. | ABERTO — decisão do dono (comprar domínio) |
| **B2** | **Qual câmera realmente envia sozinha.** A premissa "R8 tem FTP nativo" **está errada** (ver `DECISIONS.md`). Confirmar os modelos exatos no encontro. | ABERTO — encontro com a fotógrafa |
| **B3** | **Rajada**: 4,8 s por foto quando chegam juntas, 1 vCPU. 20 fotos = ~1,5 min. Mitigação mínima: reduzir a foto no celular antes de subir. | ABERTO |
| **B4** | **Disco**: fotos são BLOB no SQLite × 7 backups completos. Um evento de 800 fotos pode consumir ~8 GB. Medir o disco livre e limpar antes. | ABERTO — medir |
| **B5** | Monitor externo **nunca executou** (workflow ativo, 0 execuções) e não tem a chave do WhatsApp. Se cair no evento, ninguém avisa. | ABERTO |

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

## Decisões do dono, em aberto

1. **Domínio próprio** (B1) — qual nome, e comprar.
2. **Preço do piloto** — a proposta é que exista dinheiro real, mesmo simbólico.
3. **Proposta de sociedade da fotógrafa** — ver `BLUEPRINT.md` §10.
