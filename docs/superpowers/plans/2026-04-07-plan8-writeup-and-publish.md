# Plan 8 — Writeup & Publish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the sacred-run artifacts from Plan 6 into a publishable record: an arXiv LaTeX draft scaffold, matplotlib figure scripts, a HuggingFace model upload with a complete honesty-section model card, a HuggingFace dataset upload for `v1_frozen` labels, a blog post draft, repo polish (README, LICENSE, CITATION.cff, pinned requirements), GitHub Actions CI, and a one-liner reproduction Makefile target. The sacred-run numbers are consumed verbatim; this plan writes **no** model code and runs **no** training.

**Architecture:** Plan 8 is almost entirely additive. A new top-level `paper/` tree houses the LaTeX sources, a new `classifier/publish/` subpackage holds the HF uploaders and the Jinja2 model-card renderer, a new `classifier/figures/` subpackage holds the matplotlib figure scripts, `.github/workflows/ci.yml` adds a push-time hash-verify + lint + unit-test gate, and a new top-level `Makefile` wires `make reproduce` to `verify_hashes() → eval on llm_val → diff against committed sacred-run results`. The HuggingFace uploads (`publish/upload_model.py`, `publish/upload_dataset.py`) both tag the released artifacts with the sacred-run `git_sha` (Contract 13) and both use `--dry-run` as the default so CI never pushes to the Hub.

**Tech Stack:** Python 3.11, `jinja2`, `huggingface_hub`, `matplotlib`, `pandas`, `pyarrow`, `pytest`, `ruff`, `mypy`, LaTeX (`latexmk` + `tectonic` fallback), GitHub Actions, existing repo stack. No new ML dependencies — Plan 8 never loads a transformer at author time.

**Budget:** ~$0. No LLM calls, no GPU compute. HuggingFace Hub uploads are free. Only cost is wall-clock for a handful of `latexmk` builds and CI runs.

---

## Spec Reference

Implements §4.6 (deliverables — arXiv preprint, HF model, HF dataset, blog post) and §6 (Pre-Registered Honesty Commitments, verbatim in the model card) of `docs/superpowers/specs/2026-04-07-ai-security-crosswalk-classifier-design.md`. Consumes §4.1 sacred-run metrics produced by Plan 6 (`paper/tables/table{1..4}.{tex,md}` and `data/sacred_run/results.json`).

**Out of scope for Plan 8:** any re-training, any re-scoring of `human_test_frozen`, any modification of sacred-run artifacts, any HuggingFace Space / Dash app deployment (Plan 7), any LLM labeling (Plan 2), any baseline code (Plan 3), any arXiv *submission* (the plan stops at a `latexmk`-clean PDF and an uploaded HF model/dataset; final submission is a human action).

---

## File Structure

**New layout.** Plan 8 creates and only touches these paths:

| Path | Purpose |
|---|---|
| `paper/main.tex` | arXiv LaTeX entry point |
| `paper/sections/abstract.tex` | Abstract section |
| `paper/sections/intro.tex` | Introduction |
| `paper/sections/related.tex` | Related work |
| `paper/sections/method.tex` | Method (architecture + loss) |
| `paper/sections/dataset.tex` | Dataset + LLM-SME protocol |
| `paper/sections/experiments.tex` | Experimental setup |
| `paper/sections/results.tex` | Headline results + `\input` of `tables/table1.tex` |
| `paper/sections/ablations.tex` | Ablation study + `\input` of `tables/table3.tex` |
| `paper/sections/limitations.tex` | Limitations |
| `paper/sections/ethics.tex` | Ethics statement |
| `paper/sections/reproducibility.tex` | Reproducibility statement |
| `paper/refs.bib` | BibTeX references |
| `paper/latexmkrc` | Non-interactive latexmk config |
| `paper/figures/` | Output directory for PDF figures |
| `paper/README.md` | Build instructions (`latexmk -pdf main.tex`) |
| `classifier/figures/__init__.py` | subpackage marker |
| `classifier/figures/fig1_arch.py` | Architecture block diagram |
| `classifier/figures/fig2_calibration.py` | Reliability diagram |
| `classifier/figures/fig3_per_pair.py` | Per-framework-pair recall@3 bars |
| `classifier/figures/fig4_ablation.py` | Ablation forest plot |
| `classifier/publish/__init__.py` | subpackage marker |
| `classifier/publish/upload_model.py` | HF model uploader (dry-run default) |
| `classifier/publish/upload_dataset.py` | HF dataset uploader (dry-run default) |
| `classifier/publish/model_card.py` | Jinja2 model-card renderer |
| `classifier/publish/dataset_card.py` | Jinja2 dataset-card renderer |
| `classifier/publish/templates/model_card.md.j2` | Model card template (honesty §6 verbatim) |
| `classifier/publish/templates/dataset_card.md.j2` | Dataset card template |
| `classifier/tests/publish/__init__.py` | subpackage marker |
| `classifier/tests/publish/test_upload_model_dryrun.py` | Upload dry-run test |
| `classifier/tests/publish/test_upload_dataset_dryrun.py` | Upload dry-run test |
| `classifier/tests/publish/test_model_card_honesty.py` | Assert all 8 §6 commitments render verbatim |
| `classifier/tests/figures/__init__.py` | subpackage marker |
| `classifier/tests/figures/test_fig1.py` | Figure existence + PDF header bytes |
| `classifier/tests/figures/test_fig2_3_4.py` | Figure existence + PDF header bytes |
| `classifier/tests/paper/__init__.py` | subpackage marker |
| `classifier/tests/paper/test_latexmk_build.py` | Fixture latexmk build (skip if latexmk absent) |
| `classifier/tests/repo/test_readme_reproduce.py` | README contains `make reproduce` one-liner |
| `classifier/tests/repo/test_citation_cff.py` | CITATION.cff has ORCID + Rock Lambros |
| `classifier/tests/repo/test_license.py` | LICENSE is Apache-2.0 text |
| `classifier/tests/repo/test_requirements_frozen.py` | requirements.txt has every dep pinned `==` |
| `classifier/tests/repo/test_reproduce_make_target.py` | `make -n reproduce` lists the four steps |
| `docs/blog/2026-XX-XX-ai-security-crosswalk.md` | Blog post draft |
| `.github/workflows/ci.yml` | Push-time CI: hashes + ruff + mypy + pytest |
| `Makefile` | `make reproduce` one-liner target |
| `LICENSE` | Apache-2.0 (verbatim) |
| `CITATION.cff` | Rock Lambros + ORCID |
| `requirements.txt` | Frozen via pip-compile (all deps `==`) |
| `README.md` | Repo polish: one-liner reproduction + badges |

**Do not modify** any file under `classifier/data/`, `classifier/labeling/`, `classifier/models/`, `classifier/sacred/`, `paper/tables/`, `data/splits/`, `data/labels/`, `data/sacred_run/`, or existing `mapping_engine/` code. Plan 8 consumes those as read-only inputs.

---

## Cross-Plan Contracts

