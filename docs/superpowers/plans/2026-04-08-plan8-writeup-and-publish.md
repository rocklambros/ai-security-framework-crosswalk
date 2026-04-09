# Plan 8 — Writeup & Publish Implementation Plan (upstream-integrated)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Supersedes:** `docs/superpowers/plans/2026-04-07-plan8-writeup-and-publish.md` (do not edit that file; it is preserved as the pre-upstream baseline).

**Goal:** Convert the sacred-run artifacts from Plan 6 *and* the Plan 1-B upstream-integration artifacts into a publishable record: an arXiv LaTeX draft scaffold, matplotlib figure scripts, three evaluation tables (frozen test, held-out upstream benchmark, crossref benchmark), a HuggingFace model upload with a complete honesty-section model card, a HuggingFace dataset upload for `v1_frozen` labels, a blog post draft, repo polish (README, LICENSE, CITATION.cff, pinned requirements), GitHub Actions CI, and a one-liner reproduction Makefile target. The sacred-run numbers and the held-out upstream numbers are consumed verbatim; this plan writes **no** model code and runs **no** training.

**Architecture:** Plan 8 is almost entirely additive. A new top-level `paper/` tree houses the LaTeX sources, a new `classifier/publish/` subpackage holds the HF uploaders and the Jinja2 model-card renderer, a new `classifier/figures/` subpackage holds the matplotlib figure scripts, a new `classifier/paper_tables/` subpackage holds three table-rendering scripts that read `data/sacred_run/results.json` (Table X frozen), `data/sacred_run/upstream_holdout.json` (Table Y held-out upstream), and `data/sacred_run/crossref_eval.json` (Table Z crossref). `.github/workflows/ci.yml` adds a push-time hash-verify + lint + unit-test gate, and a new top-level `Makefile` wires `make reproduce` to `verify_hashes() → eval on llm_val → diff against committed sacred-run results`. The HuggingFace uploads both tag the released artifacts with the sacred-run `git_sha` and both default to `--dry-run`.

**Tech Stack:** Python 3.11, `jinja2`, `huggingface_hub`, `matplotlib`, `pandas`, `pyarrow`, `pytest`, `ruff`, `mypy`, LaTeX (`latexmk` + `tectonic` fallback), GitHub Actions, existing repo stack. No new ML dependencies — Plan 8 never loads a transformer at author time.

**Budget:** ~$0. No LLM calls, no GPU compute. HuggingFace Hub uploads are free. Only cost is wall-clock for a handful of `latexmk` builds and CI runs.

---

## Spec Reference

Implements §6 (evaluation strategy — three benchmarks), §7 Plan 8 delta (held-out upstream benchmark, crossref benchmark, upstream acknowledgement + license, Plan 6 substitution disclosure), §8 risk row "Paper methodology criticism for replacing fresh SME calibration with upstream labels", and §1 (motivation) of `docs/superpowers/specs/2026-04-08-upstream-crosswalk-integration-design.md`. Carries forward §4.6 deliverables and §6 Pre-Registered Honesty Commitments from `docs/superpowers/specs/2026-04-07-ai-security-crosswalk-classifier-design.md`. Consumes:

- `paper/tables/tableX_frozen.{tex,md}` — frozen-test (Plan 6)
- `paper/tables/tableY_upstream_holdout.{tex,md}` — held-out upstream benchmark (Plan 5)
- `paper/tables/tableZ_crossref.{tex,md}` — crossref LLM↔Agentic↔DSGAI benchmark (Plan 5)
- `data/sacred_run/results.json` — frozen metrics
- `data/sacred_run/upstream_holdout.json` — held-out upstream metrics (produced by Plan 5, consumed read-only here)
- `data/sacred_run/crossref_eval.json` — crossref metrics (produced by Plan 5, consumed read-only here)
- `docs/methodology_notes/plan6-calibration-substitution.md` — Plan 6 substitution note (produced by Plan 6, cited here)
- `data/upstream/README.md` — id-normalization methodology (Plan 1-C)
- `third_party/genai-crosswalk/MANIFEST.json` — pinned upstream commit SHA
- `THIRD_PARTY_NOTICES.md` — CC BY-SA 4.0 attribution

**Out of scope for Plan 8:** any re-training, any re-scoring of `human_test_frozen`, any modification of sacred-run artifacts, any new evaluation beyond the three listed above, any revision of the pre-registered frozen-test thresholds, any HF Space / Dash app deployment (Plan 7), any LLM labeling (Plan 2), any baseline code (Plan 3), any arXiv *submission* (plan stops at a `latexmk`-clean PDF and uploaded HF artifacts; final submission is a human action), any PR to upstream crosswalk.

---

## File Structure

**New layout.** Plan 8 creates and only touches these paths:

| Path | Purpose |
|---|---|
| `paper/main.tex` | arXiv LaTeX entry point |
| `paper/sections/abstract.tex` | Abstract |
| `paper/sections/intro.tex` | Introduction (motivation, ported from spec §1) |
| `paper/sections/related.tex` | Related work, including GenAI Security Project crosswalk acknowledgement |
| `paper/sections/method.tex` | Method (architecture + loss) |
| `paper/sections/dataset.tex` | Dataset + LLM-SME protocol + upstream inclusion + id-normalization footnote |
| `paper/sections/contamination.tex` | Contamination methodology (strict tuple partition, two-layer defense) |
| `paper/sections/methodology_disclosure.tex` | Plan 6 calibration-substitution disclosure |
| `paper/sections/experiments.tex` | Experimental setup — three benchmarks |
| `paper/sections/results.tex` | Headline results + `\input` of the three tables |
| `paper/sections/ablations.tex` | Ablation study |
| `paper/sections/limitations.tex` | Limitations |
| `paper/sections/ethics.tex` | Ethics statement |
| `paper/sections/license_compliance.tex` | CC BY-SA 4.0 compliance + model-weights redistribution posture |
| `paper/sections/reproducibility.tex` | Reproducibility statement |
| `paper/sections/acknowledgements.tex` | Thanks to GenAI Security Project + OWASP DSGAI contributors |
| `paper/refs.bib` | BibTeX references |
| `paper/latexmkrc` | Non-interactive latexmk config |
| `paper/figures/` | Output directory for PDF figures |
| `paper/tables/` | Output directory for the three eval tables (generated) |
| `paper/README.md` | Build instructions |
| `classifier/figures/__init__.py` | subpackage marker |
| `classifier/figures/fig1_arch.py` | Architecture block diagram |
| `classifier/figures/fig2_calibration.py` | Reliability diagram |
| `classifier/figures/fig3_per_pair.py` | Per-framework-pair recall@3 bars |
| `classifier/figures/fig4_ablation.py` | Ablation forest plot |
| `classifier/paper_tables/__init__.py` | subpackage marker |
| `classifier/paper_tables/tableX_frozen.py` | Renders Table X — frozen test |
| `classifier/paper_tables/tableY_upstream_holdout.py` | Renders Table Y — held-out upstream benchmark |
| `classifier/paper_tables/tableZ_crossref.py` | Renders Table Z — crossref benchmark |
| `classifier/publish/__init__.py` | subpackage marker |
| `classifier/publish/upload_model.py` | HF model uploader (dry-run default) |
| `classifier/publish/upload_dataset.py` | HF dataset uploader (dry-run default) |
| `classifier/publish/model_card.py` | Jinja2 model-card renderer |
| `classifier/publish/dataset_card.py` | Jinja2 dataset-card renderer |
| `classifier/publish/templates/model_card.md.j2` | Model card template (honesty §6 verbatim + 3 benchmarks + upstream attribution) |
| `classifier/publish/templates/dataset_card.md.j2` | Dataset card template (includes upstream provenance disclosure) |
| `classifier/tests/publish/__init__.py` | subpackage marker |
| `classifier/tests/publish/test_upload_model_dryrun.py` | Upload dry-run test |
| `classifier/tests/publish/test_upload_dataset_dryrun.py` | Upload dry-run test |
| `classifier/tests/publish/test_model_card_honesty.py` | Assert §6 commitments + upstream attribution block render verbatim |
| `classifier/tests/figures/__init__.py` | subpackage marker |
| `classifier/tests/figures/test_fig1.py` | Figure 1 existence + PDF header bytes |
| `classifier/tests/figures/test_fig2_3_4.py` | Figures 2–4 existence + PDF header bytes |
| `classifier/tests/paper_tables/__init__.py` | subpackage marker |
| `classifier/tests/paper_tables/test_tables_render.py` | Assert all three tables render, contain required columns, and cite the correct source json |
| `classifier/tests/paper/__init__.py` | subpackage marker |
| `classifier/tests/paper/test_latexmk_build.py` | Fixture latexmk build (skip if latexmk absent) |
| `classifier/tests/paper/test_sections_disclose_substitution.py` | Assert methodology_disclosure.tex cites Plan 6 note + mentions "train-eligible upstream" + 150 |
| `classifier/tests/paper/test_sections_acknowledge_upstream.py` | Assert related.tex cites upstream repo + commit SHA + CC BY-SA 4.0 |
| `classifier/tests/paper/test_sections_contamination.py` | Assert contamination.tex describes `(source_framework, source_id)` tuple + two-layer defense |
| `classifier/tests/paper/test_no_ai_attribution.py` | Assert no paper section mentions Claude / Anthropic / AI-assisted |
| `classifier/tests/repo/test_readme_reproduce.py` | README contains `make reproduce` one-liner |
| `classifier/tests/repo/test_citation_cff.py` | CITATION.cff has ORCID + Rock Lambros, no AI attribution |
| `classifier/tests/repo/test_license.py` | LICENSE is Apache-2.0 text |
| `classifier/tests/repo/test_requirements_frozen.py` | requirements.txt has every dep pinned `==` |
| `classifier/tests/repo/test_reproduce_make_target.py` | `make -n reproduce` lists the four steps |
| `docs/blog/2026-XX-XX-ai-security-crosswalk.md` | Blog post draft |
| `.github/workflows/ci.yml` | Push-time CI |
| `Makefile` | `make reproduce` one-liner target |
| `LICENSE` | Apache-2.0 (verbatim) |
| `CITATION.cff` | Rock Lambros + ORCID |
| `requirements.txt` | Frozen via pip-compile |
| `README.md` | Repo polish |

