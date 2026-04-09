# Plan 2 — LLM-SME Labeling (Gap-Filler) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce silver LLM-SME labels (`provenance_tag="llm_sme_v1"`, default weight 0.6) ONLY for `(source_framework, source_id, target_framework, target_node_id)` tuples in the Tier-B 26-pair matrix that are NOT already covered by a train-eligible upstream row. Plan 2 is explicitly downgraded per spec §7 to "gap-filler for pairs upstream does not cover or holds out." Upstream gold (`upstream_v1`) remains the primary training signal where it exists; this plan makes sure no `(src_fw, tgt_fw)` pair in the matrix is left with zero training signal, and emits a coverage manifest the Plan 5 trainer and Plan 6 evaluator can both consume.

**Architecture:** Four-stage pipeline. (1) A `gap_selector` joins the candidate pool `data/candidates/pool_v1.jsonl` against the train-eligible slice of `data/upstream/mappings_v1.jsonl` (`target_id_unresolved=False AND target_node_id IS NOT NULL AND held_out=False` per `data/upstream/partition.json`) to compute the per-pair set of tuples upstream does NOT cover. (2) A single-persona Level-E labeler (Claude Sonnet 4.6 via the Anthropic Message Batches API) labels those gap tuples with an idempotent disk cache keyed by `sha256(rendered_prompt + model_version)`. (3) A writer emits JSONL rows with `provenance_tag="llm_sme_v1"` as a top-level field, byte-stable via `classifier.data.splits._write_jsonl_stable`. (4) A coverage auditor computes per-pair counts of `{upstream_gold, llm_sme_silver, total}` and FAILS LOUDLY if any pair has zero total signal. No human SME block, no three-persona aggregation, no calibration set — the Plan 6 calibration pool is sourced from train-eligible upstream per spec §6 / §2 D7.

**Tech Stack:** Python 3.11, `anthropic` SDK (Messages + Batches), `jinja2`, `pydantic v2`, `tenacity`, `pandas`, `pytest`, the shipped `classifier.data.upstream_loader`, `classifier.data.upstream_id_normalize`, and `classifier.data.contamination` modules from Plan 1-B/1-C.

---

## Spec Reference

Implements the Plan 2 bullet in `docs/superpowers/specs/2026-04-08-upstream-crosswalk-integration-design.md` §7 ("Downgraded to 'gap-filler for pairs upstream does not cover or holds out.' Provenance tagging updated accordingly."), the provenance/weight contract in §4.5 (Table: `llm_sme_v1` default weight 0.6), the evaluation contract in §6 (calibration resourced from upstream, frozen test untouched), and the YAGNI list in §9 (no fresh human SME block).

**Supersedes:** `docs/superpowers/plans/2026-04-07-plan2-llm-sme-labeling.md` (retained as historical record; do NOT delete or edit).

**Depends on (already shipped):**
- Plan 1-B: `data/candidates/pool_v1.jsonl` over the Tier-B 26-pair matrix, `data/upstream/mappings_v1.jsonl`, `data/upstream/partition.json`, `classifier/data/contamination.py`.
- Plan 1-C: `target_node_id` / `target_id_unresolved` columns and `classifier/data/upstream_id_normalize.py`.

**Out of scope for Plan 2:**
- Any re-spec of upstream ingestion, contamination auditing, or id normalization (Plans 1-B/1-C already shipped them).
- Any modification of `human_test_frozen.jsonl`, `data/splits/hashes.json` existing entries, or the honesty-firewall CI tests.
- Any fresh human SME labeling (removed per spec §2 D7 and §7 Plan 6).
- Reranker, classifier training, or evaluation (Plans 4/5/6).
- Three-persona aggregation, Sonnet↔Opus κ study, isotonic calibration — those were specific to the replaced 2026-04-07 plan; the spec §4.5 per-tag weighting (single default 0.6) subsumes them.

---

## File Structure

**New files created by this plan:**

| Path | Responsibility |
|---|---|
| `classifier/labeling/__init__.py` | Subpackage marker |
| `classifier/labeling/schemas.py` | Pydantic v2 `GapTuple`, `LLMSMELabel`, `CoverageRow` |
| `classifier/labeling/gap_selector.py` | Join pool × train-eligible upstream → per-pair gap-tuple list |
| `classifier/labeling/prompts.py` | Jinja2 loader + deterministic rendered-prompt SHA |
| `classifier/labeling/client.py` | `LabelerClient` wrapping `anthropic` Batches + disk cache + cost ledger |
| `classifier/labeling/bulk.py` | Batches dispatcher over gap tuples (single persona) |
| `classifier/labeling/writer.py` | Byte-stable JSONL writer for `llm_sme_v1` rows |
| `classifier/labeling/coverage.py` | Per-pair coverage auditor + manifest emitter |
| `classifier/config/llm_sme_prompts/v1/system.j2` | Single shared system prompt |
| `classifier/config/llm_sme_prompts/v1/user.j2` | Single per-pair user prompt |
| `classifier/scripts/build_gap_tuples.py` | Entry point: select gap tuples |
| `classifier/scripts/run_llm_sme_labeling.py` | Entry point: dispatch Batches |
| `classifier/scripts/finalize_llm_sme.py` | Entry point: merge cache → JSONL → coverage audit |
| `classifier/tests/test_gap_selector.py` | Selector correctness on fixtures |
| `classifier/tests/test_llm_sme_prompts.py` | Template render + hash stability |
| `classifier/tests/test_llm_sme_client.py` | Cache + ledger + retry |
| `classifier/tests/test_llm_sme_writer.py` | `provenance_tag` presence, byte-stability |
| `classifier/tests/test_llm_sme_coverage.py` | Coverage pass/fail fixtures |
| `data/labels/llm_sme/v1/gap_tuples.jsonl` | Selected gap tuples |
| `data/labels/llm_sme/v1/raw_responses.jsonl` | Append-only raw API responses |
| `data/labels/llm_sme/v1/labels.jsonl` | Final silver labels (`provenance_tag="llm_sme_v1"`) |
| `data/labels/llm_sme/v1/coverage_manifest.json` | Per-pair `{upstream_gold, llm_sme_silver, total}` counts |
| `data/labels/llm_sme/v1/hashes.json` | SHA256 manifest for the above files |
| `data/cost_ledger.jsonl` | Append-only cost log (shared with future plans) |

