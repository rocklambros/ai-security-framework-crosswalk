"""Tests for cross-encoder classifier with CORN head."""
import pytest

torch = pytest.importorskip("torch")

from classifier.ensemble.cross_encoder import CrossEncoderClassifier


def test_init_creates_model():
    ce = CrossEncoderClassifier(
        model_name="cross-encoder/ms-marco-TinyBERT-L-2-v2",
        n_classes=4,
    )
    assert ce.n_classes == 4


def test_tokenize_pair():
    ce = CrossEncoderClassifier(
        model_name="cross-encoder/ms-marco-TinyBERT-L-2-v2",
        n_classes=4,
    )
    tokens = ce.tokenize_pair("prompt injection attack", "LLM prompt injection defense")
    assert "input_ids" in tokens
    assert tokens["input_ids"].shape[0] == 1


def test_forward_returns_logits():
    ce = CrossEncoderClassifier(
        model_name="cross-encoder/ms-marco-TinyBERT-L-2-v2",
        n_classes=4,
    )
    tokens = ce.tokenize_pair("text a", "text b")
    logits, cls_emb = ce.forward_pair(tokens)
    assert logits.shape == (1, 3)  # n_classes - 1 for CORN
    assert cls_emb.shape[0] == 1
    assert cls_emb.shape[1] > 0
