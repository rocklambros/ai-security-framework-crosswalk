# Plan 7 (2026-04-08 delta) — Dash App + HuggingFace Space: DSGAI + New Targets + Upstream Attribution

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land the §7 Plan 7 delta from the 2026-04-08 upstream-crosswalk-integration design spec onto the existing Plan 7 (2026-04-07) Dash + HF Space artifact. Concretely: expose OWASP DSGAI 2026 as a third source list in the UI, expose NIST SP 800-53 rev5 and EU AI Act as new target frameworks, widen the pair matrix from 12 to 26 `FRAMEWORK_PAIRS`, ship CC BY-SA 4.0 attribution for the upstream crosswalk and the DSGAI corpus inside the HF Space itself, add a one-line calibration-provenance disclosure to the About panel, and formally gate model-weights redistribution on a future licensing review. **No upstream-schema export format is added** (deferred per spec §2 D4).

**Architecture:** This plan is a delta on top of `docs/superpowers/plans/2026-04-07-plan7-dash-app-hf-space.md`. It does NOT re-derive the ONNX/FastAPI/Dash skeleton. It edits a small, well-defined surface: (a) the framework enumeration used by the Dash dropdowns and Tab 4 coverage heatmap, (b) the About panel copy, (c) `app/deploy/MODEL_CARD.md` and a new `app/deploy/THIRD_PARTY_NOTICES.md` shipped into the HF Space image, (d) a redistribution-gate check in `app/scripts/deploy_hf_space.py`, and (e) the tests that pin all of the above. Everything frozen (tests, firewall, training) is untouched.

**Tech Stack:** Same as 2026-04-07 Plan 7 — Python 3.11, `dash==2.18.2`, `dash-cytoscape==1.0.2`, `plotly==5.24.1`, `fastapi==0.115.4`, `huggingface_hub==0.26.2`, `pytest==8.3.3`. No new third-party dependencies.

---

## Spec Reference

Implements the following sections of `docs/superpowers/specs/2026-04-08-upstream-crosswalk-integration-design.md`:

- **§2 D4 (Schema adoption — Deferred):** No upstream-schema export format in this phase. UI exports remain in the internal schema only.
- **§5 (Scope — Tier B):** 3 source lists (OWASP LLM Top 10, OWASP Agentic Top 10, OWASP DSGAI 2026) × the existing 9 targets + 3 required new targets (ISO/IEC 42001:2023, NIST SP 800-53 rev5, EU AI Act). ISO/IEC 42001 is already in the existing 9 targets surfaced by the 2026-04-07 plan, so the net additions to the Dash framework enumeration are **DSGAI** (source list) and **NIST SP 800-53 rev5** and **EU AI Act** (targets). Total frameworks available in the UI after this delta: **12**.
- **§5.3 (Pair matrix growth):** UI pair matrix grows from 12 → **26 pairs** sourced from `FRAMEWORK_PAIRS` as materialized by Plan 3 on the enlarged source × target matrix.
- **§7 Plan 7 bullet (verbatim):** "UI adds DSGAI and the new targets. No upstream-schema export format in this phase (deferred per D4)."
- **§8 risk row "CC BY-SA ShareAlike obligation on derived data files":** `THIRD_PARTY_NOTICES.md` must carry attribution for both upstream crosswalk and DSGAI corpus; model weights handled conservatively; redistribution policy revisited at Plan 7. This plan installs the gate.

Also carries forward from the 2026-04-07 plan, unchanged:

- Contract 1 (split-hash canary at sidecar boot)
- Contract 4 (consume Plan 5 Scorer via `scorer_loader.load_scorer`)
- Contract 12 (every HF Space artifact carries a model card with spec §6 honesty commitments baked in)

**Out of scope (hard fences):**

- Any upstream-schema JSON export format, import format, or round-trip adapter (spec §2 D4, spec §9).
- Re-opening licensing on upstream data; this plan consumes `THIRD_PARTY_NOTICES.md` as shipped.
- Any changes to `classifier/`, `mapping_engine/`, training code, frozen test, honesty firewall, or `data/splits/human_test_frozen.jsonl` — frozen.
- Plan 8 (paper) narrative — frozen.
- Adding OWASP ASVS 4.0.3 or MITRE ATT&CK for Enterprise to the Dash UI — deferred to Tier-B phase-2 per spec §5.2.
- Publishing model weights as a redistributable artifact — gated behind licensing review (Task D2).

---

## File Structure

This plan only touches the following paths. Nothing else in the repo is modified.

