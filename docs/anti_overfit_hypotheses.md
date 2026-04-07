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

**Result.** _to be filled in after S4 runs_

## 2026-04-07 — H_S5: B-1 structural features re-eval under discriminative metric

**Hypothesis.** Each of the three B-1 structural features that previously had non-zero coverage but failed the saturated NDCG@10 gate (`mitigation_lexical_match` 23%, `source_out_degree_ratio` 93%, `mutual_reciprocal_rank` 93%) improves aggregate MRR by ≥ 0.02 with paired-bootstrap 95% CI excluding 0 AND has permutation-importance CI excluding 0 when re-evaluated under the anchors-vs-distractors metric.

**Predicted direction.** Positive for at least one of the three (the metric saturation was the dominant blocker; with a discriminating metric, real signal should now be measurable).

**Minimum effect size.** Δ MRR ≥ 0.02 paired-bootstrap CI excluding 0; perm-importance CI excluding 0.

**Metric.** Same as H_S4. Per-anchor LOO masking retained.

**Frozen test pairs.** Excluded.

**Result.** _to be filled in after S5 runs_

## 2026-04-07 — H_S6: reranker_v2 re-eval under discriminative metric

**Hypothesis.** The fine-tuned `BAAI/bge-reranker-base` (reranker_v2) improves aggregate MRR by ≥ 0.03 over the post-S5 pipeline, with paired-bootstrap 95% CI on the delta excluding 0, when re-evaluated under the anchors-vs-distractors metric.

**Predicted direction.** Positive — A4 training-time validation showed real per-epoch lift (val NDCG@10 0.673 → 0.720), which the saturated A5 gate could not detect.

**Minimum effect size.** Δ MRR ≥ 0.03 paired-bootstrap CI excluding 0.

**Metric.** Same as H_S4 / H_S5.

**Frozen test pairs.** Excluded.

**Result.** _to be filled in after S6 runs_

## 2026-04-07 — H_S7: frozen-test re-test under discriminative metric

**Hypothesis.** Under the anchors-vs-distractors metric and any S4-adopted thresholds, the three frozen pairs achieve aggregate MRR ≥ 0.50 AND tier_acc ≥ 0.30, both substantially above the prior (1.0000-saturated NDCG, 0.0000 tier_acc) baseline, demonstrating that the rebuild's gating harness now generalizes to abstract cross-framework targets.

**Predicted direction.** Positive — current frozen scores are degenerate, any non-trivial discriminative score is an improvement.

**Minimum effect size.** Aggregate MRR ≥ 0.50 across the three frozen pairs combined; tier_acc ≥ 0.30.

**Metric.** Per-pair MRR + tier_acc; aggregate weighted by anchor count. Each frozen pair touched ONCE in S7, never retuned regardless of result.

**Frozen test pairs.** This IS the frozen test step.

**Result.** _to be filled in after S7 runs_

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
