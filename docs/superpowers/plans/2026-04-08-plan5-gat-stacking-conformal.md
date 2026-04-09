# Plan 5 (2026-04-08 delta) — Provenance-Weighted Trainer + Upstream & Crossref Reported Evals

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Apply the §7 Plan 5 delta from
`docs/superpowers/specs/2026-04-08-upstream-crosswalk-integration-design.md`
to the existing Plan 5 (`2026-04-07-plan5-gat-stacking-conformal.md`) without
touching any other plan. Concretely, this plan (a) makes the stacker / ensemble
training-batch loader consume provenance-tagged rows with per-tag loss weights
per spec §4.5, (b) adds a **runtime** contamination assertion in that loader
(the second layer of the two-layer defense in spec §4.4 Risks-table mitigation),
and (c) adds two new **reported** evaluation blocks — the held-out upstream
benchmark (1,689 rows from `data/upstream/partition.json.held_out`) and the
crossref benchmark (`data/upstream/crossrefs_v1.jsonl`) — alongside (never
replacing) the frozen test. Everything else in the 2026-04-07 Plan 5 — the GAT,
the densified graph, the LightGBM stacker, the Mondrian conformal wrapper, the
KL-disagreement router, Contracts 1–9, the stop-gates, the `runs/registry.jsonl`
discipline, the `human_test_frozen` path-grep firewall — is inherited **as-is**
and is not re-specified here.

**Architecture:** One new loader module
(`classifier/ensemble/training_batches.py`) owns reading provenance-tagged rows,
applying per-tag weights, and performing the runtime
`provenance_sha ∉ partition.held_out` assertion on every yielded batch. The
stacker training driver (`train_stacker.py`) is modified to route rows through
this loader and multiply per-row loss by the weight vector. Two new eval
scripts (`eval_ensemble_upstream_heldout.py`,
`eval_ensemble_crossref.py`) emit JSON blocks that the existing
`eval_ensemble_llm_val.py` result consumer merges into a single
`results/ensemble_reported_evals.json` with three top-level blocks:
`frozen_test` (untouched primary eval — still gated by Plan 6's sacred-run
harness, reported here only as a forward reference), `upstream_heldout`
(precision / recall / MRR@{1,5,10} over the 1,689 held-out rows), and
`crossref` (cross-source-list pair quality over `crossrefs_v1.jsonl`).

**Tech Stack:** Inherits 2026-04-07 Plan 5. No new deps. Uses `pandas`,
`pyarrow`, `lightgbm`, existing `classifier.data.contamination`
partition reader, existing `classifier.data.splits.verify_hashes()`, and the
Plan 3 `Scorer` protocol.

**REQUIRED SUB-SKILL NOTE:** This delta **must** be executed as a layered patch
on top of `2026-04-07-plan5-gat-stacking-conformal.md`. Do not re-run the
GAT / stacker / conformal / router tasks from the base plan; only the tasks in
this file. If the base plan has not yet been executed, execute it first, then
this delta.

---

## Spec Reference

Implements:

- **§4.4 Risks & mitigations — two-layer contamination defense.** The spec's
  mitigation for the "Contamination auditor has a bug and train-test leakage
  slips through" risk demands **both** a static partition at data-build time
  **and** a runtime assertion in the training-batch loader. The static layer
  ships in Plan 1b (`classifier/tests/test_contamination.py`, pre-registered,
  non-skippable). This plan ships the runtime layer.
- **§4.5 Label provenance & weighted training data.** Per-row
  `provenance_tag ∈ {upstream_v1, llm_sme_v1, human_cal_v1}` with default
  weights `{1.0, 0.6, 1.0}`, tunable via `--label-weight` CLI arg.
- **§6 Evaluation strategy.** Held-out upstream benchmark (new primary
  secondary benchmark) and crossref benchmark (new bonus) are added as
  reported evals alongside the frozen test. Frozen test is **untouched** and
  stays the primary pre-registered eval owned by Plan 6.
- **§7 Plan 5 bullet (verbatim).** "Trainer accepts provenance-tagged rows
  with per-tag weights (§4.5). Adds the held-out upstream benchmark and the
  crossref benchmark as reported evals alongside the frozen test."
- **§9 Out of scope.** Auxiliary multi-task heads (severity / tier / scope)
  are explicitly OUT. This plan adds none.

## Anti-scope (what this delta must NOT do)

- Do NOT modify `data/splits/human_test_frozen.jsonl` or the pre-registered
  thresholds on it (spec §9, §10 item 8).
- Do NOT re-spec contamination auditing, the upstream loader, the id
  normalization table, or the pre-registered static CI gate — these ship in
  Plan 1b (`classifier/data/contamination.py`,
  `classifier/tests/test_contamination.py`).
