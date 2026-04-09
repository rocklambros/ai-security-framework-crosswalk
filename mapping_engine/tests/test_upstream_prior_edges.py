"""Unit tests for the upstream crossref prior-edge loader."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from mapping_engine.engine.upstream_prior_edges import load_upstream_prior_edges


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(r, sort_keys=True) for r in rows) + "\n")


def test_held_out_rows_are_filtered(tmp_path: Path) -> None:
    crossrefs = tmp_path / "crossrefs_v1.jsonl"
    partition = tmp_path / "partition.json"
    _write_jsonl(
        crossrefs,
        [
            {
                "source_framework": "owasp_agentic",
                "source_id": "ASI01",
                "target_framework": "owasp_llm",
                "target_id": "LLM01",
                "target_node_id": "owasp_llm:LLM01",
                "target_id_unresolved": False,
                "provenance_sha": "aaa",
            },
            {
                "source_framework": "owasp_agentic",
                "source_id": "ASI02",
                "target_framework": "owasp_llm",
                "target_id": "LLM02",
                "target_node_id": "owasp_llm:LLM02",
                "target_id_unresolved": False,
                "provenance_sha": "bbb",
            },
        ],
    )
    partition.write_text(json.dumps({"held_out": ["bbb"], "train_eligible": ["aaa"]}))

    present = {"owasp_agentic:ASI01", "owasp_agentic:ASI02", "owasp_llm:LLM01", "owasp_llm:LLM02"}
    injected, firewall_out = load_upstream_prior_edges(crossrefs, partition, present_node_ids=present)

    assert len(injected) == 1
    e = injected[0]
    assert e["source_node_id"] == "owasp_agentic:ASI01"
    assert e["target_node_id"] == "owasp_llm:LLM01"
    assert e["edge_type"] == "upstream_crossref"
    assert e["provenance"] == "upstream_crossref_v1"
    assert e["confidence"] == "authoritative"
    assert "aaa" in (e.get("notes") or "")
    assert len(firewall_out) == 1


def test_unresolved_rows_are_dropped(tmp_path: Path) -> None:
    crossrefs = tmp_path / "crossrefs_v1.jsonl"
    partition = tmp_path / "partition.json"
    _write_jsonl(
        crossrefs,
        [
            {
                "source_framework": "owasp_agentic",
                "source_id": "ASI01",
                "target_framework": "owasp_llm",
                "target_id": "LLM01",
                "target_node_id": "owasp_llm:LLM01",
                "target_id_unresolved": True,
                "provenance_sha": "aaa",
            }
        ],
    )
    partition.write_text(json.dumps({"held_out": [], "train_eligible": ["aaa"]}))

    present = {"owasp_agentic:ASI01", "owasp_llm:LLM01"}
    injected, firewall_out = load_upstream_prior_edges(crossrefs, partition, present_node_ids=present)
    assert injected == []
    assert firewall_out == []


def test_missing_nodes_are_dropped_with_warning(tmp_path: Path) -> None:
    crossrefs = tmp_path / "crossrefs_v1.jsonl"
    partition = tmp_path / "partition.json"
    _write_jsonl(
        crossrefs,
        [
            {
                "source_framework": "owasp_agentic",
                "source_id": "ASI01",
                "target_framework": "owasp_dsgai",
                "target_id": "DSGAI99",
                "target_node_id": "owasp_dsgai:DSGAI99",
                "target_id_unresolved": False,
                "provenance_sha": "aaa",
            }
        ],
    )
    partition.write_text(json.dumps({"held_out": [], "train_eligible": ["aaa"]}))

    present = {"owasp_agentic:ASI01"}  # DSGAI99 intentionally absent
    warnings: list[str] = []
    injected, firewall_out = load_upstream_prior_edges(
        crossrefs, partition, present_node_ids=present, warnings=warnings
    )
    assert injected == []
    assert any("DSGAI99" in w for w in warnings)


def test_frozen_firewall_drops_leaking_crossrefs(tmp_path: Path) -> None:
    crossrefs = tmp_path / "crossrefs.jsonl"
    _write_jsonl(
        crossrefs,
        [
            {
                "source_framework": "owasp_llm",
                "source_id": "LLM02",
                "source_node_id": "owasp_llm:LLM02",
                "target_framework": "mitre_atlas",
                "target_id": "AML.T0054",
                "target_node_id": "mitre_atlas:AML.T0054",
                "target_id_unresolved": False,
                "provenance_sha": "local_sha",
            }
        ],
    )
    partition = tmp_path / "partition.json"
    partition.write_text(json.dumps({"held_out": [], "train_eligible": ["local_sha"]}))
    frozen = tmp_path / "frozen.json"
    frozen.write_text(json.dumps({
        "source_tuples": [["owasp_llm", "LLM02"]],
        "target_tuples": [["_none_", "_none_"]],
        "pair_tuples": [],
    }))
    present = {"owasp_llm:LLM02", "mitre_atlas:AML.T0054"}
    injected, firewall_out = load_upstream_prior_edges(
        crossrefs, partition, present, frozen_tuples_path=frozen
    )
    assert injected == []
    assert len(firewall_out) == 1


def test_frozen_tuples_missing_raises(tmp_path: Path) -> None:
    crossrefs = tmp_path / "crossrefs.jsonl"
    crossrefs.write_text("")
    partition = tmp_path / "partition.json"
    partition.write_text(json.dumps({"held_out": []}))
    with pytest.raises(RuntimeError, match="frozen_tuples.json missing"):
        load_upstream_prior_edges(
            crossrefs, partition, set(),
            frozen_tuples_path=tmp_path / "nonexistent.json",
        )
