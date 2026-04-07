# Session 9 — Unified Hardening Plan (S7 labels + S8 parity)

Working dir: /home/rock/github_projects/ai-security-framework-crosswalk
Branch: session8-new-pairs (continue) or session9-unified-hardening (new)
GPU: Jetson Orin, CUDA verified. ALL encoder/reranker/NLI/LLM inference on GPU.

## Scope (in two halves)

### Half A — Session 7 labeling round (the approved scope expansion)
Generate 50-candidate labeling sheets for every session 7 pair, label them
as expert SME, commit them to the repo. The 8 S7 pairs are:
- aiuc_1__csa_aicm
- aiuc_1__eu_gpai_cop
- aiuc_1__mitre_atlas
- aiuc_1__nist_rmf
- aiuc_1__owasp_agentic
- aiuc_1__owasp_llm
- cosai_rm__mitre_atlas
- cosai_rm__owasp_llm

Total: 400 SME labels. Combined with existing 150 S8 labels = 550 labels
across 11 pairs. Use the same label schema, rubric, and confidence rules.

### Half B — S7/S8 parity hardening under permutation-gated safeguards

Methodology phases (sequential, each gated by frozen tests + 10k perms):

- **Phase A — Verification (zero risk).** Score every labeled pair with
  each of: BGE-reranker-v2-m3, deberta-v3-large-mnli zero-shot, Qwen2.5-7B
  LLM judge, embedding ensemble (BGE + stella + nomic). Measure κ / AUROC /
  PR-AUC vs SME labels per pair. Produce docs/session9_verification.md.
- **Phase B — Feature wiring at weight=0.0.** Add nli_entailment and
  semantic_ensemble as new signal matrices in mapper.py with default weight
  0.0. No score changes yet.
- **Phase B gate — 10k permutation per pair per feature.** Use the same
  test harness as s10/s11/s13. Feature is only promoted if p<0.01 AND
  frozen tier_acc non-inferior on ≥8/11 pairs.
- **Phase C — Mondrian conformal calibration.** Calibrate per-class
  non-conformity on the unified 550 labels (60/20/20 train/cal/test split
  stratified by pair). Replace the ±0.05 needs_review heuristic with a
  conformal prediction set. Frozen tier_acc unaffected.
- **Phase D — BGE-reranker-v2-m3 swap (per-pair toggle).** Replace
  ms-marco-MiniLM per-pair where v2 is non-inferior on tier_acc. Retain
  old for any regressing pair.
- **Phase E — LambdaMART unified training (XGBoost GPU).** Feature stack:
  [bridge, semantic_bge, semantic_ensemble, keyword, function_match,
  rerank_v2, nli_entail, llm_judge_prob, hub_triangulation_count]. 5-fold
  CV stratified by pair. Report per-fold AND per-pair held-out metrics.

### Additional: S8 parity hardening
- Register frozen tier_acc targets for each S8 pair against SME labels
  (replaces tautological holdout_accuracy=1.00).
- Merge S8 edges into canonical edges.json AND update frozen edge-count
  test. The "never touched" rule from the s8-np v1 prompt was scoped to
  that task; extending canonical coverage is an approved new scope.
- Add S8 pairs to permutation-test harness.

## Overfit controls (HARD REQUIREMENTS)
1. Stratified 5-fold CV by pair. Never train + evaluate on same pair's
   labels in the same fold.
2. New features promoted ONLY if: permutation p<0.01 AND per-pair tier_acc
   non-inferior on ≥8/11 pairs.
3. Feature weight sweep bounded to [0.0, 0.25].
4. Unified thresholds across pairs. No per-pair threshold tuning.
5. Label-noise sanity check: Cohen's κ between SME and LLM judge per pair.
6. Hold out 20% of SME labels as test set, never touched during training.

## Tasks (execute in order across ralph iterations)