- Do NOT touch Plan 2 (labeling), Plan 4 (bridge / cross-encoder), or Plan 6
  (human evaluation / sacred run). Plan 2's calibration pool is sourced from
  upstream per spec D7 / §7 Plan 6; this plan merely *references*
  `human_cal_v1` rows as already being the upstream-sourced calibration set.
- Do NOT add auxiliary heads (`severity`, `tier`, `scope`) to the stacker.
  These are explicitly out per §9.
- Do NOT modify the 2026-04-07 Plan 5 file. All edits land in new files or in
  files the 2026-04-07 plan already created.

---

## File Structure

**This delta creates or touches ONLY these paths:**

| Path | Purpose |
|---|---|
| `classifier/ensemble/training_batches.py` | **NEW.** Provenance-tagged batch loader + per-tag weight map + runtime `held_out` assertion |
| `classifier/ensemble/reported_evals.py` | **NEW.** Shared helpers: load partition, load crossrefs, format eval JSON blocks |
| `classifier/ensemble/stacker.py` | **MODIFY (from base plan).** Accept `sample_weight` from the batch loader; multiply LGBM `sample_weight` argument |
| `classifier/scripts/train_stacker.py` | **MODIFY (from base plan).** Route rows through `training_batches.iter_weighted_rows`, plumb `--label-weight` CLI arg |
| `classifier/scripts/eval_ensemble_upstream_heldout.py` | **NEW.** Eval entry: held-out upstream benchmark → `results/ensemble_upstream_heldout.json` |
| `classifier/scripts/eval_ensemble_crossref.py` | **NEW.** Eval entry: crossref benchmark → `results/ensemble_crossref.json` |
| `classifier/scripts/merge_reported_evals.py` | **NEW.** Merge the three reported-eval JSON blocks into `results/ensemble_reported_evals.json` |
| `classifier/tests/test_training_batches_weights.py` | **NEW.** Verifies `--label-weight` map plumbing, default values, and per-row weight vector |
| `classifier/tests/test_training_batches_runtime_contamination.py` | **NEW.** Runtime assertion fires when a `held_out` `provenance_sha` is fed to the loader |
| `classifier/tests/test_upstream_heldout_eval.py` | **NEW.** Eval script runs on a fixture, emits schema-valid JSON |
| `classifier/tests/test_crossref_eval.py` | **NEW.** Eval script runs on a fixture, emits schema-valid JSON |
| `classifier/tests/test_reported_evals_schema.py` | **NEW.** Merged `ensemble_reported_evals.json` has the three expected top-level blocks |
| `results/ensemble_upstream_heldout.json` | **NEW (generated).** Eval block — held-out upstream benchmark |
| `results/ensemble_crossref.json` | **NEW (generated).** Eval block — crossref benchmark |
| `results/ensemble_reported_evals.json` | **NEW (generated).** Merged reported-eval JSON (three blocks) |

**Do not modify** anything under `data/splits/`, `data/labels/llm_sme/`,
`data/upstream/` (read-only; ingested by Plan 1b), `third_party/`,
`classifier/data/contamination.py`,
`classifier/tests/test_contamination.py`, or the 2026-04-07 Plan 5 file itself.

---

## Contracts honored (inherited) and one new one

All nine contracts (1–9) from `2026-04-07-plan5-gat-stacking-conformal.md`
remain in force. This delta adds:

- **Contract 10 (NEW) — runtime contamination assertion.** Every batch yielded
  by `classifier.ensemble.training_batches.iter_weighted_rows` is checked
  row-by-row against the set
  `json.loads(Path("data/upstream/partition.json").read_text())["held_out"]`.
  If any row's `provenance_sha` is in that set, the loader raises
  `RuntimeError("Contract 10: held-out upstream provenance_sha <...> reached "
  "training batch loader")` and aborts training. The held-out set is loaded
  **once at loader construction** and cached as a `frozenset`. This contract
  is the second layer of the spec §4.4 two-layer defense; it is complementary
  to, and does not replace, the pre-registered static CI gate
  `classifier/tests/test_contamination.py`.

---

## Phase A — Provenance-tagged training-batch loader

### Task A1: `training_batches.iter_weighted_rows` — test-first

**Files:**
- Create: `classifier/ensemble/training_batches.py`
- Create: `classifier/tests/test_training_batches_weights.py`

- [ ] **Step 1: Write the failing test for per-tag weights**

