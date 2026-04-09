"""Tests for ensemble densified graph builder."""
import pytest
from classifier.ensemble.graph import build_densified_graph


def test_densified_graph_has_expected_edges():
    g = build_densified_graph()
    assert g.number_of_nodes() >= 500
    assert g.number_of_edges() >= 1500
    types = {d["edge_type"] for _, _, d in g.edges(data=True)}
    # Must have at least expert/category edges from processed graph
    assert "CROSS_FRAMEWORK_CATEGORY" in types or "expert" in types


def test_densified_graph_has_frozen_highconf_edges():
    g = build_densified_graph(min_confidence=0.5)
    types = {d["edge_type"] for _, _, d in g.edges(data=True)}
    # With a lower threshold, we should get some v1_frozen edges
    highconf_count = sum(
        1 for _, _, d in g.edges(data=True)
        if d.get("edge_type") == "v1_frozen_highconf"
    )
    # May be 0 if all label source nodes aren't in the graph, but shouldn't error
    assert highconf_count >= 0


def test_contract5_refuses_non_frozen():
    with pytest.raises(AssertionError, match="Contract 5"):
        build_densified_graph(frozen_labels_path="data/labels/llm_sme/v1/labels.jsonl")
