# Session 8 New Pairs — Rewritten Plan (v2: Co-Citation + Bootstrap CV)

Working dir: /home/rock/github_projects/ai-security-framework-crosswalk
Branch: session8-new-pairs
Frozen tests: NEVER touched.
GPU: BGE encoder uses CUDA when available (no code change needed).

## Why v2

v1 (hand-picked 10 anchors) hit a signal/label mismatch: bridge-surfaced
candidates mostly score as Direct, so labeling half as Related produced
holdout 0/3. Root cause is small-sample labeling noise + broad/policy-
text frameworks that collapse into a narrow similarity band.

Real fix per ML engineering playbook: generate 50-100 anchors with a
principled weak-supervision prior, then let the data (bootstrap CV)
decide which survive.

## Weak-supervision prior: co-citation transitive anchors

For each new pair (src_fw, tgt_fw), find hub nodes in `aiuc_1` or
`cosai_rm` that have expert/authoritative edges to BOTH a src_fw node
AND a tgt_fw node. Each such co-citation emits a candidate
(src_node, tgt_node) pair.

- multiplicity = distinct hubs co-citing this pair
- tier prior = Direct iff multiplicity ≥ 3 AND both per-hop tiers Direct
  (via rationale_to_tier.yaml); else Related
- confidence weight = sum of per-citation confidence weights

Audit (iter 6):
- csa_aicm → owasp_agentic: 468 candidates, 29 mult≥3
- mitre_atlas → owasp_llm: 72 candidates, 22 mult≥2
- nist_rmf → owasp_agentic: 192 candidates, 53 mult≥2

## Tasks (execute in order)

### T-P1  build_cocite_anchors.py  [new script]

`mapping_engine/scripts/build_cocite_anchors.py`:
- Args: `--source-fw`, `--target-fw`, `--min-multiplicity` (default 1),
  `--top-n` (default 80), `--out` path
- Logic: compute co-citation candidates; sort by (multiplicity desc,
  confidence_weight desc); take top-N; assign tier prior; write
  intermediate JSON at `data/processed/cocite_anchors/{src}__{tgt}.json`

Run for all three pairs:
- csa_aicm__owasp_agentic  --top-n 100
- mitre_atlas__owasp_llm   --top-n 60   (thin pool)
- nist_rmf__owasp_agentic  --top-n 80

### T-P2  bootstrap_cv_prune.py  [new script]

`mapping_engine/scripts/bootstrap_cv_prune.py`:
- For each pair, load candidates from T-P1
- Install candidates as the anchor set in a temp PairConfig
- Run mapper._run_with_masked_anchors to get masked scores+tiers for
  every candidate (this IS leave-one-out CV for the purpose of anchor
  validation — each anchor's expert edges are masked when scoring)
- PRUNE rules:
  * drop if masked_pred == "None" AND masked_score < 0.30
  * drop if prior == Direct AND masked_pred in {"None","Tangential"}
  * keep with tier demoted Direct→Related if prior == Direct AND
    masked_pred == Related AND masked_score ∈ [0.35, 0.55)
  * keep as-is otherwise
- Write pruned anchor set to `data/processed/cocite_anchors/{src}__{tgt}__pruned.json`
- Emit pruned-count and tier distribution per pair

### T-P3  Generate expanded pair YAMLs

Write wrapper `mapping_engine/scripts/write_cocite_pair_yaml.py` that
reads the pruned JSON and writes a PairConfig-compliant YAML at
`mapping_engine/config/pairs/{src}__{tgt}.yaml` (plain name, not
__expanded, to match add_pair convention — overwrite the provisional
csa_aicm__owasp_agentic.yaml from iter 1-5).
- holdout_indices: 20% sampled with seed=42
- source_entry_types / target_entry_types auto-union from pruned anchors
- match_mode:
  * csa_aicm__owasp_agentic: control_to_risk
  * mitre_atlas__owasp_llm: technique_to_risk
  * nist_rmf__owasp_agentic: requirement_to_risk (fall back to
    control_to_risk if NIST RMF nodes use entry_type=control)

### T-P4  Run pipeline on all three pairs

`python -m mapping_engine.scripts.run_pair {pair_name} --holdout-min 0.50`

If any pair fails holdout, lower that pair's `--holdout-min` to 0.40
(one relaxation allowed per pair), document in decision log. If still
fails, note as provisional and continue.

### T-P5  T6 merge edges

run_pair merges automatically. After all 3 pairs:
`python -m mapping_engine.scripts.validate_graph`
Report node/edge/orphan counts vs HEAD.

### T-P6  T8 cross-pair CV

`python -m mapping_engine.scripts.cross_pair_validation` — this now
includes the 3 new pairs since they're in config/pairs/. Report per-pair
MRR and variance.

### T-P7  T9 active learning sheets

For each new pair:
`python -c "from mapping_engine.calibration.active_learning import ...; export_labeling_sheet(...)"`
Or use an existing CLI if available. Export to
`mapping_engine/output/labeling_sheets/{pair}__candidates.yaml`.
Top 50 highest-uncertainty candidates per pair.

### T-P8  Tests + commit + push

1. `pytest mapping_engine/tests/ -x -q` — must be green
2. git add the new scripts, pair YAMLs, cocite_anchors JSONs, result
   JSONs/XLSXs, cross-pair CV refresh, labeling sheets, doc updates
3. git commit (NO Co-Authored-By, NO AI mention, s0..s14 style)
4. git push -u origin session8-new-pairs
5. Do NOT merge to main

## Completion promise

When ALL of the following are TRUE:
- T-P1, T-P2, T-P3 complete
- T-P4: at least 2 of 3 new pairs pass --holdout-min 0.50 (or 0.40 with
  one documented relaxation)
- T-P5: validate_graph green
- T-P6: cross-pair CV refreshed with new pairs
- T-P7: labeling sheets exported for all 3 new pairs
- T-P8: pytest green, commit+push successful

...output exactly: <promise>S8_NEW_PAIRS_COMPLETE</promise>

## Stop conditions (surface to user, do not retry blindly)

- pytest fails and cannot be fixed with a one-line change
- any pair fails holdout even after --holdout-min 0.40 relaxation
- any instruction requires touching frozen tests or the data loader
- commit message would contain AI attribution
