"""Tests for mapping_engine.engine.semantic."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from mapping_engine.engine.graph import get_framework_nodes, load_graph
from mapping_engine.engine.semantic import (
    _load_model,
    compute_semantic_similarity,
)

REPO = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def G():
    return load_graph(REPO / "data" / "processed" / "nodes.json",
                      REPO / "data" / "processed" / "edges.json")


@pytest.fixture(scope="module")
def sources_targets(G):
    src = sorted(get_framework_nodes(G, "aiuc_1"))
    tgt = sorted(get_framework_nodes(G, "owasp_agentic", entry_types=["risk"]))
    return src, tgt


@pytest.fixture(scope="module")
def sim(G, sources_targets):
    src, tgt = sources_targets
    return compute_semantic_similarity(G, src, tgt)


def test_shape(sources_targets, sim):
    src, tgt = sources_targets
    assert sim.shape == (len(src), len(tgt))
    assert sim.shape == (189, 10)


def test_value_range(sim):
    assert sim.min() >= 0.0
    assert sim.max() <= 1.0
    assert np.isfinite(sim).all()


def test_d004_asi02_beats_asi09(G, sources_targets, sim):
    src, tgt = sources_targets
    i = src.index("aiuc_1:D004")
    j02 = tgt.index("owasp_agentic:ASI02")
    j09 = tgt.index("owasp_agentic:ASI09")
    assert sim[i, j02] > sim[i, j09]


def test_model_uses_gpu_when_available():
    import torch

    model = _load_model("BAAI/bge-large-en-v1.5")
    if torch.cuda.is_available():
        assert str(model.device).startswith("cuda")
    else:
        assert str(model.device).startswith("cpu")
