"""Tests for human_cal loader."""
import json
import pytest
from pathlib import Path

from classifier.calibration.cal_loader import (
    load_human_cal, load_human_cal_labels, EXPERT_TIER_MAP, HUMAN_CAL_PATH,
)


def test_load_human_cal_returns_150_rows():
    if not HUMAN_CAL_PATH.exists():
        pytest.skip("human_cal.jsonl not available")
    rows = load_human_cal()
    assert len(rows) == 150


def test_expert_tier_mapping():
    if not HUMAN_CAL_PATH.exists():
        pytest.skip("human_cal.jsonl not available")
    rows = load_human_cal()
    for r in rows:
        assert r["label"] == EXPERT_TIER_MAP[r["expert_tier"]]


def test_label_array_shape():
    if not HUMAN_CAL_PATH.exists():
        pytest.skip("human_cal.jsonl not available")
    labels = load_human_cal_labels()
    assert labels.shape == (150,)
    assert set(labels.tolist()).issubset({0, 1, 2, 3})
