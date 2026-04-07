"""S4: Re-sweep (direct, related_primary) thresholds against the
anchors-vs-distractors discriminative metric.

The MRR / Recall@5 / ROC-AUC family is threshold-independent, so we
gate the sweep on Youden's J (TPR − FPR) computed over the same anchor
pool. A positive is a "true positive" if its tier_pred is Direct or
Related; a distractor is a "false positive" if it is assigned Direct or
Related. Balanced accuracy and per-tier counts are reported alongside.

Decision rule: adopt the new (direct, related_primary) thresholds only
if the 1000-resample paired-bootstrap 95 % CI on the per-anchor Youden
delta vs the current B-2 thresholds (0.45, 0.20) excludes zero AND the
direction is positive. The largest non-frozen pair is held out as inner
validation; the sweep is performed on the other 4 pairs and the held-out
pair only contributes to the gating CI.

Reads: data/processed/discriminative_baseline.json
Writes: data/processed/threshold_sweep_discriminative.json
Possibly writes: data/processed/calibrated_thresholds_b2.json
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
BASELINE_PATH = REPO / "data/processed/discriminative_baseline.json"
SWEEP_PATH = REPO / "data/processed/threshold_sweep_discriminative.json"
CAL_PATH = REPO / "data/processed/calibrated_thresholds_b2.json"

DIRECT_GRID = [round(x, 2) for x in np.arange(0.30, 0.66, 0.05)]
RELATED_GRID = [round(x, 2) for x in np.arange(0.10, 0.41, 0.05)]
B2_DIRECT = 0.45
B2_RELATED = 0.20
RNG_SEED = 20260407


def _per_anchor_youden(
    pos_scores: np.ndarray,
    dist_scores_flat: np.ndarray,
    dist_lengths: np.ndarray,
    direct: float,
    related: float,
) -> np.ndarray:
    """Per-anchor Youden contribution = TP_i − mean_FP_i.

    For anchor i, TP_i = 1 if positive >= related else 0.
    Mean_FP_i = fraction of anchor i's distractors with score >= related.
    Returning per-anchor values lets us run a paired bootstrap on the
    delta vs baseline thresholds.
    """
    tp = (pos_scores >= related).astype(float)
    fp_per_anchor = np.zeros(len(pos_scores))
    offset = 0
    for i, k in enumerate(dist_lengths):
        chunk = dist_scores_flat[offset : offset + k]
        if k > 0:
            fp_per_anchor[i] = float((chunk >= related).mean())
        offset += k
    return tp - fp_per_anchor


def _balanced_accuracy(
    pos_scores: np.ndarray,
    dist_scores_flat: np.ndarray,
    direct: float,
    related: float,
) -> dict:
    pos_direct = int((pos_scores >= direct).sum())
    pos_related = int(((pos_scores >= related) & (pos_scores < direct)).sum())
    pos_none = int((pos_scores < related).sum())
    dist_direct = int((dist_scores_flat >= direct).sum())
    dist_related = int(
        ((dist_scores_flat >= related) & (dist_scores_flat < direct)).sum()
    )
    dist_none = int((dist_scores_flat < related).sum())
    n_pos = len(pos_scores)
    n_dist = len(dist_scores_flat)
    tpr = (pos_direct + pos_related) / max(1, n_pos)
    fpr = (dist_direct + dist_related) / max(1, n_dist)
    return {
        "tpr": tpr,
        "fpr": fpr,
        "youden": tpr - fpr,
        "balanced_accuracy": 0.5 * (tpr + (1 - fpr)),
        "pos_direct": pos_direct,
        "pos_related": pos_related,
        "pos_none": pos_none,
        "dist_direct": dist_direct,
        "dist_related": dist_related,
        "dist_none": dist_none,
    }


def _flatten(per_pair_pos: list[list[float]], per_pair_dist: list[list[list[float]]]):
    pos = np.concatenate([np.asarray(p, dtype=float) for p in per_pair_pos])
    dist_lengths = np.array(
        [len(d) for pair_dists in per_pair_dist for d in pair_dists],
        dtype=int,
    )
    flat = np.concatenate(
        [np.asarray(d, dtype=float) for pair_dists in per_pair_dist for d in pair_dists]
    )
    return pos, flat, dist_lengths


def main() -> None:
    data = json.loads(BASELINE_PATH.read_text())
    per_pair = data["per_pair"]
    # Reconstruct per-pair score arrays from the flat baseline file. We
    # stored aggregated scores; rebuild per-pair from per_pair n_anchors.
    flat_pos = data["scores"]["positive"]
    flat_dist = data["scores"]["distractors"]
    cursor = 0
    per_pair_pos: list[list[float]] = []
    per_pair_dist: list[list[list[float]]] = []
    for p in per_pair:
        n = p["n_anchors_scored"]
        per_pair_pos.append(flat_pos[cursor : cursor + n])
        per_pair_dist.append(flat_dist[cursor : cursor + n])
        cursor += n
    pair_names = [p["pair"] for p in per_pair]

    # Hold out the largest non-frozen pair as inner validation.
    sizes = [len(p) for p in per_pair_pos]
    holdout_idx = int(np.argmax(sizes))
    holdout_name = pair_names[holdout_idx]
    train_pos = [p for i, p in enumerate(per_pair_pos) if i != holdout_idx]
    train_dist = [p for i, p in enumerate(per_pair_dist) if i != holdout_idx]
    holdout_pos = [per_pair_pos[holdout_idx]]
    holdout_dist = [per_pair_dist[holdout_idx]]

    train_pos_flat, train_dist_flat, train_lens = _flatten(train_pos, train_dist)
    hold_pos_flat, hold_dist_flat, hold_lens = _flatten(holdout_pos, holdout_dist)
    all_pos_flat, all_dist_flat, all_lens = _flatten(per_pair_pos, per_pair_dist)

    # Sweep on the training (4 non-holdout) pairs only.
    sweep_results = []
    best = None
    for d in DIRECT_GRID:
        for r in RELATED_GRID:
            if r >= d:
                continue
            ba = _balanced_accuracy(train_pos_flat, train_dist_flat, d, r)
            sweep_results.append({"direct": d, "related_primary": r, **ba})
            if best is None or ba["youden"] > best["youden"] or (
                ba["youden"] == best["youden"]
                and ba["balanced_accuracy"] > best["balanced_accuracy"]
            ):
                best = {"direct": d, "related_primary": r, **ba}

    # Honest test on the held-out pair using the sweep-best thresholds.
    holdout_metrics = _balanced_accuracy(
        hold_pos_flat, hold_dist_flat, best["direct"], best["related_primary"]
    )
    baseline_holdout = _balanced_accuracy(
        hold_pos_flat, hold_dist_flat, B2_DIRECT, B2_RELATED
    )

    # Aggregate (all pairs) for both threshold pairs — this is the
    # number we report next to the B-2 baseline.
    agg_swept = _balanced_accuracy(
        all_pos_flat, all_dist_flat, best["direct"], best["related_primary"]
    )
    agg_b2 = _balanced_accuracy(all_pos_flat, all_dist_flat, B2_DIRECT, B2_RELATED)

    # Paired bootstrap on per-anchor Youden delta vs B-2 thresholds.
    youden_swept = _per_anchor_youden(
        all_pos_flat, all_dist_flat, all_lens, best["direct"], best["related_primary"]
    )
    youden_b2 = _per_anchor_youden(
        all_pos_flat, all_dist_flat, all_lens, B2_DIRECT, B2_RELATED
    )
    diffs = youden_swept - youden_b2
    rng = np.random.default_rng(RNG_SEED)
    n = len(diffs)
    samples = np.empty(1000)
    for i in range(1000):
        idx = rng.integers(0, n, size=n)
        samples[i] = diffs[idx].mean()
    delta_mean = float(diffs.mean())
    delta_lo = float(np.quantile(samples, 0.025))
    delta_hi = float(np.quantile(samples, 0.975))
    ci_excludes_zero = bool(delta_lo > 0 or delta_hi < 0)
    direction_positive = delta_mean > 0
    decision = "ADOPT" if (ci_excludes_zero and direction_positive) else "KEEP_B2"

    print(f"sweep best:    direct={best['direct']} related={best['related_primary']}")
    print(f"  train Youden: {best['youden']:.4f}  balanced_acc: {best['balanced_accuracy']:.4f}")
    print(f"holdout pair: {holdout_name}")
    print(
        f"  swept Youden: {holdout_metrics['youden']:.4f}  "
        f"baseline Youden: {baseline_holdout['youden']:.4f}"
    )
    print(
        f"aggregate Youden: swept={agg_swept['youden']:.4f}  "
        f"B-2={agg_b2['youden']:.4f}"
    )
    print(
        f"paired delta Youden: {delta_mean:+.4f} "
        f"[{delta_lo:+.4f}, {delta_hi:+.4f}]"
    )
    print(f"decision: {decision}")

    out = {
        "rng_seed": RNG_SEED,
        "direct_grid": DIRECT_GRID,
        "related_grid": RELATED_GRID,
        "holdout_pair": holdout_name,
        "sweep": sweep_results,
        "best": best,
        "holdout_at_best": holdout_metrics,
        "holdout_at_b2": baseline_holdout,
        "aggregate_at_best": agg_swept,
        "aggregate_at_b2": agg_b2,
        "paired_delta_youden": {
            "mean": delta_mean,
            "lo": delta_lo,
            "hi": delta_hi,
            "ci_excludes_zero": ci_excludes_zero,
        },
        "decision": decision,
    }
    SWEEP_PATH.write_text(json.dumps(out, indent=2, default=str))
    print(f"Wrote {SWEEP_PATH}")

    if decision == "ADOPT":
        # Persist into the same file PairMapper already reads from so the
        # _load_calibrated_thresholds path picks up the new values.
        cal_data = json.loads(CAL_PATH.read_text()) if CAL_PATH.exists() else {}
        cal_data["ndcg_optimal"] = {
            "direct": best["direct"],
            "related_primary": best["related_primary"],
        }
        cal_data["session_7_5_discriminative_optimal"] = {
            "direct": best["direct"],
            "related_primary": best["related_primary"],
            "delta_youden": delta_mean,
            "delta_youden_ci": [delta_lo, delta_hi],
        }
        CAL_PATH.write_text(json.dumps(cal_data, indent=2, default=str))
        print(f"Updated {CAL_PATH}")
    else:
        print("Thresholds unchanged.")


if __name__ == "__main__":
    main()
