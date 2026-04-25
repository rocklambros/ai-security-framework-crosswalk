# Notebook + Report + HuggingFace Redesign Spec

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Rebuild the Project 1 EDA notebook from scratch with a Problem-Solution narrative arc where OpenCRE/v8/v8b/v_final lead the story; rewrite the report to match; upload the v_final ensemble to HuggingFace with a perfect-score model card; compile everything and fix all errors.

**Architecture:** New notebook (~146 cells) built cell-by-cell as a fresh .ipynb, reusing ~73 existing code cells and writing ~73 new/rewritten narrative+code cells. Report (~4,500 words) mirrors the notebook arc. HuggingFace repo hosts 3 model checkpoints with an AIBOM-compliant model card.

---

## Part 1: Notebook Redesign

### Narrative Structure — "Problem-Solution Arc"

The notebook tells one story in five acts:

1. **The Data** (Sections 2-4, ~33 cells): Base EDA satisfying COMP 4433 requirements. Schema, marginals, missingness, framework landscape. Existing cells 2-33 reused intact.

2. **The Baseline and Its Failure** (Sections 5-6, ~25 cells): v7c pipeline presented lean — architecture, compressed feature analysis + importance, frozen test results, the EQUIVALENT F1=0.000 blind spot. Ordinal regression demonstrator. Ends with the pivot: "Where can I find more labeled data for this class?"

3. **The OpenCRE Discovery** (Sections 7-8, ~20 cells): Full EDA of OpenCRE pairs. Hop-distance distribution, link types, framework coverage matrix, contamination firewall. This is where the notebook gains energy. Disagreement mining concept and v8 data assembly.

4. **The Experiments and Their Failures** (Sections 9-10, ~20 cells): v8b collapse crisis (DeBERTa-large 100% single-class, stacker train=1.0/val=0.528). This IS the "anomalies" discussion COMP 4433 requires. Each failure motivates a specific architectural change.

5. **The Breakthrough** (Sections 11-13, ~30 cells): v_final architecture (mapping-level dedup, ordinal losses, softmax averaging). Full results: confusion matrices, per-class F1, bootstrap CIs, conformal coverage, individual model progression. Full-graph deployment of 4,001 scored edges. HuggingFace model reference and future-training instructions.

**Conclusion** (~4 cells) + **Appendix A: Pipeline History** (~8 cells) + **Appendix B: Style Guide** (~1 cell).

### Abstract Rewrite

The abstract leads with: "This notebook traces the development of a 4-class ordinal classifier for AI security framework crosswalks, from a baseline that scored 0% on its most important class to a 3-model ensemble that broke through." It summarizes the full arc (v7c blind spot, OpenCRE discovery, v8 disagreement mining, v8b collapse, v_final breakthrough) in ~400 words. v7c is described in two sentences as "the starting point." The numbers: macro F1 from 0.512 to 0.558, EQUIVALENT F1 from 0.000 to 0.400, 4,001 edges scored, conformal coverage >= 90% on all 4 classes.

### Plain English Rewrite

One paragraph in the same > blockquote style: "I built a tool that compares security controls... The first version could not identify equivalent controls at all. After discovering OpenCRE, a public database that already links these standards, I tried two approaches to add its data to training — both failed in instructive ways. The third attempt stripped the architecture down to a simple average of three models trained with ordinal-aware losses and got EQUIVALENT right for the first time."

### Cell Source Mapping

