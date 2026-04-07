"""B2.9: NDCG@10-objective threshold sweep over multi-pair masked anchor data.

Loads the per-pair LOO-masked composite scores produced by learn_weights_b2.py
(via re-running PairMapper), sweeps (direct, related_primary) thresholds,
converts each anchor's score into a graded prediction (Direct=2 / Related=1
/ None=0), and selects the threshold pair that maximizes aggregate NDCG@10
across pairs. Compares against the Youden's-J optimum from the same grid.

Output: ``data/processed/calibrated_thresholds_b2.json``.

Usage::

    python -m mapping_engine.scripts.threshold_sweep_b2
"""

from __future__ import annotations

import itertools
import json
from pathlib import Path

import numpy as np

from mapping_engine.calibration.metrics import bootstrap_metric_ci, ndcg_at_k
from mapping_engine.config import load_pair_config
from mapping_engine.engine.graph import load_graph
from mapping_engine.scripts.learn_weights_b2 import (
    FROZEN_TEST_PAIRS,
    TIER_GRADE,
    _collect_masked_anchor_data,
    _expanded_pair_configs,
)

REPO = Path(__file__).resolve().parents[2]

DIRECT_GRID = [0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70]
RELATED_GRID = [0.20, 0.25, 0.30, 0.35, 0.40, 0.45]


def _grade_from_score(score: float, t_dir: float, t_rel: float) -> float:
    if score >= t_dir:
        return TIER_GRADE["Direct"]
    if score >= t_rel:
        return TIER_GRADE["Related"]
    return TIER_GRADE["None"]


def _aggregate_ndcg(
    pairs: list[tuple[np.ndarray, np.ndarray]], t_dir: float, t_rel: float
) -> float:
    """Per-pair NDCG@10 averaged across pairs (anchor-weighted)."""
    total_w, total = 0.0, 0.0
    for grades, scores in pairs:
        if len(grades) == 0:
            continue
        pred_grades = np.array([_grade_from_score(s, t_dir, t_rel) for s in scores])
        # NDCG@10 with predicted grades as scores; ideal still defined by true grades.
        n = len(grades)
        v = ndcg_at_k(grades, pred_grades, k=10)
        total += v * n
        total_w += n
    return total / max(1.0, total_w)


def _aggregate_youden(
    pairs: list[tuple[np.ndarray, np.ndarray]], t_dir: float, t_rel: float
) -> float:
    tp = fp = tn = fn = 0
    for grades, scores in pairs:
        for g, s in zip(grades, scores):
            exp_pos = g > 0
            pred_pos = s >= t_rel  # mapped if at least Related
            if exp_pos and pred_pos:
                tp += 1
            elif exp_pos and not pred_pos:
                fn += 1
            elif not exp_pos and pred_pos:
                fp += 1
            else:
                tn += 1
    sens = tp / max(1, tp + fn)
    spec = tn / max(1, tn + fp)
    return sens + spec - 1


