"""v_final 3-pod parallel GPU launcher.

Provisions fastest available GPUs (1 per model), bootstraps in parallel,
runs sweeps in parallel, rsyncs artifacts, terminates all pods.

Usage:
    python -m classifier.lambda.launch_vfinal
    python -m classifier.lambda.launch_vfinal --sweep-count 25
    python -m classifier.lambda.launch_vfinal --local-only
"""
from __future__ import annotations

import concurrent.futures
import importlib
import json
import sys
import time
from pathlib import Path

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


def _provision_pods(n_pods: int) -> list[dict]:
    gpu_type = _provision.find_fastest_available(min_vram_gb=48)
    log(f"Selected GPU: {gpu_type}")
    pods = []
    for i in range(n_pods):
        try:
            pod = _provision.create_pod(gpu_type, name=f"vfinal-{MODEL_NAMES[i]}")
            pods.append(pod)
            log(f"Pod {i} ({MODEL_NAMES[i]}) ready: {pod['pod_id']} @ {pod['ip']}:{pod['port']}")
        except Exception as e:
            log(f"Pod {i} provisioning failed: {e}")
            if not pods:
                raise
            break
    return pods


def _bootstrap_pod(pod: dict, pod_index: int) -> None:
    log(f"Bootstrapping pod {pod_index} ({MODEL_NAMES[pod_index]})...")
    _launch.bootstrap(pod["ip"], pod["port"])
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
            log(f"[{name}] Phase {phase_num} done in {elapsed/60:.1f}m")
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


def full_pipeline(sweep_count: int = 25, local_only: bool = False) -> None:
    import subprocess
    start = time.time()
    log("=" * 60)
    log("v_final PARALLEL GPU PIPELINE")
    log(f"  3 models, {sweep_count} trials each, parallel pods")
    log("=" * 60)

    log("Phase 0: Rebuild clean splits")
    subprocess.run(
        [sys.executable, "-m", "classifier.lambda.train_all_vfinal", "--phase", "0"],
        check=True,
    )

    log("Phase 1: Zero-shot BGE baseline")
    subprocess.run(
        [sys.executable, "-m", "classifier.lambda.train_all_vfinal", "--phase", "1"],
        check=True,
    )

    wandb_key = _launch._get_credential("wandb/api-key")

    if not local_only:
        log(f"Provisioning {N_MODELS} pods...")
        pods = _provision_pods(N_MODELS)

        try:
            log("Bootstrapping all pods in parallel...")
            with concurrent.futures.ThreadPoolExecutor(max_workers=len(pods)) as ex:
                list(ex.map(_bootstrap_pod, pods, range(len(pods))))

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
        log("Running locally (--local-only)")
        for phase in [2, 3]:
            for i in range(N_MODELS):
                cmd = [sys.executable, "-m", "classifier.lambda.train_all_vfinal",
                       "--phase", str(phase), "--model-index", str(i)]
                if phase == 2:
                    cmd += ["--sweep-count", str(sweep_count)]
                subprocess.run(cmd, check=True)

    log("Phase 4: Stacker sweep")
    subprocess.run(
        [sys.executable, "-m", "classifier.lambda.train_all_vfinal", "--phase", "4"],
        check=True,
    )

    log("Phase 5: Conformal calibration")
    subprocess.run(
        [sys.executable, "-m", "classifier.lambda.train_all_vfinal", "--phase", "5"],
        check=True,
    )

    log("Phase 6: Sacred evaluation")
    subprocess.run(
        [sys.executable, "-m", "classifier.lambda.train_all_vfinal", "--phase", "6"],
        check=True,
    )

    elapsed = time.time() - start
    log(f"\n{'='*60}")
    log(f"  v_final PIPELINE COMPLETE ({elapsed/3600:.1f} hours)")
    log(f"{'='*60}")


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="v_final parallel GPU pipeline")
    parser.add_argument("--sweep-count", type=int, default=25)
    parser.add_argument("--local-only", action="store_true")
    parser.add_argument("--terminate-all", action="store_true")
    args = parser.parse_args()

    if args.terminate_all:
        for pod in _provision.get_running_pods():
            _provision.terminate_pod(pod["id"])
        return

    full_pipeline(sweep_count=args.sweep_count, local_only=args.local_only)


if __name__ == "__main__":
    main()
