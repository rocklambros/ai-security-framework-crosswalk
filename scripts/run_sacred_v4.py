"""Sacred evaluation v4 — 4-method ablation (LLM direct / calibrated / CE / graph).

Runs four methods in ablation order and picks the best by macro F1.
Results are saved to results/sacred/sacred_{sha}.json.

Usage::

    python -c "from scripts.run_sacred_v4 import run_sacred_v4; run_sacred_v4()"
"""
from __future__ import annotations

import json
import subprocess
import sys
from math import ceil
from pathlib import Path
from typing import Optional

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score

from classifier.data.split_human_cal import split_human_cal
from classifier.features.fusion import build_fusion_matrix, load_llm_features

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TIER_NAMES = ["unrelated", "partial", "related", "equivalent"]

TIER_MAP = {"Direct": 3, "Related": 2, "Tangential": 1, "None": 0}

# Phase 4 ordering: train → val → cal → test
N_TRAIN = 6728
N_VAL = 1187
N_CAL = 150
N_TEST = 400
CAL_START = N_TRAIN + N_VAL          # 7915
TEST_START = N_TRAIN + N_VAL + N_CAL  # 8065

ALPHA = 0.1  # conformal coverage level: 1 - alpha = 0.90


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_test_labels() -> np.ndarray:
    """Load integer labels for human_test_frozen."""
    path = Path("data/splits/human_test_frozen.jsonl")
    labels = []
    with path.open() as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            labels.append(TIER_MAP[rec["expert_tier"]])
    return np.array(labels, dtype=np.int64)


def _load_human_cal_pairs() -> list[dict]:
    """Load all records from human_cal.jsonl (order matches split indices)."""
    path = Path("data/splits/human_cal.jsonl")
    rows = []
    with path.open() as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def _load_test_pairs() -> list[dict]:
    """Load all records from human_test_frozen.jsonl."""
    path = Path("data/splits/human_test_frozen.jsonl")
    rows = []
    with path.open() as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def _per_class_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> list[dict]:
    """Return per-class accuracy, f1, count for each tier."""
    metrics = []
    for cls_idx, cls_name in enumerate(TIER_NAMES):
        mask = y_true == cls_idx
        count = int(mask.sum())
        if count == 0:
            metrics.append({"tier": cls_name, "count": 0, "accuracy": None, "f1": None})
            continue
        correct = int((y_pred[mask] == cls_idx).sum())
        acc = correct / count
        f1 = float(f1_score(y_true, y_pred, labels=[cls_idx], average="macro", zero_division=0))
        metrics.append({"tier": cls_name, "count": count, "accuracy": float(acc), "f1": float(f1)})
    return metrics


