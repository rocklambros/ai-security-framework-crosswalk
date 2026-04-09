# classifier/lambda/launch.py
"""Local orchestrator: provision Lambda, bootstrap, train, rsync, terminate."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

from classifier.lambda.provision import (
    get_running_instances,
    poll_for_instance,
    provision_instance,
    terminate_instance,
)

SSH_KEY = os.path.expanduser("~/.ssh/id_ed25519")
SSH_OPTS = f"-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR -i {SSH_KEY}"


def _get_credential(name: str) -> str:
    """Read a credential from pass."""
    result = subprocess.run(["pass", name], capture_output=True, text=True, check=True)
    return result.stdout.strip()


def _ssh(ip: str, cmd: str, env: dict | None = None) -> subprocess.CompletedProcess:
    """Run a command on a remote Lambda instance via SSH."""
    env_prefix = ""
    if env:
        env_prefix = " ".join(f'{k}="{v}"' for k, v in env.items()) + " "
    full_cmd = f"ssh {SSH_OPTS} ubuntu@{ip} '{env_prefix}{cmd}'"
    print(f"  [ssh] {cmd[:80]}...")
    return subprocess.run(full_cmd, shell=True, capture_output=False)


def _scp_to(ip: str, local_path: str, remote_path: str) -> None:
    """Copy a file to the remote instance."""
    cmd = f"scp {SSH_OPTS} {local_path} ubuntu@{ip}:{remote_path}"
    subprocess.run(cmd, shell=True, check=True)


def _rsync_from(ip: str, remote_path: str, local_path: str) -> None:
    """Rsync artifacts from remote instance to local machine."""
    cmd = f"rsync -avz -e 'ssh {SSH_OPTS}' ubuntu@{ip}:{remote_path} {local_path}"
    print(f"  [rsync] {remote_path} → {local_path}")
    subprocess.run(cmd, shell=True, check=True)


def _rsync_between(src_ip: str, dst_ip: str, path: str) -> None:
    """Rsync between two Lambda instances via local machine as relay."""
    tmp = f"/tmp/crosswalk_relay_{int(time.time())}"
    os.makedirs(tmp, exist_ok=True)
    _rsync_from(src_ip, path, tmp + "/")
    _scp_cmd = f"rsync -avz -e 'ssh {SSH_OPTS}' {tmp}/ ubuntu@{dst_ip}:{path}"
    subprocess.run(_scp_cmd, shell=True, check=True)


def bootstrap(ip: str) -> None:
    """Bootstrap a Lambda instance."""
    creds = {
        "WANDB_API_KEY": _get_credential("wandb/api-key"),
        "HF_TOKEN": _get_credential("huggingface/token"),
    }
    # Upload bootstrap script and run it
    _scp_to(ip, "classifier/lambda/bootstrap.sh", "~/bootstrap.sh")
    _ssh(ip, "chmod +x ~/bootstrap.sh")
    _ssh(ip, "bash ~/bootstrap.sh", env=creds)


def run_remote_phase(ip: str, phase: int, sweep_count: int = 50) -> None:
    """Run a training phase on a remote Lambda instance."""
    creds = {
        "WANDB_API_KEY": _get_credential("wandb/api-key"),
        "HF_TOKEN": _get_credential("huggingface/token"),
    }
    if phase == 3:
        _ssh(ip, f"cd ~/crosswalk && python -m classifier.lambda.train_all --phase {phase} --sweep-count {sweep_count}", env=creds)
    else:
        _ssh(ip, f"cd ~/crosswalk && python -m classifier.lambda.train_all --phase {phase}", env=creds)


def rsync_artifacts_home(ip: str) -> None:
    """Rsync all training artifacts from Lambda to local machine."""
    _rsync_from(ip, "~/crosswalk/runs/", "./runs/")
    _rsync_from(ip, "~/crosswalk/results/", "./results/")
    _rsync_from(ip, "~/crosswalk/data/processed/", "./data/processed/")


def launch_a10_pipeline(sweep_count: int = 50) -> dict:
    """Provision A10, bootstrap, run Phases 2-3 (ELECTRA, then DeBERTa)."""
    print("\n=== Provisioning A10 ===")
    a10 = provision_instance("gpu_1x_a10", name="crosswalk-a10")
    print(f"  A10 provisioned: {a10['ip']} ({a10['instance_id']})")

    print("\n=== Bootstrapping A10 ===")
    bootstrap(a10["ip"])

    print("\n=== A10: Phase 2 (Contrastive Pre-Training) ===")
    run_remote_phase(a10["ip"], 2)

    print("\n=== A10: Phase 3 (Cross-Encoder Sweeps) ===")
    run_remote_phase(a10["ip"], 3, sweep_count=sweep_count)

    return a10


def launch_h100_pipeline(a10_ip: str | None, sweep_count: int = 50) -> dict:
    """Poll for 2x H100, bootstrap, rsync from A10, run remaining phases."""
    print("\n=== Polling for 2x H100 SXM5 ===")
    h100 = poll_for_instance("gpu_2x_h100_sxm5")
    print(f"  H100 provisioned: {h100['ip']} ({h100['instance_id']})")

    print("\n=== Bootstrapping H100 ===")
    bootstrap(h100["ip"])

    if a10_ip:
        print("\n=== Rsyncing A10 checkpoints to H100 ===")
        _rsync_between(a10_ip, h100["ip"], "~/crosswalk/runs/")

    print("\n=== H100: Phase 3 (remaining sweeps) ===")
    run_remote_phase(h100["ip"], 3, sweep_count=sweep_count)

    print("\n=== H100: Phase 4 (Extract CLS Embeddings) ===")
    run_remote_phase(h100["ip"], 4)

    print("\n=== H100: Phase 5 (GATv2 Retrain) ===")
    run_remote_phase(h100["ip"], 5)

    return h100


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Lambda pipeline orchestrator")
    parser.add_argument("--sweep-count", type=int, default=50, help="Trials per CE model")
    parser.add_argument("--a10-only", action="store_true", help="Only run A10 pipeline")
    parser.add_argument("--h100-only", action="store_true", help="Only run H100 pipeline (poll + provision)")
    parser.add_argument("--rsync-home", type=str, help="Rsync artifacts from IP")
    parser.add_argument("--terminate-all", action="store_true", help="Terminate all running instances")
    args = parser.parse_args()

    if args.terminate_all:
        for inst in get_running_instances():
            print(f"Terminating {inst['id']}...")
            terminate_instance(inst["id"])
        return

    if args.rsync_home:
        rsync_artifacts_home(args.rsync_home)
        return

    if args.a10_only:
        a10 = launch_a10_pipeline(sweep_count=args.sweep_count)
        print(f"\nA10 pipeline complete. Instance: {a10['instance_id']} @ {a10['ip']}")
        print("Run --rsync-home to pull artifacts, then --terminate-all when done.")
        return

    if args.h100_only:
        h100 = launch_h100_pipeline(a10_ip=None, sweep_count=args.sweep_count)
        print(f"\nH100 pipeline complete. Instance: {h100['instance_id']} @ {h100['ip']}")
        return

    # Full pipeline: A10 + H100 poller in parallel
    print("=" * 60)
    print("  FULL PIPELINE: A10 now + H100 poller")
    print("=" * 60)

    # Phase 1 locally
    print("\n=== Phase 1: Build Training Set (local) ===")
    subprocess.run([sys.executable, "-m", "classifier.scripts.build_expert_training"], check=True)

    # Launch A10 in background thread
    a10_result = {"instance": None}

    def a10_thread():
        a10_result["instance"] = launch_a10_pipeline(sweep_count=args.sweep_count)

    t = threading.Thread(target=a10_thread)
    t.start()

    # Poll for H100 in main thread
    h100 = None
    try:
        a10_ip = None
        t.join(timeout=120)
        if a10_result["instance"]:
            a10_ip = a10_result["instance"]["ip"]

        h100 = launch_h100_pipeline(a10_ip=a10_ip, sweep_count=args.sweep_count)
    except KeyboardInterrupt:
        print("\nH100 polling interrupted. A10 may still be running.")

    t.join()
    a10 = a10_result["instance"]

    print("\n=== Rsyncing artifacts home ===")
    if h100:
        rsync_artifacts_home(h100["ip"])
    elif a10:
        rsync_artifacts_home(a10["ip"])

    print("\n=== Phase 6: Stacker Sweep (local) ===")
    subprocess.run([sys.executable, "-m", "classifier.lambda.train_all", "--phase", "6"], check=True)

    print("\n=== Phase 7: Two-Stage Classifier (local) ===")
    subprocess.run([sys.executable, "-m", "classifier.lambda.train_all", "--phase", "7"], check=True)

    print("\n=== Phase 8: Conformal Calibration (local) ===")
    subprocess.run([sys.executable, "-m", "classifier.lambda.train_all", "--phase", "8"], check=True)

    print("\n=== Phase 9: Sacred Evaluation (local) ===")
    subprocess.run([sys.executable, "-m", "classifier.lambda.train_all", "--phase", "9"], check=True)

    print("\n=== Terminating all Lambda instances ===")
    for inst in get_running_instances():
        terminate_instance(inst["id"])

    print("\n" + "=" * 60)
    print("  PIPELINE COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
