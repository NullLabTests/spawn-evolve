#!/bin/bash
# Save status of running evolution on codespace
# Usage: ./monitor.sh
CODESPACE="swarm-emerg-x5rw77w4xjqvfvpq9"

echo "=== spawn-evolve monitor ==="
echo "Time: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo ""

# Check process alive
echo "--- Process ---"
gh codespace ssh -c $CODESPACE -- -t 'bash -c "ps -p \$(cat /workspaces/spawn-evolve/logs/evolve.pid 2>/dev/null) -o pid,pcpu,etime 2>/dev/null || echo DEAD"' 2>&1

# Get latest progress
echo ""
echo "--- Latest ---"
gh codespace ssh -c $CODESPACE -- -t 'bash -c "strings /workspaces/spawn-evolve/logs/deep_run.log | grep -E \"Evaluating|DONE|START|COMPLETE\" | tail -8 > /tmp/mon_progress.txt; cat /tmp/mon_progress.txt"' 2>&1

# Get escape fitness range
echo ""
echo "--- Escape Fitness ---"
gh codespace ssh -c $CODESPACE -- -t 'bash -c "strings /workspaces/spawn-evolve/logs/deep_run.log | grep \"fitness=\" | grep -v CACHED | head -20 > /tmp/mon_fit.txt; cat /tmp/mon_fit.txt"' 2>&1

# Save log locally
echo ""
echo "--- Saving local copy ---"
gh codespace ssh -c $CODESPACE -- -t 'bash -c "cat /workspaces/spawn-evolve/logs/deep_run.log > /tmp/deep_run_copy.log && wc -l /tmp/deep_run_copy.log"' 2>&1
echo "Saved at $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
