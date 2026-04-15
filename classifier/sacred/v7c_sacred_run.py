"""v7c Sacred Run: Human-calibrated LogReg on CE + GAT + baseline features.

Architecture:
  Stage 1 (already done): CE fine-tuned on expert data, GAT trained on graph
  Stage 2 (this script): LogReg trained on human_cal, evaluated on frozen test

Features:
  - CE logits (4 dims, from ce_features_v2.npz if available)
  - GAT pair features (35 dims: cosine, L2, dot, 32-dim abs diff)
  - BM25 + BGE cosine (2 dims, from baseline_features.parquet)
  - Bridge score (1 dim, computed from graph)

Trains on: human_cal_train (477 pairs with human labels)
Evaluates on: human_test_frozen (179 pairs)
"""
from __future__ import annotations

import json
import time
from collections import Counter
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    classification_report,
)
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import StandardScaler

from classifier.data.tier_mapper import map_expert_tier

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
GAT_PATH = Path("data/features/gat_embeddings.npz")
BASELINE_PATH = Path("data/features/baseline_features.parquet")
CE_FEATURES_PATH = Path("data/processed/ce_features_v2.npz")
CAL_PATH = Path("data/splits/human_cal.jsonl")
TEST_PATH = Path("data/splits/human_test_frozen.jsonl")
GRAPH_NODES = Path("data/processed/nodes.json")
GRAPH_EDGES = Path("data/processed/edges.json")
OUTPUT_DIR = Path("runs/v7c_sacred")

TIER_NAMES = ["unrelated", "partial", "related", "equivalent"]


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
def load_jsonl(path: Path) -> list[dict]:
    with open(path) as f:
        return [json.loads(line) for line in f]


def split_human_cal(
    cal_data: list[dict], train_ratio: float = 0.667, seed: int = 42
) -> tuple[list[dict], list[dict], np.ndarray, np.ndarray]:
    """Split human_cal into train/val matching the existing 477/239 split.

    Returns (cal_train, cal_val, train_indices, val_indices) where indices
    are positions in the original cal_data list (needed for CE feature slicing).
    """
    indices = np.arange(len(cal_data))
    labels = np.array([int(map_expert_tier(r["expert_tier"])) for r in cal_data])

    from sklearn.model_selection import StratifiedShuffleSplit
    sss = StratifiedShuffleSplit(n_splits=1, train_size=train_ratio, random_state=seed)
    train_idx, val_idx = next(sss.split(indices, labels))

    cal_train = [cal_data[i] for i in train_idx]
    cal_val = [cal_data[i] for i in val_idx]
    return cal_train, cal_val, train_idx, val_idx


# ---------------------------------------------------------------------------
# Feature computation
# ---------------------------------------------------------------------------
def compute_gat_features(pairs: list[dict], gat_path: Path) -> np.ndarray:
    """Compute GAT pair features: cosine, L2, dot, 32-dim abs diff = 35 features."""
    data = np.load(gat_path, allow_pickle=True)
    embeddings = data["embeddings"]
    node_ids = data["node_ids"].tolist()
    node_to_idx = {nid: i for i, nid in enumerate(node_ids)}
    emb_dim = embeddings.shape[1]

    n = len(pairs)
    cosine = np.zeros(n)
    l2 = np.zeros(n)
    dot = np.zeros(n)
    diffs = np.zeros((n, emb_dim))

    for i, r in enumerate(pairs):
        src = r["source_node_id"]
        tgt = r["target_node_id"]
        if src in node_to_idx and tgt in node_to_idx:
            emb_src = embeddings[node_to_idx[src]]
            emb_tgt = embeddings[node_to_idx[tgt]]
            norm_src = np.linalg.norm(emb_src)
            norm_tgt = np.linalg.norm(emb_tgt)
            if norm_src > 0 and norm_tgt > 0:
                cosine[i] = float(np.dot(emb_src, emb_tgt) / (norm_src * norm_tgt))
            l2[i] = np.linalg.norm(emb_src - emb_tgt)
            dot[i] = np.dot(emb_src, emb_tgt)
            diffs[i] = np.abs(emb_src - emb_tgt)

    features = np.column_stack([cosine, l2, dot, diffs])
    return features  # (n, 35)


