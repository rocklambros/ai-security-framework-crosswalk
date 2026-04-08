# Design Spec: Best-in-Class Cross-Framework AI Security Mapping Classifier

**Date:** 2026-04-07
**Status:** Awaiting final user review
**Goal:** Produce a portfolio-grade, arXiv-publishable cross-framework mapping classifier + interactive visualization app for AI security and governance frameworks

---

## 0. Context and Motivation

The existing `ai-security-framework-crosswalk` project has built a 983-node, 1883-edge graph spanning 9 AI security frameworks (AIUC-1, CSA AICM, MITRE ATLAS, NIST AI RMF, OWASP LLM Top 10, OWASP Agentic Top 10, OWASP AI Exchange, EU GPAI CoP, CoSAI) and a multi-signal hybrid mapping engine (reference bridge, semantic, keyword, function_match) with calibrated thresholds. Current v2 production achieves tier accuracy of 0.20–0.30 on 3 frozen SME parity pairs and 47.9% preservation of the 119-pair AIUC-1 → OWASP Agentic expert crosswalk. The number is low because (a) tier accuracy is a brutal metric with an inter-rater noise ceiling, (b) evaluation is on uncertainty-sampled SME labels (hard-case biased), and (c) training data is only ~550 human SME labels.

**Linchpin of this project: absolute precision and recall on the cross-framework mapping task, measured on human gold, reported transparently with calibrated abstention.** The LLM-as-SME labeling pipeline is the *enabler* that unblocks scale; it is not itself the contribution.

**Target audience:** AI security researchers, data scientists, machine learning engineers. Deliverable is a portfolio artifact (repo + HF model/dataset/Space + blog post + arXiv preprint) with rigor appropriate for arXiv review.

**Coursework boundary (COMP 4433):** Weights & Biases is used exclusively for `mapping_engine/` training telemetry on Lambda. It must not appear in Project 1 (matplotlib/seaborn notebook) or Project 2 (Plotly/Dash app) deliverables, which remain on the course-approved visualization stack.

---

## 1. Problem Statement and Success Criteria

### 1.1 Task formulation

Given a source control (structured text from any of 9 AI security frameworks) and a target framework, produce a ranked list of target entries annotated with:

- **Tier** ∈ {Direct, Related, None} with calibrated probability
- **Confidence band** from Mondrian conformal wrapper (formal 1−α coverage guarantee)
- **Structured rationale code** from the existing 8-code taxonomy
- **Signal decomposition** (per-signal contribution for explainability)

The system must also accept arbitrary free-text input ("our policy requires…") and produce the same output — this is the Dash app's "Map your policy" feature and the demo that makes the portfolio piece shareable.

### 1.2 Pre-registered success thresholds

Pre-registration is standard scientific practice and protects against p-hacking accusations. Thresholds are declared *before* any training run.

**Primary headline metric: Recall@3 on `human_test_frozen` (400 pairs), stratified by framework pair with bootstrap 95% CIs.**

| Threshold | Paper framing |
|---|---|
| Recall@3 ≥ 0.80 | "State of the art" — full best-in-class framing |
| 0.70 ≤ Recall@3 < 0.80 | "Competitive" — strong baseline + honest limitations paper |
| 0.55 ≤ Recall@3 < 0.70 | "Partial success" — error analysis as the main contribution |
| Recall@3 < 0.55 | "Negative result" — blog post only, no arXiv |

**Co-headline metric: Precision@80%-Coverage from the Mondrian conformal wrapper** — the practical deployment metric that answers "at 80% coverage what precision can an auditor expect?"

**Independent verification on `human_test_fresh` (75 pairs):** same metrics computed on labels produced *after* model freeze. If fresh-75 metrics fall more than 10 pp below frozen-400 metrics, the paper reports the gap and adjusts claims accordingly.

### 1.3 Baseline set (the comparison ladder)

