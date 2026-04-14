#!/usr/bin/env python3
"""Generate labeling sheet YAMLs from human-reviewed crosswalk data.

Creates aiuc_1__<fw>__hr_candidates.yaml files in mapping_engine/output/labeling_sheets/
for pairs from AIUC-1-Crosswalks-for-Rock.txt. These supplement the existing
50-row sheets with expert-reviewed data.
"""
from __future__ import annotations

import json
import os
import sys
from collections import defaultdict
from pathlib import Path

import yaml

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _PROJECT_ROOT)

from scripts.parse_human_crosswalk import parse_human_crosswalk

SHEETS_DIR = Path(_PROJECT_ROOT) / "mapping_engine" / "output" / "labeling_sheets"
NODES_PATH = Path(_PROJECT_ROOT) / "data" / "processed" / "nodes.json"


def main():
    edges = parse_human_crosswalk()
    nodes = {n["node_id"]: n for n in json.loads(NODES_PATH.read_text())}

    # Group by framework pair, deduplicate
    by_pair: dict[str, list] = defaultdict(list)
    seen_pairs: set[tuple] = set()
    for e in edges:
        pair_key = (e["source_node_id"], e["target_node_id"])
        if pair_key in seen_pairs:
            continue
        seen_pairs.add(pair_key)

        fw_pair = f"aiuc_1__{e['target_fw']}"
        src_node = nodes.get(e["source_node_id"], {})
        tgt_node = nodes.get(e["target_node_id"], {})

        by_pair[fw_pair].append({
            "source_node_id": e["source_node_id"],
            "target_node_id": e["target_node_id"],
            "source_name": src_node.get("name", e["source_node_id"]),
            "source_description": src_node.get("description", ""),
            "target_name": tgt_node.get("name", e["target_node_id"]),
            "target_description": e["target_description"] or tgt_node.get("description", ""),
            "expert_tier": "None",  # tier assigned by LLM scoring, not pre-labeled
        })

    total = 0
    for fw_pair, candidates in sorted(by_pair.items()):
        out_path = SHEETS_DIR / f"{fw_pair}__hr_candidates.yaml"
        data = {"candidates": candidates}
        out_path.write_text(yaml.dump(data, default_flow_style=False, allow_unicode=True))
        print(f"  {out_path.name}: {len(candidates)} candidates")
        total += len(candidates)

    print(f"\nTotal: {total} unique candidates across {len(by_pair)} framework pairs")


if __name__ == "__main__":
    main()