def compute_baseline_features(pairs: list[dict]) -> np.ndarray:
    """Load BM25 + BGE cosine from pre-computed parquet."""
    import pandas as pd
    if not BASELINE_PATH.exists():
        print("  [WARN] baseline_features.parquet not found, using zeros")
        return np.zeros((len(pairs), 2))

    df = pd.read_parquet(BASELINE_PATH)
    pk_to_row = {r["pair_key"]: i for i, r in enumerate(df.to_dict("records"))}

    features = np.zeros((len(pairs), 2))
    for i, r in enumerate(pairs):
        pk = r.get("pair_key", "")
        if pk in pk_to_row:
            idx = pk_to_row[pk]
            features[i, 0] = df.iloc[idx]["score_bge_cosine"]
            features[i, 1] = df.iloc[idx]["score_bm25"]
    return features


def compute_bridge_features(pairs: list[dict]) -> np.ndarray:
    """Compute bridge scores from graph."""
    try:
        from mapping_engine.engine.graph import load_graph
        from mapping_engine.engine.bridge import graph_bridge_scores
    except ImportError:
        print("  [WARN] mapping_engine not available, using zeros for bridge")
        return np.zeros((len(pairs), 1))

    if not GRAPH_NODES.exists() or not GRAPH_EDGES.exists():
        print("  [WARN] Graph files not found, using zeros for bridge")
        return np.zeros((len(pairs), 1))

    G = load_graph(GRAPH_NODES, GRAPH_EDGES)

    scores = np.zeros(len(pairs))
    for i, r in enumerate(pairs):
        src = r["source_node_id"]
        tgt = r["target_node_id"]
        if src in G and tgt in G:
            s = graph_bridge_scores(G, [src], [tgt], {})
            scores[i] = float(s[0][0])
    return scores.reshape(-1, 1)


def _load_ce_data() -> tuple[dict, list[str], dict[str, tuple[int, int]]] | None:
    """Load CE features and compute split offsets. Cached."""
    if not CE_FEATURES_PATH.exists():
        return None

    ce_data = dict(np.load(str(CE_FEATURES_PATH)))
    models = [k.replace("_logits", "") for k in ce_data if k.endswith("_logits")]

    n_train = sum(1 for _ in open("data/splits/expert_train.jsonl"))
    n_val = sum(1 for _ in open("data/splits/expert_val.jsonl"))
    n_cal = sum(1 for _ in open("data/splits/human_cal.jsonl"))
    n_test = sum(1 for _ in open("data/splits/human_test_frozen.jsonl"))

    offsets = {
        "expert_train": (0, n_train),
        "expert_val": (n_train, n_train + n_val),
        "human_cal": (n_train + n_val, n_train + n_val + n_cal),
        "human_test": (n_train + n_val + n_cal, n_train + n_val + n_cal + n_test),
    }
    return ce_data, models, offsets


def load_ce_logits(
    split_name: str,
    indices: np.ndarray | None = None,
    n_pairs: int | None = None,
) -> np.ndarray | None:
    """Load CE logit probabilities for a split (or subset via indices).

    Args:
        split_name: One of 'expert_train', 'expert_val', 'human_cal', 'human_test'
        indices: If provided, select these indices within the split
        n_pairs: Expected number of pairs (for validation)

    Returns (n_pairs, 4) probability matrix or None.
    """
    result = _load_ce_data()
    if result is None:
        print(f"  [WARN] {CE_FEATURES_PATH} not found, skipping CE features")
        return None

    ce_data, models, offsets = result
    start, end = offsets[split_name]

    # Average logits across all available models
    logits = np.zeros((end - start, 4))
    for m in models:
        logits += ce_data[f"{m}_logits"][start:end]
    logits /= len(models)

    # Select subset if indices provided
    if indices is not None:
        logits = logits[indices]

    # Softmax
    exp_logits = np.exp(logits - logits.max(axis=1, keepdims=True))
    proba = exp_logits / exp_logits.sum(axis=1, keepdims=True)

    if n_pairs is not None:
        assert proba.shape[0] == n_pairs, f"CE shape mismatch: {proba.shape[0]} vs {n_pairs}"

    return proba


