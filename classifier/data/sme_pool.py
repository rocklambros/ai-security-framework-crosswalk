"""Unify the 11 SME labeling sheets (550 rows) into a single DataFrame."""
from __future__ import annotations
from pathlib import Path
import yaml
import pandas as pd
from classifier.config import LABELING_SHEETS_DIR

EXPECTED_TOTAL = 550  # 11 sheets × 50 rows

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
    pair_name = path.name.replace("__candidates.yaml", "")
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
    sheets = sorted(LABELING_SHEETS_DIR.glob("*__candidates.yaml"))
    if not sheets:
        raise FileNotFoundError(f"No labeling sheets in {LABELING_SHEETS_DIR}")
    rows: list[dict] = []
    for p in sheets:
        rows.extend(_load_sheet(p))
    df = pd.DataFrame(rows)
    if len(df) != EXPECTED_TOTAL:
        raise ValueError(
            f"SME pool size {len(df)} != expected {EXPECTED_TOTAL}. "
            f"Per-sheet counts: {df.groupby('pair_name').size().to_dict()}"
        )
    df = df[list(COLUMNS)]
    return df
