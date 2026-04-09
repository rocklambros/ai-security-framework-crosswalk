# Model Card: AI Security Framework Crosswalk Stacker

## Architecture

LightGBM multiclass meta-stacker over 38 features:

- **Baseline features (3):** BM25 lexical score, BGE-M3 cosine similarity, bridge score
- **GAT features (35):** GAT cosine similarity, L2 distance, dot product, and 32-dim difference vector from a 2-layer Graph Attention Network trained on the densified framework graph (983 nodes, 6383 edges)

The stacker outputs softmax probabilities over 4 tiers:
`{unrelated, partial, related, equivalent}`.

## Post-processing

- **Mondrian conformal wrapper:** Per-tier calibrated prediction sets at alpha=0.10 (90% target coverage). Provides set-valued predictions that contain the true tier with calibrated probability.
- **KL-divergence abstention router:** Flags low-confidence predictions as `needs_review` when the stacker's class distribution is close to uniform (KL divergence below tau).

## Training Data

- 26 framework pairs across 12 AI security and governance frameworks
- Labels: v1_frozen community-sourced silver labels (LLM SME pipeline, Plan 2)
- Calibration: human_cal split for conformal calibration (Contract 9)
- Evaluation: llm_val held-out split

## Evaluation Results

| Metric | Value |
|--------|-------|
| Tier Accuracy (full ensemble) | 0.636 |
| Macro F1 (full ensemble) | 0.395 |
| Conformal marginal coverage | 0.693 |
| Average conformal set size | 2.22 |
| Bootstrap 95% CI (macro F1) | [0.328, 0.420] |

### Ablation highlights

| Configuration | Tier Acc | Macro F1 |
|---------------|----------|----------|
| Full ensemble (38 features) | 0.636 | 0.395 |
| Drop BGE (no_bge) | 0.686 | 0.397 |
| GAT only (35 features) | 0.625 | 0.437 |
| Baseline only (3 features) | 0.546 | 0.313 |
| BM25 only (1 feature) | 0.285 | 0.188 |

## Limitations

- Minority classes (equivalent, unrelated) have low per-class accuracy due to class imbalance
- Silver labels from LLM pipeline may contain systematic biases not present in expert labels
- Conformal coverage is approximate; per-tier coverage ranges from 0.90 to 1.00
- The router abstains aggressively (all 400 eval pairs flagged needs_review in the sacred run), indicating the tau threshold may need tuning for production use
- GAT embeddings are frozen from a single training run; retraining on updated graph edges may shift predictions

## Intended Use

Research and exploratory cross-framework mapping for AI security practitioners. Not intended as a sole basis for compliance decisions.

## License

Model weights: CC BY-SA 4.0
