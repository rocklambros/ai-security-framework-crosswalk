"""End-to-end smoke test: CPU, tiny data, 2 epochs, all code paths.

Catches bugs BEFORE they cost $3/hr on a GPU pod.
"""
import json
import os

import pytest
import torch

os.environ["WANDB_MODE"] = "disabled"

TINY_PAIRS = [
    {"source_text": "Access control policy", "target_text": "Authorization framework",
     "tier_label": 3, "sample_weight": 1.0, "data_source": "test",
     "source_node_id": "test:1", "target_node_id": "test:2", "pair_key": "t__t::test:1__test:2"},
    {"source_text": "Input validation", "target_text": "Data sanitization",
     "tier_label": 2, "sample_weight": 1.0, "data_source": "test",
     "source_node_id": "test:3", "target_node_id": "test:4", "pair_key": "t__t::test:3__test:4"},
    {"source_text": "Encryption at rest", "target_text": "Network monitoring",
     "tier_label": 0, "sample_weight": 1.0, "data_source": "test",
     "source_node_id": "test:5", "target_node_id": "test:6", "pair_key": "t__t::test:5__test:6"},
    {"source_text": "Incident response", "target_text": "Disaster recovery",
     "tier_label": 1, "sample_weight": 1.0, "data_source": "test",
     "source_node_id": "test:7", "target_node_id": "test:8", "pair_key": "t__t::test:7__test:8"},
    {"source_text": "Audit logging", "target_text": "Compliance reporting",
     "tier_label": 2, "sample_weight": 1.0, "data_source": "test",
     "source_node_id": "test:9", "target_node_id": "test:10", "pair_key": "t__t::test:9__test:10"},
]


@pytest.fixture
def tiny_data_dir(tmp_path):
    train_path = tmp_path / "train.jsonl"
    val_path = tmp_path / "val.jsonl"
    with train_path.open("w") as f:
        for p in TINY_PAIRS:
            json.dump(p, f)
            f.write("\n")
    with val_path.open("w") as f:
        for p in TINY_PAIRS[:3]:
            json.dump(p, f)
            f.write("\n")
    return tmp_path


@pytest.mark.parametrize("loss_type", ["kl", "corn", "focal"])
def test_cross_encoder_smoke(tiny_data_dir, loss_type):
    """Smoke test: DeBERTa-base cross-encoder with each loss function."""
    from classifier.ensemble.cross_encoder_trainer import train_cross_encoder

    metrics = train_cross_encoder(
        model_name="microsoft/deberta-v3-base",
        train_path=str(tiny_data_dir / "train.jsonl"),
        val_path=str(tiny_data_dir / "val.jsonl"),
        output_dir=str(tiny_data_dir / f"out_{loss_type}"),
        epochs=2,
        batch_size=2,
        learning_rate=2e-5,
        loss_type=loss_type,
    )
    assert "combined_f1" in metrics or "val_macro_f1" in metrics


@pytest.mark.parametrize("loss_type", ["kl", "focal"])
def test_bi_encoder_smoke(tiny_data_dir, loss_type):
    """Smoke test: BGE bi-encoder with each loss function."""
    from classifier.ensemble.cross_encoder_trainer import train_cross_encoder

    metrics = train_cross_encoder(
        model_name="BAAI/bge-small-en-v1.5",
        train_path=str(tiny_data_dir / "train.jsonl"),
        val_path=str(tiny_data_dir / "val.jsonl"),
        output_dir=str(tiny_data_dir / f"out_bge_{loss_type}"),
        epochs=2,
        batch_size=2,
        learning_rate=2e-5,
        loss_type=loss_type,
    )
    assert "combined_f1" in metrics or "val_macro_f1" in metrics