| New Section | Source Cells (current notebook) | Notes |
|---|---|---|
| 2: Setup | 2-4 | Keep as-is |
| 3: Dataset Overview | 6-19 | Keep as-is (14 cells) |
| 4: Framework Landscape | 20-33 | Keep as-is (14 cells) |
| 5: v7c Baseline | 34-37, 47-48, 51, 70-73, 82-83 | Compressed from 51 to ~15 code+narrative cells |
| 6: Uncertainty + Ordinal | 85-86, 90-91, 96-101 | Compressed from 18 to ~10 cells |
| 7: OpenCRE Discovery | 114-120 | Expanded from 7 to ~15 cells |
| 8: v8 Disagreement Mining | 121-125 | Expanded from 5 to ~10 cells |
| 9: v8b Collapse Crisis | 126-128 | Expanded from 3 to ~10 cells |
| 10: v_final Architecture | 130-135 | Expanded from 6 to ~8 cells |
| 11: v_final Results | 136-145 | Expanded from 10 to ~14 cells |
| 12: Deployment + Impact + HF | 146-149 | Expanded from 4 to ~10 cells (includes HF section) |
| 13: Conclusion | 150-152 | Rewritten (~4 cells) |
| App A: Pipeline History | 103-113 | Keep, minor updates (~8 cells) |
| App B: Style Guide | 5 | Move from Section 2 area to appendix |

### Cells Cut Entirely

- Cells 40-45 (GAT vs Node2Vec scatter, correlation matrix) — not essential for Problem-Solution arc
- Cells 54-68 (Coverage/Gaps/Orphans/UMAP — 15 cells) — coverage heatmaps already in Section 4; orphan/UMAP detail moved to v7c feature analysis if needed
- Cell 79 (duplicate GAT-only confusion matrix)
- Cells 87-89 (v6 conformal set sizes — replaced by v_final conformal)
- Cells 92-95 (what worked / future work / Project 2 preview — content moves to conclusion)

### New Cells Needed

**Section 7 (OpenCRE) — 3 new code cells:**
- Link-type distribution bar chart (Contains vs Related vs Linked To)
- Hop-distance vs classifier-tier cross-tab heatmap
- Framework-pair coverage bar chart for OpenCRE

**Section 8 (v8) — 2 new code cells:**
- Class distribution comparison (expert_train vs v8_train) grouped bar
- BGE cosine fallback distribution violin

**Section 9 (v8b) — 3 new code cells:**
- DeBERTa-large collapse rate bar chart
- Stacker probability histogram (99.8% mass at class 0)
- Per-model validation loss line chart — pull from WandB API (project: rockcyber/crosswalk-v8b; runs have train_loss/val_kl_loss/combined_f1 per epoch). Show collapse runs (n_unique_preds=1, combined_f1=0) alongside successful runs

**Section 11 (v_final Results) — 2 new code cells:**
- Adjacent-error direction bar chart
- Prediction confidence histogram (correct vs incorrect)

**Section 12 (Deployment) — 1 new code cell:**
- Framework-pair coverage improvement matrix (diff heatmap)

**Section 12 (HuggingFace) — 2 narrative cells (no code — just mention the model):**
- Markdown cell: HuggingFace repo URL, what's uploaded, how to grab it and use it
- Markdown cell: how to extend the crosswalk to new frameworks using the trained ensemble

### Visualization Compliance

Every figure must satisfy all four assigned readings:

| Principle | Source | Implementation |
|---|---|---|
| Position-on-common-scale | Cleveland & McGill (1984) | Bar/dot charts for comparisons |
| No rainbow/jet | Borland & Taylor (2007) | Sequential: `crest`, `Blues`, `Purples`. Diverging: `sns.diverging_palette(220, 20)` |
| Ordinal = luminance ramp | Borner et al. (2019) | `TIER_PALETTE` with 4 luminance-ordered blues |
| Categorical <= 6 colors | Graze & Schwabish (2024) | `FAMILY_COLOR` (3), `FRAMEWORK_PALETTE` (9 Okabe-Ito) |
| Active titles | Graze & Schwabish (2024) | Titles state the takeaway, not the variable |
| On-plot annotations | COMP 4433 requirement | Black arrow, 9-10 pt text, calls out specific finding |
| Code comments cite reading | Course requirement | Every figure code block references the perceptual principle |

**New cells (Sections 7-12) must match the citation density of Sections 3-4.** Every code cell gets:
- Comment block explaining chart type choice
- Citation of the reading that justifies it
- Annotation pointing to the key finding

