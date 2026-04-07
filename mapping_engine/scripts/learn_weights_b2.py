"""B-2 multi-pair anchor calibration with per-anchor LOO masking.

For each expanded pair config (excluding frozen test pairs), runs PairMapper
to collect leave-one-out masked composite scores per anchor, then computes
per-pair and aggregate metrics (tier_accuracy, NDCG@10, Spearman) with
5-fold CV + 1000-resample bootstrap 95% CI.

Output: ``data/processed/learned_weights_b2.json`` (B2.8 consumes this).

Usage::

    python -m mapping_engine.scripts.learn_weights_b2
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from mapping_engine.calibration.metrics import (
    bootstrap_metric_ci,
    ndcg_at_k,
    spearman,
    tier_accuracy,
)
from mapping_engine.config import load_pair_config
from mapping_engine.engine.graph import load_graph
from mapping_engine.engine.mapper import PairMapper

REPO = Path(__file__).resolve().parents[2]
PAIRS_DIR = REPO / "mapping_engine" / "config" / "pairs"

# Frozen test pairs — never touched during B-2 calibration.
FROZEN_TEST_PAIRS = {
    "aiuc_1__csa_aicm",        # B-2 frozen
    "aiuc_1__mitre_atlas",     # B-1 frozen
    "cosai_rm__owasp_llm",     # A frozen (reassigned in B2.5)
}

# Tier -> graded relevance for ranking metrics.
TIER_GRADE = {"Direct": 2.0, "Related": 1.0, "None": 0.0}


def _expanded_pair_configs() -> list[str]:
    out = []
    for p in sorted(PAIRS_DIR.glob("*__expanded.yaml")):
        name = p.stem.removesuffix("__expanded")
        if name in FROZEN_TEST_PAIRS:
            continue
        out.append(name)
    return out


def _collect_masked_anchor_data(G, cfg) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Run PairMapper and return (scores, true_grades, pred_tiers) per anchor.

    PairMapper already performs leave-one-out anchor masking when computing
    bridge features for anchor rows, so the composite scores returned here
    are leak-free.
    """
    mapper = PairMapper(G, cfg, use_learned_weights=False, enable_reranker=None)
    result = mapper.run()
    av = result.anchor_validation
    records: dict[str, dict] = {}
    records.update(av.get("training_anchors", {}))
    records.update(av.get("holdout_anchors", {}))

    scores: list[float] = []
    grades: list[float] = []
    tiers: list[str] = []
    expected: list[str] = []
    expected_lookup = {f"{p.source}__{p.target}": p.expected_tier for p in cfg.anchors.pairs}
    for key, rec in records.items():
        scores.append(float(rec.get("score", 0.0)))
        exp = expected_lookup.get(key, "None")
        expected.append(exp)
        grades.append(TIER_GRADE.get(exp, 0.0))
        tiers.append(rec.get("predicted_tier") or rec.get("assigned_tier") or "None")
    return (
        np.asarray(scores, dtype=float),
        np.asarray(grades, dtype=float),
        np.asarray(tiers, dtype=object),
        np.asarray(expected, dtype=object),
    )


def _per_pair_metrics(
    scores: np.ndarray,
    grades: np.ndarray,
    pred_tiers: np.ndarray,
    expected: np.ndarray,
    n_splits: int = 5,
) -> dict:
    """Per-pair metrics with bootstrap CI + 5-fold CV mean/std."""
    n = len(scores)
    out: dict = {"n_anchors": n}
    if n == 0:
        return out

    # Point + bootstrap CI on the full pair.
    out["tier_accuracy"] = bootstrap_metric_ci(
        tier_accuracy, expected, pred_tiers, n_resamples=1000, rng=42
    )
    out["spearman"] = bootstrap_metric_ci(
        spearman, grades, scores, n_resamples=1000, rng=42
    )
    out["ndcg_at_10"] = bootstrap_metric_ci(
        lambda g, s: ndcg_at_k(g, s, k=10),
        grades,
        scores,
        n_resamples=1000,
        rng=42,
    )

    # 5-fold CV: shuffled split, compute each metric per fold.
    rng = np.random.default_rng(42)
    order = np.arange(n)
    rng.shuffle(order)
    folds = np.array_split(order, min(n_splits, n))
    fold_acc, fold_ndcg, fold_sp = [], [], []
    for fold in folds:
        if len(fold) == 0:
            continue
        fold_acc.append(tier_accuracy(expected[fold], pred_tiers[fold]))
        fold_ndcg.append(ndcg_at_k(grades[fold], scores[fold], k=10))
        fold_sp.append(spearman(grades[fold], scores[fold]))
    out["cv_5fold"] = {
        "tier_accuracy_mean": float(np.mean(fold_acc)) if fold_acc else 0.0,
        "tier_accuracy_std": float(np.std(fold_acc, ddof=1)) if len(fold_acc) > 1 else 0.0,
        "ndcg_at_10_mean": float(np.mean(fold_ndcg)) if fold_ndcg else 0.0,
        "ndcg_at_10_std": float(np.std(fold_ndcg, ddof=1)) if len(fold_ndcg) > 1 else 0.0,
        "spearman_mean": float(np.mean(fold_sp)) if fold_sp else 0.0,
        "spearman_std": float(np.std(fold_sp, ddof=1)) if len(fold_sp) > 1 else 0.0,
        "n_folds": len(folds),
    }
    return out


