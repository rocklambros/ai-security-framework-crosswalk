# Spec 1: ML Pipeline Overhaul + Project 1 Notebook

## Summary

Replace the current LLM-trained GAT+LightGBM stacker pipeline with a multi-encoder ensemble (DeBERTa-v3-large + RoBERTa-large + ELECTRA-large) fine-tuned on the 3,210 upstream expert mappings. Add GATv2 retrained on expert-derived graph edges. Combine all signals in a LightGBM stacker with ordinal-aware loss. Recalibrate Mondrian conformal and KL-disagreement router. Validate with sacred run on human_test_frozen. Deliver a COMP 4433 Project 1 Jupyter notebook with matplotlib/seaborn exploratory visual analysis of the crosswalk data and model results.

All compute runs on Lambda H100 80GB (or 2xA100 fallback). All experiments tracked in WANDB.

## Problem Statement

The current pipeline trains on LLM-generated labels but evaluates on expert labels, producing a fatal distribution mismatch: tier_acc=37.25% on frozen test vs 65.17% on LLM-labeled val. The router abstains on 100% of test pairs. Conformal coverage is 69% (target 90%). Minority classes (equivalent, partial) are effectively unpredicted. The root cause is training data quality, not model architecture.

## Architecture

### Data Foundation

**Training data from upstream expert mappings (3,210 pairs in `data/upstream/mappings_v1.jsonl`):**

| Upstream Signal | 4-Class Label | Method |
|---|---|---|
| Foundational mapping, same scope | **equivalent** | Automated: scope="identical" or "direct" |
| Foundational mapping, broader scope | **related** | Automated: scope="broader" or "partial_overlap" |
| Expanded mapping | **partial** or **related** | User manually reviews ~200 samples to calibrate the automated mapping rule |
| Unmapped pairs (BM25 top-50 candidates with no upstream mapping) | **unrelated** | Hard negative mining |

**Hard negative mining:** BM25 retrieves plausible-looking pairs that experts did NOT map. These are more informative than random negatives.

**Expected yield:** ~2,800 training pairs + ~400 hard negatives = ~3,200 training examples, stratified across 4 classes.

**Active learning round (after initial training):** Model identifies ~150 most uncertain pairs from `data/candidates/pool_v1.jsonl`. User labels these. Retrain. Expected +2-5% accuracy.

### Leakage Firewall (Non-Negotiable)

All assertions run as an automated pre-flight check before every training job. Hard fail if any trips. Logged to WANDB.

- `human_test_frozen` (400 pairs): NEVER in training, NEVER as graph edges, NEVER in negative sampling pool
- `human_cal` (150 pairs): NEVER in training, used ONLY for Mondrian conformal calibration
- Graph construction: edges derived ONLY from training-split upstream mappings
- Negative sampling: exclude all pairs sharing a node with test/cal pairs
- Assertion code:
  ```
  assert intersection(train_pair_keys, test_pair_keys) == empty
  assert intersection(train_pair_keys, cal_pair_keys) == empty
  assert intersection(graph_edge_pairs, test_pair_keys) == empty
  assert intersection(negative_sample_nodes, test_cal_nodes) == empty
  ```

### Model Components

**Component 1: Contrastive Pre-Training (Lambda H100)**

- Supervised SimCSE on 3,210 expert pairs before classification fine-tuning
- Positive pairs: controls that share an upstream mapping (same tier). Negative pairs: controls from different framework pairs with no mapping.
- Trains all 3 encoder backbones (DeBERTa-v3-large, RoBERTa-large, ELECTRA-large)
- WANDB: contrastive loss curves, embedding UMAP visualizations, alignment/uniformity metrics
- Estimated time: ~3-4 hrs per model on H100 (~10-12 hrs total)

**Component 2: Cross-Encoder Classification Fine-Tuning (Lambda H100)**

Three cross-encoders fine-tuned independently:

| Model | Params | Base |
|---|---|---|
| DeBERTa-v3-large | 304M | Primary — disentangled attention excels at NLI-style tasks |
| RoBERTa-large | 355M | Secondary — strong general-purpose encoder |
| ELECTRA-large | 335M | Tertiary — replaced-token detection pre-training |

- Loss: CORN (Conditional Ordinal Regression Network) — respects unrelated < partial < related < equivalent ordering
- WANDB Sweeps per model: learning rate (1e-6 to 5e-5), batch size (32/64/128), epochs (3-15), warmup ratio, weight decay
- 30-50 sweep runs per model
- Output per model: 4-class logits + CLS embedding
- WANDB: loss curves, per-class F1 at each epoch, confusion matrix snapshots, gradient norms, early stopping on val loss
- Estimated time: ~15-20 min per run on H100, sweep = ~10-17 hrs per model (~30-50 hrs total)