def _confusion_matrix_dict(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    """Build confusion matrix as nested dict: true_tier → pred_tier → count."""
    cm: dict = {}
    for true_idx, true_name in enumerate(TIER_NAMES):
        row: dict = {}
        for pred_idx, pred_name in enumerate(TIER_NAMES):
            mask = (y_true == true_idx) & (y_pred == pred_idx)
            row[pred_name] = int(mask.sum())
        cm[true_name] = row
    return cm


def _conformal_coverage(
    proba_cal: np.ndarray,
    y_cal: np.ndarray,
    proba_test: np.ndarray,
    y_test: np.ndarray,
) -> dict:
    """Marginal conformal prediction (RAPS-style, label-marginal).

    Returns a dict with q_hat, mean_set_size, coverage, and pred_sets shape.
    """
    n_cal = len(y_cal)

    # Nonconformity scores on calibration set
    scores_cal = 1.0 - proba_cal[np.arange(n_cal), y_cal]

    # Quantile level (finite-sample correction)
    q_level = min(ceil((n_cal + 1) * (1 - ALPHA)) / n_cal, 1.0)
    q_hat = float(np.quantile(scores_cal, q_level))

    # Prediction sets on test
    pred_sets = (1.0 - proba_test) <= q_hat  # shape (n_test, 4)

    # Empirical coverage: fraction of test pairs where true label is in set
    n_test = len(y_test)
    coverage = float(np.mean(pred_sets[np.arange(n_test), y_test]))
    mean_set_size = float(pred_sets.sum(axis=1).mean())

    return {
        "q_hat": q_hat,
        "q_level": float(q_level),
        "coverage": coverage,
        "mean_set_size": mean_set_size,
    }


def _bootstrap_ci(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    n_resamples: int = 2000,
    seed: int = 42,
) -> dict:
    """95% bootstrap CI for macro F1."""
    rng = np.random.default_rng(seed)
    n = len(y_true)
    f1s = []
    for _ in range(n_resamples):
        idx = rng.integers(0, n, size=n)
        f1s.append(
            float(f1_score(y_true[idx], y_pred[idx], average="macro", zero_division=0))
        )
    f1s_arr = np.array(f1s)
    return {
        "mean": float(f1s_arr.mean()),
        "ci_lower": float(np.percentile(f1s_arr, 2.5)),
        "ci_upper": float(np.percentile(f1s_arr, 97.5)),
        "n_resamples": n_resamples,
    }


def _get_git_sha() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


# ---------------------------------------------------------------------------
# Method implementations
# ---------------------------------------------------------------------------

def _method_a(
    X_cal_llm: np.ndarray,
    idx_train: list[int],
    idx_val: list[int],
    y_cal: np.ndarray,
    X_test_llm: np.ndarray,
    y_test: np.ndarray,
) -> dict:
    """Method A: LLM-direct — score_to_tier on mean score, no training.

    LLM features are now [score_0, score_1, score_2, mean_score, confidence].
    Use mean_score (col 3) with default boundaries.
    """
    from classifier.llm.judge import score_to_tier

    y_pred_test = np.array([score_to_tier(s) for s in X_test_llm[:, 3]])
    macro_f1 = float(f1_score(y_test, y_pred_test, average="macro", zero_division=0))

    # Pseudo-probabilities from scores: use gaussian kernel around each tier center
    # Tier centers: 0→1.25, 1→3.75, 2→6.25, 3→8.75
    tier_centers = np.array([1.25, 3.75, 6.25, 8.75])
    sigma = 1.5

    def _score_to_proba(scores: np.ndarray) -> np.ndarray:
        """Convert mean scores to 4-class pseudo-probabilities."""
        # scores shape: (n,)
        dists = np.exp(-0.5 * ((scores[:, None] - tier_centers[None, :]) / sigma) ** 2)
        row_sums = dists.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1.0
        return dists / row_sums

    proba_cal_val = _score_to_proba(X_cal_llm[idx_val, 3])
    proba_test = _score_to_proba(X_test_llm[:, 3])

    return {
        "y_pred": y_pred_test,
        "proba_cal_val": proba_cal_val,
        "proba_test": proba_test,
        "macro_f1": macro_f1,
        "model": None,
    }


def _method_b(
    X_cal_llm: np.ndarray,
    idx_train: list[int],
    idx_val: list[int],
    y_cal: np.ndarray,
    X_test_llm: np.ndarray,
    y_test: np.ndarray,
) -> dict:
    """Method B: LLM-calibrated — RF on human_cal_train LLM features (5-dim)."""
    X_train = X_cal_llm[idx_train]
    y_train = y_cal[idx_train]

    rf = RandomForestClassifier(
        n_estimators=500, min_samples_leaf=2,
        class_weight="balanced_subsample", random_state=42,
    )
    rf.fit(X_train, y_train)

    y_pred_test = rf.predict(X_test_llm)
    macro_f1 = float(f1_score(y_test, y_pred_test, average="macro", zero_division=0))

    proba_cal_val = rf.predict_proba(X_cal_llm[idx_val])
    proba_test = rf.predict_proba(X_test_llm)

    # Align proba columns to TIER_NAMES order (0,1,2,3)
    proba_cal_val = _align_proba(proba_cal_val, rf.classes_)
    proba_test = _align_proba(proba_test, rf.classes_)

    return {
        "y_pred": y_pred_test,
        "proba_cal_val": proba_cal_val,
        "proba_test": proba_test,
        "macro_f1": macro_f1,
        "model": rf,
    }


def _method_c(
    idx_train: list[int],
    idx_val: list[int],
    y_cal: np.ndarray,
    y_test: np.ndarray,
    cal_pairs: list[dict],
    test_pairs: list[dict],
) -> dict:
    """Method C: LLM + graph fusion (306-dim), no CE.

    CE features (trained on algorithmic labels) hurt when evaluated on human
    labels, so this method skips CE and goes straight to LLM + graph.
    """
    from classifier.features.graph_features import (
        compute_pair_features,
        load_embeddings,
        load_graph,
    )

    gat_dict, n2v_dict = load_embeddings()
    graph = load_graph()

    graph_cal = compute_pair_features(cal_pairs, gat_dict, n2v_dict, graph)
    graph_test = compute_pair_features(test_pairs, gat_dict, n2v_dict, graph)

    X_cal_fused = build_fusion_matrix(
        "human_cal", ce_start=CAL_START, n_pairs=N_CAL,
        graph_features=graph_cal, include_ce=False, include_graph=True,
    )
    X_test_fused = build_fusion_matrix(
        "human_test_frozen", ce_start=TEST_START, n_pairs=N_TEST,
        graph_features=graph_test, include_ce=False, include_graph=True,
    )

    X_train = X_cal_fused[idx_train]
    y_train = y_cal[idx_train]

    rf = RandomForestClassifier(
        n_estimators=500, min_samples_leaf=3,
        class_weight="balanced_subsample", random_state=42,
    )
    rf.fit(X_train, y_train)

    y_pred_test = rf.predict(X_test_fused)
    macro_f1 = float(f1_score(y_test, y_pred_test, average="macro", zero_division=0))

    proba_cal_val = _align_proba(rf.predict_proba(X_cal_fused[idx_val]), rf.classes_)
    proba_test = _align_proba(rf.predict_proba(X_test_fused), rf.classes_)

    return {
        "y_pred": y_pred_test,
        "proba_cal_val": proba_cal_val,
        "proba_test": proba_test,
        "macro_f1": macro_f1,
        "model": rf,
    }


def _method_d(
    idx_train: list[int],
    idx_val: list[int],
    y_cal: np.ndarray,
    y_test: np.ndarray,
    cal_pairs: list[dict],
    test_pairs: list[dict],
    graph_cal: np.ndarray,
    graph_test: np.ndarray,
) -> dict:
    """Method D: LLM + CE + graph fusion (314-dim)."""
    X_cal_fused = build_fusion_matrix(
        "human_cal",
        CAL_START,
        N_CAL,
        pairs=cal_pairs,
        graph_features=graph_cal,
        include_graph=True,
    )
    X_test_fused = build_fusion_matrix(
        "human_test_frozen",
        TEST_START,
        N_TEST,
        pairs=test_pairs,
        graph_features=graph_test,
        include_graph=True,
    )

    X_train = X_cal_fused[idx_train]
    y_train = y_cal[idx_train]

    rf = RandomForestClassifier(
        n_estimators=500, min_samples_leaf=3,
        class_weight="balanced_subsample", random_state=42,
    )
    rf.fit(X_train, y_train)

    y_pred_test = rf.predict(X_test_fused)
    macro_f1 = float(f1_score(y_test, y_pred_test, average="macro", zero_division=0))

    proba_cal_val = _align_proba(rf.predict_proba(X_cal_fused[idx_val]), rf.classes_)
    proba_test = _align_proba(rf.predict_proba(X_test_fused), rf.classes_)

    return {
        "y_pred": y_pred_test,
        "proba_cal_val": proba_cal_val,
        "proba_test": proba_test,
        "macro_f1": macro_f1,
        "model": rf,
    }


def _align_proba(proba: np.ndarray, classes: np.ndarray) -> np.ndarray:
    """Re-order LR probability columns so column i = class i (0..3).

    sklearn may omit classes not present in training; this pads zeros for
    missing classes and reorders to match TIER_NAMES indexing (0, 1, 2, 3).
    """
    n = proba.shape[0]
    aligned = np.zeros((n, 4), dtype=np.float64)
    for col_idx, cls in enumerate(classes):
        cls_int = int(cls)
        if 0 <= cls_int <= 3:
            aligned[:, cls_int] = proba[:, col_idx]
    return aligned


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run_sacred_v4() -> dict:
    """Run 4-method ablation on human_test_frozen and persist results.

    Returns
    -------
    dict
        Full results dict (also written to results/sacred/sacred_{sha}.json).
    """
    # ------------------------------------------------------------------
    # 1. Load shared data
    # ------------------------------------------------------------------
    print("Loading human_cal split …")
    train_records, val_records, idx_train, idx_val = split_human_cal()

    # Labels for the full cal set (150), indexed into by idx_train / idx_val
    cal_pairs = _load_human_cal_pairs()
    y_cal_full = np.array(
        [TIER_MAP[r["expert_tier"]] for r in cal_pairs], dtype=np.int64
    )

    test_pairs = _load_test_pairs()
    y_test = _load_test_labels()

    # LLM features for cal and test (used in Methods A & B)
    print("Loading LLM features …")
    X_cal_llm = load_llm_features("human_cal")      # (150, 5)
    X_test_llm = load_llm_features("human_test_frozen")  # (400, 5)

    # Labels for validation slice
    y_cal_val = y_cal_full[idx_val]

    # ------------------------------------------------------------------
    # 2. Compute graph features (shared by Methods C & D)
    # ------------------------------------------------------------------
    from classifier.features.graph_features import (
        compute_pair_features,
        load_embeddings,
        load_graph,
    )

    print("Loading graph features …")
    gat_dict, n2v_dict = load_embeddings()
    graph = load_graph()
    graph_cal = compute_pair_features(cal_pairs, gat_dict, n2v_dict, graph)
    graph_test = compute_pair_features(test_pairs, gat_dict, n2v_dict, graph)

    # ------------------------------------------------------------------
    # 3. Run all four methods
    # ------------------------------------------------------------------
    print("Method A: LLM-direct …")
    result_a = _method_a(X_cal_llm, idx_train, idx_val, y_cal_full, X_test_llm, y_test)
    print(f"  macro_f1 = {result_a['macro_f1']:.4f}")

    print("Method B: LLM-calibrated (RF) …")
    result_b = _method_b(X_cal_llm, idx_train, idx_val, y_cal_full, X_test_llm, y_test)
    print(f"  macro_f1 = {result_b['macro_f1']:.4f}")

    print("Method C: LLM + graph (RF, no CE) …")
    result_c = _method_c(idx_train, idx_val, y_cal_full, y_test, cal_pairs, test_pairs)
    print(f"  macro_f1 = {result_c['macro_f1']:.4f}")

    print("Method D: LLM + CE + graph (RF) …")
    result_d = _method_d(idx_train, idx_val, y_cal_full, y_test, cal_pairs, test_pairs, graph_cal, graph_test)
    print(f"  macro_f1 = {result_d['macro_f1']:.4f}")

    # ------------------------------------------------------------------
    # 4. Select best method
    # ------------------------------------------------------------------
    methods = [
        ("A_llm_direct",      result_a),
        ("B_llm_rf",          result_b),
        ("C_llm_graph_rf",    result_c),
        ("D_llm_ce_graph_rf", result_d),
    ]

    best_name, best_result = max(methods, key=lambda kv: kv[1]["macro_f1"])
    print(f"\nBest method: {best_name} (macro_f1={best_result['macro_f1']:.4f})")

    y_pred_best = best_result["y_pred"]

    # ------------------------------------------------------------------
    # 4. Per-class metrics
    # ------------------------------------------------------------------
    per_class = _per_class_metrics(y_test, y_pred_best)

    # ------------------------------------------------------------------
    # 5. Confusion matrix
    # ------------------------------------------------------------------
    confusion = _confusion_matrix_dict(y_test, y_pred_best)

    # ------------------------------------------------------------------
    # 6. Conformal prediction (marginal)
    # ------------------------------------------------------------------
    conformal = _conformal_coverage(
        proba_cal=best_result["proba_cal_val"],
        y_cal=y_cal_val,
        proba_test=best_result["proba_test"],
        y_test=y_test,
    )

    # ------------------------------------------------------------------
    # 7. Bootstrap CI
    # ------------------------------------------------------------------
    print("Computing bootstrap CI …")
    bootstrap = _bootstrap_ci(y_test, y_pred_best)

    # ------------------------------------------------------------------
    # 8. Aggregate results
    # ------------------------------------------------------------------
    ablation_summary = [
        {"method": name, "macro_f1": float(res["macro_f1"])}
        for name, res in methods
    ]

    tier_accuracy = float(np.mean(y_pred_best == y_test))

    results: dict = {
        "best_method": best_name,
        "macro_f1": float(best_result["macro_f1"]),
        "tier_accuracy": tier_accuracy,
        "ablation": ablation_summary,
        "per_class": per_class,
        "confusion_matrix": confusion,
        "conformal": conformal,
        "bootstrap_ci": bootstrap,
        "n_test": int(len(y_test)),
        "n_cal_train": int(len(idx_train)),
        "n_cal_val": int(len(idx_val)),
        "tier_names": TIER_NAMES,
        "alpha": ALPHA,
    }

    # ------------------------------------------------------------------
    # 9. Persist to results/sacred/
    # ------------------------------------------------------------------
    sha = _get_git_sha()
    results["git_sha"] = sha

    out_dir = Path("results/sacred")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"sacred_{sha}.json"
    out_path.write_text(json.dumps(results, indent=2))
    print(f"\nSaved results to {out_path}")

    return results


if __name__ == "__main__":
    run_sacred_v4()
