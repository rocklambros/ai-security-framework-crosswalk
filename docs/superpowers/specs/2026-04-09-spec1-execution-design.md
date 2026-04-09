# Spec 1 Execution: ML Pipeline Training & Project 1 Notebook

## Goal

Execute the Spec 1 ML pipeline end-to-end on Lambda Cloud GPUs, producing trained cross-encoder models, a retrained GATv2, a calibrated two-stage stacker, sacred evaluation metrics, and a COMP 4433 Project 1 notebook that meets full rubric requirements.

## Architecture

Hybrid execution: CPU phases run locally on the Jetson Orin, GPU phases run on Lambda Cloud. A 1x A10 instance starts immediately for initial training; a background poller auto-provisions 2x H100 SXM5 when available for the heavy fine-tuning and GAT work. WANDB tracks all experiments under project `crosswalk-v2`. Results flow back to the repo via rsync, populating the notebook and Dash app with real metrics.

## Constraints

- **Lambda GPU scarcity:** H100s are frequently sold out. The A10 (24GB) is available now. Design must tolerate starting on A10 and migrating to H100 mid-pipeline.
- **COMP 4433 rubric:** Notebook must use matplotlib/seaborn only (no Plotly). Must include multi-plot figure with differentially sized axes, 3+ plot types, on-plot annotation, narrative discussion, fine-tuned aesthetics.
- **Deadline:** ASAP.
- **Budget:** 2x H100 at $8.38/hr for ~5-7 hours (~$50 max). A10 at $1.29/hr while waiting.

---

## Section 1: Lambda Provisioning & Automation

### 1.1 Provisioning Script

`classifier/lambda/provision.py`:

- `provision_instance(instance_type, region=None)` — calls Lambda API to launch an instance with SSH key "jetson". Returns instance ID and IP.
- `poll_for_instance(instance_type, interval=60)` — loops until the requested instance type has capacity, then provisions it. Writes status to `runs/lambda_status.json`.
- `terminate_instance(instance_id)` — tears down a running instance.
- `get_instance_status(instance_id)` — checks if instance is running/terminated.

All API calls use `pass lambda/api-key` for authentication.

### 1.2 Bootstrap Script

`classifier/lambda/bootstrap.sh`:

```
#!/bin/bash
# Run on Lambda instance after SSH connection established
set -euo pipefail

# Clone repo (or pull if already present from rsync)
if [ -d ~/crosswalk/.git ]; then
    cd ~/crosswalk && git pull
else
    git clone https://github.com/rocklambros/ai-security-framework-crosswalk.git ~/crosswalk
    cd ~/crosswalk
fi

# Install deps
pip install -r classifier/lambda/requirements-lambda.txt

# Login to WANDB and HuggingFace (keys passed as env vars via SSH)
wandb login "$WANDB_API_KEY"
huggingface-cli login --token "$HF_TOKEN"

# Pre-download models
python -c "
from transformers import AutoTokenizer, AutoModel
for m in ['microsoft/deberta-v3-large', 'roberta-large', 'google/electra-large-discriminator']:
    AutoTokenizer.from_pretrained(m)
    AutoModel.from_pretrained(m)
"
```

### 1.3 Launch Orchestrator

`classifier/lambda/launch.py` — local script that:

1. Provisions A10 immediately
2. SSHs in, runs bootstrap, starts Phase 2 + Phase 3 (ELECTRA first, smallest)
3. Kicks off H100 poller in background
4. When H100 arrives: provisions, bootstraps, rsyncs A10 checkpoints to H100, starts remaining phases
5. On completion: rsyncs all artifacts home, terminates both instances

SSH commands use `subprocess` with the "jetson" key. Credentials injected via:
```
ssh -o SendEnv=WANDB_API_KEY,HF_TOKEN ubuntu@{ip} ...
```

---

## Section 2: Training Pipeline (9 Phases)

### Phase 1: Build Expert Training Set (CPU, local)

- Run `classifier/scripts/build_expert_training.py`
- Reads `data/upstream/mappings_v1.jsonl` (3,210 rows)
- Applies tier mapping, text enrichment, hard negative mining
- Leakage firewall pre-flight check
- Output: `data/processed/expert_training_v2.parquet`

### Phase 2: Contrastive Pre-Training (GPU, A10)

