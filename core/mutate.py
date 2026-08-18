import random
import subprocess
import json
import os
import time
import sys

MUTATION_OPERATORS = [
    "rephrase",
    "specialize",
    "generalize",
    "add_constraint",
    "remove_constraint",
    "combine_strategies",
    "random_perturbation",
    "reverse_strategy",
    "simplify",
    "escalate"
]

def call_opencode(prompt, model="opencode/big-pickle", timeout=120):
    try:
        result = subprocess.run(
            ["opencode", "run", "-m", model, "--no-tui"],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=timeout,
            env={**os.environ, "NO_COLOR": "1"}
        )
        return result.stdout.strip() if result.returncode == 0 else ""
    except subprocess.TimeoutExpired:
        return ""
    except Exception as e:
        return f"ERROR: {e}"

def mutate_prompt(original_prompt, parent_fitness=0.0, sibling_prompts=None, arena="puzzles"):
    operator = random.choice(MUTATION_OPERATORS)
    mutation_instruction = _build_mutation_instruction(operator, original_prompt, arena)

    mutated = call_opencode(mutation_instruction, timeout=90)
    if not mutated or len(mutated) < 20:
        mutated = _fallback_mutate(original_prompt, operator)

    return {
        "prompt": mutated,
        "operator": operator,
        "parent_fitness": parent_fitness,
        "success": bool(mutated and len(mutated) >= 20)
    }

def _build_mutation_instruction(operator, prompt, arena):
    instructions = {
        "rephrase": f"Rewrite the following strategy prompt to be clearer and more effective for a {arena} task. Keep the core approach but improve wording:\n\n{prompt}",
        "specialize": f"Take this general strategy and make it more specialized for {arena} tasks. Add specific techniques:\n\n{prompt}",
        "generalize": f"Take this specialized strategy and make it work across multiple {arena} challenge types:\n\n{prompt}",
        "add_constraint": f"Add a new constraint or rule to this strategy that could improve its reliability:\n\n{prompt}",
        "remove_constraint": f"Remove the weakest constraint from this strategy to allow more creative solutions:\n\n{prompt}",
        "combine_strategies": f"Improve this strategy by adding elements from a different successful approach. Be creative:\n\n{prompt}",
        "random_perturbation": f"Make a random significant change to this strategy. Try something unexpected:\n\n{prompt}",
        "reverse_strategy": f"Invert or reverse the approach in this strategy. Try the opposite tactic:\n\n{prompt}",
        "simplify": f"Simplify this strategy to its most essential core steps. Remove anything redundant:\n\n{prompt}",
        "escalate": f"Make this strategy more aggressive and ambitious. Push the boundaries of what's possible:\n\n{prompt}"
    }
    return instructions.get(operator, f"Improve this strategy:\n\n{prompt}")

def _fallback_mutate(prompt, operator):
    lines = prompt.split("\n")
    if operator == "add_constraint":
        new_line = f"- Constraint added: approach must be robust to edge cases"
        lines.insert(random.randint(0, len(lines)), new_line)
    elif operator == "remove_constraint" and len(lines) > 3:
        lines.pop(random.randint(0, len(lines) - 1))
    elif operator == "random_perturbation":
        idx = random.randint(0, len(lines) - 1)
        lines[idx] = lines[idx].upper() if random.random() > 0.5 else lines[idx].lower()
    elif operator == "simplify":
        lines = lines[:max(1, len(lines) // 2)]
    elif operator == "escalate":
        lines.append("IMPORTANT: Be extremely thorough and aggressive in your approach. Leave no stone unturned.")
    else:
        lines.insert(0, f"[Mutated via {operator}]")
    return "\n".join(lines)

def crossover(parent_a, parent_b):
    prompt_a = parent_a.get("prompt", "")
    prompt_b = parent_b.get("prompt", "")
    lines_a = prompt_a.split("\n")
    lines_b = prompt_b.split("\n")

    if not lines_a or not lines_b:
        return prompt_a or prompt_b

    crossover_point_a = random.randint(0, len(lines_a))
    crossover_point_b = random.randint(0, len(lines_b))

    child_lines = lines_a[:crossover_point_a] + lines_b[crossover_point_b:]
    child = "\n".join(child_lines)

    if len(child) < 20:
        return prompt_a if parent_a.get("fitness", 0) >= parent_b.get("fitness", 0) else prompt_b
    return child

def compute_novelty(new_prompt, existing_prompts, max_compare=20):
    if not existing_prompts:
        return 1.0
    new_words = set(new_prompt.lower().split())
    similarities = []
    for existing in existing_prompts[:max_compare]:
        existing_words = set(existing.lower().split())
        if not new_words or not existing_words:
            similarities.append(0.0)
            continue
        intersection = new_words & existing_words
        union = new_words | existing_words
        jaccard = len(intersection) / max(len(union), 1)
        similarities.append(jaccard)
    avg_similarity = sum(similarities) / max(len(similarities), 1)
    novelty = 1.0 - avg_similarity
    return round(max(0.0, min(1.0, novelty)), 4)
