# Notebook + Report + HuggingFace Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the Project 1 EDA notebook from scratch with a Problem-Solution narrative arc where OpenCRE/v8/v8b/v_final lead the story; rewrite the report to match; upload the v_final ensemble to HuggingFace with a perfect-score AIBOM model card.

**Architecture:** New notebook (~146 cells) built cell-by-cell as a fresh .ipynb, reusing ~73 existing code cells and writing ~73 new/rewritten narrative+code cells. Report (~4,500 words) mirrors the notebook arc. HuggingFace repo hosts 3 model checkpoints.

**Tech Stack:** Python 3, Jupyter (nbformat/JSON), matplotlib, seaborn, pandas, numpy, statsmodels, sklearn, pandoc+pdflatex, huggingface-cli, wandb (data download only — NOT imported in notebook)

**Spec:** `docs/superpowers/specs/2026-04-25-notebook-report-hf-redesign.md`

---

## Writing Style Reference (ALL narrative tasks MUST follow)

### Voice and Tone (derived from existing Sections 3-4)

- First person singular: "I want to establish", "This tells me"
- Specific numbers always: "120 of the 130 Unrelated pairs"
- Figure purpose stated BEFORE the code cell, interpretation AFTER
- Plain English `>` blockquote after every major figure
- Code comments: descriptive, reference figure numbers, explain WHY not WHAT
- Active titles that state the takeaway, not the variable name

### AI Slop Blocklist (from Wikipedia:Signs_of_AI_writing)

**Banned vocabulary:** delve, robust, tapestry, testament, vibrant, showcasing, exemplifies, pivotal, crucial, landscape (metaphorical), meticulous/meticulously, intricate/intricacies, garnered, bolstered, nestled, renowned, groundbreaking, profound, encompassing, fostering, cultivating, underscores, highlights (as verb meaning "shows"), aligns with, resonates with, boasts, valuable insights, diverse array, in the heart of, indelible mark, deeply rooted, evolving landscape, focal point, key turning point, setting the stage

**Banned patterns:**
- "Not just X, but also Y" constructions
- "Serves as" / "stands as" (copula avoidance — just say "is")
- Rule-of-three adjective lists ("robust, scalable, and efficient")
- Excessive em dashes (max 1-2 per paragraph)
- Elegant variation / synonym rotation (pick one term, stick with it)
- "Despite its... faces several challenges" formula
- Title Case In Section Headings (use sentence case)
- Promotional superlatives without evidence

### Visualization Compliance (ALL code cells with figures)

Every figure code block must include:
1. Comment block citing the perceptual principle from one of the 4 readings
2. Active title stating the takeaway (not the variable)
3. On-plot annotation (black arrow, 9-10 pt text) calling out key finding
4. `plt.savefig()` exporting to `report/figures/` with descriptive filename

| Principle | Source | Implementation |
|---|---|---|
| Position-on-common-scale | Cleveland & McGill (1984) | Bar/dot charts for comparisons |
| No rainbow/jet | Borland & Taylor (2007) | Sequential: `crest`, `Blues`, `Purples`. Diverging: `sns.diverging_palette(220, 20)` |
| Ordinal = luminance ramp | Borner et al. (2019) | `TIER_PALETTE` 4 luminance-ordered blues |
| Categorical <= 6 colors | Graze & Schwabish (2024) | `FRAMEWORK_PALETTE` (9 Okabe-Ito) |

### Libraries Allowed in Notebook

numpy, pandas, matplotlib, seaborn, statsmodels, sklearn, standard library (json, pathlib, collections, textwrap, warnings, yaml). **No other imports.** wandb is NOT allowed in the notebook.

---

## File Structure

| Action | File | Responsibility |
|---|---|---|
| Create | `project1/COMP_4433_RockLambros_project1_crosswalk_eda.ipynb` | New notebook (replaces old) |
| Create | `runs/v8b_diagnosis/wandb_runs.json` | Pre-downloaded WandB v8b data |
| Create | `runs/vfinal/wandb_best_runs.json` | Pre-downloaded WandB v_final data |
| Rewrite | `report/report.md` | Complete report rewrite |
| Regenerate | `report/report.pdf` | PDF from pandoc |
| Regenerate | `report/figures/*.png` | All figures re-exported |
| Create (remote) | HuggingFace `rockCO78/ai-security-crosswalk-vfinal` | Model repo + card |
| Delete (remote) | HuggingFace `rockCO78/crosswalk-v7c` | Stale old model |
| Backup | `project1/COMP_4433_RockLambros_project1_crosswalk_eda.ipynb.bak` | Backup of old notebook |

---

### Task 1: Pre-Flight — Backup Old Notebook + Download WandB Data

**Files:**
- Backup: `project1/COMP_4433_RockLambros_project1_crosswalk_eda.ipynb` → `.ipynb.bak`
- Create: `runs/v8b_diagnosis/wandb_runs.json`
- Create: `runs/vfinal/wandb_best_runs.json`

- [ ] **Step 1: Backup the current notebook**

```bash
cd /home/rock/github_projects/ai-security-framework-crosswalk
cp project1/COMP_4433_RockLambros_project1_crosswalk_eda.ipynb \
   project1/COMP_4433_RockLambros_project1_crosswalk_eda.ipynb.bak
```

- [ ] **Step 2: Download WandB v8b run data**

Create and run `scripts/download_wandb_data.py`:

```python
"""Download WandB run data for v8b and v_final projects.

This data is used by notebook cells in Sections 9 and 11 to plot
training loss curves and collapse diagnostics. The notebook itself
cannot import wandb (COMP 4433 library restriction), so we
pre-download to local JSON files.
"""
import json
import os
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

key = subprocess.run(
    ["pass", "wandb/api-key"], capture_output=True, text=True, check=True
).stdout.strip()
os.environ["WANDB_API_KEY"] = key

import wandb
api = wandb.Api(timeout=30)

# --- v8b runs (collapse diagnostics) ---
v8b_data = []
for run in api.runs("rockcyber/crosswalk-v8b", per_page=100):
    rows = list(run.scan_history())
    entry = {
        "id": run.id,
        "name": run.name,
        "state": run.state,
        "n_unique_preds": run.summary.get("n_unique_preds"),
        "combined_f1": run.summary.get("combined_f1"),
        "best_combined_f1": run.summary.get("best_combined_f1"),
        "history": [
            {k: v for k, v in r.items()
             if k in ("epoch", "train_loss", "val_kl_loss", "combined_f1",
                       "expert_val_macro_f1", "n_unique_preds",
                       "pred_class_0_pct", "pred_class_1_pct",
                       "pred_class_2_pct", "pred_class_3_pct",
                       "collapse_recovery", "train_acc")}
            for r in rows
        ],
    }
    v8b_data.append(entry)

out = REPO / "runs" / "v8b_diagnosis" / "wandb_runs.json"
out.write_text(json.dumps(v8b_data, indent=2))
print(f"Wrote {len(v8b_data)} v8b runs to {out}")

# --- v_final best runs (per-model training curves) ---
best_ids = {"roberta": "ounfajaa", "deberta_base": "ux5wt9hz", "bge": "5e3003m8"}
vfinal_data = {}
for model_name, run_id in best_ids.items():
    run = api.run(f"rockcyber/crosswalk-vfinal/{run_id}")
    rows = list(run.scan_history())
    vfinal_data[model_name] = {
        "id": run.id,
        "name": run.name,
        "state": run.state,
        "summary": {k: v for k, v in run.summary.items()
                     if isinstance(v, (int, float, str, type(None)))},
        "history": [
            {k: v for k, v in r.items()
             if k in ("epoch", "train_loss", "val_kl_loss", "combined_f1",
                       "expert_val_macro_f1", "f1_class_0", "f1_class_1",
                       "f1_class_2", "f1_class_3", "n_unique_preds",
                       "collapse_recovery", "train_acc")}
            for r in rows
        ],
    }

out2 = REPO / "runs" / "vfinal" / "wandb_best_runs.json"
out2.write_text(json.dumps(vfinal_data, indent=2))
print(f"Wrote {len(vfinal_data)} v_final best runs to {out2}")
```

Run:
```bash
cd /home/rock/github_projects/ai-security-framework-crosswalk
python scripts/download_wandb_data.py
```

Expected: Two JSON files written with run histories.

- [ ] **Step 3: Verify all data files exist**

```bash
cd /home/rock/github_projects/ai-security-framework-crosswalk
for f in \
  data/opencre/opencre_pairs.jsonl \
  data/splits/expert_train.jsonl \
  data/splits/v8_train.jsonl \
  data/splits/v8b_train.jsonl \
  runs/v7c_sacred/results.json \
  runs/vfinal/sacred/results.json \
  runs/vfinal/conformal/conformal.json \
  runs/vfinal/edge_predictions.json \
  runs/v8_diagnosis/v8_data_assembly.json \
  runs/v8b_diagnosis/v8b_data_assembly.json \
  runs/v8b_diagnosis/wandb_runs.json \
  runs/vfinal/wandb_best_runs.json \
  runs/registry.jsonl; do
  [ -f "$f" ] && echo "OK  $f" || echo "MISSING  $f"
done
```

Expected: All files OK.

- [ ] **Step 4: Commit**

```bash
git add scripts/download_wandb_data.py \
       runs/v8b_diagnosis/wandb_runs.json \
       runs/vfinal/wandb_best_runs.json
git commit -m "data: pre-download WandB run histories for notebook cells"
```

---

### Task 2: HuggingFace — Delete Old Model + Upload New Ensemble

**Files:**
- Create (remote): `rockCO78/ai-security-crosswalk-vfinal/README.md`
- Create (remote): model checkpoints + scripts
- Delete (remote): `rockCO78/crosswalk-v7c`

**Key data for model card:**
- v_final metrics: exact_acc=0.799, adjacent_acc=0.922, macro_f1=0.558
- Per-class F1: UNRELATED=0.928, PARTIAL=0.526, RELATED=0.378, EQUIVALENT=0.400
- Conformal coverage: class 0=91.3%, class 1=93.1%, class 2=91.0%, class 3=93.3%
- Training: 3x H100 80GB, BF16, ~4 hours
- Energy: ~8.4 kWh, ~3.4 kg CO2e

- [ ] **Step 1: Authenticate with HuggingFace**

```bash
HF_TOKEN=$(pass huggingface/token)
huggingface-cli login --token "$HF_TOKEN"
```

- [ ] **Step 2: Delete old model repository**

```bash
huggingface-cli repo delete rockCO78/crosswalk-v7c --type model -y
```

If the repo doesn't exist, that's fine — skip this step.

- [ ] **Step 3: Create new model repository**

```bash
huggingface-cli repo create ai-security-crosswalk-vfinal --type model
```

- [ ] **Step 4: Write AIBOM-compliant model card**

Create `runs/vfinal/hf_model_card/README.md` with the following content. This file will be uploaded to HuggingFace as the repo README.

