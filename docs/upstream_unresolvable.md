# Upstream rows structurally unresolvable to our graph

This file is cited by Plan 8's upstream-acknowledgement and limitations
sections. It lists the subsets of `data/upstream/mappings_v1.jsonl` that
cannot be resolved to `data/nodes/nodes.json` node ids even after Plan 1-C's
per-framework canonicalization. These rows are excluded from both training
and the `upstream_heldout` benchmark.

## Summary

Plan 1-C resolution raised in-scope resolution from 23.5% → 82.6% overall
(97/413 → 341/413). Remaining unresolved rows fall into two categories:

### Category A — Our bug (fixable in a future plan)

None currently outstanding. All Category A rows were fixed by Plan 1-C's
per-framework canonicalizers.

### Category B — Semantic mismatch (legitimately unresolvable)

| Framework | Row count | Reason | Paper treatment |
|---|---:|---|---|
| `csa_aicm` | 61 | Upstream target_control_id uses CSA AICM tier levels (`L1..L7`) rather than control IDs. Our graph only contains control-level nodes (`I-S-01`, etc.), not tier nodes. The relationship upstream encodes is "this external control applies at CSA tier N" — that is a control↔tier relation, not a control↔control relation. | Excluded from training and `upstream_heldout`. Reported in `limitations.tex` subsection 4 as a known ontology gap. A future spec amendment could add tier-level nodes to our graph and ingest these rows, but that is out of scope for the 2026-04-08 release. |

### Category C — Upstream data quality (report and skip)

Rows dropped because `target_control_id` is null, empty, or a malformed
string after canonicalization. Counts written automatically by
`classifier/data/upstream_loader.py` into
`data/upstream/resolution_report.json` on every build.

## Impact on metrics

Excluding the 61 csa_aicm Category B rows reduces upstream's `csa_aicm`
target coverage from X% to Y% (where X and Y are filled in at sacred-run
time from `results.json`). The `upstream_heldout` benchmark is therefore
not a full test of csa_aicm mapping; pair with `frozen_test` + `crossref`
for any claims about csa_aicm performance.

## Reproducibility

Run `python -m classifier.data.upstream_loader --report-unresolved` to
regenerate the resolution report. The row counts in this file should match
the current report or be updated via a follow-up PR.
