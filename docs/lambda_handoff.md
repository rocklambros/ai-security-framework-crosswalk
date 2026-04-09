# Lambda A100 Handoff — Plan 5 Completion

**Date:** 2026-04-09
**Status:** Jetson pipeline dry-run complete. GAT + retrain blocked on Lambda.

## Why Lambda is Required

The current ensemble (3 features: BM25, BGE cosine, bridge) exhibits **majority-class collapse** — it predicts everything as "related" (class 2, 74.4% of val data). Per-class accuracy: unrelated 0%, partial 0%, related 99.6%, equivalent 0%. The 74.4% val accuracy equals the class prior; the model has no real discriminative power.

The GAT structural embeddings are expected to provide the graph-topology signal needed to distinguish minority classes. Without them, the sacred run (Plan 6) would be wasted — it's one-shot and irreversible.

## Current State on Main

- **115 tests pass**, 1 skip (GAT on Jetson)
- Stacker trained at `runs/stacker/stacker-b45bdc0c-20260409T143944/`
- Conformal calibrated, router tuned (on 3-feature model)
- Plan 6 Phase 0 infrastructure committed (pre_registered loader, cal loader, methodology note)
- All code committed through `53e6057`

## Lambda TODO (in order)

### 1. Install torch_geometric

```bash
pip install torch_geometric pyg_lib torch_scatter torch_sparse torch_cluster torch_spline_conv -f https://data.pyg.org/whl/torch-2.8.0+cu124.html
```

Verify: `python -c "import torch_geometric; print(torch_geometric.__version__)"`

### 2. Run GAT tests

```bash
python -m pytest classifier/tests/test_gat_model.py -v
```

Expected: 2 tests pass (forward shape + backward flow). These skip on Jetson.

### 3. Train GAT on densified graph

The densified graph has 983 nodes and 6,684 edges (5,767 original + 917 v1_frozen high-conf).

```python
from classifier.ensemble.graph import build_densified_graph
from classifier.ensemble.gat_model import GATEncoder
# Build graph, convert to PyG Data, train GATv2
# Save node embeddings to data/features/gat_embeddings.npz
```

Key parameters (from pre_registered.json → seeds.ensemble_seed = 20260408):
- hidden_dim=64, out_dim=32, heads=4, num_layers=2, dropout=0.3
- Train with link prediction or node classification on the densified graph
- Save learned node embeddings

### 4. Generate pair-level GAT features

For each (source, target) pair in v1_frozen labels:
- Look up source and target node embeddings from the trained GAT
- Compute: cosine similarity, L2 distance, element-wise product, concatenation
- The simplest approach: `score_gat = cosine_sim(emb[src], emb[tgt])`

Add `score_gat` to the feature matrix in `classifier/ensemble/oof_features.py`.

### 5. Update FEATURE_COLS

In `classifier/ensemble/stacker.py`:
```python
FEATURE_COLS = ["score_bge_cosine", "score_bm25", "score_bridge", "score_gat"]
```

### 6. Retrain stacker with 4 features

```bash
python -m classifier.scripts.train_stacker
```

This will:
- Build feature matrix with GAT features
- Run 20-trial Optuna search
- Train final model on llm_train
- Evaluate on llm_val
- Save to `runs/stacker/stacker-<new_id>/`

**Expected improvement:** Minority class discrimination (unrelated, partial, equivalent should have non-zero accuracy).

### 7. Recalibrate conformal + router

```bash
python -m classifier.scripts.calibrate_ensemble runs/stacker/stacker-<new_id>
```

### 8. Evaluate

```bash
python -m classifier.scripts.eval_ensemble runs/stacker/stacker-<new_id>
```

**Go/no-go criteria:**
- tier_acc > 0.75 (must beat majority-class baseline)
- At least 2/4 classes have non-zero per-class accuracy
- MRR > 0.86

### 9. Verify before Plan 6

```bash
python -m pytest classifier/tests/ -x --tb=short -q  # all pass
```

Only proceed to Plan 6 (sacred run) when the ensemble has real discriminative power across all 4 tiers.

## Files Lambda Will Modify

| File | Change |
|------|--------|
| `classifier/ensemble/oof_features.py` | Add GAT embedding lookup to `build_feature_matrix()` |
| `classifier/ensemble/stacker.py` | Add `score_gat` to `FEATURE_COLS` |
| `data/features/gat_embeddings.npz` | NEW: trained GAT node embeddings |
| `runs/stacker/stacker-<new>/` | NEW: retrained stacker run |

## Files Lambda Must NOT Modify

- `data/splits/human_test_frozen.jsonl` (Contract 8)
- `data/splits/hashes.json` (unless adding GAT hash)
- `data/labels/llm_sme/v1_frozen/` (Contract 5)
- `classifier/sacred/pre_registered.json` (Contract 15)
- Any Plan 1/1-B/2/3/4 artifacts

## After Lambda Completes Plan 5

The sequence is:
1. Plan 6: Sacred run + ablations (one-shot on human_test_frozen)
2. Plan 7: Dash app + HF Space
3. Plan 8: Writeup and publish
