"""Statistical tests for the sacred run and ablation analysis.

Implements bootstrap CI, McNemar's test, permutation test, and BH-FDR
correction as required by the pre-registered analysis plan (Contract 15).
"""
from __future__ import annotations

import numpy as np
from scipy import stats


def bootstrap_ci(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    metric_fn,
    n_resamples: int = 10000,
    alpha: float = 0.05,
    seed: int = 42,
) -> tuple[float, float, float]:
    """Bootstrap confidence interval for a metric.

    Returns (point_estimate, ci_lower, ci_upper).
    """
    rng = np.random.RandomState(seed)
    n = len(y_true)
    point = metric_fn(y_true, y_pred)
    boot_stats = np.empty(n_resamples)
    for i in range(n_resamples):
        idx = rng.randint(0, n, size=n)
        boot_stats[i] = metric_fn(y_true[idx], y_pred[idx])
    lo = float(np.percentile(boot_stats, 100 * alpha / 2))
    hi = float(np.percentile(boot_stats, 100 * (1 - alpha / 2)))
    return float(point), lo, hi


def mcnemar_test(
    y_true: np.ndarray,
    pred_a: np.ndarray,
    pred_b: np.ndarray,
) -> tuple[float, float]:
    """McNemar's test comparing two classifiers.

    Returns (statistic, p_value).
    Tests if the disagreements between pred_a and pred_b are symmetric.
    """
    correct_a = (pred_a == y_true)
    correct_b = (pred_b == y_true)
    # b: A correct, B wrong; c: A wrong, B correct
    b = int(np.sum(correct_a & ~correct_b))
    c = int(np.sum(~correct_a & correct_b))

    if b + c == 0:
        return 0.0, 1.0

    # Exact binomial test (more reliable than chi-squared for small n)
    result = stats.binomtest(b, b + c, 0.5)
    # Use chi-squared with continuity correction for the statistic
    stat = (abs(b - c) - 1) ** 2 / (b + c) if (b + c) > 0 else 0.0
    return float(stat), float(result.pvalue)


def permutation_test(
    y_true: np.ndarray,
    pred_a: np.ndarray,
    pred_b: np.ndarray,
    metric_fn=None,
    n_permutations: int = 10000,
    seed: int = 42,
) -> tuple[float, float]:
    """Permutation test for difference in metric between two classifiers.

    Returns (observed_diff, p_value).
    """
    if metric_fn is None:
        metric_fn = lambda yt, yp: float(np.mean(yt == yp))

    rng = np.random.RandomState(seed)
    obs_diff = metric_fn(y_true, pred_a) - metric_fn(y_true, pred_b)

    count = 0
    for _ in range(n_permutations):
        # For each sample, randomly swap pred_a and pred_b
        swap = rng.randint(0, 2, size=len(y_true)).astype(bool)
        perm_a = np.where(swap, pred_b, pred_a)
        perm_b = np.where(swap, pred_a, pred_b)
        perm_diff = metric_fn(y_true, perm_a) - metric_fn(y_true, perm_b)
        if abs(perm_diff) >= abs(obs_diff):
            count += 1

    p_value = (count + 1) / (n_permutations + 1)
    return float(obs_diff), float(p_value)


def bh_correct(p_values: list[float], alpha: float = 0.05) -> list[tuple[int, float, bool]]:
    """Benjamini-Hochberg FDR correction.

    Returns list of (original_index, adjusted_p_value, is_significant).
    """
    n = len(p_values)
    if n == 0:
        return []

    # Sort by p-value
    indexed = sorted(enumerate(p_values), key=lambda x: x[1])
    adjusted = [0.0] * n

    # BH adjustment
    prev_adj = 1.0
    for rank_idx in range(n - 1, -1, -1):
        orig_idx, p = indexed[rank_idx]
        rank = rank_idx + 1
        adj = min(prev_adj, p * n / rank)
        adjusted[orig_idx] = adj
        prev_adj = adj

    return [(i, adjusted[i], adjusted[i] <= alpha) for i in range(n)]
