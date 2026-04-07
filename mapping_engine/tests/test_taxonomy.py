"""Tests for mapping_engine.engine.taxonomy."""

from __future__ import annotations

from pathlib import Path

import pytest

from mapping_engine.engine.graph import load_graph
from mapping_engine.engine.taxonomy import (
    classify_function,
    classify_relevance,
    load_function_profiles,
)

REPO = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def G():
    return load_graph(REPO / "data/processed/nodes.json", REPO / "data/processed/edges.json")


def test_profiles_load():
    p = load_function_profiles()
    assert "frameworks" in p
    assert "aiuc_1" in p["frameworks"]
    assert len(p["frameworks"]["aiuc_1"]["control_functions"]) >= 50


def test_aiuc_function_lookup(G):
    # B005 = "implement real-time input filtering" → PREV
    assert classify_function(G, "aiuc_1:B005") == "PREV"
    # E006 = "conduct vendor due diligence" → VALID
    assert classify_function(G, "aiuc_1:E006") == "VALID"


def test_relevance_aiuc_owasp(G):
    # E015 → ASI06 is forced Primary by override
    assert classify_relevance(G, "aiuc_1:E015", "owasp_agentic:ASI06") == "Primary"
    # A006 → ASI06 is forced Secondary by override
    assert classify_relevance(G, "aiuc_1:A006", "owasp_agentic:ASI06") == "Secondary"