### Writing Style Rules

Derived from existing Sections 3-4 of the notebook:

- First person singular: "I want to establish", "This tells me"
- Specific numbers always: "120 of the 130 Unrelated pairs"
- Figure purpose stated BEFORE the code cell, interpretation AFTER
- Plain English > blockquote after every major figure
- No AI slop vocabulary: no "delve", "robust", "tapestry", "testament", "vibrant", "showcasing", "not just X but also Y", "serves as", "stands as"
- No excessive em dashes (max 1-2 per paragraph)
- No rule-of-three adjective lists
- Code comments: descriptive, reference figure numbers, explain WHY not WHAT

### Libraries

Allowed: numpy, pandas, matplotlib, seaborn, statsmodels, sklearn, standard library (json, pathlib, collections, textwrap, warnings, yaml).

No new imports. All new visualizations use matplotlib/seaborn.

---

## Part 2: Report Redesign

### File: `report/report.md`

Complete rewrite (~4,500 words). Same Problem-Solution arc as the notebook. First-person, evidence-driven prose. Embeds figures from `report/figures/`.

**Sections mirror the notebook:**
1. Introduction (problem statement, dataset summary)
2. The v7c Baseline (compressed, focused on EQUIVALENT failure)
3. OpenCRE Discovery (hop distances, coverage, contamination firewall)
4. v8 Disagreement Mining
5. v8b Collapse Crisis
6. v_final Architecture
7. Results (confusion matrices, per-class F1, bootstrap CIs, conformal)
8. Full-Graph Deployment
9. HuggingFace Model and Reproducibility
10. Pipeline Lineage (table)
11. Conclusion

**Figures embedded:** All 15+ PNGs exported during notebook execution. New figures from expanded sections also exported.

**PDF compilation:** `pandoc report.md -o report.pdf --pdf-engine=pdflatex`. All Unicode replaced with LaTeX math mode. No warnings.

---

## Part 3: HuggingFace Model Upload

### Old Model Deletion

Delete `rockCO78/crosswalk-v7c` (the stale v7c sklearn model). Requires HF auth via `pass huggingface` token.

### New Model Repository

**Repo name:** `rockCO78/ai-security-crosswalk-vfinal`

**Contents uploaded:**
```
ai-security-crosswalk-vfinal/
  README.md                    # Model card (AIBOM-compliant)
  roberta/
    encoder/                   # config.json, model.safetensors, tokenizer files
    head.pt                    # Classification head weights
  deberta_base/
    encoder/
    head.pt
  bge/
    encoder/
    head.pt
  scripts/
    predict_edges.py           # Inference script (from scripts/predict_edges.py)
  examples/
    example_inference.py       # Minimal usage example
```

Total upload size: ~3.4 GB (1.4G RoBERTa + 704M DeBERTa + 1.3G BGE + heads + scripts).

### Model Card (README.md) — AIBOM Perfect Score Requirements

The model card must satisfy all fields in the aibom-generator scoring rubric:

**YAML Frontmatter:**
```yaml
license: apache-2.0
pipeline_tag: text-classification
tags:
  - security
  - ai-security
  - crosswalk
  - ordinal-classification
  - ensemble
  - pytorch
datasets:
  - custom
language:
  - en
metrics:
  - f1
  - accuracy
model-index:
  - name: ai-security-crosswalk-vfinal
    results:
      - task:
          type: text-classification
          name: Ordinal Tier Classification
        dataset:
          type: custom
          name: AI Security Framework Crosswalk
          split: test
        metrics:
          - type: f1
            value: 0.558
            name: Macro F1
          - type: accuracy
            value: 0.799
            name: Exact Accuracy
```

**Required Sections (for AIBOM compliance):**

