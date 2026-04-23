"""Diagnose v7c model performance on the frozen test set.

Loads v7c predictions (or recomputes them) and produces a structured diagnosis
report covering confusion matrix, per-class metrics, error modes, and
bottleneck identification.

Usage:
    python -m classifier.scripts.diagnose_v7c

Output:
    runs/v8_diagnosis/v7c_diagnosis.json
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    f1_score,
)

from classifier.data.tier_mapper import TierLabel, map_expert_tier

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TEST_PATH = Path("data/splits/human_test_frozen.jsonl")
V7C_RUN_DIR = Path("runs/v7c_sacred")
PREDICTIONS_PATH = V7C_RUN_DIR / "test_predictions.json"
MODEL_PATH = V7C_RUN_DIR / "logreg_model.pkl"
RESULTS_PATH = V7C_RUN_DIR / "results.json"
OUTPUT_DIR = Path("runs/v8_diagnosis")
OUTPUT_PATH = OUTPUT_DIR / "v7c_diagnosis.json"

TIER_NAMES = ["UNRELATED", "PARTIAL", "RELATED", "EQUIVALENT"]
TIER_INT_TO_NAME = {int(TierLabel.UNRELATED): "UNRELATED",
                    int(TierLabel.PARTIAL): "PARTIAL",
                    int(TierLabel.RELATED): "RELATED",
                    int(TierLabel.EQUIVALENT): "EQUIVALENT"}


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_jsonl(path: Path) -> list[dict]:
    with open(path) as f:
        return [json.loads(line) for line in f]


def load_test_labels() -> tuple[list[dict], np.ndarray]:
    """Load frozen test set and return (records, y_true)."""
    records = load_jsonl(TEST_PATH)
    y_true = np.array([int(map_expert_tier(r["expert_tier"])) for r in records])
    return records, y_true


# ---------------------------------------------------------------------------
# Prediction loading strategies
# ---------------------------------------------------------------------------

def try_load_predictions_json() -> np.ndarray | None:
    """Strategy 1: Load pre-computed predictions from test_predictions.json."""
    if not PREDICTIONS_PATH.exists():
        return None
    try:
        data = json.loads(PREDICTIONS_PATH.read_text())
        # Support list of ints or list of dicts with 'pred' key
        if isinstance(data, list):
            if len(data) == 0:
                return None
            if isinstance(data[0], int):
                return np.array(data, dtype=np.int32)
            if isinstance(data[0], dict) and "pred" in data[0]:
                return np.array([d["pred"] for d in data], dtype=np.int32)
        print(f"  [WARN] Unexpected format in {PREDICTIONS_PATH}, skipping.")
        return None
    except Exception as e:
        print(f"  [WARN] Failed to load {PREDICTIONS_PATH}: {e}")
        return None


def try_recompute_from_model(test_records: list[dict]) -> np.ndarray | None:
    """Strategy 2: Recompute predictions by running saved model on test features."""
    if not MODEL_PATH.exists():
        return None
    try:
        import pickle
        with open(MODEL_PATH, "rb") as f:
            bundle = pickle.load(f)
        model = bundle["model"]
        scaler = bundle["scaler"]
        feature_names = bundle.get("features", [])

        print(f"  [INFO] Loaded model from {MODEL_PATH}")
        print(f"  [INFO] Model features ({len(feature_names)}): {feature_names[:5]}...")

        # Build feature matrix using the same logic as v7c_sacred_run.py
        # Import the feature builders from the sacred run module
        try:
            from classifier.sacred.v7c_sacred_run import build_features
        except ImportError as e:
            print(f"  [WARN] Cannot import build_features: {e}")
            return None

        print("  [INFO] Building test features (may take a moment)...")
        X_test, _ = build_features(test_records, "human_test", include_ce=True)
        X_test_scaled = scaler.transform(X_test)
        y_pred = model.predict(X_test_scaled)
        print(f"  [INFO] Recomputed {len(y_pred)} predictions from model.")
        return y_pred.astype(np.int32)

    except Exception as e:
        print(f"  [WARN] Failed to recompute from model: {e}")
        return None


def try_load_from_results_json() -> np.ndarray | None:
    """Strategy 3: Reconstruct integer predictions from results.json confusion matrix.

    The confusion matrix in results.json encodes exactly how many times each
    (true, pred) pair occurred, so we can reconstruct y_true and y_pred up to
    row ordering (sufficient for aggregate metrics).
    """
    if not RESULTS_PATH.exists():
        return None
    try:
        results = json.loads(RESULTS_PATH.read_text())
        method_key = "B_full_pipeline"
        if "methods" not in results or method_key not in results["methods"]:
            return None

        cm_nested = results["methods"][method_key]["confusion_matrix"]
        # cm_nested: {true_name: {pred_name: count}}
        lower_names = ["unrelated", "partial", "related", "equivalent"]
        name_to_int = {n: i for i, n in enumerate(lower_names)}

        y_true_list: list[int] = []
        y_pred_list: list[int] = []
        for true_name, pred_counts in cm_nested.items():
            true_int = name_to_int[true_name]
            for pred_name, count in pred_counts.items():
                pred_int = name_to_int[pred_name]
                y_true_list.extend([true_int] * count)
                y_pred_list.extend([pred_int] * count)

        if not y_true_list:
            return None

        print(f"  [INFO] Reconstructed {len(y_pred_list)} predictions from results.json "
              f"(Method B: full pipeline).")
        # Store y_true separately via global — signal to caller
        _reconstructed_y_true_cache.clear()
        _reconstructed_y_true_cache.extend(y_true_list)
        return np.array(y_pred_list, dtype=np.int32)

    except Exception as e:
        print(f"  [WARN] Failed to reconstruct from results.json: {e}")
        return None


# Mutable cache for reconstructed y_true (set by try_load_from_results_json)
_reconstructed_y_true_cache: list[int] = []


# ---------------------------------------------------------------------------
# Diagnosis computation
# ---------------------------------------------------------------------------

def compute_diagnosis(
    y_true: np.ndarray,
    y_pred: np.ndarray,
) -> dict:
    """Compute the full v8 diagnosis structure."""
    labels = [0, 1, 2, 3]

    # Distribution of true labels
    true_counts = Counter(y_true.tolist())
    distribution = {TIER_INT_TO_NAME[i]: int(true_counts.get(i, 0)) for i in labels}

    # Confusion matrix (4x4, rows=true, cols=pred)
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    cm_list = cm.tolist()

    # Per-class precision/recall/F1 via classification_report
    report = classification_report(
        y_true, y_pred,
        labels=labels,
        target_names=TIER_NAMES,
        output_dict=True,
        zero_division=0,
    )

    per_class_f1 = {name: float(report[name]["f1-score"]) for name in TIER_NAMES}
    per_class_precision = {name: float(report[name]["precision"]) for name in TIER_NAMES}
    per_class_recall = {name: float(report[name]["recall"]) for name in TIER_NAMES}

    macro_f1 = float(f1_score(y_true, y_pred, average="macro", labels=labels, zero_division=0))
    exact_accuracy = float(np.mean(y_true == y_pred))

    # Bottleneck: lowest per-class F1
    bottleneck_class = min(per_class_f1, key=lambda k: per_class_f1[k])
    bottleneck_f1 = per_class_f1[bottleneck_class]

    # Top error modes: count (true, pred) mismatches
    error_counter: Counter = Counter()
    for t, p in zip(y_true.tolist(), y_pred.tolist()):
        if t != p:
            error_counter[(TIER_INT_TO_NAME[t], TIER_INT_TO_NAME[p])] += 1

    top_error_modes = [
        {"true": true_name, "pred": pred_name, "count": count}
        for (true_name, pred_name), count in error_counter.most_common(10)
    ]

    # Recommendation based on bottleneck
    recommendation = _generate_recommendation(
        bottleneck_class=bottleneck_class,
        bottleneck_f1=bottleneck_f1,
        per_class_f1=per_class_f1,
        distribution=distribution,
        top_error_modes=top_error_modes,
        macro_f1=macro_f1,
    )

    return {
        "distribution": distribution,
        "confusion_matrix": cm_list,
        "per_class_f1": per_class_f1,
        "per_class_precision": per_class_precision,
        "per_class_recall": per_class_recall,
        "macro_f1": macro_f1,
        "exact_accuracy": exact_accuracy,
        "bottleneck_class": bottleneck_class,
        "bottleneck_f1": bottleneck_f1,
        "top_error_modes": top_error_modes,
        "recommendation": recommendation,
    }


def _generate_recommendation(
    bottleneck_class: str,
    bottleneck_f1: float,
    per_class_f1: dict,
    distribution: dict,
    top_error_modes: list[dict],
    macro_f1: float,
) -> str:
    """Generate a targeted recommendation based on diagnosis."""
    lines: list[str] = []

    # Overall health
    if macro_f1 >= 0.65:
        lines.append(f"Macro F1 of {macro_f1:.3f} is strong overall.")
    elif macro_f1 >= 0.45:
        lines.append(f"Macro F1 of {macro_f1:.3f} is moderate; room for improvement.")
    else:
        lines.append(f"Macro F1 of {macro_f1:.3f} is weak; substantial improvement needed.")

    # Bottleneck focus
    n_bottleneck = distribution.get(bottleneck_class, 0)
    lines.append(
        f"Bottleneck class is {bottleneck_class} (F1={bottleneck_f1:.3f}, "
        f"n={n_bottleneck} in test set)."
    )

    # Dominant error pattern
    if top_error_modes:
        top = top_error_modes[0]
        lines.append(
            f"Most common error: true={top['true']} predicted as {top['pred']} "
            f"({top['count']} times)."
        )

    # Class-specific guidance
    if bottleneck_class == "EQUIVALENT":
        lines.append(
            "EQUIVALENT recall is low — consider adding more EQUIVALENT training examples "
            "or using a lower decision threshold for the EQUIVALENT class."
        )
    elif bottleneck_class == "RELATED":
        lines.append(
            "RELATED class is hardest to distinguish — "
            "feature engineering for semantic similarity signals may help."
        )
    elif bottleneck_class == "PARTIAL":
        lines.append(
            "PARTIAL class confusion is common due to its overlap with RELATED and UNRELATED — "
            "consider soft-label re-weighting or boundary-aware loss."
        )
    elif bottleneck_class == "UNRELATED":
        lines.append(
            "UNRELATED precision/recall is low — "
            "negative mining to add harder negatives may improve discrimination."
        )

    # v8 direction
    lines.append(
        "For v8: prioritize data augmentation and feature improvements targeting "
        f"the {bottleneck_class} class to raise macro F1 above 0.65."
    )

    return " ".join(lines)


# ---------------------------------------------------------------------------
# Human-readable report
# ---------------------------------------------------------------------------

def print_report(diagnosis: dict, source: str) -> None:
    """Print a human-readable diagnosis report."""
    sep = "=" * 60
    print(f"\n{sep}")
    print("v7c DIAGNOSIS REPORT")
    print(f"Source: {source}")
    print(sep)

    print("\n--- Label Distribution (true) ---")
    for cls, n in diagnosis["distribution"].items():
        bar = "#" * n
        print(f"  {cls:12s}: {n:3d}  {bar}")

    print("\n--- Confusion Matrix (rows=true, cols=pred) ---")
    header = f"{'':12s}" + "".join(f"  {name:>10s}" for name in TIER_NAMES)
    print(header)
    for i, true_name in enumerate(TIER_NAMES):
        row = f"{true_name:12s}"
        for j in range(4):
            row += f"  {diagnosis['confusion_matrix'][i][j]:10d}"
        print(row)

    print("\n--- Per-Class Metrics ---")
    print(f"  {'Class':12s} {'Precision':>10s} {'Recall':>10s} {'F1':>10s}")
    for cls in TIER_NAMES:
        p = diagnosis["per_class_precision"][cls]
        r = diagnosis["per_class_recall"][cls]
        f = diagnosis["per_class_f1"][cls]
        print(f"  {cls:12s} {p:10.4f} {r:10.4f} {f:10.4f}")

    print(f"\n  Macro F1:        {diagnosis['macro_f1']:.4f}")
    print(f"  Exact Accuracy:  {diagnosis['exact_accuracy']:.4f}")

    print(f"\n--- Bottleneck ---")
    print(f"  Class: {diagnosis['bottleneck_class']}  (F1 = {diagnosis['bottleneck_f1']:.4f})")

    print("\n--- Top Error Modes ---")
    for em in diagnosis["top_error_modes"][:5]:
        print(f"  true={em['true']:12s} -> pred={em['pred']:12s}  count={em['count']}")

    print("\n--- Recommendation ---")
    # Word-wrap at ~70 chars
    words = diagnosis["recommendation"].split()
    line = "  "
    for word in words:
        if len(line) + len(word) + 1 > 72:
            print(line)
            line = "  " + word
        else:
            line += (" " if line.strip() else "") + word
    if line.strip():
        print(line)

    print(f"\n{sep}\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 60)
    print("v7c Diagnosis Script")
    print("=" * 60)

    # 1. Load ground-truth labels
    if not TEST_PATH.exists():
        print(f"ERROR: Test file not found: {TEST_PATH}")
        sys.exit(1)
    test_records, y_true = load_test_labels()
    print(f"  Loaded {len(test_records)} frozen test labels.")
    print(f"  True distribution: {dict(Counter(y_true.tolist()))}")

    # 2. Obtain predictions (try three strategies in order)
    y_pred: np.ndarray | None = None
    source: str = "unknown"

    print("\n--- Locating v7c predictions ---")

    # Strategy 1: pre-saved test_predictions.json
    y_pred = try_load_predictions_json()
    if y_pred is not None:
        source = str(PREDICTIONS_PATH)
        print(f"  [OK] Loaded predictions from {PREDICTIONS_PATH}")

    # Strategy 2: rebuild from saved model artifacts
    if y_pred is None:
        print(f"  {PREDICTIONS_PATH} not found. Trying model rebuild...")
        y_pred = try_recompute_from_model(test_records)
        if y_pred is not None:
            source = f"recomputed from {MODEL_PATH}"

    # Strategy 3: reconstruct from results.json confusion matrix
    if y_pred is None:
        print(f"  Model rebuild failed or not available. Trying results.json...")
        y_pred = try_load_from_results_json()
        if y_pred is not None:
            # Use the reconstructed y_true (from CM, ordering differs)
            y_true = np.array(_reconstructed_y_true_cache, dtype=np.int32)
            source = f"reconstructed from {RESULTS_PATH} (Method B: full pipeline)"

    if y_pred is None:
        print(
            "\nERROR: Could not obtain v7c predictions. Tried:\n"
            f"  1. {PREDICTIONS_PATH}  (not found)\n"
            f"  2. {MODEL_PATH}  (rebuild failed)\n"
            f"  3. {RESULTS_PATH}  (not found or parse error)\n\n"
            "Please run the v7c sacred run first:\n"
            "  python -m classifier.sacred.v7c_sacred_run\n"
        )
        sys.exit(1)

    if len(y_pred) != len(y_true):
        print(
            f"ERROR: Prediction length mismatch: y_pred={len(y_pred)}, y_true={len(y_true)}"
        )
        sys.exit(1)

    # 3. Compute diagnosis
    print(f"\n--- Computing diagnosis ({len(y_true)} pairs) ---")
    diagnosis = compute_diagnosis(y_true, y_pred)

    # 4. Save output
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_payload = dict(diagnosis)
    output_payload["source"] = source
    output_payload["n_test"] = len(y_true)
    OUTPUT_PATH.write_text(json.dumps(output_payload, indent=2))
    print(f"\n  Diagnosis saved to {OUTPUT_PATH}")

    # 5. Print human-readable report
    print_report(diagnosis, source=source)


if __name__ == "__main__":
    main()
