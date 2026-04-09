"""Tier label mapping for upstream expert mappings.

Provides:
    TierLabel     — IntEnum of tier categories
    map_upstream_tier() — map (tier, scope) strings to TierLabel
"""
from __future__ import annotations

from enum import IntEnum


class TierLabel(IntEnum):
    """Ordinal tier labels for classifier training.

    Higher values = stronger / more direct mapping.
    """
    UNRELATED = 0
    EXPANDED = 1
    BROADER = 2
    DIRECT = 3


# Canonicalise common spellings/capitalisations
_TIER_MAP = {
    "foundational": TierLabel.DIRECT,
    "direct": TierLabel.DIRECT,
    "core": TierLabel.DIRECT,
    "broader": TierLabel.BROADER,
    "related": TierLabel.BROADER,
    "expanded": TierLabel.EXPANDED,
    "tangential": TierLabel.EXPANDED,
    "unrelated": TierLabel.UNRELATED,
}

_SCOPE_MAP = {
    "direct": TierLabel.DIRECT,
    "broader": TierLabel.BROADER,
    "both": TierLabel.BROADER,
    "expanded": TierLabel.EXPANDED,
}


def map_upstream_tier(
    tier: str = "Expanded",
    scope: str = "Both",
) -> TierLabel:
    """Map upstream ``tier`` and ``scope`` strings to a :class:`TierLabel`.

    The tier string takes precedence; scope acts as a tiebreaker / override
    when the tier resolves to EXPANDED and scope indicates something stronger.
    """
    tier_label = _TIER_MAP.get(tier.lower().strip(), TierLabel.EXPANDED)
    scope_label = _SCOPE_MAP.get(scope.lower().strip(), TierLabel.EXPANDED)

    # If both signals agree, use tier.
    # If scope is stronger and tier is only EXPANDED, promote to scope.
    if tier_label == TierLabel.EXPANDED and scope_label > TierLabel.EXPANDED:
        return scope_label

    return tier_label
