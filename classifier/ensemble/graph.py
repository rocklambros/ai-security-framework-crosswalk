"""Build a clean crosswalk graph for the ensemble.

Sources:
  - data/processed/nodes.json + edges.json (expert + CROSS_FRAMEWORK_CATEGORY)
  - data/upstream/mappings_v1.jsonl (resolved upstream expert mappings)
  - data/upstream/partition.json (train-eligible filter)

v7: LLM-derived edges (v1_frozen_highconf) REMOVED. Replaced with
train-eligible resolved upstream expert mappings for clean GAT training.
"""
from __future__ import annotations

import json
from pathlib import Path

import networkx as nx


def _load_train_eligible_shas(
    partition_path: str = "data/upstream/partition.json",
) -> set[str]:
    """Load provenance_sha values that are train-eligible."""
    path = Path(partition_path)
    if not path.exists():
        return set()
    partition = json.loads(path.read_text())
    return set(partition.get("train_eligible", []))


def build_densified_graph(
    nodes_path: str = "data/processed/nodes.json",
    edges_path: str = "data/processed/edges.json",
    upstream_mappings_path: str = "data/upstream/mappings_v1.jsonl",
    partition_path: str = "data/upstream/partition.json",
) -> nx.DiGraph:
    """Build clean graph from processed graph + resolved upstream expert mappings.

    v7: No LLM-derived edges. Only expert-curated sources.
    """
    g = nx.DiGraph()

    # Load nodes
    nodes_raw = json.loads(Path(nodes_path).read_text())
    for n in nodes_raw:
        g.add_node(
            n["node_id"],
            framework=n.get("framework", ""),
            text=n.get("description") or n.get("name") or "",
        )

    # Load edges from processed graph (expert + category edges)
    edges_raw = json.loads(Path(edges_path).read_text())
    for e in edges_raw:
        src = e.get("source_node_id", "")
        tgt = e.get("target_node_id", "")
        if src in g and tgt in g:
            g.add_edge(
                src, tgt,
                edge_type=e.get("rationale_code") or "expert",
                weight=1.0 if e.get("confidence") == "authoritative" else 0.5,
            )

    n_base = g.number_of_edges()

    # Add train-eligible resolved upstream expert mappings as edges
    train_eligible = _load_train_eligible_shas(partition_path)
    mappings_path = Path(upstream_mappings_path)
    n_upstream = 0
    if mappings_path.exists():
        for line in mappings_path.read_text().splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            # Only add resolved mappings (target_id exists in graph)
            if row.get("target_id_unresolved", False):
                continue
            # Only add train-eligible rows (not in frozen test partition)
            if train_eligible and row.get("provenance_sha") not in train_eligible:
                continue
            src = f"{row['source_framework']}:{row['source_id']}"
            tgt = row.get("target_node_id", "")
            if not tgt:
                tgt = f"{row['target_framework']}:{row['target_control_id']}"
            # Add source node if not present (e.g. frameworks not yet in processed graph)
            if src not in g:
                g.add_node(
                    src,
                    framework=row["source_framework"],
                    text=row.get("notes") or row["source_id"],
                )
            if src in g and tgt in g and not g.has_edge(src, tgt):
                g.add_edge(
                    src, tgt,
                    edge_type="upstream_expert",
                    weight=0.8,
                )
                n_upstream += 1

    print(f"  [graph] {n_base} base edges + {n_upstream} upstream expert edges = {g.number_of_edges()} total")
    return g