**Modified files:**
- `requirements-classifier.txt` — append `anthropic==0.39.0`, `jinja2==3.1.4`, `pydantic==2.9.2`, `tenacity==9.0.0` if not already present.

**Must NOT touch:**
- `data/splits/human_test_frozen.jsonl`, `data/splits/human_cal.jsonl`, `data/splits/hashes.json` (except appending an `llm_sme_v1` sub-key in Task 7, never modifying existing entries).
- Anything under `data/upstream/`, `third_party/genai-crosswalk/`, or `mapping_engine/`.
- `classifier/data/upstream_loader.py`, `classifier/data/upstream_id_normalize.py`, `classifier/data/contamination.py`.

---

## Pre-flight

- [ ] **Step 1: Confirm dependencies shipped**

```bash
test -f data/candidates/pool_v1.jsonl
test -f data/upstream/mappings_v1.jsonl
test -f data/upstream/partition.json
python -c "from classifier.data.upstream_loader import load_all_entries; print('ok')"
python -c "from classifier.data.upstream_id_normalize import canonicalize_target; print('ok')"
python -c "from classifier.data.contamination import load_partition; print('ok') if True else None"
```

Expected: all commands succeed silently; `python` commands print `ok`. If any fail, Plan 1-B/1-C is not shipped and Plan 2 is blocked.

- [ ] **Step 2: Confirm the 26-pair matrix is the source of truth**

```bash
python -c "from classifier.data.candidates import FRAMEWORK_PAIRS; print(len(FRAMEWORK_PAIRS))"
```

Expected: `26`.

- [ ] **Step 3: Confirm upstream row schema**

```bash
head -1 data/upstream/mappings_v1.jsonl | python -c "import json,sys; r=json.loads(sys.stdin.read()); print(sorted(r.keys()))"
```

Expected output includes `source_framework`, `source_id`, `target_framework`, `target_node_id`, `target_id_unresolved`, `provenance_sha`.

---

## Task 1 — Deps + package skeleton

**Files:**
- Modify: `requirements-classifier.txt`
- Create: `classifier/labeling/__init__.py`

- [ ] **Step 1: Append deps (skip any already present)**

```
# Plan 2 additions
anthropic==0.39.0
jinja2==3.1.4
pydantic==2.9.2
tenacity==9.0.0
```

- [ ] **Step 2: Install and smoke test**

```bash
pip install -r requirements-classifier.txt
python -c "import anthropic, jinja2, pydantic, tenacity; print(anthropic.__version__)"
```

Expected: prints `0.39.0`, no ImportError.

- [ ] **Step 3: Create empty package marker**

```bash
mkdir -p classifier/labeling classifier/config/llm_sme_prompts/v1
: > classifier/labeling/__init__.py
```

- [ ] **Step 4: Commit**

```bash
git add requirements-classifier.txt classifier/labeling/__init__.py
git commit -m "plan2: add labeling subpackage + anthropic/jinja2/pydantic/tenacity deps"
```

---

## Task 2 — Schemas (pydantic v2)

**Files:**
- Create: `classifier/labeling/schemas.py`
- Create: `classifier/tests/test_llm_sme_schemas.py`

- [ ] **Step 1: Write the failing test first**

```python
# classifier/tests/test_llm_sme_schemas.py
import pytest
from classifier.labeling.schemas import GapTuple, LLMSMELabel, CoverageRow


def test_gap_tuple_roundtrip():
    g = GapTuple(
        source_framework="owasp_llm",
        source_id="LLM01",
        target_framework="mitre_atlas",
        target_node_id="mitre_atlas:AML.T0051.000",
    )
    assert g.model_dump()["source_id"] == "LLM01"


def test_llm_sme_label_requires_provenance_tag():
    lbl = LLMSMELabel(
        source_framework="owasp_llm",
        source_id="LLM01",
        target_framework="mitre_atlas",
        target_node_id="mitre_atlas:AML.T0051.000",
        relation="related",
        confidence=0.82,
        rationale="jailbreak overlap",
        prompt_sha="0" * 64,
        model_version="claude-sonnet-4-5-20251101",
    )
    d = lbl.model_dump()
    assert d["provenance_tag"] == "llm_sme_v1"
    assert d["weight"] == 0.6


def test_llm_sme_label_rejects_bad_relation():
    with pytest.raises(ValueError):
        LLMSMELabel(
            source_framework="owasp_llm",
            source_id="LLM01",
            target_framework="mitre_atlas",
            target_node_id="mitre_atlas:AML.T0051.000",
            relation="bogus",
            confidence=0.5,
            rationale="x",
            prompt_sha="0" * 64,
            model_version="m",
        )


def test_coverage_row_flags_empty_pair():
    row = CoverageRow(
        source_framework="owasp_llm",
        target_framework="mitre_atlas",
        upstream_gold=0,
        llm_sme_silver=0,
    )
    assert row.total == 0
    assert row.empty is True
```

