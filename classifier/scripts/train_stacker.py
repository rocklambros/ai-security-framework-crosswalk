"""Train the LightGBM stacker on v1_frozen features.

1. Builds feature matrix from Plan 3 cache + bridge scores
2. Tunes hyperparams via Optuna (20 trials)
3. Trains final model on llm_train, evaluates on llm_val
4. Saves model + config + registry row

Contract 1: verify_hashes() + verify_label_hashes() at entry.
Contract 5: Only reads v1_frozen labels.
Contract 6: Appends to runs/registry.jsonl.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

assert "human_test_frozen" not in ",".join(sys.argv), "Contract 2: frozen test is off limits"

from classifier.data.splits import verify_hashes
from classifier.labeling.freeze import verify_label_hashes
from classifier.ensemble.oof_features import build_feature_matrix
from classifier.ensemble.stacker import tune_stacker, train_and_evaluate, FEATURE_COLS

import numpy as np


def main():
    verify_hashes()
    verify_label_hashes()

    print("Building train feature matrix...")
    df_train = build_feature_matrix(
        labels_path="data/labels/llm_sme/v1_frozen/llm_train.jsonl",
    )
    print(f"  Train: {len(df_train)} rows, features: {FEATURE_COLS}")

    print("Building val feature matrix...")
    df_val = build_feature_matrix(
        labels_path="data/labels/llm_sme/v1_frozen/llm_val.jsonl",
    )
    print(f"  Val: {len(df_val)} rows")

    X_train = df_train[FEATURE_COLS].values
    y_train = df_train["label"].values
    w_train = df_train["weight"].values
    X_val = df_val[FEATURE_COLS].values
    y_val = df_val["label"].values

    print("Tuning hyperparameters (20 trials)...")
    best_params = tune_stacker(X_train, y_train, sample_weight=w_train, n_trials=20)
    print(f"  Best params: {best_params}")

    print("Training final model...")
    result = train_and_evaluate(
        X_train, y_train, X_val, y_val,
        sample_weight=w_train,
        params=best_params,
    )

    print(f"\n=== Stacker Results ===")
    print(f"  Run ID:       {result['run_id']}")
    print(f"  Train acc:    {result['train_acc']:.4f}")
    print(f"  Val acc:      {result['val_acc']:.4f}")
    print(f"  Train logloss: {result['train_logloss']:.4f}")
    print(f"  Val logloss:  {result['val_logloss']:.4f}")
    print(f"  Saved to:     {result['run_dir']}")


if __name__ == "__main__":
    main()
