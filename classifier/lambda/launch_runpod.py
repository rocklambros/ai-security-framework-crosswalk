# classifier/lambda/launch_runpod.py
"""RunPod orchestrator: provision pod, bootstrap, train, rsync, terminate."""
from __future__ import annotations

import importlib
import os
import subprocess
import sys
import time

_provision = importlib.import_module("classifier.lambda.provision_runpod")

SSH_KEY = os.path.expanduser("~/.ssh/id_ed25519")
SSH_OPTS = f"-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR -i {SSH_KEY}"


def _get_credential(name: str) -> str:
    result = subprocess.run(["pass", name], capture_output=True, text=True, check=True)
    return result.stdout.strip()


def _ssh(ip: str, port: int, cmd: str, env: dict | None = None, check: bool = True) -> subprocess.CompletedProcess:
    """Run a command on a remote RunPod instance via SSH.

    Pipes the command via stdin (bash -s) to avoid shell quoting issues
    with single/double quotes, f-strings, etc. in multi-line scripts.
    """
    env_lines = ""
    if env:
        env_lines = "\n".join(f'export {k}="{v}"' for k, v in env.items()) + "\n"
    script = env_lines + cmd
    ssh_cmd = f"ssh {SSH_OPTS} -p {port} root@{ip} bash -s"
    print(f"  [ssh] {cmd[:80]}...")
    result = subprocess.run(ssh_cmd, shell=True, input=script, text=True)
    if check and result.returncode != 0:
        raise RuntimeError(f"SSH command failed (exit {result.returncode}): {cmd[:120]}")
    return result


def _scp_to(ip: str, port: int, local_path: str, remote_path: str) -> None:
    cmd = f"scp {SSH_OPTS} -P {port} {local_path} root@{ip}:{remote_path}"
    subprocess.run(cmd, shell=True, check=True)


def _rsync_to(ip: str, port: int, local_path: str, remote_path: str) -> None:
    cmd = (f"rsync -avz --exclude='__pycache__' --exclude='*.pyc' --exclude='.git' "
           f"-e 'ssh {SSH_OPTS} -p {port}' {local_path} root@{ip}:{remote_path}")
    print(f"  [rsync] {local_path} -> {remote_path}")
    subprocess.run(cmd, shell=True, check=True)


def _rsync_from(ip: str, port: int, remote_path: str, local_path: str) -> None:
    cmd = f"rsync -avz -e 'ssh {SSH_OPTS} -p {port}' root@{ip}:{remote_path} {local_path}"
    print(f"  [rsync] {remote_path} -> {local_path}")
    subprocess.run(cmd, shell=True, check=True)


def bootstrap(ip: str, port: int) -> None:
    """Bootstrap RunPod instance with repo, deps, and credentials."""
    creds = {
        "WANDB_API_KEY": _get_credential("wandb/api-key"),
        "HF_TOKEN": _get_credential("huggingface/token"),
    }

    print("\n=== Installing rsync on pod ===")
    _ssh(ip, port, "apt-get update -qq && apt-get install -y -qq rsync > /dev/null 2>&1", check=False)

    print("\n=== Syncing repo to pod ===")
    _rsync_to(ip, port, "./", "/root/crosswalk/")

    print("\n=== Environment check ===")
    _ssh(ip, port, "python --version && nvidia-smi --query-gpu=name,memory.total --format=csv,noheader && python -c 'import torch; print(f\"torch={torch.__version__} cuda={torch.cuda.is_available()}\")'", check=False)

    print("\n=== Installing dependencies ===")
    _ssh(ip, port, "cd /root/crosswalk && pip install --quiet -r classifier/lambda/requirements-lambda.txt")

    print("\n=== Logging into W&B and HuggingFace ===")
    _ssh(ip, port, f"wandb login {creds['WANDB_API_KEY']}")
    _ssh(ip, port, f"huggingface-cli login --token {creds['HF_TOKEN']} --add-to-git-credential")

    print("\n=== Pre-downloading transformer models (non-fatal) ===")
    _ssh(ip, port, """cd /root/crosswalk && python -c "
from transformers import AutoModel
for m in ['microsoft/deberta-v3-large', 'roberta-large', 'microsoft/deberta-v3-base']:
    print(f'  Downloading {m}...')
    AutoModel.from_pretrained(m)
print('All models downloaded.')
" """, check=False)


