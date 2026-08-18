import json
import os
import time

class LineageTracker:
    def __init__(self, population_path="population/pool.json", graveyard_path="population/graveyard.json"):
        self.population_path = population_path
        self.graveyard_path = graveyard_path
        self.pool = self._load_json(population_path, {})
        self.graveyard = self._load_json(graveyard_path, {})
        os.makedirs(os.path.dirname(population_path), exist_ok=True)

    def _load_json(self, path, default):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return default

    def _save_json(self, path, data):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def save(self):
        self._save_json(self.population_path, self.pool)
        self._save_json(self.graveyard_path, self.graveyard)

    def register_birth(self, organism):
        org_id = organism["id"]
        self.pool[org_id] = {
            "id": org_id,
            "prompt": organism["prompt"],
            "parent_id": organism.get("parent_id"),
            "gen_born": organism["gen_born"],
            "mutation_type": organism.get("mutation_type", "none"),
            "arena": organism.get("arena", "unknown"),
            "fitness": organism.get("fitness", 0.0),
            "fitness_components": organism.get("fitness_components", {}),
            "alive": True,
            "gen_died": None,
            "cause_of_death": None,
            "tokens_used": 0,
            "rate_limit_retries": 0,
            "born_at": time.time()
        }
        self.save()

    def register_death(self, org_id, cause="selection"):
        if org_id in self.pool:
            org = self.pool.pop(org_id)
            org["alive"] = False
            org["gen_died"] = cause.get("gen", None) if isinstance(cause, dict) else None
            org["cause_of_death"] = cause if isinstance(cause, str) else cause.get("cause", "unknown")
            self.graveyard[org_id] = org
            self.save()

    def register_fitness(self, org_id, fitness, components=None, tokens=0):
        if org_id in self.pool:
            self.pool[org_id]["fitness"] = fitness
            if components:
                self.pool[org_id]["fitness_components"] = components
            self.pool[org_id]["tokens_used"] = self.pool[org_id].get("tokens_used", 0) + tokens
            self.save()

    def get_alive(self):
        return {k: v for k, v in self.pool.items() if v.get("alive", True)}

    def get_alive_by_arena(self, arena):
        return {k: v for k, v in self.pool.items() if v.get("alive", True) and v.get("arena") == arena}

    def get_parent(self, org_id):
        org = self.pool.get(org_id) or self.graveyard.get(org_id)
        if org and org.get("parent_id"):
            return self.pool.get(org["parent_id"]) or self.graveyard.get(org["parent_id"])
        return None

    def get_ancestors(self, org_id, depth=10):
        ancestors = []
        current = org_id
        for _ in range(depth):
            parent = self.get_parent(current)
            if not parent:
                break
            ancestors.append(parent["id"])
            current = parent["id"]
        return ancestors

    def get_descendants_count(self, org_id):
        count = 0
        for oid, org in self.pool.items():
            if org.get("alive", True) and org.get("parent_id") == org_id:
                count += 1 + self.get_descendants_count(oid)
        for oid, org in self.graveyard.items():
            if org.get("parent_id") == org_id:
                count += 1 + self.get_descendants_count(oid)
        return count

    def inbreeding_coefficient(self, org_id):
        ancestors = set(self.get_ancestors(org_id, depth=5))
        if len(ancestors) < 2:
            return 0.0
        parent = self.get_parent(org_id)
        if not parent:
            return 0.0
        grandparent_ids = self.get_ancestors(org_id, depth=2)
        if len(grandparent_ids) < 2:
            return 0.0
        shared = len(ancestors) / max(len(grandparent_ids), 1)
        return min(shared, 1.0)

    def lineage_depth(self, org_id):
        return len(self.get_ancestors(org_id, depth=100))

    def diversity_index(self):
        alive = self.get_alive()
        if not alive:
            return 0.0
        arena_counts = {}
        for org in alive.values():
            arena = org.get("arena", "unknown")
            arena_counts[arena] = arena_counts.get(arena, 0) + 1
        total = len(alive)
        entropy = 0.0
        for count in arena_counts.values():
            p = count / total
            if p > 0:
                entropy -= p * __import__("math").log2(p)
        return round(entropy, 4)

    def stats(self):
        alive = self.get_alive()
        dead = self.graveyard
        all_organisms = {**self.pool, **self.graveyard}
        fitnesses = [o["fitness"] for o in all_organisms.values() if o.get("fitness")]
        return {
            "alive_count": len(alive),
            "dead_count": len(dead),
            "total_born": len(all_organisms),
            "avg_fitness": round(sum(fitnesses) / max(len(fitnesses), 1), 4),
            "best_fitness": round(max(fitnesses) if fitnesses else 0, 4),
            "diversity_index": self.diversity_index(),
            "lineage_depths": {
                org_id: self.lineage_depth(org_id) for org_id in list(alive.keys())[:5]
            }
        }