def build_features(
    pairs: list[dict],
    split_name: str,
    include_ce: bool = True,
    ce_indices: np.ndarray | None = None,
) -> tuple[np.ndarray, list[str]]:
    """Build the full feature matrix for a set of pairs."""
    feature_blocks = []
    feature_names = []

    # GAT features (35 dims)
    print("  [v7c] Computing GAT features...")
    gat_feats = compute_gat_features(pairs, GAT_PATH)
    feature_blocks.append(gat_feats)
    feature_names.extend(
        ["gat_cosine", "gat_l2", "gat_dot"]
        + [f"gat_diff_{d:02d}" for d in range(gat_feats.shape[1] - 3)]
    )

    # Baseline features (2 dims: BGE cosine, BM25)
    print("  [v7c] Loading baseline features...")
    base_feats = compute_baseline_features(pairs)
    feature_blocks.append(base_feats)
    feature_names.extend(["bge_cosine", "bm25"])

    # Bridge score (1 dim)
    print("  [v7c] Computing bridge scores...")
    bridge_feats = compute_bridge_features(pairs)
    feature_blocks.append(bridge_feats)
    feature_names.append("bridge")

    # CE logits/proba (4 dims per model)
    if include_ce:
        ce_proba = load_ce_logits(split_name, indices=ce_indices, n_pairs=len(pairs))
        if ce_proba is not None:
            feature_blocks.append(ce_proba)
            feature_names.extend([f"ce_prob_{i}" for i in range(ce_proba.shape[1])])

    X = np.hstack(feature_blocks)
    print(f"  [v7c] Feature matrix: {X.shape} ({len(feature_names)} features)")
    return X, feature_names


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------
def evaluate(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    proba: np.ndarray | None = None,
    label: str = "",
) -> dict:
    """Compute comprehensive metrics."""
    acc = float(accuracy_score(y_true, y_pred))
    macro_f1 = float(f1_score(y_true, y_pred, average="macro"))
    per_class_f1 = f1_score(y_true, y_pred, average=None, labels=[0, 1, 2, 3])

    # Binary: unrelated (0) vs any-related (1,2,3)
    y_bin_true = (y_true > 0).astype(int)
    y_bin_pred = (y_pred > 0).astype(int)
    binary_acc = float(accuracy_score(y_bin_true, y_bin_pred))
    binary_f1 = float(f1_score(y_bin_true, y_bin_pred, average="macro"))

    # Adjacent accuracy: off-by-one is correct
    adjacent = np.abs(y_true.astype(int) - y_pred.astype(int)) <= 1
    adj_acc = float(adjacent.mean())

    cm = confusion_matrix(y_true, y_pred, labels=[0, 1, 2, 3])

    result = {
        "label": label,
        "tier_accuracy": acc,
        "macro_f1": macro_f1,
        "binary_accuracy": binary_acc,
        "binary_f1": binary_f1,
        "adjacent_accuracy": adj_acc,
        "per_class_f1": {TIER_NAMES[i]: float(per_class_f1[i]) for i in range(4)},
        "confusion_matrix": {
            TIER_NAMES[i]: {TIER_NAMES[j]: int(cm[i, j]) for j in range(4)}
            for i in range(4)
        },
        "class_counts": {TIER_NAMES[i]: int((y_true == i).sum()) for i in range(4)},
    }
    return result


