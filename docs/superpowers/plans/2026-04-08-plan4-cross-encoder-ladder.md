# Plan 4 — Bridge / Graph Enrichment from Upstream Crossrefs

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Date:** 2026-04-08
**Supersedes:** `docs/superpowers/plans/2026-04-07-plan4-cross-encoder-ladder.md` (preserved unchanged on disk; this file is the active Plan 4 under the upstream-integration design)
**Spec driver:** `docs/superpowers/specs/2026-04-08-upstream-crosswalk-integration-design.md` §4.3, §6, §7 Plan 4 bullet, §9
**Depends on:** Plan 1-B (`2026-04-08-plan1b-upstream-crosswalk-integration.md`) — specifically Task 6 (upstream loader) and Task 8 (contamination auditor) must have landed, so `data/upstream/crossrefs_v1.jsonl` and `data/upstream/partition.json` exist on disk.

---

## Goal

Consume the upstream-sourced **gold cross-source-list edges** from `data/upstream/crossrefs_v1.jsonl` (363 rows, LLM↔Agentic↔DSGAI) as **high-confidence prior edges** in the crosswalk knowledge graph, then re-run the bridge and node2vec benchmarks on the enriched graph to measure the lift. Wire up a new **crossref benchmark** that measures cross-source-list mapping quality on held-out crossref edges — this is the first benchmark in the project that directly targets the Session 6–8 weak spot.

Plan 4 is deliberately narrow: it extends graph construction and adds two benchmark targets. It does **not** re-architect the graph, retrain the classifier (Plan 5), or touch the cross-encoder ladder (that Plan-4 scope is preserved verbatim in the 2026-04-07 file and will be picked up again if and only if it is promoted back into scope by a future spec amendment).

## Out of scope (anti-scope)

- The full cross-encoder / 4-rung ladder / Optuna sweep — preserved unchanged in `2026-04-07-plan4-cross-encoder-ladder.md`, not executed here
- Classifier training or provenance-weighted loss (Plan 5)
- Frozen test (`data/splits/human_test_frozen.jsonl`) — never read, never written
- The honesty firewall (`classifier/data/contamination.py`) — Plan 1-B owns it; Plan 4 trusts its `partition.json` output
- Re-specifying the graph schema or rewriting `scripts/build_graph.py` from scratch — we extend, not rewrite
- Tier 2 / Tier 3 candidate-stage retrieval (BM25+bridge, cross-encoder-at-candidate) — deferred to Phase 2/3 per `project_tier23_retrieval_deferred`
- Upstream-schema export or PRs upstream — forbidden by spec §9

## Honesty commitments (carried over)

1. Plan 4 never opens `data/splits/human_test_frozen.jsonl`. A hard `assert "human_test_frozen" not in str(path)` guard is asserted at the top of every script introduced here.
2. Every script calls `classifier.data.splits.verify_hashes()` before reading anything from `data/upstream/` or `data/processed/`. A stale `data/splits/hashes.json` aborts with `HashMismatchError`.
3. The crossref benchmark uses **only** crossref rows whose `provenance_sha` is in `partition.json["held_out"]` — exactly mirroring the contamination partition on the mappings side. Held-out rows are never ingested as prior edges.
4. Benchmarks are reported **before-and-after** on a non-frozen validation split. The numbers are appended to `results/plan4_bridge_lift.json` with git SHA, run UUID, UTC timestamp, and the input artifact hashes. No in-place overwrites.

---

## File Structure

**Plan 4 creates and only touches these paths:**

| Path | Purpose |
|---|---|
| `mapping_engine/engine/upstream_prior_edges.py` | Loader: read `crossrefs_v1.jsonl`, drop held-out rows, emit `make_edge`-compatible dicts with `edge_type="upstream_crossref"`, `confidence="authoritative"`, `provenance="upstream_crossref_v1"` |
| `mapping_engine/tests/test_upstream_prior_edges.py` | Unit tests: held-out filter, canonical node-id resolution, edge dedup against existing graph |
| `scripts/build_graph.py` | Extend only: new helper `inject_upstream_crossref_edges(nodes, edges, warnings)` called after `create_cross_framework_category_edges` and before `validate_and_fix`. No behavior change when the file is absent (graceful skip + warning). |
| `mapping_engine/scripts/benchmark_bridge_lift.py` | Run bridge benchmark twice (with/without crossref edges) on the non-frozen validation split; write `results/plan4_bridge_lift.json` |
| `mapping_engine/scripts/benchmark_node2vec_lift.py` | Retrain node2vec on the enriched graph; run node2vec benchmark twice (baseline vs enriched); append to `results/plan4_node2vec_lift.json` |
| `mapping_engine/scripts/benchmark_crossref.py` | New eval target (§6 spec): measure MRR / Hit@1 / Hit@5 on held-out crossref edges as a ranking task (source node → ranked list of target nodes within the same target source-list) |
| `mapping_engine/tests/test_benchmark_crossref.py` | Smoke test on a 3-row fixture asserting the metric math (perfect ranker → MRR 1.0, inverse ranker → known value) |
| `results/plan4_bridge_lift.json` | Before/after bridge metrics (append-only, one row per run) |
| `results/plan4_node2vec_lift.json` | Before/after node2vec metrics (append-only) |
| `results/plan4_crossref_benchmark.json` | Crossref benchmark results (append-only) |
| `docs/plan4_bridge_lift_report.md` | Human-readable one-pager: before/after tables + interpretation |

