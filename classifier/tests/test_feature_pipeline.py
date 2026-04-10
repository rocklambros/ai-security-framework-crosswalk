"""Tests for PCA + probability + agreement feature pipeline."""
import numpy as np
import pytest


def test_build_features_reduces_dimensionality():
    """Feature pipeline should produce far fewer than 3081 features."""
    from classifier.ensemble.feature_pipeline import FeaturePipeline

    rng = np.random.RandomState(42)
    ce_features = {
        "deberta_logits": rng.randn(100, 3),
        "deberta_cls_emb": rng.randn(100, 1024),
        "roberta_logits": rng.randn(100, 3),
        "roberta_cls_emb": rng.randn(100, 1024),
        "electra_logits": rng.randn(100, 3),
        "electra_cls_emb": rng.randn(100, 1024),
    }

    pipe = FeaturePipeline(pca_variance=0.95)
    X_train = pipe.fit_transform(ce_features, n_train=80)
    X_all = pipe.transform(ce_features)

    assert X_train.shape[0] == 80
    assert X_all.shape[0] == 100
    assert X_all.shape[1] < 300, f"Expected <300 features, got {X_all.shape[1]}"
    assert X_all.shape[1] > 20, f"Expected >20 features, got {X_all.shape[1]}"


def test_feature_pipeline_includes_probabilities():
    """Pipeline must include softmax probabilities (12 features)."""
    from classifier.ensemble.feature_pipeline import FeaturePipeline

    rng = np.random.RandomState(42)
    ce_features = {
        "deberta_logits": rng.randn(50, 3),
        "deberta_cls_emb": rng.randn(50, 1024),
        "roberta_logits": rng.randn(50, 3),
        "roberta_cls_emb": rng.randn(50, 1024),
        "electra_logits": rng.randn(50, 3),
        "electra_cls_emb": rng.randn(50, 1024),
    }
    pipe = FeaturePipeline(pca_variance=0.95)
    pipe.fit_transform(ce_features, n_train=50)
    names = pipe.feature_names()

    prob_features = [n for n in names if "prob" in n.lower()]
    assert len(prob_features) == 12, f"Expected 12 probability features, got {len(prob_features)}"


def test_feature_pipeline_includes_agreement():
    """Pipeline must include model agreement features."""
    from classifier.ensemble.feature_pipeline import FeaturePipeline

    rng = np.random.RandomState(42)
    ce_features = {
        "deberta_logits": rng.randn(50, 3),
        "deberta_cls_emb": rng.randn(50, 1024),
        "roberta_logits": rng.randn(50, 3),
        "roberta_cls_emb": rng.randn(50, 1024),
        "electra_logits": rng.randn(50, 3),
        "electra_cls_emb": rng.randn(50, 1024),
    }
    pipe = FeaturePipeline(pca_variance=0.95)
    pipe.fit_transform(ce_features, n_train=50)
    names = pipe.feature_names()

    agree_features = [n for n in names if "agree" in n.lower() or "entropy" in n.lower() or "cosine" in n.lower()]
    assert len(agree_features) >= 4, f"Expected >=4 agreement features, got {len(agree_features)}"


def test_feature_pipeline_save_load_roundtrip(tmp_path):
    """Pipeline must save and load with identical transform output."""
    from classifier.ensemble.feature_pipeline import FeaturePipeline

    rng = np.random.RandomState(42)
    ce_features = {
        "deberta_logits": rng.randn(50, 3),
        "deberta_cls_emb": rng.randn(50, 1024),
        "roberta_logits": rng.randn(50, 3),
        "roberta_cls_emb": rng.randn(50, 1024),
        "electra_logits": rng.randn(50, 3),
        "electra_cls_emb": rng.randn(50, 1024),
    }
    pipe = FeaturePipeline(pca_variance=0.95)
    X1 = pipe.fit_transform(ce_features, n_train=50)

    pipe.save(tmp_path / "feature_pipe")
    pipe2 = FeaturePipeline.load(tmp_path / "feature_pipe")
    X2 = pipe2.transform(ce_features)

    np.testing.assert_allclose(X1, X2, atol=1e-6)
