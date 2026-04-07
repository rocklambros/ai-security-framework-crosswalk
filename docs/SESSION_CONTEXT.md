# Session Context: AI Security Framework Crosswalk

Last updated: April 7, 2026

## Session 11 Status Snapshot (current)

**Project 1: COMPLETE.** Notebook executed cleanly, zipped, pushed. Deliverable lives at `notebooks/project1_lambros.zip` (15 files, ~5.49 MB). Sections cover framework landscape, signal analysis, learned-vs-hand-tuned weights with three-curve ROC, coverage/gaps, v1-vs-v2 expert diff, and analytical next steps. Meets all COMP 4433 requirements (gridspec multipanel, 3+ plot types, on-plot annotations, narrative throughout).

**Project 2: NOT STARTED.** Design direction below.

### Shipped work (sessions 1–11)

1. Graph: 983 nodes, 1883 edges, 9 frameworks.
2. Mapping engine: pair-agnostic, 4 content signals (bridge, semantic, keyword, function_match) + composite blend with calibrated thresholds 0.45 / 0.20 / 0.10.
3. Semantic signal: sentence-transformers with per-pair Z-normalization. Fine-tune benchmark evaluated and base model kept.
4. Learned weights: logistic regression + LightGBM both evaluated against hand-tuned. Production keeps hand-tuned (bridge 0.467, semantic 0.333, keyword 0.200, function_match multiplicative) because the logistic model trades false-positive rate for a marginal true-positive gain that doesn't clear the operational bar. Coefficients archived in `data/processed/learned_weights.json` for the notebook ROC.
5. Graph bridge: 2-hop weighted Jaccard via NetworkX replaces the OWASP-LLM-specific bridge from v1. Coverage improved, v2 value visible in `bridge_comparison.csv`.
6. Cross-encoder reranking: ms-marco-MiniLM and BAAI/bge-reranker-v2-m3 evaluated on 550 SME labels (session 9 phase D). Both rejected for global adoption per non-inferiority rule.
7. Node2Vec: committed as opt-in with production weight 0.0. Bridge already captures the structural signal.
8. Contrastive fine-tuning: base model retained.
9. Active learning (session 7–9): 550 SME labels across 4 pair sheets (400 S7 + 150 S8), frozen as parity targets in `test_s9_s8_parity.py` (csa_aicm 0.22, mitre_atlas 0.20, nist_rmf 0.30).
10. Pipeline runs: 4 pairs mapped (`aiuc_1__owasp_agentic`, `csa_aicm__owasp_agentic`, `mitre_atlas__owasp_llm`, `nist_rmf__owasp_agentic`) plus exploratory sheets for 7 more pairs.
11. Cross-pair CV: see `data/processed/session8_cross_pair_validation.json`. Per-pair thresholds kept after CI gates failed for per-pair weights.
12. LambdaMART (session 9 phase E): rejected per overfit gate (delta < +0.02 on held-out pool).
13. v1 vs v2 diff (session 11): 119 expert AIUC→ASI pairs compared against the 109 v2 production pairs. 57 preserved (47.9%), 62 lost, 52 new, 0 tier flips among preserved. Flagged as regression by the 5% rule; the lost set is the next active-learning queue. Full report at `data/processed/V1_VS_V2_COMPARISON_REPORT.md`.

### Current graph state

- Nodes: 983 across 9 frameworks (AIUC-1 and CSA AICM dominate).
- Edges: 1883 (mix of intra-framework parent/child and cross-framework inferred mappings).
- Orphans: concentrated in NIST AI RMF and OWASP AI Exchange (see Figure 6.2 of the notebook).
- Cross-framework coverage: AIUC-1 row is dense; NIST/OWASP rows are empty because those frameworks act as targets only in the current pipeline.

### Library stack (approved)

numpy, pandas, matplotlib, seaborn, statsmodels, scikit-learn, networkx, sentence-transformers, lightgbm. For Project 2: plotly, dash (already in `requirements.txt`).

### Project 2 design direction (pick up next)

- Interactive crosswalk explorer: source-framework + target-framework selectors, mapping table, signal breakdown panel.
- Network view: Plotly network visualization filtered by framework pair with hover on nodes showing description + function class.
- Sankey: flow from source controls to target risks, width by composite score.
- Heatmap: domain × domain mapping density.
- Gap view: orphan controls and thin-coverage risks surfaced from the v1-vs-v2 lost set.
- Active-learning queue: surface `needs_review=true` pairs for SME triage.
- Deployment: Render or Railway (local-run fallback is fine). GitHub repo with requirements.txt + Procfile.

### Key decisions pending for Project 2

