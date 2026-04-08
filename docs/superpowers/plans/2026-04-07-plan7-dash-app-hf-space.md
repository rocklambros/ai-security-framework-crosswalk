# Plan 7 — Dash App + HuggingFace Space Deployment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the portfolio-grade interactive artifact — a Plotly Dash application with 6 tabs (pair lookup, Cytoscape graph, per-pair confidence/tier/rationale, per-framework coverage heatmap, ablation comparison, feedback form) backed by a FastAPI sidecar serving the Plan 5 final ensemble as an ONNX int8 quantized model, deployed to HuggingFace Spaces via Docker, and satisfying the COMP 4433 Project 2 rubric (explainability, accessibility, reproducibility).

**Architecture:** New top-level `app/` package parallels `classifier/`. The FastAPI sidecar loads the Plan 5 Scorer (Rung L cross-encoder ONNX int8 + LightGBM stacker + Mondrian conformal wrapper) and exposes `/predict`, `/explain`, `/feedback`. Dash process runs in the same container on a different port and talks to the sidecar over localhost HTTP. A SQLite file captures feedback events. A Dockerfile + `huggingface.yml` + `deploy_hf_space.py` script publish to a public HF Space. Every HF artifact (model, dataset, Space) carries a model card with spec §6 honesty commitments baked in (Contract 12, new in this plan).

**Tech Stack:** Python 3.11, `fastapi==0.115.4`, `uvicorn==0.32.0`, `onnx==1.17.0`, `onnxruntime==1.19.2`, `optimum[onnxruntime]==1.23.3`, `dash==2.18.2`, `dash-cytoscape==1.0.2`, `plotly==5.24.1`, `shap==0.46.0`, `sqlalchemy==2.0.36`, `httpx==0.27.2`, `huggingface_hub==0.26.2`, `pytest==8.3.3`, `pytest-asyncio==0.24.0`.

---

## Spec Reference

Implements §4.2 (Dash app architecture), §4.6 (deliverables 4 — HF Space), §6 (honesty commitments baked into model cards) of `docs/superpowers/specs/2026-04-07-ai-security-crosswalk-classifier-design.md`. Consumes the Plan 5 final ensemble Scorer (Contract 4). Enforces the split-hash canary at sidecar startup (Contract 1). Introduces a new Contract 12: every HF Space artifact MUST carry a model card with spec §6 honesty commitments baked in.

**Out of scope for Plan 7:** model training (Plans 4–5), the sacred run (Plan 6), the blog post or arXiv writeup. Plan 7 assumes the Plan 5 `Scorer.save()` artifact and the Plan 6 `ablations.json` already exist on disk.

---

## Cross-Plan Contracts (enforced here)

| # | Contract | Enforcement point in Plan 7 |
|---|---|---|
| 1 | `verify_hashes()` at service boundary | Called in FastAPI `lifespan` startup; sidecar refuses to boot on mismatch |
| 4 | Consume Plan 5 final Scorer via `app.api.scorer_loader.load_scorer()` — no reaching into internals | Task B1–B2 |
| 12 (NEW) | Every HF Space artifact carries a model card with spec §6 honesty commitments verbatim | Task G1 builds the card; `tests/test_model_card.py` greps for the 8 commitments before deploy |

---

## File Structure

Plan 7 creates and only touches these paths. **Do not modify** any existing file under `classifier/`, `mapping_engine/`, `notebooks/`, `data/frameworks/`, `data/processed/`, or `data/splits/`.

| Path | Purpose |
|---|---|
| `app/__init__.py` | Package marker |
| `app/api/__init__.py` | Sidecar package marker |
| `app/api/main.py` | FastAPI app — lifespan + routes |
| `app/api/schemas.py` | Pydantic request/response schemas |
| `app/api/scorer_loader.py` | Plan 5 Scorer loader (Contract 4) |
| `app/api/onnx_runtime.py` | ONNX int8 session wrapper + int8 export |
| `app/api/explain.py` | SHAP top-k feature attribution over stacker features |
| `app/api/feedback_store.py` | SQLite feedback persistence |
| `app/dash_app/__init__.py` | Dash package marker |
| `app/dash_app/app.py` | Dash app factory + server bootstrap |
| `app/dash_app/layout.py` | 6-tab layout + shared `dcc.Store` |
| `app/dash_app/api_client.py` | httpx client wrapping sidecar |
| `app/dash_app/tabs/__init__.py` | Tabs package marker |
| `app/dash_app/tabs/tab1_lookup.py` | Pair lookup form + results table |
| `app/dash_app/tabs/tab2_graph.py` | Cytoscape densified graph view |
| `app/dash_app/tabs/tab3_detail.py` | Per-pair confidence + tier set + rationale |
| `app/dash_app/tabs/tab4_matrix.py` | Per-framework coverage heatmap (12 pairs) |
| `app/dash_app/tabs/tab5_ablations.py` | Ablation comparison bar chart from Plan 6 `ablations.json` |
| `app/dash_app/tabs/tab6_feedback.py` | Feedback form → sidecar POST |
| `app/scripts/__init__.py` | Scripts package marker |
| `app/scripts/export_onnx_int8.py` | Export Rung L cross-encoder → ONNX int8 |
| `app/scripts/benchmark_onnx.py` | Size + p50/p95 latency benchmark |
| `app/scripts/deploy_hf_space.py` | Create/push HF Space repo |
| `app/tests/__init__.py` | Tests package marker |
| `app/tests/conftest.py` | Pytest fixtures (sidecar TestClient, fake Scorer) |
| `app/tests/test_onnx_export.py` | ONNX int8 export + parity check |
| `app/tests/test_onnx_benchmark.py` | Size (<200 MB) + p95 (<500 ms) bench gate |
| `app/tests/test_api_predict.py` | `/predict` happy path + contract-1 guard |
| `app/tests/test_api_explain.py` | `/explain` SHAP top-k shape |
| `app/tests/test_api_feedback.py` | `/feedback` POST → SQLite row |
| `app/tests/test_dash_smoke.py` | Dash app imports + renders 6 tabs |
| `app/tests/test_tab1_lookup.py` | Pair lookup callback round-trip |
| `app/tests/test_tab2_graph.py` | Cytoscape elements built from graph densification |
| `app/tests/test_tab4_matrix.py` | Heatmap covers all 12 pairs |
| `app/tests/test_tab5_ablations.py` | Reads `ablations.json`, renders bars |
| `app/tests/test_model_card.py` | Asserts all 8 spec §6 commitments in card (Contract 12) |
| `app/deploy/Dockerfile` | Multi-stage build, CPU-only base |
| `app/deploy/huggingface.yml` | HF Space config (sdk: docker) |
| `app/deploy/supervisord.conf` | Runs FastAPI + Dash in one container |
| `app/deploy/MODEL_CARD.md` | Model card with §6 commitments baked in |
| `app/deploy/RUNBOOK.md` | Local + HF deploy runbook |
| `requirements-app.txt` | New pinned deps for Plan 7 |

---

## Phase A — ONNX int8 Export + Benchmark

Goal: take the Plan 5 Rung L cross-encoder + stacker artifacts and produce a CPU-servable int8 ONNX bundle with measured size and latency.

### Task A1: Requirements + ONNX export script (failing test first)

**Files:**
- Create: `requirements-app.txt`
- Create: `app/__init__.py`, `app/api/__init__.py`, `app/scripts/__init__.py`, `app/tests/__init__.py`, `app/tests/conftest.py`
- Create: `app/tests/test_onnx_export.py`
- Create: `app/scripts/export_onnx_int8.py`
- Create: `app/api/onnx_runtime.py`

- [ ] **Step 1: Pin deps**

`requirements-app.txt`:
```
fastapi==0.115.4
uvicorn[standard]==0.32.0
pydantic==2.9.2
httpx==0.27.2
onnx==1.17.0
onnxruntime==1.19.2
optimum[onnxruntime]==1.23.3
dash==2.18.2
dash-cytoscape==1.0.2
plotly==5.24.1
shap==0.46.0
sqlalchemy==2.0.36
pytest==8.3.3
pytest-asyncio==0.24.0
```

Install: `source .venv/bin/activate && pip install -r requirements-app.txt`.

- [ ] **Step 2: Create the package skeleton**

