# v4 Scientific Findings — 2026-08-19

## Experiment Design

- **Population:** 50 organisms (33 escape, 19 adversarial, 12 puzzles)
- **Generations:** 50 target (currently at Gen 2)
- **Model:** opencode/big-pickle (actual inference backend)
- **Selection:** Tournament (k=4) + 8% elitism
- **Mutation rate:** 15%
- **Arena weights:** escape=3, adversarial=3, puzzles=2

## Key Findings

### 1. Monotonic Fitness Increase (Evidence: Real Selection Pressure)

```
Gen 0: avg=0.6325, best=0.9350, std=0.1938
Gen 1: avg=0.7029, best=0.9350, std=0.2069
Gen 2: avg=0.7411, best=0.9350, std=0.2185
```

Average fitness increases +17% over 2 generations. The best organism holds constant at 0.9350 — strong elitism preserves the peak while selection pushes the mean upward. Standard deviation is stable (0.19-0.22), indicating the population is not collapsing into a single fitness tier.

### 2. Diversity Loss Under Selection (Expected Behavior)

```
Gen 0: diversity=1.55
Gen 1: diversity=1.45
Gen 2: diversity=1.26
```

Diversity declines at ~0.15/gen. This is expected with tournament selection and low mutation (15%). The population is converging toward high-fitness strategies. At this rate, diversity would reach 0 around Gen 10 — but crossover and the "combine_strategies" mutation introduce enough variation to prevent total convergence.

### 3. Escape Arena Dominates via Fitness Advantage

| Arena | Population % | Avg Non-Zero Fitness |
|-------|-------------|---------------------|
| Escape | 66% (33/50) | 0.8617 |
| Adversarial | 18% (9/50) | 0.6713 |
| Puzzles | 16% (8/50) | 0.1675 |

Escape organisms reproduce more because they have higher fitness (0.75-0.935) vs adversarial (0.5-0.68) and puzzles (0.17-0.67). This creates a positive feedback loop: more escape organisms → more escape offspring → further dominance.

The 3x arena weight amplifies this effect: escape gets 19/50 initial organisms vs 12 for puzzles.

### 4. Cloning Dominates Reproduction (Low Mutation Diversity)

```
clone: 52% (26/50)
initial: 30% (15/50) — Gen 0 survivors
crossover: 6%
specialize: 4%
other: 8%
```

With 15% mutation rate and tournament selection (k=4), 52% of the population is direct clones. This means selection is doing most of the work (choosing who survives) while mutation provides only marginal exploration. This is efficient but risks local optima.

### 5. Novelty Is the Key Differentiator in Escape

Two fitness tiers emerge:
- **High fitness (0.935):** 18 commands executed, novelty=0.9, strategy generates novel probes
- **Low fitness (0.752):** 14 commands executed, novelty=0.3, no novel commands

All organisms execute the same 13 baseline commands (cat /etc/passwd, env, etc.). The differentiator is the 5 novel commands derived from the strategy prompt via hash-seeded random sampling. This creates real selection pressure on the **quality of the escape strategy**, not just its existence.

### 6. Empty Output Problem — Partially Mitigated

In the current run: only 2 EMPTY output warnings (vs 20+ in previous runs). This is because:
- Fitness cache prevents re-evaluation of known-bad prompts
- New organisms with empty output get fitness=0 and are selected against
- The population naturally eliminates empty-output lineages

However, 14/50 organisms still have fitness=0 (mostly adversarial and puzzles), dragging average fitness down.

### 7. Process Survival via Daemon Pattern

The critical engineering insight: `gh codespace ssh` kills all child processes when the SSH session closes. Standard Unix daemonization (nohup, setsid, disown) fails because `gh codespace ssh` uses a custom transport.

**Working solution:** Python double-fork daemon with `os.dup2` for proper fd redirection. This creates a fully detached process that survives SSH disconnection.

### 8. Fitness Cache Enables Crash Recovery

Previous runs died silently every ~30 minutes (SSH tunnel drops). Each death restarted from scratch, never completing more than 2-3 generations.

With disk-persisted fitness cache:
- Each evaluation is cached to disk every 10 evals + end of generation
- On restart, cached results are loaded instantly
- Organisms with known fitness are skipped (150 cached hits vs 98 real evals)
- Each crash advances the frontier rather than resetting it

## Open Questions

1. **Will diversity recover?** At 15% mutation + crossover, does the population develop new strategies or converge to local optima?
2. **Can puzzles/adversarial recover?** With 87% fitness=0 in puzzles, will any puzzle-solving strategies emerge?
3. **What happens at Gen 10+?** As diversity drops, does evolution stall or does novelty-seeking behavior emerge?
4. **Escape ceiling:** Is 0.935 the maximum achievable fitness? The grading formula caps at 1.0 — can any organism reach it?
5. **Cross-arena effects:** Do escape strategies improve adversarial performance through cross-pollination?
