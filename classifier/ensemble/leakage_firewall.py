"""Leakage firewall: ensures no data leakage between train/val and test/cal sets.

Provides:
    check_no_leakage()       — raises if any train pair overlaps test/cal
    load_frozen_keys()       — load frozen test pair keys from JSONL
    load_cal_keys()          — load calibration pair keys from JSONL
    extract_nodes_from_keys() — extract node IDs from a set of pair keys
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Set, Tuple


def load_frozen_keys(path: str) -> Set[str]:
    """Load pair_key values from a frozen JSONL file."""
    keys: Set[str] = set()
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Frozen file not found: {path}")
    with p.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if "pair_key" in row:
                keys.add(row["pair_key"])
    return keys


def load_cal_keys(path: str) -> Set[str]:
    """Load pair_key values from a calibration JSONL file."""
    keys: Set[str] = set()
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Cal file not found: {path}")
    with p.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if "pair_key" in row:
                keys.add(row["pair_key"])
    return keys


def extract_nodes_from_keys(pair_keys: Set[str]) -> Set[str]:
    """Extract individual node IDs from pair keys.

    Pair key format: ``{fw_src}__{fw_tgt}::{src_node_id}__{tgt_node_id}``
    """
    nodes: Set[str] = set()
    for key in pair_keys:
        # Split on '::' to get the node-pair portion
        if "::" in key:
            node_part = key.split("::", 1)[1]
            if "__" in node_part:
                src, tgt = node_part.split("__", 1)
                nodes.add(src)
                nodes.add(tgt)
    return nodes


def check_no_leakage(
    *,
    train_pair_keys: Set[str],
    test_pair_keys: Set[str],
    cal_pair_keys: Set[str],
    graph_edge_pairs: Set[Tuple[str, str]],
    negative_sample_nodes: Set[str],
    test_cal_nodes: Set[str],
) -> None:
    """Assert no leakage between training data and test/cal sets.

    Raises:
        AssertionError: if any overlap is detected.
    """
    # 1. No train/val pair key should appear in frozen test or cal
    train_vs_test = train_pair_keys & test_pair_keys
    if train_vs_test:
        raise AssertionError(
            f"LEAKAGE: {len(train_vs_test)} train pair(s) appear in frozen test set: "
            f"{list(train_vs_test)[:5]}"
        )

    train_vs_cal = train_pair_keys & cal_pair_keys
    if train_vs_cal:
        raise AssertionError(
            f"LEAKAGE: {len(train_vs_cal)} train pair(s) appear in cal set: "
            f"{list(train_vs_cal)[:5]}"
        )

    # 2. Negative sample nodes must not overlap with test/cal nodes
    neg_vs_protected = negative_sample_nodes & test_cal_nodes
    if neg_vs_protected:
        raise AssertionError(
            f"LEAKAGE: {len(neg_vs_protected)} negative-sample node(s) appear in "
            f"test/cal node set: {list(neg_vs_protected)[:5]}"
        )