**Do not modify** anything under `data/splits/`, `data/labels/`, `classifier/data/contamination.py`, `classifier/data/upstream_loader.py`, `classifier/scripts/build_upstream.py`, `third_party/genai-crosswalk/`, or the 2026-04-07 plan file.

---

## Cross-plan contracts honored

- **Contract 1 — `verify_hashes()` at entry.** Every new script calls `classifier.data.splits.verify_hashes()` before reading anything. Stale hashes abort.
- **Contract 2 — frozen-test firewall.** Hard path assert at script top: `assert "human_test_frozen" not in ",".join(sys.argv)`.
- **Contract 3 — never overwrite.** All `results/plan4_*.json` files are append-only JSONL-of-rows with `{run_id, utc, git_sha, input_hashes, metrics}`; writes go through a tiny `append_row()` helper that opens in `"a"` mode.
- **Contract 5 (from 2026-04-07 Plan 4) — v1_frozen labels only.** Still honored: the crossref benchmark reads only `data/upstream/crossrefs_v1.jsonl` + `partition.json`; no label files are opened at all.
- **Contract 8 (new) — upstream crossref edges are typed and traceable.** Every injected edge carries `edge_type="upstream_crossref"`, `provenance="upstream_crossref_v1"`, `confidence="authoritative"`, and the original `provenance_sha` from `crossrefs_v1.jsonl` in its `notes` field. This makes the enriched graph trivially filterable back to the pre-upstream state for before/after A/B runs.

---

## Phase A — Upstream prior-edge loader

### Task A1: Write the loader test first

**Files:**
- Create: `mapping_engine/tests/test_upstream_prior_edges.py`

- [ ] **Step 1: Write the test**

```python
# mapping_engine/tests/test_upstream_prior_edges.py
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
    edges = load_upstream_prior_edges(crossrefs, partition, present_node_ids=present)

    assert len(edges) == 1
    e = edges[0]
    assert e["source_node_id"] == "owasp_agentic:ASI01"
    assert e["target_node_id"] == "owasp_llm:LLM01"
    assert e["edge_type"] == "upstream_crossref"
    assert e["provenance"] == "upstream_crossref_v1"
    assert e["confidence"] == "authoritative"
    assert "aaa" in (e.get("notes") or "")


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
    edges = load_upstream_prior_edges(crossrefs, partition, present_node_ids=present)
    assert edges == []


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
    edges = load_upstream_prior_edges(
        crossrefs, partition, present_node_ids=present, warnings=warnings
    )
    assert edges == []
    assert any("DSGAI99" in w for w in warnings)
```

Run: `pytest mapping_engine/tests/test_upstream_prior_edges.py -q`
Expected: 3 failures with `ModuleNotFoundError` (module does not exist yet).

### Task A2: Implement the loader

**Files:**
- Create: `mapping_engine/engine/upstream_prior_edges.py`

- [ ] **Step 1: Write the module**

