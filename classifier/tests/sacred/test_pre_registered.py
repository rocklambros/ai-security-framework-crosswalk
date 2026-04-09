"""Tests for pre-registered constants loader (Contract 15)."""
from classifier.sacred.pre_registered import load


def test_loader_returns_dict():
    data = load()
    assert isinstance(data, dict)
    assert "conformal" in data
    assert "abstention" in data
    assert "statistical_tests" in data


def test_conformal_alpha():
    data = load()
    assert data["conformal"]["alpha"] == 0.10  # pragma: pre_reg_allowed


def test_abstention_precision_floor():
    data = load()
    assert data["abstention"]["precision_floor"] == 0.95  # pragma: pre_reg_allowed
