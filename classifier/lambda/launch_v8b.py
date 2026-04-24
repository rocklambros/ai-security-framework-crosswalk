"""v8b multi-GPU pipeline: provision up to 3 RunPod pods for parallel CE training.

Each pod trains 1 model (deberta-large, roberta-large, deberta-base) through
phases 2→3→4.  After all pods complete, rsync artifacts home and run local
CPU phases 5-9.

Usage:
    python -m classifier.lambda.launch_v8b
    python -m classifier.lambda.launch_v8b --sweep-count 30
    python -m classifier.lambda.launch_v8b --max-pods 1   # single-GPU fallback
    python -m classifier.lambda.launch_v8b --local-only
"""
from __future__ import annotations

import concurrent.futures
import importlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

_provision = importlib.import_module("classifier.lambda.provision_runpod")
_launch = importlib.import_module("classifier.lambda.launch_runpod")

LOG_FILE = Path("runs/v8b/pipeline.log")


def log(msg: str) -> None:
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line, flush=True)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


def _provision_pods(n_pods: int) -> list[dict]:
    """Provision up to n_pods RunPod instances with the fastest GPU."""
    gpu_type = _provision.find_fastest_available(min_vram_gb=48)
    log(f"Selected GPU: {gpu_type}")

    pods = []
    for i in range(n_pods):
        try:
            pod = _provision.create_pod(gpu_type, name=f"v8b-model-{i}")
            pods.append(pod)
            log(f"Pod {i} ready: {pod['pod_id']} @ {pod['ip']}:{pod['port']}")
        except Exception as e:
            log(f"Pod {i} provisioning failed: {e}")
            if not pods:
                raise
            log(f"Continuing with {len(pods)} pod(s)")
            break
    return pods


def _bootstrap_pod(pod: dict, pod_index: int) -> None:
    """Bootstrap a single pod with code, deps, and credentials."""
    log(f"Bootstrapping pod {pod_index} ({pod['pod_id']})...")
    _launch.bootstrap(pod["ip"], pod["port"])
    log(f"Pod {pod_index} bootstrapped")


def _run_pod_phases(
    pod: dict,
    model_index: int,
    sweep_count: int,
    wandb_key: str,
) -> dict:
    """Run phases 2→3→4 on a single pod for one model. Returns summary."""
    ip, port = pod["ip"], pod["port"]
    env = {"WANDB_API_KEY": wandb_key}
    model_names = ["deberta", "roberta", "deberta_base"]
    name = model_names[model_index]

    results = {}
    for phase_num in [2, 3, 4]:
        phase_start = time.time()
        cmd = (
            f"cd /root/crosswalk && python -m classifier.lambda.train_all_v8 "
            f"--phase {phase_num} --model-index {model_index}"
        )
        if phase_num == 3:
            cmd += f" --sweep-count {sweep_count}"

        log(f"[pod-{model_index}] Phase {phase_num} starting ({name})")
        try:
            _launch._ssh(ip, port, cmd, env=env)
            elapsed = time.time() - phase_start
            log(f"[pod-{model_index}] Phase {phase_num} done in {elapsed/60:.1f}m")
            results[f"phase{phase_num}"] = {"status": "ok", "elapsed": elapsed}
        except Exception as e:
            log(f"[pod-{model_index}] Phase {phase_num} FAILED: {e}")
            results[f"phase{phase_num}"] = {"status": "failed", "error": str(e)}
            break

    return {"model": name, "model_index": model_index, **results}


def _rsync_from_pod(pod: dict, pod_index: int) -> None:
    """Rsync training artifacts from a pod."""
    ip, port = pod["ip"], pod["port"]
    log(f"Rsyncing from pod {pod_index}...")
    _launch._rsync_from(ip, port, "/root/crosswalk/runs/v8b/", "./runs/v8b/")
    _launch._rsync_from(ip, port, "/root/crosswalk/data/processed/", "./data/processed/")
    _launch._rsync_from(ip, port, "/root/crosswalk/data/features/", "./data/features/")


