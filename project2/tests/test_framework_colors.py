"""Tests for framework color palette and display names."""
from components.framework_colors import (
    FRAMEWORK_COLORS, FRAMEWORK_DISPLAY_NAMES, FRAMEWORK_KEYS,
    CONFIDENCE_ORDER, CYBER_ACCENT,
    get_color, get_display_name, get_short_name,
)

def test_all_nine_frameworks_have_colors():
    assert len(FRAMEWORK_COLORS) == 9
    for key in FRAMEWORK_KEYS:
        assert key in FRAMEWORK_COLORS
        assert FRAMEWORK_COLORS[key].startswith("#")

def test_all_nine_frameworks_have_display_names():
    assert len(FRAMEWORK_DISPLAY_NAMES) == 9
    for key in FRAMEWORK_KEYS:
        assert key in FRAMEWORK_DISPLAY_NAMES

def test_get_color_returns_hex():
    assert get_color("aiuc_1") == "#1f6feb"

def test_get_color_unknown_returns_gray():
    assert get_color("unknown_framework") == "#6e7681"

def test_get_display_name_returns_string():
    assert get_display_name("aiuc_1") == "AIUC-1"

def test_get_display_name_unknown_returns_key():
    assert get_display_name("unknown") == "unknown"

def test_get_short_name():
    assert get_short_name("csa_aicm") == "CSA AICM"
    assert get_short_name("unknown") == "unknown"

def test_confidence_order():
    assert CONFIDENCE_ORDER == ["authoritative", "expert", "suggestive", "unvalidated"]

def test_cyber_accent():
    assert CYBER_ACCENT == "#00d4ff"

def test_framework_keys_order():
    assert FRAMEWORK_KEYS[0] == "aiuc_1"
    assert FRAMEWORK_KEYS[1] == "csa_aicm"