**Component 3: Domain-Adaptive Pre-Training (DAPT) — Optional**

- Masked language modeling on all ~5,000 framework control texts before fine-tuning
- Adapts LM vocabulary to security framework domain
- WANDB: MLM loss, perplexity on held-out controls
- Estimated time: ~2-3 hrs on H100
- Include if wall-clock budget allows; skip if diminishing returns

**Component 4: Control Text Enrichment (Preprocessing, No GPU)**

- Append to each control's input text: parent control text, framework category, sibling control descriptions
- Enriched text used as input to all cross-encoders
- Free accuracy lift (+1-3%) with zero compute cost

**Component 5: GATv2 Retrained on Expert Graph (Lambda H100)**

- Graph: nodes = all framework controls (~983), edges = training-split upstream mappings ONLY
- Edge weights: equivalent=1.0, related=0.7, partial=0.4
- Architecture: GATv2, 2 layers, 4 attention heads, 128 hidden, 64-dim output embeddings
- Output: per-node 64-dim embeddings; pair features = L2 diff (64) + dot product (1) + cosine similarity (1) = 66 features
- WANDB: link prediction AUC, embedding UMAP, attention weight distributions
- Estimated time: ~1-2 hrs on H100

**Component 6: Ensemble Stacker (Lambda H100 for Optuna)**

- Input features:
  - DeBERTa logits (4) + CLS similarity (1) = 5
  - RoBERTa logits (4) + CLS similarity (1) = 5
  - ELECTRA logits (4) + CLS similarity (1) = 5
  - GAT pair features (L2 diff 64 + dot 1 + cosine 1) = 66
  - BM25 score (1) + bridge score (1) = 2
  - Total: ~83 features
- Model: LightGBM with ordinal-aware custom objective (adjacent-class penalty weighting)
- Training: 5-fold stratified OOF to prevent stacker overfitting
- WANDB Sweeps: n_estimators, max_depth, learning_rate, min_child_samples, reg_alpha/lambda
- WANDB: OOF confusion matrix, per-fold metrics, feature importance, SHAP values
- Estimated time: ~2-3 hrs on H100

**Component 7: Two-Stage Classification**

- Stage 1: Binary filter (mapped vs unmapped) — high-recall threshold to avoid false negatives
- Stage 2: Ordinal classifier (equivalent/partial/related) on positives only from Stage 1
- Both stages use the same ensemble features; separate LightGBM heads
- WANDB: Stage 1 precision/recall curve, Stage 2 ordinal accuracy on filtered set

**Component 8: Conformal + Router (Recalibrated)**

- Mondrian conformal on `human_cal` (150 pairs) with new stacker outputs
- Exchangeability now holds (train and cal both expert-labeled)
- Target: marginal coverage >= 90%, average set size <= 2.0
- KL-disagreement router re-tuned on new distribution
- WANDB: coverage curves, set size distributions, router precision-recall at varying tau

### Overfitting Detection

- OOF gap: flag if stacker train accuracy exceeds OOF accuracy by >10%
- Cross-encoder: early stopping on val loss, not train loss
- WANDB alerts: programmatic alerts for train/val divergence >5%

### Evaluation Protocol

**Sacred run (one-shot, no iteration):**

- Dataset: `human_test_frozen` (400 pairs)
- Metrics: tier_accuracy, macro_F1, per-class accuracy, per-class F1
- Conformal: marginal coverage (target >= 90%), average set size
- Router: abstention rate, precision on non-abstained
- Bootstrap 95% CI (10,000 resamples)
- WANDB: all metrics + confusion matrix + calibration reliability diagram as final run

**Ablation matrix (WANDB comparison table):**

| Config | Components | Expected tier_acc |
|---|---|---|
| Single CE (DeBERTa) | CE logits, argmax | 60-70% |
| CE + ordinal loss | CE + CORN | 63-73% |
| CE + GAT | CE logits + GAT diff, stacker | 65-75% |
| Multi-CE ensemble | 3x CE + stacker | 70-80% |
| Full ensemble | 3x CE + GAT + BM25 + bridge, stacker | 72-82% |
| Full + two-stage | Binary filter then ordinal | 75-85% |
| Full + active learning | above + 150 user-labeled uncertain pairs | 80-90% |
| Full + conformal | same tier_acc, coverage >= 90%, set size <= 2.0 | 80-90% |

### Lambda H100 Compute Budget

| Phase | Estimated Hours |
|---|---|
| Contrastive pre-training (3 models) | 10-12 |
| Classification fine-tuning + WANDB Sweeps (3 models) | 30-50 |
| DAPT (optional) | 2-3 |
| GAT retrain | 1-2 |
| Feature extraction (all models) | 1 |
| Stacker Optuna sweep | 2-3 |
| Ablation matrix (full) | 5-8 |
| Sacred run + evaluation | 0.5 |
| **Total** | **~52-80 hours** |

