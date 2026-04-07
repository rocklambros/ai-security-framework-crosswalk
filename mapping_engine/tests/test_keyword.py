"""Tests for mapping_engine.engine.keyword."""

from __future__ import annotations

from pathlib import Path

import networkx as nx
import numpy as np
import pytest

from mapping_engine.engine.graph import get_framework_nodes, load_graph
from mapping_engine.engine.keyword import compute_keyword_similarity, load_synonyms

REPO = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def G():
    return load_graph(REPO / "data" / "processed" / "nodes.json",
                      REPO / "data" / "processed" / "edges.json")


def test_shape_and_range(G):
    src = sorted(get_framework_nodes(G, "aiuc_1"))
    tgt = sorted(get_framework_nodes(G, "owasp_agentic", entry_types=["risk"]))
    M = compute_keyword_similarity(G, src, tgt)
    assert M.shape == (len(src), len(tgt))
    assert M.min() >= 0.0 and M.max() <= 1.0
    assert np.isfinite(M).all()


def test_load_synonyms_nonempty():
    groups = load_synonyms()
    assert len(groups) >= 20
    assert all(isinstance(g, set) for g in groups)


def test_synonym_expansion_helps_supply_chain():
    """A doc using 'vendor due diligence' should match a 'supply chain' doc
    more strongly with synonym expansion than without."""
    H = nx.DiGraph()
    H.add_node(
        "src:1",
        node_id="src:1",
        framework="src",
        entry_type="control",
        name="Vendor Due Diligence",
        description="Conduct vendor due diligence on third party AI providers.",
    )
    H.add_node(
        "tgt:1",
        node_id="tgt:1",
        framework="tgt",
        entry_type="risk",
        name="Supply Chain Risk",
        description="Risks introduced via the supply chain of model providers.",
    )
    with_exp = compute_keyword_similarity(H, ["src:1"], ["tgt:1"])
    without_exp = compute_keyword_similarity(
        H, ["src:1"], ["tgt:1"], config={"expand_synonyms": False}
    )
    assert with_exp[0, 0] >= without_exp[0, 0]
    assert with_exp[0, 0] > 0.0
