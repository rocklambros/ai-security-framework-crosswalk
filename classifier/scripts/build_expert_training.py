"""Build expert-derived training data from upstream mappings.

Usage:
    python -m classifier.scripts.build_expert_training [--output-dir data/splits]
"""
from __future__ import annotations

import json
import random
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

from classifier.data.tier_mapper import TierLabel, map_upstream_tier
from classifier.data.negative_miner import mine_hard_negatives
from classifier.ensemble.leakage_firewall import (
    check_no_leakage,
    extract_nodes_from_keys,
    load_cal_keys,
    load_frozen_keys,
)


def _load_mappings(path: str) -> List[Dict[str, Any]]:
    rows = []
    with Path(path).open() as f:
        for line in f:
            row = json.loads(line)
            if not row.get("target_id_unresolved", False):
                rows.append(row)
    return rows


def _load_control_texts(frameworks_dir: str = "data/frameworks") -> Dict[str, str]:
    """Load control texts from processed node files."""
    texts: Dict[str, str] = {}
    nodes_path = Path("data/processed/nodes.json")
    if nodes_path.exists():
        with nodes_path.open() as f:
            nodes = json.load(f)
        for node in nodes:
            nid = node.get("node_id", "")
            text = node.get("text", "") or node.get("description", "")
            if nid and text:
                texts[nid] = text
    return texts


def build_expert_training_set(
    *,
    mappings_path: str = "data/upstream/mappings_v1.jsonl",
    frozen_path: str = "data/splits/human_test_frozen.jsonl",
    cal_path: str = "data/splits/human_cal.jsonl",
    output_dir: str = "data/splits",
    n_negatives_per_source: int = 5,
    val_fraction: float = 0.15,
    seed: int = 42,
) -> Dict[str, Any]:
    """Build stratified expert training + val sets."""
    random.seed(seed)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # Load exclusion sets
    try:
        frozen_keys = load_frozen_keys(frozen_path)
    except FileNotFoundError:
        frozen_keys = set()
    try:
        cal_keys = load_cal_keys(cal_path)
    except FileNotFoundError:
        cal_keys = set()

    frozen_cal_nodes = extract_nodes_from_keys(frozen_keys | cal_keys)

    # Load and map upstream data
    mappings = _load_mappings(mappings_path)
    positive_pairs: List[Dict] = []
    positive_pair_set: Set[Tuple[str, str]] = set()

    for row in mappings:
        src_fw = row["source_framework"]
        src_id = row["source_id"]
        tgt_node_id = row["target_node_id"]
        source_node_id = f"{src_fw}:{src_id}"

        if source_node_id in frozen_cal_nodes or tgt_node_id in frozen_cal_nodes:
            continue

        pair_key = f"{src_fw}__{row['target_framework']}::{source_node_id}__{tgt_node_id}"

        if pair_key in frozen_keys or pair_key in cal_keys:
            continue

        tier_label = map_upstream_tier(
            tier=row.get("tier", "Expanded"),
            scope=row.get("scope", "Both"),
        )

        positive_pairs.append({
            "pair_key": pair_key,
            "source_node_id": source_node_id,
            "target_node_id": tgt_node_id,
            "source_text": row.get("source_text", ""),
            "target_text": row.get("target_control_name", ""),
            "tier_label": int(tier_label),
            "data_source": "expert_upstream",
        })
        positive_pair_set.add((source_node_id, tgt_node_id))

    # Mine hard negatives
    source_texts = {}
    target_texts = {}
    for p in positive_pairs:
        source_texts[p["source_node_id"]] = p["source_text"]
        target_texts[p["target_node_id"]] = p["target_text"]

    control_texts = _load_control_texts()
    for nid, text in control_texts.items():
        if nid not in target_texts:
            target_texts[nid] = text
        if nid not in source_texts:
            source_texts[nid] = text

    neg_pairs_raw = mine_hard_negatives(
        source_texts=source_texts,
        target_texts=target_texts,
        positive_pairs=positive_pair_set,
        excluded_nodes=frozen_cal_nodes,
        n_negatives_per_source=n_negatives_per_source,
    )

    negative_pairs = []
    for src_id, tgt_id in neg_pairs_raw:
        fw_src = src_id.split(":")[0] if ":" in src_id else "unknown"
        fw_tgt = tgt_id.split(":")[0] if ":" in tgt_id else "unknown"
        pair_key = f"{fw_src}__{fw_tgt}::{src_id}__{tgt_id}"
        negative_pairs.append({
            "pair_key": pair_key,
            "source_node_id": src_id,
            "target_node_id": tgt_id,
            "source_text": source_texts.get(src_id, ""),
            "target_text": target_texts.get(tgt_id, ""),
            "tier_label": int(TierLabel.UNRELATED),
            "data_source": "hard_negative",
        })

    all_pairs = positive_pairs + negative_pairs
    random.shuffle(all_pairs)

    n_val = max(1, int(len(all_pairs) * val_fraction))
    val_set = all_pairs[:n_val]
    train_set = all_pairs[n_val:]

    # Run leakage firewall
    train_keys = {p["pair_key"] for p in train_set}
    val_keys = {p["pair_key"] for p in val_set}
    graph_edges = {(p["source_node_id"], p["target_node_id"]) for p in train_set}
    neg_nodes = set()
    for p in negative_pairs:
        neg_nodes.add(p["source_node_id"])
        neg_nodes.add(p["target_node_id"])

    check_no_leakage(
        train_pair_keys=train_keys | val_keys,
        test_pair_keys=frozen_keys,
        cal_pair_keys=cal_keys,
        graph_edge_pairs=graph_edges,
        negative_sample_nodes=neg_nodes,
        test_cal_nodes=frozen_cal_nodes,
    )

    for name, dataset in [("expert_train.jsonl", train_set), ("expert_val.jsonl", val_set)]:
        with (out / name).open("w") as f:
            for row in dataset:
                json.dump(row, f)
                f.write("\n")

    train_dist = Counter(p["tier_label"] for p in train_set)
    val_dist = Counter(p["tier_label"] for p in val_set)

    return {
        "n_train": len(train_set),
        "n_val": len(val_set),
        "n_positives": len(positive_pairs),
        "n_negatives": len(negative_pairs),
        "train_distribution": dict(train_dist),
        "val_distribution": dict(val_dist),
        "leakage_check": "PASSED",
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Build expert training data")
    parser.add_argument("--output-dir", default="data/splits")
    parser.add_argument("--n-negatives", type=int, default=5)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    stats = build_expert_training_set(
        output_dir=args.output_dir,
        n_negatives_per_source=args.n_negatives,
        seed=args.seed,
    )
    print(json.dumps(stats, indent=2))
