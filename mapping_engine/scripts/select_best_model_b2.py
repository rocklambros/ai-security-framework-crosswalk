"""B2.10: Paired-bootstrap model selection across calibration variants.

Compares per-anchor LOO-masked scores produced by each model variant on
the 5 expanded non-frozen pairs and picks the best on aggregate NDCG@10
with 1000-resample paired bootstrap CI on the per-anchor delta.

Variants compared:
  - hand_tuned: PairMapper(use_learned_weights=False)
  - logistic: PairMapper(use_learned_weights=True), reading learned_weights.json
  - lightgbm, ordinal: NOT wired into PairMapper composite scoring; their
    feature-importance / coefficient artifacts are reported but they cannot
    produce per-anchor masked scores via the same pipeline. Skipped from
    the selection with an explicit note.

Output: updates ``data/processed/learned_weights_b2.json`` with a
``best_model`` field and ``model_comparison`` block.

Usage::

    python -m mapping_engine.scripts.select_best_model_b2
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from mapping_engine.calibration.metrics import bootstrap_metric_ci, ndcg_at_k
from mapping_engine.config import load_pair_config
from mapping_engine.engine.graph import load_graph
from mapping_engine.engine.mapper import PairMapper
from mapping_engine.scripts.learn_weights_b2 import (
    FROZEN_TEST_PAIRS,
    TIER_GRADE,
    _expanded_pair_configs,
)

REPO = Path(__file__).resolve().parents[2]


def _scores_for_variant(G, cfg, use_learned: bool) -> tuple[np.ndarray, np.ndarray]:
    mapper = PairMapper(G, cfg, use_learned_weights=use_learned, enable_reranker=None)
    result = mapper.run()
    av = result.anchor_validation
    records: dict[str, dict] = {}
    records.update(av.get("training_anchors", {}))
    records.update(av.get("holdout_anchors", {}))
    expected_lookup = {f"{p.source}__{p.target}": p.expected_tier for p in cfg.anchors.pairs}
    scores: list[float] = []
    grades: list[float] = []
    for key, rec in records.items():
        scores.append(float(rec.get("score", 0.0)))
        exp = expected_lookup.get(key, "None")
        grades.append(TIER_GRADE.get(exp, 0.0))
    return np.asarray(scores, dtype=float), np.asarray(grades, dtype=float)


def _per_pair_ndcg(pair_arrays: list[tuple[np.ndarray, np.ndarray]]) -> float:
    """Anchor-weighted aggregate NDCG@10 across pairs."""
    total = total_w = 0.0
    for grades, scores in pair_arrays:
        if len(grades) == 0:
            continue
        v = ndcg_at_k(grades, scores, k=10)
        total += v * len(grades)
        total_w += len(grades)
    return total / max(1.0, total_w)


def _paired_bootstrap_delta(
    grades: np.ndarray,
    scores_a: np.ndarray,
    scores_b: np.ndarray,
    n_resamples: int = 1000,
    rng_seed: int = 42,
) -> dict:
    rng = np.random.default_rng(rng_seed)
    n = len(grades)
    deltas = np.empty(n_resamples, dtype=float)
    for i in range(n_resamples):
        idx = rng.integers(0, n, size=n)
        deltas[i] = ndcg_at_k(grades[idx], scores_a[idx], k=10) - ndcg_at_k(
            grades[idx], scores_b[idx], k=10
        )
    return {
        "point": float(np.mean(deltas)),
        "lo": float(np.quantile(deltas, 0.025)),
        "hi": float(np.quantile(deltas, 0.975)),
        "ci_excludes_zero": bool(
            np.quantile(deltas, 0.025) > 0 or np.quantile(deltas, 0.975) < 0
        ),
    }


def main() -> None:
    G = load_graph(REPO / "data/processed/nodes.json", REPO / "data/processed/edges.json")
    names = _expanded_pair_configs()
    print(f"Comparing models over {len(names)} non-frozen pairs")

    hand_pairs: list[tuple[np.ndarray, np.ndarray]] = []
    log_pairs: list[tuple[np.ndarray, np.ndarray]] = []
    all_grades: list[float] = []
    all_hand: list[float] = []
    all_log: list[float] = []
    for name in names:
        cfg = load_pair_config(name + "__expanded", validate_anchors_in=G)
        s_h, g_h = _scores_for_variant(G, cfg, use_learned=False)
        s_l, g_l = _scores_for_variant(G, cfg, use_learned=True)
        # grades should be identical (anchor order is deterministic)
        hand_pairs.append((g_h, s_h))
        log_pairs.append((g_l, s_l))
        all_grades.extend(g_h.tolist())
        all_hand.extend(s_h.tolist())
        all_log.extend(s_l.tolist())

    g_arr = np.asarray(all_grades, dtype=float)
    h_arr = np.asarray(all_hand, dtype=float)
    l_arr = np.asarray(all_log, dtype=float)

    hand_ci = bootstrap_metric_ci(
        lambda gg, ss: ndcg_at_k(gg, ss, k=10), g_arr, h_arr, n_resamples=1000, rng=42
    )
    log_ci = bootstrap_metric_ci(
        lambda gg, ss: ndcg_at_k(gg, ss, k=10), g_arr, l_arr, n_resamples=1000, rng=42
    )
    delta_log_vs_hand = _paired_bootstrap_delta(g_arr, l_arr, h_arr)

    print(
        f"\nhand_tuned NDCG@10: {hand_ci['point']:.4f} [{hand_ci['lo']:.4f}, {hand_ci['hi']:.4f}]"
    )
    print(
        f"logistic   NDCG@10: {log_ci['point']:.4f} [{log_ci['lo']:.4f}, {log_ci['hi']:.4f}]"
    )
    print(
        f"Paired delta (logistic - hand_tuned): "
        f"{delta_log_vs_hand['point']:+.4f} "
        f"[{delta_log_vs_hand['lo']:+.4f}, {delta_log_vs_hand['hi']:+.4f}]  "
        f"CI excludes 0: {delta_log_vs_hand['ci_excludes_zero']}"
    )

    # Decision: only switch if logistic CI excludes 0 in the positive direction.
    if delta_log_vs_hand["ci_excludes_zero"] and delta_log_vs_hand["point"] > 0:
        best = "logistic"
    else:
        best = "hand_tuned"
    print(f"\nBest model (paired-CI gated): {best}")

    # Update learned_weights_b2.json with the model_comparison block + best.
    out_path = REPO / "data" / "processed" / "learned_weights_b2.json"
    cur = json.loads(out_path.read_text())
    cur["best_model"] = best
    cur["model_comparison"] = {
        "schema_version": "b2.10",
        "variants_compared": ["hand_tuned", "logistic"],
        "variants_skipped": ["lightgbm", "ordinal"],
        "skip_reason": (
            "lightgbm and ordinal models from learn_weights.py are not wired "
            "into PairMapper composite scoring; they would require a separate "
            "scoring shim. The current pipeline only supports hand-tuned and "
            "logistic via use_learned_weights. Documented as deferred."
        ),
        "hand_tuned_ndcg_at_10_ci": hand_ci,
        "logistic_ndcg_at_10_ci": log_ci,
        "paired_delta_logistic_minus_hand": delta_log_vs_hand,
        "decision": best,
        "decision_rule": (
            "Switch to alternative model only if its paired-bootstrap delta vs "
            "hand-tuned has CI excluding 0 in the positive direction."
        ),
    }
    out_path.write_text(json.dumps(cur, indent=2, default=str))
    print(f"Updated {out_path}")


if __name__ == "__main__":
    main()
