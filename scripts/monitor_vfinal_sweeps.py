"""Monitor v_final W&B sweeps — prints a concise status report.

Queries the crosswalk-vfinal W&B project for active/completed runs,
reports per-model sweep progress, key metrics, and flags issues.

Usage: python scripts/monitor_vfinal_sweeps.py
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))


def get_sweep_status() -> str:
    lines = []
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    lines.append(f"=== v_final SWEEP MONITOR [{timestamp}] ===")

    try:
        import subprocess
        wandb_key = subprocess.run(
            ["pass", "wandb/api-key"], capture_output=True, text=True, check=True
        ).stdout.strip()
        os.environ["WANDB_API_KEY"] = wandb_key
        import wandb
        api = wandb.Api(timeout=30)
    except Exception as e:
        lines.append(f"ERROR: Cannot connect to W&B: {e}")
        return "\n".join(lines)

    project = "rockcyber/crosswalk-vfinal"
    model_groups = {
        "roberta": "vfinal-roberta-sweep",
        "deberta_base": "vfinal-deberta-sweep",
        "bge": "vfinal-bge-sweep",
    }

    try:
        runs = list(api.runs(project, per_page=200))
    except Exception as e:
        if "Could not find project" in str(e):
            lines.append("W&B project not created yet — sweeps haven't started.")
        else:
            lines.append(f"ERROR: Cannot fetch runs: {e}")
        # Still show pipeline log
        log_path = ROOT / "runs" / "vfinal" / "gpu_only.log"
        if log_path.exists():
            log_lines = log_path.read_text().strip().split("\n")
            last_10 = log_lines[-10:] if len(log_lines) >= 10 else log_lines
            lines.append("\nLatest pipeline log:")
            for ll in last_10:
                lines.append(f"  {ll}")
        return "\n".join(lines)

    if not runs:
        lines.append("No runs found yet — sweeps may not have started.")
        return "\n".join(lines)

    total_running = 0
    total_finished = 0
    total_failed = 0

    for model_name, group_name in model_groups.items():
        model_runs = [r for r in runs if r.group == group_name]
        running = [r for r in model_runs if r.state == "running"]
        finished = [r for r in model_runs if r.state == "finished"]
        failed = [r for r in model_runs if r.state in ("failed", "crashed")]

        total_running += len(running)
        total_finished += len(finished)
        total_failed += len(failed)

        lines.append(f"\n--- {model_name.upper()} ({group_name}) ---")
        lines.append(f"  Trials: {len(finished)} done, {len(running)} running, {len(failed)} failed / 25 total")

        if finished:
            # Best run by combined_f1
            best = max(finished, key=lambda r: r.summary.get("combined_f1", 0))
            best_cf1 = best.summary.get("combined_f1", 0)
            best_mf1 = best.summary.get("val_macro_f1", 0)
            best_loss = best.summary.get("val_loss", None)
            best_train_acc = best.summary.get("train_acc", None)
            best_val_acc = best.summary.get("val_acc", None)
            best_loss_type = best.config.get("loss_type", "?")

            lines.append(f"  BEST: combined_f1={best_cf1:.4f}, val_macro_f1={best_mf1:.4f}, loss={best_loss_type}")
            if best_loss is not None:
                lines.append(f"        val_loss={best_loss:.4f}")
            if best_train_acc is not None and best_val_acc is not None:
                gap = best_train_acc - best_val_acc
                lines.append(f"        train_acc={best_train_acc:.4f}, val_acc={best_val_acc:.4f}, gap={gap:.4f}")

            # Per-class F1 from best run
            per_class = {}
            for tier in ["UNRELATED", "PARTIAL", "RELATED", "EQUIVALENT"]:
                key = f"val_f1_{tier}"
                val = best.summary.get(key)
                if val is not None:
                    per_class[tier] = val
            if per_class:
                lines.append(f"        per-class F1: {', '.join(f'{k}={v:.3f}' for k, v in per_class.items())}")

            # Median combined_f1 across finished runs
            all_cf1 = [r.summary.get("combined_f1", 0) for r in finished]
            median_cf1 = sorted(all_cf1)[len(all_cf1) // 2]
            lines.append(f"  Median combined_f1={median_cf1:.4f} (range: {min(all_cf1):.4f} - {max(all_cf1):.4f})")

            # Loss type distribution
            loss_types = {}
            for r in finished:
                lt = r.config.get("loss_type", "?")
                cf1 = r.summary.get("combined_f1", 0)
                if lt not in loss_types or cf1 > loss_types[lt]:
                    loss_types[lt] = cf1
            if loss_types:
                lines.append(f"  Best by loss: {', '.join(f'{k}={v:.4f}' for k, v in sorted(loss_types.items()))}")

        # Check for issues
        issues = []

        # CollapseGuard: any run with val_macro_f1 < 0.20
        collapsed = [r for r in model_runs if r.summary.get("val_macro_f1", 1) < 0.20]
        if collapsed:
            issues.append(f"COLLAPSE: {len(collapsed)} runs with val_macro_f1 < 0.20")

        # OverfittingGuard: train_acc - val_acc > 0.25
        overfit = [
            r for r in model_runs
            if (r.summary.get("train_acc", 0) - r.summary.get("val_acc", 0)) > 0.25
        ]
        if overfit:
            issues.append(f"OVERFITTING: {len(overfit)} runs with train/val gap > 25pp")

        # Leakage: val_acc >= 0.98
        leaky = [r for r in model_runs if r.summary.get("val_acc", 0) >= 0.98]
        if leaky:
            issues.append(f"LEAKAGE WARNING: {len(leaky)} runs with val_acc >= 0.98")

        # All failed
        if len(failed) > 5:
            issues.append(f"HIGH FAILURE RATE: {len(failed)} trials failed")

        if issues:
            for issue in issues:
                lines.append(f"  !! {issue}")
        elif finished:
            lines.append(f"  OK — no guard violations detected")

        # Currently running details
        if running:
            for r in running[:2]:
                epoch = r.summary.get("epoch", "?")
                cur_f1 = r.summary.get("val_macro_f1", "?")
                lines.append(f"  Running: {r.id} epoch={epoch}, val_f1={cur_f1}")

    # Summary
    lines.append(f"\n=== SUMMARY: {total_finished} done, {total_running} running, {total_failed} failed ===")

    # Check pipeline log for phase status
    log_path = ROOT / "runs" / "vfinal" / "gpu_only.log"
    if log_path.exists():
        log_lines = log_path.read_text().strip().split("\n")
        last_5 = log_lines[-5:] if len(log_lines) >= 5 else log_lines
        lines.append("\nLatest pipeline log:")
        for ll in last_5:
            lines.append(f"  {ll}")

    return "\n".join(lines)


if __name__ == "__main__":
    print(get_sweep_status())
