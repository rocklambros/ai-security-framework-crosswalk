"""Test that build_densified_graph produces a clean graph without LLM edges."""
from classifier.ensemble.graph import build_densified_graph


def test_no_llm_edges_in_graph():
    """Graph should NOT contain any v1_frozen_highconf edges."""
    g = build_densified_graph()
    for u, v, data in g.edges(data=True):
        assert data.get("edge_type") != "v1_frozen_highconf", (
            f"LLM-contaminated edge found: {u} -> {v}"
        )


def test_upstream_expert_edges_present():
    """Graph should contain upstream_expert edges from resolved mappings."""
    g = build_densified_graph()
    upstream_edges = [
        (u, v) for u, v, d in g.edges(data=True)
        if d.get("edge_type") == "upstream_expert"
    ]
    # Should have > 0 upstream expert edges (there are 546 resolved mappings,
    # some filtered by partition.json, expect 200+)
    assert len(upstream_edges) > 100, (
        f"Expected >100 upstream expert edges, got {len(upstream_edges)}"
    )


def test_graph_has_expert_edges():
    """Graph should still contain the original expert edges."""
    g = build_densified_graph()
    assert g.number_of_edges() > 3000, (
        f"Expected >3000 edges (4001 base + upstream), got {g.number_of_edges()}"
    )