def conformal_predict(
    proba_cal: np.ndarray,
    y_cal: np.ndarray,
    proba_test: np.ndarray,
    alpha: float = 0.10,
) -> dict:
    """Marginal conformal prediction sets."""
    # Nonconformity scores on calibration set
    scores = 1.0 - proba_cal[np.arange(len(y_cal)), y_cal]
    q_hat = float(np.quantile(scores, (1 - alpha) * (1 + 1 / len(y_cal))))

    # Prediction sets on test
    pred_sets = proba_test >= (1.0 - q_hat)
    set_sizes = pred_sets.sum(axis=1)

    return {
        "alpha": alpha,
        "q_hat": q_hat,
        "n_cal": len(y_cal),
        "avg_set_size": float(set_sizes.mean()),
        "median_set_size": float(np.median(set_sizes)),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    t0 = time.time()
    print("=" * 60)
    print("v7c SACRED RUN: Human-Calibrated LogReg")
    print("=" * 60)

    # Load data
    cal_data = load_jsonl(CAL_PATH)
    test_data = load_jsonl(TEST_PATH)
    print(f"  human_cal: {len(cal_data)} pairs")
    print(f"  human_test_frozen: {len(test_data)} pairs")

    # Labels
    y_cal_all = np.array([int(map_expert_tier(r["expert_tier"])) for r in cal_data])
    y_test = np.array([int(map_expert_tier(r["expert_tier"])) for r in test_data])
    print(f"  cal distribution: {dict(Counter(y_cal_all))}")
    print(f"  test distribution: {dict(Counter(y_test))}")

    # Split cal into train/val
    cal_train, cal_val, cal_train_idx, cal_val_idx = split_human_cal(cal_data)
    y_cal_train = np.array([int(map_expert_tier(r["expert_tier"])) for r in cal_train])
    y_cal_val = np.array([int(map_expert_tier(r["expert_tier"])) for r in cal_val])
    print(f"  cal_train: {len(cal_train)}, cal_val: {len(cal_val)}")
    print(f"  cal_train dist: {dict(Counter(y_cal_train))}")
    print(f"  cal_val dist: {dict(Counter(y_cal_val))}")

    # Check CE features availability
    has_ce = CE_FEATURES_PATH.exists()
    print(f"\n  CE features available: {has_ce}")

    # -----------------------------------------------------------------------
    # Build features
    # -----------------------------------------------------------------------
    print("\n--- Building features ---")
    X_cal_train, feat_names = build_features(
        cal_train, "human_cal", include_ce=has_ce, ce_indices=cal_train_idx
    )
    X_cal_val, _ = build_features(
        cal_val, "human_cal", include_ce=has_ce, ce_indices=cal_val_idx
    )
    X_test, _ = build_features(test_data, "human_test", include_ce=has_ce)

    # -----------------------------------------------------------------------
    # Tune C with 5-fold CV on cal_train
    # -----------------------------------------------------------------------
    print("\n--- Tuning LogReg C parameter ---")
    scaler = StandardScaler()
    X_cal_train_scaled = scaler.fit_transform(X_cal_train)
    X_cal_val_scaled = scaler.transform(X_cal_val)
    X_test_scaled = scaler.transform(X_test)

    C_values = [0.001, 0.01, 0.1, 1.0, 10.0]
    best_c = 1.0
    best_f1 = -1.0

    for c in C_values:
        skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        fold_f1s = []
        for train_idx, val_idx in skf.split(X_cal_train_scaled, y_cal_train):
            lr = LogisticRegression(
                C=c, max_iter=2000, class_weight="balanced",
                solver="lbfgs", random_state=42,
            )
            lr.fit(X_cal_train_scaled[train_idx], y_cal_train[train_idx])
            preds = lr.predict(X_cal_train_scaled[val_idx])
            fold_f1s.append(f1_score(y_cal_train[val_idx], preds, average="macro"))
        mean_f1 = np.mean(fold_f1s)
        print(f"  C={c:8.4f}: 5-fold macro_f1 = {mean_f1:.4f} (+/- {np.std(fold_f1s):.4f})")
        if mean_f1 > best_f1:
            best_f1 = mean_f1
            best_c = c

    print(f"  Best C: {best_c}, CV macro_f1: {best_f1:.4f}")

    # -----------------------------------------------------------------------
    # Train final model on full cal_train
    # -----------------------------------------------------------------------
    print("\n--- Training final LogReg ---")
    lr_final = LogisticRegression(
        C=best_c, max_iter=2000, class_weight="balanced",
        solver="lbfgs", random_state=42,
    )
    lr_final.fit(X_cal_train_scaled, y_cal_train)

    # Validate on cal_val
    y_pred_val = lr_final.predict(X_cal_val_scaled)
    proba_val = lr_final.predict_proba(X_cal_val_scaled)
    val_metrics = evaluate(y_cal_val, y_pred_val, proba_val, label="cal_val")
    print(f"  cal_val: acc={val_metrics['tier_accuracy']:.4f}, "
          f"macro_f1={val_metrics['macro_f1']:.4f}, "
          f"binary_acc={val_metrics['binary_accuracy']:.4f}, "
          f"adj_acc={val_metrics['adjacent_accuracy']:.4f}")

    # -----------------------------------------------------------------------
    # Sacred evaluation on frozen test
    # -----------------------------------------------------------------------
    print("\n--- SACRED RUN: Frozen test evaluation ---")
    results = {"methods": {}, "features": feat_names, "n_features": len(feat_names)}

    # Method A: Raw GAT-only argmax baseline (no CE, no calibration)
    X_test_gat_only = X_test_scaled[:, :35]  # First 35 = GAT features
    lr_gat = LogisticRegression(
        C=best_c, max_iter=2000, class_weight="balanced",
        solver="lbfgs", random_state=42,
    )
    X_train_gat_only = X_cal_train_scaled[:, :35]
    lr_gat.fit(X_train_gat_only, y_cal_train)
    y_pred_a = lr_gat.predict(X_test_gat_only)
    proba_a = lr_gat.predict_proba(X_test_gat_only)
    results["methods"]["A_gat_only"] = evaluate(y_test, y_pred_a, proba_a, "GAT-only LogReg")
    print(f"  Method A (GAT-only):    acc={results['methods']['A_gat_only']['tier_accuracy']:.4f}, "
          f"macro_f1={results['methods']['A_gat_only']['macro_f1']:.4f}, "
          f"binary_acc={results['methods']['A_gat_only']['binary_accuracy']:.4f}")

    # Method B: Full features (GAT + baseline + CE if available)
    y_pred_b = lr_final.predict(X_test_scaled)
    proba_b = lr_final.predict_proba(X_test_scaled)
    results["methods"]["B_full_pipeline"] = evaluate(y_test, y_pred_b, proba_b, "Full pipeline")
    print(f"  Method B (full):        acc={results['methods']['B_full_pipeline']['tier_accuracy']:.4f}, "
          f"macro_f1={results['methods']['B_full_pipeline']['macro_f1']:.4f}, "
          f"binary_acc={results['methods']['B_full_pipeline']['binary_accuracy']:.4f}")

    # Method C: CE-only (if available)
    if has_ce:
        ce_start = len(feat_names) - 4  # Last 4 features are CE probs
        X_test_ce_only = X_test_scaled[:, ce_start:]
        lr_ce = LogisticRegression(
            C=best_c, max_iter=2000, class_weight="balanced",
            solver="lbfgs", random_state=42,
        )
        X_train_ce_only = X_cal_train_scaled[:, ce_start:]
        lr_ce.fit(X_train_ce_only, y_cal_train)
        y_pred_c = lr_ce.predict(X_test_ce_only)
        proba_c = lr_ce.predict_proba(X_test_ce_only)
        results["methods"]["C_ce_only"] = evaluate(y_test, y_pred_c, proba_c, "CE-only LogReg")
        print(f"  Method C (CE-only):     acc={results['methods']['C_ce_only']['tier_accuracy']:.4f}, "
              f"macro_f1={results['methods']['C_ce_only']['macro_f1']:.4f}, "
              f"binary_acc={results['methods']['C_ce_only']['binary_accuracy']:.4f}")

    # Method D (comparison): v7b raw CE logits (no LogReg, no GAT)
    if has_ce:
        ce_proba_test = load_ce_logits("human_test", n_pairs=len(test_data))
        if ce_proba_test is not None:
            y_pred_d = ce_proba_test.argmax(axis=1)
            results["methods"]["D_v7b_raw_ce"] = evaluate(y_test, y_pred_d, ce_proba_test, "v7b raw CE")
            print(f"  Method D (v7b raw CE):  acc={results['methods']['D_v7b_raw_ce']['tier_accuracy']:.4f}, "
                  f"macro_f1={results['methods']['D_v7b_raw_ce']['macro_f1']:.4f}, "
                  f"binary_acc={results['methods']['D_v7b_raw_ce']['binary_accuracy']:.4f}")

    # -----------------------------------------------------------------------
    # Conformal prediction (Method B)
    # -----------------------------------------------------------------------
    print("\n--- Conformal calibration (Method B) ---")
    conformal = conformal_predict(proba_val, y_cal_val, proba_b, alpha=0.10)
    results["conformal"] = conformal

    # Compute test coverage
    pred_sets = proba_b >= (1.0 - conformal["q_hat"])
    coverage = float(pred_sets[np.arange(len(y_test)), y_test].mean())
    conformal["test_coverage"] = coverage
    print(f"  q_hat={conformal['q_hat']:.4f}, "
          f"coverage={coverage:.4f}, "
          f"avg_set_size={conformal['avg_set_size']:.2f}")

    # -----------------------------------------------------------------------
    # Bootstrap CI for primary metric (Method B)
    # -----------------------------------------------------------------------
    print("\n--- Bootstrap 95% CI ---")
    rng = np.random.RandomState(42)
    boot_accs = []
    boot_f1s = []
    for _ in range(2000):
        idx = rng.choice(len(y_test), len(y_test), replace=True)
        boot_accs.append(accuracy_score(y_test[idx], y_pred_b[idx]))
        boot_f1s.append(f1_score(y_test[idx], y_pred_b[idx], average="macro"))
    results["bootstrap_ci_95"] = {
        "accuracy": {
            "lower": float(np.percentile(boot_accs, 2.5)),
            "point": float(np.mean(boot_accs)),
            "upper": float(np.percentile(boot_accs, 97.5)),
        },
        "macro_f1": {
            "lower": float(np.percentile(boot_f1s, 2.5)),
            "point": float(np.mean(boot_f1s)),
            "upper": float(np.percentile(boot_f1s, 97.5)),
        },
    }
    ci = results["bootstrap_ci_95"]
    print(f"  accuracy: {ci['accuracy']['lower']:.4f} - {ci['accuracy']['point']:.4f} - {ci['accuracy']['upper']:.4f}")
    print(f"  macro_f1: {ci['macro_f1']['lower']:.4f} - {ci['macro_f1']['point']:.4f} - {ci['macro_f1']['upper']:.4f}")

    # -----------------------------------------------------------------------
    # Feature importance
    # -----------------------------------------------------------------------
    print("\n--- Feature importance (LogReg coefficients) ---")
    coefs = np.abs(lr_final.coef_).mean(axis=0)  # Average across classes
    importance = sorted(zip(feat_names, coefs), key=lambda x: -x[1])
    results["feature_importance"] = {name: float(coef) for name, coef in importance}
    for name, coef in importance[:10]:
        print(f"  {name:20s}: {coef:.4f}")

    # -----------------------------------------------------------------------
    # Save results
    # -----------------------------------------------------------------------
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    results["elapsed_seconds"] = time.time() - t0
    results["best_C"] = best_c
    results["cv_macro_f1"] = best_f1
    results["cal_val_metrics"] = val_metrics
    results["sacred_run"] = True
    results["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    results["has_ce_features"] = has_ce

    out_path = OUTPUT_DIR / "results.json"
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"\n  Results saved to {out_path}")

    # Save model
    import pickle
    with open(OUTPUT_DIR / "logreg_model.pkl", "wb") as f:
        pickle.dump({"model": lr_final, "scaler": scaler, "features": feat_names, "best_c": best_c}, f)
    print(f"  Model saved to {OUTPUT_DIR / 'logreg_model.pkl'}")

    elapsed = time.time() - t0
    print(f"\n  Total time: {elapsed:.1f}s")
    print("=" * 60)

    return results


if __name__ == "__main__":
    main()
