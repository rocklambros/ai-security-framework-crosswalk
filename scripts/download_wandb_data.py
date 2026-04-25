"""
Pre-download WandB run histories to local JSON files.

Usage:
    python scripts/download_wandb_data.py

Outputs:
    runs/v8b_diagnosis/wandb_runs.json     - all runs from rockcyber/crosswalk-v8b
    runs/vfinal/wandb_best_runs.json       - 3 specific runs from rockcyber/crosswalk-vfinal
"""

import json
import subprocess
import sys
from pathlib import Path

import wandb

HISTORY_KEYS = [
    "epoch",
    "train_loss",
    "val_kl_loss",
    "combined_f1",
    "expert_val_macro_f1",
    "n_unique_preds",
    "pred_class_0_pct",
    "pred_class_1_pct",
    "pred_class_2_pct",
    "pred_class_3_pct",
    "collapse_recovery",
    "train_acc",
]

REPO_ROOT = Path(__file__).resolve().parent.parent


def get_wandb_key() -> str:
    result = subprocess.run(
        ["pass", "wandb/api-key"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def filter_history(history_rows: list[dict]) -> list[dict]:
    """Keep only the desired keys from each history row."""
    out = []
    for row in history_rows:
        filtered = {k: row[k] for k in HISTORY_KEYS if k in row}
        if filtered:
            out.append(filtered)
    return out


def download_v8b(api: wandb.Api) -> None:
    out_path = REPO_ROOT / "runs" / "v8b_diagnosis" / "wandb_runs.json"
    print(f"Fetching all runs from rockcyber/crosswalk-v8b ...")
    runs = api.runs("rockcyber/crosswalk-v8b")
    records = []
    for run in runs:
        print(f"  run {run.id} ({run.name}) state={run.state}")
        history = filter_history(list(run.scan_history()))
        record = {
            "id": run.id,
            "name": run.name,
            "state": run.state,
            "n_unique_preds": run.summary.get("n_unique_preds"),
            "combined_f1": run.summary.get("combined_f1"),
            "history": history,
        }
        records.append(record)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(records, f, indent=2)
    print(f"Wrote {len(records)} runs to {out_path}")


def sanitize_summary(summary_dict: dict) -> dict:
    """Recursively convert WandB summary objects to plain Python dicts/lists."""
    out = {}
    for k, v in summary_dict.items():
        if isinstance(v, dict):
            out[k] = sanitize_summary(v)
        elif isinstance(v, list):
            out[k] = [sanitize_summary(i) if isinstance(i, dict) else i for i in v]
        else:
            try:
                json.dumps(v)
                out[k] = v
            except (TypeError, ValueError):
                out[k] = str(v)
    return out


def download_vfinal(api: wandb.Api) -> None:
    out_path = REPO_ROOT / "runs" / "vfinal" / "wandb_best_runs.json"
    runs_to_fetch = {
        "roberta": "ounfajaa",
        "deberta_base": "ux5wt9hz",
        "bge": "5e3003m8",
    }
    records = {}
    for model_key, run_id in runs_to_fetch.items():
        run_path = f"rockcyber/crosswalk-vfinal/{run_id}"
        print(f"Fetching {model_key} run {run_id} from rockcyber/crosswalk-vfinal ...")
        run = api.run(run_path)
        history = filter_history(list(run.scan_history()))
        raw_summary = {k: v for k, v in run.summary.items()}
        records[model_key] = {
            "id": run.id,
            "name": run.name,
            "state": run.state,
            "n_unique_preds": run.summary.get("n_unique_preds"),
            "combined_f1": run.summary.get("combined_f1"),
            "summary": sanitize_summary(raw_summary),
            "history": history,
        }
        print(f"  {model_key}: {len(history)} history rows")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(records, f, indent=2)
    print(f"Wrote {len(records)} runs to {out_path}")


def main() -> None:
    key = get_wandb_key()
    api = wandb.Api(api_key=key)

    download_v8b(api)
    download_vfinal(api)

    print("\nAll done.")


if __name__ == "__main__":
    main()
