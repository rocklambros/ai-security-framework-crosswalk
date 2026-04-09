# classifier/tests/test_integration_v2.py
"""Integration test: verify the v2 pipeline components wire together."""
import json
import tempfile
from pathlib import Path

import numpy as np
import pytest


def test_tier_mapper_to_training_data(tmp_path):
    """Verify tier mapping produces valid training data schema."""
    from classifier.data.tier_mapper import map_upstream_tier, TierLabel

    test_cases = [
        {"tier": "Foundational", "scope": "Both", "expected": TierLabel.EQUIVALENT},
        {"tier": "Hardening", "scope": "Both", "expected": TierLabel.RELATED},
        {"tier": "Advanced", "scope": "Both", "expected": TierLabel.PARTIAL},
    ]
    for tc in test_cases:
        result = map_upstream_tier(tier=tc["tier"], scope=tc["scope"])
        assert result == tc["expected"]


def test_leakage_firewall_on_real_splits():
    """Verify leakage firewall passes on actual data splits if they exist."""
    frozen_path = Path("data/splits/human_test_frozen.jsonl")
    cal_path = Path("data/splits/human_cal.jsonl")
    if not frozen_path.exists() or not cal_path.exists():
        pytest.skip("Data splits not available")

    from classifier.ensemble.leakage_firewall import (
        load_frozen_keys, load_cal_keys, extract_nodes_from_keys, check_no_leakage,
    )

    frozen = load_frozen_keys()
    cal = load_cal_keys()
    frozen_cal_nodes = extract_nodes_from_keys(frozen | cal)

    check_no_leakage(
        train_pair_keys=set(),
        test_pair_keys=frozen,
        cal_pair_keys=cal,
        graph_edge_pairs=set(),
        negative_sample_nodes=set(),
        test_cal_nodes=frozen_cal_nodes,
    )


def test_corn_loss_roundtrip():
    """Verify CORN loss → prediction → probability roundtrip."""
    torch = pytest.importorskip("torch")
    from classifier.ensemble.corn_loss import corn_loss, corn_label_from_logits, corn_proba_from_logits

    logits = torch.randn(16, 3)
    labels = torch.randint(0, 4, (16,))

    loss = corn_loss(logits, labels, n_classes=4)
    assert loss.item() > 0

    preds = corn_label_from_logits(logits, n_classes=4)
    assert preds.shape == (16,)
    assert preds.min() >= 0 and preds.max() <= 3

    probs = corn_proba_from_logits(logits, n_classes=4)
    assert probs.shape == (16, 4)
    np.testing.assert_allclose(probs.sum(dim=1).numpy(), 1.0, atol=1e-5)


def test_two_stage_roundtrip():
    """Verify two-stage fit → predict → save → load roundtrip."""
    from classifier.ensemble.two_stage import TwoStageClassifier

    rng = np.random.RandomState(42)
    X = rng.randn(80, 10)
    y = rng.choice([0, 1, 2, 3], size=80)

    clf = TwoStageClassifier()
    clf.fit(X, y)

    proba = clf.predict_proba(X)
    assert proba.shape == (80, 4)

    preds = clf.predict(X)
    assert set(preds).issubset({0, 1, 2, 3})

    # Save/load roundtrip
    with tempfile.TemporaryDirectory() as tmpdir:
        clf.save(Path(tmpdir))
        clf2 = TwoStageClassifier.load(Path(tmpdir))
        proba2 = clf2.predict_proba(X)
        np.testing.assert_allclose(proba, proba2, atol=1e-6)
