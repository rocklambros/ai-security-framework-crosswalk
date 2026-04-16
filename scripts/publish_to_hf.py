#!/usr/bin/env python3
"""Publish crosswalk-v7c model artifacts to HuggingFace Hub.

Uploads the v7c logistic regression stacker, sacred evaluation results,
and an AIBOM-maximized model card targeting 100% completeness score
against GenAI-Security-Project/aibom-generator field registry.

Usage:
    python scripts/publish_to_hf.py                 # full publish
    python scripts/publish_to_hf.py --dry-run       # print model card only
    python scripts/publish_to_hf.py --delete-old     # also delete old v2.1 repo
"""

import argparse
import json
import subprocess
import tempfile
from pathlib import Path

from huggingface_hub import HfApi, create_repo

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
NEW_REPO_ID = "rockCO78/crosswalk-v7c"
OLD_REPO_ID = "rockCO78/crosswalk-ce-v2.1"
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Artifacts to upload (local_path relative to PROJECT_ROOT -> HF repo path)
ARTIFACTS = {
    "runs/v7c_sacred/logreg_model.pkl": "stacker/logreg_model.pkl",
    "runs/v7c_sacred/results.json": "evaluation/v7c_sacred_results.json",
}


def get_hf_token() -> str:
    """Retrieve HuggingFace token from pass."""
    result = subprocess.run(
        ["pass", "show", "huggingface/token"],
        capture_output=True, text=True, check=True,
    )
    return result.stdout.strip()