```bash
mkdir -p app/api app/dash_app/tabs app/scripts app/tests app/deploy
touch app/__init__.py app/api/__init__.py app/dash_app/__init__.py \
      app/dash_app/tabs/__init__.py app/scripts/__init__.py app/tests/__init__.py
```

- [ ] **Step 3: Shared pytest fixture**

`app/tests/conftest.py`:
```python
from __future__ import annotations
from pathlib import Path
import json
import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture
def tmp_scorer_bundle(tmp_path: Path) -> Path:
    """Minimal on-disk fake of the Plan 5 Scorer bundle for unit tests."""
    bundle = tmp_path / "scorer"
    bundle.mkdir()
    (bundle / "manifest.json").write_text(json.dumps({
        "version": "plan5-test",
        "rung_l_onnx": "rung_l.int8.onnx",
        "stacker": "stacker.lgbm",
        "conformal": "conformal.json",
        "feature_names": [f"f{i}" for i in range(32)],
    }))
    (bundle / "rung_l.int8.onnx").write_bytes(b"ONNX_FAKE")
    (bundle / "stacker.lgbm").write_bytes(b"LGBM_FAKE")
    (bundle / "conformal.json").write_text(json.dumps({"alpha": 0.2, "q": 0.33}))
    return bundle


@pytest.fixture
def fake_scorer(tmp_scorer_bundle, monkeypatch):
    """In-memory fake of Plan 5 Scorer exposing the same surface."""
    from app.api import scorer_loader

    class _Fake:
        version = "plan5-test"
        feature_names = [f"f{i}" for i in range(32)]

        def predict(self, source_text, target_text):
            return {
                "tier_probs": {"Direct": 0.71, "Related": 0.22, "None": 0.07},
                "tier": "Direct",
                "relevance": 0.88,
                "conformal_set": ["Direct"],
                "conformal_coverage": 0.80,
                "features": {f"f{i}": float(i) / 32 for i in range(32)},
                "rationale_code": "FUNCTIONAL_OVERLAP",
            }

    monkeypatch.setattr(scorer_loader, "_CACHED", _Fake())
    return _Fake()
```

- [ ] **Step 4: Write failing test for ONNX export**

`app/tests/test_onnx_export.py`:
```python
from pathlib import Path
import numpy as np
import pytest

from app.scripts import export_onnx_int8
from app.api.onnx_runtime import OnnxInt8Session


def test_export_writes_int8_bundle(tmp_path: Path):
    out = export_onnx_int8.export(
        hf_model_id="sentence-transformers/all-MiniLM-L6-v2",  # small stand-in for bge-reranker
        output_dir=tmp_path,
    )
    assert (out / "model.onnx").exists()
    assert (out / "model.int8.onnx").exists()
    assert (out / "model.int8.onnx").stat().st_size < (out / "model.onnx").stat().st_size


def test_int8_session_runs(tmp_path: Path):
    bundle = export_onnx_int8.export(
        hf_model_id="sentence-transformers/all-MiniLM-L6-v2",
        output_dir=tmp_path,
    )
    sess = OnnxInt8Session.load(bundle)
    scores = sess.score_pairs([("hello", "world"), ("foo", "bar")])
    assert scores.shape == (2,)
    assert np.isfinite(scores).all()
```

Run: `pytest app/tests/test_onnx_export.py -v` → expect `ModuleNotFoundError`.

- [ ] **Step 5: Implement `app/api/onnx_runtime.py`**

```python
"""ONNX Runtime wrapper for the int8-quantized Rung L cross-encoder."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence
import numpy as np
import onnxruntime as ort
from transformers import AutoTokenizer


@dataclass
class OnnxInt8Session:
    session: ort.InferenceSession
    tokenizer: "AutoTokenizer"
    max_length: int = 512

    @classmethod
    def load(cls, bundle_dir: Path) -> "OnnxInt8Session":
        model_path = bundle_dir / "model.int8.onnx"
        if not model_path.exists():
            raise FileNotFoundError(f"missing {model_path}")
        sess_opts = ort.SessionOptions()
        sess_opts.intra_op_num_threads = 1
        sess_opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        session = ort.InferenceSession(
            str(model_path), sess_options=sess_opts, providers=["CPUExecutionProvider"]
        )
        tokenizer = AutoTokenizer.from_pretrained(str(bundle_dir))
        return cls(session=session, tokenizer=tokenizer)

    def score_pairs(self, pairs: Sequence[tuple[str, str]]) -> np.ndarray:
        encoded = self.tokenizer(
            [p[0] for p in pairs],
            [p[1] for p in pairs],
            padding=True,
            truncation=True,
            max_length=self.max_length,
            return_tensors="np",
        )
        inputs = {k: v.astype(np.int64) for k, v in encoded.items() if k in {i.name for i in self.session.get_inputs()}}
        out = self.session.run(None, inputs)[0]
        if out.ndim == 2 and out.shape[1] == 1:
            out = out[:, 0]
        return out.astype(np.float32)
```

- [ ] **Step 6: Implement `app/scripts/export_onnx_int8.py`**

```python
"""Export a HF cross-encoder to int8 ONNX for CPU inference."""
from __future__ import annotations
import argparse
from pathlib import Path
from optimum.onnxruntime import ORTModelForSequenceClassification, ORTQuantizer
from optimum.onnxruntime.configuration import AutoQuantizationConfig
from transformers import AutoTokenizer


def export(hf_model_id: str, output_dir: Path) -> Path:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    model = ORTModelForSequenceClassification.from_pretrained(hf_model_id, export=True)
    model.save_pretrained(output_dir)
    AutoTokenizer.from_pretrained(hf_model_id).save_pretrained(output_dir)
    quantizer = ORTQuantizer.from_pretrained(output_dir)
    qconfig = AutoQuantizationConfig.avx512_vnni(is_static=False, per_channel=True)
    quantizer.quantize(save_dir=output_dir, quantization_config=qconfig)
    # Optimum writes model_quantized.onnx — rename to model.int8.onnx for our loader.
    src = output_dir / "model_quantized.onnx"
    dst = output_dir / "model.int8.onnx"
    if src.exists() and not dst.exists():
        src.rename(dst)
    return output_dir


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hf-model-id", default="BAAI/bge-reranker-v2-m3")
    ap.add_argument("--output-dir", type=Path, default=Path("data/onnx/rung_l_int8"))
    args = ap.parse_args()
    out = export(args.hf_model_id, args.output_dir)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
```

Run: `pytest app/tests/test_onnx_export.py -v` → expect 2 passed (may take ~60s on first run to download MiniLM).

- [ ] **Step 7: Commit**

```bash
git add requirements-app.txt app/__init__.py app/api/__init__.py app/api/onnx_runtime.py \
        app/dash_app/__init__.py app/dash_app/tabs/__init__.py app/scripts/__init__.py \
        app/scripts/export_onnx_int8.py app/tests/__init__.py app/tests/conftest.py \
        app/tests/test_onnx_export.py
git commit -m "plan7: onnx int8 export pipeline for rung L"
```

### Task A2: Size + latency benchmark test

**Files:**
- Create: `app/tests/test_onnx_benchmark.py`
- Create: `app/scripts/benchmark_onnx.py`

- [ ] **Step 1: Write failing benchmark test**

```python
from pathlib import Path
import pytest
from app.scripts import benchmark_onnx, export_onnx_int8

MAX_SIZE_MB = 200
MAX_P95_MS = 500


def test_benchmark_gate(tmp_path: Path):
    bundle = export_onnx_int8.export(
        hf_model_id="sentence-transformers/all-MiniLM-L6-v2",
        output_dir=tmp_path,
    )
    report = benchmark_onnx.run(bundle, n_warmup=2, n_trials=20)
    assert report["size_mb"] < MAX_SIZE_MB, report
    assert report["p95_ms"] < MAX_P95_MS, report
    assert report["p50_ms"] > 0
```

Run: `pytest app/tests/test_onnx_benchmark.py -v` → expect ModuleNotFoundError.

- [ ] **Step 2: Implement benchmark**