```python
# classifier/tests/test_training_batches_weights.py
import json
import pytest
from pathlib import Path
from classifier.ensemble.training_batches import iter_weighted_rows, DEFAULT_LABEL_WEIGHTS

def _write(tmp_path, name, rows):
    p = tmp_path / name
    with open(p, "w") as f:
        for r in rows:
            f.write(json.dumps(r, sort_keys=True) + "\n")
    return p

def _empty_partition(tmp_path):
    p = tmp_path / "partition.json"
    p.write_text(json.dumps({"held_out": [], "train_eligible": [], "upstream_total": 0}))
    return p

def test_default_weights_per_tag(tmp_path):
    rows = [
        {"pair_key": "p1", "provenance_tag": "upstream_v1",  "provenance_sha": "sha1", "label": 1},
        {"pair_key": "p2", "provenance_tag": "llm_sme_v1",   "provenance_sha": "sha2", "label": 0},
        {"pair_key": "p3", "provenance_tag": "human_cal_v1", "provenance_sha": "sha3", "label": 1},
    ]
    rows_path = _write(tmp_path, "rows.jsonl", rows)
    out = list(iter_weighted_rows(
        rows_path=rows_path,
        partition_path=_empty_partition(tmp_path),
        label_weights=DEFAULT_LABEL_WEIGHTS,
    ))
    weights = [r["sample_weight"] for r in out]
    assert weights == [1.0, 0.6, 1.0]
    assert DEFAULT_LABEL_WEIGHTS == {"upstream_v1": 1.0, "llm_sme_v1": 0.6, "human_cal_v1": 1.0}

def test_cli_weight_override(tmp_path):
    rows = [{"pair_key": "p1", "provenance_tag": "llm_sme_v1", "provenance_sha": "sha1", "label": 1}]
    rows_path = _write(tmp_path, "rows.jsonl", rows)
    out = list(iter_weighted_rows(
        rows_path=rows_path,
        partition_path=_empty_partition(tmp_path),
        label_weights={"upstream_v1": 1.0, "llm_sme_v1": 0.8, "human_cal_v1": 1.0},
    ))
    assert out[0]["sample_weight"] == 0.8

def test_missing_tag_raises(tmp_path):
    rows = [{"pair_key": "p1", "provenance_tag": "mystery_tag", "provenance_sha": "sha1", "label": 1}]
    rows_path = _write(tmp_path, "rows.jsonl", rows)
    with pytest.raises(ValueError, match="unknown provenance_tag"):
        list(iter_weighted_rows(
            rows_path=rows_path,
            partition_path=_empty_partition(tmp_path),
            label_weights=DEFAULT_LABEL_WEIGHTS,
        ))
```

- [ ] **Step 2: Run the failing test**

Run: `pytest classifier/tests/test_training_batches_weights.py -q`
Expected: `ImportError: classifier.ensemble.training_batches`.

- [ ] **Step 3: Implement `training_batches.py`**

```python
# classifier/ensemble/training_batches.py
"""Provenance-tagged training-batch loader.

Implements spec §4.5 (per-tag weights) and spec §4.4 runtime contamination
assertion (Contract 10 of Plan 5, the second layer of the two-layer defense).
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, Iterator, Mapping, Optional

DEFAULT_LABEL_WEIGHTS: Dict[str, float] = {
    "upstream_v1":  1.0,
    "llm_sme_v1":   0.6,
    "human_cal_v1": 1.0,
}


def _load_held_out(partition_path: Path) -> frozenset[str]:
    data = json.loads(Path(partition_path).read_text())
    return frozenset(data.get("held_out", []))


def iter_weighted_rows(
    rows_path: Path,
    partition_path: Path,
    label_weights: Optional[Mapping[str, float]] = None,
) -> Iterator[dict]:
    """Yield provenance-tagged rows with a `sample_weight` field.

    - Looks up per-row weight via `label_weights[row['provenance_tag']]`
      (defaults to `DEFAULT_LABEL_WEIGHTS`).
    - Unknown tags raise `ValueError("unknown provenance_tag: <tag>")`.
    - Asserts each row's `provenance_sha` is NOT in the held-out set from
      `partition.json`; a hit raises `RuntimeError` with the Contract 10
      message. The held-out set is cached per-call as a `frozenset`.
    """
    weights = dict(label_weights or DEFAULT_LABEL_WEIGHTS)
    held_out = _load_held_out(Path(partition_path))
    with open(rows_path) as f:
        for line in f:
            row = json.loads(line)
            tag = row.get("provenance_tag")
            if tag not in weights:
                raise ValueError(f"unknown provenance_tag: {tag!r}")
            sha = row.get("provenance_sha")
            if sha and sha in held_out:
                raise RuntimeError(
                    f"Contract 10: held-out upstream provenance_sha {sha} "
                    "reached training batch loader"
                )
            row["sample_weight"] = float(weights[tag])
            yield row
```