Run: `pytest classifier/tests/test_llm_sme_schemas.py -x`
Expected: 4 failures (module not yet created).

- [ ] **Step 2: Implement schemas**

```python
# classifier/labeling/schemas.py
from typing import Literal
from pydantic import BaseModel, Field, computed_field


Relation = Literal["equivalent", "related", "partial", "unrelated"]


class GapTuple(BaseModel):
    source_framework: str
    source_id: str
    target_framework: str
    target_node_id: str


class LLMSMELabel(BaseModel):
    source_framework: str
    source_id: str
    target_framework: str
    target_node_id: str
    relation: Relation
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str
    prompt_sha: str = Field(min_length=64, max_length=64)
    model_version: str
    provenance_tag: Literal["llm_sme_v1"] = "llm_sme_v1"
    weight: float = 0.6


class CoverageRow(BaseModel):
    source_framework: str
    target_framework: str
    upstream_gold: int = Field(ge=0)
    llm_sme_silver: int = Field(ge=0)

    @computed_field
    @property
    def total(self) -> int:
        return self.upstream_gold + self.llm_sme_silver

    @computed_field
    @property
    def empty(self) -> bool:
        return self.total == 0
```

Run: `pytest classifier/tests/test_llm_sme_schemas.py -x`
Expected: 4 passed.

- [ ] **Step 3: Commit**

```bash
git add classifier/labeling/schemas.py classifier/tests/test_llm_sme_schemas.py
git commit -m "plan2: pydantic schemas for gap tuples, llm_sme_v1 labels, coverage rows"
```

---

## Task 3 — Gap selector (the heart of the plan)

The selector consumes `data/candidates/pool_v1.jsonl` (the 26-pair candidate pool from Plan 1-B) and `data/upstream/mappings_v1.jsonl` + `data/upstream/partition.json` (from Plan 1-B/1-C), and emits only those candidate tuples that are NOT already covered by a train-eligible upstream row. Train-eligible is defined as spec §4.5: `target_id_unresolved=False AND target_node_id IS NOT NULL AND held_out=False` (i.e., the row is not in `partition.json["held_out"]`).

**Files:**
- Create: `classifier/labeling/gap_selector.py`
- Create: `classifier/tests/test_gap_selector.py`

- [ ] **Step 1: Write the failing test first**

```python
# classifier/tests/test_gap_selector.py
import json
from pathlib import Path
from classifier.labeling.gap_selector import select_gap_tuples


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True) + "\n")


def test_gap_selector_excludes_upstream_gold_and_held_out(tmp_path):
    pool = tmp_path / "pool.jsonl"
    mappings = tmp_path / "mappings.jsonl"
    partition = tmp_path / "partition.json"

    _write_jsonl(
        pool,
        [
            # covered by upstream gold (train-eligible)
            {"source_framework": "owasp_llm", "source_id": "LLM01",
             "target_framework": "mitre_atlas", "target_node_id": "mitre_atlas:AML.T0051.000"},
            # upstream held-out (contamination) → gap
            {"source_framework": "owasp_llm", "source_id": "LLM02",
             "target_framework": "mitre_atlas", "target_node_id": "mitre_atlas:AML.T0054"},
            # upstream row exists but target_id_unresolved → gap
            {"source_framework": "owasp_llm", "source_id": "LLM03",
             "target_framework": "csa_aicm", "target_node_id": "csa_aicm:AIS-01"},
            # no upstream row at all → gap
            {"source_framework": "owasp_llm", "source_id": "LLM04",
             "target_framework": "nist_rmf", "target_node_id": "nist_rmf:GOVERN-1.6"},
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

    gaps = select_gap_tuples(pool, mappings, partition)
    ids = sorted(g.source_id for g in gaps)
    assert ids == ["LLM02", "LLM03", "LLM04"]
```

Run: `pytest classifier/tests/test_gap_selector.py -x`
Expected: fails (module missing).

- [ ] **Step 2: Implement the selector**

```python
# classifier/labeling/gap_selector.py
from __future__ import annotations
import json
from pathlib import Path
from .schemas import GapTuple


def _train_eligible(row: dict, held_out: set[str]) -> bool:
    if row.get("target_id_unresolved", True):
        return False
    if row.get("target_node_id") in (None, ""):
        return False
    if row.get("provenance_sha") in held_out:
        return False
    return True


def _pair_key(row: dict) -> tuple[str, str, str, str]:
    return (
        row["source_framework"],
        row["source_id"],
        row["target_framework"],
        row["target_node_id"],
    )


def select_gap_tuples(
    pool_path: Path,
    mappings_path: Path,
    partition_path: Path,
) -> list[GapTuple]:
    partition = json.loads(Path(partition_path).read_text())
    held_out: set[str] = set(partition.get("held_out", []))

    covered: set[tuple[str, str, str, str]] = set()
    with Path(mappings_path).open() as fh:
        for line in fh:
            if not line.strip():
                continue
            row = json.loads(line)
            if _train_eligible(row, held_out):
                covered.add(_pair_key(row))

    gaps: list[GapTuple] = []
    seen: set[tuple[str, str, str, str]] = set()
    with Path(pool_path).open() as fh:
        for line in fh:
            if not line.strip():
                continue
            row = json.loads(line)
            key = _pair_key(row)
            if key in covered or key in seen:
                continue
            seen.add(key)
            gaps.append(
                GapTuple(
                    source_framework=row["source_framework"],
                    source_id=row["source_id"],
                    target_framework=row["target_framework"],
                    target_node_id=row["target_node_id"],
                )
            )
    return gaps
```