```python
# mapping_engine/engine/upstream_prior_edges.py
"""Load upstream crossref rows as high-confidence prior edges for the graph.

Consumes ``data/upstream/crossrefs_v1.jsonl`` (produced by Plan 1-B
``classifier.scripts.build_upstream``) and ``data/upstream/partition.json``
(produced by Plan 1-B ``classifier.scripts.run_contamination_audit``).

Held-out rows (per the strict contamination partition) are filtered out
before any edges are emitted. Unresolved rows (``target_id_unresolved=True``)
and rows whose source or target node is absent from the current nodes.json
are dropped and collected into an optional warnings list.

Every emitted edge carries:

    edge_type  = "upstream_crossref"
    provenance = "upstream_crossref_v1"
    confidence = "authoritative"
    notes      = "provenance_sha={sha}"

so that downstream code can trivially partition the graph back to its
pre-upstream state (``[e for e in edges if e.get("edge_type") != "upstream_crossref"]``)
for before/after A-B benchmarks.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable


def load_upstream_prior_edges(
    crossrefs_path: str | Path,
    partition_path: str | Path,
    present_node_ids: Iterable[str],
    warnings: list[str] | None = None,
) -> list[dict]:
    """Return a list of edge dicts ready to pass to ``add_edge``.

    Parameters
    ----------
    crossrefs_path : str | Path
        Path to ``data/upstream/crossrefs_v1.jsonl``.
    partition_path : str | Path
        Path to ``data/upstream/partition.json``. Must contain a
        ``held_out`` list of provenance_sha values.
    present_node_ids : Iterable[str]
        Set of node_ids currently in the graph. Rows referencing a
        missing source or target node are dropped.
    warnings : list[str] | None
        Optional accumulator. Skipped-row reasons are appended here.
    """
    present = set(present_node_ids)
    partition = json.loads(Path(partition_path).read_text())
    held_out = set(partition.get("held_out") or [])

    out: list[dict] = []
    with Path(crossrefs_path).open("r", encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            sha = row.get("provenance_sha") or ""
            if sha in held_out:
                continue
            if row.get("target_id_unresolved"):
                if warnings is not None:
                    warnings.append(
                        f"[upstream_prior_edges] line {line_no}: target_id_unresolved "
                        f"{row.get('target_framework')}:{row.get('target_id')}"
                    )
                continue
            src_fw = row["source_framework"]
            src_id = row["source_id"]
            src_node = f"{src_fw}:{src_id}"
            tgt_node = row.get("target_node_id") or f"{row['target_framework']}:{row['target_id']}"
            if src_node not in present:
                if warnings is not None:
                    warnings.append(
                        f"[upstream_prior_edges] line {line_no}: source node "
                        f"{src_node} not present in graph"
                    )
                continue
            if tgt_node not in present:
                if warnings is not None:
                    warnings.append(
                        f"[upstream_prior_edges] line {line_no}: target node "
                        f"{tgt_node} not present in graph"
                    )
                continue
            out.append(
                {
                    "source_node_id": src_node,
                    "target_node_id": tgt_node,
                    "source_framework": src_fw,
                    "target_framework": row["target_framework"],
                    "rationale_code": "upstream_crossref",
                    "rationale_label": "Upstream source-list crossref",
                    "relevance": "related",
                    "confidence": "authoritative",
                    "provenance": "upstream_crossref_v1",
                    "edge_type": "upstream_crossref",
                    "notes": f"provenance_sha={sha}",
                    "score": None,
                    "signals": None,
                }
            )
    return out
```

- [ ] **Step 2: Run the tests**

Run: `pytest mapping_engine/tests/test_upstream_prior_edges.py -q`
Expected: `3 passed`.

---

## Phase B — Inject crossref edges into the graph build

### Task B1: Extend `scripts/build_graph.py`

**Files:**
- Modify: `scripts/build_graph.py`

- [ ] **Step 1: Add the injection helper just above `create_stub_nodes`**

Insert verbatim after `create_cross_framework_category_edges` and before `create_stub_nodes`:

```python
def inject_upstream_crossref_edges(nodes, edges, warnings):
    """Inject upstream_crossref_v1 prior edges into the working edge dict.

    Gracefully skips if either input file is absent. Added edges go
    through ``add_edge`` so dedup + confidence ordering is honored.
    """
    from pathlib import Path

    crossrefs_path = Path("data/upstream/crossrefs_v1.jsonl")
    partition_path = Path("data/upstream/partition.json")
    if not crossrefs_path.exists() or not partition_path.exists():
        warnings.append(
            "inject_upstream_crossref_edges: upstream artifacts not found; skipping"
        )
        return 0

    from mapping_engine.engine.upstream_prior_edges import load_upstream_prior_edges

    present = set(nodes.keys())
    local_warnings: list[str] = []
    new_edges = load_upstream_prior_edges(
        crossrefs_path, partition_path, present_node_ids=present, warnings=local_warnings
    )
    warnings.extend(local_warnings)

    added = 0
    for raw in new_edges:
        e = make_edge(
            source_node_id=raw["source_node_id"],
            target_node_id=raw["target_node_id"],
            rationale_code=raw["rationale_code"],
            rationale_label=raw["rationale_label"],
            relevance=raw["relevance"],
            confidence=raw["confidence"],
            provenance=raw["provenance"],
        )
        # Preserve upstream-specific metadata that make_edge does not know about.
        e["edge_type"] = "upstream_crossref"
        e["notes"] = raw["notes"]
        before = len(edges)
        add_edge(edges, e)
        if len(edges) > before or edges[edge_key(e)] is e:
            added += 1

    warnings.append(
        f"inject_upstream_crossref_edges: added {added} upstream_crossref edges "
        f"(skipped {len(local_warnings)} rows)"
    )
    return added
```

