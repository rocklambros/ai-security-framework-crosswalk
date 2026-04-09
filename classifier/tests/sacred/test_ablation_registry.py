"""Tests for ablation registry."""
from classifier.sacred.ablation_registry import ABLATIONS, AblationConfig

REQUIRED = {
    "full",
    "no_gat",
    "no_bridge",
    "no_bge",
    "no_bm25",
    "gat_only",
    "baseline_only",
    "lexical_only",
    "no_conformal",
    "no_router",
}


def test_registry_has_required_keys():
    assert REQUIRED.issubset(set(ABLATIONS.keys()))


def test_registry_values_are_configs():
    for name, cfg in ABLATIONS.items():
        assert isinstance(cfg, AblationConfig)
        assert cfg.name == name
        assert isinstance(cfg.disable, tuple)
        assert isinstance(cfg.description, str) and cfg.description


def test_full_disables_nothing():
    assert ABLATIONS["full"].disable == ()
