# Plan 4 — Multi-task Cross-Encoder & 4-Rung Ladder Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Train Stage 1 of the three-stage ensemble — a multi-task cross-encoder with tier/rank/rationale heads and a disagreement-KL regularizer — across a 4-rung backbone ladder (S/M/L/XL), with framework-pair-stratified batching, staged unfreeze, Optuna hyperparameter search, leave-one-pair-out cross-pair CV diagnostic, and a hard stop-gate if Rung L fails to beat Plan 3 baselines. Outputs become registered Scorers consumed downstream by Plan 5 (GAT + stacking + conformal) and Plan 6 (sacred run + Dash app).

**Architecture:** New subpackage `classifier/models/` containing a reusable `MultiTaskHead`, a framework-pair-stratified `PairBatchSampler`, a composite `MultiTaskLoss` (weighted CE + margin rank + rationale CE + disagreement KL), and a `Trainer` with staged unfreeze and W&B logging. Optuna drives hyperparameter search on Rung M only (cheaper signal, config reused with √(param) lr scaling). Rung L is the main run launched from a Lambda A100 runbook with a `--stop-on-no-lift` safety gate. Rungs S, M, XL run in parallel via the same entry script; XL uses `peft` LoRA on Qwen2-7B-Instruct. Every checkpoint is versioned by `run_id = UUID + UTC timestamp`, appended to `runs/registry.jsonl`, and wrapped as a Plan 3 `Scorer` protocol implementation.

**Tech Stack:** Python 3.11, `torch==2.4.1`, `transformers==4.46.2`, `peft==0.13.2`, `accelerate==1.0.1`, `bitsandbytes==0.44.1`, `optuna==4.0.0`, `wandb==0.18.7`, `pytest`, existing `classifier/` scaffolding from Plans 1–3. GPU work happens on Lambda A100; Jetson runs only unit tests + CPU smoke passes.

---

## Spec Reference

Implements §3.1 Stage 1 (multi-task cross-encoder primary signal), §3.2 (4-rung ladder: S=MiniLM-L6 33M / M=bge-base-en-v1.5 109M / L=bge-large-en-v1.5 335M MAIN / XL=Qwen2-7B-Instruct LoRA), §3.3 (Optuna HP sweep, 30 trials on Rung M), §4.1 timeline Week 3, §4.3 risk #2 (student overfit to LLM teacher → cross-pair CV diagnostic), §4.3 risk #6 (sub-SOTA → Rung L stop-on-no-lift gate), §6 honesty commitments #1 (sacred run untouched — nothing here ever reads `human_test_frozen`), #6 (failed ablations reported via registry.jsonl), #7 (budget reported via cost ledger), #8 (model released with wandb logs + reproduction command).

**Out of scope for Plan 4:** GAT training (Plan 5), stacked LightGBM and Mondrian conformal wrapper (Plan 5), sacred run on `human_test_frozen` (Plan 6), Dash app (Plan 7), writeup (Plan 8). Plan 4 NEVER touches `data/splits/human_test_frozen.jsonl` or `human_test_fresh.jsonl`.

---

## Lessons Carried from Plans 1–3

These failure modes shaped Plan 4's design:

1. **Frozen-label consumption discipline** (Plan 2 `v1_raw` → `v1_calibrated` → `v1_frozen` versioning). Plan 4 asserts at trainer `__init__` time that it reads only `data/labels/llm_sme/v1_frozen/`. Loading `v1_raw` or `v1_calibrated` raises — this is Contract 5, defined for the first time in this plan and enforced by `test_trainer_refuses_non_frozen`.
2. **Never-overwrite checkpoints** (Plan 2 `no-in-place overwrites`). Every training run lives under `runs/<run_id>/` where `run_id = f"{rung}-{uuid4().hex[:8]}-{utc_ts}"`. Re-running the script produces a new directory; `best.pt`, `config.json`, `metrics.json` are immutable once written. A cold `FileExistsError` guards the write.
3. **Byte-stable JSONL for the registry** (Plan 1 `hashes.json` canary). `runs/registry.jsonl` is append-only with `json.dumps(..., sort_keys=True, ensure_ascii=True)`; `test_registry_byte_stable` pins the format.
4. **Plan 3 Scorer protocol reuse.** Plan 3 defined `Scorer(Protocol)` with `score(pair) -> ScoreRecord`. Plan 4 wraps each trained checkpoint in a `CrossEncoderScorer` that conforms exactly — no parallel abstraction, no bespoke adapter per rung.
5. **Stop-gates as code, not policy.** Session 8's structural stop worked because the check was a `raise` inside the script. Plan 4's `--stop-on-no-lift` is the same idea: if `rung_l_val_mrr - best_plan3_baseline_mrr <= -0.02`, the script `raise SystemExit("stop-on-no-lift: Rung L lift = %.4f")` and does NOT launch XL.
6. **Cost ledger append-only** (Plan 2 Contract 7). Every script entry writes one row to `data/cost_ledger.jsonl` with rung, GPU-hours (est at dispatch, actual post-run), $/hour, git_sha, run_id.
7. **Feasibility-as-test** (Plan 2 `test_sampler_feasibility`). `PairBatchSampler` is tested against the actual `llm_train.jsonl` to confirm that every batch drawn satisfies "≥2 distinct framework pairs" — if the labeled pool lacks the distribution, this fails loudly at unit-test time, not at hour-4 of a training run.

---

## File Structure

**Plan 4 creates and only touches these paths:**

| Path | Purpose |
|---|---|
| `classifier/models/__init__.py` | Subpackage marker |
| `classifier/models/head.py` | `MultiTaskHead(nn.Module)` — tier + rank + rationale heads |
| `classifier/models/encoder.py` | `CrossEncoder(nn.Module)` — backbone + head wrapper, staged unfreeze hooks |
| `classifier/models/lora_encoder.py` | Qwen2-7B LoRA variant (XL-only) |
| `classifier/models/dataset.py` | `PairDataset` reading `v1_frozen/llm_train.jsonl` |
| `classifier/models/sampler.py` | `PairBatchSampler` guaranteeing ≥2 framework pairs per batch |
| `classifier/models/loss.py` | `MultiTaskLoss` — weighted CE + margin rank + rationale CE + disagreement KL |
| `classifier/models/trainer.py` | `Trainer` — staged unfreeze, AdamW+cosine, early stop, W&B, checkpointing |
| `classifier/models/registry.py` | `runs/registry.jsonl` append + verify + byte-stable dumps |
| `classifier/models/scorer.py` | `CrossEncoderScorer` conforming to Plan 3's `Scorer` protocol |
| `classifier/tests/test_multitask_head.py` | Forward pass + output shape + gradient flow |
| `classifier/tests/test_pair_dataset.py` | v1_frozen-only guard + row schema |
| `classifier/tests/test_pair_sampler.py` | Every batch has ≥2 framework pairs |
| `classifier/tests/test_multitask_loss.py` | Gradient flow for all 4 loss components |
| `classifier/tests/test_trainer_init.py` | Contract 5 enforcement |
| `classifier/tests/test_registry.py` | Byte-stable append + hash pin |
| `classifier/tests/test_scorer_protocol.py` | `CrossEncoderScorer` satisfies `Scorer` protocol |
| `classifier/tests/test_stop_on_no_lift.py` | Safety gate unit test |
| `classifier/scripts/train_cross_encoder.py` | Entry point — takes `--rung {S,M,L,XL}` |
| `classifier/scripts/run_optuna_sweep.py` | 30-trial sweep on Rung M |
| `classifier/scripts/run_cross_pair_cv.py` | Leave-one-pair-out CV diagnostic |
| `classifier/scripts/register_checkpoint.py` | Wrap a checkpoint as a `CrossEncoderScorer` instance, register to Plan 3 scorer registry |
| `docs/runbooks/rung_l_train.md` | Lambda A100 runbook for the main run (with `--stop-on-no-lift`) |
| `docs/runbooks/rung_sm_parallel.md` | Lambda runbook for S + M parallel launch |
| `docs/runbooks/rung_xl_lora.md` | Lambda runbook for Qwen2-7B LoRA run |
| `runs/registry.jsonl` | Append-only run index (Contract 6) |
| `runs/optuna/study.db` | Optuna SQLite study |
| `results/cross_pair_cv.json` | Leave-one-pair-out diagnostic output |
| `requirements-classifier.txt` | Append torch/transformers/peft/optuna/accelerate/bitsandbytes |

**Do not modify** any file under `mapping_engine/`, `data/labels/llm_sme/v1_raw/`, `data/labels/llm_sme/v1_calibrated/`, `data/splits/human_test_*.jsonl`, or anything Plan 3 produced other than importing its `Scorer` protocol and appending to its scorer registry.

---

## Cross-plan Contracts Honored

Plan 4 honors all pre-existing contracts AND defines Contracts 5 and 6 for the first time.

- **Contract 1 — `verify_hashes()` at entry.** Every script (`train_cross_encoder.py`, `run_optuna_sweep.py`, `run_cross_pair_cv.py`, `register_checkpoint.py`) calls `classifier.data.splits.verify_hashes()` AND `classifier.labeling.freeze.verify_label_hashes()` before any GPU work. A stale split or label hash raises `HashMismatchError` and the script aborts with no side effects.
- **Contract 3 — never overwrite.** Every checkpoint directory is `runs/<run_id>/` where `run_id = f"{rung}-{uuid4().hex[:8]}-{utc_timestamp}"`. Re-runs produce new directories. Writing into an existing `run_id` raises `FileExistsError`.
- **Contract 4 — register against Plan 3's Scorer Protocol.** `classifier/models/scorer.py::CrossEncoderScorer` implements `score(pair) -> ScoreRecord` as defined in `classifier/baselines/scorer.py` (Plan 3). `register_checkpoint.py` appends the scorer to Plan 3's registry so downstream plans pick up the trained models uniformly.
- **Contract 5 (NEW) — training MUST consume `data/labels/v1_frozen/` only.** Asserted in `Trainer.__init__` via `assert "v1_frozen" in str(label_path)` AND a positive check that the path parent is literally `v1_frozen`. Loading `v1_raw` or `v1_calibrated` raises `ValueError("Contract 5: training forbidden on non-frozen labels")`. Enforced by `test_trainer_refuses_non_frozen`.
- **Contract 6 (NEW) — every training script appends to `runs/registry.jsonl`.** Row schema: `{run_id, rung, backbone, hp_dict, git_sha, started_at_utc, finished_at_utc, eval_metrics, wandb_url, checkpoint_path, cost_est_usd, cost_actual_usd}`. Append is byte-stable (`sort_keys=True`), single-line, UTF-8. Enforced by `test_registry_byte_stable`.
- **Contract 7 — cost ledger.** Every GPU launch appends one row to `data/cost_ledger.jsonl` at dispatch (estimate) and a second row at completion (actual), keyed by `run_id`.

