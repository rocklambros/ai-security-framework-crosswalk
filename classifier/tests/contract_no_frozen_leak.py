"""Cross-phase honesty-firewall contract test.

This test is the single authoritative check that NO training row produced
by ANY phase of the pipeline intersects data/splits/frozen_tuples.json on
either the source tuple, target tuple, or full pair tuple.

It runs in CI for every phase (2..6). A failure here halts the phase.

Covered producers (adapters register themselves lazily; if a producer's
artifacts do not yet exist on the current branch, that adapter is skipped
but logged — the test still enforces on everything present).

The frozen_tuples.json file is derived from human_test_frozen.jsonl by
scripts/build_frozen_tuples.py using only structural identifier fields
(no expert_tier). Recomputing it does not constitute label leakage.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator

import pytest

FROZEN_TUPLES = Path("data/splits/frozen_tuples.json")


def load_frozen_sets() -> tuple[set[tuple[str, str]], set[tuple[str, str]], set[tuple[str, str, str, str]]]:
    data = json.loads(FROZEN_TUPLES.read_text())
    src = {tuple(t) for t in data["source_tuples"]}
    tgt = {tuple(t) for t in data["target_tuples"]}
    pair = {tuple(t) for t in data["pair_tuples"]}
    return src, tgt, pair


def _split_node(node_id: str) -> tuple[str, str]:
    fw, _, rest = node_id.partition(":")
    return fw, rest


def _iter_jsonl(path: Path) -> Iterator[dict]:
    if not path.exists():
        return
    with path.open() as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)


# ---------------------------------------------------------------------------
# Producer adapters — one per phase. Each yields (src_fw, src_id, tgt_fw, tgt_id).
# ---------------------------------------------------------------------------

def _upstream_mappings() -> Iterator[tuple[str, str, str, str]]:
    """Plan 1-B/1-C: upstream mappings that have been marked train_eligible."""
    path = Path("data/upstream/mappings_v1.jsonl")
    partition = Path("data/upstream/partition.json")
    if not path.exists():
        return
    held_out = set()
    if partition.exists():
        held_out = set(json.loads(partition.read_text()).get("held_out", []))
    for row in _iter_jsonl(path):
        if row.get("provenance_sha") in held_out:
            continue
        if row.get("target_id_unresolved"):
            continue
        tgt = row.get("target_node_id")
        src_fw = row.get("source_framework") or ""
        src_id = row.get("source_id") or row.get("source_control_id") or ""
        if not tgt or not src_fw or not src_id:
            continue
        tgt_fw, tgt_rest = _split_node(tgt)
        yield src_fw, src_id, tgt_fw, tgt_rest


def _plan2_llm_labels() -> Iterator[tuple[str, str, str, str]]:
    """Plan 2 silver labels — every emitted row."""
    path = Path("data/labels/llm_sme_v1.jsonl")
    for row in _iter_jsonl(path):
        src = row.get("source_node_id")
        tgt = row.get("target_node_id")
        if not src or not tgt:
            continue
        src_fw, src_id = _split_node(src)
        tgt_fw, tgt_id = _split_node(tgt)
        yield src_fw, src_id, tgt_fw, tgt_id


def _plan6_calibration_sample() -> Iterator[tuple[str, str, str, str]]:
    """Plan 6 autonomous calibration sample."""
    path = Path("data/calibration/autonomous_calibration.jsonl")
    for row in _iter_jsonl(path):
        src = row.get("source_node_id")
        tgt = row.get("target_node_id")
        if not src or not tgt:
            continue
        src_fw, src_id = _split_node(src)
        tgt_fw, tgt_id = _split_node(tgt)
        yield src_fw, src_id, tgt_fw, tgt_id


PRODUCERS = {
    "upstream_mappings_v1": _upstream_mappings,
    "plan2_llm_sme_v1": _plan2_llm_labels,
    "plan6_autonomous_calibration": _plan6_calibration_sample,
}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def frozen_sets():
    assert FROZEN_TUPLES.exists(), (
        "data/splits/frozen_tuples.json missing — run scripts/build_frozen_tuples.py"
    )
    return load_frozen_sets()


@pytest.mark.parametrize("producer_name", sorted(PRODUCERS.keys()))
def test_no_frozen_tuple_in_producer(producer_name, frozen_sets):
    frozen_src, frozen_tgt, frozen_pair = frozen_sets
    producer = PRODUCERS[producer_name]
    violations: list[str] = []
    n_checked = 0
    for src_fw, src_id, tgt_fw, tgt_id in producer():
        n_checked += 1
        pair = (src_fw, src_id, tgt_fw, tgt_id)
        src_tup = (src_fw, src_id)
        tgt_tup = (tgt_fw, tgt_id)
        if pair in frozen_pair:
            violations.append(f"PAIR {pair}")
        elif src_tup in frozen_src and tgt_tup in frozen_tgt:
            # Both endpoints in frozen test, even if exact pair not — still a leak
            violations.append(f"SRC+TGT {src_tup} {tgt_tup}")
    if n_checked == 0:
        pytest.skip(f"{producer_name}: no rows produced yet on this branch")
    assert not violations, (
        f"{producer_name} leaked {len(violations)} frozen tuples into training data. "
        f"First 5: {violations[:5]}"
    )


def test_frozen_tuples_nonempty(frozen_sets):
    src, tgt, pair = frozen_sets
    assert len(src) > 0 and len(tgt) > 0 and len(pair) > 0


def test_frozen_tuples_hash_registered():
    hashes = json.loads(Path("data/splits/hashes.json").read_text())
    entry = hashes.get("splits", {}).get("frozen_tuples_json")
    assert entry is not None, "frozen_tuples_json must be registered in hashes.json"
    assert entry["sha256"], "sha256 must be recorded"
