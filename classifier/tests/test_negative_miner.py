"""Tests for hard negative mining via BM25."""
import pytest
from classifier.data.negative_miner import mine_hard_negatives


def test_returns_expected_count():
    source_texts = {"src1": "prompt injection attack", "src2": "data poisoning"}
    target_texts = {"tgt1": "injection defense", "tgt2": "model training", "tgt3": "bias"}
    positive_pairs = {("src1", "tgt1")}
    excluded_nodes = set()

    negatives = mine_hard_negatives(
        source_texts=source_texts,
        target_texts=target_texts,
        positive_pairs=positive_pairs,
        excluded_nodes=excluded_nodes,
        n_negatives_per_source=2,
    )
    assert len(negatives) >= 2
    for src, tgt in negatives:
        assert (src, tgt) not in positive_pairs


def test_excludes_test_cal_nodes():
    source_texts = {"src1": "prompt injection"}
    target_texts = {"tgt1": "injection", "tgt_excluded": "also injection"}
    positive_pairs = set()
    excluded_nodes = {"tgt_excluded"}

    negatives = mine_hard_negatives(
        source_texts=source_texts,
        target_texts=target_texts,
        positive_pairs=positive_pairs,
        excluded_nodes=excluded_nodes,
        n_negatives_per_source=5,
    )
    for _, tgt in negatives:
        assert tgt != "tgt_excluded"


def test_empty_sources_returns_empty():
    negatives = mine_hard_negatives(
        source_texts={},
        target_texts={"tgt1": "text"},
        positive_pairs=set(),
        excluded_nodes=set(),
        n_negatives_per_source=5,
    )
    assert negatives == []