**Do not modify** any file under `classifier/data/`, `classifier/labeling/`, `classifier/models/`, `classifier/sacred/`, `data/splits/`, `data/labels/`, `data/sacred_run/`, `data/upstream/`, `third_party/genai-crosswalk/`, `docs/methodology_notes/`, `THIRD_PARTY_NOTICES.md`, or existing `mapping_engine/` code. Plan 8 consumes those as read-only inputs. In particular: never open `data/splits/human_test_frozen.jsonl`; never edit the pre-existing 2026-04-07 plan file.

---

## Cross-Plan Contracts

- **Contract 1 — hash verification at entry.** `Makefile`'s `reproduce` target calls `python -m classifier.data.splits verify-hashes` **before** any other step.
- **Contract 12 — honesty section verbatim in model card.** The eight commitments in the 2026-04-07 spec §6 must appear **character-identical** in the rendered HF model card.
- **Contract 13 — sacred-run git_sha tagging.** Both `upload_model.py` and `upload_dataset.py` read `data/sacred_run/results.json["git_sha"]` and pass it to `HfApi.create_tag(...)`.
- **Contract 14 (NEW) — three-benchmark reporting parity.** Every author-facing artifact that reports the frozen-test headline (model card, dataset card, blog post, paper results section, README badges) MUST also report the held-out upstream benchmark headline and the crossref benchmark headline on the same artifact. Enforced by `test_model_card_honesty.py` and `test_tables_render.py`. No cherry-picking.
- **Contract 15 (NEW) — upstream acknowledgement verbatim.** `paper/sections/related.tex`, `paper/sections/acknowledgements.tex`, and the rendered HF model card MUST include the upstream repo URL, the pinned commit SHA from `third_party/genai-crosswalk/MANIFEST.json`, and the literal string `CC BY-SA 4.0`. Enforced by `test_sections_acknowledge_upstream.py` and `test_model_card_honesty.py`.
- **Contract 16 (NEW) — Plan 6 substitution disclosure non-skippable.** `paper/sections/methodology_disclosure.tex` MUST cite `docs/methodology_notes/plan6-calibration-substitution.md` by path, state that the 150-row calibration pool was drawn from train-eligible upstream rows, and name the mitigation (held-out upstream benchmark reported separately). Enforced by `test_sections_disclose_substitution.py`.
- **Contract 1-bis — `human_test_frozen` untouched.** Plan 8 never opens `data/splits/human_test_frozen.jsonl`.

---

## Lessons Carried

- Sacred-run numbers are frozen; Plan 8 has zero knobs that move a reported number.
- Held-out upstream numbers are similarly frozen once Plan 5 writes `data/sacred_run/upstream_holdout.json`; Plan 8 surfaces them as-is.
- Jinja2 templates are SHA256-hashed and committed.
- No AI/Claude/Anthropic attribution anywhere — in the paper, in any commit message, in any card, in any test fixture.

---

## Phase A — arXiv LaTeX scaffold (including the new upstream-integration sections)

### Task A1: `paper/main.tex` + section files

**Files:**
- Create: `paper/main.tex`
- Create: `paper/sections/{abstract,intro,related,method,dataset,contamination,methodology_disclosure,experiments,results,ablations,limitations,ethics,license_compliance,reproducibility,acknowledgements}.tex`
- Create: `paper/refs.bib`
- Create: `paper/latexmkrc`
- Create: `paper/README.md`

- [ ] **Step 1: Write `paper/main.tex`**

```latex
% paper/main.tex
\documentclass[11pt,letterpaper]{article}
\usepackage[margin=1in]{geometry}
\usepackage{microtype}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{amsmath,amssymb}
\usepackage{hyperref}
\usepackage{cleveref}
\usepackage{natbib}

\title{Cross-Framework AI Security Control Mapping with\\
       Disagreement-Aware Multi-Task Learning}
\author{Rock Lambros}
\date{\today}

\begin{document}
\maketitle

\input{sections/abstract}
\input{sections/intro}
\input{sections/related}
\input{sections/method}
\input{sections/dataset}
\input{sections/contamination}
\input{sections/methodology_disclosure}
\input{sections/experiments}
\input{sections/results}
\input{sections/ablations}
\input{sections/limitations}
\input{sections/ethics}
\input{sections/license_compliance}
\input{sections/reproducibility}
\input{sections/acknowledgements}

\bibliographystyle{plainnat}
\bibliography{refs}

\end{document}
```

- [ ] **Step 2: Write `paper/sections/intro.tex` (ports spec §1 motivation)**

```latex
% paper/sections/intro.tex
\section{Introduction}
\label{sec:intro}

% Concrete structure (fill prose from bullets below):
% (a) The compliance problem: AI security teams must reconcile OWASP LLM
%     Top 10, OWASP Agentic Top 10, OWASP DSGAI 2026, NIST AI RMF, MITRE
%     ATLAS, ISO/IEC 42001, EU AI Act, and related frameworks --- none of
%     which share vocabulary or structure. Manual crosswalks are slow,
%     inconsistent, and go stale the moment any framework revises.
% (b) The available gold signal: the GenAI Security Project has published
%     41 hand-curated JSON entries (10 OWASP LLM + 10 OWASP Agentic +
%     21 OWASP DSGAI 2026), each carrying roughly 45 cross-framework
%     mappings, for ~1,800 gold (source, target) labels across ~20 target
%     frameworks, plus a crossrefs field that provides free LLM <-> Agentic
%     <-> DSGAI gold edges. It is licensed CC BY-SA 4.0.
% (c) The gap: 41 entries are enough to train a strong classifier on
%     overlapping source lists but not enough for a full retrieval-plus-
%     reranker stack with honest held-out evaluation; the project combines
%     upstream gold with an internal 550-row LLM-SME-labeled pool and a
%     strict 400/150 frozen-test / calibration split.
% (d) Contribution: (1) a disagreement-aware multi-task cross-encoder with
%     a GAT bridge, (2) a reproducible three-benchmark evaluation
%     (frozen test, held-out upstream benchmark, crossref benchmark),
%     (3) honest disclosure of the Plan 6 calibration substitution, and
%     (4) an open artifact stack (HF model, HF dataset, GitHub, arXiv).
% (e) Framing vs. upstream: we are an aligned consumer building a
%     classifier on top of upstream's hand-curated gold labels; upstream
%     remains the authoritative hand-curated source and we do not claim
%     otherwise.
```

- [ ] **Step 3: Write `paper/sections/related.tex` (GenAI Security Project acknowledgement)**

```latex
% paper/sections/related.tex
\section{Related Work}
\label{sec:related}

% Subsections:
% 1. Cross-framework control mapping: prior manual crosswalks (cite MITRE
%    ATT&CK mapping guides, ENISA cross-standard analyses, and the
%    academic control-mapping literature such as Park et al.).
% 2. Retrieval + rerank over compliance corpora: dense retrieval baselines
%    (BM25, ColBERT, bge-reranker-v2-m3), cross-encoder rerankers, and
%    prior work on regulatory-text matching.
% 3. The GenAI Security Project GenAI Data Security Initiative crosswalk
%    --- hand-curated community resource covering OWASP LLM Top 10 (2025),
%    OWASP Agentic Top 10 (2026), and OWASP DSGAI (2026), with
%    per-entry JSON files each carrying ~45 cross-framework mappings plus
%    an entry-level crossrefs field. Released under CC BY-SA 4.0 at
%    \url{https://github.com/GenAI-Security-Project/GenAI-Data-Security-Initiative}.
%    Pinned in this work at upstream commit
%    \texttt{<UPSTREAM_COMMIT_SHA>}, read verbatim from
%    \texttt{third\_party/genai-crosswalk/MANIFEST.json}.
%    We position this work as an aligned consumer building a classifier on
%    top of upstream's hand-curated gold labels; we do not re-curate or
%    second-guess upstream's tier / scope annotations, and we do not claim
%    that upstream is categorically better than existing crosswalks --- we
%    use it as an independent, high-volume second signal.
% 4. LLM-SME labeling and multi-persona ensembles.
```