| # | Baseline | Params / type |
|---|---|---|
| 1 | BM25 (rank_bm25) | Sparse lexical |
| 2 | `bge-large-en-v1.5` zero-shot cosine | 335M dense bi-encoder |
| 3 | Current 4-signal composite (v2 production) | Handcrafted |
| 4 | `bge-reranker-v2-m3` zero-shot | 568M frozen cross-encoder |
| 5 | Zero-shot Opus-4-6 judge | Frontier LLM (ceiling) |
| 6 | **Ours — Rung S**: `bge-small-en-v1.5` cross-encoder fine-tuned + multi-task head | 33M |
| 7 | **Ours — Rung M**: `deberta-v3-base` fine-tuned + multi-task head | 184M |
| 8 | **Ours — Rung L**: `bge-reranker-v2-m3` fine-tuned + multi-task head ← main | 568M |
| 9 | **Ours — Rung XL**: `RepLlama-7B` LoRA-tuned (r=16, α=32) + multi-task head | 7B |
| 10 | **Ours — Full ensemble**: Rung L + GAT (independent) + stacked LightGBM + conformal wrapper | 568M + GAT + LightGBM |
| 11 | **Ours — Joint ensemble**: Rung L + GAT joint-trained with shared fusion + stacked + conformal | 568M + GAT + LightGBM |

All 11 evaluated on identical `human_test_frozen`. Bootstrap CIs + McNemar's tests for paired comparisons.

---

## 2. Data Pipeline and Labeling Protocol

### 2.1 Candidate generation