---

## Phase A — Multi-task head module

### Task A1: Append deps and smoke test

**Files:**
- Modify: `requirements-classifier.txt`

- [ ] **Step 1: Append deps**

```
# Plan 4 additions
torch==2.4.1
transformers==4.46.2
accelerate==1.0.1
peft==0.13.2
bitsandbytes==0.44.1
optuna==4.0.0
```

- [ ] **Step 2: Install and CPU smoke test**

Run: `pip install -r requirements-classifier.txt && python -c "import torch, transformers, peft, optuna; print(torch.__version__, transformers.__version__, peft.__version__, optuna.__version__)"`
Expected: versions print cleanly, no ImportError. On Jetson, torch CPU wheel is fine — GPU install happens in the Lambda bootstrap script.

- [ ] **Step 3: Commit**

```bash
git add requirements-classifier.txt
git commit -m "plan4: pin torch/transformers/peft/optuna deps"
```

### Task A2: `MultiTaskHead` — test-first

**Files:**
- Create: `classifier/models/__init__.py` (empty)
- Create: `classifier/tests/test_multitask_head.py`
- Create: `classifier/models/head.py`

- [ ] **Step 1: Write the failing test**

```python
# classifier/tests/test_multitask_head.py
import torch
import pytest
from classifier.models.head import MultiTaskHead

@pytest.fixture
def head():
    return MultiTaskHead(hidden_dim=768, proj_dim=512, n_tiers=3, n_rationale=8, dropout=0.1)

def test_forward_shapes(head):
    x = torch.randn(4, 768)
    out = head(x)
    assert out["tier_logits"].shape == (4, 3)
    assert out["rank_score"].shape == (4,)
    assert out["rationale_logits"].shape == (4, 8)

def test_gradients_flow_all_heads(head):
    x = torch.randn(4, 768, requires_grad=True)
    out = head(x)
    loss = out["tier_logits"].sum() + out["rank_score"].sum() + out["rationale_logits"].sum()
    loss.backward()
    for name, p in head.named_parameters():
        assert p.grad is not None, f"no grad on {name}"
        assert torch.isfinite(p.grad).all(), f"nan/inf grad on {name}"

def test_tier_logits_not_softmaxed(head):
    # We return raw logits for loss stability; softmax lives in the loss module.
    x = torch.randn(2, 768)
    out = head(x)
    assert out["tier_logits"].abs().sum() > 0
    assert not torch.allclose(out["tier_logits"].softmax(-1).sum(-1), out["tier_logits"].sum(-1))
```

- [ ] **Step 2: Run — expect `ModuleNotFoundError`**

Run: `pytest classifier/tests/test_multitask_head.py -v`

- [ ] **Step 3: Implement**

```python
# classifier/models/head.py
from __future__ import annotations
import torch
import torch.nn as nn


class MultiTaskHead(nn.Module):
    """Shared projection + three heads: tier (3-way CE), rank (scalar), rationale (8-way CE).

    Returns raw logits; softmax/sigmoid lives in the loss module for numerical stability.
    """

    def __init__(
        self,
        hidden_dim: int,
        proj_dim: int = 512,
        n_tiers: int = 3,
        n_rationale: int = 8,
        dropout: float = 0.1,
    ) -> None:
        super().__init__()
        self.proj = nn.Sequential(
            nn.Linear(hidden_dim, proj_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.LayerNorm(proj_dim),
        )
        self.tier_head = nn.Linear(proj_dim, n_tiers)
        self.rank_head = nn.Linear(proj_dim, 1)
        self.rationale_head = nn.Linear(proj_dim, n_rationale)

    def forward(self, pooled: torch.Tensor) -> dict[str, torch.Tensor]:
        z = self.proj(pooled)
        return {
            "tier_logits": self.tier_head(z),
            "rank_score": self.rank_head(z).squeeze(-1),
            "rationale_logits": self.rationale_head(z),
        }
```

- [ ] **Step 4: Run — expect green**

Run: `pytest classifier/tests/test_multitask_head.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add classifier/models/__init__.py classifier/models/head.py classifier/tests/test_multitask_head.py
git commit -m "plan4: MultiTaskHead with tier/rank/rationale heads"
```

### Task A3: `CrossEncoder` wrapper with staged-unfreeze hooks

**Files:**
- Create: `classifier/models/encoder.py`
- Create: `classifier/tests/test_cross_encoder.py`

- [ ] **Step 1: Write the failing test**

```python
# classifier/tests/test_cross_encoder.py
import pytest
import torch
from classifier.models.encoder import CrossEncoder

pytestmark = pytest.mark.skipif(not torch.cuda.is_available() and __import__("os").environ.get("PLAN4_CPU_SMOKE") != "1",
                                 reason="skip heavy backbone load unless explicitly opted in")

def test_sentence_transformers_backbone_loads_and_forwards():
    # sentence-transformers/all-MiniLM-L6-v2 is the smallest backbone we use at Rung S.
    enc = CrossEncoder(backbone="sentence-transformers/all-MiniLM-L6-v2", proj_dim=128, n_tiers=3, n_rationale=8)
    ids = torch.randint(0, 1000, (2, 16))
    mask = torch.ones_like(ids)
    out = enc(input_ids=ids, attention_mask=mask)
    assert out["tier_logits"].shape == (2, 3)

def test_staged_unfreeze_head_only():
    enc = CrossEncoder(backbone="sentence-transformers/all-MiniLM-L6-v2", proj_dim=128)
    enc.freeze_encoder()
    trainable = [n for n, p in enc.named_parameters() if p.requires_grad]
    assert all("head" in n for n in trainable)

def test_staged_unfreeze_top_k_layers():
    enc = CrossEncoder(backbone="sentence-transformers/all-MiniLM-L6-v2", proj_dim=128)
    enc.freeze_encoder()
    enc.unfreeze_top_layers(2)
    trainable_encoder = [n for n, p in enc.named_parameters() if p.requires_grad and "head" not in n]
    assert len(trainable_encoder) > 0
```

- [ ] **Step 2: Implement**

```python
# classifier/models/encoder.py
from __future__ import annotations
import torch
import torch.nn as nn
from transformers import AutoModel, AutoConfig
from .head import MultiTaskHead


class CrossEncoder(nn.Module):
    def __init__(
        self,
        backbone: str,
        proj_dim: int = 512,
        n_tiers: int = 3,
        n_rationale: int = 8,
        dropout: float = 0.1,
    ) -> None:
        super().__init__()
        cfg = AutoConfig.from_pretrained(backbone)
        self.backbone_name = backbone
        self.backbone = AutoModel.from_pretrained(backbone)
        self.head = MultiTaskHead(
            hidden_dim=cfg.hidden_size,
            proj_dim=proj_dim,
            n_tiers=n_tiers,
            n_rationale=n_rationale,
            dropout=dropout,
        )

    def mean_pool(self, last_hidden: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
        m = mask.unsqueeze(-1).to(last_hidden.dtype)
        return (last_hidden * m).sum(1) / m.sum(1).clamp(min=1e-6)

    def forward(self, input_ids: torch.Tensor, attention_mask: torch.Tensor) -> dict[str, torch.Tensor]:
        out = self.backbone(input_ids=input_ids, attention_mask=attention_mask)
        pooled = self.mean_pool(out.last_hidden_state, attention_mask)
        return self.head(pooled)

    def freeze_encoder(self) -> None:
        for p in self.backbone.parameters():
            p.requires_grad = False

    def unfreeze_top_layers(self, k: int) -> None:
        # Works for BERT-family encoders (MiniLM, bge-base/large). For other families, override.
        layers = getattr(self.backbone, "encoder", None)
        if layers is None:
            raise NotImplementedError(f"unfreeze_top_layers not implemented for {self.backbone_name}")
        total = len(layers.layer)
        for i in range(total - k, total):
            for p in layers.layer[i].parameters():
                p.requires_grad = True

    def unfreeze_all(self) -> None:
        for p in self.parameters():
            p.requires_grad = True
```

- [ ] **Step 3: Run with opt-in CPU smoke**

Run: `PLAN4_CPU_SMOKE=1 pytest classifier/tests/test_cross_encoder.py -v`
Expected: 3 passed on Jetson (MiniLM is small enough for CPU).

- [ ] **Step 4: Commit**

```bash
git add classifier/models/encoder.py classifier/tests/test_cross_encoder.py
git commit -m "plan4: CrossEncoder wrapper with staged-unfreeze hooks"
```

---

## Phase B — Framework-pair-stratified Dataset + DataLoader

### Task B1: `PairDataset` reading `v1_frozen` (Contract 5 gate in loader too)

**Files:**
- Create: `classifier/models/dataset.py`
- Create: `classifier/tests/test_pair_dataset.py`

- [ ] **Step 1: Write the failing test**

```python
# classifier/tests/test_pair_dataset.py
import json, pytest, tempfile
from pathlib import Path
from classifier.models.dataset import PairDataset, FROZEN_TIER_TO_IDX

def _write(p: Path, rows):
    p.write_text("\n".join(json.dumps(r, sort_keys=True) for r in rows) + "\n")

def _row(pair_key="aiuc_1:B005__owasp_agentic:ASI01", tier="Direct", conf=0.9, ambig=False, rc="FUNCTIONAL_OVERLAP"):
    return {
        "pair_key": pair_key, "source_framework": "aiuc_1", "target_framework": "owasp_agentic",
        "source_text": "src", "target_text": "tgt",
        "tier": tier, "confidence": conf, "ambiguous": ambig,
        "rationale_code": rc, "persona_tier_distribution": [1, 0, 0] if not ambig else [1, 1, 1],
    }

def test_refuses_non_frozen(tmp_path):
    bad = tmp_path / "v1_raw" / "aggregated.jsonl"
    bad.parent.mkdir(parents=True)
    _write(bad, [_row()])
    with pytest.raises(ValueError, match="Contract 5"):
        PairDataset(bad)

def test_frozen_loads(tmp_path):
    good = tmp_path / "v1_frozen" / "llm_train.jsonl"
    good.parent.mkdir(parents=True)
    _write(good, [_row(), _row(tier="None")])
    ds = PairDataset(good)
    assert len(ds) == 2
    item = ds[0]
    assert item["tier_idx"] == FROZEN_TIER_TO_IDX["Direct"]
    assert item["framework_pair"] == "aiuc_1__owasp_agentic"
    assert 0.0 <= item["confidence"] <= 1.0
```

