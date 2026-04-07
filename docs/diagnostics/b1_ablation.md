# B-1 Feature Ablation Matrix

## Surviving features

**None.** All five B-1 structural features evaluated in B1.2–B1.7 failed
their pre-registered anti-overfit gates and were dropped:

| Feature | Task | Reason for drop |
|---|---|---|
| `shared_parent_centrality` | B1.2 | Zero-coverage: bipartite cross-framework topology means 0 common 1-hop neighbors. |
| `source_out_degree_ratio` | B1.3 | NDCG@10 saturated at 1.0; paired delta -0.0015 [-0.0424, 0.0000]. |
| `mitigation_lexical_match` | B1.5 | NDCG@10 saturated; paired delta 0.0000 even at 23% non-zero coverage. |
| `confidence_weighted_bridge_depth` | B1.6 | Same bipartite-topology zero-coverage problem as B1.2. |
| `mutual_reciprocal_rank` | B1.7 | NDCG@10 saturated; paired delta 0.0000 at 93% non-zero coverage. |

## Ablation matrix

Surviving feature set is the empty set, so the 2^k subset matrix has
exactly one row:

| Subset | Aggregate NDCG@10 (paired vs B-2 baseline) |
|---|---|
| `{}` (B-2 baseline only) | 1.0000 [0.8421, 1.0000] (point [95% CI], from B2.7) |

There is nothing to prune.

## Why the gate is unmovable in this phase

NDCG@10 over the 5 expanded non-frozen pairs (420 anchors, 4/5 pairs
uniformly Direct) saturates at 1.0 because the gold-relevance vector
for those pairs is constant. Any monotone transform of the score
preserves the ranking, and the ideal DCG equals the actual DCG when
all true positives carry identical grades. As a result, structural
features cannot be detected via NDCG@10 even when they carry signal
across nodes (B1.3 and B1.7 had >93% non-zero coverage and still moved
the metric by exactly 0.0000).

## What would unblock B-1

The features themselves are not necessarily wrong; the *evaluation
gate* is degenerate. To make them testable would require ONE of:

1. **Populate rationale codes** for the 4 non-`owasp_agentic` framework
   pairs so `expand_anchors.py` can produce mixed `Direct`/`Related`
   tier labels (recovers ranking-metric movement).
2. **Switch metric** to one that does not degenerate on uniform
   relevance — e.g. *anchors-vs-distractors* discriminative ranking
   where distractors are sampled from non-mapped (source, target) pairs.
3. **Cross-framework category links** in the graph (would unblock
   `shared_parent_centrality` and `confidence_weighted_bridge_depth`
   independently of the metric question).

These items are out of scope for this rebuild and recorded as TODOs in
the methodology doc.

## Decision

`FEATURES` in `weight_learner.py` is left unchanged (B-2 hand-tuned
weights remain canonical). No code prunes are needed because nothing
was wired in.

---

## Session 7.5 follow-up — discriminative re-evaluation (S5, 2026-04-07)

After Session 7.5's S2/S3 shipped the anchors-vs-distractors gate (path
#2 in "What would unblock B-1" above), the three coverage>0 features
were re-run under MRR with paired-bootstrap delta and a sign-shuffled
permutation-importance test. n=381 anchors, 20 distractors per anchor,
seed=20260407, blend=0.10.

| Feature | Coverage | Δ MRR (paired) | Perm observed vs null | Decision |
|---|---|---|---|---|
| `mitigation_lexical_match` | 23 % | **+0.0116 [+0.0042, +0.0208]** | **+0.0116 vs [-0.0080, +0.0079]** | **KEEP** |
| `source_out_degree_ratio` | 93 % | +0.0020 [-0.0007, +0.0066] | +0.0020 vs [-0.0026, +0.0026] | DROP |
| `mutual_reciprocal_rank` | 93 % | +0.0084 [+0.0007, +0.0173] | +0.0084 vs [-0.0100, +0.0092] | DROP (perm fails) |

`mitigation_lexical_match` is the first B-1 feature to clear both gates
in the entire rebuild. It is wired into both the production
`PairMapper.run` composite and the masked-validation
`_run_with_masked_anchors` composite at weight 0.10 via the new
`_blend_mitigation_lexical` helper. Persisted to
`data/processed/b1_discriminative_eval.json`.
