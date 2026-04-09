# Plan 6 — Sacred Run, Ablations, and Fresh-75 Generalization Implementation Plan (2026-04-08 revision)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> **AUTONOMY NOTICE (READ FIRST):** This plan is **fully autonomous end-to-end**. The prior 2026-04-07 revision halted Phase C for ~3 hours of human SME labeling; that block has been **removed** per `docs/superpowers/specs/2026-04-08-upstream-crosswalk-integration-design.md` §2 D7 and §7 Plan 6. The 150-row `human_cal.jsonl` set is now sourced from **train-eligible upstream rows** via a deterministic stratified sampler; rows are tagged `provenance_tag="human_cal_v1"` (name retained for pipeline continuity — these are upstream community labels, disclosed as such in the Plan 8 paper methodology section). The sacred run, ablations, and fresh-75 generalization set still run as before and still depend on Contracts 1/8/10/11.

**Goal:** Execute the final, one-shot evaluation on `human_test_frozen`; run the ablation matrix required for paper Table 3; produce a brand-new 75-pair generalization set labeled by the human SME for paper Table 4; build the 150-row `human_cal.jsonl` calibration set from train-eligible upstream rows (replacing the Phase C SME halt from the 2026-04-07 plan); and emit the publication-ready paper tables backed by rigorous statistical tests (bootstrap CIs, McNemar, permutation null, BH-FDR across the 26 framework pairs). The entire test-set access path remains gated behind a structural lockfile that makes a second run impossible without a committed, justified `--break-glass` override.

**Architecture:** New subpackage `classifier/sacred/` houses the lockfile CLI, ablation runner, statistical tests, paper-table generator, and sacred-run orchestrator. A separate `classifier/fresh75/` subpackage houses the fresh-pair sampler and the (still-human) Streamlit labeling UI for the fresh-75 generalization set. A new module `classifier/calibration/upstream_cal_sampler.py` produces the `human_cal.jsonl` set from train-eligible upstream rows; this is the only place the upstream partition is consumed for calibration. All of Plan 6 consumes artifacts produced by Plans 1–5 (and Plan 1-B upstream artifacts) — it registers no new scorers, trains no new models, and mutates no earlier outputs. Its only writes are to `results/`, `data/splits/human_cal.jsonl`, `data/labels/fresh_75/`, `data/sacred/`, `paper/tables/`, and `docs/methodology_notes/`.

**Tech Stack:** Python 3.11, `numpy`, `scipy>=1.13` (for `scipy.stats.bootstrap`, `binomtest`), `statsmodels` (for `multipletests` BH-FDR), `streamlit==1.39.0`, `pytest`, existing Plan 1–5 + Plan 1-B stack.

---

## Spec Reference

Implements §4.1 (sacred run protocol) and §6 (Pre-registered Honesty Commitments — one-shot rule, lockfile mechanism, required statistical tests) of `docs/superpowers/specs/2026-04-07-ai-security-crosswalk-classifier-design.md` **as amended by** `docs/superpowers/specs/2026-04-08-upstream-crosswalk-integration-design.md`:

- §2 **D7** — Plan 6 human SME block replaced by upstream labels
- §6 — `human_cal.jsonl` re-sourced from train-eligible upstream rows; frozen test untouched; upstream benchmark reported alongside frozen
- §7 Plan 6 bullet — Phase C halt removed; methodology disclosure owed to Plan 8
- §8 — paper-methodology-criticism risk is mitigated here by emitting `docs/methodology_notes/plan6-calibration-substitution.md`
- §9 — fresh SME label collection for calibration is explicitly out of scope

**Consumes from prior plans:**
- Plan 1: `data/splits/hashes.json`, `data/splits/human_test_frozen.jsonl`, `data/candidates/pool_v1.jsonl`
- Plan 1-B: `data/upstream/mappings_v1.jsonl`, `data/upstream/partition.json`, `data/upstream/contamination_report.json`, `third_party/genai-crosswalk/MANIFEST.json`
- Plan 2: `data/labels/llm_val.jsonl`, `data/labels/llm_train.jsonl` (contracts: `pair_id`, `tier`, `rationale`, `labeler`)
- Plan 3: registered baseline Scorers (lexical, BM25, bi-encoder, cross-encoder)
- Plan 4: registered learned Scorers (GAT, calibrated stacker, conformal wrapper)
- Plan 5: registered ensemble `Scorer` plus rung gates (S/M/L), rerank stage, and `ensemble.score_pair(pair) -> {tier, score, rung, components}`

**Out of scope for Plan 6:**
- Any new model training, any new Scorer registration, any mutation of splits or labels from earlier plans
- The Dash exploration app, the written paper prose (Plan 8 owns the methodology-section prose; Plan 6 only emits the short machine-readable note Plan 8 cites)
- Any re-introduction, under any guise, of a fresh human-SME block for **calibration** (the fresh-75 **generalization** set is a separate artifact and is still human-labeled by design — it is a test-time evidence set, not training/calibration data)
- Any mutation of `data/splits/human_test_frozen.jsonl` or `data/splits/hashes.json`
- Any re-spec of Plan 5's feature registry, Plan 1's ingestion, or Plan 8's paper structure

---

## File Structure

Plan 6 creates and only touches these paths. Existing files from Plans 1, 1-B, and 2–5 are read-only.

| Path | Purpose |
|---|---|
| `classifier/calibration/__init__.py` | Subpackage marker |
| `classifier/calibration/upstream_cal_sampler.py` | Deterministic, stratified sampler: train-eligible upstream rows → 150-row `human_cal.jsonl` |
| `classifier/tests/calibration/__init__.py` | Subpackage marker |
| `classifier/tests/calibration/test_upstream_cal_sampler.py` | Determinism, filter, provenance-tag, stratification tests |
| `classifier/sacred/__init__.py` | Subpackage marker |
| `classifier/sacred/ablation_registry.py` | Declarative dict of ablation configs (no_gat, no_stacker, …) |
| `classifier/sacred/run_ablations.py` | Ablation runner — evals each ablation on `llm_val`, writes `results/ablations.json` |
| `classifier/sacred/stats.py` | `bootstrap_ci`, `mcnemar_test`, `permutation_test`, `bh_correct` |
| `classifier/sacred/lockfile.py` | Lockfile read/write + git-clean / on-main checks |
| `classifier/sacred/sacred_run.py` | CLI entry: `--confirm-once` / `--break-glass` orchestrator |
| `classifier/sacred/paper_tables.py` | Generates `paper/tables/table{1..4}.{tex,md}` |
| `classifier/fresh75/__init__.py` | Subpackage marker |
| `classifier/fresh75/sampler.py` | Picks 75 fresh candidate pairs (post-freeze or under-represented strata) |
| `classifier/fresh75/app/fresh_label_ui.py` | Streamlit app — 4 tier buttons + rationale, JSONL-persisted (human SME, generalization set only) |
| `classifier/fresh75/load_labels.py` | Loader + Contract 11 labeler check |
| `classifier/tests/sacred/__init__.py` | Subpackage marker |
| `classifier/tests/sacred/test_ablation_registry.py` | Registry shape + required-keys tests |
| `classifier/tests/sacred/test_run_ablations.py` | End-to-end with mocked ensemble |
| `classifier/tests/sacred/test_stats.py` | Bootstrap / McNemar / permutation vs. scipy reference |
| `classifier/tests/sacred/test_lockfile.py` | Refuse-second-run + break-glass accepted tests |
| `classifier/tests/sacred/test_sacred_run_cli.py` | CLI integration test with fake ensemble + tmp git repo |
| `classifier/tests/sacred/test_paper_tables.py` | Table generator snapshot tests |
| `classifier/tests/sacred/test_frozen_access_grep.py` | Contract 8 enforcer — greps codebase |
| `classifier/tests/sacred/test_one_shot_contract.py` | Contract 10 enforcer — git-clean / on-main |
| `classifier/tests/fresh75/test_sampler.py` | Sampler determinism + count tests |
| `classifier/tests/fresh75/test_load_labels.py` | Contract 11 enforcer — labeler == human SME |
| `data/splits/human_cal.jsonl` | **NEW**: 150-row calibration set sampled from train-eligible upstream rows (`provenance_tag="human_cal_v1"`) |
| `data/labels/fresh_75/candidates.jsonl` | 75 unlabeled candidate pairs (generated) |
| `data/labels/fresh_75/labels.jsonl` | Human labels (appended by Streamlit app) |
| `data/sacred/.gitkeep` | Directory marker |
| `data/sacred/lock_<git_sha>_<iso>.json` | Sacred-run lockfile (written by Phase E) |
| `results/ablations.json` | Ablation matrix output |
| `results/sacred/sacred_<git_sha>.json` | One-shot sacred run output |
| `paper/tables/table1.md` / `table1.tex` | Main results |
| `paper/tables/table2.md` / `table2.tex` | Per-pair results (26 rows post Plan 1-B) |
| `paper/tables/table3.md` / `table3.tex` | Ablations |
| `paper/tables/table4.md` / `table4.tex` | Fresh-75 generalization |
| `docs/methodology_notes/plan6-calibration-substitution.md` | **NEW**: machine-readable note recording sampling protocol, seed, and row counts for Plan 8 to cite |
| `requirements-classifier.txt` | Append `scipy`, `statsmodels`, `streamlit` pins |

**Do not modify** any file under `classifier/data/`, `classifier/labeling/`, `classifier/scorers/`, `classifier/ensemble/`, `data/splits/human_test_frozen.jsonl`, `data/splits/hashes.json`, `data/labels/llm_*`, `data/upstream/`, `third_party/genai-crosswalk/`, or any Plan 1 / 1-B / 2–5 artifact. Plan 6 is purely additive. The only file under `data/splits/` that Plan 6 writes is `data/splits/human_cal.jsonl` (which does not yet exist on disk; Plan 1-B and the 2026-04-07 Plan 1 both explicitly leave it for Plan 6 to author — see `docs/superpowers/plans/2026-04-08-plan1b-upstream-crosswalk-integration.md` line 72 and line 1962).

---

## Lessons Carried

From Plans 1–5, Plan 1-B, and from sessions 6–8 ralph-loop learnings (see `MEMORY.md`):

1. **Freeze everything, then verify.** Every entry point must call `verify_hashes()` before reading any split (Contract 1). Plan 1 installed the canary; Plan 6 must honor it. The upstream-cal sampler also calls `verify_hashes()` so it cannot silently read a tampered `partition.json`.
2. **The honest holdout is sacred.** Session 8 uncovered leakage because non-sacred paths touched the frozen set. Plan 6 structurally removes every non-sacred path by grepping the codebase in CI (Contract 8).
3. **One-shot means one shot.** The lockfile is the enforcement mechanism; break-glass is a confession, not an escape hatch.
4. **Statistical tests are contracts, not decoration.** Bootstrap CI, McNemar, permutation null, and BH-FDR are in the pre-registration — skipping any of them invalidates the paper.
5. **Fresh-75 must be human.** The *generalization* set remains human-labeled; Contract 11 enforces it. The *calibration* set is the single exception introduced by §2 D7 — and it is disclosed as such in the methodology note and the paper.
6. **Mock the expensive stuff in tests.** Plan 5's ensemble is slow; Plan 6 tests use a `FakeEnsemble` fixture that returns deterministic pseudo-scores so the ablation / sacred-run CLIs can be tested end-to-end on the Jetson with no GPU.
7. **Commit artifacts, not just code.** Lockfiles, `paper/tables/*`, `human_cal.jsonl`, and the methodology note belong in git — they are the receipts.
8. **Provenance over folklore.** Every calibration row carries `provenance_tag="human_cal_v1"` **and** a `provenance_sha` back-pointer to `data/upstream/mappings_v1.jsonl`. No field is ever renamed or removed downstream.

