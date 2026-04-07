"""Tests for mapping_engine.engine.structural (B-1 structural features)."""

from __future__ import annotations

import networkx as nx
import pytest

from mapping_engine.engine.structural import (
    compute_structural_features,
    shared_parent_centrality,
)


def test_compute_returns_shared_parent_centrality_key():
    G = nx.DiGraph()
    G.add_node("a", framework="x")
    G.add_node("b", framework="y")
    out = compute_structural_features(G, ["a"], ["b"])
    assert "shared_parent_centrality" in out
    assert out["shared_parent_centrality"].shape == (1, 1)


def test_shared_parent_centrality_counts_common_neighbors():
    G = nx.DiGraph()
    G.add_node("s")
    G.add_node("t")
    G.add_node("p")  # common parent
    G.add_edge("s", "p", confidence="expert")
    G.add_edge("t", "p", confidence="expert")
    M = shared_parent_centrality(G, ["s"], ["t"])
    # 0.90 * 0.90 = 0.81
    assert M[0, 0] == pytest.approx(0.81)


def test_shared_parent_centrality_mask_excludes_edge():
    G = nx.DiGraph()
    G.add_edge("s", "p", confidence="expert")
    G.add_edge("t", "p", confidence="expert")
    G.add_edge("s", "q", confidence="expert")
    G.add_edge("t", "q", confidence="expert")
    full = shared_parent_centrality(G, ["s"], ["t"])
    masked = shared_parent_centrality(G, ["s"], ["t"], mask_pairs={("s", "q")})
    # Without mask: 2 common neighbors (p, q), each contributing 0.81 -> 1.62
    assert full[0, 0] == pytest.approx(1.62)
    # Masking the (s, q) edge drops q from s's neighbor set entirely.
    assert masked[0, 0] == pytest.approx(0.81)
    assert masked[0, 0] < full[0, 0]


def test_compute_accepts_mask_pairs():
    G = nx.DiGraph()
    out = compute_structural_features(G, [], [], mask_pairs={("a", "b")})
    assert out["shared_parent_centrality"].shape == (0, 0)
