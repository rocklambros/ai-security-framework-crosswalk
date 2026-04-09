"""Tests for statistical test functions."""
import numpy as np
import pytest
from classifier.sacred.stats import bootstrap_ci, mcnemar_test, permutation_test, bh_correct


def _accuracy(y_true, y_pred):
    return float(np.mean(y_true == y_pred))


def test_bootstrap_ci_contains_point():
    rng = np.random.RandomState(42)
    y_true = rng.randint(0, 4, size=200)
    y_pred = y_true.copy()
    y_pred[:20] = (y_pred[:20] + 1) % 4  # 10% error
    point, lo, hi = bootstrap_ci(y_true, y_pred, _accuracy)
    assert lo <= point <= hi
    assert 0.85 < point < 0.95


def test_bootstrap_ci_width():
    rng = np.random.RandomState(42)
    y_true = rng.randint(0, 2, size=100)
    y_pred = y_true.copy()
    y_pred[:30] = 1 - y_pred[:30]
    _, lo, hi = bootstrap_ci(y_true, y_pred, _accuracy, n_resamples=5000)
    assert hi - lo > 0.05  # non-trivial width
    assert hi - lo < 0.30  # not absurdly wide


def test_mcnemar_identical_classifiers():
    y = np.array([0, 1, 2, 3] * 25)
    pred = np.array([0, 1, 2, 0] * 25)
    stat, p = mcnemar_test(y, pred, pred)
    assert p == 1.0  # identical predictions


def test_mcnemar_different_classifiers():
    y = np.array([0, 1, 0, 1] * 50)
    pred_a = y.copy()
    pred_b = np.zeros_like(y)  # always predicts 0
    stat, p = mcnemar_test(y, pred_a, pred_b)
    assert p < 0.05  # significantly different


def test_permutation_test_identical():
    y = np.array([0, 1, 2] * 30)
    pred = np.array([0, 1, 0] * 30)
    diff, p = permutation_test(y, pred, pred)
    assert diff == 0.0
    assert p > 0.95  # no difference


def test_permutation_test_different():
    y = np.array([0, 1] * 100)
    pred_a = y.copy()  # perfect
    pred_b = np.zeros(200)  # always 0
    diff, p = permutation_test(y, pred_a, pred_b, n_permutations=1000)
    assert diff > 0
    assert p < 0.05


def test_bh_correct_order():
    p_values = [0.01, 0.03, 0.049, 0.10, 0.50]
    results = bh_correct(p_values, alpha=0.05)
    # With 5 tests: p=0.01 → adj=0.05 (significant), p=0.03 → adj=0.075 (not)
    assert results[0][2] is True   # p=0.01, adj=0.05
    assert results[1][2] is False  # p=0.03, adj=0.075
    # Adjusted p-values should be >= original
    for orig_idx, adj_p, sig in results:
        assert adj_p >= p_values[orig_idx] - 1e-10


def test_bh_correct_empty():
    assert bh_correct([]) == []
