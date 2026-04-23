#!/usr/bin/env bash
# run_v8_complete.sh — Complete autonomous v8 pipeline.
#
# Phases:
#   1. Training pipeline (launch_v8.py): 10 phases, GPU on RunPod
#   2. Finalization (finalize_v8.py): notebook cells, paper update, commit
#
# Usage:
#   nohup bash scripts/run_v8_complete.sh > runs/v8/complete_pipeline.log 2>&1 &
#   nohup bash scripts/run_v8_complete.sh --local-only > runs/v8/complete_pipeline.log 2>&1 &
#
# Monitor:
#   tail -f runs/v8/pipeline.log
#   tail -f runs/v8/complete_pipeline.log

set -euo pipefail

cd "$(dirname "$0")/.."
ROOT="$(pwd)"
LOGDIR="$ROOT/runs/v8"
mkdir -p "$LOGDIR"

ts() { date "+%Y-%m-%d %H:%M:%S"; }

log() {
    echo "[$(ts)] $1" | tee -a "$LOGDIR/complete_pipeline.log"
}

log "========================================"
log "  v8 COMPLETE PIPELINE STARTING"
log "  Working dir: $ROOT"
log "========================================"

# Parse arguments to forward to launch_v8
LAUNCH_ARGS=("$@")
if [ ${#LAUNCH_ARGS[@]} -eq 0 ]; then
    LAUNCH_ARGS=("--sweep-count" "50")
fi

# ──────────────────────────────────────────
# STAGE 1: Training pipeline
# ──────────────────────────────────────────
log "STAGE 1: Training pipeline (${LAUNCH_ARGS[*]})"
log "  This may take 3-5 hours with GPU provisioning..."

if python -m classifier.lambda.launch_v8 "${LAUNCH_ARGS[@]}"; then
    log "STAGE 1 COMPLETE: Training pipeline succeeded."
else
    EXIT_CODE=$?
    log "STAGE 1 FAILED: Training pipeline exited with code $EXIT_CODE"

    # If results exist from a prior run, continue to finalization
    if [ -f "runs/v8_sacred/results.json" ]; then
        log "  Found existing results.json — continuing to finalization."
    else
        log "  No results.json found. Pipeline cannot continue."
        log "  Check: tail -100 runs/v8/pipeline.log"
        exit $EXIT_CODE
    fi
fi

# ──────────────────────────────────────────
# STAGE 2: Project 2 data regeneration
# ──────────────────────────────────────────
log "STAGE 2: Regenerating Project 2 data..."

if python project2/prepare_data.py 2>/dev/null; then
    log "  Project 2 data regenerated."
else
    log "  Project 2 data regeneration failed (non-fatal)."
fi

# ──────────────────────────────────────────
# STAGE 3: Finalization (notebook + paper)
# ──────────────────────────────────────────
log "STAGE 3: Finalization (notebook cells, paper update, commit)"

if python scripts/finalize_v8.py; then
    log "STAGE 3 COMPLETE: Finalization succeeded."
else
    log "STAGE 3 FAILED: Finalization had errors (check above)."
fi

# ──────────────────────────────────────────
# Summary
# ──────────────────────────────────────────
log ""
log "========================================"
log "  v8 COMPLETE PIPELINE FINISHED"
log "========================================"

if [ -f "runs/v8_sacred/results.json" ]; then
    python -c "
import json
r = json.loads(open('runs/v8_sacred/results.json').read())
print(f'  Exact accuracy:    {r[\"exact_acc\"]:.4f}')
print(f'  Macro F1:          {r[\"macro_f1\"]:.4f}')
print(f'  Adjacent accuracy: {r[\"adjacent_acc\"]:.4f}')
imp = r.get('improvement', {})
if imp:
    print(f'  Improvement over v7c:')
    print(f'    Exact acc delta: {imp.get(\"exact_acc_delta\", 0):+.4f}')
    print(f'    Macro F1 delta:  {imp.get(\"macro_f1_delta\", 0):+.4f}')
" 2>/dev/null | tee -a "$LOGDIR/complete_pipeline.log"
fi

log "  Logs: $LOGDIR/complete_pipeline.log"
log "  Pipeline log: $LOGDIR/pipeline.log"
log "  Results: runs/v8_sacred/results.json"
log "  Notebook: project1/COMP_4433_RockLambros_project1_crosswalk_eda.ipynb"
log "  Paper: paper/main.pdf"
