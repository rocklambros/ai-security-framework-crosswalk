# Upstream rows structurally unresolvable to our graph

This file is cited by Plan 8's upstream-acknowledgement and limitations
sections. It lists the subsets of `data/upstream/mappings_v1.jsonl` that
cannot be resolved to `data/nodes/nodes.json` node ids even after Plan 1-C's
per-framework canonicalization. These rows are excluded from both training
and the `upstream_heldout` benchmark.

## Summary

Plan 1-C resolution raised in-scope resolution from 23.5% → 82.6% overall
(97/413 → 341/413). Plan 1-D added MITRE ATLAS aliases (AML.T0022→T0012,
AML.T0032→T0020), resolving 4 more rows (542→546 total resolved).
Remaining unresolved rows fall into three categories:

### Category A — Our bug (fixable in a future plan)

| Framework | Row count | Reason | Fix |
|---|---:|---|---|
| `mitre_atlas` | 6 | 3 ATLAS technique IDs (AML.T0027 Model Inversion, AML.T0030 Information Disclosure, AML.T0045 Disinformation) absent from our ATLAS snapshot (`data/frameworks/mitre-atlas/ATLAS_compiled.json`). Likely deprecated or from a different ATLAS version than our 2026-04-05 snapshot. | Update ATLAS snapshot to include these IDs, or map to semantic equivalents if they exist in a newer ATLAS release. |

### Category B — Semantic mismatch (legitimately unresolvable)

| Framework | Row count | Reason | Paper treatment |
|---|---:|---|---|
| `maestro` | 120 | OWASP MAESTRO uses tier-level IDs (`L1..L7`) rather than individual control IDs. These were previously misattributed to `csa_aicm` (the Plan 1-A loader mapped `"MAESTRO"` → `"csa_aicm"`; corrected in Plan 1-D to `"maestro"`). MAESTRO is a separate framework; CSA AICM now has zero unresolved rows. | Excluded from training. Reported in `limitations.tex` as a known ontology gap. These rows become resolvable when Plan 4 adds MAESTRO node registries. |

### Category B2 — New frameworks without node registries (Plan 4 expansion)

2,538 rows target 18 frameworks we don't yet have node registries for.
These are structurally valid mappings from the GenAI-Data-Security-Initiative
crosswalk but cannot resolve because our graph has no nodes for these
frameworks. Plan 4 framework expansion will add node registries to unlock
them — a potential ~6x increase in training data.

| Framework | Unresolved rows |
|---|---:|
| OWASP SAMM v2.0 | 187 |
| SOC 2 | 168 |
| ISO/IEC 27001:2022 | 167 |
| PCI DSS v4.0 | 166 |
| ISO/IEC 42001:2023 | 164 |
| NIST CSF 2.0 | 164 |
| ENISA Multilayer Framework | 164 |
| NIST SP 800-82 Rev 3 | 154 |
| OWASP ASVS 4.0.3 | 151 |
| FedRAMP | 147 |
| DORA | 147 |
| ISA/IEC 62443 | 144 |
| CIS Controls v8.1 | 138 |
| NIST SP 800-218A | 136 |
| CWE/CVE | 130 |
| OWASP NHI Top 10 | 120 |
| OWASP AI Testing Guide | 60 |
| STRIDE | 22 |

Each requires: a `data/frameworks/<fw>/nodes.json` with control IDs, names,
descriptions; embeddings; and an entry in `TARGET_FRAMEWORK_TABLE` in the
upstream loader. See Plan 4 spec for the framework expansion task.

### Category C — Upstream data quality (report and skip)

Rows dropped because `target_control_id` is null, empty, or a malformed
string after canonicalization. Counts written automatically by
`classifier/data/upstream_loader.py` into
`data/upstream/resolution_report.json` on every build.

## Impact on metrics

Excluding the 120 `maestro` Category B rows (previously misattributed to
`csa_aicm`) does not affect `csa_aicm` coverage — that framework now has
zero unresolved rows. The 6 `mitre_atlas` Category A rows and 2,538
Category B2 rows are the remaining gaps; see those sections for details.

## Reproducibility

Run `python -m classifier.data.upstream_loader --report-unresolved` to
regenerate the resolution report. The row counts in this file should match
the current report or be updated via a follow-up PR.