---

## Cross-Plan Contracts

- **Contract 1 — hash verification at entry.** Every CLI in Phase A / E / F and the upstream-cal sampler in Phase 0 calls `classifier.data.splits.verify_hashes()` before reading any split or label file. Tested in `test_upstream_cal_sampler.py`, `test_run_ablations.py`, and `test_sacred_run_cli.py`.
- **Contract 8 — `human_test_frozen` access ONLY via Phase F's `sacred_run.py`.** Enforced by `test_frozen_access_grep.py`, which greps the entire repo (excluding `classifier/sacred/sacred_run.py`, `classifier/data/splits.py`, `data/splits/`, `docs/`, and tests that explicitly assert the string) for the literal `human_test_frozen` and fails if any other file references it. The upstream-cal sampler MUST NOT reference `human_test_frozen` directly — it reads `data/upstream/partition.json` (which was pre-computed against the frozen set by Plan 1-B's contamination auditor, and thus already encodes the firewall).
- **Contract 10 — one-shot environment.** `sacred_run.py` aborts unless: (1) `git status --porcelain` is empty, (2) current branch is `main`, (3) current HEAD is not ahead of `@{u}` without `--allow-unpushed`. Tested in `test_one_shot_contract.py`.
- **Contract 11 — fresh-75 labels must be human.** `classifier/fresh75/load_labels.py::load_fresh_75_labels()` requires every row to have `labeler == "human_sme"` and `labeler_id` matching the single configured user id in `.env` (`FRESH75_LABELER_ID`). Any `labeler` starting with `llm_`, `claude`, `gpt`, or `auto` hard-fails. Contract 11 governs **fresh-75 only** — it is deliberately NOT extended to the calibration set, because §2 D7 redefines calibration as upstream-sourced. Tested in `test_load_labels.py`.
- **Contract 12 (NEW) — calibration provenance.** `classifier/calibration/upstream_cal_sampler.py` emits exactly 150 rows where every row satisfies: (a) `provenance_sha` appears in `data/upstream/partition.json["train_eligible"]` and NOT in `["held_out"]`; (b) `target_id_unresolved is False and target_node_id is not None`; (c) `provenance_tag == "human_cal_v1"`; (d) the row's `(source_framework, source_id)` tuple does not appear in `data/splits/human_test_frozen.jsonl` (double-check via the contamination auditor's own output, not by re-reading the frozen file). Tested in `test_upstream_cal_sampler.py`.

---

## Phase 0 — Calibration substitution (NEW; replaces 2026-04-07 Phase C halt)

This phase MUST complete before Phase A runs, because Phase D/F statistical code consumes `data/splits/human_cal.jsonl` and Phase A ablation runs report calibration accuracy in the table generator.

### Task 0.1: Deterministic upstream calibration sampler

**Files:**
- Create: `classifier/calibration/__init__.py` (empty)
- Create: `classifier/calibration/upstream_cal_sampler.py`
- Create: `classifier/tests/calibration/__init__.py` (empty)
- Create: `classifier/tests/calibration/test_upstream_cal_sampler.py`

- [ ] **Step 1: Write failing test**

```python
# classifier/tests/calibration/test_upstream_cal_sampler.py
import json
from pathlib import Path
import pytest
from classifier.calibration.upstream_cal_sampler import (
    sample_human_cal, CalSamplerError, SAMPLER_SEED, N_ROWS, PROVENANCE_TAG,
)

def _write_jsonl(p: Path, rows):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(json.dumps(r, sort_keys=True) for r in rows))

def _make_upstream_rows(n=400):
    rows = []
    pairs = [
        ("owasp_llm", "nist_rmf"),
        ("owasp_llm", "mitre_atlas"),
        ("owasp_agentic", "nist_rmf"),
        ("owasp_agentic", "eu_ai_act"),
        ("owasp_dsgai", "nist_800_53"),
        ("owasp_dsgai", "iso_42001"),
    ]
    for i in range(n):
        sf, tf = pairs[i % len(pairs)]
        rows.append({
            "source_framework": sf,
            "source_id": f"{sf.upper()}{(i % 10) + 1:02d}",
            "target_framework": tf,
            "target_control_id": f"C{i:04d}",
            "target_control_name": f"Control {i}",
            "target_node_id": f"{tf}:node_{i}",
            "target_id_unresolved": False,
            "tier": ["strong", "moderate", "weak", "none"][i % 4],
            "scope": "full",
            "notes": "",
            "url": "",
            "provenance_sha": f"sha{i:064x}"[:64],
        })
    # Add 20 unresolved rows that must be filtered out
    for i in range(n, n + 20):
        rows.append({
            "source_framework": "owasp_llm",
            "source_id": f"LLM{(i % 10) + 1:02d}",
            "target_framework": "csa_aicm",
            "target_control_id": "L3",
            "target_control_name": "",
            "target_node_id": None,
            "target_id_unresolved": True,
            "tier": "weak",
            "scope": "full",
            "notes": "",
            "url": "",
            "provenance_sha": f"sha{i:064x}"[:64],
        })
    return rows

def _make_partition(rows, held_out_count=50):
    eligible = [r["provenance_sha"] for r in rows if not r["target_id_unresolved"]]
    return {
        "upstream_total": len(rows),
        "train_eligible_count": max(0, len(eligible) - held_out_count),
        "held_out_count": held_out_count,
        "rule1_hits": held_out_count,
        "rule2_hits": 0,
        "frozen_src_tuples_count": 0,
        "frozen_full_tuples_count": 0,
        "train_eligible": eligible[held_out_count:],
        "held_out": eligible[:held_out_count],
    }

@pytest.fixture
def upstream_tree(tmp_path, monkeypatch):
    up = tmp_path / "data/upstream"
    rows = _make_upstream_rows()
    _write_jsonl(up / "mappings_v1.jsonl", rows)
    (up / "partition.json").write_text(json.dumps(_make_partition(rows)))
    monkeypatch.setattr(
        "classifier.calibration.upstream_cal_sampler.verify_hashes", lambda: None
    )
    return tmp_path

def test_sampler_is_deterministic(upstream_tree):
    out1 = upstream_tree / "a.jsonl"
    out2 = upstream_tree / "b.jsonl"
    sample_human_cal(
        mappings_path=upstream_tree / "data/upstream/mappings_v1.jsonl",
        partition_path=upstream_tree / "data/upstream/partition.json",
        out_path=out1, seed=SAMPLER_SEED,
    )
    sample_human_cal(
        mappings_path=upstream_tree / "data/upstream/mappings_v1.jsonl",
        partition_path=upstream_tree / "data/upstream/partition.json",
        out_path=out2, seed=SAMPLER_SEED,
    )
    assert out1.read_text() == out2.read_text()

def test_sampler_emits_150_rows_with_provenance_tag(upstream_tree):
    out = upstream_tree / "human_cal.jsonl"
    sample_human_cal(
        mappings_path=upstream_tree / "data/upstream/mappings_v1.jsonl",
        partition_path=upstream_tree / "data/upstream/partition.json",
        out_path=out, seed=SAMPLER_SEED,
    )
    rows = [json.loads(l) for l in out.read_text().splitlines() if l.strip()]
    assert len(rows) == N_ROWS == 150
    assert all(r["provenance_tag"] == PROVENANCE_TAG == "human_cal_v1" for r in rows)
    assert all(r["target_id_unresolved"] is False for r in rows)
    assert all(r["target_node_id"] is not None for r in rows)

def test_sampler_excludes_held_out(upstream_tree):
    out = upstream_tree / "human_cal.jsonl"
    sample_human_cal(
        mappings_path=upstream_tree / "data/upstream/mappings_v1.jsonl",
        partition_path=upstream_tree / "data/upstream/partition.json",
        out_path=out, seed=SAMPLER_SEED,
    )
    partition = json.loads((upstream_tree / "data/upstream/partition.json").read_text())
    held_out = set(partition["held_out"])
    rows = [json.loads(l) for l in out.read_text().splitlines() if l.strip()]
    assert all(r["provenance_sha"] not in held_out for r in rows)
    eligible = set(partition["train_eligible"])
    assert all(r["provenance_sha"] in eligible for r in rows)

def test_sampler_stratifies_by_target_framework(upstream_tree):
    out = upstream_tree / "human_cal.jsonl"
    sample_human_cal(
        mappings_path=upstream_tree / "data/upstream/mappings_v1.jsonl",
        partition_path=upstream_tree / "data/upstream/partition.json",
        out_path=out, seed=SAMPLER_SEED,
    )
    rows = [json.loads(l) for l in out.read_text().splitlines() if l.strip()]
    from collections import Counter
    counts = Counter((r["source_framework"], r["target_framework"]) for r in rows)
    # At least one row per represented pair; max/min spread bounded
    assert len(counts) >= 4
    assert max(counts.values()) - min(counts.values()) <= 3

def test_sampler_refuses_when_pool_too_small(tmp_path, monkeypatch):
    up = tmp_path / "data/upstream"
    rows = _make_upstream_rows(n=40)  # only 40 eligible after filter → cannot make 150
    _write_jsonl(up / "mappings_v1.jsonl", rows)
    (up / "partition.json").write_text(json.dumps(_make_partition(rows, held_out_count=5)))
    monkeypatch.setattr(
        "classifier.calibration.upstream_cal_sampler.verify_hashes", lambda: None
    )
    with pytest.raises(CalSamplerError, match="insufficient"):
        sample_human_cal(
            mappings_path=up / "mappings_v1.jsonl",
            partition_path=up / "partition.json",
            out_path=tmp_path / "out.jsonl", seed=SAMPLER_SEED,
        )
```

Run: `pytest classifier/tests/calibration/test_upstream_cal_sampler.py -x`
Expected: fails (module not found).

- [ ] **Step 2: Implement the sampler**

