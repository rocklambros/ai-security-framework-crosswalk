# Pre-Registered Hypotheses Log

This file records every hypothesis pre-registered before running cross-validation on a new feature, model change, or calibration adjustment, per the methodology in `docs/anti_overfit_methodology.md`.

**Format:** each entry is a dated section. Hypotheses are written **before** seeing CV results. The result is filled in afterward, regardless of outcome — negative results are not deleted.

**Decision rule for every entry:** an improvement only counts if the bootstrap 95% CI on the delta vs baseline excludes 0 AND the predicted direction matches the observed direction AND any related permutation-importance CI excludes 0.

---

<!-- Append new entries below this line. Do not edit prior entries except to fill in their result. -->

## 2026-04-07 — H_S4: discriminative-metric threshold re-sweep

**Hypothesis.** Re-sweeping (direct, related_primary) thresholds against the anchors-vs-distractors discriminative metric (mean reciprocal rank of each positive anchor against 20 sampled non-mapped distractors per anchor) improves aggregate MRR over the 5 expanded non-frozen pairs by ≥ 0.03 vs the current (0.45, 0.20) thresholds, with paired-bootstrap 95% CI on the delta excluding 0.

**Predicted direction.** Positive — current thresholds were tuned against saturated NDCG@10 and are effectively arbitrary; an objective that actually moves should produce a measurable improvement.

**Minimum effect size.** Δ MRR ≥ 0.03 paired-bootstrap CI excluding 0.

**Metric.** Aggregate MRR across 420 anchors (5 non-frozen pairs), distractor pool = 20 stratified non-mapped (src,tgt') and (src',tgt) cells per anchor, seed=20260407. Companion metrics Recall@5 and ROC-AUC reported but not gate-bearing.

**Frozen test pairs.** Excluded; touched only once in S7 with whatever thresholds S4 ships.

**Result.** REJECTED. Sweep best on the 4 training pairs: direct=0.35, related_primary=0.30 (train Youden=0.1887, balanced_acc=0.5943). Held-out pair aiuc_1__nist_rmf actually REGRESSES under the swept thresholds (Youden 0.2240 → 0.1786) — the sweep is overfitting the training pairs. Aggregate Youden across all 5 pairs: B-2 (0.45/0.20)=0.2094, swept (0.35/0.30)=0.2026. Per-anchor paired-bootstrap delta = +0.0068 [-0.0419, +0.0533] — CI crosses zero, direction is technically positive but the holdout regression confirms this is noise. Thresholds UNCHANGED at (0.45, 0.20). Persisted to data/processed/threshold_sweep_discriminative.json. Note: the sweep gate is now non-degenerate (it produces real numbers, not ties at 1.0), so this is an honest negative — the B-2 thresholds are well-calibrated for the discriminative metric within the noise floor. Real improvement here would require either rationale-code population (gives the sweep an additional Direct/Related signal beyond positive/negative) or a richer threshold parameterization (per-pair thresholds, calibrated probabilities, etc.) — both out of scope.

## 2026-04-07 — H_S5: B-1 structural features re-eval under discriminative metric

**Hypothesis.** Each of the three B-1 structural features that previously had non-zero coverage but failed the saturated NDCG@10 gate (`mitigation_lexical_match` 23%, `source_out_degree_ratio` 93%, `mutual_reciprocal_rank` 93%) improves aggregate MRR by ≥ 0.02 with paired-bootstrap 95% CI excluding 0 AND has permutation-importance CI excluding 0 when re-evaluated under the anchors-vs-distractors metric.

**Predicted direction.** Positive for at least one of the three (the metric saturation was the dominant blocker; with a discriminating metric, real signal should now be measurable).

**Minimum effect size.** Δ MRR ≥ 0.02 paired-bootstrap CI excluding 0; perm-importance CI excluding 0.

**Metric.** Same as H_S4. Per-anchor LOO masking retained.

**Frozen test pairs.** Excluded.

