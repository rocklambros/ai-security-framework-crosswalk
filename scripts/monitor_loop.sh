#!/usr/bin/env bash
# Adaptive monitoring loop: 15min for first hour, 30min after.
# Each iteration runs monitor_vfinal_sweeps.py and prints the report.
set -uo pipefail

cd "$(dirname "$0")/.."
export PYTHON="/home/rock/anaconda3/envs/coursework/bin/python"
START=$(date +%s)
HOUR_SECS=3600
CHECK=0

while true; do
    CHECK=$((CHECK + 1))
    NOW=$(date +%s)
    ELAPSED=$(( NOW - START ))

    echo "--- CHECK #${CHECK} (${ELAPSED}s elapsed) ---"
    $PYTHON scripts/monitor_vfinal_sweeps.py 2>&1
    echo ""

    # Check if pipeline process is still running
    if ! pgrep -f "run_vfinal_gpu_only" > /dev/null 2>&1; then
        echo "PIPELINE PROCESS EXITED — check runs/vfinal/gpu_only.log"
        # Print last 10 lines of pipeline log
        tail -10 runs/vfinal/gpu_only.log 2>/dev/null
        break
    fi

    # Adaptive interval
    if [ $ELAPSED -lt $HOUR_SECS ]; then
        echo "Next check in 15 minutes (first hour)"
        sleep 900
    else
        echo "Next check in 30 minutes (beyond first hour)"
        sleep 1800
    fi
done

echo "=== MONITORING COMPLETE ==="