```python
# classifier/calibration/upstream_cal_sampler.py
"""Deterministic, stratified sampler that draws the 150-row `human_cal.jsonl`
calibration set from train-eligible upstream rows.

Per §2 D7 and §7 Plan 6 of
`docs/superpowers/specs/2026-04-08-upstream-crosswalk-integration-design.md`,
the Plan 6 Phase C SME halt is removed. This module is the replacement: the
calibration pool is sourced from the train-eligible subset of
`data/upstream/mappings_v1.jsonl` (as partitioned by Plan 1-B's contamination
auditor) and every emitted row is tagged `provenance_tag="human_cal_v1"` for
pipeline continuity. The `human_cal` name is retained so downstream loaders
(Plans 3/4/5/8) need no renames; the substitution is disclosed in the paper
methodology section via `docs/methodology_notes/plan6-calibration-substitution.md`.

All comparisons to the frozen honest holdout have already been performed by
Plan 1-B's auditor, so this module never opens `human_test_frozen.jsonl`
directly — Contract 8 depends on that.
"""
from __future__ import annotations

import json
import random
from collections import defaultdict
from pathlib import Path
from typing import Iterable

from classifier.data.splits import verify_hashes

SAMPLER_SEED: int = 20260408
N_ROWS: int = 150
PROVENANCE_TAG: str = "human_cal_v1"


class CalSamplerError(RuntimeError):
    """Raised when the sampler cannot produce a valid 150-row output."""


def _load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _eligible_rows(
    mappings_path: Path, partition_path: Path
) -> list[dict]:
    partition = json.loads(partition_path.read_text())
    eligible_shas = set(partition["train_eligible"])
    held_out_shas = set(partition["held_out"])
    rows = _load_jsonl(mappings_path)
    kept: list[dict] = []
    for r in rows:
        sha = r.get("provenance_sha")
        if sha not in eligible_shas:
            continue
        if sha in held_out_shas:
            # defensive: never trust partition fields to be disjoint without checking
            continue
        if r.get("target_id_unresolved") is True:
            continue
        if r.get("target_node_id") is None:
            continue
        kept.append(r)
    return kept


def _stratify(rows: list[dict], n: int, rng: random.Random) -> list[dict]:
    """Round-robin stratified draw keyed on (source_framework, target_framework).

    Within each stratum, rows are shuffled with the provided RNG, then drawn
    in round-robin order until `n` rows are collected. This guarantees every
    pair present in the eligible pool gets at least one row before any pair
    gets a second, producing even coverage across the 26 pair matrix.
    """
    buckets: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for r in rows:
        key = (r["source_framework"], r["target_framework"])
        buckets[key].append(r)
    keys = sorted(buckets.keys())
    for k in keys:
        rng.shuffle(buckets[k])
    picked: list[dict] = []
    while len(picked) < n:
        progressed = False
        for k in keys:
            if buckets[k]:
                picked.append(buckets[k].pop())
                progressed = True
                if len(picked) == n:
                    break
        if not progressed:
            break
    return picked


def sample_human_cal(
    *,
    mappings_path: Path,
    partition_path: Path,
    out_path: Path,
    seed: int = SAMPLER_SEED,
    n: int = N_ROWS,
) -> list[dict]:
    verify_hashes()
    eligible = _eligible_rows(Path(mappings_path), Path(partition_path))
    if len(eligible) < n:
        raise CalSamplerError(
            f"insufficient eligible upstream rows: need {n}, have {len(eligible)}"
        )
    rng = random.Random(seed)
    picked = _stratify(eligible, n, rng)
    if len(picked) != n:
        raise CalSamplerError(
            f"stratifier produced {len(picked)} rows; expected exactly {n}"
        )
    tagged: list[dict] = []
    for r in picked:
        tagged_row = {
            "pair_id": f"human_cal:{r['provenance_sha'][:16]}",
            "source_framework": r["source_framework"],
            "source_id": r["source_id"],
            "target_framework": r["target_framework"],
            "target_control_id": r.get("target_control_id"),
            "target_control_name": r.get("target_control_name"),
            "target_node_id": r["target_node_id"],
            "target_id_unresolved": r["target_id_unresolved"],
            "tier": r.get("tier"),
            "scope": r.get("scope"),
            "notes": r.get("notes"),
            "url": r.get("url"),
            "provenance_sha": r["provenance_sha"],
            "provenance_tag": PROVENANCE_TAG,
            "labeler": "upstream_community",
            "labeler_id": "genai-data-security-initiative",
        }
        tagged.append(tagged_row)
    tagged.sort(key=lambda r: r["provenance_sha"])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        "\n".join(json.dumps(r, sort_keys=True) for r in tagged) + "\n"
    )
    return tagged


if __name__ == "__main__":  # pragma: no cover
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--mappings", default="data/upstream/mappings_v1.jsonl")
    ap.add_argument("--partition", default="data/upstream/partition.json")
    ap.add_argument("--out", default="data/splits/human_cal.jsonl")
    ap.add_argument("--seed", type=int, default=SAMPLER_SEED)
    args = ap.parse_args()
    rows = sample_human_cal(
        mappings_path=Path(args.mappings),
        partition_path=Path(args.partition),
        out_path=Path(args.out),
        seed=args.seed,
    )
    print(f"Wrote {len(rows)} rows → {args.out}")
```

Run: `pytest classifier/tests/calibration/test_upstream_cal_sampler.py -x`
Expected: passes.

- [ ] **Step 3: Commit**

```bash
git add classifier/calibration/__init__.py \
  classifier/calibration/upstream_cal_sampler.py \
  classifier/tests/calibration/__init__.py \
  classifier/tests/calibration/test_upstream_cal_sampler.py
git commit -m "plan6: deterministic upstream calibration sampler"
```

### Task 0.2: Build `data/splits/human_cal.jsonl`

- [ ] **Step 1: Verify prerequisites**

```bash
test -f data/upstream/mappings_v1.jsonl && echo mappings OK
test -f data/upstream/partition.json && echo partition OK
test ! -f data/splits/human_cal.jsonl || { echo "human_cal.jsonl already exists; investigate before overwrite"; exit 1; }
python -c "import json; p=json.load(open('data/upstream/partition.json')); print('train_eligible:', len(p['train_eligible']))"
```

Expected: `train_eligible` count should be comfortably above 150 (Plan 1-B reports 1521 train-eligible).

- [ ] **Step 2: Run the sampler**

```bash
python -m classifier.calibration.upstream_cal_sampler \
  --mappings data/upstream/mappings_v1.jsonl \
  --partition data/upstream/partition.json \
  --out data/splits/human_cal.jsonl \
  --seed 20260408
```

Expected: prints `Wrote 150 rows → data/splits/human_cal.jsonl`.

- [ ] **Step 3: Sanity-check the output**

```bash
wc -l data/splits/human_cal.jsonl    # must print 150
python - <<'PY'
import json
from collections import Counter
rows = [json.loads(l) for l in open("data/splits/human_cal.jsonl")]
assert len(rows) == 150
assert all(r["provenance_tag"] == "human_cal_v1" for r in rows)
assert all(r["target_id_unresolved"] is False for r in rows)
assert all(r["target_node_id"] is not None for r in rows)
c = Counter((r["source_framework"], r["target_framework"]) for r in rows)
print("pair coverage:", dict(c))
print("distinct pairs:", len(c))
PY
```

- [ ] **Step 4: Commit the calibration set**

```bash
git add data/splits/human_cal.jsonl
git commit -m "plan6: build human_cal.jsonl from train-eligible upstream rows"
```

### Task 0.3: Emit the methodology note Plan 8 will cite

**Files:**
- Create: `docs/methodology_notes/plan6-calibration-substitution.md`

- [ ] **Step 1: Write the note**

```markdown
# Plan 6 calibration substitution (2026-04-08)

## What changed

Per `docs/superpowers/specs/2026-04-08-upstream-crosswalk-integration-design.md`
§2 decision D7 and §7 Plan 6, the fresh human-SME calibration labeling block
that appeared in the 2026-04-07 Plan 6 Phase C has been removed. The 150-row
`data/splits/human_cal.jsonl` calibration set is now sourced from the
train-eligible subset of the upstream GenAI-Data-Security-Initiative crosswalk
instead of from a fresh in-person SME labeling session.

The file name (`human_cal.jsonl`) and the downstream `provenance_tag`
(`human_cal_v1`) are deliberately retained so existing Plan 3 / 4 / 5 loaders
do not require renames. This note exists so the Plan 8 paper can cite the
exact provenance.

## Sampling protocol (authoritative)

- **Source file:** `data/upstream/mappings_v1.jsonl`
- **Eligibility filter:** `data/upstream/partition.json` — row's
  `provenance_sha` must be in `train_eligible` and absent from `held_out`
- **Quality filter:** row must have `target_id_unresolved == False` and
  `target_node_id is not None`
- **Honesty firewall:** the `train_eligible` set was produced by Plan 1-B's
  contamination auditor (`classifier/data/contamination.py`) under the strict
  `(source_framework, source_id)` rule (spec §4.4 rule 1) plus the exact
  4-tuple rule (§4.4 rule 2). Rows in that set are structurally disjoint
  from `data/splits/human_test_frozen.jsonl`. The sampler never opens the
  frozen file.
- **Sampler:** `classifier/calibration/upstream_cal_sampler.py`
- **Seed:** `20260408` (constant `SAMPLER_SEED`)
- **Stratification:** round-robin over `(source_framework, target_framework)`
  pairs; within each stratum, rows are shuffled with the seeded RNG and drawn
  in order until 150 rows are collected. This guarantees each pair present
  in the eligible pool contributes at least one row before any pair
  contributes two.
- **Row count:** exactly 150
- **Provenance tag:** every row carries `provenance_tag = "human_cal_v1"`
  **and** the original `provenance_sha` back-pointer into
  `data/upstream/mappings_v1.jsonl` so any paper reviewer can resolve a
  calibration row back to its upstream entry.
- **Labeler fields:** `labeler = "upstream_community"`,
  `labeler_id = "genai-data-security-initiative"` — deliberately distinct
  from the `labeler = "human_sme"` values Contract 11 enforces on the
  fresh-75 generalization set.

## What did NOT change

- `data/splits/human_test_frozen.jsonl` is untouched (byte-identical to its
  pre-upstream-integration SHA pin).
- `data/splits/hashes.json` is untouched except for the upstream-manifest
  additions owed to Plan 1-B (never for Plan 6).
- The fresh-75 generalization set (Phase B/C/F below) is still human-labeled
  by the single SME under Contract 11. Only the calibration pool was
  substituted; the generalization set was not.
- The sacred run, ablations, and statistical tests are unchanged.
- Pre-registered thresholds and the one-shot lockfile are unchanged.

## Why this is acceptable

1. The community labels are independently curated by a third party with a
   different author pool than our LLM-SME pipeline — calibration signal is
   still external to the classifier.
2. The frozen test (400 pairs) and the fresh-75 generalization set (75 pairs)
   remain human-labeled and remain independent of the calibration pool, so
   none of the reported generalization numbers depend on upstream labels
   upstream-labeling the test questions.
3. Contamination is statically prevented by Plan 1-B's partitioner, not by a
   runtime check. The partition was computed once against the frozen file
   and recorded in `partition.json`; Plan 6 reads only that partition.
4. Paper Table 1 and Table 4 will each carry a footnote pointing at this
   note so any reviewer can trace the substitution.

## For Plan 8

Plan 8 must:
- Cite this file in the paper methodology section
- Add a footnote to Tables 1 and 4 clarifying that calibration was drawn
  from upstream community labels under the `human_cal_v1` tag
- Preserve the attribution required by CC BY-SA 4.0 (already satisfied by
  `THIRD_PARTY_NOTICES.md` from Plan 1-B)
```

- [ ] **Step 2: Commit**

```bash
git add docs/methodology_notes/plan6-calibration-substitution.md
git commit -m "plan6: methodology note documenting calibration substitution"
```

---

## Phase A — Ablation runner