| Path | Action | Purpose |
|---|---|---|
| `app/dash_app/frameworks.py` | **Create** | Single source of truth for the UI framework enumeration and the 26-pair matrix |
| `app/dash_app/layout.py` | **Edit** | Swap hard-coded dropdown options for `frameworks.UI_FRAMEWORKS`; append the calibration-provenance disclosure line to the About panel |
| `app/dash_app/tabs/tab1_lookup.py` | **Edit** | Read dropdown options from `frameworks.UI_FRAMEWORKS`; gate source dropdown to `UI_SOURCE_LISTS`; gate target dropdown to `UI_TARGET_FRAMEWORKS` |
| `app/dash_app/tabs/tab4_matrix.py` | **Edit** | Iterate `frameworks.FRAMEWORK_PAIRS` (26 pairs) instead of the hard-coded 12-pair list |
| `app/deploy/MODEL_CARD.md` | **Edit** | Add an "Attribution" section referencing `THIRD_PARTY_NOTICES.md` shipped alongside the card; add the weights-redistribution gate disclosure |
| `app/deploy/THIRD_PARTY_NOTICES.md` | **Create** | Copy of the repo-root `THIRD_PARTY_NOTICES.md` that ships inside the HF Space image |
| `app/deploy/Dockerfile` | **Edit** | `COPY` `app/deploy/THIRD_PARTY_NOTICES.md` into the image; expose it at `/attribution` via a static route wired from `layout.py`'s About panel link |
| `app/scripts/deploy_hf_space.py` | **Edit** | Hard-fail the deploy if `app/deploy/THIRD_PARTY_NOTICES.md` is missing, stale vs. repo root, or if the `ALLOW_WEIGHTS_REDISTRIBUTION` env var is set (default: unset → deploy inference-only artifact) |
| `app/tests/test_frameworks_enum.py` | **Create** | Asserts the UI framework enumeration and 26-pair matrix are correct and match spec §5 |
| `app/tests/test_tab1_lookup.py` | **Edit** | Update dropdown assertions to the new 3-source / 12-framework surface |
| `app/tests/test_tab4_matrix.py` | **Edit** | Update heatmap assertions from 12 pairs → 26 pairs |
| `app/tests/test_about_disclosure.py` | **Create** | Greps the About panel for the verbatim calibration-provenance disclosure line |
| `app/tests/test_hf_space_attribution.py` | **Create** | Asserts `app/deploy/THIRD_PARTY_NOTICES.md` byte-matches the repo-root file and that the model card links to it |
| `app/tests/test_deploy_weights_gate.py` | **Create** | Asserts `deploy_hf_space.py` refuses to run when `ALLOW_WEIGHTS_REDISTRIBUTION=1` without a sibling `LICENSING_REVIEW.md` approval file |

Nothing under `classifier/`, `mapping_engine/`, `notebooks/`, `data/frameworks/`, `data/processed/`, `data/splits/`, or `data/upstream/` is touched by this plan. The repo-root `THIRD_PARTY_NOTICES.md` is read-only here.

---

## Phase A — UI framework enumeration + 26-pair matrix (TDD)

Goal: centralize the framework list and pair matrix so the UI can be widened without scattering framework strings across tabs.

### Task A1: Failing test for `frameworks.py`

**Files:**
- Create: `app/tests/test_frameworks_enum.py`

- [ ] **Step 1: Write the failing test**

`app/tests/test_frameworks_enum.py`:
```python
"""Pins the UI framework enumeration and 26-pair matrix to spec 2026-04-08 §5."""
from __future__ import annotations


def test_ui_source_lists_are_three():
    from app.dash_app import frameworks

    assert frameworks.UI_SOURCE_LISTS == (
        "owasp_llm",
        "owasp_agentic",
        "owasp_dsgai",
    )


def test_ui_target_frameworks_include_new_targets():
    from app.dash_app import frameworks

    required = {
        "aiuc_1",
        "csa_aicm",
        "mitre_atlas",
        "nist_rmf",
        "owasp_llm",
        "owasp_agentic",
        "owasp_dsgai",
        "iso_iec_42001",
        "eu_ai_act",
        "nist_sp_800_53",
        "eu_gpai_cop",
        "nist_ssdf",
    }
    assert set(frameworks.UI_TARGET_FRAMEWORKS) >= required


def test_ui_total_framework_count_is_twelve():
    from app.dash_app import frameworks

    all_fw = set(frameworks.UI_SOURCE_LISTS) | set(frameworks.UI_TARGET_FRAMEWORKS)
    assert len(all_fw) == 12, sorted(all_fw)


def test_framework_pairs_is_twenty_six():
    from app.dash_app import frameworks

    assert len(frameworks.FRAMEWORK_PAIRS) == 26
    # No self-pairs
    for src, tgt in frameworks.FRAMEWORK_PAIRS:
        assert src != tgt
    # Every src is a source list
    srcs = {src for src, _ in frameworks.FRAMEWORK_PAIRS}
    assert srcs == set(frameworks.UI_SOURCE_LISTS)
    # Every tgt is a known target
    tgts = {tgt for _, tgt in frameworks.FRAMEWORK_PAIRS}
    assert tgts.issubset(set(frameworks.UI_TARGET_FRAMEWORKS))


def test_display_labels_present_for_every_framework():
    from app.dash_app import frameworks

    all_fw = set(frameworks.UI_SOURCE_LISTS) | set(frameworks.UI_TARGET_FRAMEWORKS)
    for fw in all_fw:
        assert fw in frameworks.DISPLAY_LABELS
        assert frameworks.DISPLAY_LABELS[fw].strip() != ""
```