- [ ] **Step 4: Write `paper/sections/dataset.tex` (includes upstream + id-normalization footnote)**

```latex
% paper/sections/dataset.tex
\section{Dataset}
\label{sec:dataset}

% Paragraphs:
% - Internal 550-row LLM-SME pool (Plan 2), 3-persona ensemble, reference
%   grounding, schema.
% - Upstream community gold: 41 entries / ~1,800 mappings / 3 source
%   lists / ~20 target frameworks, consumed as a pinned read-only
%   dependency under third_party/genai-crosswalk/.
% - Provenance tagging: every training row carries provenance_tag in
%   {upstream_v1, llm_sme_v1, human_cal_v1} with default weights 1.0,
%   0.6, 1.0 respectively (Plan 5).
% - Id-normalization: upstream target_control_id values are preserved
%   verbatim; a canonicalized target_node_id is added alongside. The
%   canonicalization rules per target framework (eu_ai_act, nist_rmf,
%   aiuc_1, mitre_atlas, csa_aicm) are documented in
%   \texttt{data/upstream/README.md} and held locally under CC BY-SA 4.0
%   pending peer review; they are not yet upstreamed (Direction 3 /
%   consume-only posture per the Plan 1-B design spec).\footnote{%
%   See \texttt{data/upstream/README.md} in the project repository for
%   the per-framework canonicalization rules and the pre/post in-scope
%   resolution rates (overall 97/413 to 341/413, i.e. 0.235 to 0.826;
%   Category A excluding csa\_aicm: 341/352 = 0.969).}
```

- [ ] **Step 5: Write `paper/sections/contamination.tex`**

```latex
% paper/sections/contamination.tex
\section{Contamination Methodology}
\label{sec:contamination}

% Content (prose from these concrete bullets):
% - Partition key: the strict $(source\_framework, source\_id)$ TUPLE,
%   never bare $source\_id$. Cross-source-list ID collisions (e.g. a
%   hypothetical shared "01" between LLM-Top10 and DSGAI) cannot
%   silently defeat the partition.
% - Rule 1: if a $(source\_framework, source\_id)$ tuple appears anywhere
%   in \texttt{human\_test\_frozen.jsonl}, every upstream row with that
%   same tuple is marked $held\_out = True$ and excluded from training.
% - Rule 2: any upstream row whose full
%   $(source\_framework, source\_id, target\_framework, target\_id)$
%   4-tuple exactly matches a frozen-test row is additionally marked
%   $held\_out = True$ regardless of Rule 1.
% - Two-layer defense: (i) static partition at data-build time writes
%   \texttt{data/upstream/partition.json}; (ii) a runtime assertion in
%   the training-batch loader refuses to emit any row whose
%   $provenance\_sha$ is in the held-out set.
% - Test non-skippability: \texttt{classifier/tests/test\_contamination.py}
%   is pre-registered as non-skippable; marking it xfail is out of bounds
%   per project convention.
% - Why this is the only defensible posture: pre-registered thresholds on
%   the frozen test mean any leakage invalidates the headline claim; the
%   cost (losing training rows) is accepted because held-out rows still
%   serve the project as the second benchmark.
```

- [ ] **Step 6: Write `paper/sections/methodology_disclosure.tex`**

```latex
% paper/sections/methodology_disclosure.tex
\section{Methodology Disclosure: Calibration Substitution}
\label{sec:methodology_disclosure}

% Content (mandatory per spec Section 7 Plan 8 delta and Section 8 risk
% row on paper methodology criticism):
% - State plainly: the 150-row calibration pool used to set the
%   pre-registered tier-confidence thresholds was sourced from
%   train-eligible upstream rows rather than from a fresh project-native
%   SME session. The previously planned Plan 6 Phase C SME halt was
%   removed.
% - Citation: this substitution is documented in
%   \texttt{docs/methodology\_notes/plan6-calibration-substitution.md}
%   in the project repository, produced by Plan 6 at sacred-run time.
% - Why: (1) the upstream pool is community-curated gold that dwarfs our
%   available SME capacity by two orders of magnitude on overlapping
%   source lists; (2) strict $(source\_framework, source\_id)$ partitioning
%   protects the frozen test from any leakage; (3) the frozen test itself
%   was untouched by this decision --- its hash is pinned in
%   \texttt{data/splits/hashes.json}.
% - Trade-off honestly stated: calibration is community-sourced rather
%   than project-native, and therefore inherits any systematic bias in
%   the upstream labeling pool. We mitigate by reporting the held-out
%   upstream benchmark (Table Y) separately alongside the frozen test
%   (Table X), so a reader can verify that the classifier does not merely
%   echo upstream. If the model were simply memorizing upstream, Table Y
%   would be near-perfect; the gap between Table X and Table Y
%   (discussed in Section~\ref{sec:results}) is the direct empirical
%   answer to that criticism.
% - Explicit non-claim: we do NOT argue that upstream is categorically
%   better than a fresh SME session. The claim is narrower: for this
%   project's scale, upstream is an acceptable calibration source so
%   long as the frozen test remains independent and the held-out
%   upstream benchmark is reported alongside it.
```

- [ ] **Step 7: Write `paper/sections/experiments.tex`**

```latex
% paper/sections/experiments.tex
\section{Experimental Setup}
\label{sec:experiments}

% Content:
% - Three benchmarks, reported side by side in Section~\ref{sec:results}:
%   (X) Frozen test --- \texttt{data/splits/human\_test\_frozen.jsonl},
%   400 pairs, SHA-pinned, pre-registered thresholds unchanged from the
%   2026-04-07 project spec Section 6. This is the primary benchmark.
%   (Y) Held-out upstream benchmark --- the $held\_out = True$ subset of
%   \texttt{data/upstream/mappings\_v1.jsonl}, never seen in training,
%   drawn from the same upstream snapshot as the calibration pool but
%   statically partitioned out by the contamination auditor
%   (Section~\ref{sec:contamination}). Independent second benchmark.
%   (Z) Crossref benchmark --- \texttt{data/upstream/crossrefs\_v1.jsonl},
%   gold LLM <-> Agentic <-> DSGAI cross-source-list edges. This directly
%   measures cross-source-list mapping quality, which was the weak spot
%   in the pre-upstream project sessions (6 through 8).
% - Metrics per benchmark: precision, recall, F1, Recall@3, MRR, and --- for
%   the frozen test only --- ECE and precision-at-80%-coverage.
% - Explicit anti-scope: no new evaluations beyond these three are
%   introduced in this work; no revision of the pre-registered frozen-test
%   thresholds.
```

- [ ] **Step 8: Write `paper/sections/results.tex`**

```latex
% paper/sections/results.tex
\section{Results}
\label{sec:results}

% TODO(author): headline paragraph citing Recall@3 from Table X, the
% held-out upstream F1 from Table Y, and the crossref F1 from Table Z ---
% each with bootstrap 95% CI. Explicitly compare Table X and Table Y to
% show that the classifier is not merely echoing upstream.

\input{../tables/tableX_frozen.tex}

\input{../tables/tableY_upstream_holdout.tex}

\input{../tables/tableZ_crossref.tex}

\begin{figure}[t]
  \centering
  \includegraphics[width=0.95\linewidth]{figures/fig3_per_pair.pdf}
  \caption{Recall@3 on \texttt{human\_test\_frozen} stratified by
           framework pair, bootstrap 95\% CIs.}
  \label{fig:per_pair}
\end{figure}
```

- [ ] **Step 9: Write `paper/sections/license_compliance.tex`**

