"""Load and convert human_cal.jsonl for conformal calibration.

Maps expert_tier → numeric labels consistent with the ensemble's TIER_MAP:
  Direct → 3 (equivalent), Related → 2 (related),
  Tangential → 1 (partial), None → 0 (unrelated)

Contract 1: verify_hashes() at entry.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from classifier.data.splits import verify_hashes

EXPERT_TIER_MAP = {
    "Direct": 3,       # equivalent
    "Related": 2,      # related
    "Tangential": 1,   # partial
    "None": 0,          # unrelated
}

HUMAN_CAL_PATH = Path("data/splits/human_cal.jsonl")


def load_human_cal(
    path: Path = HUMAN_CAL_PATH,
    verify: bool = True,
) -> list[dict]:
    """Load human_cal.jsonl, adding numeric 'label' field."""
    if verify:
        verify_hashes()
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    for r in rows:
        tier = r.get("expert_tier", "None")
        r["label"] = EXPERT_TIER_MAP.get(tier, 0)
    return rows


def load_human_cal_labels(path: Path = HUMAN_CAL_PATH, verify: bool = True) -> np.ndarray:
    """Return (n,) array of numeric labels from human_cal."""
    rows = load_human_cal(path, verify=verify)
    return np.array([r["label"] for r in rows], dtype=np.int32)
