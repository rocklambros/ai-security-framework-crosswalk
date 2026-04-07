# Pre-Registered Hypotheses Log

This file records every hypothesis pre-registered before running cross-validation on a new feature, model change, or calibration adjustment, per the methodology in `docs/anti_overfit_methodology.md`.

**Format:** each entry is a dated section. Hypotheses are written **before** seeing CV results. The result is filled in afterward, regardless of outcome — negative results are not deleted.

**Decision rule for every entry:** an improvement only counts if the bootstrap 95% CI on the delta vs baseline excludes 0 AND the predicted direction matches the observed direction AND any related permutation-importance CI excludes 0.

---

<!-- Append new entries below this line. Do not edit prior entries except to fill in their result. -->

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
