#!/usr/bin/env bash
set -euo pipefail

LOGFILE="runs/vfinal/autonomous_$(date +%Y%m%d_%H%M%S).log"
mkdir -p runs/vfinal

echo "=== v_final AUTONOMOUS PIPELINE ===" | tee "$LOGFILE"
echo "Started: $(date)" | tee -a "$LOGFILE"

# Stage 1: Local smoke test
echo "Stage 1: Smoke test..." | tee -a "$LOGFILE"
WANDB_MODE=disabled python -m pytest classifier/tests/test_vfinal_smoke.py -v --timeout=600 2>&1 | tee -a "$LOGFILE"
if [ ${PIPESTATUS[0]} -ne 0 ]; then
    echo "SMOKE TEST FAILED — aborting" | tee -a "$LOGFILE"
    exit 1
fi

# Stage 2: Full pipeline (GPU + local phases)
echo "Stage 2: Full pipeline..." | tee -a "$LOGFILE"
python -m classifier.lambda.launch_vfinal --sweep-count 25 2>&1 | tee -a "$LOGFILE"

# Stage 3: Finalization
echo "Stage 3: Finalization..." | tee -a "$LOGFILE"
python scripts/finalize_vfinal.py 2>&1 | tee -a "$LOGFILE"

echo "=== COMPLETE ===" | tee -a "$LOGFILE"
echo "Finished: $(date)" | tee -a "$LOGFILE"