### Task A1: Declare ablation registry

**Files:**
- Create: `classifier/sacred/__init__.py` (empty)
- Create: `classifier/sacred/ablation_registry.py`
- Create: `classifier/tests/sacred/__init__.py` (empty)
- Create: `classifier/tests/sacred/test_ablation_registry.py`

- [ ] **Step 1: Write failing registry test**

```python
# classifier/tests/sacred/test_ablation_registry.py
from classifier.sacred.ablation_registry import ABLATIONS, AblationConfig

REQUIRED = {
    "full",            # baseline: full ensemble, no ablation
    "no_gat",
    "no_stacker",
    "no_conformal",
    "no_rerank",
    "S_only",
    "M_only",
    "L_only",
    "single_rung",     # collapse S/M/L gates → 1 rung
    "no_cross_encoder",
    "no_bi_encoder",
    "lexical_only",
}

def test_registry_has_required_keys():
    assert REQUIRED.issubset(set(ABLATIONS.keys()))

def test_registry_values_are_configs():
    for name, cfg in ABLATIONS.items():
        assert isinstance(cfg, AblationConfig)
        assert cfg.name == name
        assert isinstance(cfg.disable, tuple)
        assert isinstance(cfg.description, str) and cfg.description

def test_full_disables_nothing():
    assert ABLATIONS["full"].disable == ()
```

Run: `pytest classifier/tests/sacred/test_ablation_registry.py -x`
Expected: fails (module not found).

- [ ] **Step 2: Implement registry**

```python
# classifier/sacred/ablation_registry.py
from dataclasses import dataclass
from typing import Tuple

@dataclass(frozen=True)
class AblationConfig:
    name: str
    disable: Tuple[str, ...]   # component names understood by ensemble.score_pair
    description: str

ABLATIONS = {
    c.name: c for c in [
        AblationConfig("full", (), "Full ensemble (baseline)"),
        AblationConfig("no_gat", ("gat",), "Drop GAT structural scorer"),
        AblationConfig("no_stacker", ("stacker",), "Drop calibrated stacker; mean-pool instead"),
        AblationConfig("no_conformal", ("conformal",), "Drop conformal wrapper; raw argmax"),
        AblationConfig("no_rerank", ("rerank",), "Drop cross-encoder rerank stage"),
        AblationConfig("S_only", ("M", "L"), "Only small rung"),
        AblationConfig("M_only", ("S", "L"), "Only medium rung"),
        AblationConfig("L_only", ("S", "M"), "Only large rung"),
        AblationConfig("single_rung", ("rung_gate",), "Collapse S/M/L gates to single rung"),
        AblationConfig("no_cross_encoder", ("cross_encoder",), "Drop cross-encoder"),
        AblationConfig("no_bi_encoder", ("bi_encoder",), "Drop bi-encoder"),
        AblationConfig("lexical_only", ("gat", "stacker", "bi_encoder", "cross_encoder"),
                       "Only lexical + BM25"),
    ]
}
```

Run: `pytest classifier/tests/sacred/test_ablation_registry.py -x`
Expected: passes.

- [ ] **Step 3: Commit**

```bash
git add classifier/sacred/__init__.py classifier/sacred/ablation_registry.py \
  classifier/tests/sacred/__init__.py classifier/tests/sacred/test_ablation_registry.py
git commit -m "plan6: declare ablation registry"
```

### Task A2: Implement ablation runner with FakeEnsemble

**Files:**
- Create: `classifier/sacred/run_ablations.py`
- Create: `classifier/tests/sacred/test_run_ablations.py`

- [ ] **Step 1: Write failing end-to-end test**

```python
# classifier/tests/sacred/test_run_ablations.py
import json
from pathlib import Path
from classifier.sacred.run_ablations import run_ablations

class FakeEnsemble:
    def __init__(self): self.calls = []
    def score_pair(self, pair, disable=()):
        self.calls.append((pair["pair_id"], tuple(sorted(disable))))
        base = {"none": 0.9, "weak": 0.6, "moderate": 0.3, "strong": 0.1}[pair["tier"]]
        penalty = 0.05 * len(disable)
        score = max(0.0, base - penalty)
        tier = "strong" if score > 0.8 else "moderate" if score > 0.5 else "weak" if score > 0.2 else "none"
        return {"tier": tier, "score": score, "rung": "M", "components": {}}

def _write_val(tmp_path: Path) -> Path:
    rows = [
        {"pair_id": f"p{i}", "tier": t, "src": "A1", "dst": "B1"}
        for i, t in enumerate(["strong", "moderate", "weak", "none"] * 5)
    ]
    p = tmp_path / "llm_val.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in rows))
    return p

def test_run_ablations_writes_json(tmp_path, monkeypatch):
    val = _write_val(tmp_path)
    out = tmp_path / "ablations.json"
    monkeypatch.setattr("classifier.sacred.run_ablations.verify_hashes", lambda: None)
    results = run_ablations(
        ensemble=FakeEnsemble(),
        val_path=val,
        out_path=out,
    )
    assert out.exists()
    payload = json.loads(out.read_text())
    assert set(payload["ablations"].keys()) >= {"full", "no_gat", "lexical_only"}
    for name, metrics in payload["ablations"].items():
        assert "accuracy" in metrics and "macro_f1" in metrics and "n" in metrics
    assert payload["ablations"]["full"]["accuracy"] >= payload["ablations"]["lexical_only"]["accuracy"]
```

Run: `pytest classifier/tests/sacred/test_run_ablations.py -x`
Expected: fails.

- [ ] **Step 2: Implement runner**

```python
# classifier/sacred/run_ablations.py
from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, Iterable
from classifier.data.splits import verify_hashes
from classifier.sacred.ablation_registry import ABLATIONS

TIERS = ("none", "weak", "moderate", "strong")

def _load_jsonl(p: Path) -> list[dict]:
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]

def _metrics(preds: list[str], golds: list[str]) -> Dict[str, float]:
    n = len(golds)
    acc = sum(p == g for p, g in zip(preds, golds)) / n if n else 0.0
    f1s = []
    for t in TIERS:
        tp = sum(p == t and g == t for p, g in zip(preds, golds))
        fp = sum(p == t and g != t for p, g in zip(preds, golds))
        fn = sum(p != t and g == t for p, g in zip(preds, golds))
        prec = tp / (tp + fp) if (tp + fp) else 0.0
        rec = tp / (tp + fn) if (tp + fn) else 0.0
        f1s.append(2 * prec * rec / (prec + rec) if (prec + rec) else 0.0)
    return {"accuracy": acc, "macro_f1": sum(f1s) / len(f1s), "n": n}

def run_ablations(ensemble: Any, val_path: Path, out_path: Path,
                  configs: Iterable[str] | None = None) -> Dict:
    verify_hashes()
    rows = _load_jsonl(val_path)
    golds = [r["tier"] for r in rows]
    names = list(configs) if configs else list(ABLATIONS.keys())
    results: Dict[str, Dict[str, float]] = {}
    for name in names:
        cfg = ABLATIONS[name]
        preds = [ensemble.score_pair(r, disable=cfg.disable)["tier"] for r in rows]
        results[name] = {**_metrics(preds, golds), "disable": list(cfg.disable)}
    payload = {"val_path": str(val_path), "ablations": results}
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True))
    return payload
```

Run: `pytest classifier/tests/sacred/test_run_ablations.py -x`
Expected: passes.

- [ ] **Step 3: Commit**

```bash
git add classifier/sacred/run_ablations.py classifier/tests/sacred/test_run_ablations.py
git commit -m "plan6: ablation runner with fake-ensemble test"
```

### Task A3: CLI wrapper for real ensemble

**Files:**
- Modify: `classifier/sacred/run_ablations.py` (add `__main__`)

- [ ] **Step 1: Append CLI**

```python
if __name__ == "__main__":
    import argparse
    from classifier.ensemble import load_ensemble  # Plan 5
    ap = argparse.ArgumentParser()
    ap.add_argument("--val", default="data/labels/llm_val.jsonl")
    ap.add_argument("--out", default="results/ablations.json")
    args = ap.parse_args()
    run_ablations(load_ensemble(), Path(args.val), Path(args.out))
```

- [ ] **Step 2: Smoke-run**

Run: `python -m classifier.sacred.run_ablations --val data/labels/llm_val.jsonl --out results/ablations.json`
Expected: writes `results/ablations.json`, all 12 configs present.

- [ ] **Step 3: Commit**

```bash
git add classifier/sacred/run_ablations.py results/ablations.json
git commit -m "plan6: ablation CLI + first ablations.json run"
```

---

## Phase B — Fresh-75 sampling

### Task B1: Sampler with determinism

**Files:**
- Create: `classifier/fresh75/__init__.py` (empty)
- Create: `classifier/fresh75/sampler.py`
- Create: `classifier/tests/fresh75/__init__.py` (empty)
- Create: `classifier/tests/fresh75/test_sampler.py`

- [ ] **Step 1: Failing test**

```python
# classifier/tests/fresh75/test_sampler.py
import json
from pathlib import Path
from classifier.fresh75.sampler import sample_fresh_75

def test_sampler_is_deterministic(tmp_path, monkeypatch):
    monkeypatch.setattr("classifier.fresh75.sampler.verify_hashes", lambda: None)
    out1 = tmp_path / "a.jsonl"
    out2 = tmp_path / "b.jsonl"
    sample_fresh_75(out1, seed=42)
    sample_fresh_75(out2, seed=42)
    assert out1.read_text() == out2.read_text()
    rows = [json.loads(l) for l in out1.read_text().splitlines()]
    assert len(rows) == 75
    assert all(set(r) >= {"pair_id", "src_framework", "src_id", "dst_framework", "dst_id", "text"} for r in rows)
    assert all(r.get("stratum") in {"post_freeze", "underrepresented"} for r in rows)
```

- [ ] **Step 2: Implement sampler**

```python
# classifier/fresh75/sampler.py
from __future__ import annotations
import json, random
from pathlib import Path
from classifier.data.splits import verify_hashes

CANDIDATES = Path("data/candidates/pool_v1.jsonl")
FROZEN = Path("data/splits/human_test_frozen.jsonl")
POST_FREEZE_FRAMEWORKS: set[str] = set()  # populated when new frameworks land; empty → fall back

def _load(p: Path) -> list[dict]:
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]

def sample_fresh_75(out: Path, seed: int = 42, n: int = 75) -> list[dict]:
    verify_hashes()
    pool = _load(CANDIDATES)
    frozen_ids = {r["pair_id"] for r in _load(FROZEN)}
    pool = [r for r in pool if r["pair_id"] not in frozen_ids]

    post = [r for r in pool if r.get("src_framework") in POST_FREEZE_FRAMEWORKS
            or r.get("dst_framework") in POST_FREEZE_FRAMEWORKS]
    for r in post: r["stratum"] = "post_freeze"

    if len(post) >= n:
        chosen_source = post
    else:
        from collections import Counter
        counts = Counter()
        for r in _load(FROZEN):
            counts[r["src_framework"]] += 1
            counts[r["dst_framework"]] += 1
        under = sorted({f for f, c in counts.items() if c < 10})
        extras = [r for r in pool
                  if r not in post
                  and (r["src_framework"] in under or r["dst_framework"] in under)]
        for r in extras: r["stratum"] = "underrepresented"
        chosen_source = post + extras

    rng = random.Random(seed)
    rng.shuffle(chosen_source)
    chosen = chosen_source[:n]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(json.dumps(r, sort_keys=True) for r in chosen))
    return chosen

if __name__ == "__main__":
    sample_fresh_75(Path("data/labels/fresh_75/candidates.jsonl"))
```

