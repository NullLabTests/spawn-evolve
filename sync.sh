#!/bin/bash
# sync.sh - Periodically commit and push all data to GitHub
# Run in background on codespace: bash sync.sh &

REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || echo "/workspaces/spawn-evolve")
INTERVAL=${1:-300}  # Default 5 minutes

cd "$REPO_ROOT"

echo "$(date -Iseconds) | sync.sh started (interval=${INTERVAL}s)" >> logs/sync.log

while true; do
    sleep "$INTERVAL"

    CHANGES=$(git status --porcelain 2>/dev/null | wc -l)
    if [ "$CHANGES" -gt 0 ]; then
        GEN=$(python3 -c "
import json, os
pool = json.load(open('population/pool.json')) if os.path.exists('population/pool.json') else {}
alive = [v for v in pool.values() if v.get('alive', True)]
gens = [v.get('gen_born', 0) for v in alive]
print(max(gens) if gens else 0)
" 2>/dev/null || echo "?")

        git add -A
        git commit -m "sync: gen ${GEN} snapshot $(date -Iseconds)" --quiet 2>/dev/null
        git push origin main --quiet 2>/dev/null

        echo "$(date -Iseconds) | synced at gen ${GEN} (${CHANGES} files changed)" >> logs/sync.log
        echo "  [sync] pushed gen ${GEN}"
    fi
done