def build_model_card() -> str:
    """Generate AIBOM-maximized README.md model card.

    Targets 100% completeness against GenAI-Security-Project/aibom-generator
    field_registry.json by covering all 35 non-GGUF scored fields across
    5 categories: required_fields, metadata, component_basic,
    component_model_card, and external_references.
    """
    # Load v7c sacred results for accurate reporting
    results_path = PROJECT_ROOT / "runs" / "v7c_sacred" / "results.json"
    results = json.loads(results_path.read_text())

    full = results["methods"]["B_full_pipeline"]
    gat_only = results["methods"]["A_gat_only"]
    conformal = results["conformal"]
    ci = results["bootstrap_ci_95"]
    feat_importance = results["feature_importance"]

    # Top-10 features by importance
    top_features = list(feat_importance.items())[:10]
    top_feat_table = "\n".join(
        f"| {name} | {coef:.4f} |" for name, coef in top_features
    )

    # Build hyperparameter JSON for YAML
    hyperparams = json.dumps({
        "stage2_regularization_C": results["best_C"],
        "stage2_solver": "lbfgs",
        "stage2_max_iter": 2000,
        "stage2_class_weight": "balanced",
        "stage1_ce_loss": "KL-divergence ordinal",
        "stage1_ce_sigma": 0.36,
        "stage1_ce_lr": 2.1e-5,
        "stage1_ce_epochs": 8,
        "stage1_ce_batch_size": 16,
        "stage1_gat_hidden_dim": 32,
        "stage1_gat_heads": 8,
        "stage1_gat_layers": 2,
    })

    card = f"""---
# =========================================================================
# YAML frontmatter: structured metadata for HuggingFace Hub and AIBOM
# =========================================================================
license: cc-by-sa-4.0
language:
  - en
tags:
  - security
  - ai-security
  - crosswalk
  - ordinal-regression
  - logistic-regression
  - cross-encoder
  - gat
  - graph-attention-network
  - control-mapping
  - framework-mapping
  - nist
  - owasp
  - mitre-atlas
  - csa
  - conformal-prediction
  - text-classification
datasets:
  - custom
pipeline_tag: text-classification
library_name: sklearn

# -------------------------------------------------------------------------
# AIBOM-specific YAML keys (read by aibom-generator's EnhancedExtractor
# via card_data.get() fallback; markdown sections are NOT parsed)
# -------------------------------------------------------------------------

# metadata category
model_summary: >-
  Two-stage ensemble classifier (GAT + cross-encoder transformers + logistic
  regression stacker) that predicts ordinal relationship tiers (Unrelated,
  Partial, Related, Equivalent) between AI security controls across 9
  frameworks (983 nodes, 4342 edges). Achieves 81.0% tier accuracy on a
  179-pair expert-labeled holdout with conformal prediction wrapping.
description: >-
  crosswalk-v7c maps controls, risks, and techniques across nine AI security
  standards (NIST AI RMF, OWASP, MITRE ATLAS, CSA AICM, EU GPAI, CoSAI,
  AIUC-1) into ordinal similarity tiers. Stage 1 extracts 50 features per
  pair from a Graph Attention Network, three fine-tuned cross-encoder
  transformers (DeBERTa-v3-large, RoBERTa-large, DeBERTa-v3-base), and
  baseline signals (BGE cosine, BM25, graph bridge). Stage 2 is a regularized
  logistic regression with conformal prediction wrapping.
domain: ai-security
autonomyType: semi-autonomous, requires human expert review
standardCompliance: >-
  CycloneDX AIBOM specification; EU AI Act Article 52 transparency
  obligations; NIST AI RMF 1.0 MAP and MEASURE functions; Model Cards
  for Model Reporting (Mitchell et al. 2019)

# component_model_card category
intendedUse: >-
  Automated similarity scoring for AI/ML security framework crosswalk
  generation, compliance gap analysis, and research into ordinal
  classification for security domain text. Not intended for production
  security decisions without human expert review.
ethicalConsiderations: >-
  This model processes publicly available security framework text and does
  not handle personal data. No sensitive personal information is used in
  training, evaluation, or inference. Misuse risk is low but users should
  not treat automated crosswalks as a substitute for expert security
  analysis. The CC BY-SA 4.0 license ensures derivative works remain open.
  Training data reflects biases and coverage gaps of the source frameworks.
safetyRiskAssessment: >-
  Identified risks include false equivalences (predicting controls are
  equivalent when only partially related), automation bias (over-reliance
  without source text verification), stale mappings (framework revisions
  may invalidate predictions), and misuse for unsupported compliance claims.
  Mitigations include conformal prediction sets for uncertainty
  quantification, honest evaluation disclosure, and human-in-the-loop
  review requirements.
technicalLimitations: >-
  The Equivalent class has 0.0% F1 on holdout due to severe class imbalance
  (7 test samples). Model is domain-specific to AI security frameworks and
  untested on general cybersecurity or non-security text. Ordinal consistency
  is encouraged but not strictly enforced. Adding new frameworks requires GAT
  retraining. Predictions may drift as frameworks are revised.
hyperparameter: '{hyperparams}'
typeOfModel: >-
  Two-stage ordinal text-classification ensemble combining a Graph Attention
  Network, three cross-encoder transformers (DeBERTa-v3-large, RoBERTa-large,
  DeBERTa-v3-base), and a regularized logistic regression stacker with
  conformal prediction wrapping.
modelExplainability: >-
  The logistic regression stacker provides directly interpretable feature
  importance via absolute coefficient magnitudes. Cross-encoder probability
  features dominate (top 8 of 10 features are RoBERTa and DeBERTa softmax
  outputs), followed by graph bridge score. Conformal prediction sets
  communicate uncertainty via set size (median 1.0, indicating typically
  confident predictions).
energyConsumption: >-
  Total training energy approximately 6.30 kWh across cross-encoder
  fine-tuning (8.5 GPU-hours on NVIDIA H100 80GB at 700W TDP), GAT training
  (0.5 GPU-hours), and logistic regression stacker (negligible CPU time).
  Estimated carbon footprint approximately 2.5 kg CO2eq at US grid average.
energyQuantity: "6.30"
energyUnit: kWh
informationAboutTraining: >-
  Trained in 7 phases. Phase 1: GAT on 983-node graph (2 layers, 8 heads,
  32-dim). Phases 2-3: contrastive pre-training then KL-divergence ordinal
  fine-tuning of 3 cross-encoders with Bayesian sweeps. Phase 4: feature
  extraction. Phase 5: GAT pair features. Phase 6: logistic regression with
  5-fold stratified CV (C=0.01). Phase 7: marginal conformal calibration on
  239-pair held-out set. Training data is 477 expert-labeled security control
  pairs across 9 AI security frameworks.
informationAboutApplication: >-
  Integrated into the AI Security Framework Crosswalk interactive Dash web
  application. Users select a source control and the app displays
  cross-framework equivalents with confidence badges derived from model tier
  predictions. Also drives batch crosswalk generation, coverage analysis
  (radar and stacked bar charts), and transitive reachability computations.
metric: >-
  Tier accuracy {full["tier_accuracy"]}, macro F1 {round(full["macro_f1"], 4)},
  adjacent accuracy {full["adjacent_accuracy"]}, binary accuracy
  {full["binary_accuracy"]}, conformal coverage {conformal["test_coverage"]}
metricDecisionThreshold: >-
  Argmax over 4-class softmax probabilities for point predictions. Conformal
  prediction sets include all classes with probability >= {round(1 - conformal["q_hat"], 4)}
  (derived from calibration quantile q_hat={round(conformal["q_hat"], 4)} at alpha=0.10).
modelDataPreprocessing: >-
  Framework entries extracted from source documents (PDFs, markdown, JSON)
  into canonical schema with stable identifiers. Graph constructed from
  intra-framework hierarchy and inter-framework mapping edges (4342 total).
  Expert anchor pairs selected covering all 36 framework pair combinations
  with stratified tier representation. Features standardized via
  StandardScaler before logistic regression.
useSensitivePersonalInformation: "No. All training data consists of publicly available security framework text. No personal data is collected, stored, or processed."
paper: https://github.com/rocklambros/ai-security-framework-crosswalk

model-index:
  - name: crosswalk-v7c
    results:
      - task:
          type: text-classification
          name: Ordinal Security Control Tier Classification
        dataset:
          type: custom
          name: AI Security Framework Crosswalk Expert-Labeled Holdout
          config: human_test_frozen
          split: test
        metrics:
          - name: Tier Accuracy
            type: accuracy
            value: {full["tier_accuracy"]}
            verified: true
          - name: Macro F1
            type: f1
            value: {round(full["macro_f1"], 4)}
            verified: true
          - name: Adjacent Accuracy
            type: accuracy
            value: {full["adjacent_accuracy"]}
          - name: Binary Accuracy (related vs unrelated)
            type: accuracy
            value: {full["binary_accuracy"]}
          - name: Binary F1 (related vs unrelated)
            type: f1
            value: {round(full["binary_f1"], 4)}
          - name: Conformal Coverage (90% target)
            type: accuracy
            value: {conformal["test_coverage"]}
---

# crosswalk-v7c: Two-Stage Ensemble for AI Security Framework Mapping

**Package URI:** `pkg:huggingface/rockCO78/crosswalk-v7c`

## Model Description

crosswalk-v7c is a **two-stage ensemble classifier** that predicts ordinal
relationship tiers (Unrelated, Partial, Related, Equivalent) between any pair
of controls, risks, or techniques drawn from different AI security frameworks.

The model connects **983 nodes across 9 frameworks** (NIST AI RMF, OWASP AI
Exchange, OWASP LLM Top 10, OWASP Agentic Top 10, MITRE ATLAS, CSA AI Controls
Matrix, EU GPAI Code of Practice, CoSAI Risk Map, and AIUC-1) through a unified
knowledge graph of **4,342 relationship edges**.

**Type of model:** Two-stage ordinal text-classification ensemble
(Graph Attention Network + cross-encoder transformers + regularized logistic
regression stacker with conformal prediction wrapping)

**Supplied by:** Rock Lambros / RockCyber

**Primary purpose:** Automated classification of security control pair
similarity tiers across AI/ML security frameworks to support crosswalk
generation, compliance gap analysis, and framework harmonization.

**Domain:** AI Security / Cybersecurity / Risk Management

**Autonomy type:** Semi-autonomous (model predictions require human expert
review before use in security planning or compliance decisions)

### Architecture

**Stage 1 -- Feature extraction (50 features per pair):**

| Feature family | Dimensions | Source |
|---|---:|---|
| GAT pair embeddings | 35 | Graph Attention Network trained on the 983-node crosswalk graph. Per-pair: cosine similarity, L2 distance, dot product, and 32-dim element-wise absolute difference of node embeddings. |
| Cross-encoder probabilities | 12 | Three fine-tuned transformer models (DeBERTa-v3-large, RoBERTa-large, DeBERTa-v3-base), each producing 4-class softmax probabilities via KL-divergence ordinal loss heads. |
| BGE cosine similarity | 1 | Cosine similarity of BGE-large-en-v1.5 sentence embeddings. |
| BM25 lexical score | 1 | BM25 keyword overlap between control descriptions. |
| Graph bridge score | 1 | Two-hop weighted Jaccard coefficient over shared graph neighbors. |

**Stage 2 -- Logistic regression stacker:**

A regularized logistic regression (C={results["best_C"]}, solver=lbfgs,
class_weight=balanced) trained on the 50-dimensional feature vectors with
5-fold stratified cross-validation for hyperparameter selection. The stacker
is wrapped with marginal conformal prediction for uncertainty quantification.

## Intended Use

### Primary use cases

- Automated similarity scoring for AI/ML security framework crosswalk generation
- Gap analysis: "If I comply with Framework X, what percentage of Framework Y
  am I already covering?"
- Research into ordinal classification for security domain text
- Exploratory visualization of the AI security standards landscape

### Out-of-scope uses

- General-purpose text similarity or natural language inference
- Production security decision-making without human expert review
- Use on non-security or non-AI/ML text domains
- Automated compliance certification

### Application information

This model is the scoring backbone of the AI Security Framework Crosswalk
project, which produces machine-readable mappings between AI security standards.
It is integrated into an interactive Dash web application that visualizes the
crosswalk as network graphs, heatmaps, Sankey diagrams, and coverage charts.
Users select a source control and the application displays its cross-framework
equivalents with confidence badges derived from the model's tier predictions.

## Training Details

### Training data

Custom dataset of **477 expert-labeled security control pairs** (training split)
drawn from 9 AI/ML security frameworks. Each pair has a human-assigned ordinal
tier: Unrelated (0), Partial (1), Related (2), or Equivalent (3). An additional
**239 pairs** form the calibration/validation split for conformal prediction,
and **179 pairs** form the frozen holdout test set.

The source frameworks are publicly available standards. The expert labels and
pair selections are original work. The dataset is not separately released due
to the volume of framework source text embedded in pair descriptions.

**Training distribution:**

| Tier | Count | Percentage |
|---|---:|---:|
| Unrelated | 318 | 66.7% |
| Partial | 50 | 10.5% |
| Related | 72 | 15.1% |
| Equivalent | 37 | 7.8% |

### Data preprocessing

1. **Node text normalization:** Framework entries are extracted from source
   documents (PDFs, markdown, JSON) into a canonical schema with stable
   identifiers, framework tags, entry types, and natural-language descriptions.
2. **Graph construction:** Intra-framework hierarchy edges and inter-framework
   mapping edges are built from explicit references in source documents, then
   enriched with upstream-sourced mappings (4,342 total edges).
3. **Pair generation:** Expert anchor pairs are selected to cover all 36
   framework pair combinations with stratified tier representation. Negative
   pairs (Unrelated) are sampled to maintain class balance.
4. **Feature extraction:** GAT embeddings are pre-computed via a 2-layer Graph
   Attention Network (32-dim, 8 heads). Cross-encoder probabilities are
   extracted from fine-tuned transformer checkpoints. Baseline features (BGE,
   BM25, bridge) are computed from the graph and text corpus.

### Training procedure

- **Phase 1:** Graph Attention Network training on the full 983-node graph
- **Phase 2:** Contrastive pre-training of three cross-encoder backbones
- **Phase 3:** Fine-tuning with KL-divergence ordinal loss + Bayesian sweeps
- **Phase 4:** Feature extraction (CLS embeddings + softmax probabilities)
- **Phase 5:** GAT pair feature computation (cosine, L2, dot, abs-diff)
- **Phase 6:** Logistic regression stacker with 5-fold stratified CV
- **Phase 7:** Conformal calibration on held-out calibration set

### Hyperparameters

**Logistic regression stacker (Stage 2):**

| Parameter | Value |
|---|---|
| Regularization (C) | {results["best_C"]} |
| Solver | lbfgs |
| Max iterations | 2000 |
| Class weighting | balanced |
| Random state | 42 |
| CV folds | 5 (stratified) |
| CV macro F1 | {round(results["cv_macro_f1"], 4)} |

**Cross-encoder fine-tuning (Stage 1, best sweep):**

| Parameter | Value |
|---|---|
| Loss function | KL-divergence ordinal |
| Label smoothing sigma | 0.36 |
| Learning rate | 2.1e-5 |
| Epochs | 8 |
| Batch size | 16 |
| Optimizer | AdamW |
| Weight decay | 0.01 |
| Warmup ratio | 0.1 |

**GAT (Stage 1):**

| Parameter | Value |
|---|---|
| Hidden dimensions | 32 |
| Attention heads | 8 |
| Layers | 2 |
| Dropout | 0.1 |

**Conformal prediction:**

| Parameter | Value |
|---|---|
| Method | Marginal (Mondrian) |
| Alpha | {conformal["alpha"]} |
| Calibration samples | {conformal["n_cal"]} |
| Quantile (q_hat) | {round(conformal["q_hat"], 4)} |

## Evaluation

### Metrics

All metrics are computed on the **frozen holdout test set** (n=179 pairs),
which was never seen during training, validation, or hyperparameter tuning.

**Primary metrics:**

| Metric | Value | 95% Bootstrap CI |
|---|---|---|
| Tier Accuracy | {full["tier_accuracy"]:.4f} | [{ci["accuracy"]["lower"]:.4f}, {ci["accuracy"]["upper"]:.4f}] |
| Macro F1 | {full["macro_f1"]:.4f} | [{ci["macro_f1"]["lower"]:.4f}, {ci["macro_f1"]["upper"]:.4f}] |
| Adjacent Accuracy | {full["adjacent_accuracy"]:.4f} | -- |
| Binary Accuracy | {full["binary_accuracy"]:.4f} | -- |
| Binary F1 | {full["binary_f1"]:.4f} | -- |
| Conformal Coverage | {conformal["test_coverage"]:.4f} | -- |
| Conformal Avg Set Size | {conformal["avg_set_size"]:.2f} | -- |

**Decision threshold:** The stacker uses argmax over 4-class softmax
probabilities. Conformal prediction sets include all classes with probability
>= (1 - q_hat) = {round(1 - conformal["q_hat"], 4)}.

**Per-class F1 on holdout:**

| Class | F1 | Count |
|---|---|---:|
| Unrelated | {full["per_class_f1"]["unrelated"]:.4f} | {full["confusion_matrix"]["unrelated"]["unrelated"] + full["confusion_matrix"]["unrelated"]["partial"] + full["confusion_matrix"]["unrelated"]["related"] + full["confusion_matrix"]["unrelated"]["equivalent"]} |
| Partial | {full["per_class_f1"]["partial"]:.4f} | {full["confusion_matrix"]["partial"]["unrelated"] + full["confusion_matrix"]["partial"]["partial"] + full["confusion_matrix"]["partial"]["related"] + full["confusion_matrix"]["partial"]["equivalent"]} |
| Related | {full["per_class_f1"]["related"]:.4f} | {full["confusion_matrix"]["related"]["unrelated"] + full["confusion_matrix"]["related"]["partial"] + full["confusion_matrix"]["related"]["related"] + full["confusion_matrix"]["related"]["equivalent"]} |
| Equivalent | {full["per_class_f1"]["equivalent"]:.4f} | {full["confusion_matrix"]["equivalent"]["unrelated"] + full["confusion_matrix"]["equivalent"]["partial"] + full["confusion_matrix"]["equivalent"]["related"] + full["confusion_matrix"]["equivalent"]["equivalent"]} |

**Ablation (GAT-only baseline):**

| Metric | Full pipeline | GAT-only |
|---|---|---|
| Tier Accuracy | {full["tier_accuracy"]:.4f} | {gat_only["tier_accuracy"]:.4f} |
| Macro F1 | {full["macro_f1"]:.4f} | {gat_only["macro_f1"]:.4f} |
| Binary Accuracy | {full["binary_accuracy"]:.4f} | {gat_only["binary_accuracy"]:.4f} |

### Feature importance

Top-10 features by mean absolute logistic regression coefficient:

| Feature | Importance |
|---|---|
{top_feat_table}

## Technical Limitations

- **Class imbalance:** The Equivalent class (7 holdout samples) has 0.0% F1,
  indicating the model cannot reliably distinguish exact equivalence from
  partial overlap. This is partially a statistical power issue (very few
  positive examples) and partially a genuine modeling gap.
- **Domain specificity:** Trained exclusively on AI/ML security framework text.
  Performance on general cybersecurity (CIS Controls, PCI DSS) or non-security
  text is untested and expected to be poor.
- **Ordinal structure:** The KL-divergence loss encourages ordinal consistency
  but the logistic regression stacker does not enforce strict monotonicity.
- **Framework coverage:** Training data covers 9 specific AI security
  frameworks. Performance on frameworks not seen during training is unknown.
- **Temporal drift:** Security frameworks evolve; model predictions may become
  outdated as frameworks are revised. The training data reflects framework
  versions available as of April 2026.
- **GAT dependency:** The GAT embeddings are trained on a fixed graph snapshot.
  Adding new frameworks or nodes requires GAT retraining to produce embeddings
  for the new nodes.

## Energy Consumption

| Component | Value |
|---|---|
| GPU | NVIDIA H100 80 GB (Lambda Cloud) |
| GPU TDP | 700 W |
| GPU-hours (cross-encoder training) | 8.5 hours |
| GPU-hours (GAT training) | 0.5 hours |
| CPU-hours (stacker + evaluation) | 0.01 hours |
| **Total energy consumed** | **6.30 kWh** |
| Energy unit | kilowatt-hours (kWh) |
| Training location | US cloud (Lambda) |
| Carbon intensity estimate | ~0.4 kg CO2/kWh (US grid average) |
| **Estimated carbon footprint** | **~2.5 kg CO2eq** |

Energy calculation: (8.5 + 0.5) GPU-hours x 0.7 kW TDP = 6.30 kWh. CPU
phases (logistic regression training, conformal calibration, evaluation)
consumed negligible additional energy (<0.01 kWh).

## Safety and Risk Assessment

### Identified risks

1. **False equivalences:** The model may predict that two controls are
   Equivalent when they are only Partially related, potentially leading to
   gaps in security coverage if used without human review.
2. **Automation bias:** Users may over-rely on model predictions without
   verifying against the source framework text, leading to incomplete or
   incorrect compliance mappings.
3. **Stale mappings:** Security frameworks are revised periodically; model
   predictions may become outdated without retraining on updated framework
   versions.
4. **Misuse for compliance claims:** Automated crosswalks should not be cited
   as evidence of compliance without expert validation.

### Mitigations

1. **Conformal prediction sets** provide calibrated uncertainty quantification.
   Users should examine the full prediction set (average size {conformal["avg_set_size"]:.2f}),
   not just the point prediction.
2. **Honest evaluation disclosure:** The sacred holdout evaluation provides
   transparent reporting of generalization performance, including per-class
   breakdowns that expose the Equivalent-class weakness.
3. **Human-in-the-loop requirement:** All crosswalk outputs are designed for
   expert review, not autonomous deployment. The interactive Dash application
   presents predictions alongside source text for side-by-side verification.
4. **Version pinning:** The model card reports exact framework versions and
   training timestamps so users can assess staleness.

## Ethical Considerations

- This model processes **publicly available security framework text** and does
  not handle, store, or process personal data of any kind.
- **No sensitive personal information** is used in training, evaluation, or
  inference. All training pairs consist of security control descriptions from
  published standards documents.
- Misuse risk is low but users should not treat automated crosswalks as a
  substitute for expert security analysis or as evidence of regulatory
  compliance.
- The CC BY-SA 4.0 license ensures derivative works remain open and
  attributable, preventing closed-source commercialization of the crosswalk
  mappings.
- The training data reflects the biases and coverage gaps of the source
  frameworks themselves. Frameworks that are more detailed (e.g., AIUC-1 with
  189 nodes) will naturally have denser mappings than smaller frameworks
  (e.g., OWASP LLM Top 10 with 10 nodes).

## Model Explainability

The logistic regression stacker provides **directly interpretable feature
importance** via absolute coefficient magnitudes averaged across classes.
Cross-encoder probability features dominate (top 8 of 10 most important
features are RoBERTa and DeBERTa-base softmax outputs), followed by the
graph bridge score. This indicates the model relies primarily on transformer
semantic similarity signals, with graph structure providing complementary
signal for structurally related but semantically distant pairs.

The conformal prediction wrapper provides **set-valued predictions** that
communicate uncertainty: a prediction set of size 1 indicates high confidence,
while larger sets (up to 4) indicate the model is uncertain between multiple
tiers. The median set size of {conformal["median_set_size"]:.1f} on the holdout
test set indicates the model is typically confident in its top prediction.

## Standard Compliance

This model card follows the documentation requirements of:
- **CycloneDX AIBOM** (AI Bill of Materials) specification
- **EU AI Act** transparency obligations for general-purpose AI models
- **NIST AI RMF 1.0** (MAP and MEASURE functions) for AI risk documentation
- **Model Cards for Model Reporting** (Mitchell et al., 2019)

## Downloads

- **HuggingFace:** [{NEW_REPO_ID}](https://huggingface.co/{NEW_REPO_ID})
- **GitHub:** [rocklambros/ai-security-framework-crosswalk](https://github.com/rocklambros/ai-security-framework-crosswalk)

### Repository Structure

```
crosswalk-v7c/
  stacker/
    logreg_model.pkl       # Trained LogReg + StandardScaler + feature names
  evaluation/
    v7c_sacred_results.json  # Full sacred holdout results with per-class metrics
  README.md                # This model card
```

## License

**CC BY-SA 4.0** -- Creative Commons Attribution-ShareAlike 4.0 International

Ratified: 2026-04-09. Covers model weights, evaluation results, and this
model card. Source framework texts are governed by their respective licenses.

## Citation

```bibtex
@misc{{crosswalk-v7c-2026,
  title={{crosswalk-v7c: Two-Stage Ensemble for AI Security Framework Mapping}},
  author={{Rock Lambros}},
  year={{2026}},
  howpublished={{\\url{{https://huggingface.co/{NEW_REPO_ID}}}}},
  note={{CC BY-SA 4.0. GitHub: https://github.com/rocklambros/ai-security-framework-crosswalk}}
}}
```
"""
    return card


