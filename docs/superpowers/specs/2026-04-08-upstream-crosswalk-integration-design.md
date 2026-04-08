# Upstream Crosswalk Integration — Design Spec

**Date:** 2026-04-08
**Status:** Approved (brainstorm → spec)
**Supersedes / amends:** `2026-04-07-ai-security-crosswalk-classifier-design.md` for all sections touching data sources, scope, and Plan 6 human evaluation.
**Relationship to plans:** This spec is a pre-`writing-plans` design. Implementation plans (Plans 1–8) are updated in a follow-on step using `superpowers:writing-plans`.

## 1. Motivation

The GenAI Security Project's
[GenAI-Data-Security-Initiative/crosswalk](https://github.com/GenAI-Security-Project/GenAI-Data-Security-Initiative/tree/main/crosswalk)
publishes **41 hand-curated JSON entries** (10 OWASP LLM Top 10 + 10 OWASP Agentic Top 10 + 21 OWASP DSGAI 2026), each carrying ~45 human-curated cross-framework mappings — roughly **1,800 gold (source → target) labels** across ~20 target frameworks, plus a `crossrefs` field that provides free LLM↔Agentic↔DSGAI gold edges. The repository is licensed CC BY-SA 4.0.

Our project currently covers 2 source lists × 9 frameworks with a 550-row LLM-SME-labeled pool, a 150/400 calibration / frozen-test split (SHA-pinned, pre-registered), and eight sessions of bridge / node2vec / reranker iteration. Integrating upstream gives us:

- Gold labels that dwarf our silver LLM-SME pool on overlapping source lists
- Free gold cross-source-list edges (a weak spot in Sessions 6–8)
- A third source list (DSGAI)
- An aligned schema with a merge/contribution pathway for later
- A rich second benchmark that is independent of our pre-registered frozen test

## 2. Decisions (locked)

| ID | Decision | Choice | Rationale |
|---|---|---|---|
| D1 | Scope ambition | **Tier B** (aligned) — 3 source lists, current 9 targets + 3–5 new ones | Best value/effort ratio; keeps Tier C (full merge) reachable without rework |
| D2 | Merge direction | **Direction 3 (consume-only)** — upstream pinned read-only; no writes upstream; no PRs yet | Zero social coupling; full unilateral control; contribution pathway stays open |
| D3 | Contamination posture | **Strict** — `source_id`-level exclusion from training for any `source_id` present in `human_test_frozen.jsonl`; held-out rows become the upstream benchmark | Only defensible option given pre-registered thresholds |
| D4 | Schema adoption | **Deferred** — keep internal schema; build upstream-format adapter later if/when we contribute | Avoids Plan 1 rework; adapter is cheap to add once classifier is proven |
| D5 | DSGAI inclusion | **First-class 3rd source list** | User-approved Tier B expansion; corpus already downloaded |
| D6 | DSGAI corpus source | **Published OWASP DSGAI 2026 markdown** (not upstream JSON metadata) | Upstream JSON entries have no long-form descriptive text; embeddings need the real prose |
| D7 | Plan 6 human SME block | **Replaced** by upstream labels — Plan 6 Phase C halt removed | Orchestrator becomes fully autonomous; paper accepts the methodology trade-off |

## 3. Architecture

Three roles, three filesystem locations, strict separation:

```
data/frameworks/owasp-dsgai/
    OWASP-GenAI-Data-Security-Risks-and-Mitigations-2026-v1.0.md   ← SOURCE CORPUS
                                                                    (published OWASP markdown,
                                                                     embedded by pipeline)

third_party/genai-crosswalk/
    MANIFEST.json                                                   ← PINNED READ-ONLY DEP
    crosswalk/data/entries/*.json                                   (upstream JSON, never edited
                                                                     in place, SHA-pinned)

data/upstream/
    mappings_v1.jsonl                                               ← DERIVED ARTIFACTS
    crossrefs_v1.jsonl                                              (flattened, normalized,
    contamination_report.json                                        provenance-tagged)
    partition.json
    hashes.json
```

Invariant: upstream JSON is **never** copied into `data/frameworks/`. Corpus files and label files live in separate trees so provenance cannot be confused.

## 4. Components

### 4.1 Upstream vendor (pinned read-only dependency)

- **Location:** `third_party/genai-crosswalk/`
- **Contents:** snapshot of `crosswalk/data/entries/*.json`, `crosswalk/data/schema.json`, and `LICENSE` at a pinned commit SHA.
- **`MANIFEST.json` fields:** `upstream_repo`, `upstream_commit_sha`, `retrieved_at` (ISO-8601), `license` (`CC-BY-SA-4.0`), `attribution` (text block required by the license), `entry_count`.
- **Update policy:** updates happen only by bumping the pinned SHA and re-running the loader + contamination auditor. Never ad-hoc edited.

### 4.2 DSGAI framework ingester

- **Module:** `classifier/data/frameworks/dsgai.py`
- **Input:** `data/frameworks/owasp-dsgai/OWASP-GenAI-Data-Security-Risks-and-Mitigations-2026-v1.0.md` (CC BY-SA 4.0, 5,220 lines, published March 2026, v1.0).
- **Parser note:** the 21 entries appear as plain-text lines of the form `DSGAI## — Title` (em dash), **not** under markdown headings. Parser uses bare-ID / em-dash regex, not the heading regex used by the LLM and Agentic parsers.
- **Output:** per-entry source nodes with fields matching the existing `owasp-llm-top10` / `owasp-agentic-top10` ingesters (`node_id`, `local_id`, `framework`, `title`, `text`, section paths, …).

### 4.3 Upstream loader

- **Module:** `classifier/data/upstream_loader.py`
- **Input:** `third_party/genai-crosswalk/` (via MANIFEST pin)
- **Outputs:**
  - `data/upstream/mappings_v1.jsonl` — one row per inline mapping, with fields:
    - `source_framework`, `source_id`, `source_list`, `target_framework`, `target_control_id`, `target_control_name`, `tier`, `scope`, `notes`, `url`, `provenance_sha`
    - `provenance_sha = sha256(upstream_commit_sha + entry_id + mapping_index)`
    - **ID normalization:** the loader maps upstream's `source_list` value (`LLM-Top10-2025`, `Agentic-Top10-2026`, `DSGAI-2026`) to our internal framework identifier (`owasp_llm`, `owasp_agentic`, `owasp_dsgai`) and emits that in `source_framework`. The upstream entry `id` (e.g. `LLM01`) is emitted verbatim in `source_id`. This normalization is the sole join key the contamination auditor uses against our internal data; a mismatch here silently voids the honesty firewall, so the loader has a dedicated unit test asserting the normalization table is exhaustive and collision-free.
    - Target-framework normalization follows the same pattern: upstream's free-form `framework` field (e.g. `MITRE ATLAS`, `ISO-42001`) is mapped to our internal framework identifiers via an explicit table. Unknown target frameworks are emitted with a `target_framework_unknown=True` flag and excluded from training until the table is extended.
  - `data/upstream/crossrefs_v1.jsonl` — one row per `(source_id, target_id)` crossref, same provenance scheme
  - `data/upstream/hashes.json` — file-level SHA256 of every derived file, joined into the main `data/splits/hashes.json` manifest

### 4.4 Contamination auditor (honesty firewall)

- **Module:** `classifier/data/contamination.py`
- **Inputs:** `data/splits/human_test_frozen.jsonl`, `data/upstream/mappings_v1.jsonl`
- **Partition rules (strict):** all comparisons use the `(source_framework, source_id)` tuple — never bare `source_id` — so cross-source-list ID collisions can never silently defeat the rule.
  1. If a `(source_framework, source_id)` tuple appears *anywhere* in the frozen test, **every** upstream row with that same tuple is marked `held_out=True`.
  2. Additionally, any upstream row whose full `(source_framework, source_id, target_framework, target_id)` 4-tuple exactly matches a frozen-test row is marked `held_out=True` regardless of rule 1.
- **Outputs:**
  - `data/upstream/partition.json` — counts and the full set of held-out `provenance_sha` values
  - `data/upstream/contamination_report.json` — human-readable summary: overlapping source_ids, exact-tuple overlaps, projected training-row loss
- **CI gate:** `classifier/tests/test_contamination.py` asserts that no `provenance_sha` in `partition.json[held_out]` appears in any training batch loader output. The test is pre-registered; it MUST NOT be disabled, skipped, or xfailed. The orchestrator's rule "never disable a failing test" applies here with the tightest possible interpretation.

### 4.5 Label provenance & weighted training data

Every training row carries a `provenance_tag` field. The Plan 5 trainer accepts a `--label-weight` map keyed on tag:

| Tier | Source | `provenance_tag` | Default weight |
|---|---|---|---|
| Community gold | Upstream (train-eligible subset only) | `upstream_v1` | 1.0 |
| Silver | LLM-SME labeling (Plan 2) | `llm_sme_v1` | 0.6 (tunable) |
| Internal gold | Human calibration set | `human_cal_v1` | 1.0 |

Upstream does not *replace* LLM-SME. On pairs where upstream is held out under strict partitioning, LLM-SME remains the only training signal.

## 5. Scope (Tier B)

### 5.1 Source lists (3)

- OWASP LLM Top 10 (existing)
- OWASP Agentic Top 10 (existing)
- **OWASP DSGAI 2026 (new)**

### 5.2 Target frameworks

All 9 existing targets stay. Add **3 new targets** in the first pass, with 2 optional:

**Required:**
1. **ISO/IEC 42001:2023** — AIMS; directly AI-focused; heavy upstream coverage
2. **NIST SP 800-53 rev5** — broad federal controls; high upstream label density
3. **EU AI Act** — high strategic relevance; distinct from existing EU GPAI Code of Practice

**Optional (deferred to Tier-B phase-2 if corpus sourcing is slow):**
4. OWASP ASVS 4.0.3
5. MITRE ATT&CK for Enterprise

Each new target requires corpus ingestion (same pattern as existing frameworks) before being usable as a first-class target in the pair matrix. Targets whose corpus cannot be cleanly sourced are deferred; no fallback to "upstream metadata only" for target corpora (same reason we rejected that path for DSGAI in §2 D6).

### 5.3 Pair matrix growth

Rough estimate: current 12 pairs → **~30–40 pairs** depending on optional targets. Exact count determined by Plan 3 re-run of pair enumeration.

## 6. Evaluation strategy

- **Frozen test (untouched):** `human_test_frozen.jsonl`, 400 pairs, SHA-pinned. Pre-registered thresholds unchanged. Upstream contamination is statically impossible by construction (§4.4 rule 1).
- **Upstream benchmark (new primary secondary benchmark):** the held-out subset of `data/upstream/mappings_v1.jsonl`. Reported alongside the frozen test in all eval outputs. Paper framing: "independent second benchmark, never seen in training, drawn from a different community source."
- **Human calibration set:** `human_cal.jsonl` (150 rows). **Re-sourced** from train-eligible upstream rows instead of being collected fresh. Plan 6 Phase C SME halt is removed.
- **Cross-ref benchmark (new bonus):** `data/upstream/crossrefs_v1.jsonl` provides gold LLM↔Agentic↔DSGAI edges. New eval directly measures cross-source-list mapping quality — the weak spot in Sessions 6–8.

## 7. Plan-by-plan delta summary

This section is a **preview** for the follow-on `writing-plans` invocation. It is not itself a plan.

- **Plan 1 (infra & data splits)**
  - Finish leftover Task C steps 4, 5, 6 (`build_candidate_pool`, `build_candidates.py`, `retrieval_floor.py`) — already owed from the prior partial completion
  - Add DSGAI framework ingester (§4.2)
  - Add upstream vendor pin + manifest + `third_party/genai-crosswalk/` snapshot
  - Add upstream loader (§4.3)
  - Add contamination auditor + CI gate (§4.4)
  - Add ingestion tasks for each new target framework selected in §5.2
  - Add `THIRD_PARTY_NOTICES.md` with CC BY-SA attribution for both the DSGAI corpus and the upstream crosswalk repo
  - Extend `data/splits/hashes.json` to include upstream manifest hashes

- **Plan 2 (LLM SME labeling)** — Downgraded to "gap-filler for pairs upstream does not cover or holds out." Provenance tagging updated accordingly.

- **Plan 3 (candidate generation)** — Pair enumeration grows to the Tier-B source × target matrix. Retrieval floor report re-run on the enlarged matrix.

- **Plan 4 (bridge features / graph)** — Upstream `crossrefs_v1.jsonl` becomes high-confidence prior edges in the graph. Node2vec and bridge benchmarks re-run.

- **Plan 5 (classifier training)** — Trainer accepts provenance-tagged rows with per-tag weights (§4.5). Adds the held-out upstream benchmark and the crossref benchmark as reported evals alongside the frozen test.

- **Plan 6 (human evaluation)** — **Phase C halt removed.** Calibration data drawn from train-eligible upstream rows. No fresh SME session. Paper methodology section updated to disclose this.

- **Plan 7 (HF Space / deploy)** — UI adds DSGAI and the new targets. No upstream-schema export format in this phase (deferred per D4).

- **Plan 8 (arXiv paper)** — Narrative gains: held-out upstream benchmark, crossref benchmark, acknowledgement of upstream project and license, methodological disclosure of the Plan 6 substitution.

## 8. Risks & mitigations

| Risk | Mitigation |
|---|---|
| Strict partitioning removes most upstream training value on overlapping source lists | Accept the cost; the held-out portion becomes the upstream benchmark, so held-out rows still serve the project |
| Contamination auditor has a bug and train-test leakage slips through | Two-layer defense: static partition at data-build time AND runtime assertion in training-batch loader that no held-out `provenance_sha` appears in any batch; both pre-registered tests |
| New target frameworks' corpora are hard to source or have hostile licenses | Each new target is a separable Plan 1 task; drop to phase-2 on any blocker; no target ships without verified license |
| DSGAI parser mis-extracts entries (em-dash format, 21 expected) | Parser test asserts exactly 21 source nodes with IDs DSGAI01..DSGAI21 and non-empty body text for each; pipeline fails loudly if the count or IDs drift |
| Paper methodology criticism for replacing fresh SME calibration with upstream labels | Explicit disclosure in Plan 8; emphasize frozen-test independence; report held-out upstream benchmark separately to demonstrate the classifier does not merely echo upstream |
| CC BY-SA ShareAlike obligation on derived data files | `THIRD_PARTY_NOTICES.md` carries attribution; all derived data files under `data/upstream/` are declared CC BY-SA 4.0 in their manifest; trained model weights treated conservatively and redistribution policy revisited at Plan 7 |

## 9. Out of scope (YAGNI)

Explicitly not in this spec, do not scope-creep into them:

- PRs to upstream; any writes to the upstream repo; submodule push access
- Upstream-schema output format (deferred per D4)
- Full 20-framework target coverage; anything beyond the §5.2 Tier-B target list
- Fresh human SME label collection (replaced per D7)
- i18n; Garak / PyRIT eval integration; incidents database import; tools catalog import
- Re-freezing, re-splitting, or in any way altering `human_test_frozen.jsonl` or `data/splits/hashes.json` (except to *add* upstream manifest hashes, never to remove or modify existing entries)
- Multi-task learning on `severity` / `tier` / `scope` auxiliary heads in Plan 5's first pass
- Classifier-into-upstream merge (Tier C); kept as future optionality, not scoped here

## 10. Acceptance criteria for "this spec is implemented"

The follow-on implementation plans are complete when:

1. `third_party/genai-crosswalk/` exists with a pinned SHA and `MANIFEST.json`
2. `data/frameworks/owasp-dsgai/` is ingested into 21 source nodes by `classifier/data/frameworks/dsgai.py` with parser tests passing
3. Each new target framework in §5.2 (required set) is ingested
4. `data/upstream/mappings_v1.jsonl`, `crossrefs_v1.jsonl`, `partition.json`, and `contamination_report.json` are built deterministically from the pinned upstream snapshot
5. Contamination CI gate (`classifier/tests/test_contamination.py`) passes on CI and is marked non-skippable
6. `data/splits/hashes.json` includes upstream manifest hashes
7. `THIRD_PARTY_NOTICES.md` carries the required CC BY-SA 4.0 attribution for upstream and the DSGAI corpus
8. `human_test_frozen.jsonl` is byte-identical to its pre-upstream-integration version
9. Plan 6 no longer halts for a fresh SME block; calibration is drawn from train-eligible upstream rows
10. All eight plans (Plan 1 through Plan 8) are rewritten to reflect §7, reviewed, and ready to hand to the Phase 0 orchestrator
