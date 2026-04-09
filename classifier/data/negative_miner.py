"""Mine hard negatives for training using BM25 retrieval.

Hard negatives are plausible-looking pairs that experts did NOT map.
More informative than random negatives for training discriminative models.
"""
from __future__ import annotations

from typing import Dict, List, Set, Tuple

from rank_bm25 import BM25Okapi


def mine_hard_negatives(
    *,
    source_texts: Dict[str, str],
    target_texts: Dict[str, str],
    positive_pairs: Set[Tuple[str, str]],
    excluded_nodes: Set[str],
    n_negatives_per_source: int = 5,
    top_k: int = 50,
) -> List[Tuple[str, str]]:
    """Mine hard negatives: BM25-retrieved targets that are NOT positive pairs.

    Args:
        source_texts: {node_id: text} for source controls
        target_texts: {node_id: text} for target controls
        positive_pairs: {(source_id, target_id)} known positive mappings
        excluded_nodes: Node IDs to exclude (test/cal nodes)
        n_negatives_per_source: How many negatives to sample per source
        top_k: BM25 retrieval depth before filtering

    Returns:
        List of (source_id, target_id) hard negative pairs
    """
    if not source_texts or not target_texts:
        return []

    eligible_targets = {
        tid: text for tid, text in target_texts.items() if tid not in excluded_nodes
    }
    if not eligible_targets:
        return []

    target_ids = list(eligible_targets.keys())
    target_corpus = [eligible_targets[tid].lower().split() for tid in target_ids]

    bm25 = BM25Okapi(target_corpus)

    negatives: List[Tuple[str, str]] = []

    for src_id, src_text in source_texts.items():
        if src_id in excluded_nodes:
            continue

        query = src_text.lower().split()
        scores = bm25.get_scores(query)

        ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)

        count = 0
        for idx in ranked_indices[:top_k]:
            if count >= n_negatives_per_source:
                break
            tgt_id = target_ids[idx]
            if (src_id, tgt_id) not in positive_pairs:
                negatives.append((src_id, tgt_id))
                count += 1

    return negatives
