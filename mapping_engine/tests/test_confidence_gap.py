"""Phase D: confidence gap and needs_review flagging."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mapping_engine.config import load_pair_config
from mapping_engine.engine.graph import load_graph
from mapping_engine.engine.mapper import PairMapper
from mapping_engine.output.json_writer import write_json

REPO = Path(__file__).resolve().parents[2]
NODES = REPO / "data" / "processed" / "nodes.json"
EDGES = REPO / "data" / "processed" / "edges.json"


@pytest.mark.integration
def test_every_mapping_has_confidence_gap_and_needs_review() -> None:
    G = load_graph(NODES, EDGES)
    pair_cfg = load_pair_config("aiuc_1__owasp_agentic", validate_anchors_in=G)
    mapper = PairMapper(G, pair_cfg, enable_reranker=None)
    result = mapper.run()

    assert len(result.mappings) > 0
    for m in result.mappings:
        assert "confidence_gap" in m
        assert isinstance(m["confidence_gap"], float)
        assert "needs_review" in m
        assert isinstance(m["needs_review"], bool)
        # Recompute invariant: needs_review <=> |gap| < 0.05.
        assert m["needs_review"] == (abs(m["confidence_gap"]) < 0.05)


@pytest.mark.integration
def test_needs_review_surfaced_in_json(tmp_path: Path) -> None:
    G = load_graph(NODES, EDGES)
    pair_cfg = load_pair_config("aiuc_1__owasp_agentic", validate_anchors_in=G)
    mapper = PairMapper(G, pair_cfg, enable_reranker=None)
    result = mapper.run()

    out = tmp_path / "out.json"
    doc = write_json(result, G, pair_cfg, out)

    gap = doc["gap_analysis"]
    assert "needs_review_count" in gap
    assert isinstance(gap["needs_review_count"], int)
    assert "needs_review" in gap
    assert isinstance(gap["needs_review"], list)
    assert gap["needs_review_count"] == sum(
        1 for m in result.mappings if m.get("needs_review")
    )
    # Schema validation already runs inside write_json.
    re_read = json.loads(out.read_text())
    assert "needs_review_count" in re_read["gap_analysis"]
