import json
from pathlib import Path
from classifier.labeling.schemas import LLMSMELabel
from classifier.labeling.writer import write_labels


def test_writer_emits_provenance_tag(tmp_path):
    out = tmp_path / "labels.jsonl"
    labels = [
        LLMSMELabel(
            source_framework="owasp_llm", source_id="LLM01",
            target_framework="mitre_atlas", target_node_id="mitre_atlas:AML.T0051.000",
            relation="related", confidence=0.7, rationale="x",
            prompt_sha="0" * 64, model_version="m",
        )
    ]
    write_labels(labels, out)
    rows = [json.loads(l) for l in out.read_text().splitlines() if l.strip()]
    assert rows[0]["provenance_tag"] == "llm_sme_v1"
    assert rows[0]["weight"] == 0.6


def test_writer_is_byte_stable(tmp_path):
    out1 = tmp_path / "a.jsonl"
    out2 = tmp_path / "b.jsonl"
    labels = [
        LLMSMELabel(
            source_framework="owasp_llm", source_id="LLM01",
            target_framework="mitre_atlas", target_node_id="mitre_atlas:AML.T0051.000",
            relation="related", confidence=0.7, rationale="x",
            prompt_sha="0" * 64, model_version="m",
        )
    ]
    write_labels(labels, out1)
    write_labels(labels, out2)
    assert out1.read_bytes() == out2.read_bytes()