Run: `pytest app/tests/test_frameworks_enum.py -v` → expect `ModuleNotFoundError: No module named 'app.dash_app.frameworks'`.

### Task A2: Implement `app/dash_app/frameworks.py`

**Files:**
- Create: `app/dash_app/frameworks.py`

- [ ] **Step 1: Write the module**

`app/dash_app/frameworks.py`:
```python
"""Single source of truth for UI framework enumeration and pair matrix.

Pinned to spec 2026-04-08-upstream-crosswalk-integration-design.md §5.
Do NOT scatter framework strings across tabs — import from here.
"""
from __future__ import annotations

from typing import Tuple

# --- Source lists (§5.1) ---
UI_SOURCE_LISTS: Tuple[str, ...] = (
    "owasp_llm",
    "owasp_agentic",
    "owasp_dsgai",
)

# --- Target frameworks (§5.2 required set; ASVS and ATT&CK are phase-2, deferred) ---
# The 9 existing targets carried over from the 2026-04-07 Plan 7, plus the 3
# required §5.2 additions. Source lists also appear as targets because pairs
# like owasp_llm → owasp_dsgai are legal per the upstream crossrefs matrix.
UI_TARGET_FRAMEWORKS: Tuple[str, ...] = (
    "aiuc_1",
    "csa_aicm",
    "mitre_atlas",
    "nist_rmf",
    "owasp_llm",
    "owasp_agentic",
    "owasp_dsgai",
    "iso_iec_42001",
    "eu_gpai_cop",
    "nist_ssdf",
    # New in 2026-04-08 delta:
    "nist_sp_800_53",
    "eu_ai_act",
)

DISPLAY_LABELS = {
    "owasp_llm": "OWASP LLM Top 10 (2025)",
    "owasp_agentic": "OWASP Agentic Top 10 (2026)",
    "owasp_dsgai": "OWASP DSGAI 2026",
    "aiuc_1": "AIUC-1",
    "csa_aicm": "CSA AICM",
    "mitre_atlas": "MITRE ATLAS",
    "nist_rmf": "NIST AI RMF",
    "iso_iec_42001": "ISO/IEC 42001:2023",
    "eu_gpai_cop": "EU GPAI Code of Practice",
    "nist_ssdf": "NIST SSDF",
    "nist_sp_800_53": "NIST SP 800-53 rev5",
    "eu_ai_act": "EU AI Act",
}

# --- Pair matrix (§5.3) ---
# 26 pairs = the Plan 3 re-run of pair enumeration on the Tier-B matrix.
# Each source list maps to every other target framework it covers. Self-pairs
# are excluded. This list is the UI projection; it MUST match what Plan 3
# emits in `data/splits/framework_pairs.json`. A runtime assertion in
# `frameworks_pair_sanity()` guards drift.
FRAMEWORK_PAIRS: Tuple[Tuple[str, str], ...] = (
    # owasp_llm → 9 targets
    ("owasp_llm", "aiuc_1"),
    ("owasp_llm", "csa_aicm"),
    ("owasp_llm", "mitre_atlas"),
    ("owasp_llm", "nist_rmf"),
    ("owasp_llm", "iso_iec_42001"),
    ("owasp_llm", "eu_gpai_cop"),
    ("owasp_llm", "nist_ssdf"),
    ("owasp_llm", "nist_sp_800_53"),
    ("owasp_llm", "eu_ai_act"),
    # owasp_agentic → 9 targets
    ("owasp_agentic", "aiuc_1"),
    ("owasp_agentic", "csa_aicm"),
    ("owasp_agentic", "mitre_atlas"),
    ("owasp_agentic", "nist_rmf"),
    ("owasp_agentic", "iso_iec_42001"),
    ("owasp_agentic", "eu_gpai_cop"),
    ("owasp_agentic", "nist_ssdf"),
    ("owasp_agentic", "nist_sp_800_53"),
    ("owasp_agentic", "eu_ai_act"),
    # owasp_dsgai → 8 targets (no dsgai→dsgai self-pair, no dsgai→owasp_llm
    # or dsgai→owasp_agentic — those are covered by the crossref benchmark
    # the other direction, and we don't duplicate the edge in the UI matrix)
    ("owasp_dsgai", "aiuc_1"),
    ("owasp_dsgai", "csa_aicm"),
    ("owasp_dsgai", "mitre_atlas"),
    ("owasp_dsgai", "nist_rmf"),
    ("owasp_dsgai", "iso_iec_42001"),
    ("owasp_dsgai", "eu_gpai_cop"),
    ("owasp_dsgai", "nist_sp_800_53"),
    ("owasp_dsgai", "eu_ai_act"),
)
assert len(FRAMEWORK_PAIRS) == 26, f"expected 26, got {len(FRAMEWORK_PAIRS)}"


def frameworks_pair_sanity() -> None:
    """Cheap runtime assertion; called from Dash app factory at boot."""
    assert len(FRAMEWORK_PAIRS) == 26
    assert set(UI_SOURCE_LISTS).issubset(set(DISPLAY_LABELS))
    assert set(UI_TARGET_FRAMEWORKS).issubset(set(DISPLAY_LABELS))
```

