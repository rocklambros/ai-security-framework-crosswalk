"""Tests for framework enumeration constants."""
from app.dash_app.frameworks import (
    UI_SOURCE_LISTS,
    UI_TARGET_FRAMEWORKS,
    DISPLAY_LABELS,
    FRAMEWORK_PAIRS,
)


def test_source_lists_count():
    assert len(UI_SOURCE_LISTS) == 3


def test_target_frameworks_includes_required():
    required = {
        "aiuc_1", "csa_aicm", "mitre_atlas", "nist_rmf",
        "iso_iec_42001", "eu_gpai_cop", "nist_ssdf",
        "nist_sp_800_53", "eu_ai_act",
    }
    assert required.issubset(set(UI_TARGET_FRAMEWORKS))


def test_framework_pairs_count():
    assert len(FRAMEWORK_PAIRS) == 26


def test_display_labels_cover_all_frameworks():
    all_fw = set(UI_SOURCE_LISTS) | set(UI_TARGET_FRAMEWORKS)
    assert all_fw == set(DISPLAY_LABELS.keys())


def test_pairs_reference_valid_frameworks():
    valid_sources = set(UI_SOURCE_LISTS)
    valid_targets = set(UI_TARGET_FRAMEWORKS)
    for src, tgt in FRAMEWORK_PAIRS:
        assert src in valid_sources, f"Unknown source: {src}"
        assert tgt in valid_targets, f"Unknown target: {tgt}"


def test_no_duplicate_pairs():
    assert len(FRAMEWORK_PAIRS) == len(set(FRAMEWORK_PAIRS))
