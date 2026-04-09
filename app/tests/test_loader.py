"""Tests for data loading functions."""
import pytest
from app.dash_app.data.loader import load_mappings, load_sacred_results, load_ablations


def test_load_mappings_returns_dataframe():
    """Test loading upstream mappings — skip if data not available."""
    from pathlib import Path
    if not Path("data/upstream/mappings_v1.jsonl").exists():
        pytest.skip("mappings_v1.jsonl not found")

    df = load_mappings()
    assert len(df) > 0
    assert "source_node_id" in df.columns or "source_id" in df.columns
    assert "target_node_id" in df.columns
    assert "tier" in df.columns


def test_load_sacred_results():
    """Test loading sacred run results — returns dict or None."""
    result = load_sacred_results()
    if result is not None:
        assert "tier_accuracy" in result or "macro_f1" in result


def test_load_ablations():
    """Test loading ablation results — returns dict or None."""
    result = load_ablations()
    if result is not None:
        assert isinstance(result, (dict, list))
