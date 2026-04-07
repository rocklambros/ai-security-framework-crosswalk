# Session 8 New Pairs — Ralph Loop Task Spec

Working dir: /home/rock/github_projects/ai-security-framework-crosswalk
Branch: session8-new-pairs (already checked out, do NOT switch)
Frozen tests: NEVER touched.
Use GPU where available.

Execute tasks T0, T2, T4, T5, T6, T8, T9, T10 in order. After each task,
append a one-line decision log entry to docs/session8_new_pairs_log.md.

When ALL tasks below are complete and pytest is green and the commit + push
have succeeded, output exactly: <promise>S8_NEW_PAIRS_COMPLETE</promise>

## T0 — owasp_agentic AUC investigation

owasp_agentic AUC=0.595 is the worst non-frozen pair (see
docs/session8_hardened_ready.md §4). Hypothesis: the
applicable_capabilities field on OWASP Agentic targets carries
discriminating signal not yet wired into the composite score.

Steps:
1. Read mapping_engine/output/results/aiuc_1__owasp_agentic.json and the
   feature pipeline modules under mapping_engine/engine/.
2. Check whether applicable_capabilities is loaded into the graph at all.
3. Implement a candidate feature that uses it.
4. ANTI-OVERFIT GATE (HARD): the new feature must clear BOTH
   - paired bootstrap CI on aggregate non-frozen MRR (CI must not cross 0
     in the wrong direction), AND
   - 10k-permutation null on owasp_agentic specifically.
5. If either gate fails: REVERT the change and append a rejection ledger
   entry to docs/session8_hardened_ready.md following the s10/s11 pattern.
6. Frozen tests untouched regardless of outcome.

## T2 — csa_aicm to owasp_agentic

1. python -m mapping_engine.scripts.add_pair csa_aicm owasp_agentic
2. Use sequential-thinking MCP to choose 10 anchor pairs based on
   CSA AICM control descriptions, OWASP Agentic risk descriptions, and
   bridge scores. Write the rationale (which 10, why each) to
   docs/session8_anchors_csa_aicm__owasp_agentic.md.
3. Set 3 holdout_indices in the pair YAML.
4. Run python -m mapping_engine.scripts.run_pair csa_aicm__owasp_agentic
5. Report mapping count, tier distribution, anchor holdout accuracy.
6. If anchor holdout fails, adjust thresholds in the PAIR config only
   (NOT global) and re-run once. If it fails again, STOP and surface.

## T4 — mitre_atlas to owasp_llm

PRECONDITION: owasp_llm target descriptions have median length 0 chars
(audit confirmed). Forensic check FIRST:
1. Find which field actually holds OWASP LLM Top 10 text in the source data.
2. Either point the loader at it OR enrich per the s4 eu_gpai_cop pattern
   (see commit 02715f1 feat(s4): enrich eu_gpai_cop target descriptions).
3. Re-run the relevant baseline to confirm owasp_llm desc median > 0.

THEN scaffold mitre_atlas__owasp_llm (technique_to_risk function-match
mode). Anchors via sequential-thinking, rationale to
docs/session8_anchors_mitre_atlas__owasp_llm.md. Run pipeline. Report.

## T5 — nist_rmf to owasp_agentic

Scaffold nist_rmf__owasp_agentic (requirement_to_risk mode). Anchors via
sequential-thinking, rationale to
docs/session8_anchors_nist_rmf__owasp_agentic.md. Run pipeline. Report.

## T6 — merge new edges

Merge inferred edges from T2/T4/T5 into data/processed/edges.json. Run
python -m mapping_engine.scripts.validate_graph. Update graph_stats.json
if it exists. Report new edge count, framework pair coverage delta, and
orphan node delta.

## T8 — cross-pair CV

Run mapping_engine/scripts/cross_pair_validation.py (already exists from
the s8 commit eee3fc2) including the new pairs. Report per-pair accuracy,
average, and variance. Conclusion rule:
- variance > 20 percent — recommend per-pair weights
- variance < 10 percent — universal weights fine
- in between — defer

Save results to docs/session8_cross_pair_cv_with_new_pairs.md.

## T9 — active learning sheets

Generate active-learning labeling sheets for the three new pairs. Export
to mapping_engine/output/labeling_sheets/. Use the existing active
learning selector if one exists; if not, write a minimal one that emits
a CSV of (source_id, target_id, score, predicted_tier) for the
top-uncertainty K=50 candidates per pair.

## T10 — tests, commit, push

1. Run full pytest. If any test fails, STOP and surface.
2. git add only the files you intentionally created or modified.
3. Commit on branch session8-new-pairs.
4. CRITICAL COMMIT RULES (from /home/rock/.claude/CLAUDE.md):
   - NO Co-Authored-By trailer
   - NO mention of Claude, Anthropic, AI, Claude Code, or any AI tool
     anywhere in the commit message
   - Use the existing s0..s14 commit message style, e.g.
     feat(s8-np): csa_aicm to owasp_agentic pair
   - Prefer multiple small commits over one mega-commit
5. git push -u origin session8-new-pairs
6. Do NOT merge to main. Stop and report the branch name and commit list.

## Stop conditions (surface to user, do not retry blindly)

- pytest fails after one fix attempt
- anti-overfit gate fails twice on the same task
- anchor holdout fails after one threshold adjustment
- any instruction is ambiguous or a precondition is missing
- you are about to touch a frozen test
- you are about to commit something that mentions AI / Claude / Anthropic

When everything above is done and verified, output the completion promise
on its own line: <promise>S8_NEW_PAIRS_COMPLETE</promise>
