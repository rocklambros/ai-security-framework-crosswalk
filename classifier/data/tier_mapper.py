"""Map upstream mapping tiers to 4-class labels for training.

Upstream schema: tier ∈ {Foundational, Hardening, Advanced}, scope ∈ {Both, Build}
Target schema:   TierLabel ∈ {UNRELATED=0, PARTIAL=1, RELATED=2, EQUIVALENT=3}

Mapping rules:
  - Foundational → EQUIVALENT (strong, well-established mappings)
  - Hardening    → RELATED    (moderate, secondary mappings)
  - Advanced     → PARTIAL    (specialized, rare mappings)
  - Hard negatives (unmapped pairs mined during training) → UNRELATED
"""
from __future__ import annotations

import enum


class TierLabel(enum.IntEnum):
    UNRELATED = 0
    PARTIAL = 1
    RELATED = 2
    EQUIVALENT = 3


def map_upstream_tier(*, tier: str, scope: str) -> TierLabel:
    """Convert a single upstream (tier, scope) pair to a 4-class TierLabel."""
    tier_lower = tier.strip().lower()

    if tier_lower == "foundational":
        return TierLabel.EQUIVALENT

    if tier_lower == "hardening":
        return TierLabel.RELATED

    if tier_lower in ("advanced", "expanded"):
        return TierLabel.PARTIAL

    raise ValueError(f"Unknown tier: '{tier}'. Expected 'Foundational', 'Hardening', or 'Advanced'.")


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