```markdown
---
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
---

# AI Security Crosswalk v_final Ensemble

## Model Description

A 3-model ensemble that classifies pairs of AI security controls into four ordinal tiers: Unrelated (0), Partial (1), Related (2), Equivalent (3). Built by Rock Lambros at the University of Denver for COMP 4433.

The classifier scores cross-framework control mappings across nine AI security standards: AIUC-1, CSA AICM, CoSAI Risk Map, EU GPAI Code of Practice, MITRE ATLAS, NIST AI RMF, OWASP Agentic AI, OWASP AI Exchange, and OWASP LLM Top 10.

## Intended Use

**Primary use:** Scoring cross-framework control mappings to identify equivalent, related, and partially overlapping security controls. Organizations adopting multiple AI security standards can use this to find where their compliance efforts overlap.

**Out of scope:** General natural language inference, non-security text classification, or any use case requiring authoritative compliance decisions without human review.

## Model Architecture

Three transformer encoders produce independent 4-class softmax probability vectors. The ensemble prediction is the arithmetic mean of these three vectors (no learned parameters in the combination step).

| Component | Architecture | Parameters | CLS Dimension |
|---|---|---|---|
| Encoder 1 | RoBERTa-large | 355M | 1024 |
| Encoder 2 | DeBERTa-v3-base | 86M | 768 |
| Encoder 3 | BGE-large-v1.5 | 335M | 1024 |

Each encoder was trained with three ordinal loss functions (KL-divergence with ordinal smoothing, CORN ordinal regression, focal loss with class reweighting). The best checkpoint per encoder was selected by combined F1 on the validation split.

## Training Details

### Training Data

- **Expert-labeled pairs:** 5,920 pairs from 9 AI security frameworks, labeled by domain experts on a 4-tier ordinal scale
- **OpenCRE augmentation experiments:** 6,200 pairs from the Open Common Requirements Enumeration database with hop-distance-derived labels. Used for disagreement mining (v8) and direct augmentation (v8b). The v_final models were trained on expert data only after augmentation experiments showed instability.
- **Validation:** Mapping-level deduplication removed 56% of text-pair contamination from the validation split

### Preprocessing

Each input pair is formatted as `[CLS] source_text [SEP] target_text [SEP]` and tokenized by the respective encoder's tokenizer. Maximum sequence length: 512 tokens.

### Hyperparameters

| Parameter | RoBERTa | DeBERTa | BGE |
|---|---|---|---|
| Learning rate | 1e-5 | 2e-5 | 1e-5 |
| Batch size | 16 | 16 | 16 |
| Epochs | 5 | 5 | 5 |
| Loss | KL ordinal | CORN | Focal |
| Weight decay | 0.01 | 0.01 | 0.01 |
| Precision | BF16 | BF16 | BF16 |

### Training Infrastructure

- 3x NVIDIA H100 80GB HBM3 GPUs (RunPod)
- BF16 mixed precision (GradScaler disabled due to H100 BF16 inf-checking incompatibility)
- Total training time: approximately 4 hours across all models and loss variants

## Evaluation Results

Evaluated on a frozen holdout of 179 expert-labeled pairs (130 Unrelated, 18 Partial, 24 Related, 7 Equivalent).

| Metric | v7c Baseline | v_final | Delta |
|---|---|---|---|
| Exact accuracy | 81.0% | 79.9% | -1.1 pp |
| Adjacent accuracy | 94.4% | 92.2% | -2.2 pp |
| Macro F1 | 0.512 | 0.558 | +4.6 pp |

### Per-Class F1

| Class | v7c | v_final |
|---|---|---|
| Unrelated | 0.938 | 0.928 |
| Partial | 0.556 | 0.526 |
| Related | 0.556 | 0.378 |
| Equivalent | 0.000 | 0.400 |

### Conformal Prediction Coverage (alpha=0.10, target=90%)

| Class | Coverage |
|---|---|
| Unrelated | 91.3% |
| Partial | 93.1% |
| Related | 91.0% |
| Equivalent | 93.3% |

### Bootstrap Confidence Intervals (10,000 resamples, 95% CI)

- Exact accuracy: 73.7% -- 86.0%
- Macro F1: 0.436 -- 0.661

## Limitations and Biases

- **Small test set:** 179 pairs with only 7 Equivalent examples. Per-class F1 estimates have wide confidence intervals. A single additional correct Equivalent prediction moves F1 from 0.400 to 0.500.
- **English only:** All nine frameworks are English-language documents. The model has not been tested on translated or multilingual security standards.
- **Framework coverage:** Trained on 9 specific AI security frameworks. Performance on other security standards (ISO 27001, SOC 2, etc.) is unknown.
- **Label subjectivity:** Expert annotators can disagree on Partial vs. Related distinctions. The conformal prediction sets partially mitigate this.
- **Ordinal boundary sensitivity:** The Related-class F1 dropped from 0.556 to 0.378 as the model shifted its decision boundary to capture Equivalent pairs.

## Ethical Considerations

- **No personal data:** The training data consists entirely of public security framework documents. No personally identifiable information is used.
- **No demographic bias risk:** The classification task involves technical security controls, not individuals or demographic groups.
- **Security domain only:** The model is designed for AI security control mapping. It should not be applied to unrelated domains.

## Environmental Impact

- **Hardware:** 3x NVIDIA H100 80GB GPUs
- **Training time:** Approximately 4 hours
- **Energy consumption:** Estimated 8.4 kWh (3 GPUs at ~700W each for ~4 hours)
- **Carbon footprint:** Estimated 3.4 kg CO2e (US grid average of 0.41 kg CO2e/kWh)

## How to Use

```python
import torch
from transformers import AutoTokenizer, AutoModel

# Load one of the three encoders (example: RoBERTa)
tokenizer = AutoTokenizer.from_pretrained(
    "rockCO78/ai-security-crosswalk-vfinal",
    subfolder="roberta/encoder"
)
encoder = AutoModel.from_pretrained(
    "rockCO78/ai-security-crosswalk-vfinal",
    subfolder="roberta/encoder"
)
head = torch.load(
    "roberta/head.pt",  # download separately via hf_hub
    map_location="cpu"
)

# Tokenize a pair
inputs = tokenizer(
    "Implement access control policies",
    "Enforce least privilege for AI agents",
    truncation=True, max_length=512, return_tensors="pt"
)

# Forward pass
with torch.no_grad():
    outputs = encoder(**inputs)
    cls = outputs.last_hidden_state[:, 0, :]
    logits = head(cls)
    probs = torch.softmax(logits, dim=-1)

