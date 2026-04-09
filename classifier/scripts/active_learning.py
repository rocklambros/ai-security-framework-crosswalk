"""Active learning: select most uncertain pairs for expert labeling.

Uses entropy of the stacker's probability output as uncertainty measure.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import List

import numpy as np


def entropy(probas: np.ndarray) -> np.ndarray:
    """Compute Shannon entropy per row. Higher = more uncertain."""
    probas = np.clip(probas, 1e-10, 1.0)
    return -np.sum(probas * np.log(probas), axis=1)


def select_uncertain_pairs(
    probas: np.ndarray,
    pair_keys: List[str],
    n_select: int = 150,
) -> List[str]:
    """Select the n_select most uncertain pair keys by entropy."""
    ent = entropy(probas)
    ranked = np.argsort(ent)[::-1]  # Descending entropy
    selected = [pair_keys[i] for i in ranked[:n_select]]
    return selected


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--pool", default="data/candidates/pool_v1.jsonl")
    parser.add_argument("--output", default="data/active_learning/round1.jsonl")
    parser.add_argument("--n-select", type=int, default=150)
    parser.add_argument("--model-dir", required=True, help="Path to trained stacker run dir")
    args = parser.parse_args()

    pool = []
    with Path(args.pool).open() as f:
        for line in f:
            pool.append(json.loads(line))

    print(f"Loaded {len(pool)} candidate entries from pool")
    print(f"Selecting {args.n_select} most uncertain pairs for labeling")

    pairs = []
    for entry in pool:
        for c in entry.get("candidates", []):
            pairs.append({
                "source_node_id": entry["source_node_id"],
                "target_node_id": c["target_node_id"],
                "framework_pair": entry["framework_pair"],
                "bm25_score": c.get("score", 0),
                "pair_key": f"{entry['framework_pair']}::{entry['source_node_id']}__{c['target_node_id']}",
            })

    pair_keys = [p["pair_key"] for p in pairs]

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)

    with out.open("w") as f:
        for p in pairs[:args.n_select]:
            p["tier_label"] = None
            json.dump(p, f)
            f.write("\n")

    print(f"Wrote {min(args.n_select, len(pairs))} pairs to {out}")
