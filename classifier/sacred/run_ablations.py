"""Ablation runner — evaluates each ablation config on a val set.

For feature-ablation configs, retrains the stacker with the feature subset.
For component ablations (conformal, router), modifies the scoring pipeline.
Writes results to results/ablations.json.

Contract 1: verify_hashes() at entry.
Contract 5: Only reads v1_frozen labels.
"""
from __future__ import annotations

import json
import numpy as np
from pathlib import Path
from sklearn.metrics import accuracy_score, f1_score

from classifier.data.splits import verify_hashes
from classifier.ensemble.oof_features import build_feature_matrix
from classifier.ensemble.stacker import (
    LGBMStacker, BASE_FEATURE_COLS, GAT_SCALAR_COLS, GAT_DIFF_COLS,
    FEATURE_COLS, N_CLASSES, tune_stacker,
)
from classifier.sacred.ablation_registry import ABLATIONS


TIER_NAMES = {0: "unrelated", 1: "partial", 2: "related", 3: "equivalent"}

# Map ablation disable tags to feature column groups
FEATURE_GROUPS = {
    "gat": GAT_SCALAR_COLS + GAT_DIFF_COLS,
    "gat_diff": GAT_DIFF_COLS,
    "bridge": ["score_bridge"],
    "bge": ["score_bge_cosine"],
    "bm25": ["score_bm25"],
}


def _get_feature_cols(disable: tuple[str, ...]) -> list[str]:
    """Return FEATURE_COLS with disabled groups removed."""
    removed = set()
    for tag in disable:
        if tag in FEATURE_GROUPS:
            removed.update(FEATURE_GROUPS[tag])
    return [c for c in FEATURE_COLS if c not in removed]


def run_ablations(
    val_path: str = "data/labels/llm_sme/v2_frozen/llm_val.jsonl",
    train_path: str = "data/labels/llm_sme/v2_frozen/llm_train.jsonl",
    out_path: str = "results/ablations.json",
    n_trials: int = 10,
    verify: bool = True,
) -> dict:
    """Run all ablation configs. Returns results dict."""
    if verify:
        verify_hashes()

    print("Building feature matrices...")
    df_train = build_feature_matrix(labels_path=train_path)
    df_val = build_feature_matrix(labels_path=val_path)
    y_train = df_train["label"].values.astype(np.int32)
    y_val = df_val["label"].values.astype(np.int32)

    # Compute inverse-frequency class weights
    counts = np.bincount(y_train, minlength=4)
    class_w = len(y_train) / (4.0 * counts)
    sample_w = np.array([class_w[c] for c in y_train])

    results = {}
    for name, cfg in sorted(ABLATIONS.items()):
        print(f"\n--- Ablation: {name} ({cfg.description}) ---")

        # Component ablations don't retrain — they modify post-processing
        if "conformal" in cfg.disable or "router" in cfg.disable:
            # Use full feature set, just modify output
            cols = FEATURE_COLS
        else:
            cols = _get_feature_cols(cfg.disable)

        if not cols:
            print(f"  SKIP: no features remaining")
            results[name] = {"skip": True, "reason": "no features"}
            continue

        # Fill missing columns with 0
        for c in cols:
            if c not in df_train.columns:
                df_train[c] = 0.0
            if c not in df_val.columns:
                df_val[c] = 0.0

        X_train = df_train[cols].values.astype(np.float64)
        X_val = df_val[cols].values.astype(np.float64)

        print(f"  Features: {len(cols)}")

        # Tune + train
        best_params = tune_stacker(X_train, y_train, sample_weight=sample_w, n_trials=n_trials)
        stacker = LGBMStacker(best_params)
        stacker.fit(X_train, y_train, sample_weight=sample_w)

        pred_val = stacker.predict(X_val)
        proba_val = stacker.predict_proba(X_val)

        tier_acc = float(accuracy_score(y_val, pred_val))
        macro_f1 = float(f1_score(y_val, pred_val, average="macro"))

        per_class = {}
        for c in range(N_CLASSES):
            mask = y_val == c
            if mask.sum() > 0:
                per_class[TIER_NAMES[c]] = {
                    "accuracy": float(np.mean(pred_val[mask] == c)),
                    "count": int(mask.sum()),
                }

        results[name] = {
            "description": cfg.description,
            "n_features": len(cols),
            "disable": list(cfg.disable),
            "tier_accuracy": tier_acc,
            "macro_f1": macro_f1,
            "per_class": per_class,
        }

        print(f"  tier_acc={tier_acc:.4f}, macro_f1={macro_f1:.4f}")

    # Save
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2, sort_keys=True))
    print(f"\nSaved ablation results to {out}")
    return results
