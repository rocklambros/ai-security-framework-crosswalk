"""Tests for framework metadata constants."""
from app.dash_app.data.frameworks import (
    FRAMEWORK_LABELS,
    FRAMEWORK_COLORS,
    TIER_LABELS,
    TIER_COLORS,
    FRAMEWORK_CATEGORIES,
)


def test_framework_labels_count():
    assert len(FRAMEWORK_LABELS) == 14


def test_framework_colors_match_labels():
    assert set(FRAMEWORK_COLORS.keys()) == set(FRAMEWORK_LABELS.keys())


def test_tier_labels_has_required():
    required = {"equivalent", "related", "partial", "unrelated"}
    assert required.issubset(set(TIER_LABELS.keys()))


def test_tier_colors_has_required():
    required = {"equivalent", "related", "partial", "unrelated"}
    assert required.issubset(set(TIER_COLORS.keys()))


def test_categories_cover_all_frameworks():
    all_fw = set()
    for fws in FRAMEWORK_CATEGORIES.values():
        all_fw.update(fws)
    assert all_fw == set(FRAMEWORK_LABELS.keys())
