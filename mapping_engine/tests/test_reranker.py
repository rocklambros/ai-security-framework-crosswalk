"""Tests for mapping_engine.engine.reranker."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from mapping_engine.engine.graph import get_framework_nodes, load_graph
from mapping_engine.engine.reranker import rerank_candidates

REPO = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def G():
    return load_graph(REPO / "data/processed/nodes.json", REPO / "data/processed/edges.json")


@pytest.fixture(scope="module")
def slice_(G):
    src = sorted(get_framework_nodes(G, "aiuc_1", entry_types=["control"]))[:6]
    tgt = sorted(get_framework_nodes(G, "owasp_agentic", entry_types=["risk"]))
    rng = np.random.default_rng(0)
    composite = rng.uniform(0.0, 1.0, size=(len(src), len(tgt)))
    return src, tgt, composite


def test_shape_preserved(G, slice_):
    src, tgt, composite = slice_
    out = rerank_candidates(G, src, tgt, composite, {"reranker": {"top_k": 5}})
    assert out.shape == composite.shape
    assert out.min() >= 0.0 and out.max() <= 1.0
    assert np.isfinite(out).all()


def test_topk_changes_outside_unchanged(G, slice_):
    src, tgt, composite = slice_
    top_k = 3
    out = rerank_candidates(G, src, tgt, composite, {"reranker": {"top_k": top_k, "blend_weight": 0.30}})
    for i in range(len(src)):
        order = np.argsort(-composite[i])
        top_idx = set(order[:top_k].tolist())
        outside = [j for j in range(len(tgt)) if j not in top_idx]
        for j in outside:
            assert out[i, j] == pytest.approx(composite[i, j])
        # at least one top-k score should differ from the original
        assert any(not np.isclose(out[i, j], composite[i, j]) for j in top_idx)
