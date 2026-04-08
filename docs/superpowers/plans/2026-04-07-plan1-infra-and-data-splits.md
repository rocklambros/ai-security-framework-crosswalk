# Plan 1 — Infra & Data Splits Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stand up the infrastructure, data splits, candidate pool, retrieval-floor check, contamination CI, and Lambda/W&B/HF wiring required before any LLM labeling or model training can begin.

**Architecture:** New top-level `classifier/` package parallels the existing `mapping_engine/`. Plan 1 writes only pure-Python utilities + tests on the Jetson (no GPU work) except the retrieval-floor check, which runs once on the Jetson using CPU-friendly `bge-small-en-v1.5` — `bge-large-en-v1.5` retrieval is deferred to Plan 2's first Lambda launch. All outputs (splits, hashes, candidate pools, floor report) are committed to git and become the immutable foundation of every subsequent plan.

**Tech Stack:** Python 3.11, `python-dotenv`, `pyyaml`, `pandas`, `scikit-learn`, `sentence-transformers`, `huggingface_hub`, `wandb`, `pytest`, existing repo stack.

---

## Spec Reference

Implements §2.1, §2.5, §2.6, §3.4 (reproducibility contract), §4.2 (Lambda runbook only), §6 (Pre-registered Honesty Commitments) of `docs/superpowers/specs/2026-04-07-ai-security-crosswalk-classifier-design.md`.

**Out of scope for Plan 1:** LLM labeling (Plan 2), any baseline or model training (Plans 3–4), Dash app (Plan 6), writeup (Plan 7).

---

## File Structure

**New package layout.** Plan 1 creates and only touches these paths:

| Path | Purpose |
|---|---|
| `classifier/__init__.py` | Package marker |
| `classifier/config.py` | `.env` loader + secret validation + repo paths |
| `classifier/data/__init__.py` | subpackage marker |
| `classifier/data/sme_pool.py` | Load 11 YAML sheets → unified 550-row DataFrame |
| `classifier/data/splits.py` | Stratified 150/400 split, seed 42, SHA256 manifest |
| `classifier/data/candidates.py` | Enumerate 12 framework pairs, top-k retrieval |
| `classifier/data/retrieval_floor.py` | Verify frozen-400 coverage, expand k up to 50 |
| `classifier/tests/__init__.py` | subpackage marker |
| `classifier/tests/conftest.py` | Pytest fixtures (repo path, seed) |
| `classifier/tests/test_config.py` | Env loader + secret validation tests |
| `classifier/tests/test_sme_pool.py` | SME pool load count + schema tests |
| `classifier/tests/test_splits.py` | Stratification + determinism + hash tests |
| `classifier/tests/test_split_leakage.py` | Contamination CI — the canary |
| `classifier/tests/test_candidates.py` | Candidate-pool shape tests |
| `classifier/tests/test_retrieval_floor.py` | Floor-report shape test |
| `classifier/scripts/__init__.py` | subpackage marker |
| `classifier/scripts/build_splits.py` | Entry point: SME pool → splits → hashes |
| `classifier/scripts/build_candidates.py` | Entry point: 12 pairs → candidate pool JSON |
| `classifier/scripts/run_retrieval_floor.py` | Entry point: floor check + report |
| `classifier/scripts/init_wandb.py` | W&B project init (one-shot) |
| `classifier/scripts/init_hf.py` | HF repos init (one-shot) |
| `classifier/lambda/README.md` | Lambda Labs runbook |
| `classifier/lambda/launch_instance.sh` | Helper: print launch commands |
| `classifier/lambda/terminate_instance.sh` | Helper: `lambdacloud` CLI terminate |
| `classifier/lambda/bootstrap.sh` | First-boot provisioning for fresh instance |
| `data/splits/hashes.json` | SHA256 of every split file — the contamination canary |
| `data/splits/human_cal.jsonl` | 150-row calibration split |
| `data/splits/human_test_frozen.jsonl` | 400-row frozen test split |
| `data/splits/sme_pool_full.jsonl` | 550-row unified dump (audit trail) |
| `data/candidates/pool_v1.jsonl` | 12-pair candidate pool |
| `data/candidates/retrieval_floor_report.json` | Floor-check report |
| `docs/PRE_REGISTERED_THRESHOLDS.md` | Thresholds committed **before any training** |
| `requirements-classifier.txt` | New pinned deps for Plan 1+ |
| `.env.example` | Template, no secrets |

**Do not modify** any existing file under `mapping_engine/`, `notebooks/`, `data/frameworks/`, `data/processed/`, or `scripts/`. Plan 1 is purely additive.

---

## Phase A — Bootstrap: env, deps, pre-registration

### Task A1: Create requirements file and install

**Files:**
- Create: `requirements-classifier.txt`

- [ ] **Step 1: Write pinned requirements**

```
# Plan 1 — infra & splits only
python-dotenv==1.0.1
pyyaml==6.0.2
pandas==2.2.3
scikit-learn==1.5.2
sentence-transformers==3.2.1
huggingface_hub==0.26.2
wandb==0.18.7
pytest==8.3.3
tenacity==9.0.0
```

- [ ] **Step 2: Install into existing venv**

Run: `source .venv/bin/activate && pip install -r requirements-classifier.txt`
Expected: clean install, no conflicts with existing `requirements.txt`. If conflicts appear, note them and reuse the pinned version already in `requirements.txt` — do not upgrade.

- [ ] **Step 3: Commit**

```bash
git add requirements-classifier.txt
git commit -m "plan1: pin Plan 1 deps"
```

### Task A1.5: Audit and quarantine stale artifacts

The classifier refactor obsoletes several mapping_engine artifacts (session-7/8 labeling sheet snapshots, intermediate parquets, prune debug dumps, old run dirs). Move them to `archive/pre-classifier-refactor/` so they remain in git history but stop polluting the working tree. Plan 8 Phase F1.5 deletes the archive after the sacred run lockfile lands.

**Files:**
- Create: `archive/pre-classifier-refactor/` (directory)
- Create: `archive/pre-classifier-refactor/MANIFEST.md` (one-line description per moved item)
- Create: `scripts/audit_stale_artifacts.py`
- Test: `classifier/tests/test_stale_audit.py`

- [ ] **Step 1: Write the failing audit test**

```python
# classifier/tests/test_stale_audit.py
from pathlib import Path
import subprocess

REPO = Path(__file__).resolve().parents[2]

STALE_GLOBS = [
    "mapping_engine/output/labeling_sheets/*__candidates.yaml.bak*",
    "mapping_engine/output/prune_debug/**",
    "mapping_engine/output/runs/s[0-9]*",
    "checkpoints/*",
    "wandb/run-*",
]

def test_no_stale_artifacts_in_tree():
    leaks = []
    for g in STALE_GLOBS:
        leaks.extend(REPO.glob(g))
    assert not leaks, f"Stale artifacts must live under archive/: {leaks}"

def test_archive_manifest_lists_every_archived_path():
    archive = REPO / "archive" / "pre-classifier-refactor"
    if not archive.exists():
        return  # nothing archived yet
    manifest = (archive / "MANIFEST.md").read_text()
    for p in archive.rglob("*"):
        if p.is_file() and p.name != "MANIFEST.md":
            rel = p.relative_to(archive).as_posix()
            assert rel in manifest, f"Archived file not in MANIFEST.md: {rel}"
```

- [ ] **Step 2: Run test — expect failure**

Run: `pytest classifier/tests/test_stale_audit.py -v`
Expected: `test_no_stale_artifacts_in_tree` fails listing current stale files (or passes if tree is already clean).