def run_remote_phase(ip: str, port: int, phase: int, sweep_count: int = 50) -> None:
    """Run a training phase on the remote pod."""
    creds = {
        "WANDB_API_KEY": _get_credential("wandb/api-key"),
    }
    if phase == 3:
        _ssh(ip, port, f"cd /root/crosswalk && python -m classifier.lambda.train_all --phase {phase} --sweep-count {sweep_count}", env=creds)
    else:
        _ssh(ip, port, f"cd /root/crosswalk && python -m classifier.lambda.train_all --phase {phase}", env=creds)


def rsync_artifacts_home(ip: str, port: int) -> None:
    """Rsync all training artifacts from pod to local machine."""
    _rsync_from(ip, port, "/root/crosswalk/runs/", "./runs/")
    _rsync_from(ip, port, "/root/crosswalk/results/", "./results/")
    _rsync_from(ip, port, "/root/crosswalk/data/processed/", "./data/processed/")


def full_pipeline(sweep_count: int = 50) -> None:
    """Run the full v7 pipeline on RunPod: provision, train, rsync, terminate."""

    # Find fastest GPU
    print("=== Finding fastest available GPU ===")
    gpu_type = _provision.find_fastest_available(min_vram_gb=80)
    print(f"  Selected: {gpu_type}")

    # Provision pod
    print(f"\n=== Provisioning {gpu_type} pod ===")
    pod = _provision.create_pod(gpu_type, name="crosswalk-v7")
    ip, port, pod_id = pod["ip"], pod["port"], pod["pod_id"]
    print(f"  Pod ready: {pod_id} @ {ip}:{port}")

    try:
        # Bootstrap
        print("\n=== Bootstrapping pod ===")
        bootstrap(ip, port)

        # Phase 2: SimCSE contrastive pre-training
        print("\n=== Phase 2: SimCSE Contrastive Pre-Training ===")
        run_remote_phase(ip, port, 2)

        # Phase 3: Cross-encoder sweeps (3 models x sweep_count trials)
        print(f"\n=== Phase 3: Cross-Encoder Sweeps ({sweep_count} trials/model) ===")
        run_remote_phase(ip, port, 3, sweep_count=sweep_count)

        # Phase 4: Extract CLS embeddings
        print("\n=== Phase 4: Extract CLS Embeddings ===")
        run_remote_phase(ip, port, 4)

        # Phase 5: GATv2 retrain
        print("\n=== Phase 5: GATv2 Retrain ===")
        run_remote_phase(ip, port, 5)

        # Rsync artifacts home
        print("\n=== Rsyncing artifacts home ===")
        rsync_artifacts_home(ip, port)

        print("\n=== GPU phases complete! ===")

    finally:
        # Terminate pod
        print("\n=== Terminating pod ===")
        _provision.terminate_pod(pod_id)


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="RunPod pipeline orchestrator")
    parser.add_argument("--sweep-count", type=int, default=50, help="Trials per CE model")
    parser.add_argument("--fastest", action="store_true", help="Show fastest available GPU")
    parser.add_argument("--rsync-home", nargs=2, metavar=("IP", "PORT"), help="Rsync from IP PORT")
    parser.add_argument("--terminate-all", action="store_true", help="Terminate all pods")
    args = parser.parse_args()

    if args.terminate_all:
        for pod in _provision.get_running_pods():
            _provision.terminate_pod(pod["id"])
        return

    if args.rsync_home:
        rsync_artifacts_home(args.rsync_home[0], int(args.rsync_home[1]))
        return

    if args.fastest:
        gpu = _provision.find_fastest_available()
        print(f"Fastest available: {gpu}")
        return

    # Full pipeline
    full_pipeline(sweep_count=args.sweep_count)

    # Local phases 6-9
    print("\n=== Phase 6: Stacker Sweep (local) ===")
    subprocess.run([sys.executable, "-m", "classifier.lambda.train_all", "--phase", "6"], check=True)

    print("\n=== Phase 7: Final Stacker (local) ===")
    subprocess.run([sys.executable, "-m", "classifier.lambda.train_all", "--phase", "7"], check=True)

    print("\n=== Phase 8: Conformal Calibration (local) ===")
    subprocess.run([sys.executable, "-m", "classifier.lambda.train_all", "--phase", "8"], check=True)

    print("\n=== Phase 9: Sacred Evaluation (local) ===")
    subprocess.run([sys.executable, "-m", "classifier.lambda.train_all", "--phase", "9"], check=True)

    print("\n" + "=" * 60)
    print("  v7 PIPELINE COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