- Layout: tabs vs sidebar. Leaning tabs for separation of concerns.
- Include signal-decomposition view? Probably yes, it is the most unique affordance the project has.
- Color/theme: match the paper-context seaborn palette from Project 1 for visual continuity.

---


## Project Overview

Two-phase graduate project for COMP 4433 Data Visualization (DU, Spring 2026) that also produces a reusable community artifact for the AI security standards ecosystem.

- **Project 1 (midterm, 30%):** Exploratory visual analysis of the crosswalk graph using matplotlib/seaborn. Scientific audience. Notebook deliverable.
- **Project 2 (final, 30%):** Interactive Dash app for navigating cross-framework mappings. User-facing, deployment-ready. GitHub repo deliverable.

Both projects share the same underlying dataset: a graph of nodes (controls, risks, techniques, requirements) and edges (mapping relationships) across 10 AI security frameworks.

## Library Stack

Core (COMP 4433 approved): numpy, pandas, matplotlib, seaborn, statsmodels, sklearn

Extended (requires instructor approval): networkx, sentence-transformers, lightgbm

All ML/graph computation runs in `mapping_engine/` preprocessing scripts. The Project 1 notebook loads pre-computed results and visualizes with matplotlib/seaborn only. See `docs/IMPROVEMENT_PLAN.md` for the full ML enhancement roadmap.

## Repositories

### rocklambros/ai-security-framework-crosswalk (private)

The main project repo. Contains:

- `data/frameworks/` -- Source data for 10 frameworks (JSON, YAML, markdown)
  - `aiuc-1/` -- AIUC-1 standard JSON (51 controls, 6 domains) + Agentic Top 10 mapping v2 JSON (119 expert mappings) + 5 markdown crosswalks
  - `cosai/` -- CoSAI Risk Map YAML (risks, controls, frameworks, components)
  - `mitre-atlas/` -- ATLAS YAML/JSON (tactics, techniques, mitigations)
  - `csa-aicm/` -- CSA AICM JSON (243 controls, 18 domains)
  - `owasp-llm-top10/` -- OWASP LLM Top 10 2025 markdown
  - `owasp-agentic-top10/` -- OWASP Agentic Top 10 2026 markdown
  - `nist-ai-rmf/` -- NIST AI RMF 1.0 markdown
  - `nist-ai-600-1/` -- NIST AI 600-1 markdown
  - `eu-gpai-code-of-practice/` -- EU GPAI Code of Practice (3 chapter markdowns)
  - `owasp-ai-exchange/` -- OWASP AI Exchange markdown
- `schema/` -- Unified graph schema v1.0
  - `node.schema.json` -- Vertex schema (any framework entry)
  - `edge.schema.json` -- Edge schema (any mapping relationship)
  - `README.md` -- Design rationale, loading code, visualization mapping
- `schema_template/` -- v2 pairwise crosswalk schema (from the AIUC-1 mapping project)
  - `crosswalk-mapping-v2.schema.json` -- Validates individual pairwise crosswalk files
  - `README.md` -- Rationale taxonomy docs
- `data/processed/` -- Build output (nodes.json, edges.json, graph_stats.json)
- `mapping_engine/` -- Pair-agnostic mapping pipeline (see IMPROVEMENT_PLAN.md)
- `scripts/` -- Build and conversion scripts
- `notebooks/` -- EDA notebook (Project 1)
- `app/` -- Dash app (Project 2)
- `docs/` -- SESSION_CONTEXT.md, IMPROVEMENT_PLAN.md

### rocklambros/AIUC_2_OWASP_Agentic_Top_10 (private)

The v1 mapping engine repo. Contains the multi-signal hybrid pipeline that produced the AIUC-1 to OWASP Agentic Top 10 crosswalk. Preserved as a documented artifact. Key modules:

- `aiuc/signals.py` -- 3 content signals (reference bridge, semantic, TF-IDF keyword) + multiplicative function match boost
- `aiuc/taxonomy.py` -- 8-code rationale taxonomy, function classification, threat function profiles, relevance rules
- `aiuc/mapper.py` -- Mapping orchestrator with anchor pair validation
- `aiuc/models.py` -- Pydantic schemas for v1 + v2 crosswalk output
- `aiuc/output.py` -- Excel (5-sheet) + JSON generation
- `schemas/crosswalk-mapping-v2.schema.json` -- Output validation schema

## Current State

### Completed

1. Repo created with full directory structure and README
2. All 10 framework source data files ingested (JSON, YAML, markdown)
3. Unified graph schema v1.0 designed and pushed (node.schema.json, edge.schema.json)
4. Schema gap analysis completed: v2 pairwise schema evaluated against actual data
5. Graph build prompt written and submitted to Claude Code
6. Pair-agnostic mapping engine architecture designed
7. ML improvement plan created with 4 phases, 8 concrete enhancements (docs/IMPROVEMENT_PLAN.md)

