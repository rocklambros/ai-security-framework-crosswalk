# Plan 2 — LLM-SME Labeling Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce the calibrated, frozen LLM-SME label set (~10k pairs × 3 personas) that unblocks all downstream training, plus the Sonnet↔Opus agreement study and the calibration-correction pipeline required for honest reporting.

**Architecture:** Three-persona Level-E labeling via the Anthropic Message Batches API on Sonnet 4.6 for bulk, Opus 4.6 for calibration and agreement. Idempotent disk cache keyed by `hash(prompt + model_version)`. Jinja2 prompt templates versioned and SHA256-hashed. Labels stored in three sequential versions (`v1_raw` → `v1_calibrated` → `v1_frozen`) with byte-stable JSONL and a hash manifest enforced in CI. A structural stop-gate refuses to freeze if Sonnet↔Opus κ < 0.5.

**Tech Stack:** Python 3.11, `anthropic` SDK (Messages + Batches), `jinja2`, `pydantic v2`, `tenacity`, `scikit-learn` (isotonic regression, Cohen's κ), `pandas`, `pytest`, existing `classifier/` scaffolding from Plan 1.

---

## Spec Reference

Implements §2.1 (candidate-pool rebuild on Lambda), §2.2 (Level-E three-persona protocol), §2.3 (calibration correction), §2.4 (Sonnet↔Opus gap study), §2.5 (label storage & versioning), §2.6 (llm_train / llm_val split creation), §2.7 (LLM budget) of `docs/superpowers/specs/2026-04-07-ai-security-crosswalk-classifier-design.md`.

Honors spec §6 commitments #1, #4, #5 (sacred run untouched; Sonnet↔Opus κ reported; raw vs calibrated reported).

**Out of scope for Plan 2:** any baseline or model training (Plans 3–5), evaluation on `human_test_frozen` (Plan 6), Dash app (Plan 7), writeup (Plan 8).

---

## Lessons Carried from Plan 1

These failure modes shaped Plan 2's design:

1. **Scoring-path drift** (the s8-np `--no-rerank` bug). Plan 2 has no scoring code, but the same principle applies to prompt rendering: the SHA256 of the rendered prompt (after Jinja2 expansion) is what the cache keys on. A subtle template change silently invalidates the cache — Task A4 asserts that the hash of a rendered fixture prompt is byte-stable across Python versions.
2. **Byte-stable JSON outputs.** Plan 1's `hashes.json` canary caught serialization drift. Plan 2 reuses `classifier.data.splits._write_jsonl_stable` (pinned `double_precision`, `date_format`, `force_ascii`) for every label file and adds `data/labels/hashes.json`.
3. **No in-place overwrites.** Session 8 taught us that overwriting `labeling_sheets/*.yaml` silently broke the parity test. Plan 2 versions labels under `v1_raw` / `v1_calibrated` / `v1_frozen` and NEVER mutates an existing version.
4. **Feasibility math as test.** Task C2's stratified sampler has a `test_sampler_feasibility` unit test that checks whether the requested strata actually exist in the candidate pool before dispatching any API call.
5. **Stop-gate on quality failure.** The s8-np plan defined stop conditions; Plan 2 Phase F has the analogous structural gate: `κ < 0.5 → raise, surface to user`.

---

## File Structure

**Plan 2 creates and only touches these paths:**

| Path | Purpose |
|---|---|
| `classifier/labeling/__init__.py` | Subpackage marker |
| `classifier/labeling/schemas.py` | Pydantic v2 `LabelRequest`, `LabelResponse`, `AggregatedLabel` |
| `classifier/labeling/prompts.py` | Jinja2 loader + deterministic prompt hash |
| `classifier/labeling/client.py` | `LabelerClient` wrapping anthropic SDK + disk cache + cost ledger |
| `classifier/labeling/sampler.py` | Stratified 10k sampler over candidate pool |
| `classifier/labeling/bulk.py` | Message-Batches dispatcher, 3-persona × N-pair loop |
| `classifier/labeling/aggregate.py` | 3/3, 2/3, 0/3 persona aggregation |
| `classifier/labeling/calibration.py` | Isotonic regression + tier-flip + loss reweights |
| `classifier/labeling/agreement.py` | Sonnet↔Opus κ study |
| `classifier/labeling/freeze.py` | v1_calibrated → v1_frozen + llm_train/llm_val split |
| `classifier/config/llm_sme_prompts/v1/compliance_auditor.j2` | Persona 1 template |
| `classifier/config/llm_sme_prompts/v1/security_researcher.j2` | Persona 2 template |
| `classifier/config/llm_sme_prompts/v1/governance_lawyer.j2` | Persona 3 template |
| `classifier/config/llm_sme_prompts/v1/shared_system.j2` | Shared system preamble |
| `classifier/tests/test_prompts.py` | Template render + hash stability |
| `classifier/tests/test_labeler_client.py` | Cache + ledger + retry |
| `classifier/tests/test_sampler.py` | Stratification + feasibility |
| `classifier/tests/test_aggregate.py` | 3/3 / 2/3 / 0/3 fixtures |
| `classifier/tests/test_calibration.py` | Isotonic monotonic property + confusion math |
| `classifier/tests/test_agreement.py` | κ computation on fixture |
| `classifier/tests/test_label_leakage.py` | The frozen-label contamination canary |
| `classifier/scripts/rebuild_candidate_pool_lambda.py` | §2.1 Lambda rebuild with bge-large |
| `classifier/scripts/run_bulk_labeling.py` | Entry point: bulk Sonnet labeling |
| `classifier/scripts/run_calibration.py` | Entry point: 150 human_cal × Opus |
| `classifier/scripts/run_agreement_study.py` | Entry point: 300 × Opus |
| `classifier/scripts/freeze_labels.py` | Entry point: freeze + split |
| `data/candidates/pool_v2.jsonl` | Lambda-rebuilt bge-large pool |
| `data/labels/llm_sme/v1_raw/` | Raw per-persona responses (append-only) |
| `data/labels/llm_sme/v1_raw/aggregated.jsonl` | 3-persona aggregation |
| `data/labels/llm_sme/v1_calibrated/aggregated.jsonl` | Isotonic + tier-flip applied |
| `data/labels/llm_sme/v1_frozen/{llm_train,llm_val,aggregated}.jsonl` | Frozen + split |
| `data/labels/hashes.json` | SHA256 manifest — CI canary |
| `data/labels/calibration_report.json` | Per-persona κ, confusion, reweights |
| `data/labels/sonnet_opus_agreement.json` | κ, confidence correlation |
| `data/labels/pair_weights.json` | Per-framework-pair loss reweights |
| `data/cost_ledger.jsonl` | Append-only cost log (Contract 7) |
| `requirements-classifier.txt` | Append `anthropic`, `jinja2`, `pydantic>=2` |

**Do not modify** any file under `mapping_engine/`, `data/splits/`, `data/processed/`, or anything produced by Plan 1 other than `requirements-classifier.txt` (append only) and `data/candidates/pool_v1.jsonl` — which is superseded, not mutated.

---

## Phase A — Prompt templates and schemas

### Task A1: Append deps and import smoke test

**Files:**
- Modify: `requirements-classifier.txt`

- [ ] **Step 1: Append deps**

```
# Plan 2 additions
anthropic==0.39.0
jinja2==3.1.4
pydantic==2.9.2
```

- [ ] **Step 2: Install and smoke test**

Run: `pip install -r requirements-classifier.txt && python -c "import anthropic, jinja2, pydantic; print(anthropic.__version__, jinja2.__version__, pydantic.VERSION)"`
Expected: version string printed, no ImportError.

- [ ] **Step 3: Commit**

```bash
git add requirements-classifier.txt
git commit -m "plan2: append anthropic+jinja2+pydantic deps"
```

### Task A2: Pydantic schemas — test first

**Files:**
- Create: `classifier/labeling/__init__.py` (empty)
- Create: `classifier/tests/test_schemas.py`
- Create: `classifier/labeling/schemas.py`

- [ ] **Step 1: Write the failing test**

```python
# classifier/tests/test_schemas.py
import pytest
from classifier.labeling.schemas import LabelResponse, AggregatedLabel, Persona, Tier

def test_label_response_roundtrip():
    r = LabelResponse(
        pair_key="aiuc_1:B005__owasp_agentic:ASI01",
        persona=Persona.compliance_auditor,
        tier=Tier.direct,
        confidence=0.92,
        rationale_code="FUNCTIONAL_OVERLAP",
        rationale_text="B005 prescribes continuous monitoring that addresses ASI01.",
        grounding_quotes=["continuous monitoring of agent traffic"],
        model="claude-sonnet-4-6",
        prompt_hash="sha256:deadbeef",
    )
    d = r.model_dump()
    r2 = LabelResponse.model_validate(d)
    assert r2 == r

def test_label_response_rejects_invalid_confidence():
    with pytest.raises(ValueError):
        LabelResponse(
            pair_key="x", persona=Persona.compliance_auditor, tier=Tier.direct,
            confidence=1.5, rationale_code="X", rationale_text="y",
            grounding_quotes=[], model="m", prompt_hash="h",
        )

def test_aggregated_label_3_of_3_gold():
    responses = [
        LabelResponse(pair_key="p", persona=p, tier=Tier.direct, confidence=c,
                      rationale_code="X", rationale_text="y", grounding_quotes=[],
                      model="m", prompt_hash="h")
        for p, c in zip(Persona, (0.9, 0.8, 0.7))
    ]
    agg = AggregatedLabel.from_responses("p", responses)
    assert agg.tier == Tier.direct
    assert agg.confidence == pytest.approx(0.8)  # mean
    assert agg.ambiguous is False
    assert agg.agreement_level == "3/3"
```

- [ ] **Step 2: Run — expect failure**

Run: `pytest classifier/tests/test_schemas.py -v`
Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Implement**

```python
# classifier/labeling/schemas.py
from __future__ import annotations
from enum import Enum
from statistics import mean
from collections import Counter
from pydantic import BaseModel, Field, field_validator


class Persona(str, Enum):
    compliance_auditor = "compliance_auditor"
    security_researcher = "security_researcher"
    governance_lawyer = "governance_lawyer"


class Tier(str, Enum):
    direct = "Direct"
    related = "Related"
    none_ = "None"


class LabelRequest(BaseModel):
    pair_key: str
    source_text: str
    target_text: str
    source_framework: str
    target_framework: str
    persona: Persona
    model: str  # "claude-sonnet-4-6" or "claude-opus-4-6"
    temperature: float = 0.3


class LabelResponse(BaseModel):
    pair_key: str
    persona: Persona
    tier: Tier
    confidence: float = Field(ge=0.0, le=1.0)
    rationale_code: str
    rationale_text: str
    grounding_quotes: list[str]
    model: str
    prompt_hash: str
    timestamp: str | None = None

    @field_validator("rationale_code")
    @classmethod
    def _non_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("rationale_code must be non-empty")
        return v


class AggregatedLabel(BaseModel):
    pair_key: str
    tier: Tier
    confidence: float
    ambiguous: bool
    agreement_level: str  # "3/3" | "2/3" | "0/3"
    per_persona: list[LabelResponse]
    rationale_code: str  # majority or "AMBIGUOUS"

    @classmethod
    def from_responses(cls, pair_key: str, responses: list[LabelResponse]) -> "AggregatedLabel":
        assert len(responses) == 3, f"expected 3 persona responses, got {len(responses)}"
        tiers = [r.tier for r in responses]
        ctr = Counter(tiers)
        top_tier, top_n = ctr.most_common(1)[0]
        conf_mean = float(mean(r.confidence for r in responses))
        if top_n == 3:
            tier, conf, ambig, level = top_tier, conf_mean, False, "3/3"
        elif top_n == 2:
            tier, conf, ambig, level = top_tier, conf_mean * 0.75, False, "2/3"
        else:
            tier, conf, ambig, level = Tier.none_, conf_mean * 0.5, True, "0/3"
        rationales = [r.rationale_code for r in responses if r.tier == tier]
        rationale_code = Counter(rationales).most_common(1)[0][0] if rationales else "AMBIGUOUS"
        return cls(
            pair_key=pair_key, tier=tier, confidence=conf, ambiguous=ambig,
            agreement_level=level, per_persona=responses, rationale_code=rationale_code,
        )
```

- [ ] **Step 4: Run — expect pass**

Run: `pytest classifier/tests/test_schemas.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add classifier/labeling/__init__.py classifier/labeling/schemas.py classifier/tests/test_schemas.py
git commit -m "plan2: pydantic schemas for label request/response/aggregation"
```

### Task A3: Jinja2 prompt templates

**Files:**
- Create: `classifier/config/llm_sme_prompts/__init__.py` (empty)
- Create: `classifier/config/llm_sme_prompts/v1/shared_system.j2`
- Create: `classifier/config/llm_sme_prompts/v1/compliance_auditor.j2`
- Create: `classifier/config/llm_sme_prompts/v1/security_researcher.j2`
- Create: `classifier/config/llm_sme_prompts/v1/governance_lawyer.j2`

- [ ] **Step 1: Create shared system preamble**

```jinja2
{# classifier/config/llm_sme_prompts/v1/shared_system.j2 #}
You are one of three independent expert reviewers assessing whether a CONTROL from an AI security framework addresses a RISK (or another control) from a different framework.

Output strictly valid JSON matching this schema:
{
  "tier": "Direct" | "Related" | "None",
  "confidence": float in [0.0, 1.0],
  "rationale_code": one of ["FUNCTIONAL_OVERLAP","PROCEDURAL_OVERLAP","SCOPE_LIMITED","GOVERNANCE_ONLY","DETECTIVE_ONLY","PREVENTIVE_ONLY","TANGENTIAL","NO_RELATION"],
  "rationale_text": string, 1-3 sentences grounded in the framework text,
  "grounding_quotes": array of short verbatim quotes from the provided framework text supporting your decision
}

Definitions:
- "Direct": this control, as written, substantively addresses the risk/target.
- "Related": overlapping but limited in scope, coverage, or mechanism.
- "None": the two are unrelated or address different concerns entirely.

Do not speculate beyond the provided text. If uncertain, choose a lower tier with lower confidence rather than guessing Direct.
```

- [ ] **Step 2: Create compliance_auditor.j2**

```jinja2
{# classifier/config/llm_sme_prompts/v1/compliance_auditor.j2 #}
{% include "shared_system.j2" %}

ROLE: Compliance auditor. Your question: "Does this control, as written, provide assurance against this risk?"

SOURCE ({{ source_framework }}):
{{ source_text }}

TARGET ({{ target_framework }}):
{{ target_text }}

Assess from a compliance-evidence standpoint only. An auditor asks: "Could this control be cited in a control statement to claim coverage of the target?"
```

- [ ] **Step 3: Create security_researcher.j2**

```jinja2
{# classifier/config/llm_sme_prompts/v1/security_researcher.j2 #}
{% include "shared_system.j2" %}

ROLE: Security researcher. Your question: "Do these describe the same attack surface or defense mechanism?"

SOURCE ({{ source_framework }}):
{{ source_text }}

TARGET ({{ target_framework }}):
{{ target_text }}

Assess from an adversarial-modeling standpoint. A researcher asks: "Does the same threat model generate both of these, or do they address the same defensive primitive?"
```

- [ ] **Step 4: Create governance_lawyer.j2**

```jinja2
{# classifier/config/llm_sme_prompts/v1/governance_lawyer.j2 #}
{% include "shared_system.j2" %}

ROLE: Governance lawyer. Your question: "Would a regulator consider these to address the same obligation?"

SOURCE ({{ source_framework }}):
{{ source_text }}

TARGET ({{ target_framework }}):
{{ target_text }}

Assess from a regulatory-obligation standpoint. A lawyer asks: "Under a reasonable-interpretation standard, would a regulator accept satisfaction of one as evidence of the other?"
```

- [ ] **Step 5: Commit**

```bash
git add classifier/config/llm_sme_prompts/
git commit -m "plan2: v1 persona jinja2 templates (3 personas + shared system)"
```

### Task A4: Prompt loader + deterministic hash

**Files:**
- Create: `classifier/labeling/prompts.py`
- Create: `classifier/tests/test_prompts.py`

- [ ] **Step 1: Failing test**

```python
# classifier/tests/test_prompts.py
import hashlib
from classifier.labeling.prompts import render_prompt, prompt_hash
from classifier.labeling.schemas import Persona

FIXTURE = {
    "source_text": "The system shall log all inference requests for 90 days.",
    "target_text": "LLM07: Improper handling of inference traffic may enable abuse.",
    "source_framework": "aiuc_1",
    "target_framework": "owasp_llm",
}

def test_render_includes_role_line():
    p = render_prompt(Persona.compliance_auditor, **FIXTURE)
    assert "Compliance auditor" in p
    assert "inference requests" in p
    assert "LLM07" in p

def test_hash_stable_across_calls():
    a = prompt_hash(render_prompt(Persona.compliance_auditor, **FIXTURE))
    b = prompt_hash(render_prompt(Persona.compliance_auditor, **FIXTURE))
    assert a == b
    assert a.startswith("sha256:")
    assert len(a) == len("sha256:") + 64

def test_hash_changes_on_persona_change():
    a = prompt_hash(render_prompt(Persona.compliance_auditor, **FIXTURE))
    b = prompt_hash(render_prompt(Persona.security_researcher, **FIXTURE))
    assert a != b
```

- [ ] **Step 2: Run — expect failure**

Run: `pytest classifier/tests/test_prompts.py -v`
Expected: ModuleNotFoundError.

- [ ] **Step 3: Implement**

```python
# classifier/labeling/prompts.py
from __future__ import annotations
import hashlib
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
from classifier.labeling.schemas import Persona

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "config" / "llm_sme_prompts" / "v1"
TEMPLATE_VERSION = "v1"

_env = Environment(
    loader=FileSystemLoader(TEMPLATE_DIR),
    autoescape=select_autoescape(disabled_extensions=("j2",)),
    keep_trailing_newline=True,
    trim_blocks=False,
    lstrip_blocks=False,
)


def render_prompt(persona: Persona, *, source_text: str, target_text: str,
                  source_framework: str, target_framework: str) -> str:
    tmpl = _env.get_template(f"{persona.value}.j2")
    return tmpl.render(
        source_text=source_text, target_text=target_text,
        source_framework=source_framework, target_framework=target_framework,
    )


def prompt_hash(rendered: str) -> str:
    h = hashlib.sha256(rendered.encode("utf-8")).hexdigest()
    return f"sha256:{h}"
```

- [ ] **Step 4: Run — expect pass**

Run: `pytest classifier/tests/test_prompts.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add classifier/labeling/prompts.py classifier/tests/test_prompts.py
git commit -m "plan2: prompt loader + deterministic sha256 hash"
```

---

## Phase B — LabelerClient: Anthropic + cache + cost ledger

### Task B1: LabelerClient skeleton with cache

**Files:**
- Create: `classifier/labeling/client.py`
- Create: `classifier/tests/test_labeler_client.py`

- [ ] **Step 1: Failing test**

```python
# classifier/tests/test_labeler_client.py
import json
from pathlib import Path
from unittest.mock import MagicMock
from classifier.labeling.client import LabelerClient
from classifier.labeling.schemas import LabelRequest, Persona

FIXTURE_REQ = dict(
    pair_key="aiuc_1:B005__owasp_agentic:ASI01",
    source_text="monitor all agent traffic",
    target_text="unauthorized agent actions",
    source_framework="aiuc_1",
    target_framework="owasp_agentic",
    persona=Persona.compliance_auditor,
    model="claude-sonnet-4-6",
)

_FAKE_JSON = '{"tier":"Direct","confidence":0.85,"rationale_code":"FUNCTIONAL_OVERLAP","rationale_text":"ok","grounding_quotes":["q"]}'


def _mock_anthropic():
    client = MagicMock()
    client.messages.create.return_value.content = [MagicMock(text=_FAKE_JSON)]
    client.messages.create.return_value.usage.input_tokens = 100
    client.messages.create.return_value.usage.output_tokens = 50
    return client


def test_cache_hit_on_second_call(tmp_path):
    anth = _mock_anthropic()
    lc = LabelerClient(anthropic_client=anth, cache_dir=tmp_path/"cache",
                       ledger_path=tmp_path/"cost.jsonl")
    r1 = lc.label(LabelRequest(**FIXTURE_REQ))
    r2 = lc.label(LabelRequest(**FIXTURE_REQ))
    assert r1.tier == r2.tier
    assert anth.messages.create.call_count == 1  # second call hit cache


def test_cost_ledger_appended(tmp_path):
    anth = _mock_anthropic()
    ledger = tmp_path / "cost.jsonl"
    lc = LabelerClient(anthropic_client=anth, cache_dir=tmp_path/"cache", ledger_path=ledger)
    lc.label(LabelRequest(**FIXTURE_REQ))
    lines = ledger.read_text().splitlines()
    assert len(lines) == 1
    rec = json.loads(lines[0])
    assert rec["input_tokens"] == 100 and rec["output_tokens"] == 50
    assert rec["plan"] == "plan2"


def test_invalid_json_raises(tmp_path):
    anth = _mock_anthropic()
    anth.messages.create.return_value.content = [MagicMock(text="not json")]
    lc = LabelerClient(anthropic_client=anth, cache_dir=tmp_path/"cache",
                       ledger_path=tmp_path/"cost.jsonl")
    import pytest
    with pytest.raises(ValueError, match="invalid json"):
        lc.label(LabelRequest(**FIXTURE_REQ))
```

- [ ] **Step 2: Run — expect failure**

Run: `pytest classifier/tests/test_labeler_client.py -v`
Expected: ModuleNotFoundError.

- [ ] **Step 3: Implement**

```python
# classifier/labeling/client.py
from __future__ import annotations
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from tenacity import retry, stop_after_attempt, wait_exponential
from classifier.labeling.schemas import LabelRequest, LabelResponse, Tier, Persona
from classifier.labeling.prompts import render_prompt, prompt_hash, TEMPLATE_VERSION


# Input/output $/MTok (claude-sonnet-4-6 vs claude-opus-4-6 as of 2026-04)
PRICE_PER_MTOK = {
    "claude-sonnet-4-6":  {"in": 3.0,  "out": 15.0},
    "claude-opus-4-6":    {"in": 15.0, "out": 75.0},
}


def _cache_key(req: LabelRequest, prompt_sha: str) -> str:
    h = hashlib.sha256(
        f"{req.model}|{TEMPLATE_VERSION}|{prompt_sha}|{req.temperature}".encode()
    ).hexdigest()
    return h


class LabelerClient:
    def __init__(self, anthropic_client: Any, cache_dir: Path, ledger_path: Path,
                 plan: str = "plan2"):
        self.anth = anthropic_client
        self.cache_dir = Path(cache_dir); self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ledger_path = Path(ledger_path); self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        self.plan = plan

    @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, max=30))
    def _call(self, req: LabelRequest, rendered: str) -> tuple[str, int, int]:
        resp = self.anth.messages.create(
            model=req.model,
            max_tokens=1024,
            temperature=req.temperature,
            messages=[{"role": "user", "content": rendered}],
        )
        text = resp.content[0].text
        return text, resp.usage.input_tokens, resp.usage.output_tokens

    def _ledger_append(self, req: LabelRequest, in_tok: int, out_tok: int) -> None:
        price = PRICE_PER_MTOK.get(req.model, {"in": 0.0, "out": 0.0})
        cost_usd = (in_tok * price["in"] + out_tok * price["out"]) / 1_000_000
        rec = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "plan": self.plan,
            "model": req.model,
            "persona": req.persona.value,
            "pair_key": req.pair_key,
            "input_tokens": in_tok,
            "output_tokens": out_tok,
            "cost_usd": round(cost_usd, 6),
        }
        with open(self.ledger_path, "a") as f:
            f.write(json.dumps(rec) + "\n")

    def label(self, req: LabelRequest) -> LabelResponse:
        rendered = render_prompt(
            req.persona,
            source_text=req.source_text, target_text=req.target_text,
            source_framework=req.source_framework, target_framework=req.target_framework,
        )
        psha = prompt_hash(rendered)
        key = _cache_key(req, psha)
        cache_file = self.cache_dir / f"{key}.json"
        if cache_file.exists():
            d = json.loads(cache_file.read_text())
            return LabelResponse.model_validate(d)
        text, in_tok, out_tok = self._call(req, rendered)
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(f"invalid json from {req.model}: {e}; text={text[:200]}")
        resp = LabelResponse(
            pair_key=req.pair_key,
            persona=req.persona,
            tier=Tier(parsed["tier"]),
            confidence=float(parsed["confidence"]),
            rationale_code=parsed["rationale_code"],
            rationale_text=parsed["rationale_text"],
            grounding_quotes=list(parsed.get("grounding_quotes", [])),
            model=req.model,
            prompt_hash=psha,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        cache_file.write_text(json.dumps(resp.model_dump(), sort_keys=True, ensure_ascii=False))
        self._ledger_append(req, in_tok, out_tok)
        return resp
```

- [ ] **Step 4: Run — expect pass**

Run: `pytest classifier/tests/test_labeler_client.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add classifier/labeling/client.py classifier/tests/test_labeler_client.py
git commit -m "plan2: LabelerClient with disk cache + cost ledger + tenacity retry"
```

---

## Phase C — Candidate pool rebuild + stratified sampling

### Task C1: Rebuild candidate pool on Lambda with bge-large

**Files:**
- Create: `classifier/scripts/rebuild_candidate_pool_lambda.py`

This script runs on Lambda (GPU). It reads `data/splits/sme_pool_full.jsonl` + `mapping_engine/output/labeling_sheets/`, re-encodes all 983 nodes with `BAAI/bge-large-en-v1.5`, and re-runs top-20 retrieval across the 12 framework pairs. Output: `data/candidates/pool_v2.jsonl` + `data/candidates/pool_v2_meta.json`. Must be executed on Lambda per the Plan 1 handoff note.

- [ ] **Step 1: Write the script**

```python
# classifier/scripts/rebuild_candidate_pool_lambda.py
"""Rebuild the 12-pair candidate pool on Lambda using bge-large-en-v1.5.

Reads:
    data/splits/sme_pool_full.jsonl
    data/processed/nodes.json
    mapping_engine/config/pairs/*.yaml  (for the 12 pair definitions)

Writes:
    data/candidates/pool_v2.jsonl  (one line per (pair, source, target_topk))
    data/candidates/pool_v2_meta.json  (model, seed, k, timestamp, sha256)

Usage (on Lambda):
    python -m classifier.scripts.rebuild_candidate_pool_lambda --k 20
"""
from __future__ import annotations
import argparse, hashlib, json
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import torch
from sentence_transformers import SentenceTransformer

from classifier.config import REPO_ROOT, DATA_DIR, CANDIDATES_DIR
from classifier.data.splits import verify_hashes
from classifier.data.candidates import FRAMEWORK_PAIRS, load_nodes_by_framework


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, default=20)
    ap.add_argument("--model", default="BAAI/bge-large-en-v1.5")
    args = ap.parse_args()

    verify_hashes()  # Contract 1: never proceed on stale splits

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[rebuild_pool] device={device} model={args.model} k={args.k}")
    model = SentenceTransformer(args.model, device=device)

    nodes_by_fw = load_nodes_by_framework()
    embeds: dict[str, dict[str, np.ndarray]] = {}
    for fw, nodes in nodes_by_fw.items():
        texts = [n.get("description") or n.get("name") or n["node_id"] for n in nodes]
        E = model.encode(texts, batch_size=64, normalize_embeddings=True,
                         convert_to_numpy=True, show_progress_bar=True)
        embeds[fw] = {n["node_id"]: E[i] for i, n in enumerate(nodes)}
        print(f"[rebuild_pool] {fw}: {len(nodes)} nodes encoded")

    CANDIDATES_DIR.mkdir(parents=True, exist_ok=True)
    out_path = CANDIDATES_DIR / "pool_v2.jsonl"
    n_rows = 0
    with open(out_path, "w") as f:
        for src_fw, tgt_fw in FRAMEWORK_PAIRS:
            src_nodes = nodes_by_fw[src_fw]
            tgt_nodes = nodes_by_fw[tgt_fw]
            tgt_ids = [n["node_id"] for n in tgt_nodes]
            T = np.stack([embeds[tgt_fw][nid] for nid in tgt_ids])
            for sn in src_nodes:
                s = embeds[src_fw][sn["node_id"]]
                sims = (T @ s).astype(float)
                order = np.argsort(-sims)[:args.k]
                row = {
                    "pair_name": f"{src_fw}__{tgt_fw}",
                    "source_framework": src_fw,
                    "source_node_id": sn["node_id"],
                    "topk": [
                        {"target_node_id": tgt_ids[int(j)], "score": round(float(sims[int(j)]), 6)}
                        for j in order
                    ],
                }
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
                n_rows += 1
    sha = hashlib.sha256(out_path.read_bytes()).hexdigest()
    meta = {
        "model": args.model,
        "k": args.k,
        "rows": n_rows,
        "sha256": sha,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    (CANDIDATES_DIR / "pool_v2_meta.json").write_text(json.dumps(meta, indent=2))
    print(f"[rebuild_pool] wrote {n_rows} rows to {out_path}")
    print(f"[rebuild_pool] sha256={sha}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Dry-run on Jetson using bge-small as a sanity check**

Run: `python -m classifier.scripts.rebuild_candidate_pool_lambda --k 20 --model BAAI/bge-small-en-v1.5`
Expected: completes without error, writes `pool_v2.jsonl` and `pool_v2_meta.json`, row count matches sum of source node counts across 12 pairs.

- [ ] **Step 3: Commit (script only, not the dry-run output)**

```bash
git checkout -- data/candidates/pool_v2.jsonl data/candidates/pool_v2_meta.json 2>/dev/null || true
git add classifier/scripts/rebuild_candidate_pool_lambda.py
git commit -m "plan2: Lambda rebuild candidate pool with bge-large-en-v1.5"
```

- [ ] **Step 4: Execute on Lambda** (manual, see `classifier/lambda/README.md`)

Launch an A100 instance, `git pull`, `pip install -r requirements-classifier.txt`, run:
```bash
python -m classifier.scripts.rebuild_candidate_pool_lambda --k 20 --model BAAI/bge-large-en-v1.5
```
Commit the resulting `data/candidates/pool_v2.jsonl` + `pool_v2_meta.json` from the Lambda shell (the bootstrap script in `classifier/lambda/` handles git credentials).

### Task C2: Stratified 10k sampler over pool_v2

**Files:**
- Create: `classifier/labeling/sampler.py`
- Create: `classifier/tests/test_sampler.py`

- [ ] **Step 1: Failing test**

```python
# classifier/tests/test_sampler.py
import json, pytest
from pathlib import Path
from classifier.labeling.sampler import stratified_sample, feasibility_check

@pytest.fixture
def fake_pool(tmp_path):
    rows = []
    for pair in ("a__b", "c__d", "e__f"):
        for s in range(50):
            topk = [{"target_node_id": f"t{i}", "score": 0.9 - 0.02*i} for i in range(20)]
            rows.append({"pair_name": pair, "source_framework": pair.split("__")[0],
                         "source_node_id": f"s{pair}{s}", "topk": topk})
    p = tmp_path / "pool_v2.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in rows))
    return p

def test_feasibility_passes(fake_pool):
    assert feasibility_check(fake_pool, n_target=30) is True

def test_feasibility_raises_when_insufficient(fake_pool):
    with pytest.raises(ValueError, match="not enough pairs"):
        feasibility_check(fake_pool, n_target=10_000)

def test_sample_is_stratified_by_pair_and_bucket(fake_pool):
    sample = stratified_sample(fake_pool, n=30, seed=42)
    # 30 pairs / 3 framework pairs = 10 per pair
    from collections import Counter
    ctr = Counter((r["pair_name"], r.get("score_bucket","")) for r in sample)
    by_pair = Counter(r["pair_name"] for r in sample)
    assert set(by_pair.values()) == {10}

def test_sample_deterministic(fake_pool):
    a = [r["source_node_id"]+r["target_node_id"] for r in stratified_sample(fake_pool, n=30, seed=42)]
    b = [r["source_node_id"]+r["target_node_id"] for r in stratified_sample(fake_pool, n=30, seed=42)]
    assert a == b
```

- [ ] **Step 2: Run — expect failure**

Expected: ModuleNotFoundError.

- [ ] **Step 3: Implement**

```python
# classifier/labeling/sampler.py
from __future__ import annotations
import json
import random
from collections import defaultdict
from pathlib import Path


SCORE_BUCKETS = [(0.0, 0.3, "low"), (0.3, 0.55, "mid"), (0.55, 0.75, "high"), (0.75, 1.01, "top")]


def _bucket(score: float) -> str:
    for lo, hi, name in SCORE_BUCKETS:
        if lo <= score < hi:
            return name
    return "top"


def _iter_flat(pool_path: Path):
    with open(pool_path) as f:
        for line in f:
            row = json.loads(line)
            for tk in row["topk"]:
                yield {
                    "pair_name": row["pair_name"],
                    "source_framework": row["source_framework"],
                    "source_node_id": row["source_node_id"],
                    "target_node_id": tk["target_node_id"],
                    "score": float(tk["score"]),
                    "score_bucket": _bucket(float(tk["score"])),
                }


def feasibility_check(pool_path: Path, n_target: int) -> bool:
    total = sum(1 for _ in _iter_flat(pool_path))
    if total < n_target:
        raise ValueError(
            f"not enough pairs in {pool_path}: have {total}, need {n_target}. "
            f"Rebuild pool with larger --k or drop n_target."
        )
    return True


def stratified_sample(pool_path: Path, n: int, seed: int = 42) -> list[dict]:
    feasibility_check(pool_path, n)
    rng = random.Random(seed)
    strata: dict[tuple, list[dict]] = defaultdict(list)
    for r in _iter_flat(pool_path):
        strata[(r["pair_name"], r["score_bucket"])].append(r)
    pair_names = sorted({k[0] for k in strata})
    per_pair = n // len(pair_names)
    out: list[dict] = []
    for pair in pair_names:
        buckets = [strata[(pair, b)] for _, _, b in SCORE_BUCKETS if strata.get((pair, b))]
        if not buckets:
            continue
        per_bucket = max(1, per_pair // len(buckets))
        picked: list[dict] = []
        for b in buckets:
            rng.shuffle(b)
            picked.extend(b[:per_bucket])
        rng.shuffle(picked)
        out.extend(picked[:per_pair])
    out.sort(key=lambda r: (r["pair_name"], r["source_node_id"], r["target_node_id"]))
    return out[:n]
```

- [ ] **Step 4: Run — expect pass**

Run: `pytest classifier/tests/test_sampler.py -v`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add classifier/labeling/sampler.py classifier/tests/test_sampler.py
git commit -m "plan2: stratified sampler with pair×bucket strata + feasibility test"
```

---

## Phase D — Bulk labeling via Message Batches

### Task D1: Bulk labeling loop (Sonnet × 3 personas × 10k pairs)

**Files:**
- Create: `classifier/labeling/bulk.py`
- Create: `classifier/scripts/run_bulk_labeling.py`

- [ ] **Step 1: Implement bulk wrapper** (no unit test for the full loop — mocked in client tests)

```python
# classifier/labeling/bulk.py
from __future__ import annotations
import json
from pathlib import Path
from classifier.labeling.client import LabelerClient
from classifier.labeling.schemas import LabelRequest, LabelResponse, Persona
from classifier.data.sme_pool import load_sme_pool
from classifier.data.candidates import load_nodes_by_framework


def _node_text(n: dict) -> str:
    return (n.get("description") or n.get("name") or n.get("node_id") or "").strip()


def run_bulk(sample: list[dict], client: LabelerClient, out_dir: Path,
             model: str = "claude-sonnet-4-6") -> int:
    """Label every (pair, persona) combination. Writes one JSONL per pair_name
    under out_dir; each row is a LabelResponse."""
    nodes_by_fw = load_nodes_by_framework()
    by_id: dict[str, dict] = {}
    for fw, ns in nodes_by_fw.items():
        for n in ns:
            by_id[n["node_id"]] = n
    out_dir.mkdir(parents=True, exist_ok=True)
    n_written = 0
    for row in sample:
        src = by_id.get(row["source_node_id"])
        tgt = by_id.get(row["target_node_id"])
        if src is None or tgt is None:
            continue
        for persona in Persona:
            req = LabelRequest(
                pair_key=f"{row['pair_name']}::{row['source_node_id']}__{row['target_node_id']}",
                source_text=_node_text(src), target_text=_node_text(tgt),
                source_framework=row["source_framework"],
                target_framework=row["pair_name"].split("__")[1],
                persona=persona, model=model,
            )
            try:
                resp = client.label(req)
            except ValueError as e:
                print(f"[bulk] skip {req.pair_key}/{persona.value}: {e}")
                continue
            out_path = out_dir / f"{row['pair_name']}.jsonl"
            with open(out_path, "a") as f:
                f.write(json.dumps(resp.model_dump(), ensure_ascii=False) + "\n")
            n_written += 1
    return n_written
```

- [ ] **Step 2: Entry-point script**

```python
# classifier/scripts/run_bulk_labeling.py
"""Entry point for bulk Sonnet labeling."""
from __future__ import annotations
import argparse
from pathlib import Path
import anthropic
from classifier.config import REPO_ROOT, DATA_DIR, CANDIDATES_DIR, require_secrets
from classifier.data.splits import verify_hashes
from classifier.labeling.sampler import stratified_sample
from classifier.labeling.client import LabelerClient
from classifier.labeling.bulk import run_bulk


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=10_000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--model", default="claude-sonnet-4-6")
    args = ap.parse_args()

    verify_hashes()
    secrets = require_secrets(["ANTHROPIC_API_KEY"])
    anth = anthropic.Anthropic(api_key=secrets["ANTHROPIC_API_KEY"])

    pool_path = CANDIDATES_DIR / "pool_v2.jsonl"
    sample = stratified_sample(pool_path, n=args.n, seed=args.seed)
    print(f"[bulk] sampled {len(sample)} pairs from {pool_path}")

    client = LabelerClient(
        anthropic_client=anth,
        cache_dir=DATA_DIR / "labels" / "_cache",
        ledger_path=DATA_DIR / "cost_ledger.jsonl",
    )
    out_dir = DATA_DIR / "labels" / "llm_sme" / "v1_raw"
    n = run_bulk(sample, client, out_dir, model=args.model)
    print(f"[bulk] wrote {n} persona responses to {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 3: Commit (do not run yet — the API call is Phase E execution)**

```bash
git add classifier/labeling/bulk.py classifier/scripts/run_bulk_labeling.py
git commit -m "plan2: bulk labeling loop + run_bulk_labeling entry point"
```

### Task D2: 100-pair smoke test on Sonnet

- [ ] **Step 1: Run small batch with live API**

Run: `python -m classifier.scripts.run_bulk_labeling --n 100 --seed 42`
Expected: ~300 responses (100 pairs × 3 personas) written to `data/labels/llm_sme/v1_raw/*.jsonl`; `data/cost_ledger.jsonl` gains ~300 rows; total cost <$3; no ValueError on invalid JSON.

- [ ] **Step 2: Sanity check the cost ledger**

Run:
```bash
python -c "
import json, pathlib
rows = [json.loads(l) for l in open('data/cost_ledger.jsonl')]
print(f'rows={len(rows)} total_usd={sum(r[\"cost_usd\"] for r in rows):.2f}')
print({r['persona'] for r in rows})
"
```
Expected: `rows=300 total_usd≈2` and the persona set is `{compliance_auditor, security_researcher, governance_lawyer}`.

- [ ] **Step 3: If smoke test passes, commit the cost ledger and any cached raw labels from the smoke**

```bash
git add data/cost_ledger.jsonl data/labels/llm_sme/v1_raw/
git commit -m "plan2: 100-pair Sonnet smoke batch (cache + ledger)"
```

### Task D3: Full 10k bulk run

- [ ] **Step 1: Dispatch**

Run (expect 3–8 hours depending on rate limits; idempotent, resumable): `python -m classifier.scripts.run_bulk_labeling --n 10000 --seed 42`
Expected: ~30k responses total; total cost $250–400 logged in `data/cost_ledger.jsonl`; disk cache grows to ~30k files in `data/labels/_cache/`.

- [ ] **Step 2: Budget guardrail**

If running total in `data/cost_ledger.jsonl` exceeds $450, STOP and surface to user:
```bash
python -c "
import json
tot = sum(json.loads(l)['cost_usd'] for l in open('data/cost_ledger.jsonl'))
print(f'running_total=${tot:.2f}')
assert tot < 450, 'budget cap exceeded'
"
```

- [ ] **Step 3: Commit raw labels**

```bash
git add data/labels/llm_sme/v1_raw/ data/cost_ledger.jsonl
git commit -m "plan2: v1_raw Sonnet 3-persona labels (~10k pairs, ~30k responses)"
```

---

## Phase E — Aggregation + Calibration

### Task E1: Per-pair 3-persona aggregation

**Files:**
- Create: `classifier/labeling/aggregate.py`
- Create: `classifier/tests/test_aggregate.py`

- [ ] **Step 1: Failing test**

```python
# classifier/tests/test_aggregate.py
from pathlib import Path
import json
from classifier.labeling.aggregate import aggregate_dir
from classifier.labeling.schemas import LabelResponse, Persona, Tier

def _make_resp(pair, persona, tier, conf):
    return LabelResponse(
        pair_key=pair, persona=persona, tier=tier, confidence=conf,
        rationale_code="FUNCTIONAL_OVERLAP", rationale_text="t",
        grounding_quotes=["q"], model="claude-sonnet-4-6", prompt_hash="sha256:x",
    )

def test_3_of_3(tmp_path):
    p = tmp_path / "pair_a.jsonl"
    rows = [_make_resp("pk", Persona.compliance_auditor, Tier.direct, 0.9),
            _make_resp("pk", Persona.security_researcher, Tier.direct, 0.8),
            _make_resp("pk", Persona.governance_lawyer, Tier.direct, 0.7)]
    p.write_text("\n".join(json.dumps(r.model_dump()) for r in rows))
    out = tmp_path / "agg.jsonl"
    n = aggregate_dir(tmp_path, out)
    assert n == 1
    d = json.loads(out.read_text().splitlines()[0])
    assert d["tier"] == "Direct"
    assert d["agreement_level"] == "3/3"
    assert abs(d["confidence"] - 0.8) < 1e-6

def test_mixed_2_of_3(tmp_path):
    p = tmp_path / "pair_b.jsonl"
    rows = [_make_resp("pk2", Persona.compliance_auditor, Tier.direct, 0.9),
            _make_resp("pk2", Persona.security_researcher, Tier.related, 0.6),
            _make_resp("pk2", Persona.governance_lawyer, Tier.direct, 0.7)]
    p.write_text("\n".join(json.dumps(r.model_dump()) for r in rows))
    out = tmp_path / "agg.jsonl"
    aggregate_dir(tmp_path, out)
    d = json.loads(out.read_text().splitlines()[0])
    assert d["tier"] == "Direct"
    assert d["agreement_level"] == "2/3"
    assert d["ambiguous"] is False
```

- [ ] **Step 2: Implement**

```python
# classifier/labeling/aggregate.py
from __future__ import annotations
import json
from collections import defaultdict
from pathlib import Path
from classifier.labeling.schemas import LabelResponse, AggregatedLabel


def aggregate_dir(in_dir: Path, out_path: Path) -> int:
    by_key: dict[str, list[LabelResponse]] = defaultdict(list)
    for f in sorted(in_dir.glob("*.jsonl")):
        for line in f.read_text().splitlines():
            if not line.strip(): continue
            r = LabelResponse.model_validate_json(line)
            by_key[r.pair_key].append(r)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with open(out_path, "w") as f:
        for pk in sorted(by_key):
            resps = by_key[pk]
            if len(resps) != 3:
                continue
            agg = AggregatedLabel.from_responses(pk, resps)
            f.write(agg.model_dump_json() + "\n")
            n += 1
    return n
```

- [ ] **Step 3: Run tests + execute on v1_raw**

Run: `pytest classifier/tests/test_aggregate.py -v && python -c "from classifier.labeling.aggregate import aggregate_dir; from pathlib import Path; n = aggregate_dir(Path('data/labels/llm_sme/v1_raw'), Path('data/labels/llm_sme/v1_raw/aggregated.jsonl')); print(f'aggregated={n}')"`
Expected: tests pass, `aggregated ≈ 10000`.

- [ ] **Step 4: Commit**

```bash
git add classifier/labeling/aggregate.py classifier/tests/test_aggregate.py data/labels/llm_sme/v1_raw/aggregated.jsonl
git commit -m "plan2: 3-persona aggregation + v1_raw aggregated.jsonl"
```

### Task E2: Calibration pass on human_cal × Opus 4.6

**Files:**
- Create: `classifier/scripts/run_calibration.py`

- [ ] **Step 1: Implement**

```python
# classifier/scripts/run_calibration.py
"""Label all 150 human_cal pairs with Opus 4.6 × 3 personas.

Writes per-persona raw responses to data/labels/llm_sme/calibration_raw/*.jsonl,
then computes per-persona Cohen's κ against human_cal gold, confusion matrices,
and per-framework-pair calibration stats. Results go to
data/labels/calibration_report.json.
"""
from __future__ import annotations
import json
from pathlib import Path
import anthropic
import pandas as pd
from sklearn.metrics import cohen_kappa_score, confusion_matrix
from sklearn.isotonic import IsotonicRegression
from classifier.config import REPO_ROOT, DATA_DIR, SPLITS_DIR, require_secrets
from classifier.data.splits import verify_hashes
from classifier.labeling.client import LabelerClient
from classifier.labeling.schemas import LabelRequest, Persona, Tier
from classifier.data.candidates import load_nodes_by_framework


TIERS = ["Direct", "Related", "None"]


def main() -> int:
    verify_hashes()
    secrets = require_secrets(["ANTHROPIC_API_KEY"])
    anth = anthropic.Anthropic(api_key=secrets["ANTHROPIC_API_KEY"])
    client = LabelerClient(anth, cache_dir=DATA_DIR / "labels" / "_cache",
                           ledger_path=DATA_DIR / "cost_ledger.jsonl")

    cal = pd.read_json(SPLITS_DIR / "human_cal.jsonl", lines=True)
    nodes_by_fw = load_nodes_by_framework()
    by_id = {n["node_id"]: n for ns in nodes_by_fw.values() for n in ns}

    per_persona = {p.value: [] for p in Persona}
    gold, preds_by_p = [], {p.value: [] for p in Persona}

    for _, row in cal.iterrows():
        src = by_id.get(row["source_node_id"])
        tgt = by_id.get(row["target_node_id"])
        if src is None or tgt is None:
            continue
        gold_tier = row["expert_tier"]
        gold.append(gold_tier)
        for persona in Persona:
            req = LabelRequest(
                pair_key=row["pair_key"],
                source_text=(src.get("description") or src.get("name") or "").strip(),
                target_text=(tgt.get("description") or tgt.get("name") or "").strip(),
                source_framework=src.get("framework") or "?",
                target_framework=tgt.get("framework") or "?",
                persona=persona, model="claude-opus-4-6",
            )
            resp = client.label(req)
            per_persona[persona.value].append({
                "pair_key": row["pair_key"],
                "gold": gold_tier,
                "pred": resp.tier.value,
                "confidence": resp.confidence,
            })
            preds_by_p[persona.value].append(resp.tier.value)

    report = {"per_persona": {}, "per_pair": {}, "tier_flip": {}}
    for p, rows in per_persona.items():
        y_true = [r["gold"] for r in rows]
        y_pred = [r["pred"] for r in rows]
        kappa = float(cohen_kappa_score(y_true, y_pred, labels=TIERS))
        cm = confusion_matrix(y_true, y_pred, labels=TIERS).tolist()
        report["per_persona"][p] = {"kappa": round(kappa, 4), "confusion": cm, "n": len(rows)}

    # Fit per-persona isotonic on confidence → binary correctness
    iso = {}
    for p, rows in per_persona.items():
        x = [r["confidence"] for r in rows]
        y = [1 if r["pred"] == r["gold"] else 0 for r in rows]
        if len(x) >= 10:
            ir = IsotonicRegression(out_of_bounds="clip").fit(x, y)
            iso[p] = {"x": x, "y_calibrated": [float(v) for v in ir.predict(x)]}
    report["isotonic_calibration_preview"] = iso

    # Tier-flip table: (persona, from_tier, to_tier) rate above 0.1
    flip = {}
    for p, rows in per_persona.items():
        cnt = {t: {t2: 0 for t2 in TIERS} for t in TIERS}
        for r in rows:
            cnt[r["pred"]][r["gold"]] += 1
        tbl = {}
        for pred_t in TIERS:
            row_total = sum(cnt[pred_t].values()) or 1
            for gold_t in TIERS:
                rate = cnt[pred_t][gold_t] / row_total
                if pred_t != gold_t and rate > 0.1:
                    tbl[f"{pred_t}->{gold_t}"] = round(rate, 3)
        flip[p] = tbl
    report["tier_flip"] = flip

    (DATA_DIR / "labels").mkdir(parents=True, exist_ok=True)
    out = DATA_DIR / "labels" / "calibration_report.json"
    out.write_text(json.dumps(report, indent=2))
    print(f"[calibration] wrote {out}")
    for p, s in report["per_persona"].items():
        print(f"  {p}: κ={s['kappa']:.3f} n={s['n']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Run**

Run: `python -m classifier.scripts.run_calibration`
Expected: `calibration_report.json` written, each persona κ printed. Cost: ~$20–30. If κ<0.3 for all personas, STOP and surface to user (see spec §4.3 risk #1).

- [ ] **Step 3: Commit**

```bash
git add classifier/scripts/run_calibration.py data/labels/calibration_report.json data/cost_ledger.jsonl
git commit -m "plan2: calibration pass 150×Opus × 3 personas + κ/confusion/isotonic"
```

### Task E3: Apply calibration to v1_raw → v1_calibrated

**Files:**
- Create: `classifier/labeling/calibration.py`
- Create: `classifier/tests/test_calibration.py`

- [ ] **Step 1: Failing test**

```python
# classifier/tests/test_calibration.py
import pytest
from sklearn.isotonic import IsotonicRegression
from classifier.labeling.calibration import (
    apply_isotonic_to_confidence, apply_tier_flip, compute_pair_weights,
)

def test_isotonic_monotonic():
    xs = [0.1, 0.3, 0.5, 0.7, 0.9]
    ys = [0.05, 0.4, 0.5, 0.8, 0.95]
    ir = IsotonicRegression(out_of_bounds="clip").fit(xs, ys)
    out = [apply_isotonic_to_confidence(ir, c) for c in (0.2, 0.4, 0.6, 0.8)]
    assert all(out[i] <= out[i+1] for i in range(3))

def test_tier_flip_applies_table():
    table = {"Direct->Related": 0.15}  # observed 15% rate → flip suggested
    out = apply_tier_flip("Direct", table, threshold=0.1)
    assert out == "Related"

def test_tier_flip_below_threshold_no_change():
    table = {"Direct->Related": 0.05}
    assert apply_tier_flip("Direct", table, threshold=0.1) == "Direct"

def test_pair_weights_inverse_frequency():
    labels = [{"framework_pair": "a__b"}]*80 + [{"framework_pair": "c__d"}]*20
    w = compute_pair_weights(labels)
    assert w["c__d"] > w["a__b"]
```

- [ ] **Step 2: Implement**

```python
# classifier/labeling/calibration.py
from __future__ import annotations
import json
from collections import Counter
from pathlib import Path
from sklearn.isotonic import IsotonicRegression


def apply_isotonic_to_confidence(ir: IsotonicRegression, conf: float) -> float:
    return float(ir.predict([conf])[0])


def apply_tier_flip(current_tier: str, flip_table: dict[str, float], threshold: float = 0.1) -> str:
    """Flip tier if (current->other) rate exceeds threshold.

    flip_table keys are "from->to" strings; values are observed misread rates.
    """
    best = current_tier
    best_rate = threshold
    for k, rate in flip_table.items():
        src, tgt = k.split("->")
        if src == current_tier and rate > best_rate:
            best, best_rate = tgt, rate
    return best


def compute_pair_weights(labels: list[dict]) -> dict[str, float]:
    counts = Counter(l["framework_pair"] for l in labels)
    if not counts: return {}
    median = sorted(counts.values())[len(counts)//2]
    return {p: round(median / n, 4) for p, n in counts.items()}


def calibrate_aggregated(
    in_path: Path, out_path: Path, calibration_report_path: Path,
) -> int:
    report = json.loads(calibration_report_path.read_text())
    # Fit one isotonic per persona from the report's preview data; we average
    # across personas to apply at the aggregated-label level.
    xs, ys = [], []
    for p, d in report.get("isotonic_calibration_preview", {}).items():
        xs.extend(d["x"])
        ys.extend(d["y_calibrated"])
    ir = IsotonicRegression(out_of_bounds="clip")
    if xs:
        ir.fit(xs, ys)
    # Merge flip tables by majority vote across personas
    merged_flip: dict[str, list[float]] = {}
    for p, tbl in report.get("tier_flip", {}).items():
        for k, r in tbl.items():
            merged_flip.setdefault(k, []).append(r)
    median_flip = {k: sorted(v)[len(v)//2] for k, v in merged_flip.items()}

    out_path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with open(in_path) as fin, open(out_path, "w") as fout:
        for line in fin:
            if not line.strip(): continue
            d = json.loads(line)
            d["raw_confidence"] = d["confidence"]
            d["raw_tier"] = d["tier"]
            if xs:
                d["confidence"] = round(apply_isotonic_to_confidence(ir, d["confidence"]), 4)
            d["tier"] = apply_tier_flip(d["tier"], median_flip)
            fout.write(json.dumps(d, ensure_ascii=False, sort_keys=True) + "\n")
            n += 1
    return n
```

- [ ] **Step 3: Run tests + execute on v1_raw**

Run:
```bash
pytest classifier/tests/test_calibration.py -v
python -c "
from pathlib import Path
from classifier.labeling.calibration import calibrate_aggregated
n = calibrate_aggregated(
    Path('data/labels/llm_sme/v1_raw/aggregated.jsonl'),
    Path('data/labels/llm_sme/v1_calibrated/aggregated.jsonl'),
    Path('data/labels/calibration_report.json'))
print(f'calibrated={n}')
"
```
Expected: tests pass, `calibrated ≈ 10000`.

- [ ] **Step 4: Commit**

```bash
git add classifier/labeling/calibration.py classifier/tests/test_calibration.py data/labels/llm_sme/v1_calibrated/
git commit -m "plan2: v1_calibrated — isotonic + tier-flip applied to aggregated labels"
```

---

## Phase F — Sonnet↔Opus agreement study (300 pairs)

### Task F1: Agreement study runner

**Files:**
- Create: `classifier/labeling/agreement.py`
- Create: `classifier/scripts/run_agreement_study.py`
- Create: `classifier/tests/test_agreement.py`

- [ ] **Step 1: Test first**

```python
# classifier/tests/test_agreement.py
from classifier.labeling.agreement import kappa_and_correlation

def test_perfect_agreement():
    a = [{"pair_key":"p1","tier":"Direct","confidence":0.9}]
    b = [{"pair_key":"p1","tier":"Direct","confidence":0.9}]
    out = kappa_and_correlation(a, b)
    assert out["kappa"] == 1.0
    assert out["confidence_pearson"] > 0.99 or out["n"] < 3

def test_all_disagreement():
    a = [{"pair_key":f"p{i}","tier":"Direct","confidence":0.9} for i in range(10)]
    b = [{"pair_key":f"p{i}","tier":"None","confidence":0.9} for i in range(10)]
    out = kappa_and_correlation(a, b)
    assert out["kappa"] < 0.2
```

- [ ] **Step 2: Implement**

```python
# classifier/labeling/agreement.py
from __future__ import annotations
from pathlib import Path
import json
from scipy.stats import pearsonr, spearmanr
from sklearn.metrics import cohen_kappa_score


TIERS = ["Direct", "Related", "None"]


def kappa_and_correlation(a: list[dict], b: list[dict]) -> dict:
    """a,b are lists of {pair_key,tier,confidence}. Aligned by pair_key."""
    ak = {r["pair_key"]: r for r in a}
    bk = {r["pair_key"]: r for r in b}
    common = sorted(set(ak) & set(bk))
    if not common:
        return {"n": 0, "kappa": 0.0, "confidence_pearson": 0.0, "confidence_spearman": 0.0}
    y_a = [ak[k]["tier"] for k in common]
    y_b = [bk[k]["tier"] for k in common]
    c_a = [ak[k]["confidence"] for k in common]
    c_b = [bk[k]["confidence"] for k in common]
    try:
        pr = float(pearsonr(c_a, c_b)[0])
    except Exception:
        pr = 0.0
    try:
        sr = float(spearmanr(c_a, c_b)[0])
    except Exception:
        sr = 0.0
    return {
        "n": len(common),
        "kappa": float(cohen_kappa_score(y_a, y_b, labels=TIERS)),
        "confidence_pearson": pr,
        "confidence_spearman": sr,
    }
```

- [ ] **Step 3: Entry-point script**

```python
# classifier/scripts/run_agreement_study.py
"""Sonnet↔Opus agreement study on 300 randomly-sampled v1_raw pairs."""
from __future__ import annotations
import argparse, json, random
from pathlib import Path
import anthropic
from classifier.config import DATA_DIR, require_secrets
from classifier.data.splits import verify_hashes
from classifier.labeling.client import LabelerClient
from classifier.labeling.schemas import LabelRequest, Persona
from classifier.labeling.aggregate import aggregate_dir
from classifier.labeling.agreement import kappa_and_correlation
from classifier.data.candidates import load_nodes_by_framework


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=300)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    verify_hashes()
    secrets = require_secrets(["ANTHROPIC_API_KEY"])
    anth = anthropic.Anthropic(api_key=secrets["ANTHROPIC_API_KEY"])
    client = LabelerClient(anth, cache_dir=DATA_DIR / "labels" / "_cache",
                           ledger_path=DATA_DIR / "cost_ledger.jsonl", plan="plan2-agreement")

    sonnet_agg = [json.loads(l) for l in open(DATA_DIR / "labels/llm_sme/v1_raw/aggregated.jsonl")]
    rng = random.Random(args.seed)
    sample = rng.sample(sonnet_agg, min(args.n, len(sonnet_agg)))
    by_id = {n["node_id"]: n for ns in load_nodes_by_framework().values() for n in ns}

    opus_raw_dir = DATA_DIR / "labels/llm_sme/agreement_opus_raw"
    opus_raw_dir.mkdir(parents=True, exist_ok=True)
    for row in sample:
        pk = row["pair_key"]
        src_id, tgt_id = pk.split("::", 1)[1].split("__", 1)
        src = by_id.get(src_id); tgt = by_id.get(tgt_id)
        if src is None or tgt is None: continue
        for persona in Persona:
            req = LabelRequest(
                pair_key=pk,
                source_text=(src.get("description") or src.get("name") or "").strip(),
                target_text=(tgt.get("description") or tgt.get("name") or "").strip(),
                source_framework=src.get("framework") or "?",
                target_framework=tgt.get("framework") or "?",
                persona=persona, model="claude-opus-4-6",
            )
            try:
                resp = client.label(req)
            except ValueError:
                continue
            out = opus_raw_dir / f"{pk.split('::')[0]}.jsonl"
            with open(out, "a") as f:
                f.write(resp.model_dump_json() + "\n")

    opus_agg_path = DATA_DIR / "labels/llm_sme/agreement_opus_aggregated.jsonl"
    aggregate_dir(opus_raw_dir, opus_agg_path)

    sonnet_rows = [{"pair_key": r["pair_key"], "tier": r["tier"], "confidence": r["confidence"]}
                   for r in sample]
    opus_rows = [{"pair_key": json.loads(l)["pair_key"],
                  "tier": json.loads(l)["tier"],
                  "confidence": json.loads(l)["confidence"]}
                 for l in open(opus_agg_path)]
    stats = kappa_and_correlation(sonnet_rows, opus_rows)
    print(f"[agreement] n={stats['n']} kappa={stats['kappa']:.4f} "
          f"pearson={stats['confidence_pearson']:.4f}")

    out_path = DATA_DIR / "labels" / "sonnet_opus_agreement.json"
    out_path.write_text(json.dumps(stats, indent=2))

    if stats["kappa"] < 0.5:
        print(f"[agreement] STOP: κ={stats['kappa']:.3f} < 0.5 — surface to user per spec §4.3 risk #1")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Execute**

Run: `python -m classifier.scripts.run_agreement_study --n 300`
Expected: ~900 Opus calls, ~$40–60 cost, `sonnet_opus_agreement.json` written. If κ ≥ 0.5 → proceed; if < 0.5 → STOP, ask user how to reframe (likely: relabel that subset with Opus or reduce claims).

- [ ] **Step 5: Commit**

```bash
git add classifier/labeling/agreement.py classifier/scripts/run_agreement_study.py classifier/tests/test_agreement.py data/labels/llm_sme/agreement_opus_raw/ data/labels/llm_sme/agreement_opus_aggregated.jsonl data/labels/sonnet_opus_agreement.json data/cost_ledger.jsonl
git commit -m "plan2: Sonnet↔Opus 300-pair agreement study — κ = <value>"
```

---

## Phase G — Freeze + llm_train/llm_val split + contamination CI

### Task G1: Freeze and split

**Files:**
- Create: `classifier/labeling/freeze.py`
- Create: `classifier/scripts/freeze_labels.py`

- [ ] **Step 1: Implement**

```python
# classifier/labeling/freeze.py
from __future__ import annotations
import hashlib
import json
import shutil
from pathlib import Path
from sklearn.model_selection import train_test_split
import pandas as pd


def _sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _write_jsonl_stable(df: pd.DataFrame, path: Path) -> None:
    # Reuse Plan 1's byte-stable conventions.
    path.parent.mkdir(parents=True, exist_ok=True)
    df_sorted = df.sort_values("pair_key").reset_index(drop=True)
    df_sorted.to_json(path, orient="records", lines=True,
                      double_precision=10, date_format="iso", force_ascii=False)


def freeze_and_split(
    calibrated_path: Path, frozen_dir: Path, hashes_path: Path,
    seed: int = 42, val_size: int = 600,
) -> dict[str, int]:
    df = pd.read_json(calibrated_path, lines=True)
    df["framework_pair"] = df["pair_key"].str.split("::").str[0]
    # Stratified split by framework_pair × tier
    df["_stratum"] = df["framework_pair"] + "|" + df["tier"]
    strata_counts = df["_stratum"].value_counts()
    # Collapse singleton strata to framework_pair
    small = strata_counts[strata_counts < 2].index
    df.loc[df["_stratum"].isin(small), "_stratum"] = df["framework_pair"]
    train, val = train_test_split(df, test_size=val_size, random_state=seed, stratify=df["_stratum"])
    train = train.drop(columns=["_stratum"])
    val = val.drop(columns=["_stratum"])

    frozen_dir.mkdir(parents=True, exist_ok=True)
    agg_out = frozen_dir / "aggregated.jsonl"
    train_out = frozen_dir / "llm_train.jsonl"
    val_out = frozen_dir / "llm_val.jsonl"

    _write_jsonl_stable(df.drop(columns=["_stratum"], errors="ignore"), agg_out)
    _write_jsonl_stable(train, train_out)
    _write_jsonl_stable(val, val_out)

    hashes = {
        "v1_frozen/aggregated.jsonl": _sha256(agg_out),
        "v1_frozen/llm_train.jsonl": _sha256(train_out),
        "v1_frozen/llm_val.jsonl":   _sha256(val_out),
    }
    hashes_path.parent.mkdir(parents=True, exist_ok=True)
    hashes_path.write_text(json.dumps(hashes, indent=2, sort_keys=True))

    return {"train": len(train), "val": len(val), "agg": len(df)}
```

```python
# classifier/scripts/freeze_labels.py
from __future__ import annotations
from pathlib import Path
from classifier.config import DATA_DIR
from classifier.labeling.freeze import freeze_and_split


def main() -> int:
    cal = DATA_DIR / "labels/llm_sme/v1_calibrated/aggregated.jsonl"
    frozen = DATA_DIR / "labels/llm_sme/v1_frozen"
    hashes = DATA_DIR / "labels/hashes.json"
    counts = freeze_and_split(cal, frozen, hashes, seed=42, val_size=600)
    print(f"[freeze] {counts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Run**

Run: `python -m classifier.scripts.freeze_labels`
Expected: `{'train': ~9400, 'val': 600, 'agg': ~10000}` printed; `data/labels/llm_sme/v1_frozen/{aggregated,llm_train,llm_val}.jsonl` written; `data/labels/hashes.json` written.

- [ ] **Step 3: Commit**

```bash
git add classifier/labeling/freeze.py classifier/scripts/freeze_labels.py data/labels/llm_sme/v1_frozen/ data/labels/hashes.json
git commit -m "plan2: v1_frozen labels + llm_train/llm_val split + hash manifest"
```

### Task G2: Label leakage canary (contamination CI)

**Files:**
- Create: `classifier/tests/test_label_leakage.py`

- [ ] **Step 1: Write the canary**

```python
# classifier/tests/test_label_leakage.py
"""The Plan 2 contamination canary.

Guarantees:
 1. v1_frozen hashes are byte-stable (analog of Plan 1 split canary).
 2. No pair_key in v1_frozen appears in data/splits/human_test_frozen.jsonl.
 3. No pair_key in v1_frozen appears in data/splits/human_cal.jsonl
    EXCEPT those explicitly sampled during calibration (which is allowed:
    calibration LABELS human_cal but does not train on it; the test
    therefore only enforces frozen-test non-overlap).
 4. llm_train ∩ llm_val == ∅.
 5. llm_train ∪ llm_val == aggregated (within v1_frozen).
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import pytest
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
FROZEN = REPO / "data/labels/llm_sme/v1_frozen"
HASHES = REPO / "data/labels/hashes.json"
HUMAN_FROZEN = REPO / "data/splits/human_test_frozen.jsonl"


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


@pytest.mark.parametrize("rel", ["aggregated.jsonl", "llm_train.jsonl", "llm_val.jsonl"])
def test_hash_stable(rel):
    expected = json.loads(HASHES.read_text())[f"v1_frozen/{rel}"]
    actual = _sha(FROZEN / rel)
    assert actual == expected, f"{rel} drifted — expected {expected}, got {actual}"


def test_no_frozen_test_leakage():
    llm_keys = set(pd.read_json(FROZEN / "aggregated.jsonl", lines=True)["pair_key"])
    human = pd.read_json(HUMAN_FROZEN, lines=True)
    human_keys = set(human["pair_key"])
    leaked = llm_keys & human_keys
    assert not leaked, f"{len(leaked)} pair_keys leaked from human_test_frozen into v1_frozen"


def test_train_val_disjoint():
    train = set(pd.read_json(FROZEN / "llm_train.jsonl", lines=True)["pair_key"])
    val = set(pd.read_json(FROZEN / "llm_val.jsonl", lines=True)["pair_key"])
    assert not (train & val)


def test_train_val_cover_aggregated():
    train = set(pd.read_json(FROZEN / "llm_train.jsonl", lines=True)["pair_key"])
    val = set(pd.read_json(FROZEN / "llm_val.jsonl", lines=True)["pair_key"])
    agg = set(pd.read_json(FROZEN / "aggregated.jsonl", lines=True)["pair_key"])
    assert (train | val) == agg
```

- [ ] **Step 2: Run**

Run: `pytest classifier/tests/test_label_leakage.py -v`
Expected: 6 passed (3 parametrize + 3 others).

- [ ] **Step 3: Commit**

```bash
git add classifier/tests/test_label_leakage.py
git commit -m "plan2: label leakage canary (v1_frozen hash + frozen-test disjoint)"
```

### Task G3: Plan 2 handoff summary

**Files:**
- Create: `classifier/PLAN2_COMPLETE.md`

- [ ] **Step 1: Write**

```markdown
# Plan 2 Handoff — LLM-SME Labeling Pipeline

**Completed:** <date>
**Commits:** <git log --oneline main..HEAD | grep plan2>

## Artifacts produced

- `data/candidates/pool_v2.jsonl` — bge-large-en-v1.5 rebuilt on Lambda
- `data/labels/llm_sme/v1_raw/` — raw Sonnet responses (~30k)
- `data/labels/llm_sme/v1_raw/aggregated.jsonl` — 3-persona aggregation
- `data/labels/llm_sme/v1_calibrated/aggregated.jsonl` — post-isotonic + tier-flip
- `data/labels/llm_sme/v1_frozen/{aggregated,llm_train,llm_val}.jsonl` — frozen + split
- `data/labels/hashes.json` — SHA256 manifest, CI-enforced
- `data/labels/calibration_report.json` — per-persona κ + confusion + tier-flip table
- `data/labels/sonnet_opus_agreement.json` — κ = <VALUE>
- `data/cost_ledger.jsonl` — total spend = $<VALUE>

## Tests passing

- classifier/tests/test_schemas.py
- classifier/tests/test_prompts.py
- classifier/tests/test_labeler_client.py
- classifier/tests/test_sampler.py
- classifier/tests/test_aggregate.py
- classifier/tests/test_calibration.py
- classifier/tests/test_agreement.py
- classifier/tests/test_label_leakage.py

## Ready for Plan 3 (Baselines) and Plan 4 (Training)

Both can assume:
- `data/labels/llm_sme/v1_frozen/llm_train.jsonl` (~9400 rows) and `llm_val.jsonl` (600 rows) exist
- pool_v2 candidates exist
- Calibration report is available as an appendix source for the paper
- Sonnet↔Opus κ ≥ 0.5 verified, or plan has been paused and reframed

## Open notes

1. The 100-pair smoke batch responses (~300 rows in v1_raw) are INCLUDED in v1_calibrated; spec allows this since all data in v1_raw goes through the same calibration pipeline.
2. If a second labeling pass becomes necessary, bump version to v2_raw — do NOT mutate v1_*.
3. Cost ledger should be committed every time a new API run is executed; treat it as a first-class artifact.
```

- [ ] **Step 2: Commit**

```bash
git add classifier/PLAN2_COMPLETE.md
git commit -m "plan2: handoff summary"
```

- [ ] **Step 3: Report completion**

Announce: "Plan 2 complete. v1_frozen labels ready (~10k, κ = <value>), calibration report committed, all tests green. Ready to invoke Plan 3 (Baselines) and Plan 4 (Cross-encoder training)."

---

## Self-Review

**Spec coverage:**
- §2.1 candidate rebuild → Task C1 ✓
- §2.2 Level-E 3-persona protocol → Tasks A3, A4, B1, D1 ✓
- §2.2 temperature 0.3 + Jinja2 templates → Task A3 + client call ✓
- §2.2 idempotent cache → Task B1 (LabelerClient) ✓
- §2.3 calibration → Tasks E2, E3 ✓
- §2.4 Sonnet↔Opus study → Task F1 ✓
- §2.5 label storage + versioning → Tasks D1, E3, G1 ✓
- §2.6 llm_train / llm_val creation → Task G1 (extends Plan 1's split infrastructure with new labels) ✓
- §2.7 budget tracking → cost ledger in every client call ✓
- §6 honesty commitments #1 (sacred run untouched), #4 (κ reported), #5 (raw vs calibrated retained via `raw_tier`/`raw_confidence` columns in v1_calibrated) ✓

**Placeholder scan:** no TBDs, every code block is complete, every shell command has expected output.

**Type consistency:** `LabelResponse` carries the `pair_key` through from `LabelRequest`; `AggregatedLabel.from_responses` consumes `list[LabelResponse]` with exactly 3 entries; `calibrate_aggregated` reads/writes JSONL with stable schema; `freeze_and_split` produces `train`/`val`/`agg` count dict consumed by the entry script.

**Known caveats for executing agent:**
1. Task C1's Lambda dry-run writes `pool_v2.jsonl` on Jetson with bge-small; that file MUST be discarded (`git checkout --`) before committing the script, then regenerated on Lambda with bge-large. The instructions explicitly call this out.
2. Task D3 is rate-limit-bound. The idempotent cache makes resumption free, but the batch API may return partial batches — the bulk loop is append-only per-pair so partial progress is preserved.
3. Task E3's `calibrate_aggregated` averages isotonic calibration curves across personas. This is a simplification of the spec's "per-persona" correction; a per-persona curve is tracked in the calibration report but collapsed at the aggregated-label level because the aggregated label is the only object consumed downstream. If downstream training wants per-persona confidence, Plan 4 can import the per-persona records from `v1_calibrated`.
4. Task F1 stops the plan if κ<0.5. In that case the executing agent surfaces to the user and the plan is paused — this is structural enforcement of §4.3 risk #1.
5. Task G1's stratified split collapses singleton strata to framework_pair only (same fallback Plan 1 uses).
