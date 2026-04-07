"""Tests for mapping_engine.engine.contrastive."""

from __future__ import annotations

import networkx as nx
import numpy as np

from mapping_engine.engine.contrastive import (
    compute_contrastive_penalty,
    detect_domain_conflicts,
)


def _two_node_graph(src_text: str, tgt_text: str) -> nx.DiGraph:
    H = nx.DiGraph()
    H.add_node("src:1", node_id="src:1", framework="src", entry_type="control",
               name="source", description=src_text)
    H.add_node("tgt:1", node_id="tgt:1", framework="tgt", entry_type="risk",
               name="target", description=tgt_text)
    return H


def test_same_domain_zero_penalty():
    H = _two_node_graph(
        "prompt injection adversarial attack jailbreak",
        "prompt injection jailbreak adversarial",
    )
    sem = np.array([[0.85]])
    M = compute_contrastive_penalty(H, ["src:1"], ["tgt:1"], sem)
    assert M[0, 0] < 0.5


def test_cross_domain_high_penalty():
    H = _two_node_graph(
        "supply chain vendor procurement contract liability",
        "prompt injection jailbreak adversarial input",
    )
    sem = np.array([[0.85]])
    M = compute_contrastive_penalty(H, ["src:1"], ["tgt:1"], sem)
    assert M[0, 0] > 0.5


def test_below_threshold_no_penalty():
    H = _two_node_graph("foo bar", "baz qux")
    sem = np.array([[0.30]])
    M = compute_contrastive_penalty(H, ["src:1"], ["tgt:1"], sem)
    assert M[0, 0] == 0.0


def test_value_range():
    H = _two_node_graph("alpha beta gamma", "delta epsilon zeta")
    sem = np.array([[0.95]])
    M = compute_contrastive_penalty(H, ["src:1"], ["tgt:1"], sem)
    assert 0.0 <= M.min() and M.max() <= 1.0


def test_detect_domain_conflicts_range():
    H = _two_node_graph("alpha beta", "gamma delta")
    s = detect_domain_conflicts(H, "src:1", "tgt:1")
    assert 0.0 <= s <= 1.0
