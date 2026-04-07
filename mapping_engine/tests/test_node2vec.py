"""Tests for mapping_engine.engine.node2vec_signal."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from mapping_engine.engine.node2vec_signal import compute_node2vec_similarity

REPO = Path(__file__).resolve().parents[2]
EMB = REPO / "data" / "processed" / "node2vec_embeddings.npy"

pytestmark = pytest.mark.skipif(
    not EMB.exists(), reason="Node2Vec embeddings not trained yet"
)


def test_shape():
    src = ["aiuc_1:B005", "aiuc_1:D004"]
    tgt = ["owasp_agentic:ASI01", "owasp_agentic:ASI02", "owasp_agentic:ASI03"]
    M = compute_node2vec_similarity(src, tgt)
    assert M.shape == (2, 3)


def test_value_range():
    src = ["aiuc_1:B005", "aiuc_1:D004", "aiuc_1:E006"]
    tgt = ["owasp_agentic:ASI01", "owasp_agentic:ASI02"]
    M = compute_node2vec_similarity(src, tgt)
    assert M.min() >= -1.0 - 1e-9 and M.max() <= 1.0 + 1e-9
    assert np.isfinite(M).all()


def test_missing_nodes_zero():
    M = compute_node2vec_similarity(
        ["aiuc_1:B005", "totally:fake_node"],
        ["owasp_agentic:ASI01", "another:fake"],
    )
    assert M.shape == (2, 2)
    assert M[1, 0] == 0.0
    assert M[1, 1] == 0.0
    assert M[0, 1] == 0.0
    # the real-real pair should be a non-trivial cosine
    assert abs(M[0, 0]) > 0.0
