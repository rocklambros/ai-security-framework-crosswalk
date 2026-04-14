"""Calibrate conformal + router on llm_val, assemble EnsembleScorer.

1. Loads trained stacker from a run directory
2. Builds val feature matrix
3. Calibrates MondrianConformal on llm_val (human_cal deferred to Plan 6)
4. Tunes DisagreementRouter tau on llm_val for >= 95% precision
5. Saves conformal, router, scorer.json manifest

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

from classifier.data.splits import verify_hashes
from classifier.labeling.freeze import verify_label_hashes
from classifier.ensemble.oof_features import build_feature_matrix
from classifier.ensemble.stacker import LGBMStacker, FEATURE_COLS, N_CLASSES
from classifier.ensemble.conformal import MondrianConformal
from classifier.ensemble.router import DisagreementRouter


def main():
    verify_hashes()
    verify_label_hashes()

    run_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    if run_dir is None:
        # Find most recent stacker run
        runs = sorted(Path("runs/stacker").glob("stacker-*"))
        if not runs:
            print("No stacker runs found")
            sys.exit(1)
        run_dir = runs[-1]

    print(f"Loading stacker from {run_dir}")
    stacker = LGBMStacker.load(run_dir / "model.txt")

    print("Building val feature matrix...")
    df_val = build_feature_matrix(
        labels_path="data/labels/llm_sme/v2_frozen/llm_val.jsonl",
    )
    print(f"  Val: {len(df_val)} rows")

    X_val = df_val[FEATURE_COLS].values.astype(np.float64)
    y_val = df_val["label"].values.astype(np.int32)

    proba_val = stacker.predict_proba(X_val)
    pred_val = np.argmax(proba_val, axis=1)

    # --- Mondrian Conformal calibration ---
    print("\nCalibrating Mondrian conformal on llm_val (alpha=0.10)...")
    conformal = MondrianConformal(alpha=0.10)
    conformal.calibrate(proba_val, y_val)

    print("  q_hat per tier:")
    for tier, q in sorted(conformal.q_hat.items()):
        print(f"    tier {tier}: q_hat={q:.4f}, coverage={conformal.coverage.get(tier, 0):.4f}")

    conf_sets = conformal.predict_sets(proba_val)
    avg_set_size = np.mean([len(s) for s in conf_sets])
    print(f"  Average conformal set size: {avg_set_size:.2f}")

    conformal_path = run_dir / "conformal.json"
    conformal.save(conformal_path)
    print(f"  Saved to {conformal_path}")

    # --- Router tau tuning ---
    print("\nTuning KL-disagreement router for >= 95% precision...")
    router = DisagreementRouter(reference="uniform")
    tau = router.tune_tau(proba_val, y_val, pred_val, target_precision=0.95)

    scores = router.score(proba_val)
    review_mask = router.route(proba_val)
    n_review = int(review_mask.sum())
    n_pass = len(review_mask) - n_review
    pass_acc = float(np.mean(pred_val[~review_mask] == y_val[~review_mask])) if n_pass > 0 else 0.0

    print(f"  tau = {tau:.4f}")
    print(f"  Abstained (needs_review): {n_review}/{len(review_mask)} ({100*n_review/len(review_mask):.1f}%)")
    print(f"  Passed: {n_pass}/{len(review_mask)} ({100*n_pass/len(review_mask):.1f}%)")
    print(f"  Precision on passed: {pass_acc:.4f}")

    router_path = run_dir / "router.json"
    router.save(router_path)
    print(f"  Saved to {router_path}")

    # --- Scorer manifest ---
    scorer_manifest = {
        "scorer_name": "ensemble_v1",
        "version": "0.1.0",
        "stacker_path": str(run_dir / "model.txt"),
        "conformal_path": str(conformal_path),
        "router_path": str(router_path),
        "feature_cols": FEATURE_COLS,
        "n_classes": N_CLASSES,
        "calibration_split": "llm_val",
        "conformal_alpha": 0.10,
        "router_tau": tau,
        "val_metrics": {
            "val_acc": float(np.mean(pred_val == y_val)),
            "avg_conformal_set_size": avg_set_size,
            "abstention_rate": n_review / len(review_mask),
            "precision_on_passed": pass_acc,
        },
    }
    scorer_path = run_dir / "scorer.json"
    scorer_path.write_text(json.dumps(scorer_manifest, indent=2, sort_keys=True))
    print(f"\n=== Scorer manifest saved to {scorer_path} ===")

    # --- Quick sanity: load EnsembleScorer from run_dir ---
    from classifier.ensemble.scorer import EnsembleScorer
    scorer = EnsembleScorer.from_run_dir(run_dir)
    print(f"  Loaded EnsembleScorer: {scorer.name} v{scorer.version}")
    print("  Roundtrip OK.")


if __name__ == "__main__":
    main()
