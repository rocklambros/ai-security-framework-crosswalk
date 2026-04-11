#!/usr/bin/env bash
# Monitor Lambda GPU training progress every 5 minutes.
# Writes status to /tmp/lambda_training_status.log
# Exits automatically when training process is no longer running.

set +e  # don't exit on errors — we handle them in the loop

REMOTE="ubuntu@192.222.50.109"
SSH_OPTS="-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR -i ~/.ssh/id_ed25519"
LOG="/tmp/lambda_training_status.log"
INTERVAL=300  # 5 minutes

echo "=== Lambda Training Monitor Started $(date) ===" > "$LOG"

while true; do
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

    # Check if SSH is reachable
    if ! ssh $SSH_OPTS -o ConnectTimeout=10 "$REMOTE" "true" 2>/dev/null; then
        echo "[$TIMESTAMP] SSH UNREACHABLE — instance may be terminated" >> "$LOG"
        echo "[$TIMESTAMP] MONITOR EXITING — instance unreachable" >> "$LOG"
        break
    fi

    # Gather status in one SSH call
    STATUS=$(ssh $SSH_OPTS "$REMOTE" bash -s 2>/dev/null <<'REMOTE_SCRIPT'
# Check which phase is running
PROC=$(ps aux | grep 'train_all' | grep python | grep -v grep | head -1)
if [ -z "$PROC" ]; then
    echo "PHASE=NONE"
    echo "PROCESS=stopped"
else
    PHASE_ARG=$(echo "$PROC" | grep -oP '\-\-phase \K\d+' || echo "unknown")
    CPU_TIME=$(echo "$PROC" | awk '{print $10}')
    echo "PHASE=$PHASE_ARG"
    echo "PROCESS=running"
    echo "CPU_TIME=$CPU_TIME"
fi

# GPU stats
GPU=$(nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu --format=csv,noheader 2>/dev/null || echo "N/A")
echo "GPU=$GPU"

# Check for .pt model files (artifacts)
PT_COUNT=$(find ~/crosswalk/runs -name '*.pt' 2>/dev/null | wc -l)
echo "ARTIFACTS=$PT_COUNT"

# WANDB runs
WANDB_RUNS=$(ls -d ~/crosswalk/wandb/run-* 2>/dev/null | wc -l)
echo "WANDB_RUNS=$WANDB_RUNS"

# Last 3 lines of training log
echo "LOG_TAIL_START"
tail -3 /tmp/training.log 2>/dev/null || echo "(empty)"
echo "LOG_TAIL_END"

# Disk usage
echo "DISK=$(df -h /home/ubuntu | tail -1 | awk '{print $3"/"$2" ("$5")"}')"
REMOTE_SCRIPT
    )

    # Parse key fields
    PHASE=$(echo "$STATUS" | grep '^PHASE=' | cut -d= -f2)
    PROCESS=$(echo "$STATUS" | grep '^PROCESS=' | cut -d= -f2)
    GPU=$(echo "$STATUS" | grep '^GPU=' | cut -d= -f2-)
    ARTIFACTS=$(echo "$STATUS" | grep '^ARTIFACTS=' | cut -d= -f2)
    WANDB_RUNS=$(echo "$STATUS" | grep '^WANDB_RUNS=' | cut -d= -f2)
    DISK=$(echo "$STATUS" | grep '^DISK=' | cut -d= -f2-)

    # Write status line
    echo "[$TIMESTAMP] phase=$PHASE process=$PROCESS gpu=[$GPU] artifacts=$ARTIFACTS wandb_runs=$WANDB_RUNS disk=$DISK" >> "$LOG"

    # Check if training finished
    if [ "$PROCESS" = "stopped" ]; then
        echo "[$TIMESTAMP] TRAINING COMPLETE — no train_all process found" >> "$LOG"
        echo "[$TIMESTAMP] Final artifact count: $ARTIFACTS .pt files" >> "$LOG"
        echo "[$TIMESTAMP] MONITOR EXITING — training done" >> "$LOG"
        break
    fi

    sleep $INTERVAL
done

echo "=== Lambda Training Monitor Ended $(date) ===" >> "$LOG"
