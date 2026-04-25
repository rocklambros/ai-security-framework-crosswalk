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
# AIBOM fields
description: "3-model ensemble (RoBERTa-large, DeBERTa-v3-base, BGE-large-v1.5) for ordinal tier classification (Unrelated/Partial/Related/Equivalent) of AI security control pairs across frameworks including NIST AI RMF, OWASP AI, MITRE ATLAS, ISO/IEC 42001, and EU AI Act. Built by Rock Lambros at University of Denver."
primaryPurpose: "MACHINE-LEARNING"
typeOfModel: "ensemble-transformer-classifier"
domain: "ai-security"
autonomyType: "assistive"
intendedUse: "Scoring cross-framework AI security control mappings; assigning ordinal relationship tiers (Unrelated/Partial/Related/Equivalent) to control pairs for framework alignment analysis."
informationAboutApplication: "Primary use is scoring cross-framework control mappings for AI security frameworks. Out of scope: general NLI, non-security domains, or applications without human review."
informationAboutTraining: "5,920 expert-labeled pairs from 9 AI security frameworks. Mapping-level deduplication removed 56% contamination. Ordinal losses (KL, CORN, focal). 3x H100 80GB GPUs, BF16 mixed precision, ~4 hours."
modelDataPreprocessing: "Mapping-level deduplication to remove cross-split leakage; ordinal soft-label generation; class-balanced sampling for rare EQUIVALENT tier."
hyperparameter: "AdamW optimizer; linear warmup + cosine decay; per-model learning rates tuned via Optuna; BF16 mixed precision; max_length=512 tokens"
ethicalConsiderations: "No personal data used. Security-domain only. Outputs are advisory scores requiring human review before compliance or procurement use. Single expert labeler; no formal inter-annotator agreement measured."
technicalLimitations: "Small test set (179 pairs, 7 EQUIVALENT examples); English-only; trained on 9 specific frameworks; PARTIAL/RELATED boundary ambiguity yields lowest F1 scores."
safetyRiskAssessment: "Outputs are advisory scores, not authoritative compliance determinations. Human expert review required before use in compliance decisions, procurement, or framework adoption. No personal data processed."
energyConsumption: "~8.4 kWh estimated for training (~3.4 kg CO2e at US average grid intensity)"
energyQuantity: "8.4"
energyUnit: "kWh"
metric: "exact_accuracy=0.799; adjacent_accuracy=0.922; macro_f1=0.558; per-class F1: UNRELATED=0.928, PARTIAL=0.526, RELATED=0.378, EQUIVALENT=0.400"
metricDecisionThreshold: "Conformal prediction sets calibrated at 90% coverage target; all classes achieve >90% empirical coverage"
modelExplainability: "Softmax probability distributions over 4 tiers provide interpretable confidence scores; conformal prediction sets provide coverage-guaranteed prediction intervals"
useSensitivePersonalInformation: "No"
standardCompliance: "CycloneDX 1.6; AIBOM (OWASP GenAI Security Project)"
paper: "https://huggingface.co/rockCO78/ai-security-crosswalk-vfinal"
external_references:
  - type: website
    url: "https://huggingface.co/rockCO78/ai-security-crosswalk-vfinal"
  - type: distribution
    url: "https://huggingface.co/rockCO78/ai-security-crosswalk-vfinal/tree/main"
model-index:
  - name: ai-security-crosswalk-vfinal
    results:
      - task:
          type: text-classification
          name: Ordinal Tier Classification
        dataset:
          type: custom/ai-security-framework-crosswalk
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

# AI Security Framework Crosswalk — Ensemble Classifier (vfinal)

## Model Description

This model is a 3-model ensemble for **ordinal tier classification** of AI security control pairs across multiple frameworks. Given a pair of security controls (one from each framework), it assigns one of four ordinal relationship tiers:

| Tier | Meaning |
|------|---------|
| **UNRELATED** | No meaningful overlap |
| **PARTIAL** | Some topical overlap but different scope or depth |
| **RELATED** | Substantial overlap; controls address similar threats |
| **EQUIVALENT** | Near-identical coverage; either control satisfies the other |

Built by **Rock Lambros** at the **University of Denver** as part of dissertation research on AI security framework alignment.

## Intended Use

**Primary use:** Scoring cross-framework control mappings for AI security frameworks (NIST AI RMF, OWASP AI, MITRE ATLAS, ISO/IEC 42001, EU AI Act, ENISA, NIST SP 800-218A, NIST CSF 2.0, and others).

**Out of scope:** General natural language inference (NLI), non-security domains, or any application where automated output replaces human judgment without review.

## Model Architecture

The ensemble combines three transformer-based encoders, each with a 4-class linear classification head:

| Component | Base Model | Parameters | Embedding Dim |
|-----------|-----------|------------|---------------|
| RoBERTa-large | `roberta-large` | 355M | 1024-dim CLS |
| DeBERTa-v3-base | `microsoft/deberta-v3-base` | 86M | 768-dim CLS |
| BGE-large-v1.5 | `BAAI/bge-large-en-v1.5` | 335M | 1024-dim CLS |

**Combination strategy:** Softmax averaging of the three models' output probability distributions. No learnable parameters in the combination layer — purely post-hoc ensemble.

Each head is a single linear layer (`Linear(hidden_size, 4)`) trained independently per model.

## Training Details

**Dataset:** 5,920 expert-labeled control pairs drawn from 9 AI security frameworks. Labels were assigned by Rock Lambros using a structured annotation rubric.

**Data cleaning:** Mapping-level deduplication removed 56% contamination (cross-split leakage) from the raw dataset before train/val/test splits were finalized.

**Loss functions:** Ordinal-aware losses used during training:
- KL divergence against soft ordinal label distributions
- CORN (conditional ordinal ranking net) loss
- Focal loss with class-balanced weighting

