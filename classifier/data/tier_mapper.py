"""Map upstream mapping tiers to 4-class labels for training.

Upstream schema: tier in {Foundational, Hardening, Advanced}, scope in {Both, Build}
Target schema:   TierLabel in {UNRELATED=0, PARTIAL=1, RELATED=2, EQUIVALENT=3}

v7 mapping: Upstream tier encodes implementation maturity, NOT functional overlap.
Soft label priors express probabilistic beliefs about the functional overlap
given the maturity tier. Each upstream positive becomes 3 rows with fractional
weights that sum to upstream_weight.
"""
from __future__ import annotations

import enum
from typing import Any, Dict, List


class TierLabel(enum.IntEnum):
    UNRELATED = 0
    PARTIAL = 1
    RELATED = 2
    EQUIVALENT = 3


# Soft label priors: P(functional_overlap_tier | maturity_tier)
# Conservative estimates -- thresholds calibrated on human_cal post-training.
SOFT_PRIORS: Dict[str, Dict[TierLabel, float]] = {
    "foundational": {TierLabel.RELATED: 0.60, TierLabel.EQUIVALENT: 0.30, TierLabel.PARTIAL: 0.10},
    "hardening":    {TierLabel.RELATED: 0.70, TierLabel.PARTIAL: 0.20, TierLabel.EQUIVALENT: 0.10},
    "advanced":     {TierLabel.RELATED: 0.50, TierLabel.PARTIAL: 0.40, TierLabel.EQUIVALENT: 0.10},
    "expanded":     {TierLabel.RELATED: 0.50, TierLabel.PARTIAL: 0.40, TierLabel.EQUIVALENT: 0.10},
}

DEFAULT_UPSTREAM_WEIGHT = 0.4


def expand_soft_labels(
    row: Dict[str, Any],
    upstream_weight: float = DEFAULT_UPSTREAM_WEIGHT,
) -> List[Dict[str, Any]]:
    """Expand a single upstream row into multiple (row, label, weight) dicts.

    Each returned dict is a copy of `row` with `tier_label` and `sample_weight`
    set according to the soft prior for that tier.
    """
    tier_lower = row.get("tier", "").strip().lower()
    priors = SOFT_PRIORS.get(tier_lower)
    if priors is None:
        raise ValueError(f"Unknown tier: '{row.get('tier')}'. Expected one of {list(SOFT_PRIORS)}")

    expanded = []
    for label, prob in priors.items():
        new_row = dict(row)
        new_row["tier_label"] = int(label)
        new_row["sample_weight"] = upstream_weight * prob
        expanded.append(new_row)
    return expanded


def map_upstream_tier(*, tier: str, scope: str) -> TierLabel:
    """Convert a single upstream (tier, scope) pair to a 4-class TierLabel.

    Legacy function kept for backwards compatibility with scripts that need
    a single hard label. New training code should use expand_soft_labels().
    """
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