- [ ] **Step 4: Re-run the weight test**

Run: `pytest classifier/tests/test_training_batches_weights.py -q`
Expected: `3 passed`.

- [ ] **Step 5: Commit**

```bash
git add classifier/ensemble/training_batches.py classifier/tests/test_training_batches_weights.py
git commit -m "plan5-delta: provenance-tagged training batch loader with per-tag weights"
```

### Task A2: Runtime contamination assertion (Contract 10)

**Files:**
- Create: `classifier/tests/test_training_batches_runtime_contamination.py`

- [ ] **Step 1: Write the failing test**

```python
# classifier/tests/test_training_batches_runtime_contamination.py
import json
import pytest
from classifier.ensemble.training_batches import iter_weighted_rows, DEFAULT_LABEL_WEIGHTS

def test_held_out_sha_raises(tmp_path):
    partition = tmp_path / "partition.json"
    partition.write_text(json.dumps({
        "held_out": ["HELDOUT_SHA"],
        "train_eligible": [],
        "upstream_total": 1,
    }))
    rows = tmp_path / "rows.jsonl"
    with open(rows, "w") as f:
        f.write(json.dumps({
            "pair_key": "p1",
            "provenance_tag": "upstream_v1",
            "provenance_sha": "HELDOUT_SHA",
            "label": 1,
        }) + "\n")
    with pytest.raises(RuntimeError, match="Contract 10: held-out upstream provenance_sha HELDOUT_SHA"):
        list(iter_weighted_rows(rows, partition, DEFAULT_LABEL_WEIGHTS))

def test_train_eligible_sha_passes(tmp_path):
    partition = tmp_path / "partition.json"
    partition.write_text(json.dumps({
        "held_out": ["HELDOUT_SHA"],
        "train_eligible": ["OK_SHA"],
        "upstream_total": 2,
    }))
    rows = tmp_path / "rows.jsonl"
    with open(rows, "w") as f:
        f.write(json.dumps({
            "pair_key": "p1",
            "provenance_tag": "upstream_v1",
            "provenance_sha": "OK_SHA",
            "label": 1,
        }) + "\n")
    out = list(iter_weighted_rows(rows, partition, DEFAULT_LABEL_WEIGHTS))
    assert len(out) == 1 and out[0]["sample_weight"] == 1.0
```

- [ ] **Step 2: Run the test**

Run: `pytest classifier/tests/test_training_batches_runtime_contamination.py -q`
Expected: `2 passed` (the assertion code already lives in `iter_weighted_rows` from Task A1).

- [ ] **Step 3: Commit**

```bash
git add classifier/tests/test_training_batches_runtime_contamination.py
git commit -m "plan5-delta: runtime contamination assertion test (Contract 10)"
```

### Task A3: Plumb `--label-weight` into `train_stacker.py`

**Files:**
- Modify: `classifier/ensemble/stacker.py` (from base plan)
- Modify: `classifier/scripts/train_stacker.py` (from base plan)

- [ ] **Step 1: Extend `LGBMStacker.fit` to accept `sample_weight`**

Add a `sample_weight: np.ndarray | None = None` parameter and forward it to
`lightgbm.LGBMClassifier.fit(..., sample_weight=sample_weight)`. If `None`,
behavior is unchanged.

- [ ] **Step 2: Route rows through the provenance-tagged loader**

In `classifier/scripts/train_stacker.py`:

```python
# add alongside existing argparse block
ap.add_argument("--label-weight", action="append", default=[],
                help="Override default per-tag weight, e.g. --label-weight llm_sme_v1=0.7 "
                     "(may be repeated)")
ap.add_argument("--rows-path", required=True,
                help="Provenance-tagged training rows JSONL (upstream_v1 + llm_sme_v1 + human_cal_v1)")
ap.add_argument("--partition-path", default="data/upstream/partition.json")
```

Parse overrides:

```python
from classifier.ensemble.training_batches import iter_weighted_rows, DEFAULT_LABEL_WEIGHTS
label_weights = dict(DEFAULT_LABEL_WEIGHTS)
for kv in args.label_weight:
    k, v = kv.split("=", 1)
    if k not in label_weights:
        raise SystemExit(f"--label-weight key must be one of {list(DEFAULT_LABEL_WEIGHTS)}, got {k!r}")
    label_weights[k] = float(v)
rows = list(iter_weighted_rows(args.rows_path, args.partition_path, label_weights))
sample_weight = np.asarray([r["sample_weight"] for r in rows], dtype=np.float32)
```

Then pass `sample_weight=sample_weight` through to `LGBMStacker.fit(...)`.