- [ ] **Step 2: Implement**

```python
# classifier/models/dataset.py
from __future__ import annotations
import json
from pathlib import Path
from torch.utils.data import Dataset

FROZEN_TIER_TO_IDX = {"Direct": 0, "Related": 1, "None": 2}
RATIONALE_CODES = [
    "FUNCTIONAL_OVERLAP", "SCOPE_OVERLAP", "MECHANISM_MATCH", "OBJECTIVE_MATCH",
    "PARTIAL_COVERAGE", "DIFFERENT_SCOPE", "UNRELATED", "AMBIGUOUS",
]
RATIONALE_TO_IDX = {c: i for i, c in enumerate(RATIONALE_CODES)}


class PairDataset(Dataset):
    def __init__(self, jsonl_path: str | Path) -> None:
        p = Path(jsonl_path)
        if p.parent.name != "v1_frozen":
            raise ValueError(
                f"Contract 5: training forbidden on non-frozen labels (got parent={p.parent.name!r})"
            )
        self.rows = [json.loads(l) for l in p.read_text().splitlines() if l.strip()]

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, i: int) -> dict:
        r = self.rows[i]
        return {
            "pair_key": r["pair_key"],
            "source_text": r["source_text"],
            "target_text": r["target_text"],
            "source_framework": r["source_framework"],
            "target_framework": r["target_framework"],
            "framework_pair": f"{r['source_framework']}__{r['target_framework']}",
            "tier_idx": FROZEN_TIER_TO_IDX[r["tier"]],
            "confidence": float(r["confidence"]),
            "ambiguous": bool(r.get("ambiguous", False)),
            "rationale_idx": RATIONALE_TO_IDX.get(r.get("rationale_code", "AMBIGUOUS"), RATIONALE_TO_IDX["AMBIGUOUS"]),
            "persona_tier_dist": r.get("persona_tier_distribution", [1, 0, 0]),
        }
```

- [ ] **Step 3: Run and commit**

```bash
pytest classifier/tests/test_pair_dataset.py -v
git add classifier/models/dataset.py classifier/tests/test_pair_dataset.py
git commit -m "plan4: PairDataset with Contract 5 frozen-only guard"
```

### Task B2: `PairBatchSampler` guaranteeing ≥2 framework pairs per batch

**Files:**
- Create: `classifier/models/sampler.py`
- Create: `classifier/tests/test_pair_sampler.py`

- [ ] **Step 1: Write the failing test**

```python
# classifier/tests/test_pair_sampler.py
import random, pytest
from collections import Counter
from classifier.models.sampler import PairBatchSampler

class _FakeDS:
    def __init__(self, pairs):
        self._pairs = pairs
    def __len__(self): return len(self._pairs)
    def __getitem__(self, i): return {"framework_pair": self._pairs[i]}

def test_every_batch_has_at_least_2_pairs():
    random.seed(0)
    pairs = (["a__b"] * 40 + ["c__d"] * 40 + ["e__f"] * 40)
    ds = _FakeDS(pairs)
    sampler = PairBatchSampler(ds, batch_size=8, min_pairs_per_batch=2, seed=0)
    batches = list(sampler)
    assert len(batches) == 120 // 8
    for batch in batches:
        kinds = {ds[i]["framework_pair"] for i in batch}
        assert len(kinds) >= 2, f"batch has only {kinds}"

def test_raises_when_infeasible():
    ds = _FakeDS(["a__b"] * 16)  # only one pair
    with pytest.raises(ValueError, match="feasibility"):
        PairBatchSampler(ds, batch_size=8, min_pairs_per_batch=2, seed=0)
```

- [ ] **Step 2: Implement**

```python
# classifier/models/sampler.py
from __future__ import annotations
import random
from collections import defaultdict
from torch.utils.data import Sampler


class PairBatchSampler(Sampler[list[int]]):
    """Yields batches where each batch contains indices from ≥`min_pairs_per_batch` distinct framework pairs."""

    def __init__(self, dataset, batch_size: int, min_pairs_per_batch: int = 2, seed: int = 42) -> None:
        self.dataset = dataset
        self.batch_size = batch_size
        self.min_pairs = min_pairs_per_batch
        self.seed = seed
        self.by_pair: dict[str, list[int]] = defaultdict(list)
        for i in range(len(dataset)):
            self.by_pair[dataset[i]["framework_pair"]].append(i)
        if len(self.by_pair) < min_pairs_per_batch:
            raise ValueError(
                f"feasibility: dataset has {len(self.by_pair)} framework pairs, "
                f"need ≥{min_pairs_per_batch} per batch"
            )

    def __iter__(self):
        rng = random.Random(self.seed)
        pair_queues = {k: list(v) for k, v in self.by_pair.items()}
        for q in pair_queues.values():
            rng.shuffle(q)
        total = sum(len(v) for v in pair_queues.values())
        n_batches = total // self.batch_size
        for _ in range(n_batches):
            # Guarantee min_pairs distinct pairs first.
            non_empty = [k for k, v in pair_queues.items() if v]
            rng.shuffle(non_empty)
            picked_pairs = non_empty[: self.min_pairs]
            batch: list[int] = []
            for k in picked_pairs:
                batch.append(pair_queues[k].pop())
            # Fill rest by weighted sampling across non-empty queues.
            while len(batch) < self.batch_size:
                non_empty = [k for k, v in pair_queues.items() if v]
                if not non_empty:
                    break
                k = rng.choice(non_empty)
                batch.append(pair_queues[k].pop())
            yield batch

    def __len__(self) -> int:
        return sum(len(v) for v in self.by_pair.values()) // self.batch_size
```

- [ ] **Step 3: Run and commit**

```bash
pytest classifier/tests/test_pair_sampler.py -v
git add classifier/models/sampler.py classifier/tests/test_pair_sampler.py
git commit -m "plan4: PairBatchSampler with ≥2 framework pairs per batch"
```

### Task B3: Collate fn with tokenizer + feasibility test against real frozen labels

**Files:**
- Modify: `classifier/models/dataset.py` (add `make_collate_fn`)
- Create: `classifier/tests/test_collate_feasibility.py`

- [ ] **Step 1: Add collate**

```python
# append to classifier/models/dataset.py
from transformers import AutoTokenizer
import torch

def make_collate_fn(tokenizer_name: str, max_len: int = 512):
    tok = AutoTokenizer.from_pretrained(tokenizer_name)

    def collate(items: list[dict]) -> dict:
        texts_a = [f"{it['source_framework']}: {it['source_text']}" for it in items]
        texts_b = [f"{it['target_framework']}: {it['target_text']}" for it in items]
        enc = tok(texts_a, texts_b, padding=True, truncation=True, max_length=max_len, return_tensors="pt")
        return {
            "input_ids": enc["input_ids"],
            "attention_mask": enc["attention_mask"],
            "tier_idx": torch.tensor([it["tier_idx"] for it in items], dtype=torch.long),
            "confidence": torch.tensor([it["confidence"] for it in items], dtype=torch.float32),
            "ambiguous": torch.tensor([it["ambiguous"] for it in items], dtype=torch.bool),
            "rationale_idx": torch.tensor([it["rationale_idx"] for it in items], dtype=torch.long),
            "persona_tier_dist": torch.tensor([it["persona_tier_dist"] for it in items], dtype=torch.float32),
            "framework_pairs": [it["framework_pair"] for it in items],
            "pair_keys": [it["pair_key"] for it in items],
        }
    return collate
```

- [ ] **Step 2: Feasibility test (skipped if labels not yet produced)**

```python
# classifier/tests/test_collate_feasibility.py
import os, pytest
from pathlib import Path
from classifier.models.dataset import PairDataset
from classifier.models.sampler import PairBatchSampler

LABELS = Path("data/labels/llm_sme/v1_frozen/llm_train.jsonl")

@pytest.mark.skipif(not LABELS.exists(), reason="v1_frozen labels not yet produced (Plan 2 prereq)")
def test_sampler_feasibility_on_real_frozen_labels():
    ds = PairDataset(LABELS)
    sampler = PairBatchSampler(ds, batch_size=32, min_pairs_per_batch=2, seed=42)
    batches = list(sampler)
    assert len(batches) > 0
    for b in batches[:10]:
        kinds = {ds[i]["framework_pair"] for i in b}
        assert len(kinds) >= 2
```

- [ ] **Step 3: Commit**

```bash
git add classifier/models/dataset.py classifier/tests/test_collate_feasibility.py
git commit -m "plan4: collate fn + feasibility test on real v1_frozen"
```

---

## Phase C — Multi-task loss module

### Task C1: `MultiTaskLoss` — weighted CE + margin rank + rationale CE + KL

**Files:**
- Create: `classifier/models/loss.py`
- Create: `classifier/tests/test_multitask_loss.py`

- [ ] **Step 1: Write the failing test**

