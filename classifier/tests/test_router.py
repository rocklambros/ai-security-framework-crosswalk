"""Tests for KL-disagreement router."""
import numpy as np
import pytest
from classifier.ensemble.router import DisagreementRouter, kl_divergence


def test_kl_uniform_is_zero():
    p = np.array([[0.25, 0.25, 0.25, 0.25]])
    q = np.array([[0.25, 0.25, 0.25, 0.25]])
    kl = kl_divergence(p, q)
    assert np.isclose(kl[0], 0.0, atol=1e-8)


def test_kl_peaked_is_positive():
    p = np.array([[0.9, 0.03, 0.03, 0.04]])
    q = np.array([[0.25, 0.25, 0.25, 0.25]])
    kl = kl_divergence(p, q)
    assert kl[0] > 0.5


def test_route_low_confidence():
    router = DisagreementRouter(tau=0.5)
    # Near-uniform = low confidence = needs_review
    proba = np.array([[0.26, 0.25, 0.24, 0.25]])
    mask = router.route(proba)
    assert mask[0] == True  # needs_review


def test_route_high_confidence():
    router = DisagreementRouter(tau=0.5)
    # Very peaked = high confidence = no review
    proba = np.array([[0.92, 0.03, 0.03, 0.02]])
    mask = router.route(proba)
    assert mask[0] == False  # confident


def test_tune_tau():
    rng = np.random.default_rng(42)
    n = 100
    proba = rng.dirichlet([1, 1, 1, 1], size=n)
    y_true = rng.integers(0, 4, size=n)
    y_pred = np.argmax(proba, axis=1)
    router = DisagreementRouter()
    tau = router.tune_tau(proba, y_true, y_pred, target_precision=0.50)
    assert tau > 0


def test_save_load(tmp_path):
    router = DisagreementRouter(tau=0.42)
    path = tmp_path / "router.json"
    router.save(path)
    loaded = DisagreementRouter.load(path)
    assert loaded.tau == 0.42
