"""Data loader for the Dash app.

Reads the upstream mappings_v1.jsonl file and returns a cleaned DataFrame
suitable for the Mapping Browser page.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[3]
MAPPINGS_V1_PATH = REPO / "data" / "upstream" / "mappings_v1.jsonl"

# Columns we care about in the Mapping Browser
_KEEP_COLS = [
    "source_framework",
    "source_id",
    "target_framework",
    "target_control_id",
    "target_control_name",
    "tier",
    "scope",
    "target_id_unresolved",
    "notes",
    "url",
    "provenance_sha",
]

# Confidence proxy: tier → numeric score
_TIER_CONFIDENCE: dict[str, float] = {
    "Foundational": 0.90,
    "Hardening": 0.75,
    "Advanced": 0.60,
}

# Source type label.  All rows in mappings_v1 are human-curated expert edges;
# ML-predicted rows would carry a distinct source_type value when produced by
# the mapping engine.  We mark anything with target_id_unresolved=True as
# "needs_review" so the UI can highlight it.
_SOURCE_TYPE_EXPERT = "expert"
_SOURCE_TYPE_ML = "ml_predicted"


@lru_cache(maxsize=1)
def load_all_mappings() -> pd.DataFrame:
    """Load and return the full mappings DataFrame.

    Columns returned:
        source_framework, source_id, target_framework, target_control_id,
        target_control_name, tier, confidence, source_type, notes, url,
        provenance_sha
    """
    rows: list[dict] = []
    with open(MAPPINGS_V1_PATH, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))

    df = pd.DataFrame(rows)

    # Keep only the columns we need (tolerate missing ones gracefully)
    present = [c for c in _KEEP_COLS if c in df.columns]
    df = df[present].copy()

    # Derive confidence from tier
    df["confidence"] = df["tier"].map(_TIER_CONFIDENCE).fillna(0.50)

    # Derive source_type: rows with unresolved target ids are flagged;
    # everything else is expert-curated.
    if "target_id_unresolved" in df.columns:
        df["source_type"] = df["target_id_unresolved"].apply(
            lambda v: _SOURCE_TYPE_ML if v else _SOURCE_TYPE_EXPERT
        )
        df.drop(columns=["target_id_unresolved"], inplace=True)
    else:
        df["source_type"] = _SOURCE_TYPE_EXPERT

    return df