Run: `pytest classifier/tests/test_gap_selector.py -x`
Expected: passed.

- [ ] **Step 3: Commit**

```bash
git add classifier/labeling/gap_selector.py classifier/tests/test_gap_selector.py
git commit -m "plan2: gap selector excludes train-eligible upstream rows and held-out provenance_sha"
```

---

## Task 4 — Prompt templates + rendered-prompt hash

**Files:**
- Create: `classifier/config/llm_sme_prompts/v1/system.j2`
- Create: `classifier/config/llm_sme_prompts/v1/user.j2`
- Create: `classifier/labeling/prompts.py`
- Create: `classifier/tests/test_llm_sme_prompts.py`

- [ ] **Step 1: Write the system template**

```jinja
{# classifier/config/llm_sme_prompts/v1/system.j2 #}
You are a senior AI security subject-matter expert producing silver-tier
gap-fill labels for the ai-security-framework-crosswalk project. You will
be given one (source_control, target_control) pair and must return a
strict JSON object with keys: relation, confidence, rationale.

relation MUST be one of: "equivalent", "related", "partial", "unrelated".
confidence MUST be a float in [0.0, 1.0].
rationale MUST be a single sentence.

Respond with JSON only. No prose, no markdown fences.
```

- [ ] **Step 2: Write the user template**

```jinja
{# classifier/config/llm_sme_prompts/v1/user.j2 #}
SOURCE ({{ source_framework }} / {{ source_id }}):
{{ source_text }}

TARGET ({{ target_framework }} / {{ target_node_id }}):
{{ target_text }}

Return JSON: {"relation": "...", "confidence": 0.xx, "rationale": "..."}
```

- [ ] **Step 3: Write the failing test**

```python
# classifier/tests/test_llm_sme_prompts.py
from classifier.labeling.prompts import render_prompt, prompt_sha


def test_render_prompt_stable_hash():
    ctx = {
        "source_framework": "owasp_llm",
        "source_id": "LLM01",
        "source_text": "Prompt injection risk",
        "target_framework": "mitre_atlas",
        "target_node_id": "mitre_atlas:AML.T0051.000",
        "target_text": "Direct prompt injection technique",
    }
    sys1, usr1 = render_prompt(ctx)
    sys2, usr2 = render_prompt(ctx)
    assert sys1 == sys2
    assert usr1 == usr2
    h = prompt_sha(sys1, usr1)
    assert len(h) == 64
    assert prompt_sha(sys2, usr2) == h


def test_render_prompt_includes_ids():
    ctx = {
        "source_framework": "owasp_llm", "source_id": "LLM01",
        "source_text": "x", "target_framework": "mitre_atlas",
        "target_node_id": "mitre_atlas:AML.T0054", "target_text": "y",
    }
    _, usr = render_prompt(ctx)
    assert "LLM01" in usr
    assert "mitre_atlas:AML.T0054" in usr
```

Run: `pytest classifier/tests/test_llm_sme_prompts.py -x`
Expected: fails (module missing).

- [ ] **Step 4: Implement the prompt loader**

```python
# classifier/labeling/prompts.py
from __future__ import annotations
import hashlib
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, StrictUndefined

_TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "config" / "llm_sme_prompts" / "v1"
_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATE_DIR)),
    undefined=StrictUndefined,
    keep_trailing_newline=True,
    autoescape=False,
)


def render_prompt(ctx: dict) -> tuple[str, str]:
    system = _env.get_template("system.j2").render(**ctx)
    user = _env.get_template("user.j2").render(**ctx)
    return system, user


def prompt_sha(system: str, user: str) -> str:
    h = hashlib.sha256()
    h.update(system.encode("utf-8"))
    h.update(b"\x00")
    h.update(user.encode("utf-8"))
    return h.hexdigest()
```

Run: `pytest classifier/tests/test_llm_sme_prompts.py -x`
Expected: passed.

- [ ] **Step 5: Commit**

```bash
git add classifier/config/llm_sme_prompts classifier/labeling/prompts.py classifier/tests/test_llm_sme_prompts.py
git commit -m "plan2: jinja2 prompt templates + deterministic rendered-prompt sha"
```

---

## Task 5 — Labeler client (cache + ledger + retry)

**Files:**
- Create: `classifier/labeling/client.py`
- Create: `classifier/tests/test_llm_sme_client.py`

- [ ] **Step 1: Write the failing test with a fake anthropic client**

```python
# classifier/tests/test_llm_sme_client.py
import json
from pathlib import Path
from classifier.labeling.client import LabelerClient


class _FakeMessages:
    def __init__(self):
        self.calls = 0

    def create(self, *, model, system, messages, max_tokens):
        self.calls += 1
        return type("R", (), {
            "content": [type("B", (), {"text": '{"relation":"related","confidence":0.7,"rationale":"ok"}'})()],
            "model": model,
        })()


class _FakeClient:
    def __init__(self):
        self.messages = _FakeMessages()


def test_client_caches_on_prompt_sha(tmp_path):
    cache = tmp_path / "cache"
    ledger = tmp_path / "ledger.jsonl"
    fake = _FakeClient()
    c = LabelerClient(
        anthropic_client=fake,
        cache_dir=cache,
        ledger_path=ledger,
        model="claude-sonnet-4-5-20251101",
    )
    out1 = c.label("sysprompt", "userprompt")
    out2 = c.label("sysprompt", "userprompt")
    assert out1 == out2
    assert fake.messages.calls == 1  # second hit served from cache
    ledger_rows = [json.loads(l) for l in ledger.read_text().splitlines() if l.strip()]
    assert len(ledger_rows) == 1
    assert ledger_rows[0]["cache_hit"] is False
```

