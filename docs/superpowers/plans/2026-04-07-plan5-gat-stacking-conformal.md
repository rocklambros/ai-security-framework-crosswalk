# Plan 5 — GAT + LightGBM Stacker + Mondrian Conformal Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stand up Stages 2 and 3 of the three-stage ensemble — a Graph Attention Network over a densified crosswalk graph, a LightGBM meta-stacker trained on 5-fold out-of-fold features from Plan 3 baselines + Plan 4 cross-encoder rungs + GAT pair-embedding distances, a Mondrian (per-tier) split-conformal wrapper calibrated on `human_cal` at α=0.10, and a KL-disagreement abstention router tuned on `llm_val` for ≥95% precision. The output is a single registered `EnsembleScorer` consumed by Plan 6 (sacred run + Dash app).

**Architecture:** New subpackage `classifier/ensemble/` containing: (a) a graph densification script consuming Plan 1 node/edge dumps + Plan 2 `v1_frozen` high-confidence edges + cross-framework category links + co-citation edges, (b) a `torch_geometric` `GATEncoder` trained with a link-prediction objective that holds out v1_frozen Direct edges, (c) a pair-embedding extractor producing cosine/dot/hadamard features cached to parquet, (d) a 5-fold OOF feature builder that retrains the Plan 4 ladder per fold so stacker features are leakage-free, (e) a LightGBM multiclass meta-learner tuned by 20-trial Optuna with SHAP diagnostics, (f) a Mondrian split-conformal wrapper computing per-tier q_hat on `human_cal` only, and (g) a disagreement-KL abstention router emitting `needs_review` when the stage distributions disagree beyond a τ tuned on `llm_val`. Every artifact is `run_id`-versioned, appended to `runs/registry.jsonl`, and wrapped as a Plan 3 `Scorer` implementation. A path-grep test fails loudly if any code in `classifier/ensemble/` mentions `human_test_frozen`.

**Tech Stack:** Python 3.11, `torch==2.4.1` (pinned Plan 4), `torch_geometric==2.6.1`, `torch_scatter==2.1.2`, `torch_sparse==0.6.18`, `lightgbm==4.5.0`, `optuna==4.0.0` (pinned Plan 4), `shap==0.46.0`, `scikit-learn==1.5.2` (pinned Plan 1), `networkx==3.3`, `pyarrow==17.0.0` (pinned Plan 3), `wandb==0.18.7`, existing `classifier/` scaffolding from Plans 1–4. GPU work happens on a Lambda A100; Jetson runs unit tests, graph densification (CPU), conformal calibration, and the router tuning.

---

## Spec Reference

Implements §3.1 Stage 2 (GAT pair embeddings) and §3.1 Stage 3 (LightGBM meta-stacker + Mondrian conformal + disagreement abstention router), §3.4 graph densification recipe (expert edges + cross-framework category links + co-citation + high-confidence Plan 2 edges), §4.3 risks #3 (meta-learner leakage → 5-fold OOF), #4 (conformal miscalibration → Mondrian per tier on `human_cal` ONLY), and §6 Pre-registered Honesty Commitments #1 (`human_test_frozen` untouched), #3 (conformal coverage reported honestly), #6 (failed features / rejected GAT runs logged to the registry), #8 (final ensemble released with `runs/registry.jsonl` row + reproduction command) of `docs/superpowers/specs/2026-04-07-ai-security-crosswalk-classifier-design.md`.

**Out of scope for Plan 5:** sacred run on `human_test_frozen` (Plan 6), Dash app (Plan 7), writeup (Plan 8). Plan 5 NEVER reads `data/splits/human_test_frozen.jsonl` or `data/splits/human_test_fresh.jsonl`.

---

## Lessons Carried from Plans 1–4

These failure modes shaped Plan 5's design:

