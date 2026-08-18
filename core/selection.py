import random

def tournament_select(pool, tournament_size=3, n_select=None):
    alive = {k: v for k, v in pool.items() if v.get("alive", True)}
    if not alive:
        return []
    if n_select is None:
        n_select = len(alive)
    selected = []
    for _ in range(n_select):
        competitors = random.sample(list(alive.values()), min(tournament_size, len(alive)))
        winner = max(competitors, key=lambda o: o.get("fitness", 0.0))
        selected.append(winner)
    return selected

def elitism_select(pool, top_pct=0.1):
    alive = {k: v for k, v in pool.items() if v.get("alive", True)}
    if not alive:
        return []
    sorted_by_fitness = sorted(alive.values(), key=lambda o: o.get("fitness", 0.0), reverse=True)
    n_elite = max(1, int(len(sorted_by_fitness) * top_pct))
    return sorted_by_fitness[:n_elite]

def survivor_select(pool, offspring, pop_size, elitism_pct=0.1, tournament_size=3):
    all_candidates = list(pool.values()) + list(offspring)
    all_alive = [o for o in all_candidates if o.get("alive", True)]
    if not all_alive:
        return []

    elite = elitism_select({o["id"]: o for o in all_alive}, top_pct=elitism_pct)
    elite_ids = {e["id"] for e in elite}
    remaining = [o for o in all_alive if o["id"] not in elite_ids]

    needed = pop_size - len(elite)
    if needed <= 0:
        survivors = elite[:pop_size]
    else:
        if remaining:
            tournament_pool = {o["id"]: o for o in remaining}
            tourn_selected = tournament_select(tournament_pool, tournament_size=tournament_size, n_select=needed)
            survivors = elite + tourn_selected
        else:
            survivors = elite[:pop_size]

    return survivors[:pop_size]

def rank_select(pool, n_select):
    alive = {k: v for k, v in pool.items() if v.get("alive", True)}
    if not alive:
        return []
    sorted_pool = sorted(alive.values(), key=lambda o: o.get("fitness", 0.0), reverse=True)
    n = len(sorted_pool)
    weights = [n - i for i in range(n)]
    total_weight = sum(weights)
    probs = [w / total_weight for w in weights]
    selected = []
    for _ in range(n_select):
        idx = random.choices(range(n), weights=probs, k=1)[0]
        selected.append(sorted_pool[idx])
    return selected
