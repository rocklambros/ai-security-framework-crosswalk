"""Tests for active learning uncertainty selector."""
import numpy as np
import pytest
from classifier.scripts.active_learning import select_uncertain_pairs


def test_selects_most_uncertain():
    probas = np.array([
        [0.01, 0.01, 0.01, 0.97],  # confident
        [0.25, 0.25, 0.25, 0.25],  # maximally uncertain
        [0.1, 0.2, 0.3, 0.4],     # somewhat uncertain
    ])
    pair_keys = ["confident_pair", "uncertain_pair", "medium_pair"]

    selected = select_uncertain_pairs(probas, pair_keys, n_select=2)
    assert len(selected) == 2
    assert selected[0] == "uncertain_pair"  # Most uncertain first


def test_respects_n_select():
    probas = np.random.rand(100, 4)
    probas = probas / probas.sum(axis=1, keepdims=True)
    pair_keys = [f"pair_{i}" for i in range(100)]

    selected = select_uncertain_pairs(probas, pair_keys, n_select=15)
    assert len(selected) == 15
