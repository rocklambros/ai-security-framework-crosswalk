# Frozen Test Set Results

Each phase of the B-2 / B-1 / A rebuild reserves one framework pair as a single-shot frozen test set. These pairs are touched exactly once per phase, with NO retuning afterwards regardless of outcome. Results are appended below in chronological order.

## Phase B-2 — `aiuc_1 -> csa_aicm`

- **Date:** 2026-04-06
- **Anchors:** 257 (auto-expanded from expert/authoritative cross-framework edges via `expand_anchors.py`; all `expected_tier=Direct` because rationale codes are unpopulated for this pair, defaulting to Direct via `rationale_to_tier.yaml`)
- **Pipeline:** B-2 calibrated `PairMapper` (hand-tuned weights, calibrated thresholds direct=0.45 / related_primary=0.20 from B2.9 NDCG@10 sweep)
- **NDCG@10:** 1.0000 [1.0000, 1.0000] (1000-resample bootstrap)
- **Tier accuracy:** 0.0000 [0.0000, 0.0000]

**Interpretation.** NDCG@10 saturates at 1.0 because the expected-tier vector is uniformly Direct (graded relevance = 2.0 for every anchor), so any ordering of predictions over true-positive pairs yields the ideal DCG. The metric is degenerate on this pair under the current rationale-code-derived expected_tier scheme.

Tier accuracy is 0.0 because PairMapper's composite scores against the 257 expert-mapped CSA AICM controls predominantly fall below the calibrated direct/related thresholds, so the assigned tier is `None` for nearly every anchor while expected is `Direct`. This is a mass tier-classification miss, NOT a ranking failure.

**Decision (NO retuning).** B-2 calibration is left as-is. The frozen test reveals two known limitations of the B-2 phase that B-1 and A are designed to address:

1. The current composite-score floor is too high for cross-framework anchors that are semantically distant but expert-asserted (CSA AICM is a generic controls catalogue with abstract phrasings, where the bridge/keyword/semantic signal is weaker than for OWASP Agentic).
2. Uniform-Direct expected tiers from rationale='?' make tier-accuracy metrics uninformative; only ranking metrics carry signal, and ranking is degenerate when all gold labels are equal.

These limitations are explicitly noted in `docs/anti_overfit_methodology.md` and the B-1 / A phases will revisit them via structural features and a fine-tuned reranker.

Recorded once. NOT to be retuned for B-2.

---

## Phase B-1 — `aiuc_1 -> mitre_atlas`

- **Date:** 2026-04-07
- **Anchors:** 32 (auto-expanded from expert/authoritative cross-framework edges via `expand_anchors.py` with `--target-entry-types technique mitigation`; all `expected_tier=Direct` per rationale_to_tier defaults)
- **Pipeline:** B-1 = B-2 baseline (no B-1 structural features survived their anti-overfit gates; see `docs/diagnostics/b1_ablation.md`). Hand-tuned weights, calibrated thresholds direct=0.45 / related_primary=0.20.
- **NDCG@10:** 1.0000 [1.0000, 1.0000] (1000-resample bootstrap)
- **Tier accuracy:** 0.0000 [0.0000, 0.0000]

**Interpretation.** Same dual degeneracy as B-2: uniform-Direct expected tiers force NDCG@10 to saturate at 1.0 regardless of ordering, while composite scores against MITRE ATLAS techniques/mitigations fall below the calibrated direct/related thresholds, producing a mass tier-classification miss. Because B-1 inherits the B-2 model unchanged, this result is fully consistent with the B-2 frozen-test outcome on csa_aicm.

**Decision (NO retuning).** B-1 calibration is left as-is. The unblockers documented in `docs/diagnostics/b1_ablation.md` (populate rationale codes, switch to anchors-vs-distractors metric, build cross-framework category links) remain the only routes to making this gate informative, and they are explicitly out of scope for the current rebuild.

Recorded once. NOT to be retuned for B-1.

---
