"""Relaunch deberta-large with BF16 + higher LR on a fresh RunPod pod.

Runs phases 2→3→4 independently of the main pipeline.
Usage: python scripts/relaunch_deberta_large.py [--sweep-count 30]
"""
from __future__ import annotations

import importlib
import subprocess
import sys
import time

_provision = importlib.import_module("classifier.lambda.provision_runpod")
_launch = importlib.import_module("classifier.lambda.launch_runpod")


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--sweep-count", type=int, default=30)
    args = parser.parse_args()

    print("=== Provisioning largest available GPU ===")
    gpu_type = _provision.find_fastest_available(min_vram_gb=48)
    print(f"  GPU: {gpu_type}")

    pod = _provision.create_pod(gpu_type, name="v8b-deberta-large-relaunch")
    ip, port = pod["ip"], pod["port"]
    print(f"  Pod: {pod['pod_id']} @ {ip}:{port}")

    print("\n=== Bootstrapping ===")
    _launch.bootstrap(ip, port)
    print("  Bootstrap complete")

    wandb_key = _launch._get_credential("wandb/api-key")
    env = {"WANDB_API_KEY": wandb_key}

    for phase in [2, 3, 4]:
        print(f"\n=== Phase {phase} (deberta-large, model_index=0) ===")
        t0 = time.time()
        cmd = (
            f"cd /root/crosswalk && python -m classifier.lambda.train_all_v8 "
            f"--phase {phase} --model-index 0"
        )
        if phase == 3:
            cmd += f" --sweep-count {args.sweep_count}"
        try:
            _launch._ssh(ip, port, cmd, env=env)
            elapsed = time.time() - t0
            print(f"  Phase {phase} done in {elapsed/60:.1f}m")
        except Exception as e:
            print(f"  Phase {phase} FAILED: {e}")
            break

    print("\n=== Rsyncing artifacts ===")
    _launch._rsync_from(ip, port, "/root/crosswalk/runs/v8b/", "./runs/v8b/")
    _launch._rsync_from(ip, port, "/root/crosswalk/data/processed/", "./data/processed/")

    print("\n=== Terminating pod ===")
    _provision.terminate_pod(pod["pod_id"])
    print("Done.")


if __name__ == "__main__":
    main()
