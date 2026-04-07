"""Smoke test for the S8 cross-pair validation harness.

Runs the harness's _eval_pair on a single small pair end-to-end and
checks the row dict has the expected keys + sane types. Uses the
smallest expanded pair (cosai_rm__owasp_llm has only 18 anchors) to
keep runtime under 30 s.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from mapping_engine.engine.graph import load_graph
from mapping_engine.scripts.cross_pair_validation import _eval_pair, _render_md

REPO = Path(__file__).resolve().parents[2]


@pytest.mark.timeout(120)
def test_cross_pair_validation_smoke():
    G = load_graph(REPO / "data/processed/nodes.json", REPO / "data/processed/edges.json")
    row = _eval_pair(G, "cosai_rm__owasp_llm")
    assert row["pair"] == "cosai_rm__owasp_llm"
    assert isinstance(row["n_mappings"], int) and row["n_mappings"] >= 0
    assert set(row["tier_counts"].keys()) >= {"Direct", "Related", "None"}
    assert isinstance(row["needs_review_count"], int)
    # n_anchors_scored may be 0 due to the cosai_rm source-side anchor-skipping
    # bug noted in S7; the row should still render in the markdown.
    assert isinstance(row["n_anchors_scored"], int)
    md = _render_md([row])
    assert "cosai_rm__owasp_llm" in md
    assert "MRR [95% CI]" in md
