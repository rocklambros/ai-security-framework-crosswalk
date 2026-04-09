"""Emit wide parquet (pair_key x scorer_name) for Plan 5 stacker."""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from classifier.baselines.protocol import ScoreRecord


def build_feature_cache(
    all_records: dict[str, list[ScoreRecord]],
    out_path: Path,
) -> None:
    """Build wide parquet: one row per pair_key, one column per scorer."""
    # Collect all pair_keys and scorer names
    pair_keys: set[str] = set()
    scorer_names: list[str] = sorted(all_records.keys())
    scores_by_pair: dict[str, dict[str, float]] = defaultdict(dict)

    for scorer_name, records in all_records.items():
        for r in records:
            pair_keys.add(r.pair_key)
            scores_by_pair[r.pair_key][scorer_name] = r.score

    sorted_keys = sorted(pair_keys)
    columns = {"pair_key": sorted_keys}
    for sn in scorer_names:
        columns[f"score_{sn}"] = [
            scores_by_pair[pk].get(sn, float("nan")) for pk in sorted_keys
        ]

    tbl = pa.table(columns)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(tbl, out_path, compression="snappy", use_dictionary=False)
