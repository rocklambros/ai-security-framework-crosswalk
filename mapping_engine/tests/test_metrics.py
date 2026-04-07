"""Tests for mapping_engine.calibration.metrics."""

from __future__ import annotations

import numpy as np
import pytest

from mapping_engine.calibration.metrics import (
    bootstrap_metric_ci,
    ndcg_at_k,
    spearman,
    tier_accuracy,
)


def test_tier_accuracy_basic():
    assert tier_accuracy(["Direct", "Related", "None"], ["Direct", "Related", "None"]) == 1.0
    assert tier_accuracy(["Direct", "Related"], ["Direct", "None"]) == 0.5
    assert tier_accuracy([], []) == 0.0


def test_spearman_perfect_and_inverse():
    assert spearman([1, 2, 3, 4], [10, 20, 30, 40]) == pytest.approx(1.0)
    assert spearman([1, 2, 3, 4], [40, 30, 20, 10]) == pytest.approx(-1.0)
    assert spearman([1, 1, 1, 1], [4, 3, 2, 1]) == 0.0
    assert spearman([1], [1]) == 0.0


def test_spearman_handles_ties():
    # Two ties on each side, average ranks should yield a positive correlation.
    s = spearman([1, 2, 2, 3], [10, 20, 20, 30])
    assert s == pytest.approx(1.0)


def test_ndcg_at_k_perfect_and_reversed():
    rel = [3, 2, 1, 0]
    assert ndcg_at_k(rel, [4, 3, 2, 1], k=4) == pytest.approx(1.0)
    # Reversed ranking: still > 0 but < 1
    val = ndcg_at_k(rel, [1, 2, 3, 4], k=4)
    assert 0.0 < val < 1.0
    # Empty
    assert ndcg_at_k([], [], k=10) == 0.0
    # All-zero relevance returns 0
    assert ndcg_at_k([0, 0, 0], [1, 2, 3], k=3) == 0.0


def test_ndcg_at_k_truncates_to_k():
    rel = np.array([3, 2, 1, 0, 0, 0, 0, 0, 0, 0, 0])
    score = np.arange(11)[::-1]
    v = ndcg_at_k(rel, score, k=3)
    assert v == pytest.approx(1.0)


def test_bootstrap_metric_ci_brackets_point():
    rng = np.random.default_rng(0)
    y_true = rng.integers(0, 2, size=200)
    y_pred = y_true.copy()
    y_pred[:10] = 1 - y_pred[:10]  # 5% error -> 0.95 accuracy
    out = bootstrap_metric_ci(
        lambda a, b: float((a == b).mean()),
        y_true,
        y_pred,
        n_resamples=400,
        rng=1,
    )
    assert out["point"] == pytest.approx(0.95)
    assert out["lo"] <= out["point"] <= out["hi"]
    assert 0.0 <= out["lo"] <= 1.0
    assert 0.0 <= out["hi"] <= 1.0
    assert out["n_resamples"] == 400


def test_bootstrap_metric_ci_empty_raises():
    with pytest.raises(ValueError):
        bootstrap_metric_ci(lambda a: 0.0, np.array([]))


def test_bootstrap_metric_ci_mismatched_lengths_raises():
    with pytest.raises(ValueError):
        bootstrap_metric_ci(lambda a, b: 0.0, np.array([1, 2, 3]), np.array([1, 2]))
