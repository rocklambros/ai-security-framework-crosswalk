"""Tests for LightGBM stacker."""
import numpy as np
import pytest
from classifier.ensemble.stacker import LGBMStacker, tune_stacker, N_CLASSES


@pytest.fixture
def toy_data():
    rng = np.random.default_rng(42)
    n = 200
    X = rng.standard_normal((n, 3))
    y = rng.integers(0, N_CLASSES, size=n)
    return X, y


def test_fit_predict_shape(toy_data):
    X, y = toy_data
    stacker = LGBMStacker({"n_estimators": 10})
    stacker.fit(X, y)
    proba = stacker.predict_proba(X)
    assert proba.shape == (200, N_CLASSES)
    assert np.allclose(proba.sum(axis=1), 1.0, atol=1e-6)


def test_predict_returns_classes(toy_data):
    X, y = toy_data
    stacker = LGBMStacker({"n_estimators": 10})
    stacker.fit(X, y)
    preds = stacker.predict(X)
    assert preds.shape == (200,)
    assert set(preds).issubset({0, 1, 2, 3})


def test_sample_weight_accepted(toy_data):
    X, y = toy_data
    w = np.ones(200) * 0.6
    stacker = LGBMStacker({"n_estimators": 10})
    stacker.fit(X, y, sample_weight=w)
    proba = stacker.predict_proba(X)
    assert proba.shape == (200, N_CLASSES)


def test_save_load(toy_data, tmp_path):
    X, y = toy_data
    stacker = LGBMStacker({"n_estimators": 10})
    stacker.fit(X, y)
    path = tmp_path / "model.txt"
    stacker.save(path)
    loaded = LGBMStacker.load(path)
    np.testing.assert_allclose(
        stacker.predict_proba(X), loaded.predict_proba(X), atol=1e-10
    )


def test_tune_stacker_returns_params(toy_data):
    X, y = toy_data
    params = tune_stacker(X, y, n_trials=3, n_splits=3)
    assert "num_leaves" in params
    assert "learning_rate" in params


def test_not_fitted_raises():
    stacker = LGBMStacker()
    with pytest.raises(RuntimeError, match="not fitted"):
        stacker.predict_proba(np.zeros((5, 3)))
