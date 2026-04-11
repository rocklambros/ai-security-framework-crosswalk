#!/bin/bash
# classifier/lambda/run_phase.sh
# Run a specific training phase on the Lambda instance.
# Usage: run_phase.sh <phase_number> [--sweep-count N]
set -euo pipefail

cd ~/crosswalk

PHASE=${1:?Usage: run_phase.sh <phase_number> [--sweep-count N]}
SWEEP_COUNT=${2:-50}

echo "=== Running Phase $PHASE (sweep_count=$SWEEP_COUNT) ==="

if [ "$PHASE" = "3" ]; then
    python -m classifier.lambda.train_all --phase "$PHASE" --sweep-count "$SWEEP_COUNT"
else
    python -m classifier.lambda.train_all --phase "$PHASE"
fi

echo "=== Phase $PHASE complete ==="