1. **Model Description** — What it does, who built it, intended use
2. **Intended Use** — Primary: scoring cross-framework control mappings. Out-of-scope: general NLI
3. **Model Architecture** — 3-model ensemble (RoBERTa-large, DeBERTa-v3-base, BGE-large-v1.5) with softmax averaging
4. **Training Details**
   - Training data: 5,920 expert-labeled pairs + OpenCRE augmentation experiments
   - Preprocessing: mapping-level deduplication (56% contamination removed)
   - Hyperparameters: ordinal losses (KL, CORN, focal), learning rates, batch sizes, epochs
   - Training infrastructure: 3x H100 80GB GPUs, BF16 precision, ~4 hours total
5. **Evaluation Results** — Table with all metrics (exact acc, adjacent acc, macro F1, per-class F1, conformal coverage)
6. **Limitations and Biases** — Small test set (179 pairs, 7 EQUIVALENT), English-only frameworks, bootstrap CIs show wide intervals
7. **Ethical Considerations** — No personal data, no demographic bias risk, security-domain only
8. **Environmental Impact** — 3x H100 80GB at ~700W each for ~4 hours = ~8.4 kWh; estimated ~3.4 kg CO2e using US grid average (0.41 kg/kWh)
9. **How to Use** — Code snippet showing how to load and run inference
10. **How to Train on New Frameworks** — Step-by-step instructions for adding a 10th framework
11. **Citation** — BibTeX entry
12. **Safety and Risk Assessment** — Model outputs are advisory, not authoritative; human review required for compliance decisions

### Notebook Section for HuggingFace

New Section 12 subsection: "Model Availability and Reproducibility"

- Markdown cell: states the HuggingFace repo URL, describes what's uploaded, tells reader where to grab it and how to use it
- Markdown cell: "Training Additional Frameworks" — step-by-step instructions for extending the crosswalk to new frameworks

### Report Section for HuggingFace

Section 9: "Model Availability and Reproducibility" (~300 words). States the repo, summarizes the model card, describes how to extend.

---

## Part 4: Compilation and Validation

### Notebook Execution

```bash
cd project1
jupyter nbconvert --to notebook --execute \
  --ExecutePreprocessor.timeout=600 \
  COMP_4433_RockLambros_project1_crosswalk_eda.ipynb \
  --output COMP_4433_RockLambros_project1_crosswalk_eda.ipynb
```

All cells must execute without errors. Figures exported to `report/figures/` via `plt.savefig()` in code cells.

### Report PDF

```bash
cd report
pandoc report.md -o report.pdf --pdf-engine=pdflatex -V geometry:margin=1in -V fontsize=11pt
```

No Unicode characters in the markdown (all replaced with LaTeX equivalents). No warnings.

### Test Suite

```bash
python -m pytest mapping_engine/tests/ project2/tests/ -q
```

All 123 tests pass.

### COMP 4433 Rubric Checklist

- [ ] Multiple plots with differentially sized axes (GridSpec) — at least 3 figures
- [ ] Three+ different plot types — bar, heatmap, boxplot, violin, KDE, scatter, line, pie, imshow
- [ ] At least one on-plot annotation — present in 25+ cells
- [ ] Analytical approaches discussion — ordinal regression demonstrator + future work
- [ ] Anomalies, trends, observations — v8b collapse crisis, stacker overfitting, EQUIVALENT breakthrough
- [ ] Libraries: numpy, pandas, matplotlib, seaborn, statsmodels, sklearn only
- [ ] Well-organized with narrative explanation of plots
- [ ] Fine-tuned aesthetics, appropriate color use

### HuggingFace Validation

```bash
pip install aibom-generator
aibom generate rockCO78/ai-security-crosswalk-vfinal --output aibom.json
# Score should be 100/100
```

---

## Execution Order

1. HuggingFace: login, delete old model, create new repo, upload checkpoints + model card
2. Build notebook from scratch (new .ipynb, cell by cell)
3. Execute notebook, fix any errors
4. Rewrite report from notebook figures
5. Compile PDF, fix any errors
6. Run test suite
7. Validate AIBOM score
8. Commit and push
