"""Tests for upstream tier → 4-class mapping."""
import pytest
from classifier.data.tier_mapper import (
    SOFT_PRIORS, TierLabel, expand_soft_labels, map_expert_tier, map_upstream_tier,
)


def test_soft_priors_sum_to_one():
    for tier, priors in SOFT_PRIORS.items():
        total = sum(priors.values())
        assert abs(total - 1.0) < 1e-9, f"{tier} priors sum to {total}"


def test_soft_priors_all_tiers_present():
    for tier in ("foundational", "hardening", "advanced", "expanded"):
        assert tier in SOFT_PRIORS, f"Missing tier: {tier}"


def test_expand_soft_labels_foundational():
    row = {"tier": "Foundational", "source_text": "a", "target_text": "b"}
    expanded = expand_soft_labels(row, upstream_weight=0.4)
    assert len(expanded) == 3
    labels = {r["tier_label"] for r in expanded}
    assert labels == {TierLabel.RELATED, TierLabel.EQUIVALENT, TierLabel.PARTIAL}
    # Check weights sum to upstream_weight
    total_weight = sum(r["sample_weight"] for r in expanded)
    assert abs(total_weight - 0.4) < 1e-9


def test_expand_soft_labels_hardening():
    row = {"tier": "Hardening", "source_text": "a", "target_text": "b"}
    expanded = expand_soft_labels(row, upstream_weight=0.4)
    assert len(expanded) == 3
    weights = {r["tier_label"]: r["sample_weight"] for r in expanded}
    assert abs(weights[TierLabel.RELATED] - 0.4 * 0.70) < 1e-9
    assert abs(weights[TierLabel.PARTIAL] - 0.4 * 0.20) < 1e-9
    assert abs(weights[TierLabel.EQUIVALENT] - 0.4 * 0.10) < 1e-9


def test_expand_soft_labels_preserves_fields():
    row = {"tier": "Advanced", "source_text": "x", "target_text": "y", "pair_key": "pk"}
    expanded = expand_soft_labels(row, upstream_weight=1.0)
    for r in expanded:
        assert r["source_text"] == "x"
        assert r["target_text"] == "y"
        assert r["pair_key"] == "pk"


def test_map_upstream_tier_still_works():
    """Legacy function still returns single label (used by other scripts)."""
    assert map_upstream_tier(tier="Foundational", scope="Both") == TierLabel.EQUIVALENT


def test_expand_soft_labels_default_weight():
    row = {"tier": "Foundational", "source_text": "a", "target_text": "b"}
    expanded = expand_soft_labels(row)
    total_weight = sum(r["sample_weight"] for r in expanded)
    assert abs(total_weight - 0.4) < 1e-9  # default upstream_weight=0.4


def test_foundational_build_scope():
    assert map_upstream_tier(tier="Foundational", scope="Build") == TierLabel.EQUIVALENT


def test_hardening_maps_to_related():
    assert map_upstream_tier(tier="Hardening", scope="Both") == TierLabel.RELATED


def test_advanced_maps_to_partial():
    assert map_upstream_tier(tier="Advanced", scope="Both") == TierLabel.PARTIAL


def test_expanded_maps_to_partial():
    assert map_upstream_tier(tier="Expanded", scope="Both") == TierLabel.PARTIAL


def test_unknown_tier_raises():
    with pytest.raises(ValueError, match="Unknown tier"):
        map_upstream_tier(tier="Invalid", scope="Both")


def test_tier_label_values():
    assert TierLabel.UNRELATED.value == 0
    assert TierLabel.PARTIAL.value == 1
    assert TierLabel.RELATED.value == 2
    assert TierLabel.EQUIVALENT.value == 3