**Compute:** 3x NVIDIA H100 80GB SXM GPUs, BF16 mixed precision, ~4 hours total wall-clock time.

**Hyperparameters:** AdamW optimizer, linear warmup + cosine decay, per-model learning rates tuned via Optuna (tracked in Sacred).

## Evaluation Results

### Overall Metrics (179-pair test set)

| Metric | Value |
|--------|-------|
| Exact Accuracy | **79.9%** |
| Adjacent Accuracy (±1 tier) | **92.2%** |
| Macro F1 | **0.558** |

### Per-Class F1 Scores

| Class | F1 | Support |
|-------|----|---------|
| UNRELATED | 0.928 | ~87 |
| PARTIAL | 0.526 | ~55 |
| RELATED | 0.378 | ~30 |
| EQUIVALENT | 0.400 | 7 |

### Conformal Prediction Coverage

Conformal prediction sets (calibrated at 90% target coverage) achieve >90% empirical coverage for all four classes on the held-out test set.

## Limitations and Biases

- **Small test set:** 179 pairs total, with only 7 EQUIVALENT examples. Per-class metrics for EQUIVALENT are high-variance.
- **English-only:** All frameworks and controls are in English; no multilingual support.
- **Framework coverage:** Trained on 9 specific AI security frameworks. Performance on out-of-distribution frameworks (e.g., sector-specific CISA guidance) is unknown.
- **Expert labeler bias:** A single expert (Rock Lambros) labeled all training data; inter-annotator agreement was not formally measured.
- **Ordinal collapsing:** The PARTIAL/RELATED boundary is the hardest to learn (lowest F1s), reflecting genuine annotation ambiguity in the middle tiers.

## Ethical Considerations

- No personal data of any kind was used in training or evaluation.
- All training data consists of publicly available security framework control text.
- This is a security-domain tool; outputs should be treated as advisory scores requiring human review before use in compliance or procurement decisions.
- The model does not generate free text and cannot be used for content generation or harmful repurposing.

## Environmental Impact

| Resource | Value |
|----------|-------|
| GPUs | 3x NVIDIA H100 80GB SXM |
| Estimated TDP per GPU | ~700W |
| Training wall time | ~4 hours |
| Estimated energy | ~8.4 kWh |
| Estimated CO2e | ~3.4 kg (US average grid) |

Estimate assumes 400g CO2/kWh US average grid intensity. Actual emissions may differ based on datacenter location and energy mix.

## How to Use

```python
import torch
from transformers import AutoTokenizer, AutoModel

# Load one encoder (RoBERTa shown; repeat for deberta_base and bge)
encoder = AutoModel.from_pretrained("rockCO78/ai-security-crosswalk-vfinal/roberta/encoder")
tokenizer = AutoTokenizer.from_pretrained("rockCO78/ai-security-crosswalk-vfinal/roberta/encoder")

# Load the classification head
head_state = torch.load("roberta/head.pt", map_location="cpu")
head = torch.nn.Linear(1024, 4)
head.load_state_dict(head_state)
head.eval()
encoder.eval()

LABELS = ["UNRELATED", "PARTIAL", "RELATED", "EQUIVALENT"]

def predict_pair(control_a: str, control_b: str) -> dict:
    """Predict ordinal relationship tier for a control pair."""
    text = f"{control_a} [SEP] {control_b}"
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
    with torch.no_grad():
        hidden = encoder(**inputs).last_hidden_state[:, 0, :]  # CLS token
        logits = head(hidden)
        probs = torch.softmax(logits, dim=-1).squeeze()
    return {label: round(prob.item(), 4) for label, prob in zip(LABELS, probs)}

# Example usage
result = predict_pair(
    "Implement data minimization for AI training datasets",
    "Limit collection of personal data to what is necessary for the stated purpose"
)
print(result)
# For full ensemble, average softmax outputs from all three models
```

## How to Train on New Frameworks

To fine-tune or extend this model on additional AI security frameworks:

1. **Collect control pairs.** Enumerate all cross-framework control combinations (or sample strategically using embedding similarity pre-filtering).
2. **Label using the rubric.** Assign UNRELATED / PARTIAL / RELATED / EQUIVALENT using the annotation guide in `scripts/` (see `predict_edges.py` for label definitions).
3. **Deduplicate at mapping level.** Remove any pairs where the same mapping appears in both train and test splits to prevent leakage.
4. **Fine-tune each encoder independently.** Use ordinal losses (KL soft-label, CORN, or focal) rather than standard cross-entropy to preserve tier ordering.
5. **Evaluate with adjacent accuracy.** Exact accuracy understates model quality for ordinal tasks; report adjacent accuracy (±1 tier) alongside macro F1.

## Citation

```bibtex
@misc{lambros2026crosswalk,
  author       = {Lambros, Rock},
  title        = {AI Security Framework Crosswalk: Ordinal Classification of Control Relationships},
  year         = {2026},
  institution  = {University of Denver},
  howpublished = {\url{https://huggingface.co/rockCO78/ai-security-crosswalk-vfinal}},
  note         = {Dissertation research; 3-model ensemble for ordinal tier classification across AI security frameworks}
}
```

## Safety and Risk Assessment

**Outputs are advisory scores, not authoritative compliance determinations.**

- The model assigns probabilistic tiers; human expert review is required before using predictions to inform compliance decisions, procurement, or framework adoption.
- Tier predictions should be validated against primary framework documentation before any downstream use.
- The model has no knowledge of organizational context, implementation details, or regulatory jurisdiction — factors that are essential for real compliance assessment.
- Users operating in regulated environments (finance, healthcare, critical infrastructure) must apply additional human review commensurate with their risk tolerance.
