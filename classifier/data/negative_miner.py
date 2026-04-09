"""Hard negative mining for training data construction.

Provides:
    mine_hard_negatives() — return (source_id, target_id) pairs that are
                            plausible negatives based on lexical similarity.
"""
from __future__ import annotations

import random
from typing import Dict, List, Set, Tuple


def _simple_overlap(a: str, b: str) -> float:
    """Token-overlap Jaccard similarity (fast, no deps)."""
    if not a or not b:
        return 0.0
    ta = set(a.lower().split())
    tb = set(b.lower().split())
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def mine_hard_negatives(
    *,
    source_texts: Dict[str, str],
    target_texts: Dict[str, str],
    positive_pairs: Set[Tuple[str, str]],
    excluded_nodes: Set[str],
    n_negatives_per_source: int = 5,
    seed: int = 42,
) -> List[Tuple[str, str]]:
    """Mine hard negatives: target nodes that look similar but are not positives.

    Parameters
    ----------
    source_texts:
        Mapping of source_node_id -> text.
    target_texts:
        Mapping of target_node_id -> text.
    positive_pairs:
        Set of (source_node_id, target_node_id) known-positive pairs to exclude.
    excluded_nodes:
        Node IDs that must not appear in any returned pair (test/cal leakage guard).
    n_negatives_per_source:
        Maximum number of hard negatives to mine per source node.
    seed:
        Random seed for reproducibility.

    Returns
    -------
    List of (source_node_id, target_node_id) negative pairs.
    """
    rng = random.Random(seed)
    negatives: List[Tuple[str, str]] = []

    # Eligible target nodes (not excluded)
    eligible_targets = [
        tid for tid in target_texts if tid not in excluded_nodes
    ]

    for src_id, src_text in source_texts.items():
        if src_id in excluded_nodes:
            continue

        # Score all eligible targets
        scored = []
        for tgt_id in eligible_targets:
            if (src_id, tgt_id) in positive_pairs:
                continue
            sim = _simple_overlap(src_text, target_texts[tgt_id])
            scored.append((sim, tgt_id))

        if not scored:
            continue

        # Sort by similarity descending; pick top-N with a small shuffle for variety
        scored.sort(key=lambda x: x[0], reverse=True)
        top_k = min(n_negatives_per_source * 3, len(scored))
        candidates = [tgt_id for _, tgt_id in scored[:top_k]]
        rng.shuffle(candidates)

        chosen = candidates[:n_negatives_per_source]
        for tgt_id in chosen:
            negatives.append((src_id, tgt_id))

    return negatives