```python
"""Measure size + latency of an int8 ONNX cross-encoder bundle."""
from __future__ import annotations
import argparse
import json
import time
from pathlib import Path
from statistics import median
import numpy as np
from app.api.onnx_runtime import OnnxInt8Session


_SAMPLE_PAIRS = [
    ("The system shall enforce MFA on privileged access.",
     "Require multi-factor authentication for administrative actions."),
    ("Monitor agent tool invocations for anomalies.",
     "Log every agentic tool call and flag deviations."),
]


def run(bundle_dir: Path, n_warmup: int = 3, n_trials: int = 50) -> dict:
    sess = OnnxInt8Session.load(bundle_dir)
    size_bytes = (bundle_dir / "model.int8.onnx").stat().st_size
    for _ in range(n_warmup):
        sess.score_pairs(_SAMPLE_PAIRS)
    times_ms: list[float] = []
    for _ in range(n_trials):
        t0 = time.perf_counter()
        sess.score_pairs(_SAMPLE_PAIRS)
        times_ms.append((time.perf_counter() - t0) * 1000)
    arr = np.array(times_ms)
    return {
        "size_mb": size_bytes / (1024 * 1024),
        "p50_ms": float(median(arr)),
        "p95_ms": float(np.percentile(arr, 95)),
        "n_trials": n_trials,
        "sample_batch": len(_SAMPLE_PAIRS),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("bundle_dir", type=Path)
    ap.add_argument("--out", type=Path, default=Path("data/onnx/benchmark.json"))
    args = ap.parse_args()
    report = run(args.bundle_dir)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
```

Run: `pytest app/tests/test_onnx_benchmark.py -v` → expect 1 passed.

- [ ] **Step 3: Commit**

```bash
git add app/scripts/benchmark_onnx.py app/tests/test_onnx_benchmark.py
git commit -m "plan7: onnx size+latency benchmark gate"
```

### Task A3: Plan 5 Scorer loader (Contract 4)

**Files:**
- Create: `app/api/scorer_loader.py`

- [ ] **Step 1: Implement the loader (no tests — exercised via sidecar tests in Phase B)**

```python
"""Load the Plan 5 final ensemble Scorer (Contract 4).

This module is the ONLY place in Plan 7 code that knows the on-disk layout of
Plan 5's Scorer bundle. Everything else consumes the dict interface produced
by `Scorer.predict(source_text, target_text)`.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
from typing import Any

_CACHED: Any | None = None


def _default_bundle_dir() -> Path:
    return Path(os.environ.get("SCORER_BUNDLE_DIR", "data/plan5/scorer_bundle"))


def load_scorer(bundle_dir: Path | None = None) -> Any:
    """Return a process-wide singleton Scorer."""
    global _CACHED
    if _CACHED is not None:
        return _CACHED
    bundle_dir = bundle_dir or _default_bundle_dir()
    manifest = json.loads((bundle_dir / "manifest.json").read_text())
    # Plan 5 ships `classifier.inference.scorer.Scorer.from_bundle(...)`.
    from classifier.inference.scorer import Scorer  # provided by Plan 5
    _CACHED = Scorer.from_bundle(bundle_dir, manifest=manifest)
    return _CACHED


def reset_cache() -> None:
    global _CACHED
    _CACHED = None
```

- [ ] **Step 2: Commit**

```bash
git add app/api/scorer_loader.py
git commit -m "plan7: plan5 scorer loader (contract 4)"
```

---

## Phase B — FastAPI Sidecar

### Task B1: Pydantic schemas + `/predict` endpoint (failing test first)

**Files:**
- Create: `app/api/schemas.py`
- Create: `app/api/main.py`
- Create: `app/tests/test_api_predict.py`

- [ ] **Step 1: Write failing TestClient test**

`app/tests/test_api_predict.py`:
```python
import pytest
from fastapi.testclient import TestClient
from app.api.main import create_app


@pytest.fixture
def client(fake_scorer, monkeypatch):
    monkeypatch.setattr("app.api.main.verify_hashes", lambda: None)
    return TestClient(create_app())


def test_predict_happy_path(client):
    r = client.post("/predict", json={
        "source_text": "enforce mfa on admins",
        "target_text": "require mfa for privileged access",
        "source_framework": "aiuc-1",
        "target_framework": "owasp-agentic",
    })
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["tier"] in {"Direct", "Related", "None"}
    assert 0.0 <= data["tier_probs"]["Direct"] <= 1.0
    assert "conformal_set" in data
    assert data["model_version"] == "plan5-test"


def test_predict_refuses_when_hashes_stale(monkeypatch, fake_scorer):
    def _bad():
        raise RuntimeError("split hash mismatch")
    monkeypatch.setattr("app.api.main.verify_hashes", _bad)
    with pytest.raises(RuntimeError):
        TestClient(create_app()).__enter__()
```

Run: expect ModuleNotFoundError.

- [ ] **Step 2: Implement schemas**

```python
# app/api/schemas.py
from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field

Tier = Literal["Direct", "Related", "None"]


class PredictRequest(BaseModel):
    source_text: str = Field(min_length=1, max_length=4000)
    target_text: str = Field(min_length=1, max_length=4000)
    source_framework: str
    target_framework: str


class PredictResponse(BaseModel):
    tier: Tier
    tier_probs: dict[str, float]
    relevance: float
    conformal_set: list[Tier]
    conformal_coverage: float
    rationale_code: str
    model_version: str


class ExplainRequest(PredictRequest):
    top_k: int = 5


class ExplainResponse(BaseModel):
    top_features: list[dict]  # [{name, value, shap}]
    model_version: str


class FeedbackRequest(BaseModel):
    pair_key: str
    predicted_tier: Tier
    user_tier: Tier
    agree: bool
    comment: str = ""
    session_id: str = "anon"


class FeedbackResponse(BaseModel):
    id: int
    stored_at: str
```

- [ ] **Step 3: Implement `app/api/main.py`**

```python
"""FastAPI sidecar for the Plan 5 ensemble."""
from __future__ import annotations
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from classifier.data.splits import verify_hashes  # Contract 1
from app.api import scorer_loader
from app.api.schemas import (
    PredictRequest, PredictResponse,
    ExplainRequest, ExplainResponse,
    FeedbackRequest, FeedbackResponse,
)
from app.api.explain import shap_top_k
from app.api.feedback_store import FeedbackStore

log = logging.getLogger("plan7.sidecar")


@asynccontextmanager
async def lifespan(app: FastAPI):
    verify_hashes()  # Contract 1 — refuse to boot on stale splits
    app.state.scorer = scorer_loader.load_scorer()
    app.state.feedback = FeedbackStore.open_default()
    log.info("sidecar ready version=%s", app.state.scorer.version)
    yield
    app.state.feedback.close()


def create_app() -> FastAPI:
    app = FastAPI(title="ai-security-crosswalk sidecar", version="0.1", lifespan=lifespan)

    @app.get("/health")
    def health():
        return {"status": "ok", "version": getattr(app.state, "scorer", None) and app.state.scorer.version}

    @app.post("/predict", response_model=PredictResponse)
    def predict(req: PredictRequest) -> PredictResponse:
        out = app.state.scorer.predict(req.source_text, req.target_text)
        return PredictResponse(
            tier=out["tier"],
            tier_probs=out["tier_probs"],
            relevance=out["relevance"],
            conformal_set=out["conformal_set"],
            conformal_coverage=out["conformal_coverage"],
            rationale_code=out["rationale_code"],
            model_version=app.state.scorer.version,
        )

    @app.post("/explain", response_model=ExplainResponse)
    def explain(req: ExplainRequest) -> ExplainResponse:
        out = app.state.scorer.predict(req.source_text, req.target_text)
        top = shap_top_k(app.state.scorer, out["features"], k=req.top_k)
        return ExplainResponse(top_features=top, model_version=app.state.scorer.version)

    @app.post("/feedback", response_model=FeedbackResponse)
    def feedback(req: FeedbackRequest) -> FeedbackResponse:
        row = app.state.feedback.insert(req.model_dump())
        return FeedbackResponse(id=row["id"], stored_at=row["stored_at"])

    return app
```

Run `pytest app/tests/test_api_predict.py -v` once the remaining B2–B4 modules exist; for now the test imports will fail and that is expected at this step.

- [ ] **Step 4: Commit**

```bash
git add app/api/schemas.py app/api/main.py app/tests/test_api_predict.py
git commit -m "plan7: fastapi sidecar /predict + contract-1 guard"
```

### Task B2: `/explain` SHAP top-k

**Files:**
- Create: `app/api/explain.py`
- Create: `app/tests/test_api_explain.py`

- [ ] **Step 1: Failing test**

