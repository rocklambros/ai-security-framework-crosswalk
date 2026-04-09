"""Tests for Mondrian conformal wrapper."""
import numpy as np
import pytest
from classifier.ensemble.conformal import MondrianConformal


@pytest.fixture
def calibration_data():
    rng = np.random.default_rng(42)
    n = 200
    y = rng.integers(0, 4, size=n)
    # Create proba that's somewhat aligned with y
    proba = rng.dirichlet([0.5, 0.5, 0.5, 0.5], size=n)
    for i in range(n):
        proba[i, y[i]] += 0.5
    proba = proba / proba.sum(axis=1, keepdims=True)
    return proba, y


def test_calibrate_sets_q_hat(calibration_data):
    proba, y = calibration_data
    mc = MondrianConformal(alpha=0.10)
    mc.calibrate(proba, y)
    assert len(mc.q_hat) == 4
    for tier, q in mc.q_hat.items():
        assert 0 < q < 1, f"tier {tier}: q_hat={q} out of (0,1)"


def test_coverage_near_target(calibration_data):
    proba, y = calibration_data
    mc = MondrianConformal(alpha=0.10)
    mc.calibrate(proba, y)
    for tier, cov in mc.coverage.items():
        assert cov >= 0.80, f"tier {tier}: coverage {cov:.3f} too low"


def test_predict_sets_nonempty(calibration_data):
    proba, y = calibration_data
    mc = MondrianConformal(alpha=0.10)
    mc.calibrate(proba, y)
    sets = mc.predict_sets(proba)
    assert len(sets) == len(proba)
    for s in sets:
        assert len(s) >= 1


def test_save_load(calibration_data, tmp_path):
    proba, y = calibration_data
    mc = MondrianConformal(alpha=0.10)
    mc.calibrate(proba, y)
    path = tmp_path / "q_hat.json"
    mc.save(path)
    loaded = MondrianConformal.load(path)
    assert loaded.q_hat == mc.q_hat
    assert loaded.alpha == mc.alpha
