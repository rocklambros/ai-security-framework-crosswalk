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

from classifier.data.tier_mapper import TierLabel, expand_soft_labels
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
            # Synthesize target_node_id for unresolved rows so all rows are usable.
            # Unresolved rows have valid text (target_control_name) — only the graph
            # node_id is missing, which only matters for GAT features (Phase 5).
            if row.get("target_id_unresolved", False) and not row.get("target_node_id"):
                row["target_node_id"] = f"{row['target_framework']}:{row['target_control_id']}"
            rows.append(row)
    return rows


def _load_control_texts(frameworks_dir: str = "data/frameworks") -> Dict[str, str]:
    """Load control texts from processed nodes + source framework files."""
    texts: Dict[str, str] = {}

    # 1. Load from nodes.json (covers owasp_agentic, owasp_llm, and target frameworks)
    nodes_path = Path("data/processed/nodes.json")
    if nodes_path.exists():
        with nodes_path.open() as f:
            nodes = json.load(f)
        for node in nodes:
            nid = node.get("node_id", "")
            text = node.get("description", "") or node.get("text", "")
            if nid and text:
                texts[nid] = text

    # 2. Parse DSGAI control titles from the source text file
    dsgai_path = Path(frameworks_dir) / "owasp-dsgai" / "OWASP-GenAI-Data-Security-Risks-and-Mitigations-2026-v1.0.txt"
    if dsgai_path.exists():
        import re
        content = dsgai_path.read_text()
        seen: Set[str] = set()
        for match in re.finditer(r"(DSGAI\d+)\s*[—–-]\s*(.+?)(?:\n|$)", content):
            ctrl_id = match.group(1)
            if ctrl_id not in seen:
                seen.add(ctrl_id)
                title = match.group(2).strip()
                # Clean page numbers from titles
                title = re.sub(r"\s+\d+$", "", title)
                texts[f"owasp_dsgai:{ctrl_id}"] = title

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
    leakage_mode: str = "pair",
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

    # Load control texts FIRST so we can look up source/target descriptions
    control_texts = _load_control_texts()

    # Load and map upstream data
    mappings = _load_mappings(mappings_path)
    positive_pairs: List[Dict] = []
    positive_pair_set: Set[Tuple[str, str]] = set()

    for row in mappings:
        src_fw = row["source_framework"]
        src_id = row["source_id"]
        tgt_node_id = row["target_node_id"]
        source_node_id = f"{src_fw}:{src_id}"

        if leakage_mode == "node":
            if source_node_id in frozen_cal_nodes or tgt_node_id in frozen_cal_nodes:
                continue

        pair_key = f"{src_fw}__{row['target_framework']}::{source_node_id}__{tgt_node_id}"

        if pair_key in frozen_keys or pair_key in cal_keys:
            continue

        # Look up source text from control_texts dict (nodes.json + DSGAI titles).
        # Fall back to source_id if no description found.
        source_text = control_texts.get(source_node_id, src_id)

        # Target text: use target_control_name, enriched with notes when available
        target_text = row.get("target_control_name", "")
        notes = row.get("notes", "")
        if notes and target_text:
            target_text = f"{target_text} -- {notes}"
        elif notes:
            target_text = notes

        # Soft label expansion: each upstream positive becomes 3 rows
        base_row = {
            "pair_key": pair_key,
            "source_node_id": source_node_id,
            "target_node_id": tgt_node_id,
            "source_text": source_text,
            "target_text": target_text,
            "data_source": "expert_upstream",
            "tier": row.get("tier", "Foundational"),
        }
        expanded = expand_soft_labels(base_row)
        for exp_row in expanded:
            positive_pairs.append(exp_row)

        positive_pair_set.add((source_node_id, tgt_node_id))

    # Build text dicts for negative mining
    source_texts = {}
    target_texts = {}
    for p in positive_pairs:
        source_texts[p["source_node_id"]] = p["source_text"]
        target_texts[p["target_node_id"]] = p["target_text"]

    for nid, text in control_texts.items():
        if nid not in target_texts:
            target_texts[nid] = text
        if nid not in source_texts:
            source_texts[nid] = text

    neg_excluded = frozen_cal_nodes if leakage_mode == "node" else set()
    neg_pairs_raw = mine_hard_negatives(
        source_texts=source_texts,
        target_texts=target_texts,
        positive_pairs=positive_pair_set,
        excluded_nodes=neg_excluded,
        n_negatives_per_source=n_negatives_per_source,
    )

    negative_pairs = []
    for src_id, tgt_id in neg_pairs_raw:
        fw_src = src_id.split(":")[0] if ":" in src_id else "unknown"
        fw_tgt = tgt_id.split(":")[0] if ":" in tgt_id else "unknown"
        pair_key = f"{fw_src}__{fw_tgt}::{src_id}__{tgt_id}"
        # Skip negatives whose pair_key coincides with a frozen or cal pair.
        # The negative miner operates at node level and cannot avoid this; we
        # filter here to guarantee the firewall passes in both "node" and "pair" modes.
        if pair_key in frozen_keys or pair_key in cal_keys:
            continue
        negative_pairs.append({
            "pair_key": pair_key,
            "source_node_id": src_id,
            "target_node_id": tgt_id,
            "source_text": source_texts.get(src_id, ""),
            "target_text": target_texts.get(tgt_id, ""),
            "tier_label": int(TierLabel.UNRELATED),
            "sample_weight": 0.4,
            "data_source": "hard_negative",
        })

    # --- Mapping-level split (prevents text-pair contamination) ---
    mapping_groups: Dict[Tuple[str, str], List[Dict]] = {}
    for p in positive_pairs:
        key = (p["source_node_id"], p["target_node_id"])
        mapping_groups.setdefault(key, []).append(p)

    mapping_keys = list(mapping_groups.keys())
    random.shuffle(mapping_keys)
    n_val_mappings = max(1, int(len(mapping_keys) * val_fraction))

    val_mapping_keys = set(mapping_keys[:n_val_mappings])

    val_positives = []
    train_positives = []
    for mk, rows in mapping_groups.items():
        if mk in val_mapping_keys:
            val_positives.extend(rows)
        else:
            train_positives.extend(rows)

    # Negatives go entirely to train (they're synthetic)
    train_set = train_positives + negative_pairs
    val_set = val_positives
    random.shuffle(train_set)
    random.shuffle(val_set)

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
        mode=leakage_mode,
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
    parser.add_argument("--leakage-mode", choices=["node", "pair"], default="pair")
    args = parser.parse_args()

    stats = build_expert_training_set(
        output_dir=args.output_dir,
        n_negatives_per_source=args.n_negatives,
        seed=args.seed,
        leakage_mode=args.leakage_mode,
    )
    print(json.dumps(stats, indent=2))
