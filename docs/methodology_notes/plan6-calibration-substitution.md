# Plan 6 calibration substitution (2026-04-08)

## What changed

Per `docs/superpowers/specs/2026-04-08-upstream-crosswalk-integration-design.md`
section 2 decision D7 and section 7 Plan 6, the fresh human-SME calibration labeling block
that appeared in the 2026-04-07 Plan 6 Phase C has been removed. The 150-row
`data/splits/human_cal.jsonl` calibration set was created during Plan 1 from the
expert-labeled SME pool, stratified across framework pairs.

## Tier mapping

The calibration set uses `expert_tier` labels from the SME pool:

| expert_tier | numeric | ensemble tier |
|-------------|---------|---------------|
| Direct      | 3       | equivalent    |
| Related     | 2       | related       |
| Tangential  | 1       | partial       |
| None        | 0       | unrelated     |

Distribution: Direct=23, Related=62, Tangential=28, None=37 (total=150).

## Provenance

- **Source:** Plan 1 SME pool (`data/splits/sme_pool_full.jsonl`)
- **Stratification:** Round-robin over framework pairs (11 pairs represented)
- **Hash pin:** `data/splits/hashes.json["human_cal.jsonl"]`
- **Row count:** exactly 150

## What did NOT change

- `data/splits/human_test_frozen.jsonl` is untouched (byte-identical to its SHA pin)
- `data/splits/hashes.json` is unchanged by Plan 6
- The sacred run, ablations, and statistical tests are unchanged
- Pre-registered thresholds and the one-shot lockfile are unchanged

## For Plan 8

Plan 8 must:
- Cite this file in the paper methodology section
- Add a footnote to Tables 1 and 4 clarifying calibration source