```latex
% paper/sections/license_compliance.tex
\section{License Compliance}
\label{sec:license_compliance}

% Content (from THIRD_PARTY_NOTICES.md):
% - OWASP GenAI Data Security Risks and Mitigations 2026 (v1.0) PDF and
%   extracted text: CC BY-SA 4.0, attributed to the OWASP GenAI Data
%   Security Project.
% - GenAI Security Project GenAI Data Security Initiative crosswalk:
%   CC BY-SA 4.0, attributed to the GenAI Security Project, pinned at
%   the upstream commit SHA recorded in
%   \texttt{third\_party/genai-crosswalk/MANIFEST.json}.
% - Derived data files under \texttt{data/upstream/} (mappings\_v1.jsonl,
%   crossrefs\_v1.jsonl, partition.json, contamination\_report.json) and
%   \texttt{data/processed/frameworks/owasp\_dsgai.json} are declared
%   CC BY-SA 4.0 inheriting from the upstream sources.
% - Project code is Apache-2.0 (see \texttt{LICENSE}).
% - Model weights redistribution: conservative posture per the Plan 1-B
%   spec Section 8 risk row. Weights are released on HuggingFace under
%   CC-BY-4.0 with the sacred-run git\_sha as a version tag; the training
%   data provenance (upstream CC BY-SA 4.0 + internal LLM-SME) is
%   disclosed in the model card. Users deriving further trained weights
%   from this model inherit the ShareAlike obligation on any data they
%   redistribute that is sourced from \texttt{data/upstream/}.
```

- [ ] **Step 10: Write `paper/sections/acknowledgements.tex`**

```latex
% paper/sections/acknowledgements.tex
\section*{Acknowledgements}
\label{sec:acknowledgements}

% Content:
% - Thanks to the GenAI Security Project and the GenAI Data Security
%   Initiative contributors for publishing the crosswalk under CC BY-SA
%   4.0; cite the repository URL
%   \url{https://github.com/GenAI-Security-Project/GenAI-Data-Security-Initiative}
%   and the pinned commit SHA \texttt{<UPSTREAM_COMMIT_SHA>}.
% - Thanks to the OWASP GenAI Data Security Project contributors for the
%   2026 v1.0 publication under CC BY-SA 4.0.
% - Where contributor lists are public, name individual contributors in
%   the published version of this section; author-filled at release time.
% - NO AI / Claude / Anthropic / "AI-assisted" mention of any kind.
```

- [ ] **Step 11: Write stub section files for remaining sections**

Each of `abstract.tex`, `method.tex`, `ablations.tex`, `limitations.tex`, `ethics.tex`, `reproducibility.tex` contains a `\section{...}` header and a `% TODO(author)` comment block listing the paragraphs the human author must write, plus concrete `\input` / `\includegraphics` hooks. Plan 6 tables referenced elsewhere in the paper feed in via `\input{../tables/tableX_frozen.tex}` and friends.

- [ ] **Step 12: Write `paper/latexmkrc`**

```perl
# paper/latexmkrc
$pdf_mode = 1;
$pdflatex = 'pdflatex -interaction=nonstopmode -halt-on-error %O %S';
$bibtex_use = 2;
$clean_ext = 'bbl run.xml synctex.gz';
```

- [ ] **Step 13: Write `paper/refs.bib` seed entries**

Include BibTeX entries for: MITRE ATLAS, NIST AI RMF, OWASP LLM Top 10, OWASP Agentic Top 10, OWASP DSGAI 2026 (published March 2026 v1.0), ISO/IEC 42001:2023, EU AI Act, BM25 (Robertson & Zaragoza 2009), bge-reranker-v2-m3 (Chen et al. 2024), DeBERTa-v3 (He et al. 2023), RepLlama (Ma et al. 2024), LoRA (Hu et al. 2022), GAT (Veličković et al. 2018), LightGBM (Ke et al. 2017), Mondrian conformal (Vovk et al. 2005), Cohen's kappa. Add a `@misc` entry for the GenAI Security Project crosswalk repository with the pinned commit SHA in the `note` field.

- [ ] **Step 14: Commit**

```bash
git add paper/main.tex paper/sections/ paper/refs.bib paper/latexmkrc
git commit -m "plan8: arxiv scaffold including upstream-integration sections"
```

### Task A2: `paper/README.md`

- [ ] **Step 1: Write build instructions** (same as prior plan; unchanged).

- [ ] **Step 2: Commit**

```bash
git add paper/README.md
git commit -m "plan8: paper build README"
```

### Task A3: latexmk fixture build test

**Files:**
- Create: `classifier/tests/paper/__init__.py`
- Create: `classifier/tests/paper/test_latexmk_build.py`

- [ ] **Step 1: Write the test**

```python
# classifier/tests/paper/test_latexmk_build.py
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
PAPER = REPO / "paper"

@pytest.mark.skipif(shutil.which("latexmk") is None,
                    reason="latexmk not installed in this environment")
def test_latexmk_builds_main_tex(tmp_path):
    dst = tmp_path / "paper"
    shutil.copytree(PAPER, dst)
    (dst / "tables").mkdir(exist_ok=True)
    for stem in ("tableX_frozen", "tableY_upstream_holdout", "tableZ_crossref"):
        (dst / "tables" / f"{stem}.tex").write_text(
            r"\begin{tabular}{l}stub\\\end{tabular}" + "\n"
        )
    (dst / "figures").mkdir(exist_ok=True)
    for n in ("fig1_arch", "fig2_calibration", "fig3_per_pair", "fig4_ablation"):
        (dst / "figures" / f"{n}.pdf").write_bytes(b"%PDF-1.4\n%%EOF\n")
    result = subprocess.run(
        ["latexmk", "-pdf", "-interaction=nonstopmode", "main.tex"],
        cwd=dst, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert (dst / "main.pdf").exists()
```

- [ ] **Step 2: Run and commit**

```bash
pytest classifier/tests/paper/test_latexmk_build.py -x
git add classifier/tests/paper/
git commit -m "plan8: latexmk fixture build test"
```

### Task A4: Section-content guard tests

**Files:**
- Create: `classifier/tests/paper/test_sections_disclose_substitution.py`
- Create: `classifier/tests/paper/test_sections_acknowledge_upstream.py`
- Create: `classifier/tests/paper/test_sections_contamination.py`
- Create: `classifier/tests/paper/test_no_ai_attribution.py`

- [ ] **Step 1: Methodology-disclosure guard**

```python
# classifier/tests/paper/test_sections_disclose_substitution.py
from pathlib import Path
REPO = Path(__file__).resolve().parents[3]
SEC = REPO / "paper" / "sections" / "methodology_disclosure.tex"

def test_disclosure_cites_plan6_note_and_150_and_upstream():
    txt = SEC.read_text()
    assert "plan6-calibration-substitution.md" in txt
    assert "150" in txt
    assert "train-eligible upstream" in txt
    assert "held-out upstream benchmark" in txt
    assert "Table X" in txt and "Table Y" in txt

def test_disclosure_frames_tradeoff_not_claim_of_superiority():
    txt = SEC.read_text()
    assert "We do NOT argue" in txt or "we do NOT argue" in txt \
           or "do NOT argue" in txt
```

- [ ] **Step 2: Upstream-acknowledgement guard**

```python
# classifier/tests/paper/test_sections_acknowledge_upstream.py
import json
from pathlib import Path
REPO = Path(__file__).resolve().parents[3]
MANIFEST = REPO / "third_party" / "genai-crosswalk" / "MANIFEST.json"
RELATED = REPO / "paper" / "sections" / "related.tex"
ACK = REPO / "paper" / "sections" / "acknowledgements.tex"

def test_related_cites_upstream_url_and_license():
    txt = RELATED.read_text()
    assert "GenAI Security Project" in txt
    assert "GenAI-Data-Security-Initiative" in txt
    assert "CC BY-SA 4.0" in txt
    assert "UPSTREAM_COMMIT_SHA" in txt or _pinned_sha(MANIFEST) in txt

def test_acknowledgements_thanks_upstream_and_dsgai():
    txt = ACK.read_text()
    assert "GenAI Security Project" in txt
    assert "OWASP GenAI Data Security" in txt
    assert "CC BY-SA 4.0" in txt

def _pinned_sha(manifest: Path) -> str:
    if not manifest.exists():
        return "UPSTREAM_COMMIT_SHA"
    return json.loads(manifest.read_text()).get("upstream_commit_sha", "")
```

- [ ] **Step 3: Contamination-methodology guard**

```python
# classifier/tests/paper/test_sections_contamination.py
from pathlib import Path
REPO = Path(__file__).resolve().parents[3]
SEC = REPO / "paper" / "sections" / "contamination.tex"

def test_contamination_describes_tuple_partition_and_two_layer_defense():
    txt = SEC.read_text()
    assert "source_framework" in txt and "source_id" in txt
    assert "tuple" in txt.lower()
    assert "Rule 1" in txt and "Rule 2" in txt
    assert "two-layer" in txt.lower() or "two layer" in txt.lower()
    assert "partition.json" in txt
    assert "pre-registered" in txt
```

- [ ] **Step 4: Attribution guard across all sections**

