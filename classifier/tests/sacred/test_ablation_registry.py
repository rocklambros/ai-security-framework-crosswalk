"""Tests for ablation registry."""
from classifier.sacred.ablation_registry import (
    ABLATIONS,
    V2_ABLATIONS,
    ALL_ABLATIONS,
    get_ablation,
)

V1_REQUIRED = {
    "no_gat",
    "no_bm25",
    "no_bridge",
    "no_stacker",
    "lexical_only",
    "biencoder_only",
}

V2_REQUIRED = {
    "ce_deberta_only",
    "ce_deberta_corn",
    "ce_plus_gat",
    "multi_ce",
    "full_v2",
    "full_v2_two_stage",
}


def test_v1_registry_has_required_keys():
    assert V1_REQUIRED.issubset(set(ABLATIONS.keys()))


def test_v2_registry_has_required_keys():
    assert V2_REQUIRED.issubset(set(V2_ABLATIONS.keys()))


def test_all_ablations_merges_both():
    assert set(ALL_ABLATIONS.keys()) == set(ABLATIONS.keys()) | set(V2_ABLATIONS.keys())


def test_registry_values_are_dicts():
    for name, cfg in ALL_ABLATIONS.items():
        assert isinstance(cfg, dict)
        assert "description" in cfg
        assert isinstance(cfg["description"], str) and cfg["description"]


def test_get_ablation_returns_config():
    cfg = get_ablation("full_v2")
    assert cfg["description"] == "Full v2 ensemble: 3x CE + GAT + BM25 + bridge"


def test_get_ablation_raises_on_unknown():
    import pytest

    with pytest.raises(KeyError, match="Unknown ablation"):
        get_ablation("nonexistent_ablation")
