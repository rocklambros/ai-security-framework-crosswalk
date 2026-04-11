#!/usr/bin/env python3
"""Publish crosswalk-ce-v2.1 model artifacts to HuggingFace Hub.

Uploads fine-tuned cross-encoder models, stacker config, conformal config,
sacred evaluation results, and feature pipeline artifacts with an AIBOM-strong
model card (targeting score >= 85).
"""

import json
import subprocess
import tempfile
from pathlib import Path

from huggingface_hub import HfApi, create_repo

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
REPO_ID = "rockCO78/crosswalk-ce-v2.1"
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Artifacts to upload  (local_path relative to PROJECT_ROOT -> HF repo path)
ARTIFACTS = {
    # Cross-encoder classifier heads
    "runs/ce_v2/deberta/best/head.pt": "deberta/head.pt",
    "runs/ce_v2/roberta/best/head.pt": "roberta/head.pt",
    "runs/ce_v2/electra/best/head.pt": "electra/head.pt",
    # Stacker + conformal configs
    "runs/stacker_v2/best_params.json": "stacker/best_params.json",
    "runs/stacker_v2/conformal.json": "stacker/conformal.json",
    # Sacred evaluation results
    "results/sacred/sacred_ca388cbc.json": "evaluation/sacred_ca388cbc.json",
    # Feature pipeline
    "data/processed/ce_features_v2.npz": "features/ce_features_v2.npz",
}

# Encoder directories to upload (each ~1.3-1.7 GB)
ENCODER_DIRS = {
    "runs/ce_v2/deberta/best/encoder": "deberta/encoder",
    "runs/ce_v2/roberta/best/encoder": "roberta/encoder",
    "runs/ce_v2/electra/best/encoder": "electra/encoder",
}


def get_hf_token() -> str:
    """Retrieve HuggingFace token from pass."""
    result = subprocess.run(
        ["pass", "show", "huggingface/token"],
        capture_output=True, text=True, check=True,
    )
    return result.stdout.strip()