```python
# app/tests/test_api_explain.py
import pytest
from fastapi.testclient import TestClient
from app.api.main import create_app


@pytest.fixture
def client(fake_scorer, monkeypatch):
    monkeypatch.setattr("app.api.main.verify_hashes", lambda: None)
    monkeypatch.setattr(
        "app.api.explain._shap_values",
        lambda scorer, feats: {name: (i - 16) / 32 for i, name in enumerate(feats)},
    )
    return TestClient(create_app())


def test_explain_top_k(client):
    r = client.post("/explain", json={
        "source_text": "a", "target_text": "b",
        "source_framework": "aiuc-1", "target_framework": "owasp-agentic",
        "top_k": 5,
    })
    assert r.status_code == 200, r.text
    data = r.json()
    assert len(data["top_features"]) == 5
    assert {f["name"] for f in data["top_features"]}.issubset({f"f{i}" for i in range(32)})
    assert all("shap" in f and "value" in f for f in data["top_features"])
```

- [ ] **Step 2: Implement `app/api/explain.py`**

```python
"""SHAP top-k feature attribution over the Plan 5 stacker features."""
from __future__ import annotations
from typing import Any
import numpy as np


def _shap_values(scorer: Any, features: dict[str, float]) -> dict[str, float]:
    """Return a {feature_name: shap_value} dict.

    Plan 5 bundles a TreeExplainer on its LightGBM stacker; we call it here.
    A unit-test monkeypatch replaces this function with a deterministic stub.
    """
    import shap
    explainer = shap.TreeExplainer(scorer.stacker)
    names = list(features.keys())
    x = np.array([[features[n] for n in names]], dtype=np.float32)
    sv = explainer.shap_values(x)
    # Binary / multi-class trees may return a list; collapse to per-feature magnitude
    if isinstance(sv, list):
        sv = np.mean([np.abs(s) for s in sv], axis=0)
    sv = np.asarray(sv).reshape(-1)
    return dict(zip(names, sv.tolist()))


def shap_top_k(scorer: Any, features: dict[str, float], k: int) -> list[dict]:
    values = _shap_values(scorer, features)
    ranked = sorted(values.items(), key=lambda kv: abs(kv[1]), reverse=True)[:k]
    return [{"name": name, "value": features[name], "shap": shap} for name, shap in ranked]
```

- [ ] **Step 3: Run both API tests**

Run: `pytest app/tests/test_api_predict.py app/tests/test_api_explain.py -v` → 3 passed.

- [ ] **Step 4: Commit**

```bash
git add app/api/explain.py app/tests/test_api_explain.py
git commit -m "plan7: /explain shap top-k"
```

### Task B3: `/feedback` + SQLite store

**Files:**
- Create: `app/api/feedback_store.py`
- Create: `app/tests/test_api_feedback.py`

- [ ] **Step 1: Failing test**

```python
# app/tests/test_api_feedback.py
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from app.api.main import create_app
from app.api.feedback_store import FeedbackStore


@pytest.fixture
def client(fake_scorer, monkeypatch, tmp_path: Path):
    monkeypatch.setattr("app.api.main.verify_hashes", lambda: None)
    monkeypatch.setattr(FeedbackStore, "open_default",
                        classmethod(lambda cls: cls.open(tmp_path / "fb.sqlite")))
    return TestClient(create_app()), tmp_path / "fb.sqlite"


def test_feedback_roundtrip(client):
    tc, db_path = client
    r = tc.post("/feedback", json={
        "pair_key": "aiuc-1:C-1.2__owasp-agentic:ASI-03",
        "predicted_tier": "Direct",
        "user_tier": "Related",
        "agree": False,
        "comment": "overlaps but not identical",
        "session_id": "sess1",
    })
    assert r.status_code == 200, r.text
    assert r.json()["id"] >= 1
    assert db_path.exists()
    store = FeedbackStore.open(db_path)
    rows = store.all()
    assert len(rows) == 1
    assert rows[0]["user_tier"] == "Related"
```

- [ ] **Step 2: Implement `app/api/feedback_store.py`**

```python
"""Minimal SQLite store for Dash feedback events."""
from __future__ import annotations
import datetime as dt
import os
from pathlib import Path
from sqlalchemy import (create_engine, Column, Integer, String, Boolean,
                        DateTime, MetaData, Table, insert, select)


_metadata = MetaData()

feedback = Table(
    "feedback", _metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("pair_key", String, nullable=False),
    Column("predicted_tier", String, nullable=False),
    Column("user_tier", String, nullable=False),
    Column("agree", Boolean, nullable=False),
    Column("comment", String, nullable=False, default=""),
    Column("session_id", String, nullable=False, default="anon"),
    Column("stored_at", DateTime, nullable=False),
)


class FeedbackStore:
    def __init__(self, engine):
        self.engine = engine
        _metadata.create_all(engine)

    @classmethod
    def open(cls, path: Path) -> "FeedbackStore":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        return cls(create_engine(f"sqlite:///{path}", future=True))

    @classmethod
    def open_default(cls) -> "FeedbackStore":
        return cls.open(Path(os.environ.get("FEEDBACK_DB", "data/feedback.sqlite")))

    def insert(self, payload: dict) -> dict:
        now = dt.datetime.utcnow()
        with self.engine.begin() as conn:
            result = conn.execute(insert(feedback).values(stored_at=now, **payload))
            new_id = result.inserted_primary_key[0]
        return {"id": new_id, "stored_at": now.isoformat()}

    def all(self) -> list[dict]:
        with self.engine.begin() as conn:
            rows = conn.execute(select(feedback)).mappings().all()
        return [dict(r) for r in rows]

    def close(self) -> None:
        self.engine.dispose()
```

Run: `pytest app/tests/test_api_feedback.py -v` → 1 passed.

- [ ] **Step 3: Commit**

```bash
git add app/api/feedback_store.py app/tests/test_api_feedback.py
git commit -m "plan7: /feedback sqlite store"
```

### Task B4: Sidecar integration sanity (all three endpoints under one TestClient)

**Files:**
- Modify: `app/tests/test_api_predict.py` — add a combined smoke check

- [ ] **Step 1: Append combined check**

Add at the bottom of `test_api_predict.py`:
```python
def test_health_endpoint(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
```

Run: `pytest app/tests/test_api_predict.py app/tests/test_api_explain.py app/tests/test_api_feedback.py -v` → all green.

- [ ] **Step 2: Commit**

```bash
git add app/tests/test_api_predict.py
git commit -m "plan7: sidecar /health smoke"
```

---

## Phase C — Dash App Skeleton

### Task C1: 6-tab layout + dcc.Store + smoke render

**Files:**
- Create: `app/dash_app/app.py`
- Create: `app/dash_app/layout.py`
- Create: `app/dash_app/api_client.py`
- Create: `app/tests/test_dash_smoke.py`

- [ ] **Step 1: Failing smoke test**

```python
# app/tests/test_dash_smoke.py
from app.dash_app.app import create_dash_app


def test_dash_app_has_six_tabs():
    app = create_dash_app()
    layout_repr = str(app.layout)
    for tab_id in ("tab-lookup", "tab-graph", "tab-detail",
                   "tab-matrix", "tab-ablations", "tab-feedback"):
        assert tab_id in layout_repr
    assert "pair-store" in layout_repr  # dcc.Store id
```

- [ ] **Step 2: Implement `api_client.py`**

```python
"""httpx client wrapping the FastAPI sidecar."""
from __future__ import annotations
import os
import httpx


class SidecarClient:
    def __init__(self, base_url: str | None = None, timeout: float = 10.0):
        self.base_url = base_url or os.environ.get("SIDECAR_URL", "http://127.0.0.1:8001")
        self._client = httpx.Client(base_url=self.base_url, timeout=timeout)

    def predict(self, payload: dict) -> dict:
        return self._client.post("/predict", json=payload).raise_for_status().json()

    def explain(self, payload: dict) -> dict:
        return self._client.post("/explain", json=payload).raise_for_status().json()

    def feedback(self, payload: dict) -> dict:
        return self._client.post("/feedback", json=payload).raise_for_status().json()

    def health(self) -> dict:
        return self._client.get("/health").raise_for_status().json()
```

- [ ] **Step 3: Implement `layout.py`**

