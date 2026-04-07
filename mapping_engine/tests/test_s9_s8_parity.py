"""Frozen S8 tier_acc parity test against the 150 SME labels.

Replaces the tautological holdout_accuracy=1.00 from the s8-np v2 co-citation
bootstrap. These targets are computed against the SME labeling sheets in
mapping_engine/output/labeling_sheets/ and pinned here so any future scoring
change must be non-inferior.
"""
from __future__ import annotations
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
SHEETS = REPO / "mapping_engine/output/labeling_sheets"

# Frozen targets from session9_s8_frozen_tier_acc.json (S9 unified hardening).
FROZEN = {
    "csa_aicm__owasp_agentic": 0.22,
    "mitre_atlas__owasp_llm": 0.20,
    "nist_rmf__owasp_agentic": 0.30,
}


def _tier_for_score(s: float) -> str:
    if s >= 0.45:
        return "Direct"
    if s >= 0.20:
        return "Related"
    if s >= 0.10:
        return "Tangential"
    return "None"


def _tier_acc(pair: str) -> float:
    d = yaml.safe_load((SHEETS / f"{pair}__candidates.yaml").read_text())
    cs = [c for c in d["candidates"] if c.get("expert_tier")]
    y = [c["expert_tier"] for c in cs]
    p = [_tier_for_score(float(c["composite_score"])) for c in cs]
    return sum(1 for a, b in zip(y, p) if a == b) / len(cs)


def test_s8_frozen_tier_acc_non_inferior():
    for pair, target in FROZEN.items():
        actual = _tier_acc(pair)
        assert actual >= target - 1e-6, (
            f"{pair} regressed: {actual:.4f} < frozen {target:.4f}"
        )