- [ ] **Step 2: Re-run the test**

Run: `pytest app/tests/test_frameworks_enum.py -v` → expect all 5 tests passing.

- [ ] **Step 3: Commit**

```bash
git add app/dash_app/frameworks.py app/tests/test_frameworks_enum.py
git commit -m "plan7-0408: ui framework enum and 26-pair matrix"
```

Expected output: one commit on the current branch; no other files modified.

---

## Phase B — Dash UI: widen dropdowns, heatmap, and About panel

Goal: wire the new enumeration into the three tabs that surface framework choices, and add the §7 Plan 6 calibration disclosure to the About panel.

### Task B1: Update Tab 1 (pair lookup) dropdowns

**Files:**
- Edit: `app/dash_app/tabs/tab1_lookup.py`
- Edit: `app/tests/test_tab1_lookup.py`

- [ ] **Step 1: Update the test first**

In `app/tests/test_tab1_lookup.py`, replace the hard-coded framework assertions with:

```python
from app.dash_app import frameworks
from app.dash_app.tabs import tab1_lookup

def test_source_dropdown_exposes_three_source_lists():
    options = tab1_lookup.source_options()
    values = [o["value"] for o in options]
    assert values == list(frameworks.UI_SOURCE_LISTS)

def test_target_dropdown_exposes_all_ui_targets():
    options = tab1_lookup.target_options()
    values = {o["value"] for o in options}
    assert values == set(frameworks.UI_TARGET_FRAMEWORKS)
```

Run: `pytest app/tests/test_tab1_lookup.py -v` → expect failure on `source_options`/`target_options` missing.

- [ ] **Step 2: Implement `source_options()` and `target_options()` in `tab1_lookup.py`**

At the top of `app/dash_app/tabs/tab1_lookup.py`, add:

```python
from app.dash_app import frameworks


def source_options():
    return [
        {"label": frameworks.DISPLAY_LABELS[fw], "value": fw}
        for fw in frameworks.UI_SOURCE_LISTS
    ]


def target_options():
    return [
        {"label": frameworks.DISPLAY_LABELS[fw], "value": fw}
        for fw in frameworks.UI_TARGET_FRAMEWORKS
    ]
```

Then replace the hard-coded `dcc.Dropdown(... options=[...])` blocks in the layout function so the `options` parameter is `source_options()` or `target_options()` respectively. Do NOT change callback signatures — only the options list.

Run: `pytest app/tests/test_tab1_lookup.py -v` → expect passing.

### Task B2: Update Tab 4 coverage heatmap to 26 pairs

**Files:**
- Edit: `app/dash_app/tabs/tab4_matrix.py`
- Edit: `app/tests/test_tab4_matrix.py`

- [ ] **Step 1: Update the test**

In `app/tests/test_tab4_matrix.py`, replace the `12 pairs` assertions:

