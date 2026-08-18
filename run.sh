#!/bin/bash
set -e

MODE=${1:-pilot}
ARENA=${2:-puzzles}
GENS=${3:-10}
SYNC=${SYNC:-true}

echo "╔══════════════════════════════════════════╗"
echo "║          spawn-evolve                    ║"
echo "║  Open-ended agent evolution              ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "  Mode:      $MODE"
echo "  Arena:     $ARENA"
echo "  Generations: $GENS"
echo "  Model:     opencode/big-pickle"
echo ""

export PATH="$HOME/.opencode/bin:$PATH"

# Setup if needed
if ! python3 -c "import json" 2>/dev/null; then
    bash setup.sh
fi

# Init git if not already
if [ ! -d .git ]; then
    git init
    git add -A
    git commit -m "initial: spawn-evolve scaffold" --quiet
fi

# Start background sync in codespace
if [ -n "$CODESPACE_NAME" ] && [ "$SYNC" = true ]; then
    bash sync.sh &
    SYNC_PID=$!
    echo "[sync] Background sync started (PID: $SYNC_PID)"
fi

# Run evolution
ARENA_FLAG=""
if [ "$ARENA" = "all" ]; then
    ARENA_FLAG="--all-arenas"
else
    for a in $ARENA; do
        ARENA_FLAG="$ARENA_FLAG $a"
    done
fi

echo "[evolve] Starting evolution..."
python3 core/evolve.py \
    --mode "$MODE" \
    $ARENA_FLAG \
    --generations "$GENS" \
    --model "opencode/big-pickle"

# Generate report
echo "[report] Generating final report..."
python3 core/report.py --output reports/final_report.md

# Final sync
if [ -n "$CODESPACE_NAME" ]; then
    git add -A
    git commit -m "final: complete run - mode=$MODE arena=$ARENA gens=$GENS" --quiet 2>/dev/null
    git push origin main --quiet 2>/dev/null
    echo "[sync] Final push complete"
fi

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║  Run complete                            ║"
echo "║  Report: reports/final_report.md          ║"
echo "║  Data:   generations/ + population/       ║"
echo "╚══════════════════════════════════════════╝"
