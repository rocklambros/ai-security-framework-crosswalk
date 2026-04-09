# Orchestrator runbook (committed)

`prompts/phase-0-meta.md` is the *invocation surface* — it's edited per
session and is gitignored. The **durable orchestration rules** live here,
in this committed file, so session turnover and context compression cannot
lose them.

A phase orchestrator MUST read this file at session start and obey it.

---

## Honesty firewall pre-gate (Plan 1-D, mandatory before any phase runs)

Before executing **any** phase ≥ 2, the orchestrator MUST verify:

1. `data/splits/frozen_tuples.json` exists and matches its SHA in
   `data/splits/hashes.json["splits"]["frozen_tuples_json"]["sha256"]`. If
   missing or mismatched, run `python3 scripts/build_frozen_tuples.py` on a
   hotfix branch and halt the phase until merged.

2. `pytest classifier/tests/contract_no_frozen_leak.py classifier/tests/test_pre_registered_lockfile.py -x -q`
   is green against the current branch head. The first test is
   informative-not-load-bearing — it catches producer-level drift early.
   The load-bearing check is `iter_weighted_rows` Contract 10 layer 0 in
   `classifier/ensemble/training_batches.py`. Both must pass in every
   phase's CI.

3. `classifier/sacred/pre_registered.json` exists and matches the committed
   SHA in `data/splits/hashes.json["pre_registered"]["sha256"]`. Plan 6
   runtime reads α, abstention precision, seeds, and all §6 constants from
   this file via `classifier.sacred.pre_registered.load()`; a mismatch
   aborts the sacred run.

4. `make verify-firewall` passes on a clean checkout. The Makefile target
   (installed by Plan 1-D) re-runs `scripts/build_frozen_tuples.py` in a
   tmp directory and diffs against the committed artifact, then runs the
   three firewall contract tests above.

These four checks are independent of, and mandatory in addition to, the
per-phase verification gates.

---

## Go/no-go checkpoint after Plan 5

After Plan 5 merges, evaluate the `EnsembleScorer` on `llm_val` via the
Plan 3 harness and inspect `runs/registry.jsonl` for the ensemble-assembly
run's R@1. If **R@1 < 0.30 on `llm_val`**, halt the loop and report to the
user before starting Phase 6.

Rationale: Phase 6 spends ~3 human hours on fresh-75 labeling and fires
the one-shot sacred run. If the ensemble cannot clear a reasonable bar on
the non-frozen validation set, those costs will produce a weak publication
at best and a retraction risk at worst. The user can then decide to (a)
iterate Plan 4/5 on a new branch, (b) lower the publication ambition and
proceed, or (c) pause the project.

Do NOT auto-proceed past this checkpoint; it requires explicit user
acknowledgement in a reply.

---

## Subagent review discipline (META — Plan 1-D)

Never commit a multi-plan rewrite without an integration review of every
output. When dispatching parallel subagents to rewrite coupled plans, the
orchestrator MUST:

1. Read each subagent's output end-to-end before commit.
2. Run the cross-phase `contract_no_frozen_leak.py` test against every new
   producer adapter registered in the output.
3. Grep the new plan text for any of: `human_test_frozen`, `frozen_tuples`,
   `Contract 10`, `Contract 15`, `pre_registered`, and verify each
   reference is structurally consistent with the other plans' usage.
4. Verify spec §6 numeric thresholds are read from `pre_registered.json`,
   not hardcoded as Python literals.
5. Dispatch a spec-compliance reviewer subagent BEFORE commit, not after.

A green CI against subagent-written tests is NOT proof of correctness —
the same subagent wrote the test and the code. Integration contracts live
above the subagent's scope and must be orchestrator-authored.

---

## Halting conditions (report and stop)

- 5 failed repair attempts on any phase.
- A pre-flight check fails in a way the orchestrator cannot safely fix.
- Any honesty-commitment contract test fails — these are pre-registered;
  do not "fix" them — report.
- Any of the four firewall pre-gate checks above fails.
- Plan 5 go/no-go checkpoint yields R@1 < 0.30 on `llm_val`.
