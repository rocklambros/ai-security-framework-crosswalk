"""Tests for the label freeze module."""
import json
import pytest
from pathlib import Path

from classifier.labeling.freeze import (
    freeze_and_split,
    verify_label_hashes,
    LabelHashMismatchError,
)


def _make_labels(tmp_path, n=20):
    """Create minimal v1 labels + frozen_tuples fixtures."""
    v1 = tmp_path / "v1"
    v1.mkdir()
    labels = []
    relations = ["related", "unrelated", "partial", "equivalent"]
    for i in range(n):
        labels.append({
            "source_framework": f"fw_src",
            "source_id": f"S{i:03d}",
            "target_framework": f"fw_tgt",
            "target_node_id": f"fw_tgt:T{i:03d}",
            "relation": relations[i % len(relations)],
            "confidence": 0.8,
            "provenance_tag": "llm_sme_v1",
            "weight": 0.6,
        })
    with (v1 / "labels.jsonl").open("w") as f:
        for r in labels:
            f.write(json.dumps(r, sort_keys=True) + "\n")

    ft = tmp_path / "frozen_tuples.json"
    ft.write_text(json.dumps({
        "source_tuples": [["fw_frozen", "FS001"]],
        "target_tuples": [["fw_frozen", "FT001"]],
        "pair_tuples": [["fw_frozen", "FS001", "fw_frozen", "FT001"]],
    }))
    return v1, ft


def test_freeze_and_split_creates_files(tmp_path):
    v1, ft = _make_labels(tmp_path, n=20)
    out = tmp_path / "v1_frozen"
    result = freeze_and_split(v1_dir=v1, out_dir=out, frozen_tuples_path=ft)
    assert result["n_total"] == 20
    assert result["n_train"] + result["n_val"] == 20
    assert (out / "llm_train.jsonl").exists()
    assert (out / "llm_val.jsonl").exists()
    assert (out / "hashes.json").exists()


def test_verify_label_hashes_passes(tmp_path):
    v1, ft = _make_labels(tmp_path)
    out = tmp_path / "v1_frozen"
    freeze_and_split(v1_dir=v1, out_dir=out, frozen_tuples_path=ft)
    verify_label_hashes(frozen_dir=out)  # should not raise


def test_verify_label_hashes_fails_on_tamper(tmp_path):
    v1, ft = _make_labels(tmp_path)
    out = tmp_path / "v1_frozen"
    freeze_and_split(v1_dir=v1, out_dir=out, frozen_tuples_path=ft)
    # Tamper with train file
    (out / "llm_train.jsonl").write_text("corrupted\n")
    with pytest.raises(LabelHashMismatchError):
        verify_label_hashes(frozen_dir=out)


def test_contract3_no_overwrite(tmp_path):
    v1, ft = _make_labels(tmp_path)
    out = tmp_path / "v1_frozen"
    freeze_and_split(v1_dir=v1, out_dir=out, frozen_tuples_path=ft)
    with pytest.raises(FileExistsError, match="Contract 3"):
        freeze_and_split(v1_dir=v1, out_dir=out, frozen_tuples_path=ft)


def test_frozen_overlap_aborts(tmp_path):
    v1 = tmp_path / "v1"
    v1.mkdir()
    labels = [{
        "source_framework": "fw_frozen",
        "source_id": "FS001",
        "target_framework": "fw_tgt",
        "target_node_id": "fw_tgt:T001",
        "relation": "related",
        "confidence": 0.8,
        "provenance_tag": "llm_sme_v1",
        "weight": 0.6,
    }]
    with (v1 / "labels.jsonl").open("w") as f:
        for r in labels:
            f.write(json.dumps(r) + "\n")

    ft = tmp_path / "frozen_tuples.json"
    ft.write_text(json.dumps({
        "source_tuples": [["fw_frozen", "FS001"]],
        "target_tuples": [],
        "pair_tuples": [],
    }))

    with pytest.raises(RuntimeError, match="Frozen source endpoint"):
        freeze_and_split(v1_dir=v1, out_dir=tmp_path / "out", frozen_tuples_path=ft)
