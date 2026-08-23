# ROADMAP.md — Foto na Hora (SaaS em nuvem)

> Sprints. **S0 é exclusivamente viabilidade técnica.** Nenhum produto é construído antes de o S0 provar, com números, o caminho para **P95 < 10s** (sobre hotspot real), a escolha de facial e o custo por evento.
> Cada sprint só fecha pelo Gauntlet (`docs/GAUNTLET.md`): funcional + performance + confiabilidade.

---

## Estado atual
**Fase: S0 — Feasibility Gauntlet — PARCIAL / PAUSADO (2026-08-23).**
Compute provado sem câmera (EXP-04/05/06 ✅ — ver `docs/BENCHMARKS.md` §0): processar+reconhecer+casar < 0,6s/foto em CPU, facial 97,2%. **Pausado aguardando as câmeras R8/T6 + hotspot** para medir o risco restante (upload/rede, EXP-01/02/03/08). Sem código de produção.

---

## S0 — Feasibility Gauntlet  *(sprint atual)*
**Meta:** responder empiricamente e decidir se **P95 < 10s** é plausível **na nuvem sobre hotspot real**, qual engine facial, e o custo por evento.
Só **experimentos descartáveis** e **benchmarks** — nunca código de produção.

Incógnitas:
1. Como a **Canon R8** entrega o JPEG para a nuvem (Wi-Fi/FTP nativo vs uploader tethered)?
2. Como a **Canon T6** entrega o JPEG?
3. Qual o **throughput de upload** num hotspot 4G/5G real?
4. Quanto leva o **processamento** (watermark + otimização)?
5. **Facial gerenciado vs self-hosted:** melhor precisão × latência × **custo**?
6. Quanto leva **selfie → match** (caminho do convidado)?
7. Quantos **convidados simultâneos** com feed ao vivo?
8. **P95 < 10s** disparo→celular é atingível sobre hotspot real?
9. O sistema **aguenta a Internet oscilar** sem perder foto?
10. Qual o **custo por evento**?

**Pré-requisitos:** ADR-0001 (repo git), env `fotonahora` do LAB, contas de teste (nuvem + face API), hotspot 4G/5G.
**Gate de saída:** relatório + `BENCHMARKS.md` preenchido + **(a)** ACCEPT/REJECT do P95 + **(b)** decisão facial (ADR-0009) + **(c)** custo por evento.

## S1 — Upload Câmera → Nuvem
Uploader robusto para R8 e T6 (caminho vencedor do S0), com `photo_id`, dedup, fila com retry. **Alvo:** upload P95 no orçamento; sem perder disparos em rajada quando a rede oscila.

## S2 — Processamento + Watermark
Ingest → decode → derivadas → **watermark** → otimização, na nuvem. **Alvo:** processing latency no orçamento; watermark correto; robustez a arquivo parcial.

## S3 — Reconhecimento Facial
Detecção + embedding com a opção vencedora do S0 (gerenciado ou self-hosted). **Alvo:** detection+embedding P95 no orçamento; precisão mínima; custo sob controle.

## S4 — Match + Feed ao Vivo
Índice/match selfie→fotos e o **feed pessoal que enche ao vivo**. **Alvo:** match latency baixa; precisão/recall aceitáveis; feed atualiza "na hora".

## S5 — App do Convidado + Painel do Fotógrafo
Web app (QR → selfie → feed → download) e painel simples (criar evento, QR, uploads). Sessão com escopo/expiração; consentimento. **Alvo:** delivery no orçamento; **turnkey** para não-técnico.

## S6 — Performance End-to-End
Integração completa; medição **disparo → celular** sobre hotspot real; tuning por número. **Alvo:** **E2E P95 < 10s** sustentado sob carga + concorrência de convidados.

## S7 — Resiliência
Internet oscila, upload duplicado, arquivo corrompido/parcial, reprocessamento, fila segura, reentrega. **Alvo:** degradação graciosa, zero foto perdida.

## S8 — Empacotamento Comercial
Onboarding do fotógrafo, precificação (custo por evento → preço), operação por não-engenheiro, suporte, documentação. **Alvo:** vendável e operável num evento real.

---

### Pós-MVP (backlog de diferenciais)
Edge/offline para locais sem sinal · NFC/pulseira (registro/entrega por toque) · edição de cor por IA · associação por RFID/EXIF.

### Regras de avanço
Não pular sprint. Não iniciar produto antes do **Gate S0**. Mudança de stack/dependência entra por ADR. Aprovação humana ao fim de cada sprint.