Run: `pytest classifier/tests/test_llm_sme_client.py -x`
Expected: fails.

- [ ] **Step 2: Implement the client**

```python
# classifier/labeling/client.py
from __future__ import annotations
import json
import time
from dataclasses import dataclass
from pathlib import Path
from tenacity import retry, stop_after_attempt, wait_exponential
from .prompts import prompt_sha


@dataclass
class LabelerClient:
    anthropic_client: object
    cache_dir: Path
    ledger_path: Path
    model: str
    max_tokens: int = 512

    def __post_init__(self) -> None:
        self.cache_dir = Path(self.cache_dir)
        self.ledger_path = Path(self.ledger_path)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)

    def _cache_path(self, sha: str) -> Path:
        return self.cache_dir / f"{sha}.json"

    def _append_ledger(self, row: dict) -> None:
        with self.ledger_path.open("a") as fh:
            fh.write(json.dumps(row, sort_keys=True) + "\n")

    @retry(stop=stop_after_attempt(5), wait=wait_exponential(min=1, max=30))
    def _call_api(self, system: str, user: str) -> str:
        resp = self.anthropic_client.messages.create(
            model=self.model,
            system=system,
            messages=[{"role": "user", "content": user}],
            max_tokens=self.max_tokens,
        )
        return resp.content[0].text

    def label(self, system: str, user: str) -> dict:
        sha = prompt_sha(system, user)
        cache = self._cache_path(sha)
        if cache.exists():
            self._append_ledger({
                "ts": time.time(), "prompt_sha": sha, "model": self.model, "cache_hit": True,
            })
            return json.loads(cache.read_text())
        text = self._call_api(system, user)
        parsed = json.loads(text)
        parsed["_prompt_sha"] = sha
        parsed["_model_version"] = self.model
        cache.write_text(json.dumps(parsed, sort_keys=True))
        self._append_ledger({
            "ts": time.time(), "prompt_sha": sha, "model": self.model, "cache_hit": False,
        })
        return parsed
```

Run: `pytest classifier/tests/test_llm_sme_client.py -x`
Expected: passed.

- [ ] **Step 3: Commit**

```bash
git add classifier/labeling/client.py classifier/tests/test_llm_sme_client.py
git commit -m "plan2: labeler client with sha-keyed disk cache + cost ledger + tenacity retry"
```

---

## Task 6 — Bulk dispatcher + writer

**Files:**
- Create: `classifier/labeling/bulk.py`
- Create: `classifier/labeling/writer.py`
- Create: `classifier/tests/test_llm_sme_writer.py`

- [ ] **Step 1: Writer failing test**

```python
# classifier/tests/test_llm_sme_writer.py
import json
from pathlib import Path
from classifier.labeling.schemas import LLMSMELabel
from classifier.labeling.writer import write_labels


def test_writer_emits_provenance_tag(tmp_path):
    out = tmp_path / "labels.jsonl"
    labels = [
        LLMSMELabel(
            source_framework="owasp_llm", source_id="LLM01",
            target_framework="mitre_atlas", target_node_id="mitre_atlas:AML.T0051.000",
            relation="related", confidence=0.7, rationale="x",
            prompt_sha="0" * 64, model_version="m",
        )
    ]
    write_labels(labels, out)
    rows = [json.loads(l) for l in out.read_text().splitlines() if l.strip()]
    assert rows[0]["provenance_tag"] == "llm_sme_v1"
    assert rows[0]["weight"] == 0.6


def test_writer_is_byte_stable(tmp_path):
    out1 = tmp_path / "a.jsonl"
    out2 = tmp_path / "b.jsonl"
    labels = [
        LLMSMELabel(
            source_framework="owasp_llm", source_id="LLM01",
            target_framework="mitre_atlas", target_node_id="mitre_atlas:AML.T0051.000",
            relation="related", confidence=0.7, rationale="x",
            prompt_sha="0" * 64, model_version="m",
        )
    ]
    write_labels(labels, out1)
    write_labels(labels, out2)
    assert out1.read_bytes() == out2.read_bytes()
```

Run: `pytest classifier/tests/test_llm_sme_writer.py -x`
Expected: fails.

- [ ] **Step 2: Implement the writer**

```python
# classifier/labeling/writer.py
from __future__ import annotations
import json
from pathlib import Path
from .schemas import LLMSMELabel


def write_labels(labels: list[LLMSMELabel], out_path: Path) -> None:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w") as fh:
        for lbl in labels:
            d = lbl.model_dump()
            fh.write(json.dumps(d, sort_keys=True, ensure_ascii=False) + "\n")
```

Run: `pytest classifier/tests/test_llm_sme_writer.py -x`
Expected: passed.

- [ ] **Step 3: Implement the bulk dispatcher**

