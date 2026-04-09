"""Map upstream mapping tiers to 4-class labels for training.

Upstream schema: tier ∈ {Foundational, Expanded}, scope ∈ {Direct, Both, Broader, Partial, ...}
Target schema:   TierLabel ∈ {UNRELATED=0, PARTIAL=1, RELATED=2, EQUIVALENT=3}

Mapping rules (from spec §Data Foundation):
  - Foundational + (Direct|Both|Identical) → EQUIVALENT
  - Foundational + (Broader|Partial|Partial_overlap) → RELATED
  - Expanded → PARTIAL
"""
from __future__ import annotations

import enum


class TierLabel(enum.IntEnum):
    UNRELATED = 0
    PARTIAL = 1
    RELATED = 2
    EQUIVALENT = 3


# Scopes that indicate direct/identical mapping
_EQUIVALENT_SCOPES = frozenset({"Direct", "Both", "Identical", "direct", "both", "identical"})
# Scopes that indicate broader/partial overlap
_RELATED_SCOPES = frozenset({
    "Broader", "Partial", "Partial_overlap", "partial_overlap",
    "broader", "partial",
})


def map_upstream_tier(*, tier: str, scope: str) -> TierLabel:
    """Convert a single upstream (tier, scope) pair to a 4-class TierLabel."""
    tier_lower = tier.strip().lower()
    scope_normalized = scope.strip()

    if tier_lower == "foundational":
        if scope_normalized in _EQUIVALENT_SCOPES:
            return TierLabel.EQUIVALENT
        if scope_normalized in _RELATED_SCOPES:
            return TierLabel.RELATED
        # Default for foundational with unknown scope: RELATED (conservative)
        return TierLabel.RELATED

    if tier_lower == "expanded":
        return TierLabel.PARTIAL

    raise ValueError(f"Unknown tier: '{tier}'. Expected 'Foundational' or 'Expanded'.")


def map_expert_tier(expert_tier: str) -> TierLabel:
    """Convert expert_tier strings from human_test_frozen/human_cal to TierLabel.

    Expert schema: Direct=3, Related=2, Tangential=1, None=0
    """
    mapping = {
        "Direct": TierLabel.EQUIVALENT,
        "Related": TierLabel.RELATED,
        "Tangential": TierLabel.PARTIAL,
        "None": TierLabel.UNRELATED,
    }
    if expert_tier not in mapping:
        raise ValueError(f"Unknown expert_tier: '{expert_tier}'")
    return mapping[expert_tier]
