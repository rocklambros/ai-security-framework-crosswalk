"""Build a densified crosswalk graph for the ensemble.

Sources:
  - data/processed/nodes.json + edges.json (expert + CROSS_FRAMEWORK_CATEGORY)
  - data/labels/llm_sme/v1_frozen/llm_train.jsonl (high-confidence Direct labels)

The densified graph is a superset of the mapping engine graph, adding
v1_frozen high-confidence edges as additional signal for the GAT.
"""
from __future__ import annotations

import json
from pathlib import Path

import networkx as nx


def build_densified_graph(
    nodes_path: str = "data/processed/nodes.json",
    edges_path: str = "data/processed/edges.json",
    frozen_labels_path: str = "data/labels/llm_sme/v1_frozen/llm_train.jsonl",
    min_confidence: float = 0.75,
) -> nx.DiGraph:
    """Build densified graph from processed graph + high-confidence frozen labels.

    Contract 5: frozen_labels_path must contain 'v1_frozen'.
    """
    assert "v1_frozen" in str(frozen_labels_path), "Contract 5: training must use v1_frozen labels"

    g = nx.DiGraph()

    # Load nodes
    nodes_raw = json.loads(Path(nodes_path).read_text())
    for n in nodes_raw:
        g.add_node(
            n["node_id"],
            framework=n.get("framework", ""),
            text=n.get("description") or n.get("name") or "",
        )

    # Load edges from processed graph
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

    # Add high-confidence v1_frozen Direct labels as edges
    labels_path = Path(frozen_labels_path)
    if labels_path.exists():
        for line in labels_path.read_text().splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("relation") != "related" and row.get("relation") != "equivalent":
                continue
            conf = row.get("confidence", 0.0)
            if conf < min_confidence:
                continue
            src = f"{row['source_framework']}:{row['source_id']}"
            tgt = row["target_node_id"]
            if src in g and tgt in g and not g.has_edge(src, tgt):
                g.add_edge(
                    src, tgt,
                    edge_type="v1_frozen_highconf",
                    weight=float(conf),
                )

    return g
