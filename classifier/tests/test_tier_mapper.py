"""Tests for upstream tier → 4-class mapping."""
import pytest
from classifier.data.tier_mapper import map_upstream_tier, TierLabel


def test_foundational_direct_scope():
    assert map_upstream_tier(tier="Foundational", scope="Direct") == TierLabel.EQUIVALENT


def test_foundational_both_scope():
    assert map_upstream_tier(tier="Foundational", scope="Both") == TierLabel.EQUIVALENT


def test_foundational_broader_scope():
    assert map_upstream_tier(tier="Foundational", scope="Broader") == TierLabel.RELATED


def test_foundational_partial_overlap():
    assert map_upstream_tier(tier="Foundational", scope="Partial") == TierLabel.RELATED


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
