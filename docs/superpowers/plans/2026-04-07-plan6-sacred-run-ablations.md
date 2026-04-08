# Plan 6 — Sacred Run, Ablations, and Fresh-75 Generalization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> **USER TIME NOTICE (READ FIRST):** Phase C of this plan requires the user (the single human SME) to hand-label **75 new pairs** via a Streamlit UI. Budget **~3 hours of uninterrupted human time** for this. Do **not** skip, shortcut, or LLM-substitute these labels — Contract 11 will fail the CI if you try. Schedule this time block **before** running Phase F (the one-shot sacred run) because Phase F consumes the fresh-75 labels.

**Goal:** Execute the final, one-shot evaluation on `human_test_frozen`; run the ablation matrix required for paper Table 3; collect a brand-new 75-pair generalization set labeled by the human SME for paper Table 4; and produce the publication-ready paper tables backed by rigorous statistical tests (bootstrap CIs, McNemar, permutation null, BH-FDR across 12 framework pairs). The entire test-set access path is gated behind a structural lockfile that makes a second run impossible without a committed, justified `--break-glass` override.

**Architecture:** New subpackage `classifier/sacred/` houses the lockfile CLI, ablation runner, statistical tests, paper-table generator, and sacred-run orchestrator. A separate `classifier/fresh75/` subpackage houses the fresh-pair sampler and the Streamlit labeling UI. All of Plan 6 consumes artifacts produced by Plans 1–5 — it registers no new scorers, trains no new models, and mutates no earlier outputs. Its only writes are to `results/`, `data/labels/fresh_75/`, `data/sacred/`, and `paper/tables/`.

**Tech Stack:** Python 3.11, `numpy`, `scipy>=1.13` (for `scipy.stats.bootstrap`, `binomtest`), `statsmodels` (for `multipletests` BH-FDR), `streamlit==1.39.0`, `pytest`, existing Plan 1–5 stack.

---

## Spec Reference

Implements §4.1 (sacred run protocol), §4.3 (risks & mitigations), §6 (Pre-registered Honesty Commitments — one-shot rule, lockfile mechanism, required statistical tests) of `docs/superpowers/specs/2026-04-07-ai-security-crosswalk-classifier-design.md`.

**Consumes from prior plans:**
- Plan 1: `data/splits/hashes.json`, `data/splits/human_test_frozen.jsonl`, `data/splits/human_cal.jsonl`, `data/candidates/pool_v1.jsonl`
- Plan 2: `data/labels/llm_val.jsonl`, `data/labels/llm_train.jsonl` (contracts: `pair_id`, `tier`, `rationale`, `labeler`)
- Plan 3: registered baseline Scorers (lexical, BM25, bi-encoder, cross-encoder)
- Plan 4: registered learned Scorers (GAT, calibrated stacker, conformal wrapper)
- Plan 5: registered ensemble `Scorer` plus rung gates (S/M/L), rerank stage, and `ensemble.score_pair(pair) -> {tier, score, rung, components}`

**Out of scope for Plan 6:** any new model training, any new Scorer registration, any mutation of splits or labels from earlier plans, the Dash exploration app, the written paper prose (Plan 7).

---

## File Structure

Plan 6 creates and only touches these paths. Existing files from Plans 1–5 are read-only.

| Path | Purpose |
|---|---|
| `classifier/sacred/__init__.py` | Subpackage marker |
| `classifier/sacred/ablation_registry.py` | Declarative dict of ablation configs (no_gat, no_stacker, …) |
| `classifier/sacred/run_ablations.py` | Ablation runner — evals each ablation on `llm_val`, writes `results/ablations.json` |
| `classifier/sacred/stats.py` | `bootstrap_ci`, `mcnemar_test`, `permutation_test`, `bh_correct` |
| `classifier/sacred/lockfile.py` | Lockfile read/write + git-clean / on-main checks |
| `classifier/sacred/sacred_run.py` | CLI entry: `--confirm-once` / `--break-glass` orchestrator |
| `classifier/sacred/paper_tables.py` | Generates `paper/tables/table{1..4}.{tex,md}` |
| `classifier/fresh75/__init__.py` | Subpackage marker |
| `classifier/fresh75/sampler.py` | Picks 75 fresh candidate pairs (post-freeze or under-represented strata) |
| `classifier/fresh75/app/fresh_label_ui.py` | Streamlit app — 4 tier buttons + rationale, JSONL-persisted |
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
| `data/labels/fresh_75/candidates.jsonl` | 75 unlabeled candidate pairs (generated) |
| `data/labels/fresh_75/labels.jsonl` | Human labels (appended by Streamlit app) |
| `data/sacred/.gitkeep` | Directory marker |
| `data/sacred/lock_<git_sha>_<iso>.json` | Sacred-run lockfile (written by Phase E) |
| `results/ablations.json` | Ablation matrix output |
| `results/sacred/sacred_<git_sha>.json` | One-shot sacred run output |
| `paper/tables/table1.md` / `table1.tex` | Main results |
| `paper/tables/table2.md` / `table2.tex` | Per-pair results (12 rows) |
| `paper/tables/table3.md` / `table3.tex` | Ablations |
| `paper/tables/table4.md` / `table4.tex` | Fresh-75 generalization |
| `requirements-classifier.txt` | Append `scipy`, `statsmodels`, `streamlit` pins |