With H100 (~2-3x faster than A100 for transformer training), wall-clock is roughly 50-70% of these estimates.

### WANDB Project Structure

```
crosswalk-v2/
  contrastive-pretrain/     # SimCSE runs (3 models)
  ce-deberta-sweep/         # DeBERTa classification sweep
  ce-roberta-sweep/         # RoBERTa classification sweep
  ce-electra-sweep/         # ELECTRA classification sweep
  gat-retrain/              # GATv2 on expert graph
  stacker-sweep/            # LightGBM Optuna
  two-stage/                # Binary + ordinal heads
  ablations/                # Component ablation comparison
  sacred/                   # Final evaluation
```

All intermediate artifacts (checkpoints, embeddings, predictions, datasets) versioned as WANDB Artifacts.

## COMP 4433 Project 1: Jupyter Notebook

**Dataset:** The crosswalk data — 3,210 upstream expert mappings + 400 frozen test pairs + model predictions + feature distributions.

**Allowed libraries:** numpy, pandas, matplotlib, seaborn, statsmodels, sklearn (per COMP 4433 Project 1 constraints).

### Notebook Structure

1. **Data Overview**
   - Framework counts by source and target (seaborn countplot)
   - Mapping tier distribution (pie chart + bar chart)
   - Class balance visualization across framework pairs
   - Missing data analysis

2. **Feature Distributions**
   - BM25 scores by tier (violin plots)
   - Cross-encoder logits by tier (KDE plots)
   - GAT embedding norms by tier (box plots)
   - Feature correlation heatmap (seaborn heatmap)

3. **Relationship Analysis**
   - Cross-encoder score vs BM25 score, colored by tier (scatter + regression line)
   - Feature pair plots for top-5 most discriminative features (seaborn pairplot)
   - Tier separability via PCA/t-SNE of ensemble features (scatter)

4. **Framework Coverage Analysis**
   - Which framework pairs have most/fewest mappings (matplotlib bar, annotated)
   - Coverage heatmap with differentially-sized axes using GridSpec (matplotlib)
   - On-plot annotation: highlight the framework pair with lowest coverage and annotate with count

5. **Model Performance Deep Dive**
   - Confusion matrix before vs after pipeline overhaul (seaborn heatmap, side-by-side with GridSpec)
   - Per-class ROC curves (matplotlib multi-line)
   - Calibration reliability diagram (matplotlib)

6. **Ablation Comparison**
   - Grouped bar chart: tier_acc and macro_F1 across configs (matplotlib)
   - On-plot annotations: delta values between configs
   - Statistical significance via statsmodels (paired t-test or bootstrap)

7. **Anomalies, Trends, Observations**
   - Outlier detection in feature space (isolation forest from sklearn, visualized)
   - Label disagreement analysis (where model disagrees with expert)
   - Discussion of what further analytical approaches could leverage these data

### Project 1 Requirements Checklist

- [x] Real-world dataset (not built-in Seaborn): crosswalk data
- [x] Multiple plots with differentially-sized axes: GridSpec in sections 4 and 5
- [x] At least 3 different plot types: violin, heatmap, scatter, bar, KDE, ROC, pie (7+)
- [x] At least 1 on-plot annotation: delta annotations in ablation bars, coverage annotation
- [x] Analytical approaches discussion: cross-encoder ensemble for predicting unmapped pairs
- [x] Anomalies/trends/observations: per-section narrative + dedicated section 7
- [x] Narrative explanation: markdown cells between every plot

### Aesthetics

- Custom color palette: colorblind-safe (seaborn "colorblind" or curated WCAG-compliant palette)
- Reduced visual clutter: `sns.despine()`, minimal gridlines, no chartjunk
- Professional typography: consistent font sizes, LaTeX-style axis labels where appropriate
- Tight layouts: `constrained_layout=True` or `plt.tight_layout()`
- Consistent tier color coding across all plots: equivalent=#3fb950, related=#58a6ff, partial=#d29922, unrelated=#484f58

## Dependencies

- Spec 2 (Dash app) consumes the trained model artifacts and prediction outputs from this spec
- Active learning round requires user availability for ~150 label annotations
- Lambda H100 instance availability

## Success Criteria

1. Sacred run tier_acc >= 75% on human_test_frozen (400 pairs)
2. Macro F1 >= 0.60
3. Per-class accuracy: no class below 50% (especially equivalent and partial)
4. Conformal coverage >= 90% with average set size <= 2.0
5. Router abstention rate < 30% (was 100%)
6. All WANDB experiments tracked and reproducible
7. Project 1 notebook meets all COMP 4433 requirements
8. Zero leakage violations (automated assertions pass)