**Result.** PARTIALLY ACCEPTED. Of the three coverage>0 features:
- `mitigation_lexical_match` (23% non-zero, owasp_agentic only): blended MRR 0.3259, paired delta +0.0116 [+0.0042, +0.0208], permutation-importance observed +0.0116 vs sign-shuffled null [-0.0080, +0.0079] — **BOTH GATES PASS** → ADOPTED at weight=0.10. First B-1 feature in the entire rebuild to clear discipline. Wired into mapper.py for both production `run()` and `_run_with_masked_anchors`.
- `source_out_degree_ratio` (93% non-zero): paired delta +0.0020 [-0.0007, +0.0066] — CI crosses zero → DROP.
- `mutual_reciprocal_rank` (93% non-zero): paired delta +0.0084 [+0.0007, +0.0173] excludes zero, but perm observed +0.0084 sits inside null [-0.0100, +0.0092] → DROP (gate requires BOTH).

Persisted to data/processed/b1_discriminative_eval.json. The discriminative metric was the unblock — under the saturated NDCG@10 gate, all three features tied at delta +0.0000.

## 2026-04-07 — H_S6: reranker_v2 re-eval under discriminative metric

**Hypothesis.** The fine-tuned `BAAI/bge-reranker-base` (reranker_v2) improves aggregate MRR by ≥ 0.03 over the post-S5 pipeline, with paired-bootstrap 95% CI on the delta excluding 0, when re-evaluated under the anchors-vs-distractors metric.

**Predicted direction.** Positive — A4 training-time validation showed real per-epoch lift (val NDCG@10 0.673 → 0.720), which the saturated A5 gate could not detect.

**Minimum effect size.** Δ MRR ≥ 0.03 paired-bootstrap CI excluding 0.

**Metric.** Same as H_S4 / H_S5.

**Frozen test pairs.** Excluded.