```python
# classifier/labeling/bulk.py
from __future__ import annotations
from pathlib import Path
from typing import Callable
from .client import LabelerClient
from .prompts import render_prompt, prompt_sha
from .schemas import GapTuple, LLMSMELabel


def label_gap_tuples(
    gaps: list[GapTuple],
    text_lookup: Callable[[str, str], str],
    client: LabelerClient,
) -> list[LLMSMELabel]:
    """text_lookup(framework, node_id) -> text body (from nodes.json)."""
    out: list[LLMSMELabel] = []
    for g in gaps:
        ctx = {
            "source_framework": g.source_framework,
            "source_id": g.source_id,
            "source_text": text_lookup(g.source_framework, g.source_id),
            "target_framework": g.target_framework,
            "target_node_id": g.target_node_id,
            "target_text": text_lookup(g.target_framework, g.target_node_id.split(":", 1)[-1]),
        }
        system, user = render_prompt(ctx)
        sha = prompt_sha(system, user)
        resp = client.label(system, user)
        out.append(
            LLMSMELabel(
                source_framework=g.source_framework,
                source_id=g.source_id,
                target_framework=g.target_framework,
                target_node_id=g.target_node_id,
                relation=resp["relation"],
                confidence=float(resp["confidence"]),
                rationale=resp["rationale"],
                prompt_sha=sha,
                model_version=client.model,
            )
        )
    return out
```

- [ ] **Step 4: Commit**

```bash
git add classifier/labeling/bulk.py classifier/labeling/writer.py classifier/tests/test_llm_sme_writer.py
git commit -m "plan2: bulk gap-tuple dispatcher + byte-stable llm_sme_v1 writer"
```

---

## Task 7 — Coverage auditor (fails loudly on empty pairs)

**Files:**
- Create: `classifier/labeling/coverage.py`
- Create: `classifier/tests/test_llm_sme_coverage.py`

- [ ] **Step 1: Failing test**

```python
# classifier/tests/test_llm_sme_coverage.py
import json
from pathlib import Path
import pytest
from classifier.labeling.coverage import audit_coverage, CoverageError


def _j(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(r, sort_keys=True) for r in rows) + "\n")


def test_audit_fails_on_empty_pair(tmp_path):
    mappings = tmp_path / "mappings.jsonl"
    labels = tmp_path / "labels.jsonl"
    partition = tmp_path / "partition.json"
    _j(mappings, [
        {"source_framework": "owasp_llm", "source_id": "LLM01",
         "target_framework": "mitre_atlas", "target_node_id": "mitre_atlas:AML.T0051.000",
         "target_id_unresolved": False, "provenance_sha": "a" * 64},
    ])
    _j(labels, [])
    partition.write_text(json.dumps({"held_out": []}))
    pairs = [("owasp_llm", "mitre_atlas"), ("owasp_llm", "csa_aicm")]
    with pytest.raises(CoverageError):
        audit_coverage(pairs, mappings, labels, partition, tmp_path / "manifest.json")


def test_audit_passes_when_silver_fills_gap(tmp_path):
    mappings = tmp_path / "mappings.jsonl"
    labels = tmp_path / "labels.jsonl"
    partition = tmp_path / "partition.json"
    _j(mappings, [
        {"source_framework": "owasp_llm", "source_id": "LLM01",
         "target_framework": "mitre_atlas", "target_node_id": "mitre_atlas:AML.T0051.000",
         "target_id_unresolved": False, "provenance_sha": "a" * 64},
    ])
    _j(labels, [
        {"source_framework": "owasp_llm", "source_id": "LLM02",
         "target_framework": "csa_aicm", "target_node_id": "csa_aicm:AIS-01",
         "provenance_tag": "llm_sme_v1", "weight": 0.6},
    ])
    partition.write_text(json.dumps({"held_out": []}))
    manifest = tmp_path / "manifest.json"
    pairs = [("owasp_llm", "mitre_atlas"), ("owasp_llm", "csa_aicm")]
    audit_coverage(pairs, mappings, labels, partition, manifest)
    data = json.loads(manifest.read_text())
    by_pair = {(r["source_framework"], r["target_framework"]): r for r in data["pairs"]}
    assert by_pair[("owasp_llm", "mitre_atlas")]["upstream_gold"] == 1
    assert by_pair[("owasp_llm", "csa_aicm")]["llm_sme_silver"] == 1
```

Run: `pytest classifier/tests/test_llm_sme_coverage.py -x`
Expected: fails.

- [ ] **Step 2: Implement the auditor**

```python
# classifier/labeling/coverage.py
from __future__ import annotations
import json
from collections import defaultdict
from pathlib import Path
from .schemas import CoverageRow


class CoverageError(RuntimeError):
    pass


def _iter_jsonl(path: Path):
    with Path(path).open() as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)


def audit_coverage(
    pairs: list[tuple[str, str]],
    mappings_path: Path,
    labels_path: Path,
    partition_path: Path,
    manifest_path: Path,
) -> list[CoverageRow]:
    held_out = set(json.loads(Path(partition_path).read_text()).get("held_out", []))
    gold: dict[tuple[str, str], int] = defaultdict(int)
    for row in _iter_jsonl(mappings_path):
        if row.get("target_id_unresolved", True):
            continue
        if not row.get("target_node_id"):
            continue
        if row.get("provenance_sha") in held_out:
            continue
        gold[(row["source_framework"], row["target_framework"])] += 1

    silver: dict[tuple[str, str], int] = defaultdict(int)
    for row in _iter_jsonl(labels_path):
        if row.get("provenance_tag") != "llm_sme_v1":
            continue
        silver[(row["source_framework"], row["target_framework"])] += 1

    rows: list[CoverageRow] = []
    empties: list[tuple[str, str]] = []
    for src, tgt in pairs:
        r = CoverageRow(
            source_framework=src,
            target_framework=tgt,
            upstream_gold=gold.get((src, tgt), 0),
            llm_sme_silver=silver.get((src, tgt), 0),
        )
        rows.append(r)
        if r.empty:
            empties.append((src, tgt))

    manifest_path = Path(manifest_path)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(
            {"pairs": [r.model_dump() for r in rows]},
            sort_keys=True, indent=2,
        ) + "\n"
    )
    if empties:
        raise CoverageError(
            f"{len(empties)} pair(s) have zero training signal: {empties}"
        )
    return rows
```