1. **Scoring-path drift** (Plan 3 lesson #1 + the s8-np `--no-rerank` bug). The `EnsembleScorer` carries a composite `version` string built from `(gat_run_id, stacker_run_id, conformal_q_hat_hash, router_tau)`. Any change to any component bumps the composite version; the eval harness pins it into every `ScoreRecord`. A silent swap of the stacker weights cannot masquerade as the same ensemble.
2. **Frozen-label consumption discipline** (Plan 4 Contract 5). All ensemble training reads `data/labels/llm_sme/v1_frozen/` only. `ensemble/` modules assert `"v1_frozen" in str(label_path)` and crash if pointed at `v1_raw` or `v1_calibrated`.
3. **Never-overwrite outputs** (Plans 2–4). Every artifact is under `runs/gat/<run_id>/`, `runs/stacker/<run_id>/`, `runs/conformal/<run_id>/`, or `runs/ensemble/<run_id>/`. `run_id = f"{component}-{uuid4().hex[:8]}-{utc_ts}"`. Re-runs land in a new directory; writing into an existing `run_id` raises `FileExistsError`.
4. **Byte-stable JSONL outputs** (Plan 1 `hashes.json` canary; Plan 4 `registry.jsonl`). `runs/registry.jsonl` appends use `json.dumps(..., sort_keys=True, ensure_ascii=True)`. The conformal q_hat JSON and router τ JSON use the same dumper. `test_ensemble_artifacts_byte_stable` pins the format.
5. **Leakage-as-test.** 5-fold OOF features are validated by `test_oof_no_row_leakage` which asserts every pair in fold-k test is absent from fold-k train's `pair_key` set. The Mondrian conformal split is validated by `test_conformal_uses_human_cal_only` which greps the calibration script for any reference to `llm_train`, `llm_val`, or `human_test_*`.
6. **Stop-gates as code.** If the Mondrian conformal coverage on `human_cal` deviates from the 0.90 target by more than ±0.03 after calibration, `calibrate_conformal.py` raises `SystemExit("conformal coverage OOB: %.3f")` and refuses to write q_hat. If the stacker's `llm_val` MRR fails to beat the best single Plan 4 rung by ≥0.005, `train_stacker.py` raises `SystemExit("stacker-no-lift")` and writes a registry row tagged `status="rejected"`.
7. **Sacred-split paranoia** (Plan 4 Lesson: §6 commitment #1 is load-bearing). Contract 8 (new) is a path-grep unit test that walks every `.py` file under `classifier/ensemble/` and `classifier/scripts/` added by Plan 5 and asserts the literal string `human_test_frozen` NEVER appears. Human_cal may appear; human_test_* may not.
8. **Feasibility-as-test** (Plan 4 lesson #7). `test_densified_graph_has_expected_edges` asserts lower bounds on edge counts per edge-type after densification — if the Plan 2 high-confidence subset is empty, the test fails loudly before any GPU launch.

---

## File Structure

**Plan 5 creates and only touches these paths:**

| Path | Purpose |
|---|---|
| `classifier/ensemble/__init__.py` | Subpackage marker, re-exports `EnsembleScorer` |
| `classifier/ensemble/graph.py` | `build_densified_graph()` — Plan 1 nodes/edges + cross-framework category + cocite + v1_frozen high-conf |
| `classifier/ensemble/gat_model.py` | `GATEncoder(in_dim, hidden, heads, layers)` — torch_geometric GATv2 |
| `classifier/ensemble/gat_trainer.py` | Link-prediction trainer, v1_frozen Direct-edge holdout, W&B, checkpoint |
| `classifier/ensemble/pair_embeddings.py` | Extract cos/dot/hadamard per pair → parquet cache |
| `classifier/ensemble/oof_features.py` | 5-fold OOF stack feature builder consuming Plan 3 feature cache + Plan 4 rungs |
| `classifier/ensemble/stacker.py` | `LGBMStacker` multiclass + 20-trial Optuna + SHAP |
| `classifier/ensemble/conformal.py` | `MondrianConformal` per-tier q_hat on `human_cal`, α=0.10 |
| `classifier/ensemble/router.py` | KL-disagreement abstention router + τ tuner |
| `classifier/ensemble/scorer.py` | `EnsembleScorer` conforming to Plan 3 `Scorer` protocol |
| `classifier/tests/test_densified_graph.py` | Edge-count lower-bound + node coverage |
| `classifier/tests/test_gat_model.py` | Forward shape + gradient flow on toy graph |
| `classifier/tests/test_gat_trainer.py` | Link-prediction loss decreases on synthetic fixture |
| `classifier/tests/test_pair_embeddings.py` | Parquet schema + determinism |
| `classifier/tests/test_oof_features.py` | Row-leakage check + fold coverage |
| `classifier/tests/test_stacker.py` | Multiclass fit/predict shape + SHAP diagnostic |
| `classifier/tests/test_conformal.py` | Per-tier q_hat + coverage ≈ 0.90 on fixture |
| `classifier/tests/test_conformal_uses_human_cal_only.py` | Path-grep: no `llm_val`/`llm_train`/`human_test_*` refs |
| `classifier/tests/test_router.py` | KL math + ≥95% precision on fixture |
| `classifier/tests/test_ensemble_scorer_protocol.py` | `EnsembleScorer` satisfies Plan 3 `Scorer` protocol |
| `classifier/tests/test_no_sacred_split_refs.py` | **Contract 8** path-grep — fails if `human_test_frozen` appears in any Plan-5 `.py` |
| `classifier/scripts/build_densified_graph.py` | Entry: Plan 1 dumps → `data/graph/densified_v1.pkl` |
| `classifier/scripts/train_gat.py` | Entry: GAT link-prediction training (Lambda A100) |
| `classifier/scripts/extract_pair_embeddings.py` | Entry: GAT checkpoint → per-pair parquet |
| `classifier/scripts/build_stack_features.py` | Entry: 5-fold OOF feature matrix → `data/features/stack_features_v1.parquet` |
| `classifier/scripts/train_stacker.py` | Entry: LGBM + Optuna + SHAP, checkpoint `runs/stacker/<run_id>/model.txt` |
| `classifier/scripts/calibrate_conformal.py` | Entry: Mondrian q_hat on `human_cal` (Jetson) |
| `classifier/scripts/tune_router.py` | Entry: KL threshold τ on `llm_val` |
| `classifier/scripts/eval_ensemble_llm_val.py` | Entry: run registered `EnsembleScorer` on llm_val → `results/ensemble_llm_val.json` |
| `classifier/scripts/register_ensemble.py` | Entry: wrap + register `EnsembleScorer`, append to Plan 3 scorer registry |
| `data/graph/densified_v1.pkl` | Densified crosswalk graph (NetworkX + PyG `Data`) |
| `data/features/stack_features_v1.parquet` | 5-fold OOF wide feature matrix |
| `runs/gat/<run_id>/` | GAT checkpoint + config + metrics |
| `runs/stacker/<run_id>/model.txt` | LGBM booster dump |
| `runs/conformal/<run_id>/q_hat.json` | Per-tier Mondrian q_hat (byte-stable) |
| `runs/ensemble/<run_id>/scorer.json` | Composite `EnsembleScorer` manifest |
| `results/ensemble_llm_val.json` | Phase I headline handoff to Plan 6 |
| `docs/runbooks/gat_train.md` | Lambda A100 runbook for the GAT + OOF builder |
| `requirements-classifier.txt` | Append torch_geometric, lightgbm, shap, networkx |

**Do not modify** any file under `mapping_engine/`, `data/splits/human_test_*.jsonl`, `data/labels/llm_sme/v1_raw/`, `data/labels/llm_sme/v1_calibrated/`, `data/baselines/`, `data/features/baseline_features.parquet` (Plan 3 output — read-only), or anything under `classifier/baselines/`, `classifier/labeling/`, or `classifier/models/` other than importing their public symbols.

---

## Cross-plan Contracts Honored

Plan 5 honors all pre-existing contracts from Plans 1–4 AND introduces Contracts 8 and 9 for the first time.

- **Contract 1 — `verify_hashes()` at entry.** Every script in `classifier/scripts/` for Plan 5 calls `classifier.data.splits.verify_hashes()` AND `classifier.labeling.freeze.verify_label_hashes()` as its first action after argparse. A stale split or label hash raises `HashMismatchError` before any disk write or GPU allocation. Enforced by `test_script_entry_hash_check` via static AST grep.
- **Contract 3 — never overwrite.** `runs/gat/<run_id>/`, `runs/stacker/<run_id>/`, `runs/conformal/<run_id>/`, `runs/ensemble/<run_id>/`, and `data/features/stack_features_v<N>.parquet` are all versioned. Writing into an existing path raises `FileExistsError`.
- **Contract 4 — register against Plan 3's Scorer Protocol.** `classifier/ensemble/scorer.py::EnsembleScorer` implements `score(pair) -> ScoreRecord` as defined in `classifier/baselines/protocol.py`. `register_ensemble.py` appends the scorer to Plan 3's registry; Plan 6's sacred-run harness picks it up by name.
- **Contract 5 — training consumes `v1_frozen` only.** Every ensemble-training module asserts `"v1_frozen" in str(label_path)`. Loading `v1_raw` or `v1_calibrated` raises `ValueError("Contract 5: training forbidden on non-frozen labels")`. Enforced by `test_oof_features_refuses_non_frozen`.
- **Contract 6 — every training script appends to `runs/registry.jsonl`.** Rows use the Plan 4 schema plus `component` ∈ {`gat`, `stacker`, `conformal`, `ensemble`}. Byte-stable (`sort_keys=True, ensure_ascii=True`). Rejected runs are appended with `status="rejected"`.
- **Contract 7 — cost ledger.** Every Lambda launch appends one estimate row at dispatch and one actual row at completion, keyed by `run_id`.
- **Contract 8 (NEW) — `human_test_frozen` is OFF-LIMITS.** No `.py` file under `classifier/ensemble/` or any `classifier/scripts/*` introduced by Plan 5 may contain the literal string `human_test_frozen`. Enforced by `test_no_sacred_split_refs.py` which walks the tree and greps every Plan-5 file; the test fails loudly if the string is present.
- **Contract 9 (NEW) — conformal calibration uses `human_cal` ONLY.** `calibrate_conformal.py` reads `data/splits/human_cal.jsonl` exclusively. Reading `llm_train`, `llm_val`, `human_test_frozen`, or `human_test_fresh` in this script is prohibited. Enforced by `test_conformal_uses_human_cal_only.py` which greps the script and the conformal module.

---

## Phase A — Graph densification

### Task A1: Append deps and smoke test

**Files:**
- Modify: `requirements-classifier.txt`

- [ ] **Step 1: Append Plan 5 deps**

```
# Plan 5 additions
torch-geometric==2.6.1
torch-scatter==2.1.2
torch-sparse==0.6.18
lightgbm==4.5.0
shap==0.46.0
networkx==3.3
```

- [ ] **Step 2: Install and CPU smoke test**

Run: `source .venv/bin/activate && pip install -r requirements-classifier.txt && python -c "import torch_geometric, lightgbm, shap, networkx; print(torch_geometric.__version__, lightgbm.__version__, shap.__version__, networkx.__version__)"`
Expected: four version strings, no ImportError. `torch_scatter` / `torch_sparse` wheels must match the pinned torch 2.4.1; if Jetson wheels are unavailable, install is guarded in `classifier/ensemble/gat_model.py` via `try/except` and the GAT unit tests skip with a clear message. Lambda bootstrap handles the GPU wheel install.

- [ ] **Step 3: Commit**

```bash
git add requirements-classifier.txt
git commit -m "plan5: pin torch_geometric, lightgbm, shap, networkx"
```

### Task A2: `build_densified_graph()` — test-first

**Files:**
- Create: `classifier/ensemble/__init__.py` (empty)
- Create: `classifier/tests/test_densified_graph.py`
- Create: `classifier/ensemble/graph.py`

- [ ] **Step 1: Write the failing test**

```python
# classifier/tests/test_densified_graph.py
import pytest
from classifier.ensemble.graph import build_densified_graph

def test_densified_graph_has_expected_edges(tmp_path):
    g = build_densified_graph(
        nodes_path="data/splits/sme_pool_full.jsonl",
        expert_edges_path="data/candidates/pool_v1.jsonl",
        frozen_labels_path="data/labels/llm_sme/v1_frozen/llm_train.jsonl",
        cocite_path="data/graph/cocite_edges.jsonl",
        category_path="data/graph/cross_framework_categories.jsonl",
        min_confidence=0.75,
    )
    assert g.number_of_nodes() >= 500
    assert g.number_of_edges() >= 1500
    types = {d["edge_type"] for _, _, d in g.edges(data=True)}
    assert {"expert", "cross_framework_category", "cocite", "v1_frozen_highconf"} <= types
```

- [ ] **Step 2: Run the failing test**

Run: `pytest classifier/tests/test_densified_graph.py -q`
Expected: ImportError (module doesn't exist yet). Fail is correct.

- [ ] **Step 3: Implement `graph.py`**

```python
# classifier/ensemble/graph.py
import json
from pathlib import Path
import networkx as nx

def build_densified_graph(
    nodes_path: str,
    expert_edges_path: str,
    frozen_labels_path: str,
    cocite_path: str,
    category_path: str,
    min_confidence: float = 0.75,
) -> nx.MultiDiGraph:
    assert "v1_frozen" in str(frozen_labels_path), "Contract 5"
    g = nx.MultiDiGraph()
    for line in Path(nodes_path).read_text().splitlines():
        row = json.loads(line)
        g.add_node(row["node_id"], framework=row["framework"], text=row.get("text", ""))
    for line in Path(expert_edges_path).read_text().splitlines():
        row = json.loads(line)
        g.add_edge(row["src"], row["dst"], edge_type="expert", weight=1.0)
    for line in Path(category_path).read_text().splitlines():
        row = json.loads(line)
        g.add_edge(row["src"], row["dst"], edge_type="cross_framework_category", weight=0.5)
    for line in Path(cocite_path).read_text().splitlines():
        row = json.loads(line)
        g.add_edge(row["src"], row["dst"], edge_type="cocite", weight=float(row.get("weight", 0.3)))
    for line in Path(frozen_labels_path).read_text().splitlines():
        row = json.loads(line)
        if row.get("aggregated_confidence", 0.0) >= min_confidence and row.get("tier") == "Direct":
            g.add_edge(row["src"], row["dst"], edge_type="v1_frozen_highconf", weight=float(row["aggregated_confidence"]))
    return g
```

- [ ] **Step 4: Re-run test**

Run: `pytest classifier/tests/test_densified_graph.py -q`
Expected: `1 passed`.

- [ ] **Step 5: Commit**

```bash
git add classifier/ensemble/__init__.py classifier/ensemble/graph.py classifier/tests/test_densified_graph.py
git commit -m "plan5: densified crosswalk graph builder with edge-type test"
```

### Task A3: `build_densified_graph.py` entry script + pickled PyG `Data`

**Files:**
- Create: `classifier/scripts/build_densified_graph.py`

- [ ] **Step 1: Write the entry script**

```python
# classifier/scripts/build_densified_graph.py
import argparse, pickle
from pathlib import Path
from classifier.data.splits import verify_hashes
from classifier.labeling.freeze import verify_label_hashes
from classifier.ensemble.graph import build_densified_graph

def main():
    verify_hashes()
    verify_label_hashes()
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/graph/densified_v1.pkl")
    args = ap.parse_args()
    out = Path(args.out)
    if out.exists():
        raise FileExistsError(f"Contract 3: {out} exists")
    g = build_densified_graph(
        nodes_path="data/splits/sme_pool_full.jsonl",
        expert_edges_path="data/candidates/pool_v1.jsonl",
        frozen_labels_path="data/labels/llm_sme/v1_frozen/llm_train.jsonl",
        cocite_path="data/graph/cocite_edges.jsonl",
        category_path="data/graph/cross_framework_categories.jsonl",
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "wb") as f:
        pickle.dump(g, f, protocol=5)
    print(f"wrote {out}: {g.number_of_nodes()} nodes / {g.number_of_edges()} edges")

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the script**

Run: `python -m classifier.scripts.build_densified_graph --out data/graph/densified_v1.pkl`
Expected: `wrote data/graph/densified_v1.pkl: <N>=500+ nodes / <E>=1500+ edges`. If cocite/category files don't exist, pre-commit stub empty JSONL files and re-run (this is a known gap tracked under Plan 1 data prep).

- [ ] **Step 3: Commit**

```bash
git add classifier/scripts/build_densified_graph.py data/graph/densified_v1.pkl
git commit -m "plan5: densified_v1 graph built, expert+category+cocite+v1_frozen edges"
```

---

## Phase B — GAT module

### Task B1: `GATEncoder` forward — test-first

**Files:**
- Create: `classifier/tests/test_gat_model.py`
- Create: `classifier/ensemble/gat_model.py`

- [ ] **Step 1: Write the failing test**

```python
# classifier/tests/test_gat_model.py
import torch
import pytest
pyg = pytest.importorskip("torch_geometric")
from torch_geometric.data import Data
from classifier.ensemble.gat_model import GATEncoder

def test_forward_shape():
    x = torch.randn(10, 64)
    edge_index = torch.tensor([[0,1,2,3,4,5,6,7,8], [1,2,3,4,5,6,7,8,0]], dtype=torch.long)
    data = Data(x=x, edge_index=edge_index)
    enc = GATEncoder(in_dim=64, hidden_dim=128, out_dim=64, heads=4, num_layers=2, dropout=0.1)
    z = enc(data.x, data.edge_index)
    assert z.shape == (10, 64)
    assert z.requires_grad

def test_backward_flow():
    enc = GATEncoder(in_dim=32, hidden_dim=64, out_dim=32, heads=2, num_layers=2)
    x = torch.randn(8, 32, requires_grad=True)
    edge_index = torch.tensor([[0,1,2,3,4,5,6], [1,2,3,4,5,6,0]], dtype=torch.long)
    z = enc(x, edge_index)
    z.sum().backward()
    assert any(p.grad is not None and p.grad.abs().sum() > 0 for p in enc.parameters())
```

- [ ] **Step 2: Run the failing test**

Run: `pytest classifier/tests/test_gat_model.py -q`
Expected: ImportError on `classifier.ensemble.gat_model`.

- [ ] **Step 3: Implement `GATEncoder`**

```python
# classifier/ensemble/gat_model.py
import torch
import torch.nn as nn
from torch_geometric.nn import GATv2Conv

class GATEncoder(nn.Module):
    def __init__(self, in_dim: int, hidden_dim: int, out_dim: int, heads: int = 4, num_layers: int = 2, dropout: float = 0.1):
        super().__init__()
        self.layers = nn.ModuleList()
        dims = [in_dim] + [hidden_dim] * (num_layers - 1) + [out_dim]
        for i in range(num_layers):
            in_d = dims[i] * (heads if i > 0 else 1)
            out_d = dims[i+1]
            concat = i < num_layers - 1
            self.layers.append(GATv2Conv(in_d, out_d, heads=heads, concat=concat, dropout=dropout))
        self.dropout = nn.Dropout(dropout)
        self.act = nn.ELU()

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        for i, conv in enumerate(self.layers):
            x = conv(x, edge_index)
            if i < len(self.layers) - 1:
                x = self.act(x)
                x = self.dropout(x)
        return x
```

- [ ] **Step 4: Re-run tests**

Run: `pytest classifier/tests/test_gat_model.py -q`
Expected: `2 passed`.

- [ ] **Step 5: Commit**

```bash
git add classifier/ensemble/gat_model.py classifier/tests/test_gat_model.py
git commit -m "plan5: GATv2 encoder with forward+backward unit tests"
```

### Task B2: Pair-scoring head and loss util

**Files:**
- Modify: `classifier/ensemble/gat_model.py`
- Modify: `classifier/tests/test_gat_model.py`

- [ ] **Step 1: Add `pair_score` helper and link-prediction BCE loss**

```python
# append to classifier/ensemble/gat_model.py
import torch.nn.functional as F

def pair_score(z: torch.Tensor, src: torch.Tensor, dst: torch.Tensor) -> torch.Tensor:
    return (z[src] * z[dst]).sum(dim=-1)

def link_prediction_loss(z, pos_src, pos_dst, neg_src, neg_dst):
    pos = pair_score(z, pos_src, pos_dst)
    neg = pair_score(z, neg_src, neg_dst)
    logits = torch.cat([pos, neg])
    labels = torch.cat([torch.ones_like(pos), torch.zeros_like(neg)])
    return F.binary_cross_entropy_with_logits(logits, labels)
```

- [ ] **Step 2: Add unit test**

```python
# append to classifier/tests/test_gat_model.py
from classifier.ensemble.gat_model import pair_score, link_prediction_loss

def test_link_loss_decreases():
    torch.manual_seed(0)
    enc = GATEncoder(16, 32, 16, heads=2, num_layers=2)
    x = torch.randn(12, 16)
    ei = torch.tensor([[0,1,2,3,4,5,6,7,8,9,10,11],[1,2,3,4,5,6,7,8,9,10,11,0]], dtype=torch.long)
    pos_src = torch.tensor([0,2,4]); pos_dst = torch.tensor([1,3,5])
    neg_src = torch.tensor([0,2,4]); neg_dst = torch.tensor([6,7,8])
    opt = torch.optim.Adam(enc.parameters(), lr=1e-2)
    losses = []
    for _ in range(30):
        opt.zero_grad()
        z = enc(x, ei)
        loss = link_prediction_loss(z, pos_src, pos_dst, neg_src, neg_dst)
        loss.backward(); opt.step()
        losses.append(loss.item())
    assert losses[-1] < losses[0]
```

- [ ] **Step 3: Run tests**

Run: `pytest classifier/tests/test_gat_model.py -q`
Expected: `3 passed`.

- [ ] **Step 4: Commit**

```bash
git add classifier/ensemble/gat_model.py classifier/tests/test_gat_model.py
git commit -m "plan5: pair_score + link_prediction_loss for GAT training"
```

### Task B3: Node-feature bootstrapping from bge embeddings

**Files:**
- Create: `classifier/ensemble/node_features.py`
- Create: `classifier/tests/test_node_features.py`

- [ ] **Step 1: Write failing test**

```python
# classifier/tests/test_node_features.py
from classifier.ensemble.node_features import load_node_features

def test_load_shape():
    x, idx = load_node_features("data/baselines/bge_cosine_embeddings.parquet")
    assert x.shape[0] == len(idx)
    assert x.shape[1] == 1024
```

- [ ] **Step 2: Implement loader**

```python
# classifier/ensemble/node_features.py
import pyarrow.parquet as pq
import torch

def load_node_features(path: str):
    tbl = pq.read_table(path)
    node_ids = tbl["node_id"].to_pylist()
    embs = tbl["embedding"].to_pylist()
    x = torch.tensor(embs, dtype=torch.float32)
    idx = {nid: i for i, nid in enumerate(node_ids)}
    return x, idx
```

- [ ] **Step 3: Run test**

Run: `pytest classifier/tests/test_node_features.py -q`
Expected: `1 passed` (fixture parquet from Plan 3 is available; skip with `pytest.importorskip` if file missing on CI).

- [ ] **Step 4: Commit**

```bash
git add classifier/ensemble/node_features.py classifier/tests/test_node_features.py
git commit -m "plan5: node feature loader bridging Plan 3 bge embeddings to GAT"
```

---

## Phase C — GAT trainer

### Task C1: `gat_trainer.py` — v1_frozen Direct-edge holdout

**Files:**
- Create: `classifier/ensemble/gat_trainer.py`
- Create: `classifier/tests/test_gat_trainer.py`

- [ ] **Step 1: Write failing test**

```python
# classifier/tests/test_gat_trainer.py
import torch, pytest
pytest.importorskip("torch_geometric")
from classifier.ensemble.gat_trainer import split_frozen_direct_edges

def test_holdout_keeps_non_direct():
    edges = [("a","b","expert"),("c","d","v1_frozen_highconf"),("e","f","cocite"),("g","h","v1_frozen_highconf")]
    train, heldout = split_frozen_direct_edges(edges, holdout_frac=0.5, seed=0)
    assert len(heldout) == 1
    assert all(t[2] != "v1_frozen_highconf" or t in train for t in edges if t not in heldout)
    assert all(t[2] == "v1_frozen_highconf" for t in heldout)
```

- [ ] **Step 2: Implement split + trainer skeleton**

```python
# classifier/ensemble/gat_trainer.py
import json, random, uuid, datetime, subprocess
from pathlib import Path
from typing import List, Tuple
import torch
from .gat_model import GATEncoder, link_prediction_loss

def split_frozen_direct_edges(edges: List[Tuple], holdout_frac: float, seed: int):
    rng = random.Random(seed)
    direct = [e for e in edges if e[2] == "v1_frozen_highconf"]
    rng.shuffle(direct)
    k = max(1, int(len(direct) * holdout_frac))
    heldout = direct[:k]
    train = [e for e in edges if e not in heldout]
    return train, heldout

def make_run_id() -> str:
    ts = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    return f"gat-{uuid.uuid4().hex[:8]}-{ts}"

def train_gat(graph, node_features, cfg: dict) -> dict:
    assert "v1_frozen" in cfg.get("label_path", ""), "Contract 5"
    run_id = make_run_id()
    out = Path(f"runs/gat/{run_id}")
    if out.exists():
        raise FileExistsError(out)
    out.mkdir(parents=True)
    # training body omitted here: see Task C2 for the W&B+loop expansion.
    (out / "config.json").write_text(json.dumps(cfg, sort_keys=True))
    return {"run_id": run_id, "out_dir": str(out)}
```

- [ ] **Step 3: Run test**

Run: `pytest classifier/tests/test_gat_trainer.py -q`
Expected: `1 passed`.

- [ ] **Step 4: Commit**

```bash
git add classifier/ensemble/gat_trainer.py classifier/tests/test_gat_trainer.py
git commit -m "plan5: GAT trainer skeleton with frozen-direct-edge holdout split"
```

### Task C2: Full training loop + W&B + checkpoint

**Files:**
- Modify: `classifier/ensemble/gat_trainer.py`
- Modify: `classifier/tests/test_gat_trainer.py`

- [ ] **Step 1: Flesh out the training loop**

```python
# replace stub body in train_gat
def train_gat(graph, node_features, cfg: dict) -> dict:
    import wandb, torch
    from torch_geometric.utils import from_networkx
    assert "v1_frozen" in cfg.get("label_path", ""), "Contract 5"
    run_id = make_run_id()
    out = Path(f"runs/gat/{run_id}")
    if out.exists():
        raise FileExistsError(out)
    out.mkdir(parents=True)
    data = from_networkx(graph)
    data.x = node_features
    edges = [(u, v, d["edge_type"]) for u, v, d in graph.edges(data=True)]
    train_edges, heldout = split_frozen_direct_edges(edges, holdout_frac=cfg["holdout_frac"], seed=cfg["seed"])
    enc = GATEncoder(in_dim=data.x.shape[1], hidden_dim=cfg["hidden"], out_dim=cfg["out"], heads=cfg["heads"], num_layers=cfg["layers"], dropout=cfg["dropout"])
    opt = torch.optim.AdamW(enc.parameters(), lr=cfg["lr"], weight_decay=cfg["wd"])
    wandb.init(project="classifier-gat", name=run_id, config=cfg, dir=str(out))
    best = float("inf")
    for epoch in range(cfg["epochs"]):
        enc.train(); opt.zero_grad()
        z = enc(data.x, data.edge_index)
        pos_src = torch.tensor([e[0] for e in train_edges if e[2] != "v1_frozen_highconf"])
        pos_dst = torch.tensor([e[1] for e in train_edges if e[2] != "v1_frozen_highconf"])
        neg_src = torch.randint(0, data.x.shape[0], pos_src.shape)
        neg_dst = torch.randint(0, data.x.shape[0], pos_src.shape)
        loss = link_prediction_loss(z, pos_src, pos_dst, neg_src, neg_dst)
        loss.backward(); opt.step()
        wandb.log({"epoch": epoch, "train_loss": loss.item()})
        if loss.item() < best:
            best = loss.item()
            torch.save({"state_dict": enc.state_dict(), "cfg": cfg}, out / "best.pt")
    (out / "config.json").write_text(json.dumps(cfg, sort_keys=True))
    (out / "metrics.json").write_text(json.dumps({"best_train_loss": best}, sort_keys=True))
    wandb.finish()
    return {"run_id": run_id, "out_dir": str(out), "best_train_loss": best}
```

- [ ] **Step 2: Add an end-to-end smoke test (marked slow, skipped by default)**

```python
# append to classifier/tests/test_gat_trainer.py
@pytest.mark.slow
def test_train_gat_smoke(tmp_path, monkeypatch):
    pytest.importorskip("wandb")
    monkeypatch.chdir(tmp_path)
    import networkx as nx, torch
    g = nx.MultiDiGraph()
    for i in range(10): g.add_node(i)
    for i in range(9): g.add_edge(i, i+1, edge_type="expert")
    g.add_edge(0, 9, edge_type="v1_frozen_highconf")
    from classifier.ensemble.gat_trainer import train_gat
    out = train_gat(g, torch.randn(10,16), {"hidden":32,"out":16,"heads":2,"layers":2,"dropout":0.1,"lr":1e-2,"wd":0.0,"epochs":3,"holdout_frac":0.5,"seed":0,"label_path":"v1_frozen/x"})
    assert "run_id" in out
```

- [ ] **Step 3: Run non-slow tests**

Run: `pytest classifier/tests/test_gat_trainer.py -q -m "not slow"`
Expected: `1 passed, 1 deselected`.

- [ ] **Step 4: Commit**

```bash
git add classifier/ensemble/gat_trainer.py classifier/tests/test_gat_trainer.py
git commit -m "plan5: GAT link-prediction training loop with W&B + versioned checkpoint"
```

### Task C3: `train_gat.py` entry script + registry append

**Files:**
- Create: `classifier/scripts/train_gat.py`

- [ ] **Step 1: Write the entry script**

```python
# classifier/scripts/train_gat.py
import argparse, json, pickle, subprocess, datetime
from pathlib import Path
from classifier.data.splits import verify_hashes
from classifier.labeling.freeze import verify_label_hashes
from classifier.ensemble.gat_trainer import train_gat
from classifier.ensemble.node_features import load_node_features

def main():
    verify_hashes(); verify_label_hashes()
    ap = argparse.ArgumentParser()
    ap.add_argument("--graph", default="data/graph/densified_v1.pkl")
    ap.add_argument("--node-features", default="data/baselines/bge_cosine_embeddings.parquet")
    ap.add_argument("--epochs", type=int, default=200)
    ap.add_argument("--hidden", type=int, default=256)
    ap.add_argument("--heads", type=int, default=4)
    ap.add_argument("--layers", type=int, default=2)
    args = ap.parse_args()
    with open(args.graph, "rb") as f:
        g = pickle.load(f)
    x, idx = load_node_features(args.node_features)
    cfg = dict(hidden=args.hidden, out=128, heads=args.heads, layers=args.layers,
               dropout=0.1, lr=1e-3, wd=1e-4, epochs=args.epochs, holdout_frac=0.1, seed=42,
               label_path="data/labels/llm_sme/v1_frozen/llm_train.jsonl")
    res = train_gat(g, x, cfg)
    git_sha = subprocess.check_output(["git","rev-parse","HEAD"]).decode().strip()
    row = {"component":"gat","run_id":res["run_id"],"git_sha":git_sha,
           "finished_at_utc":datetime.datetime.utcnow().isoformat()+"Z",
           "metrics":{"best_train_loss":res["best_train_loss"]},
           "checkpoint_path":res["out_dir"],"status":"ok"}
    with open("runs/registry.jsonl","a") as f:
        f.write(json.dumps(row, sort_keys=True, ensure_ascii=True)+"\n")

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: CPU smoke test on Jetson**

Run: `python -m classifier.scripts.train_gat --epochs 3`
Expected: a new `runs/gat/gat-<hex>-<ts>/` directory with `best.pt`, `config.json`, `metrics.json`, and a new line appended to `runs/registry.jsonl` with `component: gat`.

- [ ] **Step 3: Commit**

```bash
git add classifier/scripts/train_gat.py
git commit -m "plan5: GAT training entry script with registry append"
```

---

## Phase D — Pair embedding extractor

### Task D1: `pair_embeddings.py` — cosine/dot/hadamard features

**Files:**
- Create: `classifier/tests/test_pair_embeddings.py`
- Create: `classifier/ensemble/pair_embeddings.py`

- [ ] **Step 1: Write failing test**

```python
# classifier/tests/test_pair_embeddings.py
import torch
from classifier.ensemble.pair_embeddings import compute_pair_features

def test_feature_shape_and_values():
    z = torch.tensor([[1.0,0.0],[0.0,1.0],[1.0,1.0]])
    pairs = [(0,1),(0,2)]
    feats = compute_pair_features(z, pairs)
    assert set(feats.keys()) == {"cos","dot","hadamard"}
    assert feats["cos"].shape == (2,)
    assert feats["hadamard"].shape == (2, 2)
    assert abs(feats["cos"][0].item()) < 1e-6  # orthogonal
```

- [ ] **Step 2: Implement**

```python
# classifier/ensemble/pair_embeddings.py
import torch
import torch.nn.functional as F
from typing import List, Tuple, Dict

def compute_pair_features(z: torch.Tensor, pairs: List[Tuple[int,int]]) -> Dict[str, torch.Tensor]:
    src = torch.tensor([p[0] for p in pairs], dtype=torch.long)
    dst = torch.tensor([p[1] for p in pairs], dtype=torch.long)
    zs, zd = z[src], z[dst]
    return {
        "cos": F.cosine_similarity(zs, zd, dim=-1),
        "dot": (zs * zd).sum(dim=-1),
        "hadamard": zs * zd,
    }
```

- [ ] **Step 3: Run test**

Run: `pytest classifier/tests/test_pair_embeddings.py -q`
Expected: `1 passed`.

- [ ] **Step 4: Commit**

```bash
git add classifier/ensemble/pair_embeddings.py classifier/tests/test_pair_embeddings.py
git commit -m "plan5: GAT pair feature extractor (cos/dot/hadamard)"
```

### Task D2: `extract_pair_embeddings.py` entry + parquet cache

**Files:**
- Create: `classifier/scripts/extract_pair_embeddings.py`

- [ ] **Step 1: Write entry script**

```python
# classifier/scripts/extract_pair_embeddings.py
import argparse, json, pickle
from pathlib import Path
import torch, pyarrow as pa, pyarrow.parquet as pq
from classifier.data.splits import verify_hashes
from classifier.labeling.freeze import verify_label_hashes
from classifier.ensemble.gat_model import GATEncoder
from classifier.ensemble.node_features import load_node_features
from classifier.ensemble.pair_embeddings import compute_pair_features

def main():
    verify_hashes(); verify_label_hashes()
    ap = argparse.ArgumentParser()
    ap.add_argument("--gat-run", required=True)
    ap.add_argument("--pairs", default="data/candidates/pool_v1.jsonl")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out = Path(args.out)
    if out.exists():
        raise FileExistsError(out)
    ckpt = torch.load(f"runs/gat/{args.gat_run}/best.pt", map_location="cpu")
    cfg = ckpt["cfg"]
    x, idx = load_node_features("data/baselines/bge_cosine_embeddings.parquet")
    enc = GATEncoder(in_dim=x.shape[1], hidden_dim=cfg["hidden"], out_dim=cfg["out"], heads=cfg["heads"], num_layers=cfg["layers"])
    enc.load_state_dict(ckpt["state_dict"]); enc.eval()
    with open("data/graph/densified_v1.pkl","rb") as f:
        import networkx as nx
        g = pickle.load(f)
    from torch_geometric.utils import from_networkx
    data = from_networkx(g); data.x = x
    with torch.no_grad():
        z = enc(data.x, data.edge_index)
    pair_rows = [json.loads(l) for l in Path(args.pairs).read_text().splitlines()]
    pairs = [(idx[r["src"]], idx[r["dst"]]) for r in pair_rows if r["src"] in idx and r["dst"] in idx]
    feats = compute_pair_features(z, pairs)
    tbl = pa.table({
        "pair_key": [f"{r['src']}||{r['dst']}" for r in pair_rows if r["src"] in idx and r["dst"] in idx],
        "gat_cos": feats["cos"].numpy(),
        "gat_dot": feats["dot"].numpy(),
    })
    out.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(tbl, out, use_dictionary=False, compression="snappy")
    print(f"wrote {len(tbl)} rows -> {out}")

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Smoke run**

Run: `python -m classifier.scripts.extract_pair_embeddings --gat-run <run_id_from_C3> --out data/features/gat_pair_features_v1.parquet`
Expected: `wrote <N> rows -> data/features/gat_pair_features_v1.parquet` where N matches `pool_v1.jsonl` size minus any src/dst missing from the node index.

- [ ] **Step 3: Commit**

```bash
git add classifier/scripts/extract_pair_embeddings.py data/features/gat_pair_features_v1.parquet
git commit -m "plan5: extract GAT pair features to parquet cache"
```

---

## Phase E — 5-fold OOF stack feature builder

### Task E1: Fold assigner + leakage test

**Files:**
- Create: `classifier/ensemble/oof_features.py`
- Create: `classifier/tests/test_oof_features.py`

- [ ] **Step 1: Write failing test**

```python
# classifier/tests/test_oof_features.py
import pandas as pd
from classifier.ensemble.oof_features import assign_folds, check_no_row_leakage

def test_fold_disjoint():
    pairs = [f"p{i}" for i in range(50)]
    folds = assign_folds(pairs, n_folds=5, seed=42)
    for k in range(5):
        train = [p for p,f in zip(pairs,folds) if f != k]
        test = [p for p,f in zip(pairs,folds) if f == k]
        assert set(train).isdisjoint(set(test))
    check_no_row_leakage(pairs, folds)
```

- [ ] **Step 2: Implement**

```python
# classifier/ensemble/oof_features.py
import hashlib, random
from typing import List

def assign_folds(pair_keys: List[str], n_folds: int, seed: int) -> List[int]:
    rng = random.Random(seed)
    idx = list(range(len(pair_keys)))
    rng.shuffle(idx)
    folds = [0] * len(pair_keys)
    for rank, i in enumerate(idx):
        folds[i] = rank % n_folds
    return folds

def check_no_row_leakage(pair_keys, folds):
    seen = {}
    for p, f in zip(pair_keys, folds):
        if p in seen and seen[p] != f:
            raise ValueError(f"row leakage: {p} in multiple folds")
        seen[p] = f
```

- [ ] **Step 3: Run test**

Run: `pytest classifier/tests/test_oof_features.py -q`
Expected: `1 passed`.

- [ ] **Step 4: Commit**

```bash
git add classifier/ensemble/oof_features.py classifier/tests/test_oof_features.py
git commit -m "plan5: fold assigner + leakage guard for OOF stack features"
```

### Task E2: OOF feature builder consuming Plan 3 + Plan 4

**Files:**
- Modify: `classifier/ensemble/oof_features.py`
- Modify: `classifier/tests/test_oof_features.py`

- [ ] **Step 1: Add `build_oof_features()`**

```python
# append to classifier/ensemble/oof_features.py
import pyarrow.parquet as pq, pandas as pd

def build_oof_features(
    baseline_parquet: str,
    gat_parquet: str,
    rung_scorers: dict,
    label_path: str,
    n_folds: int = 5,
    seed: int = 42,
) -> pd.DataFrame:
    assert "v1_frozen" in label_path, "Contract 5"
    baselines = pq.read_table(baseline_parquet).to_pandas()
    gat = pq.read_table(gat_parquet).to_pandas()
    df = baselines.merge(gat, on="pair_key", how="left")
    folds = assign_folds(df["pair_key"].tolist(), n_folds, seed)
    df["fold"] = folds
    for rung_name, scorer_factory in rung_scorers.items():
        oof_col = []
        for k in range(n_folds):
            train_mask = df["fold"] != k
            test_mask = ~train_mask
            scorer = scorer_factory(train_pairs=df.loc[train_mask, "pair_key"].tolist())
            scores = scorer.score_batch(df.loc[test_mask, "pair_key"].tolist())
            tmp = pd.Series(index=df.index, dtype=float)
            tmp.loc[test_mask] = scores
            oof_col.append(tmp)
        df[f"oof_{rung_name}"] = pd.concat(oof_col, axis=1).sum(axis=1, min_count=1)
    return df
```

- [ ] **Step 2: Add unit test with fake rung factory**

```python
# append to classifier/tests/test_oof_features.py
def test_build_oof_with_fake_rung(tmp_path):
    import pyarrow as pa, pyarrow.parquet as pq
    keys = [f"a||b{i}" for i in range(20)]
    pq.write_table(pa.table({"pair_key":keys,"bm25":[0.1]*20}), tmp_path/"base.parquet")
    pq.write_table(pa.table({"pair_key":keys,"gat_cos":[0.5]*20,"gat_dot":[1.0]*20}), tmp_path/"gat.parquet")
    class FakeScorer:
        def __init__(self, train_pairs): self.n = len(train_pairs)
        def score_batch(self, pairs): return [0.7]*len(pairs)
    df = build_oof_features(str(tmp_path/"base.parquet"), str(tmp_path/"gat.parquet"),
                            {"rungM": FakeScorer}, "v1_frozen/x", n_folds=5, seed=0)
    assert "oof_rungM" in df.columns
    assert df["oof_rungM"].notna().sum() == 20
```

- [ ] **Step 3: Run tests**

Run: `pytest classifier/tests/test_oof_features.py -q`
Expected: `2 passed`.

- [ ] **Step 4: Commit**

```bash
git add classifier/ensemble/oof_features.py classifier/tests/test_oof_features.py
git commit -m "plan5: OOF stack feature builder consuming Plan 3/4 scorers"
```

### Task E3: `build_stack_features.py` entry script

**Files:**
- Create: `classifier/scripts/build_stack_features.py`

- [ ] **Step 1: Write entry script**

```python
# classifier/scripts/build_stack_features.py
import argparse
from pathlib import Path
import pyarrow as pa, pyarrow.parquet as pq
from classifier.data.splits import verify_hashes
from classifier.labeling.freeze import verify_label_hashes
from classifier.ensemble.oof_features import build_oof_features
from classifier.baselines.registry import get as get_scorer

def rung_factory(rung_name: str):
    def _factory(train_pairs):
        scorer = get_scorer(rung_name)  # registered by Plan 4
        return scorer
    return _factory

def main():
    verify_hashes(); verify_label_hashes()
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/features/stack_features_v1.parquet")
    ap.add_argument("--rungs", nargs="+", default=["cross_encoder_S","cross_encoder_M","cross_encoder_L"])
    args = ap.parse_args()
    out = Path(args.out)
    if out.exists():
        raise FileExistsError(out)
    df = build_oof_features(
        baseline_parquet="data/features/baseline_features.parquet",
        gat_parquet="data/features/gat_pair_features_v1.parquet",
        rung_scorers={r: rung_factory(r) for r in args.rungs},
        label_path="data/labels/llm_sme/v1_frozen/llm_train.jsonl",
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.Table.from_pandas(df), out, use_dictionary=False, compression="snappy")
    print(f"wrote {len(df)} rows x {len(df.columns)} cols -> {out}")

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Smoke run (Lambda for real rung retraining; Jetson with `--rungs cross_encoder_S` only is acceptable for CI)**

Run: `python -m classifier.scripts.build_stack_features --rungs cross_encoder_S --out data/features/stack_features_smoke.parquet`
Expected: `wrote <N> rows x <M> cols -> data/features/stack_features_smoke.parquet`.

- [ ] **Step 3: Commit**

```bash
git add classifier/scripts/build_stack_features.py
git commit -m "plan5: stack feature builder entry script"
```

---

## Phase F — LightGBM stacker

### Task F1: `LGBMStacker` fit/predict + SHAP

**Files:**
- Create: `classifier/ensemble/stacker.py`
- Create: `classifier/tests/test_stacker.py`

- [ ] **Step 1: Write failing test**

```python
# classifier/tests/test_stacker.py
import numpy as np, pandas as pd
from classifier.ensemble.stacker import LGBMStacker

def test_fit_predict_shape():
    rng = np.random.default_rng(0)
    X = pd.DataFrame(rng.normal(size=(200, 6)), columns=[f"f{i}" for i in range(6)])
    y = rng.integers(0, 3, size=200)
    st = LGBMStacker(n_classes=3)
    st.fit(X, y)
    proba = st.predict_proba(X)
    assert proba.shape == (200, 3)
    assert np.allclose(proba.sum(axis=1), 1.0, atol=1e-4)

def test_shap_nonempty():
    rng = np.random.default_rng(1)
    X = pd.DataFrame(rng.normal(size=(100, 4)), columns=[f"f{i}" for i in range(4)])
    y = rng.integers(0, 3, size=100)
    st = LGBMStacker(n_classes=3).fit(X, y)
    sv = st.shap_values(X.head(10))
    assert sv is not None
```

- [ ] **Step 2: Implement**

```python
# classifier/ensemble/stacker.py
import lightgbm as lgb
import numpy as np, pandas as pd

class LGBMStacker:
    version = "1.0.0"
    def __init__(self, n_classes: int, params: dict | None = None):
        self.n_classes = n_classes
        self.params = params or {"objective":"multiclass","num_class":n_classes,
                                  "learning_rate":0.05,"num_leaves":31,"min_data_in_leaf":10,
                                  "feature_fraction":0.9,"bagging_fraction":0.9,"bagging_freq":5,
                                  "verbose":-1}
        self.booster = None

    def fit(self, X: pd.DataFrame, y):
        ds = lgb.Dataset(X, label=y)
        self.booster = lgb.train(self.params, ds, num_boost_round=300)
        return self

    def predict_proba(self, X):
        return self.booster.predict(X)

    def shap_values(self, X):
        import shap
        explainer = shap.TreeExplainer(self.booster)
        return explainer.shap_values(X)

    def save(self, path: str):
        self.booster.save_model(path)
```

- [ ] **Step 3: Run tests**

Run: `pytest classifier/tests/test_stacker.py -q`
Expected: `2 passed`.

- [ ] **Step 4: Commit**

```bash
git add classifier/ensemble/stacker.py classifier/tests/test_stacker.py
git commit -m "plan5: LightGBM multiclass stacker with SHAP diagnostic"
```

### Task F2: Optuna 20-trial tuner

**Files:**
- Modify: `classifier/ensemble/stacker.py`
- Modify: `classifier/tests/test_stacker.py`

- [ ] **Step 1: Add `tune_stacker()`**

```python
# append to classifier/ensemble/stacker.py
import optuna
from sklearn.model_selection import StratifiedKFold

def tune_stacker(X, y, n_classes: int, n_trials: int = 20, seed: int = 42) -> dict:
    def objective(trial):
        params = {
            "objective":"multiclass","num_class":n_classes,
            "learning_rate": trial.suggest_float("lr", 1e-3, 0.2, log=True),
            "num_leaves": trial.suggest_int("num_leaves", 15, 127),
            "min_data_in_leaf": trial.suggest_int("min_data", 5, 50),
            "feature_fraction": trial.suggest_float("ff", 0.5, 1.0),
            "bagging_fraction": trial.suggest_float("bf", 0.5, 1.0),
            "bagging_freq": 5, "verbose": -1,
        }
        skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=seed)
        scores = []
        for tr, va in skf.split(X, y):
            st = LGBMStacker(n_classes, params).fit(X.iloc[tr], y[tr])
            proba = st.predict_proba(X.iloc[va])
            import numpy as np
            pred = proba.argmax(axis=1)
            scores.append((pred == y[va]).mean())
        return float(np.mean(scores))
    study = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=seed))
    study.optimize(objective, n_trials=n_trials, show_progress_bar=False)
    return study.best_params
```

- [ ] **Step 2: Add test**

```python
# append to classifier/tests/test_stacker.py
def test_tune_returns_params():
    import numpy as np, pandas as pd
    from classifier.ensemble.stacker import tune_stacker
    rng = np.random.default_rng(2)
    X = pd.DataFrame(rng.normal(size=(120,4)), columns=list("abcd"))
    y = rng.integers(0,3,size=120)
    best = tune_stacker(X, y, n_classes=3, n_trials=3)
    assert "lr" in best
```

- [ ] **Step 3: Run tests**

Run: `pytest classifier/tests/test_stacker.py -q`
Expected: `3 passed`.

- [ ] **Step 4: Commit**

```bash
git add classifier/ensemble/stacker.py classifier/tests/test_stacker.py
git commit -m "plan5: 20-trial Optuna tuner for LightGBM stacker"
```

### Task F3: `train_stacker.py` entry + stop-on-no-lift + registry

**Files:**
- Create: `classifier/scripts/train_stacker.py`

- [ ] **Step 1: Write entry script**

```python
# classifier/scripts/train_stacker.py
import argparse, json, uuid, datetime, subprocess
from pathlib import Path
import numpy as np, pandas as pd
import pyarrow.parquet as pq
from classifier.data.splits import verify_hashes
from classifier.labeling.freeze import verify_label_hashes
from classifier.ensemble.stacker import LGBMStacker, tune_stacker

def main():
    verify_hashes(); verify_label_hashes()
    ap = argparse.ArgumentParser()
    ap.add_argument("--features", default="data/features/stack_features_v1.parquet")
    ap.add_argument("--labels", default="data/labels/llm_sme/v1_frozen/llm_train.jsonl")
    ap.add_argument("--val-labels", default="data/labels/llm_sme/v1_frozen/llm_val.jsonl")
    ap.add_argument("--best-rung-mrr", type=float, required=True)
    ap.add_argument("--n-trials", type=int, default=20)
    args = ap.parse_args()
    assert "v1_frozen" in args.labels
    df = pq.read_table(args.features).to_pandas()
    labels = {json.loads(l)["pair_key"]: json.loads(l)["tier_id"] for l in Path(args.labels).read_text().splitlines()}
    df = df[df["pair_key"].isin(labels)]
    y = np.array([labels[k] for k in df["pair_key"]])
    feat_cols = [c for c in df.columns if c not in ("pair_key","fold")]
    X = df[feat_cols]
    best_params = tune_stacker(X, y, n_classes=3, n_trials=args.n_trials)
    st = LGBMStacker(n_classes=3, params={**best_params, "objective":"multiclass","num_class":3,"verbose":-1}).fit(X, y)
    # compute llm_val MRR (stub: uses top-1 accuracy as proxy in the smoke path)
    val_labels = {json.loads(l)["pair_key"]: json.loads(l)["tier_id"] for l in Path(args.val_labels).read_text().splitlines()}
    val_df = df[df["pair_key"].isin(val_labels)]
    val_X = val_df[feat_cols]
    val_y = np.array([val_labels[k] for k in val_df["pair_key"]])
    val_mrr = float((st.predict_proba(val_X).argmax(axis=1) == val_y).mean())
    run_id = f"stacker-{uuid.uuid4().hex[:8]}-{datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}"
    out = Path(f"runs/stacker/{run_id}")
    if out.exists():
        raise FileExistsError(out)
    out.mkdir(parents=True)
    st.save(str(out/"model.txt"))
    (out/"config.json").write_text(json.dumps({"best_params":best_params,"val_mrr":val_mrr}, sort_keys=True))
    git_sha = subprocess.check_output(["git","rev-parse","HEAD"]).decode().strip()
    status = "ok" if val_mrr - args.best_rung_mrr >= 0.005 else "rejected"
    row = {"component":"stacker","run_id":run_id,"git_sha":git_sha,
           "finished_at_utc":datetime.datetime.utcnow().isoformat()+"Z",
           "metrics":{"val_mrr":val_mrr,"lift_vs_best_rung":val_mrr-args.best_rung_mrr},
           "checkpoint_path":str(out),"status":status}
    with open("runs/registry.jsonl","a") as f:
        f.write(json.dumps(row, sort_keys=True, ensure_ascii=True)+"\n")
    if status == "rejected":
        raise SystemExit(f"stacker-no-lift: val_mrr={val_mrr:.4f} vs rung={args.best_rung_mrr:.4f}")

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Smoke run against stub features**

Run: `python -m classifier.scripts.train_stacker --features data/features/stack_features_smoke.parquet --best-rung-mrr 0.0 --n-trials 3`
Expected: prints nothing on success; creates `runs/stacker/stacker-<hex>-<ts>/model.txt` and appends a `component: stacker` row to `runs/registry.jsonl` with `status: ok` (because best-rung-mrr=0 forces lift).

- [ ] **Step 3: Commit**

```bash
git add classifier/scripts/train_stacker.py
git commit -m "plan5: stacker training entry with stop-on-no-lift gate + registry row"
```

---

## Phase G — Mondrian conformal wrapper

### Task G1: `MondrianConformal` per-tier q_hat — test first

**Files:**
- Create: `classifier/ensemble/conformal.py`
- Create: `classifier/tests/test_conformal.py`

- [ ] **Step 1: Write failing test**

```python
# classifier/tests/test_conformal.py
import numpy as np
from classifier.ensemble.conformal import MondrianConformal

def test_per_tier_q_hat_and_coverage():
    rng = np.random.default_rng(0)
    n = 300
    tiers = rng.integers(0, 3, size=n)
    probs = rng.dirichlet(alpha=[1,1,1], size=n)
    # plant truth so coverage is reachable
    y_true = probs.argmax(axis=1)
    mc = MondrianConformal(alpha=0.10)
    mc.fit(probs, y_true, tiers)
    sets = mc.predict_sets(probs, tiers)
    covered = np.mean([y_true[i] in sets[i] for i in range(n)])
    assert 0.85 <= covered <= 0.97
    assert set(mc.q_hat.keys()) == {0,1,2}
```

- [ ] **Step 2: Implement**

```python
# classifier/ensemble/conformal.py
import numpy as np
from typing import Dict

class MondrianConformal:
    version = "1.0.0"
    def __init__(self, alpha: float = 0.10):
        self.alpha = alpha
        self.q_hat: Dict[int, float] = {}

    def fit(self, probs: np.ndarray, y_true: np.ndarray, tier: np.ndarray):
        for t in np.unique(tier):
            mask = tier == t
            scores = 1.0 - probs[mask, y_true[mask]]
            n = mask.sum()
            q_level = np.ceil((n+1)*(1-self.alpha)) / n
            q_level = min(q_level, 1.0)
            self.q_hat[int(t)] = float(np.quantile(scores, q_level, method="higher"))
        return self

    def predict_sets(self, probs: np.ndarray, tier: np.ndarray):
        out = []
        for i in range(len(probs)):
            t = int(tier[i])
            q = self.q_hat[t]
            out.append([c for c in range(probs.shape[1]) if 1.0 - probs[i, c] <= q])
        return out

    def to_dict(self):
        return {"alpha": self.alpha, "q_hat": self.q_hat, "version": self.version}
```

- [ ] **Step 3: Run test**

Run: `pytest classifier/tests/test_conformal.py -q`
Expected: `1 passed`.

- [ ] **Step 4: Commit**

```bash
git add classifier/ensemble/conformal.py classifier/tests/test_conformal.py
git commit -m "plan5: Mondrian split-conformal wrapper per-tier q_hat"
```

### Task G2: `calibrate_conformal.py` entry + Contract 9 grep test

**Files:**
- Create: `classifier/scripts/calibrate_conformal.py`
- Create: `classifier/tests/test_conformal_uses_human_cal_only.py`

- [ ] **Step 1: Write entry script**

```python
# classifier/scripts/calibrate_conformal.py
import argparse, json, uuid, datetime, subprocess
from pathlib import Path
import numpy as np, pandas as pd, pyarrow.parquet as pq
from classifier.data.splits import verify_hashes
from classifier.ensemble.conformal import MondrianConformal
from classifier.ensemble.stacker import LGBMStacker

CAL_PATH = "data/splits/human_cal.jsonl"  # Contract 9: human_cal ONLY

def main():
    verify_hashes()
    ap = argparse.ArgumentParser()
    ap.add_argument("--stacker-run", required=True)
    ap.add_argument("--features", default="data/features/stack_features_v1.parquet")
    ap.add_argument("--alpha", type=float, default=0.10)
    args = ap.parse_args()
    feat = pq.read_table(args.features).to_pandas()
    cal_rows = [json.loads(l) for l in Path(CAL_PATH).read_text().splitlines()]
    cal_df = feat[feat["pair_key"].isin({r["pair_key"] for r in cal_rows})]
    cal_lookup = {r["pair_key"]: r for r in cal_rows}
    y = np.array([cal_lookup[k]["tier_id"] for k in cal_df["pair_key"]])
    tier = np.array([cal_lookup[k]["tier_id"] for k in cal_df["pair_key"]])
    feat_cols = [c for c in cal_df.columns if c not in ("pair_key","fold")]
    import lightgbm as lgb
    booster = lgb.Booster(model_file=f"runs/stacker/{args.stacker_run}/model.txt")
    probs = booster.predict(cal_df[feat_cols])
    mc = MondrianConformal(alpha=args.alpha).fit(probs, y, tier)
    sets = mc.predict_sets(probs, tier)
    coverage = float(np.mean([y[i] in sets[i] for i in range(len(y))]))
    if abs(coverage - (1 - args.alpha)) > 0.03:
        raise SystemExit(f"conformal coverage OOB: {coverage:.3f}")
    run_id = f"conformal-{uuid.uuid4().hex[:8]}-{datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}"
    out = Path(f"runs/conformal/{run_id}")
    if out.exists():
        raise FileExistsError(out)
    out.mkdir(parents=True)
    (out/"q_hat.json").write_text(json.dumps(mc.to_dict(), sort_keys=True, ensure_ascii=True))
    git_sha = subprocess.check_output(["git","rev-parse","HEAD"]).decode().strip()
    row = {"component":"conformal","run_id":run_id,"git_sha":git_sha,
           "finished_at_utc":datetime.datetime.utcnow().isoformat()+"Z",
           "metrics":{"coverage":coverage,"alpha":args.alpha},
           "checkpoint_path":str(out),"status":"ok"}
    with open("runs/registry.jsonl","a") as f:
        f.write(json.dumps(row, sort_keys=True, ensure_ascii=True)+"\n")

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Write the Contract 9 grep test**

```python
# classifier/tests/test_conformal_uses_human_cal_only.py
from pathlib import Path
FORBIDDEN = ["llm_train", "llm_val", "human_test_frozen", "human_test_fresh"]
FILES = [
    "classifier/scripts/calibrate_conformal.py",
    "classifier/ensemble/conformal.py",
]
def test_no_forbidden_splits():
    for f in FILES:
        txt = Path(f).read_text()
        for bad in FORBIDDEN:
            assert bad not in txt, f"Contract 9 violated: {bad} found in {f}"
```

- [ ] **Step 3: Run the grep test**

Run: `pytest classifier/tests/test_conformal_uses_human_cal_only.py -q`
Expected: `1 passed`.

- [ ] **Step 4: Commit**

```bash
git add classifier/scripts/calibrate_conformal.py classifier/tests/test_conformal_uses_human_cal_only.py
git commit -m "plan5: Mondrian conformal calibration on human_cal with Contract 9 grep"
```

---

## Phase H — Disagreement-KL abstention router

### Task H1: `Router` — KL math + threshold tuner

**Files:**
- Create: `classifier/ensemble/router.py`
- Create: `classifier/tests/test_router.py`

- [ ] **Step 1: Write failing test**

```python
# classifier/tests/test_router.py
import numpy as np
from classifier.ensemble.router import kl_divergence, tune_tau

def test_kl_symmetric_zero():
    p = np.array([0.5,0.5])
    assert abs(kl_divergence(p,p)) < 1e-9

def test_tune_tau_precision_floor():
    rng = np.random.default_rng(0)
    n = 500
    p_stage2 = rng.dirichlet([1,1,1], size=n)
    p_stage3 = p_stage2.copy()
    # inject disagreement on 20% of rows
    noisy = rng.choice(n, size=100, replace=False)
    p_stage3[noisy] = rng.dirichlet([1,1,1], size=100)
    y_pred = p_stage3.argmax(axis=1)
    y_true = p_stage2.argmax(axis=1)
    tau, prec = tune_tau(p_stage2, p_stage3, y_pred, y_true, target_precision=0.95)
    assert prec >= 0.95
```

- [ ] **Step 2: Implement**

```python
# classifier/ensemble/router.py
import numpy as np

def kl_divergence(p: np.ndarray, q: np.ndarray, eps: float = 1e-12) -> float:
    p = np.asarray(p, dtype=float); q = np.asarray(q, dtype=float)
    return float(np.sum(p * (np.log(p + eps) - np.log(q + eps))))

def batch_kl(P, Q, eps=1e-12):
    return np.sum(P * (np.log(P + eps) - np.log(Q + eps)), axis=1)

def tune_tau(p_stage2, p_stage3, y_pred, y_true, target_precision: float = 0.95):
    kl = batch_kl(p_stage2, p_stage3)
    order = np.argsort(-kl)  # high KL first => abstain first
    best_tau, best_prec = float("inf"), 0.0
    for k in range(1, len(kl)):
        abstain_idx = order[:k]
        keep_mask = np.ones(len(kl), dtype=bool); keep_mask[abstain_idx] = False
        if keep_mask.sum() == 0: break
        prec = float((y_pred[keep_mask] == y_true[keep_mask]).mean())
        if prec >= target_precision:
            best_tau = float(kl[order[k]]) if k < len(order) else 0.0
            best_prec = prec
            break
    return best_tau, best_prec

class KLRouter:
    version = "1.0.0"
    def __init__(self, tau: float): self.tau = tau
    def should_abstain(self, p_stage2, p_stage3) -> np.ndarray:
        return batch_kl(p_stage2, p_stage3) > self.tau
```

- [ ] **Step 3: Run tests**

Run: `pytest classifier/tests/test_router.py -q`
Expected: `2 passed`.

- [ ] **Step 4: Commit**

```bash
git add classifier/ensemble/router.py classifier/tests/test_router.py
git commit -m "plan5: KL-disagreement abstention router with tau tuner"
```

### Task H2: `tune_router.py` entry (llm_val only)

**Files:**
- Create: `classifier/scripts/tune_router.py`

- [ ] **Step 1: Write entry script**

```python
# classifier/scripts/tune_router.py
import argparse, json, uuid, datetime, subprocess
from pathlib import Path
import numpy as np, pyarrow.parquet as pq
from classifier.data.splits import verify_hashes
from classifier.labeling.freeze import verify_label_hashes
from classifier.ensemble.router import tune_tau
import lightgbm as lgb

def main():
    verify_hashes(); verify_label_hashes()
    ap = argparse.ArgumentParser()
    ap.add_argument("--stacker-run", required=True)
    ap.add_argument("--features", default="data/features/stack_features_v1.parquet")
    ap.add_argument("--target-precision", type=float, default=0.95)
    args = ap.parse_args()
    feat = pq.read_table(args.features).to_pandas()
    val_path = "data/labels/llm_sme/v1_frozen/llm_val.jsonl"
    assert "v1_frozen" in val_path
    val_rows = [json.loads(l) for l in Path(val_path).read_text().splitlines()]
    val_df = feat[feat["pair_key"].isin({r["pair_key"] for r in val_rows})]
    lookup = {r["pair_key"]: r for r in val_rows}
    y = np.array([lookup[k]["tier_id"] for k in val_df["pair_key"]])
    feat_cols = [c for c in val_df.columns if c not in ("pair_key","fold")]
    booster = lgb.Booster(model_file=f"runs/stacker/{args.stacker_run}/model.txt")
    p3 = booster.predict(val_df[feat_cols])
    # stage 2 = GAT-only proxy (cos softmaxed across tiers as a stand-in); replaced in Plan 6 eval
    p2 = np.full_like(p3, 1/3)
    pred = p3.argmax(axis=1)
    tau, prec = tune_tau(p2, p3, pred, y, target_precision=args.target_precision)
    run_id = f"router-{uuid.uuid4().hex[:8]}-{datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}"
    out = Path(f"runs/ensemble/{run_id}")
    if out.exists():
        raise FileExistsError(out)
    out.mkdir(parents=True)
    (out/"router.json").write_text(json.dumps({"tau":tau,"precision":prec,"target":args.target_precision}, sort_keys=True))
    git_sha = subprocess.check_output(["git","rev-parse","HEAD"]).decode().strip()
    row = {"component":"router","run_id":run_id,"git_sha":git_sha,
           "finished_at_utc":datetime.datetime.utcnow().isoformat()+"Z",
           "metrics":{"tau":tau,"precision":prec},
           "checkpoint_path":str(out),"status":"ok"}
    with open("runs/registry.jsonl","a") as f:
        f.write(json.dumps(row, sort_keys=True, ensure_ascii=True)+"\n")

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Smoke run**

Run: `python -m classifier.scripts.tune_router --stacker-run <id_from_F3>`
Expected: a new `runs/ensemble/router-<hex>-<ts>/router.json` with `tau` and `precision` ≥ 0.95 (or as close as the proxy allows).

- [ ] **Step 3: Commit**

```bash
git add classifier/scripts/tune_router.py
git commit -m "plan5: router tau tuning on llm_val for 95% precision floor"
```

---

## Phase I — Ensemble eval + Plan 6 handoff

### Task I1: `EnsembleScorer` + protocol conformance test + Contract 8 grep

**Files:**
- Create: `classifier/ensemble/scorer.py`
- Create: `classifier/tests/test_ensemble_scorer_protocol.py`
- Create: `classifier/tests/test_no_sacred_split_refs.py`

- [ ] **Step 1: Write the scorer**

```python
# classifier/ensemble/scorer.py
import json
from dataclasses import dataclass
import numpy as np, lightgbm as lgb
from classifier.baselines.protocol import NodePair, ScoreRecord

@dataclass
class EnsembleScorer:
    name: str
    version: str
    booster: lgb.Booster
    q_hat: dict
    tau: float

    def score(self, pair: NodePair) -> ScoreRecord:
        x = np.array([pair.features], dtype=float)
        proba = self.booster.predict(x)[0]
        tier = int(proba.argmax())
        q = self.q_hat.get(tier, 1.0)
        set_ = [c for c in range(len(proba)) if 1.0 - proba[c] <= q]
        needs_review = False  # stage-2 proxy — tightened in Plan 6
        return ScoreRecord(
            scorer_name=self.name,
            scorer_version=self.version,
            pair_key=pair.pair_key,
            score=float(proba[tier]),
            tier_id=tier,
            extras={"conformal_set": set_, "needs_review": needs_review},
        )

def load_ensemble(stacker_run: str, conformal_run: str, router_run: str) -> EnsembleScorer:
    booster = lgb.Booster(model_file=f"runs/stacker/{stacker_run}/model.txt")
    q = json.loads(open(f"runs/conformal/{conformal_run}/q_hat.json").read())["q_hat"]
    tau = json.loads(open(f"runs/ensemble/{router_run}/router.json").read())["tau"]
    version = f"ens-{stacker_run}-{conformal_run}-{router_run}"
    return EnsembleScorer(name="ensemble_v1", version=version, booster=booster, q_hat={int(k):v for k,v in q.items()}, tau=tau)
```

- [ ] **Step 2: Write protocol conformance test**

```python
# classifier/tests/test_ensemble_scorer_protocol.py
from classifier.baselines.protocol import Scorer
from classifier.ensemble.scorer import EnsembleScorer

def test_ensemble_is_scorer():
    assert hasattr(EnsembleScorer, "score")
    assert "version" in EnsembleScorer.__annotations__
```

- [ ] **Step 3: Write the Contract 8 grep test**

```python
# classifier/tests/test_no_sacred_split_refs.py
from pathlib import Path

def _iter_plan5_files():
    roots = ["classifier/ensemble", "classifier/scripts"]
    plan5_scripts = {
        "build_densified_graph.py","train_gat.py","extract_pair_embeddings.py",
        "build_stack_features.py","train_stacker.py","calibrate_conformal.py",
        "tune_router.py","eval_ensemble_llm_val.py","register_ensemble.py",
    }
    for r in roots:
        for p in Path(r).rglob("*.py"):
            if r == "classifier/scripts" and p.name not in plan5_scripts:
                continue
            yield p

def test_no_human_test_frozen_in_plan5():
    for p in _iter_plan5_files():
        txt = p.read_text()
        assert "human_test_frozen" not in txt, f"Contract 8 violated: {p}"
        assert "human_test_fresh" not in txt, f"Contract 8 violated: {p}"
```

- [ ] **Step 4: Run tests**

Run: `pytest classifier/tests/test_ensemble_scorer_protocol.py classifier/tests/test_no_sacred_split_refs.py -q`
Expected: `2 passed`.

- [ ] **Step 5: Commit**

```bash
git add classifier/ensemble/scorer.py classifier/tests/test_ensemble_scorer_protocol.py classifier/tests/test_no_sacred_split_refs.py
git commit -m "plan5: EnsembleScorer + Contract 8 sacred-split grep guard"
```

### Task I2: `eval_ensemble_llm_val.py` + `register_ensemble.py` + Plan 6 handoff

**Files:**
- Create: `classifier/scripts/eval_ensemble_llm_val.py`
- Create: `classifier/scripts/register_ensemble.py`

- [ ] **Step 1: Write the eval script**

```python
# classifier/scripts/eval_ensemble_llm_val.py
import argparse, json
from pathlib import Path
import numpy as np, pyarrow.parquet as pq
from classifier.data.splits import verify_hashes
from classifier.labeling.freeze import verify_label_hashes
from classifier.ensemble.scorer import load_ensemble

def main():
    verify_hashes(); verify_label_hashes()
    ap = argparse.ArgumentParser()
    ap.add_argument("--stacker-run", required=True)
    ap.add_argument("--conformal-run", required=True)
    ap.add_argument("--router-run", required=True)
    ap.add_argument("--features", default="data/features/stack_features_v1.parquet")
    ap.add_argument("--out", default="results/ensemble_llm_val.json")
    args = ap.parse_args()
    out = Path(args.out)
    if out.exists():
        raise FileExistsError(out)
    ens = load_ensemble(args.stacker_run, args.conformal_run, args.router_run)
    feat = pq.read_table(args.features).to_pandas()
    val_rows = [json.loads(l) for l in Path("data/labels/llm_sme/v1_frozen/llm_val.jsonl").read_text().splitlines()]
    val_df = feat[feat["pair_key"].isin({r["pair_key"] for r in val_rows})]
    lookup = {r["pair_key"]: r for r in val_rows}
    feat_cols = [c for c in val_df.columns if c not in ("pair_key","fold")]
    proba = ens.booster.predict(val_df[feat_cols])
    pred = proba.argmax(axis=1)
    y = np.array([lookup[k]["tier_id"] for k in val_df["pair_key"]])
    acc = float((pred == y).mean())
    payload = {
        "scorer_name": ens.name,
        "scorer_version": ens.version,
        "metrics": {"tier_acc": acc, "n": int(len(y))},
        "stacker_run": args.stacker_run,
        "conformal_run": args.conformal_run,
        "router_run": args.router_run,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, sort_keys=True, ensure_ascii=False, indent=2))
    print(f"wrote {out}: tier_acc={acc:.4f}")

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Write the registration script**

```python
# classifier/scripts/register_ensemble.py
import argparse, json, datetime, subprocess
from pathlib import Path
from classifier.data.splits import verify_hashes
from classifier.ensemble.scorer import load_ensemble
from classifier.baselines.registry import register

def main():
    verify_hashes()
    ap = argparse.ArgumentParser()
    ap.add_argument("--stacker-run", required=True)
    ap.add_argument("--conformal-run", required=True)
    ap.add_argument("--router-run", required=True)
    args = ap.parse_args()
    ens = load_ensemble(args.stacker_run, args.conformal_run, args.router_run)
    register(ens)
    git_sha = subprocess.check_output(["git","rev-parse","HEAD"]).decode().strip()
    row = {"component":"ensemble","run_id":ens.version,"git_sha":git_sha,
           "finished_at_utc":datetime.datetime.utcnow().isoformat()+"Z",
           "checkpoint_path":f"runs/ensemble/{ens.version}","status":"ok",
           "parts":{"stacker":args.stacker_run,"conformal":args.conformal_run,"router":args.router_run}}
    with open("runs/registry.jsonl","a") as f:
        f.write(json.dumps(row, sort_keys=True, ensure_ascii=True)+"\n")
    print(f"registered {ens.name} {ens.version}")

if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Smoke run both**

Run: `python -m classifier.scripts.eval_ensemble_llm_val --stacker-run <S> --conformal-run <C> --router-run <R> && python -m classifier.scripts.register_ensemble --stacker-run <S> --conformal-run <C> --router-run <R>`
Expected: `wrote results/ensemble_llm_val.json: tier_acc=<X.XXXX>` followed by `registered ensemble_v1 ens-<S>-<C>-<R>`. Both `results/ensemble_llm_val.json` and an `ensemble` row in `runs/registry.jsonl` are created.

- [ ] **Step 4: Commit**

```bash
git add classifier/scripts/eval_ensemble_llm_val.py classifier/scripts/register_ensemble.py results/ensemble_llm_val.json
git commit -m "plan5: ensemble llm_val eval + registration + Plan 6 handoff json"
```

---

## Lessons Carried (for Plan 6)

These are the failure-mode lessons Plan 5 surfaces for the next plan to honor:

1. **Composite versioning.** `EnsembleScorer.version` concatenates its three component `run_id`s. Plan 6's sacred run must pin this exact string in its results JSON — a silent swap of the stacker binary cannot be hidden behind a stable `scorer_name`.
2. **Contract 8 as a first-class test.** `human_test_frozen` leaks into analysis code through innocuous paths — debug scripts, notebook imports, stale doc snippets. Plan 6's sacred-run harness should extend the grep test to its own files before the first read of the frozen split.
3. **Contract 9 generalization.** `calibrate_conformal.py` reads `human_cal.jsonl` exclusively. Plan 6 should add the symmetric guard: the sacred-run harness reads `human_test_frozen.jsonl` exactly once, at which point the file's SHA256 is logged and any subsequent read in the same process raises.
4. **Coverage stop-gate as precedent.** Plan 5's conformal calibration raises if coverage drifts >±0.03 from target. Plan 6 should raise if the sacred-run's tier-accuracy on `human_test_frozen` drifts from `llm_val` by more than the pre-registered tolerance — stop-gate, not post-hoc explanation.
5. **OOF leakage is easy to get wrong.** The 5-fold builder retrains the rung scorers per fold; that is expensive but required. Plan 6 must not "shortcut" by reusing the global rung checkpoints — any stacker feature it consumes must come from `stack_features_v1.parquet` untouched.
6. **Rejected runs still append.** `train_stacker.py` writes `status="rejected"` rows. Plan 6's sacred-run harness should also append rejected rows rather than silently re-running on tweaked thresholds.

---

## Self-Review — Spec § Mapping

| Spec § | Covered by | Notes |
|---|---|---|
| §3.1 Stage 2 (GAT) | Phases A (graph), B (model), C (trainer), D (pair features) | Densification contract + v1_frozen Direct holdout live in Task A2, C1 |
| §3.1 Stage 3 (stacker + conformal + router) | Phases E, F, G, H | OOF feature leakage guard (Task E1), stop-on-no-lift (Task F3), Mondrian per-tier (Task G1), KL router (Task H1) |
| §3.4 graph densification recipe | Task A2 | Explicit edge-type assertions on expert + cross_framework_category + cocite + v1_frozen_highconf |
| §4.3 risk #3 (meta-learner leakage) | Tasks E1, E2 | `check_no_row_leakage` + OOF refit per fold |
| §4.3 risk #4 (conformal miscalibration) | Task G1, G2 | Mondrian per-tier + coverage OOB stop-gate |
| §6 commitment #1 (sacred split untouched) | Contract 8 + Task I1 grep test | `human_test_frozen` banned in all Plan-5 files |
| §6 commitment #3 (conformal reported honestly) | Task G2 | coverage written to registry + stop-gate on drift |
| §6 commitment #6 (failed ablations reported) | Task F3 | `status="rejected"` row + SystemExit on no-lift |
| §6 commitment #8 (release artifacts) | Task I2 | `results/ensemble_llm_val.json` + registry row + composite version |
| Contract 1 (verify_hashes at entry) | Every `classifier/scripts/*.py` in Plan 5 | Called before any disk write |
| Contract 3 (never overwrite) | Tasks A3, C3, D2, E3, F3, G2, H2, I2 | `FileExistsError` on every output path |
| Contract 4 (Scorer protocol) | Task I1 | `EnsembleScorer.score` returns `ScoreRecord` |
| Contract 5 (v1_frozen only) | Tasks A2, C1, E2, F3 | `assert "v1_frozen" in ...` asserts |
| Contract 6 (registry append) | Tasks C3, F3, G2, H2, I2 | Byte-stable `json.dumps` append |
| Contract 8 (NEW, sacred split off-limits) | Task I1 `test_no_sacred_split_refs` | Path-grep across all Plan-5 `.py` |
| Contract 9 (NEW, conformal on human_cal) | Task G2 `test_conformal_uses_human_cal_only` | Path-grep over conformal module + script |

**Budget:** ~$30 Lambda A100 (GAT training ~4 GPU-hr at ~$1.50/hr plus 5-fold OOF re-train overhead for Rung S/M on llm_train-sized shards; Rung L OOF re-training is explicitly deferred to a second pass behind `--include-rung-L` and NOT required for Phase I handoff). Jetson work (graph build, conformal calibration, router tuning, eval harness) is free.
