"""Tests for mapping_engine.calibration.diagnostics."""

from __future__ import annotations

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

from mapping_engine.calibration.diagnostics import (
    bootstrap_ci,
    learning_curve,
    permutation_importance_ci,
    reliability_curve,
)


def _make_classification(n: int = 200, seed: int = 0) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    X = rng.normal(size=(n, 4))
    # Only feature 0 and 1 carry signal; 2 and 3 are noise.
    y = ((X[:, 0] + X[:, 1] + 0.2 * rng.normal(size=n)) > 0).astype(np.int64)
    return X, y


def test_bootstrap_ci_brackets_point_estimate():
    rng = np.random.default_rng(0)
    y_true = rng.integers(0, 2, size=200)
    y_pred = y_true.copy()
    y_pred[:20] = 1 - y_pred[:20]  # 10% error
    out = bootstrap_ci(accuracy_score, y_true, y_pred, n_resamples=500, rng=1)
    assert 0.0 <= out["lo"] <= out["point"] <= out["hi"] <= 1.0
    assert out["point"] == 0.9
    assert out["n_resamples"] == 500
    assert "alpha" in out


def test_bootstrap_ci_empty_raises():
    import pytest

    with pytest.raises(ValueError):
        bootstrap_ci(accuracy_score, np.array([]), np.array([]))


def test_permutation_importance_ci_drops_noise_features():
    X, y = _make_classification(n=300, seed=1)
    model = LogisticRegression(max_iter=500).fit(X, y)
    out = permutation_importance_ci(
        model, X, y, feature_names=["a", "b", "noise1", "noise2"], n_repeats=20, rng=2
    )
    # Real features should have positive importance with CI excluding zero.
    assert out["a"]["mean"] > 0
    assert out["b"]["mean"] > 0
    assert out["a"]["ci_excludes_zero"] is True
    assert out["b"]["ci_excludes_zero"] is True
    # Noise features should have small importance, often with CI overlapping zero.
    assert out["noise1"]["mean"] < out["a"]["mean"]
    assert out["noise2"]["mean"] < out["b"]["mean"]


def test_learning_curve_shape_and_keys():
    X, y = _make_classification(n=200, seed=2)
    factory = lambda: LogisticRegression(max_iter=500)
    out = learning_curve(factory, X, y, fractions=(0.4, 0.7, 1.0), cv=4, rng=42)
    assert len(out["fractions"]) == 3
    assert len(out["train_mean"]) == 3
    assert len(out["cv_mean"]) == 3
    assert len(out["cv_std"]) == 3
    # CV std must be non-negative.
    for s in out["cv_std"]:
        assert s >= 0.0


def test_reliability_curve_perfect_calibration_is_diagonal():
    rng = np.random.default_rng(3)
    n = 5000
    proba = rng.uniform(0.0, 1.0, size=n)
    y_true = (rng.uniform(size=n) < proba).astype(np.int64)
    out = reliability_curve(y_true, proba, n_bins=10)
    assert len(out["bin_centers"]) == len(out["predicted_mean"])
    assert len(out["bin_centers"]) == len(out["observed_mean"])
    # In a well-sampled diagonal, |observed - predicted| should be small per bin.
    diffs = np.abs(np.array(out["observed_mean"]) - np.array(out["predicted_mean"]))
    assert diffs.max() < 0.10


def test_reliability_curve_skips_empty_bins():
    # All probabilities in [0.4, 0.6] — only middle bins should be populated.
    n = 200
    proba = np.linspace(0.4, 0.6, n)
    y_true = (proba > 0.5).astype(np.int64)
    out = reliability_curve(y_true, proba, n_bins=10)
    # Bins outside [0.4, 0.6] should be omitted.
    for center in out["bin_centers"]:
        assert 0.35 <= center <= 0.65