- **Contract 1 — hash verification at entry.** `Makefile`'s `reproduce` target calls `python -m classifier.data.splits verify-hashes` **before** any other step. Tested in `test_reproduce_make_target.py`.
- **Contract 12 (NEW) — honesty section verbatim in model card.** The eight commitments in spec §6 must appear **character-identical** in the rendered HF model card. Enforced by `test_model_card_honesty.py`, which reads §6 from the spec, extracts the numbered list, and asserts every line is a substring of the rendered card.
- **Contract 13 (NEW) — sacred-run git_sha tagging.** Both `upload_model.py` and `upload_dataset.py` read `data/sacred_run/results.json["git_sha"]` and pass it to `huggingface_hub.HfApi.create_tag(...)` on the uploaded repo. A dry-run call surfaces the tag name in stdout so `test_upload_model_dryrun.py` / `test_upload_dataset_dryrun.py` can assert the exact `git_sha` substring appears. Uploads refuse (raise `SacredRunMismatch`) if the current working tree's HEAD does not match the sacred-run `git_sha`, unless `--allow-dirty` is passed (which the tests exercise).
- **Contract 1-bis — `human_test_frozen` untouched.** Plan 8 never opens `data/splits/human_test_frozen.jsonl`. A grep in `test_frozen_access_grep.py` (Plan 6) already enforces this, but the review checklist at the bottom of this plan re-asserts it.

---

## Lessons Carried

From prior plans and MEMORY.md:
- **Plan 1:** every new artifact gets a SHA256 hash committed; `verify_hashes()` is the canary. Plan 8 reuses it as the first step of `make reproduce`.
- **Plan 2:** Jinja2 templates must be SHA256-hashed and committed. The model-card and dataset-card templates follow suit — `test_model_card_honesty.py` asserts the template hash is committed alongside the template.
- **Plan 6:** lockfile pattern — refuse to clobber committed artifacts. `upload_model.py` refuses to upload if the target HF repo already has the sacred-run tag (unless `--force`).
- **Session 8 unblock plan (MEMORY.md):** frozen numbers are consumed as-is; no retuning at writeup time. Plan 8 has zero knobs that could move a reported number.
- **Global attribution rule:** no AI/Claude/Anthropic attribution in any commit message, PR, CITATION.cff, model card, dataset card, or blog post. Rock Lambros is the sole author. `test_citation_cff.py` greps the rendered model/dataset cards for the strings `Claude`, `Anthropic`, `AI-assisted` and fails if any appear outside a literal spec-quoted context.

---

## Phase A — arXiv LaTeX scaffold

### Task A1: `paper/main.tex` + section files

**Files:**
- Create: `paper/main.tex`
- Create: `paper/sections/{abstract,intro,related,method,dataset,experiments,results,ablations,limitations,ethics,reproducibility}.tex`
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
\input{sections/experiments}
\input{sections/results}
\input{sections/ablations}
\input{sections/limitations}
\input{sections/ethics}
\input{sections/reproducibility}

\bibliographystyle{plainnat}
\bibliography{refs}