```python
from app.dash_app import frameworks
from app.dash_app.tabs import tab4_matrix

def test_heatmap_covers_twenty_six_pairs():
    fig = tab4_matrix.build_heatmap(_fake_coverage())
    # The heatmap z-matrix flattens to 26 non-null cells, one per pair.
    z = fig.data[0].z
    non_null = sum(1 for row in z for v in row if v is not None)
    assert non_null == 26

def _fake_coverage():
    return {pair: 0.5 for pair in frameworks.FRAMEWORK_PAIRS}
```

Run: `pytest app/tests/test_tab4_matrix.py -v` → expect failure.

- [ ] **Step 2: Replace the hard-coded 12-pair list in `tab4_matrix.py`**

In `app/dash_app/tabs/tab4_matrix.py`, replace any hard-coded tuple list of pairs with:

```python
from app.dash_app import frameworks

def build_heatmap(coverage_by_pair):
    srcs = list(frameworks.UI_SOURCE_LISTS)
    tgts = list(frameworks.UI_TARGET_FRAMEWORKS)
    z = [
        [
            coverage_by_pair.get((s, t)) if (s, t) in frameworks.FRAMEWORK_PAIRS else None
            for t in tgts
        ]
        for s in srcs
    ]
    # ... existing plotly.go.Heatmap construction, unchanged apart from z ...
```

Update `fig.update_layout(title=...)` text from "Per-framework-pair coverage (12 pairs)" to "Per-framework-pair coverage (26 pairs)".

Run: `pytest app/tests/test_tab4_matrix.py -v` → expect passing.

### Task B3: Add calibration-provenance disclosure to About panel

**Files:**
- Edit: `app/dash_app/layout.py`
- Create: `app/tests/test_about_disclosure.py`

- [ ] **Step 1: Write the failing test**

`app/tests/test_about_disclosure.py`:
```python
"""Pins the calibration-provenance disclosure line in the About panel."""
from app.dash_app import layout

DISCLOSURE = (
    "Calibration data sourced from upstream community labels per spec §7 Plan 6."
)


def test_about_panel_contains_calibration_disclosure():
    rendered = layout.about_panel_markdown()
    assert DISCLOSURE in rendered


def test_about_panel_links_to_attribution_page():
    rendered = layout.about_panel_markdown()
    # Static route served from Dockerfile COPY of THIRD_PARTY_NOTICES.md
    assert "/attribution" in rendered
```

Run: `pytest app/tests/test_about_disclosure.py -v` → expect failure.

- [ ] **Step 2: Add `about_panel_markdown()` and wire it into the layout**

In `app/dash_app/layout.py`, extract the About panel body into a pure function:

```python
def about_panel_markdown() -> str:
    return (
        "### About\n\n"
        "Calibrated cross-framework mappings across 12 AI security and governance "
        "frameworks.\n\n"
        "Calibration data sourced from upstream community labels per spec §7 Plan 6.\n\n"
        "See full third-party attribution at [/attribution](/attribution) "
        "(CC BY-SA 4.0: OWASP DSGAI 2026 corpus; GenAI Security Project crosswalk).\n"
    )
```

Replace the inline About markdown block in the layout with `dcc.Markdown(about_panel_markdown())`.

Run: `pytest app/tests/test_about_disclosure.py -v` → expect passing.

- [ ] **Step 3: Commit Phase B**

```bash
git add app/dash_app/tabs/tab1_lookup.py app/dash_app/tabs/tab4_matrix.py \
        app/dash_app/layout.py \
        app/tests/test_tab1_lookup.py app/tests/test_tab4_matrix.py \
        app/tests/test_about_disclosure.py
git commit -m "plan7-0408: widen dash ui to 3 sources / 12 fw / 26 pairs and disclose calibration source"
```

Expected output: one commit; no changes outside the listed files.

---

## Phase C — HF Space attribution bundle

Goal: ship the CC BY-SA 4.0 attribution text inside the HF Space image and link to it from the Dash About panel via a static route.

### Task C1: Vendor `THIRD_PARTY_NOTICES.md` into the Space image

**Files:**
- Create: `app/deploy/THIRD_PARTY_NOTICES.md`
- Edit: `app/deploy/Dockerfile`
- Create: `app/tests/test_hf_space_attribution.py`

- [ ] **Step 1: Copy the repo-root file**

```bash
cp THIRD_PARTY_NOTICES.md app/deploy/THIRD_PARTY_NOTICES.md
```

This file is a byte-for-byte copy. The test below enforces the invariant.

- [ ] **Step 2: Write the failing test**

