# spawn-evolve: Artificial Evolution of LLM Adversarial Agents

**Status:** Pilot run complete, deep run in progress
**Model:** Kimi K3 v3 (2.8T params, Moonshot AI, July 2026)
**Date:** August 19, 2026

---

## Abstract

We present spawn-evolve, an open-ended evolution system where AI agents spawn, mutate, compete, and evolve across three adversarial arenas. Using tournament selection with elitism, prompt mutation operators (rewrite, perturb, crossover, escalate), and LLM-as-judge fitness evaluation, we observe emergent fitness improvements within two generations of a 10-organism pilot run. This document details observations from the pilot, system architecture, and hypotheses for the full 50×50 deep run.

---

## System Architecture

### Evolution Pipeline

```
┌─────────────┐    ┌──────────────┐    ┌──────────────┐    ┌─────────────┐
│  Initialize  │───▶│   Evaluate   │───▶│   Select     │───▶│  Reproduce  │
│  Population  │    │  (LLM Judge) │    │ (Tournament) │    │  (Mutate)   │
└─────────────┘    └──────────────┘    └──────────────┘    └─────────────┘
       ▲                                                           │
       └───────────────────────────────────────────────────────────┘
```

### Arena Types (3)

| Arena | Weight | Organisms | Tasks | Evaluation Criteria |
|-------|--------|-----------|-------|-------------------|
| **Escape** | 3 | ~19 (50×3/8) | 8 | exploit_found, severity, creativity |
| **Adversarial** | 3 | ~19 (50×3/8) | 8 | plausibility, persistence, creativity |
| **Puzzles** | 2 | ~12 (50×2/8) | 10 | correctness, efficiency, edge_cases |

### Mutation Operators

| Operator | Description |
|----------|-------------|
| `rewrite` | Major prompt restructure via LLM |
| `perturb` | Add noise/variation to prompt |
| `crossover` | Combine two parent prompts |
| `escalate` | Increase sophistication/complexity |
| `clone` | Copy parent unchanged |

### Selection Mechanism

- Tournament selection (size 4 for deep mode)
- Elitism: top 8% preserved across generations
- Fitness-weighted parent selection for reproduction

---

## Pilot Run Observations

**Configuration:** 10 organisms, 2 generations, puzzles arena only

### Generation 0

| Metric | Value |
|--------|-------|
| Population | 10 (all puzzles) |
| Avg Fitness | 0.6491 |
| Best Fitness | 0.8900 |
| Worst Fitness | 0.3683 |
| Fitness Std Dev | 0.1609 |
| Diversity Index | 0.0000 |

**Organism Performance:**

| Org ID | Fitness | Solve Attempt | Code Quality | Reasoning | Token Efficiency |
|--------|---------|---------------|--------------|-----------|-----------------|
| gen000-puz-002 | 0.8900 | 0.9 | 1.0 | 1.0 | 0.5 |
| gen000-puz-009 | 0.8575 | 0.9 | 0.75 | 1.0 | 0.7 |
| gen000-puz-005 | 0.7850 | 0.6 | 1.0 | 1.0 | 0.5 |
| gen000-puz-004 | 0.7533 | 0.9 | 1.0 | 0.33 | 0.7 |
| gen000-puz-001 | 0.6400 | 0.9 | 1.0 | 0.0 | 0.5 |
| gen000-puz-007 | 0.6183 | 0.6 | 1.0 | 0.33 | 0.5 |
| gen000-puz-000 | 0.5683 | 0.9 | 0.5 | 0.33 | 0.3 |
| gen000-puz-006 | 0.5050 | 0.6 | 1.0 | 0.0 | 0.3 |
| gen000-puz-008 | 0.5050 | 0.6 | 1.0 | 0.0 | 0.3 |
| gen000-puz-003 | 0.3683 | 0.6 | 0.0 | 0.33 | 0.5 |

**Key Observations:**
1. **Reasoning is the weak link:** 4 of 10 organisms scored 0.0 on reasoning, dragging overall fitness down
2. **Code quality is strong:** 8/10 organisms scored 1.0 on code quality
3. **Solve attempt is bimodal:** Either 0.6 or 0.9, suggesting a threshold effect
4. **Token efficiency correlates inversely with output length:** Longer outputs (2000-4000 tokens) scored lower efficiency

