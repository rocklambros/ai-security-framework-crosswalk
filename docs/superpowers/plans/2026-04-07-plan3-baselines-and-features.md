# Plan 3 — Baselines & Feature Cache Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stand up the comparison ladder — rows 1–5 of the spec §1.3 baseline table (BM25, `bge-large-en-v1.5` cosine zero-shot, v2 composite, `bge-reranker-v2-m3` zero-shot, Opus 4.6 zero-shot ceiling) — behind a uniform `Scorer` protocol + registry so Plans 4–5 can register learned models without touching the eval harness. Emit a per-pair feature cache consumed by Plan 5's stacker.

**Architecture:** A new `classifier/baselines/` subpackage. Every baseline implements a single `Scorer` Protocol (pairs → list[ScoreRecord]); a module-level registry lists all scorers discoverable by name. Two "heavy" baselines (bge cosine, bge-reranker) run on Lambda A100; embeddings / per-pair scores are cached to parquet under `data/baselines/` and loaded on the Jetson for the eval harness. The Opus 4.6 zero-shot ceiling reuses Plan 2's `LabelerClient` with a single "unbiased expert" prompt and three temperature samples per pair (majority vote). The eval harness loads `llm_val` from Plan 2 and writes one JSON results file per run. The final feature cache is a wide parquet (`pair_key × scorer_name`) that Plan 5's stacker reads directly.

**Tech Stack:** Python 3.11, `rank_bm25==0.2.2`, `pyarrow==17.0.0`, `sentence-transformers==3.2.1` (pinned in Plan 1), `torch`, `FlagEmbedding==1.3.2` for the bge-reranker-v2-m3, existing `classifier/` scaffolding from Plans 1–2, existing `mapping_engine.engine.mapper`, `pytest`.

---

## Spec Reference

Implements §1.3 rows 1–5 of `docs/superpowers/specs/2026-04-07-ai-security-crosswalk-classifier-design.md` (BM25, bge-large cosine, v2 composite, bge-reranker-v2-m3, Opus zero-shot ceiling), §3.5 (compute budget — zero-shot baselines line ~$15 + Opus ceiling $60–100), §4.1 (evaluation metrics: R@1/R@3/R@5/MRR/tier-acc used by the harness), and §6 honesty commitments #1 (`human_test_frozen` untouched — Plan 3 evaluates on `llm_val`, never frozen), #6 (failed scorers still reported), #8 (scorer code committed with pinned hyperparameters).

**Out of scope for Plan 3:** any learned model training (Plan 4), stacked meta-learner + conformal wrapper (Plan 5), any run against `human_test_frozen` (Plan 6), Dash app (Plan 7), writeup (Plan 8).

---

## Lessons Carried from Plans 1 & 2

These failure modes shaped Plan 3's design:

