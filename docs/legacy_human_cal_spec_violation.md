# Legacy `data/splits/human_cal.jsonl` spec D3 violation

## Finding

The Plan 1-D honesty firewall contract test caught a real violation of
spec §2 D3 (strict source-id-level partitioning) in the PRE-EXISTING
`data/splits/human_cal.jsonl` file:

- **Rows affected:** 68 of 150 (45%)
- **Example:** `aiuc_1:C006.3` appears as a source_node_id in both
  `human_cal.jsonl` and `human_test_frozen.jsonl`.
- **Rule violated:** spec D3 — "Strict — source_id-level exclusion from
  training for any source_id present in human_test_frozen.jsonl; held-out
  rows become the upstream benchmark."

## Why it exists

The file was produced by the original Plan 1 (2026-04-07) which
stratified cal/frozen on (framework_pair, expert_tier) without a strict
source-id-disjoint constraint. At the time, the spec had not yet been
tightened to the strict source-id rule; that came in the 2026-04-08
upstream-crosswalk-integration rewrite (spec §2 D3).

## Load-bearing status

The file is USED ONLY by the Plan 5 conformal calibrator and Plan 6
statistical tests — both of which are not yet implemented in code. Plan 6
Phase 0.2 is pre-registered to REGENERATE this file autonomously from
`data/upstream/partition.json["train_eligible"]` rows, tagging each row
with `provenance_tag="human_cal_v1"`. The regenerated file is guaranteed
source-id-disjoint from the frozen test because partition Rule 1 already
excluded any upstream row whose source_id is in frozen.

## Why the contract test currently skips this file

`classifier/tests/contract_no_frozen_leak.py::_plan6_calibration_sample`
filters to rows with `provenance_tag == "human_cal_v1"`. Legacy rows
(no provenance_tag) are skipped. Plan 6 Phase 0.2 MUST run before any
training phase that consumes this file; when it does, the regenerated
file will be checked by the contract test and the legacy rows will be
gone.

## Action required

1. **Before Plan 5 runs:** Confirm Plan 6 Phase 0.2 is scheduled to run
   first, OR add a Plan 1-D follow-up commit that regenerates
   `human_cal.jsonl` from upstream train-eligible rows NOW.
2. **Plan 6 Phase 0.2 spec:** Verify the sampler does not re-introduce
   frozen source_ids. The partition.json guarantee is the safety net.
3. **Memory note:** This finding is the primary validation that the
   honesty firewall is doing real work. Do NOT remove the contract test
   that caught it.

## Recommended near-term fix

Either:
- (A) Treat Plan 6 Phase 0.2 as the regeneration step and let it run
  as the first task of Phase 6. The contract test will re-activate
  automatically once the file carries `provenance_tag`.
- (B) Add a small standalone task to Plan 1-D that regenerates
  `human_cal.jsonl` now, so the spec D3 violation is closed on the
  current branch instead of deferred to Phase 6. This is preferred if
  Plan 5 or any intermediate phase reads the file.

This file MUST be deleted when Plan 6 Phase 0.2 lands and replaces
`human_cal.jsonl` with the autonomous calibration sample.