- [ ] **Step 2: Call it in `main()` immediately after `create_cross_framework_category_edges`**

Locate the line in `main()` that calls `create_cross_framework_category_edges(nodes, edges, warnings)` and insert directly below it:

```python
    inject_upstream_crossref_edges(nodes, edges, warnings)
```

- [ ] **Step 3: Rebuild the graph**

Run: `python scripts/build_graph.py`
Expected: the tail of stdout contains a line like
`inject_upstream_crossref_edges: added N upstream_crossref edges (skipped M rows)`
with `N` on the order of 300 (363 total minus held-out minus any unresolved/missing-node rows). `data/processed/edges.json` is rewritten. `data/processed/nodes.json` is unchanged.

- [ ] **Step 4: Quick sanity check**

Run:
```
python - <<'PY'
import json
edges = json.loads(open("data/processed/edges.json").read())
up = [e for e in edges if e.get("edge_type") == "upstream_crossref"]
print("total_edges", len(edges), "upstream_crossref", len(up))
assert len(up) > 0
assert all(e.get("confidence") == "authoritative" for e in up)
PY
```
Expected: `total_edges <N> upstream_crossref <M>` with M > 0; assertions pass.

---

## Phase C — Bridge benchmark lift (before/after)

### Task C1: `benchmark_bridge_lift.py`

**Files:**
- Create: `mapping_engine/scripts/benchmark_bridge_lift.py`

- [ ] **Step 1: Write the script**

