"""Anchors-vs-distractors discriminative ranking metric.

For each anchor we have one positive score and ``k`` distractor scores.
The metric is the mean reciprocal rank (MRR) of the positive against the
combined pool, plus Recall@5 and ROC-AUC for diagnostic context. A
1000-resample bootstrap utility provides 95 % CIs over the per-anchor
reciprocal-rank vector.

This file deliberately keeps zero dependency on the rest of the
calibration package — a future caller passes already-computed score
arrays in.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np


@dataclass(frozen=True)
class DiscriminativeScore:
    mrr: float
    recall_at_5: float
    roc_auc: float
    n_anchors: int

    def to_dict(self) -> dict:
        return {
            "mrr": float(self.mrr),
            "recall_at_5": float(self.recall_at_5),
            "roc_auc": float(self.roc_auc),
            "n_anchors": int(self.n_anchors),
        }


def _per_anchor_reciprocal_rank(
    positive: float, distractors: Sequence[float]
) -> float:
    """Reciprocal rank of ``positive`` in the descending sort of
    ``[positive, *distractors]``. Ties are broken pessimistically: if
    ``m`` distractors equal the positive, the positive's rank is
    ``1 + m`` (i.e. it sits below the tied distractors).

    Pessimistic ties are the right default because PairMapper composite
    scores are heavily quantized at the boundaries (0.0, 1.0) and an
    optimistic tie-break would inflate the metric on degenerate scoring.
    """
    above = sum(1 for d in distractors if d > positive)
    tied = sum(1 for d in distractors if d == positive)
    rank = 1 + above + tied
    return 1.0 / rank


def _per_anchor_recall_at_5(
    positive: float, distractors: Sequence[float]
) -> float:
    above = sum(1 for d in distractors if d > positive)
    tied = sum(1 for d in distractors if d == positive)
    rank = 1 + above + tied
    return 1.0 if rank <= 5 else 0.0


def score(
    positive_scores: Sequence[float],
    distractor_scores: Sequence[Sequence[float]],
) -> DiscriminativeScore:
    """Compute MRR, Recall@5, and ROC-AUC for an anchor batch.

    Parameters
    ----------
    positive_scores:
        Length-N array of one composite score per positive anchor.
    distractor_scores:
        Length-N sequence; entry i is the per-distractor score array for
        anchor i. Lengths may vary across anchors.
    """
    if len(positive_scores) != len(distractor_scores):
        raise ValueError("positive and distractor lengths must match")
    if len(positive_scores) == 0:
        return DiscriminativeScore(0.0, 0.0, 0.0, 0)

    rrs = np.array(
        [
            _per_anchor_reciprocal_rank(p, d)
            for p, d in zip(positive_scores, distractor_scores)
        ]
    )
    r5 = np.array(
        [
            _per_anchor_recall_at_5(p, d)
            for p, d in zip(positive_scores, distractor_scores)
        ]
    )

    # ROC-AUC over the flattened (positive vs distractor) score pool.
    y_pos = np.ones(len(positive_scores))
    y_neg_chunks = [np.zeros(len(d)) for d in distractor_scores]
    s_pos = np.asarray(positive_scores, dtype=float)
    s_neg = np.concatenate([np.asarray(d, dtype=float) for d in distractor_scores])
    y = np.concatenate([y_pos, np.concatenate(y_neg_chunks)])
    s = np.concatenate([s_pos, s_neg])
    auc = _roc_auc(y, s)

    return DiscriminativeScore(
        mrr=float(rrs.mean()),
        recall_at_5=float(r5.mean()),
        roc_auc=float(auc),
        n_anchors=len(positive_scores),
    )


def _roc_auc(y: np.ndarray, s: np.ndarray) -> float:
    """Mann-Whitney U formulation. Robust to ties."""
    y = np.asarray(y)
    s = np.asarray(s)
    if len(np.unique(y)) < 2:
        return 0.5
    order = np.argsort(s, kind="mergesort")
    ranks = np.empty_like(order, dtype=float)
    ranks[order] = np.arange(1, len(s) + 1)
    # Average ranks for ties.
    sorted_s = s[order]
    i = 0
    while i < len(sorted_s):
        j = i
        while j + 1 < len(sorted_s) and sorted_s[j + 1] == sorted_s[i]:
            j += 1
        if j > i:
            avg = ranks[order[i : j + 1]].mean()
            ranks[order[i : j + 1]] = avg
        i = j + 1
    n_pos = int(y.sum())
    n_neg = len(y) - n_pos
    if n_pos == 0 or n_neg == 0:
        return 0.5
    sum_ranks_pos = ranks[y == 1].sum()
    u = sum_ranks_pos - n_pos * (n_pos + 1) / 2
    return float(u / (n_pos * n_neg))


def bootstrap_ci(
    positive_scores: Sequence[float],
    distractor_scores: Sequence[Sequence[float]],
    n_resamples: int = 1000,
    rng_seed: int = 20260407,
    alpha: float = 0.05,
) -> dict:
    """Bootstrap a 95 % CI on MRR, Recall@5, and ROC-AUC.

    Resamples are drawn over anchors (per-anchor reciprocal-rank vector
    is the unit of resampling). For ROC-AUC the resample re-pools each
    anchor's distractors, which is the consistent thing to do given the
    metric is computed over the flattened pool.
    """
    n = len(positive_scores)
    if n == 0:
        return {
            "mrr": (0.0, 0.0, 0.0),
            "recall_at_5": (0.0, 0.0, 0.0),
            "roc_auc": (0.5, 0.5, 0.5),
            "n_resamples": n_resamples,
        }
    rng = np.random.default_rng(rng_seed)
    positive_arr = np.asarray(positive_scores, dtype=float)
    rrs = np.array(
        [
            _per_anchor_reciprocal_rank(p, d)
            for p, d in zip(positive_scores, distractor_scores)
        ]
    )
    r5 = np.array(
        [
            _per_anchor_recall_at_5(p, d)
            for p, d in zip(positive_scores, distractor_scores)
        ]
    )

    mrr_samples = np.empty(n_resamples)
    r5_samples = np.empty(n_resamples)
    auc_samples = np.empty(n_resamples)
    for i in range(n_resamples):
        idx = rng.integers(0, n, size=n)
        mrr_samples[i] = rrs[idx].mean()
        r5_samples[i] = r5[idx].mean()
        s_pos = positive_arr[idx]
        s_neg = np.concatenate(
            [np.asarray(distractor_scores[j], dtype=float) for j in idx]
        )
        y = np.concatenate([np.ones(len(s_pos)), np.zeros(len(s_neg))])
        auc_samples[i] = _roc_auc(y, np.concatenate([s_pos, s_neg]))

    def _ci(arr: np.ndarray) -> tuple[float, float, float]:
        lo = float(np.quantile(arr, alpha / 2))
        hi = float(np.quantile(arr, 1 - alpha / 2))
        return (float(arr.mean()), lo, hi)

    return {
        "mrr": _ci(mrr_samples),
        "recall_at_5": _ci(r5_samples),
        "roc_auc": _ci(auc_samples),
        "n_resamples": n_resamples,
    }


def paired_bootstrap_delta(
    positive_a: Sequence[float],
    distractors_a: Sequence[Sequence[float]],
    positive_b: Sequence[float],
    distractors_b: Sequence[Sequence[float]],
    n_resamples: int = 1000,
    rng_seed: int = 20260407,
    alpha: float = 0.05,
) -> dict:
    """Paired bootstrap on the per-anchor MRR delta (a - b)."""
    n = len(positive_a)
    if n != len(positive_b) or n != len(distractors_a) or n != len(distractors_b):
        raise ValueError("paired bootstrap requires identical anchor ordering")
    rrs_a = np.array(
        [
            _per_anchor_reciprocal_rank(p, d)
            for p, d in zip(positive_a, distractors_a)
        ]
    )
    rrs_b = np.array(
        [
            _per_anchor_reciprocal_rank(p, d)
            for p, d in zip(positive_b, distractors_b)
        ]
    )
    diffs = rrs_a - rrs_b
    rng = np.random.default_rng(rng_seed)
    samples = np.empty(n_resamples)
    for i in range(n_resamples):
        idx = rng.integers(0, n, size=n)
        samples[i] = diffs[idx].mean()
    lo = float(np.quantile(samples, alpha / 2))
    hi = float(np.quantile(samples, 1 - alpha / 2))
    return {
        "delta_mrr_mean": float(diffs.mean()),
        "delta_mrr_ci": (lo, hi),
        "ci_excludes_zero": bool(lo > 0 or hi < 0),
        "n_resamples": n_resamples,
    }
