# Session 8 — Hardened Ready

Closing summary for the Session 7.6 hardening loop (S0–S14). All 15
atomic tasks complete; pipeline ready for Session 8.

## Final non-frozen scores (`discriminative_baseline_s7_6.json`)

| pair | n | MRR | 95% CI | Recall@5 | ROC-AUC |
|---|---:|---:|---|---:|---:|
| `aiuc_1__eu_gpai_cop`    |  60 | 0.4250 | [0.347, 0.512] | 0.717 | 0.803 |
| `aiuc_1__nist_rmf`       | 152 | 0.3245 | [0.278, 0.381] | 0.467 | 0.690 |
| `aiuc_1__owasp_agentic`  | 109 | 0.4226 | [0.368, 0.482] | 0.771 | 0.595 |
| `aiuc_1__owasp_llm`      |  60 | 0.3781 | [0.306, 0.456] | 0.683 | 0.528 |
| `cosai_rm__mitre_atlas`  |  29 | 0.5351 | [0.395, 0.674] | 0.759 | 0.866 |
| **AGGREGATE**            | **410** | **0.3880** | **[0.357, 0.420]** | **0.637** | **0.719** |

Session 7.5 baseline was n=381 MRR=0.3402. Session 7.6 marches that to
n=410 MRR=0.3880 (+0.048 absolute, paired CI clears 0) **with the
mitigation_lexical_match feature removed**, i.e. the lift comes from
target-side enrichment + cross-framework category links, not blend
tuning. Frozen tests untouched.

## Adopted-feature ledger (final, post-7.6)

| signal | weight | source |
|---|---:|---|
| bridge | 0.45 | B-2 weight learner |
| semantic | 0.20 | B-2 weight learner |
| keyword | 0.20 | B-2 weight learner |
| function_match | 0.15 | B-2 weight learner |
| **mitigation_lexical_match** | **0.0 (removed)** | S8 rollback (CI crossed 0 under enriched text) |
| shared_parent_centrality | 0.0 (rejected) | S10 (paired Δ inside perm null) |
| confidence_weighted_bridge_depth | 0.0 (rejected) | S10 (collapses to same 1-hop walk) |
| mutual_reciprocal_rank | 0.0 (rejected) | S11 (genuinely null at 10k perms) |
| source_out_degree_ratio | 0.0 (rejected) | B-1 |
| node2vec | 0.0 (opt-in) | Session 6 |

## What changed in Session 7.6

| step | change | effect |
|---|---|---|
| S1 | cosai_rm anchors unblocked (`source_entry_types += risk`) | +1 scorable pair |
| S2 | re-baseline w/ cosai_rm__mitre_atlas | aggregate 0.3389 (n=410) |
| S3 | eu_gpai_cop forensic diagnosis | smoking gun: 0-char descriptions |
| S4 | eu_gpai_cop enrichment from markdown | eu_gpai_cop MRR 0.1202→0.4125 (+0.2923) |
| S5 | csa_aicm enrichment via add_node merge fix | csa_aicm desc median 0→159 chars |
| S6 | mitre_atlas (already at median 483) | NO-OP |
| S7 | nist_rmf enrichment from markdown | nist_rmf MRR 0.3001→0.3260 (+0.0259) |
| S8 | re-baseline + lexical re-adopt | rollback: lexical CI crossed 0, dropped |
| S9 | cross-framework category links | +3884 edges; aggregate +0.0049 |
| S10 | re-eval shared_parent / confidence_weighted_bridge | both still null |
| S11 | mutual_reciprocal_rank @ 10k perms | genuinely null |
| S12 | distractor count sweep n∈{10,20,40,80} | KEEP n=20 (within 1.5× n=80 width) |
| S13 | per-pair threshold sweep | structural invariance, KEEP global |
| S14 | wrap-up (this doc) | — |

## Anti-overfit posture

- All H_76_S4..H_76_S13 hypotheses pre-registered in
  `docs/anti_overfit_hypotheses.md` BEFORE evaluation.
- 1000-resample bootstrap CI on every metric; 10k perms on the S11
  re-test.
- Per-pair −0.02 MRR cap enforced — no per-pair regression breached it.
- Frozen tests **NEVER** touched in this loop.

## Open limitations

1. **Anchor count is the bottleneck.** Distractor sweep (S12) shows CI
   widths are essentially flat across n∈{10..80} (0.060–0.065). The
   path to tighter CIs is more anchors, not more distractors.
2. **csa_aicm gate unenforceable inside the loop.** csa_aicm is B-2
   frozen so the S5 enrichment win lands only on the next frozen-test
   refresh.
3. **Per-pair threshold calibration deferred.** Discriminative metric
   is invariant under (direct, related_primary) thresholds; that
   calibration belongs to a precision/recall metric on the
   classification step and is out of scope for ranking hardening.
4. **owasp_agentic AUC=0.595.** This pair retains the worst AUC of
   the non-frozen set; Session 8 should investigate whether the
   `applicable_capabilities` field carries discriminating signal that
   isn't yet wired into the composite.

## Green/red checklist

- [x] All 15 atomic tasks complete (S0–S14)
- [x] Aggregate non-frozen MRR ≥ Session 7.5 baseline (0.3880 ≥ 0.3402)
- [x] No per-pair −0.02 cap breach
- [x] Frozen tests untouched
- [x] All anti-overfit hypotheses pre-registered
- [x] pytest 88 passed, 0 xfails (every iteration)
- [x] Reliability diagram refreshed (`docs/diagnostics/session7_6_reliability.png`)
- [x] Cross-pair validation refreshed (`docs/session8_cross_pair_validation.md`)
- [x] Decision log appended for every task
