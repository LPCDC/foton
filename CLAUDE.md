# CLAUDE.md — Foto na Hora

> Guia operacional para qualquer agente/IA ou humano trabalhando neste repositório.
> Este arquivo tem precedência sobre comportamento padrão. Leia antes de escrever qualquer linha.

---

## 1. Objetivo do Produto

**Foto na Hora** é um produto **SaaS** que se **vende a fotógrafos de eventos**.

Fluxo:

```
Fotógrafo clica (Canon R8 / T6)
   → foto sobe para a nuvem
   → tratamento (watermark + otimização)
   → detecção facial + embedding
   → match com a selfie do convidado
   → convidado recebe/baixa NA HORA, sem instalar nada
```

- **Sem hardware no evento.** O equipamento da fotógrafa é irrelevante — qualquer celular abre o evento.
- **Convidado:** escaneia 1 QR → tira uma selfie 1x → vê a galeria pessoal **enchendo ao vivo** → baixa.
- **Fotógrafo (cliente pagante):** abre o evento no painel, mostra o QR, fotografa. Tem que ser **turnkey** (o cliente-alvo não é técnico).

## 2. Requisito Central (SLA)

> **Do disparo (shutter) à foto no celular do convidado: P95 < 10 segundos.**

- A métrica que importa é **P95 end-to-end**, não a média.
- "Funciona" não basta. Só é aceito o que **cumpre o P95 e a confiabilidade** do sprint.
- Toda latência relevante é medida e registrada em `docs/BENCHMARKS.md`.

## 3. Arquitetura: SaaS em nuvem, turnkey, "na hora"

- Pipeline roda **na nuvem** (um serviço). Nada de appliance/edge no MVP.
- **Depende de Internet no local** — resolvido com **hotspot 4G/5G** (padrão do mercado de foto de evento). Trade-off aceito conscientemente.
- **Diferencial deliberado:** **tempo real / "na hora"** (feed pessoal ao vivo), não o reconhecimento facial em si (commodity no Brasil). Concorrentes (TIME&SPACE, Fotop, 4.events…) entregam "link pra acessar depois"; nós entregamos **durante a festa**.
- Edge/offline, NFC e edição por IA ficam **guardados para pós-MVP** — ver `docs/ROADMAP.md` e `docs/DECISIONS.md`.

## 4. Princípios de Engenharia (invioláveis)

1. **Não assumir capacidades das câmeras sem teste.** Como R8 e T6 entregam o JPEG (Wi-Fi/FTP nativo vs uploader tethered) e em quanto tempo é **empírico** (S0). Nada de chutar.
2. **Medir antes de otimizar.** Nenhuma otimização entra sem um número que a justifique.
3. **Não adicionar dependências sem justificativa.** Toda lib/serviço/modelo exige ADR em `docs/DECISIONS.md`. Preferir o menor stack que cumpra o SLA. **Simplicidade é requisito** — o produto é vendido a não-técnicos.
4. **Preservar a separação entre componentes.** Uploader, backend, facial, storage/CDN, app do convidado e painel comunicam por contratos explícitos. Cada estágio é substituível e mensurável isoladamente.
5. **Nada de decisão arquitetural silenciosa.** Mudou contrato/estágio/dependência → ADR.
6. **Marcar o desconhecido.** Informação não medida é escrita como `UNKNOWN — REQUIRES EXPERIMENT`. Proibido inventar números.

## 5. Regras de Testes

- Todo estágio tem teste isolado (unit/contrato) **e** medição de latência.
- Todo experimento do Gauntlet produz artefato reproduzível (script + dados + resultado em `docs/BENCHMARKS.md`).
- Conclusão de sprint = **funcional + performance (P95) + confiabilidade**, por evidência, não por afirmação.
- Confiabilidade inclui cenários de falha (Roadmap S7): Internet oscila, upload duplicado, arquivo parcial, câmera desconecta.
- Nunca declarar "passa" sem rodar e ler a saída.

## 6. Regras de Logging / Observabilidade

- Cada foto tem um **id de rastreio** que a acompanha por todos os estágios.
- Cada estágio loga: `photo_id`, `stage`, `t_in`, `t_out`, `latency_ms`, `status`.
- Logs estruturados (JSON) para calcular P50/P95/P99, throughput e **custo por evento**.
- Relógio monotônico para latência; wall-clock para correlação. Sem PII em logs (ver §7).

## 7. Segurança e Privacidade

> Biometria facial é dado sensível. O processamento é na nuvem, então o cuidado é ainda maior.

- **Selfies e embeddings dos convidados são efêmeros por padrão**, atados à sessão do evento; descartados ao fim, salvo consentimento explícito.
- **Consentimento do convidado** é parte do fluxo, não um detalhe. Base legal / retenção (LGPD) a definir com o operador → vira ADR quando decidido.
- Nenhuma PII (rostos, selfies, embeddings, nomes) em logs, URLs ou query strings.
- QR / sessão do convidado com escopo e expiração; não vira link público permanente.
- Se o facial for **API gerenciada** (ex.: Rekognition/Azure), avaliar onde os dados trafegam/ficam — entra na ADR-0009 e na de privacidade.
- Credenciais/segredos nunca no código; nunca commitados.

## 8. Protocolo Gauntlet (resumo)

Nenhuma peça é "concluída" só porque funciona. Ciclo obrigatório (detalhe em `docs/GAUNTLET.md`):

```
DISCOVER → DECOMPOSE → EXPERIMENT → BUILD → TEST → CRITIQUE → BENCHMARK → ACCEPT / REJECT → REFINE
```

- **BENCHMARK** e **ACCEPT/REJECT** são obrigatórios. Aceite exige cumprir performance do sprint **e** confiabilidade.

## 9. Estado Atual do Projeto

> Esta seção descreve o momento em que o projeto foi planejado (S0, pré-código). Está
> **desatualizada** e mantida aqui só como registro — **`BLUEPRINT.md` na raiz do repo é
> a fonte de verdade do estado atual** e deve ser lido primeiro em qualquer sessão nova.

- **Fase real (2026-08-28):** em **produção**, com cliente real (Patrícia, fotógrafa em
  Santos). Não é mais S0 — o app roda em `https://getfoton.duckdns.org`, repo público em
  `github.com/LPCDC/foton`. Próximo marco: `docs/PILOTO-1.md` (piloto real com câmera).
- Documentos vivos e atualizados: `BLUEPRINT.md` (estado geral) · `docs/DECISIONS.md`
  (ADRs, incluindo as que documentam o que mudou desde o S0) · `docs/BENCHMARKS.md`
  (medições reais em produção) · `docs/PILOTO-1.md` · `docs/TESTES.md` ·
  `docs/ROTEIRO-CAMERAS.md`.
- `docs/ARCHITECTURE.md`, `docs/ROADMAP.md` e a parte antiga de `docs/GAUNTLET.md` são
  **histórico do planejamento original** — cada um tem um aviso no topo explicando o quê
  mudou e apontando para o documento atual.

## 10. Ordem de Trabalho para o Agente

1. Nunca pule direto para código. Discovery → decisão registrada (ADR) → experimento → medição.
2. Faltou número → `UNKNOWN — REQUIRES EXPERIMENT` + propor o experimento.
3. Mudou arquitetura/dependência → ADR antes.
4. Reporte com honestidade (falhou = falhou, com a saída).
5. Pare e peça aprovação humana nos gates do Roadmap.
