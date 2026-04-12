"""Tests for the data loader module."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from components.data_loader import (
    get_nodes_df,
    get_edges_df,
    get_framework_stats,
    get_coverage_matrix,
    get_hierarchy,
    get_transitive_mappings,
    get_graph_metrics,
    get_node_by_id,
)


def test_nodes_df_has_expected_columns():
    df = get_nodes_df()
    assert "node_id" in df.columns
    assert "framework" in df.columns
    assert "name" in df.columns
    assert len(df) == 983


def test_edges_df_has_expected_columns():
    df = get_edges_df()
    assert "source_node_id" in df.columns
    assert "target_node_id" in df.columns
    assert len(df) == 5813


def test_framework_stats_loaded():
    stats = get_framework_stats()
    assert len(stats) == 9
    assert stats["aiuc_1"]["node_count"] == 189


def test_coverage_matrix_loaded():
    matrix = get_coverage_matrix()
    assert "aiuc_1" in matrix
    assert "csa_aicm" in matrix["aiuc_1"]


def test_hierarchy_loaded():
    h = get_hierarchy()
    assert "aiuc_1" in h
    assert "ids" in h["aiuc_1"]


def test_transitive_mappings_loaded():
    t = get_transitive_mappings()
    assert "owasp_agentic:ASI02" in t


def test_get_node_by_id():
    node = get_node_by_id("owasp_agentic:ASI02")
    assert node is not None
    assert node["name"] == "Tool Misuse and Exploitation"


def test_get_node_by_id_missing():
    node = get_node_by_id("nonexistent:X99")
    assert node is None
