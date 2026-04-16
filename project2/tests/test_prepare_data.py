"""Tests for the data preparation pipeline."""

import json
import os

import pytest


@pytest.fixture
def data_dir():
    """Provide path to project2/data which has real nodes.json and edges.json."""
    base = os.path.join(os.path.dirname(__file__), "..", "data")
    assert os.path.isfile(os.path.join(base, "nodes.json")), "nodes.json not found"
    assert os.path.isfile(os.path.join(base, "edges.json")), "edges.json not found"
    return base


@pytest.fixture
def derived_dir(data_dir):
    """Run prepare_data and return the derived output directory."""
    from prepare_data import prepare_all

    out = os.path.join(data_dir, "derived")
    prepare_all(data_dir, out)
    return out


def test_framework_stats_has_all_nine(derived_dir):
    with open(os.path.join(derived_dir, "framework_stats.json")) as f:
        stats = json.load(f)
    assert len(stats) == 9
    assert "aiuc_1" in stats
    assert stats["aiuc_1"]["node_count"] == 189


def test_framework_stats_has_expected_keys(derived_dir):
    with open(os.path.join(derived_dir, "framework_stats.json")) as f:
        stats = json.load(f)
    for fw, data in stats.items():
        assert "node_count" in data
        assert "edge_count_out" in data
        assert "edge_count_in" in data
        assert "entry_type_counts" in data
        assert "domain_counts" in data


def test_coverage_matrix_is_symmetric_keys(derived_dir):
    with open(os.path.join(derived_dir, "coverage_matrix.json")) as f:
        matrix = json.load(f)
    # Every source framework should have entries for other frameworks
    assert "aiuc_1" in matrix
    for source_fw in matrix:
        for target_fw in matrix[source_fw]:
            assert source_fw != target_fw, "Self-coverage should not be included"
            assert "total_pct" in matrix[source_fw][target_fw]


def test_hierarchy_produces_sunburst_data(derived_dir):
    with open(os.path.join(derived_dir, "hierarchy.json")) as f:
        hierarchy = json.load(f)
    assert "aiuc_1" in hierarchy
    aiuc = hierarchy["aiuc_1"]
    assert "ids" in aiuc
    assert "labels" in aiuc
    assert "parents" in aiuc
    assert len(aiuc["ids"]) == len(aiuc["labels"]) == len(aiuc["parents"])
    assert len(aiuc["ids"]) > 0


def test_transitive_mappings_for_asi02(derived_dir):
    with open(os.path.join(derived_dir, "transitive_mappings.json")) as f:
        trans = json.load(f)
    assert "owasp_agentic:ASI02" in trans
    asi02 = trans["owasp_agentic:ASI02"]
    assert "direct" in asi02
    assert "transitive" in asi02
    # ASI02 has 35 direct mappings (AIUC-1 + upstream sources)
    assert len(asi02["direct"]) == 35
    # ASI02 should reach CSA AICM transitively
    csa_transitive = [
        t for t in asi02["transitive"] if t["target_framework"] == "csa_aicm"
    ]
    assert len(csa_transitive) > 0
    # Each transitive mapping should have a bridge_node_id
    for t in asi02["transitive"]:
        assert "bridge_node_id" in t
        assert "bridge_node_name" in t
        assert "target_node_id" in t
        assert "target_framework" in t


def test_graph_metrics_has_pair_data(derived_dir):
    with open(os.path.join(derived_dir, "graph_metrics.json")) as f:
        metrics = json.load(f)
    assert "framework_pairs" in metrics
    assert "node_degrees" in metrics
    # Check a known pair
    pair_key = "aiuc_1->csa_aicm"
    assert pair_key in metrics["framework_pairs"]
    pair = metrics["framework_pairs"][pair_key]
    assert "edge_count" in pair
    assert "confidence_counts" in pair
    assert "rationale_counts" in pair


def test_all_derived_files_exist(derived_dir):
    expected = [
        "framework_stats.json",
        "coverage_matrix.json",
        "graph_metrics.json",
        "hierarchy.json",
        "transitive_mappings.json",
    ]
    for fname in expected:
        path = os.path.join(derived_dir, fname)
        assert os.path.isfile(path), f"Missing: {fname}"