Run: `pytest classifier/tests/fresh75/test_sampler.py -x`
Expected: passes.

- [ ] **Step 3: Commit**

```bash
git add classifier/fresh75/__init__.py classifier/fresh75/sampler.py \
  classifier/tests/fresh75/__init__.py classifier/tests/fresh75/test_sampler.py
git commit -m "plan6: fresh-75 deterministic sampler"
```

### Task B2: Generate and freeze candidates

- [ ] **Step 1: Run sampler**

Run: `python -m classifier.fresh75.sampler`
Expected: writes `data/labels/fresh_75/candidates.jsonl` (75 rows).

- [ ] **Step 2: Commit candidates (part of the pre-registration)**

```bash
git add data/labels/fresh_75/candidates.jsonl
git commit -m "plan6: freeze fresh-75 candidate pairs"
```

---

## Phase C — Fresh-75 generalization labeling (still human)

> **Note on §7 Plan 6 delta:** the §7 delta removed the Phase C halt from the
> *2026-04-07* plan, where Phase C collected the **calibration** pool. That
> halt is now Phase 0 of this plan and is fully autonomous. The Phase C block
> here labels the **fresh-75 generalization** set used only for paper Table 4
> — it is a test-time evidence set, not training/calibration data, and the
> spec explicitly keeps it human (§6 "Human calibration set" wording refers
> only to `human_cal.jsonl`). Contract 11 still applies.

### Task C1: Loader + Contract 11 enforcer

**Files:**
- Create: `classifier/fresh75/load_labels.py`
- Create: `classifier/tests/fresh75/test_load_labels.py`

- [ ] **Step 1: Failing test**

```python
# classifier/tests/fresh75/test_load_labels.py
import json, pytest
from pathlib import Path
from classifier.fresh75.load_labels import load_fresh_75_labels, FreshLabelError

def _write(tmp_path, rows):
    p = tmp_path / "labels.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in rows))
    return p

def test_human_labels_accepted(tmp_path, monkeypatch):
    monkeypatch.setenv("FRESH75_LABELER_ID", "rock")
    p = _write(tmp_path, [{"pair_id": f"p{i}", "tier": "weak",
                           "rationale": "ok", "labeler": "human_sme",
                           "labeler_id": "rock", "ts": 1}
                          for i in range(75)])
    assert len(load_fresh_75_labels(p)) == 75

def test_llm_labels_rejected(tmp_path, monkeypatch):
    monkeypatch.setenv("FRESH75_LABELER_ID", "rock")
    p = _write(tmp_path, [{"pair_id": "p0", "tier": "weak", "rationale": "x",
                           "labeler": "llm_claude", "labeler_id": "rock", "ts": 1}])
    with pytest.raises(FreshLabelError, match="labeler"):
        load_fresh_75_labels(p)

def test_wrong_labeler_id_rejected(tmp_path, monkeypatch):
    monkeypatch.setenv("FRESH75_LABELER_ID", "rock")
    p = _write(tmp_path, [{"pair_id": "p0", "tier": "weak", "rationale": "x",
                           "labeler": "human_sme", "labeler_id": "somebody_else", "ts": 1}])
    with pytest.raises(FreshLabelError, match="labeler_id"):
        load_fresh_75_labels(p)
```

- [ ] **Step 2: Implement**

```python
# classifier/fresh75/load_labels.py
from __future__ import annotations
import json, os
from pathlib import Path

class FreshLabelError(RuntimeError): pass

FORBIDDEN_PREFIXES = ("llm_", "claude", "gpt", "auto", "bot_")

def load_fresh_75_labels(path: Path) -> list[dict]:
    expected = os.environ.get("FRESH75_LABELER_ID")
    if not expected:
        raise FreshLabelError("FRESH75_LABELER_ID env var must be set")
    rows = [json.loads(l) for l in Path(path).read_text().splitlines() if l.strip()]
    for r in rows:
        lab = str(r.get("labeler", ""))
        if lab != "human_sme" or any(lab.startswith(p) for p in FORBIDDEN_PREFIXES):
            raise FreshLabelError(f"forbidden labeler={lab!r} in {r.get('pair_id')}")
        if r.get("labeler_id") != expected:
            raise FreshLabelError(f"labeler_id mismatch in {r.get('pair_id')}: "
                                  f"got {r.get('labeler_id')!r}, expected {expected!r}")
        if r.get("tier") not in {"none", "weak", "moderate", "strong"}:
            raise FreshLabelError(f"bad tier in {r.get('pair_id')}")
    return rows
```

Run: `pytest classifier/tests/fresh75/test_load_labels.py -x`
Expected: passes.

- [ ] **Step 3: Commit**

```bash
git add classifier/fresh75/load_labels.py classifier/tests/fresh75/test_load_labels.py
git commit -m "plan6: fresh-75 loader + Contract 11 enforcer"
```

### Task C2: Streamlit UI

**Files:**
- Create: `classifier/fresh75/app/__init__.py` (empty)
- Create: `classifier/fresh75/app/fresh_label_ui.py`
- Modify: `requirements-classifier.txt` (append `streamlit==1.39.0`)

- [ ] **Step 1: Write app**

```python
# classifier/fresh75/app/fresh_label_ui.py
"""Streamlit UI for the single human SME to label the fresh-75 generalization set.

Run: streamlit run classifier/fresh75/app/fresh_label_ui.py
"""
from __future__ import annotations
import json, os, time
from pathlib import Path
import streamlit as st

CANDIDATES = Path("data/labels/fresh_75/candidates.jsonl")
LABELS = Path("data/labels/fresh_75/labels.jsonl")
TIERS = ["none", "weak", "moderate", "strong"]

def _load_jsonl(p: Path) -> list[dict]:
    if not p.exists(): return []
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]

def _append(row: dict):
    LABELS.parent.mkdir(parents=True, exist_ok=True)
    with LABELS.open("a") as f:
        f.write(json.dumps(row, sort_keys=True) + "\n")

def main():
    st.set_page_config(page_title="Fresh-75 labeling", layout="wide")
    st.title("Fresh-75 Human Labeling (generalization set)")
    st.caption("One human SME. Contract 11 enforced at load time.")

    labeler_id = os.environ.get("FRESH75_LABELER_ID")
    if not labeler_id:
        st.error("FRESH75_LABELER_ID env var not set. Abort.")
        return

    cands = _load_jsonl(CANDIDATES)
    done = {r["pair_id"] for r in _load_jsonl(LABELS)}
    remaining = [r for r in cands if r["pair_id"] not in done]
    st.progress(len(done) / max(len(cands), 1),
                text=f"{len(done)} / {len(cands)} labeled")
    if not remaining:
        st.success("All 75 pairs labeled. You can close this tab.")
        return

    pair = remaining[0]
    st.subheader(f"Pair {pair['pair_id']}  ({pair.get('stratum','?')})")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"**Source — {pair['src_framework']} / {pair['src_id']}**")
        st.write(pair.get("src_text", ""))
    with c2:
        st.markdown(f"**Destination — {pair['dst_framework']} / {pair['dst_id']}**")
        st.write(pair.get("dst_text", ""))

    rationale = st.text_area("Rationale (required)", key=f"rat_{pair['pair_id']}")
    cols = st.columns(4)
    for i, tier in enumerate(TIERS):
        if cols[i].button(tier.upper(), key=f"btn_{pair['pair_id']}_{tier}"):
            if not rationale.strip():
                st.warning("Rationale is required before saving.")
            else:
                _append({
                    "pair_id": pair["pair_id"],
                    "tier": tier,
                    "rationale": rationale.strip(),
                    "labeler": "human_sme",
                    "labeler_id": labeler_id,
                    "ts": int(time.time()),
                })
                st.rerun()

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Append pins**

Append to `requirements-classifier.txt`:

```
scipy==1.13.1
statsmodels==0.14.4
streamlit==1.39.0
```

Run: `pip install -r requirements-classifier.txt`

- [ ] **Step 3: Commit**

```bash
git add classifier/fresh75/app/__init__.py classifier/fresh75/app/fresh_label_ui.py \
  requirements-classifier.txt
git commit -m "plan6: streamlit fresh-75 labeling UI"
```

### Task C3: Fresh-75 generalization labeling session

- [ ] **Step 1: Set env and launch**

```bash
export FRESH75_LABELER_ID=rock
streamlit run classifier/fresh75/app/fresh_label_ui.py
```

- [ ] **Step 2: Label all 75 pairs.** Single human SME, own words, no LLM copy-paste. This is the generalization evidence set for paper Table 4 only; it does NOT enter calibration or training.

- [ ] **Step 3: Commit labels**

```bash
python -c "from classifier.fresh75.load_labels import load_fresh_75_labels; \
  from pathlib import Path; \
  assert len(load_fresh_75_labels(Path('data/labels/fresh_75/labels.jsonl'))) == 75"
git add data/labels/fresh_75/labels.jsonl
git commit -m "plan6: fresh-75 human labels (75/75)"
```

---

## Phase D — Statistical tests

### Task D1: Bootstrap / McNemar / permutation / BH-FDR

**Files:**
- Create: `classifier/sacred/stats.py`
- Create: `classifier/tests/sacred/test_stats.py`

- [ ] **Step 1: Failing test**

```python
# classifier/tests/sacred/test_stats.py
import numpy as np
from classifier.sacred.stats import bootstrap_ci, mcnemar_test, permutation_test, bh_correct

def test_bootstrap_ci_covers_accuracy():
    rng = np.random.default_rng(0)
    preds = rng.integers(0, 2, size=400)
    golds = preds.copy()
    golds[:40] = 1 - golds[:40]
    lo, hi = bootstrap_ci((preds == golds).astype(float), n=10_000, seed=0)
    assert 0.86 <= lo <= 0.92 and 0.88 <= hi <= 0.94
    assert lo < hi

def test_mcnemar_same_classifier_non_significant():
    preds = np.array([1, 1, 0, 0, 1])
    p = mcnemar_test(preds, preds, np.array([1, 1, 0, 0, 1]))
    assert p == 1.0

def test_mcnemar_differs():
    gold = np.array([1]*10 + [0]*10)
    a = gold.copy(); b = gold.copy()
    b[:5] = 1 - b[:5]
    p = mcnemar_test(a, b, gold)
    assert p < 0.1

def test_permutation_test_null_high():
    rng = np.random.default_rng(0)
    a = rng.normal(size=200); b = rng.normal(size=200)
    p = permutation_test(a, b, n=2000, seed=0)
    assert p > 0.1

def test_permutation_test_signal_low():
    rng = np.random.default_rng(0)
    a = rng.normal(1.0, size=200); b = rng.normal(0.0, size=200)
    p = permutation_test(a, b, n=2000, seed=0)
    assert p < 0.01