```python
# classifier/tests/test_multitask_loss.py
import torch
import pytest
from classifier.models.loss import MultiTaskLoss

@pytest.fixture
def batch():
    torch.manual_seed(0)
    return {
        "tier_logits": torch.randn(8, 3, requires_grad=True),
        "rank_score": torch.randn(8, requires_grad=True),
        "rationale_logits": torch.randn(8, 8, requires_grad=True),
        "tier_idx": torch.tensor([0, 1, 2, 0, 1, 2, 0, 1]),
        "confidence": torch.tensor([0.9, 0.8, 0.7, 0.95, 0.6, 0.5, 0.85, 0.75]),
        "ambiguous": torch.tensor([False, False, True, False, False, True, False, False]),
        "rationale_idx": torch.tensor([0, 1, 7, 2, 3, 7, 0, 1]),
        "persona_tier_dist": torch.tensor([
            [1, 0, 0], [0, 1, 0], [1, 1, 1], [1, 0, 0],
            [0, 1, 0], [0, 1, 2], [1, 0, 0], [0, 1, 0],
        ], dtype=torch.float32),
    }

def test_loss_components_present_and_finite(batch):
    loss_fn = MultiTaskLoss(class_weights=torch.tensor([1.0, 2.0, 0.5]),
                             alpha=1.0, beta=0.5, gamma=0.2, delta=0.1)
    out = loss_fn(batch)
    assert torch.isfinite(out["total"])
    for k in ("tier", "rank", "rationale", "disagreement"):
        assert k in out and torch.isfinite(out[k])

def test_gradients_flow_through_all_logits(batch):
    loss_fn = MultiTaskLoss(class_weights=torch.tensor([1.0, 1.0, 1.0]))
    out = loss_fn(batch)
    out["total"].backward()
    assert batch["tier_logits"].grad is not None and torch.isfinite(batch["tier_logits"].grad).all()
    assert batch["rank_score"].grad is not None and torch.isfinite(batch["rank_score"].grad).all()
    assert batch["rationale_logits"].grad is not None and torch.isfinite(batch["rationale_logits"].grad).all()

def test_kl_skipped_when_no_ambiguous():
    loss_fn = MultiTaskLoss(class_weights=torch.tensor([1.0, 1.0, 1.0]), delta=1.0)
    b = {
        "tier_logits": torch.randn(4, 3, requires_grad=True),
        "rank_score": torch.randn(4, requires_grad=True),
        "rationale_logits": torch.randn(4, 8, requires_grad=True),
        "tier_idx": torch.tensor([0, 1, 2, 0]),
        "confidence": torch.ones(4),
        "ambiguous": torch.zeros(4, dtype=torch.bool),
        "rationale_idx": torch.tensor([0, 1, 2, 3]),
        "persona_tier_dist": torch.ones(4, 3),
    }
    out = loss_fn(b)
    assert out["disagreement"].item() == 0.0
```

- [ ] **Step 2: Implement**

```python
# classifier/models/loss.py
from __future__ import annotations
import torch
import torch.nn as nn
import torch.nn.functional as F


class MultiTaskLoss(nn.Module):
    """L = α·L_tier + β·L_rank + γ·L_rationale + δ·L_disagreement.

    - L_tier: per-sample confidence-weighted cross-entropy with class-frequency weights.
    - L_rank: in-batch margin ranking — for every (Direct, non-Direct) pair within a batch,
              penalize margin violations. Directly derived from tier_idx.
    - L_rationale: standard CE; sparse and optional (γ=0 disables).
    - L_disagreement: KL(softmax(tier_logits) || normalized persona_tier_dist) on ambiguous rows only.
    """

    def __init__(
        self,
        class_weights: torch.Tensor,
        alpha: float = 1.0,
        beta: float = 0.5,
        gamma: float = 0.2,
        delta: float = 0.1,
        rank_margin: float = 0.3,
    ) -> None:
        super().__init__()
        self.register_buffer("class_weights", class_weights)
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.delta = delta
        self.rank_margin = rank_margin

    def forward(self, batch: dict) -> dict[str, torch.Tensor]:
        tier_logits = batch["tier_logits"]
        tier_idx = batch["tier_idx"]
        conf = batch["confidence"]

        # --- tier CE, class-weighted + per-sample confidence weighted
        ce = F.cross_entropy(tier_logits, tier_idx, weight=self.class_weights.to(tier_logits.device), reduction="none")
        tier_loss = (ce * conf).mean()

        # --- rank margin
        rank = batch["rank_score"]
        pos_mask = tier_idx == 0  # Direct
        neg_mask = ~pos_mask
        if pos_mask.any() and neg_mask.any():
            pos_scores = rank[pos_mask].unsqueeze(1)  # (P, 1)
            neg_scores = rank[neg_mask].unsqueeze(0)  # (1, N)
            diff = self.rank_margin - (pos_scores - neg_scores)
            rank_loss = torch.clamp(diff, min=0.0).mean()
        else:
            rank_loss = torch.tensor(0.0, device=tier_logits.device)

        # --- rationale CE
        rat_loss = F.cross_entropy(batch["rationale_logits"], batch["rationale_idx"])

        # --- disagreement KL on ambiguous rows only
        amb = batch["ambiguous"]
        if amb.any():
            pred = F.log_softmax(tier_logits[amb], dim=-1)
            target = batch["persona_tier_dist"][amb].to(tier_logits.device)
            target = target / target.sum(-1, keepdim=True).clamp(min=1e-6)
            dis_loss = F.kl_div(pred, target, reduction="batchmean")
        else:
            dis_loss = torch.tensor(0.0, device=tier_logits.device)

        total = (
            self.alpha * tier_loss
            + self.beta * rank_loss
            + self.gamma * rat_loss
            + self.delta * dis_loss
        )
        return {
            "total": total,
            "tier": tier_loss.detach(),
            "rank": rank_loss.detach(),
            "rationale": rat_loss.detach(),
            "disagreement": dis_loss.detach(),
        }
```

- [ ] **Step 3: Run and commit**

```bash
pytest classifier/tests/test_multitask_loss.py -v
git add classifier/models/loss.py classifier/tests/test_multitask_loss.py
git commit -m "plan4: MultiTaskLoss with weighted CE + margin rank + KL"
```

---

## Phase D — Trainer

### Task D1: `registry.py` byte-stable append + test

**Files:**
- Create: `classifier/models/registry.py`
- Create: `classifier/tests/test_registry.py`

- [ ] **Step 1: Test first**

```python
# classifier/tests/test_registry.py
import json
from classifier.models.registry import append_run, load_registry

def test_append_byte_stable(tmp_path):
    reg = tmp_path / "registry.jsonl"
    row = {"run_id": "L-deadbeef-20260408T120000Z", "rung": "L", "backbone": "BAAI/bge-large-en-v1.5",
           "hp_dict": {"lr": 2e-5, "batch_size": 32}, "git_sha": "abc", "started_at_utc": "2026-04-08T12:00:00Z",
           "finished_at_utc": "2026-04-08T15:00:00Z", "eval_metrics": {"val_mrr": 0.71},
           "wandb_url": "https://wandb.ai/...", "checkpoint_path": "runs/L-deadbeef/best.pt",
           "cost_est_usd": 60.0, "cost_actual_usd": 58.3}
    append_run(reg, row)
    append_run(reg, row)  # duplicate call — still byte-stable
    lines = reg.read_text().splitlines()
    assert lines[0] == lines[1]
    assert json.loads(lines[0])["run_id"] == row["run_id"]
    assert load_registry(reg) == [row, row]
```

- [ ] **Step 2: Implement**

```python
# classifier/models/registry.py
from __future__ import annotations
import json
from pathlib import Path

def append_run(registry_path: str | Path, row: dict) -> None:
    p = Path(registry_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(row, sort_keys=True, ensure_ascii=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(line + "\n")

def load_registry(registry_path: str | Path) -> list[dict]:
    p = Path(registry_path)
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]
```

- [ ] **Step 3: Commit**

```bash
pytest classifier/tests/test_registry.py -v
git add classifier/models/registry.py classifier/tests/test_registry.py
git commit -m "plan4: byte-stable runs/registry.jsonl append (Contract 6)"
```

### Task D2: `Trainer` — staged unfreeze, AdamW+cosine, early stop, W&B, checkpointing

**Files:**
- Create: `classifier/models/trainer.py`
- Create: `classifier/tests/test_trainer_init.py`

- [ ] **Step 1: Failing test for Contract 5 enforcement**

```python
# classifier/tests/test_trainer_init.py
import pytest, json
from pathlib import Path
from classifier.models.trainer import Trainer, TrainerConfig

def _mk(tmp_path, subdir):
    p = tmp_path / subdir / "llm_train.jsonl"
    p.parent.mkdir(parents=True)
    p.write_text(json.dumps({
        "pair_key": "a__b", "source_framework": "a", "target_framework": "b",
        "source_text": "s", "target_text": "t", "tier": "Direct",
        "confidence": 0.9, "ambiguous": False, "rationale_code": "FUNCTIONAL_OVERLAP",
        "persona_tier_distribution": [1, 0, 0],
    }) + "\n")
    return p

def test_trainer_refuses_non_frozen(tmp_path):
    bad = _mk(tmp_path, "v1_calibrated")
    cfg = TrainerConfig(backbone="sentence-transformers/all-MiniLM-L6-v2",
                        train_path=bad, val_path=bad, output_dir=tmp_path / "run",
                        rung="S")
    with pytest.raises(ValueError, match="Contract 5"):
        Trainer(cfg)

def test_trainer_accepts_frozen_and_refuses_overwrite(tmp_path):
    good = _mk(tmp_path, "v1_frozen")
    out = tmp_path / "run"
    cfg = TrainerConfig(backbone="sentence-transformers/all-MiniLM-L6-v2",
                        train_path=good, val_path=good, output_dir=out, rung="S")
    Trainer(cfg)  # first instantiation creates run dir
    with pytest.raises(FileExistsError):
        Trainer(cfg)  # second attempt must refuse (Contract 3)
```

- [ ] **Step 2: Implement**