- Run `classifier/ensemble/contrastive_pretrain.py` for each of 3 base models
- Supervised SimCSE: positive pairs from expert mappings, negatives from hard mining
- 3-5 epochs, batch size 64 (A10 can handle base model + contrastive head)
- Output: `runs/ce_v2/contrastive/{model}_simcse.pt` per model
- WANDB group: `contrastive-pretrain`

### Phase 3: Cross-Encoder Fine-Tuning Sweeps (GPU, A10 → H100)

- 50 Bayesian trials per model via WANDB sweeps
- Hyperband early termination (eta=3, min_iter=3 epochs)
- Sweep parameters: learning_rate, batch_size, epochs, warmup_ratio, weight_decay, dropout
- Objective: `val_macro_f1`
- CORN ordinal loss for all models
- A10 starts with ELECTRA (fits in 24GB), then DeBERTa (tight with fp16 + grad checkpointing)
- H100 takes over remaining models when available
- WANDB tracks trial completion — H100 skips already-finished trials
- Output: `runs/ce_v2/{model}/best_model.pt` per model
- WANDB groups: `ce-deberta`, `ce-roberta`, `ce-electra`

### Phase 4: Extract CLS Embeddings (GPU, H100)

- Load each fine-tuned encoder
- Run inference over all control texts to extract [CLS] embeddings
- Compute pairwise CLS similarity features
- Output: 12 CE logit columns + 3 CLS sim columns per pair

### Phase 5: GATv2 Retrain (GPU, H100 required)

- Train GATv2 on the framework-control graph with 64-dim node embeddings
- Uses updated graph with enriched text features
- Output: `runs/gat_v2/model.pt`, 64-dim diff features + 2 scalar features per pair

### Phase 6: LightGBM Stacker Sweep (CPU)

- Optuna Bayesian optimization, logged to WANDB group `stacker-optuna`
- 83 V2 features: 12 CE logits + 3 CLS sims + 64 GAT diffs + 2 GAT scalars + 2 baselines
- 5-fold stratified CV
- Output: `runs/stacker_v2/model.txt`

### Phase 7: Two-Stage Classifier Fit (CPU)

- Stage 1: Binary (mapped vs unmapped), high-recall threshold (~0.95)
- Stage 2: Ordinal (equivalent/related/partial) on positives
- Output: `runs/stacker_v2/two_stage/stage1.txt`, `stage2.txt`, `config.json`

### Phase 8: Mondrian Conformal Calibration (CPU)

- Calibrate on `human_cal.jsonl` split
- Mondrian: per-class conformal sets
- Target marginal coverage: 0.90
- Output: `runs/stacker_v2/conformal.json`

### Phase 9: Sacred Evaluation + Ablation Matrix (CPU)

- Evaluate on frozen test set (`human_test_frozen.jsonl`)
- Run 6 V2 ablation configs: ce_deberta_only, ce_deberta_corn, ce_plus_gat, multi_ce, full_v2, full_v2_two_stage
- Git-state enforcement (Contract 10)
- Output: `results/sacred/sacred_{sha}.json`, `results/ablations_v2.json`
- Baseline to beat: macro_f1 0.226, tier_accuracy 0.373

---

## Section 3: WANDB Configuration

- **Project:** `crosswalk-v2`
- **Entity:** None (personal account)

**Sweep groups:**

| Group | Method | Trials | Objective | Early Term |
|-------|--------|--------|-----------|------------|
| `contrastive-pretrain` | Fixed | 3 runs | — | — |
| `ce-deberta` | Bayes | 50 | val_macro_f1 ↑ | Hyperband η=3, min=3 |
| `ce-roberta` | Bayes | 50 | val_macro_f1 ↑ | Hyperband η=3, min=3 |
| `ce-electra` | Bayes | 50 | val_macro_f1 ↑ | Hyperband η=3, min=3 |
| `stacker-optuna` | Bayes | 50 | oof_macro_f1 ↑ | — |

**Metrics per CE trial:** val_macro_f1, val_tier_accuracy, val_logloss, train_loss/epoch, learning_rate, best_epoch

**Artifacts:** Best model checkpoint per sweep (WANDB artifact), confusion matrix, training curves.

---

## Section 4: Checkpoint Management & Handoff

