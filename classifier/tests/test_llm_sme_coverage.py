import json
from pathlib import Path
import pytest
from classifier.labeling.coverage import audit_coverage, CoverageError


def _j(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(r, sort_keys=True) for r in rows) + "\n")


def test_audit_fails_on_empty_pair(tmp_path):
    mappings = tmp_path / "mappings.jsonl"
    labels = tmp_path / "labels.jsonl"
    partition = tmp_path / "partition.json"
    _j(mappings, [
        {"source_framework": "owasp_llm", "source_id": "LLM01",
         "target_framework": "mitre_atlas", "target_node_id": "mitre_atlas:AML.T0051.000",
         "target_id_unresolved": False, "provenance_sha": "a" * 64},
    ])
    _j(labels, [])
    partition.write_text(json.dumps({"held_out": []}))
    pairs = [("owasp_llm", "mitre_atlas"), ("owasp_llm", "csa_aicm")]
    with pytest.raises(CoverageError):
        audit_coverage(pairs, mappings, labels, partition, tmp_path / "manifest.json")


def test_audit_passes_when_silver_fills_gap(tmp_path):
    mappings = tmp_path / "mappings.jsonl"
    labels = tmp_path / "labels.jsonl"
    partition = tmp_path / "partition.json"
    _j(mappings, [
        {"source_framework": "owasp_llm", "source_id": "LLM01",
         "target_framework": "mitre_atlas", "target_node_id": "mitre_atlas:AML.T0051.000",
         "target_id_unresolved": False, "provenance_sha": "a" * 64},
    ])
    _j(labels, [
        {"source_framework": "owasp_llm", "source_id": "LLM02",
         "target_framework": "csa_aicm", "target_node_id": "csa_aicm:AIS-01",
         "provenance_tag": "llm_sme_v1", "weight": 0.6},
    ])
    partition.write_text(json.dumps({"held_out": []}))
    manifest = tmp_path / "manifest.json"
    pairs = [("owasp_llm", "mitre_atlas"), ("owasp_llm", "csa_aicm")]
    audit_coverage(pairs, mappings, labels, partition, manifest)
    data = json.loads(manifest.read_text())
    by_pair = {(r["source_framework"], r["target_framework"]): r for r in data["pairs"]}
    assert by_pair[("owasp_llm", "mitre_atlas")]["upstream_gold"] == 1
    assert by_pair[("owasp_llm", "csa_aicm")]["llm_sme_silver"] == 1