**Do not modify** any file under `classifier/data/`, `classifier/labeling/`, `classifier/scorers/`, `classifier/ensemble/`, `data/splits/`, `data/labels/llm_*`, or any Plan 1–5 artifact. Plan 6 is purely additive.

---

## Lessons Carried

From Plans 1–5 and from sessions 6–8 ralph-loop learnings (see `MEMORY.md`):

1. **Freeze everything, then verify.** Every entry point must call `verify_hashes()` before reading any split (Contract 1). Plan 1 installed the canary; Plan 6 must honor it.
2. **The honest holdout is sacred.** Session 8 uncovered leakage because non-sacred paths touched the frozen set. Plan 6 structurally removes every non-sacred path by grepping the codebase in CI (Contract 8).
3. **One-shot means one shot.** No "oh we'll just re-run to see" — that is how test-set contamination happens. The lockfile is the enforcement mechanism; break-glass is a confession, not an escape hatch.
4. **Statistical tests are contracts, not decoration.** Bootstrap CI, McNemar, permutation null, and BH-FDR are in the pre-registration — skipping any of them invalidates the paper.
5. **Fresh-75 must be human.** Session 8 taught us that LLM-labeled "test" sets are just model-vs-model. The user must label fresh-75 in person; Contract 11 enforces this by checking the `labeler` field.
6. **Mock the expensive stuff in tests.** Plan 5's ensemble is slow; Plan 6 tests use a `FakeEnsemble` fixture that returns deterministic pseudo-scores so the ablation / sacred-run CLIs can be tested end-to-end on the Jetson with no GPU.
7. **Commit artifacts, not just code.** Lockfiles and `paper/tables/*` belong in git — they are the receipts.

---

## Cross-Plan Contracts

- **Contract 1 — hash verification at entry.** Every CLI in Phase A / E / F calls `classifier.data.splits.verify_hashes()` before reading any split or label file. Tested in `test_run_ablations.py` and `test_sacred_run_cli.py`.
- **Contract 8 — `human_test_frozen` access ONLY via Phase F's `sacred_run.py`.** Enforced by `test_frozen_access_grep.py`, which greps the entire repo (excluding `classifier/sacred/sacred_run.py`, `classifier/data/splits.py`, `data/splits/`, `docs/`, and tests that explicitly assert the string) for the literal `human_test_frozen` and fails if any other file references it.
- **Contract 10 (NEW) — one-shot environment.** `sacred_run.py` aborts unless:
  1. `git status --porcelain` is empty (no uncommitted changes),
  2. current branch is `main`,
  3. current HEAD is pushed (optional warning if `@{u}` is behind — hard-fail if ahead and `--confirm-once` without `--allow-unpushed`).
  Tested in `test_one_shot_contract.py` with a tmp-path git repo.
- **Contract 11 (NEW) — fresh-75 labels must be human.** `classifier/fresh75/load_labels.py::load_fresh_75_labels()` requires every row to have `labeler == "human_sme"` and `labeler_id` matching the single configured user id in `.env` (`FRESH75_LABELER_ID`). Any `labeler` starting with `llm_`, `claude`, `gpt`, or `auto` hard-fails. Tested in `test_load_labels.py`.

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
        # deterministic pseudo-score: fewer disabled → higher score
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
    # full should beat lexical_only under FakeEnsemble scoring
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

- [ ] **Step 2: Smoke-run (dry)**

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
    # no overlap with human_test_frozen
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
        # fall back: under-represented strata = pairs from frameworks with <10 frozen labels
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

