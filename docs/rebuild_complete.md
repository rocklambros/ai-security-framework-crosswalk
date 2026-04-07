# B-2 / B-1 / A Rebuild — Complete

The B-2 / B-1 / A rebuild planned in
`memory/project_b2_b1_a_rebuild_plan.md` is complete.

**Final pipeline.** B-2 hand-tuned weights with NDCG@10-objective
thresholds (`direct=0.45`, `related_primary=0.20`). Nothing else stuck:
all 5 B-1 structural features were dropped on their anti-overfit gates,
and the Phase A reranker_v2 fine-tune was dropped on a paired-bootstrap
delta of +0.0000 against the saturated NDCG@10 metric.

**Anti-overfit summary.** 8 hypotheses pre-registered before CV in
`docs/anti_overfit_hypotheses.md`, all 8 REJECTED with full bootstrap
CIs. 1000-resample bootstrap on every metric. Three frozen test sets
each touched exactly once and never retuned.

**Frozen test results.**

| Phase | Frozen pair | n | NDCG@10 | tier accuracy |
|---|---|---|---|---|
| B-2 | `aiuc_1 -> csa_aicm`     | 257 | 1.0000 | 0.0000 |
| B-1 | `aiuc_1 -> mitre_atlas`  |  32 | 1.0000 | 0.0000 |
| A   | `cosai_rm -> owasp_llm`  |  18 | 1.0000 | 0.0000 |

(Phase A pair reassigned during B2.5 — `aiuc_1 -> cosai_rm` has 0
expert/authoritative edges.)

**Why every gate failed.** 4 of 5 expanded non-frozen pairs and all
three frozen pairs have unpopulated rationale codes, so every
expected_tier defaults to `Direct`. NDCG@10 saturates at 1.0 under
uniform graded relevance and cannot detect score improvements. The
frozen tier_accuracy of 0 is a separate honest signal that calibrated
thresholds are too high for abstract cross-framework targets, and is
documented but not retuned per the frozen-test discipline.

**Pointers.**
- Plan and per-task history: `memory/project_b2_b1_a_rebuild_plan.md`
- Cross-phase summary: `docs/cross_phase_summary.md`
- Frozen test results: `docs/frozen_test_results.md`
- B-1 ablation matrix: `docs/diagnostics/b1_ablation.md`
- Hypothesis log: `docs/anti_overfit_hypotheses.md`
- Anti-overfit methodology: `docs/anti_overfit_methodology.md`

**Final pytest:** 69 passed, 0 xfails.
