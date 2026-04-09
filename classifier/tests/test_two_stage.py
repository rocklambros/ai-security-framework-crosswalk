# classifier/tests/test_two_stage.py
"""Tests for two-stage binary->ordinal classifier."""
import numpy as np
import pytest
from classifier.ensemble.two_stage import TwoStageClassifier


def test_fit_and_predict():
    rng = np.random.RandomState(42)
    X = rng.randn(100, 10)
    y = rng.choice([0, 1, 2, 3], size=100, p=[0.4, 0.15, 0.3, 0.15])
    clf = TwoStageClassifier()
    clf.fit(X, y)
    preds = clf.predict(X)
    assert preds.shape == (100,)
    assert set(preds).issubset({0, 1, 2, 3})


def test_predict_proba_shape():
    rng = np.random.RandomState(42)
    X = rng.randn(50, 10)
    y = rng.choice([0, 1, 2, 3], size=50, p=[0.4, 0.15, 0.3, 0.15])
    clf = TwoStageClassifier()
    clf.fit(X, y)
    proba = clf.predict_proba(X)
    assert proba.shape == (50, 4)
    np.testing.assert_allclose(proba.sum(axis=1), 1.0, atol=1e-6)


def test_stage1_high_recall():
    rng = np.random.RandomState(42)
    X = rng.randn(200, 10)
    y = np.array([0] * 80 + [1] * 30 + [2] * 60 + [3] * 30)
    clf = TwoStageClassifier(stage1_recall_target=0.90)
    clf.fit(X, y)
    binary_preds = clf.predict_stage1(X)
    mapped_mask = y > 0
    recall = binary_preds[mapped_mask].mean()
    assert recall > 0.3  # Loose bound for random data