def main() -> None:
    G = load_graph(REPO / "data/processed/nodes.json", REPO / "data/processed/edges.json")
    names = _expanded_pair_configs()
    print(f"Sweeping thresholds over {len(names)} non-frozen pairs")

    pair_arrays: list[tuple[np.ndarray, np.ndarray]] = []
    all_grades: list[float] = []
    all_scores: list[float] = []
    for name in names:
        cfg = load_pair_config(name + "__expanded", validate_anchors_in=G)
        scores, grades, _pred, _exp = _collect_masked_anchor_data(G, cfg)
        pair_arrays.append((grades, scores))
        all_grades.extend(grades.tolist())
        all_scores.extend(scores.tolist())
    all_g = np.asarray(all_grades, dtype=float)
    all_s = np.asarray(all_scores, dtype=float)

    rows = []
    for t_dir, t_rel in itertools.product(DIRECT_GRID, RELATED_GRID):
        if t_rel >= t_dir:
            continue
        ndcg = _aggregate_ndcg(pair_arrays, t_dir, t_rel)
        youden = _aggregate_youden(pair_arrays, t_dir, t_rel)
        rows.append(
            {"direct": t_dir, "related_primary": t_rel, "ndcg_at_10": ndcg, "youden_j": youden}
        )

    rows.sort(key=lambda r: (-r["ndcg_at_10"], -r["youden_j"]))
    best_ndcg = rows[0]
    rows_by_y = sorted(rows, key=lambda r: (-r["youden_j"], -r["ndcg_at_10"]))
    best_youden = rows_by_y[0]

    # Bootstrap CI on the chosen NDCG@10 (aggregate over all anchors using
    # per-anchor predicted grades from the chosen thresholds).
    pred_grades_best = np.array(
        [_grade_from_score(s, best_ndcg["direct"], best_ndcg["related_primary"]) for s in all_s]
    )
    pred_grades_y = np.array(
        [_grade_from_score(s, best_youden["direct"], best_youden["related_primary"]) for s in all_s]
    )
    ci_best = bootstrap_metric_ci(
        lambda g, p: ndcg_at_k(g, p, k=10),
        all_g,
        pred_grades_best,
        n_resamples=1000,
        rng=42,
    )
    ci_y = bootstrap_metric_ci(
        lambda g, p: ndcg_at_k(g, p, k=10),
        all_g,
        pred_grades_y,
        n_resamples=1000,
        rng=42,
    )

    # Paired bootstrap on the delta (NDCG-optimized minus Youden-optimized).
    rng = np.random.default_rng(42)
    n = len(all_g)
    deltas = np.empty(1000, dtype=float)
    for i in range(1000):
        idx = rng.integers(0, n, size=n)
        d = ndcg_at_k(all_g[idx], pred_grades_best[idx], k=10) - ndcg_at_k(
            all_g[idx], pred_grades_y[idx], k=10
        )
        deltas[i] = d
    delta_lo, delta_hi = float(np.quantile(deltas, 0.025)), float(np.quantile(deltas, 0.975))
    delta_point = float(np.mean(deltas))

    print("\nTop 5 NDCG-optimal threshold pairs:")
    for r in rows[:5]:
        print(
            f"  direct={r['direct']:.2f} related={r['related_primary']:.2f}  "
            f"NDCG@10={r['ndcg_at_10']:.4f}  Youden={r['youden_j']:.4f}"
        )
    print(
        f"\nNDCG-optimal: direct={best_ndcg['direct']} related={best_ndcg['related_primary']}  "
        f"NDCG@10={ci_best['point']:.4f} [{ci_best['lo']:.4f}, {ci_best['hi']:.4f}]"
    )
    print(
        f"Youden-optimal: direct={best_youden['direct']} related={best_youden['related_primary']}  "
        f"NDCG@10={ci_y['point']:.4f} [{ci_y['lo']:.4f}, {ci_y['hi']:.4f}]"
    )
    print(
        f"Delta NDCG@10 (paired bootstrap): {delta_point:+.4f} "
        f"[{delta_lo:+.4f}, {delta_hi:+.4f}]  "
        f"CI excludes 0: {bool(delta_lo > 0 or delta_hi < 0)}"
    )

    out = {
        "schema_version": "b2.9",
        "frozen_test_pairs_excluded": sorted(FROZEN_TEST_PAIRS),
        "grids": {"direct": DIRECT_GRID, "related_primary": RELATED_GRID},
        "sweep": rows,
        "ndcg_optimal": {
            "direct": best_ndcg["direct"],
            "related_primary": best_ndcg["related_primary"],
            "ndcg_at_10_ci": ci_best,
        },
        "youden_optimal": {
            "direct": best_youden["direct"],
            "related_primary": best_youden["related_primary"],
            "ndcg_at_10_ci": ci_y,
        },
        "paired_delta_ndcg": {
            "point": delta_point,
            "lo": delta_lo,
            "hi": delta_hi,
            "ci_excludes_zero": bool(delta_lo > 0 or delta_hi < 0),
        },
        "n_anchors": int(n),
    }
    out_path = REPO / "data" / "processed" / "calibrated_thresholds_b2.json"
    out_path.write_text(json.dumps(out, indent=2, default=str))
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
