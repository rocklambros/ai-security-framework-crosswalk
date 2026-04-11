"""Phase 0 validation gate: LLM-as-judge quality check on human_cal_val pairs.

Run before committing to expensive bulk scoring. Scores the 50-pair validation
split with Sonnet (3 votes), applies an Opus tiebreaker on non-unanimous pairs,
and gates on macro F1 against human expert labels.
"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)

from classifier.data.split_human_cal import split_human_cal
from classifier.llm.cost_tracker import CostTracker
from classifier.llm.prompts import select_few_shot_examples
from classifier.llm.scorer import ScoredPair, opus_tiebreaker, score_pairs_bulk

RESULTS_PATH = Path("results/phase0_validation_gate.json")


async def run_validation_gate(
    min_macro_f1: float = 0.45,
    n_votes: int = 3,
    use_opus_tiebreaker: bool = True,
    wandb_run: Any = None,
) -> dict[str, Any]:
    """Run Phase 0 validation gate on human_cal_val pairs.

    Steps:
    1. Load human_cal train/val split.
    2. Select few-shot examples from train (5 per tier).
    3. Score human_cal_val (50 pairs) with Sonnet × n_votes via score_pairs_bulk.
    4. Run Opus tiebreaker on non-unanimous pairs (if use_opus_tiebreaker=True).
    5. Compute tier_accuracy, macro_f1, per_class_f1, confusion_matrix, n_unanimous.
    6. Print results clearly.
    7. Log metrics to wandb_run with "phase0/" prefix (if provided).
    8. Gate check: fail loudly if macro_f1 < min_macro_f1.
    9. Save result dict to results/phase0_validation_gate.json.
    10. Return result dict with gate_passed bool.
    """
    print("=" * 60)
    print("Phase 0 Validation Gate")
    print("=" * 60)

    # 1. Load train/val split
    print("\n[1/5] Loading human_cal split …")
    train_records, val_records, _idx_train, _idx_val = split_human_cal()
    print(f"  train={len(train_records)} val={len(val_records)}")

    # 2. Select few-shot examples
    print("\n[2/5] Selecting few-shot examples (5 per tier) …")
    few_shot_examples = select_few_shot_examples(train_records, n_per_tier=5)
    print(f"  Selected {len(few_shot_examples)} examples")

    # 3. Score val pairs with Sonnet
    print(f"\n[3/5] Scoring {len(val_records)} val pairs × {n_votes} votes …")
    cost_tracker = CostTracker()
    scored: list[ScoredPair] = await score_pairs_bulk(
        pairs=val_records,
        few_shot_examples=few_shot_examples,
        n_votes=n_votes,
        max_concurrent=20,
        cost_tracker=cost_tracker,
    )

    # 4. Opus tiebreaker on non-unanimous pairs
    n_unanimous_before = sum(1 for sp in scored if sp.is_unanimous)
    if use_opus_tiebreaker:
        disagreed = [sp for sp in scored if not sp.is_unanimous]
        if disagreed:
            print(
                f"\n[4/5] Opus tiebreaker on {len(disagreed)} non-unanimous pairs …"
            )
            await opus_tiebreaker(
                disagreed=disagreed,
                few_shot_examples=few_shot_examples,
                max_concurrent=10,
                cost_tracker=cost_tracker,
            )
        else:
            print("\n[4/5] All pairs unanimous — no Opus calls needed.")
    else:
        print("\n[4/5] Opus tiebreaker skipped (use_opus_tiebreaker=False).")

    n_unanimous_after = sum(1 for sp in scored if sp.is_unanimous)

    # 5. Compute metrics
    print("\n[5/5] Computing metrics …")
    y_true = [r["tier_label"] for r in val_records]
    y_pred = [sp.final_tier for sp in scored]

    tier_accuracy = float(accuracy_score(y_true, y_pred))
    macro_f1 = float(f1_score(y_true, y_pred, average="macro", zero_division=0))
    per_class_f1_arr = f1_score(y_true, y_pred, average=None, zero_division=0, labels=[0, 1, 2, 3])
    per_class_f1: dict[str, float] = {
        f"tier_{t}": float(v) for t, v in enumerate(per_class_f1_arr)
    }
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1, 2, 3])
    report_str = classification_report(
        y_true, y_pred, labels=[0, 1, 2, 3],
        target_names=["Tier0", "Tier1", "Tier2", "Tier3"],
        zero_division=0,
    )

    # 6. Print results
    print("\n--- Results ---")
    print(f"  n_val          : {len(val_records)}")
    print(f"  n_unanimous    : {n_unanimous_after} / {len(scored)} "
          f"(before tiebreaker: {n_unanimous_before})")
    print(f"  tier_accuracy  : {tier_accuracy:.4f}")
    print(f"  macro_f1       : {macro_f1:.4f}  (threshold={min_macro_f1})")
    print("\nPer-class F1:")
    for label, val in per_class_f1.items():
        print(f"  {label}: {val:.4f}")
    print("\nConfusion matrix (rows=true, cols=pred, tiers 0-3):")
    print(cm)
    print("\nClassification report:")
    print(report_str)
    cost_tracker.log()

    # 7. WandB logging
    if wandb_run is not None:
        metrics: dict[str, float] = {
            "phase0/tier_accuracy": tier_accuracy,
            "phase0/macro_f1": macro_f1,
            "phase0/n_unanimous": float(n_unanimous_after),
            "phase0/n_val": float(len(val_records)),
        }
        metrics.update({f"phase0/{k}_f1": v for k, v in per_class_f1.items()})
        wandb_run.log(metrics)
        print("  Logged metrics to wandb.")

    # 8. Gate check
    gate_passed = macro_f1 >= min_macro_f1
    print("\n" + "=" * 60)
    if gate_passed:
        print(f"GATE PASSED  macro_f1={macro_f1:.4f} >= {min_macro_f1}")
    else:
        print(f"GATE FAILED  macro_f1={macro_f1:.4f} < {min_macro_f1}")
        print(
            "Action: Do NOT proceed to bulk scoring. Investigate prompt quality,\n"
            "  few-shot balance, or model selection before re-running the gate."
        )
    print("=" * 60)

    # 9. Build and save result dict
    result: dict[str, Any] = {
        "gate_passed": gate_passed,
        "min_macro_f1": min_macro_f1,
        "macro_f1": macro_f1,
        "tier_accuracy": tier_accuracy,
        "per_class_f1": per_class_f1,
        "confusion_matrix": cm.tolist(),
        "n_val": len(val_records),
        "n_unanimous": n_unanimous_after,
        "n_unanimous_before_tiebreaker": n_unanimous_before,
        "n_votes": n_votes,
        "use_opus_tiebreaker": use_opus_tiebreaker,
        "cost_summary": cost_tracker.summary(),
    }

    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with RESULTS_PATH.open("w") as f:
        json.dump(result, f, indent=2)
    print(f"\nSaved results → {RESULTS_PATH}")

    # 10. Return
    return result


if __name__ == "__main__":
    asyncio.run(run_validation_gate())