### Blocked

- `scripts/build_graph.py` status unknown. `data/processed/` is empty as of April 6. Need to check Claude Code session or rebuild.

### Next Steps (in order)

1. **Unblock graph build.** Check Claude Code session. If failed, rebuild build_graph.py and run.
2. **Implement Phase 1.3** (graph bridge via 2-hop weighted Jaccard in networkx)
3. **Implement Phase 1.1** (upgrade embedding model to bge-large-en-v1.5)
4. **Run baseline comparison** on AIUC-1 to OWASP Agentic: v1 pipeline vs Phase 1 upgrades
5. **Implement Phase 1.2** (learned signal weights via logistic regression / LightGBM)
6. **Run first new pair:** CSA AICM to OWASP Agentic (243 controls, stress test)
7. **Implement Phase 2** (cross-encoder reranking + active learning)
8. **Build Project 1 notebook** visualizing each improvement phase with matplotlib/seaborn
9. **Phase 3-4** deferred to Project 2 timeline or post-course

## Mapping Engine Architecture

```
mapping_engine/
├── __init__.py
├── config/
│   ├── defaults.yaml                # Default weights, thresholds, models
│   ├── synonyms.yaml                # Shared synonym groups
│   ├── function_profiles.yaml       # Per-framework function class assignments
│   └── pairs/                       # Per-pair YAML configs
│       ├── aiuc_1__owasp_agentic.yaml
│       ├── csa_aicm__owasp_agentic.yaml
│       └── ...
├── engine/
│   ├── graph.py                     # Load graph into NetworkX
│   ├── bridge.py                    # 2-hop weighted Jaccard (Signal 1)
│   ├── semantic.py                  # sentence-transformers + Z-score (Signal 2)
│   ├── keyword.py                   # TF-IDF with synonym expansion (Signal 3)
│   ├── function_match.py            # 3-mode boost (Signal 4)
│   ├── reranker.py                  # Cross-encoder second stage
│   ├── contrastive.py               # Negative signal detection
│   ├── composer.py                  # Weighted composite + tier assignment
│   ├── taxonomy.py                  # Rationale classification
│   └── mapper.py                    # Orchestrator
├── calibration/
│   ├── anchor_validation.py         # Holdout accuracy
│   ├── weight_stability.py          # +/-15% perturbation
│   ├── weight_learner.py            # Logistic regression / LightGBM
│   └── cross_pair_cv.py             # Leave-one-pair-out CV
├── scripts/
│   ├── run_pair.py
│   ├── run_all.py
│   ├── add_pair.py
│   └── validate_graph.py
├── output/
│   ├── json_writer.py
│   ├── excel_writer.py
│   └── graph_writer.py
└── tests/
```

## Anti-Overfitting Gates

Every `run_pair.py` execution reports:
1. Anchor holdout accuracy (3 held-out anchors, pass if all hit expected tier)
2. Weight stability (perturb each weight +/-15%, report % of mappings that change tier, fail if >20%)
3. Mapping density check (flag if >2x or <0.3x density of validated pairs)

## Function Match Modes

1. control-to-risk: control's function_class in threat's function_profile. Boost 1.5x. (existing)
2. control-to-control: same class = 1.3x, complementary (PREV/DETECT, SCOPE/ISOLATE) = 1.15x.
3. technique-to-risk: tactic-to-risk lookup table. Boost 1.3x.

Auto-detected from entry_type of source and target nodes.

## Course Requirements Reference

### Project 1 (matplotlib/seaborn EDA)

- At least one figure with multiple plots and differentially sized axes
- At least three different plot types
- At least one on-plot annotation
- Narrative explanation of each plot
- Discussion of anomalies, trends, observations
- Considerations for analytical approaches
- Deliverable: zipped notebook + data files

### Project 2 (Plotly/Dash app)

- At least 4 Dash Core Components
- At least 1 callback decorator
- At least 3 different Plotly chart types
- Narrative/instructional info for user navigation
- Deployment-ready GitHub repo
- Explanatory purpose

## Key Technical Decisions

- Graph data model over pairwise crosswalk files. NetworkX in-memory, serialized as nodes.json + edges.json.
- EU GPAI Code of Practice over EU AI Act directly. Discrete mappable commitments.
- OWASP COMPASS dropped. Methodology tool, not a control framework.
- CSA AICM xlsx gitignored. License restriction. Derived JSON is fine.
- Confidence gradient on edges: authoritative > expert > inferred > unvalidated.
- AIUC_2_OWASP repo preserved as v1 artifact. All new work in crosswalk repo mapping_engine/.
