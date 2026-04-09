"""Tests for contrastive pre-training data preparation."""
import pytest
from classifier.ensemble.contrastive_pretrain import build_contrastive_pairs


def test_build_contrastive_pairs():
    mappings = [
        {"source_node_id": "a:1", "target_node_id": "b:1", "tier_label": 3,
         "source_text": "prompt injection", "target_text": "LLM injection"},
        {"source_node_id": "a:2", "target_node_id": "b:2", "tier_label": 2,
         "source_text": "data poisoning", "target_text": "training data attack"},
    ]
    pairs = build_contrastive_pairs(mappings, n_negatives=1, seed=42)
    assert len(pairs) > 0
    for p in pairs:
        assert "anchor" in p
        assert "positive" in p or "negative" in p
        assert "label" in p


def test_contrastive_pairs_has_both_labels():
    mappings = [
        {"source_node_id": "a:1", "target_node_id": "b:1", "tier_label": 3,
         "source_text": "text a1", "target_text": "text b1"},
        {"source_node_id": "a:2", "target_node_id": "b:2", "tier_label": 2,
         "source_text": "text a2", "target_text": "text b2"},
        {"source_node_id": "a:3", "target_node_id": "b:3", "tier_label": 1,
         "source_text": "text a3", "target_text": "text b3"},
    ]
    pairs = build_contrastive_pairs(mappings, n_negatives=2, seed=42)
    labels = [p["label"] for p in pairs]
    assert 1 in labels
    assert 0 in labels