```python
"""6-tab Dash layout with a shared dcc.Store for cross-tab state."""
from __future__ import annotations
from dash import dcc, html
from app.dash_app.tabs import (
    tab1_lookup, tab2_graph, tab3_detail,
    tab4_matrix, tab5_ablations, tab6_feedback,
)


def build_layout() -> html.Div:
    return html.Div(
        [
            html.H1("AI Security Framework Crosswalk"),
            html.P(
                "Explore calibrated cross-framework mappings with conformal abstention. "
                "Select a pair in Tab 1 or click a node in Tab 2; Tab 3 shows per-pair "
                "confidence, tier set, and rationale.",
                className="lead",
            ),
            dcc.Store(id="pair-store", storage_type="memory"),
            dcc.Tabs(
                id="tabs",
                value="tab-lookup",
                children=[
                    dcc.Tab(label="1 · Lookup", value="tab-lookup", children=tab1_lookup.build()),
                    dcc.Tab(label="2 · Graph", value="tab-graph", children=tab2_graph.build()),
                    dcc.Tab(label="3 · Detail", value="tab-detail", children=tab3_detail.build()),
                    dcc.Tab(label="4 · Matrix", value="tab-matrix", children=tab4_matrix.build()),
                    dcc.Tab(label="5 · Ablations", value="tab-ablations", children=tab5_ablations.build()),
                    dcc.Tab(label="6 · Feedback", value="tab-feedback", children=tab6_feedback.build()),
                ],
            ),
        ],
        role="main",
    )
```

- [ ] **Step 4: Implement `app.py`**

```python
"""Dash app factory."""
from __future__ import annotations
import dash
from app.dash_app.layout import build_layout


def create_dash_app() -> dash.Dash:
    app = dash.Dash(
        __name__,
        title="AI Security Crosswalk",
        suppress_callback_exceptions=True,
        update_title=None,
    )
    app.layout = build_layout()
    # Callbacks are registered lazily by each tab module on first import inside build_layout().
    from app.dash_app.tabs import tab1_lookup, tab3_detail, tab6_feedback
    tab1_lookup.register_callbacks(app)
    tab3_detail.register_callbacks(app)
    tab6_feedback.register_callbacks(app)
    return app


if __name__ == "__main__":
    create_dash_app().run(host="0.0.0.0", port=8050, debug=False)
```

- [ ] **Step 5: Stub each tab's `build()` so the skeleton renders**

Create `app/dash_app/tabs/tab1_lookup.py`, `tab2_graph.py`, `tab3_detail.py`, `tab4_matrix.py`, `tab5_ablations.py`, `tab6_feedback.py` each with:
```python
from dash import html

def build():
    return html.Div("placeholder", id="tab-<name>")

def register_callbacks(app):
    pass
```
Replacing `<name>` with `lookup`, `graph`, `detail`, `matrix`, `ablations`, `feedback`. Only `tab1_lookup.py`, `tab3_detail.py`, `tab6_feedback.py` need `register_callbacks` — the other three can omit it.

Run: `pytest app/tests/test_dash_smoke.py -v` → 1 passed.

- [ ] **Step 6: Commit**

```bash
git add app/dash_app/ app/tests/test_dash_smoke.py
git commit -m "plan7: dash skeleton 6 tabs + shared store"
```

---

## Phase D — Tab 1 Lookup + Tab 2 Cytoscape Graph

### Task D1: Tab 1 pair lookup callback

**Files:**
- Modify: `app/dash_app/tabs/tab1_lookup.py`
- Create: `app/tests/test_tab1_lookup.py`

- [ ] **Step 1: Failing callback test**

```python
# app/tests/test_tab1_lookup.py
from unittest.mock import MagicMock
from app.dash_app.tabs import tab1_lookup


def test_lookup_callback_calls_sidecar():
    fake_client = MagicMock()
    fake_client.predict.return_value = {
        "tier": "Direct", "tier_probs": {"Direct": 0.9, "Related": 0.08, "None": 0.02},
        "relevance": 0.9, "conformal_set": ["Direct"], "conformal_coverage": 0.8,
        "rationale_code": "FUNCTIONAL_OVERLAP", "model_version": "plan5-test",
    }
    store, text = tab1_lookup._lookup(
        n_clicks=1,
        source_text="enforce mfa on admins",
        target_text="require mfa for privileged",
        source_fw="aiuc-1", target_fw="owasp-agentic",
        client=fake_client,
    )
    assert store["tier"] == "Direct"
    assert "Direct" in text
    fake_client.predict.assert_called_once()
```

- [ ] **Step 2: Implement Tab 1**

```python
"""Tab 1 — pair lookup form."""
from __future__ import annotations
from dash import dcc, html, Input, Output, State, callback_context, no_update
from app.dash_app.api_client import SidecarClient

_FRAMEWORKS = ["aiuc-1", "owasp-agentic", "owasp-llm", "mitre-atlas",
               "nist-ai-rmf", "csa-aicm", "owasp-ai-exchange", "eu-gpai-cop", "cosai"]


def build():
    return html.Div([
        html.H2("Pair Lookup"),
        html.P("Enter a source and target control to get a calibrated tier + rationale."),
        html.Label("Source framework"),
        dcc.Dropdown(id="t1-src-fw", options=[{"label": f, "value": f} for f in _FRAMEWORKS], value="aiuc-1"),
        html.Label("Source text"),
        dcc.Textarea(id="t1-src", style={"width": "100%", "height": 80}),
        html.Label("Target framework"),
        dcc.Dropdown(id="t1-tgt-fw", options=[{"label": f, "value": f} for f in _FRAMEWORKS], value="owasp-agentic"),
        html.Label("Target text"),
        dcc.Textarea(id="t1-tgt", style={"width": "100%", "height": 80}),
        html.Button("Map", id="t1-go", n_clicks=0),
        html.Div(id="t1-result", role="status"),
    ], id="tab-lookup")


def _lookup(n_clicks, source_text, target_text, source_fw, target_fw, client):
    if not n_clicks:
        return no_update, ""
    out = client.predict({
        "source_text": source_text or "",
        "target_text": target_text or "",
        "source_framework": source_fw,
        "target_framework": target_fw,
    })
    summary = (f"Tier: {out['tier']} "
               f"(Direct={out['tier_probs']['Direct']:.2f}, "
               f"Related={out['tier_probs']['Related']:.2f}) "
               f"· conformal set: {out['conformal_set']}")
    return out, summary


def register_callbacks(app):
    client = SidecarClient()

    @app.callback(
        Output("pair-store", "data"),
        Output("t1-result", "children"),
        Input("t1-go", "n_clicks"),
        State("t1-src", "value"), State("t1-tgt", "value"),
        State("t1-src-fw", "value"), State("t1-tgt-fw", "value"),
        prevent_initial_call=True,
    )
    def _cb(n, s, t, sf, tf):
        return _lookup(n, s, t, sf, tf, client)
```

Run: `pytest app/tests/test_tab1_lookup.py -v` → 1 passed.

- [ ] **Step 3: Commit**

```bash
git add app/dash_app/tabs/tab1_lookup.py app/tests/test_tab1_lookup.py
git commit -m "plan7: tab1 pair lookup callback"
```

### Task D2: Tab 2 Cytoscape densified graph

**Files:**
- Modify: `app/dash_app/tabs/tab2_graph.py`
- Create: `app/tests/test_tab2_graph.py`

- [ ] **Step 1: Failing test**

```python
# app/tests/test_tab2_graph.py
from app.dash_app.tabs import tab2_graph


def test_elements_built_from_fake_graph():
    graph = {
        "nodes": [{"id": "aiuc-1:C-1.2", "framework": "aiuc-1", "label": "MFA"},
                   {"id": "owasp-agentic:ASI-03", "framework": "owasp-agentic", "label": "Identity"}],
        "edges": [{"source": "aiuc-1:C-1.2", "target": "owasp-agentic:ASI-03", "tier": "Direct"}],
    }
    elements = tab2_graph._build_elements(graph)
    ids = {e["data"]["id"] for e in elements if "id" in e["data"]}
    assert ids == {"aiuc-1:C-1.2", "owasp-agentic:ASI-03",
                   "aiuc-1:C-1.2->owasp-agentic:ASI-03"}
```

- [ ] **Step 2: Implement Tab 2**