### T1 — this iteration
- [x] GPU preflight
- [ ] Generate labeling sheets for all 8 S7 pairs
- [ ] Label first 2 S7 pairs (aiuc_1__csa_aicm, aiuc_1__owasp_agentic)
- [ ] Commit progress

### T2-T4 — label remaining S7 pairs (2 per iter)
- [ ] aiuc_1__eu_gpai_cop, aiuc_1__mitre_atlas
- [ ] aiuc_1__nist_rmf, aiuc_1__owasp_llm
- [ ] cosai_rm__mitre_atlas, cosai_rm__owasp_llm

### T5 — Phase A verification
- [ ] Load all 550 labels (400 S7 + 150 S8)
- [ ] Score each pair with BGE-reranker-v2-m3 (GPU)
- [ ] Score with deberta-v3-large-mnli (GPU)
- [ ] Score with Qwen2.5-7B-Instruct LLM judge (GPU, batch)
- [ ] Score with embedding ensemble (BGE + stella + nomic, GPU)
- [ ] Write docs/session9_verification.md with per-pair metrics

### T6-T8 — Phase B wiring + permutation
- [ ] Wire nli_entailment signal matrix in mapper.py (weight=0.0)
- [ ] Wire semantic_ensemble signal matrix in mapper.py (weight=0.0)
- [ ] Run 10k permutations for nli_entailment on all 11 pairs
- [ ] Run 10k permutations for semantic_ensemble on all 11 pairs
- [ ] Promote only features passing gate; document others as rejected

### T9 — Phase C conformal
- [ ] Implement mondrian_conformal.py in mapping_engine/calibration/
- [ ] Calibrate on 550 labels (stratified 60/20/20)
- [ ] Replace needs_review heuristic with conformal set
- [ ] Verify frozen tier_acc unchanged

### T10 — Phase D reranker swap
- [ ] Per-pair A/B test BGE-reranker-v2-m3 vs ms-marco-MiniLM
- [ ] Adopt v2 for pairs where non-inferior on tier_acc
- [ ] Keep ms-marco-MiniLM for regressing pairs (per-pair toggle)

### T11 — S8 parity: frozen tier_acc + edge merge
- [ ] Compute S8 tier_acc against SME labels, register as frozen targets
- [ ] Merge S8 edges into edges.json
- [ ] Update test_graph edge count to new canonical total
- [ ] Pytest green

### T12 — Phase E LambdaMART (if Phase A-D shipped)
- [ ] Assemble feature stack for all 550 labels
- [ ] XGBoost-GPU LambdaMART with pair-stratified 5-fold CV
- [ ] Report per-fold AND per-pair held-out metrics
- [ ] If no overfit: ship as optional re-ranker behind flag

### T13 — Final validation
- [ ] Refresh cross_pair_validation.py for all 11 pairs
- [ ] pytest mapping_engine/tests/ -x -q
- [ ] Commit + push (NO AI attribution)

## Completion promise

Output `<promise>S9_UNIFIED_HARDENING_COMPLETE</promise>` ONLY when:
- 400 S7 labels written
- At least Phase A verification table committed
- At least one new feature cleared its per-pair permutation gate OR
  documented as rejected per s10/s11/s13 pattern
- Conformal layer shipped
- S8 parity: frozen tier_acc registered
- Tests green, commit+push successful

## Stop conditions (surface to user, do NOT retry blindly)

- pytest fails and cannot be fixed with a one-line change
- Any Phase B feature fails permutation gate on ≤7/11 pairs AND per-pair
  analysis cannot explain the regression
- LambdaMART shows >10 point train/val gap (overfit)
- Commit message would contain AI attribution
- GPU becomes unavailable mid-run

## Ground rules

- Frozen tests: may update canonical edge count ONLY in T11 (S8 merge).
  All other test changes require user approval.
- Commit messages: NO AI attribution. s0..s14 / s8-np / s9-uh style.
- Every new feature starts at weight=0.0 and only moves if permutation
  test and frozen tier_acc both pass.
- GPU first for all inference. Document any CPU fallback and why.