```python
# mapping_engine/scripts/benchmark_bridge_lift.py
"""Before-and-after bridge benchmark on the non-frozen validation split.

Runs the same bridge benchmark twice against the currently built graph:

    1. Baseline — strip upstream_crossref edges in memory
    2. Enriched — keep them

and appends one row to ``results/plan4_bridge_lift.json`` with both
metric dicts, the git SHA, UTC timestamp, and input-artifact hashes.

Honesty:
    * Asserts ``human_test_frozen`` never appears in argv.
    * Calls ``classifier.data.splits.verify_hashes()`` before reading data.
    * Reads only ``data/processed/nodes.json`` + ``edges.json`` and the
      non-frozen validation split.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import networkx as nx

from classifier.data.splits import verify_hashes
from mapping_engine.engine.graph import load_graph
from mapping_engine.engine.bridge import graph_bridge_scores


RESULTS_PATH = Path("results/plan4_bridge_lift.json")
VAL_SPLIT = Path("data/splits/human_val.jsonl")  # non-frozen


def _sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _git_sha() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"


def _strip_upstream_crossref_edges(G: nx.DiGraph) -> nx.DiGraph:
    H = G.copy()
    to_remove = [
        (u, v) for u, v, d in H.edges(data=True) if d.get("edge_type") == "upstream_crossref"
    ]
    H.remove_edges_from(to_remove)
    return H


def _load_val_pairs(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text().splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _metrics_for_graph(G: nx.DiGraph, pairs: list[dict]) -> dict:
    """Compute MRR and Hit@{1,5,20} using bridge_scores as the ranker.

    For each (source, target) gold pair in ``pairs``, bridge-rank every
    node in the target framework and record the rank of the gold target.
    """
    from collections import defaultdict

    by_tgt_fw: dict[str, list[str]] = defaultdict(list)
    for nid, d in G.nodes(data=True):
        fw = d.get("framework")
        if fw:
            by_tgt_fw[fw].append(nid)

    reciprocal_ranks: list[float] = []
    hits = {1: 0, 5: 0, 20: 0}
    considered = 0
    for row in pairs:
        src = row["source_node_id"]
        gold = row["target_node_id"]
        tgt_fw = row.get("target_framework") or gold.split(":")[0]
        tgt_nodes = by_tgt_fw.get(tgt_fw, [])
        if src not in G or gold not in tgt_nodes:
            continue
        bridge = graph_bridge_scores(G, [src], tgt_nodes, {})
        # bridge is shape (1, len(tgt_nodes)); rank the gold target
        scores = list(zip(tgt_nodes, bridge[0]))
        scores.sort(key=lambda t: t[1], reverse=True)
        rank = next((i + 1 for i, (n, _) in enumerate(scores) if n == gold), None)
        if rank is None:
            continue
        considered += 1
        reciprocal_ranks.append(1.0 / rank)
        for k in hits:
            if rank <= k:
                hits[k] += 1

    n = max(considered, 1)
    return {
        "n_pairs_scored": considered,
        "mrr": sum(reciprocal_ranks) / n,
        "hit_at_1": hits[1] / n,
        "hit_at_5": hits[5] / n,
        "hit_at_20": hits[20] / n,
    }


def main() -> None:
    assert "human_test_frozen" not in ",".join(sys.argv), "Contract 2: frozen test is off limits"
    parser = argparse.ArgumentParser()
    parser.add_argument("--val", default=str(VAL_SPLIT))
    args = parser.parse_args()

    verify_hashes()

    nodes_path = Path("data/processed/nodes.json")
    edges_path = Path("data/processed/edges.json")
    val_path = Path(args.val)

    G_enriched = load_graph(nodes_path, edges_path)
    G_baseline = _strip_upstream_crossref_edges(G_enriched)
    pairs = _load_val_pairs(val_path)

    enriched = _metrics_for_graph(G_enriched, pairs)
    baseline = _metrics_for_graph(G_baseline, pairs)

    row = {
        "run_id": str(uuid.uuid4()),
        "utc": datetime.now(timezone.utc).isoformat(),
        "git_sha": _git_sha(),
        "input_hashes": {
            "nodes.json": _sha256(nodes_path),
            "edges.json": _sha256(edges_path),
            "val_split": _sha256(val_path),
        },
        "baseline": baseline,
        "enriched": enriched,
        "delta": {k: enriched[k] - baseline[k] for k in ("mrr", "hit_at_1", "hit_at_5", "hit_at_20")},
    }
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with RESULTS_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, sort_keys=True) + "\n")
    print(json.dumps(row, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run it**

Run: `python -m mapping_engine.scripts.benchmark_bridge_lift`
Expected: a JSON row prints to stdout; `results/plan4_bridge_lift.json` now contains one more line. `enriched.mrr >= baseline.mrr` is the expected direction but is NOT asserted at script level (a regression is a finding, not a crash).

- [ ] **Step 3: Hand-verify**

Inspect the printed JSON. The `delta.mrr` field on the non-frozen val split should be a small positive number. If it is strongly negative (worse than -0.01), stop here and file the finding in `docs/plan4_bridge_lift_report.md` before proceeding to Phase D — this is a real investigation signal, not a known-bad.

---

## Phase D — Node2vec benchmark lift

### Task D1: `benchmark_node2vec_lift.py`

**Files:**
- Create: `mapping_engine/scripts/benchmark_node2vec_lift.py`

- [ ] **Step 1: Write the script**

```python
# mapping_engine/scripts/benchmark_node2vec_lift.py
"""Before-and-after node2vec benchmark on the enriched graph.

1. Train node2vec on the baseline graph (upstream_crossref edges stripped).
2. Train node2vec on the enriched graph (all edges).
3. Re-use ``mapping_engine.scripts.benchmark_node2vec`` to score each model
   on the non-frozen validation split.
4. Append one row to ``results/plan4_node2vec_lift.json``.

Honesty guarantees match Phase C.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from classifier.data.splits import verify_hashes
from mapping_engine.engine.graph import load_graph
from mapping_engine.scripts.train_node2vec import train_and_save
from mapping_engine.scripts.benchmark_node2vec import score_pairs


RESULTS_PATH = Path("results/plan4_node2vec_lift.json")
VAL_SPLIT = Path("data/splits/human_val.jsonl")


def _sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _git_sha() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"


def _write_filtered_edges(src_edges: Path, dst_edges: Path, keep_upstream: bool) -> None:
    edges = json.loads(src_edges.read_text())
    if not keep_upstream:
        edges = [e for e in edges if e.get("edge_type") != "upstream_crossref"]
    dst_edges.write_text(json.dumps(edges))


def main() -> None:
    assert "human_test_frozen" not in ",".join(sys.argv), "Contract 2: frozen test is off limits"
    parser = argparse.ArgumentParser()
    parser.add_argument("--val", default=str(VAL_SPLIT))
    parser.add_argument("--workdir", default="runs/plan4_node2vec")
    args = parser.parse_args()

    verify_hashes()

    workdir = Path(args.workdir)
    workdir.mkdir(parents=True, exist_ok=True)

    nodes_path = Path("data/processed/nodes.json")
    edges_path = Path("data/processed/edges.json")
    val_path = Path(args.val)

    baseline_edges = workdir / "edges_baseline.json"
    enriched_edges = workdir / "edges_enriched.json"
    _write_filtered_edges(edges_path, baseline_edges, keep_upstream=False)
    _write_filtered_edges(edges_path, enriched_edges, keep_upstream=True)

    G_baseline = load_graph(nodes_path, baseline_edges)
    G_enriched = load_graph(nodes_path, enriched_edges)

    baseline_vecs = workdir / "baseline_vecs.npy"
    baseline_vocab = workdir / "baseline_vocab.json"
    enriched_vecs = workdir / "enriched_vecs.npy"
    enriched_vocab = workdir / "enriched_vocab.json"

    train_and_save(G_baseline, baseline_vecs, baseline_vocab)
    train_and_save(G_enriched, enriched_vecs, enriched_vocab)

    pairs = [json.loads(l) for l in val_path.read_text().splitlines() if l.strip()]
    baseline_metrics = score_pairs(baseline_vecs, baseline_vocab, pairs)
    enriched_metrics = score_pairs(enriched_vecs, enriched_vocab, pairs)

    row = {
        "run_id": str(uuid.uuid4()),
        "utc": datetime.now(timezone.utc).isoformat(),
        "git_sha": _git_sha(),
        "input_hashes": {
            "nodes.json": _sha256(nodes_path),
            "edges.json": _sha256(edges_path),
            "val_split": _sha256(val_path),
        },
        "baseline": baseline_metrics,
        "enriched": enriched_metrics,
        "delta": {
            k: enriched_metrics.get(k, 0.0) - baseline_metrics.get(k, 0.0)
            for k in baseline_metrics
        },
    }
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with RESULTS_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, sort_keys=True) + "\n")
    print(json.dumps(row, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
```

Note: `train_and_save` and `score_pairs` are the helper entry points already factored out in `train_node2vec.py` and `benchmark_node2vec.py`. If they are not yet factored, the first step of this task is to extract them as pure functions (moving, not rewriting) with matching signatures — that refactor is in-scope and is the only edit permitted to those two files.

- [ ] **Step 2: Run it**

Run: `python -m mapping_engine.scripts.benchmark_node2vec_lift`
Expected: two node2vec training runs complete, one JSON row appended, stdout shows baseline vs enriched metric dicts and deltas. As with Phase C, direction is expected-positive but not asserted.

---

## Phase E — Crossref benchmark (new primary eval, §6 spec bullet 4)

### Task E1: Benchmark test first

**Files:**
- Create: `mapping_engine/tests/test_benchmark_crossref.py`

- [ ] **Step 1: Write the test**

```python
# mapping_engine/tests/test_benchmark_crossref.py
"""Smoke test for the crossref ranking benchmark math."""
from __future__ import annotations

import math

from mapping_engine.scripts.benchmark_crossref import rank_metrics


def test_perfect_ranker() -> None:
    # Three queries, gold always at rank 1.
    ranks = [1, 1, 1]
    m = rank_metrics(ranks)
    assert m["mrr"] == 1.0
    assert m["hit_at_1"] == 1.0
    assert m["hit_at_5"] == 1.0


def test_inverse_ranker() -> None:
    # Gold always at rank 10 out of 10.
    ranks = [10, 10, 10]
    m = rank_metrics(ranks)
    assert math.isclose(m["mrr"], 0.1, abs_tol=1e-9)
    assert m["hit_at_1"] == 0.0
    assert m["hit_at_5"] == 0.0


def test_mixed() -> None:
    ranks = [1, 2, 10]
    m = rank_metrics(ranks)
    assert math.isclose(m["mrr"], (1.0 + 0.5 + 0.1) / 3, abs_tol=1e-9)
    assert math.isclose(m["hit_at_1"], 1 / 3, abs_tol=1e-9)
    assert math.isclose(m["hit_at_5"], 2 / 3, abs_tol=1e-9)
```

Run: `pytest mapping_engine/tests/test_benchmark_crossref.py -q`
Expected: 3 `ModuleNotFoundError` failures.

### Task E2: `benchmark_crossref.py`

**Files:**
- Create: `mapping_engine/scripts/benchmark_crossref.py`

- [ ] **Step 1: Write the script**

```python
# mapping_engine/scripts/benchmark_crossref.py
"""Cross-source-list mapping benchmark on held-out upstream crossrefs.