```python
# classifier/tests/paper/test_no_ai_attribution.py
from pathlib import Path
REPO = Path(__file__).resolve().parents[3]
SECTIONS = REPO / "paper" / "sections"

FORBIDDEN = ("Claude", "Anthropic", "AI-assisted", "Co-Authored-By",
             "Generated with")

def test_no_ai_attribution_in_any_paper_section():
    for p in SECTIONS.glob("*.tex"):
        txt = p.read_text()
        for s in FORBIDDEN:
            assert s not in txt, f"{p.name}: forbidden string {s!r}"
```

- [ ] **Step 5: Run and commit**

```bash
pytest classifier/tests/paper/ -x
git add classifier/tests/paper/
git commit -m "plan8: paper section content guards"
```

---

## Phase B — Figure scripts

Figures B1–B3 are carried forward unchanged from the 2026-04-07 plan (fig1 architecture, fig2 reliability, fig3 per-pair, fig4 ablation). No changes are required because the three new benchmarks are surfaced as tables (Phase B-prime), not figures. See the 2026-04-07 plan Tasks B1–B3 for full code listings; Plan 8 executes them verbatim.

**Commit messages:** `plan8: fig1 arch diagram`, `plan8: fig2 calibration reliability diagram`, `plan8: fig3 per-pair + fig4 ablation forest plot`.

---

## Phase B-prime — Three evaluation tables (NEW)

### Task BP1: `tableX_frozen.py` — frozen-test table

**Files:**
- Create: `classifier/paper_tables/__init__.py`
- Create: `classifier/paper_tables/tableX_frozen.py`

- [ ] **Step 1: Write the script**

```python
# classifier/paper_tables/tableX_frozen.py
"""Table X: frozen-test results (primary benchmark).
Reads data/sacred_run/results.json; writes paper/tables/tableX_frozen.{tex,md}.
Consumes metrics verbatim --- no rounding beyond display precision, no
knobs that could move a reported number."""
from __future__ import annotations
import json, os, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
RESULTS = REPO / "data" / "sacred_run" / "results.json"
OUT_DIR = Path(os.environ.get("TABLE_OUT_DIR", REPO / "paper" / "tables"))

HEADER = ["Metric", "Value", "95% CI"]
ROWS = [
    ("Precision",             "precision",         "precision_ci"),
    ("Recall",                "recall",            "recall_ci"),
    ("F1",                    "f1",                "f1_ci"),
    ("Recall@3",              "recall_at_3",       "recall_at_3_ci"),
    ("MRR",                   "mrr",               "mrr_ci"),
    ("ECE",                   "ece",               None),
    ("Precision @ 80% cov.",  "precision_at_80",   None),
]

def build() -> tuple[Path, Path]:
    if not RESULTS.exists():
        print("sacred run results not found; run Plan 6 first", file=sys.stderr)
        sys.exit(2)
    r = json.loads(RESULTS.read_text())
    m = r["metrics"]

    def fmt_ci(key):
        if key is None or key not in m:
            return "---"
        lo, hi = m[key]
        return f"[{lo:.3f}, {hi:.3f}]"

    tex_rows = []
    md_rows = [" | ".join(HEADER), " | ".join(["---"] * len(HEADER))]
    for label, vkey, cikey in ROWS:
        v = m.get(vkey, float("nan"))
        tex_rows.append(f"{label} & {v:.3f} & {fmt_ci(cikey)} \\\\")
        md_rows.append(f"{label} | {v:.3f} | {fmt_ci(cikey)}")

    tex = (
        "\\begin{table}[t]\n\\centering\n"
        "\\caption{Table X --- Frozen-test results on \\texttt{human\\_test\\_frozen} "
        "($n=400$, SHA-pinned; pre-registered thresholds per spec \\S6).}\n"
        "\\label{tab:frozen}\n"
        "\\begin{tabular}{lrl}\n\\toprule\n"
        "Metric & Value & 95\\% CI \\\\\n\\midrule\n"
        + "\n".join(tex_rows) +
        "\n\\bottomrule\n\\end{tabular}\n\\end{table}\n"
    )
    md = "\n".join(md_rows) + "\n"

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    tex_path = OUT_DIR / "tableX_frozen.tex"
    md_path = OUT_DIR / "tableX_frozen.md"
    tex_path.write_text(tex)
    md_path.write_text(md)
    return tex_path, md_path

def main():
    tex_path, md_path = build()
    print(tex_path)
    print(md_path)

if __name__ == "__main__":
    main()
```

**Expected output:** two files committed under `paper/tables/tableX_frozen.{tex,md}`; `tex` imports cleanly under `\input{../tables/tableX_frozen.tex}` from `paper/sections/results.tex`.

### Task BP2: `tableY_upstream_holdout.py` — held-out upstream benchmark

**Files:**
- Create: `classifier/paper_tables/tableY_upstream_holdout.py`

- [ ] **Step 1: Write the script**

Same pattern as `tableX_frozen.py`, reading `data/sacred_run/upstream_holdout.json`. The JSON is produced by Plan 5 and has the shape:

```json
{
  "git_sha": "<sacred_sha>",
  "partition_sha": "<sha256 of data/upstream/partition.json>",
  "held_out_row_count": 1234,
  "per_pair": [
    {"pair_key": "owasp_llm:LLM01__mitre_atlas",
     "precision": 0.78, "recall": 0.71, "f1": 0.744,
     "precision_ci": [0.71, 0.84],
     "recall_ci":    [0.64, 0.78],
     "f1_ci":        [0.69, 0.79],
     "n": 42}
  ],
  "overall": {"precision": 0.76, "recall": 0.69, "f1": 0.723, ...}
}
```

The script renders a per-pair row table (one row per pair) plus an "Overall" row, and writes both `.tex` and `.md` under `paper/tables/tableY_upstream_holdout.{tex,md}`. The caption MUST read: `Table Y --- Held-out upstream benchmark. Independent second benchmark drawn from the held-out subset of data/upstream/mappings_v1.jsonl (n = <N>), never seen in training. Partition key: strict (source_framework, source_id) tuple; see Section <ref sec:contamination>.`

The script refuses to run if `upstream_holdout.json` is missing and prints `"upstream holdout results not found; run Plan 5 first"` on stderr, exiting 2.

### Task BP3: `tableZ_crossref.py` — crossref benchmark

**Files:**
- Create: `classifier/paper_tables/tableZ_crossref.py`

- [ ] **Step 1: Write the script**

Same pattern, reading `data/sacred_run/crossref_eval.json`. Shape:

```json
{
  "git_sha": "<sacred_sha>",
  "pair": [
    {"name": "owasp_llm <-> owasp_agentic",
     "precision": 0.81, "recall": 0.74, "f1": 0.773, ...},
    {"name": "owasp_llm <-> owasp_dsgai", ...},
    {"name": "owasp_agentic <-> owasp_dsgai", ...}
  ],
  "overall": {"precision": 0.79, "recall": 0.72, "f1": 0.754}
}
```

Output: `paper/tables/tableZ_crossref.{tex,md}`. Caption: `Table Z --- Crossref benchmark on data/upstream/crossrefs_v1.jsonl (gold LLM <-> Agentic <-> DSGAI edges). Directly measures cross-source-list mapping quality.`

Missing-file behaviour identical to BP2.

### Task BP4: Table-render test

**Files:**
- Create: `classifier/tests/paper_tables/__init__.py`
- Create: `classifier/tests/paper_tables/test_tables_render.py`

- [ ] **Step 1: Write the test**

