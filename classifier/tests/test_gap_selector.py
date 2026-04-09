import json
from pathlib import Path
from classifier.labeling.gap_selector import select_gap_tuples


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True) + "\n")


def test_gap_selector_excludes_upstream_covered_frozen_and_heldout(tmp_path):
    pool = tmp_path / "pool.jsonl"
    mappings = tmp_path / "mappings.jsonl"
    partition = tmp_path / "partition.json"
    frozen = tmp_path / "frozen_tuples.json"

    _write_jsonl(
        pool,
        [
            # covered by upstream gold (train-eligible) -> NOT a gap
            {"source_framework": "owasp_llm", "source_id": "LLM01",
             "target_framework": "mitre_atlas", "target_node_id": "mitre_atlas:AML.T0051.000"},
            # upstream held-out AND source_id in frozen test -> MUST NOT be a gap (layer 0 firewall)
            {"source_framework": "owasp_llm", "source_id": "LLM02",
             "target_framework": "mitre_atlas", "target_node_id": "mitre_atlas:AML.T0054"},
            # upstream row exists but target_id_unresolved -> gap IF source/target not frozen
            {"source_framework": "owasp_llm", "source_id": "LLM03",
             "target_framework": "csa_aicm", "target_node_id": "csa_aicm:AIS-01"},
            # no upstream row at all -> gap IF source/target not frozen
            {"source_framework": "owasp_llm", "source_id": "LLM04",
             "target_framework": "nist_rmf", "target_node_id": "nist_rmf:GOVERN-1.6"},
            # target_node_id appears in frozen target set -> MUST NOT be a gap (layer 0 firewall)
            {"source_framework": "owasp_llm", "source_id": "LLM05",
             "target_framework": "mitre_atlas", "target_node_id": "mitre_atlas:AML.T0999"},
        ],
    )
    _write_jsonl(
        mappings,
        [
            {"source_framework": "owasp_llm", "source_id": "LLM01",
             "target_framework": "mitre_atlas", "target_node_id": "mitre_atlas:AML.T0051.000",
             "target_id_unresolved": False, "provenance_sha": "a" * 64},
            {"source_framework": "owasp_llm", "source_id": "LLM02",
             "target_framework": "mitre_atlas", "target_node_id": "mitre_atlas:AML.T0054",
             "target_id_unresolved": False, "provenance_sha": "b" * 64},
            {"source_framework": "owasp_llm", "source_id": "LLM03",
             "target_framework": "csa_aicm", "target_node_id": None,
             "target_id_unresolved": True, "provenance_sha": "c" * 64},
        ],
    )
    partition.write_text(json.dumps({"held_out": ["b" * 64]}))
    frozen.write_text(json.dumps({
        "source_tuples": [["owasp_llm", "LLM02"]],
        "target_tuples": [["mitre_atlas", "AML.T0999"]],
        "pair_tuples": [["owasp_llm", "LLM02", "mitre_atlas", "AML.T0054"]],
    }))

    gaps = select_gap_tuples(pool, mappings, partition, frozen)
    ids = sorted(g.source_id for g in gaps)
    # LLM01 covered; LLM02 firewall (src); LLM05 firewall (tgt); LLM03/LLM04 legitimate gaps
    assert ids == ["LLM03", "LLM04"]


def test_gap_selector_refuses_when_frozen_tuples_missing(tmp_path):
    """Contract: if frozen_tuples.json is missing, the selector MUST refuse to run."""
    import pytest
    pool = tmp_path / "pool.jsonl"
    mappings = tmp_path / "mappings.jsonl"
    partition = tmp_path / "partition.json"
    _write_jsonl(pool, [])
    _write_jsonl(mappings, [])
    partition.write_text(json.dumps({"held_out": []}))
    with pytest.raises((FileNotFoundError, RuntimeError)):
        select_gap_tuples(pool, mappings, partition, tmp_path / "does-not-exist.json")
