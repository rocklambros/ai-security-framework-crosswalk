"""End-to-end integration test for the AIUC-1 -> OWASP Agentic pair.

Runs the full ``PairMapper`` pipeline, writes the JSON output (validating
against the v2 schema), and asserts that the per-anchor LOO-masked
ranking quality on the expanded multi-pair anchor set meets a baseline:
aggregate NDCG@10 with bootstrap 95% CI lower bound clearly above the
random / majority baseline (0.50).
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from mapping_engine.calibration.metrics import bootstrap_metric_ci, ndcg_at_k
from mapping_engine.config import load_pair_config
from mapping_engine.engine.graph import load_graph
from mapping_engine.engine.mapper import PairMapper
from mapping_engine.output.json_writer import write_json
from mapping_engine.scripts.learn_weights_b2 import (
    TIER_GRADE,
    _expanded_pair_configs,
)

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


@pytest.mark.integration
def test_b2_aggregate_ndcg_at_10_beats_baseline() -> None:
    """B-2 acceptance bar: aggregate NDCG@10 across all expanded non-frozen
    pairs must beat the 0.50 random/majority baseline with bootstrap 95%
    CI lower bound > 0.50.
    """
    G = load_graph(NODES, EDGES)
    all_grades: list[float] = []
    all_scores: list[float] = []
    pair_names = _expanded_pair_configs()
    assert pair_names, "no expanded non-frozen pair configs found"
    for name in pair_names:
        cfg = load_pair_config(name + "__expanded", validate_anchors_in=G)
        mapper = PairMapper(G, cfg, enable_reranker=None)
        result = mapper.run()
        av = result.anchor_validation
        records: dict = {}
        records.update(av.get("training_anchors", {}))
        records.update(av.get("holdout_anchors", {}))
        expected_lookup = {
            f"{p.source}__{p.target}": p.expected_tier for p in cfg.anchors.pairs
        }
        for key, rec in records.items():
            all_scores.append(float(rec.get("score", 0.0)))
            all_grades.append(TIER_GRADE.get(expected_lookup.get(key, "None"), 0.0))

    g = np.asarray(all_grades, dtype=float)
    s = np.asarray(all_scores, dtype=float)
    ci = bootstrap_metric_ci(
        lambda gg, ss: ndcg_at_k(gg, ss, k=10), g, s, n_resamples=500, rng=42
    )
    assert ci["lo"] > 0.50, (
        f"aggregate NDCG@10 lower bound {ci['lo']:.3f} not above baseline 0.50; "
        f"point={ci['point']:.3f} hi={ci['hi']:.3f} n={len(g)}"
    )