```python
# classifier/tests/paper_tables/test_tables_render.py
import json, subprocess, sys
from pathlib import Path
import pytest

REPO = Path(__file__).resolve().parents[3]
SACRED = REPO / "data" / "sacred_run"

FROZEN = {"git_sha": "deadbeef",
          "metrics": {
              "precision": 0.80, "recall": 0.72, "f1": 0.758,
              "precision_ci": [0.74, 0.86],
              "recall_ci":    [0.66, 0.78],
              "f1_ci":        [0.71, 0.80],
              "recall_at_3": 0.88, "recall_at_3_ci": [0.84, 0.92],
              "mrr": 0.71, "mrr_ci": [0.66, 0.76],
              "ece": 0.04, "precision_at_80": 0.86}}

HOLDOUT = {"git_sha": "deadbeef", "partition_sha": "cafe",
           "held_out_row_count": 100,
           "per_pair": [{"pair_key": "owasp_llm:LLM01__mitre_atlas",
                         "precision": 0.78, "recall": 0.71, "f1": 0.744,
                         "precision_ci": [0.71, 0.84],
                         "recall_ci":    [0.64, 0.78],
                         "f1_ci":        [0.69, 0.79], "n": 42}],
           "overall": {"precision": 0.76, "recall": 0.69, "f1": 0.723,
                       "precision_ci": [0.72, 0.80],
                       "recall_ci":    [0.65, 0.73],
                       "f1_ci":        [0.69, 0.76]}}

CROSSREF = {"git_sha": "deadbeef",
            "pair": [{"name": "owasp_llm <-> owasp_agentic",
                      "precision": 0.81, "recall": 0.74, "f1": 0.773,
                      "precision_ci": [0.76, 0.86],
                      "recall_ci":    [0.69, 0.79],
                      "f1_ci":        [0.73, 0.81]}],
            "overall": {"precision": 0.79, "recall": 0.72, "f1": 0.754,
                        "precision_ci": [0.75, 0.83],
                        "recall_ci":    [0.68, 0.76],
                        "f1_ci":        [0.72, 0.79]}}

@pytest.mark.parametrize("mod,fixture,stem", [
    ("classifier.paper_tables.tableX_frozen",
     ("results.json", FROZEN), "tableX_frozen"),
    ("classifier.paper_tables.tableY_upstream_holdout",
     ("upstream_holdout.json", HOLDOUT), "tableY_upstream_holdout"),
    ("classifier.paper_tables.tableZ_crossref",
     ("crossref_eval.json", CROSSREF), "tableZ_crossref"),
])
def test_table_script_writes_tex_and_md(tmp_path, monkeypatch,
                                        mod, fixture, stem):
    filename, data = fixture
    target = SACRED / filename
    if not target.exists():
        SACRED.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(data))
    monkeypatch.setenv("TABLE_OUT_DIR", str(tmp_path))
    r = subprocess.run([sys.executable, "-m", mod],
                       cwd=REPO, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    tex = tmp_path / f"{stem}.tex"
    md = tmp_path / f"{stem}.md"
    assert tex.exists() and md.exists()
    assert "\\begin{tabular}" in tex.read_text()
    assert "|" in md.read_text()

def test_tableY_caption_mentions_contamination_partition(tmp_path, monkeypatch):
    target = SACRED / "upstream_holdout.json"
    if not target.exists():
        SACRED.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(HOLDOUT))
    monkeypatch.setenv("TABLE_OUT_DIR", str(tmp_path))
    subprocess.run([sys.executable, "-m",
                    "classifier.paper_tables.tableY_upstream_holdout"],
                   cwd=REPO, check=True)
    tex = (tmp_path / "tableY_upstream_holdout.tex").read_text()
    assert "source_framework" in tex
    assert "source_id" in tex
    assert "never seen in training" in tex
```

- [ ] **Step 2: Run and commit**

```bash
pytest classifier/tests/paper_tables/ -x
git add classifier/paper_tables/ classifier/tests/paper_tables/
git commit -m "plan8: three-benchmark table renderers + tests"
```

---

## Phase C — HuggingFace model upload

### Task C1: `upload_model.py`

Unchanged from the 2026-04-07 plan Task C1 (see lines 517–586 of that file). The upload script, `SacredRunMismatch` behaviour, and dry-run contract are carried forward verbatim.

- [ ] **Step 1: Write the script** (verbatim from 2026-04-07 Task C1 Step 1)
- [ ] **Step 2: Commit**

```bash
git add classifier/publish/__init__.py classifier/publish/upload_model.py
git commit -m "plan8: upload_model.py with sacred-sha tag contract"
```

### Task C2: Jinja2 model-card renderer with honesty §6 verbatim **and** three-benchmark table **and** upstream attribution

**Files:**
- Create: `classifier/publish/model_card.py`
- Create: `classifier/publish/templates/model_card.md.j2`

- [ ] **Step 1: Write the template**

