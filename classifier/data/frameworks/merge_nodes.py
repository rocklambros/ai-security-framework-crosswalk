"""Merge per-framework node JSON files into data/processed/nodes.json.

Idempotent: dedup by node_id. Preserves existing nodes for frameworks
not in the per-framework directory (i.e. the original 9 frameworks built
by Sessions 1-8).

Key-shape note: existing nodes.json (983 nodes from Sessions 1-8) uses
``node_id`` as the primary key — no adaptation is required. The dedup key
is always ``n.get("node_id") or n.get("id")`` so the function also handles
hypothetical legacy shapes without mutating records.
"""
from __future__ import annotations
import json
from pathlib import Path


def merge_into_nodes_json(nodes_path: Path, frameworks_dir: Path) -> dict:
    raw = json.loads(Path(nodes_path).read_text())
    base = raw if isinstance(raw, list) else raw.get("nodes", list(raw.values()))
    by_id: dict[str, dict] = {(n.get("node_id") or n.get("id")): n for n in base}
    base_count = len(by_id)

    added = 0
    for p in sorted(Path(frameworks_dir).glob("*.json")):
        for n in json.loads(p.read_text()):
            nid = n.get("node_id") or n.get("id")
            if nid not in by_id:
                by_id[nid] = n
                added += 1

    merged = list(by_id.values())
    Path(nodes_path).write_text(json.dumps(merged, indent=2))
    return {"base": base_count, "added": added, "total": len(merged)}
