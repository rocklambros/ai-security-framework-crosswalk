"""Stratified 150/400 split of the 550-row SME pool. Seed 42. Deterministic."""
from __future__ import annotations
import pandas as pd
from sklearn.model_selection import train_test_split

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
