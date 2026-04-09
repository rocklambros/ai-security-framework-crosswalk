"""Pre-flight leakage assertions. Hard fail if any data leaks between splits.

Run before every training job. Log results to WANDB if available.
"""
from __future__ import annotations

import sys
from typing import Set, Tuple


def check_no_leakage(
    *,
    train_pair_keys: Set[str],
    test_pair_keys: Set[str],
    cal_pair_keys: Set[str],
    graph_edge_pairs: Set[Tuple[str, str]],
    negative_sample_nodes: Set[str],
    test_cal_nodes: Set[str],
) -> None:
    """Assert zero data leakage across all split boundaries.

    Raises SystemExit on any violation — training MUST NOT proceed.
    """
    # 1. Train ∩ Test = ∅
    overlap = train_pair_keys & test_pair_keys
    if overlap:
        sys.exit(
            f"LEAKAGE DETECTED: {len(overlap)} pairs leaked between train and test. "
            f"First 3: {list(overlap)[:3]}"
        )

    # 2. Train ∩ Cal = ∅
    overlap = train_pair_keys & cal_pair_keys
    if overlap:
        sys.exit(
            f"LEAKAGE DETECTED: {len(overlap)} pairs leaked between train and cal. "
            f"First 3: {list(overlap)[:3]}"
        )

    # 3. Graph edges must not contain test/cal pair nodes
    graph_nodes = set()
    for src, tgt in graph_edge_pairs:
        graph_nodes.add(src)
        graph_nodes.add(tgt)
    graph_test_overlap = graph_nodes & test_cal_nodes
    if graph_test_overlap:
        sys.exit(
            f"LEAKAGE DETECTED: {len(graph_test_overlap)} nodes leaked between "
            f"graph edges and test/cal. First 3: {list(graph_test_overlap)[:3]}"
        )

    # 4. Negative sample nodes ∩ Test/Cal nodes = ∅
    neg_overlap = negative_sample_nodes & test_cal_nodes
    if neg_overlap:
        sys.exit(
            f"LEAKAGE DETECTED: {len(neg_overlap)} nodes leaked between "
            f"negative samples and test_cal. First 3: {list(neg_overlap)[:3]}"
        )


def load_frozen_keys(path: str = "data/splits/human_test_frozen.jsonl") -> Set[str]:
    """Load pair_key values from the frozen test set."""
    import json
    from pathlib import Path

    keys = set()
    with Path(path).open() as f:
        for line in f:
            row = json.loads(line)
            keys.add(row["pair_key"])
    return keys


def load_cal_keys(path: str = "data/splits/human_cal.jsonl") -> Set[str]:
    """Load pair_key values from the calibration set."""
    import json
    from pathlib import Path

    keys = set()
    with Path(path).open() as f:
        for line in f:
            row = json.loads(line)
            keys.add(row["pair_key"])
    return keys


def extract_nodes_from_keys(pair_keys: Set[str]) -> Set[str]:
    """Extract all node IDs from pair keys like 'fp::node1__node2'."""
    nodes = set()
    for pk in pair_keys:
        parts = pk.split("::")
        if len(parts) >= 2:
            node_part = parts[-1]
            for node in node_part.split("__"):
                nodes.add(node)
    return nodes
