"""Unify SME labeling sheets into a single DataFrame."""
from __future__ import annotations
from pathlib import Path
import yaml
import pandas as pd
from classifier.config import LABELING_SHEETS_DIR

COLUMNS: tuple[str, ...] = (
    "pair_key",
    "pair_name",
    "framework_pair",
    "source_node_id",
    "target_node_id",
    "source_text",
    "target_text",
    "expert_tier",
)


def _load_sheet(path: Path) -> list[dict]:
    data = yaml.safe_load(path.read_text())
    # Strip suffixes: both __candidates.yaml and __hr_candidates.yaml
    pair_name = path.name.replace("__hr_candidates.yaml", "").replace("__candidates.yaml", "")
    rows = []
    for c in data["candidates"]:
        rows.append({
            "pair_key": f"{pair_name}::{c['source_node_id']}__{c['target_node_id']}",
            "pair_name": pair_name,
            "framework_pair": pair_name,
            "source_node_id": c["source_node_id"],
            "target_node_id": c["target_node_id"],
            "source_text": (c.get("source_description") or c.get("source_name") or "").strip(),
            "target_text": (c.get("target_description") or c.get("target_name") or "").strip(),
            "expert_tier": c.get("expert_tier") or "None",
        })
    return rows


def load_sme_pool() -> pd.DataFrame:
    sheets = sorted(LABELING_SHEETS_DIR.glob("*_candidates.yaml"))
    if not sheets:
        raise FileNotFoundError(f"No labeling sheets in {LABELING_SHEETS_DIR}")
    rows: list[dict] = []
    for p in sheets:
        rows.extend(_load_sheet(p))
    df = pd.DataFrame(rows)
    # Deduplicate on pair_key (HR sheets may overlap with original sheets)
    df = df.drop_duplicates(subset="pair_key", keep="last")
    df = df[list(COLUMNS)]
    print(f"SME pool: {len(df)} rows from {len(sheets)} sheets")
    return df