Defined by `2026-04-08-upstream-crosswalk-integration-design.md` §6 bullet 4.

Measures whether the crosswalk engine can recover upstream LLM↔Agentic↔DSGAI
gold edges that were held out by the contamination partition. Evaluation
uses the bridge score as the ranker (same as Phase C) on the enriched
graph — the enriched graph is free of held-out rows by construction, so
this is a clean test.

Honesty:
    * Asserts ``human_test_frozen`` never appears in argv.
    * Calls ``verify_hashes`` before any reads.
    * Reads only ``data/upstream/crossrefs_v1.jsonl``, ``partition.json``,
      and ``data/processed/{nodes,edges}.json``. Never opens any
      ``data/splits/human_*`` files.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from classifier.data.splits import verify_hashes
from mapping_engine.engine.graph import load_graph
from mapping_engine.engine.bridge import graph_bridge_scores


RESULTS_PATH = Path("results/plan4_crossref_benchmark.json")


def rank_metrics(ranks: list[int]) -> dict:
    if not ranks:
        return {"n": 0, "mrr": 0.0, "hit_at_1": 0.0, "hit_at_5": 0.0, "hit_at_20": 0.0}
    n = len(ranks)
    mrr = sum(1.0 / r for r in ranks) / n
    return {
        "n": n,
        "mrr": mrr,
        "hit_at_1": sum(1 for r in ranks if r <= 1) / n,
        "hit_at_5": sum(1 for r in ranks if r <= 5) / n,
        "hit_at_20": sum(1 for r in ranks if r <= 20) / n,
    }