```python
"""Tab 2 — Cytoscape densified graph view."""
from __future__ import annotations
import json
from pathlib import Path
from dash import html
import dash_cytoscape as cyto


_STYLESHEET = [
    {"selector": "node", "style": {"label": "data(label)", "font-size": 10}},
    {"selector": "edge[tier = 'Direct']", "style": {"line-color": "#2b8a3e"}},
    {"selector": "edge[tier = 'Related']", "style": {"line-color": "#f59f00"}},
]


def _load_graph() -> dict:
    path = Path("data/plan5/densified_graph.json")
    if not path.exists():
        return {"nodes": [], "edges": []}
    return json.loads(path.read_text())


def _build_elements(graph: dict) -> list[dict]:
    elements: list[dict] = []
    for n in graph["nodes"]:
        elements.append({"data": {
            "id": n["id"], "label": n.get("label", n["id"]),
            "framework": n.get("framework", ""),
        }})
    for e in graph["edges"]:
        eid = f"{e['source']}->{e['target']}"
        elements.append({"data": {
            "id": eid, "source": e["source"], "target": e["target"],
            "tier": e.get("tier", "Related"),
        }})
    return elements


def build():
    graph = _load_graph()
    return html.Div([
        html.H2("Densified Crosswalk Graph"),
        html.P("Click an edge to load the pair in Tab 3."),
        cyto.Cytoscape(
            id="t2-cyto",
            elements=_build_elements(graph),
            layout={"name": "cose"},
            stylesheet=_STYLESHEET,
            style={"width": "100%", "height": "600px"},
        ),
    ], id="tab-graph")
```

Run: `pytest app/tests/test_tab2_graph.py -v` → 1 passed.

- [ ] **Step 3: Commit**

```bash
git add app/dash_app/tabs/tab2_graph.py app/tests/test_tab2_graph.py
git commit -m "plan7: tab2 cytoscape densified graph"
```

### Task D3: Cross-tab wiring — click in Tab 2 pushes pair into `pair-store`

**Files:**
- Modify: `app/dash_app/tabs/tab2_graph.py`
- Modify: `app/dash_app/app.py`

- [ ] **Step 1: Add click callback**

Append to `tab2_graph.py`:
```python
from dash import Input, Output


def register_callbacks(app):
    @app.callback(
        Output("pair-store", "data", allow_duplicate=True),
        Input("t2-cyto", "tapEdgeData"),
        prevent_initial_call=True,
    )
    def _on_edge_tap(edge_data):
        if not edge_data:
            return {}
        return {"pair_key": edge_data["id"], "source": edge_data["source"],
                "target": edge_data["target"], "tier": edge_data.get("tier")}
```

And register in `app.py`:
```python
    from app.dash_app.tabs import tab2_graph
    tab2_graph.register_callbacks(app)
```

- [ ] **Step 2: Commit**

```bash
git add app/dash_app/tabs/tab2_graph.py app/dash_app/app.py
git commit -m "plan7: tab2 tap edge pushes pair into shared store"
```

---

## Phase E — Tab 3 Detail + Tab 4 Matrix

### Task E1: Tab 3 per-pair confidence + conformal set + rationale

**Files:**
- Modify: `app/dash_app/tabs/tab3_detail.py`

- [ ] **Step 1: Implement Tab 3 (tested indirectly via sidecar integration)**

```python
"""Tab 3 — per-pair confidence + tier set + rationale."""
from __future__ import annotations
from dash import dcc, html, Input, Output, no_update
import plotly.graph_objects as go
from app.dash_app.api_client import SidecarClient


def build():
    return html.Div([
        html.H2("Pair Detail"),
        html.Div(id="t3-summary", role="status"),
        dcc.Graph(id="t3-probs"),
        dcc.Graph(id="t3-shap"),
        html.Div(id="t3-rationale"),
    ], id="tab-detail")


def _probs_figure(tier_probs: dict) -> go.Figure:
    fig = go.Figure(go.Bar(x=list(tier_probs.keys()), y=list(tier_probs.values())))
    fig.update_layout(title="Tier probability", yaxis_range=[0, 1])
    return fig


def _shap_figure(top_features: list[dict]) -> go.Figure:
    names = [f["name"] for f in top_features]
    vals = [f["shap"] for f in top_features]
    fig = go.Figure(go.Bar(x=vals, y=names, orientation="h"))
    fig.update_layout(title="Top-k SHAP contributions")
    return fig


def register_callbacks(app):
    client = SidecarClient()

    @app.callback(
        Output("t3-summary", "children"),
        Output("t3-probs", "figure"),
        Output("t3-shap", "figure"),
        Output("t3-rationale", "children"),
        Input("pair-store", "data"),
        prevent_initial_call=True,
    )
    def _render(pair):
        if not pair or "source" not in pair:
            return no_update, no_update, no_update, no_update
        src = pair.get("source_text") or pair.get("source", "")
        tgt = pair.get("target_text") or pair.get("target", "")
        payload = {"source_text": src, "target_text": tgt,
                   "source_framework": "aiuc-1", "target_framework": "owasp-agentic"}
        pred = client.predict(payload)
        expl = client.explain({**payload, "top_k": 5})
        summary = f"Conformal set: {pred['conformal_set']} (coverage={pred['conformal_coverage']:.2f})"
        rationale = html.Pre(f"Rationale code: {pred['rationale_code']}")
        return summary, _probs_figure(pred["tier_probs"]), _shap_figure(expl["top_features"]), rationale
```

- [ ] **Step 2: Commit**

```bash
git add app/dash_app/tabs/tab3_detail.py
git commit -m "plan7: tab3 per-pair confidence + shap + rationale"
```

### Task E2: Tab 4 per-framework coverage heatmap over 12 pairs

**Files:**
- Modify: `app/dash_app/tabs/tab4_matrix.py`
- Create: `app/tests/test_tab4_matrix.py`

- [ ] **Step 1: Failing test**

```python
# app/tests/test_tab4_matrix.py
from app.dash_app.tabs import tab4_matrix


def test_matrix_covers_twelve_pairs():
    coverage = {f"pair_{i}": {"total": 100, "covered": 80} for i in range(12)}
    fig = tab4_matrix._build_heatmap(coverage)
    assert fig.data[0].z is not None
    # one cell per pair
    assert sum(len(row) for row in fig.data[0].z) == 12
```

- [ ] **Step 2: Implement Tab 4**

```python
"""Tab 4 — per-framework coverage heatmap (12 framework pairs)."""
from __future__ import annotations
import json
from pathlib import Path
from dash import dcc, html
import plotly.express as px


def _load_coverage() -> dict:
    path = Path("data/plan5/coverage_matrix.json")
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _build_heatmap(coverage: dict):
    pairs = sorted(coverage.keys())
    values = [coverage[p]["covered"] / max(coverage[p]["total"], 1) for p in pairs]
    # Arrange as 3x4 grid; falls back to 1-D if fewer pairs
    ncols = 4
    rows = [values[i:i + ncols] for i in range(0, len(values), ncols)]
    labels = [pairs[i:i + ncols] for i in range(0, len(pairs), ncols)]
    fig = px.imshow(
        rows,
        x=labels[0] if labels else None,
        zmin=0, zmax=1,
        color_continuous_scale="Viridis",
        labels={"color": "coverage"},
    )
    fig.update_layout(title="Per-framework-pair coverage (12 pairs)")
    return fig


def build():
    fig = _build_heatmap(_load_coverage() or {f"pair_{i}": {"total": 1, "covered": 0} for i in range(12)})
    return html.Div([
        html.H2("Coverage Matrix"),
        html.P("Fraction of source nodes with ≥1 mapped target per framework pair."),
        dcc.Graph(figure=fig),
    ], id="tab-matrix")
```

Run: `pytest app/tests/test_tab4_matrix.py -v` → 1 passed.

- [ ] **Step 3: Commit**

```bash
git add app/dash_app/tabs/tab4_matrix.py app/tests/test_tab4_matrix.py
git commit -m "plan7: tab4 coverage heatmap"
```

---

## Phase F — Tab 5 Ablations + Tab 6 Feedback

### Task F1: Tab 5 reads Plan 6 `ablations.json`

**Files:**
- Modify: `app/dash_app/tabs/tab5_ablations.py`
- Create: `app/tests/test_tab5_ablations.py`

- [ ] **Step 1: Failing test**