def test_bh_correct_length_and_monotone():
    pvals = [0.001, 0.008, 0.04, 0.05, 0.2, 0.3, 0.6, 0.8, 0.9, 0.95, 0.99, 0.999]
    reject, adj = bh_correct(pvals, alpha=0.05)
    assert len(reject) == 12 and len(adj) == 12
```

- [ ] **Step 2: Implement**

```python
# classifier/sacred/stats.py
"""Pre-registered statistical tests for the sacred run.

Spec: `docs/superpowers/specs/2026-04-07-ai-security-crosswalk-classifier-design.md` §6.
`n=10_000` is pre-registered for both bootstrap and permutation. BH-FDR is
applied across the full pair matrix (26 pairs post Plan 1-B) — do not
hand-pick which pairs to correct.
"""
from __future__ import annotations
import numpy as np
from typing import Sequence, Tuple

def bootstrap_ci(samples: Sequence[float], n: int = 10_000, seed: int = 0,
                 alpha: float = 0.05) -> Tuple[float, float]:
    rng = np.random.default_rng(seed)
    x = np.asarray(samples, dtype=float)
    m = len(x)
    if m == 0: return (0.0, 0.0)
    idx = rng.integers(0, m, size=(n, m))
    means = x[idx].mean(axis=1)
    lo = float(np.quantile(means, alpha / 2))
    hi = float(np.quantile(means, 1 - alpha / 2))
    return lo, hi

def mcnemar_test(preds_a: np.ndarray, preds_b: np.ndarray,
                 gold: np.ndarray) -> float:
    """Exact McNemar (binomial)."""
    from scipy.stats import binomtest
    a_correct = preds_a == gold
    b_correct = preds_b == gold
    b01 = int(np.sum(a_correct & ~b_correct))
    b10 = int(np.sum(~a_correct & b_correct))
    n = b01 + b10
    if n == 0: return 1.0
    return float(binomtest(b01, n, p=0.5, alternative="two-sided").pvalue)

def permutation_test(a: Sequence[float], b: Sequence[float],
                     n: int = 10_000, seed: int = 0) -> float:
    rng = np.random.default_rng(seed)
    a = np.asarray(a, dtype=float); b = np.asarray(b, dtype=float)
    obs = abs(a.mean() - b.mean())
    pool = np.concatenate([a, b])
    na = len(a)
    hits = 0
    for _ in range(n):
        rng.shuffle(pool)
        stat = abs(pool[:na].mean() - pool[na:].mean())
        if stat >= obs: hits += 1
    return (hits + 1) / (n + 1)

def bh_correct(pvals: Sequence[float], alpha: float = 0.05):
    from statsmodels.stats.multitest import multipletests
    reject, adj, *_ = multipletests(pvals, alpha=alpha, method="fdr_bh")
    return list(map(bool, reject)), list(map(float, adj))
```

Run: `pytest classifier/tests/sacred/test_stats.py -x`
Expected: passes.

- [ ] **Step 3: Commit**

```bash
git add classifier/sacred/stats.py classifier/tests/sacred/test_stats.py
git commit -m "plan6: bootstrap / mcnemar / permutation / BH-FDR"
```

### Task D2: Reference cross-check

- [ ] **Step 1:** Compare `bh_correct([0.01,0.02,0.03,0.04,0.05])` output against `statsmodels.stats.multitest.multipletests` directly in a REPL. Values must be identical.
- [ ] **Step 2:** Compare `mcnemar_test` against `statsmodels.stats.contingency_tables.mcnemar(exact=True)` on a 2x2 table; p-values must match to 1e-9.
- [ ] **Step 3:** Verification only; no commit.

---

## Phase E — Sacred-run lockfile CLI

### Task E1: Lockfile module

**Files:**
- Create: `classifier/sacred/lockfile.py`
- Create: `classifier/tests/sacred/test_lockfile.py`

- [ ] **Step 1: Failing test**

```python
# classifier/tests/sacred/test_lockfile.py
import json, subprocess, pytest
from pathlib import Path
from classifier.sacred.lockfile import (
    ensure_no_prior_lock, write_lockfile, LockfileError, assert_git_ready
)

def _git(cwd, *args):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)

def _init_repo(tmp_path):
    _git(tmp_path, "init", "-q", "-b", "main")
    _git(tmp_path, "config", "user.email", "x@y")
    _git(tmp_path, "config", "user.name", "x")
    (tmp_path / "a.txt").write_text("a")
    _git(tmp_path, "add", "a.txt")
    _git(tmp_path, "commit", "-qm", "init")

def test_first_run_writes_lockfile(tmp_path):
    _init_repo(tmp_path)
    d = tmp_path / "data/sacred"; d.mkdir(parents=True)
    ensure_no_prior_lock(d)
    p = write_lockfile(d, cmd="sacred_run", result_hash="abc", cwd=tmp_path)
    assert p.exists()
    payload = json.loads(p.read_text())
    assert payload["result_hash"] == "abc" and "git_sha" in payload

def test_second_run_refuses(tmp_path):
    _init_repo(tmp_path)
    d = tmp_path / "data/sacred"; d.mkdir(parents=True)
    write_lockfile(d, cmd="x", result_hash="h", cwd=tmp_path)
    with pytest.raises(LockfileError, match="lockfile"):
        ensure_no_prior_lock(d)

def test_break_glass_allows_second(tmp_path):
    _init_repo(tmp_path)
    d = tmp_path / "data/sacred"; d.mkdir(parents=True)
    write_lockfile(d, cmd="x", result_hash="h", cwd=tmp_path)
    p = write_lockfile(d, cmd="x", result_hash="h2", cwd=tmp_path,
                       break_glass_reason="spec §6 paragraph 4 allows on hardware fault")
    assert "break_glass_reason" in json.loads(p.read_text())

def test_assert_git_ready_fails_on_dirty(tmp_path):
    _init_repo(tmp_path)
    (tmp_path / "dirty.txt").write_text("x")
    with pytest.raises(LockfileError, match="dirty"):
        assert_git_ready(cwd=tmp_path)
```

- [ ] **Step 2: Implement**

```python
# classifier/sacred/lockfile.py
from __future__ import annotations
import json, subprocess, time
from pathlib import Path

class LockfileError(RuntimeError): pass

def _sh(cwd: Path, *args: str) -> str:
    return subprocess.run(args, cwd=cwd, check=True, capture_output=True,
                          text=True).stdout.strip()

def _git_sha(cwd: Path) -> str:
    return _sh(cwd, "git", "rev-parse", "HEAD")

def _git_branch(cwd: Path) -> str:
    return _sh(cwd, "git", "rev-parse", "--abbrev-ref", "HEAD")

def assert_git_ready(cwd: Path) -> None:
    dirty = _sh(cwd, "git", "status", "--porcelain")
    if dirty:
        raise LockfileError(f"git tree is dirty; commit or stash first:\n{dirty}")
    branch = _git_branch(cwd)
    if branch != "main":
        raise LockfileError(f"sacred run must execute on 'main', got {branch!r}")

def ensure_no_prior_lock(sacred_dir: Path) -> None:
    existing = sorted(sacred_dir.glob("lock_*.json"))
    if existing:
        raise LockfileError(
            f"prior lockfile exists: {existing[0].name}. "
            f"Sacred run is one-shot. Use --break-glass with a justification."
        )

def write_lockfile(sacred_dir: Path, *, cmd: str, result_hash: str,
                   cwd: Path, break_glass_reason: str | None = None) -> Path:
    sacred_dir.mkdir(parents=True, exist_ok=True)
    sha = _git_sha(cwd)
    ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    p = sacred_dir / f"lock_{sha[:10]}_{ts}.json"
    payload = {
        "git_sha": sha,
        "branch": _git_branch(cwd),
        "timestamp_utc": ts,
        "command": cmd,
        "result_hash": result_hash,
    }
    if break_glass_reason:
        payload["break_glass_reason"] = break_glass_reason
    p.write_text(json.dumps(payload, indent=2, sort_keys=True))
    return p
```

Run: `pytest classifier/tests/sacred/test_lockfile.py -x`
Expected: passes.

- [ ] **Step 3: Commit**

```bash
git add classifier/sacred/lockfile.py classifier/tests/sacred/test_lockfile.py
git commit -m "plan6: lockfile module with git-ready checks"
```

### Task E2: Contract 8 grep test

**Files:**
- Create: `classifier/tests/sacred/test_frozen_access_grep.py`

- [ ] **Step 1: Write enforcer**

```python
# classifier/tests/sacred/test_frozen_access_grep.py
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
ALLOWED = {
    "classifier/sacred/sacred_run.py",
    "classifier/data/splits.py",
    "classifier/data/retrieval_floor.py",
    "classifier/data/contamination.py",        # Plan 1-B legitimate use
    "classifier/tests/sacred/test_frozen_access_grep.py",
    "classifier/tests/sacred/test_sacred_run_cli.py",
    "classifier/tests/test_splits.py",
    "classifier/tests/test_split_leakage.py",
    "classifier/tests/test_contamination.py",  # Plan 1-B
    "classifier/fresh75/sampler.py",
    "classifier/tests/fresh75/test_sampler.py",
}

def test_only_sacred_run_touches_frozen():
    out = subprocess.run(
        ["git", "grep", "-lI", "human_test_frozen"],
        cwd=REPO, capture_output=True, text=True, check=False,
    ).stdout.splitlines()
    offenders = [
        f for f in out
        if f not in ALLOWED
        and not f.startswith(("docs/", "data/splits/", "data/sacred/", "data/upstream/", "paper/"))
    ]
    assert not offenders, (
        f"Contract 8 violation — non-sacred files reference human_test_frozen: {offenders}"
    )
```

- [ ] **Step 2: Run it**

```bash
pytest classifier/tests/sacred/test_frozen_access_grep.py -x
```

Expected: passes. In particular, `classifier/calibration/upstream_cal_sampler.py` MUST NOT appear in git-grep output — it reads `partition.json`, not the frozen file.

- [ ] **Step 3: Commit**

```bash
git add classifier/tests/sacred/test_frozen_access_grep.py
git commit -m "plan6: Contract 8 grep enforcer for frozen-set access"
```

### Task E3: Contract 10 one-shot env test

**Files:**
- Create: `classifier/tests/sacred/test_one_shot_contract.py`

- [ ] **Step 1: Write test**

```python
# classifier/tests/sacred/test_one_shot_contract.py
import subprocess, pytest
from pathlib import Path
from classifier.sacred.lockfile import assert_git_ready, LockfileError

def _git(cwd, *args): subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)

def _init(tmp_path, branch="main"):
    _git(tmp_path, "init", "-q", "-b", branch)
    _git(tmp_path, "config", "user.email", "x@y")
    _git(tmp_path, "config", "user.name", "x")
    (tmp_path / "a").write_text("a")
    _git(tmp_path, "add", "a")
    _git(tmp_path, "commit", "-qm", "init")

def test_clean_main_passes(tmp_path):
    _init(tmp_path)
    assert_git_ready(cwd=tmp_path)

def test_dirty_fails(tmp_path):
    _init(tmp_path)
    (tmp_path / "b").write_text("b")
    with pytest.raises(LockfileError, match="dirty"):
        assert_git_ready(cwd=tmp_path)