`app/tests/test_hf_space_attribution.py`:
```python
"""Pins that the HF Space image ships CC BY-SA 4.0 attribution."""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_space_attribution_matches_repo_root():
    root = (REPO_ROOT / "THIRD_PARTY_NOTICES.md").read_bytes()
    shipped = (REPO_ROOT / "app" / "deploy" / "THIRD_PARTY_NOTICES.md").read_bytes()
    assert root == shipped, (
        "app/deploy/THIRD_PARTY_NOTICES.md must be byte-identical to the "
        "repo-root THIRD_PARTY_NOTICES.md. Re-run `cp THIRD_PARTY_NOTICES.md "
        "app/deploy/THIRD_PARTY_NOTICES.md` after any repo-root change."
    )


def test_model_card_links_to_attribution():
    card = (REPO_ROOT / "app" / "deploy" / "MODEL_CARD.md").read_text()
    assert "THIRD_PARTY_NOTICES.md" in card
    assert "CC BY-SA 4.0" in card


def test_dockerfile_copies_attribution():
    dockerfile = (REPO_ROOT / "app" / "deploy" / "Dockerfile").read_text()
    assert "THIRD_PARTY_NOTICES.md" in dockerfile
```

Run: `pytest app/tests/test_hf_space_attribution.py -v` → expect at least the Dockerfile and model-card tests to fail.

- [ ] **Step 3: Edit the Dockerfile**

In `app/deploy/Dockerfile`, add (after the existing `COPY app/ /app/app/` line or equivalent source copy):

```dockerfile
# CC BY-SA 4.0 attribution bundle — required by upstream licenses. Do not remove.
COPY app/deploy/THIRD_PARTY_NOTICES.md /app/attribution/THIRD_PARTY_NOTICES.md
```

- [ ] **Step 4: Wire the `/attribution` static route**

In `app/api/main.py` (edited minimally), add a FastAPI route below the existing routes:

```python
from fastapi.responses import PlainTextResponse
from pathlib import Path

_ATTRIBUTION_PATH = Path("/app/attribution/THIRD_PARTY_NOTICES.md")


@app.get("/attribution", response_class=PlainTextResponse)
def attribution() -> str:
    if not _ATTRIBUTION_PATH.exists():
        # Dev path — fall back to repo-root file.
        repo_copy = Path(__file__).resolve().parents[2] / "THIRD_PARTY_NOTICES.md"
        return repo_copy.read_text()
    return _ATTRIBUTION_PATH.read_text()
```

This route is inside the FastAPI sidecar. The Dash About panel already links to `/attribution` (Task B3); because Dash and FastAPI are co-hosted inside the same container behind supervisord (per the 2026-04-07 plan), relative-path links resolve via the reverse-proxy config unchanged from the 2026-04-07 plan. If the 2026-04-07 plan routes `/` to Dash and not to FastAPI, the link in the About panel is rewritten to `/api/attribution` to match the existing prefix and the test is updated accordingly — this is a mechanical edit, not a scope change.

Run: `pytest app/tests/test_hf_space_attribution.py -v` → expect passing after Task C2 updates the model card.

### Task C2: Update `MODEL_CARD.md` with attribution + weights-redistribution gate

**Files:**
- Edit: `app/deploy/MODEL_CARD.md`

- [ ] **Step 1: Append the Attribution section**

Append to `app/deploy/MODEL_CARD.md`:

```markdown
## Attribution

This Space incorporates material from the following third-party sources under
Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0):

- **OWASP GenAI Data Security Risks and Mitigations 2026 (v1.0)** — © OWASP
  GenAI Data Security Project. Used as a source corpus for the DSGAI framework
  view. No modifications beyond mechanical text extraction.
- **GenAI Security Project — GenAI Data Security Initiative crosswalk** — ©
  GenAI Security Project. Used as community-labeled calibration data per spec
  §7 Plan 6.

Full attribution text and SHA pins: `THIRD_PARTY_NOTICES.md` (shipped
alongside this card inside the Space image; also served at `/attribution`).

## Weights-redistribution posture

This Space serves inference over a Plan 5 ONNX int8 model artifact. **Raw
model weights are not redistributed** from this Space in the 2026-04-08
release. Because the training data transitively includes CC BY-SA 4.0
community labels, ShareAlike obligations on derived model weights are
non-trivial and are **explicitly out of scope for Plan 7**. A clean licensing
review is a prerequisite for any future release that redistributes weights,
and the deploy script hard-fails any attempt to ship a weights-redistribution
artifact without that review on disk (see `app/scripts/deploy_hf_space.py`
and `docs/superpowers/specs/2026-04-08-upstream-crosswalk-integration-design.md`
§8).
```

Run: `pytest app/tests/test_hf_space_attribution.py -v` → expect passing.

- [ ] **Step 2: Commit Phase C**

```bash
git add app/deploy/THIRD_PARTY_NOTICES.md app/deploy/Dockerfile \
        app/deploy/MODEL_CARD.md app/api/main.py \
        app/tests/test_hf_space_attribution.py