def _sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _git_sha() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"


def main() -> None:
    assert "human_test_frozen" not in ",".join(sys.argv), "Contract 2: frozen test is off limits"
    parser = argparse.ArgumentParser()
    parser.add_argument("--crossrefs", default="data/upstream/crossrefs_v1.jsonl")
    parser.add_argument("--partition", default="data/upstream/partition.json")
    args = parser.parse_args()

    verify_hashes()

    nodes_path = Path("data/processed/nodes.json")
    edges_path = Path("data/processed/edges.json")
    crossrefs_path = Path(args.crossrefs)
    partition_path = Path(args.partition)

    G = load_graph(nodes_path, edges_path)

    by_fw: dict[str, list[str]] = defaultdict(list)
    for nid, d in G.nodes(data=True):
        fw = d.get("framework")
        if fw:
            by_fw[fw].append(nid)

    partition = json.loads(partition_path.read_text())
    held_out = set(partition.get("held_out") or [])
    if not held_out:
        print("[benchmark_crossref] WARNING: empty held_out set; benchmark will be empty")

    ranks: list[int] = []
    skipped = 0
    for line in crossrefs_path.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("provenance_sha") not in held_out:
            continue
        if row.get("target_id_unresolved"):
            skipped += 1
            continue
        src = f"{row['source_framework']}:{row['source_id']}"
        gold = row.get("target_node_id") or f"{row['target_framework']}:{row['target_id']}"
        tgt_fw = row["target_framework"]
        candidates = by_fw.get(tgt_fw, [])
        if src not in G or gold not in candidates:
            skipped += 1
            continue
        bridge = graph_bridge_scores(G, [src], candidates, {})
        scored = sorted(zip(candidates, bridge[0]), key=lambda t: t[1], reverse=True)
        rank = next((i + 1 for i, (n, _) in enumerate(scored) if n == gold), None)
        if rank is None:
            skipped += 1
            continue
        ranks.append(rank)

    metrics = rank_metrics(ranks)
    metrics["skipped"] = skipped

    row_out = {
        "run_id": str(uuid.uuid4()),
        "utc": datetime.now(timezone.utc).isoformat(),
        "git_sha": _git_sha(),
        "input_hashes": {
            "nodes.json": _sha256(nodes_path),
            "edges.json": _sha256(edges_path),
            "crossrefs_v1.jsonl": _sha256(crossrefs_path),
            "partition.json": _sha256(partition_path),
        },
        "metrics": metrics,
    }
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with RESULTS_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row_out, sort_keys=True) + "\n")
    print(json.dumps(row_out, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the unit test**

Run: `pytest mapping_engine/tests/test_benchmark_crossref.py -q`
Expected: `3 passed`.

- [ ] **Step 3: Run the benchmark**

Run: `python -m mapping_engine.scripts.benchmark_crossref`
Expected: one JSON row printed and appended to `results/plan4_crossref_benchmark.json`. If `held_out` is empty (partition produced no crossref hold-outs under rule 1), the script still runs and prints `n=0` — that is a valid finding and must be documented in the report.

---

## Phase F — Report and self-review

### Task F1: Write the report

**Files:**
- Create: `docs/plan4_bridge_lift_report.md`

- [ ] **Step 1: Fill in the report from the three results files**

Required sections (one line per bullet, filled in from the JSON rows):

```markdown
# Plan 4 — Bridge / Graph Enrichment Report

Date:          <UTC timestamp>
Git SHA:       <short SHA>
Upstream pin:  <from third_party/genai-crosswalk/MANIFEST.json upstream_commit_sha>

## Graph delta

- upstream_crossref edges injected: <N>
- skipped (held out): <H>
- skipped (unresolved / missing node): <M>
- total edges before: <E0>
- total edges after:  <E1>

## Bridge benchmark (non-frozen val, n=<n>)

| metric   | baseline | enriched | delta |
|----------|---------:|---------:|------:|
| MRR      |     ...  |     ...  |   ... |
| Hit@1    |     ...  |     ...  |   ... |
| Hit@5    |     ...  |     ...  |   ... |
| Hit@20   |     ...  |     ...  |   ... |

## Node2vec benchmark (non-frozen val, n=<n>)

Same table shape.

## Crossref benchmark (held-out crossref edges, n=<n>)

| metric | value |
|--------|------:|
| MRR    |  ...  |
| Hit@1  |  ...  |
| Hit@5  |  ...  |
| Hit@20 |  ...  |

## Interpretation

- <1–2 sentences on whether the expected lift materialized>
- <1 sentence on anything surprising or regressive>
- <Explicit statement that human_test_frozen was not read by any script in this plan>
```

### Task F2: Self-review checklist

- [ ] `rg -n "human_test_frozen" mapping_engine/scripts/benchmark_bridge_lift.py mapping_engine/scripts/benchmark_node2vec_lift.py mapping_engine/scripts/benchmark_crossref.py mapping_engine/engine/upstream_prior_edges.py` returns **only** the `assert "human_test_frozen" not in ...` guard lines.
- [ ] `rg -n "upstream_crossref" data/processed/edges.json` returns ≥ 1 hit.
- [ ] `pytest mapping_engine/tests/test_upstream_prior_edges.py mapping_engine/tests/test_benchmark_crossref.py -q` → all green.
- [ ] `python scripts/build_graph.py` is idempotent: running it twice produces byte-identical `edges.json` (sanity via `sha256sum`).
- [ ] `results/plan4_bridge_lift.json`, `results/plan4_node2vec_lift.json`, and `results/plan4_crossref_benchmark.json` each gained exactly one line.
- [ ] No file under `classifier/data/`, `data/labels/`, `data/splits/`, `third_party/genai-crosswalk/`, or `docs/superpowers/plans/2026-04-07-plan4-cross-encoder-ladder.md` was modified.
- [ ] `git status --porcelain` contains only the Plan 4 file set declared in the File Structure section.
- [ ] `docs/plan4_bridge_lift_report.md` is filled in with actual numbers, not placeholder ellipses.
- [ ] The 2026-04-07 cross-encoder-ladder plan file is byte-identical to its pre-Plan-4 version (verify with `git diff --stat docs/superpowers/plans/2026-04-07-plan4-cross-encoder-ladder.md`).

---

## Risks & mitigations specific to this plan

| Risk | Mitigation |
|---|---|
| `crossrefs_v1.jsonl` uses node ids absent from `nodes.json` (e.g. DSGAI not yet ingested) | Loader drops the row with a warning and the report shows the skipped count; if DSGAI nodes are missing entirely, block on Plan 1-B Task 4 (DSGAI ingester) rather than partially injecting |
| Bridge metric regresses on enrichment (high-confidence edges shift the graph centroid the wrong way) | Report, don't mask. The script does not assert direction; Phase F Task F1 explicitly requires interpretation of regressions. If a regression is real, Plan 5 will weight `upstream_crossref` edges lower via `edge_weight_by_type` config — a single-line hook that already exists in `bridge.py`. |
| Node2vec non-determinism muddies the A/B | Use a fixed seed in `train_and_save` (already pinned in `train_node2vec.py`) and run each condition once; don't bootstrap in this plan — that is Plan 5 work |
| Crossref held-out set is empty because partition rule 1 put all crossref provenance_shas on the train-eligible side | The benchmark then reports `n=0`. That is still a valid, honest result; the report must call it out, and the remediation (expand held-out rule to crossrefs_v1 explicitly) belongs in a follow-on spec amendment, not in this plan |
| `scripts/build_graph.py` is rerun in CI and Plan 1-B upstream artifacts are absent | Injection is wrapped in `if not crossrefs_path.exists()` with a warning; the graph build remains green in all environments |

---

## Done criteria

Plan 4 is complete when:

1. `mapping_engine/engine/upstream_prior_edges.py` exists with tests green
2. `scripts/build_graph.py` injects `upstream_crossref` edges and the rebuilt `data/processed/edges.json` contains ≥ 1 such edge
3. `results/plan4_bridge_lift.json` has at least one row with `baseline` and `enriched` metric blocks
4. `results/plan4_node2vec_lift.json` has at least one row
5. `results/plan4_crossref_benchmark.json` has at least one row
6. `docs/plan4_bridge_lift_report.md` exists and is filled in with real numbers
7. Every item in the Phase F self-review checklist is checked
8. `git diff docs/superpowers/plans/2026-04-07-plan4-cross-encoder-ladder.md` is empty (the prior plan file is untouched)
9. `git diff data/splits/human_test_frozen.jsonl data/splits/hashes.json` is empty (frozen test and split hashes are untouched)
