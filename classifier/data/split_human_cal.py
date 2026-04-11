"""Stratified split of human_cal.jsonl into train/val for CE fine-tuning."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from sklearn.model_selection import train_test_split

from classifier.data.tier_mapper import map_expert_tier

HUMAN_CAL_PATH = Path("data/splits/human_cal.jsonl")

TIER_MAP = {"Direct": 3, "Related": 2, "Tangential": 1, "None": 0}


def split_human_cal(
    path: Path = HUMAN_CAL_PATH,
    train_ratio: float = 0.667,
    seed: int = 42,
) -> tuple[list[dict], list[dict], list[int], list[int]]:
    """Split human_cal into train (~100) and val (~50), stratified by expert_tier.

    Each returned record has 'tier_label' (int) added.
    Returns (train_records, val_records, idx_train, idx_val).
    """
    rows = []
    with path.open() as f:
        for line in f:
            row = json.loads(line)
            row["tier_label"] = TIER_MAP[row["expert_tier"]]
            rows.append(row)

    labels = [r["tier_label"] for r in rows]
    idx_train, idx_val = train_test_split(
        list(range(len(rows))),
        train_size=train_ratio,
        stratify=labels,
        random_state=seed,
    )
    train = [rows[i] for i in idx_train]
    val = [rows[i] for i in idx_val]

    # Verify stratification
    for name, subset in [("train", train), ("val", val)]:
        dist = np.bincount([r["tier_label"] for r in subset], minlength=4)
        print(f"  human_cal_{name}: {len(subset)} pairs, dist={dist.tolist()}")

    return train, val, sorted(idx_train), sorted(idx_val)