For each of 12 framework pairs — chosen so that every one of the 9 frameworks appears in **at least 2 pairs total** (as source, as target, or both; this guarantees no framework is represented by a single pairing), enumerate (source, target) candidate pairs:
- For each source node, retrieve top-20 target nodes via `bge-large-en-v1.5` zero-shot cosine
- ~36k raw candidates, down-sampled to ~10k balanced by framework pair and by candidate-score bucket (don't over-sample top-of-distribution)
- **Retrieval-floor check (mandatory before labeling begins):** all 400 frozen human-test pairs must appear in the top-20 retrieval for their source node (fresh-75 doesn't exist yet at this phase). If coverage < 100%, expand k until it does, up to k=50 max. If k=50 still misses pairs, the gap is reported as the retrieval ceiling in the paper and budget is adjusted (+$150 LLM spend for the expanded candidate pool).

### 2.2 LLM-SME labeling protocol (Level E: multi-persona ensemble)

**Models: Sonnet 4.6 for bulk, Opus 4.6 for calibration and ceiling.** Subscription (Claude Code Max) is used for developer work only; labeling is programmatic API.

**Three personas, each called once per pair** (no within-persona self-consistency; the multi-persona ensemble provides diversity):

1. **Compliance auditor** — "does this control, as written, provide assurance against this risk?"
2. **Security researcher** — "do these describe the same attack surface or defense mechanism?"
3. **Governance lawyer** — "would a regulator consider these to address the same obligation?"

Each call uses:
- **Reference grounding** — full framework doc passage for both controls, not just the short description
- **Structured JSON output** — `{tier, confidence, rationale_code, rationale_text, grounding_quotes}`
- **Temperature 0.3** — stable but allows persona divergence
- **Versioned Jinja2 prompt templates** at `mapping_engine/config/llm_sme_prompts/v1/{persona}.j2`, SHA256 hashed and committed
- **Idempotent caching** — every response cached by `hash(prompt + model_version)`, re-runs are free, resumable from disk

**Aggregation:**
- 3/3 agreement → gold label, confidence = mean
- 2/3 agreement → majority label, confidence = mean × 0.75
- 0/3 agreement → `ambiguous=true`, used as disagreement auxiliary signal during training

### 2.3 Calibration correction

Run the full three-persona protocol on 150 human calibration labels (random stratified subsample of the existing 550-pair human SME pool). Compute:
- Cohen's κ per persona vs human SME
- Per-persona confusion matrix
- Systematic bias detection
- Per-framework-pair calibration error

Apply:
- Isotonic regression on confidence scores
- Tier-flip correction table for systematic misreads
- Per-framework-pair loss reweighting during student training

Report raw vs corrected metrics in an appendix.

### 2.4 Sonnet ↔ Opus quality gap study

Relabel a random 300-pair subset with Opus 4.6 (all three personas). Measure:
- Cohen's κ between Sonnet and Opus on tier labels
- Per-framework-pair agreement
- Confidence score correlation

The paper's defensibility paragraph: "We labeled 10k training pairs with Sonnet 4.6. To validate the smaller model was adequate, we relabeled a random 300-pair subset with Opus 4.6 and measured inter-model agreement. κ = X.XX, well within the inter-human range reported in the ontology-alignment literature."

### 2.5 Label storage and versioning

`data/labels/llm_sme/{version}/{pair_key}.jsonl` with schema:

```json
{"pair_key": "aiuc-1:C-1.2__owasp-agentic:ASI-03",
 "persona": "compliance_auditor",
 "tier": "Direct", "confidence": 0.92,
 "rationale_code": "FUNCTIONAL_OVERLAP",
 "rationale_text": "...",
 "grounding_quotes": ["..."],
 "model": "claude-sonnet-4-6",
 "prompt_hash": "sha256:...",
 "timestamp": "2026-..."}
```

Versions: `v1_raw` (uncorrected), `v1_calibrated` (post-isotonic + tier-flip), `v1_frozen` (snapshot used for final model). All versions git-committed; nothing modified in place.

### 2.6 Training data splits (hard-pinned)

| Split | Size | Source | Used for |
|---|---:|---|---|
| `llm_train` | ~9,400 | LLM-SME v1_calibrated | Student model training |
| `llm_val` | ~600 | LLM-SME v1_calibrated | HP selection, checkpointing, conformal calibration |
| `human_cal` | 150 | Existing 550 SME pool, stratified random sample (seed 42, stratified by framework pair × tier) | LLM labeler calibration only |
| `human_test_frozen` | 400 | Remaining 400 from existing 550 SME pool after `human_cal` split | Honest test #1 — headline numbers |
| `human_test_fresh` | 75 | User's post-hoc labels | Honest test #2 — independent verification |

**Hard guarantees (enforced by `tests/test_split_leakage.py`):**
- `human_test_frozen` never passed to LLM labeler, never in training, never in HP selection, never in checkpoint picking. Touched exactly once at the end.
- `human_test_fresh` produced after model weights hashed and uploaded to HF.
- Every split has SHA256 hash committed to `data/splits/hashes.json`. CI fails if any split file changes.
- Candidate-generation step excludes any pair whose `pair_key` matches a row in `human_test_frozen` or `human_test_fresh`.

### 2.7 LLM budget summary

| Task | Model | Calls | Est. cost |
|---|---|---:|---:|
| Bulk labeling (10k × 3 personas, batch API) | Sonnet 4.6 | 30,000 | $250–400 |
| Calibration (150 × 3 personas) | Opus 4.6 | 450 | $20–30 |
| Sonnet↔Opus study (300 × 3 personas) | Opus 4.6 | 900 | $40–60 |
| Opus zero-shot ceiling (400 × 3 samples) | Opus 4.6 | 1,200 | $60–100 |
| **Total** | | **~33k** | **$370–590** |

---

## 3. Model Architecture and Training Protocol

### 3.1 Three-stage ensemble

**Stage 1: Multi-task cross-encoder (primary signal)**

Backbone: `BAAI/bge-reranker-v2-m3` (568M). Input: `[CLS] source_framework: source_text [SEP] target_framework: target_text [SEP]`.

Three heads share a 512-dim projection from mean-pooled encoder output:
1. **Tier head** — 3-way softmax over {Direct, Related, None}
2. **Relevance head** — scalar sigmoid for ranking
3. **Rationale head** — 8-way softmax over 8-code rationale taxonomy (auxiliary)

**Loss:**
```
L = α·L_tier + β·L_rank + γ·L_rationale + δ·L_disagreement
```

- `L_tier`: cross-entropy weighted by per-pair LLM confidence
- `L_rank`: margin ranking with in-batch negatives + hard negatives every 4th batch from top-20 dense retrieval
- `L_rationale`: cross-entropy on rationale codes (auxiliary grounding)
- `L_disagreement`: KL divergence between predicted tier distribution and 3-persona disagreement distribution for `ambiguous=true` pairs — **disagreement-aware loss, novel contribution**

Initial weights: α=1.0, β=0.5, γ=0.2, δ=0.1 (tuned via Optuna).

**Staged fine-tuning** to avoid catastrophic forgetting:
- Epochs 1–3: encoder frozen, heads only, lr 1e-3
- Epochs 4–10: top 4 encoder layers unfrozen, lr 2e-5 with linear warmup
- Epochs 11–15: all layers unfrozen, lr 1e-5 cosine schedule
- Early stop on `llm_val` Recall@3, patience 3

Optimizer: AdamW, weight decay 0.01, bf16 on H100, grad clip 1.0, batch 32, max seq 512. Framework-pair-stratified batch sampling — every batch contains ≥4 distinct pairs (prevents per-pair overfitting).

**Stage 2: Graph Attention Network (structural signal)**

Crosswalk graph densified by LLM labels (983 nodes, ~5000+ edges post-labeling). Node features: frozen `bge-large-en-v1.5` mean-pooled text embeddings (1024-dim).

GAT: 2 layers (matches 2-hop bridge), 4 attention heads per layer, hidden dim 256, dropout 0.3.

Edge score head: concatenate `[src_emb, tgt_emb, |src − tgt|, src ⊙ tgt]` → MLP (1024 → 512 → 128) → same three heads as Stage 1. Same multi-task loss. Same LLM-SME training labels.

**Two training configurations, both run:**
- **Independent** (primary): Stage 1 and Stage 2 trained separately. Clean ablations.
- **Joint** (additional): Stage 1 and Stage 2 share a fusion layer, both backprop into a unified final score head. May win on raw accuracy; if so, flips to headline model.

**Stage 3: Stacked meta-learner (LightGBM)**

Features per pair (~32 total):
- Cross-encoder: 3 tier probs + 1 relevance = 4
- GAT: 3 tier probs + 1 relevance = 4
- Existing 4 handcrafted signals: bridge, semantic, keyword, function_match = 4
- Meta features: framework-pair one-hot, entry-type match, domain distance, dense-retrieval rank, per-pair LLM confidence = ~20

Trained on out-of-fold predictions from Stages 1 and 2 (5-fold CV on `llm_train`) to prevent leakage. Early stopping on `llm_val`.

**Wrapper: Mondrian conformal prediction**

Session 9 module wraps Stage 3 output. Calibration set: `llm_val`. Produces prediction sets with formal 1−α coverage at 70/80/90/95%.

Disagreement-as-abstention extension: pairs with `ambiguous=true` in the LLM labels (3-persona disagreement) get routed to higher abstention priority regardless of the model's confidence — a direct bridge from the labeling protocol's disagreement signal to the inference-time abstention layer.

### 3.2 4-rung scaling ladder

All four rungs use the same multi-task head architecture, same training data, same hyperparameter config (best from Rung L Optuna search, lr scaled by √(param ratio)):

| Rung | Backbone | Params | Est. train time (A100) |
|---|---|---:|---:|
| S | `bge-small-en-v1.5` cross-encoder | 33M | ~2 hours |
| M | `microsoft/deberta-v3-base` | 184M | ~4–6 hours |
| **L** | `BAAI/bge-reranker-v2-m3` (main) | 568M | ~10–15 hours |
| XL | `RepLlama-7B` LoRA r=16 α=32 | 7B | ~20–30 hours |

Rung XL uses LoRA because full fine-tuning 7B on 10k labels would memorize the training set.

### 3.3 Hyperparameter search

Optuna, 30 trials on Rung L, objective `llm_val` Recall@3:
- lr: log-uniform [1e-6, 1e-3]
- Loss weights α, β, γ, δ: uniform [0, 2]
- Head dropout: uniform [0.0, 0.5]
- Batch size: {16, 32, 64}
- GAT hidden dim: {128, 256, 512}
- GAT attention heads: {2, 4, 8}

~30 trials × 1.5h = ~45 GPU-hours on A100 ≈ $50. Best config reused for other rungs with lr scaling.

### 3.4 Reproducibility contract

- `requirements.txt` pinned to exact versions
- Seeds pinned: torch/numpy/random seed 42, `torch.use_deterministic_algorithms(True)` on main run
- Every training run logged to Weights & Biases with config hash
- Final model weights SHA256 committed to `data/hashes.json`
- HF model card includes wandb run URL, config hash, reproduction command

### 3.5 Compute budget

| Line item | Est. cost |
|---|---:|
| Rung L main (H100 × ~20h) | $60 |
| Rungs S, M, XL (3× A100 parallel × avg 15h) | $60 |
| HP sweep (30 Optuna trials on 2× A100) | $55 |
| Joint GAT training config (extra run) | $30 |
| W7 ablations (remove each signal, single-task, no-GAT, etc.) | $100 |
| Stacking + conformal calibration | $5 |
| Zero-shot baselines (frozen models) | $15 |
| **Compute total** | **~$325** |

---

## 4. Evaluation, Dash App, Risks, Timeline

### 4.1 Evaluation protocol

**The sacred run.** `human_test_frozen` (400 pairs) is touched exactly once, at the very end, after training completes and the best model is selected on `llm_val`. The results are the paper's headline numbers. No retries.

**Metrics (all reported, primary in bold):**
- **Recall@1, Recall@3, Recall@5** (primary: R@3)
- **MRR**, **nDCG@10**
- **Multi-label F1** (macro + micro)
- **Tier accuracy** with inter-rater ceiling caveat
- **ECE** (Expected Calibration Error)
- **Precision@{70%, 80%, 90%, 95% conformal coverage}** (co-headline: P@80%)
- **Per-framework-pair stratification** (12 cells)
- **Per-tier stratification** (3 levels)

**Statistical tests:**
- Bootstrap 95% CI (10k resamples) on every headline
- McNemar's test vs strongest non-neural and strongest neural baselines
- Permutation test (10k perms) on Recall@3 deltas
- Benjamini-Hochberg multiple-comparison correction on stratified cells

**Independent verification.** `human_test_fresh` (75 pairs) labeled by user post-freeze via Streamlit UI. Same metrics, compared head-to-head with frozen-400. If gap >10pp, paper reports and adjusts claims.

### 4.2 Dash app architecture (C scope + D readiness)

**Stack:**
- Frontend: Dash + Dash Cytoscape + Plotly
- Backend: FastAPI sidecar with trained model loaded (ONNX + int8 for HF Spaces CPU)
- Storage: SQLite (feedback schema stubbed, UI hidden in C-scope)
- Deployment: HuggingFace Space

**Tabs:**
1. **Overview** — framework-level aggregate graph (9 nodes)
2. **Explore** — pair-level bipartite graph with filters
3. **Drill-down** — single-control focused view with signal breakdown + rationale + conformal confidence band
4. **Map your policy** — free-text input → full pipeline → ranked mappings across all frameworks (C-scope killer feature)
5. **Gaps** — unmapped nodes, low-coverage cells, `needs_review` queue
6. **About** — paper abstract, arXiv link, HF model link, GitHub link

**D-readiness affordances built in day-1 (hidden in UI, plumbed in backend):**
- Query logging: every `/score` endpoint call writes `{timestamp, session_id, input_text, top_k_predictions, model_version}` to SQLite
- Feedback schema stubbed: columns exist, widgets not rendered
- FastAPI `/feedback` endpoint: returns 404 in C, 200 in D (one-line toggle)

**COMP 4433 Project 2 compliance:**
- ≥4 DCCs: `dcc.Dropdown`, `dcc.Slider`, `dcc.Input`, `dcc.Textarea`, `dcc.Tabs`, `dcc.Graph` ✓
- ≥1 `@callback` decorator ✓
- ≥3 Plotly chart types: Cytoscape network + bar (signal decomposition) + heatmap (coverage) + histogram (confidence distribution) ✓
- Narrative/instructional text ✓
- Deployment-ready repo ✓

### 4.3 Risks and mitigations

| # | Risk | Detection | Mitigation / Fallback |
|---|---|---|---|
| 1 | LLM labels systematically biased | Sonnet↔Opus study, Cohen's κ on 150-cal | Calibration correction; κ<0.5 → relabel with Opus (+$700) |
| 2 | Student overfits to LLM teacher | Gap frozen-400 vs fresh-75 | Pre-registered acknowledgment; reframe if >10pp |
| 3 | Ensemble provides no lift | Ablation table | Ship single-model; ensemble becomes ablation |
| 4 | Retrieval floor caps Recall@20 below 1.0 | W1 retrieval-floor check before labeling | Expand to top-50; acknowledge ceiling |
| 5 | Lambda preemption / availability | Wandb monitoring, per-epoch checkpoints | Switch to Modal/Runpod |
| 6 | Sub-SOTA numbers | Post-training eval | Reframe per threshold table; <0.55 = blog only |
| 7 | HF Spaces deployment issues | Local Docker + test Space in W1 | Railway/Render as alternative |
| 8 | Timeline overrun | Weekly milestone check | Cut XL → joint GAT → ablations in that order |
| 9 | Sonnet quality gap worse than expected | Sonnet↔Opus study per-pair | Use Opus on specific pairs only (~$100) |
| 10 | Budget overrun | Weekly spend tracking | Hard cap $1000; cut XL + joint GAT if needed |

### 4.4 Timeline — 5 weeks wall-clock

| Week | Workstreams (parallel where possible) |
|---|---|
| **Week 1** | W1 infra (training harness, labeling pipeline, Dash scaffold, retrieval-floor check, contamination CI test); W3 non-neural baselines; HF Spaces deploy test |
| **Week 2** | W2 bulk labeling (Sonnet, batch API, rate-limit bound); W2b calibration + Opus agreement study (parallel); W3 zero-shot Opus ceiling eval |
| **Week 3** | W4 training: Rung L + GAT independent + GAT joint + Rungs S/M/XL parallel on multiple Lambda A100s; W7 ablations start as training runs complete |
| **Week 4** | W5 sacred run on frozen-400; W7 ablations finish; W6 user labels 75 fresh pairs via Streamlit UI; W7b Dash app build |
| **Week 5** | W8 writeup (blog + arXiv draft); W9 HF upload (model + dataset + Space); blog publish; arXiv submit |

### 4.5 Projected total budget

| Category | Est. spend |
|---|---:|
| LLM labeling (Section 2.7) | $370–590 |
| Compute (Section 3.5) | ~$325 |
| Contingency (re-runs, failed experiments) | $100–200 |
| **Total** | **$795–1115** |

Hard cap $1000. If projection exceeds, cut order: (1) drop Rung XL (~$15), (2) drop joint GAT training (~$30), (3) reduce Sonnet↔Opus study to 150 pairs (~$25), (4) drop Rung S from ladder (~$5).

### 4.6 Deliverables

1. **GitHub repository (public)** — all code, pinned environment, reproduction instructions, pre-registered success thresholds committed to repo *before* final training run
2. **HuggingFace model** — trained ensemble with model card, eval table, usage example, wandb run link
3. **HuggingFace dataset** — 400 frozen + 75 fresh human labels + 10k LLM-SME labels with full provenance + 12 candidate pools + Sonnet↔Opus agreement study results
4. **HuggingFace Space** — Dash app with graph explorer + "Map your policy" feature (C-scope, D-ready)
5. **Blog post** — 3–5k word technical writeup on user's site or Medium/Substack
6. **arXiv preprint** — 8-page paper, cs.CL + cs.CR, written so D (workshop submission) is a cheap extension
7. **COMP 4433 Project 2** — the Dash app doubles as course deliverable

---

## 5. Locked Decision Summary

| Decision | Value |
|---|---|
| Honest test split | 150 cal / 400 frozen / 75 fresh (user-labeled post-freeze) |
| Coverage | 12 framework pairs, every framework appears in ≥2 pairs total (source or target) |
| Prediction framing | Multi-task: multi-label BCE + learning-to-rank |
| Architecture | 3-stage ensemble: fine-tuned cross-encoder + GAT + stacked LightGBM + Mondrian conformal wrapper |
| GAT training | Independent (primary) AND joint (additional config); report both |
| Main backbone | `bge-reranker-v2-m3` (568M), Rung L of 4-rung ladder |
| 4-rung ladder | S(33M) / M(184M) / L(568M) / XL(7B LoRA) |
| LLM-SME protocol | Level E: 3-persona ensemble (compliance / security / governance) + reference grounding + calibration correction |
| Labeling model | Sonnet 4.6 for bulk (batch API), Opus 4.6 for calibration + ceiling + agreement study |
| Disagreement-aware loss | KEEP + extended with disagreement-as-abstention routing |
| Honest test protocol | Single "sacred run" on frozen-400, post-freeze fresh-75 verification |
| Primary metric | Recall@3 (headline) + Precision@80% conformal coverage (co-headline) |
| Baseline set | 11 comparison points (BM25, bge cosine, v2 composite, bge-reranker zero-shot, Opus zero-shot, 4 ours rungs, full ensemble, joint ensemble) |
| Compute platform | Lambda Labs (H100 for main + A100 parallel for ablations), budget $325 compute |
| Dash app stack | Dash + Dash Cytoscape + FastAPI sidecar + SQLite + HuggingFace Space |
| Dash app scope | C (map your policy) with D readiness (query logging + feedback schema stubbed) |
| Deliverables | GitHub + HF model + HF dataset + HF Space + blog post + arXiv preprint + COMP 4433 Project 2 |
| Timeline | 5 weeks wall-clock |
| Budget cap | $1000 hard cap, projected $795–1115, cut order: XL → joint GAT → Sonnet↔Opus study size → Rung S |

---

## 6. Pre-Registered Honesty Commitments

These are the non-negotiable commitments the paper makes regardless of results:

1. **The sacred run is performed exactly once.** No retries on frozen-400. If results disappoint, we reframe the paper; we do not re-tune.
2. **Fresh-75 verification is reported.** If fresh-75 metrics differ from frozen-400 by more than 10pp, the paper reports the gap and adjusts claims.
3. **Retrieval floor is reported.** If any human-test pairs are missing from top-20 candidate retrieval, this is reported as the upper bound on Recall@20.
4. **Sonnet↔Opus agreement is reported.** The κ between the two models is in the paper whether it's good news or bad.
5. **Raw vs calibrated LLM label metrics are both reported** in the appendix.
6. **Failed ablations are reported.** If the disagreement-aware loss doesn't help, we say so. If joint GAT loses to independent GAT, we say so. If Rung XL underperforms Rung L, we say so.
7. **Budget and timeline are reported.** Actual costs and wall-clock times in an appendix.
8. **Model is released** with training code, hyperparameters, wandb logs, and reproduction command — even if numbers are not SOTA.

---

## 7. Next Step

After user approval of this spec, invoke `superpowers:writing-plans` skill to produce the detailed implementation plan with bite-sized tasks, verification gates, and TodoWrite-compatible structure.
