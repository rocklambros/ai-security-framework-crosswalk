"""Evaluate the EnsembleScorer on llm_val and compute delta vs Plan 3 baselines.

Metrics: tier_accuracy, MRR@1, per-class accuracy, abstention stats.

Contract 1: verify_hashes() + verify_label_hashes() at entry.
Contract 5: Only reads v1_frozen labels.
"""
from __future__ import annotations

import sys

_SACRED = "human_test" + "_frozen"
assert _SACRED not in ",".join(sys.argv), "Contract 2: frozen test is off limits"

import json
import numpy as np
from pathlib import Path
from collections import Counter

from classifier.data.splits import verify_hashes
from classifier.labeling.freeze import verify_label_hashes
from classifier.ensemble.oof_features import build_feature_matrix, TIER_MAP
from classifier.ensemble.stacker import LGBMStacker, FEATURE_COLS, N_CLASSES
from classifier.ensemble.conformal import MondrianConformal
from classifier.ensemble.router import DisagreementRouter
from classifier.ensemble.scorer import EnsembleScorer

TIER_NAMES = {v: k for k, v in TIER_MAP.items()}


def compute_mrr(y_true: np.ndarray, proba: np.ndarray) -> float:
    """Mean Reciprocal Rank: for each sample, rank of the true class."""
    n = len(y_true)
    rr_sum = 0.0
    for i in range(n):
        ranked = np.argsort(-proba[i])
        rank = int(np.where(ranked == y_true[i])[0][0]) + 1
        rr_sum += 1.0 / rank
    return rr_sum / n


def main():
    verify_hashes()
    verify_label_hashes()

    run_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    if run_dir is None:
        runs = sorted(Path("runs/stacker").glob("stacker-*"))
        if not runs:
            print("No stacker runs found")
            sys.exit(1)
        run_dir = runs[-1]

    print(f"=== Ensemble Evaluation: {run_dir.name} ===\n")

    # Load ensemble
    scorer = EnsembleScorer.from_run_dir(run_dir)
    stacker = scorer.stacker

    # Build val features
    print("Building val feature matrix...")
    df_val = build_feature_matrix(
        labels_path="data/labels/llm_sme/v1_frozen/llm_val.jsonl",
    )
    X_val = df_val[FEATURE_COLS].values.astype(np.float64)
    y_val = df_val["label"].values.astype(np.int32)

    proba_val = stacker.predict_proba(X_val)
    pred_val = np.argmax(proba_val, axis=1)

    # --- Overall metrics ---
    tier_acc = float(np.mean(pred_val == y_val))
    mrr = compute_mrr(y_val, proba_val)
    print(f"Tier accuracy:  {tier_acc:.4f}")
    print(f"MRR:            {mrr:.4f}")

    # --- Per-class metrics ---
    print("\nPer-class accuracy:")
    for cls in range(N_CLASSES):
        mask = y_val == cls
        if mask.sum() == 0:
            continue
        cls_acc = float(np.mean(pred_val[mask] == cls))
        cls_name = TIER_NAMES.get(cls, str(cls))
        print(f"  {cls_name:12s} ({mask.sum():3d} samples): {cls_acc:.4f}")

    # --- Conformal stats ---
    conf_sets = scorer.conformal.predict_sets(proba_val)
    avg_set = np.mean([len(s) for s in conf_sets])
    coverage = np.mean([y_val[i] in s for i, s in enumerate(conf_sets)])
    print(f"\nConformal set size (avg): {avg_set:.2f}")
    print(f"Conformal marginal coverage: {coverage:.4f}")

    # --- Router stats ---
    review_mask = scorer.router.route(proba_val)
    n_review = int(review_mask.sum())
    n_pass = len(review_mask) - n_review
    if n_pass > 0:
        pass_acc = float(np.mean(pred_val[~review_mask] == y_val[~review_mask]))
    else:
        pass_acc = 0.0
    print(f"\nRouter abstention: {n_review}/{len(review_mask)} ({100*n_review/len(review_mask):.1f}%)")
    print(f"Precision on passed: {pass_acc:.4f} ({n_pass} samples)")

    # --- Confusion matrix ---
    print("\nConfusion matrix (rows=true, cols=pred):")
    print(f"{'':12s}", end="")
    for c in range(N_CLASSES):
        print(f" {TIER_NAMES.get(c, str(c)):>10s}", end="")
    print()
    for true_cls in range(N_CLASSES):
        row_mask = y_val == true_cls
        name = TIER_NAMES.get(true_cls, str(true_cls))
        print(f"{name:12s}", end="")
        for pred_cls in range(N_CLASSES):
            count = int(np.sum((y_val == true_cls) & (pred_val == pred_cls)))
            print(f" {count:10d}", end="")
        print()

    # --- Go/no-go: R@1 >= 0.30 ---
    r_at_1 = float(np.mean(pred_val == y_val))  # same as tier_acc for multiclass
    print(f"\n=== GO/NO-GO: tier_acc (R@1) = {r_at_1:.4f} ", end="")
    if r_at_1 >= 0.30:
        print("PASS >=0.30 ===")
    else:
        print("FAIL <0.30 ===")

    # Save eval results
    eval_results = {
        "run_id": run_dir.name,
        "val_samples": len(y_val),
        "tier_accuracy": tier_acc,
        "mrr": mrr,
        "conformal_avg_set_size": avg_set,
        "conformal_marginal_coverage": coverage,
        "router_tau": scorer.router.tau,
        "abstention_rate": n_review / len(review_mask),
        "precision_on_passed": pass_acc,
        "per_class_accuracy": {
            TIER_NAMES.get(c, str(c)): float(np.mean(pred_val[y_val == c] == c))
            for c in range(N_CLASSES) if (y_val == c).sum() > 0
        },
        "label_distribution": dict(Counter(y_val.tolist())),
    }
    eval_path = run_dir / "eval_llm_val.json"
    eval_path.write_text(json.dumps(eval_results, indent=2, sort_keys=True))
    print(f"\nSaved eval to {eval_path}")


if __name__ == "__main__":
    main()
