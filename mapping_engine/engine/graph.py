"""Graph loader for the crosswalk knowledge graph.

Loads nodes.json + edges.json into a NetworkX DiGraph keyed by ``node_id``
(e.g. ``"aiuc_1:B005"``). Every JSON attribute is preserved on the node/edge
so downstream signal modules can read framework, entry_type, function_class,
keywords, confidence, etc. without re-parsing the source files.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

import networkx as nx


def load_graph(nodes_path: str | Path, edges_path: str | Path) -> nx.DiGraph:
    """Load nodes.json + edges.json into a directed ``DiGraph``.

    Each node is added with key ``node_id`` and **all** JSON fields as
    attributes. Each edge is added with all JSON fields as edge attributes.

    Example
    -------
    >>> G = load_graph("data/processed/nodes.json", "data/processed/edges.json")
    >>> G.number_of_nodes(), G.number_of_edges()
    (983, 1883)
    """
    nodes = json.loads(Path(nodes_path).read_text())
    edges = json.loads(Path(edges_path).read_text())

    G: nx.DiGraph = nx.DiGraph()
    for n in nodes:
        nid = n["node_id"]
        G.add_node(nid, **n)
    for e in edges:
        s = e["source_node_id"]
        t = e["target_node_id"]
        G.add_edge(s, t, **e)
    return G


def get_framework_nodes(
    G: nx.DiGraph,
    framework: str,
    entry_types: Iterable[str] | None = None,
) -> list[str]:
    """Return node_ids belonging to ``framework``, optionally filtered by entry_type.

    Example
    -------
    >>> get_framework_nodes(G, "owasp_agentic", entry_types=["risk"])  # doctest: +SKIP
    ['owasp_agentic:ASI01', ..., 'owasp_agentic:ASI10']
    """
    et = set(entry_types) if entry_types is not None else None
    out: list[str] = []
    for nid, data in G.nodes(data=True):
        if data.get("framework") != framework:
            continue
        if et is not None and data.get("entry_type") not in et:
            continue
        out.append(nid)
    return out


def get_node_text(G: nx.DiGraph, node_id: str) -> str:
    """Build a text blob for embedding/keyword matching: name + description + keywords."""
    d = G.nodes[node_id]
    parts: list[str] = []
    for k in ("name", "title", "description"):
        v = d.get(k)
        if v:
            parts.append(str(v))
    kws = d.get("keywords") or []
    if isinstance(kws, list):
        parts.extend(str(k) for k in kws if k)
    return " ".join(parts).strip()


def get_cross_framework_edges(
    G: nx.DiGraph, source_fw: str, target_fw: str
) -> list[dict]:
    """Return edge attribute dicts where source_framework→target_framework matches."""
    out: list[dict] = []
    for _, _, data in G.edges(data=True):
        if data.get("source_framework") == source_fw and data.get("target_framework") == target_fw:
            out.append(data)
    return out


if __name__ == "__main__":
    G = load_graph("data/processed/nodes.json", "data/processed/edges.json")
    print(f"Loaded graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
