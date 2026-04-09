"""Stratified 150/400 split of the 550-row SME pool. Seed 42. Deterministic."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

HASHES_PATH = Path("data/splits/hashes.json")
SEED = 42
CAL_SIZE = 150
FROZEN_SIZE = 400  # 550 - 150


def build_splits(
    df: pd.DataFrame,
    seed: int = SEED,
    cal_size: int = CAL_SIZE,
    frozen_size: int = FROZEN_SIZE,
) -> dict[str, pd.DataFrame]:
    """Stratify on (framework_pair × expert_tier). Return cal + frozen splits."""
    if len(df) != cal_size + frozen_size:
        raise ValueError(
            f"unexpected pool size {len(df)}, expected {cal_size + frozen_size}"
        )
    strata = df["framework_pair"].astype(str) + "::" + df["expert_tier"].astype(str)
    counts = strata.value_counts()
    if (counts < 2).any():
        strata = df["framework_pair"].astype(str)
    cal, frozen = train_test_split(
        df,
        train_size=cal_size,
        random_state=seed,
        stratify=strata,
        shuffle=True,
    )
    return {
        "human_cal": cal.sort_values("pair_key").reset_index(drop=True),
        "human_test_frozen": frozen.sort_values("pair_key").reset_index(drop=True),
    }


class HashMismatchError(Exception):
    pass


def verify_hashes(hashes_path: Path = HASHES_PATH) -> None:
    """Verify that key data files match their recorded SHA-256 hashes.

    Raises HashMismatchError if any file has been tampered with or is missing.
    """
    if not hashes_path.exists():
        raise HashMismatchError(f"Hashes file not found: {hashes_path}")
    recorded = json.loads(hashes_path.read_text())
    # Check the split files themselves
    for filename in ("human_cal.jsonl", "human_test_frozen.jsonl", "sme_pool_full.jsonl"):
        expected = recorded.get(filename)
        if not expected:
            continue
        fpath = hashes_path.parent / filename
        if not fpath.exists():
            raise HashMismatchError(f"Split file missing: {fpath}")
        actual = hashlib.sha256(fpath.read_bytes()).hexdigest()
        if actual != expected:
            raise HashMismatchError(
                f"Hash mismatch for {fpath}: expected {expected[:16]}..., got {actual[:16]}..."
            )
