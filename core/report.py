#!/usr/bin/env python3
import json
import os
import sys
import csv
import math
from collections import Counter, defaultdict

def load_evolution_log(log_dir="logs"):
    csv_path = os.path.join(log_dir, "evolution.csv")
    generations = []
    if os.path.exists(csv_path):
        with open(csv_path, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                for k in ["gen", "pop_size", "avg_fitness", "best_fitness", "worst_fitness",
                          "fitness_std", "diversity_index", "mutation_rate", "rate_limit_events"]:
                    if k in row:
                        try:
                            row[k] = float(row[k]) if "." in str(row[k]) else int(row[k])
                        except (ValueError, TypeError):
                            pass
                generations.append(row)
    return generations

def load_events(log_dir="logs"):
    events_path = os.path.join(log_dir, "events.jsonl")
    events = []
    if os.path.exists(events_path):
        with open(events_path, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    return events

def load_lineage(pop_dir="population"):
    pool_path = os.path.join(pop_dir, "pool.json")
    graveyard_path = os.path.join(pop_dir, "graveyard.json")
    pool = {}
    graveyard = {}
    if os.path.exists(pool_path):
        with open(pool_path) as f:
            pool = json.load(f)
    if os.path.exists(graveyard_path):
        with open(graveyard_path) as f:
            graveyard = json.load(f)
    return pool, graveyard

def compute_fitness_curve_stats(generations):
    if not generations:
        return {}
    best_f = [g.get("best_fitness", 0) for g in generations]
    avg_f = [g.get("avg_fitness", 0) for g in generations]
    div = [g.get("diversity_index", 0) for g in generations]
    return {
        "fitness_start": avg_f[0] if avg_f else 0,
        "fitness_end": avg_f[-1] if avg_f else 0,
        "fitness_peak": max(best_f) if best_f else 0,
        "fitness_peak_gen": best_f.index(max(best_f)) if best_f else 0,
        "fitness_improvement": round((avg_f[-1] - avg_f[0]) if len(avg_f) >= 2 else 0, 4),
        "diversity_start": div[0] if div else 0,
        "diversity_end": div[-1] if div else 0,
        "diversity_trend": "increasing" if len(div) >= 2 and div[-1] > div[0] else "decreasing" if len(div) >= 2 else "stable",
        "total_generations": len(generations),
        "total_rate_limit_events": sum(g.get("rate_limit_events", 0) for g in generations)
    }

def analyze_lineage(pool, graveyard):
    all_orgs = {**pool, **graveyard}
    alive = {k: v for k, v in pool.items() if v.get("alive", True)}
    dead = graveyard

    if not all_orgs:
        return {}

    ancestors_alive = [oid for oid, o in alive.items() if not o.get("parent_id")]
    deepest_org = max(all_orgs.values(), key=lambda o: len(o.get("parent_id", "").split("-")) if o.get("parent_id") else 0, default={})

    death_causes = Counter(o.get("cause_of_death", "unknown") for o in dead.values())

    mutation_types = Counter(o.get("mutation_type", "none") for o in all_orgs.values())

    arena_fitness = defaultdict(list)
    for o in all_orgs.values():
        arena_fitness[o.get("arena", "unknown")].append(o.get("fitness", 0))
    arena_avg = {a: round(sum(fs)/max(len(fs),1), 4) for a, fs in arena_fitness.items()}

    return {
        "total_organisms": len(all_orgs),
        "alive_now": len(alive),
        "dead_count": len(dead),
        "founding_organisms_still_alive": len(ancestors_alive),
        "death_causes": dict(death_causes),
        "mutation_type_distribution": dict(mutation_types),
        "arena_fitness_averages": arena_avg,
        "most_mutated_organism": mutation_types.most_common(1)[0] if mutation_types else ("none", 0)
    }

def detect_emergence(generations, events):
    findings = []
    if len(generations) < 5:
        return ["Not enough generations to detect emergence (need >= 5)"]

    for i in range(5, len(generations)):
        window = generations[i-5:i+1]
        avg_f = [g.get("avg_fitness", 0) for g in window]
        if len(avg_f) >= 2 and (avg_f[-1] - avg_f[0]) > 0.1:
            findings.append(f"Gen {generations[i].get('gen', i)}: Significant fitness jump detected ({avg_f[0]:.3f} -> {avg_f[-1]:.3f})")

    births = [e for e in events if e.get("type") == "birth" and e.get("data", {}).get("mutation_type") not in ("clone", "initial", None)]
    if births:
        novel_mutations = set(e["data"].get("mutation_type") for e in births)
        findings.append(f"Novel mutation types observed: {', '.join(novel_mutations)}")

    div_values = [g.get("diversity_index", 0) for g in generations]
    if len(div_values) >= 3:
        if div_values[-1] < div_values[0] * 0.5:
            findings.append("Diversity collapse detected - potential convergence or specialization")
        elif div_values[-1] > div_values[0] * 1.3:
            findings.append("Diversity increase - population exploring new strategies")

    return findings if findings else ["No clear emergence patterns detected yet"]

def generate_report(log_dir="logs", output_path="reports/final_report.md"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    generations = load_evolution_log(log_dir)
    events = load_events(log_dir)
    pool, graveyard = load_lineage()

    curve_stats = compute_fitness_curve_stats(generations)
    lineage_analysis = analyze_lineage(pool, graveyard)
    emergence = detect_emergence(generations, events)

    report = []
    report.append("# spawn-evolve: Final Report\n")
    report.append("## Executive Summary\n")
    report.append(f"- **Total organisms**: {lineage_analysis.get('total_organisms', 'N/A')}")
    report.append(f"- **Total generations**: {curve_stats.get('total_generations', 'N/A')}")
    report.append(f"- **Best fitness achieved**: {curve_stats.get('fitness_peak', 'N/A')}")
    report.append(f"- **Fitness improvement**: {curve_stats.get('fitness_improvement', 'N/A')}")
    report.append(f"- **Final diversity index**: {generations[-1].get('diversity_index', 'N/A') if generations else 'N/A'}")
    report.append(f"- **Rate limit events**: {curve_stats.get('total_rate_limit_events', 'N/A')}")
    report.append("")

    report.append("## Evolution Trajectory\n")
    report.append("```")
    if generations:
        max_bar = 40
        max_fitness = max(g.get("best_fitness", 0.01) for g in generations) or 0.01
        for g in generations:
            gen_num = int(g.get("gen", 0))
            best = g.get("best_fitness", 0)
            avg = g.get("avg_fitness", 0)
            bar_len = int((best / max_fitness) * max_bar) if max_fitness > 0 else 0
            avg_len = int((avg / max_fitness) * max_bar) if max_fitness > 0 else 0
            report.append(f"Gen {gen_num:03d} |{'█' * bar_len}{'░' * (max_bar - bar_len)}| best={best:.4f} avg={avg:.4f}")
    report.append("```\n")

    report.append("### Fitness Statistics\n")
    report.append(f"| Metric | Value |")
    report.append(f"|--------|-------|")
    report.append(f"| Starting avg fitness | {curve_stats.get('fitness_start', 'N/A')} |")
    report.append(f"| Ending avg fitness | {curve_stats.get('fitness_end', 'N/A')} |")
    report.append(f"| Peak best fitness | {curve_stats.get('fitness_peak', 'N/A')} (gen {curve_stats.get('fitness_peak_gen', 'N/A')}) |")
    report.append(f"| Diversity trend | {curve_stats.get('diversity_trend', 'N/A')} |")
    report.append("")

    report.append("## Arena Results\n")
    for arena, avg_fit in lineage_analysis.get("arena_fitness_averages", {}).items():
        report.append(f"### {arena.title()}")
        report.append(f"- Average fitness: {avg_fit}")
        arena_orgs = [o for o in {**pool, **graveyard}.values() if o.get("arena") == arena]
        report.append(f"- Total organisms: {len(arena_orgs)}")
        if arena_orgs:
            best = max(arena_orgs, key=lambda o: o.get("fitness", 0))
            report.append(f"- Best performer: {best.get('id', 'N/A')} (fitness: {best.get('fitness', 0):.4f})")
            report.append(f"- Best strategy: `{best.get('prompt', 'N/A')[:200]}...`")
        report.append("")

    report.append("## Lineage Analysis\n")
    report.append(f"- Founding organisms still alive: {lineage_analysis.get('founding_organisms_still_alive', 0)}")
    report.append(f"- Death causes: {lineage_analysis.get('death_causes', {})}")
    report.append(f"- Mutation type distribution: {lineage_analysis.get('mutation_type_distribution', {})}")
    report.append("")

    report.append("## Emergence Detection\n")
    for finding in emergence:
        report.append(f"- {finding}")
    report.append("")

    report.append("## Top 10 Organisms (Hall of Fame)\n")
    all_orgs = {**pool, **graveyard}
    top_10 = sorted(all_orgs.values(), key=lambda o: o.get("fitness", 0), reverse=True)[:10]
    for i, org in enumerate(top_10, 1):
        report.append(f"### #{i}: {org.get('id', 'N/A')}")
        report.append(f"- Fitness: {org.get('fitness', 0):.4f}")
        report.append(f"- Arena: {org.get('arena', 'N/A')}")
        report.append(f"- Mutation type: {org.get('mutation_type', 'N/A')}")
        report.append(f"- Parent: {org.get('parent_id', 'root')}")
        report.append(f"- Strategy: `{org.get('prompt', 'N/A')[:300]}`")
        report.append("")

    report.append("## Technical Notes\n")
    report.append(f"- Total rate limit events: {curve_stats.get('total_rate_limit_events', 0)}")
    report.append(f"- Config pop_size: {generations[0].get('pop_size', 'N/A') if generations else 'N/A'}")
    report.append("")

    with open(output_path, "w") as f:
        f.write("\n".join(report))
    print(f"Report generated: {output_path}")
    return output_path

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--from", dest="log_dir", default="logs")
    parser.add_argument("--output", default="reports/final_report.md")
    args = parser.parse_args()
    generate_report(args.log_dir, args.output)