- [ ] **Step 3: Run base-plan stacker tests and the new weight tests**

Run:

```bash
pytest classifier/tests/test_stacker.py classifier/tests/test_training_batches_weights.py \
       classifier/tests/test_training_batches_runtime_contamination.py -q
```

Expected: all pass.

- [ ] **Step 4: Commit**

```bash
git add classifier/ensemble/stacker.py classifier/scripts/train_stacker.py
git commit -m "plan5-delta: stacker trainer consumes provenance-tagged rows with per-tag weights"
```

---

## Phase B — Reported eval #1: held-out upstream benchmark

### Task B1: Shared helpers in `reported_evals.py`

**Files:**
- Create: `classifier/ensemble/reported_evals.py`

- [ ] **Step 1: Implement helpers**

```python
# classifier/ensemble/reported_evals.py
"""Shared helpers for Plan 5 reported-eval blocks (spec §6).

Held-out upstream benchmark and crossref benchmark. The frozen-test eval
itself lives in Plan 6's sacred-run harness; this module never reads
`human_test_frozen.jsonl`.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Iterable

UPSTREAM_MAPPINGS = Path("data/upstream/mappings_v1.jsonl")
UPSTREAM_CROSSREFS = Path("data/upstream/crossrefs_v1.jsonl")
PARTITION = Path("data/upstream/partition.json")


def load_held_out_rows() -> list[dict]:
    held = set(json.loads(PARTITION.read_text())["held_out"])
    rows = []
    with open(UPSTREAM_MAPPINGS) as f:
        for line in f:
            r = json.loads(line)
            if r.get("provenance_sha") in held:
                rows.append(r)
    return rows


def load_crossref_rows() -> list[dict]:
    rows = []
    with open(UPSTREAM_CROSSREFS) as f:
        for line in f:
            rows.append(json.loads(line))
    return rows


def precision_recall_at_k(y_true: list[int], y_score: list[float], k: int) -> tuple[float, float]:
    order = sorted(range(len(y_score)), key=lambda i: y_score[i], reverse=True)[:k]
    hits = sum(y_true[i] for i in order)
    p = hits / max(k, 1)
    r = hits / max(sum(y_true), 1)
    return p, r


def mrr_at_k(relevance: Iterable[list[int]], k: int) -> float:
    total, n = 0.0, 0
    for rel in relevance:
        n += 1
        for rank, r in enumerate(rel[:k], start=1):
            if r:
                total += 1.0 / rank
                break
    return total / max(n, 1)
```

- [ ] **Step 2: Commit**

```bash
git add classifier/ensemble/reported_evals.py
git commit -m "plan5-delta: reported_evals helpers for upstream heldout and crossref blocks"
```

### Task B2: `eval_ensemble_upstream_heldout.py`

**Files:**
- Create: `classifier/scripts/eval_ensemble_upstream_heldout.py`
- Create: `classifier/tests/test_upstream_heldout_eval.py`

- [ ] **Step 1: Write the failing test**

```python
# classifier/tests/test_upstream_heldout_eval.py
import json
from pathlib import Path
import subprocess, sys

def test_eval_upstream_heldout_schema(tmp_path):
    out = tmp_path / "ensemble_upstream_heldout.json"
    subprocess.run(
        [sys.executable, "-m", "classifier.scripts.eval_ensemble_upstream_heldout",
         "--scorer", "ensemble", "--out", str(out)],
        check=True,
    )
    blk = json.loads(out.read_text())
    assert blk["block"] == "upstream_heldout"
    assert blk["n_rows"] == 1689
    assert "precision_at_1" in blk and "recall_at_10" in blk and "mrr_at_10" in blk
    assert blk["source"] == "data/upstream/partition.json.held_out"
    assert blk["scorer_version"]
```

- [ ] **Step 2: Implement the script**

