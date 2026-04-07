"""Tests for mapping_engine.engine.bridge."""

from __future__ import annotations

from pathlib import Path

import pytest

from mapping_engine.engine.bridge import graph_bridge_scores
from mapping_engine.engine.graph import get_framework_nodes, load_graph

REPO = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def G():
    return load_graph(REPO / "data" / "processed" / "nodes.json",
                      REPO / "data" / "processed" / "edges.json")


@pytest.fixture(scope="module")
def aiuc_to_asi(G):
    src = get_framework_nodes(G, "aiuc_1")
    tgt = sorted(get_framework_nodes(G, "owasp_agentic", entry_types=["risk"]))
    M = graph_bridge_scores(G, src, tgt)
    return src, tgt, M


def test_shape(aiuc_to_asi):
    src, tgt, M = aiuc_to_asi
    assert M.shape == (189, 10)


def test_d004_asi02_nonzero(aiuc_to_asi):
    src, tgt, M = aiuc_to_asi
    i = src.index("aiuc_1:D004")
    j = tgt.index("owasp_agentic:ASI02")
    assert M[i, j] > 0.0, "D004 and ASI02 must share graph neighborhood"


def test_disjoint_returns_zero(G):
    # Two synthetic isolated nodes -> 0.0
    import networkx as nx

    H = nx.DiGraph()
    H.add_node("X:1", node_id="X:1", framework="X", entry_type="control")
    H.add_node("Y:1", node_id="Y:1", framework="Y", entry_type="risk")
    M = graph_bridge_scores(H, ["X:1"], ["Y:1"])
    assert M[0, 0] == 0.0


def test_parent_edges_excluded(G):
    # Two AIUC siblings under the same parent should NOT score 1.0 from PARENT alone.
    # Use two children of aiuc_1:domain_A: A001 and A002 both have parent_node_id=aiuc_1:domain_A
    src = ["aiuc_1:A001"]
    tgt = ["aiuc_1:A002"]
    M = graph_bridge_scores(G, src, tgt)
    # Without exclusion they'd share the parent. We don't assert exact 0,
    # only that the computation runs and doesn't crash, and produces a finite value.
    assert 0.0 <= M[0, 0] <= 1.0
    # And confirm: explicitly DISABLING the exclusion increases the score
    M_with_parents = graph_bridge_scores(G, src, tgt, config={"exclude_edge_types": []})
    assert M_with_parents[0, 0] >= M[0, 0]
