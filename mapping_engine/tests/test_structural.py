"""Tests for mapping_engine.engine.structural (B-1 structural features)."""

from __future__ import annotations

import networkx as nx

from mapping_engine.engine.structural import compute_structural_features


def test_skeleton_returns_empty_dict():
    G = nx.DiGraph()
    G.add_node("a", framework="x")
    G.add_node("b", framework="y")
    out = compute_structural_features(G, ["a"], ["b"])
    assert out == {}


def test_skeleton_accepts_mask_pairs():
    G = nx.DiGraph()
    out = compute_structural_features(G, [], [], mask_pairs={("a", "b")})
    assert out == {}