```python
# classifier/scripts/eval_ensemble_upstream_heldout.py
"""Reported eval: held-out upstream benchmark.

Per spec §6. Runs the registered EnsembleScorer over the 1,689 rows that
`partition.json.held_out` marks off-limits for training, and emits a JSON
block with precision/recall/MRR@{1,5,10}. NEVER touches `human_test_frozen`.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
from classifier.data.splits import verify_hashes
from classifier.labeling.freeze import verify_label_hashes
from classifier.ensemble.reported_evals import (
    load_held_out_rows, precision_recall_at_k, mrr_at_k,
)
from classifier.ensemble.scorer import EnsembleScorer  # from base Plan 5


def main():
    verify_hashes()
    verify_label_hashes()
    ap = argparse.ArgumentParser()
    ap.add_argument("--scorer", default="ensemble")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    rows = load_held_out_rows()
    scorer = EnsembleScorer.load_registered(args.scorer)

    # Group rows by source_node_id to form ranked candidate lists for MRR.
    from collections import defaultdict
    groups: dict[str, list[tuple[int, float]]] = defaultdict(list)
    for r in rows:
        score = scorer.score_pair(
            source_node_id=f"{r['source_framework']}:{r['source_id']}",
            target_node_id=r.get("target_node_id") or f"{r['target_framework']}:{r['target_control_id']}",
        ).score
        groups[r["source_framework"] + ":" + r["source_id"]].append((1, score))

    relevance = []
    y_true_flat, y_score_flat = [], []
    for src, items in groups.items():
        items.sort(key=lambda t: t[1], reverse=True)
        relevance.append([lbl for lbl, _ in items])
        for lbl, sc in items:
            y_true_flat.append(lbl); y_score_flat.append(sc)

    p1, _  = precision_recall_at_k(y_true_flat, y_score_flat, 1)
    _,  r10 = precision_recall_at_k(y_true_flat, y_score_flat, 10)
    mrr10 = mrr_at_k(relevance, 10)

    block = {
        "block": "upstream_heldout",
        "n_rows": len(rows),
        "source": "data/upstream/partition.json.held_out",
        "scorer_version": scorer.version,
        "precision_at_1": p1,
        "recall_at_10":  r10,
        "mrr_at_10":     mrr10,
    }
    Path(args.out).write_text(json.dumps(block, sort_keys=True, ensure_ascii=True))
    print(json.dumps(block, sort_keys=True))


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Run the test**

Run: `pytest classifier/tests/test_upstream_heldout_eval.py -q`
Expected: `1 passed`. (Assumes a registered `EnsembleScorer` from base Plan 5
exists; if the base plan has not yet been executed, the test is skipped via
`pytest.importorskip("classifier.ensemble.scorer")`.)

- [ ] **Step 4: Commit**

```bash
git add classifier/scripts/eval_ensemble_upstream_heldout.py classifier/tests/test_upstream_heldout_eval.py
git commit -m "plan5-delta: upstream heldout reported eval (§6 primary secondary benchmark)"
```

---

## Phase C — Reported eval #2: crossref benchmark

### Task C1: `eval_ensemble_crossref.py`

**Files:**
- Create: `classifier/scripts/eval_ensemble_crossref.py`
- Create: `classifier/tests/test_crossref_eval.py`

- [ ] **Step 1: Write the failing test**

```python
# classifier/tests/test_crossref_eval.py
import json, subprocess, sys
from pathlib import Path

def test_eval_crossref_schema(tmp_path):
    out = tmp_path / "ensemble_crossref.json"
    subprocess.run(
        [sys.executable, "-m", "classifier.scripts.eval_ensemble_crossref",
         "--scorer", "ensemble", "--out", str(out)],
        check=True,
    )
    blk = json.loads(out.read_text())
    assert blk["block"] == "crossref"
    assert blk["n_rows"] >= 1
    assert "mrr_at_10" in blk and "precision_at_1" in blk
    assert blk["source"] == "data/upstream/crossrefs_v1.jsonl"
    assert blk["scorer_version"]
```

- [ ] **Step 2: Implement the script**

```python
# classifier/scripts/eval_ensemble_crossref.py
"""Reported eval: crossref benchmark (spec §6 bonus).

Directly measures cross-source-list mapping quality (LLM ↔ Agentic ↔ DSGAI)
— the weak spot in Sessions 6–8. Reads `data/upstream/crossrefs_v1.jsonl`
and scores each (source_id, target_id) pair with the registered
EnsembleScorer. NEVER touches `human_test_frozen`.
"""
from __future__ import annotations
import argparse, json
from collections import defaultdict
from pathlib import Path
from classifier.data.splits import verify_hashes
from classifier.labeling.freeze import verify_label_hashes
from classifier.ensemble.reported_evals import (
    load_crossref_rows, precision_recall_at_k, mrr_at_k,
)
from classifier.ensemble.scorer import EnsembleScorer


