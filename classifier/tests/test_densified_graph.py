"""Tests for ensemble densified graph builder (v7: clean graph)."""
from classifier.ensemble.graph import build_densified_graph


def test_densified_graph_has_expected_edges():
    g = build_densified_graph()
    assert g.number_of_nodes() >= 500
    assert g.number_of_edges() >= 1500
    types = {d["edge_type"] for _, _, d in g.edges(data=True)}
    # Must have at least expert/category edges from processed graph
    assert "CROSS_FRAMEWORK_CATEGORY" in types or "expert" in types


def test_no_llm_edges_in_v7_graph():
    """v7: LLM-derived edges must be completely removed."""
    g = build_densified_graph()
    types = {d["edge_type"] for _, _, d in g.edges(data=True)}
    assert "v1_frozen_highconf" not in types, "LLM edges should not exist in v7 graph"


def test_upstream_expert_edges_present():
    """v7: Graph should contain upstream_expert edges."""
    g = build_densified_graph()
    types = {d["edge_type"] for _, _, d in g.edges(data=True)}
    assert "upstream_expert" in types, "upstream_expert edges missing"