def _aggregate(per_pair: dict[str, dict]) -> dict:
    """Anchor-weighted aggregate across pairs (concatenate-then-resample)."""
    all_scores: list[float] = []
    all_grades: list[float] = []
    all_pred: list[str] = []
    all_exp: list[str] = []
    for name, pair_data in per_pair.items():
        all_scores.extend(pair_data["_arrays"]["scores"])
        all_grades.extend(pair_data["_arrays"]["grades"])
        all_pred.extend(pair_data["_arrays"]["pred"])
        all_exp.extend(pair_data["_arrays"]["expected"])
    if not all_scores:
        return {}
    s = np.asarray(all_scores, dtype=float)
    g = np.asarray(all_grades, dtype=float)
    p = np.asarray(all_pred, dtype=object)
    e = np.asarray(all_exp, dtype=object)
    return {
        "n_anchors_total": len(s),
        "tier_accuracy": bootstrap_metric_ci(tier_accuracy, e, p, n_resamples=1000, rng=42),
        "ndcg_at_10": bootstrap_metric_ci(
            lambda gg, ss: ndcg_at_k(gg, ss, k=10), g, s, n_resamples=1000, rng=42
        ),
        "spearman": bootstrap_metric_ci(spearman, g, s, n_resamples=1000, rng=42),
    }


def main() -> None:
    G = load_graph(REPO / "data/processed/nodes.json", REPO / "data/processed/edges.json")
    pair_names = _expanded_pair_configs()
    print(f"Loading {len(pair_names)} expanded pairs (frozen excluded): {pair_names}")

    per_pair: dict[str, dict] = {}
    for name in pair_names:
        try:
            cfg = load_pair_config(name + "__expanded", validate_anchors_in=G)
        except Exception as exc:
            print(f"  [skip] {name}: {exc}")
            continue
        scores, grades, pred_tiers, expected = _collect_masked_anchor_data(G, cfg)
        metrics = _per_pair_metrics(scores, grades, pred_tiers, expected)
        metrics["_arrays"] = {
            "scores": scores.tolist(),
            "grades": grades.tolist(),
            "pred": pred_tiers.tolist(),
            "expected": expected.tolist(),
        }
        per_pair[name] = metrics
        if metrics.get("n_anchors", 0):
            ndcg = metrics["ndcg_at_10"]
            print(
                f"  {name:<32} n={metrics['n_anchors']:>3}  "
                f"NDCG@10={ndcg['point']:.3f} [{ndcg['lo']:.3f},{ndcg['hi']:.3f}]"
            )

    aggregate = _aggregate(per_pair)

    # Strip the heavy _arrays before persisting.
    persisted_pairs = {
        name: {k: v for k, v in m.items() if k != "_arrays"}
        for name, m in per_pair.items()
    }

    out = {
        "schema_version": "b2.7",
        "frozen_test_pairs_excluded": sorted(FROZEN_TEST_PAIRS),
        "per_pair": persisted_pairs,
        "aggregate": aggregate,
    }
    out_path = REPO / "data" / "processed" / "learned_weights_b2.json"
    out_path.write_text(json.dumps(out, indent=2, default=str))
    print(f"\nWrote {out_path}")
    if aggregate:
        agg = aggregate["ndcg_at_10"]
        print(
            f"Aggregate NDCG@10: {agg['point']:.3f} "
            f"[{agg['lo']:.3f}, {agg['hi']:.3f}] over {aggregate['n_anchors_total']} anchors"
        )


if __name__ == "__main__":
    main()
