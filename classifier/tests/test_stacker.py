"""Tests for classifier.ensemble.stacker."""


def test_feature_cols_defined():
    from classifier.ensemble.stacker import FEATURE_COLS
    assert isinstance(FEATURE_COLS, list)
    assert len(FEATURE_COLS) > 0


def test_v2_feature_cols_count():
    from classifier.ensemble.stacker import FEATURE_COLS_V2
    assert len(FEATURE_COLS_V2) == 83


def test_stacker_v2_init():
    from classifier.ensemble.stacker import LGBMStacker
    s = LGBMStacker(version="v2")
    assert len(s.feature_cols) == 83


def test_stacker_v1_init():
    from classifier.ensemble.stacker import LGBMStacker, FEATURE_COLS
    s = LGBMStacker(version="v1")
    assert s.feature_cols is FEATURE_COLS


def test_stacker_default_version_is_v1():
    from classifier.ensemble.stacker import LGBMStacker, FEATURE_COLS
    s = LGBMStacker()
    assert s.version == "v1"
    assert s.feature_cols is FEATURE_COLS