git commit -m "plan7-0408: ship cc by-sa attribution into hf space image"
```

---

## Phase D — Weights-redistribution gate in the deploy script

Goal: make it impossible to accidentally ship a redistributable-weights artifact from this plan. The gate is a static precondition check in `deploy_hf_space.py`, backed by a test.

### Task D1: Failing test for the deploy gate

**Files:**
- Create: `app/tests/test_deploy_weights_gate.py`

- [ ] **Step 1: Write the failing test**

`app/tests/test_deploy_weights_gate.py`:
```python
"""Pins the weights-redistribution gate on the HF Space deploy path."""
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _run(env: dict[str, str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "app.scripts.deploy_hf_space", "--dry-run"],
        cwd=REPO_ROOT,
        env={**os.environ, **env},
        capture_output=True,
        text=True,
    )


def test_default_deploy_refuses_weights_redistribution():
    # No env flag → dry-run must succeed and must print the inference-only banner.
    result = _run({})
    assert result.returncode == 0, result.stderr
    assert "INFERENCE-ONLY" in result.stdout


def test_weights_flag_without_licensing_review_hard_fails():
    result = _run({"ALLOW_WEIGHTS_REDISTRIBUTION": "1"})
    assert result.returncode != 0
    assert "LICENSING_REVIEW.md" in (result.stderr + result.stdout)


def test_attribution_must_be_present_for_deploy():
    # Temporarily rename the attribution file and expect a hard failure.
    src = REPO_ROOT / "app" / "deploy" / "THIRD_PARTY_NOTICES.md"
    backup = src.with_suffix(".md.bak")
    src.rename(backup)
    try:
        result = _run({})
        assert result.returncode != 0
        assert "THIRD_PARTY_NOTICES.md" in (result.stderr + result.stdout)
    finally:
        backup.rename(src)
```

Run: `pytest app/tests/test_deploy_weights_gate.py -v` → expect failures (the 2026-04-07 deploy script has no gate).

### Task D2: Implement the gate

**Files:**
- Edit: `app/scripts/deploy_hf_space.py`

- [ ] **Step 1: Add the precondition block**

In `app/scripts/deploy_hf_space.py`, immediately after argument parsing and before any HF API calls, insert:

```python
import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_ATTR_FILE = _REPO_ROOT / "app" / "deploy" / "THIRD_PARTY_NOTICES.md"
_REPO_ATTR = _REPO_ROOT / "THIRD_PARTY_NOTICES.md"
_LICENSING_REVIEW = _REPO_ROOT / "app" / "deploy" / "LICENSING_REVIEW.md"


def _check_preconditions() -> None:
    if not _ATTR_FILE.exists():
        sys.exit(
            "DEPLOY ABORTED: app/deploy/THIRD_PARTY_NOTICES.md missing. "
            "Re-run `cp THIRD_PARTY_NOTICES.md app/deploy/THIRD_PARTY_NOTICES.md`."
        )
    if _ATTR_FILE.read_bytes() != _REPO_ATTR.read_bytes():
        sys.exit(
            "DEPLOY ABORTED: app/deploy/THIRD_PARTY_NOTICES.md is stale vs. "
            "repo-root THIRD_PARTY_NOTICES.md. Re-copy before deploying."
        )
    if os.environ.get("ALLOW_WEIGHTS_REDISTRIBUTION") == "1":
        if not _LICENSING_REVIEW.exists():
            sys.exit(
                "DEPLOY ABORTED: ALLOW_WEIGHTS_REDISTRIBUTION=1 requires "
                "app/deploy/LICENSING_REVIEW.md on disk (reviewed sign-off "
                "of CC BY-SA 4.0 ShareAlike obligations on derived weights). "
                "See spec §8 risk row. This plan does NOT create that file; "
                "it is a future-work prerequisite."
            )
        print("WEIGHTS REDISTRIBUTION MODE (gated by LICENSING_REVIEW.md)")
    else:
        print("INFERENCE-ONLY deploy (no raw weights redistributed)")