### A10 → H100 Migration

When the H100 poller succeeds:

1. SSH into A10, `tar` completed checkpoints: `runs/ce_v2/`
2. `scp` tarball to H100 (or pull from local machine)
3. H100 resumes WANDB sweeps — already-completed trials are skipped (WANDB sweep agent tracks state)
4. A10 can continue running if a sweep is mid-trial, or terminate

### Lambda → Local Rsync

On pipeline completion:

```bash
rsync -avz ubuntu@{h100_ip}:~/crosswalk/runs/ ./runs/
rsync -avz ubuntu@{h100_ip}:~/crosswalk/results/ ./results/
```

Then terminate all Lambda instances.

### Artifact Inventory (Post-Pipeline)

```
runs/ce_v2/deberta/best_model.pt
runs/ce_v2/roberta/best_model.pt
runs/ce_v2/electra/best_model.pt
runs/ce_v2/contrastive/{model}_simcse.pt  (×3)
runs/gat_v2/model.pt
runs/stacker_v2/model.txt
runs/stacker_v2/two_stage/stage1.txt
runs/stacker_v2/two_stage/stage2.txt
runs/stacker_v2/two_stage/config.json
runs/stacker_v2/conformal.json
results/sacred/sacred_{sha}.json
results/ablations_v2.json
```

---

## Section 5: COMP 4433 Project 1 Notebook

### 5.1 Rubric Requirements

Per COMP_4433_Project_1.md:

- **Library constraint:** matplotlib, seaborn, numpy, pandas, sklearn, statsmodels only. No Plotly. Request instructor approval for lightgbm if referenced.
- **At least one multi-plot figure** with differentially sized axes (GridSpec)
- **At least three different plot types** from matplotlib/seaborn
- **At least one on-plot annotation**
- **Narrative explanation** of each plot (intent before, observations after)
- **Fine-tuned aesthetics** — minimal clutter, appropriate color, proper labels/titles/legends
- **Discussion of analytical approaches** applicable to the data
- **Discussion of anomalies, trends, observations of interest**
- **Conclusion and future work** section (teasing Project 2: Dash visualization app)

### 5.2 Notebook Rewrite

The existing `notebooks/project1_exploratory.ipynb` (Plotly-based) must be **completely rewritten** using matplotlib/seaborn.

**Tone:** First person, conversational but technically rigorous. "I chose this dataset because..." not "The dataset was selected due to...". Engaging for a scientific audience without being stuffy.

**Code comments:** Every code cell has detailed inline comments explaining what each block does and why. Not just `# load data` — more like `# Load the 3,210 expert-curated mappings from v1 of the crosswalk dataset`.

### 5.3 Notebook Structure

**Section 1: Introduction & Problem Statement** (markdown)
- First-person framing: why I chose this dataset, what problem it addresses
- 14 frameworks, 3,210 expert-curated cross-framework mappings
- Four-tier ordinal classification: unrelated < partial < related < equivalent
- What we hope to learn from exploring this data

**Section 2: Data Loading & Initial Exploration**
- Load `mappings_v1.jsonl` into DataFrame
- Shape, dtypes, head(), describe()
- Missing data assessment
- Value counts for tier, scope, framework columns

**Section 3: Distribution Analysis**
- **Plot 1:** Violin/box plots of BM25 scores by tier (seaborn `violinplot`)
- **Plot 2:** Histogram/KDE of bridge graph scores (seaborn `histplot` with `kde=True`)
- Narrative on how score distributions differ across tiers
- Discussion of class imbalance (unrelated is the majority class)

**Section 4: Framework Coverage & Relationships**
- **Plot 3: Multi-plot figure with GridSpec** — large heatmap (left, 2/3 width) showing framework-pair mapping counts + small stacked bar (right top) showing tier composition per framework + small horizontal bar (right bottom) showing total controls per framework. Differentially sized axes.
- **On-plot annotation** on the heatmap: call out the densest framework pair and the sparsest
- Discussion of which framework pairs have the most/least coverage

**Section 5: Feature Correlations & Relationships**
- **Plot 4:** Correlation heatmap of numeric features (seaborn `heatmap` with mask for upper triangle)
- **Plot 5:** Pairplot or scatter matrix of key features colored by tier (seaborn `pairplot`)
- Discussion of which features discriminate well between tiers

