import pytest
from classifier.labeling.schemas import GapTuple, LLMSMELabel, CoverageRow


def test_gap_tuple_roundtrip():
    g = GapTuple(
        source_framework="owasp_llm",
        source_id="LLM01",
        target_framework="mitre_atlas",
        target_node_id="mitre_atlas:AML.T0051.000",
    )
    assert g.model_dump()["source_id"] == "LLM01"


def test_llm_sme_label_requires_provenance_tag():
    lbl = LLMSMELabel(
        source_framework="owasp_llm",
        source_id="LLM01",
        target_framework="mitre_atlas",
        target_node_id="mitre_atlas:AML.T0051.000",
        relation="related",
        confidence=0.82,
        rationale="jailbreak overlap",
        prompt_sha="0" * 64,
        model_version="claude-sonnet-4-5-20251101",
    )
    d = lbl.model_dump()
    assert d["provenance_tag"] == "llm_sme_v1"
    assert d["weight"] == 0.6


def test_llm_sme_label_rejects_bad_relation():
    with pytest.raises(ValueError):
        LLMSMELabel(
            source_framework="owasp_llm",
            source_id="LLM01",
            target_framework="mitre_atlas",
            target_node_id="mitre_atlas:AML.T0051.000",
            relation="bogus",
            confidence=0.5,
            rationale="x",
            prompt_sha="0" * 64,
            model_version="m",
        )


def test_coverage_row_flags_empty_pair():
    row = CoverageRow(
        source_framework="owasp_llm",
        target_framework="mitre_atlas",
        upstream_gold=0,
        llm_sme_silver=0,
    )
    assert row.total == 0
    assert row.empty is True
