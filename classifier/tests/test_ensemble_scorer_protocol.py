"""Test that EnsembleScorer conforms to Plan 3 Scorer protocol."""
import numpy as np
import pytest
from classifier.baselines.protocol import NodePair, ScoreRecord, Scorer
from classifier.ensemble.stacker import LGBMStacker
from classifier.ensemble.conformal import MondrianConformal
from classifier.ensemble.router import DisagreementRouter
from classifier.ensemble.scorer import EnsembleScorer


@pytest.fixture
def toy_ensemble():
    rng = np.random.default_rng(42)
    X = rng.standard_normal((100, 3))
    y = rng.integers(0, 4, size=100)
    stacker = LGBMStacker({"n_estimators": 10})
    stacker.fit(X, y)

    proba = stacker.predict_proba(X)
    conformal = MondrianConformal(alpha=0.10)
    conformal.calibrate(proba, y)

    router = DisagreementRouter(tau=0.5)
    return EnsembleScorer(stacker, conformal, router, version="test-0.1")


def test_scorer_has_protocol_attributes(toy_ensemble):
    assert hasattr(toy_ensemble, "name")
    assert hasattr(toy_ensemble, "version")
    assert hasattr(toy_ensemble, "score")


def test_score_features_returns_score_records(toy_ensemble):
    rng = np.random.default_rng(42)
    pairs = [
        NodePair(
            pair_key=f"test_pair_{i}",
            source_node_id=f"fw_a:S{i}",
            source_framework="fw_a",
            source_text="source text",
            target_node_id=f"fw_b:T{i}",
            target_framework="fw_b",
            target_text="target text",
        )
        for i in range(5)
    ]
    X = rng.standard_normal((5, 3))
    records = toy_ensemble.score_features(pairs, X)
    assert len(records) == 5
    for r in records:
        assert isinstance(r, ScoreRecord)
        assert r.scorer_name == "ensemble_v1"
        assert r.tier_pred in ("unrelated", "partial", "related", "equivalent")
        assert 0 <= r.score <= 1
        assert "conformal_set" in r.extras
        assert "needs_review" in r.extras