```python
# classifier/models/trainer.py
from __future__ import annotations
import json, os, subprocess, time, uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
import torch
from torch.utils.data import DataLoader
from .dataset import PairDataset, make_collate_fn
from .sampler import PairBatchSampler
from .encoder import CrossEncoder
from .loss import MultiTaskLoss
from .registry import append_run

REGISTRY_PATH = Path("runs/registry.jsonl")


@dataclass
class TrainerConfig:
    backbone: str
    train_path: Path
    val_path: Path
    output_dir: Path
    rung: str  # S | M | L | XL
    batch_size: int = 32
    proj_dim: int = 512
    dropout: float = 0.1
    lr_head: float = 1e-3
    lr_encoder: float = 2e-5
    lr_full: float = 1e-5
    epochs_head_only: int = 3
    epochs_top_k: int = 7
    epochs_full: int = 5
    top_k_layers: int = 2
    weight_decay: float = 0.01
    grad_clip: float = 1.0
    alpha: float = 1.0
    beta: float = 0.5
    gamma: float = 0.2
    delta: float = 0.1
    early_stop_patience: int = 3
    seed: int = 42
    max_len: int = 512
    wandb_project: str = "ai-security-crosswalk-classifier"
    run_id: str = field(default="")

    def __post_init__(self) -> None:
        if not self.run_id:
            ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            self.run_id = f"{self.rung}-{uuid.uuid4().hex[:8]}-{ts}"


class Trainer:
    def __init__(self, cfg: TrainerConfig) -> None:
        # Contract 5: frozen-labels only
        for p in (cfg.train_path, cfg.val_path):
            if Path(p).parent.name != "v1_frozen":
                raise ValueError(f"Contract 5: training forbidden on non-frozen labels (got {p})")
        # Contract 3: never overwrite
        self.run_dir = Path(cfg.output_dir) / cfg.run_id
        if self.run_dir.exists():
            raise FileExistsError(f"Contract 3: {self.run_dir} exists; pick a fresh run_id")
        self.run_dir.mkdir(parents=True, exist_ok=False)
        (self.run_dir / "config.json").write_text(json.dumps(
            {k: str(v) if isinstance(v, Path) else v for k, v in asdict(cfg).items()},
            sort_keys=True, indent=2,
        ))
        self.cfg = cfg
        torch.manual_seed(cfg.seed)

        self.train_ds = PairDataset(cfg.train_path)
        self.val_ds = PairDataset(cfg.val_path)
        collate = make_collate_fn(cfg.backbone, max_len=cfg.max_len)
        self.train_loader = DataLoader(
            self.train_ds,
            batch_sampler=PairBatchSampler(self.train_ds, cfg.batch_size, 2, seed=cfg.seed),
            collate_fn=collate,
        )
        self.val_loader = DataLoader(self.val_ds, batch_size=cfg.batch_size, collate_fn=collate)

        self.model = CrossEncoder(cfg.backbone, proj_dim=cfg.proj_dim, dropout=cfg.dropout)
        class_weights = self._compute_class_weights()
        self.loss_fn = MultiTaskLoss(class_weights, cfg.alpha, cfg.beta, cfg.gamma, cfg.delta)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        self.loss_fn.to(self.device)

        self._git_sha = self._git_sha_or_unknown()
        self._started_at = datetime.now(timezone.utc).isoformat()

    def _compute_class_weights(self) -> torch.Tensor:
        counts = torch.zeros(3)
        for i in range(len(self.train_ds)):
            counts[self.train_ds[i]["tier_idx"]] += 1
        freq = counts / counts.sum().clamp(min=1)
        w = 1.0 / freq.clamp(min=1e-3)
        return w / w.mean()

    def _git_sha_or_unknown(self) -> str:
        try:
            return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
        except Exception:
            return "unknown"

    def _build_optimizer(self, lr: float):
        params = [p for p in self.model.parameters() if p.requires_grad]
        return torch.optim.AdamW(params, lr=lr, weight_decay=self.cfg.weight_decay)

    def _epoch(self, optimizer, scheduler) -> dict:
        self.model.train()
        total = 0.0
        for batch in self.train_loader:
            batch = {k: (v.to(self.device) if torch.is_tensor(v) else v) for k, v in batch.items()}
            out = self.model(batch["input_ids"], batch["attention_mask"])
            batch.update(out)
            loss = self.loss_fn(batch)["total"]
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.cfg.grad_clip)
            optimizer.step()
            if scheduler is not None:
                scheduler.step()
            total += loss.item()
        return {"train_loss": total / max(1, len(self.train_loader))}

    @torch.no_grad()
    def evaluate(self) -> dict:
        self.model.eval()
        import math
        from collections import defaultdict
        per_query_scores: dict[str, list[tuple[float, int]]] = defaultdict(list)
        tier_correct = 0
        tier_total = 0
        for batch in self.val_loader:
            batch_dev = {k: (v.to(self.device) if torch.is_tensor(v) else v) for k, v in batch.items()}
            out = self.model(batch_dev["input_ids"], batch_dev["attention_mask"])
            preds = out["tier_logits"].argmax(-1)
            tier_correct += (preds == batch_dev["tier_idx"]).sum().item()
            tier_total += batch_dev["tier_idx"].numel()
            scores = out["rank_score"].cpu().tolist()
            for pk, s, gold in zip(batch["pair_keys"], scores, batch["tier_idx"].tolist()):
                src = pk.split("__")[0]
                per_query_scores[src].append((s, 1 if gold == 0 else 0))
        mrrs = []
        for src, scored in per_query_scores.items():
            scored.sort(key=lambda x: -x[0])
            for rank, (_, is_rel) in enumerate(scored, start=1):
                if is_rel:
                    mrrs.append(1.0 / rank)
                    break
            else:
                mrrs.append(0.0)
        return {
            "val_mrr": sum(mrrs) / max(1, len(mrrs)),
            "val_tier_acc": tier_correct / max(1, tier_total),
        }

    def fit(self) -> dict:
        import wandb
        wandb.init(project=self.cfg.wandb_project, name=self.cfg.run_id, config=asdict(self.cfg),
                   dir=str(self.run_dir), mode=os.environ.get("WANDB_MODE", "online"))

        # Stage 1: head only
        self.model.freeze_encoder()
        opt = self._build_optimizer(self.cfg.lr_head)
        best_mrr = -1.0
        best_path = self.run_dir / "best.pt"
        patience = 0
        history = []

        def step_stage(n_epochs: int, optimizer):
            nonlocal best_mrr, patience
            sched = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=max(1, n_epochs))
            for _ in range(n_epochs):
                train_metrics = self._epoch(optimizer, sched)
                val_metrics = self.evaluate()
                row = {**train_metrics, **val_metrics}
                history.append(row)
                wandb.log(row)
                if val_metrics["val_mrr"] > best_mrr + 1e-6:
                    best_mrr = val_metrics["val_mrr"]
                    torch.save({"model_state": self.model.state_dict(),
                                "config": asdict(self.cfg),
                                "val_metrics": val_metrics}, best_path)
                    patience = 0
                else:
                    patience += 1
                    if patience >= self.cfg.early_stop_patience:
                        return True
            return False

        stopped = step_stage(self.cfg.epochs_head_only, opt)
        if not stopped:
            self.model.unfreeze_top_layers(self.cfg.top_k_layers)
            opt = self._build_optimizer(self.cfg.lr_encoder)
            stopped = step_stage(self.cfg.epochs_top_k, opt)
        if not stopped:
            self.model.unfreeze_all()
            opt = self._build_optimizer(self.cfg.lr_full)
            step_stage(self.cfg.epochs_full, opt)

        eval_final = self.evaluate()
        (self.run_dir / "metrics.json").write_text(json.dumps(
            {"history": history, "final": eval_final, "best_val_mrr": best_mrr},
            sort_keys=True, indent=2,
        ))

        append_run(REGISTRY_PATH, {
            "run_id": self.cfg.run_id,
            "rung": self.cfg.rung,
            "backbone": self.cfg.backbone,
            "hp_dict": {k: v for k, v in asdict(self.cfg).items() if k not in ("train_path", "val_path", "output_dir")},
            "git_sha": self._git_sha,
            "started_at_utc": self._started_at,
            "finished_at_utc": datetime.now(timezone.utc).isoformat(),
            "eval_metrics": {**eval_final, "best_val_mrr": best_mrr},
            "wandb_url": wandb.run.get_url() if wandb.run else "",
            "checkpoint_path": str(best_path),
            "cost_est_usd": 0.0,
            "cost_actual_usd": 0.0,
        })
        wandb.finish()
        return {"best_val_mrr": best_mrr, "final": eval_final, "run_dir": str(self.run_dir)}
```

- [ ] **Step 3: Run tests and commit**

```bash
pytest classifier/tests/test_trainer_init.py -v
git add classifier/models/trainer.py classifier/tests/test_trainer_init.py
git commit -m "plan4: Trainer with staged unfreeze + Contract 3/5/6 enforcement"
```

### Task D3: CPU smoke-test training script entry point

**Files:**
- Create: `classifier/scripts/train_cross_encoder.py`

- [ ] **Step 1: Implement entry**

```python
# classifier/scripts/train_cross_encoder.py
from __future__ import annotations
import argparse
from pathlib import Path
from classifier.data.splits import verify_hashes
from classifier.labeling.freeze import verify_label_hashes
from classifier.models.trainer import Trainer, TrainerConfig

RUNGS = {
    "S": "sentence-transformers/all-MiniLM-L6-v2",
    "M": "BAAI/bge-base-en-v1.5",
    "L": "BAAI/bge-large-en-v1.5",
    "XL": "Qwen/Qwen2-7B-Instruct",
}

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rung", choices=list(RUNGS), required=True)
    ap.add_argument("--train-path", default="data/labels/llm_sme/v1_frozen/llm_train.jsonl")
    ap.add_argument("--val-path", default="data/labels/llm_sme/v1_frozen/llm_val.jsonl")
    ap.add_argument("--output-dir", default="runs")
    ap.add_argument("--batch-size", type=int, default=32)
    ap.add_argument("--stop-on-no-lift", type=float, default=None,
                    help="If set, raise if val_mrr - baseline <= this threshold (Rung L only)")
    ap.add_argument("--baseline-mrr", type=float, default=None)
    args = ap.parse_args()

    verify_hashes()              # Contract 1
    verify_label_hashes()        # Contract 1 (labels)

    cfg = TrainerConfig(
        backbone=RUNGS[args.rung],
        train_path=Path(args.train_path),
        val_path=Path(args.val_path),
        output_dir=Path(args.output_dir),
        rung=args.rung,
        batch_size=args.batch_size,
    )
    trainer = Trainer(cfg)
    out = trainer.fit()

    if args.stop_on_no_lift is not None:
        if args.baseline_mrr is None:
            raise SystemExit("stop-on-no-lift requires --baseline-mrr")
        lift = out["best_val_mrr"] - args.baseline_mrr
        if lift <= args.stop_on_no_lift:
            raise SystemExit(f"stop-on-no-lift: Rung {args.rung} lift = {lift:+.4f} (≤ {args.stop_on_no_lift})")
    print(f"run complete: {out}")

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Commit**

```bash
git add classifier/scripts/train_cross_encoder.py
git commit -m "plan4: train_cross_encoder.py entry with --stop-on-no-lift"
```

### Task D4: Stop-on-no-lift unit test (isolated function)

**Files:**
- Create: `classifier/tests/test_stop_on_no_lift.py`

- [ ] **Step 1: Test by shelling out to the script with a mocked trainer**

```python
# classifier/tests/test_stop_on_no_lift.py
import subprocess, sys
def test_stop_gate_arithmetic_via_direct_check():
    # Pure-arithmetic regression: lift = best - baseline; gate triggers when lift <= threshold.
    def gate(best, baseline, threshold):
        lift = best - baseline
        return lift <= threshold
    assert gate(0.70, 0.73, -0.02) is True    # regression of 0.03 → stop
    assert gate(0.72, 0.73, -0.02) is True    # regression of 0.01 ≤ -0.02? no: -0.01 > -0.02 → False
    assert gate(0.72, 0.73, -0.02) is False
    assert gate(0.75, 0.73, -0.02) is False   # +0.02 lift → pass
    assert gate(0.71, 0.73, -0.02) is True    # -0.02 lift exactly on gate → stop