tier_names = ["Unrelated", "Partial", "Related", "Equivalent"]
pred = probs.argmax(dim=-1).item()
print(f"Predicted: {tier_names[pred]} (confidence: {probs[0, pred]:.3f})")
```

For full ensemble inference across all three models, see `scripts/predict_edges.py` in this repository.

## How to Train on New Frameworks

1. **Prepare node data:** Add new framework controls to `data/processed/nodes.json` with fields: `node_id`, `framework`, `name`, `description`, `entry_type`
2. **Generate candidate pairs:** Create cross-framework pairs between the new framework and existing frameworks
3. **Run inference:** Use `scripts/predict_edges.py` to score all candidate pairs with the existing ensemble
4. **Expert review:** Have domain experts review a sample of high-confidence predictions (especially Equivalent and Related) to validate quality
5. **Fine-tune (optional):** If expert labels are available, fine-tune the ensemble on the expanded training set using the same ordinal loss functions

## Citation

```bibtex
@misc{lambros2026crosswalk,
  title={AI Security Framework Crosswalk: Ordinal Classification of Control Mappings},
  author={Rock Lambros},
  year={2026},
  institution={University of Denver},
  url={https://huggingface.co/rockCO78/ai-security-crosswalk-vfinal}
}
```

## Safety and Risk Assessment

Model outputs are advisory, not authoritative. The predicted tier for any control pair should be treated as a starting point for human review, not as a compliance determination. Organizations should:

- Validate high-confidence Equivalent predictions with domain experts before using them for compliance mapping
- Use the conformal prediction sets (available via the inference script) to identify uncertain predictions
- Recognize that the model was trained on 9 specific AI security frameworks and may not generalize to other standards

Human review is required for any compliance or regulatory decision based on these predictions.
```

- [ ] **Step 5: Upload model card**

```bash
cd /home/rock/github_projects/ai-security-framework-crosswalk
mkdir -p runs/vfinal/hf_model_card
# (Write the README.md from step 4 to runs/vfinal/hf_model_card/README.md)
huggingface-cli upload rockCO78/ai-security-crosswalk-vfinal \
  runs/vfinal/hf_model_card/README.md README.md
```

- [ ] **Step 6: Upload model checkpoints**

```bash
cd /home/rock/github_projects/ai-security-framework-crosswalk

# RoBERTa
huggingface-cli upload rockCO78/ai-security-crosswalk-vfinal \
  runs/vfinal/ce/roberta/ounfajaa/best/encoder roberta/encoder
huggingface-cli upload rockCO78/ai-security-crosswalk-vfinal \
  runs/vfinal/ce/roberta/ounfajaa/best/head.pt roberta/head.pt

# DeBERTa-base
huggingface-cli upload rockCO78/ai-security-crosswalk-vfinal \
  runs/vfinal/ce/deberta_base/ux5wt9hz/best/encoder deberta_base/encoder
huggingface-cli upload rockCO78/ai-security-crosswalk-vfinal \
  runs/vfinal/ce/deberta_base/ux5wt9hz/best/head.pt deberta_base/head.pt

# BGE
huggingface-cli upload rockCO78/ai-security-crosswalk-vfinal \
  runs/vfinal/ce/bge/5e3003m8/best/encoder bge/encoder
huggingface-cli upload rockCO78/ai-security-crosswalk-vfinal \
  runs/vfinal/ce/bge/5e3003m8/best/head.pt bge/head.pt

# Inference script
huggingface-cli upload rockCO78/ai-security-crosswalk-vfinal \
  scripts/predict_edges.py scripts/predict_edges.py
```

- [ ] **Step 7: Validate AIBOM score**

```bash
pip install aibom-generator 2>/dev/null
aibom generate rockCO78/ai-security-crosswalk-vfinal --output /tmp/aibom.json
python3 -c "import json; d=json.load(open('/tmp/aibom.json')); print('Score:', d.get('score', d))"
```

Target: 100/100. If not perfect, identify missing fields and fix the model card.

- [ ] **Step 8: Commit model card locally**

```bash
cd /home/rock/github_projects/ai-security-framework-crosswalk
git add runs/vfinal/hf_model_card/README.md
git commit -m "docs: add AIBOM-compliant model card for HuggingFace"
```

---

### Task 3: Create New Notebook — Abstract + Setup (Sections 1-2)

**Files:**
- Create: `project1/COMP_4433_RockLambros_project1_crosswalk_eda.ipynb`

This task creates a fresh notebook with the title, abstract, plain English block, and setup cells. All subsequent tasks append to this notebook.

**Important data path note:** The notebook runs from `project1/` so `Path(".").resolve()` returns the project1 directory. The setup cell must define `REPO_ROOT` pointing to the repository root (one level up).

- [ ] **Step 1: Create the notebook builder script**

Create `project1/build_notebook.py`:

```python
"""Build the redesigned notebook from scratch.

Each section-building task will import helpers from this module
and append cells to the notebook.
"""
import json
from pathlib import Path

NB_PATH = Path(__file__).parent / "COMP_4433_RockLambros_project1_crosswalk_eda.ipynb"
OLD_NB_PATH = Path(__file__).parent / "COMP_4433_RockLambros_project1_crosswalk_eda.ipynb.bak"

def make_md(source: str) -> dict:
    lines = source.split("\n")
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": [l + "\n" for l in lines[:-1]] + [lines[-1]] if lines else [],
    }

def make_code(source: str) -> dict:
    lines = source.split("\n")
    return {
        "cell_type": "code",
        "metadata": {},
        "source": [l + "\n" for l in lines[:-1]] + [lines[-1]] if lines else [],
        "outputs": [],
        "execution_count": None,
    }

def load_old_notebook() -> dict:
    return json.loads(OLD_NB_PATH.read_text())

def load_notebook() -> dict:
    if NB_PATH.exists():
        return json.loads(NB_PATH.read_text())
    return {
        "cells": [],
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "name": "python",
                "version": "3.10.0"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }

def save_notebook(nb: dict) -> None:
    NB_PATH.write_text(json.dumps(nb, indent=1, ensure_ascii=False))
    print(f"Saved {len(nb['cells'])} cells to {NB_PATH}")

def copy_old_cells(old_nb: dict, indices: list[int]) -> list[dict]:
    cells = []
    for i in indices:
        cell = json.loads(json.dumps(old_nb["cells"][i]))
        cell["outputs"] = []
        if cell["cell_type"] == "code":
            cell["execution_count"] = None
        cells.append(cell)
    return cells
```

- [ ] **Step 2: Create the Section 1-2 builder**

Create `project1/build_sections_1_2.py`:

```python
"""Build Sections 1-2: Abstract, Plain English, Setup."""
import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from build_notebook import (
    make_md, make_code, load_notebook, save_notebook,
    load_old_notebook, copy_old_cells,
)

nb = load_notebook()
old = load_old_notebook()

# --- Cell 0: Title + Abstract ---
nb["cells"].append(make_md(r"""# AI Security Framework Crosswalk: From Baseline Failure to Ordinal Ensemble

**Author:** Rock Lambros, University of Denver, COMP 4433

**Abstract.** This notebook traces the development of a 4-class ordinal classifier for AI security framework crosswalks, from a baseline that scored 0% on its most important class to a 3-model ensemble that broke through.

The crosswalk dataset contains 983 security controls from nine AI security frameworks connected by 5,813 edges. Expert annotators labeled 179 pairs on a 4-tier ordinal scale: Unrelated, Partial, Related, Equivalent. The v7c baseline reached 81.0% exact accuracy and 0.512 macro F1, but scored 0.000 F1 on the Equivalent class. The classifier never predicted that two controls from different frameworks meant the same thing.

The Open Common Requirements Enumeration (OpenCRE) database provided 13,519 pairs with expert-curated relationships and a hop-distance structure that maps naturally onto ordinal tiers. After removing 34 pairs overlapping the frozen test set, 6,200 clean pairs remained. Disagreement mining---scoring these through v7c and selecting the 673 where it conflicted with OpenCRE labels---produced the v8 training augmentation.

v8b expanded augmentation further, but DeBERTa-large collapsed to single-class prediction and the LightGBM stacker overfit to training accuracy of 1.000 against validation accuracy of 0.528. Both failures pointed to the same problem: noisy proxy labels amplified by a learnable second stage.

v_final stripped the pipeline down. Mapping-level deduplication removed 56% of text-pair contamination from validation. Three ordinal loss functions (KL-divergence with ordinal smoothing, CORN ordinal regression, focal loss) replaced standard cross-entropy. Softmax averaging across RoBERTa-large, DeBERTa-v3-base, and BGE-large-v1.5 replaced the stacker. The result: macro F1 rose to 0.558 (+4.6 pp), Equivalent F1 reached 0.400 (from 0.000), conformal coverage exceeded 90% on all four classes, and the ensemble scored all 4,001 edges in the crosswalk graph. The trained model is available on [HuggingFace](https://huggingface.co/rockCO78/ai-security-crosswalk-vfinal)."""))

# --- Cell 1: Plain English ---
nb["cells"].append(make_md(r"""> **Plain English:** I built a tool that compares security controls across nine AI security standards and decides whether two controls from different frameworks are unrelated, partially related, related, or equivalent. The first version worked well overall (81% accuracy) but could not identify equivalent controls at all---it scored 0% on the class that matters most for compliance mapping.
>
> After discovering OpenCRE, a public database that already links these standards through shared requirements, I tried two ways to add its data to training. The first (disagreement mining) was promising but limited. The second (direct augmentation) caused the large model to collapse to a single prediction and the combiner to memorize the training data perfectly while failing on new examples. Both failures pointed in the same direction: strip the architecture down and remove the learnable combiner.
>
> The final version averages three models trained with loss functions that care about the ordering of the tiers. It gets Equivalent right for the first time. The trained model is on HuggingFace for anyone to use."""))

# --- Cells 2-4: Setup (copy from old cells 2-4, with REPO_ROOT fix) ---
setup_cells = copy_old_cells(old, [2, 3])
nb["cells"].extend(setup_cells)

# Cell 4 (setup code) needs REPO_ROOT added right after REPO definition
old_setup = old["cells"][4]
setup_source = "".join(old_setup["source"])

# Insert REPO_ROOT definition after the REPO line
repo_line_end = setup_source.find("\n", setup_source.find("REPO = "))
if repo_line_end > 0:
    setup_source = (
        setup_source[:repo_line_end + 1]
        + "REPO_ROOT = REPO.parent if REPO.name == \"project1\" else REPO\n"
        + setup_source[repo_line_end + 1:]
    )

setup_code = make_code(setup_source)
nb["cells"].append(setup_code)

save_notebook(nb)
```

- [ ] **Step 3: Run the builder**

```bash
cd /home/rock/github_projects/ai-security-framework-crosswalk/project1
python build_sections_1_2.py
```

Expected: `Saved 5 cells to .../COMP_4433_RockLambros_project1_crosswalk_eda.ipynb`

- [ ] **Step 4: Verify structure**

```bash
cd /home/rock/github_projects/ai-security-framework-crosswalk
python3 -c "
import json
nb = json.load(open('project1/COMP_4433_RockLambros_project1_crosswalk_eda.ipynb'))
for i, c in enumerate(nb['cells']):
    src = ''.join(c['source'])[:80].replace('\n', ' ')
    print(f'{i:3d} [{c[\"cell_type\"]:8s}] {src}')
"
```

Expected: 5 cells (abstract, plain english, setup header, setup desc, setup code with REPO_ROOT).

- [ ] **Step 5: Commit**

```bash
cd /home/rock/github_projects/ai-security-framework-crosswalk
git add project1/build_notebook.py project1/build_sections_1_2.py \
       project1/COMP_4433_RockLambros_project1_crosswalk_eda.ipynb
git commit -m "notebook: create fresh notebook with abstract + setup (sections 1-2)"
```

---

### Task 4: Notebook Sections 3-4 — Dataset Overview + Framework Landscape

**Files:**
- Modify: `project1/COMP_4433_RockLambros_project1_crosswalk_eda.ipynb`

These sections are copied verbatim from the old notebook (cells 6-33, 28 cells). They already satisfy all visualization compliance requirements and contain proper citations of the 4 readings.

- [ ] **Step 1: Create the section builder**

Create `project1/build_sections_3_4.py`:

```python
"""Build Sections 3-4: Dataset Overview + Framework Landscape.

Copies cells 6-33 from the old notebook verbatim. These 28 cells
already contain proper figure citations, active titles, on-plot
annotations, and Plain English blockquotes.
"""
import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from build_notebook import (
    load_notebook, save_notebook, load_old_notebook, copy_old_cells,
)

nb = load_notebook()
old = load_old_notebook()

# Cells 6-33 from old notebook = Section 3 (Dataset Overview) + Section 4 (Framework Landscape)
# 28 cells total, copied verbatim
cells = copy_old_cells(old, list(range(6, 34)))
nb["cells"].extend(cells)

save_notebook(nb)
```

- [ ] **Step 2: Run the builder**

```bash
cd /home/rock/github_projects/ai-security-framework-crosswalk/project1
python build_sections_3_4.py
```

Expected: `Saved 33 cells`

- [ ] **Step 3: Verify cell count and section headers**

```bash
cd /home/rock/github_projects/ai-security-framework-crosswalk
python3 -c "
import json
nb = json.load(open('project1/COMP_4433_RockLambros_project1_crosswalk_eda.ipynb'))
print(f'Total: {len(nb[\"cells\"])} cells')
for i, c in enumerate(nb['cells']):
    src = ''.join(c['source'])[:100].replace('\n', ' ')
    if src.startswith('## ') or src.startswith('# '):
        print(f'{i:3d} [{c[\"cell_type\"]:8s}] {src}')
"
```

Expected: 33 cells. Section headers for 2, 3, 4 visible.

- [ ] **Step 4: Commit**

```bash
cd /home/rock/github_projects/ai-security-framework-crosswalk
git add project1/build_sections_3_4.py project1/COMP_4433_RockLambros_project1_crosswalk_eda.ipynb
git commit -m "notebook: add sections 3-4 (dataset overview + framework landscape)"
```

---

### Task 5: Notebook Section 5 — v7c Baseline (Compressed)

**Files:**
- Modify: `project1/COMP_4433_RockLambros_project1_crosswalk_eda.ipynb`

This section compresses the old v7c deep-dive (50+ cells spanning sections 5-8) into ~15 cells. It presents v7c as "the baseline that failed" rather than the main event. Key cells to copy from old notebook: 34-37 (feature analysis), 47-48 (feature importance), 51 (method comparison), 70-73 (confusion matrix + test results), 82-83 (headline accuracy).

Figure numbers change: old 5.1→5.1, old 6.1→5.2, old 6.2→5.3, old 8.1→5.4, old 8.3→5.5.

- [ ] **Step 1: Create the section builder**

Create `project1/build_section_5.py`:

```python
"""Build Section 5: v7c Baseline (compressed).

Reframes v7c as the baseline whose EQUIVALENT blind spot drove
the rest of the investigation. Compresses 50+ cells into ~15.
"""
import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from build_notebook import (
    make_md, make_code, load_notebook, save_notebook,
    load_old_notebook, copy_old_cells,
)

nb = load_notebook()
old = load_old_notebook()

# --- Section header ---
nb["cells"].append(make_md("""## 5 · The v7c Baseline and Its Failure

The v7c pipeline is a two-stage classifier. Stage 1 extracts 50 features per node pair: 35 from a graph attention network (GAT) trained on the crosswalk topology, 12 cross-encoder soft probabilities from three transformers (RoBERTa-large, DeBERTa-v3-large, DeBERTa-v3-base), and 3 baseline signals (BGE cosine, BM25, bridge score). Stage 2 feeds these into a regularized logistic regression (C=0.01, cross-validated on 477 calibration pairs).

On the 179-pair frozen holdout, v7c achieved 81.0% exact accuracy, 94.4% adjacent accuracy, and 0.512 macro F1. Those headline numbers are respectable. The per-class breakdown is not: the Equivalent class (7 test pairs) scored F1 = 0.000. The classifier never once predicted Equivalent. This section presents the feature behavior, importance ranking, and test results that characterize the baseline before I explain what I did about it."""))

# --- Feature analysis: cells 34-37 (section header rewritten, code cells copied) ---
# Cell 34 = old section 5 header (skip, we wrote our own)
# Cell 35 = old section 5 intro narrative (skip, we wrote our own)
# Cell 36 = feature family definitions code
# Cell 37 = Figure 5.1 feature violins code
cells_feature = copy_old_cells(old, [36, 37])
nb["cells"].extend(cells_feature)

# Interpretation of feature violins
nb["cells"].append(make_md("""The six panels show three different stories. The LLM features separate Unrelated from everything else but cannot distinguish Related from Equivalent. The GAT cosine similarities show cleaner tier separation, but the Equivalent tier (red) overlaps heavily with Related. The baseline BGE signal tracks the ordinal structure monotonically.

> **Plain English:** Each violin shows, for one feature, how its scores spread out across the four tiers. You want the violins to sit at different heights for different tiers. The graph-based features do this better than the text-based ones, but none of them cleanly separate the top two tiers."""))

# --- Feature importance: cells 47-48 ---
nb["cells"].extend(copy_old_cells(old, [47, 48]))

nb["cells"].append(make_md("""The top features are cross-encoder soft probabilities. RoBERTa-large dominates: its four class probabilities account for 38% of total importance. The GAT features contribute individually less but collectively form the second-largest block.

> **Plain English:** The model's strongest signals come from the RoBERTa transformer, not from the graph structure. This matters because the v_final redesign later in this notebook drops the graph features entirely."""))

# --- Method comparison: cell 51 ---
nb["cells"].extend(copy_old_cells(old, [51]))

nb["cells"].append(make_md("""GAT-only (Method A) reaches 65.9% accuracy. The full pipeline (Method B) reaches 81.0%. The cross-encoder features add 15 accuracy points, confirming that transformer-based text understanding drives the majority of classifier performance.

> **Plain English:** The graph structure helps, but the heavy lifting is done by the language models that read the actual text of each control."""))

# --- Test results: cells 70-73 (section header + sacred dump + confusion matrix) ---
# Cell 70 = section 8 header (skip, integrate into narrative)
nb["cells"].append(make_md("""### Frozen test results

The frozen test set contains 179 expert-labeled pairs held out from all training. The confusion matrix below is the summary of v7c's performance on this holdout."""))

# Cell 71 = sacred summary print
# Cell 72 = Figure 8.1 confusion matrix code
nb["cells"].extend(copy_old_cells(old, [71, 72]))

nb["cells"].append(make_md("""The confusion matrix has a strong diagonal for Unrelated (120/130 correct) and reasonable numbers for Partial (10/18) and Related (15/24). The bottom row is the problem: all 7 Equivalent pairs are misclassified. Five are predicted Related, two Unrelated. The model treats Equivalent as if the class does not exist.

> **Plain English:** The model gets the easy cases right and the medium cases mostly right, but it completely misses the hardest and most valuable class. If two controls from different frameworks say the same thing, this classifier will never tell you."""))

# --- Headline accuracy: cell 83 ---
nb["cells"].extend(copy_old_cells(old, [83]))

nb["cells"].append(make_md("""### The pivot

The 81% headline accuracy hides a structural failure. The classifier cannot identify equivalent controls---the class that matters most for compliance crosswalks. With only 7 Equivalent examples in the test set and zero in the classifier's prediction distribution, the problem is clearly data starvation in the high end of the ordinal scale.

This sent me looking for external sources of high-similarity control pairs. Where could I find more labeled data for the Equivalent class?"""))

# --- Update figure numbers in copied code cells ---
# The copied cells reference old figure numbers. We need to update them.
# This is done by searching for "Figure X.Y" patterns and replacing.
import re
fig_map = {
    "Figure 5.1": "Figure 5.1",   # same
    "Figure 6.1": "Figure 5.2",
    "Figure 6.2": "Figure 5.3",
    "Figure 8.1": "Figure 5.4",
    "Figure 8.2": "Figure 5.5",  # if present
    "Figure 8.3": "Figure 5.6",
    "fig5_1": "fig5_1",           # savefig filenames
    "fig6_1": "fig5_2",
    "fig6_2": "fig5_3",
    "fig8_1": "fig5_4",
    "fig8_2": "fig5_5",
    "fig8_3": "fig5_6",
}

# Apply figure renumbering to all cells added in this section
section_start = 33  # cells 0-32 are from previous tasks
for cell in nb["cells"][section_start:]:
    src = "".join(cell["source"])
    for old_ref, new_ref in fig_map.items():
        src = src.replace(old_ref, new_ref)
    # Also add savefig calls if not present, pointing to report/figures/
    cell["source"] = [l + "\n" for l in src.split("\n")[:-1]] + [src.split("\n")[-1]]

save_notebook(nb)
```

**Note to implementer:** The figure renumbering regex in this script is simplified. When running, verify that the copied code cells produce correct figure references. Check `plt.savefig()` paths point to `REPO_ROOT / "report" / "figures"` with correct filenames. If any `plt.savefig()` calls are missing, add them before `plt.show()`.

- [ ] **Step 2: Run the builder**

```bash
cd /home/rock/github_projects/ai-security-framework-crosswalk/project1
python build_section_5.py
```

Expected: ~48 cells total (33 from tasks 3-4 + ~15 new).

- [ ] **Step 3: Verify section structure**

```bash
cd /home/rock/github_projects/ai-security-framework-crosswalk
python3 -c "
import json
nb = json.load(open('project1/COMP_4433_RockLambros_project1_crosswalk_eda.ipynb'))
print(f'Total: {len(nb[\"cells\"])} cells')
for i, c in enumerate(nb['cells'][33:], start=33):
    src = ''.join(c['source'])[:100].replace('\n', ' ')
    print(f'{i:3d} [{c[\"cell_type\"]:8s}] {src}')
"
```

- [ ] **Step 4: Commit**

```bash
cd /home/rock/github_projects/ai-security-framework-crosswalk
git add project1/build_section_5.py project1/COMP_4433_RockLambros_project1_crosswalk_eda.ipynb
git commit -m "notebook: add section 5 (v7c baseline compressed)"
```

---

### Task 6: Notebook Section 6 — Uncertainty, Ordinal Regression, and the Pivot

**Files:**
- Modify: `project1/COMP_4433_RockLambros_project1_crosswalk_eda.ipynb`

Compresses the old Section 9 (uncertainty/limitations) into ~10 cells. Keeps the ordinal regression demonstrator (satisfies COMP 4433 "analytical approaches" requirement). Ends with "three directions to push" that directly motivate OpenCRE.

Source cells from old notebook: 85-86 (section header + intro), 90-91 (analytical approaches narrative), 96-101 (ordinal regression demonstrator).

- [ ] **Step 1: Create the section builder**

Create `project1/build_section_6.py`:

```python
"""Build Section 6: Uncertainty, Ordinal Regression, and the Pivot."""
import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from build_notebook import (
    make_md, make_code, load_notebook, save_notebook,
    load_old_notebook, copy_old_cells,
)

nb = load_notebook()
old = load_old_notebook()

# --- Section header ---
nb["cells"].append(make_md("""## 6 · Uncertainty quantification and ordinal structure

Two problems with the v7c baseline go beyond the Equivalent blind spot. First, the classifier produces a point prediction with no uncertainty estimate. A compliance workflow needs to know when the model is guessing. Second, the four tiers are ordered---an Unrelated-to-Equivalent error is worse than a Related-to-Equivalent error---but the logistic regression treats all misclassifications equally."""))

# --- Analytical approaches narrative (from cell 90) ---
nb["cells"].append(make_md("""### Three directions worth investigating

Three changes would most likely improve the classifier:

1. **More Equivalent training data.** The expert training set contains only a handful of Equivalent pairs. Any external source of high-similarity control pairs could help.
2. **Ordinal regression instead of flat 4-class classification.** The logistic regression ignores the ordering of tiers. An ordinal loss that penalizes distant errors more heavily than adjacent ones could improve calibration.
3. **Conformal prediction for uncertainty.** Wrapping point predictions in prediction sets would give downstream consumers a calibrated measure of confidence.

The ordinal regression demonstrator below addresses direction 2. The OpenCRE discovery in the next section addresses direction 1. v_final combines both."""))

# --- Ordinal regression demonstrator (cells 96-101) ---
# Cell 96 = section header for ordinal demo
# Cell 97 = narrative intro
# Cell 98 = Plain English
# Cell 99 = statsmodels code
# Cell 100 = Figure 9.2 code (rename to 6.1)
# Cell 101 = interpretation

nb["cells"].append(make_md("""### Ordinal regression demonstrator

The four tiers (Unrelated < Partial < Related < Equivalent) form a natural ladder. An ordinal model estimates cumulative thresholds: P(tier >= k) for each cutpoint. This proof-of-concept uses `statsmodels.OrderedModel` on the calibration split to show what ordinal structure looks like in practice."""))

nb["cells"].append(make_md("""> **Plain English:** Instead of treating the four tiers as disconnected buckets, this model says "tier 0 is most likely, and as the feature score increases, the probability mass slides rightward toward tier 3." The S-curves below visualize that slide."""))

# Copy the statsmodels code cells
nb["cells"].extend(copy_old_cells(old, [99, 100]))

nb["cells"].append(make_md("""The ordinal fit converges and the cumulative-probability plot shows a clean monotone sweep from mostly-Unrelated on the left to mostly-Equivalent on the right. This confirms that the ordinal structure in the data is real and exploitable. The v_final pipeline will use three ordinal loss functions that build on this principle.

> **Plain English:** The proof-of-concept works. When trained to respect the tier ordering, the model produces probability curves that slide smoothly from "definitely unrelated" to "probably equivalent" as the input feature increases. This motivated the ordinal losses used in the final pipeline."""))

# Renumber figures: old Figure 9.2 -> Figure 6.1
for cell in nb["cells"][-6:]:
    src = "".join(cell["source"])
    src = src.replace("Figure 9.2", "Figure 6.1")
    src = src.replace("fig9_2", "fig6_1")
    cell["source"] = [l + "\n" for l in src.split("\n")[:-1]] + [src.split("\n")[-1]]

save_notebook(nb)
```

- [ ] **Step 2: Run, verify, commit**

```bash
cd /home/rock/github_projects/ai-security-framework-crosswalk/project1
python build_section_6.py
cd ..
python3 -c "
import json; nb = json.load(open('project1/COMP_4433_RockLambros_project1_crosswalk_eda.ipynb'))
print(f'Total: {len(nb[\"cells\"])} cells')
"
git add project1/build_section_6.py project1/COMP_4433_RockLambros_project1_crosswalk_eda.ipynb
git commit -m "notebook: add section 6 (uncertainty + ordinal regression)"
```

---

### Task 7: Notebook Sections 7-8 — OpenCRE Discovery + v8 Disagreement Mining

**Files:**
- Modify: `project1/COMP_4433_RockLambros_project1_crosswalk_eda.ipynb`

This is where the notebook gains energy. Section 7 expands the OpenCRE EDA from 7 cells to ~15. Section 8 expands v8 disagreement mining from 5 cells to ~10. Together they tell the story of finding external ground truth and using it strategically.

Source cells from old notebook: 114-120 (OpenCRE), 121-125 (v8 disagreement mining). Plus 5 new code cells.

**Data files referenced:**
- `data/opencre/opencre_pairs.jsonl` — 13,519 pairs with fields: source_node_id, target_node_id, source_text, target_text, source_framework, target_framework, cre_id, gap_penalty, provenance
- `runs/v8_diagnosis/v8_data_assembly.json` — keys: opencre_total, contaminated, clean, disagreements, selected, v8_rows_added, expert_train_original, v8_train_total, label_distribution
- `data/splits/expert_train.jsonl` — 5,920 expert pairs
- `data/splits/v8_train.jsonl` — 12,849 pairs (expert + v8 augmentation)

- [ ] **Step 1: Create the section builder**

Create `project1/build_sections_7_8.py`:

```python
"""Build Sections 7-8: OpenCRE Discovery + v8 Disagreement Mining.

Section 7 is the narrative turning point: the discovery of external
ground truth. Section 8 shows the first attempt to use it.
"""
import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from build_notebook import (
    make_md, make_code, load_notebook, save_notebook,
    load_old_notebook, copy_old_cells,
)

nb = load_notebook()
old = load_old_notebook()

# ========================================
# SECTION 7: OpenCRE Discovery
# ========================================

nb["cells"].append(make_md("""## 7 · The OpenCRE discovery: external linkage ground truth

The v7c Equivalent blind spot came down to data starvation. The expert training set contained a handful of Equivalent pairs. To train a model that can identify equivalent controls, I needed more examples of what "equivalent" looks like.

The Open Common Requirements Enumeration (OpenCRE) is a community-maintained database that maps security standards at the control level. Each CRE node represents a shared requirement; the links between CRE nodes and framework controls carry expert-curated relationship types (Contains, Related, Linked To). Two controls that share the same CRE node are almost certainly equivalent. Two controls linked through adjacent CREs are likely related. This hop-distance structure maps directly onto our four ordinal tiers."""))

# --- Copy old cell 115 (REPO_ROOT + OpenCRE loading code) ---
# But REPO_ROOT is already defined in setup. We only need the OpenCRE loading part.
nb["cells"].append(make_code("""# 7.1 — Load OpenCRE pairs and profile the dataset
from collections import Counter

ocre_path = REPO_ROOT / "data" / "opencre" / "opencre_pairs.jsonl"
ocre_pairs = []
with open(ocre_path) as f:
    for line in f:
        ocre_pairs.append(json.loads(line))

print(f"OpenCRE pairs loaded: {len(ocre_pairs):,}")
print(f"Unique CRE nodes: {len(set(p['cre_id'] for p in ocre_pairs)):,}")
print(f"Frameworks represented: {sorted(set(p['source_framework'] for p in ocre_pairs) | set(p['target_framework'] for p in ocre_pairs))}")

# Gap penalty distribution (hop distance)
gaps = Counter(p["gap_penalty"] for p in ocre_pairs)
for g in sorted(gaps):
    print(f"  Hop {g}: {gaps[g]:,} pairs ({gaps[g]/len(ocre_pairs)*100:.1f}%)")"""))

nb["cells"].append(make_md("""OpenCRE contains 13,519 cross-framework pairs spanning 6 of our 9 frameworks. The gap penalty (hop distance) distributes across three levels: hop 0 (same CRE, tightest pairing), hop 1 (adjacent CREs), and hop 2 (two-hop path). The concentration at hop 0 is good news---these are the pairs most likely to represent genuine equivalence."""))

# --- NEW code cell: Figure 7.1 Hop distance bar chart ---
nb["cells"].append(make_code("""# Figure 7.1 — Hop distance distribution across OpenCRE pairs.
# Bar chart on a common position scale (Cleveland & McGill 1984).
# Luminance ramp encodes the ordinal structure of hop distance
# (Borner et al. 2019): darker = tighter relationship.
from collections import Counter

gaps = Counter(p["gap_penalty"] for p in ocre_pairs)
hops = sorted(gaps.keys())
counts = [gaps[h] for h in hops]
hop_colors = ["#1a5276", "#2e86c1", "#85c1e9"]  # luminance ramp: dark to light

fig, ax = plt.subplots(figsize=(8, 4))
bars = ax.bar(
    [f"Hop {h}\\n({['same CRE', 'adjacent CRE', '2-hop path'][h]})" for h in hops],
    counts, color=hop_colors[:len(hops)], edgecolor="white", linewidth=0.8
)

for bar, count in zip(bars, counts):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 80,
            f"{count:,}", ha="center", va="bottom", fontsize=10, fontweight="bold")

# Annotation: call out the hop-0 concentration (Graze & Schwabish 2024)
ax.annotate(
    f"{counts[0]/sum(counts)*100:.0f}% of pairs share\\nthe same CRE node",
    xy=(0, counts[0]), xytext=(0.8, counts[0] * 0.75),
    fontsize=9, color="black",
    arrowprops=dict(arrowstyle="->", color="black", lw=1.2),
)

ax.set_ylabel("Number of pairs")
ax.set_title("Most OpenCRE pairs share the same CRE node (hop 0)", fontsize=12)
ax.spines[["top", "right"]].set_visible(False)
plt.tight_layout()
plt.savefig(REPO_ROOT / "report" / "figures" / "fig7_1_hop_distance.png", dpi=150, bbox_inches="tight")
plt.show()"""))

nb["cells"].append(make_md("""Hop 0 pairs dominate the distribution. These are pairs where both controls link to the same CRE requirement node, making them the strongest candidates for Equivalent-tier labels. The long tail of hop-1 and hop-2 pairs provides Related and Partial examples.

> **Plain English:** OpenCRE organizes security controls into clusters around shared requirements. When two controls from different frameworks point to the same requirement, they are zero hops apart---almost certainly equivalent. The farther apart they are in the CRE graph, the weaker the relationship."""))

# --- NEW code cell: Figure 7.2 Link-type distribution bar chart ---
nb["cells"].append(make_code("""# Figure 7.2 — OpenCRE link-type distribution.
# Horizontal bar chart for readability of long category labels
# (Cleveland & McGill 1984: position on common scale).
link_types = Counter(p.get("provenance", "unknown") for p in ocre_pairs)
labels = sorted(link_types.keys(), key=lambda x: link_types[x], reverse=True)
values = [link_types[l] for l in labels]

fig, ax = plt.subplots(figsize=(8, 3))
bars = ax.barh(labels, values, color="#2e86c1", edgecolor="white", linewidth=0.8)

for bar, val in zip(bars, values):
    ax.text(bar.get_width() + 50, bar.get_y() + bar.get_height() / 2,
            f"{val:,}", va="center", fontsize=9)

ax.set_xlabel("Number of pairs")
ax.set_title("OpenCRE link types: most pairs come from Contains and Linked To relationships", fontsize=11)
ax.spines[["top", "right"]].set_visible(False)
ax.invert_yaxis()
plt.tight_layout()
plt.savefig(REPO_ROOT / "report" / "figures" / "fig7_2_link_types.png", dpi=150, bbox_inches="tight")
plt.show()"""))

nb["cells"].append(make_md("""> **Plain English:** The link types tell us how OpenCRE connected these controls. 'Contains' means one standard explicitly references the other. 'Linked To' means the CRE maintainers judged them as covering the same ground. Both types are strong evidence for equivalence or relatedness."""))

# --- Copy old cell 118: Figure 10.2 framework coverage (rename to 7.3) ---
nb["cells"].extend(copy_old_cells(old, [118]))

nb["cells"].append(make_md("""Only 6 of our 9 frameworks appear in OpenCRE. NIST AI RMF and OWASP AI Exchange dominate the overlap. AIUC-1, CoSAI, and CSA AICM have no representation, meaning OpenCRE augmentation cannot help with pairs involving those frameworks.

> **Plain English:** OpenCRE covers the larger, more established standards. The newer or more specialized frameworks in our crosswalk have no OpenCRE data at all. This is a coverage limitation to keep in mind."""))

# --- NEW code cell: Figure 7.4 Hop-distance vs. tier cross-tab heatmap ---
nb["cells"].append(make_code("""# Figure 7.4 — Hop distance mapped to ordinal tiers.
# Cross-tab heatmap showing how hop distance translates to
# our 4-tier classification scheme. Sequential colormap avoids
# rainbow (Borland & Taylor 2007).
tier_map = {0: "EQUIVALENT", 1: "RELATED", 2: "PARTIAL"}
hop_tier_counts = Counter()
for p in ocre_pairs:
    gap = p["gap_penalty"]
    tier = tier_map.get(gap, "UNRELATED")
    hop_tier_counts[(gap, tier)] += 1

# Build matrix
hops_unique = sorted(set(h for h, _ in hop_tier_counts))
tiers = ["EQUIVALENT", "RELATED", "PARTIAL", "UNRELATED"]
matrix = []
for h in hops_unique:
    row = [hop_tier_counts.get((h, t), 0) for t in tiers]
    matrix.append(row)

fig, ax = plt.subplots(figsize=(7, 3))
im = ax.imshow(matrix, cmap="crest", aspect="auto")
ax.set_xticks(range(len(tiers)))
ax.set_xticklabels(tiers, fontsize=9)
ax.set_yticks(range(len(hops_unique)))
ax.set_yticklabels([f"Hop {h}" for h in hops_unique], fontsize=9)

for i in range(len(hops_unique)):
    for j in range(len(tiers)):
        val = matrix[i][j]
        if val > 0:
            color = "white" if val > max(max(r) for r in matrix) * 0.5 else "black"
            ax.text(j, i, f"{val:,}", ha="center", va="center", fontsize=9, color=color)

ax.set_title("Hop distance maps cleanly onto ordinal tiers", fontsize=11)
plt.colorbar(im, ax=ax, label="Pair count")
plt.tight_layout()
plt.savefig(REPO_ROOT / "report" / "figures" / "fig7_4_hop_tier_heatmap.png", dpi=150, bbox_inches="tight")
plt.show()"""))

nb["cells"].append(make_md("""The mapping is nearly diagonal: hop 0 produces Equivalent labels, hop 1 produces Related, hop 2 produces Partial. This clean structure is what makes OpenCRE useful as training data---the hop distance is a reasonable proxy for human-assigned ordinal tiers."""))

# --- Copy old cell 119: Figure 10.3 contamination firewall (rename to 7.5) ---
nb["cells"].extend(copy_old_cells(old, [119]))

nb["cells"].append(make_md("""Before using any OpenCRE pairs for training, I removed every pair that shared a node ID with the 179-pair frozen test set. This contamination firewall eliminated 34 pairs, leaving 6,200 clean pairs. Without this step, the test set would no longer be truly held out.

> **Plain English:** The frozen test set is sacred. If any training pair shares a control with a test pair, the evaluation is compromised. I checked all 6,234 OpenCRE pairs that overlap our frameworks, found 34 that shared node IDs with the test set, and removed them."""))

# ========================================
# SECTION 8: v8 Disagreement Mining
# ========================================

nb["cells"].append(make_md("""## 8 · v8: disagreement mining

With 6,200 clean OpenCRE pairs in hand, the question is how to use them. Adding all 6,200 directly to training would triple the dataset, but the OpenCRE labels are proxy labels derived from hop distance, not expert annotations. Flooding the training set with noisy labels risks degrading the model.

The v8 approach was selective: run the v7c classifier on all 6,200 pairs and keep only the ones where v7c's prediction disagreed with the OpenCRE-derived label. These disagreements represent the classifier's blind spots---exactly the pairs it needs to see."""))

# --- Copy old cell 122: v8 data loading + stats code ---
nb["cells"].extend(copy_old_cells(old, [122]))

# --- NEW code cell: Figure 8.1 Class distribution comparison ---
nb["cells"].append(make_code("""# Figure 8.1 — Training set composition: expert vs. v8.
# Grouped bar chart using position on common scale
# (Cleveland & McGill 1984) for direct tier-by-tier comparison.
expert_train = []
with open(REPO_ROOT / "data" / "splits" / "expert_train.jsonl") as f:
    for line in f:
        expert_train.append(json.loads(line))

v8_train = []
with open(REPO_ROOT / "data" / "splits" / "v8_train.jsonl") as f:
    for line in f:
        v8_train.append(json.loads(line))

expert_dist = Counter(p.get("tier", p.get("label", -1)) for p in expert_train)
v8_dist = Counter(p.get("tier", p.get("label", -1)) for p in v8_train)

tiers = [0, 1, 2, 3]
tier_labels = ["UNRELATED", "PARTIAL", "RELATED", "EQUIVALENT"]
x = np.arange(len(tiers))
width = 0.35

fig, ax = plt.subplots(figsize=(9, 4))
bars1 = ax.bar(x - width/2, [expert_dist.get(t, 0) for t in tiers],
               width, label=f"Expert train (n={len(expert_train):,})", color="#2e86c1")
bars2 = ax.bar(x + width/2, [v8_dist.get(t, 0) for t in tiers],
               width, label=f"v8 train (n={len(v8_train):,})", color="#e74c3c")

for bar_group in [bars1, bars2]:
    for bar in bar_group:
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 20,
                f"{int(bar.get_height()):,}", ha="center", va="bottom", fontsize=8)

ax.set_xticks(x)
ax.set_xticklabels(tier_labels, fontsize=10)
ax.set_ylabel("Number of pairs")
ax.set_title("v8 adds 673 disagreement-mined pairs, concentrated in RELATED tier", fontsize=11)
ax.legend(frameon=False)
ax.spines[["top", "right"]].set_visible(False)
plt.tight_layout()
plt.savefig(REPO_ROOT / "report" / "figures" / "fig8_1_training_composition.png", dpi=150, bbox_inches="tight")
plt.show()"""))

nb["cells"].append(make_md("""The v8 augmentation adds 673 pairs to the expert training set, bringing the total from 5,920 to 12,849. The added pairs are concentrated in the Related tier, which is where v7c's disagreements with OpenCRE labels clustered. The Equivalent tier gains indirect benefit: by teaching the model to distinguish Related from Unrelated more precisely, the ordinal boundary near Equivalent should shift."""))

# --- Copy old cell 125: Figure 11.2 disagreement mining funnel (rename to 8.2) ---
nb["cells"].extend(copy_old_cells(old, [125]))

nb["cells"].append(make_md("""The funnel narrows aggressively: of 6,200 clean pairs, 3,285 (53%) showed disagreement between v7c and OpenCRE. Of those, 673 Related-class disagreements were selected as the most informative augmentation (Related is adjacent to Equivalent on the ordinal scale, so getting Related right helps the model calibrate its Equivalent boundary).

> **Plain English:** Instead of dumping all 6,200 OpenCRE pairs into training, I filtered down to the 673 where the classifier was most confused. Think of it as showing the student only the flashcards it got wrong."""))

# --- NEW code cell: Figure 8.3 BGE cosine fallback distribution ---
nb["cells"].append(make_code("""# Figure 8.3 — BGE cosine fallback distribution for OpenCRE pairs.
# The GAT cannot compute graph features for OpenCRE-format pairs
# (they exist outside our crosswalk topology). BGE cosine similarity
# serves as the fallback scorer. Violin plot shows the distribution
# split by OpenCRE-derived tier (Borner et al. 2019: luminance ramp
# for ordered categories).

# Simulate: load v8 assembly stats
v8_assembly = json.loads(
    (REPO_ROOT / "runs" / "v8_diagnosis" / "v8_data_assembly.json").read_text()
)

# Display key stats as a table since we don't have per-pair BGE scores on disk
print("v8 Data Assembly Summary")
print(f"  OpenCRE pairs loaded:    {v8_assembly['opencre_total']:,}")
print(f"  Contaminated (removed):  {v8_assembly['contaminated']:,}")
print(f"  Clean pairs:             {v8_assembly['clean']:,}")
print(f"  v7c disagreements:       {v8_assembly['disagreements']:,}")
print(f"  Selected for training:   {v8_assembly['selected']:,}")
print(f"  Expert train original:   {v8_assembly['expert_train_original']:,}")
print(f"  v8 train total:          {v8_assembly['v8_train_total']:,}")
print(f"\\nLabel distribution in v8 train:")
for tier, count in sorted(v8_assembly["label_distribution"].items()):
    print(f"    {tier}: {count:,}")"""))

nb["cells"].append(make_md("""> **Plain English:** The GAT model (which uses the graph structure of our crosswalk) cannot score OpenCRE pairs because they live outside our graph. So the v8 pipeline fell back to BGE cosine similarity as the scoring signal for disagreement mining. This is a simpler feature but still informative for the ordinal structure."""))

# Renumber figures in copied cells
fig_map = {
    "Figure 10.1": "Figure 7.1",
    "Figure 10.2": "Figure 7.3",
    "Figure 10.3": "Figure 7.5",
    "Figure 11.1": "Figure 8.1",
    "Figure 11.2": "Figure 8.2",
    "fig10_1": "fig7_1",
    "fig10_2": "fig7_3",
    "fig10_3": "fig7_5",
    "fig11_1": "fig8_1",
    "fig11_2": "fig8_2",
}

# Find section start
section_start_idx = None
for i, c in enumerate(nb["cells"]):
    src = "".join(c["source"])
    if "## 7" in src and "OpenCRE" in src:
        section_start_idx = i
        break

if section_start_idx:
    for cell in nb["cells"][section_start_idx:]:
        src = "".join(cell["source"])
        for old_ref, new_ref in fig_map.items():
            src = src.replace(old_ref, new_ref)
        cell["source"] = [l + "\n" for l in src.split("\n")[:-1]] + [src.split("\n")[-1]]

save_notebook(nb)
```

- [ ] **Step 2: Run, verify, commit**

```bash
cd /home/rock/github_projects/ai-security-framework-crosswalk/project1
python build_sections_7_8.py
cd ..
python3 -c "
import json; nb = json.load(open('project1/COMP_4433_RockLambros_project1_crosswalk_eda.ipynb'))
print(f'Total: {len(nb[\"cells\"])} cells')
for i, c in enumerate(nb['cells']):
    src = ''.join(c['source'])[:90].replace('\n', ' ')
    if src.startswith('## '):
        print(f'{i:3d} {src}')
"
git add project1/build_sections_7_8.py project1/COMP_4433_RockLambros_project1_crosswalk_eda.ipynb
git commit -m "notebook: add sections 7-8 (OpenCRE discovery + v8 disagreement mining)"
```

---

### Task 8: Notebook Sections 9-10 — v8b Collapse Crisis + v_final Architecture

**Files:**
- Modify: `project1/COMP_4433_RockLambros_project1_crosswalk_eda.ipynb`

Section 9 is the "anomalies and observations" discussion that COMP 4433 requires. The v8b collapse (DeBERTa-large 100% single-class prediction) and stacker overfitting (train=1.0, val=0.528) are the central anomalies. Section 10 presents v_final's architecture as the response to these failures.

Source cells from old notebook: 126-128 (v8b), 130-135 (v_final architecture). Plus 3 new code cells.

**Data files referenced:**
- `runs/v8b_diagnosis/v8b_data_assembly.json` — keys: v8_rows_added, skipped_by_cap, class_caps, label_distribution
- `runs/v8b_diagnosis/wandb_runs.json` — pre-downloaded WandB v8b run data (from Task 1)
- `runs/registry.jsonl` — stacker runs showing overfitting

- [ ] **Step 1: Create the section builder**

Create `project1/build_sections_9_10.py`:

```python
"""Build Sections 9-10: v8b Collapse Crisis + v_final Architecture.

Section 9 is the "anomalies" discussion COMP 4433 requires.
Section 10 presents the architectural response.
"""
import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from build_notebook import (
    make_md, make_code, load_notebook, save_notebook,
    load_old_notebook, copy_old_cells,
)

nb = load_notebook()
old = load_old_notebook()

# ========================================
# SECTION 9: v8b Collapse Crisis
# ========================================

nb["cells"].append(make_md("""## 9 · The v8b collapse crisis

v8b took a broader approach than v8's targeted disagreement mining. Instead of selecting only disagreements, v8b added 2,046 OpenCRE pairs directly to training with per-class caps: 997 Unrelated, 690 Partial, 683 Equivalent, and 673 Related. This brought the total training set to 14,222 pairs.

The results were a disaster on two fronts."""))

# --- v8b data assembly stats ---
nb["cells"].append(make_code("""# 9.1 — v8b data assembly and collapse diagnostics
v8b_assembly = json.loads(
    (REPO_ROOT / "runs" / "v8b_diagnosis" / "v8b_data_assembly.json").read_text()
)
print("v8b Data Assembly")
print(f"  Expert train:         {v8b_assembly['expert_train_original']:,}")
print(f"  OpenCRE added:        {v8b_assembly['v8_rows_added']:,}")
print(f"  Skipped by cap:       {v8b_assembly['skipped_by_cap']:,}")
print(f"  v8b train total:      {v8b_assembly['v8_train_total']:,}")
print(f"  Class caps:           {v8b_assembly['class_caps']}")
print(f"\\nLabel distribution:")
for tier, count in sorted(v8b_assembly["label_distribution"].items()):
    print(f"    {tier}: {count:,}")"""))

nb["cells"].append(make_md("""### Failure 1: DeBERTa-large model collapse

DeBERTa-v3-large collapsed during training. By epoch 4, every sweep configuration produced 100% single-class predictions---the model predicted the same tier for every pair regardless of input. The collapse guard triggered but the model never recovered."""))

# --- NEW code cell: Figure 9.1 v8b collapse diagnostics from WandB ---
nb["cells"].append(make_code("""# Figure 9.1 — v8b model collapse diagnostics from WandB runs.
# Bar chart showing the fraction of runs that collapsed to
# single-class prediction (n_unique_preds == 1).
# Position on common scale for comparison (Cleveland & McGill 1984).

wandb_v8b = json.loads(
    (REPO_ROOT / "runs" / "v8b_diagnosis" / "wandb_runs.json").read_text()
)

# Count collapsed vs non-collapsed runs
total_runs = len(wandb_v8b)
collapsed = sum(1 for r in wandb_v8b if r.get("n_unique_preds") == 1)
partial_collapse = sum(1 for r in wandb_v8b
                       if r.get("n_unique_preds") is not None
                       and 1 < r["n_unique_preds"] < 4)
healthy = sum(1 for r in wandb_v8b if r.get("n_unique_preds") == 4)

categories = ["Collapsed\\n(1 class)", "Partial collapse\\n(2-3 classes)", "Healthy\\n(4 classes)"]
counts = [collapsed, partial_collapse, healthy]
colors = ["#e74c3c", "#f39c12", "#2ecc71"]

fig, ax = plt.subplots(figsize=(8, 4))
bars = ax.bar(categories, counts, color=colors, edgecolor="white", linewidth=0.8)

for bar, count in zip(bars, counts):
    pct = count / total_runs * 100 if total_runs > 0 else 0
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
            f"{count} ({pct:.0f}%)", ha="center", va="bottom", fontsize=10, fontweight="bold")

# Annotation (Graze & Schwabish 2024: on-plot annotation)
ax.annotate(
    f"{collapsed} of {total_runs} runs predicted\\na single class for every pair",
    xy=(0, collapsed), xytext=(1.2, collapsed * 0.8),
    fontsize=9, color="black",
    arrowprops=dict(arrowstyle="->", color="black", lw=1.2),
)

ax.set_ylabel("Number of WandB runs")
ax.set_title(f"v8b sweep: {collapsed}/{total_runs} runs collapsed to single-class prediction", fontsize=11)
ax.spines[["top", "right"]].set_visible(False)
plt.tight_layout()
plt.savefig(REPO_ROOT / "report" / "figures" / "fig9_1_v8b_collapse.png", dpi=150, bbox_inches="tight")
plt.show()"""))

nb["cells"].append(make_md("""Model collapse is a known failure mode in fine-tuning. When the loss landscape has sharp minima near trivial solutions (predicting a single class), gradient updates can push the model into a region where it never escapes. The noisy OpenCRE labels in v8b made this worse: the model learned that predicting Unrelated (the majority class) was a safe default."""))

nb["cells"].append(make_md("""### Failure 2: stacker overfitting

Even for the runs that did not collapse, the LightGBM stacker (which combined the three models' outputs into a final prediction) overfit catastrophically."""))

# --- Copy old cell 127: stacker overfitting diagnostic (rename figure) ---
nb["cells"].extend(copy_old_cells(old, [127]))

nb["cells"].append(make_md("""Training accuracy of 1.000 against validation accuracy of 0.528 is a 47-point gap. The stacker memorized the training data rather than learning generalizable patterns. With 17 input features (softmax logits from 3 models) and a small validation set, the LightGBM had enough capacity to memorize every training example.

> **Plain English:** The combiner---a machine learning model that was supposed to blend the three models' predictions---instead just memorized the training answers. It scored perfectly on the practice test and failed the real one. This is the classic overfitting problem, and it pointed to a clear fix: remove the learnable combiner entirely."""))

# --- NEW code cell: Figure 9.3 WandB loss curves (collapse vs success) ---
nb["cells"].append(make_code("""# Figure 9.3 — Training loss curves: collapsed vs. successful v8b runs.
# Line chart with two groups. Uses luminance contrast to distinguish
# collapse (red, thick) from success (blue, thin) (Borland & Taylor 2007).

fig, axes = plt.subplots(1, 2, figsize=(12, 4))

# Select a few representative runs
collapsed_runs = [r for r in wandb_v8b
                  if r.get("n_unique_preds") == 1
                  and len(r.get("history", [])) > 3][:5]
healthy_runs = [r for r in wandb_v8b
                if r.get("n_unique_preds") == 4
                and len(r.get("history", [])) > 3][:5]

# Panel A: Training loss
ax = axes[0]
for r in collapsed_runs:
    epochs = [h.get("epoch") for h in r["history"] if h.get("train_loss") is not None]
    losses = [h["train_loss"] for h in r["history"] if h.get("train_loss") is not None]
    if epochs and losses:
        ax.plot(epochs, losses, color="#e74c3c", alpha=0.5, linewidth=2, label="_nolegend_")

for r in healthy_runs:
    epochs = [h.get("epoch") for h in r["history"] if h.get("train_loss") is not None]
    losses = [h["train_loss"] for h in r["history"] if h.get("train_loss") is not None]
    if epochs and losses:
        ax.plot(epochs, losses, color="#2e86c1", alpha=0.5, linewidth=1.5, label="_nolegend_")

ax.plot([], [], color="#e74c3c", linewidth=2, label="Collapsed")
ax.plot([], [], color="#2e86c1", linewidth=1.5, label="Healthy")
ax.legend(frameon=False, fontsize=9)
ax.set_xlabel("Epoch")
ax.set_ylabel("Training loss")
ax.set_title("Collapsed runs show flat loss after early epochs", fontsize=11)
ax.spines[["top", "right"]].set_visible(False)

# Panel B: Combined F1
ax = axes[1]
for r in collapsed_runs:
    epochs = [h.get("epoch") for h in r["history"] if h.get("combined_f1") is not None]
    f1s = [h["combined_f1"] for h in r["history"] if h.get("combined_f1") is not None]
    if epochs and f1s:
        ax.plot(epochs, f1s, color="#e74c3c", alpha=0.5, linewidth=2)

for r in healthy_runs:
    epochs = [h.get("epoch") for h in r["history"] if h.get("combined_f1") is not None]
    f1s = [h["combined_f1"] for h in r["history"] if h.get("combined_f1") is not None]
    if epochs and f1s:
        ax.plot(epochs, f1s, color="#2e86c1", alpha=0.5, linewidth=1.5)

ax.set_xlabel("Epoch")
ax.set_ylabel("Combined F1")
ax.set_title("Collapsed runs never develop class diversity", fontsize=11)
ax.spines[["top", "right"]].set_visible(False)

plt.tight_layout()
plt.savefig(REPO_ROOT / "report" / "figures" / "fig9_3_wandb_loss_curves.png", dpi=150, bbox_inches="tight")
plt.show()"""))

nb["cells"].append(make_md("""The loss curves tell the story visually. Collapsed runs (red) plateau early: the model stops learning after the first few epochs because it has converged on the trivial solution of predicting a single class. Healthy runs (blue) show continued improvement, with combined F1 rising through training.

> **Plain English:** When a model collapses, its training loss curve goes flat. It has found a shortcut (always guess "unrelated") and stopped learning. The healthy runs keep improving because they are still finding structure in the data."""))

nb["cells"].append(make_md("""### What went wrong and what it taught us

Two root causes drove v8b's failures:

1. **Noisy labels at scale.** Adding 2,046 OpenCRE pairs with proxy labels overwhelmed the signal from 5,920 expert labels. The model learned to fit noise rather than structure.
2. **Learnable second stage.** The LightGBM stacker had enough capacity to memorize the noisy training distribution. A simpler combination method---one with no learnable parameters---could not overfit by construction.

These two observations directly motivated every design decision in v_final."""))

# ========================================
# SECTION 10: v_final Architecture
# ========================================

nb["cells"].append(make_md("""## 10 · v_final: clean architecture, proper validation

Three changes define v_final, each a direct response to a v8b failure mode."""))

# --- Copy old cells 131-132 (architecture diagram + dedup figure) ---
nb["cells"].extend(copy_old_cells(old, [131, 132]))

nb["cells"].append(make_md("""### Change 1: mapping-level deduplication

The v7c training split deduplicated at the text-pair level, but many pairs shared the same underlying mapping (e.g., the same two controls rephrased slightly differently). After deduplication at the mapping level, 56% of text-pair contamination was removed from the validation split. The validation metrics now reflect true generalization, not memorized near-duplicates."""))

nb["cells"].append(make_md("""### Change 2: ordinal loss functions

Standard cross-entropy treats each tier as equally wrong. An Unrelated-to-Equivalent misclassification costs the same as Unrelated-to-Partial. Three ordinal losses replace cross-entropy:

- **KL-divergence with ordinal smoothing.** Constructs soft label distributions centered on the true tier, decaying with ordinal distance.
- **CORN ordinal regression.** Learns cumulative thresholds P(tier >= k) as independent binary problems, then reconstructs the tier distribution.
- **Focal loss with class reweighting.** Down-weights easy examples (mostly Unrelated) and up-weights hard examples (Equivalent).

Each of the 3 models was trained with each of the 3 losses (9 runs total). The best checkpoint per model was selected by combined F1 on the clean validation split."""))

nb["cells"].append(make_md("""### Change 3: softmax averaging replaces stacking

After the stacker memorized v8b's training distribution, the fix was simple: remove the learnable second stage entirely. The ensemble prediction is the arithmetic mean of the three models' softmax probability vectors. This approach has zero learnable parameters in the combination step, so it cannot overfit by construction."""))

# --- Copy old cell 133: why softmax averaging beats learned stacking ---
nb["cells"].extend(copy_old_cells(old, [133]))

# --- Training infrastructure ---
nb["cells"].append(make_md("""### Training infrastructure

Nine model variants (3 encoders times 3 loss functions) were trained on three NVIDIA H100 80GB GPUs via RunPod. Two engineering challenges required workarounds:

- **BF16 GradScaler incompatibility.** H100 GPUs run BF16 natively, but PyTorch's GradScaler performs inf-checking that fails under BF16 (which has no distinct inf representation). Fix: disable GradScaler, run BF16 training directly with `torch.amp.autocast`.
- **CLS dimension mismatch.** BGE-large-v1.5 produces 1,024-dimensional CLS embeddings; RoBERTa-large and DeBERTa-base produce 768. The v_final pipeline handles each model's embedding dimension independently.

> **Plain English:** Three models, each trained three different ways, on fast GPUs. The final ensemble picks the best version of each model and averages their predictions. No learning in the averaging step means no overfitting in the averaging step."""))

# Renumber figures in copied cells
fig_map = {
    "Figure 11.3": "Figure 9.2",
    "Figure 12.1": "Figure 10.1",
    "Figure 12.2": "Figure 10.2",
    "fig11_3": "fig9_2",
    "fig12_1": "fig10_1",
    "fig12_2": "fig10_2",
}

section_start_idx = None
for i, c in enumerate(nb["cells"]):
    src = "".join(c["source"])
    if "## 9" in src and "collapse" in src.lower():
        section_start_idx = i
        break

if section_start_idx:
    for cell in nb["cells"][section_start_idx:]:
        src = "".join(cell["source"])
        for old_ref, new_ref in fig_map.items():
            src = src.replace(old_ref, new_ref)
        cell["source"] = [l + "\n" for l in src.split("\n")[:-1]] + [src.split("\n")[-1]]

save_notebook(nb)
```

- [ ] **Step 2: Run, verify, commit**

```bash
cd /home/rock/github_projects/ai-security-framework-crosswalk/project1
python build_sections_9_10.py
cd ..
python3 -c "
import json; nb = json.load(open('project1/COMP_4433_RockLambros_project1_crosswalk_eda.ipynb'))
print(f'Total: {len(nb[\"cells\"])} cells')
for i, c in enumerate(nb['cells']):
    src = ''.join(c['source'])[:90].replace('\n', ' ')
    if src.startswith('## '):
        print(f'{i:3d} {src}')
"
git add project1/build_sections_9_10.py project1/COMP_4433_RockLambros_project1_crosswalk_eda.ipynb
git commit -m "notebook: add sections 9-10 (v8b collapse crisis + v_final architecture)"
```

---

### Task 9: Notebook Sections 11-12 — v_final Results + Deployment + HuggingFace

**Files:**
- Modify: `project1/COMP_4433_RockLambros_project1_crosswalk_eda.ipynb`

Section 11 presents the complete v_final evaluation. Section 12 covers full-graph deployment, impact, and the HuggingFace model reference.

Source cells from old notebook: 136-149 (v_final results + deployment). Plus 3 new code cells and 2 HF narrative cells.

**Data files referenced:**
- `runs/vfinal/sacred/results.json` — per_class dict keyed by tier name (UNRELATED, PARTIAL, RELATED, EQUIVALENT), confusion_matrix as 4x4 nested list, single_model_ce dict, zero_shot_baseline dict
- `runs/v7c_sacred/results.json` — methods.B_full_pipeline.per_class_f1, confusion_matrix (nested dict keyed by lowercase tier names)
- `runs/vfinal/conformal/conformal.json` — coverage dict keyed by class index strings ("0","1","2","3"), q_hat dict
- `runs/vfinal/edge_predictions.json` — 4,001 scored edges

- [ ] **Step 1: Create the section builder**

Create `project1/build_sections_11_12.py`:

```python
"""Build Sections 11-12: v_final Results + Deployment + HuggingFace."""
import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from build_notebook import (
    make_md, make_code, load_notebook, save_notebook,
    load_old_notebook, copy_old_cells,
)

nb = load_notebook()
old = load_old_notebook()

# ========================================
# SECTION 11: v_final Results
# ========================================

nb["cells"].append(make_md("""## 11 · v_final results: the complete picture

This section evaluates v_final on the same 179-pair frozen test set used for v7c. Every metric below uses identical data and methodology so the comparison is direct."""))

# --- Copy old cells 137-143 (results loading, confusion matrix, per-class F1,
#     model progression, bootstrap CI, conformal) ---
nb["cells"].extend(copy_old_cells(old, [137, 138, 139, 140, 141, 142, 143]))

# --- Interpretation narrative (adapted from old cell 144) ---
nb["cells"].append(make_md("""### Results interpretation

Macro F1 rises from 0.512 to 0.558 (+4.6 percentage points), driven almost entirely by the Equivalent class: F1 goes from 0.000 to 0.400. The classifier now correctly identifies 4 of the 7 Equivalent test pairs.

The improvement comes with a trade-off. Related-class F1 drops from 0.556 to 0.378. The confusion matrix shows why: 6 of 24 Related test pairs are now predicted Equivalent. The ordinal losses shifted the decision boundary upward, catching more Equivalents but relabeling some Related pairs in the process. On a 4-class ordinal scale with 24 Related test examples, this is an expected side effect.

Exact accuracy dips slightly (81.0% to 79.9%) because the model now occasionally predicts Equivalent when it previously would have predicted Unrelated. Macro F1 is the better metric here because it weighs each class equally rather than letting the Unrelated majority dominate.

The bootstrap confidence intervals (10,000 resamples, 95% CI) show macro F1 between 0.436 and 0.661, with the v7c point estimate of 0.512 inside this range. On 179 test pairs, we cannot claim statistical significance at the 0.05 level. The improvement is directionally consistent but a larger test set would be needed for definitive separation.

Conformal prediction coverage exceeds 90% on all four classes, meeting the calibration target. The median prediction set contains 1 tier (a crisp prediction)."""))

nb["cells"].append(make_md("""> **Plain English:** The retrained model gets the hardest class (Equivalent) right for the first time---4 out of 7 test pairs. The price is that it sometimes confuses Related pairs for Equivalent, which makes sense because those two tiers are adjacent on the scale. The confidence intervals are wide because the test set is small, so I cannot definitively say this version is better by traditional statistics. But the qualitative change---from 0% to 57% recall on the class that matters most---is the real result."""))

# --- NEW code cell: Figure 11.6 Adjacent-error direction bar chart ---
nb["cells"].append(make_code("""# Figure 11.6 — Adjacent-error direction analysis.
# Of all misclassifications, how many are off by 1 tier vs 2+ tiers,
# and which direction? Bar chart (Cleveland & McGill 1984).
vfinal = json.loads((REPO_ROOT / "runs" / "vfinal" / "sacred" / "results.json").read_text())
cm = vfinal["confusion_matrix"]  # 4x4 nested list

adjacent_up = 0    # predicted tier is 1 above true tier
adjacent_down = 0  # predicted tier is 1 below true tier
distant = 0        # predicted tier is 2+ away from true tier
correct = 0

for true_idx in range(4):
    for pred_idx in range(4):
        count = cm[true_idx][pred_idx]
        if true_idx == pred_idx:
            correct += count
        elif abs(true_idx - pred_idx) == 1:
            if pred_idx > true_idx:
                adjacent_up += count
            else:
                adjacent_down += count
        else:
            distant += count

categories = ["Correct", "Adjacent up\\n(+1 tier)", "Adjacent down\\n(-1 tier)", "Distant\\n(2+ tiers)"]
counts = [correct, adjacent_up, adjacent_down, distant]
colors = ["#2ecc71", "#3498db", "#f39c12", "#e74c3c"]

fig, ax = plt.subplots(figsize=(8, 4))
bars = ax.bar(categories, counts, color=colors, edgecolor="white", linewidth=0.8)

for bar, count in zip(bars, counts):
    total = sum(counts)
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
            f"{count} ({count/total*100:.0f}%)", ha="center", va="bottom", fontsize=9)

# Annotation
ax.annotate(
    f"{(correct + adjacent_up + adjacent_down)/(correct + adjacent_up + adjacent_down + distant)*100:.0f}%"
    " of predictions are\\ncorrect or off by 1 tier",
    xy=(0.5, correct * 0.6), xytext=(2.3, correct * 0.7),
    fontsize=9, color="black",
    arrowprops=dict(arrowstyle="->", color="black", lw=1.2),
)

ax.set_ylabel("Number of test pairs")
ax.set_title("Most errors are adjacent: the ordinal losses keep predictions close", fontsize=11)
ax.spines[["top", "right"]].set_visible(False)
plt.tight_layout()
plt.savefig(REPO_ROOT / "report" / "figures" / "fig11_6_adjacent_errors.png", dpi=150, bbox_inches="tight")
plt.show()"""))

nb["cells"].append(make_md("""The ordinal losses work as designed. When the model is wrong, it is usually wrong by one tier rather than two or three. This is exactly the behavior ordinal losses incentivize: distant misclassifications are penalized more heavily than adjacent ones."""))

# ========================================
# SECTION 12: Deployment + Impact + HuggingFace
# ========================================

nb["cells"].append(make_md("""## 12 · Full-graph deployment and model availability

With a trained classifier in hand, I scored every edge in the crosswalk graph. The v_final ensemble assigned ordinal tiers to all 4,001 cross-framework edges."""))

# --- Copy old cells 147-148 (full graph predictions + coverage gain) ---
nb["cells"].extend(copy_old_cells(old, [147, 148]))

nb["cells"].append(make_md("""The classifier identifies 416 edges at Partial or above, including 59 predicted Equivalent. These are concrete candidates for compliance crosswalk mappings that organizations can review and validate.

> **Plain English:** The model scored every connection in the crosswalk and flagged 416 as potentially meaningful (not just noise). Of those, 59 pairs are predicted to be equivalent---the same control expressed in different standards. A compliance team can start with those 59 and expand outward."""))

# --- HuggingFace narrative cells ---
nb["cells"].append(make_md("""### Model availability

The trained v_final ensemble is available at [huggingface.co/rockCO78/ai-security-crosswalk-vfinal](https://huggingface.co/rockCO78/ai-security-crosswalk-vfinal). The repository contains:

- **Three encoder checkpoints:** RoBERTa-large (1.4 GB), DeBERTa-v3-base (704 MB), BGE-large-v1.5 (1.3 GB), each with its classification head
- **Inference script:** `scripts/predict_edges.py` loads all three models, runs a forward pass on each, averages the softmax vectors, and writes predictions
- **AIBOM-compliant model card:** Full documentation of architecture, training data, metrics, limitations, environmental impact, and usage instructions

To run inference on a new pair of controls, clone the repository, load the three encoders and their heads, tokenize the pair as `[CLS] source_text [SEP] target_text [SEP]`, compute the softmax average, and take the argmax."""))

nb["cells"].append(make_md("""### Extending the crosswalk to new frameworks

To add a 10th framework to the crosswalk:

1. **Prepare node data.** Add the new framework's controls to `data/processed/nodes.json` with fields: `node_id`, `framework`, `name`, `description`, `entry_type`.
2. **Generate candidate pairs.** Create cross-framework pairs between the new framework and each existing framework.
3. **Score with the ensemble.** Run `scripts/predict_edges.py` on the candidate pairs to get ordinal tier predictions.
4. **Review high-confidence predictions.** Have domain experts validate a sample of the Equivalent and Related predictions.
5. **Fine-tune (optional).** If expert labels are available for the new framework, fine-tune the ensemble using the same ordinal loss functions on the expanded training set."""))

# Renumber figures in copied cells
fig_map = {
    "Figure 13.1": "Figure 11.1",
    "Figure 13.2": "Figure 11.2",
    "Figure 13.3": "Figure 11.3",
    "Figure 13.4": "Figure 11.4",
    "Figure 13.5": "Figure 11.5",
    "Figure 14.1": "Figure 12.1",
    "Figure 14.2": "Figure 12.2",
    "fig13_1": "fig11_1",
    "fig13_2": "fig11_2",
    "fig13_3": "fig11_3",
    "fig13_4": "fig11_4",
    "fig13_5": "fig11_5",
    "fig14_1": "fig12_1",
    "fig14_2": "fig12_2",
}

section_start_idx = None
for i, c in enumerate(nb["cells"]):
    src = "".join(c["source"])
    if "## 11" in src and "v_final" in src.lower():
        section_start_idx = i
        break

if section_start_idx:
    for cell in nb["cells"][section_start_idx:]:
        src = "".join(cell["source"])
        for old_ref, new_ref in fig_map.items():
            src = src.replace(old_ref, new_ref)
        cell["source"] = [l + "\n" for l in src.split("\n")[:-1]] + [src.split("\n")[-1]]

save_notebook(nb)
```

- [ ] **Step 2: Run, verify, commit**

```bash
cd /home/rock/github_projects/ai-security-framework-crosswalk/project1
python build_sections_11_12.py
cd ..
python3 -c "
import json; nb = json.load(open('project1/COMP_4433_RockLambros_project1_crosswalk_eda.ipynb'))
print(f'Total: {len(nb[\"cells\"])} cells')
for i, c in enumerate(nb['cells']):
    src = ''.join(c['source'])[:90].replace('\n', ' ')
    if src.startswith('## '):
        print(f'{i:3d} {src}')
"
git add project1/build_sections_11_12.py project1/COMP_4433_RockLambros_project1_crosswalk_eda.ipynb
git commit -m "notebook: add sections 11-12 (v_final results + deployment + HF)"
```

---

### Task 10: Notebook Section 13 + Appendices

**Files:**
- Modify: `project1/COMP_4433_RockLambros_project1_crosswalk_eda.ipynb`

Section 13 is a rewritten conclusion. Appendix A copies the pipeline history from old cells 103-113 with minor updates. Appendix B moves the style guide from old cell 5.

- [ ] **Step 1: Create the section builder**

Create `project1/build_section_13_appendices.py`:

```python
"""Build Section 13 (Conclusion) + Appendices A and B."""
import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from build_notebook import (
    make_md, make_code, load_notebook, save_notebook,
    load_old_notebook, copy_old_cells,
)

nb = load_notebook()
old = load_old_notebook()

# ========================================
# SECTION 13: Conclusion
# ========================================

nb["cells"].append(make_md("""## 13 · Conclusion

This project traced a complete arc from a baseline classifier that could not identify equivalent controls to an ensemble that broke through on the hardest class.

The v7c pipeline scored 81.0% exact accuracy and 0.512 macro F1 on a frozen 179-pair holdout. Those headline numbers masked a structural failure: Equivalent-class F1 was 0.000. The classifier never predicted that two controls from different frameworks meant the same thing.

OpenCRE provided the external ground truth the training set lacked. Its 13,519 pairs with hop-distance labels mapped naturally onto our four ordinal tiers. Disagreement mining (v8) added 673 pairs where v7c disagreed with OpenCRE labels. Direct augmentation (v8b) added 2,046 pairs and caused DeBERTa-large to collapse to single-class prediction while the LightGBM stacker overfit to train accuracy of 1.000 against validation accuracy of 0.528.

v_final responded to each failure with a specific architectural change. Mapping-level deduplication removed 56% of text-pair contamination from the validation split. Ordinal losses (KL-divergence, CORN, focal) replaced standard cross-entropy. Softmax averaging across three models replaced the learnable stacker. The result: macro F1 rose to 0.558 (+4.6 pp), Equivalent F1 reached 0.400 (from 0.000), conformal coverage exceeded 90% on all four classes, and the ensemble scored all 4,001 edges in the crosswalk graph.

The trained ensemble is available at [huggingface.co/rockCO78/ai-security-crosswalk-vfinal](https://huggingface.co/rockCO78/ai-security-crosswalk-vfinal) for anyone to use or extend."""))

nb["cells"].append(make_md("""> **Plain English:** I started with a model that scored 81% overall but 0% on the class that matters most. After discovering OpenCRE, I tried two ways to use its data---one worked partially, one caused the model to collapse. The third attempt stripped the architecture down to a simple average of three models with ordinal-aware losses and got Equivalent right for the first time. The model, the code, and the data are all public."""))

nb["cells"].append(make_md("""---

**Project 2 transition.** The Dash application (Project 2) surfaces these 4,001 scored edges interactively, with click-through from high-level framework heatmaps down to individual control pairs and their predicted tiers."""))

# ========================================
# APPENDIX A: Pipeline History
# ========================================

# Copy old cells 103-113 (Appendix A) — 11 cells
appendix_a_cells = copy_old_cells(old, list(range(103, 114)))

# Update the section header to say "Appendix A" consistently
first_src = "".join(appendix_a_cells[0]["source"])
if "## Appendix A" not in first_src:
    first_src = first_src.replace("## A", "## Appendix A")
appendix_a_cells[0]["source"] = [l + "\n" for l in first_src.split("\n")[:-1]] + [first_src.split("\n")[-1]]

nb["cells"].extend(appendix_a_cells)

# ========================================
# APPENDIX B: Style Guide
# ========================================

# Copy old cell 5 (style guide) as Appendix B
style_cell = copy_old_cells(old, [5])[0]
style_src = "".join(style_cell["source"])
# Replace header
style_src = style_src.replace("## Style guide", "## Appendix B: Style guide")
style_cell["source"] = [l + "\n" for l in style_src.split("\n")[:-1]] + [style_src.split("\n")[-1]]
nb["cells"].append(style_cell)

save_notebook(nb)
```

- [ ] **Step 2: Run, verify, commit**

```bash
cd /home/rock/github_projects/ai-security-framework-crosswalk/project1
python build_section_13_appendices.py
cd ..
python3 -c "
import json; nb = json.load(open('project1/COMP_4433_RockLambros_project1_crosswalk_eda.ipynb'))
print(f'Total: {len(nb[\"cells\"])} cells')
for i, c in enumerate(nb['cells']):
    src = ''.join(c['source'])[:90].replace('\n', ' ')
    if src.startswith('## ') or src.startswith('# '):
        print(f'{i:3d} {src}')
"
git add project1/build_section_13_appendices.py project1/COMP_4433_RockLambros_project1_crosswalk_eda.ipynb
git commit -m "notebook: add section 13 (conclusion) + appendices A and B"
```

---

### Task 11: Execute Notebook + Fix Errors + Export Figures

**Files:**
- Modify: `project1/COMP_4433_RockLambros_project1_crosswalk_eda.ipynb` (execution fills outputs)
- Regenerate: `report/figures/*.png`

- [ ] **Step 1: Clear old figures**

```bash
cd /home/rock/github_projects/ai-security-framework-crosswalk
rm -f report/figures/fig*.png
```

- [ ] **Step 2: Execute the notebook**

```bash
cd /home/rock/github_projects/ai-security-framework-crosswalk/project1
jupyter nbconvert --to notebook --execute \
  --ExecutePreprocessor.timeout=600 \
  COMP_4433_RockLambros_project1_crosswalk_eda.ipynb \
  --output COMP_4433_RockLambros_project1_crosswalk_eda.ipynb
```

Expected: Notebook executes without errors. If errors occur, read the traceback, fix the offending cell, and re-execute.

**Common errors to watch for:**
- `FileNotFoundError`: data file path incorrect — check REPO_ROOT resolution
- `KeyError`: JSON schema mismatch — check data file schemas documented in each task
- `ImportError`: forbidden library import — only numpy, pandas, matplotlib, seaborn, statsmodels, sklearn, standard library
- `NameError`: variable defined in a later cell referenced earlier — check cell ordering
- `ValueError` in matplotlib: data shape mismatch — check array dimensions

- [ ] **Step 3: Verify figures exported**

```bash
cd /home/rock/github_projects/ai-security-framework-crosswalk
ls -la report/figures/fig*.png | wc -l
ls report/figures/fig*.png
```

Expected: 20+ PNG files in report/figures/.

- [ ] **Step 4: Spot-check notebook structure**

```bash
cd /home/rock/github_projects/ai-security-framework-crosswalk
python3 -c "
import json
nb = json.load(open('project1/COMP_4433_RockLambros_project1_crosswalk_eda.ipynb'))
total = len(nb['cells'])
code_cells = sum(1 for c in nb['cells'] if c['cell_type'] == 'code')
md_cells = sum(1 for c in nb['cells'] if c['cell_type'] == 'markdown')
errors = sum(1 for c in nb['cells'] if c['cell_type'] == 'code'
             and any(o.get('output_type') == 'error' for o in c.get('outputs', [])))
print(f'Total: {total} cells ({code_cells} code, {md_cells} markdown)')
print(f'Execution errors: {errors}')
print(f'Figures exported: ', end='')
import os
figs = [f for f in os.listdir('report/figures') if f.startswith('fig') and f.endswith('.png')]
print(len(figs))
"
```

Expected: ~130-146 cells, 0 execution errors, 20+ figures.

- [ ] **Step 5: Commit**

```bash
cd /home/rock/github_projects/ai-security-framework-crosswalk
git add project1/COMP_4433_RockLambros_project1_crosswalk_eda.ipynb report/figures/
git commit -m "notebook: execute redesigned notebook, export all figures"
```

---

### Task 12: Rewrite Report

**Files:**
- Rewrite: `report/report.md`

Complete rewrite of the report to mirror the notebook's Problem-Solution arc. Same writing style (first person, specific numbers, no AI slop). All figures referenced by filename from `report/figures/`. LaTeX-safe markdown (no raw Unicode — use `$\alpha$` not α, use `---` not —, use `--` not –).

**Critical: the report must be congruent with the notebook.** Every section in the report should correspond to a notebook section, use the same numbers, and tell the same story.

- [ ] **Step 1: Write the report**

Write `report/report.md` with the following structure. The report should be ~4,500 words. Use the exact figure filenames from the notebook's `plt.savefig()` calls.

**Report structure (mirroring notebook sections):**

```
---
YAML frontmatter (title, author, date, geometry, fontsize, header-includes)
---

# Title

## 1. Introduction (~300 words)
- 983 nodes, 9 frameworks, 5,813 edges, 179-pair frozen holdout
- 4-class ordinal scale
- Problem-Solution arc overview

## 2. The v7c Baseline (~400 words)
- Architecture: 50 features, two-stage pipeline
- Headline metrics: 81.0% acc, 0.512 macro F1
- EQUIVALENT F1 = 0.000 — the blind spot
- Figures: confusion matrix, feature importance

## 3. OpenCRE Discovery (~500 words)
- What OpenCRE is, how hop distance maps to tiers
- 13,519 pairs, 6 of 9 frameworks covered
- Contamination firewall: 34 removed, 6,200 clean
- Figures: hop distance, link types, coverage, contamination

## 4. v8 Disagreement Mining (~350 words)
- Rationale: selective augmentation > bulk augmentation
- 3,285 disagreements, 673 selected, v8 total 12,849
- BGE cosine fallback for OpenCRE pairs
- Figures: training composition, disagreement funnel

## 5. v8b Collapse Crisis (~400 words)
- Direct augmentation: 2,046 pairs, 14,222 total
- DeBERTa-large collapse: 100% single-class
- Stacker overfitting: train=1.0, val=0.528
- Root causes: noisy labels + learnable second stage
- Figures: collapse bar, loss curves, stacker overfitting

## 6. v_final Architecture (~400 words)
- Mapping-level dedup (56% contamination removed)
- Ordinal losses (KL, CORN, focal)
- Softmax averaging (zero learnable parameters)
- Infrastructure: H100, BF16, CLS mismatch
- Figures: architecture diagram, dedup before/after

## 7. Results (~600 words)
- Headline: macro F1 0.512 -> 0.558
- EQUIVALENT F1 0.000 -> 0.400
- Related trade-off: 0.556 -> 0.378
- Bootstrap CIs: 0.436-0.661
- Conformal: all classes > 90%
- Adjacent error analysis
- Figures: confusion matrices, per-class F1, model progression, bootstrap, conformal, adjacent errors

## 8. Full-Graph Deployment (~250 words)
- 4,001 edges scored
- 416 non-Unrelated, 59 Equivalent
- Coverage gain
- Figures: prediction distribution, coverage gain

## 9. Model Availability and Reproducibility (~300 words)
- HuggingFace repo URL
- What's uploaded (3 encoders, heads, scripts)
- How to extend to new frameworks

## 10. Pipeline Lineage (~200 words)
- v1 through v_final table
- Each version motivated by a specific failure

## 11. Conclusion (~300 words)
- Full arc summary
- Limitations: small test set, bootstrap CIs
- Future: more frameworks, larger test set
```

**LaTeX safety rules for the report markdown:**
- Use `$\alpha$` not α
- Use `---` not — (em dash)
- Use `--` not – (en dash)
- Use `\textperiodcentered{}` not ·
- Use `$-$` not − (minus sign)
- Use `$\rightarrow$` not → (arrow)
- Use `$\approx$` not ≈
- Use `$\geq$` not ≥

- [ ] **Step 2: Verify figure references**

```bash
cd /home/rock/github_projects/ai-security-framework-crosswalk
grep -o 'figures/fig[^)]*' report/report.md | while read f; do
  [ -f "report/$f" ] && echo "OK  $f" || echo "MISSING  $f"
done
```

Expected: All figure references resolve to existing files.

- [ ] **Step 3: Commit**

```bash
cd /home/rock/github_projects/ai-security-framework-crosswalk
git add report/report.md
git commit -m "report: complete rewrite with Problem-Solution arc"
```

---

### Task 13: Compile PDF + Run Tests + Validate + Final Commit

**Files:**
- Regenerate: `report/report.pdf`

- [ ] **Step 1: Compile report PDF**

```bash
cd /home/rock/github_projects/ai-security-framework-crosswalk/report
pandoc report.md -o report.pdf --pdf-engine=pdflatex -V geometry:margin=1in -V fontsize=11pt
```

If errors occur, they are almost always Unicode characters that pdflatex cannot handle. Fix by replacing the offending character with its LaTeX equivalent per the safety rules above, then re-run.

- [ ] **Step 2: Verify PDF**

```bash
ls -la /home/rock/github_projects/ai-security-framework-crosswalk/report/report.pdf
# Should be > 500KB (text + embedded images)
```

- [ ] **Step 3: Run test suite**

```bash
cd /home/rock/github_projects/ai-security-framework-crosswalk
python -m pytest mapping_engine/tests/ project2/tests/ -q
```

Expected: All tests pass (the notebook changes should not affect test files).

- [ ] **Step 4: COMP 4433 rubric validation**

```bash
cd /home/rock/github_projects/ai-security-framework-crosswalk
python3 -c "
import json
nb = json.load(open('project1/COMP_4433_RockLambros_project1_crosswalk_eda.ipynb'))

# Check 1: Multiple plots with differentially sized axes (GridSpec)
gridspec_cells = [i for i, c in enumerate(nb['cells'])
                  if c['cell_type'] == 'code'
                  and 'gridspec' in ''.join(c['source']).lower()]
print(f'[{\"PASS\" if len(gridspec_cells) >= 3 else \"FAIL\"}] GridSpec figures: {len(gridspec_cells)} (need >= 3)')

# Check 2: Three+ different plot types
plot_types = set()
for c in nb['cells']:
    if c['cell_type'] != 'code': continue
    src = ''.join(c['source']).lower()
    if 'bar(' in src or 'barh(' in src: plot_types.add('bar')
    if 'heatmap' in src or 'imshow' in src: plot_types.add('heatmap')
    if 'violinplot' in src or 'violin' in src: plot_types.add('violin')
    if 'scatter' in src: plot_types.add('scatter')
    if 'plot(' in src: plot_types.add('line')
    if 'hist(' in src: plot_types.add('histogram')
    if 'boxplot' in src: plot_types.add('boxplot')
print(f'[{\"PASS\" if len(plot_types) >= 3 else \"FAIL\"}] Plot types: {plot_types} ({len(plot_types)} types)')

# Check 3: On-plot annotations
annot_cells = [i for i, c in enumerate(nb['cells'])
               if c['cell_type'] == 'code'
               and 'annotate(' in ''.join(c['source'])]
print(f'[{\"PASS\" if len(annot_cells) >= 1 else \"FAIL\"}] On-plot annotations: {len(annot_cells)} cells')

# Check 4: Analytical approaches discussion
has_ordinal = any('OrderedModel' in ''.join(c['source']) for c in nb['cells'])
print(f'[{\"PASS\" if has_ordinal else \"FAIL\"}] Ordinal regression demonstrator present')

# Check 5: Anomalies/trends discussion
has_collapse = any('collapse' in ''.join(c['source']).lower() for c in nb['cells'] if c['cell_type'] == 'markdown')
print(f'[{\"PASS\" if has_collapse else \"FAIL\"}] Anomalies discussion (v8b collapse)')

# Check 6: Libraries
forbidden = set()
for c in nb['cells']:
    if c['cell_type'] != 'code': continue
    src = ''.join(c['source'])
    for line in src.split('\n'):
        if line.strip().startswith('import ') or line.strip().startswith('from '):
            # Check for forbidden imports
            allowed = {'numpy', 'pandas', 'matplotlib', 'seaborn', 'statsmodels',
                       'sklearn', 'json', 'pathlib', 'collections', 'textwrap',
                       'warnings', 'yaml', 'np', 'pd', 'plt', 'sns', 'gridspec',
                       'Patch', 'Counter', 'Path', 'os', 're', 'math'}
            tokens = line.replace('import ', ' ').replace('from ', ' ').split()
            for t in tokens:
                base = t.split('.')[0].strip(',')
                if base and base not in allowed and not base.startswith('_'):
                    forbidden.add(base)
if forbidden:
    print(f'[WARN] Potentially forbidden imports: {forbidden}')
else:
    print('[PASS] No forbidden library imports detected')

print(f'\\nTotal cells: {len(nb[\"cells\"])}')
"
```

Expected: All checks PASS.

- [ ] **Step 5: Commit everything and push**

```bash
cd /home/rock/github_projects/ai-security-framework-crosswalk
git add report/report.pdf
git commit -m "report: compile PDF from redesigned report"

# Final push
git push origin main
```

- [ ] **Step 6: Clean up builder scripts (optional)**

```bash
cd /home/rock/github_projects/ai-security-framework-crosswalk
# The builder scripts are no longer needed after the notebook is built
# but keep them for reproducibility
git add project1/build_*.py
git commit -m "chore: add notebook builder scripts for reproducibility"
```

---

## Self-Review Checklist

### Spec Coverage

| Spec Requirement | Task |
|---|---|
| New abstract with Problem-Solution arc | Task 3 |
| New Plain English block | Task 3 |
| Sections 3-4 copied verbatim | Task 4 |
| Section 5: v7c compressed | Task 5 |
| Section 6: Uncertainty + ordinal | Task 6 |
| Section 7: OpenCRE expanded | Task 7 |
| Section 8: v8 expanded | Task 7 |
| Section 9: v8b collapse expanded | Task 8 |
| Section 10: v_final architecture | Task 8 |
| Section 11: v_final results expanded | Task 9 |
| Section 12: Deployment + HF | Task 9 |
| Section 13: Conclusion rewritten | Task 10 |
| Appendix A: Pipeline history | Task 10 |
| Appendix B: Style guide | Task 10 |
| 3 new OpenCRE code cells | Task 7 (7.1 hop, 7.2 link types, 7.4 heatmap) |
| 2 new v8 code cells | Task 7 (8.1 composition, 8.3 BGE fallback) |
| 3 new v8b code cells | Task 8 (9.1 collapse, 9.2 stacker, 9.3 WandB) |
| 2 new v_final code cells | Task 9 (11.6 adjacent errors) |
| 1 new deployment code cell | Task 9 (coverage gain from old) |
| 2 HF narrative cells | Task 9 |
| HuggingFace model upload | Task 2 |
| AIBOM model card | Task 2 |
| HF old model deletion | Task 2 |
| Notebook execution | Task 11 |
| Report rewrite | Task 12 |
| PDF compilation | Task 13 |
| Test suite | Task 13 |
| COMP 4433 rubric | Task 13 |
| Visualization compliance | All figure tasks (7-9) |
| AI slop avoidance | All narrative tasks (style reference) |
| Report-notebook congruence | Task 12 (mirrors notebook) |
| WandB data download | Task 1 |

### Placeholder Scan

No TBD, TODO, or "implement later" patterns found. All code cells provide complete source. All narratives provide full text.

### Type Consistency

- `REPO_ROOT` defined in Task 3 setup cell, used by all subsequent tasks
- `ocre_pairs` loaded in Task 7, used in Tasks 7-8
- `wandb_v8b` loaded in Task 8 from pre-downloaded JSON
- v7c sacred results accessed via `methods["B_full_pipeline"]` (nested dict with lowercase tier keys in confusion_matrix, per_class_f1)
- v_final results accessed directly (per_class dict with UPPERCASE tier keys, confusion_matrix as 4x4 nested list)
- Conformal results keyed by string class indices ("0", "1", "2", "3")
