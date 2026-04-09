"""Tests for leakage firewall assertions."""
import pytest
from classifier.ensemble.leakage_firewall import check_no_leakage


def test_clean_split_passes():
    train_keys = {"a::x__y", "b::x__y", "c::x__y"}
    test_keys = {"d::x__y", "e::x__y"}
    cal_keys = {"f::x__y"}
    graph_edges = {("a", "x"), ("b", "y")}
    neg_nodes = {"a", "b", "c"}
    test_cal_nodes = {"d", "e", "f"}
    check_no_leakage(
        train_pair_keys=train_keys,
        test_pair_keys=test_keys,
        cal_pair_keys=cal_keys,
        graph_edge_pairs=graph_edges,
        negative_sample_nodes=neg_nodes,
        test_cal_nodes=test_cal_nodes,
    )


def test_train_test_overlap_raises():
    train_keys = {"a::x__y", "LEAKED::x__y"}
    test_keys = {"LEAKED::x__y", "e::x__y"}
    with pytest.raises(SystemExit, match="LEAKAGE.*train.*test"):
        check_no_leakage(
            train_pair_keys=train_keys,
            test_pair_keys=test_keys,
            cal_pair_keys=set(),
            graph_edge_pairs=set(),
            negative_sample_nodes=set(),
            test_cal_nodes=set(),
        )


def test_train_cal_overlap_raises():
    train_keys = {"a::x__y", "LEAKED::x__y"}
    cal_keys = {"LEAKED::x__y"}
    with pytest.raises(SystemExit, match="LEAKAGE.*train.*cal"):
        check_no_leakage(
            train_pair_keys=train_keys,
            test_pair_keys=set(),
            cal_pair_keys=cal_keys,
            graph_edge_pairs=set(),
            negative_sample_nodes=set(),
            test_cal_nodes=set(),
        )


def test_graph_test_overlap_raises():
    graph_edges = {("d", "e")}
    test_keys = {"d::x__y"}
    with pytest.raises(SystemExit, match="LEAKAGE.*graph.*test"):
        check_no_leakage(
            train_pair_keys=set(),
            test_pair_keys=test_keys,
            cal_pair_keys=set(),
            graph_edge_pairs=graph_edges,
            negative_sample_nodes=set(),
            test_cal_nodes={"d", "e"},
        )


def test_negative_node_overlap_raises():
    neg_nodes = {"d"}
    with pytest.raises(SystemExit, match="LEAKAGE.*negative.*test_cal"):
        check_no_leakage(
            train_pair_keys=set(),
            test_pair_keys=set(),
            cal_pair_keys=set(),
            graph_edge_pairs=set(),
            negative_sample_nodes=neg_nodes,
            test_cal_nodes={"d"},
        )
