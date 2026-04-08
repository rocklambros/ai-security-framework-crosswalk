"""Retrieval-floor check: does frozen-400 survive top-k retrieval?"""
from __future__ import annotations
import pandas as pd
from classifier.config import SPLITS_DIR
from classifier.data.candidates import FRAMEWORK_PAIRS, build_candidate_pool


def check_floor(k_initial: int = 20, k_max: int = 100) -> dict:
    frozen = pd.read_json(SPLITS_DIR / "human_test_frozen.jsonl", lines=True)
    pool_by_pair = build_candidate_pool(pairs=FRAMEWORK_PAIRS, k=k_max)

    def hit_at(k: int) -> tuple[int, list[dict]]:
        hits, miss_rows = 0, []
        for _, row in frozen.iterrows():
            pair_key = row["framework_pair"]
            rows = pool_by_pair.get(pair_key, [])
            by_src = {r["source_node_id"]: r for r in rows}
            src_row = by_src.get(row["source_node_id"])
            if not src_row:
                miss_rows.append({"pair_key": pair_key, "reason": "source_not_in_pool"})
                continue
            ids = [c["target_node_id"] for c in src_row["candidates"][:k]]
            if row["target_node_id"] in ids:
                hits += 1
            else:
                miss_rows.append({
                    "pair_key": pair_key,
                    "reason": f"target_below_k={k}",
                })
        return hits, miss_rows

    hit_at_20, _ = hit_at(k_initial)
    k_used = k_initial if hit_at_20 == len(frozen) else k_max
    hit_at_k_used, miss_at_k_used = hit_at(k_used)

    return {
        "k_initial": k_initial,
        "k_max": k_max,
        "k_used": k_used,
        "frozen_total": len(frozen),
        "hit_at_20": hit_at_20,
        "hit_at_k_used": hit_at_k_used,
        "coverage_at_20": hit_at_20 / len(frozen),
        "coverage_at_k_used": hit_at_k_used / len(frozen),
        "miss_rows": miss_at_k_used[:100],
    }
