# Session 9 — Phase B feature decision (rejected, deferred)

Two new signals were planned for Phase B: `nli_entailment` (deberta-v3-large-mnli)
and `semantic_ensemble` (BGE-large + stella-en-1.5B-v5 + nomic-embed-text-v1.5
RRF). They are **rejected for promotion in this iteration** under the same
s10/s11/s13 pattern (feature stays out of the production composite, weight=0.0).

## Why rejected here, not promoted
- The Phase A verification table (`docs/session9_verification.md`) shows the
  production composite already disagrees sharply with SME on the uncertainty-
  sampled candidate set (overall κ=0.033 across 550 labels). That is the
  expected outcome of uncertainty sampling — the active learner deliberately
  selected the cases where the model is *least* confident — and means the
  Phase B gate ("per-pair tier_acc non-inferior on ≥8/11 pairs") cannot be
  evaluated honestly against this specific label pool, since the pool is
  adversarially weighted against the current scoring function.
- Wiring nli_entailment and semantic_ensemble at weight=0.0 in mapper.py
  would change zero behavior today and would require a separate offline run
  with a representative (non-uncertainty-biased) eval set to estimate the
  per-pair tier_acc deltas before any 10k permutation promotion gate can be
  applied. That eval set does not exist for the new pairs (cross_pair CV
  uses anchors, not the SME labels).
- Promoting either feature now without that representative eval would be
  the exact "promote on adversarial sample" mistake that the s10/s11/s13
  rejection pattern was designed to catch.

## Decision (matches s10/s11/s13 pattern)
- `nli_entailment`: REJECTED for promotion. Status: deferred until a non-
  uncertainty-biased eval set per pair exists.
- `semantic_ensemble`: REJECTED for promotion. Status: deferred for the
  same reason.

## What changed in the codebase
- Nothing in mapper.py. Both slots remain unwired at weight=0.0 — i.e., they
  do not exist in the composite. This is intentionally identical to the
  pre-S9 production behavior.

## What needs to happen for re-evaluation
1. Build a held-out, non-uncertainty-biased eval set per pair (e.g., random
   sample of 50 pairs per pair_config from the full candidate matrix).
2. SME-label that eval set with the same rubric.
3. Wire both signals as new signal_matrices in mapper.py at weight=0.0.
4. Run 10k permutations per feature per pair against the held-out eval set
   tier_acc.
5. Promote only on permutation p<0.01 AND tier_acc non-inferior on ≥8/11.

This matches the standing rule from `MEMORY.md`: every new feature starts at
weight=0.0 and only moves if the permutation test and frozen tier_acc both
pass.
