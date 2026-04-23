"""Gap analysis penalty feature from OpenCRE graph.

For each (source, target) pair, looks up the minimum gap-analysis penalty
across all CREs that bridge those two framework sections. This is an
orthogonal signal to text embeddings — it encodes expert-curated graph
distance between controls.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

OPENCRE_PAIRS_PATH = Path("data/opencre/opencre_pairs.jsonl")


def _canonical_key(src: str, tgt: str) -> tuple[str, str]:
    return (min(src, tgt), max(src, tgt))


def load_penalty_index(opencre_pairs: list[dict] | None = None) -> dict[tuple[str, str], float]:
    """Build lookup: (src_node_id, tgt_node_id) -> min gap penalty."""
    if opencre_pairs is None:
        if not OPENCRE_PAIRS_PATH.exists():
            return {}
        with open(OPENCRE_PAIRS_PATH) as f:
            opencre_pairs = [json.loads(line) for line in f]

    index: dict[tuple[str, str], float] = {}
    for pair in opencre_pairs:
        key = _canonical_key(pair["source_node_id"], pair["target_node_id"])
        penalty = pair.get("gap_penalty", -1)
        if key not in index or penalty < index[key]:
            index[key] = float(penalty)
    return index


def compute_gap_penalties(
    eval_pairs: list[dict],
    opencre_pairs: list[dict] | None = None,
    sentinel: float = -1.0,
) -> np.ndarray:
    """Compute gap penalty feature for a list of evaluation pairs.

    Returns shape (n_pairs,) array. Pairs not in OpenCRE get `sentinel`.
    """
    index = load_penalty_index(opencre_pairs)
    penalties = np.full(len(eval_pairs), sentinel, dtype=np.float32)
    for i, pair in enumerate(eval_pairs):
        key = _canonical_key(pair["source_node_id"], pair["target_node_id"])
        if key in index:
            penalties[i] = index[key]
    return penalties
