"""v8 overnight autonomous runner.

Single command to: provision largest GPU -> train full v8 pipeline ->
rsync artifacts -> run local phases -> sacred evaluation -> terminate pod.

Usage:
    python -m classifier.lambda.launch_v8
    python -m classifier.lambda.launch_v8 --sweep-count 30
    python -m classifier.lambda.launch_v8 --local-only  # skip GPU phases
"""
from __future__ import annotations

import importlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

_provision = importlib.import_module("classifier.lambda.provision_runpod")
_launch_v7 = importlib.import_module("classifier.lambda.launch_runpod")

SSH_KEY = os.path.expanduser("~/.ssh/id_ed25519")
SSH_OPTS = f"-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR -i {SSH_KEY}"

LOG_FILE = Path("runs/v8/pipeline.log")


def log(msg: str) -> None:
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


def run_local_phase(phase: int, sweep_count: int = 50) -> None:
    """Run a training phase locally."""
    cmd = [sys.executable, "-m", "classifier.lambda.train_all_v8", "--phase", str(phase)]
    if phase == 3:
        cmd += ["--sweep-count", str(sweep_count)]
    log(f"Running phase {phase} locally...")
    subprocess.run(cmd, check=True)


def full_pipeline(sweep_count: int = 50, local_only: bool = False) -> None:
    """Run the full v8 pipeline."""
    start = time.time()
    log("=" * 60)
    log("v8 OVERNIGHT PIPELINE STARTING")
    log("=" * 60)

    # Phase 0-1: CPU phases (always local)
    log("Phase 0: OpenCRE extraction + v7c diagnosis")
    run_local_phase(0)

    log("Phase 1: v8 training data assembly")
    run_local_phase(1)

    if not local_only:
        # GPU phases on RunPod
        log("Finding fastest available GPU...")
        gpu_type = _provision.find_fastest_available(min_vram_gb=80)
        log(f"Selected GPU: {gpu_type}")

        log(f"Provisioning {gpu_type} pod...")
        pod = _provision.create_pod(gpu_type, name="crosswalk-v8")
        ip, port, pod_id = pod["ip"], pod["port"], pod["pod_id"]
        log(f"Pod ready: {pod_id} @ {ip}:{port}")

        try:
            # Bootstrap
            log("Bootstrapping pod...")
            _launch_v7.bootstrap(ip, port)

            wandb_key = _launch_v7._get_credential("wandb/api-key")
            env = {"WANDB_API_KEY": wandb_key}

            for phase_num, phase_name in [
                (2, "Contrastive pre-training"),
                (3, f"Cross-encoder sweeps ({sweep_count} trials/model)"),
                (4, "Extract CLS embeddings"),
                (5, "GATv2 retrain"),
            ]:
                log(f"Phase {phase_num}: {phase_name} (GPU)")
                phase_cmd = f"cd /root/crosswalk && python -m classifier.lambda.train_all_v8 --phase {phase_num}"
                if phase_num == 3:
                    phase_cmd += f" --sweep-count {sweep_count}"
                _launch_v7._ssh(ip, port, phase_cmd, env=env)

            # Rsync artifacts home
            log("Rsyncing GPU artifacts home...")
            _launch_v7._rsync_from(ip, port, "/root/crosswalk/runs/v8/", "./runs/v8/")
            _launch_v7._rsync_from(ip, port, "/root/crosswalk/data/processed/", "./data/processed/")
            _launch_v7._rsync_from(ip, port, "/root/crosswalk/data/features/", "./data/features/")

            log("GPU phases complete!")

        finally:
            log(f"Terminating pod {pod_id}...")
            _provision.terminate_pod(pod_id)
    else:
        log("Skipping GPU phases (--local-only mode)")
        for phase in [2, 3, 4, 5]:
            run_local_phase(phase, sweep_count=sweep_count)

    # Local CPU phases
    log("Phase 6: Stacker sweep")
    run_local_phase(6)

    log("Phase 7: Final stacker")
    run_local_phase(7)

    log("Phase 8: Conformal calibration")
    run_local_phase(8)

    log("Phase 9: Sacred evaluation")
    run_local_phase(9)

    elapsed = time.time() - start
    hours = elapsed / 3600
    log(f"\n{'='*60}")
    log(f"  v8 PIPELINE COMPLETE ({hours:.1f} hours)")
    log(f"  Results: runs/v8_sacred/results.json")
    log(f"  Log: {LOG_FILE}")
    log(f"{'='*60}")

    try:
        results = json.loads(Path("runs/v8_sacred/results.json").read_text())
        msg = (
            f"v8 pipeline complete in {hours:.1f}h. "
            f"Exact acc: {results['exact_acc']:.4f}, "
            f"Macro F1: {results['macro_f1']:.4f}"
        )
        log(f"RESULT: {msg}")
    except Exception:
        pass


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="v8 overnight autonomous pipeline")
    parser.add_argument("--sweep-count", type=int, default=50, help="CE sweep trials per model")
    parser.add_argument("--local-only", action="store_true", help="Skip GPU provisioning (run all locally)")
    parser.add_argument("--fastest", action="store_true", help="Show fastest available GPU")
    args = parser.parse_args()

    if args.fastest:
        gpu = _provision.find_fastest_available()
        print(f"Fastest available: {gpu}")
        return

    full_pipeline(sweep_count=args.sweep_count, local_only=args.local_only)


if __name__ == "__main__":
    main()
