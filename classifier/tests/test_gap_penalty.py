"""Tests for gap analysis penalty feature extraction."""
import numpy as np
import pytest
from classifier.features.gap_penalty import compute_gap_penalties


def test_compute_gap_penalties_known_pair():
    """Pairs with OpenCRE data should get their penalty value."""
    opencre_pairs = [
        {"source_node_id": "asvs:V1.1", "target_node_id": "cwe:287", "gap_penalty": 0},
        {"source_node_id": "asvs:V1.2", "target_node_id": "cwe:79", "gap_penalty": 2},
    ]
    eval_pairs = [
        {"source_node_id": "asvs:V1.1", "target_node_id": "cwe:287"},
        {"source_node_id": "asvs:V1.2", "target_node_id": "cwe:79"},
        {"source_node_id": "mitre_atlas:T001", "target_node_id": "nist_rmf:GOV-1"},
    ]
    penalties = compute_gap_penalties(eval_pairs, opencre_pairs)
    assert penalties.shape == (3,)
    assert penalties[0] == 0.0
    assert penalties[1] == 2.0
    assert penalties[2] == -1.0  # sentinel for "no OpenCRE data"


def test_compute_gap_penalties_reverse_order():
    """Pair order shouldn't matter (canonical ordering)."""
    opencre_pairs = [
        {"source_node_id": "asvs:V1.1", "target_node_id": "cwe:287", "gap_penalty": 0},
    ]
    eval_pairs = [
        {"source_node_id": "cwe:287", "target_node_id": "asvs:V1.1"},  # reversed
    ]
    penalties = compute_gap_penalties(eval_pairs, opencre_pairs)
    assert penalties[0] == 0.0