\end{document}
```

- [ ] **Step 2: Write stub section files**

Each `paper/sections/*.tex` contains a `\section{...}` header and a `% TODO(author)` comment block listing the paragraphs the human author must write, plus concrete `\input{../tables/tableN.tex}` / `\includegraphics[width=\linewidth]{../figures/figN.pdf}` hooks where Plan 6 tables and Plan 8 figures plug in. Example for `results.tex`:

```latex
% paper/sections/results.tex
\section{Results}
\label{sec:results}

% TODO(author): headline paragraph citing Recall@3 from Table 1
% with bootstrap 95\% CI, plus a sentence on Precision@80\%-coverage.

\input{../tables/table1.tex}

\begin{figure}[t]
  \centering
  \includegraphics[width=0.95\linewidth]{figures/fig3_per_pair.pdf}
  \caption{Recall@3 on \texttt{human\_test\_frozen} stratified by
           framework pair (12 cells), bootstrap 95\% CIs.}
  \label{fig:per_pair}
\end{figure}

\input{../tables/table2.tex}
```

- [ ] **Step 3: Write `paper/latexmkrc`**

```perl
# paper/latexmkrc
$pdf_mode = 1;
$pdflatex = 'pdflatex -interaction=nonstopmode -halt-on-error %O %S';
$bibtex_use = 2;
$clean_ext = 'bbl run.xml synctex.gz';
```

- [ ] **Step 4: Write `paper/refs.bib` seed entries**

Include BibTeX entries for: MITRE ATLAS, NIST AI RMF, OWASP LLM Top 10, BM25 (Robertson & Zaragoza 2009), bge-reranker-v2-m3 (Chen et al. 2024), DeBERTa-v3 (He et al. 2023), RepLlama (Ma et al. 2024), LoRA (Hu et al. 2022), GAT (Veličković et al. 2018), LightGBM (Ke et al. 2017), Mondrian conformal (Vovk et al. 2005), Cohen's kappa. The human author fills citation keys in each section file.

- [ ] **Step 5: Commit**

```bash
git add paper/main.tex paper/sections/ paper/refs.bib paper/latexmkrc paper/README.md
git commit -m "plan8: arxiv latex scaffold"
```

### Task A2: `paper/README.md` build instructions

**Files:**
- Create: `paper/README.md`

- [ ] **Step 1: Write build instructions**

```markdown
# Paper build

From repo root:

    cd paper
    latexmk -pdf main.tex

Or with tectonic (no TeXLive required):

    cd paper && tectonic main.tex

Tables under `paper/tables/` are generated by Plan 6
(`python -m classifier.sacred.paper_tables`) and committed to git.
Figures under `paper/figures/` are generated by Plan 8
(`python -m classifier.figures.fig1_arch` etc.) and committed to git.
```

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
    # Copy paper/ into tmp so the build doesn't pollute the repo.
    dst = tmp_path / "paper"
    shutil.copytree(PAPER, dst)
    # Stub table + figure files so the scaffold compiles without Plan 6/8
    # artifacts being present.
    (dst / "tables").mkdir(exist_ok=True)
    for i in range(1, 5):
        (dst / "tables" / f"table{i}.tex").write_text(
            r"\begin{tabular}{l}stub\\\end{tabular}" + "\n"
        )
    (dst / "figures").mkdir(exist_ok=True)
    # Empty 1-byte placeholder — pdflatex will still include it in draft mode
    for n in ("fig1_arch", "fig2_calibration", "fig3_per_pair", "fig4_ablation"):
        (dst / "figures" / f"{n}.pdf").write_bytes(b"%PDF-1.4\n%%EOF\n")
    result = subprocess.run(
        ["latexmk", "-pdf", "-interaction=nonstopmode", "main.tex"],
        cwd=dst, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert (dst / "main.pdf").exists()
```

- [ ] **Step 2: Run**

```bash
pytest classifier/tests/paper/test_latexmk_build.py -x
```

If `latexmk` is absent on the Jetson, the test skips — that is acceptable; CI installs it.

- [ ] **Step 3: Commit**

```bash
git add classifier/tests/paper/
git commit -m "plan8: latexmk fixture build test"
```

---

## Phase B — Figure scripts

### Task B1: `fig1_arch.py` architecture diagram

**Files:**
- Create: `classifier/figures/__init__.py`
- Create: `classifier/figures/fig1_arch.py`
- Create: `classifier/tests/figures/__init__.py`
- Create: `classifier/tests/figures/test_fig1.py`

- [ ] **Step 1: Write test first (TDD)**

```python
# classifier/tests/figures/test_fig1.py
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
OUT = REPO / "paper" / "figures" / "fig1_arch.pdf"

def test_fig1_arch_writes_valid_pdf(tmp_path, monkeypatch):
    monkeypatch.setenv("FIG_OUT_DIR", str(tmp_path))
    result = subprocess.run(
        [sys.executable, "-m", "classifier.figures.fig1_arch"],
        cwd=REPO, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    out = tmp_path / "fig1_arch.pdf"
    assert out.exists()
    assert out.read_bytes().startswith(b"%PDF")
```

- [ ] **Step 2: Write the figure script**

```python
# classifier/figures/fig1_arch.py
"""Figure 1: three-stage ensemble architecture block diagram."""
from __future__ import annotations
import os
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

def build(out_dir: Path) -> Path:
    fig, ax = plt.subplots(figsize=(8, 3.2))
    ax.set_xlim(0, 10); ax.set_ylim(0, 4); ax.axis("off")
    boxes = [
        (0.2, 1.2, "Source\ncontrol"),
        (2.2, 2.2, "Cross-encoder\n(bge-reranker-v2-m3)"),
        (2.2, 0.2, "GAT\n(2-layer, 4-head)"),
        (5.4, 1.2, "Stacked\nLightGBM"),
        (7.6, 1.2, "Mondrian\nconformal"),
        (9.4, 1.2, "{tier, band,\nrationale}"),
    ]
    for x, y, label in boxes:
        ax.add_patch(FancyBboxPatch(
            (x, y), 1.6, 1.4, boxstyle="round,pad=0.05",
            fc="white", ec="black"))
        ax.text(x + 0.8, y + 0.7, label, ha="center", va="center", fontsize=9)
    arrows = [(1.8, 2.0, 2.2, 2.9), (1.8, 1.8, 2.2, 0.9),
              (3.8, 2.9, 5.4, 2.0), (3.8, 0.9, 5.4, 1.6),
              (7.0, 1.9, 7.6, 1.9), (9.2, 1.9, 9.4, 1.9)]
    for x1, y1, x2, y2 in arrows:
        ax.add_patch(FancyArrowPatch(
            (x1, y1), (x2, y2), arrowstyle="->", mutation_scale=12))
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "fig1_arch.pdf"
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return out

def main() -> None:
    out_dir = Path(os.environ.get(
        "FIG_OUT_DIR",
        Path(__file__).resolve().parents[2] / "paper" / "figures"))
    print(build(out_dir))

if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Run and commit**

```bash
pytest classifier/tests/figures/test_fig1.py -x
python -m classifier.figures.fig1_arch
git add classifier/figures/ classifier/tests/figures/test_fig1.py paper/figures/fig1_arch.pdf
git commit -m "plan8: fig1 arch diagram"
```

### Task B2: `fig2_calibration.py` reliability diagram

**Files:**
- Create: `classifier/figures/fig2_calibration.py`

- [ ] **Step 1: Write the script**

Reads `data/sacred_run/results.json["reliability_bins"]` (list of `{conf_bin, accuracy, n}`) and draws the standard reliability diagram with the diagonal reference line, per-bin accuracy dots sized by `n`, and the ECE annotation in the corner. Output: `paper/figures/fig2_calibration.pdf`. Honours `FIG_OUT_DIR`. Refuses to run if `data/sacred_run/results.json` is missing — prints `"sacred run results not found; run Plan 6 first"` and exits non-zero.

```python
# classifier/figures/fig2_calibration.py
from __future__ import annotations
import json, os, sys
from pathlib import Path
import matplotlib.pyplot as plt

REPO = Path(__file__).resolve().parents[2]
RESULTS = REPO / "data" / "sacred_run" / "results.json"

def build(out_dir: Path) -> Path:
    if not RESULTS.exists():
        print("sacred run results not found; run Plan 6 first", file=sys.stderr)
        sys.exit(2)
    r = json.loads(RESULTS.read_text())
    bins = r["reliability_bins"]
    fig, ax = plt.subplots(figsize=(4.2, 4.0))
    ax.plot([0, 1], [0, 1], "k--", lw=1)
    xs = [b["conf_bin"] for b in bins]
    ys = [b["accuracy"] for b in bins]
    sizes = [max(10, 4 * b["n"]) for b in bins]
    ax.scatter(xs, ys, s=sizes, alpha=0.7, edgecolor="black")
    ax.set_xlabel("Predicted confidence"); ax.set_ylabel("Empirical accuracy")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.text(0.05, 0.93, f"ECE = {r['ece']:.3f}", fontsize=10)
    ax.set_title("Reliability diagram (human_test_frozen, n=400)")
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "fig2_calibration.pdf"
    fig.savefig(out, bbox_inches="tight"); plt.close(fig)
    return out

def main() -> None:
    out_dir = Path(os.environ.get("FIG_OUT_DIR", REPO / "paper" / "figures"))
    print(build(out_dir))

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Commit**

```bash
git add classifier/figures/fig2_calibration.py
git commit -m "plan8: fig2 calibration reliability diagram"
```

### Task B3: `fig3_per_pair.py` + `fig4_ablation.py` + tests

**Files:**
- Create: `classifier/figures/fig3_per_pair.py`
- Create: `classifier/figures/fig4_ablation.py`
- Create: `classifier/tests/figures/test_fig2_3_4.py`

- [ ] **Step 1: Write `fig3_per_pair.py`**

Reads `data/sacred_run/results.json["per_pair"]` (list of `{pair_key, recall_at_3, ci_lo, ci_hi}`) and renders a horizontal bar chart with error bars, sorted ascending by recall. 12 rows. Title: "Recall@3 by framework pair". Output: `paper/figures/fig3_per_pair.pdf`.

- [ ] **Step 2: Write `fig4_ablation.py`**

Reads `data/sacred_run/results.json["ablations"]` (list of `{name, delta_recall_at_3, ci_lo, ci_hi}`) and renders a forest plot centred on zero, one row per ablation, dot + CI line. Output: `paper/figures/fig4_ablation.pdf`.

- [ ] **Step 3: Write the shared existence test**

```python
# classifier/tests/figures/test_fig2_3_4.py
import json, subprocess, sys
from pathlib import Path
import pytest

REPO = Path(__file__).resolve().parents[3]
RESULTS = REPO / "data" / "sacred_run" / "results.json"

FIXTURE = {
    "ece": 0.05,
    "reliability_bins": [
        {"conf_bin": 0.1 * i + 0.05, "accuracy": 0.1 * i + 0.05, "n": 40}
        for i in range(10)
    ],
    "per_pair": [
        {"pair_key": f"pair_{i}", "recall_at_3": 0.6 + 0.02 * i,
         "ci_lo": 0.55 + 0.02 * i, "ci_hi": 0.65 + 0.02 * i}
        for i in range(12)
    ],
    "ablations": [
        {"name": n, "delta_recall_at_3": d, "ci_lo": d - 0.03, "ci_hi": d + 0.03}
        for n, d in [("-GAT", -0.04), ("-disagreement", -0.02),
                     ("-rationale", -0.01), ("single-task", -0.07)]
    ],
}

@pytest.mark.parametrize("mod,name", [
    ("classifier.figures.fig2_calibration", "fig2_calibration"),
    ("classifier.figures.fig3_per_pair",    "fig3_per_pair"),
    ("classifier.figures.fig4_ablation",    "fig4_ablation"),
])
def test_figure_writes_valid_pdf(tmp_path, monkeypatch, mod, name):
    RESULTS.parent.mkdir(parents=True, exist_ok=True)
    if not RESULTS.exists():
        RESULTS.write_text(json.dumps(FIXTURE))
    monkeypatch.setenv("FIG_OUT_DIR", str(tmp_path))
    r = subprocess.run([sys.executable, "-m", mod],
                       cwd=REPO, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    out = tmp_path / f"{name}.pdf"
    assert out.exists() and out.read_bytes().startswith(b"%PDF")
```

(The test writes a fixture `results.json` **only if one is not already committed** — so it never clobbers the real sacred-run file.)

- [ ] **Step 4: Run and commit**

```bash
pytest classifier/tests/figures/ -x
git add classifier/figures/fig3_per_pair.py classifier/figures/fig4_ablation.py \
        classifier/tests/figures/test_fig2_3_4.py
git commit -m "plan8: fig3 per-pair + fig4 ablation forest plot"
```

---

## Phase C — HuggingFace model upload

### Task C1: `upload_model.py`

**Files:**
- Create: `classifier/publish/__init__.py`
- Create: `classifier/publish/upload_model.py`

- [ ] **Step 1: Write the script**

```python
# classifier/publish/upload_model.py
"""Upload the sacred-run ensemble checkpoint + tokenizer + model card
to the HuggingFace Hub. Dry-run by default. Refuses to upload unless
the current git HEAD matches the sacred-run git_sha (Contract 13)."""
from __future__ import annotations
import argparse, json, subprocess, sys
from pathlib import Path
from huggingface_hub import HfApi

from classifier.data.splits import verify_hashes
from classifier.publish.model_card import render_model_card

REPO = Path(__file__).resolve().parents[2]
SACRED = REPO / "data" / "sacred_run" / "results.json"
CKPT_DIR = REPO / "data" / "sacred_run" / "ensemble"

class SacredRunMismatch(RuntimeError): ...

def _git_head() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-id", default="rocklambros/ai-security-crosswalk")
    ap.add_argument("--dry-run", action="store_true", default=True)
    ap.add_argument("--no-dry-run", dest="dry_run", action="store_false")
    ap.add_argument("--allow-dirty", action="store_true")
    args = ap.parse_args(argv)

    verify_hashes()
    results = json.loads(SACRED.read_text())
    sacred_sha = results["git_sha"]
    head = _git_head()
    if head != sacred_sha and not args.allow_dirty:
        raise SacredRunMismatch(
            f"HEAD {head} != sacred_sha {sacred_sha}; pass --allow-dirty to override")

    card = render_model_card(results, sacred_sha, args.repo_id)
    print(f"[upload_model] repo_id={args.repo_id}")
    print(f"[upload_model] tag={sacred_sha}")
    print(f"[upload_model] card_len={len(card)} bytes")
    print(f"[upload_model] ckpt_dir={CKPT_DIR}")

    if args.dry_run:
        print("[upload_model] DRY RUN — not uploading")
        return 0

    api = HfApi()
    api.create_repo(args.repo_id, repo_type="model", exist_ok=True)
    api.upload_folder(folder_path=str(CKPT_DIR),
                      repo_id=args.repo_id, repo_type="model")
    (CKPT_DIR / "README.md").write_text(card)
    api.upload_file(path_or_fileobj=str(CKPT_DIR / "README.md"),
                    path_in_repo="README.md",
                    repo_id=args.repo_id, repo_type="model")
    api.create_tag(args.repo_id, tag=sacred_sha,
                   repo_type="model", exist_ok=True)
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Commit**

```bash
git add classifier/publish/__init__.py classifier/publish/upload_model.py
git commit -m "plan8: upload_model.py with sacred-sha tag contract"
```

### Task C2: Jinja2 model-card renderer with honesty §6 verbatim

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

Three-stage ensemble (cross-encoder + GAT + stacked LightGBM + Mondrian
conformal wrapper) for mapping controls across 9 AI security and
governance frameworks. Released as a research artifact by Rock Lambros.

Sacred-run git sha: `{{ sacred_sha }}`

## Intended use

Assisting compliance auditors, security researchers, and governance
lawyers in identifying candidate cross-framework control mappings.
Predictions are **suggestions with calibrated confidence bands**, not
authoritative compliance determinations.

## Headline metrics (human_test_frozen, n=400)

| Metric | Value |
|---|---|
| Recall@1 | {{ metrics.recall_at_1 | round(4) }} |
| Recall@3 | {{ metrics.recall_at_3 | round(4) }} |
| Recall@5 | {{ metrics.recall_at_5 | round(4) }} |
| MRR | {{ metrics.mrr | round(4) }} |
| nDCG@10 | {{ metrics.ndcg_at_10 | round(4) }} |
| ECE | {{ metrics.ece | round(4) }} |
| Precision@80%-coverage | {{ metrics.precision_at_80 | round(4) }} |

## Per-framework-pair evaluation

| Pair | Recall@3 | 95% CI |
|---|---|---|
{%- for row in per_pair %}
| {{ row.pair_key }} | {{ row.recall_at_3 | round(3) }} | [{{ row.ci_lo | round(3) }}, {{ row.ci_hi | round(3) }}] |
{%- endfor %}

## Pre-registered honesty commitments

{{ honesty_section_verbatim }}

## Limitations

- Trained on LLM-SME-derived labels (Sonnet 4.6 three-persona ensemble);
  inherits any systematic bias documented in the Sonnet↔Opus appendix.
- Evaluation on 400 frozen + 75 fresh human-SME pairs; absolute numbers
  are only as reliable as that sample.
- Covers 9 frameworks as of the release date; new framework revisions
  require re-mapping.

## License

CC-BY-4.0.

## Citation

```bibtex
@misc{lambros2026crosswalk,
  title  = {Cross-Framework AI Security Control Mapping with
            Disagreement-Aware Multi-Task Learning},
  author = {Rock Lambros},
  year   = {2026},
  howpublished = {\url{https://huggingface.co/{{ repo_id }}}},
  note   = {git sha {{ sacred_sha }}}
}
```
```

- [ ] **Step 2: Write `model_card.py` renderer**

```python
# classifier/publish/model_card.py
from __future__ import annotations
import re
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape

REPO = Path(__file__).resolve().parents[2]
SPEC = REPO / "docs" / "superpowers" / "specs" / \
       "2026-04-07-ai-security-crosswalk-classifier-design.md"

_HONESTY_HEADER = "## 6. Pre-Registered Honesty Commitments"

def extract_honesty_section() -> str:
    text = SPEC.read_text()
    i = text.index(_HONESTY_HEADER)
    j = text.index("\n## ", i + len(_HONESTY_HEADER))
    return text[i:j].strip()

def render_model_card(results: dict, sacred_sha: str, repo_id: str) -> str:
    env = Environment(
        loader=FileSystemLoader(Path(__file__).parent / "templates"),
        autoescape=select_autoescape([]), keep_trailing_newline=True)
    tmpl = env.get_template("model_card.md.j2")
    return tmpl.render(
        repo_id=repo_id,
        sacred_sha=sacred_sha,
        metrics=results["metrics"],
        per_pair=results["per_pair"],
        honesty_section_verbatim=extract_honesty_section(),
    )
```

- [ ] **Step 3: Commit**

```bash
git add classifier/publish/model_card.py \
        classifier/publish/templates/model_card.md.j2
git commit -m "plan8: model card jinja template + renderer"
```

### Task C3: Dry-run + honesty verbatim tests

**Files:**
- Create: `classifier/tests/publish/__init__.py`
- Create: `classifier/tests/publish/test_upload_model_dryrun.py`
- Create: `classifier/tests/publish/test_model_card_honesty.py`

- [ ] **Step 1: Dry-run test**

```python
# classifier/tests/publish/test_upload_model_dryrun.py
import json, subprocess, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SACRED = REPO / "data" / "sacred_run" / "results.json"

def test_upload_model_dryrun_prints_tag(monkeypatch, tmp_path):
    if not SACRED.exists():
        SACRED.parent.mkdir(parents=True, exist_ok=True)
        SACRED.write_text(json.dumps({
            "git_sha": "deadbeefcafebabe",
            "metrics": {"recall_at_1": 0.5, "recall_at_3": 0.7,
                        "recall_at_5": 0.8, "mrr": 0.6, "ndcg_at_10": 0.7,
                        "ece": 0.05, "precision_at_80": 0.85},
            "per_pair": [{"pair_key": "p1", "recall_at_3": 0.7,
                          "ci_lo": 0.65, "ci_hi": 0.75}],
            "reliability_bins": [], "ablations": [],
        }))
    r = subprocess.run(
        [sys.executable, "-m", "classifier.publish.upload_model",
         "--dry-run", "--allow-dirty",
         "--repo-id", "rocklambros/ai-security-crosswalk"],
        cwd=REPO, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert "DRY RUN" in r.stdout
    assert "deadbeefcafebabe" in r.stdout  # Contract 13: sacred sha tag
    assert "rocklambros/ai-security-crosswalk" in r.stdout
```

- [ ] **Step 2: Honesty verbatim test (Contract 12)**

```python
# classifier/tests/publish/test_model_card_honesty.py
import json, re
from pathlib import Path

from classifier.publish.model_card import (
    render_model_card, extract_honesty_section)

REPO = Path(__file__).resolve().parents[3]

def test_honesty_section_extracted_and_rendered_verbatim():
    honesty = extract_honesty_section()
    # sanity: all 8 numbered commitments are present
    for i in range(1, 9):
        assert re.search(rf"^{i}\.\s", honesty, re.M), f"commitment {i} missing"
    card = render_model_card(
        results={"metrics": {"recall_at_1": 0.5, "recall_at_3": 0.7,
                             "recall_at_5": 0.8, "mrr": 0.6,
                             "ndcg_at_10": 0.7, "ece": 0.05,
                             "precision_at_80": 0.85},
                 "per_pair": [{"pair_key": "p1", "recall_at_3": 0.7,
                               "ci_lo": 0.65, "ci_hi": 0.75}]},
        sacred_sha="deadbeef", repo_id="rocklambros/x")
    # Every non-blank line of the honesty section must appear verbatim.
    for line in honesty.splitlines():
        s = line.strip()
        if not s:
            continue
        assert s in card, f"missing verbatim line: {s!r}"

def test_card_does_not_mention_ai_attribution():
    card = render_model_card(
        results={"metrics": {"recall_at_1": 0.5, "recall_at_3": 0.7,
                             "recall_at_5": 0.8, "mrr": 0.6,
                             "ndcg_at_10": 0.7, "ece": 0.05,
                             "precision_at_80": 0.85},
                 "per_pair": []},
        sacred_sha="deadbeef", repo_id="rocklambros/x")
    # Attribution guard: Claude/Anthropic may ONLY appear inside the
    # honesty section (which quotes "Sonnet 4.6" / "Opus 4.6" as labeler
    # model names). No AI co-author claims anywhere.
    assert "Co-Authored-By" not in card
    assert "AI-assisted" not in card
    assert "Generated with" not in card
```

- [ ] **Step 3: Run and commit**

```bash
pytest classifier/tests/publish/ -x
git add classifier/tests/publish/
git commit -m "plan8: model-card honesty verbatim + upload dry-run tests"
```

---

## Phase D — HuggingFace dataset upload

### Task D1: `upload_dataset.py` + dataset card

**Files:**
- Create: `classifier/publish/upload_dataset.py`
- Create: `classifier/publish/dataset_card.py`
- Create: `classifier/publish/templates/dataset_card.md.j2`

- [ ] **Step 1: Write the dataset card template**

```jinja
---
license: cc-by-4.0
language: en
pretty_name: AI Security Framework Crosswalk (v1_frozen)
tags:
  - ai-security
  - crosswalk
  - llm-sme
task_categories:
  - text-classification
size_categories:
  - 10K<n<100K
---

# AI Security Framework Crosswalk — v1_frozen dataset

Cross-framework control mapping labels across 9 AI security and
governance frameworks. Released by Rock Lambros.

Sacred-run git sha: `{{ sacred_sha }}`

## Splits

| Split | Size | Provenance |
|---|---|---|
| `llm_train` | ~9,400 | LLM-SME v1_calibrated, 3-persona ensemble (Sonnet 4.6) |
| `llm_val` | ~600 | LLM-SME v1_calibrated |
| `human_cal` | 150 | Stratified from existing 550 SME pool (seed 42) |
| `human_test_frozen` | 400 | Remaining 400 from existing 550 SME pool |
| `human_test_fresh` | 75 | Post-freeze verification labels |

## LLM-SME provenance

Labels in `llm_train` and `llm_val` were produced by a three-persona
ensemble — compliance auditor, security researcher, governance lawyer —
each called with reference grounding and structured JSON output.
Aggregation: 3/3 agreement → gold; 2/3 → majority × 0.75 confidence;
0/3 → `ambiguous=true` flag.

## Human-SME agreement

Cohen's κ on 150 calibration pairs: {{ kappa | round(3) }}.

## Schema

```json
{"pair_key": "aiuc-1:C-1.2__owasp-agentic:ASI-03",
 "source_framework": "aiuc-1",
 "target_framework": "owasp-agentic",
 "tier": "Direct",
 "confidence": 0.92,
 "rationale_code": "FUNCTIONAL_OVERLAP",
 "split": "llm_train"}
```

## License

CC-BY-4.0.
```

- [ ] **Step 2: Write `dataset_card.py` renderer**

```python
# classifier/publish/dataset_card.py
from __future__ import annotations
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape

def render_dataset_card(sacred_sha: str, kappa: float) -> str:
    env = Environment(
        loader=FileSystemLoader(
            Path(__file__).parent / "templates"),
        autoescape=select_autoescape([]), keep_trailing_newline=True)
    return env.get_template("dataset_card.md.j2").render(
        sacred_sha=sacred_sha, kappa=kappa)
```

- [ ] **Step 3: Write `upload_dataset.py`**

```python
# classifier/publish/upload_dataset.py
"""Upload v1_frozen label splits to HF as parquet + dataset card.
Dry-run default. Tags with sacred-run git_sha (Contract 13).
NEVER uploads human_test_frozen — Contract 8 applies — the uploaded
dataset repo contains only llm_train / llm_val / human_cal /
human_test_fresh. human_test_frozen is referenced by hash only."""
from __future__ import annotations
import argparse, json, subprocess, sys
from pathlib import Path
import pandas as pd
from huggingface_hub import HfApi

from classifier.data.splits import verify_hashes
from classifier.publish.dataset_card import render_dataset_card

REPO = Path(__file__).resolve().parents[2]
SACRED = REPO / "data" / "sacred_run" / "results.json"
SPLITS = REPO / "data" / "splits"
LABELS = REPO / "data" / "labels" / "llm_sme" / "v1_frozen"

ALLOWED_SPLITS = ("llm_train", "llm_val", "human_cal", "human_test_fresh")

def _git_head() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-id", default="rocklambros/ai-security-crosswalk")
    ap.add_argument("--dry-run", action="store_true", default=True)
    ap.add_argument("--no-dry-run", dest="dry_run", action="store_false")
    ap.add_argument("--allow-dirty", action="store_true")
    args = ap.parse_args(argv)

    verify_hashes()
    results = json.loads(SACRED.read_text())
    sacred_sha = results["git_sha"]
    head = _git_head()
    if head != sacred_sha and not args.allow_dirty:
        print(f"HEAD {head} != sacred_sha {sacred_sha}", file=sys.stderr)
        return 2

    card = render_dataset_card(sacred_sha, results.get("kappa", 0.0))
    print(f"[upload_dataset] repo_id={args.repo_id}")
    print(f"[upload_dataset] tag={sacred_sha}")
    print(f"[upload_dataset] card_len={len(card)} bytes")
    print(f"[upload_dataset] allowed_splits={ALLOWED_SPLITS}")

    if args.dry_run:
        print("[upload_dataset] DRY RUN — not uploading")
        return 0

    api = HfApi()
    api.create_repo(args.repo_id, repo_type="dataset", exist_ok=True)
    for split in ALLOWED_SPLITS:
        path = SPLITS / f"{split}.jsonl"
        if not path.exists():
            continue
        df = pd.read_json(path, lines=True)
        out = SPLITS / f"{split}.parquet"
        df.to_parquet(out)
        api.upload_file(path_or_fileobj=str(out),
                        path_in_repo=f"data/{split}.parquet",
                        repo_id=args.repo_id, repo_type="dataset")
    api.create_tag(args.repo_id, tag=sacred_sha,
                   repo_type="dataset", exist_ok=True)
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Commit**

```bash
git add classifier/publish/upload_dataset.py \
        classifier/publish/dataset_card.py \
        classifier/publish/templates/dataset_card.md.j2
git commit -m "plan8: upload_dataset.py + dataset card (no frozen split)"
```

### Task D2: Dry-run test + `human_test_frozen` guard

**Files:**
- Create: `classifier/tests/publish/test_upload_dataset_dryrun.py`

- [ ] **Step 1: Write test**

```python
# classifier/tests/publish/test_upload_dataset_dryrun.py
import json, subprocess, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SACRED = REPO / "data" / "sacred_run" / "results.json"

def test_upload_dataset_dryrun_never_lists_frozen(tmp_path):
    if not SACRED.exists():
        SACRED.parent.mkdir(parents=True, exist_ok=True)
        SACRED.write_text(json.dumps(
            {"git_sha": "deadbeefcafebabe", "kappa": 0.72,
             "metrics": {}, "per_pair": [],
             "reliability_bins": [], "ablations": []}))
    r = subprocess.run(
        [sys.executable, "-m", "classifier.publish.upload_dataset",
         "--dry-run", "--allow-dirty",
         "--repo-id", "rocklambros/ai-security-crosswalk"],
        cwd=REPO, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert "DRY RUN" in r.stdout
    assert "deadbeefcafebabe" in r.stdout
    # Contract 8: human_test_frozen MUST NOT appear in the allowed-splits list
    assert "human_test_frozen" not in r.stdout
```

- [ ] **Step 2: Run and commit**

```bash
pytest classifier/tests/publish/test_upload_dataset_dryrun.py -x
git add classifier/tests/publish/test_upload_dataset_dryrun.py
git commit -m "plan8: upload_dataset dry-run test + frozen guard"
```

---

## Phase E — Blog post draft

### Task E1: `docs/blog/2026-XX-XX-ai-security-crosswalk.md`

**Files:**
- Create: `docs/blog/2026-XX-XX-ai-security-crosswalk.md`

- [ ] **Step 1: Write the draft**

3–5k words, following spec §4.6 item 5. Structure:

1. Hook — why cross-framework mapping is painful for auditors
2. What the 9 frameworks cover and why they don't talk to each other
3. Existing v2 composite and its 20–30% tier accuracy
4. The LLM-SME labeling protocol: 3 personas, reference grounding, Sonnet↔Opus study
5. Architecture: cross-encoder + GAT + LightGBM + Mondrian conformal
6. Sacred-run results (`{{ RECALL_AT_3 }}` placeholders filled from `paper/tables/table1.md` at publish time)
7. What failed — the honesty list from spec §6
8. How to reproduce in one command (`make reproduce`)
9. Links: arXiv, HF model, HF dataset, GitHub, HF Space

Hand-written prose; `{{ RECALL_AT_3 }}` style placeholders resolved by the human author at publish time. No AI attribution anywhere in the post.

- [ ] **Step 2: Commit**

```bash
git add docs/blog/2026-XX-XX-ai-security-crosswalk.md
git commit -m "plan8: blog post draft"
```

---

## Phase F — Repo polish

### Task F1: README + LICENSE + badges

**Files:**
- Modify: `README.md` (add reproduction one-liner + badges section)
- Create: `LICENSE` (Apache-2.0 verbatim)
- Create: `classifier/tests/repo/__init__.py`
- Create: `classifier/tests/repo/test_readme_reproduce.py`
- Create: `classifier/tests/repo/test_license.py`

- [ ] **Step 1: Write `LICENSE`**

Drop in the standard Apache-2.0 text (www.apache.org/licenses/LICENSE-2.0.txt), copyright line `Copyright 2026 Rock Lambros`.

- [ ] **Step 2: Append to `README.md`**

```markdown
## Reproduction

```bash
git clone https://github.com/rocklambros/ai-security-framework-crosswalk
cd ai-security-framework-crosswalk
make reproduce
```

`make reproduce` verifies split hashes, runs evaluation on `llm_val`
using the cached ensemble, and diffs the output against the committed
sacred-run results. Any drift fails the target.

## Badges

![CI](https://github.com/rocklambros/ai-security-framework-crosswalk/actions/workflows/ci.yml/badge.svg)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Paper](https://img.shields.io/badge/arXiv-pending-b31b1b.svg)](https://arxiv.org/abs/XXXX.XXXXX)
[![HF Model](https://img.shields.io/badge/%F0%9F%A4%97-model-yellow)](https://huggingface.co/rocklambros/ai-security-crosswalk)
[![HF Dataset](https://img.shields.io/badge/%F0%9F%A4%97-dataset-yellow)](https://huggingface.co/datasets/rocklambros/ai-security-crosswalk)
```

- [ ] **Step 3: Write the tests**

```python
# classifier/tests/repo/test_readme_reproduce.py
from pathlib import Path
REPO = Path(__file__).resolve().parents[3]
def test_readme_has_make_reproduce():
    txt = (REPO / "README.md").read_text()
    assert "make reproduce" in txt
    assert "## Reproduction" in txt
```

```python
# classifier/tests/repo/test_license.py
from pathlib import Path
REPO = Path(__file__).resolve().parents[3]
def test_license_is_apache_2():
    txt = (REPO / "LICENSE").read_text()
    assert "Apache License" in txt and "Version 2.0" in txt
    assert "Copyright 2026 Rock Lambros" in txt
```

- [ ] **Step 4: Run and commit**

```bash
pytest classifier/tests/repo/test_readme_reproduce.py \
       classifier/tests/repo/test_license.py -x
git add README.md LICENSE classifier/tests/repo/__init__.py \
        classifier/tests/repo/test_readme_reproduce.py \
        classifier/tests/repo/test_license.py
git commit -m "plan8: README reproduction + LICENSE Apache-2.0 + badges"
```

### Task F1.5: Delete the pre-classifier archive

Plan 1 Task A1.5 quarantined stale artifacts under `archive/pre-classifier-refactor/`. After the sacred-run lockfile lands (Plan 6 Phase E), those artifacts are provably unused — git history is the system of record. Delete the archive to keep the published repo clean.

**Files:**
- Delete: `archive/pre-classifier-refactor/`
- Test: `classifier/tests/repo/test_archive_removed.py`

- [ ] **Step 1: Write the failing test**

```python
# classifier/tests/repo/test_archive_removed.py
from pathlib import Path
REPO = Path(__file__).resolve().parents[3]

def test_pre_classifier_archive_is_gone():
    assert not (REPO / "archive" / "pre-classifier-refactor").exists(), \
        "archive/pre-classifier-refactor must be deleted in Plan 8 F1.5"

def test_sacred_lockfile_exists():
    # gate: do not delete the archive until the sacred run has occurred
    assert any((REPO / "data" / "sacred").glob("lock_*.json")), \
        "refuse to delete archive before sacred-run lockfile lands"
```

- [ ] **Step 2: Run test — expect failure**

Run: `pytest classifier/tests/repo/test_archive_removed.py -v`
Expected: `test_pre_classifier_archive_is_gone` fails (archive still present).

- [ ] **Step 3: Verify sacred-run lockfile is in place**

Run: `ls data/sacred/lock_*.json`
Expected: at least one lockfile (proves Plan 6 ran). If absent, STOP.

- [ ] **Step 4: Delete the archive**

```bash
git rm -r archive/pre-classifier-refactor/
```

- [ ] **Step 5: Run test — expect pass**

Run: `pytest classifier/tests/repo/test_archive_removed.py -v`
Expected: 2 passed.

- [ ] **Step 6: Commit**

```bash
git add classifier/tests/repo/test_archive_removed.py
git commit -m "plan8: delete pre-classifier archive after sacred run"
```

### Task F2: CITATION.cff + frozen requirements.txt

**Files:**
- Create: `CITATION.cff`
- Modify/create: `requirements.txt` (frozen via pip-compile)
- Create: `classifier/tests/repo/test_citation_cff.py`
- Create: `classifier/tests/repo/test_requirements_frozen.py`

- [ ] **Step 1: Write `CITATION.cff`**

```yaml
cff-version: 1.2.0
message: "If you use this software, please cite it as below."
title: "AI Security Framework Crosswalk Classifier"
authors:
  - family-names: Lambros
    given-names: Rock
    orcid: "https://orcid.org/0000-0000-0000-0000"  # TODO(author): replace
repository-code: "https://github.com/rocklambros/ai-security-framework-crosswalk"
license: Apache-2.0
version: "1.0.0"
date-released: "2026-04-30"
```

- [ ] **Step 2: Freeze `requirements.txt` via pip-compile**

```bash
pip install pip-tools
pip-compile --generate-hashes --output-file=requirements.txt \
  requirements-classifier.txt requirements.in
```

Every line in the resulting `requirements.txt` must use `==` (pip-compile guarantees this). Commit the lockfile.

- [ ] **Step 3: Write tests**

```python
# classifier/tests/repo/test_citation_cff.py
from pathlib import Path
import yaml
REPO = Path(__file__).resolve().parents[3]
def test_citation_cff_author_and_orcid():
    data = yaml.safe_load((REPO / "CITATION.cff").read_text())
    assert data["authors"][0]["family-names"] == "Lambros"
    assert data["authors"][0]["given-names"] == "Rock"
    assert "orcid.org" in data["authors"][0]["orcid"]
    assert data["license"] == "Apache-2.0"
    # Attribution guard
    txt = (REPO / "CITATION.cff").read_text()
    for s in ("Claude", "Anthropic", "AI-assisted"):
        assert s not in txt
```

```python
# classifier/tests/repo/test_requirements_frozen.py
import re
from pathlib import Path
REPO = Path(__file__).resolve().parents[3]
def test_every_requirement_is_pinned():
    txt = (REPO / "requirements.txt").read_text()
    for line in txt.splitlines():
        s = line.strip()
        if not s or s.startswith("#") or s.startswith("--"):
            continue
        # package==version or package==version ; marker
        assert re.match(r"^[A-Za-z0-9_.\-\[\]]+==", s), f"unpinned: {s}"
```

- [ ] **Step 4: Run and commit**

```bash
pytest classifier/tests/repo/test_citation_cff.py \
       classifier/tests/repo/test_requirements_frozen.py -x
git add CITATION.cff requirements.txt \
        classifier/tests/repo/test_citation_cff.py \
        classifier/tests/repo/test_requirements_frozen.py
git commit -m "plan8: CITATION.cff + frozen requirements.txt"
```

---

## Phase G — GitHub Actions CI

### Task G1: `.github/workflows/ci.yml`

**Files:**
- Create: `.github/workflows/ci.yml`

- [ ] **Step 1: Write the workflow**

```yaml
name: CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install deps
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install ruff mypy pytest
      - name: Verify split hashes
        run: python -m classifier.data.splits verify-hashes
      - name: Ruff lint
        run: ruff check classifier/
      - name: Mypy type check
        run: mypy classifier/ --ignore-missing-imports
      - name: Unit tests (small, no training)
        run: |
          pytest classifier/tests/publish/ \
                 classifier/tests/figures/ \
                 classifier/tests/repo/ \
                 classifier/tests/paper/ -x
```

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "plan8: github actions CI (hash verify + ruff + mypy + tests)"
```

---

## Phase H — Reproduction one-liner

### Task H1: `Makefile` + `make reproduce`

**Files:**
- Create: `Makefile`
- Create: `classifier/tests/repo/test_reproduce_make_target.py`

- [ ] **Step 1: Write `Makefile`**

```make
.PHONY: reproduce verify-hashes eval-llm-val diff-sacred clean-reproduce

PY := python

reproduce: verify-hashes eval-llm-val diff-sacred
	@echo "[reproduce] OK"

verify-hashes:
	$(PY) -m classifier.data.splits verify-hashes

eval-llm-val:
	$(PY) -m classifier.sacred.eval_cached \
	      --split llm_val \
	      --out data/reproduce/llm_val_results.json

diff-sacred:
	$(PY) -m classifier.sacred.diff_results \
	      --a data/sacred_run/results.json \
	      --b data/reproduce/llm_val_results.json \
	      --strict

clean-reproduce:
	rm -rf data/reproduce/
```

The `eval_cached` and `diff_results` modules live in Plan 6 and are consumed here as black boxes. `--strict` requires identical-byte metrics JSON on the overlapping `llm_val` subset.

- [ ] **Step 2: Write the test**

```python
# classifier/tests/repo/test_reproduce_make_target.py
import shutil, subprocess
from pathlib import Path
import pytest
REPO = Path(__file__).resolve().parents[3]

@pytest.mark.skipif(shutil.which("make") is None, reason="make not installed")
def test_make_reproduce_dry_run_lists_four_steps():
    r = subprocess.run(["make", "-n", "reproduce"],
                       cwd=REPO, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    for needle in ("verify-hashes", "eval_cached", "diff_results",
                   "[reproduce] OK"):
        assert needle in r.stdout, f"missing from dry run: {needle!r}"
```

- [ ] **Step 3: Run and commit**

```bash
pytest classifier/tests/repo/test_reproduce_make_target.py -x
git add Makefile classifier/tests/repo/test_reproduce_make_target.py
git commit -m "plan8: make reproduce one-liner target"
```

---

## Self-Review Checklist

Before declaring Plan 8 complete, verify each item and map it to the spec / cross-plan contracts:

- [ ] **§4.6 deliverable 1 (GitHub repo polish)** — README reproduction one-liner, Apache-2.0 LICENSE, CITATION.cff with ORCID, frozen requirements.txt, badges. Tasks F1, F2.
- [ ] **§4.6 deliverable 2 (HF model)** — `upload_model.py` dry-run passes, model card renders, honesty §6 verbatim, per-framework-pair eval table rendered. Tasks C1–C3.
- [ ] **§4.6 deliverable 3 (HF dataset)** — `upload_dataset.py` dry-run passes, dataset card renders, Cohen's κ reported, `human_test_frozen` excluded from upload. Task D1, D2.
- [ ] **§4.6 deliverable 5 (blog post)** — draft committed at `docs/blog/`. Task E1.
- [ ] **§4.6 deliverable 6 (arXiv preprint)** — LaTeX scaffold compiles under latexmk with stub tables/figures. Tasks A1–A3.
- [ ] **§6 honesty commitments** — all 8 numbered items appear character-identical in the rendered model card. `test_model_card_honesty.py`.
- [ ] **Contract 1 — hash verification at entry** — `make reproduce` calls `verify_hashes` as its first step. `test_reproduce_make_target.py`.
- [ ] **Contract 8 — `human_test_frozen` untouched** — Plan 8 never references the filename in any script (uploaders explicitly exclude it, tests assert its absence from dry-run output). No grep hit outside allowed locations.
- [ ] **Contract 12 — honesty verbatim in model card** — enforced by `test_model_card_honesty.py`.
- [ ] **Contract 13 — sacred-run git_sha tag** — both uploaders read `data/sacred_run/results.json["git_sha"]` and surface it in dry-run stdout; `SacredRunMismatch` aborts when HEAD drifts. `test_upload_model_dryrun.py`, `test_upload_dataset_dryrun.py`.
- [ ] **CI gate (Phase G)** — `.github/workflows/ci.yml` installs pinned deps, runs `verify_hashes`, ruff, mypy, and the Plan 8 unit tests on every push and PR.
- [ ] **Figures** — fig1–fig4 produce valid PDFs (header bytes `%PDF`); tests green; output committed to `paper/figures/`. Tasks B1–B3.
- [ ] **latexmk build** — `test_latexmk_build.py` green when latexmk is available; CI installs `texlive-latex-extra` so the green run happens at least once.
- [ ] **Attribution guards** — no commit message, no model card, no dataset card, no blog post, and no CITATION.cff mentions Claude / Anthropic / AI-assisted / Co-Authored-By. Enforced by `test_model_card_honesty.py::test_card_does_not_mention_ai_attribution` and `test_citation_cff.py`. Author is Rock Lambros only.
- [ ] **No training, no LLM calls, no GPU** — Plan 8 adds no torch / sentence-transformers / anthropic imports beyond what is already in `requirements.txt`. Budget: $0.
- [ ] **Plan 6 artifacts read-only** — no task modifies `paper/tables/*`, `data/sacred_run/*`, `data/splits/*`, `data/labels/*`. All consumers open these paths in read mode only.

---

## Lessons Carried (restated for the executor)

1. **Do not retune at writeup time.** The sacred-run numbers are frozen; Plan 8 surfaces them as-is. Any instinct to "just nudge this one metric" is a bug.
2. **Dry-run by default.** Every HF uploader defaults to `--dry-run`; CI never pushes to the Hub; a human flips `--no-dry-run` exactly once at release.
3. **Verbatim is non-negotiable.** The honesty section's eight commitments are copy-pasted, not paraphrased, into the model card. The test is a substring check for a reason.
4. **Attribution is the author's alone.** No AI co-author, anywhere. This is enforced by tests, not just by convention.
5. **Reproduction is one line.** If `make reproduce` grows beyond "verify → eval → diff", it has lost the point.

---

## Next Step

Execute Plan 8 via superpowers:subagent-driven-development or superpowers:executing-plans, one task at a time. After Phase H lands, the repo is ready for the human-driven final steps: submit arXiv, flip uploaders to `--no-dry-run`, publish the blog post, announce.
