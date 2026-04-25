"""Launch just the GPU portion of v_final: provision pods, sweep, rsync, local phases 4-6.

Skips phases 0-1 (assumed already done or running separately).
Usage: nohup python scripts/run_vfinal_gpu_only.py > runs/vfinal/gpu_only.log 2>&1 &
"""
from __future__ import annotations

import importlib
import json
import os
import sys
import time
import concurrent.futures
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

_provision = importlib.import_module("classifier.lambda.provision_runpod")
_launch = importlib.import_module("classifier.lambda.launch_runpod")

LOG_FILE = Path("runs/vfinal/pipeline.log")
N_MODELS = 3
MODEL_NAMES = ["roberta", "deberta_base", "bge"]


def log(msg: str) -> None:
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line, flush=True)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


def _bootstrap_pod(pod: dict, pod_index: int) -> None:
    log(f"Bootstrapping pod {pod_index} ({MODEL_NAMES[pod_index]})...")
    _launch.bootstrap(pod["ip"], pod["port"])
    if MODEL_NAMES[pod_index] == "bge":
        log(f"Pre-downloading BGE-large for bi-encoder pod...")
        _launch._ssh(pod["ip"], pod["port"],
                      'python -c "from transformers import AutoModel, AutoTokenizer; '
                      "AutoModel.from_pretrained('BAAI/bge-large-en-v1.5'); "
                      "AutoTokenizer.from_pretrained('BAAI/bge-large-en-v1.5'); "
                      "print('BGE-large downloaded')\"", check=False)
    log(f"Pod {pod_index} bootstrapped")


def _run_pod_phases(pod: dict, model_index: int, sweep_count: int, wandb_key: str) -> dict:
    ip, port = pod["ip"], pod["port"]
    env = {"WANDB_API_KEY": wandb_key}
    name = MODEL_NAMES[model_index]
    results = {}

    for phase_num in [2, 3]:
        phase_start = time.time()
        cmd = (
            f"cd /root/crosswalk && python -m classifier.lambda.train_all_vfinal "
            f"--phase {phase_num} --model-index {model_index}"
        )
        if phase_num == 2:
            cmd += f" --sweep-count {sweep_count}"

        log(f"[{name}] Phase {phase_num} starting")
        try:
            _launch._ssh(ip, port, cmd, env=env)
            elapsed = time.time() - phase_start
            log(f"[{name}] Phase {phase_num} COMPLETE in {elapsed/60:.1f}m")
            results[f"phase{phase_num}"] = {"status": "ok", "elapsed": elapsed}
        except Exception as e:
            log(f"[{name}] Phase {phase_num} FAILED: {e}")
            results[f"phase{phase_num}"] = {"status": "failed", "error": str(e)}
            break

    return {"model": name, "model_index": model_index, **results}


def _rsync_from_pod(pod: dict, pod_index: int) -> None:
    ip, port = pod["ip"], pod["port"]
    log(f"Rsyncing from pod {pod_index} ({MODEL_NAMES[pod_index]})...")
    _launch._rsync_from(ip, port, "/root/crosswalk/runs/vfinal/", "./runs/vfinal/")
    _launch._rsync_from(ip, port, "/root/crosswalk/data/features/", "./data/features/")
    log(f"Rsync from pod {pod_index} COMPLETE")


def main():
    start = time.time()
    sweep_count = 25

    log("=" * 60)
    log("v_final GPU-ONLY PIPELINE (skipping phases 0-1)")
    log(f"  3 models, {sweep_count} trials each, parallel H100 pods")
    log("=" * 60)

    wandb_key = _launch._get_credential("wandb/api-key")

    log(f"Provisioning {N_MODELS} pods...")
    gpu_type = _provision.find_fastest_available(min_vram_gb=48)
    log(f"Selected GPU: {gpu_type}")

    pods = []
    for i in range(N_MODELS):
        try:
            pod = _provision.create_pod(gpu_type, name=f"vfinal-{MODEL_NAMES[i]}")
            pods.append(pod)
            log(f"Pod {i} ({MODEL_NAMES[i]}) ready: {pod['pod_id']} @ {pod['ip']}:{pod['port']}")
        except Exception as e:
            log(f"Pod {i} provisioning FAILED: {e}")
            if not pods:
                raise
            break

    try:
        log(f"Bootstrapping {len(pods)} pods in parallel...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(pods)) as ex:
            list(ex.map(_bootstrap_pod, pods, range(len(pods))))
        log("All pods bootstrapped")

        log(f"Launching {len(pods)} sweeps in parallel...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(pods)) as ex:
            futures = {
                ex.submit(_run_pod_phases, pods[i], i, sweep_count, wandb_key): i
                for i in range(min(N_MODELS, len(pods)))
            }
            for future in concurrent.futures.as_completed(futures):
                idx = futures[future]
                try:
                    result = future.result()
                    log(f"[{MODEL_NAMES[idx]}] completed: {json.dumps(result, default=str)}")
                except Exception as e:
                    log(f"[{MODEL_NAMES[idx]}] EXCEPTION: {e}")

        log("All GPU phases complete. Rsyncing artifacts...")
        for i, pod in enumerate(pods):
            _rsync_from_pod(pod, i)
        log("All artifacts rsynced")

    finally:
        for pod in pods:
            log(f"Terminating pod {pod['pod_id']}...")
            try:
                _provision.terminate_pod(pod["pod_id"])
            except Exception as e:
                log(f"  terminate failed: {e}")

    # Local phases 4-6
    import subprocess

    log("Phase 4: Stacker sweep (local)")
    subprocess.run(
        [sys.executable, "-m", "classifier.lambda.train_all_vfinal", "--phase", "4"],
        check=True,
    )
    log("Phase 4 COMPLETE")

    log("Phase 5: Conformal calibration (local)")
    subprocess.run(
        [sys.executable, "-m", "classifier.lambda.train_all_vfinal", "--phase", "5"],
        check=True,
    )
    log("Phase 5 COMPLETE")

    log("Phase 6: Sacred evaluation (local)")
    subprocess.run(
        [sys.executable, "-m", "classifier.lambda.train_all_vfinal", "--phase", "6"],
        check=True,
    )
    log("Phase 6 COMPLETE")

    # Finalization
    log("Running finalization...")
    subprocess.run(
        [sys.executable, "scripts/finalize_vfinal.py"],
        check=True,
    )
    log("Finalization COMPLETE")

    elapsed = time.time() - start
    log(f"\n{'='*60}")
    log(f"  v_final PIPELINE FULLY COMPLETE ({elapsed/3600:.1f} hours)")
    log(f"{'='*60}")


if __name__ == "__main__":
    main()
