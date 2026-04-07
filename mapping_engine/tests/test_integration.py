"""End-to-end integration test for the AIUC-1 -> OWASP Agentic pair.

This is the acceptance bar for Session 7. It runs the full ``PairMapper``
pipeline, writes the JSON output (validating against the v2 schema), and
asserts that anchor holdout accuracy is 1.0.
"""

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
def test_aiuc_owasp_agentic_end_to_end(tmp_path: Path) -> None:
    G = load_graph(NODES, EDGES)
    pair_cfg = load_pair_config("aiuc_1__owasp_agentic", validate_anchors_in=G)

    mapper = PairMapper(G, pair_cfg, enable_reranker=None)
    result = mapper.run()

    assert len(result.mappings) > 0, "expected non-empty mappings list"
    assert result.composite_scores.shape == (
        len(result.source_nodes), len(result.target_nodes),
    )

    out = tmp_path / "aiuc_1__owasp_agentic.json"
    doc = write_json(result, G, pair_cfg, out)
    assert out.exists()
    re_read = json.loads(out.read_text())
    assert re_read["metadata"]["schema_version"] == "2.0"
    assert "control_level" in re_read
    assert len(re_read["control_level"]["target_to_source"]) == 10

    assert result.anchor_validation["masked"] is True
    holdout_acc = result.anchor_validation["holdout_accuracy"]
    assert holdout_acc >= 0.66, (
        f"anchor holdout accuracy {holdout_acc} < 0.66; "
        f"holdout={result.anchor_validation['holdout_anchors']}"
    )