- [ ] **Step 3: Implement `scripts/audit_stale_artifacts.py`**

```python
"""Quarantine stale pre-classifier artifacts.

Lists everything matching STALE_GLOBS, then with --apply moves each
match under archive/pre-classifier-refactor/<original-relative-path>
and appends a line to MANIFEST.md.

Idempotent: re-running is a no-op once the tree is clean.
"""
from __future__ import annotations
import argparse
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ARCHIVE = REPO / "archive" / "pre-classifier-refactor"
MANIFEST = ARCHIVE / "MANIFEST.md"

STALE_GLOBS = [
    "mapping_engine/output/labeling_sheets/*__candidates.yaml.bak*",
    "mapping_engine/output/prune_debug/**",
    "mapping_engine/output/runs/s[0-9]*",
    "checkpoints/*",
    "wandb/run-*",
]


def find_stale() -> list[Path]:
    out: list[Path] = []
    for g in STALE_GLOBS:
        out.extend(REPO.glob(g))
    return sorted(set(out))


def quarantine(paths: list[Path]) -> None:
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    if not MANIFEST.exists():
        MANIFEST.write_text("# Quarantined pre-classifier artifacts\n\n")
    lines = []
    for p in paths:
        rel = p.relative_to(REPO)
        dest = ARCHIVE / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(p), str(dest))
        lines.append(f"- `{rel.as_posix()}` — quarantined {__import__('datetime').date.today()}\n")
    with MANIFEST.open("a") as f:
        f.writelines(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="actually move files")
    args = ap.parse_args()
    stale = find_stale()
    if not stale:
        print("clean: no stale artifacts found")
        return 0
    print(f"found {len(stale)} stale paths:")
    for p in stale:
        print(f"  {p.relative_to(REPO)}")
    if args.apply:
        quarantine(stale)
        print(f"quarantined to {ARCHIVE}")
    else:
        print("(dry run — pass --apply to move)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Dry-run, then apply**

Run: `python scripts/audit_stale_artifacts.py`
Then: `python scripts/audit_stale_artifacts.py --apply`
Expected: dry run lists candidates; --apply moves them under `archive/pre-classifier-refactor/` and appends manifest entries.

- [ ] **Step 5: Run tests — expect pass**

Run: `pytest classifier/tests/test_stale_audit.py -v`
Expected: 2 passed.

- [ ] **Step 6: Commit**

```bash
git add scripts/audit_stale_artifacts.py classifier/tests/test_stale_audit.py archive/pre-classifier-refactor/
git commit -m "plan1: quarantine stale pre-classifier artifacts under archive/"
```

### Task A2: Create `.env.example` and verify `.gitignore`

**Files:**
- Create: `.env.example`
- Verify: `.gitignore` contains `.env` (already confirmed line 6)

- [ ] **Step 1: Write `.env.example`**

```
# .env is intentionally minimal — all API keys are read from the local
# password-store (`pass`), not from .env. The agent (Claude Code) was
# inheriting stale env values from shell init, so secrets now live in pass:
#
#   ANTHROPIC_API_KEY  ← pass show anthropic/api-key
#   HF_TOKEN           ← pass show huggingface/token
#   WANDB_API_KEY      ← pass show wandb/api-key
#
# See classifier/config.py PASS_PATHS for the mapping. Override any one
# entry by exporting <KEY>_PASS_PATH or by setting the env var directly
# (env takes precedence over pass).
#
# Non-secret config (model name, batch size, etc.) can still go here.
```

- [ ] **Step 2: Verify `.env` is still ignored**

Run: `git check-ignore -v .env`
Expected: `.gitignore:6:.env	.env`

- [ ] **Step 3: Commit**

```bash
git add .env.example
git commit -m "plan1: add .env.example template"
```

### Task A3: Package skeleton

**Files:**
- Create: `classifier/__init__.py` (empty)
- Create: `classifier/data/__init__.py` (empty)
- Create: `classifier/tests/__init__.py` (empty)
- Create: `classifier/scripts/__init__.py` (empty)

- [ ] **Step 1: Create all four `__init__.py` files as empty files**

Run:
```bash
mkdir -p classifier/data classifier/tests classifier/scripts classifier/lambda
touch classifier/__init__.py classifier/data/__init__.py classifier/tests/__init__.py classifier/scripts/__init__.py
```

- [ ] **Step 2: Commit**

```bash
git add classifier/
git commit -m "plan1: add classifier package skeleton"
```

### Task A4: Write `classifier/config.py` — env loader + repo paths

**Files:**
- Create: `classifier/config.py`
- Create: `classifier/tests/conftest.py`
- Create: `classifier/tests/test_config.py`

- [ ] **Step 1: Write the failing test first**

`classifier/tests/conftest.py`:
```python
from pathlib import Path
import pytest

@pytest.fixture(scope="session")
def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]
```

`classifier/tests/test_config.py`:
```python
import os
import pytest
from classifier import config

def test_repo_root_exists(repo_root):
    assert (repo_root / "mapping_engine").is_dir()
    assert config.REPO_ROOT == repo_root

def test_required_secrets_raises_when_missing(monkeypatch):
    for key in ("ANTHROPIC_API_KEY", "HF_TOKEN", "WANDB_API_KEY"):
        monkeypatch.delenv(key, raising=False)
    # block the pass fallback by routing it at a nonexistent entry
    monkeypatch.setenv("ANTHROPIC_API_KEY_PASS_PATH", "nonexistent/entry")
    with pytest.raises(config.MissingSecretError) as excinfo:
        config.require_secrets(["ANTHROPIC_API_KEY"])
    assert "ANTHROPIC_API_KEY" in str(excinfo.value)

