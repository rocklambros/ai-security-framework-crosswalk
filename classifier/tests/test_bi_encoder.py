import torch
from classifier.ensemble.bi_encoder import BiEncoderClassifier


def test_bi_encoder_forward_shape():
    model = BiEncoderClassifier(
        model_name="BAAI/bge-small-en-v1.5",  # Small for testing
        n_classes=4,
        head_type="kl",
    )
    tokens = model.tokenize_batch(
        ["access control policy"], ["authorization framework"]
    )
    logits, cls_emb = model.forward_from_tokens(tokens)
    assert logits.shape == (1, 4)
    assert cls_emb.shape[0] == 1
    assert cls_emb.shape[1] > 0


def test_bi_encoder_predict_proba():
    model = BiEncoderClassifier(
        model_name="BAAI/bge-small-en-v1.5",
        n_classes=4,
        head_type="kl",
    )
    probs = model.predict_proba(
        ["input validation", "data encryption"],
        ["sanitize user input", "AES-256 cipher"],
    )
    assert probs.shape == (2, 4)
    assert abs(probs.sum(axis=1) - 1.0).max() < 1e-5


def test_bi_encoder_corn_head():
    model = BiEncoderClassifier(
        model_name="BAAI/bge-small-en-v1.5",
        n_classes=4,
        head_type="corn",
    )
    tokens = model.tokenize_batch(["test a"], ["test b"])
    logits, _ = model.forward_from_tokens(tokens)
    assert logits.shape == (1, 3)  # n_classes - 1 for CORN


def test_bi_encoder_save_load(tmp_path):
    model = BiEncoderClassifier(
        model_name="BAAI/bge-small-en-v1.5",
        n_classes=4,
        head_type="kl",
    )
    model.save(tmp_path / "test_be")

    loaded = BiEncoderClassifier.load(tmp_path / "test_be")
    tokens = loaded.tokenize_batch(["test"], ["test"])
    logits, _ = loaded.forward_from_tokens(tokens)
    assert logits.shape == (1, 4)