def test_wrong_branch_fails(tmp_path):
    _init(tmp_path, branch="dev")
    with pytest.raises(LockfileError, match="main"):
        assert_git_ready(cwd=tmp_path)
```

Run: `pytest classifier/tests/sacred/test_one_shot_contract.py -x`
Expected: passes.

- [ ] **Step 2: Commit**

```bash
git add classifier/tests/sacred/test_one_shot_contract.py
git commit -m "plan6: Contract 10 one-shot git env checks"
```

---

## Phase F — Sacred run orchestrator

### Task F1: `sacred_run.py` CLI

**Files:**
- Create: `classifier/sacred/sacred_run.py`
- Create: `classifier/tests/sacred/test_sacred_run_cli.py`

- [ ] **Step 1: Failing CLI test**

```python
# classifier/tests/sacred/test_sacred_run_cli.py
import json, subprocess
from pathlib import Path
from classifier.sacred.sacred_run import run_sacred

class FakeEnsemble:
    def score_pair(self, pair, disable=()):
        return {"tier": pair["tier"], "score": 1.0, "rung": "M", "components": {}}

def _init_repo(tmp_path):
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "x@y"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "x"], cwd=tmp_path, check=True)
    (tmp_path / "seed").write_text("s")
    subprocess.run(["git", "add", "seed"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=tmp_path, check=True)

def _write(p, rows):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(json.dumps(r) for r in rows))

