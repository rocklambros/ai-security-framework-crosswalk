# SESSION 8 Readiness

This page is the green/red checklist for entering SESSION 8 (Run
Pipeline on New Pairs + Cross-Pair Validation). All items below were
shipped by the Session 7.5 ralph-loop run; see
`memory/project_session8_unblock_plan.md` for the per-task atomic log.

## Headline

**The rebuild's gating harness now works end-to-end.** Frozen tier
accuracy went from 0.0000 to 0.7938 (B-2) / 0.5938 (B-1) under the
discriminative metric, with no threshold retuning, no rationale-code
labeling, and no graph surgery. The bottleneck the rebuild diagnosed
("metric is degenerate, scores were always fine") is empirically
confirmed: the same composite scores that scored tier_acc=0 under
NDCG@10 saturation now hit ~0.79 under a non-degenerate gate.

## Final scores

### Discriminative non-frozen baseline (post-S5, n=381)

| Metric | Value (95% CI) |
|---|---|
| MRR  | 0.3402 [0.3066, 0.3708] |
| Recall@5 | 0.5433 [0.4882, 0.5906] |
| ROC-AUC | 0.6498 [0.6235, 0.6752] |

### Frozen one-shot (S7)

| Phase | Pair | n | MRR [95% CI] | Tier acc |
|---|---|---|---|---|
| B-2 | `aiuc_1 -> csa_aicm` | 257 | 0.4354 [0.3912, 0.4794] | **0.7938** |
| B-1 | `aiuc_1 -> mitre_atlas` | 32 | 0.4379 [0.2953, 0.5869] | **0.5938** |
| A   | `cosai_rm -> owasp_llm` | 0 | n/a (cosai_rm bug) | n/a |

### Per-pair from the Session 8 cross-pair harness

See `docs/session8_cross_pair_validation.md` for the full table.

## Green checks

- [x] Anchors-vs-distractors sampler shipped + tested (S1)
- [x] Discriminative metric (MRR / Recall@5 / ROC-AUC + bootstrap + paired delta) shipped + tested (S2)
- [x] B-2 baseline frozen under the new metric (S3)
- [x] Threshold re-sweep ran honestly (kept B-2 0.45/0.20; paired CI overlapped 0) (S4)
- [x] B-1 structural feature re-eval — `mitigation_lexical_match` ADOPTED into production composite (S5)
- [x] Reranker_v2 re-eval — confirmed dropped under non-saturated gate (delta -0.1065 [-0.1269, -0.0875]) (S6)
- [x] Frozen tests one-shot, no retuning, tier_acc 0.0 → 0.79 (S7)
- [x] Cross-pair validation harness for SESSION 8 + smoke test (S8)
- [x] All 4 pre-registered hypotheses (H_S4..H_S7) closed with full bootstrap CIs in `docs/anti_overfit_hypotheses.md`
- [x] 86 pytest, 0 xfails

## Known limitations carried into SESSION 8

- **`cosai_rm__*` anchor-skipping bug.** Both `cosai_rm__mitre_atlas`
  (29 anchors) and `cosai_rm__owasp_llm` (18 anchors, the Phase A
  frozen pair) report `n_anc=0` from the discriminative harness because
  cosai_rm source nodes do not surface in PairMapper's
  `anchor_validation` masked records. Production mappings (`n_map=17`
  and `n_map=2` respectively) are unaffected, but the discriminative
  metric cannot score these pairs until the bug is fixed. Filed for
  SESSION 8 follow-up; root cause likely lives in
  `_run_with_masked_anchors` key construction when the source framework
  is not aiuc_1.

- **MRR target (≥ 0.50) not cleared on frozen tests.** Aggregate
  weighted MRR is 0.4357. Distractors still overlap positives in
  the [0.20, 0.45] composite-score band. The remaining lift requires
  ONE of: rationale-code labeling for non-`owasp_agentic` pairs,
  per-pair threshold calibration, or richer cross-framework category
  links during graph build. Out of scope for the current loop.

- **`reranker_v2` is empirically harmful**, not just unhelpful.
  Per-pair regressions are uniform (-0.05 to -0.15 MRR). Don't
  re-enable without re-training on a non-frozen anchor mix that
  includes the cosai_rm pairs.

## How to run SESSION 8

```bash
# Regenerate the cross-pair table any time the pipeline changes:
python -m mapping_engine.scripts.cross_pair_validation

# Run the production pipeline on a single pair:
python -m mapping_engine.scripts.run_pair <source_fw>__<target_fw>

# Re-run the discriminative baseline (S3) to refresh
# data/processed/discriminative_baseline.json:
python -m mapping_engine.scripts.eval_discriminative_baseline

# Re-run the one-shot frozen tests (S7) — this is destructive of
# the "touched once" discipline; use only when the pipeline has
# changed in a way that requires the frozen scores to be refreshed:
python -m mapping_engine.scripts.run_frozen_tests_discriminative
```

## Verdict

SESSION 8 is unblocked. Proceed.