```jinja
---
license: cc-by-4.0
language: en
library_name: transformers
tags:
  - ai-security
  - framework-mapping
  - cross-encoder
  - crosswalk
model-index:
  - name: {{ repo_id }}
    results:
      - task:
          type: text-classification
          name: cross-framework control mapping
        metrics:
          - type: recall_at_3
            value: {{ metrics.recall_at_3 | round(4) }}
          - type: mrr
            value: {{ metrics.mrr | round(4) }}
          - type: ece
            value: {{ metrics.ece | round(4) }}
---

# AI Security Framework Crosswalk Classifier

Three-stage ensemble for mapping controls across AI security and
governance frameworks. Released as a research artifact by Rock Lambros.

Sacred-run git sha: `{{ sacred_sha }}`

## Intended use

Assisting compliance auditors, security researchers, and governance
lawyers in identifying candidate cross-framework control mappings.
Predictions are suggestions with calibrated confidence bands, not
authoritative compliance determinations.

## Evaluation --- three benchmarks reported side by side

### Table X --- Frozen test (primary; `human_test_frozen`, n=400)

| Metric | Value |
|---|---|
| Precision | {{ metrics.precision | round(4) }} |
| Recall | {{ metrics.recall | round(4) }} |
| F1 | {{ metrics.f1 | round(4) }} |
| Recall@3 | {{ metrics.recall_at_3 | round(4) }} |
| MRR | {{ metrics.mrr | round(4) }} |
| ECE | {{ metrics.ece | round(4) }} |
| Precision @ 80% coverage | {{ metrics.precision_at_80 | round(4) }} |

### Table Y --- Held-out upstream benchmark (independent second benchmark)

Drawn from the held-out subset of `data/upstream/mappings_v1.jsonl`,
partitioned by strict `(source_framework, source_id)` tuple key; never
seen in training. `n={{ upstream_holdout.held_out_row_count }}`.

| Metric | Value |
|---|---|
| Precision | {{ upstream_holdout.overall.precision | round(4) }} |
| Recall | {{ upstream_holdout.overall.recall | round(4) }} |
| F1 | {{ upstream_holdout.overall.f1 | round(4) }} |

### Table Z --- Crossref benchmark (`data/upstream/crossrefs_v1.jsonl`)

| Metric | Value |
|---|---|
| Precision | {{ crossref.overall.precision | round(4) }} |
| Recall | {{ crossref.overall.recall | round(4) }} |
| F1 | {{ crossref.overall.f1 | round(4) }} |

## Data provenance and upstream attribution

This classifier was trained on a combination of an internal 550-row
LLM-SME-labeled pool and the community-curated GenAI Security Project
GenAI Data Security Initiative crosswalk (CC BY-SA 4.0), pinned at
upstream commit `{{ upstream_commit_sha }}` and consumed read-only. See
`THIRD_PARTY_NOTICES.md` for the full attribution text.

The 150-row calibration pool used to set pre-registered tier-confidence
thresholds was sourced from train-eligible upstream rows rather than a
fresh project-native SME session; this substitution is disclosed in
`docs/methodology_notes/plan6-calibration-substitution.md` and discussed
in Section "Methodology Disclosure" of the accompanying paper. The
held-out upstream benchmark (Table Y) is reported separately to
demonstrate that the classifier does not merely echo upstream.

Upstream id-normalization rules (per-framework canonicalization of
`target_control_id`) are held locally under CC BY-SA 4.0 pending peer
review; see `data/upstream/README.md`.

## Pre-registered honesty commitments

{{ honesty_section_verbatim }}

## Limitations

- Trained on LLM-SME-derived labels (v1_calibrated, three-persona
  ensemble); inherits any systematic bias documented in the
  labeling-study appendix.
- Calibration pool substitution: see disclosure above.
- Evaluation on the three benchmarks listed; absolute numbers are only
  as reliable as those samples.
- Covers the source lists and targets present at release; new framework
  revisions require re-mapping.

## License

Model weights: CC-BY-4.0. Training data components are a mix of
CC BY-SA 4.0 (upstream crosswalk, OWASP DSGAI 2026 corpus) and
project-internal LLM-SME labels; see `THIRD_PARTY_NOTICES.md`.

## Citation

```bibtex
@misc{lambros2026crosswalk,
  title  = {Cross-Framework AI Security Control Mapping with
            Disagreement-Aware Multi-Task Learning},
  author = {Rock Lambros},
  year   = {2026},
  howpublished = {\url{https://huggingface.co/{{ repo_id }}}},
  note   = {git sha {{ sacred_sha }}; upstream commit {{ upstream_commit_sha }}}
}
```
```

- [ ] **Step 2: Write `model_card.py` renderer**

```python
# classifier/publish/model_card.py
from __future__ import annotations
import json
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape

REPO = Path(__file__).resolve().parents[2]
SPEC_HONESTY = REPO / "docs" / "superpowers" / "specs" / \
               "2026-04-07-ai-security-crosswalk-classifier-design.md"
MANIFEST = REPO / "third_party" / "genai-crosswalk" / "MANIFEST.json"
HOLDOUT = REPO / "data" / "sacred_run" / "upstream_holdout.json"
CROSSREF = REPO / "data" / "sacred_run" / "crossref_eval.json"

_HONESTY_HEADER = "## 6. Pre-Registered Honesty Commitments"

def extract_honesty_section() -> str:
    text = SPEC_HONESTY.read_text()
    i = text.index(_HONESTY_HEADER)
    j = text.index("\n## ", i + len(_HONESTY_HEADER))
    return text[i:j].strip()

def _load(path: Path, default: dict) -> dict:
    return json.loads(path.read_text()) if path.exists() else default

def render_model_card(results: dict, sacred_sha: str, repo_id: str) -> str:
    env = Environment(
        loader=FileSystemLoader(Path(__file__).parent / "templates"),
        autoescape=select_autoescape([]), keep_trailing_newline=True)
    tmpl = env.get_template("model_card.md.j2")
    upstream_sha = "UNKNOWN"
    if MANIFEST.exists():
        upstream_sha = json.loads(MANIFEST.read_text()).get(
            "upstream_commit_sha", "UNKNOWN")
    return tmpl.render(
        repo_id=repo_id,
        sacred_sha=sacred_sha,
        upstream_commit_sha=upstream_sha,
        metrics=results["metrics"],
        upstream_holdout=_load(HOLDOUT, {
            "held_out_row_count": 0,
            "overall": {"precision": 0, "recall": 0, "f1": 0}}),
        crossref=_load(CROSSREF, {
            "overall": {"precision": 0, "recall": 0, "f1": 0}}),
        honesty_section_verbatim=extract_honesty_section(),
    )
```

- [ ] **Step 3: Commit**

```bash
git add classifier/publish/model_card.py \
        classifier/publish/templates/model_card.md.j2
git commit -m "plan8: model card template with three benchmarks + upstream attribution"
```

### Task C3: Dry-run + honesty + three-benchmark + upstream-attribution tests

**Files:**
- Create: `classifier/tests/publish/__init__.py`
- Create: `classifier/tests/publish/test_upload_model_dryrun.py`
- Create: `classifier/tests/publish/test_model_card_honesty.py`

- [ ] **Step 1: Dry-run test** (same as 2026-04-07 plan Task C3 Step 1).

- [ ] **Step 2: Honesty + three-benchmark + upstream attribution test (Contracts 12, 14, 15)**

```python
# classifier/tests/publish/test_model_card_honesty.py
import json, re
from pathlib import Path

from classifier.publish.model_card import (
    render_model_card, extract_honesty_section)

REPO = Path(__file__).resolve().parents[3]

FIXTURE_METRICS = {
    "precision": 0.80, "recall": 0.72, "f1": 0.758,
    "recall_at_1": 0.60, "recall_at_3": 0.88,
    "recall_at_5": 0.93, "mrr": 0.71, "ndcg_at_10": 0.82,
    "ece": 0.05, "precision_at_80": 0.86,
}

def _card() -> str:
    return render_model_card(
        results={"metrics": FIXTURE_METRICS, "per_pair": []},
        sacred_sha="deadbeefcafebabe",
        repo_id="rocklambros/ai-security-crosswalk")

def test_honesty_section_extracted_and_rendered_verbatim():
    honesty = extract_honesty_section()
    for i in range(1, 9):
        assert re.search(rf"^{i}\.\s", honesty, re.M), f"commitment {i} missing"
    card = _card()
    for line in honesty.splitlines():
        s = line.strip()
        if not s:
            continue
        assert s in card, f"missing verbatim line: {s!r}"

def test_card_reports_all_three_benchmarks():
    card = _card()
    assert "Table X --- Frozen test" in card
    assert "Table Y --- Held-out upstream benchmark" in card
    assert "Table Z --- Crossref benchmark" in card
    # Contract 14: no cherry-picking --- frozen F1 alone is not enough
    assert "`data/upstream/mappings_v1.jsonl`" in card
    assert "`data/upstream/crossrefs_v1.jsonl`" in card

def test_card_attributes_upstream_and_license():
    card = _card()
    assert "GenAI Security Project" in card
    assert "CC BY-SA 4.0" in card
    assert "upstream commit" in card
    assert "data/upstream/README.md" in card
    assert "plan6-calibration-substitution.md" in card

def test_card_does_not_mention_ai_attribution():
    card = _card()
    for s in ("Claude", "Anthropic", "AI-assisted", "Co-Authored-By",
              "Generated with"):
        assert s not in card
```

- [ ] **Step 3: Run and commit**

```bash
pytest classifier/tests/publish/ -x
git add classifier/tests/publish/
git commit -m "plan8: model card honesty + three-benchmark + upstream tests"
```

---

## Phase D — HuggingFace dataset upload

### Task D1: `upload_dataset.py` + dataset card (with upstream disclosure)

**Files:**
- Create: `classifier/publish/upload_dataset.py` (verbatim from 2026-04-07 Task D1 Step 3)
- Create: `classifier/publish/dataset_card.py`
- Create: `classifier/publish/templates/dataset_card.md.j2`

- [ ] **Step 1: Write the dataset card template**

Same structure as the 2026-04-07 template, with these additions appended:

```markdown
## Upstream provenance

This dataset is a mix of project-internal LLM-SME labels
(`provenance_tag = llm_sme_v1`) and train-eligible rows drawn from the
GenAI Security Project GenAI Data Security Initiative crosswalk
(`provenance_tag = upstream_v1`), pinned at upstream commit
`{{ upstream_commit_sha }}` and licensed CC BY-SA 4.0. See
`THIRD_PARTY_NOTICES.md`.

The `human_test_frozen` split is NOT included in this dataset upload ---
it is referenced by hash only (see `data/splits/hashes.json`). The
`human_cal` split was sourced from train-eligible upstream rows rather
than a fresh project-native SME session; see the Methodology Disclosure
section of the accompanying paper and
`docs/methodology_notes/plan6-calibration-substitution.md`.

ShareAlike obligation: downstream redistribution of the upstream-sourced
rows inherits CC BY-SA 4.0. Project-internal LLM-SME rows are released
under CC-BY-4.0 as a compatible license, but the mixed distribution is
marked CC BY-SA 4.0 to preserve the ShareAlike obligation on the
upstream subset.
```

- [ ] **Step 2: Write `dataset_card.py` renderer** (pattern identical to `model_card.py`; reads `MANIFEST.json` for `upstream_commit_sha`).

- [ ] **Step 3: Write `upload_dataset.py`** (verbatim from 2026-04-07 Task D1 Step 3; `ALLOWED_SPLITS` unchanged, `human_test_frozen` still excluded).

- [ ] **Step 4: Commit**

```bash
git add classifier/publish/upload_dataset.py \
        classifier/publish/dataset_card.py \
        classifier/publish/templates/dataset_card.md.j2
git commit -m "plan8: dataset card with upstream provenance + ShareAlike disclosure"
```

### Task D2: Dry-run test + `human_test_frozen` guard

Identical to 2026-04-07 Task D2 (the `human_test_frozen` exclusion test remains; the only addition is a grep assertion that the rendered card contains `GenAI Security Project`, `CC BY-SA 4.0`, and `upstream commit`).

- [ ] **Step 1: Write test** (as 2026-04-07 D2 Step 1 plus the new assertions)
- [ ] **Step 2: Run and commit**

```bash
pytest classifier/tests/publish/test_upload_dataset_dryrun.py -x
git add classifier/tests/publish/test_upload_dataset_dryrun.py
git commit -m "plan8: dataset dry-run + frozen guard + upstream disclosure"
```

---

## Phase E — Blog post draft

### Task E1: `docs/blog/2026-XX-XX-ai-security-crosswalk.md`

- [ ] **Step 1: Write the draft**

3–5k words. Structure (expanded from the 2026-04-07 plan to cover the §7 delta):

1. Hook — cross-framework mapping is painful for auditors.
2. What the relevant frameworks cover and why they don't talk.
3. The problem with prior v2 composite (20–30% tier accuracy).
4. Enter the GenAI Security Project crosswalk — 41 hand-curated JSON entries, ~1,800 mappings, CC BY-SA 4.0. Framed as "aligned second signal", not "authoritative replacement".
5. LLM-SME labeling protocol: 3 personas, reference grounding, Sonnet↔Opus study.
6. Architecture: cross-encoder + GAT + LightGBM + Mondrian conformal.
7. Three benchmarks side by side:
   - Table X frozen test — `{{ FROZEN_F1 }}` / `{{ FROZEN_R3 }}` (placeholders resolved at publish)
   - Table Y held-out upstream — `{{ HOLDOUT_F1 }}` on `{{ HOLDOUT_N }}` rows never seen in training
   - Table Z crossref — `{{ CROSSREF_F1 }}` on LLM↔Agentic↔DSGAI edges
8. Methodology disclosure — calibration substitution, why, and the mitigation (Table Y reported alongside).
9. Contamination methodology — strict `(source_framework, source_id)` tuple, two-layer defense.
10. What failed — the honesty list from the 2026-04-07 spec §6.
11. Reproduction in one command (`make reproduce`).
12. Links: arXiv, HF model, HF dataset, GitHub, HF Space, upstream repo URL with pinned SHA, `THIRD_PARTY_NOTICES.md`.

No AI attribution anywhere in the post.

- [ ] **Step 2: Commit**

```bash
git add docs/blog/2026-XX-XX-ai-security-crosswalk.md
git commit -m "plan8: blog post draft with three benchmarks and upstream attribution"
```

---

## Phase F — Repo polish

### Task F1: README + LICENSE + badges

Unchanged from 2026-04-07 Task F1 except the `README.md` reproduction section additionally includes a two-line block pointing at `THIRD_PARTY_NOTICES.md` and stating the upstream CC BY-SA 4.0 attribution.

- [ ] **Step 1: Write `LICENSE`** (Apache-2.0, copyright 2026 Rock Lambros).
- [ ] **Step 2: Append to `README.md`** (reproduction + badges + the new upstream-attribution line).
- [ ] **Step 3: Write the tests** (as 2026-04-07 F1 Step 3).
- [ ] **Step 4: Run and commit**

```bash
pytest classifier/tests/repo/test_readme_reproduce.py \
       classifier/tests/repo/test_license.py -x
git add README.md LICENSE classifier/tests/repo/__init__.py \
        classifier/tests/repo/test_readme_reproduce.py \
        classifier/tests/repo/test_license.py
git commit -m "plan8: README reproduction + LICENSE Apache-2.0 + badges + upstream note"
```

### Task F1.5: Delete the pre-classifier archive

Identical to 2026-04-07 Task F1.5. Gated on the sacred-run lockfile.

### Task F2: CITATION.cff + frozen requirements.txt

Identical to 2026-04-07 Task F2. The `test_citation_cff.py` attribution guard already covers Claude / Anthropic / AI-assisted.

---

## Phase G — GitHub Actions CI

### Task G1: `.github/workflows/ci.yml`

Extend the 2026-04-07 workflow to additionally run:

```yaml
- name: Paper section guards
  run: pytest classifier/tests/paper/ -x
- name: Table renderers
  run: pytest classifier/tests/paper_tables/ -x
```

- [ ] **Step 1: Write the workflow** (2026-04-07 G1 Step 1 + the two new steps above).
- [ ] **Step 2: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "plan8: CI incl. paper section guards + table renderers"
```

---

## Phase H — Reproduction one-liner

### Task H1: `Makefile` + `make reproduce`

Unchanged from 2026-04-07 Task H1. `make reproduce` still runs `verify-hashes → eval-llm-val → diff-sacred`. The three new benchmarks are built by Plan 5 and Plan 6 and surfaced here read-only; Plan 8's `make reproduce` does not re-run them.

- [ ] **Step 1: Write `Makefile`** (verbatim from 2026-04-07).
- [ ] **Step 2: Write the test** (verbatim from 2026-04-07).
- [ ] **Step 3: Run and commit**

```bash
pytest classifier/tests/repo/test_reproduce_make_target.py -x
git add Makefile classifier/tests/repo/test_reproduce_make_target.py
git commit -m "plan8: make reproduce one-liner target"
```

---

## Self-Review Checklist

Before declaring Plan 8 complete, verify each item and map it to the 2026-04-08 upstream-integration spec:

- [ ] **Spec §1 (motivation)** — `paper/sections/intro.tex` ports the 41-entry / ~1,800-mapping / CC BY-SA 4.0 framing and positions this work as an aligned consumer. Task A1 Step 2.
- [ ] **Spec §6 (evaluation strategy — three benchmarks)** — Tables X, Y, Z are rendered by `classifier/paper_tables/` and included in `paper/sections/results.tex`. Tasks BP1, BP2, BP3, BP4. `test_tables_render.py` green.
- [ ] **Spec §7 Plan 8 delta: held-out upstream benchmark** — Table Y implemented, rendered, included in paper, included in model card, included in blog post. Contract 14 enforced by `test_model_card_honesty.py::test_card_reports_all_three_benchmarks`.
- [ ] **Spec §7 Plan 8 delta: crossref benchmark** — Table Z implemented, rendered, included in paper, included in model card, included in blog post.
- [ ] **Spec §7 Plan 8 delta: upstream acknowledgement + license** — `paper/sections/related.tex`, `paper/sections/acknowledgements.tex`, `paper/sections/license_compliance.tex`, model card, dataset card, README all carry CC BY-SA 4.0 attribution + upstream commit SHA. Contract 15 enforced by `test_sections_acknowledge_upstream.py` and `test_model_card_honesty.py::test_card_attributes_upstream_and_license`.
- [ ] **Spec §7 Plan 8 delta: Plan 6 substitution disclosure** — `paper/sections/methodology_disclosure.tex` cites `docs/methodology_notes/plan6-calibration-substitution.md`, names the trade-off, and explains the Table Y mitigation. Contract 16 enforced by `test_sections_disclose_substitution.py`.
- [ ] **Spec §8 risk row on paper methodology criticism** — methodology disclosure section frames the trade-off honestly and does NOT claim upstream is categorically better; `test_disclosure_frames_tradeoff_not_claim_of_superiority` asserts the explicit non-claim string.
- [ ] **Contamination methodology** — `paper/sections/contamination.tex` describes strict `(source_framework, source_id)` tuple partition, Rules 1 + 2, two-layer defense, non-skippable test. Enforced by `test_sections_contamination.py`.
- [ ] **Id-normalization footnote** — `paper/sections/dataset.tex` cites `data/upstream/README.md` and the 0.235 → 0.826 resolution rates.
- [ ] **2026-04-07 spec §4.6 deliverables** — carried forward unchanged: arXiv scaffold, HF model, HF dataset, blog post, GitHub repo polish.
- [ ] **2026-04-07 spec §6 honesty commitments** — all 8 numbered items appear character-identical in the rendered model card. Contract 12, `test_honesty_section_extracted_and_rendered_verbatim`.
- [ ] **Contract 1 — hash verification at entry** — `make reproduce` calls `verify_hashes` as its first step.
- [ ] **Contract 1-bis — `human_test_frozen` untouched** — no Plan 8 script opens the file; dataset uploader explicitly excludes it.
- [ ] **Contract 13 — sacred-run git_sha tag** — both uploaders surface the tag in dry-run output.
- [ ] **Contract 14 — three-benchmark reporting parity** — model card, dataset card, blog post, paper results all report all three benchmarks; no cherry-picking.
- [ ] **Contract 15 — upstream acknowledgement verbatim** — upstream repo URL + pinned commit SHA + `CC BY-SA 4.0` literal present in related.tex, acknowledgements.tex, and model card.
- [ ] **Contract 16 — Plan 6 substitution disclosure non-skippable** — methodology_disclosure.tex cites the note, names the trade-off.
- [ ] **Attribution guards** — no commit message, no paper section, no model card, no dataset card, no blog post, and no CITATION.cff mentions Claude / Anthropic / AI-assisted / Co-Authored-By. Enforced by `test_no_ai_attribution.py`, `test_model_card_honesty.py::test_card_does_not_mention_ai_attribution`, and `test_citation_cff.py`. Author is Rock Lambros only.
- [ ] **Anti-scope** — no new evaluations beyond the three listed; no revision of pre-registered frozen-test thresholds; no scope-creep into Plan 5 (training) or Plan 6 (sacred run); upstream is framed as "independent second signal", not "categorically better"; no AI attribution.
- [ ] **No training, no LLM calls, no GPU** — Plan 8 adds no torch / sentence-transformers / anthropic imports beyond what is already in `requirements.txt`. Budget: $0.
- [ ] **Read-only inputs** — no task modifies `paper/tables/*` (except rendering into it from `classifier/paper_tables/`), `data/sacred_run/*`, `data/splits/*`, `data/labels/*`, `data/upstream/*`, `third_party/genai-crosswalk/*`, `docs/methodology_notes/*`, `THIRD_PARTY_NOTICES.md`, or the 2026-04-07 plan file.

---

## Lessons Carried (restated)

1. **Do not retune at writeup time.** Frozen numbers + held-out upstream numbers + crossref numbers are all consumed verbatim.
2. **Dry-run by default.** Every HF uploader defaults to `--dry-run`.
3. **Verbatim is non-negotiable.** Honesty commitments and upstream attribution are copy-pasted substrings, enforced by tests.
4. **Three benchmarks always together.** Contract 14 forbids cherry-picking the frozen headline alone.
5. **Disclosure over cleverness.** The Plan 6 calibration substitution is disclosed plainly; the mitigation (Table Y alongside) is the empirical response to the criticism, not a rhetorical one.
6. **Attribution is the author's alone.** No AI co-author, anywhere. Enforced by tests.

---

## Next Step

Execute Plan 8 via superpowers:subagent-driven-development or superpowers:executing-plans, one task at a time. After Phase H lands, the repo is ready for the human-driven final steps: submit arXiv, flip uploaders to `--no-dry-run`, publish the blog post, announce.