```python
# app/tests/test_tab5_ablations.py
import json
from pathlib import Path
from app.dash_app.tabs import tab5_ablations


def test_renders_bars_from_json(tmp_path: Path, monkeypatch):
    payload = {"variants": [
        {"name": "full", "recall_at_3": 0.78, "p_at_80": 0.82},
        {"name": "no_gat", "recall_at_3": 0.74, "p_at_80": 0.79},
        {"name": "no_disagreement_loss", "recall_at_3": 0.77, "p_at_80": 0.80},
    ]}
    p = tmp_path / "ablations.json"
    p.write_text(json.dumps(payload))
    monkeypatch.setattr(tab5_ablations, "_ABLATIONS_PATH", p)
    fig = tab5_ablations._build_figure()
    assert any("full" in str(t.x) for t in fig.data)
```

- [ ] **Step 2: Implement Tab 5**

```python
"""Tab 5 — ablation comparison bar chart from Plan 6 ablations.json."""
from __future__ import annotations
import json
from pathlib import Path
from dash import dcc, html
import plotly.graph_objects as go

_ABLATIONS_PATH = Path("data/plan6/ablations.json")


def _load() -> dict:
    if not _ABLATIONS_PATH.exists():
        return {"variants": []}
    return json.loads(_ABLATIONS_PATH.read_text())


def _build_figure() -> go.Figure:
    data = _load()
    variants = data.get("variants", [])
    names = [v["name"] for v in variants]
    r3 = [v.get("recall_at_3", 0.0) for v in variants]
    p80 = [v.get("p_at_80", 0.0) for v in variants]
    fig = go.Figure()
    fig.add_bar(name="Recall@3", x=names, y=r3)
    fig.add_bar(name="P@80% coverage", x=names, y=p80)
    fig.update_layout(barmode="group", yaxis_range=[0, 1], title="Ablation comparison")
    return fig


def build():
    return html.Div([
        html.H2("Ablations"),
        html.P("Each bar pair is a trained variant. Numbers come from data/plan6/ablations.json."),
        dcc.Graph(figure=_build_figure()),
    ], id="tab-ablations")
```

Run: `pytest app/tests/test_tab5_ablations.py -v` → 1 passed.

- [ ] **Step 3: Commit**

```bash
git add app/dash_app/tabs/tab5_ablations.py app/tests/test_tab5_ablations.py
git commit -m "plan7: tab5 ablations from plan6 json"
```

### Task F2: Tab 6 feedback form → sidecar POST → SQLite

**Files:**
- Modify: `app/dash_app/tabs/tab6_feedback.py`

- [ ] **Step 1: Implement Tab 6**

```python
"""Tab 6 — feedback form."""
from __future__ import annotations
from dash import dcc, html, Input, Output, State, no_update
from app.dash_app.api_client import SidecarClient


def build():
    return html.Div([
        html.H2("Feedback"),
        html.P("Help calibrate the model. Your feedback is stored locally in a SQLite file."),
        html.Label("Predicted tier"),
        dcc.Dropdown(id="t6-predicted", options=[{"label": t, "value": t} for t in ("Direct", "Related", "None")], value="Direct"),
        html.Label("Your judgment"),
        dcc.Dropdown(id="t6-user", options=[{"label": t, "value": t} for t in ("Direct", "Related", "None")], value="Direct"),
        html.Label("Comment"),
        dcc.Textarea(id="t6-comment", style={"width": "100%", "height": 80}),
        html.Button("Submit", id="t6-go", n_clicks=0),
        html.Div(id="t6-status", role="status"),
    ], id="tab-feedback")


def register_callbacks(app):
    client = SidecarClient()

    @app.callback(
        Output("t6-status", "children"),
        Input("t6-go", "n_clicks"),
        State("pair-store", "data"),
        State("t6-predicted", "value"),
        State("t6-user", "value"),
        State("t6-comment", "value"),
        prevent_initial_call=True,
    )
    def _submit(n, pair, predicted, user, comment):
        if not n or not pair:
            return no_update
        resp = client.feedback({
            "pair_key": pair.get("pair_key", "unknown"),
            "predicted_tier": predicted,
            "user_tier": user,
            "agree": predicted == user,
            "comment": comment or "",
            "session_id": "dash",
        })
        return f"Recorded feedback id={resp['id']}"
```

- [ ] **Step 2: Commit**

```bash
git add app/dash_app/tabs/tab6_feedback.py
git commit -m "plan7: tab6 feedback form"
```

---

## Phase G — HuggingFace Space Deployment

### Task G1: Dockerfile + supervisord + model card (Contract 12)

**Files:**
- Create: `app/deploy/Dockerfile`
- Create: `app/deploy/supervisord.conf`
- Create: `app/deploy/huggingface.yml`
- Create: `app/deploy/MODEL_CARD.md`
- Create: `app/deploy/RUNBOOK.md`
- Create: `app/tests/test_model_card.py`

- [ ] **Step 1: Dockerfile**

```dockerfile
# app/deploy/Dockerfile
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    SIDECAR_URL=http://127.0.0.1:8001 \
    FEEDBACK_DB=/data/feedback.sqlite \
    SCORER_BUNDLE_DIR=/opt/app/data/plan5/scorer_bundle

RUN apt-get update && apt-get install -y --no-install-recommends supervisor \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/app
COPY requirements-app.txt .
RUN pip install -r requirements-app.txt

COPY app ./app
COPY classifier ./classifier
COPY data ./data
COPY app/deploy/supervisord.conf /etc/supervisor/conf.d/app.conf

RUN mkdir -p /data
EXPOSE 7860
CMD ["supervisord", "-c", "/etc/supervisor/conf.d/app.conf", "-n"]
```

- [ ] **Step 2: supervisord**

```ini
; app/deploy/supervisord.conf
[supervisord]
nodaemon=true

[program:sidecar]
command=uvicorn app.api.main:create_app --factory --host 127.0.0.1 --port 8001
autorestart=true
stdout_logfile=/dev/stdout
stderr_logfile=/dev/stderr
stdout_logfile_maxbytes=0
stderr_logfile_maxbytes=0

[program:dash]
command=python -m app.dash_app.app
environment=PORT=7860
autorestart=true
stdout_logfile=/dev/stdout
stderr_logfile=/dev/stderr
stdout_logfile_maxbytes=0
stderr_logfile_maxbytes=0
```

Note: adjust `app/dash_app/app.py` `__main__` block to honor `PORT` env var:
```python
if __name__ == "__main__":
    import os
    create_dash_app().run(host="0.0.0.0", port=int(os.environ.get("PORT", "8050")), debug=False)
```

- [ ] **Step 3: huggingface.yml**

```yaml
# app/deploy/huggingface.yml
title: AI Security Framework Crosswalk
emoji: shield
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
license: mit
```

- [ ] **Step 4: MODEL_CARD.md — bake in spec §6 commitments (Contract 12)**

```markdown
# AI Security Framework Crosswalk — Model Card

## Intended use
Calibrated cross-framework mappings across 9 AI security and governance
frameworks (AIUC-1, CSA AICM, MITRE ATLAS, NIST AI RMF, OWASP LLM Top 10,
OWASP Agentic Top 10, OWASP AI Exchange, EU GPAI CoP, CoSAI) with formal
conformal abstention.

## Metrics
See `data/plan6/ablations.json` for the full ablation ladder. Headline
numbers from the single sacred run on `human_test_frozen` (400 pairs) are
recorded in the paper appendix and reproduced verbatim in the HF dataset
card.

## Pre-registered honesty commitments (spec §6, verbatim)

1. The sacred run is performed exactly once. No retries on frozen-400. If
   results disappoint, we reframe the paper; we do not re-tune.
2. Fresh-75 verification is reported. If fresh-75 metrics differ from
   frozen-400 by more than 10pp, the paper reports the gap and adjusts
   claims.
3. Retrieval floor is reported. If any human-test pairs are missing from
   top-20 candidate retrieval, this is reported as the upper bound on
   Recall@20.
4. Sonnet-Opus agreement is reported. The kappa between the two models is
   in the paper whether it is good news or bad.
5. Raw vs calibrated LLM label metrics are both reported in the appendix.
6. Failed ablations are reported. If the disagreement-aware loss does not
   help, we say so. If joint GAT loses to independent GAT, we say so. If
   Rung XL underperforms Rung L, we say so.
7. Budget and timeline are reported. Actual costs and wall-clock times in
   an appendix.
8. Model is released with training code, hyperparameters, wandb logs, and
   reproduction command, even if numbers are not SOTA.

## Limitations
- Trained predominantly on LLM-SME labels; inter-rater noise bounds tier
  accuracy.
- English-only.
- Conformal coverage is marginal, not per-pair conditional beyond Mondrian
  framework-pair strata.

## Reproduction
```
git clone <repo>
pip install -r requirements-classifier.txt -r requirements-app.txt
python -m app.scripts.export_onnx_int8
pytest app/tests
```
```

