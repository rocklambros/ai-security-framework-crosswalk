# Plan 3 — Baselines & Feature Cache (Tier-B rewrite)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the baseline ladder (BM25, `bge-base-en-v1.5` cosine zero-shot, v2 composite, `bge-reranker-v2-m3` zero-shot, Opus 4.6 zero-shot ceiling) onto the already-shipped Tier-B 26-pair candidate pool (`data/candidates/pool_v1.jsonl`), emit per-pair feature diagnostics across the enlarged matrix, and re-run the retrieval-floor report as a formal gate any time Plan 2's silver labels or the pair matrix change. Candidate-pool construction itself is NOT in scope for this rewrite — Plan 1-B has already shipped `pool_v1.jsonl` at depth 100 on the full 26-pair matrix with the richer `_node_text` and BGE-base-en-v1.5 embeddings.

**Architecture:** The `classifier/baselines/` subpackage from the 2026-04-07 draft stands: every baseline implements a single `Scorer` Protocol (pairs → list[ScoreRecord]); a module-level registry lists all scorers discoverable by name. Heavy baselines (bge cosine, bge-reranker) cache embeddings / per-pair scores to parquet under `data/baselines/` and are loaded on the Jetson for the eval harness. The Opus 4.6 zero-shot ceiling reuses Plan 2's `LabelerClient` with one "unbiased expert" prompt and three temperature samples per pair (majority vote). The eval harness loads `llm_val` from Plan 2 and writes one JSON results file per run. A new per-pair coverage diagnostic iterates over the 26 framework pairs in `classifier.data.candidates.FRAMEWORK_PAIRS` and reports scorer coverage / null-rate / rank-of-gold for each pair so Plan 5's stacker and Plan 8's paper both see where the enlarged matrix is thin. The retrieval-floor gate from Plan 1-B (`classifier/data/retrieval_floor.py`) is re-invoked from a new Plan 3 script after Plan 2 publishes new silver labels; the `human_test_frozen` denominator is never altered.

**Tech Stack:** Python 3.11, `rank_bm25==0.2.2`, `pyarrow==17.0.0`, `sentence-transformers==3.2.1`, `torch`, `FlagEmbedding==1.3.2`, existing `classifier/` scaffolding from Plans 1 / 1-B / 2, existing `mapping_engine.engine.mapper`, `pytest`.

---

## Spec Reference

Implements §7 Plan 3 bullet of `docs/superpowers/specs/2026-04-08-upstream-crosswalk-integration-design.md`:

> **Plan 3 (candidate generation)** — Pair enumeration grows to the Tier-B source × target matrix. Retrieval floor report re-run on the enlarged matrix.