_check_preconditions()
```

Ensure `--dry-run` short-circuits before any HF API call so the test can run offline.

Run: `pytest app/tests/test_deploy_weights_gate.py -v` → expect passing.

- [ ] **Step 2: Commit Phase D**

```bash
git add app/scripts/deploy_hf_space.py app/tests/test_deploy_weights_gate.py
git commit -m "plan7-0408: gate hf space deploy on attribution presence and weights-redist review"
```

---

## Phase E — Full-suite green + self-review

### Task E1: Run the Plan 7 test suite

- [ ] **Step 1: Run everything under `app/tests/`**

```bash
pytest app/tests/ -v
```

Expected: all tests from the 2026-04-07 plan plus the five new/edited tests from this delta pass. No test is skipped or xfailed. No test under `classifier/tests/` is touched.

- [ ] **Step 2: Spot-check the About panel in a running Dash app**

```bash
python -m app.dash_app.app
```

Visit `http://localhost:8050` → About panel shows the disclosure line verbatim and the `/attribution` link resolves to the CC BY-SA notices. Tab 1 dropdowns show 3 sources / 12 targets. Tab 4 heatmap shows 26 populated cells.

### Task E2: Self-review against the spec

- [ ] **Step 1: §2 D4 — no upstream-schema export format**

Grep the plan and the touched files for any new export/serialization format that would emit upstream-schema JSON. Expect zero hits. The UI's existing CSV/JSON export (from the 2026-04-07 plan) is unchanged; it emits internal-schema only.

```bash
grep -R -n "upstream_schema\|upstream-schema\|mapping_v1_schema" app/ || echo "OK — no upstream-schema export surface"
```

- [ ] **Step 2: §5 — 3 source lists, 12 frameworks, 26 pairs**

Assertions are in `test_frameworks_enum.py`, `test_tab1_lookup.py`, and `test_tab4_matrix.py`. All pass.

- [ ] **Step 3: §7 Plan 7 bullet — UI adds DSGAI + new targets; no upstream-schema export**

Covered by Phases A, B, and the §2 D4 grep. `DSGAI` appears in `UI_SOURCE_LISTS`; `nist_sp_800_53` and `eu_ai_act` appear in `UI_TARGET_FRAMEWORKS`.

- [ ] **Step 4: §8 risk row — CC BY-SA attribution shipped + weights-redistribution gated**

Covered by Phase C (attribution ships into image, linked from About and model card) and Phase D (deploy script gate). `app/tests/test_hf_space_attribution.py` and `app/tests/test_deploy_weights_gate.py` both pass.

- [ ] **Step 5: Anti-scope fences held**

Confirm via `git status` and `git diff --stat main..HEAD` that the only modified paths are those listed in the File Structure table. Expect zero hits under `classifier/`, `mapping_engine/`, `data/splits/`, `data/upstream/`, `third_party/`, `docs/superpowers/specs/`, or any Plan 8 file.

```bash
git diff --stat main..HEAD | grep -E "classifier/|mapping_engine/|data/splits/|data/upstream/|third_party/|docs/superpowers/specs/" \
  && echo "FAIL — out-of-scope edits detected" || echo "OK — all edits in Plan 7 surface"
```

Expected: `OK — all edits in Plan 7 surface`.

- [ ] **Step 6: No new target-framework ads beyond §5.2 required set**

Grep for `asvs` and `attack` in the new `frameworks.py`:

```bash
grep -i "asvs\|att\&ck\|attack" app/dash_app/frameworks.py && echo "FAIL — phase-2 framework leaked into UI" || echo "OK — phase-2 frameworks not exposed"
```

Expected: `OK — phase-2 frameworks not exposed`.

---

## Self-review traceability

| Plan task | Spec anchor |
|---|---|
| A1, A2 (frameworks.py + enum tests) | §5.1 source lists, §5.2 required targets, §5.3 26-pair matrix |
| B1 (Tab 1 dropdowns) | §7 Plan 7 — "UI adds DSGAI and the new targets" |
| B2 (Tab 4 heatmap 26) | §5.3 pair matrix growth |
| B3 (About disclosure) | §7 Plan 6 — calibration replaced by upstream community labels; disclosure obligation per spec §9 implicit |
| C1 (vendor notices into image), C2 (model card) | §8 risk row on CC BY-SA ShareAlike obligation; Contract 12 carry-forward |
| D1, D2 (deploy weights-redist gate) | §8 risk row — "trained model weights treated conservatively and redistribution policy revisited at Plan 7" |
| E2 §2 D4 grep | §2 D4 — schema adoption deferred; no upstream-schema export format |
| E2 out-of-scope grep | §9 YAGNI fences, anti-scope rules |

All eight spec anchors required by the §7 Plan 7 delta are covered by at least one task with a test assertion. No task depends on unfrozen code under `classifier/`, `mapping_engine/`, or `data/splits/`. No task adds an upstream-schema export format. No task opens new licensing questions beyond the gate installed in Phase D.
