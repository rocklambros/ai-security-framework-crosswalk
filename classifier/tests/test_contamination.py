"""Pre-registered honesty firewall.

DO NOT skip, xfail, or disable any assertion in this file. The orchestrator's
"never disable a failing test" rule applies here with the tightest possible
interpretation. If this test fails, the partition is broken — fix the partition,
not the test.
"""
import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
PARTITION = REPO / "data" / "upstream" / "partition.json"
UPSTREAM = REPO / "data" / "upstream" / "mappings_v1.jsonl"
FROZEN = REPO / "data" / "splits" / "human_test_frozen.jsonl"


def _load_partition() -> dict:
    assert PARTITION.exists(), (
        "data/upstream/partition.json missing — run "
        "classifier/scripts/run_contamination_audit.py before running this test"
    )
    return json.loads(PARTITION.read_text())


def test_partition_disjoint():
    p = _load_partition()
    eligible = set(p["train_eligible"])
    held = set(p["held_out"])
    assert eligible.isdisjoint(held), "train_eligible and held_out overlap — partition is broken"
    assert len(eligible) + len(held) == p["upstream_total"], "partition does not cover all rows"


def test_held_out_provenance_shas_never_appear_in_training_loader():
    p = _load_partition()
    upstream_src_ids = set()
    with open(UPSTREAM) as f:
        for line in f:
            r = json.loads(line)
            upstream_src_ids.add((r["source_framework"], r["source_id"]))
    if any(fw in ("owasp_llm", "owasp_agentic") for fw, _ in upstream_src_ids):
        assert p["held_out_count"] > 0, (
            "upstream contains LLM/Agentic source_ids that are in the frozen test, "
            "but held_out_count is 0 — the partition is silently broken"
        )


def test_no_held_out_row_matches_a_train_eligible_full_tuple():
    p = _load_partition()
    held = set(p["held_out"])
    eligible = set(p["train_eligible"])

    by_sha: dict[str, dict] = {}
    with open(UPSTREAM) as f:
        for line in f:
            r = json.loads(line)
            by_sha[r["provenance_sha"]] = r

    held_full = {
        (r["source_framework"], r["source_id"], r["target_framework"], r.get("target_control_id") or "")
        for sha, r in by_sha.items() if sha in held
    }
    elig_full = {
        (r["source_framework"], r["source_id"], r["target_framework"], r.get("target_control_id") or "")
        for sha, r in by_sha.items() if sha in eligible
    }
    overlap = held_full & elig_full
    assert not overlap, f"full-tuple collision between held_out and train_eligible: {list(overlap)[:5]}"