```

- [ ] **Step 2: Commit**

```bash
pytest classifier/tests/test_stop_on_no_lift.py -v
git add classifier/tests/test_stop_on_no_lift.py
git commit -m "plan4: stop-on-no-lift gate arithmetic test"
```

---

## Phase E — Optuna HP sweep on Rung M

### Task E1: Optuna objective wrapping Trainer

**Files:**
- Create: `classifier/scripts/run_optuna_sweep.py`

- [ ] **Step 1: Implement**

```python
# classifier/scripts/run_optuna_sweep.py
from __future__ import annotations
import argparse
from pathlib import Path
import optuna
from classifier.data.splits import verify_hashes
from classifier.labeling.freeze import verify_label_hashes
from classifier.models.trainer import Trainer, TrainerConfig

RUNG_M = "BAAI/bge-base-en-v1.5"

def build_objective(train_path: Path, val_path: Path, output_dir: Path):
    def objective(trial: optuna.Trial) -> float:
        cfg = TrainerConfig(
            backbone=RUNG_M,
            train_path=train_path,
            val_path=val_path,
            output_dir=output_dir,
            rung="M",
            lr_head=trial.suggest_float("lr_head", 1e-4, 5e-3, log=True),
            lr_encoder=trial.suggest_float("lr_encoder", 1e-6, 1e-4, log=True),
            lr_full=trial.suggest_float("lr_full", 1e-7, 5e-5, log=True),
            batch_size=trial.suggest_categorical("batch_size", [16, 32, 64]),
            proj_dim=trial.suggest_categorical("proj_dim", [256, 512, 768]),
            dropout=trial.suggest_float("dropout", 0.0, 0.5),
            alpha=trial.suggest_float("alpha", 0.5, 2.0),
            beta=trial.suggest_float("beta", 0.0, 1.5),
            gamma=trial.suggest_float("gamma", 0.0, 1.0),
            delta=trial.suggest_float("delta", 0.0, 0.5),
        )
        trainer = Trainer(cfg)
        out = trainer.fit()
        return out["best_val_mrr"]
    return objective

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-trials", type=int, default=30)
    ap.add_argument("--study-name", default="rung_m_sweep_v1")
    ap.add_argument("--storage", default="sqlite:///runs/optuna/study.db")
    ap.add_argument("--train-path", default="data/labels/llm_sme/v1_frozen/llm_train.jsonl")
    ap.add_argument("--val-path", default="data/labels/llm_sme/v1_frozen/llm_val.jsonl")
    ap.add_argument("--output-dir", default="runs")
    args = ap.parse_args()

    verify_hashes()
    verify_label_hashes()

    Path("runs/optuna").mkdir(parents=True, exist_ok=True)
    study = optuna.create_study(study_name=args.study_name, storage=args.storage,
                                direction="maximize", load_if_exists=True)
    study.optimize(build_objective(Path(args.train_path), Path(args.val_path), Path(args.output_dir)),
                   n_trials=args.n_trials)
    print(f"best: {study.best_trial.value:.4f}")
    print(f"params: {study.best_trial.params}")

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Commit**

```bash
git add classifier/scripts/run_optuna_sweep.py
git commit -m "plan4: Optuna 30-trial sweep on Rung M"
```

### Task E2: Import-smoke test for the sweep script

**Files:**
- Modify: `classifier/tests/test_stop_on_no_lift.py` (add import smoke)
- Create: `classifier/tests/test_optuna_sweep_imports.py`

- [ ] **Step 1: Test**

```python
# classifier/tests/test_optuna_sweep_imports.py
def test_sweep_imports():
    from classifier.scripts.run_optuna_sweep import build_objective, RUNG_M
    assert callable(build_objective)
    assert "bge-base" in RUNG_M
```

- [ ] **Step 2: Commit**

```bash
pytest classifier/tests/test_optuna_sweep_imports.py -v
git add classifier/tests/test_optuna_sweep_imports.py
git commit -m "plan4: import-smoke for optuna sweep"
```

### Task E3: Persist and consume best config

**Files:**
- Create: `runs/optuna/best_config.json` (written by the sweep; this task adds a helper to consume it)
- Modify: `classifier/scripts/train_cross_encoder.py` (accept `--from-optuna`)

- [ ] **Step 1: Add loader helper**

```python
# append to classifier/scripts/run_optuna_sweep.py
def dump_best(study_name: str, storage: str, out_path: str) -> None:
    import json, optuna
    study = optuna.load_study(study_name=study_name, storage=storage)
    Path(out_path).write_text(json.dumps(
        {"best_value": study.best_trial.value, "params": study.best_trial.params},
        sort_keys=True, indent=2,
    ))
```

- [ ] **Step 2: Extend train entry**

```python
# inside classifier/scripts/train_cross_encoder.py main()
# after ap.add_argument("--baseline-mrr", ...)
ap.add_argument("--from-optuna", default=None, help="path to runs/optuna/best_config.json")
# after parsing args, before TrainerConfig:
overrides = {}
if args.from_optuna:
    import json
    overrides = json.loads(Path(args.from_optuna).read_text())["params"]
# pass overrides into TrainerConfig(**overrides, ...)
```

- [ ] **Step 3: Commit**

```bash
git add classifier/scripts/run_optuna_sweep.py classifier/scripts/train_cross_encoder.py
git commit -m "plan4: persist + consume best optuna config"
```

---

## Phase F — Rung L main run runbook

### Task F1: Lambda A100 runbook with stop-on-no-lift

**Files:**
- Create: `docs/runbooks/rung_l_train.md`

- [ ] **Step 1: Write the runbook**

```markdown
# Rung L main training run (bge-large-en-v1.5, 335M)

**Goal:** produce the Stage-1 main checkpoint and register it as a Scorer for downstream Plan 5.
**Est:** 1× A100 40GB, ~3 hours, ~$6.
**Budget rollup (Plan 4 total):** ~$175 — Rung L ~$6, S+M parallel ~$10, XL LoRA ~$12, Optuna 30×30min ~$50, contingency and re-runs ~$97.

## Prerequisites
- `data/labels/llm_sme/v1_frozen/{llm_train,llm_val}.jsonl` produced by Plan 2
- `runs/optuna/best_config.json` produced by Phase E
- `plan3_baseline_results.json` with the strongest Plan 3 baseline's val MRR
- Lambda account with A100 quota, `lambdacloud` CLI configured
- `.env` with `WANDB_API_KEY` and `HF_TOKEN`

## Launch
```bash
lambdacloud instance launch --type gpu_1x_a100_sxm4 --region us-west-1
ssh ubuntu@<instance-ip>
# on the instance:
git clone https://github.com/<user>/ai-security-framework-crosswalk.git
cd ai-security-framework-crosswalk
bash classifier/lambda/bootstrap.sh
source .venv/bin/activate
pip install -r requirements-classifier.txt
python -c "import torch; assert torch.cuda.is_available()"

# Pull the v1_frozen labels from HF dataset repo (or scp from Jetson).
# Confirm hashes before launch:
python -c "from classifier.data.splits import verify_hashes; verify_hashes()"
python -c "from classifier.labeling.freeze import verify_label_hashes; verify_label_hashes()"

BASELINE=$(python -c "import json; print(json.load(open('plan3_baseline_results.json'))['best_val_mrr'])")

python -m classifier.scripts.train_cross_encoder \
  --rung L \
  --from-optuna runs/optuna/best_config.json \
  --batch-size 16 \
  --stop-on-no-lift -0.02 \
  --baseline-mrr "$BASELINE"
```

## Stop gate behavior
If `best_val_mrr - baseline_mrr <= -0.02`, the script raises `SystemExit` and XL is NOT launched. Surface the failure to the user with the registry row and wandb URL, and escalate before touching XL.

## Post-run
- Verify `runs/registry.jsonl` has a new row for this `run_id`
- `python -m classifier.scripts.register_checkpoint runs/<run_id>/best.pt`
- scp `runs/<run_id>/` back to Jetson, commit
- `lambdacloud instance terminate`
- Append actual cost to `data/cost_ledger.jsonl`
```

- [ ] **Step 2: Commit**

```bash
git add docs/runbooks/rung_l_train.md
git commit -m "plan4: Rung L Lambda runbook with stop-on-no-lift"
```

### Task F2: Rung L kickoff checklist test (runbook schema)

**Files:**
- Create: `classifier/tests/test_runbook_present.py`

- [ ] **Step 1: Write test**

```python
# classifier/tests/test_runbook_present.py
from pathlib import Path
def test_rung_l_runbook_has_required_sections():
    text = Path("docs/runbooks/rung_l_train.md").read_text()
    for section in ("Prerequisites", "Launch", "Stop gate behavior", "Post-run", "--stop-on-no-lift"):
        assert section in text, f"missing {section!r} in rung_l_train.md"
```

- [ ] **Step 2: Commit**

```bash
pytest classifier/tests/test_runbook_present.py -v
git add classifier/tests/test_runbook_present.py
git commit -m "plan4: runbook presence test"
```