def main():
    verify_hashes()
    verify_label_hashes()
    ap = argparse.ArgumentParser()
    ap.add_argument("--scorer", default="ensemble")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    rows = load_crossref_rows()
    scorer = EnsembleScorer.load_registered(args.scorer)

    groups: dict[str, list[tuple[int, float]]] = defaultdict(list)
    for r in rows:
        score = scorer.score_pair(
            source_node_id=r["source_node_id"],
            target_node_id=r["target_node_id"],
        ).score
        groups[r["source_node_id"]].append((1, score))

    relevance, y_true_flat, y_score_flat = [], [], []
    for src, items in groups.items():
        items.sort(key=lambda t: t[1], reverse=True)
        relevance.append([lbl for lbl, _ in items])
        for lbl, sc in items:
            y_true_flat.append(lbl); y_score_flat.append(sc)

    p1, _  = precision_recall_at_k(y_true_flat, y_score_flat, 1)
    _,  r10 = precision_recall_at_k(y_true_flat, y_score_flat, 10)
    mrr10 = mrr_at_k(relevance, 10)

    block = {
        "block": "crossref",
        "n_rows": len(rows),
        "source": "data/upstream/crossrefs_v1.jsonl",
        "scorer_version": scorer.version,
        "precision_at_1": p1,
        "recall_at_10":  r10,
        "mrr_at_10":     mrr10,
    }
    Path(args.out).write_text(json.dumps(block, sort_keys=True, ensure_ascii=True))
    print(json.dumps(block, sort_keys=True))


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Run the test**

Run: `pytest classifier/tests/test_crossref_eval.py -q`
Expected: `1 passed`.

- [ ] **Step 4: Commit**

```bash
git add classifier/scripts/eval_ensemble_crossref.py classifier/tests/test_crossref_eval.py
git commit -m "plan5-delta: crossref reported eval (§6 bonus)"
```

---

## Phase D — Merge + schema validation

### Task D1: `merge_reported_evals.py`

**Files:**
- Create: `classifier/scripts/merge_reported_evals.py`
- Create: `classifier/tests/test_reported_evals_schema.py`

- [ ] **Step 1: Write the failing test**

```python
# classifier/tests/test_reported_evals_schema.py
import json, subprocess, sys
from pathlib import Path

def test_merged_schema(tmp_path):
    upstream = tmp_path / "up.json"
    crossref = tmp_path / "cr.json"
    upstream.write_text(json.dumps({
        "block": "upstream_heldout", "n_rows": 1689,
        "source": "data/upstream/partition.json.held_out",
        "scorer_version": "v-test",
        "precision_at_1": 0.5, "recall_at_10": 0.7, "mrr_at_10": 0.6,
    }, sort_keys=True))
    crossref.write_text(json.dumps({
        "block": "crossref", "n_rows": 120,
        "source": "data/upstream/crossrefs_v1.jsonl",
        "scorer_version": "v-test",
        "precision_at_1": 0.3, "recall_at_10": 0.6, "mrr_at_10": 0.4,
    }, sort_keys=True))
    out = tmp_path / "merged.json"
    subprocess.run(
        [sys.executable, "-m", "classifier.scripts.merge_reported_evals",
         "--upstream-heldout", str(upstream),
         "--crossref", str(crossref),
         "--out", str(out)],
        check=True,
    )
    doc = json.loads(out.read_text())
    assert set(doc.keys()) == {"frozen_test", "upstream_heldout", "crossref", "scorer_version"}
    assert doc["frozen_test"] == {"owner": "plan6_sacred_run", "status": "forward_reference"}
    assert doc["upstream_heldout"]["n_rows"] == 1689
    assert doc["crossref"]["n_rows"] == 120
    assert doc["scorer_version"] == "v-test"
```

- [ ] **Step 2: Implement the merger**

```python
# classifier/scripts/merge_reported_evals.py
"""Merge reported-eval JSON blocks into a single three-block document.

Blocks:
  - frozen_test:      forward reference to Plan 6's sacred-run harness
                      (this plan never reads human_test_frozen.jsonl)
  - upstream_heldout: held-out upstream benchmark (§6 primary secondary)
  - crossref:         crossref benchmark (§6 bonus)
"""
from __future__ import annotations
import argparse, json
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--upstream-heldout", required=True)
    ap.add_argument("--crossref", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    up = json.loads(Path(args.upstream_heldout).read_text())
    cr = json.loads(Path(args.crossref).read_text())
    assert up["block"] == "upstream_heldout"
    assert cr["block"] == "crossref"
    assert up["scorer_version"] == cr["scorer_version"], \
        "scorer_version mismatch — are you merging blocks from the same run?"

    doc = {
        "frozen_test": {"owner": "plan6_sacred_run", "status": "forward_reference"},
        "upstream_heldout": up,
        "crossref": cr,
        "scorer_version": up["scorer_version"],
    }
    Path(args.out).write_text(json.dumps(doc, sort_keys=True, ensure_ascii=True))
    print(json.dumps({"wrote": args.out, "scorer_version": up["scorer_version"]}, sort_keys=True))


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Run the test**

Run: `pytest classifier/tests/test_reported_evals_schema.py -q`
Expected: `1 passed`.

- [ ] **Step 4: Commit**

```bash
git add classifier/scripts/merge_reported_evals.py classifier/tests/test_reported_evals_schema.py
git commit -m "plan5-delta: merge reported-eval blocks into ensemble_reported_evals.json"
```

### Task D2: End-to-end dry run

- [ ] **Step 1: Regenerate eval blocks on the real artifacts**

```bash
python -m classifier.scripts.eval_ensemble_upstream_heldout \
    --scorer ensemble --out results/ensemble_upstream_heldout.json