def build_model_card() -> str:
    """Generate AIBOM-strong README.md model card."""
    # Load sacred results for accurate reporting
    sacred_path = PROJECT_ROOT / "results" / "sacred" / "sacred_ca388cbc.json"
    sacred = json.loads(sacred_path.read_text())

    # Load stacker params
    stacker_path = PROJECT_ROOT / "runs" / "stacker_v2" / "best_params.json"
    stacker = json.loads(stacker_path.read_text())

    # Load conformal config
    conformal_path = PROJECT_ROOT / "runs" / "stacker_v2" / "conformal.json"
    conformal = json.loads(conformal_path.read_text())

    tier_acc = sacred["tier_accuracy"]
    macro_f1 = sacred["macro_f1"]
    ci = sacred["bootstrap_ci_95"]
    conf = sacred["conformal"]
    per_class = sacred["per_class"]

    card = f"""---
license: cc-by-sa-4.0
language: en
tags:
  - security
  - crosswalk
  - ordinal-regression
  - cross-encoder
  - control-mapping
  - nist
  - owasp
  - mitre-atlas
datasets:
  - custom
pipeline_tag: text-classification
model-index:
  - name: crosswalk-ce-v2.1
    results:
      - task:
          type: text-classification
          name: Security Control Mapping
        dataset:
          type: custom
          name: AI Security Framework Crosswalk
        metrics:
          - name: Tier Accuracy (validation)
            type: accuracy
            value: 0.985
          - name: Macro F1 (validation)
            type: f1
            value: 0.9821
          - name: Tier Accuracy (sacred holdout)
            type: accuracy
            value: {tier_acc}
          - name: Macro F1 (sacred holdout)
            type: f1
            value: {round(macro_f1, 4)}
---

# Model Card for crosswalk-ce-v2.1

**Package URI:** `pkg:huggingface/rockCO78/crosswalk-ce-v2.1`

**Supplied by:** Rock Lambros / RockCyber

**Type:** Ensemble of fine-tuned cross-encoder transformer models with LightGBM stacker

## Model Description

crosswalk-ce-v2.1 is an ensemble of three fine-tuned cross-encoder transformers
(DeBERTa-v3-large, RoBERTa-large, ELECTRA-large) combined with a LightGBM
stacker for **ordinal security-control mapping**. Given a pair of security
controls from different frameworks (e.g., NIST CSF, OWASP Top-10, MITRE ATLAS),
the model predicts a similarity tier: *equivalent*, *partial*, *related*, or
*unrelated*.

This is a **research artifact** from the AI Security Framework Crosswalk
project, which builds machine-readable mappings between AI/ML security
frameworks. The model serves as the scoring backbone for automated crosswalk
generation.

**Type of model:** Ordinal text-classification ensemble (cross-encoder + gradient-boosted stacker)

**Primary purpose:** Automated scoring of security control pair similarity across
AI/ML security frameworks to support crosswalk generation and gap analysis.

### Architecture

1. **Cross-encoders (Phase 2-3):** Three transformer models fine-tuned with
   KL-divergence ordinal loss on security control pairs. Each produces CLS
   embeddings (1024-dim) and 4-class softmax probabilities.
2. **Feature pipeline (Phase 4):** Extracts CLS embeddings and softmax
   probabilities from all three encoders, concatenated into a unified feature
   vector.
3. **LightGBM stacker (Phase 6-7):** Gradient-boosted meta-learner trained on
   cross-encoder features with Bayesian hyperparameter optimization.
4. **Conformal calibration (Phase 8):** Mondrian conformal prediction sets
   providing coverage guarantees.

## Intended Use

### Primary Use Cases

- Automated similarity scoring for AI/ML security framework crosswalk generation
- Gap analysis between security control frameworks (NIST CSF, OWASP, MITRE ATLAS, etc.)
- Research into ordinal classification for security domain text

### Out-of-Scope Uses

- General-purpose text similarity or NLI
- Production security decision-making without human review
- Use on non-security text domains

## Training Details

### Training Data

Custom dataset of security control pairs from AI/ML security frameworks
(NIST AI RMF, NIST CSF 2.0, OWASP Top-10 for LLM Applications, MITRE ATLAS,
ISO 42001, MAESTRO, and others). Pairs are labeled with ordinal similarity tiers
by domain experts. The dataset is not publicly released due to licensing
constraints on some source frameworks.

### Training Procedure

- **Phase 2:** Contrastive pre-training of three encoder backbones
- **Phase 3:** Fine-tuning with KL-divergence ordinal loss + Bayesian sweeps (155 runs via W&B)
- **Phase 4:** Feature extraction (CLS embeddings + softmax probabilities)
- **Phase 6-7:** LightGBM stacker training with Bayesian hyperparameter optimization
- **Phase 8:** Conformal calibration on held-out calibration set

### Training Hyperparameters

**Cross-encoder fine-tuning (best sweep configuration):**

| Parameter | Value |
|-----------|-------|
| Loss function | KL-divergence ordinal |
| Sigma (label smoothing) | 0.36 |
| Learning rate | 2.1e-5 |
| Epochs | 8 |
| Batch size | 16 |
| Optimizer | AdamW |
| Weight decay | 0.01 |
| Warmup ratio | 0.1 |

**LightGBM stacker:**

| Parameter | Value |
|-----------|-------|
| num_leaves | {stacker['num_leaves']} |
| learning_rate | {round(stacker['learning_rate'], 4)} |
| min_child_samples | {stacker['min_child_samples']} |
| subsample | {round(stacker['subsample'], 4)} |
| colsample_bytree | {round(stacker['colsample_bytree'], 4)} |
| n_estimators | {stacker['n_estimators']} |
| reg_alpha | {round(stacker['reg_alpha'], 4)} |
| reg_lambda | {round(stacker['reg_lambda'], 4)} |

**Conformal calibration:**

| Parameter | Value |
|-----------|-------|
| Method | {conformal['method']} |
| Alpha | {conformal['alpha']} |
| Calibration samples | {conformal['n_cal']} |
| Target marginal coverage | {conformal['marginal_coverage']} |

### Training Infrastructure

- **GPU:** NVIDIA GH200 480GB (97,871 MiB VRAM)
- **Training time:** ~8.5 hours total (Phases 2-4)
- **Sweep runs:** 155 (W&B project: rockcyber/crosswalk-v2)

## Evaluation

### Validation Results (best sweep run)

| Metric | Value |
|--------|-------|
| Tier Accuracy | 0.985 |
| Macro F1 | 0.9821 |

### Sacred Holdout Results (n={sacred['n_pairs']} pairs)

The sacred holdout is a **fully independent** test set, never seen during
training, validation, or hyperparameter tuning.

| Metric | Value |
|--------|-------|
| Tier Accuracy | {tier_acc} |
| Macro F1 | {round(macro_f1, 4)} |
| 95% Bootstrap CI | [{ci['lower']}, {ci['upper']}] |
| Conformal Marginal Coverage | {conf['marginal_coverage']} |
| Conformal Avg Set Size | {conf['avg_set_size']} |

**Per-class accuracy on sacred holdout:**

| Class | Accuracy | Count |
|-------|----------|-------|
| equivalent | {round(per_class['equivalent']['accuracy'] * 100, 1)}% | {per_class['equivalent']['count']} |
| partial | {round(per_class['partial']['accuracy'] * 100, 1)}% | {per_class['partial']['count']} |
| related | {round(per_class['related']['accuracy'] * 100, 1)}% | {per_class['related']['count']} |
| unrelated | {round(per_class['unrelated']['accuracy'] * 100, 1)}% | {per_class['unrelated']['count']} |

**Honest assessment:** The sacred holdout tier accuracy of {tier_acc} is
significantly below the validation accuracy of 0.985, indicating substantial
overfitting to the training distribution. The model performs best on the
*related* class (65.6%) but struggles with *equivalent* (0.0%) and *unrelated*
(24.4%) distinctions. This gap is a known limitation and an active area of
research.

## Technical Limitations

- **Distribution shift:** Large gap between validation (98.5%) and holdout
  (37.25%) accuracy indicates the model has not generalized to unseen framework
  pairs. The sacred holdout deliberately includes framework combinations absent
  from training.
- **Class imbalance:** The *equivalent* class has 0% accuracy on holdout,
  suggesting the model cannot reliably distinguish exact equivalence from partial
  overlap in unseen domains.
- **Domain specificity:** Trained exclusively on AI/ML security framework text.
  Performance on general security or non-security text is untested and expected
  to be poor.
- **Ordinal structure:** The KL-divergence loss encourages ordinal consistency
  but the stacker does not enforce monotonicity.
- **Framework coverage:** Training data covers a limited set of frameworks.
  Performance on frameworks not seen during training (e.g., CIS Controls,
  PCI DSS) is unknown.

## Energy Consumption

| Component | Value |
|-----------|-------|
| GPU | NVIDIA GH200 480GB |
| TDP | ~900 W (0.9 kW) |
| GPU-hours | ~8.5 hours |
| Estimated energy | **7.65 kWh** |
| Training location | US cloud (Lambda) |

Energy estimate: 8.5 GPU-hours x 0.9 kW TDP = 7.65 kWh for Phases 2-4
(cross-encoder training). CPU phases (stacker training, conformal calibration)
consumed negligible additional energy.

## Safety and Risk Assessment

### Risks

- **False equivalences:** The model may predict that two controls are
  *equivalent* when they are only *partially* related, potentially leading to
  gaps in security coverage if used without human review.
- **Automation bias:** Users may over-rely on model predictions without
  verifying against the source framework text.
- **Stale mappings:** Security frameworks evolve; model predictions may become
  outdated as frameworks are revised.

### Mitigations

- Conformal prediction sets provide uncertainty quantification — users should
  examine the full prediction set, not just the point prediction.
- The sacred holdout evaluation provides an honest assessment of generalization.
- All crosswalk outputs should be reviewed by a domain expert before use in
  security planning or compliance.

## Ethical Considerations

- This model processes publicly available security framework text and does not
  handle personal data.
- Misuse risk is low but users should not treat automated crosswalks as a
  substitute for expert security analysis.
- The CC BY-SA 4.0 license ensures derivative works remain open.

## Downloads

- **HuggingFace repository:** [rockCO78/crosswalk-ce-v2.1](https://huggingface.co/rockCO78/crosswalk-ce-v2.1)
- **GitHub project:** [ai-security-framework-crosswalk](https://github.com/rocklambros/ai-security-framework-crosswalk)

### Repository Structure

```
crosswalk-ce-v2.1/
├── deberta/
│   ├── encoder/          # DeBERTa-v3-large fine-tuned weights + tokenizer
│   └── head.pt           # Classification head
├── roberta/
│   ├── encoder/          # RoBERTa-large fine-tuned weights + tokenizer
│   └── head.pt           # Classification head
├── electra/
│   ├── encoder/          # ELECTRA-large fine-tuned weights + tokenizer
│   └── head.pt           # Classification head
├── stacker/
│   ├── best_params.json  # LightGBM hyperparameters
│   └── conformal.json    # Conformal calibration config
├── evaluation/
│   └── sacred_ca388cbc.json  # Sacred holdout results
├── features/
│   └── ce_features_v2.npz   # Pre-extracted feature vectors (104 MB)
└── README.md             # This model card
```

## License

CC BY-SA 4.0 — Creative Commons Attribution-ShareAlike 4.0 International

Ratified: 2026-04-09

## Citation

```bibtex
@misc{{crosswalk-ce-v2.1,
  title={{crosswalk-ce-v2.1: Cross-Encoder Ensemble for Security Framework Mapping}},
  author={{Rock Lambros}},
  year={{2026}},
  url={{https://huggingface.co/rockCO78/crosswalk-ce-v2.1}},
  license={{CC BY-SA 4.0}}
}}
```
"""
    return card