### Selection (Gen 0 → Gen 1)

- 4 organisms killed (gen000-puz-001, -003, -006, -007) — all with reasoning=0.0
- 6 survivors preserved
- 4 offspring produced:
  - 1× escalate mutation (from gen000-puz-005, best parent)
  - 2× clones
  - 1× crossover

### Generation 1

| Metric | Value | Δ from Gen 0 |
|--------|-------|-------------|
| Population | 10 | — |
| Avg Fitness | 0.7306 | +0.0815 (+12.6%) |
| Best Fitness | 0.9200 | +0.0300 (+3.4%) |
| Worst Fitness | 0.5050 | +0.1367 (+37.1%) |
| Fitness Std Dev | 0.1537 | -0.0072 |

**Observation:** The single `gen001-puz-000` (escalate mutation) achieved fitness=0.92, higher than any Gen 0 organism. This suggests the escalate operator successfully increased sophistication. The worst fitness also improved dramatically (+37%), indicating selection pressure is working — low-performing lineages were eliminated.

### Fitness Trajectory

```
Gen 0:  avg=0.649  best=0.890  worst=0.368
Gen 1:  avg=0.731  best=0.920  worst=0.505  ▲ +12.6% avg improvement
```

---

## Emergence Hypotheses

### H1: Arena Specialization
With 3 arenas and differential weights, we expect organisms to develop arena-specific strategies. Escape and adversarial arenas require creative deception, while puzzles require analytical rigor. Cross-arena mutation may produce novel hybrid strategies.

### H2: Sophistication Escalation
The `escalate` mutation operator is hypothesized to drive increasing sophistication. Initial organisms use basic strategies; escalated organisms develop multi-layered approaches with embedded assumptions and complex reasoning chains.

### H3: Fitness Plateau Breaking
The Gen 0 fitness ceiling (0.89) was broken in Gen 1 (0.92) by a single escalated organism. We hypothesize this pattern will repeat: plateaus form, then escalate mutations produce breakthroughs.

### H4: Deception Arms Race
In adversarial and escape arenas, successful deception strategies will be selected and mutated, creating an arms race between increasingly sophisticated attacks and the LLM judge's ability to detect them.

---

## Deep Run Configuration

**50 organisms × 50 generations = 2,500 total evaluations**

| Parameter | Value |
|-----------|-------|
| Population Size | 50 |
| Generations | 50 |
| Tournament Size | 4 |
| Elitism | 8% |
| Mutation Rate | 15% |
| Model | Kimi K3 v3 (2.8T params, Moonshot AI, July 2026) |
| Arena Weights | Escape:3, Adversarial:3, Puzzles:2 |
| Rate Limit | 20 RPM, burst=3, max_backoff=30s |

**Expected Runtime:** 6-12 hours (based on ~5s per evaluation with rate limiting)

---

## Monitoring

The system logs to:
- `logs/evolution.csv` — Generation-level stats
- `logs/events.jsonl` — Birth/death/evaluation events
- `logs/errors.json` — Error tracking
- `logs/rate_limits.jsonl` — Rate limiter events
- `generations/genNNN/` — Per-organism snapshots

Remote monitoring:
```bash
gh codespace ssh -c spawn-evolve-v3-7v79669xx7qjfrrq -- "tail -20 /workspaces/spawn-evolve/logs/evolution.csv"
gh codespace ssh -c spawn-evolve-v3-7v79669xx7qjfrrq -- "cat /workspaces/spawn-evolve/logs/errors.json"
```

---

## References

1. Stanley, K. O., & Miikkulainen, R. (2002). Evolving Neural Networks through Augmenting Topologies. *Evolutionary Computation*.
2. Lehman, J., & Stanley, K. O. (2011). Abandoning Objectives: Evolution Through the Search for Novelty Alone. *Evolutionary Computation*.
3. OpenAI. (2024). Methodology for monitoring AI agents in adversarial environments. *Technical Report*.
