"""Tests for mapping_engine.engine.graph."""

from __future__ import annotations

from pathlib import Path

import pytest

from mapping_engine.engine.graph import (
    get_cross_framework_edges,
    get_framework_nodes,
    get_node_text,
    load_graph,
)

REPO = Path(__file__).resolve().parents[2]
NODES = REPO / "data" / "processed" / "nodes.json"
EDGES = REPO / "data" / "processed" / "edges.json"


@pytest.fixture(scope="module")
def G():
    return load_graph(NODES, EDGES)


def test_load_counts(G):
    assert G.number_of_nodes() == 983
    assert G.number_of_edges() == 3393


def test_aiuc_nodes(G):
    assert len(get_framework_nodes(G, "aiuc_1")) == 189


def test_owasp_agentic_risks(G):
    risks = get_framework_nodes(G, "owasp_agentic", entry_types=["risk"])
    assert len(risks) == 10


def test_node_text_nonempty(G):
    txt = get_node_text(G, "aiuc_1:B005")
    assert isinstance(txt, str) and len(txt) > 0


def test_cross_framework_edges(G):
    edges = get_cross_framework_edges(G, "aiuc_1", "owasp_agentic")
    assert len(edges) == 119