def main():
    token = get_hf_token()
    api = HfApi(token=token)

    # 1. Create repo (or get existing)
    print(f"Creating/accessing repo: {REPO_ID}")
    create_repo(REPO_ID, token=token, repo_type="model", exist_ok=True)

    # 2. Upload README.md model card
    print("Generating and uploading model card...")
    card_content = build_model_card()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(card_content)
        card_path = f.name
    api.upload_file(
        path_or_fileobj=card_path,
        path_in_repo="README.md",
        repo_id=REPO_ID,
        commit_message="Add AIBOM-strong model card",
    )
    print("  -> README.md uploaded")

    # 3. Upload individual artifacts
    for local_rel, repo_path in ARTIFACTS.items():
        local_path = PROJECT_ROOT / local_rel
        if not local_path.exists():
            print(f"  WARNING: {local_path} not found, skipping")
            continue
        size_mb = local_path.stat().st_size / (1024 * 1024)
        print(f"Uploading {repo_path} ({size_mb:.1f} MB)...")
        api.upload_file(
            path_or_fileobj=str(local_path),
            path_in_repo=repo_path,
            repo_id=REPO_ID,
            commit_message=f"Add {repo_path}",
        )
        print(f"  -> {repo_path} uploaded")

    # 4. Upload encoder directories
    for local_rel, repo_path in ENCODER_DIRS.items():
        local_path = PROJECT_ROOT / local_rel
        if not local_path.exists():
            print(f"  WARNING: {local_path} not found, skipping")
            continue
        size_gb = sum(f.stat().st_size for f in local_path.rglob("*") if f.is_file()) / (1024**3)
        print(f"Uploading {repo_path}/ ({size_gb:.2f} GB)...")
        api.upload_folder(
            folder_path=str(local_path),
            path_in_repo=repo_path,
            repo_id=REPO_ID,
            commit_message=f"Add {repo_path} weights + tokenizer",
        )
        print(f"  -> {repo_path}/ uploaded")

    url = f"https://huggingface.co/{REPO_ID}"
    print(f"\nDone! Repository: {url}")
    return url


if __name__ == "__main__":
    main()