Also honors:
- §5 (Tier-B scope: 3 source lists × up to 12 target frameworks, ~26–40 pairs — final count is 26, already shipped in `classifier/data/candidates.py::FRAMEWORK_PAIRS`)
- §6 (evaluation strategy: `human_test_frozen` untouched; upstream benchmark and crossref benchmark are Plan 5 concerns, not Plan 3's)
- §9 (out of scope: no re-freezing, no pool rebuild under a new embedding model, no reranker-ladder scope creep)

Relative to `docs/superpowers/specs/2026-04-07-ai-security-crosswalk-classifier-design.md` §1.3 rows 1–5, §3.5 compute budget, §4.1 metrics, and §6 honesty commitments #1 / #6 / #8 still apply.

**Out of scope for Plan 3:**
- Rebuilding `pool_v1.jsonl` or changing the retrieval model (Plan 1-B shipped it; this plan treats it as frozen input).
- Any "Tier 2 / Tier 3 retrieval improvement" work. BM25+bridge fusion and cross-encoder rerank at candidate stage are deferred to Phase 2/3 reranker work per project memory `project_tier23_retrieval_deferred.md`.
- Any learned model training (Plan 4), stacked meta-learner + conformal wrapper (Plan 5), any run against `human_test_frozen` (Plan 6), Dash app (Plan 7), writeup (Plan 8).
- Upstream integration, `source_id` normalization, or the contamination auditor (Plan 1-B).
- Any modification to the 26-pair matrix. The matrix is frozen by Plan 1-B; if it changes, Plan 1-B is re-run first, then Plan 3 re-runs its gate.

**Accepted architectural ceiling:** `coverage_at_20 = 0.6500` / `coverage_at_k_used(100) = 0.8825` on `human_test_frozen` is the bge-base-en-v1.5 retrieval ceiling on this matrix. It is NOT a Plan 3 bug and MUST NOT be "fixed" inside Plan 3 — lifting it is Phase 2/3 reranker work.

---

## Deltas versus the 2026-04-07 draft

This is a rewrite of `docs/superpowers/plans/2026-04-07-plan3-baselines-and-features.md`. Concrete changes:

1. **Candidate-pool construction removed.** The 2026-04-07 draft was written before Plan 1-B shipped. Any Phase / Task that would have built `pool_v1.jsonl`, picked an embedding model, or enumerated pairs is gone. This plan consumes `data/candidates/pool_v1.jsonl` read-only.
2. **Pair matrix is 26, not 12.** Every fixture, CLI, and diagnostic iterates over `classifier.data.candidates.FRAMEWORK_PAIRS` (len = 26). No hard-coded 12-pair literals anywhere.
3. **Embedding model is `BAAI/bge-base-en-v1.5`** (Plan 1-B choice), not `bge-large-en-v1.5`. The `BGECosineScorer` name stays; the model revision pin bumps the scorer `version` string to `2.0.0` to make the algorithmic change visible in the results JSON per lesson 1 of the 2026-04-07 draft.
4. **New Phase H — per-pair feature coverage diagnostics.** Writes `data/features/per_pair_coverage.json` reporting, per framework-pair: number of `llm_val` rows, null rate for each scorer, rank-of-gold distribution, and whether the pair is under-represented (< 5 rows).
5. **New Phase I — retrieval-floor gate re-run.** Invokes `classifier.data.retrieval_floor.check_floor` after Plan 2 publishes new silver labels. Writes `data/candidates/retrieval_floor_report_plan3_rerun_<ts>.json` and asserts parity with Plan 1-B's frozen-test numbers (0.6500 / 0.8825). A drift fails the gate; Plan 3 halts.
6. **Dead-code audit.** A greppable CI test forbids the literals `range(12)`, `= 12` next to `pairs`, and bare `FRAMEWORK_PAIRS[:12]` to keep us from silently regressing to the 12-pair era.
7. **Phases A–G (Scorer Protocol, registry, BM25, BGE cosine, v2 composite, BGE reranker, Opus ceiling, eval harness, feature cache) are retained** with the adjustments above. See the 2026-04-07 draft for their line-by-line text — this rewrite only restates the deltas, not the full bodies, and each task below cross-references the 2026-04-07 section it supersedes.

---

## Lessons Carried from Plans 1, 1-B, and 2

1. **Scoring-path drift** (the s8-np `--no-rerank` bug). `Scorer.version` MUST bump on any scoring change. `BGECosineScorer.version = "2.0.0"` to reflect the bge-base-en-v1.5 switch.
2. **Byte-stable JSON outputs** (`hashes.json` canary). `json.dumps(..., sort_keys=True, ensure_ascii=False, indent=2)`.
3. **No in-place overwrites.** `data/baselines/run_YYYYMMDD_HHMMSS/`; `latest` symlink updated only after all tests pass.
4. **Version bumping.** Any revision-pin bump (model, tokenizer, k1/b) bumps the version string BEFORE the next run. Harness refuses to overwrite `(scorer_name, scorer_version)` results.
5. **Feasibility math as test.** Every baseline has a `test_*_runs_on_fixture` test with a 5-pair fixture before any Lambda or Opus spend.
6. **Architectural ceilings are documented, not silently fixed.** Any Plan 3 result reporting `recall@20` or `coverage_at_20` MUST cite the Plan 1-B retrieval_floor_report.json number alongside it.

---

## Cross-plan contracts honored

1. **Contract 1 — `verify_hashes()` at every CLI entry point.** Every script in `classifier/scripts/` for Plan 3 calls `classifier.data.splits.verify_hashes()` as its first line after argparse.
2. **Contract 2 — pool versioning.** Plan 3 consumes `data/candidates/pool_v1.jsonl` (Plan 1-B) and `data/labels/llm_sme/v1_frozen/` (Plan 2) exclusively. Neither is ever rewritten.
3. **Contract 3 — never overwrite.** Output directories versioned (`data/baselines/run_<ts>/`, `data/features/baseline_features_v<scorer_set_hash>.parquet`, `data/candidates/retrieval_floor_report_plan3_rerun_<ts>.json`).
4. **Contract 4 — Scorer Protocol.** Defined in Phase A; exported from `classifier.baselines.protocol`. Plans 4–5 register learned models against it with no modification to the registry module.
5. **Contract 7 — every API call appends to `data/cost_ledger.jsonl`.** Phase F (Opus ceiling) reuses Plan 2's `LabelerClient`.
6. **Contract (Plan 1-B) — retrieval-floor as a gate.** Phase I re-runs `check_floor()` and asserts the Plan 1-B baseline numbers are unchanged. Any drift halts Plan 3.

---

## File Structure

| Path | Purpose |
|---|---|
| `classifier/baselines/__init__.py` | Subpackage marker, re-exports `Scorer`, `NodePair`, `ScoreRecord`, `REGISTRY` |
| `classifier/baselines/protocol.py` | `Scorer` Protocol + `NodePair` + `ScoreRecord` dataclasses |
| `classifier/baselines/registry.py` | `register(scorer)` + `get(name)` + `all_scorers()` |
| `classifier/baselines/bm25.py` | `BM25Scorer` (rank_bm25) |
| `classifier/baselines/bge_cosine.py` | `BGECosineScorer` — reads cached bge-base-en-v1.5 embeddings parquet |
| `classifier/baselines/v2_composite.py` | `V2CompositeScorer` — wraps `mapping_engine.engine.mapper` |
| `classifier/baselines/bge_reranker.py` | `BGERerankerScorer` — reads cached per-pair scores parquet |
| `classifier/baselines/opus_zero_shot.py` | `OpusZeroShotScorer` — reuses Plan 2's `LabelerClient` |
| `classifier/baselines/eval_harness.py` | Load llm_val, run all registered scorers, compute R@K / MRR / tier-acc |
| `classifier/baselines/feature_cache.py` | Emit wide parquet (pair_key × scorer_name) |
| `classifier/baselines/per_pair_coverage.py` | Per-pair scorer-coverage diagnostic over the 26-pair matrix |
| `classifier/config/llm_sme_prompts/v1/unbiased_expert.j2` | Single-persona ceiling prompt |
| `classifier/tests/test_scorer_protocol.py` | Protocol shape + dataclass tests |
| `classifier/tests/test_registry.py` | Register/get/duplicate-name tests |
| `classifier/tests/test_bm25.py` | BM25 on 5-pair fixture |
| `classifier/tests/test_bge_cosine.py` | Cached-embedding loader + cosine math; asserts `BAAI/bge-base-en-v1.5` revision pin |
| `classifier/tests/test_v2_composite.py` | Wraps mapping_engine, returns ScoreRecords |
| `classifier/tests/test_bge_reranker.py` | Cached-score loader + shape |
| `classifier/tests/test_opus_zero_shot.py` | LabelerClient mock + 3-sample majority vote |
| `classifier/tests/test_eval_harness.py` | Metrics math + JSON schema |
| `classifier/tests/test_feature_cache.py` | Wide parquet shape + nullability |
| `classifier/tests/test_per_pair_coverage.py` | Coverage dict shape + 26-pair completeness |
| `classifier/tests/test_retrieval_floor_gate.py` | Plan 1-B baseline parity gate (0.6500 / 0.8825) |
| `classifier/tests/test_no_12_pair_deadcode.py` | Grep-style guard against 12-pair-era literals |
| `classifier/scripts/run_bm25_baseline.py` | CLI: BM25 on llm_val → results JSON |
| `classifier/scripts/build_bge_embeddings_lambda.py` | CLI (Lambda): encode all nodes with `BAAI/bge-base-en-v1.5`, write parquet |
| `classifier/scripts/run_bge_cosine_baseline.py` | CLI: bge cosine on llm_val → results JSON |
| `classifier/scripts/run_v2_composite_baseline.py` | CLI: v2 on llm_val → results JSON |
| `classifier/scripts/build_bge_reranker_scores_lambda.py` | CLI (Lambda): batch-score all pairs |
| `classifier/scripts/run_bge_reranker_baseline.py` | CLI: bge-reranker on llm_val → results JSON |
| `classifier/scripts/run_opus_ceiling_baseline.py` | CLI: Opus 4.6 on llm_val × 3 samples |
| `classifier/scripts/run_all_baselines_eval.py` | CLI: eval harness over the full registry |
| `classifier/scripts/build_baseline_feature_cache.py` | CLI: emit wide parquet for Plan 5 |
| `classifier/scripts/build_per_pair_coverage.py` | CLI: emit per-pair coverage JSON |
| `classifier/scripts/run_retrieval_floor_plan3_rerun.py` | CLI: Phase I gate |
| `data/baselines/bge_cosine_embeddings.parquet` | Cached node embeddings (Lambda-produced, bge-base-en-v1.5) |
| `data/baselines/bge_reranker_scores.parquet` | Cached per-pair cross-encoder scores (Lambda) |
| `data/baselines/run_<ts>/results_llm_val.json` | Eval harness headline numbers |
| `data/baselines/latest` | Symlink to most recent run dir |
| `data/features/baseline_features.parquet` | Wide pair×scorer parquet for Plan 5 stacker |
| `data/features/per_pair_coverage.json` | Per-pair scorer coverage diagnostic |
| `data/candidates/retrieval_floor_report_plan3_rerun_<ts>.json` | Phase I gate output |
| `classifier/BASELINES_COMPLETE.md` | Phase J handoff summary |
| `requirements-classifier.txt` | Append `rank_bm25`, `pyarrow`, `FlagEmbedding` |

**Do not modify** any file under `mapping_engine/` (Plan 3 imports it read-only), `data/splits/`, `data/candidates/pool_v1.jsonl`, `data/candidates/retrieval_floor_report.json`, `data/labels/llm_sme/v1_frozen/` (Plan 2 frozen outputs), Plan 2's `classifier/labeling/`, or `classifier/data/candidates.py` (Plan 1-B owner).

---

## Phase A — Scorer protocol, dataclasses, registry

Bodies are identical to the 2026-04-07 draft Phase A (Tasks A1 / A2 / A3). Re-read that file for the full code and commit commands. No deltas.

### Task A1: Dataclasses and Scorer Protocol — test first
Same as 2026-04-07 Task A1. Run `pytest classifier/tests/test_scorer_protocol.py -v`; expect 3 passed.

### Task A2: Registry — test first
Same as 2026-04-07 Task A2. Run `pytest classifier/tests/test_registry.py -v`; expect 3 passed.

### Task A3: Re-export and fixture pairs
Same as 2026-04-07 Task A3. Produces `classifier/tests/fixtures/pairs_5.jsonl`. Expected: 5 lines, valid JSON.

---

## Phase B — BM25 baseline

Bodies identical to 2026-04-07 draft Phase B (Tasks B1 / B2).

### Task B1: `BM25Scorer` — test first
Same as 2026-04-07 Task B1. `BM25Scorer.version = "1.0.0"`. Run `pytest classifier/tests/test_bm25.py -v`; expect 2 passed.

### Task B2: `run_bm25_baseline.py` CLI
Same as 2026-04-07 Task B2, with the following two deltas:

- [ ] **Delta 1: Iterate over the 26-pair matrix.** The CLI loads `llm_val` and the 26-pair pool as-is — no filter to the original 12 pairs.
- [ ] **Delta 2: First line after argparse is `from classifier.data.splits import verify_hashes; verify_hashes()`.**

Run: `python -m classifier.scripts.run_bm25_baseline --pool data/candidates/pool_v1.jsonl --out data/baselines/run_$(date +%Y%m%d_%H%M%S)/results_llm_val.json`
Expected: JSON file written with one entry per scorer; `pairs_scored` equals the llm_val row count.

---

## Phase C — BGE cosine baseline (`BAAI/bge-base-en-v1.5`)

### Task C1: `BGECosineScorer` — test first

**Files:**
- Create: `classifier/tests/test_bge_cosine.py`
- Create: `classifier/baselines/bge_cosine.py`

- [ ] **Step 1: Write the failing test**

```python
# classifier/tests/test_bge_cosine.py
import pytest, json
from pathlib import Path
from classifier.baselines.bge_cosine import BGECosineScorer, MODEL_NAME
from classifier.baselines.protocol import NodePair


FIXTURE = Path(__file__).parent / "fixtures" / "pairs_5.jsonl"


def test_model_pin_is_bge_base():
    assert MODEL_NAME == "BAAI/bge-base-en-v1.5"


def test_scorer_version_reflects_model_bump():
    # Plan 1-B switched from bge-large to bge-base; version string must bump.
    assert BGECosineScorer.version == "2.0.0"


def test_bge_cosine_runs_on_fixture(monkeypatch, tmp_path):
    import numpy as np, pyarrow as pa, pyarrow.parquet as pq
    pairs = [NodePair(**json.loads(l)) for l in FIXTURE.read_text().splitlines()]
    node_ids = sorted({p.source_node_id for p in pairs} | {p.target_node_id for p in pairs})
    dim = 8
    rng = np.random.default_rng(0)
    embs = rng.standard_normal((len(node_ids), dim)).astype("float32")
    embs /= np.linalg.norm(embs, axis=1, keepdims=True)
    tbl = pa.table({"node_id": node_ids, **{f"e{i}": embs[:, i] for i in range(dim)}})
    parquet_path = tmp_path / "bge_cosine_embeddings.parquet"
    pq.write_table(tbl, parquet_path)
    s = BGECosineScorer(embeddings_path=parquet_path)
    records = s.score(pairs)
    assert len(records) == 5
    assert all(-1.0 <= r.score <= 1.0 for r in records)
```

- [ ] **Step 2: Run — expect failure**
Run: `pytest classifier/tests/test_bge_cosine.py -v`
Expected: `ModuleNotFoundError: No module named 'classifier.baselines.bge_cosine'`

- [ ] **Step 3: Implement `classifier/baselines/bge_cosine.py`**

```python
"""BGE cosine baseline, reading a Lambda-produced embeddings parquet.

Model pin: BAAI/bge-base-en-v1.5 (Plan 1-B). Bumping this pin MUST bump
BGECosineScorer.version so the eval-harness results JSON reflects the change.
"""
from __future__ import annotations

from pathlib import Path
import numpy as np
import pyarrow.parquet as pq

from classifier.baselines.protocol import NodePair, ScoreRecord

MODEL_NAME = "BAAI/bge-base-en-v1.5"


class BGECosineScorer:
    name = "bge_cosine"
    version = "2.0.0"  # 2.0.0 = bge-base-en-v1.5 (was 1.0.0 = bge-large-en-v1.5)

    def __init__(self, embeddings_path: Path):
        tbl = pq.read_table(embeddings_path)
        cols = [c for c in tbl.column_names if c.startswith("e")]
        self._ids = tbl.column("node_id").to_pylist()
        self._emb = np.stack([tbl.column(c).to_numpy() for c in cols], axis=1)
        self._idx = {nid: i for i, nid in enumerate(self._ids)}

    def score(self, pairs: list[NodePair]) -> list[ScoreRecord]:
        out: list[ScoreRecord] = []
        for p in pairs:
            i = self._idx.get(p.source_node_id)
            j = self._idx.get(p.target_node_id)
            if i is None or j is None:
                score = float("nan")
            else:
                score = float(self._emb[i] @ self._emb[j])
            out.append(ScoreRecord(
                pair_key=p.pair_key, scorer_name=self.name, scorer_version=self.version,
                score=score, tier_pred=None, tier_probs=None,
                extras={"model": MODEL_NAME},
            ))
        return out
```

- [ ] **Step 4: Run — expect pass**
Run: `pytest classifier/tests/test_bge_cosine.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**
```bash
git add classifier/baselines/bge_cosine.py classifier/tests/test_bge_cosine.py
git commit -m "plan3: BGECosineScorer pinned to bge-base-en-v1.5 (version 2.0.0)"
```

### Task C2: `build_bge_embeddings_lambda.py` CLI

Same as 2026-04-07 Task C2 with model name pinned to `BAAI/bge-base-en-v1.5`. CLI hard-codes `MODEL_NAME = "BAAI/bge-base-en-v1.5"` to match `classifier.baselines.bge_cosine.MODEL_NAME`. No `--model` flag — a change of model is a code edit + version bump, not a runtime arg.

### Task C3: `run_bge_cosine_baseline.py` CLI
Same as 2026-04-07 Task C3. Adds `verify_hashes()` as first line after argparse. Run against the 26-pair pool.

---

## Phase D — v2 composite baseline

Bodies identical to 2026-04-07 draft Phase D (Tasks D1 / D2). `V2CompositeScorer.version = "1.0.0"`. Run `pytest classifier/tests/test_v2_composite.py -v`; expect fixture test pass.

---

## Phase E — BGE reranker baseline

Bodies identical to 2026-04-07 draft Phase E (Tasks E1 / E2 / E3). `BGERerankerScorer.version = "1.0.0"`. Lambda-only embed step; Jetson reads the parquet. Run `pytest classifier/tests/test_bge_reranker.py -v`; expect fixture test pass.

---

## Phase F — Opus 4.6 zero-shot ceiling

Bodies identical to 2026-04-07 draft Phase F (Tasks F1 / F2 / F3). `OpusZeroShotScorer.version = "1.0.0"`. Three temperature samples per pair; majority vote. Reuses Plan 2's `LabelerClient` and cost ledger. Run `pytest classifier/tests/test_opus_zero_shot.py -v`; expect mocked-client test pass.

---

## Phase G — Eval harness + feature cache

Bodies identical to 2026-04-07 draft Phase G (Tasks G1 / G2 / G3 / G4), with these deltas:

- [ ] **Delta G-a: Results JSON schema adds `pool_matrix_size` and `pool_matrix_sha256`.** `pool_matrix_size` = 26; `pool_matrix_sha256` = SHA-256 of `data/candidates/pool_v1.jsonl`. The harness refuses to run if the hash does not match the Plan 1-B hash recorded in `data/splits/hashes.json`.
- [ ] **Delta G-b: Per-scorer output rows include `framework_pair`** so Phase H can pivot without a re-join.

Run: `pytest classifier/tests/test_eval_harness.py classifier/tests/test_feature_cache.py -v`
Expected: all passing.

---

## Phase H — Per-pair scorer coverage diagnostic (new)

### Task H1: `per_pair_coverage.py` — test first

**Files:**
- Create: `classifier/tests/test_per_pair_coverage.py`
- Create: `classifier/baselines/per_pair_coverage.py`

- [ ] **Step 1: Write the failing test**

```python
# classifier/tests/test_per_pair_coverage.py
from classifier.baselines.per_pair_coverage import compute_per_pair_coverage
from classifier.data.candidates import FRAMEWORK_PAIRS


def _fake_records():
    # two pairs, two scorers, one null
    return [
        {"framework_pair": "aiuc_1__owasp_agentic", "scorer_name": "bm25", "score": 0.5, "rank_of_gold": 1},
        {"framework_pair": "aiuc_1__owasp_agentic", "scorer_name": "bge_cosine", "score": 0.7, "rank_of_gold": 2},
        {"framework_pair": "owasp_dsgai__nist_800_53", "scorer_name": "bm25", "score": None, "rank_of_gold": None},
        {"framework_pair": "owasp_dsgai__nist_800_53", "scorer_name": "bge_cosine", "score": 0.3, "rank_of_gold": 5},
    ]


def test_compute_per_pair_coverage_shape():
    out = compute_per_pair_coverage(_fake_records(), framework_pairs=FRAMEWORK_PAIRS)
    assert set(out.keys()) == {f"{a}__{b}" for a, b in FRAMEWORK_PAIRS}
    row = out["aiuc_1__owasp_agentic"]
    assert row["n_rows"] == 1
    assert row["scorers"]["bm25"]["null_rate"] == 0.0
    assert row["scorers"]["bge_cosine"]["null_rate"] == 0.0
    missing_pair = out[f"{FRAMEWORK_PAIRS[-1][0]}__{FRAMEWORK_PAIRS[-1][1]}"]
    assert missing_pair["n_rows"] == 0
    assert missing_pair["under_represented"] is True


def test_all_26_pairs_present():
    out = compute_per_pair_coverage([], framework_pairs=FRAMEWORK_PAIRS)
    assert len(out) == 26
```

- [ ] **Step 2: Run — expect failure**
Run: `pytest classifier/tests/test_per_pair_coverage.py -v`
Expected: ModuleNotFoundError.

- [ ] **Step 3: Implement `classifier/baselines/per_pair_coverage.py`**

```python
"""Per-framework-pair scorer coverage diagnostic.

For each of the 26 Tier-B framework pairs, compute:
  - n_rows: number of llm_val rows in the pair
  - scorers[name].null_rate: fraction of rows where the scorer produced NaN/None
  - scorers[name].rank_of_gold_median: median rank of the gold target
  - under_represented: True if n_rows < 5 (Plan 5 stacker should down-weight)
"""
from __future__ import annotations

from collections import defaultdict
from statistics import median


def compute_per_pair_coverage(records: list[dict], framework_pairs: list[tuple[str, str]]) -> dict:
    by_pair: dict[str, list[dict]] = defaultdict(list)
    for r in records:
        by_pair[r["framework_pair"]].append(r)

    out: dict[str, dict] = {}
    for a, b in framework_pairs:
        key = f"{a}__{b}"
        rows = by_pair.get(key, [])
        scorers = defaultdict(list)
        for r in rows:
            scorers[r["scorer_name"]].append(r)
        pair_rows_by_key = defaultdict(set)
        for r in rows:
            pair_rows_by_key[r["scorer_name"]].add(r.get("pair_key") or id(r))
        n_rows = max((len(v) for v in pair_rows_by_key.values()), default=0)
        scorer_out: dict[str, dict] = {}
        for name, lst in scorers.items():
            nulls = sum(1 for r in lst if r.get("score") is None)
            ranks = [r["rank_of_gold"] for r in lst if r.get("rank_of_gold") is not None]
            scorer_out[name] = {
                "null_rate": (nulls / len(lst)) if lst else 0.0,
                "rank_of_gold_median": float(median(ranks)) if ranks else None,
                "n": len(lst),
            }
        out[key] = {
            "n_rows": n_rows,
            "scorers": scorer_out,
            "under_represented": n_rows < 5,
        }
    return out
```

- [ ] **Step 4: Run — expect pass**
Run: `pytest classifier/tests/test_per_pair_coverage.py -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**
```bash
git add classifier/baselines/per_pair_coverage.py classifier/tests/test_per_pair_coverage.py
git commit -m "plan3: per-pair scorer coverage diagnostic across 26-pair matrix"
```

### Task H2: `build_per_pair_coverage.py` CLI

**Files:**
- Create: `classifier/scripts/build_per_pair_coverage.py`

- [ ] **Step 1: Implement**

```python
"""CLI: emit data/features/per_pair_coverage.json from the latest baseline run."""
from __future__ import annotations

import argparse, json
from pathlib import Path

from classifier.data.splits import verify_hashes
from classifier.data.candidates import FRAMEWORK_PAIRS
from classifier.baselines.per_pair_coverage import compute_per_pair_coverage


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=Path("data/features/per_pair_coverage.json"))
    args = ap.parse_args()
    verify_hashes()
    records: list[dict] = []
    for p in sorted(args.run_dir.glob("*_records.jsonl")):
        for line in p.read_text().splitlines():
            records.append(json.loads(line))
    out = compute_per_pair_coverage(records, framework_pairs=FRAMEWORK_PAIRS)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, sort_keys=True, ensure_ascii=False, indent=2))
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run on the latest baseline run**

Run: `python -m classifier.scripts.build_per_pair_coverage --run-dir data/baselines/latest`
Expected: `data/features/per_pair_coverage.json` created; `jq 'keys | length' data/features/per_pair_coverage.json` prints `26`.

- [ ] **Step 3: Commit**
```bash
git add classifier/scripts/build_per_pair_coverage.py data/features/per_pair_coverage.json
git commit -m "plan3: per-pair coverage diagnostic CLI + first run output"
```

---

## Phase I — Retrieval-floor gate re-run (new)

### Task I1: Retrieval-floor parity gate — test first

**Files:**
- Create: `classifier/tests/test_retrieval_floor_gate.py`
- Create: `classifier/scripts/run_retrieval_floor_plan3_rerun.py`

- [ ] **Step 1: Write the failing test**

```python
# classifier/tests/test_retrieval_floor_gate.py
import json
from classifier.config import CANDIDATES_DIR

BASELINE = {"coverage_at_20": 0.65, "coverage_at_k_used": 0.8825, "k_used": 100}


def test_plan1b_baseline_present():
    report = json.loads((CANDIDATES_DIR / "retrieval_floor_report.json").read_text())
    for k, v in BASELINE.items():
        assert report[k] == v, f"{k}: {report[k]} != {v}"
```

- [ ] **Step 2: Run — expect pass (baseline already on disk from Plan 1-B)**
Run: `pytest classifier/tests/test_retrieval_floor_gate.py -v`
Expected: 1 passed.

- [ ] **Step 3: Implement the Plan 3 re-run CLI**

```python
"""CLI: re-run classifier.data.retrieval_floor.check_floor and assert parity
with the Plan 1-B baseline (coverage_at_20=0.6500, coverage_at_k_used=0.8825).

Invoked whenever Plan 2 publishes new silver labels that change the llm_val
denominator. The frozen-test denominator is NEVER altered.
"""
from __future__ import annotations

import argparse, json, datetime as dt
from pathlib import Path

from classifier.config import CANDIDATES_DIR
from classifier.data.splits import verify_hashes
from classifier.data.retrieval_floor import check_floor

BASELINE = {"coverage_at_20": 0.65, "coverage_at_k_used": 0.8825}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--k-initial", type=int, default=20)
    ap.add_argument("--k-max", type=int, default=100)
    args = ap.parse_args()
    verify_hashes()
    report = check_floor(k_initial=args.k_initial, k_max=args.k_max, from_disk=True)
    drift = {k: (report[k], BASELINE[k]) for k in BASELINE if report[k] != BASELINE[k]}
    ts = dt.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    out = CANDIDATES_DIR / f"retrieval_floor_report_plan3_rerun_{ts}.json"
    out.write_text(json.dumps({"report": report, "drift": drift}, sort_keys=True, ensure_ascii=False, indent=2))
    if drift:
        raise SystemExit(f"retrieval-floor drift detected vs Plan 1-B baseline: {drift}")
    print(f"parity OK; wrote {out}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the gate**

Run: `python -m classifier.scripts.run_retrieval_floor_plan3_rerun`
Expected: `parity OK; wrote data/candidates/retrieval_floor_report_plan3_rerun_<ts>.json` and exit code 0.

- [ ] **Step 5: Commit**
```bash
git add classifier/tests/test_retrieval_floor_gate.py classifier/scripts/run_retrieval_floor_plan3_rerun.py data/candidates/retrieval_floor_report_plan3_rerun_*.json
git commit -m "plan3: retrieval-floor parity gate vs Plan 1-B baseline"
```

---

## Phase J — Dead-code audit for the 12-pair era

### Task J1: Grep guard — test first

**Files:**
- Create: `classifier/tests/test_no_12_pair_deadcode.py`

- [ ] **Step 1: Write the test**

```python
# classifier/tests/test_no_12_pair_deadcode.py
import re
from pathlib import Path

FORBIDDEN = [
    re.compile(r"FRAMEWORK_PAIRS\[:12\]"),
    re.compile(r"range\(\s*12\s*\).*pair", re.IGNORECASE),
    re.compile(r"assert\s+len\(\s*FRAMEWORK_PAIRS\s*\)\s*==\s*12"),
]

ROOT = Path(__file__).resolve().parents[2]
SCAN_DIRS = [ROOT / "classifier", ROOT / "mapping_engine"]


def test_no_12_pair_literals():
    hits: list[str] = []
    for d in SCAN_DIRS:
        if not d.exists():
            continue
        for py in d.rglob("*.py"):
            if py.name == "test_no_12_pair_deadcode.py":
                continue
            text = py.read_text(errors="ignore")
            for rx in FORBIDDEN:
                if rx.search(text):
                    hits.append(f"{py}: {rx.pattern}")
    assert not hits, "12-pair-era dead code found:\n" + "\n".join(hits)
```

- [ ] **Step 2: Run — expect pass**
Run: `pytest classifier/tests/test_no_12_pair_deadcode.py -v`
Expected: 1 passed. If it fails, the listed files must be updated to use the 26-pair matrix before the phase can close.

- [ ] **Step 3: Commit**
```bash
git add classifier/tests/test_no_12_pair_deadcode.py
git commit -m "plan3: CI guard against 12-pair-era dead code"
```

---

## Phase K — Handoff

### Task K1: Full-ladder eval run on llm_val (26-pair pool)

- [ ] **Step 1: Run the harness**

Run: `python -m classifier.scripts.run_all_baselines_eval --pool data/candidates/pool_v1.jsonl --llm-val data/labels/llm_sme/v1_frozen/llm_val.jsonl --out-dir data/baselines/run_$(date +%Y%m%d_%H%M%S)`
Expected: `results_llm_val.json` written; `pool_matrix_size == 26`; `pool_matrix_sha256` matches `data/splits/hashes.json`.

- [ ] **Step 2: Refresh per-pair coverage**

Run: `python -m classifier.scripts.build_per_pair_coverage --run-dir data/baselines/latest`
Expected: `data/features/per_pair_coverage.json` rewritten; `jq '[.[] | select(.under_represented)] | length' data/features/per_pair_coverage.json` printed for awareness.

- [ ] **Step 3: Build the feature cache**

Run: `python -m classifier.scripts.build_baseline_feature_cache --run-dir data/baselines/latest --out data/features/baseline_features.parquet`
Expected: parquet written; row count equals llm_val row count.

- [ ] **Step 4: Run the full Plan 3 test battery**

Run: `pytest classifier/tests/test_scorer_protocol.py classifier/tests/test_registry.py classifier/tests/test_bm25.py classifier/tests/test_bge_cosine.py classifier/tests/test_v2_composite.py classifier/tests/test_bge_reranker.py classifier/tests/test_opus_zero_shot.py classifier/tests/test_eval_harness.py classifier/tests/test_feature_cache.py classifier/tests/test_per_pair_coverage.py classifier/tests/test_retrieval_floor_gate.py classifier/tests/test_no_12_pair_deadcode.py -v`
Expected: all passing.

### Task K2: Handoff summary

**Files:**
- Create: `classifier/BASELINES_COMPLETE.md`

- [ ] **Step 1: Write the handoff doc**

Contents MUST include:
- Scorer name → version table
- Headline metrics (R@1 / R@3 / R@5 / MRR / tier-acc) per scorer on llm_val
- Pool matrix: 26 pairs, `pool_v1.jsonl` SHA-256 from `data/splits/hashes.json`
- Retrieval-floor parity: `coverage_at_20 = 0.6500`, `coverage_at_k_used(100) = 0.8825` (unchanged vs Plan 1-B baseline)
- Pointer to `data/features/baseline_features.parquet` for Plan 5
- Pointer to `data/features/per_pair_coverage.json` for Plan 5 stacker weighting and Plan 8 paper
- Explicit note: lifting the 0.6500 ceiling is Phase 2/3 reranker work, NOT Plan 3

- [ ] **Step 2: Commit**
```bash
git add classifier/BASELINES_COMPLETE.md
git commit -m "plan3: handoff summary"
```

---

## Self-review

Mapping tasks to spec items:

- **§7 Plan 3 bullet — "Pair enumeration grows to the Tier-B source × target matrix":** honored by consuming `classifier.data.candidates.FRAMEWORK_PAIRS` (len = 26) in every CLI and fixture; Phase J forbids 12-pair literals; Phase H builds a per-pair diagnostic covering all 26 pairs.
- **§7 Plan 3 bullet — "Retrieval floor report re-run on the enlarged matrix":** honored by Phase I's `run_retrieval_floor_plan3_rerun.py` + parity gate against the Plan 1-B baseline (`0.6500` / `0.8825`). Frozen test is read-only.
- **§5 Tier-B scope (3 source lists × current 9 + required new targets, ~26 pairs):** honored — Phase 3 never redefines pairs and defers to `classifier/data/candidates.py` as the single source of truth.
- **§6 evaluation strategy — frozen test untouched:** honored — every CLI runs against `llm_val` (Plan 2) and the retrieval-floor report (Plan 1-B artifact); no Plan 3 code opens `human_test_frozen.jsonl` for mutation.
- **§9 out-of-scope (no re-freezing / no scope creep into reranker work):** honored — the 0.6500 / 0.8825 ceiling is documented as architectural, Phase 2/3 reranker improvements are explicitly deferred per `project_tier23_retrieval_deferred.md`.
- **Lesson 1 (scoring-path drift):** `BGECosineScorer.version = "2.0.0"` reflects the bge-base-en-v1.5 switch versus the 2026-04-07 draft's bge-large assumption. Harness refuses to overwrite a `(scorer_name, scorer_version)` result file.
- **Cross-plan contracts 1 / 2 / 3 / 4 / 7:** honored per the "Cross-plan contracts honored" section above.
- **Anti-scope rules from the task brief:** no upstream integration work, no contamination logic, no frozen-test mutation, no reranker-ladder scope, no "Tier 2/3 retrieval improvements," no pool rebuild, no new embedding model.