Run: `pytest classifier/tests/test_llm_sme_coverage.py -x`
Expected: passed.

- [ ] **Step 3: Commit**

```bash
git add classifier/labeling/coverage.py classifier/tests/test_llm_sme_coverage.py
git commit -m "plan2: per-pair coverage auditor fails loudly on zero-signal pairs"
```

---

## Task 8 — Entry-point scripts

**Files:**
- Create: `classifier/scripts/build_gap_tuples.py`
- Create: `classifier/scripts/run_llm_sme_labeling.py`
- Create: `classifier/scripts/finalize_llm_sme.py`

- [ ] **Step 1: `build_gap_tuples.py`**

```python
# classifier/scripts/build_gap_tuples.py
from __future__ import annotations
import json
from pathlib import Path
from classifier.labeling.gap_selector import select_gap_tuples


POOL = Path("data/candidates/pool_v1.jsonl")
MAPPINGS = Path("data/upstream/mappings_v1.jsonl")
PARTITION = Path("data/upstream/partition.json")
OUT = Path("data/labels/llm_sme/v1/gap_tuples.jsonl")


def main() -> None:
    gaps = select_gap_tuples(POOL, MAPPINGS, PARTITION)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w") as fh:
        for g in gaps:
            fh.write(json.dumps(g.model_dump(), sort_keys=True) + "\n")
    print(f"wrote {len(gaps)} gap tuples → {OUT}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: `run_llm_sme_labeling.py`**

```python
# classifier/scripts/run_llm_sme_labeling.py
from __future__ import annotations
import json
import os
from pathlib import Path
import anthropic
from classifier.labeling.bulk import label_gap_tuples
from classifier.labeling.client import LabelerClient
from classifier.labeling.schemas import GapTuple
from classifier.labeling.writer import write_labels


GAPS = Path("data/labels/llm_sme/v1/gap_tuples.jsonl")
LABELS = Path("data/labels/llm_sme/v1/labels.jsonl")
CACHE = Path("data/labels/llm_sme/v1/cache")
LEDGER = Path("data/cost_ledger.jsonl")
NODES = Path("data/processed/nodes.json")
MODEL = "claude-sonnet-4-5-20251101"


def _text_lookup_factory():
    nodes = json.loads(NODES.read_text())
    index: dict[tuple[str, str], str] = {}
    for n in nodes:
        index[(n["framework"], n.get("local_id") or n["node_id"].split(":", 1)[-1])] = n.get("text", "")
    def lookup(framework: str, node_id: str) -> str:
        local = node_id.split(":", 1)[-1] if ":" in node_id else node_id
        return index.get((framework, local), "")
    return lookup


