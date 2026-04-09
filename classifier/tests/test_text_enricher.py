"""Tests for control text enrichment."""
from classifier.data.text_enricher import enrich_control_text


def test_adds_parent_text():
    controls = {
        "fw:P1": {"text": "Parent control", "parent_id": None, "category": "Gov"},
        "fw:C1": {"text": "Child control", "parent_id": "fw:P1", "category": "Gov"},
    }
    enriched = enrich_control_text("fw:C1", controls)
    assert "Parent control" in enriched
    assert "Child control" in enriched


def test_adds_category():
    controls = {
        "fw:C1": {"text": "Some control", "parent_id": None, "category": "Governance"},
    }
    enriched = enrich_control_text("fw:C1", controls)
    assert "Governance" in enriched


def test_no_parent_still_works():
    controls = {
        "fw:C1": {"text": "Standalone control", "parent_id": None, "category": "Risk"},
    }
    enriched = enrich_control_text("fw:C1", controls)
    assert "Standalone control" in enriched
    assert "Risk" in enriched


def test_missing_control_returns_empty():
    controls = {}
    enriched = enrich_control_text("fw:MISSING", controls)
    assert enriched == ""
