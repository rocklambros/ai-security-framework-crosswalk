"""Tests for mapping_engine.engine.function_match."""

from __future__ import annotations

from pathlib import Path

import pytest

from mapping_engine.engine.function_match import (
    THREAT_FUNCTION_PROFILES,
    _detect_mode,
    compute_function_match,
)
from mapping_engine.engine.graph import load_graph

REPO = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def G():
    return load_graph(REPO / "data" / "processed" / "nodes.json",
                      REPO / "data" / "processed" / "edges.json")


def test_b005_asi01_match(G):
    # B005 = PREV; ASI01 profile contains PREV → 1.0
    M = compute_function_match(G, ["aiuc_1:B005"], ["owasp_agentic:ASI01"])
    assert M[0, 0] == 1.0


def test_e016_asi02_no_match(G):
    # E016 = DISCLOSE; ASI02 profile = {SCOPE,VALID,DETECT,GATE,ISOLATE} → 0.0
    assert "DISCLOSE" not in THREAT_FUNCTION_PROFILES["ASI02"]
    M = compute_function_match(G, ["aiuc_1:E016"], ["owasp_agentic:ASI02"])
    assert M[0, 0] == 0.0


def test_mode_autodetect(G):
    # control vs risk
    assert _detect_mode(G, "aiuc_1:B005", "owasp_agentic:ASI01") == "control_to_risk"
    # control vs control
    assert _detect_mode(G, "aiuc_1:B005", "aiuc_1:D004") == "control_to_control"
