"""Stratified split of the SME pool. Seed 42. Deterministic."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

HASHES_PATH = Path("data/splits/hashes.json")
SEED = 42
FROZEN_FRACTION = 0.20  # 20% frozen test


def build_splits(
    df: pd.DataFrame,
    seed: int = SEED,
    frozen_fraction: float = FROZEN_FRACTION,
    *,
    cal_size: int | None = None,
    frozen_size: int | None = None,
) -> dict[str, pd.DataFrame]:
    """Stratify on (framework_pair x expert_tier). Return cal + frozen splits.

    If cal_size/frozen_size are provided explicitly (for tests), use them.
    Otherwise compute from frozen_fraction.
    """
    if frozen_size is not None and cal_size is not None:
        # Explicit sizes (used by unit tests with small synthetic data)
        if len(df) != cal_size + frozen_size:
            raise ValueError(
                f"unexpected pool size {len(df)}, expected {cal_size + frozen_size}"
            )
    else:
        frozen_size = int(len(df) * frozen_fraction)
        cal_size = len(df) - frozen_size

    strata = df["framework_pair"].astype(str) + "::" + df["expert_tier"].astype(str)
    counts = strata.value_counts()
    if (counts < 2).any():
        strata = df["framework_pair"].astype(str)
    cal, frozen = train_test_split(
        df,
        test_size=frozen_size,
        random_state=seed,
        stratify=strata,
        shuffle=True,
    )
    print(f"Split: {len(cal)} cal + {len(frozen)} frozen (total {len(df)})")
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
