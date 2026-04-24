"""v8 Sacred Run: evaluate v8 stacker on frozen test, compare against v7c.

Pre-registered constants from classifier/sacred/pre_registered.json.
Uses the same frozen test as v7c (179 pairs) for direct comparison.
"""
from __future__ import annotations

import json
import time
from collections import Counter
from pathlib import Path

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)

from classifier.data.tier_mapper import TierLabel, map_expert_tier
from classifier.features.gap_penalty import compute_gap_penalties

TEST_PATH = Path("data/splits/human_test_frozen.jsonl")
V8_MODEL_DIR = Path("runs/v8b/stacker/final")
V7C_RESULTS = Path("runs/v7c_sacred/results.json")
OUTPUT_DIR = Path("runs/v8b_sacred")
PRE_REG = Path("classifier/sacred/pre_registered.json")

TIER_NAMES = ["UNRELATED", "PARTIAL", "RELATED", "EQUIVALENT"]


def load_jsonl(path: Path) -> list[dict]:
    with open(path) as f:
        return [json.loads(line) for line in f]


def run_v8_sacred() -> dict:
    """Run the v8 sacred evaluation."""
    t0 = time.time()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    pre_reg = json.loads(PRE_REG.read_text())
    seed = pre_reg["seeds"]["sacred_run_seed"]

    test_data = load_jsonl(TEST_PATH)
    y_true = np.array([int(map_expert_tier(r["expert_tier"])) for r in test_data])

    print(f"Frozen test: {len(test_data)} pairs")
    print(f"Distribution: {dict(Counter(int(y) for y in y_true))}")

    from classifier.ensemble.stacker import LGBMStacker
    import pickle

    model_path = V8_MODEL_DIR / "model.pkl"
    if model_path.exists():
        with open(model_path, "rb") as f:
            bundle = pickle.load(f)
        model = bundle["model"]
        scaler = bundle.get("scaler")
    else:
        model_txt = V8_MODEL_DIR / "model.txt"
        stacker = LGBMStacker(version="v3")
        stacker.model = __import__("lightgbm").Booster(model_file=str(model_txt))
        model = stacker
        scaler = None

    ce_features = np.load("data/processed/ce_features_v8b_deberta.npz")["test_features"]
    gat_features = np.load("data/features/gat_embeddings_v8b.npz")["test_pair_features"]
    import pandas as pd
    baseline_df = pd.read_parquet("data/features/baseline_features.parquet")
    gap_penalties = compute_gap_penalties(test_data)

    X_test = np.column_stack([
        ce_features,
        gat_features,
        baseline_df.iloc[:len(test_data)][["score_bm25", "score_bridge"]].values,
        gap_penalties.reshape(-1, 1),
    ])

    if scaler:
        X_test = scaler.transform(X_test)

    if hasattr(model, "predict"):
        y_pred = model.predict(X_test)
        if hasattr(y_pred[0], "__len__"):
            y_pred = np.argmax(y_pred, axis=1)
        y_pred = y_pred.astype(int)
    else:
        y_pred = np.argmax(model.predict(X_test), axis=1)

    if hasattr(model, "predict_proba"):
        y_proba = model.predict_proba(X_test)
    else:
        y_proba = model.predict(X_test)

    exact_acc = float(accuracy_score(y_true, y_pred))
    macro_f1 = float(f1_score(y_true, y_pred, average="macro", zero_division=0))
    per_class = classification_report(y_true, y_pred, target_names=TIER_NAMES, output_dict=True, zero_division=0)
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1, 2, 3])

    adjacent_acc = float(np.mean(np.abs(y_true - y_pred) <= 1))

    v7c = {}
    if V7C_RESULTS.exists():
        v7c_data = json.loads(V7C_RESULTS.read_text())
        methods = v7c_data.get("methods", {})
        b_method = methods.get("B_full_pipeline", {})
        if b_method:
            v7c = {
                "exact_acc": b_method.get("accuracy"),
                "macro_f1": b_method.get("macro_f1"),
                "adjacent_acc": b_method.get("adjacent_accuracy"),
            }

    print(f"\n{'='*60}")
    print(f"v8 SACRED EVALUATION RESULTS")
    print(f"{'='*60}")
    print(f"\nExact accuracy:    {exact_acc:.4f}" + (f" (v7c: {v7c.get('exact_acc', '?')})" if v7c else ""))
    print(f"Adjacent accuracy: {adjacent_acc:.4f}" + (f" (v7c: {v7c.get('adjacent_acc', '?')})" if v7c else ""))
    print(f"Macro F1:          {macro_f1:.4f}" + (f" (v7c: {v7c.get('macro_f1', '?')})" if v7c else ""))
    print(f"\nPer-class F1:")
    for name in TIER_NAMES:
        f1 = per_class[name]["f1-score"]
        print(f"  {name:12s}: {f1:.4f}")

    print(f"\nConfusion matrix (rows=true, cols=pred):")
    print(f"{'':>12} " + " ".join(f"{n:>10}" for n in TIER_NAMES))
    for i, name in enumerate(TIER_NAMES):
        print(f"{name:>12} " + " ".join(f"{cm[i, j]:>10}" for j in range(4)))

    results = {
        "version": "v8b",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "seed": seed,
        "test_size": len(test_data),
        "exact_acc": exact_acc,
        "adjacent_acc": adjacent_acc,
        "macro_f1": macro_f1,
        "per_class": {
            name: {"f1-score": per_class[name]["f1-score"],
                   "precision": per_class[name]["precision"],
                   "recall": per_class[name]["recall"],
                   "support": per_class[name]["support"]}
            for name in TIER_NAMES
        },
        "confusion_matrix": cm.tolist(),
        "v7c_comparison": v7c,
        "improvement": {
            "exact_acc_delta": exact_acc - v7c.get("exact_acc", exact_acc),
            "macro_f1_delta": macro_f1 - v7c.get("macro_f1", macro_f1),
        } if v7c else {},
    }

    (OUTPUT_DIR / "results.json").write_text(json.dumps(results, indent=2))

    predictions = {
        "y_true": y_true.tolist(),
        "y_pred": y_pred.tolist(),
        "y_proba": y_proba.tolist() if isinstance(y_proba, np.ndarray) else y_proba,
        "test_size": len(test_data),
    }
    (OUTPUT_DIR / "test_predictions.json").write_text(json.dumps(predictions, indent=2))

    elapsed = time.time() - t0
    print(f"\nSacred evaluation complete in {elapsed:.1f}s")
    print(f"Results saved to {OUTPUT_DIR}")
    return results


if __name__ == "__main__":
    run_v8_sacred()
