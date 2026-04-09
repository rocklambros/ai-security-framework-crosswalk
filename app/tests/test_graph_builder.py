"""Tests for cytoscape graph element builder."""
import pandas as pd
import pytest
from app.dash_app.components.graph_builder import build_cytoscape_elements


def test_builds_nodes_and_edges():
    df = pd.DataFrame([
        {"source_framework": "owasp_llm", "source_id": "LLM01",
         "target_framework": "mitre_atlas", "target_node_id": "mitre_atlas:AML.T0051",
         "target_control_name": "Prompt Injection", "tier": "Foundational",
         "scope": "Direct", "data_source": "expert"},
    ])
    elements = build_cytoscape_elements(df)

    node_els = [e for e in elements if "source" not in e.get("data", {})]
    edge_els = [e for e in elements if "source" in e.get("data", {})]

    assert len(node_els) >= 2  # At least 2 framework nodes
    assert len(edge_els) >= 1  # At least 1 edge


def test_edge_has_tier_class():
    df = pd.DataFrame([
        {"source_framework": "owasp_llm", "source_id": "LLM01",
         "target_framework": "mitre_atlas", "target_node_id": "mitre_atlas:AML.T0051",
         "target_control_name": "Test", "tier": "Foundational",
         "scope": "Direct", "data_source": "expert"},
    ])
    elements = build_cytoscape_elements(df)
    edges = [e for e in elements if "source" in e.get("data", {})]
    assert len(edges) > 0
    assert "classes" in edges[0]