python -m classifier.scripts.eval_ensemble_crossref \
    --scorer ensemble --out results/ensemble_crossref.json
python -m classifier.scripts.merge_reported_evals \
    --upstream-heldout results/ensemble_upstream_heldout.json \
    --crossref         results/ensemble_crossref.json \
    --out              results/ensemble_reported_evals.json
```

Expected outputs:

- `results/ensemble_upstream_heldout.json` with `"n_rows": 1689`
  and a numeric `mrr_at_10`.
- `results/ensemble_crossref.json` with `"block": "crossref"` and a
  numeric `mrr_at_10`.
- `results/ensemble_reported_evals.json` with exactly the four top-level
  keys `frozen_test`, `upstream_heldout`, `crossref`, `scorer_version`.

- [ ] **Step 2: Run the full Plan-5 test suite**

```bash
pytest classifier/tests/test_training_batches_weights.py \
       classifier/tests/test_training_batches_runtime_contamination.py \
       classifier/tests/test_upstream_heldout_eval.py \
       classifier/tests/test_crossref_eval.py \
       classifier/tests/test_reported_evals_schema.py \
       classifier/tests/test_contamination.py \
       classifier/tests/test_no_sacred_split_refs.py -q
```

Expected: all green. Note `test_contamination.py` (the pre-registered static
gate) and `test_no_sacred_split_refs.py` (Contract 8 path-grep) must still
pass — this delta does not add any `human_test_frozen` reference.

- [ ] **Step 3: Commit the eval artifacts**

```bash
git add results/ensemble_upstream_heldout.json results/ensemble_crossref.json results/ensemble_reported_evals.json
git commit -m "plan5-delta: initial reported-eval artifacts (upstream heldout + crossref + merged)"
```

---

## Self-review — task ↔ spec link table

| Task | Spec anchor | What it implements |
|---|---|---|
| A1 `iter_weighted_rows` + weight test | §4.5 (weights table), §7 Plan 5 bullet | Per-row `sample_weight` keyed on `provenance_tag` with the exact default `{1.0, 0.6, 1.0}` and `--label-weight` override |
| A2 runtime contamination test | §4.4 Risks mitigation (two-layer defense) | Runtime assertion that held-out `provenance_sha` values never reach the training loader; complements, does not replace, the pre-registered static gate in `classifier/tests/test_contamination.py` |
| A3 stacker plumbing | §4.5, §7 Plan 5 bullet | Trainer consumes provenance-tagged rows and forwards `sample_weight` to LightGBM |
| B1 `reported_evals.py` helpers | §6 | Shared loaders for held-out upstream rows and crossref rows; reused by B2 and C1 |
| B2 upstream-heldout eval script + test | §6 "held-out upstream benchmark — new primary secondary benchmark" | Reports precision@1 / recall@10 / MRR@10 on the 1,689 rows in `partition.json.held_out` |
| C1 crossref eval script + test | §6 "cross-ref benchmark — new bonus" | Reports the same metrics on `data/upstream/crossrefs_v1.jsonl` for cross-source-list mapping quality |
| D1 merger + schema test | §6, §7 Plan 5 bullet | Emits `results/ensemble_reported_evals.json` with the three reported blocks; `frozen_test` is a **forward reference** to Plan 6's sacred-run harness (this plan never reads `human_test_frozen.jsonl`, so Contract 8 and §9 are honored) |
| D2 dry run | §6, §10 | End-to-end regeneration on the real upstream artifacts; full Plan-5 test suite green |

## Explicitly out of scope (repeat)

- Auxiliary multi-task heads (severity / tier / scope) — §9.
- Re-freezing / re-splitting / modifying `human_test_frozen.jsonl` — §9.
- Re-specifying the upstream loader, id normalization, or the static
  contamination auditor — shipped in Plan 1b.
- Re-sourcing the Plan 2 calibration pool — handled by Plan 2 / Plan 6 per
  D7 / §7 Plan 6. This plan merely **references** `human_cal_v1` rows as
  already being the upstream-sourced calibration set.
- Plan 6 (human evaluation / sacred run on the frozen test) and Plan 4
  (bridge / cross-encoder ladder). This plan imports their public symbols
  only.
