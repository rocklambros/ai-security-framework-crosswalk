"""Train logistic / LightGBM / ordinal weight models and compare them.

Train on the AIUC-1 expert mappings, evaluate on the AIUC-1 anchor
holdout and the held-out NIST RMF validation set, and persist the best
model's learned weights.

Usage::

    python -m mapping_engine.scripts.learn_weights
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from mapping_engine.calibration.weight_learner import (
    FEATURES,
    HAND_WEIGHTS,
    compare_to_hand_tuned,
    evaluate_hand_tuned,
    evaluate_model,
    train_lightgbm,
    train_logistic,
    train_ordinal,
)
from mapping_engine.calibration.weight_stability import analyze_weight_stability
from mapping_engine.config import load_pair_config
from mapping_engine.engine.graph import load_graph

REPO = Path(__file__).resolve().parents[2]


def _holdout_pairs(cfg) -> list[tuple[str, str]]:
    pairs = cfg.anchors.pairs
    idx = set(cfg.anchors.holdout_indices or [])
    return [(pairs[i].source, pairs[i].target) for i in idx]


def main() -> None:
    train_df = pd.read_csv(REPO / "data/processed/training_data.csv")
    nist_df = pd.read_csv(REPO / "data/processed/nist_validation_data.csv")

    G = load_graph(REPO / "data/processed/nodes.json", REPO / "data/processed/edges.json")
    cfg = load_pair_config("aiuc_1__owasp_agentic", validate_anchors_in=G)
    holdout = _holdout_pairs(cfg)
    hold_mask = train_df.apply(
        lambda r: (r["source_node_id"], r["target_node_id"]) in holdout, axis=1
    )
    holdout_df = train_df[hold_mask].copy()

    # Train all three models on the AIUC training set (ex-holdout)
    fit_df = train_df[~hold_mask].copy()
    log_model, log_coefs = train_logistic(fit_df)
    lgb_model, lgb_imp = train_lightgbm(fit_df)
    ord_model, ord_coefs = train_ordinal(fit_df)

    rows = [
        ("Hand-tuned",
         evaluate_hand_tuned(fit_df),
         evaluate_hand_tuned(holdout_df) if len(holdout_df) else {},
         evaluate_hand_tuned(nist_df)),
        ("Logistic",
         evaluate_model(log_model, fit_df, "logistic"),
         evaluate_model(log_model, holdout_df, "logistic") if len(holdout_df) else {},
         evaluate_model(log_model, nist_df, "logistic")),
        ("LightGBM",
         evaluate_model(lgb_model, fit_df, "lightgbm"),
         evaluate_model(lgb_model, holdout_df, "lightgbm") if len(holdout_df) else {},
         evaluate_model(lgb_model, nist_df, "lightgbm")),
        ("Ordinal",
         evaluate_model(ord_model, fit_df, "ordinal"),
         evaluate_model(ord_model, holdout_df, "ordinal") if len(holdout_df) else {},
         evaluate_model(ord_model, nist_df, "ordinal")),
    ]

    print(f"\n{'Model':<12} | {'Train Acc':>9} | {'Hold Acc':>9} | {'NIST Acc':>9} | {'NIST F1':>9}")
    print("-" * 65)
    for name, train_m, hold_m, nist_m in rows:
        print(
            f"{name:<12} | "
            f"{train_m.get('accuracy', 0):>9.3f} | "
            f"{hold_m.get('accuracy', 0):>9.3f} | "
            f"{nist_m.get('accuracy', 0):>9.3f} | "
            f"{nist_m.get('f1', 0):>9.3f}"
        )

    # Pick the best model on NIST accuracy
    best_name, best_metric = "Hand-tuned", rows[0][3].get("accuracy", 0.0)
    for name, _, _, nist_m in rows[1:]:
        if nist_m.get("accuracy", 0.0) > best_metric:
            best_name, best_metric = name, nist_m.get("accuracy", 0.0)

    print(f"\nBest model on NIST accuracy: {best_name} ({best_metric:.3f})")
    hand_nist = rows[0][3].get("accuracy", 0.0)
    if best_name != "Hand-tuned" and (best_metric - hand_nist) > 0.05:
        print(f"  → Beats hand-tuned by {(best_metric-hand_nist)*100:.1f} pts; new default candidate.")
    else:
        print("  → Margin too small; keeping hand-tuned as default.")

    # Stability analysis on the chosen learned model (default to logistic)
    stability = analyze_weight_stability(fit_df, log_model, "logistic")

    out = {
        "models": {
            "logistic": {"coefficients": log_coefs},
            "lightgbm": {"feature_importance": lgb_imp},
            "ordinal": {"coefficients": ord_coefs},
        },
        "evaluations": {
            name: {"train": tr, "holdout": ho, "nist": ni}
            for name, tr, ho, ni in rows
        },
        "best_model": best_name,
        "hand_weights": HAND_WEIGHTS,
        "compare_logistic_vs_hand_nist": compare_to_hand_tuned(
            nist_df, HAND_WEIGHTS, log_model, "logistic"
        ),
        "weight_stability_logistic": stability,
    }
    out_path = REPO / "data" / "processed" / "weight_comparison.json"
    out_path.write_text(json.dumps(out, indent=2, default=str))
    print(f"\nWrote {out_path}")

    learned_path = REPO / "data" / "processed" / "learned_weights.json"
    learned_path.write_text(
        json.dumps(
            {
                "best_model": best_name,
                "logistic_coefficients": log_coefs,
                "lightgbm_feature_importance": lgb_imp,
                "ordinal_coefficients": ord_coefs,
            },
            indent=2,
        )
    )
    print(f"Wrote {learned_path}")

    stab_path = REPO / "data" / "processed" / "weight_stability.json"
    stab_path.write_text(json.dumps(stability, indent=2))
    print(f"Wrote {stab_path}")


if __name__ == "__main__":
    main()