- [ ] **Step 5: Contract 12 enforcement test**

```python
# app/tests/test_model_card.py
from pathlib import Path
import re

CARD = Path(__file__).resolve().parents[1] / "deploy" / "MODEL_CARD.md"

COMMITMENTS = [
    "sacred run is performed exactly once",
    "Fresh-75 verification is reported",
    "Retrieval floor is reported",
    "Sonnet-Opus agreement is reported",
    "Raw vs calibrated LLM label metrics",
    "Failed ablations are reported",
    "Budget and timeline are reported",
    "Model is released",
]


def test_all_eight_commitments_present():
    text = CARD.read_text()
    missing = [c for c in COMMITMENTS if c not in text]
    assert not missing, f"missing commitments: {missing}"


def test_card_numbered_list_has_eight():
    text = CARD.read_text()
    nums = re.findall(r"^\d+\. ", text, flags=re.MULTILINE)
    assert len(nums) >= 8
```

Run: `pytest app/tests/test_model_card.py -v` → 2 passed.

- [ ] **Step 6: RUNBOOK.md**

```markdown
# Plan 7 Deploy Runbook

## Local
1. `python -m app.scripts.export_onnx_int8 --output-dir data/onnx/rung_l_int8`
2. `SCORER_BUNDLE_DIR=data/plan5/scorer_bundle uvicorn app.api.main:create_app --factory --port 8001`
3. `python -m app.dash_app.app` and visit http://127.0.0.1:8050
4. `pytest app/tests`

## HuggingFace Space
1. `export HF_TOKEN=...`
2. `python -m app.scripts.deploy_hf_space --repo-id rlambros/ai-sec-crosswalk --dir app/deploy`
3. Visit https://huggingface.co/spaces/rlambros/ai-sec-crosswalk

## Rollback
`huggingface-cli repo delete <repo-id> --type space`
```

- [ ] **Step 7: Commit**

```bash
git add app/deploy/ app/tests/test_model_card.py
git commit -m "plan7: dockerfile + model card + contract 12 test"
```

### Task G2: `deploy_hf_space.py` + runbook

**Files:**
- Create: `app/scripts/deploy_hf_space.py`

- [ ] **Step 1: Implement deploy script**

```python
"""Create or update the HuggingFace Space for the Dash app."""
from __future__ import annotations
import argparse
import os
import shutil
from pathlib import Path
from huggingface_hub import HfApi, create_repo


def deploy(repo_id: str, deploy_dir: Path, token: str | None = None) -> str:
    token = token or os.environ.get("HF_TOKEN")
    if not token:
        raise RuntimeError("HF_TOKEN not set")
    api = HfApi(token=token)
    create_repo(repo_id, repo_type="space", space_sdk="docker", exist_ok=True, token=token)
    # Verify Contract 12 before upload
    card = deploy_dir / "MODEL_CARD.md"
    text = card.read_text()
    for needle in ("sacred run is performed exactly once",
                   "Retrieval floor is reported",
                   "Failed ablations are reported"):
        if needle not in text:
            raise RuntimeError(f"Contract 12 violation — missing in MODEL_CARD.md: {needle}")
    api.upload_folder(folder_path=str(deploy_dir), repo_id=repo_id,
                      repo_type="space", commit_message="plan7 deploy")
    return f"https://huggingface.co/spaces/{repo_id}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-id", required=True)
    ap.add_argument("--dir", type=Path, default=Path("app/deploy"))
    args = ap.parse_args()
    print(deploy(args.repo_id, args.dir))


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Commit**

```bash
git add app/scripts/deploy_hf_space.py
git commit -m "plan7: hf space deploy script with contract-12 guard"
```

---

## COMP 4433 Project 2 Compliance Checklist

| Rubric item | Mapped task(s) | Evidence |
|---|---|---|
| ≥4 distinct `dcc` components | C1, D1, F2 | `dcc.Dropdown`, `dcc.Textarea`, `dcc.Input` (via Textarea), `dcc.Tabs`, `dcc.Graph`, `dcc.Store` |
| ≥1 `@app.callback` | D1, E1, F2 | Three tabs register callbacks |
| ≥3 Plotly chart types | D2, E1, E2, F1 | Cytoscape network (Tab 2), Bar (Tab 3 probs, Tab 5 ablations), Heatmap (Tab 4), horizontal bar (Tab 3 SHAP) |
| Narrative / instructional text | C1, D1, E1, E2, F1, F2 | Each tab has an `html.P` explanation |
| Explainability | B2, E1 | `/explain` SHAP top-k rendered in Tab 3 |
| Accessibility | C1, D1, F2 | `role="main"` on layout, `role="status"` on result/status divs, all inputs have `html.Label` |
| Reproducibility | A1, A2, G1 | Pinned `requirements-app.txt`, Dockerfile, runbook, `verify_hashes()` at boot |
| Deployment-ready | G1, G2 | Dockerfile + HF Space config + deploy script |
| Feedback capture | B3, F2 | SQLite-backed feedback endpoint + form |
| Honesty commitments visible to end users | G1 | Model card renders in the HF Space repo root |

---

## Lessons Carried

From Plans 1–6 that apply directly here:

1. **Contract 1 is a service-boundary test, not a decoration.** Plan 2 learned that silent stale splits corrupt label files; Plan 7 applies the same lesson at the sidecar lifespan so a running Space cannot drift from the frozen hashes.
2. **Keep Scorer internals behind a single loader.** Plan 5 reshuffled the stacker feature order twice during development. `scorer_loader.load_scorer()` is the only place Plan 7 touches the on-disk bundle, so a future reshuffle is a one-line change.
3. **TDD the transport, monkeypatch the model.** Every FastAPI test uses a `fake_scorer` fixture — we test the HTTP contract without loading the 568M cross-encoder in CI.
4. **Pre-commit the honesty claims.** Plan 1 pre-registered success thresholds in git; Plan 7 pre-registers honesty commitments in the model card and enforces them via `test_model_card.py` so a well-intentioned edit cannot silently drop a commitment.
5. **Size gates beat "it worked on my machine".** Plan 4 shipped a benchmark harness; Plan 7 reuses the pattern (`test_onnx_benchmark.py`) so the int8 bundle cannot regress past 200 MB / 500 ms p95 without a failing test.
6. **One container, two processes, supervisord.** HF Spaces only exposes a single port; splitting into two containers requires Nginx and more moving parts than a student Space warrants.

---

## Self-Review — Spec § Mapping

| Spec § | Plan 7 coverage |
|---|---|
| §4.2 Dash app stack (Dash + Cytoscape + FastAPI + SQLite + HF Space) | Phases B, C, D, F, G |
| §4.2 Tabs (6-tab structure) | C1, D1, D2, E1, E2, F1, F2 |
| §4.2 D-readiness (query logging, feedback schema, `/feedback` toggle) | B3 (store), F2 (form) — `/feedback` is live, not stubbed, because Plan 7 ships C + D in one pass |
| §4.2 ONNX int8 for HF Spaces CPU | A1, A2 |
| §4.2 COMP 4433 Project 2 compliance | Dedicated checklist above |
| §4.6 Deliverable #4 (HF Space with Dash app) | G1, G2 |
| §6 Honesty commitments baked into shipped artifact | G1 (MODEL_CARD.md), `test_model_card.py` enforcement, `deploy_hf_space.py` pre-push guard |
| Contract 1 (verify_hashes at service boundary) | B1 sidecar lifespan |
| Contract 4 (consume Plan 5 final Scorer) | A3 `scorer_loader` is the single consumer |
| Contract 12 (NEW — model card commitments) | G1 + `app/tests/test_model_card.py` + `deploy_hf_space.py` guard |

**Budget estimate:** ~$0. All tests run CPU-only on the Jetson. HF Space deploy is free-tier CPU Basic. No LLM calls, no GPU training.

**What Plan 7 explicitly does NOT do:** no model training, no label generation, no sacred run, no blog post. Those are Plans 4–6 and the writeup (future plan).
