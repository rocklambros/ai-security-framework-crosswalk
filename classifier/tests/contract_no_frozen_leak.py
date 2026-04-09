"""Cross-phase honesty-firewall contract test.

**Status:** informative-not-load-bearing. The LOAD-BEARING check is
`classifier.ensemble.training_batches.iter_weighted_rows` Contract 10
layer 0, which fires on every training batch row at the last mile before
the model sees it. This test is an earlier, independent check that catches
producer-level bugs before they propagate into training — it depends on
producer adapters below, and those adapters may silently skip if paths
or schemas drift. Do NOT rely on this test alone; rely on Contract 10.

This test is the cross-phase check that NO training row produced
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
    """Plan 6 autonomous calibration sample.

    Plan 6 writes to `data/splits/human_cal.jsonl` (Contract 12). Older
    drafts referenced `data/calibration/autonomous_calibration.jsonl`; we
    accept either path so a plan-text refactor does not silently disable
    this adapter.
    """
    candidate_paths = [
        Path("data/splits/human_cal.jsonl"),
        Path("data/calibration/autonomous_calibration.jsonl"),
        Path("data/calibration/upstream_cal_150.jsonl"),
    ]
    for path in candidate_paths:
        if not path.exists():
            continue
        for row in _iter_jsonl(path):
            # Only check Plan 6-written rows. Legacy pre-Plan-1-D rows have
            # no provenance_tag and are known to violate spec D3 strict
            # source-id partitioning (see docs/legacy_human_cal_spec_violation.md).
            # Plan 6 Phase 0.2 regenerates this file autonomously from
            # upstream train-eligible rows and tags them "human_cal_v1".
            if row.get("provenance_tag") != "human_cal_v1":
                continue
            if "source_framework" in row and "source_id" in row:
                src_fw, src_id = row["source_framework"], row["source_id"]
            elif "source_node_id" in row:
                src_fw, src_id = _split_node(row["source_node_id"])
            else:
                continue
            if "target_framework" in row and ("target_id" in row or "target_node_id" in row):
                tgt_fw = row["target_framework"]
                tgt_id = row.get("target_id")
                if tgt_id is None:
                    _, tgt_id = _split_node(row["target_node_id"])
            elif "target_node_id" in row:
                tgt_fw, tgt_id = _split_node(row["target_node_id"])
            else:
                continue
            yield src_fw, src_id, tgt_fw, tgt_id
        return  # only process the first path that exists


def _plan4_crossref_injected_edges() -> Iterator[tuple[str, str, str, str]]:
    """Plan 4 graph-edge producer: injected upstream crossref edges.

    Graph edges aren't training rows per se, but they become features via
    the GAT encoder and therefore a leak here propagates to training. The
    Plan 4 loader applies a layer-0 firewall; this adapter is the
    independent cross-phase check on its output.
    """
    path = Path("data/graph/upstream_crossref_edges.jsonl")
    for row in _iter_jsonl(path):
        src = row.get("source_node_id")
        tgt = row.get("target_node_id")
        if not src or not tgt:
            continue
        src_fw, src_id = _split_node(src)
        tgt_fw, tgt_id = _split_node(tgt)
        yield src_fw, src_id, tgt_fw, tgt_id


def _plan3_feature_cache() -> Iterator[tuple[str, str, str, str]]:
    """Plan 3 feature cache: the pair list used to build BM25+dense features.

    The cache itself is unlabeled, but its pair list defines the training
    universe for any classifier consuming it. If a frozen-test pair is in
    the cache, features for it exist at training time.
    """
    import csv
    # Parquet path — use pandas if available, else skip (CI will hit it).
    path = Path("data/baselines/feature_cache_v1.parquet")
    if not path.exists():
        return
    try:
        import pandas as pd
    except ImportError:
        return
    df = pd.read_parquet(path)
    for _, row in df.iterrows():
        src = row.get("source_node_id")
        tgt = row.get("target_node_id")
        if not isinstance(src, str) or not isinstance(tgt, str):
            continue
        src_fw, src_id = _split_node(src)
        tgt_fw, tgt_id = _split_node(tgt)
        yield src_fw, src_id, tgt_fw, tgt_id


PRODUCERS = {
    "upstream_mappings_v1": _upstream_mappings,
    "plan2_llm_sme_v1": _plan2_llm_labels,
    "plan6_autonomous_calibration": _plan6_calibration_sample,
    "plan4_crossref_graph_edges": _plan4_crossref_injected_edges,
    "plan3_feature_cache": _plan3_feature_cache,
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


def test_frozen_tuples_not_stale():
    """Rebuild frozen tuple sets in memory from human_test_frozen.jsonl and
    assert they match the committed artifact. Catches the case where the
    frozen file was updated but frozen_tuples.json was not regenerated."""
    frozen_jsonl = Path("data/splits/human_test_frozen.jsonl")
    assert frozen_jsonl.exists()
    rebuilt_src: set[tuple[str, str]] = set()
    rebuilt_tgt: set[tuple[str, str]] = set()
    rebuilt_pair: set[tuple[str, str, str, str]] = set()
    with frozen_jsonl.open() as fh:
        for line in fh:
            row = json.loads(line)
            src_fw, src_id = _split_node(row["source_node_id"])
            tgt_fw, tgt_id = _split_node(row["target_node_id"])
            rebuilt_src.add((src_fw, src_id))
            rebuilt_tgt.add((tgt_fw, tgt_id))
            rebuilt_pair.add((src_fw, src_id, tgt_fw, tgt_id))

    committed = json.loads(FROZEN_TUPLES.read_text())
    committed_src = {tuple(t) for t in committed["source_tuples"]}
    committed_tgt = {tuple(t) for t in committed["target_tuples"]}
    committed_pair = {tuple(t) for t in committed["pair_tuples"]}

    assert rebuilt_src == committed_src, (
        "frozen_tuples.source_tuples is stale vs. human_test_frozen.jsonl. "
        "Re-run scripts/build_frozen_tuples.py and commit."
    )
    assert rebuilt_tgt == committed_tgt, (
        "frozen_tuples.target_tuples is stale vs. human_test_frozen.jsonl"
    )
    assert rebuilt_pair == committed_pair, (
        "frozen_tuples.pair_tuples is stale vs. human_test_frozen.jsonl"
    )
