"""Tests for mapping_engine.calibration.weight_learner."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from mapping_engine.calibration.weight_learner import (
    FEATURES,
    evaluate_model,
    train_lightgbm,
    train_logistic,
    train_ordinal,
)

REPO = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def synthetic_df() -> pd.DataFrame:
    """A synthetic but well-separated dataset (no graph required)."""
    rng = np.random.default_rng(0)
    n = 200
    pos = pd.DataFrame(
        {
            "bridge_score": rng.uniform(0.5, 1.0, n // 2),
            "semantic_score": rng.uniform(0.6, 1.0, n // 2),
            "keyword_score": rng.uniform(0.4, 1.0, n // 2),
            "function_match": rng.choice([0.0, 1.0], n // 2, p=[0.2, 0.8]),
        }
    )
    pos["is_mapped"] = 1
    pos["expert_tier"] = "Direct"
    neg = pd.DataFrame(
        {
            "bridge_score": rng.uniform(0.0, 0.4, n // 2),
            "semantic_score": rng.uniform(0.0, 0.4, n // 2),
            "keyword_score": rng.uniform(0.0, 0.4, n // 2),
            "function_match": rng.choice([0.0, 1.0], n // 2, p=[0.8, 0.2]),
        }
    )
    neg["is_mapped"] = 0
    neg["expert_tier"] = "None"
    return pd.concat([pos, neg], ignore_index=True).sample(frac=1, random_state=1).reset_index(drop=True)


def test_logistic_coefficients_shape(synthetic_df):
    model, coefs = train_logistic(synthetic_df)
    assert set(FEATURES).issubset(coefs.keys())
    assert "intercept" in coefs
    assert len(model.coef_[0]) == len(FEATURES)


def test_logistic_high_train_accuracy(synthetic_df):
    model, _ = train_logistic(synthetic_df)
    metrics = evaluate_model(model, synthetic_df, "logistic")
    assert metrics["accuracy"] > 0.80


def test_evaluate_model_returns_metrics(synthetic_df):
    model, _ = train_logistic(synthetic_df)
    metrics = evaluate_model(model, synthetic_df, "logistic")
    for key in ("accuracy", "precision", "recall", "f1", "roc_auc"):
        assert key in metrics
        assert 0.0 <= metrics[key] <= 1.0


def test_lightgbm_trains(synthetic_df):
    model, imp = train_lightgbm(synthetic_df)
    assert set(FEATURES).issubset(imp.keys())
    metrics = evaluate_model(model, synthetic_df, "lightgbm")
    assert metrics["accuracy"] > 0.75


def test_ordinal_trains(synthetic_df):
    model, coefs = train_ordinal(synthetic_df)
    assert set(FEATURES).issubset(coefs.keys())
    metrics = evaluate_model(model, synthetic_df, "ordinal")
    assert "tier_accuracy" in metrics
