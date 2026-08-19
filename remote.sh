#!/bin/bash
# Reliable remote execution for spawn-evolve codespace
# Uses gh codespace ssh with retry logic (NOT the flaky --stdio proxy)
#
# Usage:
#   ./remote.sh <command>         # Run command on codespace
#   ./remote.sh status           # Check evolution status  
#   ./remote.sh log [lines]      # View log (default: last 20 lines)
#   ./remote.sh start            # Start keep-alive + evolution
#   ./remote.sh stop             # Stop evolution

CODESPACE="swarm-emerg-x5rw77w4xjqvfvpq9"
WORKSPACE="/workspaces/spawn-evolve"
MAX_RETRIES=3
RETRY_DELAY=10

run_remote() {
    local attempt=0
    while [ $attempt -lt $MAX_RETRIES ]; do
        result=$(gh codespace ssh -c "$CODESPACE" -- -t "$@" 2>&1)
        exit_code=$?
        if echo "$result" | grep -q "ALIVE\|OK\|DONE\|SSH_OK"; then
            echo "$result" | grep -v "Pseudo-terminal will not be allocated"
            return 0
        elif [ $exit_code -eq 0 ] && [ -n "$result" ]; then
            echo "$result" | grep -v "Pseudo-terminal will not be allocated"
            return 0
        fi
        attempt=$((attempt + 1))
        if [ $attempt -lt $MAX_RETRIES ]; then
            echo "Retry $attempt/$MAX_RETRIES (waiting ${RETRY_DELAY}s)..." >&2
            sleep $RETRY_DELAY
        fi
    done
    echo "FAILED after $MAX_RETRIES attempts" >&2
    return 1
}

case "${1:-help}" in
    status)
        echo "=== Process ==="
        run_remote "ps -p \$(cat $WORKSPACE/logs/evolve.pid 2>/dev/null) -o pid,pcpu,etime 2>/dev/null || echo 'NOT RUNNING'"
        echo ""
        echo "=== Latest Log ==="
        run_remote "strings $WORKSPACE/logs/deep_run.log | tail -5"
        echo ""
        echo "=== Keep-alive ==="
        run_remote "ls -la /tmp/spawn-evolve-keepalive 2>/dev/null || echo 'NO KEEPALIVE'"
        ;;
    log)
        LINES=${2:-20}
        run_remote "strings $WORKSPACE/logs/deep_run.log | tail -$LINES"
        ;;
    start)
        echo "Starting keep-alive..."
        run_remote "nohup bash -c 'while true; do touch /tmp/spawn-evolve-keepalive; sleep 240; done' > /dev/null 2>&1 &"
        echo "Starting evolution..."
        run_remote "cd $WORKSPACE && nohup python3 -u core/evolve.py --mode deep --all-arenas --model opencode/big-pickle > logs/deep_run.log 2>&1 & echo \$! > logs/evolve.pid && echo PID=\$(cat logs/evolve.pid)"
        ;;
    stop)
        run_remote "kill \$(cat $WORKSPACE/logs/evolve.pid 2>/dev/null) 2>/dev/null && echo STOPPED || echo 'NOT RUNNING'"
        ;;
    help)
        echo "Usage: $0 <status|log|start|stop|command>"
        echo ""
        echo "  status    Check evolution status"
        echo "  log [n]   View last n lines of log (default: 20)"
        echo "  start     Start keep-alive and evolution"
        echo "  stop      Stop evolution"
        echo "  <cmd>     Run arbitrary command on codespace"
        ;;
    *)
        run_remote "$@"
        ;;
esac