**Section 6: Model Architecture Overview** (markdown + code)
- Description of the v2 multi-encoder ensemble pipeline
- CORN ordinal loss explanation with mathematical formulation
- 83-feature stacker breakdown
- Two-stage classification rationale
- This section addresses the rubric's "analytical approaches" requirement

**Section 7: Training Results & Evaluation**
- Reads `results/sacred/sacred_{sha}.json` and `results/ablations_v2.json`
- **Plot 6:** Confusion matrix (seaborn `heatmap`, row-normalized, annotated)
- **Plot 7:** Grouped bar chart of ablation results (matplotlib `bar` with grouped bars for tier_accuracy and macro_f1 across 6 ablation configs)
- Narrative comparing v1 baseline (macro_f1: 0.226) to v2 results
- Discussion of which components contribute most (ablation analysis)

**Section 8: Conclusion & Future Work** (markdown)
- Summary of key findings from the exploratory analysis
- What the data tells us about cross-framework mapping feasibility
- Anomalies and trends of interest
- Future work: Project 2 will build an interactive Dash visualization app with network graphs, coverage dashboards, and real-time model performance monitoring
- Potential extensions: active learning, additional frameworks, conformal prediction refinement

### 5.4 Visual Style

- **Color palette:** Use a consistent seaborn palette throughout (e.g., `"husl"` or custom 4-color palette for tiers)
- **Tier colors:** Consistent across all plots — green (equivalent), blue (related), amber (partial), red (unrelated)
- **Figure sizing:** `plt.figure(figsize=(12, 8))` or similar for readability
- **Despined axes:** `sns.despine()` on all applicable plots
- **No unnecessary gridlines** — only where they aid reading
- **Font sizes:** Titles 14pt, axis labels 12pt, tick labels 10pt
- **Tight layouts:** `plt.tight_layout()` or `constrained_layout=True`

### 5.5 Deliverable

Zip file containing:
- `project1_crosswalk_eda.ipynb` (the notebook)
- `data/` folder with `mappings_v1.jsonl` and any processed files the notebook reads
- `results/` folder with sacred and ablation JSON files
- No model checkpoint files (too large) — notebook reads metric summaries only

---

## Section 6: Execution Timeline

| Step | What | Where | Est. Time |
|------|------|-------|-----------|
| 0 | Provision A10, start H100 poller | Local | 2 min |
| 1 | Phase 1: Build training set | Local (CPU) | 5 min |
| 2 | Phase 2: Contrastive pre-training | A10 | 30-60 min |
| 3 | Phase 3a: Fine-tune ELECTRA (50 trials) | A10 | 2-3 hrs |
| 3b | Phase 3b: Fine-tune DeBERTa (50 trials) | A10 or H100 | 2-3 hrs |
| 3c | Phase 3c: Fine-tune RoBERTa (50 trials) | H100 | 2-3 hrs |
| 4 | Phase 4: Extract CLS embeddings | H100 | 30 min |
| 5 | Phase 5: GATv2 retrain | H100 | 1-2 hrs |
| 6 | Phase 6: Stacker sweep | Local or Lambda CPU | 30 min |
| 7 | Phase 7: Two-stage fit | Local | 5 min |
| 8 | Phase 8: Conformal calibration | Local | 5 min |
| 9 | Phase 9: Sacred eval + ablations | Local | 10 min |
| 10 | Rsync artifacts, terminate instances | Local | 5 min |
| 11 | Rewrite Project 1 notebook | Local | 1-2 hrs |

**Total wall-clock estimate:** 5-7 hours (GPU phases dominate, many overlap)
**Total Lambda cost estimate:** ~$30-50

---

## Section 7: Success Criteria

1. **All 9 phases complete** without error
2. **WANDB dashboard** shows 150 CE sweep trials + stacker sweep
3. **Sacred results** show improvement over v1 baseline (macro_f1 > 0.226, tier_accuracy > 0.373)
4. **Notebook meets all rubric items:** matplotlib/seaborn only, multi-plot GridSpec figure, 3+ plot types, on-plot annotation, first-person narrative, detailed comments, conclusion + future work
5. **Dash app** Model Performance page populated with real sacred/ablation data
6. **All Lambda instances terminated** after pipeline completes
