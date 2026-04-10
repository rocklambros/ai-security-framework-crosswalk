"""Tests for pair-level leakage exclusion mode."""
import json
import tempfile
from pathlib import Path

import pytest


def test_pair_level_excludes_exact_pairs():
    """Pair-level mode must exclude exact pair_key matches."""
    from classifier.ensemble.leakage_firewall import check_no_leakage

    train_keys = {"fw1__fw2::A__B", "fw1__fw2::A__C", "fw1__fw2::D__E"}
    test_keys = {"fw1__fw2::A__B"}

    with pytest.raises(SystemExit):
        check_no_leakage(
            train_pair_keys=train_keys,
            test_pair_keys=test_keys,
            cal_pair_keys=set(),
            graph_edge_pairs=set(),
            negative_sample_nodes=set(),
            test_cal_nodes=set(),
            mode="pair",
        )


def test_pair_level_allows_shared_nodes():
    """Pair-level mode must allow training pairs that share nodes with test."""
    from classifier.ensemble.leakage_firewall import check_no_leakage

    train_keys = {"fw1__fw2::A__C", "fw1__fw2::D__E"}
    test_keys = {"fw1__fw2::A__B"}
    test_cal_nodes = {"A", "B"}

    check_no_leakage(
        train_pair_keys=train_keys,
        test_pair_keys=test_keys,
        cal_pair_keys=set(),
        graph_edge_pairs={("A", "C"), ("D", "E")},
        negative_sample_nodes={"A", "C", "D", "E"},
        test_cal_nodes=test_cal_nodes,
        mode="pair",
    )


def test_node_level_rejects_shared_nodes():
    """Node-level mode (legacy) must reject training pairs sharing nodes."""
    from classifier.ensemble.leakage_firewall import check_no_leakage

    train_keys = {"fw1__fw2::A__C"}
    test_keys = {"fw1__fw2::A__B"}
    test_cal_nodes = {"A", "B"}

    with pytest.raises(SystemExit):
        check_no_leakage(
            train_pair_keys=train_keys,
            test_pair_keys=test_keys,
            cal_pair_keys=set(),
            graph_edge_pairs={("A", "C")},
            negative_sample_nodes={"A", "C"},
            test_cal_nodes=test_cal_nodes,
            mode="node",
        )


def test_build_expert_training_pair_level_produces_more_data():
    """Pair-level exclusion should produce more training pairs than node-level."""
    from classifier.scripts.build_expert_training import build_expert_training_set
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        stats_node = build_expert_training_set(
            output_dir=tmpdir, leakage_mode="node"
        )
    with tempfile.TemporaryDirectory() as tmpdir:
        stats_pair = build_expert_training_set(
            output_dir=tmpdir, leakage_mode="pair"
        )

    assert stats_pair["n_positives"] > stats_node["n_positives"], (
        f"Pair-level ({stats_pair['n_positives']}) should produce more positives "
        f"than node-level ({stats_node['n_positives']})"
    )
