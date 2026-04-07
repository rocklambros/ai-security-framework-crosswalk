"""Tests for mapping_engine.calibration.weight_stability."""

from __future__ import annotations

import numpy as np
import pandas as pd

from mapping_engine.calibration.weight_learner import FEATURES, train_logistic
from mapping_engine.calibration.weight_stability import analyze_weight_stability


def _make_df() -> pd.DataFrame:
    rng = np.random.default_rng(7)
    n = 120
    pos = pd.DataFrame(
        {
            "bridge_score": rng.uniform(0.5, 1.0, n // 2),
            "semantic_score": rng.uniform(0.6, 1.0, n // 2),
            "keyword_score": rng.uniform(0.4, 1.0, n // 2),
            "function_match": rng.choice([0.0, 1.0], n // 2, p=[0.2, 0.8]),
            "is_mapped": 1,
            "expert_tier": "Direct",
        }
    )
    neg = pd.DataFrame(
        {
            "bridge_score": rng.uniform(0.0, 0.4, n // 2),
            "semantic_score": rng.uniform(0.0, 0.4, n // 2),
            "keyword_score": rng.uniform(0.0, 0.4, n // 2),
            "function_match": rng.choice([0.0, 1.0], n // 2, p=[0.8, 0.2]),
            "is_mapped": 0,
            "expert_tier": "None",
        }
    )
    return pd.concat([pos, neg], ignore_index=True)


def test_zero_perturbation_no_change():
    df = _make_df()
    model, _ = train_logistic(df)
    out = analyze_weight_stability(df, model, "logistic", perturbation=0.0)
    for feat, stats in out.items():
        assert stats["pct_changed"] == 0.0


def test_returns_all_features():
    df = _make_df()
    model, _ = train_logistic(df)
    out = analyze_weight_stability(df, model, "logistic", perturbation=0.15)
    assert set(out.keys()) == set(FEATURES)
    for stats in out.values():
        assert "pct_changed" in stats
