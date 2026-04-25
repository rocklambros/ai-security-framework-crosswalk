#!/usr/bin/env bash
# v_final GPU pipeline — designed to run under nohup.
# Runs the full launch_vfinal.py pipeline (phases 0-6 + pod provisioning).
# Usage: nohup bash scripts/run_vfinal_gpu.sh > runs/vfinal/gpu_pipeline.log 2>&1 &
set -euo pipefail

cd "$(dirname "$0")/.."
export PATH="/home/rock/anaconda3/envs/coursework/bin:$PATH"

echo "=== v_final GPU PIPELINE ==="
echo "Started: $(date)"
echo "Python: $(which python)"
echo "Working dir: $(pwd)"

python -m classifier.lambda.launch_vfinal --sweep-count 25

echo ""
echo "=== GPU PIPELINE COMPLETE ==="
echo "Finished: $(date)"

# Run finalization
echo "=== FINALIZATION ==="
python scripts/finalize_vfinal.py

echo "=== ALL DONE ==="
echo "Finished: $(date)"
