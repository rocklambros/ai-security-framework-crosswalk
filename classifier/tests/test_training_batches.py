"""Tests for provenance-weighted training batch loader (Contract 10)."""
import json
import pytest
from pathlib import Path

from classifier.ensemble.training_batches import iter_weighted_rows, DEFAULT_LABEL_WEIGHTS


def _write_jsonl(tmp_path, name, rows):
    p = tmp_path / name
    with open(p, "w") as f:
        for r in rows:
            f.write(json.dumps(r, sort_keys=True) + "\n")
    return p


def _setup(tmp_path, labels, frozen_src=None, frozen_tgt=None, frozen_pairs=None, held_out=None):
    labels_path = _write_jsonl(tmp_path, "labels.jsonl", labels)
    ft = tmp_path / "frozen_tuples.json"
    ft.write_text(json.dumps({
        "source_tuples": frozen_src or [],
        "target_tuples": frozen_tgt or [],
        "pair_tuples": frozen_pairs or [],
    }))
    part = tmp_path / "partition.json"
    part.write_text(json.dumps({"held_out": held_out or [], "train_eligible": []}))
    return labels_path, ft, part


def _label(src_fw="fw_a", src_id="S001", tgt_fw="fw_b", tgt_id="T001",
           tag="llm_sme_v1", prov_sha=""):
    return {
        "source_framework": src_fw,
        "source_id": src_id,
        "target_framework": tgt_fw,
        "target_node_id": f"{tgt_fw}:{tgt_id}",
        "provenance_tag": tag,
        "provenance_sha": prov_sha,
        "relation": "related",
        "confidence": 0.8,
    }


def test_yields_rows_with_weights(tmp_path):
    labels = [_label(tag="llm_sme_v1"), _label(src_id="S002", tag="upstream_v1")]
    lp, ft, part = _setup(tmp_path, labels)
    rows = list(iter_weighted_rows(lp, frozen_tuples_path=ft, partition_path=part))
    assert len(rows) == 2
    assert rows[0][1] == DEFAULT_LABEL_WEIGHTS["llm_sme_v1"]
    assert rows[1][1] == DEFAULT_LABEL_WEIGHTS["upstream_v1"]


def test_custom_weight_map(tmp_path):
    labels = [_label(tag="llm_sme_v1")]
    lp, ft, part = _setup(tmp_path, labels)
    rows = list(iter_weighted_rows(lp, weight_map={"llm_sme_v1": 0.9},
                                   frozen_tuples_path=ft, partition_path=part))
    assert rows[0][1] == 0.9


def test_layer0_frozen_source_raises(tmp_path):
    labels = [_label(src_fw="fw_a", src_id="S001")]
    lp, ft, part = _setup(tmp_path, labels, frozen_src=[["fw_a", "S001"]])
    with pytest.raises(RuntimeError, match="Layer 0.*frozen source"):
        list(iter_weighted_rows(lp, frozen_tuples_path=ft, partition_path=part))


def test_layer0_frozen_target_raises(tmp_path):
    labels = [_label(tgt_fw="fw_b", tgt_id="T001")]
    lp, ft, part = _setup(tmp_path, labels, frozen_tgt=[["fw_b", "T001"]])
    with pytest.raises(RuntimeError, match="Layer 0.*frozen target"):
        list(iter_weighted_rows(lp, frozen_tuples_path=ft, partition_path=part))


def test_layer1_held_out_sha_raises(tmp_path):
    labels = [_label(prov_sha="abc123")]
    lp, ft, part = _setup(tmp_path, labels, held_out=["abc123"])
    with pytest.raises(RuntimeError, match="Layer 1.*held-out"):
        list(iter_weighted_rows(lp, frozen_tuples_path=ft, partition_path=part))


def test_missing_frozen_tuples_raises(tmp_path):
    labels = [_label()]
    lp = _write_jsonl(tmp_path, "labels.jsonl", labels)
    with pytest.raises(FileNotFoundError, match="frozen_tuples.json missing"):
        list(iter_weighted_rows(lp, frozen_tuples_path=tmp_path / "nonexistent.json",
                                partition_path=tmp_path / "partition.json"))


def test_clean_labels_pass_both_layers(tmp_path):
    """All v1_frozen labels should pass both layers (0 frozen overlap)."""
    frozen_path = Path("data/splits/frozen_tuples.json")
    part_path = Path("data/upstream/partition.json")
    labels_path = Path("data/labels/llm_sme/v1_frozen/llm_train.jsonl")
    if not all(p.exists() for p in [frozen_path, part_path, labels_path]):
        pytest.skip("data files not available")
    rows = list(iter_weighted_rows(labels_path, frozen_tuples_path=frozen_path,
                                   partition_path=part_path))
    assert len(rows) > 0
