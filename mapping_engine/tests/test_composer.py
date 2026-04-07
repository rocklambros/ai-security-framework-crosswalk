"""Tests for mapping_engine.engine.composer."""

from __future__ import annotations

import numpy as np

from mapping_engine.engine.composer import (
    TIER_DIRECT,
    TIER_NONE,
    TIER_RELATED,
    assign_tiers,
    compose_scores,
)

CONFIG = {
    "weights": {"bridge": 0.45, "semantic": 0.35, "keyword": 0.20, "boost": 0.50},
    "thresholds": {
        "direct": 0.55,
        "related_primary": 0.35,
        "related_secondary": 0.50,
        "gov_floor": 0.22,
        "tangential": 0.20,
    },
}


def _ones(shape):
    return np.ones(shape, dtype=np.float64)


def _zeros(shape):
    return np.zeros(shape, dtype=np.float64)


def test_perfect_signals_capped_at_one():
    shape = (2, 3)
    composite, tiers = compose_scores(
        _ones(shape), _ones(shape), _ones(shape), _ones(shape), CONFIG
    )
    assert np.allclose(composite, 1.0)
    assert (tiers == TIER_DIRECT).all()


def test_zero_signals_yield_none():
    shape = (2, 3)
    composite, tiers = compose_scores(
        _zeros(shape), _zeros(shape), _zeros(shape), _zeros(shape), CONFIG
    )
    assert np.allclose(composite, 0.0)
    assert (tiers == TIER_NONE).all()


def test_threshold_boundary_direct():
    composite = np.array([[0.55, 0.5499, 0.35, 0.20, 0.19]])
    relevance = np.ones_like(composite, dtype=np.int8)
    tiers = assign_tiers(composite, relevance, CONFIG)
    assert tiers[0, 0] == TIER_DIRECT
    assert tiers[0, 1] == TIER_RELATED  # Primary related
    assert tiers[0, 2] == TIER_RELATED  # exactly at related_primary
    assert tiers[0, 3] == 1  # tangential
    assert tiers[0, 4] == TIER_NONE


def test_gov_floor_promotion():
    # composite below related_primary (0.35) but above gov_floor (0.22)
    composite = np.array([[0.25]])
    relevance = np.ones_like(composite, dtype=np.int8)
    fm = np.array([[1.0]])
    tiers_no_gov = assign_tiers(
        composite, relevance, CONFIG, function_match=fm, function_classes=["PREV"]
    )
    tiers_gov = assign_tiers(
        composite, relevance, CONFIG, function_match=fm, function_classes=["GOVERN"]
    )
    assert tiers_no_gov[0, 0] == 1  # tangential only
    assert tiers_gov[0, 0] == TIER_RELATED  # promoted
