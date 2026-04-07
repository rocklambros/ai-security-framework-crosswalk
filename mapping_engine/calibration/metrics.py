"""Ranking and tier metrics with bootstrap CI for B-2 calibration.

All functions accept plain numpy arrays / sequences and return plain Python
floats or dicts. Used by ``learn_weights.py`` (B2.7+) to evaluate per-pair
and aggregate calibration quality with confidence intervals.
"""

from __future__ import annotations

from typing import Callable, Sequence

import numpy as np


def tier_accuracy(y_true: Sequence, y_pred: Sequence) -> float:
    """Fraction of items where predicted tier label equals true tier label."""
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    if len(y_true) == 0:
        return 0.0
    return float((y_true == y_pred).mean())


def spearman(y_true: Sequence[float], y_score: Sequence[float]) -> float:
    """Spearman rank correlation between true relevance and predicted score.

    Returns 0.0 for empty input or zero-variance input (degenerate case).
    Implemented locally to avoid pulling scipy.stats just for one call.
    """
    y_true = np.asarray(y_true, dtype=float)
    y_score = np.asarray(y_score, dtype=float)
    n = len(y_true)
    if n < 2:
        return 0.0
    rt = _rankdata(y_true)
    rs = _rankdata(y_score)
    rt -= rt.mean()
    rs -= rs.mean()
    denom = float(np.sqrt((rt * rt).sum() * (rs * rs).sum()))
    if denom == 0.0:
        return 0.0
    return float((rt * rs).sum() / denom)


def _rankdata(a: np.ndarray) -> np.ndarray:
    """Average-rank tie-breaking, matches scipy.stats.rankdata default."""
    a = np.asarray(a, dtype=float)
    order = np.argsort(a, kind="mergesort")
    ranks = np.empty_like(order, dtype=float)
    ranks[order] = np.arange(1, len(a) + 1, dtype=float)
    # average ties
    sorted_a = a[order]
    i = 0
    while i < len(a):
        j = i + 1
        while j < len(a) and sorted_a[j] == sorted_a[i]:
            j += 1
        if j - i > 1:
            avg = ranks[order[i:j]].mean()
            ranks[order[i:j]] = avg
        i = j
    return ranks


def ndcg_at_k(y_true: Sequence[float], y_score: Sequence[float], k: int = 10) -> float:
    """Normalized DCG at k. y_true is graded relevance (e.g. tier weight)."""
    y_true = np.asarray(y_true, dtype=float)
    y_score = np.asarray(y_score, dtype=float)
    n = len(y_true)
    if n == 0:
        return 0.0
    k = min(k, n)
    order = np.argsort(-y_score, kind="mergesort")[:k]
    gains = (2.0 ** y_true[order] - 1.0)
    discounts = 1.0 / np.log2(np.arange(2, k + 2))
    dcg = float((gains * discounts).sum())
    ideal_order = np.argsort(-y_true, kind="mergesort")[:k]
    ideal_gains = (2.0 ** y_true[ideal_order] - 1.0)
    idcg = float((ideal_gains * discounts).sum())
    if idcg == 0.0:
        return 0.0
    return dcg / idcg


def bootstrap_metric_ci(
    metric_fn: Callable,
    *arrays: Sequence,
    n_resamples: int = 1000,
    alpha: float = 0.05,
    rng: int | np.random.Generator | None = None,
) -> dict:
    """Generic bootstrap CI for a metric callable with paired arrays.

    All ``arrays`` are resampled jointly with the same row indices, so paired
    structure (e.g. y_true, y_score) is preserved. Returns a dict with
    ``point``, ``lo``, ``hi``, ``mean``, ``std``, ``n_resamples``, ``alpha``.
    """
    if not arrays:
        raise ValueError("at least one array required")
    arrs = [np.asarray(a) for a in arrays]
    n = len(arrs[0])
    if n == 0:
        raise ValueError("empty input")
    if any(len(a) != n for a in arrs):
        raise ValueError("all arrays must share length")
    if isinstance(rng, np.random.Generator):
        gen = rng
    else:
        gen = np.random.default_rng(rng)
    point = float(metric_fn(*arrs))
    samples = np.empty(n_resamples, dtype=float)
    for i in range(n_resamples):
        idx = gen.integers(0, n, size=n)
        samples[i] = float(metric_fn(*[a[idx] for a in arrs]))
    lo = float(np.quantile(samples, alpha / 2))
    hi = float(np.quantile(samples, 1 - alpha / 2))
    return {
        "point": point,
        "lo": lo,
        "hi": hi,
        "mean": float(samples.mean()),
        "std": float(samples.std(ddof=1)) if n_resamples > 1 else 0.0,
        "n_resamples": n_resamples,
        "alpha": alpha,
    }