1. **Scoring-path drift** (the s8-np `--no-rerank` bug). Plan 3's `Scorer` Protocol requires a `version: str` attribute that MUST bump on any scoring change. The eval harness writes `{scorer_name, scorer_version}` into every `ScoreRecord` and into the baseline results JSON so a silent algorithmic drift cannot masquerade as the same scorer.
2. **Byte-stable JSON outputs** (Plan 1's `hashes.json` canary). The baselines results JSON uses `json.dumps(..., sort_keys=True, ensure_ascii=False, indent=2)` so git diffs are meaningful. The parquet feature cache uses `pyarrow` with `use_dictionary=False, compression="snappy"` for deterministic bytes.
3. **No in-place overwrites** (Session 8's YAML-mutation bug). Plan 3 never rewrites `data/baselines/*` or `data/features/*` in place. Any re-run lands under a new subdir (`data/baselines/run_YYYYMMDD_HHMMSS/`) and a symlink `data/baselines/latest` is updated only after the full harness completes and all tests pass.
4. **Scorer version bumping.** `BM25Scorer.version = "1.0.0"` etc. — if any implementation constant changes (tokenizer, k1, b, embedding model revision pin), the version string is bumped BEFORE the next run. Task G2's harness refuses to overwrite an existing results file with the same `(scorer_name, scorer_version)`.
5. **Feasibility math as test.** Every baseline has a `test_*_runs_on_fixture` test with a 5-pair fixture before any Lambda or Opus spend.

---

## Cross-plan contracts honored

1. **Contract 1 — `verify_hashes()` at every CLI entry point.** Every script in `classifier/scripts/` for Plan 3 calls `classifier.data.splits.verify_hashes()` as its first line after argparse.
2. **Contract 2 — pool versioning.** Plan 3 consumes `data/pool/pool_v2/` (spec: `data/candidates/pool_v2.jsonl`) from Plan 2 exclusively. `pool_v1` is never touched.
3. **Contract 3 — never overwrite.** Output directories are versioned (`data/baselines/run_<ts>/`, `data/features/baseline_features_v<scorer_set_hash>.parquet`).
4. **Contract 4 — Scorer Protocol.** Defined in Phase A below; exported from `classifier.baselines.protocol`. Plans 4–5 register learned models against it with no modification to the registry module.
5. **Contract 7 — every API call appends to `data/cost_ledger.jsonl`.** Phase F (Opus ceiling) reuses Plan 2's `LabelerClient` so ledger writes happen for free.

---

## File Structure

| Path | Purpose |
|---|---|
| `classifier/baselines/__init__.py` | Subpackage marker, re-exports `Scorer`, `NodePair`, `ScoreRecord`, `REGISTRY` |
| `classifier/baselines/protocol.py` | `Scorer` Protocol + `NodePair` + `ScoreRecord` dataclasses |
| `classifier/baselines/registry.py` | `register(scorer)` + `get(name)` + `all_scorers()` |
| `classifier/baselines/bm25.py` | `BM25Scorer` (rank_bm25) |
| `classifier/baselines/bge_cosine.py` | `BGECosineScorer` — reads cached embeddings parquet |
| `classifier/baselines/v2_composite.py` | `V2CompositeScorer` — wraps `mapping_engine.engine.mapper` |
| `classifier/baselines/bge_reranker.py` | `BGERerankerScorer` — reads cached per-pair scores parquet |
| `classifier/baselines/opus_zero_shot.py` | `OpusZeroShotScorer` — reuses Plan 2's `LabelerClient` |
| `classifier/baselines/eval_harness.py` | Load llm_val, run all registered scorers, compute R@K / MRR / tier-acc |
| `classifier/baselines/feature_cache.py` | Emit wide parquet (pair_key × scorer_name) |
| `classifier/config/llm_sme_prompts/v1/unbiased_expert.j2` | Single-persona ceiling prompt |
| `classifier/tests/test_scorer_protocol.py` | Protocol shape + dataclass tests |
| `classifier/tests/test_registry.py` | Register/get/duplicate-name tests |
| `classifier/tests/test_bm25.py` | BM25 on 5-pair fixture |
| `classifier/tests/test_bge_cosine.py` | Cached-embedding loader + cosine math |
| `classifier/tests/test_v2_composite.py` | Wraps mapping_engine, returns ScoreRecords |
| `classifier/tests/test_bge_reranker.py` | Cached-score loader + shape |
| `classifier/tests/test_opus_zero_shot.py` | LabelerClient mock + 3-sample majority vote |
| `classifier/tests/test_eval_harness.py` | Metrics math + JSON schema |
| `classifier/tests/test_feature_cache.py` | Wide parquet shape + nullability |
| `classifier/scripts/run_bm25_baseline.py` | CLI: BM25 on llm_val → results JSON |
| `classifier/scripts/build_bge_embeddings_lambda.py` | CLI (Lambda): encode all nodes, write parquet |
| `classifier/scripts/run_bge_cosine_baseline.py` | CLI: bge cosine on llm_val → results JSON |
| `classifier/scripts/run_v2_composite_baseline.py` | CLI: v2 on llm_val → results JSON |
| `classifier/scripts/build_bge_reranker_scores_lambda.py` | CLI (Lambda): batch-score all pairs |
| `classifier/scripts/run_bge_reranker_baseline.py` | CLI: bge-reranker on llm_val → results JSON |
| `classifier/scripts/run_opus_ceiling_baseline.py` | CLI: Opus 4.6 on llm_val × 3 samples |
| `classifier/scripts/run_all_baselines_eval.py` | CLI: eval harness over the full registry |
| `classifier/scripts/build_baseline_feature_cache.py` | CLI: emit wide parquet for Plan 5 |
| `data/baselines/bge_cosine_embeddings.parquet` | Cached node embeddings (Lambda-produced) |
| `data/baselines/bge_reranker_scores.parquet` | Cached per-pair cross-encoder scores (Lambda) |
| `data/baselines/run_<ts>/results_llm_val.json` | Eval harness headline numbers |
| `data/baselines/latest` | Symlink to most recent run dir |
| `data/features/baseline_features.parquet` | Wide pair×scorer parquet for Plan 5 stacker |
| `classifier/BASELINES_COMPLETE.md` | Phase I handoff summary |
| `requirements-classifier.txt` | Append `rank_bm25`, `pyarrow`, `FlagEmbedding` |

**Do not modify** any file under `mapping_engine/` (Plan 3 imports it read-only), `data/splits/`, `data/labels/llm_sme/v1_frozen/` (Plan 2 frozen outputs), or Plan 2's `classifier/labeling/`.

---

## Phase A — Scorer protocol, dataclasses, registry

### Task A1: Dataclasses and Scorer Protocol — test first

**Files:**
- Create: `classifier/baselines/__init__.py` (empty)
- Create: `classifier/tests/test_scorer_protocol.py`
- Create: `classifier/baselines/protocol.py`

- [ ] **Step 1: Append deps to `requirements-classifier.txt`**

```
# Plan 3 additions
rank_bm25==0.2.2
pyarrow==17.0.0
FlagEmbedding==1.3.2
```

- [ ] **Step 2: Install and smoke test**

Run: `source .venv/bin/activate && pip install -r requirements-classifier.txt && python -c "import rank_bm25, pyarrow; print(rank_bm25.__version__ if hasattr(rank_bm25,'__version__') else 'ok', pyarrow.__version__)"`
Expected: version string, no ImportError. `FlagEmbedding` import may be skipped on Jetson — it is only required on Lambda; the import smoke is guarded by `try/except` in `classifier/baselines/bge_reranker.py`.

- [ ] **Step 3: Write the failing test**

`classifier/tests/test_scorer_protocol.py`:
```python
from classifier.baselines.protocol import NodePair, ScoreRecord, Scorer


def test_nodepair_fields():
    p = NodePair(
        pair_key="aiuc-1:C-1.2__owasp-agentic:ASI-03",
        source_node_id="aiuc-1:C-1.2",
        source_framework="aiuc-1",
        source_text="source control text",
        target_node_id="owasp-agentic:ASI-03",
        target_framework="owasp-agentic",
        target_text="target control text",
    )
    assert p.pair_key.startswith("aiuc-1:")
    assert p.source_framework == "aiuc-1"


def test_score_record_fields():
    r = ScoreRecord(
        pair_key="a__b",
        scorer_name="bm25",
        scorer_version="1.0.0",
        score=0.42,
        tier_pred=None,
        tier_probs=None,
        extras={},
    )
    assert r.score == 0.42
    assert r.tier_pred is None


def test_scorer_protocol_structural():
    class Dummy:
        name = "dummy"
        version = "0.0.0"
        def score(self, pairs):
            return [ScoreRecord(pair_key=p.pair_key, scorer_name=self.name,
                                scorer_version=self.version, score=0.0,
                                tier_pred=None, tier_probs=None, extras={}) for p in pairs]
    d: Scorer = Dummy()  # structural subtyping check
    assert d.name == "dummy"
    out = d.score([])
    assert out == []
```

- [ ] **Step 4: Run — expect failure**

Run: `pytest classifier/tests/test_scorer_protocol.py -v`
Expected: `ModuleNotFoundError: No module named 'classifier.baselines.protocol'`

- [ ] **Step 5: Implement `classifier/baselines/protocol.py`**

```python
"""Scorer Protocol + NodePair + ScoreRecord dataclasses.

Contract 4: Plans 4–5 register learned models against this Protocol without
modifying this module. Every Scorer MUST expose name (stable identifier) and
version (bump on any algorithmic change) — the eval harness refuses to overwrite
a results file with the same (name, version) pair.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class NodePair:
    pair_key: str
    source_node_id: str
    source_framework: str
    source_text: str
    target_node_id: str
    target_framework: str
    target_text: str


@dataclass
class ScoreRecord:
    pair_key: str
    scorer_name: str
    scorer_version: str
    score: float
    tier_pred: str | None
    tier_probs: dict[str, float] | None
    extras: dict = field(default_factory=dict)


@runtime_checkable
class Scorer(Protocol):
    name: str
    version: str

    def score(self, pairs: list[NodePair]) -> list[ScoreRecord]: ...
```

- [ ] **Step 6: Run — expect pass**

Run: `pytest classifier/tests/test_scorer_protocol.py -v`
Expected: 3 passed.

- [ ] **Step 7: Commit**

```bash
git add classifier/baselines/__init__.py classifier/baselines/protocol.py classifier/tests/test_scorer_protocol.py requirements-classifier.txt
git commit -m "plan3: Scorer protocol + NodePair + ScoreRecord dataclasses"
```

### Task A2: Registry — test first

**Files:**
- Create: `classifier/tests/test_registry.py`
- Create: `classifier/baselines/registry.py`

- [ ] **Step 1: Write the failing test**

```python
# classifier/tests/test_registry.py
import pytest
from classifier.baselines.protocol import ScoreRecord
from classifier.baselines import registry


class _Fake:
    def __init__(self, name, version="1.0.0"):
        self.name = name; self.version = version
    def score(self, pairs):
        return []


def setup_function(_):
    registry._REGISTRY.clear()


def test_register_and_get():
    s = _Fake("bm25")
    registry.register(s)
    assert registry.get("bm25") is s


def test_register_duplicate_name_raises():
    registry.register(_Fake("bm25"))
    with pytest.raises(ValueError, match="already registered"):
        registry.register(_Fake("bm25"))


def test_all_scorers_stable_order():
    registry.register(_Fake("bm25"))
    registry.register(_Fake("bge_cosine"))
    registry.register(_Fake("v2_composite"))
    names = [s.name for s in registry.all_scorers()]
    assert names == sorted(names)
```

- [ ] **Step 2: Run — expect failure**

Run: `pytest classifier/tests/test_registry.py -v`
Expected: ImportError on `classifier.baselines.registry`.

- [ ] **Step 3: Implement `classifier/baselines/registry.py`**

```python
"""Module-level Scorer registry. Clear in tests via `_REGISTRY.clear()`."""
from __future__ import annotations

from classifier.baselines.protocol import Scorer


_REGISTRY: dict[str, Scorer] = {}


def register(scorer: Scorer) -> None:
    if scorer.name in _REGISTRY:
        raise ValueError(f"Scorer {scorer.name!r} already registered")
    _REGISTRY[scorer.name] = scorer


def get(name: str) -> Scorer:
    if name not in _REGISTRY:
        raise KeyError(f"no scorer named {name!r}; registered: {sorted(_REGISTRY)}")
    return _REGISTRY[name]


def all_scorers() -> list[Scorer]:
    return [_REGISTRY[k] for k in sorted(_REGISTRY)]
```

- [ ] **Step 4: Run — expect pass**

Run: `pytest classifier/tests/test_registry.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add classifier/baselines/registry.py classifier/tests/test_registry.py
git commit -m "plan3: scorer registry with duplicate-name guard"
```

### Task A3: Re-export and fixture pairs

**Files:**
- Modify: `classifier/baselines/__init__.py`
- Create: `classifier/tests/fixtures/pairs_5.jsonl`

- [ ] **Step 1: Write `classifier/baselines/__init__.py`**

```python
"""classifier.baselines — baseline scorers + Scorer protocol."""
from classifier.baselines.protocol import NodePair, ScoreRecord, Scorer
from classifier.baselines import registry

__all__ = ["NodePair", "ScoreRecord", "Scorer", "registry"]
```

- [ ] **Step 2: Create the 5-pair fixture**

`classifier/tests/fixtures/pairs_5.jsonl`:
```json
{"pair_key":"aiuc-1:C-1.1__owasp-agentic:ASI-01","source_node_id":"aiuc-1:C-1.1","source_framework":"aiuc-1","source_text":"Authenticate all agent actions with short-lived credentials.","target_node_id":"owasp-agentic:ASI-01","target_framework":"owasp-agentic","target_text":"Agent identity spoofing: adversary impersonates the agent to downstream tools."}
{"pair_key":"aiuc-1:C-2.3__mitre-atlas:AML.T0051","source_node_id":"aiuc-1:C-2.3","source_framework":"aiuc-1","source_text":"Log all prompts and model outputs with tamper-evident storage.","target_node_id":"mitre-atlas:AML.T0051","target_framework":"mitre-atlas","target_text":"LLM Prompt Injection: adversary crafts input that bypasses model safeguards."}
{"pair_key":"nist-ai-rmf:MG-3.1__owasp-llm:LLM01","source_node_id":"nist-ai-rmf:MG-3.1","source_framework":"nist-ai-rmf","source_text":"Monitor for emergent risks and incidents across the AI lifecycle.","target_node_id":"owasp-llm:LLM01","target_framework":"owasp-llm","target_text":"Prompt injection vulnerabilities."}
{"pair_key":"csa-aicm:MLC-01__cosai:SEC-001","source_node_id":"csa-aicm:MLC-01","source_framework":"csa-aicm","source_text":"Maintain an inventory of training datasets with provenance metadata.","target_node_id":"cosai:SEC-001","target_framework":"cosai","target_text":"Data supply-chain integrity controls for model training."}
{"pair_key":"eu-gpai:OBL-7__owasp-ai-exchange:AIEX-12","source_node_id":"eu-gpai:OBL-7","source_framework":"eu-gpai","source_text":"General-purpose AI providers shall disclose a summary of training data.","target_node_id":"owasp-ai-exchange:AIEX-12","target_framework":"owasp-ai-exchange","target_text":"Training data documentation and disclosure controls."}
```

- [ ] **Step 3: Commit**

```bash
git add classifier/baselines/__init__.py classifier/tests/fixtures/pairs_5.jsonl
git commit -m "plan3: baselines package re-exports + 5-pair fixture"
```

---

## Phase B — BM25 baseline

### Task B1: BM25Scorer — test first

**Files:**
- Create: `classifier/tests/test_bm25.py`
- Create: `classifier/baselines/bm25.py`

- [ ] **Step 1: Write the failing test**

```python
# classifier/tests/test_bm25.py
import json
from pathlib import Path
from classifier.baselines.bm25 import BM25Scorer
from classifier.baselines.protocol import NodePair


FIXTURE = Path(__file__).parent / "fixtures" / "pairs_5.jsonl"


def _load_pairs():
    return [NodePair(**json.loads(l)) for l in FIXTURE.read_text().splitlines()]


def test_bm25_runs_on_fixture():
    s = BM25Scorer()
    assert s.name == "bm25"
    assert s.version == "1.0.0"
    records = s.score(_load_pairs())
    assert len(records) == 5
    assert all(r.scorer_name == "bm25" for r in records)
    assert all(isinstance(r.score, float) for r in records)
    assert all(r.tier_pred is None for r in records)


def test_bm25_deterministic():
    s = BM25Scorer()
    pairs = _load_pairs()
    r1 = [r.score for r in s.score(pairs)]
    r2 = [r.score for r in s.score(pairs)]
    assert r1 == r2
```

- [ ] **Step 2: Run — expect failure**

Run: `pytest classifier/tests/test_bm25.py -v`
Expected: ModuleNotFoundError on `classifier.baselines.bm25`.

- [ ] **Step 3: Implement `classifier/baselines/bm25.py`**

```python
"""BM25 baseline (rank_bm25). Row 1 of §1.3.

Score definition: for each pair, tokenize the source text as a query and
tokenize the target text as a 1-doc corpus; the BM25 score of the target
against the source is the scalar. This is a *pair* scorer, not a retrieval
scorer — we evaluate how well BM25 relevance ranks the true target among
distractors in the eval harness.
"""
from __future__ import annotations

import re
from classifier.baselines.protocol import NodePair, ScoreRecord
from rank_bm25 import BM25Okapi


_TOKEN_RE = re.compile(r"[A-Za-z0-9]+")


def _tokenize(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text)]


class BM25Scorer:
    name = "bm25"
    version = "1.0.0"

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b

    def score(self, pairs: list[NodePair]) -> list[ScoreRecord]:
        out: list[ScoreRecord] = []
        for p in pairs:
            query = _tokenize(p.source_text)
            corpus = [_tokenize(p.target_text)]
            bm25 = BM25Okapi(corpus, k1=self.k1, b=self.b)
            s = float(bm25.get_scores(query)[0])
            out.append(ScoreRecord(
                pair_key=p.pair_key, scorer_name=self.name, scorer_version=self.version,
                score=s, tier_pred=None, tier_probs=None,
                extras={"k1": self.k1, "b": self.b},
            ))
        return out
```

- [ ] **Step 4: Run — expect pass**

Run: `pytest classifier/tests/test_bm25.py -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add classifier/baselines/bm25.py classifier/tests/test_bm25.py
git commit -m "plan3: BM25 baseline scorer (rank_bm25)"
```

### Task B2: BM25 registration + CLI

**Files:**
- Create: `classifier/scripts/run_bm25_baseline.py`

- [ ] **Step 1: Write the CLI**

```python
"""CLI: run BM25 baseline on llm_val; write a results JSON.

Honors Contract 1 (verify_hashes), Contract 3 (versioned output dir).
"""
from __future__ import annotations

import argparse, json
from datetime import datetime, timezone
from pathlib import Path

from classifier.config import DATA_DIR
from classifier.data.splits import verify_hashes
from classifier.baselines import registry
from classifier.baselines.bm25 import BM25Scorer
from classifier.baselines.eval_harness import load_llm_val_pairs, evaluate_scorer, write_results


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-root", default=str(DATA_DIR / "baselines"))
    args = ap.parse_args()

    verify_hashes()  # Contract 1

    scorer = BM25Scorer()
    try:
        registry.register(scorer)
    except ValueError:
        pass  # already registered in the running process

    pairs, gold = load_llm_val_pairs()
    result = evaluate_scorer(scorer, pairs, gold)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    run_dir = Path(args.out_root) / f"run_{ts}_bm25"
    write_results(run_dir, {scorer.name: result})
    print(f"wrote {run_dir}/results_llm_val.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Dry-run (harness not yet built — expect ImportError)**

Run: `python -m classifier.scripts.run_bm25_baseline --help`
Expected: `ImportError` because `eval_harness` is not yet implemented. This is fine — Task G1 builds it and we will re-run this CLI in Task G3.

- [ ] **Step 3: Commit the CLI skeleton**

```bash
git add classifier/scripts/run_bm25_baseline.py
git commit -m "plan3: BM25 CLI entry point (harness pending Task G1)"
```

---

## Phase C — bge-large-en-v1.5 cosine zero-shot

### Task C1: Lambda embeddings script

**Files:**
- Create: `classifier/scripts/build_bge_embeddings_lambda.py`

This script runs on Lambda (GPU). It reads every node in `data/processed/nodes.json`, encodes with `BAAI/bge-large-en-v1.5`, and writes a parquet with columns `[node_id, framework, embedding_f32]` where `embedding_f32` is a 1024-dim list. Output: `data/baselines/bge_cosine_embeddings.parquet`.

- [ ] **Step 1: Write the script**

```python
"""Encode all 983 nodes with bge-large-en-v1.5 and cache to parquet.

Run on Lambda A100. ~3 minutes of GPU time. Idempotent: refuses to overwrite.
"""
from __future__ import annotations

import argparse, json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
from sentence_transformers import SentenceTransformer

from classifier.config import REPO_ROOT, DATA_DIR
from classifier.data.splits import verify_hashes


MODEL_NAME = "BAAI/bge-large-en-v1.5"
OUT_PATH = DATA_DIR / "baselines" / "bge_cosine_embeddings.parquet"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    verify_hashes()  # Contract 1

    if OUT_PATH.exists() and not args.force:
        print(f"SKIP: {OUT_PATH} exists; pass --force to rewrite")
        return 0

    nodes = json.loads((REPO_ROOT / "data" / "processed" / "nodes.json").read_text())
    ids = [n["id"] for n in nodes]
    frameworks = [n["framework"] for n in nodes]
    texts = [n["text"] for n in nodes]

    model = SentenceTransformer(MODEL_NAME, device="cuda")
    embs = model.encode(texts, batch_size=64, normalize_embeddings=True,
                        convert_to_numpy=True, show_progress_bar=True).astype(np.float32)

    table = pa.table({
        "node_id": ids,
        "framework": frameworks,
        "embedding_f32": [e.tolist() for e in embs],
    })
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, OUT_PATH, compression="snappy", use_dictionary=False)

    meta = {
        "model": MODEL_NAME,
        "n_nodes": len(ids),
        "dim": int(embs.shape[1]),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    (OUT_PATH.with_suffix(".meta.json")).write_text(json.dumps(meta, sort_keys=True, indent=2))
    print(f"wrote {OUT_PATH} ({len(ids)} rows, dim {embs.shape[1]})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Commit (runs on Lambda later)**

```bash
git add classifier/scripts/build_bge_embeddings_lambda.py
git commit -m "plan3: Lambda script to cache bge-large-en-v1.5 node embeddings"
```

### Task C2: BGECosineScorer — test first

**Files:**
- Create: `classifier/tests/test_bge_cosine.py`
- Create: `classifier/baselines/bge_cosine.py`

- [ ] **Step 1: Write the failing test**

```python
# classifier/tests/test_bge_cosine.py
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from classifier.baselines.bge_cosine import BGECosineScorer
from classifier.baselines.protocol import NodePair


def _make_fixture_parquet(tmp_path):
    rng = np.random.default_rng(0)
    ids = ["aiuc-1:C-1.1", "owasp-agentic:ASI-01", "other:X"]
    embs = rng.standard_normal((3, 8)).astype(np.float32)
    embs /= np.linalg.norm(embs, axis=1, keepdims=True)
    table = pa.table({"node_id": ids, "framework": ["a", "b", "c"],
                      "embedding_f32": [e.tolist() for e in embs]})
    p = tmp_path / "emb.parquet"
    pq.write_table(table, p)
    return p, embs, ids


def test_bge_cosine_matches_numpy(tmp_path):
    p, embs, ids = _make_fixture_parquet(tmp_path)
    s = BGECosineScorer(embeddings_path=p)
    assert s.name == "bge_cosine" and s.version == "1.0.0"
    pair = NodePair(pair_key="aiuc-1:C-1.1__owasp-agentic:ASI-01",
                    source_node_id="aiuc-1:C-1.1", source_framework="aiuc-1",
                    source_text="", target_node_id="owasp-agentic:ASI-01",
                    target_framework="owasp-agentic", target_text="")
    [rec] = s.score([pair])
    expected = float(embs[0] @ embs[1])
    assert abs(rec.score - expected) < 1e-6


def test_missing_node_raises(tmp_path):
    p, _, _ = _make_fixture_parquet(tmp_path)
    s = BGECosineScorer(embeddings_path=p)
    bad = NodePair(pair_key="a__b", source_node_id="nope:1", source_framework="a",
                   source_text="", target_node_id="owasp-agentic:ASI-01",
                   target_framework="b", target_text="")
    with pytest.raises(KeyError, match="nope:1"):
        s.score([bad])
```

- [ ] **Step 2: Run — expect failure**

Run: `pytest classifier/tests/test_bge_cosine.py -v`
Expected: ModuleNotFoundError.

- [ ] **Step 3: Implement `classifier/baselines/bge_cosine.py`**

```python
"""bge-large-en-v1.5 zero-shot cosine. Row 2 of §1.3.

Reads cached embeddings parquet written on Lambda by
`classifier/scripts/build_bge_embeddings_lambda.py`. Embeddings are expected
to be L2-normalized, so cosine == dot product.
"""
from __future__ import annotations

from pathlib import Path
import numpy as np
import pyarrow.parquet as pq

from classifier.baselines.protocol import NodePair, ScoreRecord
from classifier.config import DATA_DIR


DEFAULT_EMB_PATH = DATA_DIR / "baselines" / "bge_cosine_embeddings.parquet"


class BGECosineScorer:
    name = "bge_cosine"
    version = "1.0.0"

    def __init__(self, embeddings_path: Path = DEFAULT_EMB_PATH):
        self.embeddings_path = Path(embeddings_path)
        table = pq.read_table(self.embeddings_path)
        ids = table.column("node_id").to_pylist()
        embs = np.asarray(table.column("embedding_f32").to_pylist(), dtype=np.float32)
        self._index: dict[str, np.ndarray] = {i: e for i, e in zip(ids, embs)}

    def _get(self, node_id: str) -> np.ndarray:
        if node_id not in self._index:
            raise KeyError(f"node_id {node_id!r} not in embeddings cache {self.embeddings_path}")
        return self._index[node_id]

    def score(self, pairs: list[NodePair]) -> list[ScoreRecord]:
        out: list[ScoreRecord] = []
        for p in pairs:
            s = float(self._get(p.source_node_id) @ self._get(p.target_node_id))
            out.append(ScoreRecord(
                pair_key=p.pair_key, scorer_name=self.name, scorer_version=self.version,
                score=s, tier_pred=None, tier_probs=None,
                extras={"embeddings_path": str(self.embeddings_path.name)},
            ))
        return out
```

- [ ] **Step 4: Run — expect pass**

Run: `pytest classifier/tests/test_bge_cosine.py -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add classifier/baselines/bge_cosine.py classifier/tests/test_bge_cosine.py
git commit -m "plan3: bge-large-en-v1.5 cosine zero-shot scorer"
```

### Task C3: BGECosine CLI

**Files:**
- Create: `classifier/scripts/run_bge_cosine_baseline.py`

- [ ] **Step 1: Write the CLI**

```python
"""CLI: run bge-large cosine on llm_val; writes results JSON."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from classifier.config import DATA_DIR
from classifier.data.splits import verify_hashes
from classifier.baselines.bge_cosine import BGECosineScorer
from classifier.baselines.eval_harness import load_llm_val_pairs, evaluate_scorer, write_results


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-root", default=str(DATA_DIR / "baselines"))
    args = ap.parse_args()

    verify_hashes()

    scorer = BGECosineScorer()
    pairs, gold = load_llm_val_pairs()
    result = evaluate_scorer(scorer, pairs, gold)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    run_dir = Path(args.out_root) / f"run_{ts}_bge_cosine"
    write_results(run_dir, {scorer.name: result})
    print(f"wrote {run_dir}/results_llm_val.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Commit**

```bash
git add classifier/scripts/run_bge_cosine_baseline.py
git commit -m "plan3: bge cosine baseline CLI"
```

---

## Phase D — v2 composite (existing mapping_engine)

### Task D1: V2CompositeScorer — test first

**Files:**
- Create: `classifier/tests/test_v2_composite.py`
- Create: `classifier/baselines/v2_composite.py`

- [ ] **Step 1: Write the failing test**

```python
# classifier/tests/test_v2_composite.py
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from classifier.baselines.v2_composite import V2CompositeScorer
from classifier.baselines.protocol import NodePair


FIXTURE = Path(__file__).parent / "fixtures" / "pairs_5.jsonl"


def _load_pairs():
    return [NodePair(**json.loads(l)) for l in FIXTURE.read_text().splitlines()]


def test_v2_composite_wraps_mapper():
    fake = MagicMock()
    fake.score_pair.return_value = {
        "composite_score": 0.73,
        "tier": "Related",
        "tier_probs": {"Direct": 0.2, "Related": 0.6, "None": 0.2},
        "signals": {"bridge": 0.5, "semantic": 0.8, "keyword": 0.3, "function_match": 0.7},
    }
    s = V2CompositeScorer(mapper=fake)
    assert s.name == "v2_composite"
    assert s.version.startswith("2.")
    records = s.score(_load_pairs())
    assert len(records) == 5
    assert fake.score_pair.call_count == 5
    assert all(r.score == 0.73 for r in records)
    assert all(r.tier_pred == "Related" for r in records)
    assert records[0].extras["signals"]["semantic"] == 0.8
```

- [ ] **Step 2: Run — expect failure**

Run: `pytest classifier/tests/test_v2_composite.py -v`
Expected: ModuleNotFoundError.

- [ ] **Step 3: Implement `classifier/baselines/v2_composite.py`**

```python
"""v2 composite baseline — wraps the existing mapping_engine.engine.mapper.

Row 3 of §1.3. This is the current production 4-signal composite
(bridge / semantic / keyword / function_match). The scorer does NOT modify
mapping_engine; it only calls `score_pair` as a read-only client.

Version string: "2." + mapping_engine package version so any mapping_engine
change auto-invalidates cached results.
"""
from __future__ import annotations

from classifier.baselines.protocol import NodePair, ScoreRecord


def _default_mapper():
    from mapping_engine.engine.mapper import Mapper  # lazy import
    return Mapper()


def _mapping_engine_version() -> str:
    try:
        import mapping_engine
        return getattr(mapping_engine, "__version__", "unknown")
    except Exception:
        return "unknown"


class V2CompositeScorer:
    name = "v2_composite"

    def __init__(self, mapper=None):
        self.mapper = mapper if mapper is not None else _default_mapper()
        self.version = "2." + _mapping_engine_version()

    def score(self, pairs: list[NodePair]) -> list[ScoreRecord]:
        out: list[ScoreRecord] = []
        for p in pairs:
            r = self.mapper.score_pair(
                source_id=p.source_node_id, target_id=p.target_node_id,
                source_text=p.source_text, target_text=p.target_text,
                source_framework=p.source_framework, target_framework=p.target_framework,
            )
            out.append(ScoreRecord(
                pair_key=p.pair_key, scorer_name=self.name, scorer_version=self.version,
                score=float(r["composite_score"]),
                tier_pred=r.get("tier"),
                tier_probs=r.get("tier_probs"),
                extras={"signals": r.get("signals", {})},
            ))
        return out
```

- [ ] **Step 4: Run — expect pass**

Run: `pytest classifier/tests/test_v2_composite.py -v`
Expected: 1 passed.

- [ ] **Step 5: Commit**

```bash
git add classifier/baselines/v2_composite.py classifier/tests/test_v2_composite.py
git commit -m "plan3: v2 composite baseline wrapping mapping_engine.mapper"
```

### Task D2: V2 composite CLI

**Files:**
- Create: `classifier/scripts/run_v2_composite_baseline.py`

- [ ] **Step 1: Write the CLI**

```python
"""CLI: run v2 composite on llm_val; writes results JSON."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from classifier.config import DATA_DIR
from classifier.data.splits import verify_hashes
from classifier.baselines.v2_composite import V2CompositeScorer
from classifier.baselines.eval_harness import load_llm_val_pairs, evaluate_scorer, write_results


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-root", default=str(DATA_DIR / "baselines"))
    args = ap.parse_args()

    verify_hashes()

    scorer = V2CompositeScorer()
    pairs, gold = load_llm_val_pairs()
    result = evaluate_scorer(scorer, pairs, gold)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    run_dir = Path(args.out_root) / f"run_{ts}_v2_composite"
    write_results(run_dir, {scorer.name: result})
    print(f"wrote {run_dir}/results_llm_val.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Commit**

```bash
git add classifier/scripts/run_v2_composite_baseline.py
git commit -m "plan3: v2 composite baseline CLI"
```

---

## Phase E — bge-reranker-v2-m3 zero-shot

### Task E1: Lambda batch inference script

**Files:**
- Create: `classifier/scripts/build_bge_reranker_scores_lambda.py`

This runs on Lambda (GPU). It reads `data/candidates/pool_v2.jsonl` (Contract 2 — Plan 2's pool), scores every (source, candidate_target) pair with `BAAI/bge-reranker-v2-m3`, and writes `data/baselines/bge_reranker_scores.parquet` with columns `[pair_key, source_node_id, target_node_id, score_f32]`. Budget: ~50k pair evaluations × 0.8s/pair batched at 32 → ~20 min A100 ≈ $3.

- [ ] **Step 1: Write the script**

```python
"""Batch-score all pool_v2 (source, target_topk) pairs with bge-reranker-v2-m3.

Run on Lambda A100. ~20 min. Idempotent: refuses to overwrite.
"""
from __future__ import annotations

import argparse, json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from classifier.config import REPO_ROOT, DATA_DIR
from classifier.data.splits import verify_hashes


MODEL_NAME = "BAAI/bge-reranker-v2-m3"
POOL_PATH = DATA_DIR / "candidates" / "pool_v2.jsonl"
OUT_PATH = DATA_DIR / "baselines" / "bge_reranker_scores.parquet"


def _load_node_text() -> dict[str, str]:
    nodes = json.loads((REPO_ROOT / "data" / "processed" / "nodes.json").read_text())
    return {n["id"]: n["text"] for n in nodes}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--batch-size", type=int, default=32)
    args = ap.parse_args()

    verify_hashes()

    if OUT_PATH.exists() and not args.force:
        print(f"SKIP: {OUT_PATH} exists; pass --force to rewrite")
        return 0

    from FlagEmbedding import FlagReranker
    reranker = FlagReranker(MODEL_NAME, use_fp16=True)

    node_text = _load_node_text()
    rows = []
    with open(POOL_PATH) as f:
        for line in f:
            rows.append(json.loads(line))

    pair_keys, srcs, tgts, inputs = [], [], [], []
    for row in rows:
        src_id = row["source_node_id"]
        for cand in row["candidates"]:
            tgt_id = cand["target_node_id"]
            pair_keys.append(f"{src_id}__{tgt_id}")
            srcs.append(src_id); tgts.append(tgt_id)
            inputs.append([node_text[src_id], node_text[tgt_id]])

    scores = reranker.compute_score(inputs, batch_size=args.batch_size, normalize=True)
    scores_f32 = np.asarray(scores, dtype=np.float32)

    table = pa.table({"pair_key": pair_keys, "source_node_id": srcs,
                      "target_node_id": tgts, "score_f32": scores_f32})
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, OUT_PATH, compression="snappy", use_dictionary=False)

    meta = {"model": MODEL_NAME, "n_pairs": len(pair_keys),
            "timestamp": datetime.now(timezone.utc).isoformat()}
    OUT_PATH.with_suffix(".meta.json").write_text(json.dumps(meta, sort_keys=True, indent=2))
    print(f"wrote {OUT_PATH} ({len(pair_keys)} pairs)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Commit**

```bash
git add classifier/scripts/build_bge_reranker_scores_lambda.py
git commit -m "plan3: Lambda script to cache bge-reranker-v2-m3 zero-shot scores"
```

### Task E2: BGERerankerScorer + CLI — test first

**Files:**
- Create: `classifier/tests/test_bge_reranker.py`
- Create: `classifier/baselines/bge_reranker.py`
- Create: `classifier/scripts/run_bge_reranker_baseline.py`

- [ ] **Step 1: Write the failing test**

```python
# classifier/tests/test_bge_reranker.py
import pyarrow as pa, pyarrow.parquet as pq, pytest
from classifier.baselines.bge_reranker import BGERerankerScorer
from classifier.baselines.protocol import NodePair


def _make_cache(tmp_path):
    p = tmp_path / "scores.parquet"
    table = pa.table({
        "pair_key": ["aiuc-1:C-1.1__owasp-agentic:ASI-01"],
        "source_node_id": ["aiuc-1:C-1.1"],
        "target_node_id": ["owasp-agentic:ASI-01"],
        "score_f32": [0.91],
    })
    pq.write_table(table, p); return p


def test_reranker_cache_lookup(tmp_path):
    p = _make_cache(tmp_path)
    s = BGERerankerScorer(scores_path=p)
    assert s.name == "bge_reranker" and s.version == "1.0.0"
    pair = NodePair(pair_key="aiuc-1:C-1.1__owasp-agentic:ASI-01",
                    source_node_id="aiuc-1:C-1.1", source_framework="a", source_text="",
                    target_node_id="owasp-agentic:ASI-01", target_framework="b", target_text="")
    [rec] = s.score([pair])
    assert abs(rec.score - 0.91) < 1e-6


def test_reranker_missing_pair_raises(tmp_path):
    p = _make_cache(tmp_path)
    s = BGERerankerScorer(scores_path=p)
    bad = NodePair(pair_key="x__y", source_node_id="x", source_framework="a",
                   source_text="", target_node_id="y", target_framework="b", target_text="")
    with pytest.raises(KeyError, match="x__y"):
        s.score([bad])
```

- [ ] **Step 2: Run — expect failure**

Run: `pytest classifier/tests/test_bge_reranker.py -v`
Expected: ModuleNotFoundError.

- [ ] **Step 3: Implement `classifier/baselines/bge_reranker.py`**

```python
"""bge-reranker-v2-m3 zero-shot baseline. Row 4 of §1.3.

Reads the per-pair score parquet produced on Lambda by
`classifier/scripts/build_bge_reranker_scores_lambda.py`.
"""
from __future__ import annotations

from pathlib import Path
import pyarrow.parquet as pq

from classifier.baselines.protocol import NodePair, ScoreRecord
from classifier.config import DATA_DIR


DEFAULT_SCORES_PATH = DATA_DIR / "baselines" / "bge_reranker_scores.parquet"


class BGERerankerScorer:
    name = "bge_reranker"
    version = "1.0.0"

    def __init__(self, scores_path: Path = DEFAULT_SCORES_PATH):
        self.scores_path = Path(scores_path)
        table = pq.read_table(self.scores_path)
        keys = table.column("pair_key").to_pylist()
        scores = table.column("score_f32").to_pylist()
        self._index: dict[str, float] = dict(zip(keys, scores))

    def score(self, pairs: list[NodePair]) -> list[ScoreRecord]:
        out: list[ScoreRecord] = []
        for p in pairs:
            if p.pair_key not in self._index:
                raise KeyError(f"pair {p.pair_key!r} not in reranker cache {self.scores_path}")
            out.append(ScoreRecord(
                pair_key=p.pair_key, scorer_name=self.name, scorer_version=self.version,
                score=float(self._index[p.pair_key]),
                tier_pred=None, tier_probs=None, extras={},
            ))
        return out
```

- [ ] **Step 4: Write the CLI**

```python
# classifier/scripts/run_bge_reranker_baseline.py
"""CLI: run bge-reranker baseline on llm_val; writes results JSON."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
from pathlib import Path

from classifier.config import DATA_DIR
from classifier.data.splits import verify_hashes
from classifier.baselines.bge_reranker import BGERerankerScorer
from classifier.baselines.eval_harness import load_llm_val_pairs, evaluate_scorer, write_results


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-root", default=str(DATA_DIR / "baselines"))
    args = ap.parse_args()
    verify_hashes()
    scorer = BGERerankerScorer()
    pairs, gold = load_llm_val_pairs()
    result = evaluate_scorer(scorer, pairs, gold)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    run_dir = Path(args.out_root) / f"run_{ts}_bge_reranker"
    write_results(run_dir, {scorer.name: result})
    print(f"wrote {run_dir}/results_llm_val.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: Run — expect pass**

Run: `pytest classifier/tests/test_bge_reranker.py -v`
Expected: 2 passed.

- [ ] **Step 6: Commit**

```bash
git add classifier/baselines/bge_reranker.py classifier/tests/test_bge_reranker.py classifier/scripts/run_bge_reranker_baseline.py
git commit -m "plan3: bge-reranker-v2-m3 zero-shot scorer + CLI"
```

---

## Phase F — Opus 4.6 zero-shot ceiling

### Task F1: Unbiased-expert prompt template

**Files:**
- Create: `classifier/config/llm_sme_prompts/v1/unbiased_expert.j2`

- [ ] **Step 1: Write the template**

```jinja
You are an unbiased senior AI security expert. Given two controls from
different frameworks, classify their relationship with no persona bias.

Source framework: {{ source_framework }}
Source control: {{ source_text }}

Target framework: {{ target_framework }}
Target control: {{ target_text }}

Return strictly valid JSON with keys:
  "tier"            — one of "Direct", "Related", "None"
  "confidence"      — float in [0,1]
  "rationale_code"  — one of FUNCTIONAL_OVERLAP, SCOPE_DIFFERENCE, DOMAIN_SHIFT,
                      GENERALIZATION, SPECIALIZATION, COMPLEMENTARY,
                      UNRELATED, INSUFFICIENT_CONTEXT
  "rationale_text"  — <=400 chars
  "grounding_quotes" — list of short quoted spans

No prose outside the JSON object.
```

- [ ] **Step 2: Commit**

```bash
git add classifier/config/llm_sme_prompts/v1/unbiased_expert.j2
git commit -m "plan3: unbiased-expert prompt for Opus 4.6 ceiling"
```

### Task F2: OpusZeroShotScorer — test first

**Files:**
- Create: `classifier/tests/test_opus_zero_shot.py`
- Create: `classifier/baselines/opus_zero_shot.py`

- [ ] **Step 1: Write the failing test**

```python
# classifier/tests/test_opus_zero_shot.py
import json
from pathlib import Path
from unittest.mock import MagicMock
from classifier.baselines.opus_zero_shot import OpusZeroShotScorer
from classifier.baselines.protocol import NodePair


def _fake_labeler():
    lc = MagicMock()
    # two Direct, one Related → majority Direct
    responses = [
        MagicMock(tier=MagicMock(value="Direct"), confidence=0.9),
        MagicMock(tier=MagicMock(value="Direct"), confidence=0.8),
        MagicMock(tier=MagicMock(value="Related"), confidence=0.6),
    ]
    lc.label.side_effect = responses
    return lc


def test_opus_zero_shot_majority_vote():
    lc = _fake_labeler()
    s = OpusZeroShotScorer(labeler_client=lc, samples=3, model="claude-opus-4-6")
    assert s.name == "opus_zero_shot" and s.version == "1.0.0"
    p = NodePair(pair_key="a__b", source_node_id="a", source_framework="x",
                 source_text="S", target_node_id="b", target_framework="y", target_text="T")
    [rec] = s.score([p])
    assert rec.tier_pred == "Direct"
    assert rec.tier_probs == {"Direct": 2/3, "Related": 1/3, "None": 0.0}
    # score = confidence-weighted Direct prob
    assert 0 <= rec.score <= 1
    assert lc.label.call_count == 3


def test_budget_guard_raises(monkeypatch, tmp_path):
    ledger = tmp_path / "cost_ledger.jsonl"
    # pre-seed ledger with $119 of spend
    ledger.write_text(json.dumps({"cost_usd": 119.0}) + "\n")
    from classifier.baselines import opus_zero_shot as ozs
    monkeypatch.setattr(ozs, "COST_LEDGER_PATH", ledger)
    monkeypatch.setattr(ozs, "BUDGET_CAP_USD", 120.0)
    with __import__("pytest").raises(RuntimeError, match="budget"):
        ozs.assert_budget_ok(projected_cost=10.0)
```

- [ ] **Step 2: Run — expect failure**

Run: `pytest classifier/tests/test_opus_zero_shot.py -v`
Expected: ModuleNotFoundError.

- [ ] **Step 3: Implement `classifier/baselines/opus_zero_shot.py`**

```python
"""Opus 4.6 zero-shot ceiling baseline. Row 5 of §1.3.

Reuses Plan 2's LabelerClient with a single "unbiased expert" prompt. Each
pair is sampled 3 times; the tier with the majority vote is emitted; the
scalar `score` is the confidence-weighted probability of the Direct tier
(continuous, usable by the eval harness's R@K metric).

Budget guard: refuses to run if projected ledger total would exceed
BUDGET_CAP_USD (default $120, per plan guardrail).
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from classifier.baselines.protocol import NodePair, ScoreRecord
from classifier.config import DATA_DIR


COST_LEDGER_PATH = DATA_DIR / "cost_ledger.jsonl"
BUDGET_CAP_USD = 120.0


def _current_spend() -> float:
    if not COST_LEDGER_PATH.exists():
        return 0.0
    total = 0.0
    for line in COST_LEDGER_PATH.read_text().splitlines():
        try:
            total += float(json.loads(line).get("cost_usd", 0.0))
        except Exception:
            continue
    return total


def assert_budget_ok(projected_cost: float) -> None:
    spent = _current_spend()
    if spent + projected_cost > BUDGET_CAP_USD:
        raise RuntimeError(
            f"budget guardrail: spent ${spent:.2f} + projected ${projected_cost:.2f} "
            f"exceeds cap ${BUDGET_CAP_USD:.2f}"
        )


class OpusZeroShotScorer:
    name = "opus_zero_shot"
    version = "1.0.0"

    def __init__(self, labeler_client, samples: int = 3, model: str = "claude-opus-4-6"):
        self.lc = labeler_client
        self.samples = samples
        self.model = model

    def score(self, pairs: list[NodePair]) -> list[ScoreRecord]:
        # Local import keeps Plan 3 Scorer Protocol import-graph clean.
        from classifier.labeling.schemas import LabelRequest, Persona, Tier  # noqa: F401

        out: list[ScoreRecord] = []
        for p in pairs:
            tiers: list[str] = []
            confs: list[float] = []
            for _ in range(self.samples):
                req = LabelRequest(
                    pair_key=p.pair_key,
                    persona=Persona("unbiased_expert"),
                    source_node_id=p.source_node_id, source_text=p.source_text,
                    source_framework=p.source_framework,
                    target_node_id=p.target_node_id, target_text=p.target_text,
                    target_framework=p.target_framework,
                    model=self.model, temperature=0.3,
                )
                resp = self.lc.label(req)
                tiers.append(resp.tier.value)
                confs.append(float(resp.confidence))
            counts = Counter(tiers)
            majority = counts.most_common(1)[0][0]
            probs = {t: counts.get(t, 0) / self.samples for t in ("Direct", "Related", "None")}
            # continuous score: confidence-weighted P(Direct)
            direct_conf = sum(c for t, c in zip(tiers, confs) if t == "Direct")
            score_val = direct_conf / (self.samples or 1)
            out.append(ScoreRecord(
                pair_key=p.pair_key, scorer_name=self.name, scorer_version=self.version,
                score=float(score_val), tier_pred=majority, tier_probs=probs,
                extras={"samples": self.samples, "model": self.model},
            ))
        return out
```

- [ ] **Step 4: Add `unbiased_expert` to the Persona enum**

Plan 2's `classifier/labeling/schemas.py` declares a `Persona` enum with the three SME personas. Append one member without renaming anything:

Open `classifier/labeling/schemas.py`, find the `Persona` enum, and add:
```python
    UNBIASED_EXPERT = "unbiased_expert"
```

And register the template path in `classifier/labeling/prompts.py` where personas are mapped to `.j2` filenames — add:
```python
    Persona.UNBIASED_EXPERT: "unbiased_expert.j2",
```

- [ ] **Step 5: Run — expect pass**

Run: `pytest classifier/tests/test_opus_zero_shot.py classifier/tests/test_schemas.py classifier/tests/test_prompts.py -v`
Expected: all pass. If the Plan 2 persona test is strict about enum membership, update the fixture to match — do not remove Plan 2's personas.

- [ ] **Step 6: Commit**

```bash
git add classifier/baselines/opus_zero_shot.py classifier/tests/test_opus_zero_shot.py classifier/labeling/schemas.py classifier/labeling/prompts.py
git commit -m "plan3: Opus 4.6 zero-shot ceiling scorer + unbiased_expert persona"
```

### Task F3: Opus ceiling CLI with budget guard

**Files:**
- Create: `classifier/scripts/run_opus_ceiling_baseline.py`

- [ ] **Step 1: Write the CLI**

```python
"""CLI: run Opus 4.6 zero-shot ceiling on llm_val (400 pairs × 3 samples).

Budget guardrail: $100 projected + existing ledger must stay under $120.
Idempotent disk cache in Plan 2's LabelerClient means resume is free.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from anthropic import Anthropic

from classifier.config import DATA_DIR, require_secrets
from classifier.data.splits import verify_hashes
from classifier.baselines.opus_zero_shot import OpusZeroShotScorer, assert_budget_ok
from classifier.baselines.eval_harness import load_llm_val_pairs, evaluate_scorer, write_results
from classifier.labeling.client import LabelerClient


PROJECTED_COST_USD = 100.0  # 400 pairs × 3 samples × Opus 4.6 pricing estimate


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-root", default=str(DATA_DIR / "baselines"))
    ap.add_argument("--samples", type=int, default=3)
    ap.add_argument("--max-pairs", type=int, default=400)
    args = ap.parse_args()

    verify_hashes()
    assert_budget_ok(projected_cost=PROJECTED_COST_USD)

    secrets = require_secrets(["ANTHROPIC_API_KEY"])
    anth = Anthropic(api_key=secrets["ANTHROPIC_API_KEY"])
    lc = LabelerClient(
        anthropic_client=anth,
        cache_dir=DATA_DIR / "labels" / "_cache",
        ledger_path=DATA_DIR / "cost_ledger.jsonl",
        plan="plan3-opus-ceiling",
    )
    scorer = OpusZeroShotScorer(labeler_client=lc, samples=args.samples)

    pairs, gold = load_llm_val_pairs()
    pairs = pairs[: args.max_pairs]
    gold = {k: gold[k] for k in (p.pair_key for p in pairs) if k in gold}

    result = evaluate_scorer(scorer, pairs, gold)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    run_dir = Path(args.out_root) / f"run_{ts}_opus_ceiling"
    write_results(run_dir, {scorer.name: result})
    print(f"wrote {run_dir}/results_llm_val.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Commit**

```bash
git add classifier/scripts/run_opus_ceiling_baseline.py
git commit -m "plan3: Opus ceiling CLI with $120 budget guardrail"
```

---

## Phase G — Eval harness + metrics + results

### Task G1: Eval harness core — test first

**Files:**
- Create: `classifier/tests/test_eval_harness.py`
- Create: `classifier/baselines/eval_harness.py`

The harness loads `llm_val` from Plan 2's frozen output (`data/labels/llm_sme/v1_frozen/llm_val.jsonl`) and the candidate pool `data/candidates/pool_v2.jsonl`, constructs `NodePair`s for every (source_node, candidate_target), runs a scorer, and computes R@1 / R@3 / R@5 / R@10 / MRR / tier-acc grouped by source_node_id (gold target = the `pair_key` from llm_val's row).

- [ ] **Step 1: Write the failing test**

```python
# classifier/tests/test_eval_harness.py
import json
from classifier.baselines.protocol import NodePair, ScoreRecord
from classifier.baselines.eval_harness import compute_metrics, evaluate_scorer


class _StubScorer:
    name = "stub"
    version = "0.0.0"
    def __init__(self, scores): self._scores = scores
    def score(self, pairs):
        return [ScoreRecord(pair_key=p.pair_key, scorer_name=self.name,
                            scorer_version=self.version,
                            score=self._scores[p.pair_key],
                            tier_pred="Direct", tier_probs=None, extras={})
                for p in pairs]


def _make_pair(src, tgt):
    return NodePair(pair_key=f"{src}__{tgt}", source_node_id=src, source_framework="a",
                    source_text="", target_node_id=tgt, target_framework="b", target_text="")


def test_compute_metrics_perfect_ranking():
    # source s1 with 3 candidates; gold is t1; scorer gives t1 highest
    pairs = [_make_pair("s1", "t1"), _make_pair("s1", "t2"), _make_pair("s1", "t3")]
    scores = {"s1__t1": 0.9, "s1__t2": 0.5, "s1__t3": 0.1}
    gold = {"s1": {"target_node_id": "t1", "tier": "Direct"}}
    records = _StubScorer(scores).score(pairs)
    m = compute_metrics(records, pairs, gold)
    assert m["recall_at_1"] == 1.0
    assert m["recall_at_3"] == 1.0
    assert m["mrr"] == 1.0
    assert m["tier_acc"] == 1.0


def test_compute_metrics_rank_2():
    pairs = [_make_pair("s1", "t1"), _make_pair("s1", "t2"), _make_pair("s1", "t3")]
    scores = {"s1__t1": 0.3, "s1__t2": 0.9, "s1__t3": 0.1}
    gold = {"s1": {"target_node_id": "t1", "tier": "Direct"}}
    records = _StubScorer(scores).score(pairs)
    m = compute_metrics(records, pairs, gold)
    assert m["recall_at_1"] == 0.0
    assert m["recall_at_3"] == 1.0
    assert m["mrr"] == 0.5  # 1/2
```

- [ ] **Step 2: Run — expect failure**

Run: `pytest classifier/tests/test_eval_harness.py -v`
Expected: ModuleNotFoundError.

- [ ] **Step 3: Implement `classifier/baselines/eval_harness.py`**

```python
"""Eval harness: llm_val loader + metrics + results JSON writer."""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from datetime import datetime, timezone

from classifier.baselines.protocol import NodePair, ScoreRecord, Scorer
from classifier.config import DATA_DIR, REPO_ROOT


LLM_VAL_PATH = DATA_DIR / "labels" / "llm_sme" / "v1_frozen" / "llm_val.jsonl"
POOL_V2_PATH = DATA_DIR / "candidates" / "pool_v2.jsonl"


def load_llm_val_pairs() -> tuple[list[NodePair], dict[str, dict]]:
    """Return (candidate_pairs, gold) where gold[source_node_id] = {target_node_id, tier}."""
    nodes = json.loads((REPO_ROOT / "data" / "processed" / "nodes.json").read_text())
    node_idx = {n["id"]: n for n in nodes}

    gold: dict[str, dict] = {}
    for line in LLM_VAL_PATH.read_text().splitlines():
        row = json.loads(line)
        src_id = row["source_node_id"]
        gold[src_id] = {"target_node_id": row["target_node_id"], "tier": row["tier"]}

    pairs: list[NodePair] = []
    with open(POOL_V2_PATH) as f:
        for line in f:
            row = json.loads(line)
            src_id = row["source_node_id"]
            if src_id not in gold:
                continue
            src = node_idx[src_id]
            for cand in row["candidates"]:
                tgt_id = cand["target_node_id"]
                tgt = node_idx[tgt_id]
                pairs.append(NodePair(
                    pair_key=f"{src_id}__{tgt_id}",
                    source_node_id=src_id, source_framework=src["framework"],
                    source_text=src["text"],
                    target_node_id=tgt_id, target_framework=tgt["framework"],
                    target_text=tgt["text"],
                ))
    return pairs, gold


def compute_metrics(records: list[ScoreRecord], pairs: list[NodePair],
                    gold: dict[str, dict]) -> dict:
    pair_by_key = {p.pair_key: p for p in pairs}
    by_source: dict[str, list[tuple[float, str, str]]] = defaultdict(list)
    tier_by_key: dict[str, str | None] = {}
    for r in records:
        p = pair_by_key[r.pair_key]
        by_source[p.source_node_id].append((r.score, p.target_node_id, r.pair_key))
        tier_by_key[r.pair_key] = r.tier_pred

    ks = (1, 3, 5, 10)
    hits = {k: 0 for k in ks}
    recip_ranks: list[float] = []
    tier_correct = 0
    tier_total = 0
    n = 0
    for src, scored in by_source.items():
        if src not in gold:
            continue
        scored.sort(key=lambda t: (-t[0], t[1]))  # stable tiebreak by target_id
        gold_tgt = gold[src]["target_node_id"]
        ranks = [i for i, (_, tgt, _) in enumerate(scored, start=1) if tgt == gold_tgt]
        if not ranks:
            rr = 0.0
            for k in ks:
                pass
        else:
            r = ranks[0]
            rr = 1.0 / r
            for k in ks:
                if r <= k:
                    hits[k] += 1
            # tier accuracy only evaluated when gold target is ranked
            gold_pair_key = f"{src}__{gold_tgt}"
            pred_tier = tier_by_key.get(gold_pair_key)
            if pred_tier is not None:
                tier_total += 1
                if pred_tier == gold[src]["tier"]:
                    tier_correct += 1
        recip_ranks.append(rr)
        n += 1

    return {
        "n_sources": n,
        "recall_at_1": hits[1] / n if n else 0.0,
        "recall_at_3": hits[3] / n if n else 0.0,
        "recall_at_5": hits[5] / n if n else 0.0,
        "recall_at_10": hits[10] / n if n else 0.0,
        "mrr": sum(recip_ranks) / n if n else 0.0,
        "tier_acc": tier_correct / tier_total if tier_total else 0.0,
        "tier_n": tier_total,
    }


def evaluate_scorer(scorer: Scorer, pairs: list[NodePair], gold: dict) -> dict:
    records = scorer.score(pairs)
    metrics = compute_metrics(records, pairs, gold)
    return {
        "scorer_name": scorer.name,
        "scorer_version": scorer.version,
        "metrics": metrics,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def write_results(run_dir: Path, results_by_scorer: dict[str, dict]) -> Path:
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    out_path = run_dir / "results_llm_val.json"
    # Contract 3: refuse to overwrite existing results
    if out_path.exists():
        raise FileExistsError(f"refuse to overwrite {out_path}")
    out_path.write_text(json.dumps(results_by_scorer, sort_keys=True, indent=2, ensure_ascii=False))
    # update `latest` symlink
    latest = run_dir.parent / "latest"
    if latest.is_symlink() or latest.exists():
        latest.unlink()
    latest.symlink_to(run_dir.name)
    return out_path
```

- [ ] **Step 4: Run — expect pass**

Run: `pytest classifier/tests/test_eval_harness.py -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add classifier/baselines/eval_harness.py classifier/tests/test_eval_harness.py
git commit -m "plan3: eval harness — load llm_val, compute R@K/MRR/tier-acc"
```

### Task G2: All-baselines orchestrator CLI

**Files:**
- Create: `classifier/scripts/run_all_baselines_eval.py`

- [ ] **Step 1: Write the CLI**

```python
"""CLI: register every Plan 3 scorer and run the eval harness.

Writes a single `results_llm_val.json` keyed by scorer name. Refuses to
overwrite — re-runs land under a fresh `run_<ts>/` dir.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from classifier.config import DATA_DIR
from classifier.data.splits import verify_hashes
from classifier.baselines import registry
from classifier.baselines.bm25 import BM25Scorer
from classifier.baselines.bge_cosine import BGECosineScorer
from classifier.baselines.v2_composite import V2CompositeScorer
from classifier.baselines.bge_reranker import BGERerankerScorer
from classifier.baselines.eval_harness import load_llm_val_pairs, evaluate_scorer, write_results


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-root", default=str(DATA_DIR / "baselines"))
    ap.add_argument("--skip", nargs="*", default=[], help="scorer names to skip")
    args = ap.parse_args()

    verify_hashes()

    for S in (BM25Scorer, BGECosineScorer, V2CompositeScorer, BGERerankerScorer):
        try:
            registry.register(S())
        except ValueError:
            pass

    pairs, gold = load_llm_val_pairs()
    results: dict[str, dict] = {}
    for scorer in registry.all_scorers():
        if scorer.name in args.skip:
            continue
        print(f"running scorer={scorer.name} v={scorer.version}")
        results[scorer.name] = evaluate_scorer(scorer, pairs, gold)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    run_dir = Path(args.out_root) / f"run_{ts}_all"
    out = write_results(run_dir, results)
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Commit**

```bash
git add classifier/scripts/run_all_baselines_eval.py
git commit -m "plan3: run_all_baselines_eval orchestrator"
```

### Task G3: End-to-end dry-run on Jetson (BM25 + v2 composite only)

- [ ] **Step 1: Run the two non-GPU baselines**

Run: `python -m classifier.scripts.run_all_baselines_eval --skip bge_cosine bge_reranker opus_zero_shot`
Expected: creates `data/baselines/run_<ts>_all/results_llm_val.json` with two keys (`bm25`, `v2_composite`). Each contains `metrics.recall_at_3`, `metrics.mrr`, `metrics.tier_acc` as floats.

- [ ] **Step 2: Verify the JSON with a one-liner**

Run: `python -c "import json; d=json.load(open('data/baselines/latest/results_llm_val.json')); print(list(d)); print({k: d[k]['metrics']['recall_at_3'] for k in d})"`
Expected: `['bm25', 'v2_composite']` then a dict of R@3 floats.

- [ ] **Step 3: Commit the dry-run artifact**

```bash
git add data/baselines/run_*_all/results_llm_val.json data/baselines/latest
git commit -m "plan3: Jetson dry-run results (bm25 + v2_composite on llm_val)"
```

---

## Phase H — Feature cache for Plan 5 stacker

### Task H1: Wide feature parquet — test first

**Files:**
- Create: `classifier/tests/test_feature_cache.py`
- Create: `classifier/baselines/feature_cache.py`
- Create: `classifier/scripts/build_baseline_feature_cache.py`

- [ ] **Step 1: Write the failing test**

```python
# classifier/tests/test_feature_cache.py
import pyarrow.parquet as pq
from classifier.baselines.protocol import ScoreRecord, NodePair
from classifier.baselines.feature_cache import build_feature_table


def _pair(k): return NodePair(pair_key=k, source_node_id="s", source_framework="a",
                               source_text="", target_node_id="t", target_framework="b",
                               target_text="")


def test_build_feature_table_wide(tmp_path):
    pairs = [_pair("p1"), _pair("p2")]
    records_by_scorer = {
        "bm25": [
            ScoreRecord(pair_key="p1", scorer_name="bm25", scorer_version="1.0.0",
                        score=0.2, tier_pred=None, tier_probs=None, extras={}),
            ScoreRecord(pair_key="p2", scorer_name="bm25", scorer_version="1.0.0",
                        score=0.5, tier_pred=None, tier_probs=None, extras={}),
        ],
        "bge_cosine": [
            ScoreRecord(pair_key="p1", scorer_name="bge_cosine", scorer_version="1.0.0",
                        score=0.9, tier_pred=None, tier_probs=None, extras={}),
            # p2 intentionally missing → NaN column value
        ],
    }
    out = tmp_path / "feat.parquet"
    build_feature_table(pairs, records_by_scorer, out_path=out)
    t = pq.read_table(out)
    cols = t.column_names
    assert "pair_key" in cols and "bm25" in cols and "bge_cosine" in cols
    d = t.to_pydict()
    assert d["pair_key"] == ["p1", "p2"]
    assert d["bm25"] == [0.2, 0.5]
    assert d["bge_cosine"][0] == 0.9
    assert d["bge_cosine"][1] is None
```

- [ ] **Step 2: Run — expect failure**

Run: `pytest classifier/tests/test_feature_cache.py -v`
Expected: ModuleNotFoundError.

- [ ] **Step 3: Implement `classifier/baselines/feature_cache.py`**

```python
"""Wide feature parquet: rows = pairs, columns = scorer names.

Consumed by Plan 5's stacker. Null entries are allowed when a scorer did not
produce a score for a pair (e.g. bge_reranker cache miss). Plan 5 imputes.
"""
from __future__ import annotations

from pathlib import Path
import pyarrow as pa
import pyarrow.parquet as pq

from classifier.baselines.protocol import NodePair, ScoreRecord


def build_feature_table(pairs: list[NodePair],
                        records_by_scorer: dict[str, list[ScoreRecord]],
                        out_path: Path) -> Path:
    pair_keys = [p.pair_key for p in pairs]
    table_cols: dict[str, list] = {"pair_key": pair_keys}
    for scorer_name, records in records_by_scorer.items():
        by_key = {r.pair_key: r.score for r in records}
        table_cols[scorer_name] = [by_key.get(k) for k in pair_keys]
    table = pa.table(table_cols)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, out_path, compression="snappy", use_dictionary=False)
    return out_path
```

- [ ] **Step 4: Write the CLI**

```python
# classifier/scripts/build_baseline_feature_cache.py
"""CLI: compute every registered scorer on llm_val and emit wide parquet."""
from __future__ import annotations

import argparse
from pathlib import Path

from classifier.config import DATA_DIR
from classifier.data.splits import verify_hashes
from classifier.baselines import registry
from classifier.baselines.bm25 import BM25Scorer
from classifier.baselines.bge_cosine import BGECosineScorer
from classifier.baselines.v2_composite import V2CompositeScorer
from classifier.baselines.bge_reranker import BGERerankerScorer
from classifier.baselines.eval_harness import load_llm_val_pairs
from classifier.baselines.feature_cache import build_feature_table


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(DATA_DIR / "features" / "baseline_features.parquet"))
    ap.add_argument("--skip", nargs="*", default=[])
    args = ap.parse_args()

    verify_hashes()

    for S in (BM25Scorer, BGECosineScorer, V2CompositeScorer, BGERerankerScorer):
        try:
            registry.register(S())
        except ValueError:
            pass

    pairs, _gold = load_llm_val_pairs()
    records_by_scorer: dict[str, list] = {}
    for scorer in registry.all_scorers():
        if scorer.name in args.skip:
            continue
        print(f"scoring {scorer.name} v{scorer.version}")
        records_by_scorer[scorer.name] = scorer.score(pairs)

    out = Path(args.out)
    if out.exists():
        raise FileExistsError(f"refuse to overwrite {out} — bump filename")
    build_feature_table(pairs, records_by_scorer, out_path=out)
    print(f"wrote {out} ({len(pairs)} pairs, {len(records_by_scorer)} scorers)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: Run — expect pass**

Run: `pytest classifier/tests/test_feature_cache.py -v`
Expected: 1 passed.

- [ ] **Step 6: Commit**

```bash
git add classifier/baselines/feature_cache.py classifier/tests/test_feature_cache.py classifier/scripts/build_baseline_feature_cache.py
git commit -m "plan3: baseline feature cache (wide pair×scorer parquet) for Plan 5"
```

---

## Phase I — Handoff

### Task I1: Plan 3 handoff summary

**Files:**
- Create: `classifier/BASELINES_COMPLETE.md`

- [ ] **Step 1: Run the full Plan 3 test suite**

Run: `pytest classifier/tests/test_scorer_protocol.py classifier/tests/test_registry.py classifier/tests/test_bm25.py classifier/tests/test_bge_cosine.py classifier/tests/test_v2_composite.py classifier/tests/test_bge_reranker.py classifier/tests/test_opus_zero_shot.py classifier/tests/test_eval_harness.py classifier/tests/test_feature_cache.py -v`
Expected: all pass. If any fail, fix before writing the handoff doc.

- [ ] **Step 2: Write `classifier/BASELINES_COMPLETE.md`**

```markdown
# Plan 3 Handoff — Baselines & Feature Cache

**Completed:** <date>
**Branch / commits:** <paste `git log --oneline main..HEAD | head -40`>

## Scorers registered (spec §1.3 rows 1–5)

| Name | Version | Source | Runs on |
|---|---|---|---|
| bm25 | 1.0.0 | classifier/baselines/bm25.py | Jetson |
| bge_cosine | 1.0.0 | classifier/baselines/bge_cosine.py (cache built on Lambda) | Jetson (uses cached parquet) |
| v2_composite | 2.<mapping_engine version> | classifier/baselines/v2_composite.py | Jetson |
| bge_reranker | 1.0.0 | classifier/baselines/bge_reranker.py (scores built on Lambda) | Jetson (uses cached parquet) |
| opus_zero_shot | 1.0.0 | classifier/baselines/opus_zero_shot.py | Jetson, API calls to Opus 4.6 |

## Artifacts produced

- `data/baselines/bge_cosine_embeddings.parquet` — 983 × 1024 float32
- `data/baselines/bge_reranker_scores.parquet` — ~50k per-pair scores
- `data/baselines/run_<ts>_all/results_llm_val.json` — headline table
- `data/baselines/latest` → symlink to most recent run
- `data/features/baseline_features.parquet` — wide pair×scorer for Plan 5
- `data/cost_ledger.jsonl` — Opus ceiling spend appended

## Tests passing

- `test_scorer_protocol.py`
- `test_registry.py`
- `test_bm25.py`
- `test_bge_cosine.py`
- `test_v2_composite.py`
- `test_bge_reranker.py`
- `test_opus_zero_shot.py`
- `test_eval_harness.py`
- `test_feature_cache.py`

## Ready for Plans 4 & 5

Plan 4 (learned cross-encoder) can register its fine-tuned scorer against
`classifier.baselines.registry` with `name="ours_rung_l"` etc., and the eval
harness will pick it up with zero changes.

Plan 5 (stacker + conformal) reads `data/features/baseline_features.parquet`
directly. Column order is alphabetical by scorer name; null entries allowed.

## Honesty log

- `human_test_frozen` was NOT touched. All Plan 3 numbers are on `llm_val`.
- Opus ceiling budget guardrail: spent $<value>, cap $120.
```

- [ ] **Step 3: Commit**

```bash
git add classifier/BASELINES_COMPLETE.md
git commit -m "plan3: handoff summary"
```

- [ ] **Step 4: Report completion**

Announce: "Plan 3 complete. 5 baselines registered against Scorer protocol, eval harness + feature cache green, cost ledger under $120. Ready to invoke Plan 4 (learned cross-encoder rungs)."

---

## Self-Review

**Spec coverage (§ numbers from the design spec):**
- §1.3 row 1 BM25 → Tasks B1, B2 ✓
- §1.3 row 2 bge-large cosine → Tasks C1, C2, C3 ✓
- §1.3 row 3 v2 composite → Tasks D1, D2 ✓
- §1.3 row 4 bge-reranker-v2-m3 → Tasks E1, E2 ✓
- §1.3 row 5 Opus zero-shot → Tasks F1, F2, F3 ✓
- §3.5 compute budget "zero-shot baselines ~$15" → Tasks C1 + E1 (Lambda cache scripts) ✓
- §3.5 "~$100 Opus ceiling" + $120 guardrail → Task F2 `assert_budget_ok` + F3 CLI ✓
- §4.1 metrics R@1/3/5/10 + MRR + tier_acc → Task G1 `compute_metrics` ✓
- §6 honesty commitment #1 (frozen-400 untouched) → Plan 3 evaluates on `llm_val` only; verified by handoff doc ✓
- §6 honesty commitment #6 (failed baselines reported) → registry + eval harness emit ALL scorers, no filtering ✓

**Cross-plan contract coverage:**
- Contract 1 verify_hashes → every CLI in `classifier/scripts/run_*.py` and `build_*.py` calls it ✓
- Contract 2 pool_v2 → `load_llm_val_pairs` reads `data/candidates/pool_v2.jsonl` and nothing else ✓
- Contract 3 no overwrite → `write_results` raises on existing file; feature cache CLI raises on existing file ✓
- Contract 4 Scorer Protocol → defined in Task A1, registered in Tasks B2/C3/D2/E2/F3 ✓
- Contract 7 cost ledger → Opus ceiling reuses Plan 2 `LabelerClient` (ledger write is automatic) ✓

**Placeholder scan:** no TBDs, no "implement later", every code block is complete, every shell command has expected output.

**Type consistency:** `NodePair` → `Scorer.score` → `list[ScoreRecord]` pipeline is uniform; `load_llm_val_pairs` returns `(list[NodePair], dict[str, dict])` consumed identically in every `run_*_baseline.py`; `compute_metrics` signature `(records, pairs, gold) -> dict` is consumed by both `evaluate_scorer` and the feature-cache tests.

**Known caveats for the executing agent:**
1. Phase C and E require Lambda — the CLIs in Tasks C3/E2 Step 4 assume the `.parquet` caches already exist. On the Jetson dry-run (Task G3), skip `bge_cosine` and `bge_reranker` via `--skip`. After Lambda produces the caches, re-run without `--skip` and regenerate the feature cache.
2. Task F2 Step 4 appends a member to Plan 2's `Persona` enum and its prompt-map dict. Read Plan 2's `classifier/labeling/schemas.py` first and only append — do not rename or remove existing members. If Plan 2's tests pin the Persona set exactly, add `UNBIASED_EXPERT` to their expected set as a one-line fix.
3. Task G1's `tier_acc` is only computed when the gold target is in the ranked candidates. Sources whose gold is missing from the candidate pool are counted in denominator `n` (for recall) but excluded from tier_acc denominator. The handoff doc reports both `tier_acc` and `tier_n` so the reader sees the effective coverage.
4. Task F3's `PROJECTED_COST_USD = 100.0` is an estimate. If the first 20 pairs of a run cost materially more than $5, STOP and surface to user — do not burn through the guardrail by raw call count.
5. The `latest` symlink in `data/baselines/` is a convenience; CI should not depend on it. Tests read the parquet via explicit paths.