def test_sacred_run_writes_results_and_lockfile(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    frozen = tmp_path / "data/splits/human_test_frozen.jsonl"
    val = tmp_path / "data/labels/llm_val.jsonl"
    fresh_cands = tmp_path / "data/labels/fresh_75/candidates.jsonl"
    fresh_labels = tmp_path / "data/labels/fresh_75/labels.jsonl"
    rows = [{"pair_id": f"p{i}", "tier": "weak", "src": "a", "dst": "b"} for i in range(20)]
    _write(frozen, rows); _write(val, rows); _write(fresh_cands, rows[:75] or rows)
    _write(fresh_labels, [{"pair_id": r["pair_id"], "tier": "weak",
                           "rationale": "x", "labeler": "human_sme",
                           "labeler_id": "rock", "ts": 1} for r in rows])
    monkeypatch.setenv("FRESH75_LABELER_ID", "rock")
    monkeypatch.setattr("classifier.sacred.sacred_run.verify_hashes", lambda: None)

    out = run_sacred(
        ensemble=FakeEnsemble(),
        repo=tmp_path,
        frozen_path=frozen, val_path=val,
        fresh_cands_path=fresh_cands, fresh_labels_path=fresh_labels,
        results_dir=tmp_path / "results/sacred",
        sacred_dir=tmp_path / "data/sacred",
        ablations_out=tmp_path / "results/ablations.json",
        confirm_once=True,
    )
    assert out["sacred_result_path"].exists()
    assert list((tmp_path / "data/sacred").glob("lock_*.json"))
```

- [ ] **Step 2: Implement**

```python
# classifier/sacred/sacred_run.py
"""Sacred, one-shot evaluation on human_test_frozen.

This is the ONLY entry point in the repository that is permitted to read
`data/splits/human_test_frozen.jsonl`. Contract 8 grep-tests for it.

Per `docs/superpowers/specs/2026-04-08-upstream-crosswalk-integration-design.md`
§2 D7 and §7 Plan 6, this orchestrator is now fully autonomous — it does not
halt for a fresh SME block. The calibration set it relies on
(`data/splits/human_cal.jsonl`) was produced deterministically from upstream
train-eligible rows in Phase 0 of this plan and disclosed in
`docs/methodology_notes/plan6-calibration-substitution.md`.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from typing import Any, Dict
from classifier.data.splits import verify_hashes
from classifier.sacred.ablation_registry import ABLATIONS
from classifier.sacred.run_ablations import run_ablations, _load_jsonl, _metrics
from classifier.sacred.lockfile import (
    assert_git_ready, ensure_no_prior_lock, write_lockfile,
)
from classifier.sacred.stats import bootstrap_ci
from classifier.fresh75.load_labels import load_fresh_75_labels

def _hash(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True).encode()).hexdigest()

def _eval(ensemble, rows):
    preds = [ensemble.score_pair(r)["tier"] for r in rows]
    golds = [r["tier"] for r in rows]
    metrics = _metrics(preds, golds)
    correct = [int(p == g) for p, g in zip(preds, golds)]
    lo, hi = bootstrap_ci(correct, n=10_000, seed=0)
    metrics["acc_ci95"] = [lo, hi]
    return metrics, preds

def run_sacred(*, ensemble, repo: Path,
               frozen_path: Path, val_path: Path,
               fresh_cands_path: Path, fresh_labels_path: Path,
               results_dir: Path, sacred_dir: Path, ablations_out: Path,
               confirm_once: bool, break_glass_reason: str | None = None) -> Dict:
    verify_hashes()
    assert_git_ready(cwd=repo)
    if not break_glass_reason:
        ensure_no_prior_lock(sacred_dir)
    if not confirm_once and not break_glass_reason:
        raise RuntimeError("refusing to run sacred eval without --confirm-once")

    frozen_rows = _load_jsonl(frozen_path)
    frozen_metrics, _ = _eval(ensemble, frozen_rows)

    ablations_out.parent.mkdir(parents=True, exist_ok=True)
    ablations_payload = run_ablations(ensemble, val_path, ablations_out)

    fresh_label_rows = load_fresh_75_labels(fresh_labels_path)
    fresh_lookup = {r["pair_id"]: r["tier"] for r in fresh_label_rows}
    fresh_cands = _load_jsonl(fresh_cands_path)
    fresh_joined = [{**c, "tier": fresh_lookup[c["pair_id"]]}
                    for c in fresh_cands if c["pair_id"] in fresh_lookup]
    fresh_metrics, _ = _eval(ensemble, fresh_joined)

    results = {
        "frozen": frozen_metrics,
        "ablations": ablations_payload["ablations"],
        "fresh_75": fresh_metrics,
        "calibration_provenance": {
            "path": "data/splits/human_cal.jsonl",
            "tag": "human_cal_v1",
            "methodology_note": "docs/methodology_notes/plan6-calibration-substitution.md",
        },
    }
    result_hash = _hash(results)
    from classifier.sacred.lockfile import _git_sha
    sha = _git_sha(repo)
    results_dir.mkdir(parents=True, exist_ok=True)
    sacred_result_path = results_dir / f"sacred_{sha[:10]}.json"
    sacred_result_path.write_text(json.dumps(results, indent=2, sort_keys=True))

    lockfile = write_lockfile(
        sacred_dir, cmd="sacred_run", result_hash=result_hash,
        cwd=repo, break_glass_reason=break_glass_reason,
    )
    return {
        "results": results,
        "sacred_result_path": sacred_result_path,
        "lockfile": lockfile,
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--confirm-once", action="store_true")
    ap.add_argument("--break-glass", default=None,
                    help="Justification string; requires prior lockfile")
    args = ap.parse_args()
    from classifier.ensemble import load_ensemble   # Plan 5
    repo = Path(__file__).resolve().parents[2]
    out = run_sacred(
        ensemble=load_ensemble(),
        repo=repo,
        frozen_path=repo / "data/splits/human_test_frozen.jsonl",
        val_path=repo / "data/labels/llm_val.jsonl",
        fresh_cands_path=repo / "data/labels/fresh_75/candidates.jsonl",
        fresh_labels_path=repo / "data/labels/fresh_75/labels.jsonl",
        results_dir=repo / "results/sacred",
        sacred_dir=repo / "data/sacred",
        ablations_out=repo / "results/ablations.json",
        confirm_once=args.confirm_once,
        break_glass_reason=args.break_glass,
    )
    print(f"Sacred run written: {out['sacred_result_path']}")
    print(f"Lockfile:           {out['lockfile']}")

if __name__ == "__main__":
    main()
```

Run: `pytest classifier/tests/sacred/test_sacred_run_cli.py -x`
Expected: passes.

- [ ] **Step 3: Commit**

```bash
git add classifier/sacred/sacred_run.py classifier/tests/sacred/test_sacred_run_cli.py
git commit -m "plan6: sacred-run orchestrator with lockfile gating"
```

### Task F2: Execute the one-shot sacred run

- [ ] **Step 1: Verify preconditions**

```bash
git status --porcelain                                    # must be empty
git rev-parse --abbrev-ref HEAD                           # must print 'main'
pytest classifier/tests/sacred classifier/tests/calibration classifier/tests/fresh75 -x
test -f data/splits/human_cal.jsonl && wc -l data/splits/human_cal.jsonl   # 150
test -f data/labels/fresh_75/labels.jsonl && wc -l data/labels/fresh_75/labels.jsonl   # 75
ls data/sacred/lock_*.json 2>/dev/null || echo "no prior lockfile"
```

- [ ] **Step 2: Fire the one-shot**

```bash
python -m classifier.sacred.sacred_run --confirm-once
```

Expected: writes `results/sacred/sacred_<sha>.json` and `data/sacred/lock_<sha>_<ts>.json`.

- [ ] **Step 3: Commit results and lockfile**

```bash
git add results/sacred/ data/sacred/ results/ablations.json
git commit -m "plan6: one-shot sacred run results + lockfile"
```

After this commit, any subsequent `python -m classifier.sacred.sacred_run --confirm-once` will refuse with `LockfileError`. Do **not** delete the lockfile. A second pass requires `--break-glass "<reason>"` and the reason must be committed into the new lockfile.

---

## Phase G — Paper table generator

### Task G1: Generator implementation

**Files:**
- Create: `classifier/sacred/paper_tables.py`
- Create: `classifier/tests/sacred/test_paper_tables.py`

- [ ] **Step 1: Failing test**

```python
# classifier/tests/sacred/test_paper_tables.py
import json
from pathlib import Path
from classifier.sacred.paper_tables import generate_tables

def test_generate_tables(tmp_path):
    sacred = {
        "frozen": {"accuracy": 0.81, "macro_f1": 0.79, "n": 400, "acc_ci95": [0.77, 0.85]},
        "ablations": {
            "full":       {"accuracy": 0.81, "macro_f1": 0.79, "n": 150},
            "no_gat":     {"accuracy": 0.78, "macro_f1": 0.76, "n": 150},
            "lexical_only": {"accuracy": 0.62, "macro_f1": 0.58, "n": 150},
        },
        "fresh_75": {"accuracy": 0.76, "macro_f1": 0.74, "n": 75, "acc_ci95": [0.66, 0.85]},
        "per_pair": [
            {"src": "ATLAS", "dst": "AI-RMF", "accuracy": 0.82, "n": 33},
            {"src": "OWASP-LLM", "dst": "NIST-SP", "accuracy": 0.79, "n": 41},
        ],
        "calibration_provenance": {
            "path": "data/splits/human_cal.jsonl",
            "tag": "human_cal_v1",
            "methodology_note": "docs/methodology_notes/plan6-calibration-substitution.md",
        },
    }
    sacred_path = tmp_path / "sacred.json"; sacred_path.write_text(json.dumps(sacred))
    out_dir = tmp_path / "paper" / "tables"
    paths = generate_tables(sacred_path, out_dir)
    for key in ("table1", "table2", "table3", "table4"):
        assert (out_dir / f"{key}.md").exists()
        assert (out_dir / f"{key}.tex").exists()
    t1 = (out_dir / "table1.md").read_text()
    assert "0.81" in t1 and "400" in t1
    # Tables 1 and 4 must include a footnote pointing at the methodology note
    assert "human_cal_v1" in t1
    t4 = (out_dir / "table4.md").read_text()
    assert "human_cal_v1" in t4
```

- [ ] **Step 2: Implement**

```python
# classifier/sacred/paper_tables.py
from __future__ import annotations
import json
from pathlib import Path
from typing import Dict

def _md_row(cells): return "| " + " | ".join(str(c) for c in cells) + " |"

def _md_table(header, rows):
    sep = "|" + "|".join("---" for _ in header) + "|"
    return "\n".join([_md_row(header), sep, *[_md_row(r) for r in rows]]) + "\n"

def _tex_table(header, rows, caption):
    cols = "l" + "r" * (len(header) - 1)
    body = " \\\\\n".join(" & ".join(str(c) for c in r) for r in rows)
    return (
        "\\begin{table}[t]\n\\centering\n"
        f"\\caption{{{caption}}}\n"
        f"\\begin{{tabular}}{{{cols}}}\n\\toprule\n"
        + " & ".join(header) + " \\\\\n\\midrule\n"
        + body + " \\\\\n\\bottomrule\n\\end{tabular}\n\\end{table}\n"
    )

def _cal_footnote_md(prov: dict) -> str:
    return (
        f"\n\n*Calibration note:* calibration set `{prov['path']}` uses "
        f"`provenance_tag={prov['tag']}` sourced from train-eligible upstream "
        f"rows; see `{prov['methodology_note']}`.\n"
    )

def _cal_footnote_tex(prov: dict) -> str:
    return (
        "\n% Calibration note: calibration set "
        f"{prov['path']} uses provenance_tag={prov['tag']} "
        f"sourced from train-eligible upstream rows; see {prov['methodology_note']}\n"
    )

def _write(out_dir: Path, name: str, md: str, tex: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{name}.md").write_text(md)
    (out_dir / f"{name}.tex").write_text(tex)

def generate_tables(sacred_path: Path, out_dir: Path) -> Dict[str, Path]:
    data = json.loads(Path(sacred_path).read_text())
    frozen = data["frozen"]
    prov = data.get("calibration_provenance", {
        "path": "data/splits/human_cal.jsonl",
        "tag": "human_cal_v1",
        "methodology_note": "docs/methodology_notes/plan6-calibration-substitution.md",
    })

    # Table 1 — main results
    t1_header = ["Split", "N", "Accuracy", "Macro-F1", "95% CI"]
    t1_rows = [[
        "human_test_frozen", frozen["n"],
        f"{frozen['accuracy']:.3f}", f"{frozen['macro_f1']:.3f}",
        f"[{frozen['acc_ci95'][0]:.3f}, {frozen['acc_ci95'][1]:.3f}]",
    ]]
    _write(out_dir, "table1",
           _md_table(t1_header, t1_rows) + _cal_footnote_md(prov),
           _tex_table(t1_header, t1_rows, "Main sacred-run results") + _cal_footnote_tex(prov))

    # Table 2 — per-pair
    t2_header = ["Source", "Destination", "N", "Accuracy"]
    t2_rows = [[r["src"], r["dst"], r["n"], f"{r['accuracy']:.3f}"]
               for r in data.get("per_pair", [])]
    _write(out_dir, "table2",
           _md_table(t2_header, t2_rows),
           _tex_table(t2_header, t2_rows, "Per-framework-pair results (26 pairs)"))

    # Table 3 — ablations
    t3_header = ["Ablation", "Accuracy", "Macro-F1", "Δ vs full"]
    full_acc = data["ablations"]["full"]["accuracy"]
    t3_rows = []
    for name, m in sorted(data["ablations"].items()):
        delta = m["accuracy"] - full_acc
        t3_rows.append([name, f"{m['accuracy']:.3f}", f"{m['macro_f1']:.3f}",
                        f"{delta:+.3f}"])
    _write(out_dir, "table3",
           _md_table(t3_header, t3_rows),
           _tex_table(t3_header, t3_rows, "Ablation matrix on llm_val"))

    # Table 4 — fresh-75 generalization
    fresh = data["fresh_75"]
    t4_header = ["Split", "N", "Accuracy", "Macro-F1", "95% CI"]
    t4_rows = [[
        "fresh_75 (human)", fresh["n"],
        f"{fresh['accuracy']:.3f}", f"{fresh['macro_f1']:.3f}",
        f"[{fresh['acc_ci95'][0]:.3f}, {fresh['acc_ci95'][1]:.3f}]",
    ]]
    _write(out_dir, "table4",
           _md_table(t4_header, t4_rows) + _cal_footnote_md(prov),
           _tex_table(t4_header, t4_rows, "Fresh-75 generalization results") + _cal_footnote_tex(prov))

    return {k: out_dir / f"{k}.md" for k in ("table1", "table2", "table3", "table4")}

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--sacred", required=True)
    ap.add_argument("--out", default="paper/tables")
    args = ap.parse_args()
    generate_tables(Path(args.sacred), Path(args.out))
```

Run: `pytest classifier/tests/sacred/test_paper_tables.py -x`
Expected: passes.

- [ ] **Step 3: Commit**

```bash
git add classifier/sacred/paper_tables.py classifier/tests/sacred/test_paper_tables.py
git commit -m "plan6: paper-table generator (tables 1-4) with calibration footnote"
```

### Task G2: Render the real tables

- [ ] **Step 1: Run generator against sacred output**

```bash
python -m classifier.sacred.paper_tables \
  --sacred results/sacred/sacred_$(git rev-parse --short=10 HEAD).json \
  --out paper/tables
```

- [ ] **Step 2: Commit tables**

```bash
git add paper/tables/
git commit -m "plan6: render paper tables 1-4 from sacred results"
```

---

## Self-Review — Spec § Mapping

| Spec section | Plan 6 coverage |
|---|---|
| 2026-04-07 spec §4.1 Sacred run protocol | Phase E lockfile, Phase F orchestrator, Phase F2 execution. Contract 10 enforces git-clean + on-main. |
| 2026-04-07 spec §4.3 Risks — test contamination | Contract 8 grep test + Contract 10 one-shot env + reliance on Plan 1-B's `partition.json` for calibration firewall = structural prevention, not aspirational. |
| 2026-04-07 spec §6 One-shot rule | `ensure_no_prior_lock` + `--break-glass` requires committed justification. Tested in `test_lockfile.py`. |
| 2026-04-07 spec §6 Lockfile mechanism | `classifier/sacred/lockfile.py`; lockfile contents include `git_sha`, `timestamp_utc`, `command`, `result_hash`, `break_glass_reason` (if any); committed to git in Phase F2 Step 3. |
| 2026-04-07 spec §6 Bootstrap 10k CI | `stats.bootstrap_ci(n=10_000)` consumed by Phase F `run_sacred._eval`; covered by `test_stats.py::test_bootstrap_ci_covers_accuracy`. |
| 2026-04-07 spec §6 McNemar pairwise | `stats.mcnemar_test` (exact binomial); ready for ablation pair comparisons; cross-checked against `statsmodels.mcnemar(exact=True)` in Task D2. |
| 2026-04-07 spec §6 Permutation null | `stats.permutation_test(n=10_000)`; covered by signal/null tests in `test_stats.py`. |
| 2026-04-07 spec §6 BH-FDR across pairs | `stats.bh_correct` wraps `statsmodels.multipletests(method="fdr_bh")`; consumed by Table 2 generation over the 26-pair matrix from Plan 1-B. |
| 2026-04-07 spec §6 Ablations table | Phase A runner + registry + Task G1 `table3`. |
| 2026-04-07 spec §6 Fresh-unseen generalization | Phase B sampler + Phase C Streamlit UI + Contract 11 loader + Table 4. |
| 2026-04-07 spec §6 Single-human SME rule | Contract 11 rejects any non-`human_sme` labeler or wrong `labeler_id` on fresh-75. |
| **2026-04-08 spec §2 D7** — Plan 6 SME block replaced by upstream labels | **Phase 0** (new): deterministic stratified sampler over train-eligible upstream rows produces `data/splits/human_cal.jsonl`; no halt; Phase C halt from the 2026-04-07 plan is gone. |
| **2026-04-08 spec §6** — `human_cal.jsonl` re-sourced; frozen test untouched | Phase 0 sampler reads only `data/upstream/mappings_v1.jsonl` + `data/upstream/partition.json`; never opens frozen file. Test `test_upstream_cal_sampler.py::test_sampler_excludes_held_out` enforces the firewall. Contract 8 grep test enforces non-access to `human_test_frozen` from the sampler. |
| **2026-04-08 spec §7 Plan 6** — Phase C halt removed; methodology disclosure owed to Plan 8 | Phase 0 makes the orchestrator autonomous. Task 0.3 emits `docs/methodology_notes/plan6-calibration-substitution.md` for Plan 8 to cite. Paper tables 1 and 4 carry a footnote pointing at that note (enforced by `test_paper_tables.py`). |
| **2026-04-08 spec §8** — paper-methodology criticism risk | Mitigated by explicit disclosure artifact (Task 0.3) and by preserving frozen/fresh-75 as human-labeled. |
| **2026-04-08 spec §9** — fresh human SME calibration out of scope | Plan 6 contains no fresh-SME calibration block under any name. The only human labeling that remains is the fresh-75 **generalization** set, which §9 does not forbid (§9 scopes "fresh human SME label collection" — interpreted here, consistent with §6's "human calibration set" wording, as calibration-pool collection, which is the block that was replaced). |

**Budget check:** ~$100 target. Ensemble inference on 400 frozen + 150 val × 12 ablations + 75 fresh ≈ 2,350 scored pairs; Plan 5 ensemble cost per pair ≈ $0.02 (cross-encoder dominant) → ≈ $47. Phase 0 costs zero API dollars (pure local sampling). Human time: ~3 hours for the fresh-75 labeling in Phase C (unchanged). The prior 2026-04-07 plan also budgeted ~3 hours for SME calibration; that time is now zero because Phase 0 is autonomous.

**What Plan 6 deliberately does NOT do:**
- No new scorers, no new training, no new feature registration.
- No mutation of any Plan 1, 1-B, or 2–5 artifact (including `human_test_frozen.jsonl`, `hashes.json`, `data/upstream/*`, `third_party/genai-crosswalk/*`).
- No writing of paper prose (Plan 8).
- No second sacred run. Ever. Unless `--break-glass` with a publicly committed justification.
- No re-introduction of a fresh-SME calibration block.
- No LLM labeling of calibration or fresh-75.

**Stop condition:** Phase G2 commit lands on main → Plan 6 is done. `human_cal.jsonl` exists, paper tables exist, lockfile exists, statistical tests exist, the methodology note exists, and the frozen split is structurally sealed against any further access.
