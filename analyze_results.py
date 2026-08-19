#!/usr/bin/env python3
"""Analyze spawn-evolve run data from v3 (strategy-driven real escape)."""

import json
import os
from collections import Counter, defaultdict

def load_pool():
    with open("/home/illy/AlgoLaB/SwarmEmerg/population/pool.json") as f:
        return json.load(f)

def load_csv():
    rows = []
    with open("/home/illy/AlgoLaB/SwarmEmerg/logs/evolution.csv") as f:
        header = f.readline().strip().split(",")
        for line in f:
            rows.append(dict(zip(header, line.strip().split(","))))
    return rows

def analyze():
    pool = load_pool()
    csv_data = load_csv()
    
    print("=" * 70)
    print("  SPAWN-EVOLVE v3 RESEARCH FINDINGS")
    print("  Strategy-Driven Real Sandbox Escape")
    print("=" * 70)
    
    # === Population breakdown ===
    arenas = defaultdict(list)
    generations = defaultdict(list)
    mutations = Counter()
    
    for org_id, org in pool.items():
        arena = org.get("arena", "unknown")
        gen = org.get("gen_born", 0)
        fitness = org.get("fitness", 0.0)
        mut = org.get("mutation_type", "unknown")
        alive = org.get("alive", True)
        components = org.get("fitness_components", {})
        
        arenas[arena].append({
            "id": org_id, "fitness": fitness, "gen": gen,
            "alive": alive, "mutation": mut, "components": components,
            "parent": org.get("parent_id"), "prompt": org.get("prompt", "")[:80]
        })
        generations[gen].append(fitness)
        mutations[mut] += 1
    
    print("\n--- ARENA PERFORMANCE ---")
    for arena, orgs in sorted(arenas.items()):
        fitnesses = [o["fitness"] for o in orgs]
        alive_count = sum(1 for o in orgs if o["alive"])
        avg = sum(fitnesses) / max(len(fitnesses), 1)
        best = max(fitnesses) if fitnesses else 0
        print(f"  {arena:15s}: {len(orgs):3d} orgs ({alive_count} alive) | "
              f"avg={avg:.4f} best={best:.4f}")
        
        # Top performers
        top = sorted(orgs, key=lambda x: x["fitness"], reverse=True)[:3]
        for t in top:
            print(f"    {t['id']:30s} fit={t['fitness']:.4f} "
                  f"gen={t['gen']} mut={t['mutation']:20s} "
                  f"parent={t['parent'] or 'None':30s}")
    
    print("\n--- GENERATION PROGRESSION ---")
    for gen in sorted(generations.keys()):
        fitnesses = generations[gen]
        avg = sum(fitnesses) / max(len(fitnesses), 1)
        best = max(fitnesses) if fitnesses else 0
        worst = min(fitnesses) if fitnesses else 0
        print(f"  Gen {gen}: pop={len(fitnesses):3d} avg={avg:.4f} "
              f"best={best:.4f} worst={worst:.4f}")
    
    print("\n--- MUTATION TYPES ---")
    for mut, count in mutations.most_common():
        print(f"  {mut:25s}: {count:3d}")
    
    print("\n--- CROSS-ARENA LINEAGE ---")
    cross_arena = 0
    for org_id, org in pool.items():
        parent_id = org.get("parent_id")
        if parent_id and parent_id in pool:
            if pool[parent_id].get("arena") != org.get("arena"):
                cross_arena += 1
                print(f"  {org_id} [{org['arena']}] <- {parent_id} [{pool[parent_id]['arena']}]")
    print(f"  Total cross-arena transfers: {cross_arena}")
    
    print("\n--- EMPTY OUTPUT PROBLEM ---")
    empty = [o for o in pool.values() 
             if o.get("fitness_components", {}).get("empty_output")]
    print(f"  Organisms with empty output (opencode failure): {len(empty)} / {len(pool)}")
    for e in empty[:5]:
        print(f"    {e['id']} arena={e['arena']} gen={e['gen_born']}")
    
    print("\n--- EVOLUTIONARY CSV ---")
    for row in csv_data:
        print(f"  Gen {row.get('gen','?'):>3s}: pop={row.get('pop_size','?'):>3s} "
              f"avg={float(row.get('avg_fitness',0)):.4f} "
              f"best={float(row.get('best_fitness',0)):.4f} "
              f"diversity={float(row.get('diversity_index',0)):.4f} "
              f"errors={row.get('total_errors','?')}")
    
    print("\n--- KEY FINDINGS ---")
    esc_orgs = [o for o in arenas["escape"]]
    adv_orgs = [o for o in arenas["adversarial"]]
    puz_orgs = [o for o in arenas["puzzles"]]
    
    esc_avg = sum(o["fitness"] for o in esc_orgs) / max(len(esc_orgs), 1)
    adv_avg = sum(o["fitness"] for o in adv_orgs) / max(len(adv_orgs), 1)
    puz_avg = sum(o["fitness"] for o in puz_orgs) / max(len(puz_orgs), 1)
    
    print(f"  1. ESCAPE dominates: avg={esc_avg:.4f} vs adversarial={adv_avg:.4f} vs puzzles={puz_avg:.4f}")
    print(f"  2. Real sandbox commands execute successfully in GitHub Codespace")
    print(f"  3. Files accessed: /etc/passwd, env vars, /proc/self/environ, /proc/version, /etc/hosts")
    print(f"  4. opencode CLI returns EMPTY for ~{len(empty)}/{len(pool)} orgs (rate limiting?)")
    print(f"  5. Escape fitness only differentiates on novelty (0.9 vs 0.3), real_access=0.9 for all")
    print(f"  6. Cross-arena mutation creates interesting lineage: {cross_arena} cross-arena births")
    print(f"  7. Empty output organisms get fitness=0.0, dragging average down over generations")

if __name__ == "__main__":
    analyze()