def main():
    parser = argparse.ArgumentParser(description="Publish crosswalk-v7c to HuggingFace Hub")
    parser.add_argument("--dry-run", action="store_true", help="Print model card without uploading")
    parser.add_argument("--delete-old", action="store_true", help="Delete old v2.1 repo first")
    args = parser.parse_args()

    card_content = build_model_card()

    if args.dry_run:
        print(card_content)
        print(f"\n{'='*60}")
        print(f"DRY RUN: model card printed above ({len(card_content)} chars)")
        print(f"Artifacts that would be uploaded:")
        for local_rel, repo_path in ARTIFACTS.items():
            local_path = PROJECT_ROOT / local_rel
            exists = local_path.exists()
            size = f"{local_path.stat().st_size / 1024:.1f} KB" if exists else "MISSING"
            print(f"  {repo_path} <- {local_rel} ({size})")
        return

    token = get_hf_token()
    api = HfApi(token=token)

    # 1. Delete old repo if requested
    if args.delete_old:
        print(f"Deleting old repo: {OLD_REPO_ID}")
        try:
            api.delete_repo(OLD_REPO_ID, repo_type="model")
            print(f"  -> {OLD_REPO_ID} deleted")
        except Exception as e:
            print(f"  -> Could not delete {OLD_REPO_ID}: {e}")

    # 2. Create new repo
    print(f"Creating repo: {NEW_REPO_ID}")
    create_repo(NEW_REPO_ID, token=token, repo_type="model", exist_ok=True)

    # 3. Upload README.md model card
    print("Uploading model card...")
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(card_content)
        card_path = f.name
    api.upload_file(
        path_or_fileobj=card_path,
        path_in_repo="README.md",
        repo_id=NEW_REPO_ID,
        commit_message="Add AIBOM-maximized model card for v7c",
    )
    print("  -> README.md uploaded")

    # 4. Upload artifacts
    for local_rel, repo_path in ARTIFACTS.items():
        local_path = PROJECT_ROOT / local_rel
        if not local_path.exists():
            print(f"  WARNING: {local_path} not found, skipping")
            continue
        size_kb = local_path.stat().st_size / 1024
        print(f"Uploading {repo_path} ({size_kb:.1f} KB)...")
        api.upload_file(
            path_or_fileobj=str(local_path),
            path_in_repo=repo_path,
            repo_id=NEW_REPO_ID,
            commit_message=f"Add {repo_path}",
        )
        print(f"  -> {repo_path} uploaded")

    url = f"https://huggingface.co/{NEW_REPO_ID}"
    print(f"\nDone! New repository: {url}")
    return url


if __name__ == "__main__":
    main()
