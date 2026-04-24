"""Test that expert training split has zero text-pair overlap."""
import json
from pathlib import Path


def test_no_textpair_overlap_between_train_val():
    """After rebuild, no (source_text, target_text) pair should appear in both splits."""
    train_path = Path("data/splits/expert_train.jsonl")
    val_path = Path("data/splits/expert_val.jsonl")
    if not train_path.exists() or not val_path.exists():
        import pytest
        pytest.skip("Splits not yet built")

    train_pairs = set()
    with train_path.open() as f:
        for line in f:
            row = json.loads(line)
            train_pairs.add((row["source_text"], row["target_text"]))

    overlap = 0
    with val_path.open() as f:
        for line in f:
            row = json.loads(line)
            if (row["source_text"], row["target_text"]) in train_pairs:
                overlap += 1

    assert overlap == 0, f"{overlap} text pairs appear in both train and val"


def test_val_has_positive_classes():
    """Val set must have all 3 positive tier_label classes (1, 2, 3).
    Negatives (label=0) are kept entirely in train since they are synthetic."""
    val_path = Path("data/splits/expert_val.jsonl")
    if not val_path.exists():
        import pytest
        pytest.skip("Splits not yet built")

    labels = set()
    with val_path.open() as f:
        for line in f:
            labels.add(json.loads(line)["tier_label"])
    assert {1, 2, 3}.issubset(labels), f"Missing positive classes in val: {set(range(1, 4)) - labels}"


def test_mapping_level_split_preserves_counts():
    """Total rows should be within a reasonable range and val should not be trivially small."""
    train_path = Path("data/splits/expert_train.jsonl")
    val_path = Path("data/splits/expert_val.jsonl")
    if not train_path.exists():
        import pytest
        pytest.skip("Splits not yet built")

    n_train = sum(1 for _ in train_path.open())
    n_val = sum(1 for _ in val_path.open())
    total = n_train + n_val
    assert total > 1_000, f"Unexpected total (too small): {total}"
    assert n_val > 100, f"Val too small: {n_val}"
