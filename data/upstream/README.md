# data/upstream/

## Purpose

This directory holds derived artifacts flattened from the pinned
GenAI-Data-Security-Initiative crosswalk snapshot under
`third_party/genai-crosswalk/`. The raw upstream JSON entries are never
edited. Everything here is regenerable from
`classifier/scripts/build_upstream.py` +
`classifier/scripts/run_contamination_audit.py`.

## Target id normalization (Plan 1-C)

Upstream `target_control_id` values are preserved verbatim in
`mappings_v1.jsonl`. A separate canonicalized `target_node_id`
(`"{framework}:{local_id}"`) is added alongside, together with a
`target_id_unresolved` boolean. Canonicalization rules live in
`classifier/data/upstream_id_normalize.py`.

### Category A — format mismatch, fixed here

- **eu_ai_act** — Upstream places a free-text obligation description in
  `control_id` and the article reference in `control_name`
  (e.g. `"Art. 9 — Risk management"`). The canonicalizer parses
  `control_name` with `^Art\.\s*(\d+)` and produces `Art{n}`. Sub-article
  annotations like `Art. 53(1)(a)` collapse to `Art53` — the sub-article
  text is preserved in the raw description field.
- **nist_rmf** — Upstream abbreviates the function prefix: `GV`, `MP`,
  `MS`, `MG`. nodes.json spells them out: `GOVERN`, `MAP`, `MEASURE`,
  `MANAGE`. The canonicalizer expands the prefix and keeps the rest
  (`GV-1.6` → `GOVERN-1.6`). Already-expanded values pass through.
- **aiuc_1** — Single-letter values `A..F` refer to AIUC domains
  (nodes.json has `domain_A..domain_F`). Values matching
  `[A-F]\d{3}(\.\d+)?` (e.g. `B005`, `A001.1`) are already valid control
  ids and pass through. Everything else (date strings, `"Primary DSGAI
  entries"`, comma-separated DSGAI id lists) is a non-control header row
  and stays unresolved.
- **mitre_atlas** — Identity passthrough. nodes.json contains both
  mitigations (`AML.M####`) and techniques (`AML.T####`). Two techniques
  (`AML.T0027`, `AML.T0045`) are absent from the pinned ATLAS snapshot
  and remain unresolved — fixing that requires re-ingesting ATLAS, which
  is out of scope for Plan 1-C.

### Category B — corpus-absent, intentionally unresolved

- **csa_aicm** — Upstream uses tier/level designators `L1..L7`. These
  are not control ids; the csa_aicm corpus has no matching nodes
  (controls are `A-A-01`, `AIS-01`, `LOG-01`, …). 61 in-scope rows stay
  unresolved by design.

### Pre- and post-fix in-scope resolution rates

Counted on the 413-row subset where both source and target framework are
in the 12-framework set and (src_fw, tgt_fw) is in the 26-pair matrix.

| target_framework | rows | before | after |
|---|---:|---:|---:|
| eu_ai_act   | 124 | 0/124 (0.000) | 124/124 (1.000) |
| nist_rmf    |  84 | 0/84  (0.000) | 84/84  (1.000) |
| aiuc_1      |  81 | 36/81 (0.444) | 72/81  (0.889) |
| mitre_atlas |  63 | 61/63 (0.968) | 61/63  (0.968) |
| csa_aicm    |  61 | 0/61  (0.000) | 0/61   (0.000) |
| **total**   | 413 | 97/413 (0.235) | 341/413 (0.826) |

Category A only (excluding csa_aicm): 341/352 = 0.969.

## Why not upstreamed

Per the project spec (Direction 3, consume-only), this repository does
not submit PRs to the upstream GenAI-Data-Security-Initiative crosswalk
at this stage. The canonicalization rules above are held locally until
they are validated by the classifier training pipeline and peer
reviewed. Upstream contribution remains on the Plan 7+ roadmap.

## Files

- `mappings_v1.jsonl` — one row per upstream mapping entry, with raw
  upstream fields preserved plus `target_node_id` /
  `target_id_unresolved` added.
- `crossrefs_v1.jsonl` — source-list crossrefs (LLM↔Agentic↔DSGAI).
- `partition.json` — strict contamination partition (Rules 1 + 2) over
  the full 3210-row mappings set.
- `contamination_report.json` — summary counts for `partition.json`.

## License

All files under `data/upstream/` are derived from the upstream
GenAI-Data-Security-Initiative crosswalk and are redistributed under
**CC BY-SA 4.0 ShareAlike** with attribution. See
`THIRD_PARTY_NOTICES.md` at the repo root for the full attribution text
and the upstream commit pin.

## Reproducibility

```
python -m classifier.scripts.build_upstream
python -m classifier.scripts.run_contamination_audit
python - <<'PY'
import hashlib, json
from pathlib import Path
h = json.loads(Path("data/splits/hashes.json").read_text())
for f in ["data/upstream/mappings_v1.jsonl",
          "data/upstream/crossrefs_v1.jsonl",
          "data/upstream/partition.json"]:
    want = h["upstream_v1"][f]
    got = hashlib.sha256(Path(f).read_bytes()).hexdigest()
    print(f, "OK" if want == got else f"MISMATCH {got}")
PY
```