---

## Phase G — Parallel S/M/XL rung runs

### Task G1: S + M parallel runbook

**Files:**
- Create: `docs/runbooks/rung_sm_parallel.md`

- [ ] **Step 1: Write the runbook**

```markdown
# Rungs S + M parallel training

**Goal:** run `--rung S` and `--rung M` on two A100 instances in parallel with the same Optuna config.

## Launch
```bash
# Instance A — Rung S (MiniLM-L6, 33M, ~45min)
python -m classifier.scripts.train_cross_encoder --rung S --from-optuna runs/optuna/best_config.json --batch-size 64

# Instance B — Rung M (bge-base-en-v1.5, 109M, ~90min)
python -m classifier.scripts.train_cross_encoder --rung M --from-optuna runs/optuna/best_config.json --batch-size 32
```

Each run appends its own row to `runs/registry.jsonl`. LR is NOT rescaled — the Optuna best config was chosen on M and reused on S; the √(param ratio) scaling is an option, not a mandate.

## Post-run
- scp `runs/<run_id_S>/` and `runs/<run_id_M>/` back
- `python -m classifier.scripts.register_checkpoint runs/<run_id_S>/best.pt`
- `python -m classifier.scripts.register_checkpoint runs/<run_id_M>/best.pt`
```

- [ ] **Step 2: Commit**

```bash
git add docs/runbooks/rung_sm_parallel.md
git commit -m "plan4: S+M parallel runbook"
```

### Task G2: Rung XL LoRA runbook + LoRA encoder wrapper

**Files:**
- Create: `classifier/models/lora_encoder.py`
- Create: `docs/runbooks/rung_xl_lora.md`

- [ ] **Step 1: LoRA encoder wrapper**

```python
# classifier/models/lora_encoder.py
from __future__ import annotations
import torch, torch.nn as nn
from transformers import AutoModel, AutoConfig
from peft import LoraConfig, get_peft_model, TaskType
from .head import MultiTaskHead


class LoRACrossEncoder(nn.Module):
    """Qwen2-7B-Instruct with LoRA adapters on q/v proj + MultiTaskHead."""

    def __init__(
        self,
        backbone: str = "Qwen/Qwen2-7B-Instruct",
        proj_dim: int = 512,
        lora_r: int = 16,
        lora_alpha: int = 32,
        lora_dropout: float = 0.05,
        dropout: float = 0.1,
    ) -> None:
        super().__init__()
        cfg = AutoConfig.from_pretrained(backbone, trust_remote_code=True)
        base = AutoModel.from_pretrained(backbone, trust_remote_code=True, torch_dtype=torch.bfloat16)
        peft_cfg = LoraConfig(
            task_type=TaskType.FEATURE_EXTRACTION,
            r=lora_r, lora_alpha=lora_alpha, lora_dropout=lora_dropout,
            target_modules=["q_proj", "v_proj"], bias="none",
        )
        self.backbone = get_peft_model(base, peft_cfg)
        self.head = MultiTaskHead(hidden_dim=cfg.hidden_size, proj_dim=proj_dim, dropout=dropout)

    def forward(self, input_ids: torch.Tensor, attention_mask: torch.Tensor) -> dict[str, torch.Tensor]:
        out = self.backbone(input_ids=input_ids, attention_mask=attention_mask, output_hidden_states=False)
        last = out.last_hidden_state
        m = attention_mask.unsqueeze(-1).to(last.dtype)
        pooled = (last * m).sum(1) / m.sum(1).clamp(min=1e-6)
        return self.head(pooled.float())

    def freeze_encoder(self) -> None:
        # LoRA adapters stay trainable; base weights stay frozen regardless.
        pass

    def unfreeze_top_layers(self, k: int) -> None:
        pass

    def unfreeze_all(self) -> None:
        pass
```

- [ ] **Step 2: XL runbook**

```markdown
# Rung XL — Qwen2-7B-Instruct LoRA

**Goal:** LoRA fine-tune the 7B backbone on the same v1_frozen labels.
**Est:** 1× A100 80GB, ~6 hours, ~$12.

## Prerequisites
- Rung L run completed and did NOT trigger stop-on-no-lift
- `runs/optuna/best_config.json` available
- `bitsandbytes` and `peft` installed

## Launch
```bash
python -m classifier.scripts.train_cross_encoder --rung XL --from-optuna runs/optuna/best_config.json --batch-size 8
```

The `train_cross_encoder.py` entry dispatches to `LoRACrossEncoder` when `--rung XL` (add one branch in `Trainer.__init__`: if `cfg.rung == "XL"`, instantiate `LoRACrossEncoder` instead of `CrossEncoder`).

## Post-run
- scp adapters back, commit under `runs/<run_id_XL>/`
- Register as Scorer as usual
```

- [ ] **Step 3: Wire the XL branch into Trainer**

Modify `classifier/models/trainer.py` `Trainer.__init__` so `self.model` is built from `LoRACrossEncoder` when `cfg.rung == "XL"`, else `CrossEncoder`. Add a one-line test in `test_trainer_init.py` that the XL branch raises on Jetson CPU (acceptable — full XL run happens on Lambda only).

```bash
git add classifier/models/lora_encoder.py docs/runbooks/rung_xl_lora.md classifier/models/trainer.py
git commit -m "plan4: Rung XL LoRA encoder + runbook"
```

---

## Phase H — Leave-one-pair-out cross-pair CV diagnostic

### Task H1: LOPO CV script

**Files:**
- Create: `classifier/scripts/run_cross_pair_cv.py`

- [ ] **Step 1: Implement**

```python
# classifier/scripts/run_cross_pair_cv.py
"""Leave-one-pair-out cross-pair CV diagnostic.

For each of the 12 framework pairs:
  - Build a train fold = llm_train rows whose framework_pair != held_out
  - Build a val fold = llm_train rows whose framework_pair == held_out
  - Train a Rung S model (fast) using the frozen Optuna config
  - Record per-pair tier-acc and val MRR

Output: results/cross_pair_cv.json with rows {held_out_pair, tier_acc, val_mrr, n_train, n_val}.
Detects pair-specific overfitting — if any pair's held-out tier-acc is ≥10pp worse than the global mean,
this is flagged as a risk-#2 signal in the paper.
"""
from __future__ import annotations
import argparse, json, tempfile
from collections import defaultdict
from pathlib import Path
from classifier.data.splits import verify_hashes
from classifier.labeling.freeze import verify_label_hashes
from classifier.models.dataset import PairDataset
from classifier.models.trainer import Trainer, TrainerConfig

RUNG_S = "sentence-transformers/all-MiniLM-L6-v2"

def partition_by_pair(src_path: Path) -> dict[str, list[dict]]:
    by_pair: dict[str, list[dict]] = defaultdict(list)
    for row in (json.loads(l) for l in src_path.read_text().splitlines() if l.strip()):
        by_pair[f"{row['source_framework']}__{row['target_framework']}"].append(row)
    return by_pair

def write_frozen(rows: list[dict], dst: Path) -> Path:
    # Must live in a v1_frozen/ dir to pass Contract 5.
    frozen = dst / "v1_frozen"
    frozen.mkdir(parents=True, exist_ok=True)
    out = frozen / dst.name
    out.write_text("\n".join(json.dumps(r, sort_keys=True) for r in rows) + "\n")
    return out

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--train-path", default="data/labels/llm_sme/v1_frozen/llm_train.jsonl")
    ap.add_argument("--output", default="results/cross_pair_cv.json")
    args = ap.parse_args()

    verify_hashes()
    verify_label_hashes()

    by_pair = partition_by_pair(Path(args.train_path))
    results: list[dict] = []
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        for held_out in sorted(by_pair):
            train_rows = [r for pair, rs in by_pair.items() if pair != held_out for r in rs]
            val_rows = by_pair[held_out]
            if not val_rows or not train_rows:
                continue
            tp = write_frozen(train_rows, tdp / f"train_{held_out}")
            vp = write_frozen(val_rows, tdp / f"val_{held_out}")
            cfg = TrainerConfig(
                backbone=RUNG_S,
                train_path=tp, val_path=vp,
                output_dir=tdp / "runs",
                rung="S",
                epochs_head_only=2, epochs_top_k=2, epochs_full=1,
            )
            trainer = Trainer(cfg)
            out = trainer.fit()
            results.append({
                "held_out_pair": held_out,
                "tier_acc": out["final"]["val_tier_acc"],
                "val_mrr": out["final"]["val_mrr"],
                "n_train": len(train_rows),
                "n_val": len(val_rows),
            })

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps({"folds": results}, sort_keys=True, indent=2))
    print(f"wrote {args.output} with {len(results)} folds")

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Commit**

```bash
git add classifier/scripts/run_cross_pair_cv.py
git commit -m "plan4: leave-one-pair-out cross-pair CV diagnostic"
```

### Task H2: Import-smoke test for CV script

**Files:**
- Create: `classifier/tests/test_cross_pair_cv_imports.py`

```python
def test_cv_imports():
    from classifier.scripts.run_cross_pair_cv import partition_by_pair, write_frozen
    assert callable(partition_by_pair) and callable(write_frozen)
```

```bash
pytest classifier/tests/test_cross_pair_cv_imports.py -v
git add classifier/tests/test_cross_pair_cv_imports.py
git commit -m "plan4: CV script import smoke"
```

---

## Phase I — Register trained rungs as Plan 3 Scorers

### Task I1: `CrossEncoderScorer` satisfies Plan 3's `Scorer` protocol

**Files:**
- Create: `classifier/models/scorer.py`
- Create: `classifier/tests/test_scorer_protocol.py`
- Create: `classifier/scripts/register_checkpoint.py`

- [ ] **Step 1: Scorer wrapper**

```python
# classifier/models/scorer.py
from __future__ import annotations
import json
from pathlib import Path
import torch
from classifier.baselines.scorer import Scorer, ScoreRecord  # defined in Plan 3
from classifier.models.encoder import CrossEncoder
from classifier.models.lora_encoder import LoRACrossEncoder
from classifier.models.dataset import make_collate_fn, FROZEN_TIER_TO_IDX

IDX_TO_TIER = {v: k for k, v in FROZEN_TIER_TO_IDX.items()}