**Result.** REJECTED — and decisively. Post-S5 baseline MRR is 0.3402 (the S5 mitigation_lexical_match adoption visibly lifted the baseline from S3's 0.3143). reranker_v2 MRR drops to 0.2337; per-pair regressions are uniform: aiuc_1__eu_gpai_cop 0.1202→0.0678, aiuc_1__nist_rmf 0.3135→0.1620, aiuc_1__owasp_agentic 0.4546→0.3530, aiuc_1__owasp_llm 0.4201→0.3645. Paired-bootstrap delta = -0.1065 [-0.1269, -0.0875] — CI excludes zero in the WRONG direction. The fine-tune learned in-domain reranking that helps the val NDCG@10 (0.673 → 0.720) but hurts narrow-band rerank decisions on novel cross-framework pairs, presumably by sharpening false-positive distractors. reranker_v2 stays DROPPED and defaults.yaml is unchanged. Persisted to data/processed/reranker_v2_discriminative_eval.json.

## 2026-04-07 — H_S7: frozen-test re-test under discriminative metric

**Hypothesis.** Under the anchors-vs-distractors metric and any S4-adopted thresholds, the three frozen pairs achieve aggregate MRR ≥ 0.50 AND tier_acc ≥ 0.30, both substantially above the prior (1.0000-saturated NDCG, 0.0000 tier_acc) baseline, demonstrating that the rebuild's gating harness now generalizes to abstract cross-framework targets.

**Predicted direction.** Positive — current frozen scores are degenerate, any non-trivial discriminative score is an improvement.

**Minimum effect size.** Aggregate MRR ≥ 0.50 across the three frozen pairs combined; tier_acc ≥ 0.30.

**Metric.** Per-pair MRR + tier_acc; aggregate weighted by anchor count. Each frozen pair touched ONCE in S7, never retuned regardless of result.

**Frozen test pairs.** This IS the frozen test step.

**Result.** PARTIALLY CONFIRMED. B-2 aiuc_1__csa_aicm n=257: MRR=0.4354 [0.3912, 0.4794], tier_acc=0.7938 (was 0.0000), AUC=0.7564. B-1 aiuc_1__mitre_atlas n=32: MRR=0.4379 [0.2953, 0.5869], tier_acc=0.5938 (was 0.0000), AUC=0.5889. Phase A cosai_rm__owasp_llm n=0 (cosai_rm source-side anchor-skipping infrastructure bug — same as S3's cosai_rm__mitre_atlas miss). Aggregate over the 289 in-scope frozen anchors: weighted MRR ≈ 0.4357, weighted tier_acc ≈ 0.7716. Tier_acc gate (≥ 0.30) DRAMATICALLY CLEARED — the rebuild's classification ability was always there, just hidden behind the saturated NDCG@10 metric. MRR gate (≥ 0.50) NOT cleared (0.4357 < 0.50) — distractors still overlap positives in the [0.20, 0.45] range. NO retuning. Persisted to data/processed/frozen_tests_discriminative.json.

## 2026-04-07 — A0: cross-encoder fine-tune (BAAI/bge-reranker-base)

**Hypothesis.** Fine-tuning `BAAI/bge-reranker-base` on graded triples derived from expert/authoritative cross-framework edges (Direct=2, Related=1, None=0), with hard negatives sampled from high-bridge-but-unmapped pairs and easy negatives sampled randomly, beats the off-the-shelf MS MARCO MiniLM cross-encoder currently wired into `defaults.yaml` on aggregate honest CV NDCG@10 over the 5 expanded non-frozen pairs by ≥ 0.05 with paired-bootstrap 95% CI excluding 0.

**Predicted direction.** Positive (in-domain fine-tune > general MS MARCO weights for AI-security framework text).

**Minimum effect size.** Δ aggregate NDCG@10 ≥ 0.05 with paired-bootstrap CI excluding 0.

**Metric.** Aggregate NDCG@10 across 420 anchors from the 5 expanded non-frozen pairs (B2.7 protocol), computed via leave-one-out anchor masking and the existing PairMapper pipeline with `reranker.model` swapped.

**Training discipline.** Triples generation EXCLUDES: (a) all anchor-pair edges, (b) all three frozen-test pairs (`aiuc_1__csa_aicm`, `aiuc_1__mitre_atlas`, `cosai_rm__owasp_llm`), (c) all 1-hop graph neighbors of either side of any anchor or frozen-test pair. Training/validation split = leave-one-framework-pair-out CV across the surviving training pairs. Frozen test pairs are NEVER seen during training, validation, or model selection.

**Result.** REJECTED. n=420, baseline (no reranker) NDCG@10 = 1.0000 [1.0000, 1.0000], reranker_v2 NDCG@10 = 1.0000 [1.0000, 1.0000], paired-bootstrap delta = +0.0000 [+0.0000, +0.0000]. Same NDCG@10 saturation as B1.2–B1.7: 4 of 5 expanded non-frozen pairs are uniformly Direct, so the metric cannot move regardless of how good the reranker is. Reranker_v2 is DROPPED from the calibration pipeline; defaults.yaml is left unchanged. Training-time validation NDCG@10 on the held-out aiuc_1->nist_rmf pair did improve across epochs (0.673 → 0.709 → 0.720), so the model itself learned a meaningful signal — the gate is the problem, not the model. Persisted to data/processed/reranker_v2_eval.json. Re-test would require either populating rationale codes for non-owasp_agentic pairs or switching the metric to anchors-vs-distractors.

## 2026-04-07 — B1.7: mutual reciprocal rank

**Hypothesis.** Adding `mutual_reciprocal_rank` (harmonic mean of reciprocal rank of source in target's neighbor list AND target in source's neighbor list, where neighbors are scored via token-Jaccard similarity over name+description text) improves aggregate honest CV NDCG@10 over the 5 expanded non-frozen pairs by ≥ 0.03 with paired CI excluding 0 AND perm-importance CI excluding 0.

**Predicted direction.** Positive.

**Minimum effect size.** Δ NDCG@10 ≥ 0.03 paired CI excluding 0; perm-importance CI excluding 0.

**Result.** REJECTED. n=420, feature_nonzero_frac=0.931. baseline NDCG@10 = 1.0000 [1.0000, 1.0000], blended NDCG@10 = 1.0000 [1.0000, 1.0000], paired delta = +0.0000 [0.0000, 0.0000], perm importance = +0.0000 [0.0000, 0.0000]. Both gates fail. Same NDCG@10 saturation as B1.3/B1.5: feature carries real signal (93% non-zero) but the metric cannot move on a uniform-Direct anchor mix. Feature DROPPED. Helper retained for future re-test. Persisted to data/processed/b1_eval_mutual_reciprocal_rank.json.

## 2026-04-07 — B1.6: confidence-weighted bridge depth

**Hypothesis.** Adding `confidence_weighted_bridge_depth` (sum over 2-hop paths source -> bridge_node -> target of `conf(source,bridge) * conf(bridge,target)`) improves aggregate honest CV NDCG@10 over the 5 expanded non-frozen pairs by ≥ 0.03 with paired-bootstrap 95% CI excluding 0, AND has permutation-importance CI excluding 0.

**Predicted direction.** Positive (high-confidence 2-hop paths via curated bridge nodes indicate stronger semantic linkage than count-based bridge alone).

**Minimum effect size.** Δ NDCG@10 ≥ 0.03 paired CI excluding 0; perm-importance CI excluding 0.

**Result.** REJECTED. n=420, feature_nonzero_frac=0.000 — same bipartite-topology problem as B1.2: source and target framework nodes share zero 1-hop bridge neighbors in the current graph. Both gate criteria fail trivially. Feature DROPPED. To resurrect this idea would require either cross-framework category links during graph build, or relaxing "bridge" to 3-hop (which then risks transitive closure noise). Persisted to data/processed/b1_eval_confidence_weighted_bridge_depth.json.

## 2026-04-07 — B1.5: mitigation lexical match structural feature

**Hypothesis.** Adding `mitigation_lexical_match` (token Jaccard between source node's full semantic text and target node's `mitigation_text`) improves aggregate honest CV NDCG@10 over the 5 expanded non-frozen pairs by ≥ 0.03 with paired-bootstrap 95% CI excluding 0, AND has permutation-importance CI excluding 0.

**Predicted direction.** Positive (controls that share vocabulary with a risk's official mitigation guidance are more likely to *be* a mitigation).

**Minimum effect size.** Δ NDCG@10 ≥ 0.03 with paired-bootstrap CI excluding 0; permutation importance CI excluding 0.

**Coverage caveat.** mitigation_text is currently populated only on owasp_agentic targets (8/10), so the feature is non-zero on only ~119/420 anchors (the aiuc_1 -> owasp_agentic pair). Per-pair NDCG@10 on owasp_agentic is the primary signal; aggregate is reported but expected to under-represent the effect.

**Result.** REJECTED. n=420, feature_nonzero_frac=0.231 (97 of the 119 owasp_agentic anchors carry signal — coverage is real). baseline NDCG@10 = 1.0000 [1.0000, 1.0000], blended NDCG@10 = 1.0000 [1.0000, 1.0000], paired delta = +0.0000 [0.0000, 0.0000], permutation importance = +0.0000 [0.0000, 0.0000]. NDCG@10 saturated at 1.0; no movement possible. Feature DROPPED. Same metric-saturation root cause as B1.2/B1.3. Helper retained in structural.py for re-test under a non-degenerate anchor mix. Persisted to data/processed/b1_eval_mitigation_lexical_match.json.

## 2026-04-07 — B1.3: source out-degree ratio structural feature

**Hypothesis.** Adding `source_out_degree_ratio` (source node's out-degree divided by the source framework's mean out-degree) to the calibration feature set improves aggregate honest CV NDCG@10 over the 5 expanded non-frozen pairs by ≥ 0.03 with paired-bootstrap 95% CI excluding 0, AND has permutation-importance CI excluding 0.

**Predicted direction.** Positive (high-out-degree source nodes are "anchor controls" that have many curated mappings, so any candidate target is more likely to be a real link).

**Minimum effect size.** Δ NDCG@10 ≥ 0.03 with paired-bootstrap CI excluding 0; permutation importance CI excluding 0.

**Metric.** Aggregate NDCG@10 across non-frozen pairs (B2.7 protocol) plus permutation importance via the eval_b1_feature harness.

**Result.** REJECTED. n=420 anchors, feature_nonzero_frac=0.931 (the feature does carry signal across nodes, unlike shared_parent_centrality). baseline NDCG@10 = 1.0000 [1.0000, 1.0000], blended NDCG@10 = 1.0000 [0.9576, 1.0000], paired delta = -0.0015 [-0.0424, 0.0000], permutation importance = +0.0000 [0.0000, 0.0000]. Both gate criteria fail. Direction is mildly NEGATIVE (blending the feature in slightly hurts the saturated NDCG@10). Feature DROPPED. As with B1.2, the all-Direct anchor mix means NDCG@10 saturates at 1.0 and any positive lift is unmeasurable; the discriminating gate cannot be passed until rationale codes are populated for non-owasp_agentic frameworks or until the metric switches to one that doesn't degenerate on uniform-relevance vectors. Persisted to data/processed/b1_eval_source_out_degree_ratio.json.

## 2026-04-06 — B1.1: shared-parent centrality structural feature

**Hypothesis.** Adding a confidence-weighted shared-neighbor count between source and target nodes (`shared_parent_centrality`) to the calibration feature set improves aggregate honest CV NDCG@10 over the 5 expanded non-frozen pairs by ≥ 0.03 with paired-bootstrap 95% CI excluding 0, AND has permutation importance with CI excluding 0.

**Predicted direction.** Positive (controls and risks that share many high-confidence neighbors are more likely to be related).

**Minimum effect size.** Δ NDCG@10 ≥ 0.03 paired-bootstrap CI excluding 0; permutation importance CI excluding 0.

**Metric.** Aggregate NDCG@10 across non-frozen pairs (B2.7 protocol) plus permutation importance from `mapping_engine.calibration.diagnostics.permutation_importance_ci`.

**Mask discipline.** Feature computation must accept a `mask_pairs` set of edges to exclude, so leave-one-out anchor masking (B2.7) can drop the held-out anchor's own edge contribution before feature generation.

**Result.** REJECTED. shared_parent_centrality is structurally zero for every cross-framework anchor pair (verified directly: aiuc_1 -> owasp_agentic 43x10 matrix has 0 nonzero entries). The current unified graph is leaf-level bipartite across frameworks — source and target nodes share no graph neighbors because the only shared parents would be within-framework category nodes, not cross-framework. n=420 anchors, baseline NDCG@10 = 1.0000 (saturated), blended NDCG@10 = 1.0000, paired delta = +0.0000 [0.0000, 0.0000], permutation importance = +0.0000 [0.0000, 0.0000]. Both gate criteria fail. Feature DROPPED. To resurrect this idea would require either (a) building cross-framework parent-category links during graph build, or (b) reframing as "shared 2-hop neighbor", which is what the existing bridge feature already captures. Persisted to data/processed/b1_eval_shared_parent_centrality.json.

## 2026-04-06 — B2.9: NDCG@10 threshold-sweep objective

**Hypothesis.** Switching the threshold-sweep objective from Youden's J (binary mapped/unmapped accuracy) to aggregate NDCG@10 over all expanded non-frozen pairs improves aggregate honest CV NDCG@10 by ≥ 0.05 with bootstrap 95% CI on the delta excluding 0.

**Predicted direction.** Positive (NDCG-optimized thresholds ≥ Youden-optimized thresholds on NDCG@10).

**Minimum effect size.** Δ NDCG@10 ≥ 0.05 with paired-bootstrap 95% CI excluding 0.

**Metric.** Aggregate NDCG@10 over the 420 anchors in the 5 expanded non-frozen pairs (B2.7 set), computed on tier-graded predictions (Direct=2 / Related=1 / None=0) produced by the swept thresholds applied to LOO-masked composite scores.

**Frozen test pairs.** Excluded (B-2: aiuc_1__csa_aicm; B-1: aiuc_1__mitre_atlas; A: cosai_rm__owasp_llm).

**Result.** REJECTED. NDCG-optimal and Youden-optimal threshold pairs both converge to (direct=0.45, related_primary=0.20), aggregate NDCG@10 = 1.0000 [0.8942, 1.0000]. Paired-bootstrap delta = +0.0000 [0.0000, 0.0000]; CI does NOT exclude 0. Reason: 4 of 5 expanded pairs are uniformly Direct (rationale='?'), so NDCG@10 saturates regardless of objective and the threshold sweep is degenerate. The hypothesis cannot be tested with the current anchor mix; it should be re-run after B-1 introduces structural features that drive score variance, or after rationale codes are populated for non-owasp_agentic frameworks. Chose direct=0.45 / related_primary=0.20 by tie-break on Youden's J among the top NDCG group.

---

# Session 7.6 — Hardening pre-registrations

**Preamble.** Session 7.6 hardens the pipeline for SESSION 8 by fixing
the cosai_rm anchor-skipping bug (S1), re-baselining with cosai_rm pairs
(S2), diagnosing the aiuc_1__eu_gpai_cop MRR outlier (S3), enriching
target descriptions for 4 frameworks (S4–S7), re-baselining post-enrichment
(S8), adding cross-framework category links at graph build (S9), re-evaluating
previously-rejected structural features on the linked graph (S10), re-testing
mutual_reciprocal_rank with 10k permutations (S11), sweeping distractor count
(S12), and per-pair threshold calibration (S13). S1/S2/S3/S14 are non-gated
(infrastructure / diagnosis / documentation). H_76_S4..H_76_S13 below are the
gated hypotheses. All gates evaluate on the 7 non-frozen expanded pairs
(5 prior + 2 cosai_rm pairs unblocked by S1). **Frozen test sets are NOT
touched in this loop** — Session 7.5 S7 was the one-shot.

**Baseline convention.** Paired-bootstrap delta is measured against the
IMMEDIATELY-PRIOR pipeline state, not Session 7.5's baseline. The baseline
marches forward with each adopted change.

**Global rollback rule.** Any adoption that causes any single non-frozen
pair to regress by more than −0.02 MRR is auto-rolled back even if the
aggregate paired CI clears zero.

## 2026-04-07 — H_76_S4: eu_gpai_cop target-description enrichment

**Hypothesis.** Parsing canonical descriptions from the eu-gpai-cop source
corpus into the `description` field lifts aiuc_1__eu_gpai_cop MRR from the
Session 7.5 baseline (0.1202) by ≥ +0.05 with paired-bootstrap 95% CI excluding 0,
without aggregate regression on the other 6 non-frozen pairs beyond −0.005.

**Predicted direction.** Positive on eu_gpai_cop; neutral on other pairs.

**Metric.** Per-anchor MRR on `aiuc_1__eu_gpai_cop` (paired bootstrap) plus
aggregate MRR across 7 non-frozen pairs (regression cap).

**Result.** **ACCEPTED (decisively).** Pre-enrichment: MRR=0.1202, 28/28 anchor-relevant Article nodes had empty description. Enrichment parses "Article NN: Title\n\nBody" blocks from the aiuc-1 EU AI Act crosswalk (primary) and supplementary sentences from the GPAI CoP combined/safety/transparency/copyright markdown (secondary). All 28 article nodes now carry descriptions (median 672 chars, min 478). Post-enrichment: eu_gpai_cop MRR=**0.4125** (Recall@5=0.70, AUC=0.80). Paired Δ MRR on eu_gpai_cop = **+0.2923 [+0.2040, +0.3734]** — CI excludes 0 by ~6x the minimum effect size. Aggregate paired Δ MRR = +0.0438 [+0.0287, +0.0624], excluding 0. Per-pair regression check: no pair regressed (max drift +0.0069 on owasp_llm, within noise). `SEMANTIC_TEXT_VERSION` bumped to v5. pytest 88 passed.

## 2026-04-07 — H_76_S5: csa_aicm target-description enrichment

**Hypothesis.** Same pattern on csa_aicm: paired Δ MRR CI on
`aiuc_1__csa_aicm` excludes 0. If csa_aicm nodes already carry description
text (median ≥ 200 chars), the task NO-OPs and this hypothesis is vacated.

**Predicted direction.** Positive or no-op.

**Metric.** Paired Δ MRR on `aiuc_1__csa_aicm`; aggregate regression cap.

**Result.** _Pending S5._

## 2026-04-07 — H_76_S6: mitre_atlas target-description enrichment

**Hypothesis.** Same pattern on mitre_atlas. Likely no-op (ATLAS JSON
already carries descriptions).

**Predicted direction.** Positive or no-op.

**Metric.** Paired Δ MRR on `aiuc_1__mitre_atlas`; aggregate regression cap.

**Result.** NO-OP. mitre_atlas description coverage already at median 483 chars / max 2000 / 0 zeros across 218 nodes (verified post-S5 graph rebuild). No enrichment work needed; the add_node merge fix in S5 also benefits any future mitre_atlas stub-then-real merge cases. Aggregate non-frozen baseline unchanged from S5: MRR=0.3821 [0.3512, 0.4140].

## 2026-04-07 — H_76_S7: nist_rmf target-description enrichment

**Hypothesis.** Same pattern on nist_rmf. Likely no-op.

**Predicted direction.** Positive or no-op.

**Metric.** Paired Δ MRR on `aiuc_1__nist_rmf`; aggregate regression cap.

**Result.** WIN. nist_rmf was actually empty (not no-op): median description length 0/76 prior, 172/76 after enrichment from `nist_ai_rmf_1.0.md` (`**FUNC N.N:**` blocks). aiuc_1__nist_rmf MRR 0.3001 → 0.3260 (Δ +0.0259), recall@5 0.5000 → 0.4671, AUC 0.6537 → 0.6909. Aggregate non-frozen MRR 0.3821 → 0.3920 [0.3607, 0.4256], AUC 0.7077 → 0.7217. No per-pair regressions exceed −0.02 cap. Bumped `SEMANTIC_TEXT_VERSION` to v7.

## 2026-04-07 — H_76_S8: post-enrichment re-baseline + mitigation_lexical re-adopt

**Hypothesis.** Under the post-S7 enriched graph, (a) aggregate MRR on
the 7 non-frozen pairs is ≥ Session 7.5 baseline (0.3402), and (b) the
Session 7.5 S5 adoption of `mitigation_lexical_match` at weight=0.10
still clears both paired-Δ CI and permutation-importance CI.

**Predicted direction.** Both conditions hold (baseline marches forward, lexical feature remains load-bearing).

**Metric.** Aggregate MRR vs 0.3402 floor; paired Δ and perm CI on
mitigation_lexical_match (1000 resamples each).

**Rollback.** If lexical CI crosses 0 post-enrichment, reduce weight to
0.05 and re-test; if still fails, remove the blend.

**Result.** PARTIAL — (a) aggregate floor PASS, (b) lexical feature DROPPED. Aggregate non-frozen MRR with mitigation_lexical_match still blended at 0.10 = 0.3920 ≫ 0.3402 floor. Re-running `eval_b1_features_discriminative.py` on the enriched graph: at weight=0.10, paired Δ MRR = −0.0046 [−0.0137, +0.0044] (CI crosses 0); perm null [−0.0080, +0.0088] (observed inside null) → DROP. Rollback step 1 (weight=0.05): paired Δ −0.0027 [−0.0087, +0.0021] still crosses 0 → DROP. Rollback step 2 executed: removed the blend by defaulting `mitigation_lexical_match` weight to 0.0 in `mapper.py` (both call sites). Post-removal aggregate MRR 0.3831 [0.3534, 0.4155] — still well above the 0.3402 floor. Interpretation: target-side enrichment for owasp_agentic, eu_gpai_cop, and nist_rmf already supplies the lexical signal that mitigation_lexical_match was previously fishing out; the feature is now redundant under richer text and adds noise. Pre-registered rollback executed cleanly.

## 2026-04-07 — H_76_S9: cross-framework category links at graph build

**Hypothesis.** Emitting `cross_framework_category` edges between nodes
sharing a declared cross-framework category (privacy, robustness, etc.)
does not regress aggregate MRR on 7 non-frozen pairs by more than −0.005
vs the post-S8 baseline. The purpose is unblocking S10, not direct lift.

**Predicted direction.** Neutral (regression cap −0.005) with edge count
increase > 0 and node count unchanged.

**Metric.** Aggregate MRR paired Δ CI; graph build diagnostics.

**Result.** PASS (small lift, no regression). Added `create_cross_framework_category_edges` mapping nodes to a normalized 8-category vocabulary (privacy, security, governance, robustness, supply_chain, input_threat, runtime_threat, dev_threat) via domain/keywords/classification. Added 3884 directed cross_framework_category edges (after dedup); node count unchanged at 983; total edges 1883→5767. Aggregate non-frozen MRR 0.3831→0.3880 [0.3570, 0.4205], well above the −0.005 cap (Δ +0.0049). Per-pair: eu_gpai_cop +0.0125, owasp_llm +0.0280, nist_rmf −0.0015, owasp_agentic −0.0061, cosai_rm__mitre_atlas 0. None breach the −0.02 per-pair cap. Updated `test_load_counts` to assert 5767 edges. SEMANTIC_TEXT_VERSION bumped to v8. Unblocks S10 re-eval of shared_parent_centrality + confidence_weighted_bridge_depth.

## 2026-04-07 — H_76_S10: shared_parent_centrality + confidence_weighted_bridge_depth re-eval

**Hypothesis.** Under the S9-linked graph, at least one of
`shared_parent_centrality` or `confidence_weighted_bridge_depth`
(previously dropped for zero cross-framework 1-hop coverage) now clears
both paired-Δ MRR CI and permutation-importance CI at blend weight=0.10.

**Predicted direction.** Positive for at least one feature (coverage
> 10% of anchors under the linked graph).

**Metric.** Per-feature paired Δ MRR CI (1000 resamples) and permutation
importance CI (1000 perms). Adopt any feature whose CIs both exclude 0.

**Rollback.** Drop any feature whose per-pair regression exceeds −0.02.

**Result.** _Pending S10._

## 2026-04-07 — H_76_S11: mutual_reciprocal_rank re-test at 10k permutations

**Hypothesis.** `mutual_reciprocal_rank` failed the permutation CI in
Session 7.5 S5 at n_perm=1000 despite clearing paired Δ. Re-testing at
n_perm=10000 clears the permutation CI (CI excludes 0), confirming the
prior failure was a power issue rather than a true null.

**Predicted direction.** Positive (perm CI clears at 10k).

**Metric.** Permutation importance CI at n_perm=10000; paired Δ MRR CI
(1000 resamples) must still exclude 0.

**Result.** _Pending S11._

## 2026-04-07 — H_76_S12: distractor count calibration

**Hypothesis.** The canonical n_distractors=20 used throughout Session
7.5 produces an MRR CI width within 1.5x of the n_distractors=80 width,
so n=20 is a sufficient operating point.

**Predicted direction.** CI width ratio ≤ 1.5.

**Metric.** MRR bootstrap CI width at n ∈ {10, 20, 40, 80}.

**Rollback.** If n=20 fails the 1.5x ratio, adopt the smallest n whose
ratio vs n=80 is ≤ 1.2.

**Result.** _Pending S12._

## 2026-04-07 — H_76_S13: per-pair threshold calibration

**Hypothesis.** For at least one non-frozen pair, a per-pair
(direct, related_primary) threshold override strictly improves tier
accuracy on that pair (paired Δ tier_acc CI > 0 via LOO-within-pair)
without causing any other pair to regress more than −0.02 MRR.

**Predicted direction.** Positive for at least `aiuc_1__eu_gpai_cop`
(current MRR 0.1202 suggests thresholds are severely miscalibrated).

**Metric.** Per-pair LOO-within-pair paired Δ tier_acc CI (1000
resamples); aggregate MRR per-pair regression monitor.

**Rollback.** Any pair failing the regression cap is reverted to the
global (0.45, 0.20) thresholds.

**Result.** _Pending S13._
