"""Tests for black-box label shift correction."""
import numpy as np
import pytest


def test_label_shift_preserves_probabilities():
    """Adjusted probabilities should still be valid (sum to 1, non-negative)."""
    from classifier.ensemble.label_shift import adjust_label_shift

    rng = np.random.RandomState(42)
    proba = rng.dirichlet([1, 1, 1, 1], size=50)
    source_prior = np.array([0.64, 0.00, 0.09, 0.27])
    target_prior = np.array([0.20, 0.20, 0.47, 0.15])

    adjusted = adjust_label_shift(proba, source_prior, target_prior)
    np.testing.assert_allclose(adjusted.sum(axis=1), 1.0, atol=1e-6)
    assert (adjusted >= 0).all()


def test_label_shift_upweights_missing_class():
    """Class with zero source prior but nonzero target prior should be upweighted."""
    from classifier.ensemble.label_shift import adjust_label_shift

    proba = np.array([[0.4, 0.01, 0.3, 0.29]])
    source_prior = np.array([0.64, 0.001, 0.09, 0.27])
    target_prior = np.array([0.20, 0.20, 0.47, 0.15])

    adjusted = adjust_label_shift(proba, source_prior, target_prior)
    assert adjusted[0, 1] > proba[0, 1]


def test_label_shift_identity_when_priors_equal():
    """No adjustment when source and target priors match."""
    from classifier.ensemble.label_shift import adjust_label_shift

    rng = np.random.RandomState(42)
    proba = rng.dirichlet([1, 1, 1, 1], size=20)
    prior = np.array([0.25, 0.25, 0.25, 0.25])

    adjusted = adjust_label_shift(proba, prior, prior)
    np.testing.assert_allclose(adjusted, proba, atol=1e-6)
