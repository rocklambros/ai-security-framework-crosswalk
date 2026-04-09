"""Per-framework-pair scorer coverage diagnostic.

For each of the 26 Tier-B framework pairs, compute:
  - n_rows: number of llm_val rows in the pair
  - scorers[name].null_rate: fraction of rows where the scorer produced NaN/None
  - scorers[name].rank_of_gold_median: median rank of the gold target
  - under_represented: True if n_rows < 5 (Plan 5 stacker should down-weight)
"""
from __future__ import annotations

from collections import defaultdict
from statistics import median


def compute_per_pair_coverage(records: list[dict], framework_pairs: list[tuple[str, str]]) -> dict:
    by_pair: dict[str, list[dict]] = defaultdict(list)
    for r in records:
        by_pair[r["framework_pair"]].append(r)

    out: dict[str, dict] = {}
    for a, b in framework_pairs:
        key = f"{a}__{b}"
        rows = by_pair.get(key, [])
        scorers = defaultdict(list)
        for r in rows:
            scorers[r["scorer_name"]].append(r)
        pair_rows_by_key = defaultdict(set)
        for r in rows:
            pair_rows_by_key[r["scorer_name"]].add(r.get("pair_key") or id(r))
        n_rows = max((len(v) for v in pair_rows_by_key.values()), default=0)
        scorer_out: dict[str, dict] = {}
        for name, lst in scorers.items():
            nulls = sum(1 for r in lst if r.get("score") is None)
            ranks = [r["rank_of_gold"] for r in lst if r.get("rank_of_gold") is not None]
            scorer_out[name] = {
                "null_rate": (nulls / len(lst)) if lst else 0.0,
                "rank_of_gold_median": float(median(ranks)) if ranks else None,
                "n": len(lst),
            }
        out[key] = {
            "n_rows": n_rows,
            "scorers": scorer_out,
            "under_represented": n_rows < 5,
        }
    return out