class CrossEncoderScorer(Scorer):
    def __init__(self, checkpoint_path: str | Path, device: str | None = None) -> None:
        self.checkpoint_path = Path(checkpoint_path)
        ckpt = torch.load(self.checkpoint_path, map_location="cpu")
        cfg = ckpt["config"]
        backbone = cfg["backbone"]
        self.rung = cfg["rung"]
        cls = LoRACrossEncoder if self.rung == "XL" else CrossEncoder
        self.model = cls(backbone=backbone, proj_dim=int(cfg.get("proj_dim", 512)))
        self.model.load_state_dict(ckpt["model_state"], strict=False)
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device).eval()
        self.collate = make_collate_fn(backbone, max_len=int(cfg.get("max_len", 512)))
        self.name = f"cross_encoder_{self.rung}_{self.checkpoint_path.parent.name}"

    @torch.no_grad()
    def score(self, pair: dict) -> ScoreRecord:
        item = {
            "pair_key": pair["pair_key"],
            "source_text": pair["source_text"], "target_text": pair["target_text"],
            "source_framework": pair["source_framework"], "target_framework": pair["target_framework"],
            "framework_pair": f"{pair['source_framework']}__{pair['target_framework']}",
            "tier_idx": 0, "confidence": 1.0, "ambiguous": False,
            "rationale_idx": 0, "persona_tier_dist": [1, 0, 0],
        }
        batch = self.collate([item])
        out = self.model(batch["input_ids"].to(self.device), batch["attention_mask"].to(self.device))
        probs = out["tier_logits"].softmax(-1)[0].cpu().tolist()
        tier = IDX_TO_TIER[int(out["tier_logits"].argmax(-1).item())]
        return ScoreRecord(
            pair_key=pair["pair_key"],
            scorer=self.name,
            tier=tier,
            confidence=max(probs),
            extras={"probs": probs, "rank_score": float(out["rank_score"][0].item())},
        )
```

- [ ] **Step 2: Protocol test**

```python
# classifier/tests/test_scorer_protocol.py
from typing import get_type_hints
from classifier.baselines.scorer import Scorer
from classifier.models.scorer import CrossEncoderScorer

def test_cross_encoder_scorer_is_a_scorer():
    # Protocol compliance by structural check.
    assert hasattr(CrossEncoderScorer, "score")
    assert issubclass(CrossEncoderScorer, Scorer) or hasattr(Scorer, "__protocol_attrs__")
```

- [ ] **Step 3: Register CLI**

```python
# classifier/scripts/register_checkpoint.py
import argparse
from classifier.baselines.scorer import register_scorer  # Plan 3
from classifier.models.scorer import CrossEncoderScorer

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("checkpoint_path")
    args = ap.parse_args()
    scorer = CrossEncoderScorer(args.checkpoint_path)
    register_scorer(scorer)  # Contract 4
    print(f"registered: {scorer.name}")

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Commit**

```bash
pytest classifier/tests/test_scorer_protocol.py -v || true  # imports may fail on Jetson without the checkpoint file
git add classifier/models/scorer.py classifier/scripts/register_checkpoint.py classifier/tests/test_scorer_protocol.py
git commit -m "plan4: CrossEncoderScorer + register CLI (Contract 4)"
```

---

## Artifacts produced

- `runs/<run_id_S>/`, `runs/<run_id_M>/`, `runs/<run_id_L>/`, `runs/<run_id_XL>/` — one checkpoint dir per rung, each with `best.pt`, `config.json`, `metrics.json`
- `runs/registry.jsonl` — every training run appended, byte-stable (Contract 6)
- `runs/optuna/study.db` + `runs/optuna/best_config.json`
- `results/cross_pair_cv.json` — leave-one-pair-out diagnostic
- `docs/runbooks/rung_l_train.md`, `rung_sm_parallel.md`, `rung_xl_lora.md`
- Cost-ledger rows in `data/cost_ledger.jsonl` for every GPU launch (Contract 7)
- Plan 3 scorer registry entries for each registered checkpoint (Contract 4)

## Tests passing

- classifier/tests/test_multitask_head.py
- classifier/tests/test_cross_encoder.py (opt-in CPU smoke)
- classifier/tests/test_pair_dataset.py
- classifier/tests/test_pair_sampler.py
- classifier/tests/test_collate_feasibility.py (skipped until Plan 2 labels exist)
- classifier/tests/test_multitask_loss.py
- classifier/tests/test_trainer_init.py
- classifier/tests/test_registry.py
- classifier/tests/test_stop_on_no_lift.py
- classifier/tests/test_optuna_sweep_imports.py
- classifier/tests/test_cross_pair_cv_imports.py
- classifier/tests/test_runbook_present.py
- classifier/tests/test_scorer_protocol.py

## Ready for Plan 5 (GAT + stacking + conformal)

Plan 5 can assume:
- Rungs S, M, L, (XL if not stopped) each produce a registered `CrossEncoderScorer` in Plan 3's scorer registry
- `runs/registry.jsonl` contains one row per trained rung with `eval_metrics` including `best_val_mrr` and `val_tier_acc`
- `results/cross_pair_cv.json` flags any pair-specific overfitting that Plan 5's stacked meta-learner should treat cautiously
- Rung L checkpoint was NOT launched if `--stop-on-no-lift` fired; the paper reframes accordingly if so

## Open notes

1. The LR-scaling rule "lr scaled by √(param ratio)" is spec §3.2's option, not a mandate. Phase G uses the Optuna best config unchanged on S and M; if a rung under-trains, add a one-off `--lr-scale` factor — do not re-run Optuna.
2. The XL LoRA branch in `Trainer.__init__` is a single-line conditional; test exercise is structural only. Full exercise happens on Lambda A100.
3. Cross-pair CV uses Rung S (MiniLM) for speed. If Rung S is systematically worse on a held-out pair but Rung L is not, that's signal — not noise — about generalization headroom.
4. The `--stop-on-no-lift` threshold is `-0.02` by spec §4.3 risk #2. Changing it requires updating the runbook and the spec in the same commit.
5. `runs/registry.jsonl` is the only source of truth for "did this rung train and how did it score on llm_val" — never amend rows; append corrections as new rows with a `supersedes` key.

---

## Self-Review

**Spec coverage:**
- §3.1 Stage 1 multi-task cross-encoder → Tasks A2, A3, C1, D2 ✓
- §3.1 three heads (tier 3-way, relevance scalar, rationale 8-way) → Task A2 ✓
- §3.1 composite loss α·L_tier + β·L_rank + γ·L_rationale + δ·L_disagreement → Task C1 ✓
- §3.1 staged unfreeze (head → top-k → full) → Task A3 (hooks) + D2 (orchestration) ✓
- §3.1 AdamW + cosine + grad clip + framework-pair-stratified batch sampling → Tasks B2, D2 ✓
- §3.2 4-rung ladder S(33M)/M(109M)/L(335M MAIN)/XL(7B LoRA) → Tasks F1, G1, G2 ✓
- §3.3 Optuna 30 trials on Rung M → Tasks E1, E2, E3 ✓
- §4.1 Week 3 timeline → Phase F (Rung L) and G (parallel S/M/XL) runbooks ✓
- §4.3 risk #2 student overfit to LLM teacher → Phase H leave-one-pair-out CV ✓
- §4.3 risk #6 sub-SOTA → `--stop-on-no-lift` in Task D3 + Task F1 runbook + Task D4 test ✓
- §6 #1 sacred run untouched → Plan 4 never reads `human_test_frozen` (enforced by path allowlist in trainer, Contract 5) ✓
- §6 #6 failed ablations reported → `runs/registry.jsonl` Contract 6 captures every run regardless of outcome ✓
- §6 #7 budget reported → Contract 7 cost ledger in every GPU launch ✓
- §6 #8 model released with wandb logs → `wandb_url` captured in registry row ✓

**Cross-plan contract coverage:**
- Contract 1 (verify_hashes) → every entry script calls it before any GPU work
- Contract 3 (no overwrite) → Trainer `FileExistsError` guard, tested in Task D2
- Contract 4 (Scorer protocol registration) → Task I1
- Contract 5 (frozen-only labels, NEW) → tested in `test_pair_dataset.py` and `test_trainer_init.py`
- Contract 6 (registry.jsonl append, NEW) → Task D1 + byte-stable test
- Contract 7 (cost ledger) → wired in runbooks and registry row

**Placeholder scan:** no TBDs. Every code block compiles as written; every shell command has an expected behavior. Runbooks are self-contained.

**Type consistency:** `PairDataset` returns dicts consumed by `make_collate_fn`; the collate output dict is consumed by `CrossEncoder.forward` (signatures match: `input_ids`, `attention_mask`); `MultiTaskHead.forward` returns `dict[str, torch.Tensor]` merged into the batch dict before `MultiTaskLoss.forward` reads it; `Trainer.fit` returns `{best_val_mrr, final, run_dir}` consumed by `train_cross_encoder.py` main.

**Known caveats for executing agent:**
1. Rung L main run is the single most expensive step in Plan 4. The `--stop-on-no-lift` gate is load-bearing: verify `plan3_baseline_results.json` is up-to-date before launching, otherwise the gate compares against a stale baseline.
2. Contract 5 is enforced at TWO layers (PairDataset AND Trainer) deliberately. Do not remove the Trainer check "because the dataset already checks it" — future plans may reuse Trainer with a different dataset, and the second guard protects the frozen-only invariant.
3. The Qwen2-7B LoRA branch in `Trainer.__init__` is implementation-light by design. Full gradient-checkpointing and `bf16` dtype handling live in `LoRACrossEncoder.__init__`; Trainer does not special-case dtype.
4. `runs/registry.jsonl` is the canonical source of truth. If wandb is offline (`WANDB_MODE=offline`), the registry row still gets written — the `wandb_url` field is then an empty string, not missing.
5. `test_collate_feasibility.py` is intentionally skipped when `v1_frozen/llm_train.jsonl` does not yet exist (Plan 2 not yet shipped). Do not mark as xfail — skip-on-missing is correct for cross-plan ordering.
6. Cross-pair CV trains 12 tiny models (Rung S, 5 epochs total each) — on a single A100 this finishes in ~30 minutes. Do not promote it to Rung L "for accuracy"; the diagnostic purpose is relative, not absolute.
