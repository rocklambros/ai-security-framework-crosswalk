# Pre-Registered Hypotheses Log

This file records every hypothesis pre-registered before running cross-validation on a new feature, model change, or calibration adjustment, per the methodology in `docs/anti_overfit_methodology.md`.

**Format:** each entry is a dated section. Hypotheses are written **before** seeing CV results. The result is filled in afterward, regardless of outcome — negative results are not deleted.

**Decision rule for every entry:** an improvement only counts if the bootstrap 95% CI on the delta vs baseline excludes 0 AND the predicted direction matches the observed direction AND any related permutation-importance CI excludes 0.

---

<!-- Append new entries below this line. Do not edit prior entries except to fill in their result. -->

## 2026-04-06 — B2.9: NDCG@10 threshold-sweep objective

**Hypothesis.** Switching the threshold-sweep objective from Youden's J (binary mapped/unmapped accuracy) to aggregate NDCG@10 over all expanded non-frozen pairs improves aggregate honest CV NDCG@10 by ≥ 0.05 with bootstrap 95% CI on the delta excluding 0.

**Predicted direction.** Positive (NDCG-optimized thresholds ≥ Youden-optimized thresholds on NDCG@10).

**Minimum effect size.** Δ NDCG@10 ≥ 0.05 with paired-bootstrap 95% CI excluding 0.

**Metric.** Aggregate NDCG@10 over the 420 anchors in the 5 expanded non-frozen pairs (B2.7 set), computed on tier-graded predictions (Direct=2 / Related=1 / None=0) produced by the swept thresholds applied to LOO-masked composite scores.

**Frozen test pairs.** Excluded (B-2: aiuc_1__csa_aicm; B-1: aiuc_1__mitre_atlas; A: cosai_rm__owasp_llm).

**Result.** REJECTED. NDCG-optimal and Youden-optimal threshold pairs both converge to (direct=0.45, related_primary=0.20), aggregate NDCG@10 = 1.0000 [0.8942, 1.0000]. Paired-bootstrap delta = +0.0000 [0.0000, 0.0000]; CI does NOT exclude 0. Reason: 4 of 5 expanded pairs are uniformly Direct (rationale='?'), so NDCG@10 saturates regardless of objective and the threshold sweep is degenerate. The hypothesis cannot be tested with the current anchor mix; it should be re-run after B-1 introduces structural features that drive score variance, or after rationale codes are populated for non-owasp_agentic frameworks. Chose direct=0.45 / related_primary=0.20 by tie-break on Youden's J among the top NDCG group.