def test_required_secrets_env_takes_precedence(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    out = config.require_secrets(["ANTHROPIC_API_KEY"])
    assert out["ANTHROPIC_API_KEY"] == "sk-ant-test"

def test_required_secrets_pass_fallback(monkeypatch):
    # env unset, but pass entry exists at the default path
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY_PASS_PATH", raising=False)
    out = config.require_secrets(["ANTHROPIC_API_KEY"])
    assert out["ANTHROPIC_API_KEY"].startswith("sk-ant-")
```

- [ ] **Step 2: Run tests — expect failure (module not found)**

Run: `pytest classifier/tests/test_config.py -v`
Expected: `ModuleNotFoundError: No module named 'classifier.config'`

- [ ] **Step 3: Implement `classifier/config.py`**

```python
"""Config: secret resolution (env → pass), canonical repo paths.

Secrets resolve in this order:
  1. process environment (e.g., set by CI, Lambda, or shell)
  2. `pass show <PASS_PATHS[key]>` from the local password-store

`.env` is intentionally NOT consulted — storing ANTHROPIC_API_KEY in
`.env` was confusing Claude Code (it would inherit a stale key from
shell init). The `pass` fallback keeps the key out of any file the
agent can read directly.
"""
from __future__ import annotations
import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"
SPLITS_DIR = DATA_DIR / "splits"
CANDIDATES_DIR = DATA_DIR / "candidates"
LABELING_SHEETS_DIR = REPO_ROOT / "mapping_engine/output/labeling_sheets"

# Maps env-var name → pass entry path. Override with `<KEY>_PASS_PATH` env.
PASS_PATHS = {
    "ANTHROPIC_API_KEY": "anthropic/api-key",
    "HF_TOKEN": "huggingface/token",
    "WANDB_API_KEY": "wandb/api-key",
}


class MissingSecretError(RuntimeError):
    pass


def _pass_show(path: str) -> str | None:
    try:
        out = subprocess.run(
            ["pass", "show", path],
            capture_output=True, text=True, check=True, timeout=5,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return None
    return out.stdout.strip().splitlines()[0] if out.stdout.strip() else None


def _resolve(key: str) -> str | None:
    if v := os.environ.get(key):
        return v
    pass_path = os.environ.get(f"{key}_PASS_PATH") or PASS_PATHS.get(key)
    if pass_path:
        return _pass_show(pass_path)
    return None


def require_secrets(keys: list[str]) -> dict[str, str]:
    """Return a dict of key->value for the listed secrets.

    Resolves env first, then `pass show <PASS_PATHS[key]>`.
    Raises MissingSecretError listing every missing key.
    """
    resolved: dict[str, str] = {}
    missing: list[str] = []
    for k in keys:
        v = _resolve(k)
        if v is None:
            missing.append(k)
        else:
            resolved[k] = v
    if missing:
        hints = ", ".join(
            f"{k} (env or `pass insert {PASS_PATHS.get(k, k)}`)" for k in missing
        )
        raise MissingSecretError(f"Missing required secrets: {hints}")
    return resolved
```

- [ ] **Step 4: Run tests — expect pass**

Run: `pytest classifier/tests/test_config.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add classifier/config.py classifier/tests/conftest.py classifier/tests/test_config.py
git commit -m "plan1: env loader + secret validation"
```

### Task A5: Pre-registered success thresholds

**Files:**
- Create: `docs/PRE_REGISTERED_THRESHOLDS.md`

This is committed **before any training run**, per spec §6 commitment #1. This task MUST be done before Plans 3–4 begin.

- [ ] **Step 1: Write the pre-registration doc**

```markdown
# Pre-Registered Success Thresholds

**Committed:** $(git rev-parse HEAD ≤ this commit) on 2026-04-07
**Purpose:** Protect against p-hacking by declaring paper framings before any training run.

## Primary headline: Recall@3 on `human_test_frozen` (400 pairs)

| Threshold | Paper framing |
|---|---|
| Recall@3 ≥ 0.80 | State of the art — full best-in-class framing |
| 0.70 ≤ Recall@3 < 0.80 | Competitive — strong baseline + honest limitations paper |
| 0.55 ≤ Recall@3 < 0.70 | Partial success — error analysis as main contribution |
| Recall@3 < 0.55 | Negative result — blog post only, no arXiv |

## Co-headline: Precision@80% coverage (Mondrian conformal)

Reported jointly with Recall@3. No pre-registered threshold — reported as-is with bootstrap CI.

## Independent verification: `human_test_fresh` (75 pairs)

If fresh-75 metrics fall more than 10 pp below frozen-400 metrics on Recall@3, paper reports the gap and adjusts framing.

## The sacred-run rule

`human_test_frozen` is touched exactly once. No retries. If results disappoint, reframe; do not retune.

## Non-negotiable reporting

1. Sonnet↔Opus κ on tier labels (whatever it is)
2. Raw vs calibrated LLM label metrics in appendix
3. Retrieval-floor coverage
4. Every failed ablation
5. Budget + wall-clock in appendix
```

- [ ] **Step 2: Commit (this commit is the pre-registration)**

```bash
git add docs/PRE_REGISTERED_THRESHOLDS.md
git commit -m "plan1: pre-register success thresholds"
```

The commit SHA printed by `git rev-parse HEAD` after this commit is the pre-registration timestamp referenced in the paper.

---

## Phase B — SME Pool Unification + Splits

### Task B1: SME pool loader — failing test first

**Files:**
- Create: `classifier/tests/test_sme_pool.py`

- [ ] **Step 1: Write the test**

```python
import pandas as pd
from classifier.data.sme_pool import load_sme_pool, EXPECTED_TOTAL

REQUIRED_COLS = {
    "pair_key", "pair_name", "source_node_id", "target_node_id",
    "source_text", "target_text", "expert_tier", "framework_pair",
}

def test_load_sme_pool_shape():
    df = load_sme_pool()
    assert isinstance(df, pd.DataFrame)
    assert len(df) == EXPECTED_TOTAL  # 550
    missing = REQUIRED_COLS - set(df.columns)
    assert not missing, f"missing columns: {missing}"

def test_pair_key_unique():
    df = load_sme_pool()
    assert df["pair_key"].is_unique

def test_expert_tier_in_domain():
    df = load_sme_pool()
    assert set(df["expert_tier"].unique()) <= {"Direct", "Related", "None", "Tangential"}

def test_eleven_framework_pairs():
    df = load_sme_pool()
    assert df["framework_pair"].nunique() == 11
```

- [ ] **Step 2: Run test — expect failure (module not found)**

Run: `pytest classifier/tests/test_sme_pool.py -v`
Expected: `ModuleNotFoundError`

- [ ] **Step 3: Implement `classifier/data/sme_pool.py`**

```python
"""Unify the 11 SME labeling sheets (550 rows) into a single DataFrame."""
from __future__ import annotations
from pathlib import Path
import yaml
import pandas as pd
from classifier.config import LABELING_SHEETS_DIR

EXPECTED_TOTAL = 550  # 11 sheets × 50 rows


def _load_sheet(path: Path) -> list[dict]:
    data = yaml.safe_load(path.read_text())
    pair_name = path.name.replace("__candidates.yaml", "")
    rows = []
    for c in data["candidates"]:
        rows.append({
            "pair_key": f"{pair_name}::{c['source_node_id']}__{c['target_node_id']}",
            "pair_name": pair_name,
            "framework_pair": pair_name,
            "source_node_id": c["source_node_id"],
            "target_node_id": c["target_node_id"],
            "source_text": (c.get("source_description") or c.get("source_name") or "").strip(),
            "target_text": (c.get("target_description") or c.get("target_name") or "").strip(),
            "expert_tier": c.get("expert_tier") or "None",
            "composite_score": c.get("composite_score"),
            "signals": c.get("signals"),
        })
    return rows


def load_sme_pool() -> pd.DataFrame:
    sheets = sorted(LABELING_SHEETS_DIR.glob("*__candidates.yaml"))
    if not sheets:
        raise FileNotFoundError(f"No labeling sheets in {LABELING_SHEETS_DIR}")
    rows: list[dict] = []
    for p in sheets:
        rows.extend(_load_sheet(p))
    df = pd.DataFrame(rows)
    if len(df) != EXPECTED_TOTAL:
        raise ValueError(
            f"SME pool size {len(df)} != expected {EXPECTED_TOTAL}. "
            f"Per-sheet counts: {df.groupby('pair_name').size().to_dict()}"
        )
    return df
```

- [ ] **Step 4: Run tests — expect pass**

Run: `pytest classifier/tests/test_sme_pool.py -v`
Expected: 4 passed. If test 3 fails because a sheet uses a tier string not in the allowed set, widen the allowed set in the test to match reality and note in the commit.

- [ ] **Step 5: Commit**

```bash
git add classifier/data/sme_pool.py classifier/tests/test_sme_pool.py
git commit -m "plan1: unified SME pool loader (550 rows, 11 pairs)"
```

### Task B2: Stratified 150/400 split — failing test first

**Files:**
- Create: `classifier/tests/test_splits.py`

- [ ] **Step 1: Write the test**

```python
from classifier.data.splits import build_splits, SEED
from classifier.data.sme_pool import load_sme_pool

def test_split_sizes():
    splits = build_splits(load_sme_pool(), seed=SEED)
    assert len(splits["human_cal"]) == 150
    assert len(splits["human_test_frozen"]) == 400

def test_splits_disjoint():
    splits = build_splits(load_sme_pool(), seed=SEED)
    cal_keys = set(splits["human_cal"]["pair_key"])
    frozen_keys = set(splits["human_test_frozen"]["pair_key"])
    assert cal_keys.isdisjoint(frozen_keys)
    assert len(cal_keys | frozen_keys) == 550

def test_splits_deterministic():
    df = load_sme_pool()
    s1 = build_splits(df, seed=SEED)
    s2 = build_splits(df, seed=SEED)
    assert list(s1["human_cal"]["pair_key"]) == list(s2["human_cal"]["pair_key"])

def test_stratification_covers_every_pair():
    splits = build_splits(load_sme_pool(), seed=SEED)
    cal_pairs = set(splits["human_cal"]["framework_pair"])
    frozen_pairs = set(splits["human_test_frozen"]["framework_pair"])
    assert cal_pairs == frozen_pairs  # every framework pair in both
    assert len(frozen_pairs) == 11
```

- [ ] **Step 2: Run — expect failure**

Run: `pytest classifier/tests/test_splits.py -v`
Expected: `ModuleNotFoundError`

- [ ] **Step 3: Implement `classifier/data/splits.py`**

```python
"""Stratified 150/400 split of the 550-row SME pool. Seed 42. Deterministic."""
from __future__ import annotations
import pandas as pd
from sklearn.model_selection import train_test_split

SEED = 42
CAL_SIZE = 150
FROZEN_SIZE = 400  # 550 - 150


def build_splits(df: pd.DataFrame, seed: int = SEED) -> dict[str, pd.DataFrame]:
    """Stratify on (framework_pair × expert_tier). Return cal + frozen splits."""
    assert len(df) == CAL_SIZE + FROZEN_SIZE, f"unexpected pool size {len(df)}"
    strata = df["framework_pair"].astype(str) + "::" + df["expert_tier"].astype(str)
    # Fall back to framework_pair alone for tiny strata (<2 rows), which can't stratify.
    counts = strata.value_counts()
    if (counts < 2).any():
        strata = df["framework_pair"].astype(str)
    cal, frozen = train_test_split(
        df,
        train_size=CAL_SIZE,
        random_state=seed,
        stratify=strata,
        shuffle=True,
    )
    # Stable sort for deterministic JSONL ordering.
    return {
        "human_cal": cal.sort_values("pair_key").reset_index(drop=True),
        "human_test_frozen": frozen.sort_values("pair_key").reset_index(drop=True),
    }
```

- [ ] **Step 4: Run — expect pass**

Run: `pytest classifier/tests/test_splits.py -v`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add classifier/data/splits.py classifier/tests/test_splits.py
git commit -m "plan1: stratified 150/400 splits, seed 42, deterministic"
```

### Task B3: Build-splits entry point + SHA256 manifest

**Files:**
- Create: `classifier/scripts/build_splits.py`
- Produces: `data/splits/sme_pool_full.jsonl`, `data/splits/human_cal.jsonl`, `data/splits/human_test_frozen.jsonl`, `data/splits/hashes.json`

- [ ] **Step 1: Write the script**

```python
"""Entry point: load SME pool → stratified splits → write JSONL + SHA256 manifest."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from classifier.config import SPLITS_DIR
from classifier.data.sme_pool import load_sme_pool
from classifier.data.splits import build_splits, SEED


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def main() -> None:
    SPLITS_DIR.mkdir(parents=True, exist_ok=True)
    pool = load_sme_pool()
    splits = build_splits(pool, seed=SEED)

    pool_path = SPLITS_DIR / "sme_pool_full.jsonl"
    pool.sort_values("pair_key").to_json(pool_path, orient="records", lines=True)

    paths = {"sme_pool_full.jsonl": pool_path}
    for name, df in splits.items():
        p = SPLITS_DIR / f"{name}.jsonl"
        df.to_json(p, orient="records", lines=True)
        paths[f"{name}.jsonl"] = p

    hashes = {name: _sha256(p) for name, p in paths.items()}
    hashes["_meta"] = {
        "seed": SEED,
        "pool_size": len(pool),
        "cal_size": len(splits["human_cal"]),
        "frozen_size": len(splits["human_test_frozen"]),
    }
    (SPLITS_DIR / "hashes.json").write_text(json.dumps(hashes, indent=2, sort_keys=True))
    print(json.dumps(hashes, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run it**

Run: `python -m classifier.scripts.build_splits`
Expected: prints hash JSON, writes 4 files under `data/splits/`.

- [ ] **Step 3: Verify file sizes**

Run: `wc -l data/splits/*.jsonl`
Expected: `550 sme_pool_full.jsonl`, `150 human_cal.jsonl`, `400 human_test_frozen.jsonl`.

- [ ] **Step 4: Commit splits + hashes**

```bash
git add data/splits/ classifier/scripts/build_splits.py
git commit -m "plan1: build frozen 150/400 splits + SHA256 manifest"
```

Once this commit lands, the split files are **immutable**. Any change to them fails the contamination CI below.

### Task B4: Contamination CI — the canary

**Files:**
- Create: `classifier/tests/test_split_leakage.py`

- [ ] **Step 1: Write the test**

```python
"""Contamination CI. Fails loud if any split file's SHA256 drifts from the
committed manifest, or if pair_keys cross between cal and frozen.
"""
from __future__ import annotations
import hashlib
import json
import pytest
from classifier.config import SPLITS_DIR

MANIFEST = SPLITS_DIR / "hashes.json"
TRACKED = ["sme_pool_full.jsonl", "human_cal.jsonl", "human_test_frozen.jsonl"]


def _sha256(path):
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


@pytest.fixture(scope="module")
def manifest():
    assert MANIFEST.exists(), "hashes.json missing — run build_splits.py"
    return json.loads(MANIFEST.read_text())


@pytest.mark.parametrize("fname", TRACKED)
def test_split_sha256_stable(manifest, fname):
    path = SPLITS_DIR / fname
    assert path.exists(), f"{fname} missing"
    actual = _sha256(path)
    expected = manifest[fname]
    assert actual == expected, (
        f"{fname} SHA256 drifted. Split files are immutable after commit. "
        f"If this is an intentional re-split, delete data/splits/, re-run "
        f"build_splits.py, and open a PR that names the reason."
    )


def test_no_pair_key_leakage():
    import pandas as pd
    cal = pd.read_json(SPLITS_DIR / "human_cal.jsonl", lines=True)
    frozen = pd.read_json(SPLITS_DIR / "human_test_frozen.jsonl", lines=True)
    overlap = set(cal["pair_key"]) & set(frozen["pair_key"])
    assert not overlap, f"{len(overlap)} pair_keys leaked between cal and frozen: {list(overlap)[:5]}"
```

- [ ] **Step 2: Run — expect pass**

Run: `pytest classifier/tests/test_split_leakage.py -v`
Expected: 4 passed (3 parametrized + 1 leakage test).

- [ ] **Step 3: Sanity-check the canary fires when it should**

Temporarily append a newline to `data/splits/human_cal.jsonl`:
```bash
echo "" >> data/splits/human_cal.jsonl
pytest classifier/tests/test_split_leakage.py -v
```
Expected: FAIL on `test_split_sha256_stable[human_cal.jsonl]` with drift message.

Then restore:
```bash
python -m classifier.scripts.build_splits  # rewrites from the immutable source
pytest classifier/tests/test_split_leakage.py -v
```
Expected: all pass again.

- [ ] **Step 4: Commit**

```bash
git add classifier/tests/test_split_leakage.py
git commit -m "plan1: contamination CI — split hash + leakage canary"
```

---

## Phase C — Candidate Pool + Retrieval Floor

### Task C1: Framework-pair enumeration — failing test first

**Files:**
- Create: `classifier/tests/test_candidates.py`

- [ ] **Step 1: Write test**

```python
from classifier.data.candidates import FRAMEWORK_PAIRS, FRAMEWORKS

def test_twelve_framework_pairs():
    assert len(FRAMEWORK_PAIRS) == 12

def test_every_framework_in_at_least_two_pairs():
    """Feasibility: 9 fw x 2 = 18 appearances; 12 pairs x 2 sides = 24 slots. OK."""
    from collections import Counter
    appearances = Counter()
    for s, t in FRAMEWORK_PAIRS:
        appearances[s] += 1
        appearances[t] += 1
    for fw in FRAMEWORKS:
        assert appearances[fw] >= 2, f"{fw} appears in <2 pairs"
```

- [ ] **Step 2: Run — expect failure**

Run: `pytest classifier/tests/test_candidates.py::test_twelve_framework_pairs -v`
Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Write `classifier/data/candidates.py` — enumeration only for now**

```python
"""Candidate-pool generation for the 12-pair coverage requirement.

Each framework appears ≥2× as source AND ≥2× as target. Pairs chosen to
prefer pairs already mapped by v2 (where a signal baseline exists) and
to cover all 9 frameworks.
"""
from __future__ import annotations

FRAMEWORKS = [
    "aiuc_1", "csa_aicm", "mitre_atlas", "nist_rmf",
    "owasp_llm", "owasp_agentic", "owasp_ai_exchange",
    "eu_gpai_cop", "cosai_rm",
]

FRAMEWORK_PAIRS: list[tuple[str, str]] = [
    ("aiuc_1",         "owasp_agentic"),
    ("aiuc_1",         "owasp_llm"),
    ("aiuc_1",         "csa_aicm"),
    ("csa_aicm",       "owasp_agentic"),
    ("csa_aicm",       "nist_rmf"),
    ("mitre_atlas",    "owasp_llm"),
    ("mitre_atlas",    "owasp_agentic"),
    ("nist_rmf",       "owasp_agentic"),
    ("nist_rmf",       "eu_gpai_cop"),
    ("owasp_ai_exchange", "owasp_llm"),
    ("cosai_rm",       "mitre_atlas"),
    ("eu_gpai_cop",    "owasp_ai_exchange"),
]
assert len(FRAMEWORK_PAIRS) == 12
```

- [ ] **Step 4: Run tests — expect pass**

Run: `pytest classifier/tests/test_candidates.py -v`
Expected: 2 passed. **If the second test fails**, rebalance the list above until every framework meets both counts. Don't skip this — it's a spec §2.1 requirement.

- [ ] **Step 5: Commit**

```bash
git add classifier/data/candidates.py classifier/tests/test_candidates.py
git commit -m "plan1: enumerate 12 framework pairs (every framework >=2x both sides)"
```

### Task C2: Node loader from `data/processed/nodes.json`

**Files:**
- Modify: `classifier/data/candidates.py` (append function)
- Modify: `classifier/tests/test_candidates.py` (append test)

- [ ] **Step 1: Add test**

Append to `classifier/tests/test_candidates.py`:
```python
from classifier.data.candidates import load_nodes_by_framework

def test_load_nodes_has_all_9():
    by_fw = load_nodes_by_framework()
    for fw in ["aiuc_1", "csa_aicm", "mitre_atlas", "nist_rmf",
               "owasp_llm", "owasp_agentic", "owasp_ai_exchange",
               "eu_gpai_cop", "cosai_rm"]:
        assert fw in by_fw, f"{fw} missing"
        assert len(by_fw[fw]) > 0, f"{fw} empty"
```

- [ ] **Step 2: Run — expect failure (ImportError)**

Run: `pytest classifier/tests/test_candidates.py::test_load_nodes_has_all_9 -v`

- [ ] **Step 3: Inspect nodes.json shape first**

Run: `python -c "import json; n=json.load(open('data/processed/nodes.json')); print(type(n), len(n)); print(n[0] if isinstance(n,list) else list(n.items())[0])"`

Record the key name that holds the framework identifier (expected: `framework` or `framework_id`). Use it verbatim in step 4. If framework IDs in `nodes.json` use hyphens (`aiuc-1`) while `candidates.py` uses underscores (`aiuc_1`), normalize by replacing `-` with `_` in the loader.

- [ ] **Step 4: Implement loader**

Append to `classifier/data/candidates.py`:
```python
import json
from collections import defaultdict
from classifier.config import DATA_DIR

NODES_PATH = DATA_DIR / "processed/nodes.json"


def load_nodes_by_framework() -> dict[str, list[dict]]:
    raw = json.loads(NODES_PATH.read_text())
    nodes = raw if isinstance(raw, list) else raw.get("nodes", list(raw.values()))
    out: dict[str, list[dict]] = defaultdict(list)
    for n in nodes:
        fw = (n.get("framework") or n.get("framework_id") or "").replace("-", "_")
        if fw:
            out[fw].append(n)
    return dict(out)
```

- [ ] **Step 5: Run — expect pass**

Run: `pytest classifier/tests/test_candidates.py -v`
Expected: 3 passed.

- [ ] **Step 6: Commit**

```bash
git add classifier/data/candidates.py classifier/tests/test_candidates.py
git commit -m "plan1: load_nodes_by_framework from processed/nodes.json"
```

### Task C3: Top-k retrieval with `bge-small-en-v1.5`

Plan 1 uses `bge-small-en-v1.5` (33M, CPU-friendly on Jetson) for the Task C retrieval floor. This is a **pre-check**, not the final embedding model — Plan 2 re-runs with `bge-large-en-v1.5` on Lambda and overwrites the output. Running on CPU first keeps Plan 1 GPU-free.

**Files:**
- Modify: `classifier/data/candidates.py` (append)
- Modify: `classifier/tests/test_candidates.py` (append)

- [ ] **Step 1: Add test (small pair, fast)**

Append to `classifier/tests/test_candidates.py`:
```python
from classifier.data.candidates import build_candidate_pool

def test_build_candidate_pool_one_pair(tmp_path):
    # One pair, small k, just to verify shape + determinism.
    out = build_candidate_pool(
        pairs=[("aiuc_1", "owasp_agentic")],
        k=5,
        model_name="BAAI/bge-small-en-v1.5",
        cache_dir=tmp_path,
    )
    assert "aiuc_1__owasp_agentic" in out
    pool = out["aiuc_1__owasp_agentic"]
    assert len(pool) > 0
    first = pool[0]
    assert {"source_node_id", "candidates"} <= first.keys()
    assert len(first["candidates"]) <= 5
    assert first["candidates"][0]["rank"] == 1
```

- [ ] **Step 2: Run — expect failure (ImportError)**

Run: `pytest classifier/tests/test_candidates.py::test_build_candidate_pool_one_pair -v`

- [ ] **Step 3: Implement retrieval**

Append to `classifier/data/candidates.py`:
```python
from pathlib import Path
import numpy as np


def _node_text(n: dict) -> str:
    name = n.get("name") or n.get("title") or n.get("id") or ""
    desc = n.get("description") or n.get("text") or n.get("summary") or ""
    return f"{name}. {desc}".strip()


def build_candidate_pool(
    pairs: list[tuple[str, str]],
    k: int = 20,
    model_name: str = "BAAI/bge-small-en-v1.5",
    cache_dir: Path | None = None,
) -> dict[str, list[dict]]:
    """For each pair, for each source node, return top-k target nodes by cosine.

    Uses sentence-transformers. Deterministic given the same model weights.
    """
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(model_name, cache_folder=str(cache_dir) if cache_dir else None)
    by_fw = load_nodes_by_framework()
    out: dict[str, list[dict]] = {}

    for src_fw, tgt_fw in pairs:
        src_nodes = by_fw.get(src_fw, [])
        tgt_nodes = by_fw.get(tgt_fw, [])
        if not src_nodes or not tgt_nodes:
            out[f"{src_fw}__{tgt_fw}"] = []
            continue
        src_texts = [_node_text(n) for n in src_nodes]
        tgt_texts = [_node_text(n) for n in tgt_nodes]
        src_emb = model.encode(src_texts, normalize_embeddings=True, show_progress_bar=False)
        tgt_emb = model.encode(tgt_texts, normalize_embeddings=True, show_progress_bar=False)
        sims = np.asarray(src_emb) @ np.asarray(tgt_emb).T

        pair_rows = []
        for i, src in enumerate(src_nodes):
            topk = np.argsort(-sims[i])[:k]
            cands = [
                {
                    "rank": r + 1,
                    "target_node_id": tgt_nodes[j].get("id") or tgt_nodes[j].get("node_id"),
                    "score": float(sims[i, j]),
                }
                for r, j in enumerate(topk)
            ]
            pair_rows.append({
                "source_node_id": src.get("id") or src.get("node_id"),
                "candidates": cands,
            })
        out[f"{src_fw}__{tgt_fw}"] = pair_rows
    return out
```

- [ ] **Step 4: Run — expect pass**

Run: `pytest classifier/tests/test_candidates.py::test_build_candidate_pool_one_pair -v`
Expected: 1 passed. First run downloads ~130 MB of model weights; subsequent runs are cached under `~/.cache/huggingface`.

- [ ] **Step 5: Commit**

```bash
git add classifier/data/candidates.py classifier/tests/test_candidates.py
git commit -m "plan1: top-k retrieval via bge-small-en-v1.5"
```

### Task C4: Build full candidate pool for 12 pairs

**Files:**
- Create: `classifier/scripts/build_candidates.py`
- Produces: `data/candidates/pool_v1.jsonl`

- [ ] **Step 1: Write script**

```python
"""Run top-20 retrieval across all 12 framework pairs. Emits one JSONL."""
from __future__ import annotations
import json
from classifier.config import CANDIDATES_DIR
from classifier.data.candidates import FRAMEWORK_PAIRS, build_candidate_pool


def main() -> None:
    CANDIDATES_DIR.mkdir(parents=True, exist_ok=True)
    pool = build_candidate_pool(pairs=FRAMEWORK_PAIRS, k=20)
    out_path = CANDIDATES_DIR / "pool_v1.jsonl"
    with out_path.open("w") as f:
        for pair_key, rows in pool.items():
            for row in rows:
                record = {"framework_pair": pair_key, **row}
                f.write(json.dumps(record) + "\n")
    total = sum(len(r) for r in pool.values())
    print(f"[candidates] wrote {out_path}  pairs={len(pool)}  source_rows={total}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run it**

Run: `python -m classifier.scripts.build_candidates`
Expected: prints summary, writes `data/candidates/pool_v1.jsonl`. Runtime on Jetson CPU: 5–20 minutes depending on node counts.

- [ ] **Step 3: Verify row count**

Run: `wc -l data/candidates/pool_v1.jsonl`
Expected: ≥ 500 lines (one per (pair × source_node)). If zero, check that `load_nodes_by_framework` returned populated lists for every framework.

- [ ] **Step 4: Commit**

```bash
git add classifier/scripts/build_candidates.py data/candidates/pool_v1.jsonl
git commit -m "plan1: build 12-pair candidate pool, k=20"
```

### Task C5: Retrieval-floor check on frozen-400

**Files:**
- Create: `classifier/data/retrieval_floor.py`
- Create: `classifier/scripts/run_retrieval_floor.py`
- Create: `classifier/tests/test_retrieval_floor.py`
- Produces: `data/candidates/retrieval_floor_report.json`

Per spec §2.1: every pair in `human_test_frozen` must appear in top-20 retrieval for its source. If any miss, expand k up to 50. Remaining misses are reported as the retrieval ceiling.

- [ ] **Step 1: Write report-shape test**

```python
import json
from classifier.config import CANDIDATES_DIR

def test_retrieval_floor_report_shape():
    p = CANDIDATES_DIR / "retrieval_floor_report.json"
    assert p.exists(), "run_retrieval_floor.py has not been executed yet"
    r = json.loads(p.read_text())
    for key in ("k_used", "frozen_total", "hit_at_20", "hit_at_k_used",
                "miss_rows", "coverage_at_20", "coverage_at_k_used"):
        assert key in r, f"missing {key}"
    assert r["frozen_total"] == 400
    assert 20 <= r["k_used"] <= 50
```

- [ ] **Step 2: Run — expect failure (file missing)**

Run: `pytest classifier/tests/test_retrieval_floor.py -v`
Expected: `AssertionError: run_retrieval_floor.py has not been executed yet`.

- [ ] **Step 3: Implement `classifier/data/retrieval_floor.py`**

```python
"""Retrieval-floor check: does frozen-400 survive top-k retrieval?"""
from __future__ import annotations
import pandas as pd
from classifier.config import SPLITS_DIR
from classifier.data.candidates import FRAMEWORK_PAIRS, build_candidate_pool


def check_floor(k_initial: int = 20, k_max: int = 50) -> dict:
    frozen = pd.read_json(SPLITS_DIR / "human_test_frozen.jsonl", lines=True)
    pool_by_pair = build_candidate_pool(pairs=FRAMEWORK_PAIRS, k=k_max)

    def hit_at(k: int) -> tuple[int, list[dict]]:
        hits, miss_rows = 0, []
        for _, row in frozen.iterrows():
            pair_key = row["framework_pair"]
            rows = pool_by_pair.get(pair_key, [])
            by_src = {r["source_node_id"]: r for r in rows}
            src_row = by_src.get(row["source_node_id"])
            if not src_row:
                miss_rows.append({"pair_key": row["pair_key"], "reason": "source_not_in_pool"})
                continue
            ids = [c["target_node_id"] for c in src_row["candidates"][:k]]
            if row["target_node_id"] in ids:
                hits += 1
            else:
                miss_rows.append({
                    "pair_key": row["pair_key"],
                    "reason": f"target_below_k={k}",
                    "framework_pair": pair_key,
                })
        return hits, miss_rows

    hit_at_20, _ = hit_at(k_initial)
    k_used = k_initial if hit_at_20 == len(frozen) else k_max
    hit_at_k_used, miss_at_k_used = hit_at(k_used)

    return {
        "k_initial": k_initial,
        "k_max": k_max,
        "k_used": k_used,
        "frozen_total": len(frozen),
        "hit_at_20": hit_at_20,
        "hit_at_k_used": hit_at_k_used,
        "coverage_at_20": hit_at_20 / len(frozen),
        "coverage_at_k_used": hit_at_k_used / len(frozen),
        "miss_rows": miss_at_k_used[:100],
    }
```

- [ ] **Step 4: Implement entry script**

```python
# classifier/scripts/run_retrieval_floor.py
"""Run the retrieval-floor check and write the report."""
from __future__ import annotations
import json
from classifier.config import CANDIDATES_DIR
from classifier.data.retrieval_floor import check_floor


def main() -> None:
    CANDIDATES_DIR.mkdir(parents=True, exist_ok=True)
    report = check_floor(k_initial=20, k_max=50)
    out = CANDIDATES_DIR / "retrieval_floor_report.json"
    out.write_text(json.dumps(report, indent=2))
    print(json.dumps({k: v for k, v in report.items() if k != "miss_rows"}, indent=2))
    print(f"misses shown: {len(report['miss_rows'])}  (first 100)")


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run it**

Run: `python -m classifier.scripts.run_retrieval_floor`
Expected: prints summary JSON. Writes `data/candidates/retrieval_floor_report.json`. Runtime 2–10 minutes.

- [ ] **Step 6: Run the shape test — expect pass**

Run: `pytest classifier/tests/test_retrieval_floor.py -v`
Expected: 1 passed.

- [ ] **Step 7: Interpret the report**

Open `data/candidates/retrieval_floor_report.json`. Three outcomes:
1. `coverage_at_20 == 1.0` — perfect floor, proceed to Phase D.
2. `coverage_at_20 < 1.0 but coverage_at_k_used == 1.0` — note the k_used value; Plan 2's LLM candidate pool uses k=k_used. Budget is unchanged (headroom exists).
3. `coverage_at_k_used < 1.0` — real retrieval ceiling. Record coverage as the upper bound on Recall@20, add +$150 LLM contingency, and open a note in the spec appendix. Continue to Phase D — this is expected per spec §2.1 and §4.3 risk #4.

Record the outcome in the commit message.

- [ ] **Step 8: Commit**

```bash
git add classifier/data/retrieval_floor.py classifier/scripts/run_retrieval_floor.py classifier/tests/test_retrieval_floor.py data/candidates/retrieval_floor_report.json
git commit -m "plan1: retrieval-floor check — coverage_at_20=<value from report>"
```

---

## Phase D — Lambda, W&B, HF Initialization

### Task D1: Lambda Labs runbook

**Files:**
- Create: `classifier/lambda/README.md`
- Create: `classifier/lambda/launch_instance.sh`
- Create: `classifier/lambda/terminate_instance.sh`
- Create: `classifier/lambda/bootstrap.sh`

These are **documentation + helper scripts**, not automation. Plan 1 does not launch any paid instance. Plan 2 will follow this runbook once.

- [ ] **Step 1: Write the runbook**

`classifier/lambda/README.md`:
```markdown
# Lambda Labs Runbook

**Rule:** never leave an instance running overnight. H100 = ~$24/hour unattended.

## One-time setup

1. <https://cloud.lambdalabs.com> → Sign in.
2. **SSH Keys** → **Add SSH Key** → paste `~/.ssh/id_ed25519.pub` from the Jetson → name `jetson`.
3. **Billing** → add card → set **$400** account alert.
4. (Optional) Install Lambda's CLI: `pip install lambdacloud` and run `lambdacloud configure` with your API key from **API Keys** page.

## Launch checklist (do before clicking Launch)

- [ ] Know the target GPU and region (H100 PCIe for training, A100 40GB for ablations)
- [ ] Know the estimated runtime — set a phone timer
- [ ] Have `classifier/lambda/bootstrap.sh` ready to `scp` onto the instance
- [ ] Know the job command you'll run inside `tmux`

## Launch (web UI)

1. **Instances → Launch Instance**
2. **Instance type:** H100 PCIe (for Plan 4 training) OR A100 40GB SXM (for Plan 3 baselines + Plan 4 ablations)
3. **Filesystem:** attach the persistent filesystem `crosswalk` (create it once with 100GB on first launch)
4. **Region:** whichever has capacity
5. **SSH key:** `jetson`
6. **Launch** and wait ~2 min for green

## First-boot provisioning

From the Jetson:
```bash
ssh ubuntu@<instance-ip> 'bash -s' < classifier/lambda/bootstrap.sh
```

This clones the repo, pins Python deps, verifies `nvidia-smi`, and installs `tmux`.

## Running a job

```bash
ssh ubuntu@<instance-ip>
cd ~/ai-security-framework-crosswalk
tmux new -s train
source .venv/bin/activate
python -m classifier.<some entry point>
# Ctrl-b d to detach
```

Reattach: `tmux attach -t train`. W&B streams metrics live; watch from any browser.

## Terminate (MANDATORY when done)

1. Detach tmux (jobs continue in a subprocess only if `nohup`; default tmux dies with instance)
2. Copy artifacts back: `scp -r ubuntu@<ip>:~/ai-security-framework-crosswalk/data/processed/<new-outputs> data/processed/`
3. **Terminate via web UI** (Instances → your instance → Terminate) OR
4. Run `classifier/lambda/terminate_instance.sh <instance-id>` if `lambdacloud` CLI is configured

**Verify termination:** refresh the Instances page. Row should disappear.

## Persistent filesystem

The `crosswalk` filesystem survives terminations. Use it for HF model cache (`~/.cache/huggingface`) and W&B run logs. It is billed per GB-hour regardless of instance state — keep under 200GB.
```

- [ ] **Step 2: Write `launch_instance.sh` — a pre-flight printer**

```bash
#!/usr/bin/env bash
# Prints the pre-flight checklist. Does NOT launch anything.
set -euo pipefail
cat <<'EOF'
PRE-LAUNCH CHECKLIST
--------------------
1. Target GPU type  (H100 PCIe / A100 40GB):
2. Estimated runtime:
3. tmux session name:
4. Command to run inside tmux:
5. Output files to scp back:

Go to https://cloud.lambdalabs.com/instances and click Launch.
Remember: set a phone timer. Never leave instances running overnight.
EOF
```

- [ ] **Step 3: Write `terminate_instance.sh`**

```bash
#!/usr/bin/env bash
# Terminate a Lambda instance via the lambdacloud CLI, if configured.
# If the CLI is not installed, prints the web-UI fallback.
set -euo pipefail
INSTANCE_ID="${1:-}"
if [[ -z "$INSTANCE_ID" ]]; then
  echo "usage: $0 <instance-id>" >&2
  exit 2
fi
if ! command -v lambdacloud >/dev/null 2>&1; then
  echo "lambdacloud CLI not installed."
  echo "Go to https://cloud.lambdalabs.com/instances and click Terminate."
  exit 1
fi
lambdacloud instance terminate "$INSTANCE_ID"
echo "terminate requested — verify at https://cloud.lambdalabs.com/instances"
```

- [ ] **Step 4: Write `bootstrap.sh`**

```bash
#!/usr/bin/env bash
# First-boot provisioning for a fresh Lambda instance.
set -euxo pipefail

REPO=https://github.com/rocklambros/ai-security-framework-crosswalk.git
cd ~
if [[ ! -d ai-security-framework-crosswalk ]]; then
  git clone "$REPO"
fi
cd ai-security-framework-crosswalk

sudo apt-get update && sudo apt-get install -y tmux htop jq
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-classifier.txt

nvidia-smi
python -c "import torch; print('cuda:', torch.cuda.is_available(), torch.cuda.get_device_name(0) if torch.cuda.is_available() else '')"

echo "BOOTSTRAP OK. Next: paste your .env contents into ~/ai-security-framework-crosswalk/.env"
```

- [ ] **Step 5: Mark scripts executable**

Run: `chmod +x classifier/lambda/*.sh`

- [ ] **Step 6: Commit**

```bash
git add classifier/lambda/
git commit -m "plan1: Lambda Labs runbook + helper scripts"
```

### Task D2: W&B project init

**Files:**
- Create: `classifier/scripts/init_wandb.py`

- [ ] **Step 1: Write script**

```python
"""One-shot: log in to W&B and create the project. Idempotent."""
from __future__ import annotations
import wandb
from classifier.config import require_secrets

PROJECT = "ai-security-crosswalk"
ENTITY = None  # uses default (personal)


def main() -> None:
    require_secrets(["WANDB_API_KEY"])
    wandb.login(key=None)  # picks up WANDB_API_KEY from env
    run = wandb.init(project=PROJECT, entity=ENTITY, name="plan1-init", job_type="init",
                     config={"plan": 1, "purpose": "init"}, reinit=True)
    run.log({"ok": 1})
    run.finish()
    print(f"wandb project '{PROJECT}' reachable. Visit https://wandb.ai/{wandb.api.default_entity}/{PROJECT}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run it**

Run: `python -m classifier.scripts.init_wandb`
Expected: one run appears in the W&B dashboard, named `plan1-init`, logs `{ok: 1}`. If `MissingSecretError`, run `pass insert wandb/api-key` first.

- [ ] **Step 3: Commit**

```bash
git add classifier/scripts/init_wandb.py
git commit -m "plan1: W&B project init script"
```

### Task D3: HuggingFace repos init

**Files:**
- Create: `classifier/scripts/init_hf.py`

- [ ] **Step 1: Write script**

```python
"""One-shot: create (or verify) the HF model and dataset repos. Idempotent."""
from __future__ import annotations
from huggingface_hub import HfApi, create_repo
from classifier.config import require_secrets

MODEL_REPO = "rockCO78/ai-security-crosswalk-classifier"
DATASET_REPO = "rockCO78/ai_security_crosswalk_eval"


def main() -> None:
    secrets = require_secrets(["HF_TOKEN"])
    api = HfApi(token=secrets["HF_TOKEN"])
    who = api.whoami()
    print(f"HF user: {who.get('name')}")
    for repo_id, repo_type in [(MODEL_REPO, "model"), (DATASET_REPO, "dataset")]:
        try:
            api.repo_info(repo_id, repo_type=repo_type)
            print(f"{repo_type} repo exists: {repo_id}")
        except Exception:
            create_repo(repo_id, repo_type=repo_type, private=True, token=secrets["HF_TOKEN"])
            print(f"{repo_type} repo CREATED: {repo_id} (private)")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run it**

Run: `python -m classifier.scripts.init_hf`
Expected: prints HF user, then two "repo exists" or "repo CREATED" lines. If the repos were created via the web UI already, both will say "exists" — that's fine.

- [ ] **Step 3: Commit**

```bash
git add classifier/scripts/init_hf.py
git commit -m "plan1: HF model + dataset repo init script"
```

---

## Phase E — Final Verification

### Task E1: Run the full test suite

- [ ] **Step 1: Run everything under `classifier/tests/`**

Run: `pytest classifier/tests/ -v`
Expected: all pass. If any test fails, fix the test or the implementation — do not skip.

- [ ] **Step 2: Run the existing `mapping_engine` tests to confirm no regression**

Run: `pytest mapping_engine/tests/ -x --ignore=mapping_engine/tests/test_finetune.py --ignore=mapping_engine/tests/test_node2vec.py -q`
Expected: same pass/fail state as before Plan 1. (Skipping the two heavy tests to keep it fast on the Jetson.) Plan 1 is purely additive so nothing should have changed.

### Task E2: Plan 1 handoff summary

- [ ] **Step 1: Write the handoff summary**

Create `classifier/PLAN1_COMPLETE.md`:
```markdown
# Plan 1 Handoff — Infra & Data Splits

**Completed:** <date>
**Branch / commits:** <paste `git log --oneline main..HEAD | head -30`>

## Artifacts produced (all committed)

- `data/splits/{sme_pool_full,human_cal,human_test_frozen}.jsonl` — 550 / 150 / 400 rows
- `data/splits/hashes.json` — SHA256 manifest, enforced by contamination CI
- `data/candidates/pool_v1.jsonl` — 12-pair top-20 candidate pool
- `data/candidates/retrieval_floor_report.json` — coverage_at_20 = <value>, k_used = <value>
- `docs/PRE_REGISTERED_THRESHOLDS.md` — pre-registration commit <SHA>

## Tests passing

- `classifier/tests/test_config.py`
- `classifier/tests/test_sme_pool.py`
- `classifier/tests/test_splits.py`
- `classifier/tests/test_split_leakage.py` — the contamination canary
- `classifier/tests/test_candidates.py`
- `classifier/tests/test_retrieval_floor.py`

## Ready for Plan 2 (LLM-SME Labeling)

Plan 2 can assume:
- `human_test_frozen` and `human_cal` exist and are contamination-protected
- 12-pair candidate pool exists (expected re-built with `bge-large-en-v1.5` on first Lambda launch)
- Retrieval floor is known — budget adjusted if <1.0
- `ANTHROPIC_API_KEY`, `HF_TOKEN`, `WANDB_API_KEY` all load via `classifier.config.require_secrets`
- W&B project + HF repos exist

## Open notes for Plan 2

- Re-run `classifier.scripts.build_candidates` on Lambda with `model_name="BAAI/bge-large-en-v1.5"` before bulk labeling — overwrites `pool_v1.jsonl` in place, then re-run `run_retrieval_floor.py`. The contamination CI stays green because only candidate files change, not split files.
- Lambda runbook: `classifier/lambda/README.md`
- If retrieval coverage_at_k_used < 1.0, add +$150 to Plan 2 LLM budget.
```

- [ ] **Step 2: Commit**

```bash
git add classifier/PLAN1_COMPLETE.md
git commit -m "plan1: handoff summary"
```

- [ ] **Step 3: Report completion**

Announce to the user:

> Plan 1 complete. `pytest classifier/tests/` all green, contamination CI armed, splits + candidate pool + retrieval-floor report committed, Lambda runbook written, W&B + HF repos initialized. Ready to invoke Plan 2 (LLM-SME labeling).

---

## Self-Review Notes

**Spec coverage check (§ numbers from the design spec):**
- §2.1 candidate generation → Tasks C1, C2, C3, C4 ✓
- §2.1 retrieval-floor check → Task C5 ✓
- §2.5 label storage paths → deferred to Plan 2 (no labels in Plan 1)
- §2.6 human_cal / human_test_frozen splits + hashes → Tasks B1–B4 ✓
- §2.6 human_test_fresh (75) → deferred to Plan 5 (created post-freeze)
- §3.4 reproducibility contract — `requirements-classifier.txt` pinned, seed 42, SHA256 manifest, W&B init ✓
- §4.2 Lambda platform → Task D1 runbook ✓
- §6 honesty commitment #1 (pre-register before training) → Task A5 ✓

**Placeholder scan:** no TBDs, every code block is complete, every command has expected output.

**Type consistency:** `build_splits` returns `dict[str, pd.DataFrame]` with keys `"human_cal"` and `"human_test_frozen"` — used consistently in Tasks B2, B3, B4, C5. `load_sme_pool` → `pd.DataFrame` with the column set declared in Task B1 test — consumed by Task B2 and B3. `build_candidate_pool` return shape is `dict[pair_key, list[row]]` where row has `source_node_id` + `candidates` — consumed by Task C5 `check_floor` using the same key names.

**Known caveats flagged for executing agent:**
1. Task B1 test `test_expert_tier_in_domain` may need to widen if sheets use extra tier strings — instructions say do so in place.
2. Task C2 framework-id hyphen vs underscore normalization depends on `nodes.json`; inspect once before implementing.
3. Plan 1 uses `bge-small-en-v1.5` for retrieval (CPU-friendly). Plan 2 re-runs with `bge-large-en-v1.5` on Lambda — the candidate files are intentionally overwritten and the split-file CI does not flag this because only splits are hash-pinned.