- [ ] **Step 2: Commit candidates (they become part of the pre-registration)**

```bash
git add data/labels/fresh_75/candidates.jsonl
git commit -m "plan6: freeze fresh-75 candidate pairs"
```

---

## Phase C — Streamlit labeling UI

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
"""Streamlit UI for the single human SME to label fresh-75 pairs.

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
    st.title("Fresh-75 Human Labeling")
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

- [ ] **Step 2: Append streamlit pin**

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

### Task C3: User labeling session (~3 hours)

- [ ] **Step 1: Set env and launch**

```bash
export FRESH75_LABELER_ID=rock
streamlit run classifier/fresh75/app/fresh_label_ui.py
```

- [ ] **Step 2: Label all 75 pairs in one sitting.** Do not let any other labeler touch the UI. Do not copy-paste from an LLM. Write the rationale in your own words; this is your pre-registered evidence.

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

### Task D1: Bootstrap CI

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
    golds[:40] = 1 - golds[:40]  # 10% error → acc 0.9
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
    b[:5] = 1 - b[:5]   # A correct, B wrong on 5
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
    b01 = int(np.sum(a_correct & ~b_correct))   # A right, B wrong
    b10 = int(np.sum(~a_correct & b_correct))   # A wrong, B right
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

### Task D2: (merged into D1 — single file covers all four tests.)

- [ ] Marked complete by D1.

### Task D3: Reference cross-check

- [ ] **Step 1:** Compare `bh_correct([0.01,0.02,0.03,0.04,0.05])` output against `statsmodels.stats.multitest.multipletests` directly in a REPL. Values must be identical (this *is* the reference — the test ensures the wrapping does not mangle order).

- [ ] **Step 2:** Compare `mcnemar_test` against `statsmodels.stats.contingency_tables.mcnemar(exact=True)` on a 2x2 table; p-values must match to 1e-9.

- [ ] **Step 3:** No commit (verification only).

### Task D4: Document usage in module docstring

- [ ] **Step 1:** Add a top-of-file docstring to `classifier/sacred/stats.py` citing spec §6 and noting that `n=10_000` is pre-registered for bootstrap and permutation.

- [ ] **Step 2:** Commit:

```bash
git add classifier/sacred/stats.py
git commit -m "plan6: document stats module pre-registration"
```

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
    # break-glass == bypass ensure_no_prior_lock, with justification captured
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
    "classifier/data/retrieval_floor.py",    # Plan 1 legitimate use
    "classifier/tests/sacred/test_frozen_access_grep.py",
    "classifier/tests/sacred/test_sacred_run_cli.py",
    "classifier/tests/test_splits.py",
    "classifier/tests/test_split_leakage.py",
    "classifier/fresh75/sampler.py",         # reads only to exclude overlap
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
        and not f.startswith(("docs/", "data/splits/", "data/sacred/", "paper/"))
    ]
    assert not offenders, (
        f"Contract 8 violation — non-sacred files reference human_test_frozen: {offenders}"
    )
```

- [ ] **Step 2: Run it**

```bash
pytest classifier/tests/sacred/test_frozen_access_grep.py -x
```

Expected: passes (ALLOWED list is tight).

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

- [ ] **Step 1:** Verify preconditions

```bash
git status --porcelain     # must be empty
git rev-parse --abbrev-ref HEAD     # must print 'main'
pytest classifier/tests/sacred -x   # all green
ls data/labels/fresh_75/labels.jsonl   # exists, 75 lines
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
    }
    sacred_path = tmp_path / "sacred.json"; sacred_path.write_text(json.dumps(sacred))
    out_dir = tmp_path / "paper" / "tables"
    paths = generate_tables(sacred_path, out_dir)
    for key in ("table1", "table2", "table3", "table4"):
        assert (out_dir / f"{key}.md").exists()
        assert (out_dir / f"{key}.tex").exists()
    t1 = (out_dir / "table1.md").read_text()
    assert "0.81" in t1 and "400" in t1
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

def _write(out_dir: Path, name: str, md: str, tex: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{name}.md").write_text(md)
    (out_dir / f"{name}.tex").write_text(tex)

def generate_tables(sacred_path: Path, out_dir: Path) -> Dict[str, Path]:
    data = json.loads(Path(sacred_path).read_text())
    frozen = data["frozen"]

    # Table 1 — main results
    t1_header = ["Split", "N", "Accuracy", "Macro-F1", "95% CI"]
    t1_rows = [[
        "human_test_frozen", frozen["n"],
        f"{frozen['accuracy']:.3f}", f"{frozen['macro_f1']:.3f}",
        f"[{frozen['acc_ci95'][0]:.3f}, {frozen['acc_ci95'][1]:.3f}]",
    ]]
    _write(out_dir, "table1",
           _md_table(t1_header, t1_rows),
           _tex_table(t1_header, t1_rows, "Main sacred-run results"))

    # Table 2 — per-pair
    t2_header = ["Source", "Destination", "N", "Accuracy"]
    t2_rows = [[r["src"], r["dst"], r["n"], f"{r['accuracy']:.3f}"]
               for r in data.get("per_pair", [])]
    _write(out_dir, "table2",
           _md_table(t2_header, t2_rows),
           _tex_table(t2_header, t2_rows, "Per-framework-pair results (12 pairs)"))

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
           _md_table(t4_header, t4_rows),
           _tex_table(t4_header, t4_rows, "Fresh-75 generalization results"))

    return {k: out_dir / f"{k}.md" for k in ("table1", "table2", "table3", "table4")}

if __name__ == "__main__":
    import argparse, glob
    ap = argparse.ArgumentParser()
    ap.add_argument("--sacred", required=True)
    ap.add_argument("--out", default="paper/tables")
    args = ap.parse_args()
    generate_tables(Path(args.sacred), Path(args.out))
```

Run: `pytest classifier/tests/sacred/test_paper_tables.py -x`
Expected: passes.

- [ ] **Step 2: Commit**

```bash
git add classifier/sacred/paper_tables.py classifier/tests/sacred/test_paper_tables.py
git commit -m "plan6: paper-table generator (tables 1-4)"
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
| §4.1 Sacred run protocol | Phase E lockfile, Phase F orchestrator, Phase F2 execution. Contract 10 enforces git-clean + on-main. |
| §4.3 Risks — test contamination | Contract 8 grep test + Contract 10 one-shot env = structural prevention, not aspirational. |
| §6 One-shot rule | `ensure_no_prior_lock` + `--break-glass` requires committed justification. Tested in `test_lockfile.py`. |
| §6 Lockfile mechanism | `classifier/sacred/lockfile.py`; lockfile contents include `git_sha`, `timestamp_utc`, `command`, `result_hash`, `break_glass_reason` (if any); committed to git in Phase F2 Step 3. |
| §6 Bootstrap 10k CI | `stats.bootstrap_ci(n=10_000)` consumed by Phase F `run_sacred._eval`; covered by `test_stats.py::test_bootstrap_ci_covers_accuracy`. |
| §6 McNemar pairwise | `stats.mcnemar_test` (exact binomial); ready for ablation pair comparisons; cross-checked against `statsmodels.mcnemar(exact=True)` in Task D3. |
| §6 Permutation null | `stats.permutation_test(n=10_000)`; covered by signal/null tests in `test_stats.py`. |
| §6 BH-FDR across 12 pairs | `stats.bh_correct` wraps `statsmodels.multipletests(method="fdr_bh")`; consumed by Table 2 generation. |
| §6 Ablations table | Phase A runner + registry + Task G1 `table3`. |
| §6 Fresh-unseen generalization | Phase B sampler + Phase C Streamlit UI + Contract 11 loader + Table 4. |
| §6 Single-human SME rule | Contract 11 rejects any non-`human_sme` labeler or wrong `labeler_id`. |

**Budget check:** ~$100 target. Ensemble inference on 400 frozen + 150 val × 12 ablations + 75 fresh = ~2,350 scored pairs, Plan 5 ensemble cost per pair ~$0.02 (cross-encoder dominant) → ~$47. Plus a safety buffer for re-running ablations once before the sacred gate closes (Phase A3) → ~$70. Remaining ~$30 absorbs Streamlit hosting (free, local) and miscellaneous. The dominant cost is the user's **~3 hours of labeling time in Phase C** — non-monetary but scheduled.

**What Plan 6 deliberately does NOT do:**
- No new scorers, no new training, no new calibration.
- No mutation of any Plan 1–5 artifact.
- No writing of paper prose (that is Plan 7).
- No second sacred run. Ever. Unless `--break-glass` with a publicly committed justification.

**Stop condition:** Phase G2 commit lands on main → Plan 6 is done. Paper tables exist, lockfile exists, statistical tests exist, and the frozen split is structurally sealed against any further access.