def full_pipeline(
    sweep_count: int = 50,
    max_pods: int = 3,
    local_only: bool = False,
) -> None:
    start = time.time()
    log("=" * 60)
    log("v8b MULTI-GPU PIPELINE STARTING")
    log(f"  sweep_count={sweep_count}, max_pods={max_pods}")
    log("=" * 60)

    log("Phase 0: OpenCRE extraction with hierarchy pairs")
    subprocess.run(
        [sys.executable, "-m", "classifier.lambda.train_all_v8", "--phase", "0"],
        check=True,
    )

    log("Phase 1: v8b training data assembly (hierarchy labels)")
    subprocess.run(
        [sys.executable, "-m", "classifier.lambda.train_all_v8", "--phase", "1"],
        check=True,
    )

    n_models = 3
    wandb_key = _launch._get_credential("wandb/api-key")

    if not local_only:
        n_pods = min(max_pods, n_models)
        log(f"Provisioning {n_pods} pod(s) for {n_models} models...")
        pods = _provision_pods(n_pods)
        actual_pods = len(pods)

        try:
            for i, pod in enumerate(pods):
                _bootstrap_pod(pod, i)

            if actual_pods >= n_models:
                log(f"Launching {n_models} models on {actual_pods} pods in PARALLEL")
                with concurrent.futures.ThreadPoolExecutor(max_workers=actual_pods) as ex:
                    futures = {
                        ex.submit(
                            _run_pod_phases, pods[i], i, sweep_count, wandb_key
                        ): i
                        for i in range(n_models)
                    }
                    for future in concurrent.futures.as_completed(futures):
                        idx = futures[future]
                        try:
                            result = future.result()
                            log(f"[pod-{idx}] completed: {json.dumps(result, default=str)}")
                        except Exception as e:
                            log(f"[pod-{idx}] EXCEPTION: {e}")
            else:
                log(f"Only {actual_pods} pod(s) available — running models sequentially per pod")
                for model_idx in range(n_models):
                    pod = pods[model_idx % actual_pods]
                    result = _run_pod_phases(pod, model_idx, sweep_count, wandb_key)
                    log(f"Model {model_idx} done: {json.dumps(result, default=str)}")

            log("Rsyncing artifacts from all pods...")
            for i, pod in enumerate(pods):
                _rsync_from_pod(pod, i)

        finally:
            for pod in pods:
                log(f"Terminating pod {pod['pod_id']}...")
                try:
                    _provision.terminate_pod(pod["pod_id"])
                except Exception as e:
                    log(f"  terminate failed: {e}")
    else:
        log("Running GPU phases locally (--local-only)")
        for phase in [2, 3, 4]:
            cmd = [sys.executable, "-m", "classifier.lambda.train_all_v8",
                   "--phase", str(phase)]
            if phase == 3:
                cmd += ["--sweep-count", str(sweep_count)]
            subprocess.run(cmd, check=True)

    log("Phase 5: GATv2 retrain (local)")
    subprocess.run(
        [sys.executable, "-m", "classifier.lambda.train_all_v8", "--phase", "5"],
        check=True,
    )

    log("Phase 6: Stacker sweep (local)")
    subprocess.run(
        [sys.executable, "-m", "classifier.lambda.train_all_v8", "--phase", "6"],
        check=True,
    )

    log("Phase 7: Final stacker (local)")
    subprocess.run(
        [sys.executable, "-m", "classifier.lambda.train_all_v8", "--phase", "7"],
        check=True,
    )

    log("Phase 8: Conformal calibration (local)")
    subprocess.run(
        [sys.executable, "-m", "classifier.lambda.train_all_v8", "--phase", "8"],
        check=True,
    )

    log("Phase 9: Sacred evaluation (local)")
    subprocess.run(
        [sys.executable, "-m", "classifier.lambda.train_all_v8", "--phase", "9"],
        check=True,
    )

    elapsed = time.time() - start
    hours = elapsed / 3600
    log(f"\n{'='*60}")
    log(f"  v8b PIPELINE COMPLETE ({hours:.1f} hours)")
    log(f"{'='*60}")


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="v8b multi-GPU pipeline")
    parser.add_argument("--sweep-count", type=int, default=50)
    parser.add_argument("--max-pods", type=int, default=3, help="Max RunPod instances (1-3)")
    parser.add_argument("--local-only", action="store_true")
    parser.add_argument("--fastest", action="store_true", help="Show fastest GPU")
    parser.add_argument("--terminate-all", action="store_true")
    args = parser.parse_args()

    if args.terminate_all:
        for pod in _provision.get_running_pods():
            _provision.terminate_pod(pod["id"])
        return

    if args.fastest:
        gpu = _provision.find_fastest_available()
        print(f"Fastest available: {gpu}")
        return

    full_pipeline(
        sweep_count=args.sweep_count,
        max_pods=args.max_pods,
        local_only=args.local_only,
    )


if __name__ == "__main__":
    main()
