#!/usr/bin/env python3
"""Verify no AIUC-1 subcontrol cross-framework edges remain in the graph."""
import json
from pathlib import Path


def main():
    nodes = {n["node_id"]: n for n in json.loads(Path("data/processed/nodes.json").read_text())}
    edges = json.loads(Path("data/processed/edges.json").read_text())

    subctrl_ids = {
        nid for nid, n in nodes.items()
        if n.get("framework") == "aiuc_1" and n.get("entry_type") == "activity"
    }
    print(f"AIUC-1 subcontrol nodes: {len(subctrl_ids)}")

    violations = []
    for e in edges:
        if e.get("rationale_code") == "PARENT":
            continue
        src, tgt = e["source_node_id"], e["target_node_id"]
        src_fw = src.split(":")[0] if ":" in src else ""
        tgt_fw = tgt.split(":")[0] if ":" in tgt else ""
        if src_fw != tgt_fw and (src in subctrl_ids or tgt in subctrl_ids):
            violations.append(e)

    if violations:
        print(f"FAIL: {len(violations)} subcontrol cross-fw edges remain!")
        for v in violations[:5]:
            print(f"  {v['source_node_id']} -> {v['target_node_id']} ({v.get('rationale_code')})")
        raise SystemExit(1)

    # Check human review edges exist
    human_edges = [e for e in edges if e.get("provenance") == "AIUC-1-Crosswalks-for-Rock.txt"]
    print(f"Human-review expert edges: {len(human_edges)}")
    assert len(human_edges) > 500, f"Expected 500+ human review edges, got {len(human_edges)}"

    # Check subcontrol PARENT edges still exist
    parent_edges = [
        e for e in edges
        if e.get("rationale_code") == "PARENT"
        and (e["source_node_id"] in subctrl_ids or e["target_node_id"] in subctrl_ids)
    ]
    print(f"Subcontrol PARENT edges (hierarchy): {len(parent_edges)}")
    assert len(parent_edges) > 100, f"Expected 100+ parent edges, got {len(parent_edges)}"

    # Check eu_gpai_cop edges are untouched
    eu_edges = [e for e in edges if "eu_gpai_cop" in e.get("source_node_id", "") or "eu_gpai_cop" in e.get("target_node_id", "")]
    print(f"EU GPAI CoP edges (should be ~340): {len(eu_edges)}")

    print("PASS: All checks passed.")


if __name__ == "__main__":
    main()