def main() -> None:
    gaps = [GapTuple(**json.loads(l)) for l in GAPS.read_text().splitlines() if l.strip()]
    client = LabelerClient(
        anthropic_client=anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"]),
        cache_dir=CACHE,
        ledger_path=LEDGER,
        model=MODEL,
    )
    labels = label_gap_tuples(gaps, _text_lookup_factory(), client)
    write_labels(labels, LABELS)
    print(f"wrote {len(labels)} silver labels → {LABELS}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: `finalize_llm_sme.py`**

```python
# classifier/scripts/finalize_llm_sme.py
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from classifier.data.candidates import FRAMEWORK_PAIRS
from classifier.labeling.coverage import audit_coverage


MAPPINGS = Path("data/upstream/mappings_v1.jsonl")
LABELS = Path("data/labels/llm_sme/v1/labels.jsonl")
PARTITION = Path("data/upstream/partition.json")
MANIFEST = Path("data/labels/llm_sme/v1/coverage_manifest.json")
HASHES = Path("data/labels/llm_sme/v1/hashes.json")


def main() -> None:
    audit_coverage(FRAMEWORK_PAIRS, MAPPINGS, LABELS, PARTITION, MANIFEST)
    files = [
        "data/labels/llm_sme/v1/gap_tuples.jsonl",
        "data/labels/llm_sme/v1/labels.jsonl",
        "data/labels/llm_sme/v1/coverage_manifest.json",
    ]
    hashes = {
        f: hashlib.sha256(Path(f).read_bytes()).hexdigest()
        for f in files if Path(f).exists()
    }
    HASHES.write_text(json.dumps({"llm_sme_v1": hashes}, sort_keys=True, indent=2) + "\n")
    print(f"coverage OK; hashes → {HASHES}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Smoke-run the gap builder (no API needed)**

```bash
python -m classifier.scripts.build_gap_tuples
wc -l data/labels/llm_sme/v1/gap_tuples.jsonl
```

Expected: non-zero line count; the number is the count of pool tuples not covered by train-eligible upstream.

- [ ] **Step 5: Commit**

```bash
git add classifier/scripts/build_gap_tuples.py classifier/scripts/run_llm_sme_labeling.py classifier/scripts/finalize_llm_sme.py data/labels/llm_sme/v1/gap_tuples.jsonl
git commit -m "plan2: entry-point scripts + initial gap_tuples.jsonl"
```

---

## Task 9 — Run the labeling + finalize

This is the only task that spends LLM budget. It requires `ANTHROPIC_API_KEY` in the environment (routed via `pass` per the project plan conventions).

- [ ] **Step 1: Dry-run cost estimate**

```bash
python -c "
import json
from pathlib import Path
n = sum(1 for _ in Path('data/labels/llm_sme/v1/gap_tuples.jsonl').open() if _.strip())
print(f'{n} gap tuples, rough estimate ~{n * 0.004:.2f} USD at Sonnet 4.6 rates')
"
```

Expected: printed estimate. If it exceeds the Plan 2 budget (≤ $100 for gap-filling), STOP and surface to the user before proceeding.

- [ ] **Step 2: Run the labeler**

```bash
ANTHROPIC_API_KEY="$(pass show anthropic/api-key)" python -m classifier.scripts.run_llm_sme_labeling
```

Expected: writes `data/labels/llm_sme/v1/labels.jsonl` with one row per gap tuple, each carrying `"provenance_tag":"llm_sme_v1"` and `"weight":0.6`.

- [ ] **Step 3: Finalize + audit**

```bash
python -m classifier.scripts.finalize_llm_sme
cat data/labels/llm_sme/v1/coverage_manifest.json | python -m json.tool | head -40
```

Expected: prints `coverage OK; hashes → data/labels/llm_sme/v1/hashes.json`, no `CoverageError`. Every entry in the manifest has `total >= 1`.

- [ ] **Step 4: Spot-check provenance tag on every row**

```bash
python -c "
import json
from pathlib import Path
bad = []
for line in Path('data/labels/llm_sme/v1/labels.jsonl').open():
    r = json.loads(line)
    if r.get('provenance_tag') != 'llm_sme_v1' or r.get('weight') != 0.6:
        bad.append(r)
print('bad rows:', len(bad))
assert not bad
"
```

Expected: `bad rows: 0`.

- [ ] **Step 5: Commit the derived artifacts**

```bash
git add data/labels/llm_sme/v1/labels.jsonl data/labels/llm_sme/v1/coverage_manifest.json data/labels/llm_sme/v1/hashes.json
git commit -m "plan2: silver llm_sme_v1 labels + coverage manifest (gap-filler only)"
```

---

## Task 10 — Full regression sweep

- [ ] **Step 1: Run every Plan 2 test + the honesty firewall test**

```bash
pytest classifier/tests/test_llm_sme_schemas.py classifier/tests/test_gap_selector.py \
       classifier/tests/test_llm_sme_prompts.py classifier/tests/test_llm_sme_client.py \
       classifier/tests/test_llm_sme_writer.py classifier/tests/test_llm_sme_coverage.py \
       classifier/tests/test_contamination.py -x
```

Expected: all green. The contamination test MUST remain passing — Plan 2 does not relax it.

- [ ] **Step 2: Confirm no forbidden files were touched**

```bash
git diff --name-only main -- data/splits/human_test_frozen.jsonl data/upstream/ third_party/genai-crosswalk/ mapping_engine/
```

Expected: empty output.

- [ ] **Step 3: Final commit tag**

```bash
git commit --allow-empty -m "plan2: complete — gap-fill labeling shipped, coverage manifest green"
```

---

## Self-review — spec items this plan satisfies

| Spec item | Where addressed |
|---|---|
| §7 Plan 2 downgrade to "gap-filler for pairs upstream does not cover or holds out" | Task 3 gap selector + Task 7 coverage auditor together enforce this — Plan 2 produces zero rows for `(src, tgt)` tuples already covered by train-eligible upstream |
| §4.5 `provenance_tag="llm_sme_v1"` as top-level field | `LLMSMELabel` schema (Task 2), writer test (Task 6), row spot-check (Task 9 Step 4) |
| §4.5 default weight 0.6 for `llm_sme_v1` | `LLMSMELabel.weight = 0.6` default, asserted in tests |
| §4.5 "Upstream does not replace LLM-SME. On pairs where upstream is held out under strict partitioning, LLM-SME remains the only training signal." | Task 3 selector includes held-out `provenance_sha` rows as gaps (test fixture `LLM02` → `AML.T0054`) |
| §6 Calibration resourced from upstream, not fresh SME | Out-of-scope section + Task 2 has no three-persona / κ code; no `human_cal.jsonl` writes anywhere in this plan |
| §6 Frozen test untouched | Task 10 Step 2 guards it via `git diff --name-only` |
| §9 No fresh human SME block | Out-of-scope section, no Phase-C scripts, no SME sheet generation |
| §9 No reranker / trainer / classifier work | Out-of-scope section; the plan only writes silver labels + coverage manifest |
| Plan 1-C target canonicalization already available | Task 3 uses `target_node_id` + `target_id_unresolved` directly from `data/upstream/mappings_v1.jsonl` instead of re-implementing normalization |
| Loud failure on zero-signal pairs (synthesis bullet) | `CoverageError` raised in `audit_coverage`, test `test_audit_fails_on_empty_pair` |
| Coverage manifest consumable by Plan 5 / Plan 6 | `data/labels/llm_sme/v1/coverage_manifest.json` with `{upstream_gold, llm_sme_silver, total}` per pair |

**Not in this plan (intentional):** upstream ingestion, contamination auditing, id normalization, reranker, classifier training, evaluation, human SME block, three-persona aggregation, isotonic calibration, Sonnet↔Opus κ study, llm_train/llm_val split (folded into Plan 5 since there is now no need for a Plan-2-owned split when upstream is the primary signal).
