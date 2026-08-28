# GAUNTLET.md — Protocolo de Qualidade

> O ciclo abaixo (medir antes/depois, registrar em `docs/BENCHMARKS.md`, só aceitar com
> número) continua sendo seguido na prática, mesmo fora da estrutura de sprints S0-S8
> original (ver aviso em `docs/ROADMAP.md`). "Gate S0" no fim deste arquivo é histórico —
> o projeto já está em produção. O método continua valendo.
>
> Uma implementação **não** é concluída só porque funciona funcionalmente.
> Ela precisa satisfazer os critérios de **performance** e **confiabilidade** definidos para o sprint.

---

## O Ciclo

```
DISCOVER → DECOMPOSE → EXPERIMENT → BUILD → TEST → CRITIQUE → BENCHMARK → ACCEPT / REJECT → REFINE
                ▲                                                              │
                └──────────────────── (REJECT / REFINE) ──────────────────────┘
```

## As Fases

### 1. DISCOVER
Entender o problema e o desconhecido. Levantar perguntas empíricas. Tudo que não foi medido é marcado `UNKNOWN — REQUIRES EXPERIMENT`. Sem chutar capacidades (câmeras, GPU, rede).

### 2. DECOMPOSE
Quebrar em partes isoladas e mensuráveis, mapeadas aos componentes de `docs/ARCHITECTURE.md`. Definir contratos entre partes. Cada parte deve poder ser medida sozinha.

### 3. EXPERIMENT
Provas de conceito **descartáveis** para responder às incógnitas (ex.: como a T6 entrega imagem; latência de embedding na GPU). Código de experimento não é código de produção. Gera dados, não features.

### 4. BUILD
Implementar a versão mínima que respeita os contratos e a separação de componentes (CLAUDE.md §4). Sem dependência nova sem ADR.

### 5. TEST
Testes funcionais + de contrato + de falha. Rodar e **ler a saída**. "Passa" só com evidência.

### 6. CRITIQUE
Revisão crítica: acoplamento indevido? dependência injustificada? PII vazando? caminho de falha ignorado? decisão sem ADR? Quebra de princípio → volta.

### 7. BENCHMARK
Medir as latências relevantes e recursos, registrar em `docs/BENCHMARKS.md` com **P50/P95/P99** e throughput. Sem medição não há aceite.

### 8. ACCEPT / REJECT
Comparar contra o **alvo do sprint**:
- **ACCEPT** se: cumpre funcional **E** performance (P95) **E** confiabilidade definidos.
- **REJECT** caso contrário → volta para EXPERIMENT ou REFINE.

### 9. REFINE
Otimizar/corrigir **guiado por número** (nunca por palpite — CLAUDE.md §4.2). Reentrar no ciclo até ACCEPT.

## Definition of Done (por peça)

Uma peça só está "done" quando **todas** valem:

- [ ] Funciona (testes funcionais/contrato passam, com saída lida).
- [ ] Cumpre o alvo de **performance** do sprint (P95 medido e registrado).
- [ ] Cumpre os critérios de **confiabilidade** (cenários de falha do escopo tratados).
- [ ] Não introduz dependência/decisão sem **ADR**.
- [ ] Preserva a **separação de componentes** e os contratos.
- [ ] Sem **PII** em logs/URLs; privacidade respeitada.
- [ ] Resultados registrados em `docs/BENCHMARKS.md`; decisões em `docs/DECISIONS.md`.

## Gates do Projeto

- **Gate S0:** só se avança para construção de produto se o S0 provar (com números) um caminho plausível para **P95 < 10 s**. Se não, replanejar (hardware, engine, protocolo de câmera).
- Cada sprint do Roadmap tem seu próprio alvo de performance/confiabilidade que serve de critério de ACCEPT.
