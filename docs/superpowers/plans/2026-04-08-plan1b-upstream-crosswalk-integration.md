# Plan 1-B — Upstream Crosswalk Integration & Plan 1 Finishing

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Finish the leftover Task C-3/C-4/C-5 work from Plan 1 (`2026-04-07-plan1-infra-and-data-splits.md`) AND deliver the upstream crosswalk integration described in `docs/superpowers/specs/2026-04-08-upstream-crosswalk-integration-design.md` (Tier B, consume-only). On completion, the Phase 0 orchestrator's pre-flight for Phase 2 passes: `data/candidates/pool_v1.jsonl` exists on the enlarged Tier-B framework matrix, the contamination CI gate is green, and all upstream artifacts are committed.

**Architecture:** Three-tier filesystem separation per spec §3 — source corpora live under `data/frameworks/`, the upstream JSON snapshot is pinned read-only under `third_party/genai-crosswalk/`, and derived artifacts (flattened mappings, contamination partition) live under `data/upstream/`. Each new source/target framework gets its own ingester that emits a per-framework node JSON file under `data/processed/frameworks/`, and a single merge step rebuilds `data/processed/nodes.json` from all per-framework files (preserving the original 9 frameworks via a backup-and-merge pattern). Strict source-id-level contamination partitioning is enforced both as a static data-build step AND as a runtime test in the training-batch loader.

**Tech Stack:** Python 3.10+, sentence-transformers (BGE), pytest, BeautifulSoup4 (for HTML parsing of EU AI Act), `lxml` (for OSCAL XML if used), git, sha256.

**Spec reference:** `docs/superpowers/specs/2026-04-08-upstream-crosswalk-integration-design.md` — every task below maps to a spec section.

**Branching:** This plan ships on a feature branch `plan1b/upstream-integration`, NOT directly on `main`. The original Plan 1 was committed to `main`; Plan 1-B is large enough that it warrants a branch + PR. Pre-flight: confirm `git status` is clean (after the pending `.gitignore` commit lands) and `main` is at `5976e1d` or later.

---

## Scope note

ISO/IEC 42001:2023 was dropped from the Tier-B target set (user decision 2026-04-08): paywalled, cannot legally redistribute, and we don't need another framework right now. The new Tier-B targets shipped by this plan are **NIST SP 800-53 rev5** and **EU AI Act** only. The pair matrix is 22 pairs (12 original + 4 DSGAI-as-source + 6 existing-source × new-target).

The `prompts/` `.gitignore` change is committed on `main` as Task 0 (user-approved) so the feature branch starts from a clean tree.

---

## File Structure

**New files (created by this plan):**

- `data/frameworks/owasp-dsgai/MANIFEST.json` — provenance for the DSGAI corpus
- `classifier/data/frameworks/__init__.py`
- `classifier/data/frameworks/dsgai.py` — DSGAI markdown → node ingester
- `classifier/data/frameworks/nist_800_53.py` — NIST SP 800-53 rev5 OSCAL → node ingester
- `classifier/data/frameworks/eu_ai_act.py` — EU AI Act HTML → node ingester
- `classifier/data/frameworks/merge_nodes.py` — merges per-framework node files into `data/processed/nodes.json`
- `classifier/scripts/build_candidates.py` — leftover Plan 1 C-4
- `classifier/data/retrieval_floor.py` — leftover Plan 1 C-5
- `classifier/scripts/run_retrieval_floor.py` — leftover Plan 1 C-5
- `classifier/data/upstream_loader.py` — flattens upstream JSON entries → `data/upstream/mappings_v1.jsonl` + `crossrefs_v1.jsonl`
- `classifier/scripts/build_upstream.py` — entry-point script that runs the loader
- `classifier/data/contamination.py` — strict source-id-level partition computation
- `classifier/scripts/run_contamination_audit.py`
- `classifier/tests/test_dsgai_ingester.py`
- `classifier/tests/test_nist_800_53_ingester.py`
- `classifier/tests/test_eu_ai_act_ingester.py`
- `classifier/tests/test_upstream_loader.py`
- `classifier/tests/test_contamination.py` (the pre-registered honesty firewall test)
- `classifier/tests/test_candidates.py` — extended with Task 1 test
- `classifier/tests/test_retrieval_floor.py`
- `third_party/genai-crosswalk/MANIFEST.json` + snapshot of `crosswalk/data/entries/*.json` and `crosswalk/data/schema.json`
- `data/upstream/mappings_v1.jsonl` (derived; commit it)
- `data/upstream/crossrefs_v1.jsonl` (derived; commit it)
- `data/upstream/partition.json` (derived; commit it)
- `data/upstream/contamination_report.json` (derived; commit it)
- `data/upstream/hashes.json` (derived; commit it)
- `data/processed/frameworks/owasp_dsgai.json` (derived per-framework nodes)
- `data/processed/frameworks/nist_800_53.json` (derived)
- `data/processed/frameworks/eu_ai_act.json` (derived)
- `data/processed/nodes.json.bak.20260408` (backup of the original 9-framework nodes file)
- `data/candidates/pool_v1.jsonl` (FINAL artifact; produced once on Tier-B matrix)
- `data/candidates/retrieval_floor_report.json`
- `THIRD_PARTY_NOTICES.md`
- Per new target framework: a corpus file under `data/frameworks/<framework>/` (downloaded by the implementer in the relevant task's Step 1)

**Modified files:**

- `classifier/data/candidates.py` — append `build_candidate_pool()` function (Task 1); update `FRAMEWORKS` and `FRAMEWORK_PAIRS` constants to Tier-B matrix (Task 13)
- `data/splits/hashes.json` — extend with upstream + new-framework manifest hashes (Task 9)
- `.gitignore` — pre-task commit of the existing local change

**Out of scope (do not touch):**
- `data/splits/human_test_frozen.jsonl` — frozen, byte-identical, never modified
- `data/splits/sme_pool_full.jsonl`, `data/splits/human_cal.jsonl` — Plan 6's domain
- Anything under `mapping_engine/` (Sessions 1-8 artifacts; not part of Plan 1-B)

---

## Pre-flight (do this before Task 1)

- [ ] **Step 1: Commit the pending `.gitignore` change**

```bash
git diff .gitignore
git add .gitignore
git commit -m "ignore prompts/ directory (orchestrator working files)"
```

- [ ] **Step 2: Push and create the feature branch**

```bash
git push origin main
git checkout -b plan1b/upstream-integration
git status
```

Expected: clean tree on `plan1b/upstream-integration`.

- [ ] **Step 3: Verify Phase 1 partial state**

Run:
```bash
ls data/splits/hashes.json data/splits/human_test_frozen.jsonl data/splits/sme_pool_full.jsonl
ls data/processed/nodes.json
ls data/frameworks/owasp-dsgai/OWASP-GenAI-Data-Security-Risks-and-Mitigations-2026-v1.0.md
```
Expected: all five files present. If any are missing, halt and report.

---

## Task 1: Finish leftover Plan 1 Task C-3 — `build_candidate_pool` function

**Files:**
- Modify: `classifier/data/candidates.py` (append)
- Modify: `classifier/tests/test_candidates.py` (append)

This is verbatim the original Plan 1 Task C-3 (see `docs/superpowers/plans/2026-04-07-plan1-infra-and-data-splits.md` lines 1000–1101) which never landed. Reproduced in full so this plan is self-contained.

- [ ] **Step 1: Add the failing test**

Append to `classifier/tests/test_candidates.py`:

```python
from classifier.data.candidates import build_candidate_pool


def test_build_candidate_pool_one_pair(tmp_path):
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

- [ ] **Step 2: Run — expect ImportError**

```bash
pytest classifier/tests/test_candidates.py::test_build_candidate_pool_one_pair -v
```
Expected: FAIL with `ImportError: cannot import name 'build_candidate_pool'`.

- [ ] **Step 3: Implement the function**

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
    """For each (src_fw, tgt_fw) pair, return top-k target nodes per source node by cosine.

    Deterministic given the same model weights. Uses sentence-transformers.
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

```bash
pytest classifier/tests/test_candidates.py::test_build_candidate_pool_one_pair -v
```
Expected: 1 passed. First run downloads ~130 MB of model weights into `~/.cache/huggingface`.

- [ ] **Step 5: Commit**

```bash
git add classifier/data/candidates.py classifier/tests/test_candidates.py
git commit -m "plan1b: build_candidate_pool top-k retrieval (finishes Plan 1 C-3)"
```

---

## Task 2: Finish leftover Plan 1 Task C-4 — `build_candidates.py` script (write only; defer running to Task 14)

**Files:**
- Create: `classifier/scripts/build_candidates.py`

This task **only writes the script.** Running it is deferred to Task 14, after the Tier-B framework matrix lands. Running it now would produce a `pool_v1.jsonl` against the obsolete 12-pair matrix and waste 5–20 minutes of CPU.

- [ ] **Step 1: Create the script**

```python
"""Run top-20 retrieval across all framework pairs in classifier.data.candidates.FRAMEWORK_PAIRS.
Emits one JSONL row per (pair, source_node)."""
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

- [ ] **Step 2: Lint check (script imports resolve)**

```bash
python -c "import classifier.scripts.build_candidates"
```
Expected: no output, exit 0.

- [ ] **Step 3: Commit**

```bash
git add classifier/scripts/build_candidates.py
git commit -m "plan1b: build_candidates entry script (finishes Plan 1 C-4 write phase)"
```

---

## Task 3: Finish leftover Plan 1 Task C-5 — `retrieval_floor.py` + test + script (write only; defer running to Task 14)

**Files:**
- Create: `classifier/data/retrieval_floor.py`
- Create: `classifier/scripts/run_retrieval_floor.py`
- Create: `classifier/tests/test_retrieval_floor.py`

Same deferral as Task 2: write the code, defer execution to Task 14.

- [ ] **Step 1: Write the report-shape test**

```python
# classifier/tests/test_retrieval_floor.py
import json
import pytest
from classifier.config import CANDIDATES_DIR


@pytest.mark.skipif(
    not (CANDIDATES_DIR / "retrieval_floor_report.json").exists(),
    reason="run_retrieval_floor.py has not been executed yet (Task 14)",
)
def test_retrieval_floor_report_shape():
    p = CANDIDATES_DIR / "retrieval_floor_report.json"
    r = json.loads(p.read_text())
    for key in ("k_used", "frozen_total", "hit_at_20", "hit_at_k_used",
                "miss_rows", "coverage_at_20", "coverage_at_k_used"):
        assert key in r, f"missing {key}"
    assert r["frozen_total"] == 400
    assert 20 <= r["k_used"] <= 50
```

Note the `skipif`: this lets the test land before Task 14 runs the actual report. After Task 14, it becomes a real assertion.

- [ ] **Step 2: Run — expect skip (or pass after Task 14)**

```bash
pytest classifier/tests/test_retrieval_floor.py -v
```
Expected: 1 skipped.

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
                miss_rows.append({"pair_key": pair_key, "reason": "source_not_in_pool"})
                continue
            ids = [c["target_node_id"] for c in src_row["candidates"][:k]]
            if row["target_node_id"] in ids:
                hits += 1
            else:
                miss_rows.append({
                    "pair_key": pair_key,
                    "reason": f"target_below_k={k}",
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

- [ ] **Step 4: Implement the entry script**

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

- [ ] **Step 5: Commit**

```bash
git add classifier/data/retrieval_floor.py classifier/scripts/run_retrieval_floor.py classifier/tests/test_retrieval_floor.py
git commit -m "plan1b: retrieval_floor scaffolding (finishes Plan 1 C-5 write phase)"
```

---

## Task 4: DSGAI corpus ingester

**Files:**
- Create: `data/frameworks/owasp-dsgai/MANIFEST.json`
- Create: `classifier/data/frameworks/__init__.py`
- Create: `classifier/data/frameworks/dsgai.py`
- Create: `classifier/tests/test_dsgai_ingester.py`
- Create: `data/processed/frameworks/owasp_dsgai.json` (output of running the ingester)

**Spec reference:** §4.2.

**Parser key fact:** the 21 entries in the OWASP DSGAI markdown appear as plain-text lines of the form `DSGAI## — Title` (em dash `—`, NOT hyphen `-`), NOT under markdown headings. Verify this with `grep -nE "^DSGAI[0-9]{2} — " data/frameworks/owasp-dsgai/OWASP-GenAI-Data-Security-Risks-and-Mitigations-2026-v1.0.md` before writing the parser — confirm exactly 21 matches.

- [ ] **Step 1: Verify entry pattern**

```bash
grep -cE "^DSGAI[0-9]{2} — " data/frameworks/owasp-dsgai/OWASP-GenAI-Data-Security-Risks-and-Mitigations-2026-v1.0.md
```
Expected: `21`. If the count differs, inspect the file with `head -200` and adjust the regex in the parser code below to match the actual format. Common alternates: `DSGAI##: Title`, `## DSGAI## — Title`. Document the chosen regex in the parser docstring.

- [ ] **Step 2: Write the corpus MANIFEST**

```bash
mkdir -p data/frameworks/owasp-dsgai
cat > data/frameworks/owasp-dsgai/MANIFEST.json <<'EOF'
{
  "framework_id": "owasp_dsgai",
  "framework_name": "OWASP GenAI Data Security Risks and Mitigations",
  "version": "1.0",
  "release_date": "2026-03",
  "source_file": "OWASP-GenAI-Data-Security-Risks-and-Mitigations-2026-v1.0.md",
  "source_url": "https://genai.owasp.org/",
  "license": "CC-BY-SA-4.0",
  "attribution": "OWASP GenAI Data Security Project. Licensed under CC BY-SA 4.0.",
  "expected_node_count": 21,
  "id_pattern": "DSGAI(0[1-9]|1[0-9]|2[01])"
}
EOF
```

- [ ] **Step 3: Write the failing test**

```python
# classifier/tests/test_dsgai_ingester.py
import json
from pathlib import Path
import pytest
from classifier.data.frameworks.dsgai import ingest_dsgai

REPO = Path(__file__).resolve().parents[2]
DSGAI_MD = REPO / "data" / "frameworks" / "owasp-dsgai" / "OWASP-GenAI-Data-Security-Risks-and-Mitigations-2026-v1.0.md"


def test_ingest_dsgai_returns_21_nodes():
    nodes = ingest_dsgai(DSGAI_MD)
    assert len(nodes) == 21
    ids = [n["local_id"] for n in nodes]
    assert ids == [f"DSGAI{i:02d}" for i in range(1, 22)]


def test_ingest_dsgai_nodes_have_required_fields():
    nodes = ingest_dsgai(DSGAI_MD)
    for n in nodes:
        assert n["framework"] == "owasp_dsgai"
        assert n["node_id"].startswith("owasp_dsgai:DSGAI")
        assert n["title"] and isinstance(n["title"], str)
        assert n["text"] and len(n["text"]) > 50, f"node {n['local_id']} has too-short body"
```

- [ ] **Step 4: Run — expect ImportError**

```bash
pytest classifier/tests/test_dsgai_ingester.py -v
```
Expected: FAIL with `ModuleNotFoundError: classifier.data.frameworks.dsgai`.

- [ ] **Step 5: Implement the ingester**

```python
# classifier/data/frameworks/__init__.py
```
(empty file)

```python
# classifier/data/frameworks/dsgai.py
"""OWASP DSGAI 2026 markdown → node list ingester.

Source corpus is published OWASP DSGAI 2026 v1.0 (CC BY-SA 4.0).
The 21 entries appear as plain-text headings of the form
`DSGAI## — Title` (em dash). Each entry's body is everything between
its header and the next entry's header (or EOF).
"""
from __future__ import annotations
import re
from pathlib import Path

ENTRY_RE = re.compile(r"^(DSGAI(\d{2})) — (.+)$", re.MULTILINE)


def ingest_dsgai(md_path: Path) -> list[dict]:
    text = Path(md_path).read_text(encoding="utf-8")
    matches = list(ENTRY_RE.finditer(text))
    if len(matches) != 21:
        raise ValueError(
            f"expected 21 DSGAI entries, found {len(matches)} in {md_path}. "
            f"Check the entry regex against the actual file format."
        )

    nodes: list[dict] = []
    for i, m in enumerate(matches):
        local_id = m.group(1)            # "DSGAI01"
        title = m.group(3).strip()       # "Sensitive Data Leakage"
        body_start = m.end()
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[body_start:body_end].strip()

        nodes.append({
            "node_id": f"owasp_dsgai:{local_id}",
            "local_id": local_id,
            "framework": "owasp_dsgai",
            "title": title,
            "text": body,
        })
    return nodes
```

- [ ] **Step 6: Run — expect pass**

```bash
pytest classifier/tests/test_dsgai_ingester.py -v
```
Expected: 2 passed. If the entry-count assertion fails, the regex needs adjustment per Step 1's diagnostic.

- [ ] **Step 7: Run the ingester and write the per-framework JSON**

```bash
mkdir -p data/processed/frameworks
python -c "
import json
from pathlib import Path
from classifier.data.frameworks.dsgai import ingest_dsgai
nodes = ingest_dsgai(Path('data/frameworks/owasp-dsgai/OWASP-GenAI-Data-Security-Risks-and-Mitigations-2026-v1.0.md'))
Path('data/processed/frameworks/owasp_dsgai.json').write_text(json.dumps(nodes, indent=2))
print(f'wrote {len(nodes)} nodes')
"
```
Expected: `wrote 21 nodes`.

- [ ] **Step 8: Commit**

```bash
git add classifier/data/frameworks/__init__.py classifier/data/frameworks/dsgai.py classifier/tests/test_dsgai_ingester.py data/frameworks/owasp-dsgai/MANIFEST.json data/processed/frameworks/owasp_dsgai.json
git commit -m "plan1b: DSGAI corpus ingester (21 source nodes)"
```

---

## Task 5: Vendor upstream crosswalk repo as pinned read-only dependency

**Files:**
- Create: `third_party/genai-crosswalk/MANIFEST.json`
- Create: `third_party/genai-crosswalk/crosswalk/data/entries/*.json` (41 files copied from upstream)
- Create: `third_party/genai-crosswalk/crosswalk/data/schema.json`
- Create: `third_party/genai-crosswalk/LICENSE`

**Spec reference:** §4.1.

- [ ] **Step 1: Pick a pinned upstream commit**

```bash
git ls-remote https://github.com/GenAI-Security-Project/GenAI-Data-Security-Initiative HEAD
```
Record the commit SHA. Save to a shell variable for the next steps:
```bash
export UPSTREAM_SHA=<paste the SHA from above>
```

- [ ] **Step 2: Clone the upstream repo to a temp dir at the pinned SHA**

```bash
mkdir -p /tmp/upstream-pin
git clone --depth 1 https://github.com/GenAI-Security-Project/GenAI-Data-Security-Initiative /tmp/upstream-pin/repo
( cd /tmp/upstream-pin/repo && git checkout "$UPSTREAM_SHA" )
```

- [ ] **Step 3: Copy the snapshot into `third_party/`**

```bash
mkdir -p third_party/genai-crosswalk/crosswalk/data/entries
cp /tmp/upstream-pin/repo/crosswalk/data/entries/*.json third_party/genai-crosswalk/crosswalk/data/entries/
cp /tmp/upstream-pin/repo/crosswalk/data/schema.json third_party/genai-crosswalk/crosswalk/data/schema.json
cp /tmp/upstream-pin/repo/LICENSE third_party/genai-crosswalk/LICENSE
ls third_party/genai-crosswalk/crosswalk/data/entries/ | wc -l
```
Expected: `41`.

- [ ] **Step 4: Write the MANIFEST**

```bash
cat > third_party/genai-crosswalk/MANIFEST.json <<EOF
{
  "upstream_repo": "https://github.com/GenAI-Security-Project/GenAI-Data-Security-Initiative",
  "upstream_commit_sha": "$UPSTREAM_SHA",
  "retrieved_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "license": "CC-BY-SA-4.0",
  "attribution": "GenAI Security Project — GenAI Data Security Initiative crosswalk. Licensed under CC BY-SA 4.0.",
  "entry_count": 41,
  "entry_breakdown": {"LLM": 10, "ASI": 10, "DSGAI": 21}
}
EOF
```

- [ ] **Step 5: Verify the snapshot**

```bash
test -f third_party/genai-crosswalk/MANIFEST.json
test -f third_party/genai-crosswalk/LICENSE
test -f third_party/genai-crosswalk/crosswalk/data/schema.json
ls third_party/genai-crosswalk/crosswalk/data/entries/LLM01.json
ls third_party/genai-crosswalk/crosswalk/data/entries/ASI10.json
ls third_party/genai-crosswalk/crosswalk/data/entries/DSGAI21.json
```
All commands should succeed silently.

- [ ] **Step 6: Commit**

```bash
git add third_party/genai-crosswalk/
git commit -m "plan1b: vendor upstream crosswalk @ pinned SHA (read-only dep)"
```

---

## Task 6: Upstream loader — flatten entries into mappings + crossrefs

**Files:**
- Create: `classifier/data/upstream_loader.py`
- Create: `classifier/scripts/build_upstream.py`
- Create: `classifier/tests/test_upstream_loader.py`
- Output: `data/upstream/mappings_v1.jsonl`, `data/upstream/crossrefs_v1.jsonl`

**Spec reference:** §4.3.

- [ ] **Step 1: Write the loader test**

```python
# classifier/tests/test_upstream_loader.py
import json
from pathlib import Path
from classifier.data.upstream_loader import (
    SOURCE_LIST_TO_FRAMEWORK,
    flatten_entry,
    load_all_entries,
)

REPO = Path(__file__).resolve().parents[2]
ENTRIES = REPO / "third_party" / "genai-crosswalk" / "crosswalk" / "data" / "entries"


def test_source_list_normalization_table_is_exhaustive():
    expected = {"LLM-Top10-2025", "Agentic-Top10-2026", "DSGAI-2026"}
    assert expected.issubset(set(SOURCE_LIST_TO_FRAMEWORK.keys()))
    targets = set(SOURCE_LIST_TO_FRAMEWORK.values())
    assert targets == {"owasp_llm", "owasp_agentic", "owasp_dsgai"}


def test_flatten_entry_emits_one_row_per_mapping():
    raw = json.loads((ENTRIES / "LLM01.json").read_text())
    rows = flatten_entry(raw, upstream_commit_sha="deadbeef" * 5)
    assert len(rows) == len(raw["mappings"])
    first = rows[0]
    assert first["source_framework"] == "owasp_llm"
    assert first["source_id"] == "LLM01"
    assert first["source_list"] == "LLM-Top10-2025"
    assert "target_framework" in first
    assert "provenance_sha" in first and len(first["provenance_sha"]) == 64


def test_load_all_entries_covers_41():
    rows = load_all_entries(ENTRIES, upstream_commit_sha="deadbeef" * 5)
    source_ids = {r["source_id"] for r in rows}
    assert len(source_ids) == 41
    assert "LLM01" in source_ids and "ASI10" in source_ids and "DSGAI21" in source_ids
```

- [ ] **Step 2: Run — expect ImportError**

```bash
pytest classifier/tests/test_upstream_loader.py -v
```
Expected: FAIL.

- [ ] **Step 3: Implement the loader**

```python
# classifier/data/upstream_loader.py
"""Flatten upstream GenAI-Data-Security-Initiative crosswalk entries
into row-oriented mappings and crossrefs JSONL.

Spec: docs/superpowers/specs/2026-04-08-upstream-crosswalk-integration-design.md §4.3
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

SOURCE_LIST_TO_FRAMEWORK: dict[str, str] = {
    "LLM-Top10-2025": "owasp_llm",
    "Agentic-Top10-2026": "owasp_agentic",
    "DSGAI-2026": "owasp_dsgai",
}

# Target-framework normalization table. Keys are upstream's free-form
# `framework` string; values are our internal framework identifiers.
# Unknown targets get target_framework_unknown=True and are excluded
# from training (per spec §4.3).
TARGET_FRAMEWORK_TABLE: dict[str, str] = {
    "MITRE ATLAS": "mitre_atlas",
    "MITRE-ATLAS": "mitre_atlas",
    "NIST AI RMF 1.0": "nist_rmf",
    "NIST AI RMF": "nist_rmf",
    "NIST-AI-RMF": "nist_rmf",
    "AIUC-1": "aiuc_1",
    "CSA AICM": "csa_aicm",
    "CSA-AICM": "csa_aicm",
    "MAESTRO": "csa_aicm",  # CSA renamed AICM → MAESTRO in some refs
    "OWASP AI Exchange": "owasp_ai_exchange",
    "OWASP-AI-Exchange": "owasp_ai_exchange",
    "EU GPAI Code of Practice": "eu_gpai_cop",
    "CoSAI": "cosai_rm",
    "COSAI": "cosai_rm",
    "NIST SP 800-53": "nist_800_53",
    "NIST SP 800-53 Rev 5": "nist_800_53",
    "NIST-800-53": "nist_800_53",
    "EU AI Act": "eu_ai_act",
    "EU-AI-Act": "eu_ai_act",
}


def _provenance_sha(upstream_commit_sha: str, entry_id: str, mapping_index: int) -> str:
    h = hashlib.sha256()
    h.update(upstream_commit_sha.encode())
    h.update(b"|")
    h.update(entry_id.encode())
    h.update(b"|")
    h.update(str(mapping_index).encode())
    return h.hexdigest()


def flatten_entry(entry: dict, upstream_commit_sha: str) -> list[dict]:
    src_list = entry.get("source_list", "")
    src_framework = SOURCE_LIST_TO_FRAMEWORK.get(src_list)
    if src_framework is None:
        raise ValueError(
            f"unknown source_list {src_list!r} in entry {entry.get('id')}; "
            f"extend SOURCE_LIST_TO_FRAMEWORK"
        )
    src_id = entry["id"]

    rows: list[dict] = []
    for idx, m in enumerate(entry.get("mappings", [])):
        upstream_target = (m.get("framework") or "").strip()
        target_framework = TARGET_FRAMEWORK_TABLE.get(upstream_target)
        rows.append({
            "source_framework": src_framework,
            "source_id": src_id,
            "source_list": src_list,
            "target_framework": target_framework or upstream_target,
            "target_framework_unknown": target_framework is None,
            "target_control_id": m.get("control_id"),
            "target_control_name": m.get("control_name"),
            "tier": m.get("tier"),
            "scope": m.get("scope"),
            "url": m.get("url"),
            "notes": m.get("notes"),
            "provenance_sha": _provenance_sha(upstream_commit_sha, src_id, idx),
        })
    return rows


def flatten_crossrefs(entry: dict, upstream_commit_sha: str) -> list[dict]:
    src_list = entry.get("source_list", "")
    src_framework = SOURCE_LIST_TO_FRAMEWORK.get(src_list, "")
    src_id = entry["id"]
    cx = entry.get("crossrefs", {}) or {}
    out: list[dict] = []
    for target_list, target_ids in cx.items():
        # crossref keys look like "agentic_top10", "dsgai_2026", "llm_top10"
        target_framework = {
            "agentic_top10": "owasp_agentic",
            "llm_top10": "owasp_llm",
            "dsgai_2026": "owasp_dsgai",
        }.get(target_list, target_list)
        for idx, t_id in enumerate(target_ids or []):
            out.append({
                "source_framework": src_framework,
                "source_id": src_id,
                "target_framework": target_framework,
                "target_id": t_id,
                "provenance_sha": _provenance_sha(
                    upstream_commit_sha, f"{src_id}::xref::{target_list}", idx
                ),
            })
    return out


def load_all_entries(entries_dir: Path, upstream_commit_sha: str) -> list[dict]:
    rows: list[dict] = []
    for p in sorted(Path(entries_dir).glob("*.json")):
        entry = json.loads(p.read_text())
        rows.extend(flatten_entry(entry, upstream_commit_sha))
    return rows


def load_all_crossrefs(entries_dir: Path, upstream_commit_sha: str) -> list[dict]:
    rows: list[dict] = []
    for p in sorted(Path(entries_dir).glob("*.json")):
        entry = json.loads(p.read_text())
        rows.extend(flatten_crossrefs(entry, upstream_commit_sha))
    return rows
```

- [ ] **Step 4: Run — expect pass**

```bash
pytest classifier/tests/test_upstream_loader.py -v
```
Expected: 3 passed.

- [ ] **Step 5: Write the entry script**

```python
# classifier/scripts/build_upstream.py
"""Build data/upstream/{mappings_v1,crossrefs_v1}.jsonl from the pinned snapshot."""
from __future__ import annotations
import json
from pathlib import Path

from classifier.data.upstream_loader import load_all_entries, load_all_crossrefs

REPO = Path(__file__).resolve().parents[2]
THIRD = REPO / "third_party" / "genai-crosswalk"
OUT_DIR = REPO / "data" / "upstream"


def main() -> None:
    manifest = json.loads((THIRD / "MANIFEST.json").read_text())
    sha = manifest["upstream_commit_sha"]
    entries_dir = THIRD / "crosswalk" / "data" / "entries"

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    mappings = load_all_entries(entries_dir, sha)
    with (OUT_DIR / "mappings_v1.jsonl").open("w") as f:
        for r in mappings:
            f.write(json.dumps(r) + "\n")

    crossrefs = load_all_crossrefs(entries_dir, sha)
    with (OUT_DIR / "crossrefs_v1.jsonl").open("w") as f:
        for r in crossrefs:
            f.write(json.dumps(r) + "\n")

    unknown_targets = sorted({r["target_framework"] for r in mappings if r["target_framework_unknown"]})
    print(f"[upstream] mappings={len(mappings)} crossrefs={len(crossrefs)}")
    print(f"[upstream] unknown target frameworks ({len(unknown_targets)}): {unknown_targets}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 6: Run the build**

```bash
python -m classifier.scripts.build_upstream
wc -l data/upstream/mappings_v1.jsonl data/upstream/crossrefs_v1.jsonl
```
Expected: ~1500-2000 lines in mappings_v1.jsonl, ~50-200 in crossrefs_v1.jsonl. Note the printed "unknown target frameworks" list — these are upstream targets we don't yet have a normalization for; they're flagged but not blocking.

- [ ] **Step 7: Commit**

```bash
git add classifier/data/upstream_loader.py classifier/scripts/build_upstream.py classifier/tests/test_upstream_loader.py data/upstream/mappings_v1.jsonl data/upstream/crossrefs_v1.jsonl
git commit -m "plan1b: upstream loader (mappings + crossrefs flattened)"
```

---

## Task 7: Contamination auditor — strict source-id-level partition

**Files:**
- Create: `classifier/data/contamination.py`
- Create: `classifier/scripts/run_contamination_audit.py`
- Output: `data/upstream/partition.json`, `data/upstream/contamination_report.json`

**Spec reference:** §4.4. Comparisons MUST use the `(source_framework, source_id)` 2-tuple — never bare `source_id` — to prevent cross-source-list ID collisions from silently defeating the rule.

- [ ] **Step 1: Implement the auditor**

```python
# classifier/data/contamination.py
"""Strict source-id-level contamination partition for upstream labels.

Spec: docs/superpowers/specs/2026-04-08-upstream-crosswalk-integration-design.md §4.4

Partition rules (strict):
  Rule 1: If a (source_framework, source_id) tuple appears anywhere in the
          frozen test, ALL upstream rows with that tuple are held_out.
  Rule 2: Additionally, any upstream row whose full
          (source_framework, source_id, target_framework, target_id) 4-tuple
          exactly matches a frozen-test row is held_out regardless of Rule 1.
"""
from __future__ import annotations
import json
from pathlib import Path

import pandas as pd


def compute_partition(
    frozen_test_path: Path,
    upstream_mappings_path: Path,
) -> dict:
    frozen = pd.read_json(frozen_test_path, lines=True)

    # Frozen test row schema (from Plan 1):
    #   framework_pair, source_node_id, target_node_id, ...
    # source_node_id format: "<framework>:<local_id>", e.g. "owasp_llm:LLM01"
    def split_node_id(nid: str) -> tuple[str, str]:
        if ":" in nid:
            fw, local = nid.split(":", 1)
            return fw, local
        return "", nid

    frozen_src_tuples: set[tuple[str, str]] = set()
    frozen_full_tuples: set[tuple[str, str, str, str]] = set()
    for _, row in frozen.iterrows():
        src_fw, src_id = split_node_id(row["source_node_id"])
        tgt_fw, tgt_id = split_node_id(row["target_node_id"])
        frozen_src_tuples.add((src_fw, src_id))
        frozen_full_tuples.add((src_fw, src_id, tgt_fw, tgt_id))

    upstream_rows: list[dict] = []
    with open(upstream_mappings_path) as f:
        for line in f:
            upstream_rows.append(json.loads(line))

    held_out: list[str] = []
    train_eligible: list[str] = []
    rule1_hits = 0
    rule2_hits = 0

    for r in upstream_rows:
        src_tuple = (r["source_framework"], r["source_id"])
        full_tuple = (
            r["source_framework"],
            r["source_id"],
            r["target_framework"],
            r.get("target_control_id") or "",
        )
        rule1 = src_tuple in frozen_src_tuples
        rule2 = full_tuple in frozen_full_tuples
        if rule1:
            rule1_hits += 1
        if rule2:
            rule2_hits += 1
        if rule1 or rule2:
            held_out.append(r["provenance_sha"])
        else:
            train_eligible.append(r["provenance_sha"])

    return {
        "upstream_total": len(upstream_rows),
        "train_eligible_count": len(train_eligible),
        "held_out_count": len(held_out),
        "rule1_hits": rule1_hits,
        "rule2_hits": rule2_hits,
        "frozen_src_tuples_count": len(frozen_src_tuples),
        "frozen_full_tuples_count": len(frozen_full_tuples),
        "train_eligible": train_eligible,
        "held_out": held_out,
    }


def write_partition_and_report(
    partition: dict,
    partition_path: Path,
    report_path: Path,
) -> None:
    partition_path.write_text(json.dumps(partition, indent=2))

    summary = {k: v for k, v in partition.items() if k not in ("train_eligible", "held_out")}
    summary["held_out_pct"] = (
        partition["held_out_count"] / partition["upstream_total"] if partition["upstream_total"] else 0.0
    )
    summary["projection"] = (
        "Strict partitioning per spec §4.4. Held-out rows are reserved for the "
        "upstream benchmark (spec §6) and MUST NOT enter training batches."
    )
    report_path.write_text(json.dumps(summary, indent=2))
```

- [ ] **Step 2: Write the entry script**

```python
# classifier/scripts/run_contamination_audit.py
from __future__ import annotations
from pathlib import Path
from classifier.data.contamination import compute_partition, write_partition_and_report

REPO = Path(__file__).resolve().parents[2]
FROZEN = REPO / "data" / "splits" / "human_test_frozen.jsonl"
UPSTREAM = REPO / "data" / "upstream" / "mappings_v1.jsonl"
PARTITION = REPO / "data" / "upstream" / "partition.json"
REPORT = REPO / "data" / "upstream" / "contamination_report.json"


def main() -> None:
    partition = compute_partition(FROZEN, UPSTREAM)
    write_partition_and_report(partition, PARTITION, REPORT)
    print(f"upstream_total={partition['upstream_total']}")
    print(f"train_eligible={partition['train_eligible_count']}")
    print(f"held_out={partition['held_out_count']} (rule1={partition['rule1_hits']} rule2={partition['rule2_hits']})")


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Run the audit**

```bash
python -m classifier.scripts.run_contamination_audit
cat data/upstream/contamination_report.json
```
Expected: prints counts, writes both files. The held_out_count should be > 0 (because LLM01..10 and ASI01..10 are in our frozen test).

- [ ] **Step 4: Commit**

```bash
git add classifier/data/contamination.py classifier/scripts/run_contamination_audit.py data/upstream/partition.json data/upstream/contamination_report.json
git commit -m "plan1b: contamination auditor + strict partition"
```

---

## Task 8: Contamination CI gate test (pre-registered, non-skippable honesty firewall)

**Files:**
- Create: `classifier/tests/test_contamination.py`

**Spec reference:** §4.4 final paragraph. This test is pre-registered and MUST NOT be skipped, xfailed, or disabled.

- [ ] **Step 1: Write the test**

```python
# classifier/tests/test_contamination.py
"""Pre-registered honesty firewall.

DO NOT skip, xfail, or disable any assertion in this file. The orchestrator's
"never disable a failing test" rule applies here with the tightest possible
interpretation. If this test fails, the partition is broken — fix the partition,
not the test.
"""
import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
PARTITION = REPO / "data" / "upstream" / "partition.json"
UPSTREAM = REPO / "data" / "upstream" / "mappings_v1.jsonl"
FROZEN = REPO / "data" / "splits" / "human_test_frozen.jsonl"


def _load_partition() -> dict:
    assert PARTITION.exists(), (
        "data/upstream/partition.json missing — run "
        "classifier/scripts/run_contamination_audit.py before running this test"
    )
    return json.loads(PARTITION.read_text())


def test_partition_disjoint():
    p = _load_partition()
    eligible = set(p["train_eligible"])
    held = set(p["held_out"])
    assert eligible.isdisjoint(held), "train_eligible and held_out overlap — partition is broken"
    assert len(eligible) + len(held) == p["upstream_total"], "partition does not cover all rows"


def test_held_out_provenance_shas_never_appear_in_training_loader():
    """Runtime defense: any future training-batch loader is required to honor
    `held_out` from partition.json. This test asserts the data file is well-formed
    and that the held_out set is non-empty whenever the upstream snapshot includes
    source_ids that are in the frozen test.
    """
    p = _load_partition()
    # Sanity: if upstream contains LLM01..10 or ASI01..10, held_out must be non-empty
    # because our frozen test includes those source frameworks.
    upstream_src_ids = set()
    with open(UPSTREAM) as f:
        for line in f:
            r = json.loads(line)
            upstream_src_ids.add((r["source_framework"], r["source_id"]))
    if any(fw in ("owasp_llm", "owasp_agentic") for fw, _ in upstream_src_ids):
        assert p["held_out_count"] > 0, (
            "upstream contains LLM/Agentic source_ids that are in the frozen test, "
            "but held_out_count is 0 — the partition is silently broken"
        )


def test_no_held_out_row_matches_a_train_eligible_full_tuple():
    """Cross-check Rule 2: no held-out row should share a full
    (src_fw, src_id, tgt_fw, tgt_ctrl_id) tuple with any train-eligible row.
    """
    p = _load_partition()
    held = set(p["held_out"])
    eligible = set(p["train_eligible"])

    by_sha: dict[str, dict] = {}
    with open(UPSTREAM) as f:
        for line in f:
            r = json.loads(line)
            by_sha[r["provenance_sha"]] = r

    held_full = {
        (r["source_framework"], r["source_id"], r["target_framework"], r.get("target_control_id") or "")
        for sha, r in by_sha.items() if sha in held
    }
    elig_full = {
        (r["source_framework"], r["source_id"], r["target_framework"], r.get("target_control_id") or "")
        for sha, r in by_sha.items() if sha in eligible
    }
    overlap = held_full & elig_full
    assert not overlap, f"full-tuple collision between held_out and train_eligible: {list(overlap)[:5]}"
```

- [ ] **Step 2: Run — expect pass**

```bash
pytest classifier/tests/test_contamination.py -v
```
Expected: 3 passed.

- [ ] **Step 3: Verify the test cannot be silently skipped**

```bash
grep -n "skip\|xfail" classifier/tests/test_contamination.py
```
Expected: NO matches (the docstring text doesn't count, only decorators).

- [ ] **Step 4: Commit**

```bash
git add classifier/tests/test_contamination.py
git commit -m "plan1b: contamination CI gate (pre-registered honesty firewall)"
```

---

## Task 9: THIRD_PARTY_NOTICES.md + extend hashes.json

**Files:**
- Create: `THIRD_PARTY_NOTICES.md`
- Modify: `data/splits/hashes.json` (add upstream + new-framework manifest hashes)

- [ ] **Step 1: Write THIRD_PARTY_NOTICES.md**

```bash
cat > THIRD_PARTY_NOTICES.md <<'EOF'
# Third-Party Notices

This project incorporates the following third-party content. Each is used
under its own license; see individual entries for terms.

## OWASP GenAI Data Security Risks and Mitigations 2026 (v1.0)

- **Source:** https://genai.owasp.org/
- **File:** `data/frameworks/owasp-dsgai/OWASP-GenAI-Data-Security-Risks-and-Mitigations-2026-v1.0.md`
- **License:** Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)
- **Attribution:** © OWASP GenAI Data Security Project. Licensed under CC BY-SA 4.0.
- **Modifications:** None to the source PDF/markdown text. Derived node-list
  files under `data/processed/frameworks/owasp_dsgai.json` are extractions
  and remain CC BY-SA 4.0.

## GenAI Security Project — GenAI Data Security Initiative crosswalk

- **Source:** https://github.com/GenAI-Security-Project/GenAI-Data-Security-Initiative
- **Pinned at:** see `third_party/genai-crosswalk/MANIFEST.json` (`upstream_commit_sha`)
- **Files:** `third_party/genai-crosswalk/crosswalk/data/entries/*.json`,
  `third_party/genai-crosswalk/crosswalk/data/schema.json`,
  `third_party/genai-crosswalk/LICENSE`
- **License:** Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)
- **Attribution:** © GenAI Security Project. Licensed under CC BY-SA 4.0.
- **Modifications:** None. Files are vendored verbatim. Derived flattened
  files under `data/upstream/` are transformations and remain CC BY-SA 4.0.

## Derived data files inheriting CC BY-SA 4.0

The following files are derived from the above sources and are distributed
under CC BY-SA 4.0:

- `data/upstream/mappings_v1.jsonl`
- `data/upstream/crossrefs_v1.jsonl`
- `data/upstream/partition.json`
- `data/upstream/contamination_report.json`
- `data/processed/frameworks/owasp_dsgai.json`
EOF
```

- [ ] **Step 2: Compute and append hashes**

```python
python <<'PY'
import hashlib, json
from pathlib import Path

REPO = Path(".")
HASHES = REPO / "data/splits/hashes.json"
FILES = [
    "third_party/genai-crosswalk/MANIFEST.json",
    "data/frameworks/owasp-dsgai/MANIFEST.json",
    "data/upstream/mappings_v1.jsonl",
    "data/upstream/crossrefs_v1.jsonl",
    "data/upstream/partition.json",
    "data/processed/frameworks/owasp_dsgai.json",
    "THIRD_PARTY_NOTICES.md",
]

current = json.loads(HASHES.read_text())
upstream_section = {}
for rel in FILES:
    p = REPO / rel
    if not p.exists():
        raise SystemExit(f"missing {rel}")
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    upstream_section[rel] = h
current["upstream_v1"] = upstream_section
HASHES.write_text(json.dumps(current, indent=2, sort_keys=True))
print("appended upstream_v1 section to hashes.json")
PY
```

- [ ] **Step 3: Verify hashes.json structure**

```bash
python -c "import json; d = json.load(open('data/splits/hashes.json')); assert 'upstream_v1' in d; print(list(d.keys()))"
```
Expected: prints the top-level keys including `upstream_v1`. Existing top-level keys (e.g. for the frozen split hashes) MUST still be present — verify by eye.

- [ ] **Step 4: Commit**

```bash
git add THIRD_PARTY_NOTICES.md data/splits/hashes.json
git commit -m "plan1b: third-party notices + extend hashes.json with upstream section"
```

---

## Task 10: NIST SP 800-53 rev5 ingester (new target framework)

**Files:**
- Create: `data/frameworks/nist-800-53/MANIFEST.json`
- Create: `data/frameworks/nist-800-53/<oscal_catalog_filename>.json` (downloaded by implementer)
- Create: `classifier/data/frameworks/nist_800_53.py`
- Create: `classifier/tests/test_nist_800_53_ingester.py`
- Output: `data/processed/frameworks/nist_800_53.json`

**Source:** NIST OSCAL JSON catalog of SP 800-53 rev5 (US Government, public domain). Canonical location:
`https://csrc.nist.gov/CSRC/media/Publications/sp/800-53/rev-5/final/sp800-53r5-control-catalog.json` (verify the URL is current; NIST OSCAL distribution may have moved to GitHub at `usnistgov/oscal-content`).

- [ ] **Step 1: Download the OSCAL catalog**

```bash
mkdir -p data/frameworks/nist-800-53
curl -L -o data/frameworks/nist-800-53/NIST_SP-800-53_rev5_catalog.json \
  "https://raw.githubusercontent.com/usnistgov/oscal-content/main/nist.gov/SP800-53/rev5/json/NIST_SP-800-53_rev5_catalog.json"
ls -lh data/frameworks/nist-800-53/NIST_SP-800-53_rev5_catalog.json
```
Expected: a multi-MB JSON file. If the URL 404s, check `https://github.com/usnistgov/oscal-content/tree/main/nist.gov/SP800-53/rev5/json` for the current filename and adjust.

- [ ] **Step 2: Write the MANIFEST**

```bash
cat > data/frameworks/nist-800-53/MANIFEST.json <<'EOF'
{
  "framework_id": "nist_800_53",
  "framework_name": "NIST SP 800-53 Rev 5 — Security and Privacy Controls",
  "version": "rev5",
  "release_date": "2020-09",
  "source_file": "NIST_SP-800-53_rev5_catalog.json",
  "source_url": "https://github.com/usnistgov/oscal-content/tree/main/nist.gov/SP800-53/rev5/json",
  "license": "Public Domain (US Government work, 17 USC § 105)",
  "attribution": "NIST Special Publication 800-53 Rev. 5. Public domain.",
  "format": "OSCAL JSON catalog",
  "expected_min_node_count": 300
}
EOF
```

- [ ] **Step 3: Write the failing test**

```python
# classifier/tests/test_nist_800_53_ingester.py
from pathlib import Path
from classifier.data.frameworks.nist_800_53 import ingest_nist_800_53

REPO = Path(__file__).resolve().parents[2]
CATALOG = REPO / "data" / "frameworks" / "nist-800-53" / "NIST_SP-800-53_rev5_catalog.json"


def test_ingest_returns_at_least_300_controls():
    nodes = ingest_nist_800_53(CATALOG)
    assert len(nodes) >= 300, f"expected >=300 controls, got {len(nodes)}"


def test_ingest_node_shape():
    nodes = ingest_nist_800_53(CATALOG)
    n = nodes[0]
    assert n["framework"] == "nist_800_53"
    assert n["node_id"].startswith("nist_800_53:")
    assert n["local_id"]
    assert n["title"]
    assert len(n["text"]) > 30
```

- [ ] **Step 4: Run — expect ImportError**

```bash
pytest classifier/tests/test_nist_800_53_ingester.py -v
```

- [ ] **Step 5: Implement the ingester**

```python
# classifier/data/frameworks/nist_800_53.py
"""NIST SP 800-53 rev5 OSCAL JSON catalog → node list ingester.

OSCAL structure (simplified):
  catalog
    groups[]
      groups[]              (optional sub-groups)
      controls[]
        id          e.g. "ac-1"
        title       e.g. "Policy and Procedures"
        params[]    parameter definitions
        parts[]     prose statements (statement, guidance, ...)
        controls[]  enhancements (optional)

We emit one node per control AND one node per enhancement.
"""
from __future__ import annotations
import json
from pathlib import Path


def _extract_text(parts: list[dict]) -> str:
    chunks: list[str] = []
    for part in parts or []:
        if "prose" in part and part["prose"]:
            chunks.append(part["prose"])
        if "parts" in part:
            chunks.append(_extract_text(part["parts"]))
    return "\n".join(c for c in chunks if c).strip()


def _walk(group: dict, out: list[dict]) -> None:
    for ctrl in group.get("controls", []) or []:
        _emit(ctrl, out)
    for sub in group.get("groups", []) or []:
        _walk(sub, out)


def _emit(ctrl: dict, out: list[dict]) -> None:
    local_id = ctrl["id"].upper()  # "ac-1" → "AC-1"
    title = ctrl.get("title", "")
    text = _extract_text(ctrl.get("parts", []))
    out.append({
        "node_id": f"nist_800_53:{local_id}",
        "local_id": local_id,
        "framework": "nist_800_53",
        "title": title,
        "text": text or title,
    })
    for enh in ctrl.get("controls", []) or []:
        _emit(enh, out)


def ingest_nist_800_53(catalog_path: Path) -> list[dict]:
    raw = json.loads(Path(catalog_path).read_text())
    catalog = raw.get("catalog", raw)
    out: list[dict] = []
    for group in catalog.get("groups", []) or []:
        _walk(group, out)
    return out
```

- [ ] **Step 6: Run — expect pass**

```bash
pytest classifier/tests/test_nist_800_53_ingester.py -v
```

- [ ] **Step 7: Run the ingester and write the per-framework JSON**

```bash
python -c "
import json
from pathlib import Path
from classifier.data.frameworks.nist_800_53 import ingest_nist_800_53
nodes = ingest_nist_800_53(Path('data/frameworks/nist-800-53/NIST_SP-800-53_rev5_catalog.json'))
Path('data/processed/frameworks/nist_800_53.json').write_text(json.dumps(nodes, indent=2))
print(f'wrote {len(nodes)} nodes')
"
```
Expected: ~1000 nodes (rev5 has ~287 base controls and ~700 enhancements).

- [ ] **Step 8: Commit**

```bash
git add data/frameworks/nist-800-53/ classifier/data/frameworks/nist_800_53.py classifier/tests/test_nist_800_53_ingester.py data/processed/frameworks/nist_800_53.json
git commit -m "plan1b: NIST SP 800-53 rev5 ingester (~1000 nodes)"
```

---

## Task 11: EU AI Act ingester (new target framework)

**Files:**
- Create: `data/frameworks/eu-ai-act/MANIFEST.json`
- Create: `data/frameworks/eu-ai-act/eu_ai_act_text.html` (or `.txt`, downloaded by implementer)
- Create: `classifier/data/frameworks/eu_ai_act.py`
- Create: `classifier/tests/test_eu_ai_act_ingester.py`
- Output: `data/processed/frameworks/eu_ai_act.json`

**Source:** EUR-Lex Regulation (EU) 2024/1689 (the AI Act). The plain HTML version is at `https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1689`. License: reuse permitted with attribution under Commission Decision 2011/833/EU.

- [ ] **Step 1: Download the EU AI Act text**

The EUR-Lex HTML version has stable article anchors. Download as HTML:

```bash
mkdir -p data/frameworks/eu-ai-act
curl -L -A "Mozilla/5.0" -o data/frameworks/eu-ai-act/eu_ai_act_2024_1689.html \
  "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32024R1689"
ls -lh data/frameworks/eu-ai-act/eu_ai_act_2024_1689.html
```
Expected: a multi-MB HTML file. If EUR-Lex blocks the curl, the implementer downloads it via a browser and drops it at the same path.

- [ ] **Step 2: Write the MANIFEST**

```bash
cat > data/frameworks/eu-ai-act/MANIFEST.json <<'EOF'
{
  "framework_id": "eu_ai_act",
  "framework_name": "EU AI Act — Regulation (EU) 2024/1689",
  "version": "2024/1689",
  "release_date": "2024-07-12",
  "source_file": "eu_ai_act_2024_1689.html",
  "source_url": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1689",
  "license": "Commission Decision 2011/833/EU (reuse permitted with attribution)",
  "attribution": "© European Union, 1998-2026. Reuse permitted with attribution per Commission Decision 2011/833/EU.",
  "format": "HTML (EUR-Lex)",
  "expected_min_node_count": 100
}
EOF
```

- [ ] **Step 3: Write the failing test**

```python
# classifier/tests/test_eu_ai_act_ingester.py
from pathlib import Path
from classifier.data.frameworks.eu_ai_act import ingest_eu_ai_act

REPO = Path(__file__).resolve().parents[2]
HTML = REPO / "data" / "frameworks" / "eu-ai-act" / "eu_ai_act_2024_1689.html"


def test_ingest_returns_articles():
    nodes = ingest_eu_ai_act(HTML)
    assert len(nodes) >= 100, f"expected >=100 article nodes, got {len(nodes)}"
    assert all(n["framework"] == "eu_ai_act" for n in nodes)
    assert any("Article 1" in n["title"] for n in nodes)
```

- [ ] **Step 4: Run — expect failure**

```bash
pytest classifier/tests/test_eu_ai_act_ingester.py -v
```

- [ ] **Step 5: Implement the ingester**

The EUR-Lex HTML uses a stable structure: article headings appear in `<p class="ti-art">` (article number) followed by a `<p class="sti-art">` (article title), with body in subsequent `<p class="normal">` paragraphs. The exact class names may vary; the implementer SHOULD inspect the file before finalizing the parser.

```python
# classifier/data/frameworks/eu_ai_act.py
"""EU AI Act (Regulation 2024/1689) HTML → article-level node list ingester.

Source: EUR-Lex CELEX 32024R1689. Articles are the natural granularity.
Parser strategy:
  1. Use BeautifulSoup to walk the document
  2. For each <p> with class containing "ti-art", treat it as an article
     boundary; the next sibling with class "sti-art" is the title; everything
     until the next "ti-art" or end-of-document is the body.
  3. The class names on EUR-Lex pages are stable but the implementer should
     verify with `grep "ti-art" data/frameworks/eu-ai-act/eu_ai_act_2024_1689.html`
     before running the test.
"""
from __future__ import annotations
import re
from pathlib import Path

from bs4 import BeautifulSoup

ARTICLE_NUM_RE = re.compile(r"Article\s+(\d+[a-z]?)", re.IGNORECASE)


def ingest_eu_ai_act(html_path: Path) -> list[dict]:
    soup = BeautifulSoup(Path(html_path).read_text(encoding="utf-8"), "html.parser")
    paragraphs = soup.find_all("p")

    nodes: list[dict] = []
    current_num: str | None = None
    current_title_parts: list[str] = []
    current_body: list[str] = []

    def flush() -> None:
        nonlocal current_num, current_title_parts, current_body
        if current_num:
            title = " ".join(current_title_parts).strip() or f"Article {current_num}"
            body = "\n".join(current_body).strip()
            nodes.append({
                "node_id": f"eu_ai_act:Art{current_num}",
                "local_id": f"Art{current_num}",
                "framework": "eu_ai_act",
                "title": f"Article {current_num} — {title}" if title else f"Article {current_num}",
                "text": body or title,
            })
        current_num = None
        current_title_parts = []
        current_body = []

    for p in paragraphs:
        cls = " ".join(p.get("class", []))
        text = p.get_text(" ", strip=True)
        if "ti-art" in cls:
            flush()
            m = ARTICLE_NUM_RE.search(text)
            if m:
                current_num = m.group(1)
        elif "sti-art" in cls and current_num:
            current_title_parts.append(text)
        elif current_num and text:
            current_body.append(text)
    flush()
    return nodes
```

- [ ] **Step 6: Run — expect pass (after possibly tweaking class names)**

```bash
pytest classifier/tests/test_eu_ai_act_ingester.py -v
```

If the test fails on class names, run:
```bash
grep -oE 'class="[^"]*ti-art[^"]*"' data/frameworks/eu-ai-act/eu_ai_act_2024_1689.html | sort -u | head
```
and adjust the parser's class detection.

- [ ] **Step 7: Run the ingester**

```bash
python -c "
import json
from pathlib import Path
from classifier.data.frameworks.eu_ai_act import ingest_eu_ai_act
nodes = ingest_eu_ai_act(Path('data/frameworks/eu-ai-act/eu_ai_act_2024_1689.html'))
Path('data/processed/frameworks/eu_ai_act.json').write_text(json.dumps(nodes, indent=2))
print(f'wrote {len(nodes)} article nodes')
"
```
Expected: ~110 nodes (the AI Act has 113 articles).

- [ ] **Step 8: Commit**

```bash
git add data/frameworks/eu-ai-act/ classifier/data/frameworks/eu_ai_act.py classifier/tests/test_eu_ai_act_ingester.py data/processed/frameworks/eu_ai_act.json
git commit -m "plan1b: EU AI Act ingester (~110 article nodes)"
```

---


## Task 13: Update FRAMEWORKS and FRAMEWORK_PAIRS to Tier-B matrix + merge nodes.json

**Files:**
- Modify: `classifier/data/candidates.py` (replace `FRAMEWORKS` and `FRAMEWORK_PAIRS` constants)
- Create: `classifier/data/frameworks/merge_nodes.py`
- Create: `classifier/tests/test_merge_nodes.py`
- Modify: `data/processed/nodes.json` (rebuild)
- Create: `data/processed/nodes.json.bak.20260408` (backup of pre-merge file)

**Spec reference:** §5.

- [ ] **Step 1: Backup existing nodes.json**

```bash
cp data/processed/nodes.json data/processed/nodes.json.bak.20260408
ls -lh data/processed/nodes.json.bak.20260408
```

- [ ] **Step 2: Write the merge script test**

```python
# classifier/tests/test_merge_nodes.py
import json
from pathlib import Path
from classifier.data.frameworks.merge_nodes import merge_into_nodes_json

REPO = Path(__file__).resolve().parents[2]


def test_merge_preserves_existing_frameworks(tmp_path):
    base = [
        {"node_id": "owasp_llm:LLM01", "framework": "owasp_llm", "title": "x", "text": "x"},
        {"node_id": "aiuc_1:CTL-1", "framework": "aiuc_1", "title": "y", "text": "y"},
    ]
    new1 = [{"node_id": "owasp_dsgai:DSGAI01", "framework": "owasp_dsgai", "title": "z", "text": "z"}]
    new2 = [{"node_id": "eu_ai_act:Art1", "framework": "eu_ai_act", "title": "a", "text": "a"}]

    base_path = tmp_path / "nodes.json"
    base_path.write_text(json.dumps(base))

    new_dir = tmp_path / "frameworks"
    new_dir.mkdir()
    (new_dir / "owasp_dsgai.json").write_text(json.dumps(new1))
    (new_dir / "eu_ai_act.json").write_text(json.dumps(new2))

    result = merge_into_nodes_json(base_path, new_dir)
    merged = json.loads(base_path.read_text())
    assert len(merged) == 4
    fws = {n["framework"] for n in merged}
    assert {"owasp_llm", "aiuc_1", "owasp_dsgai", "eu_ai_act"} == fws
    assert result["added"] == 2 and result["base"] == 2 and result["total"] == 4


def test_merge_does_not_duplicate_on_re_run(tmp_path):
    base = [{"node_id": "owasp_dsgai:DSGAI01", "framework": "owasp_dsgai", "title": "x", "text": "x"}]
    new = [{"node_id": "owasp_dsgai:DSGAI01", "framework": "owasp_dsgai", "title": "x", "text": "x"}]
    base_path = tmp_path / "nodes.json"
    base_path.write_text(json.dumps(base))
    new_dir = tmp_path / "frameworks"
    new_dir.mkdir()
    (new_dir / "owasp_dsgai.json").write_text(json.dumps(new))
    merge_into_nodes_json(base_path, new_dir)
    merged = json.loads(base_path.read_text())
    assert len(merged) == 1
```

- [ ] **Step 3: Run — expect ImportError**

```bash
pytest classifier/tests/test_merge_nodes.py -v
```

- [ ] **Step 4: Implement the merge script**

```python
# classifier/data/frameworks/merge_nodes.py
"""Merge per-framework node JSON files into data/processed/nodes.json.

Idempotent: dedup by node_id. Preserves existing nodes for frameworks
not in the per-framework directory (i.e. the original 9 frameworks built
by Sessions 1-8).
"""
from __future__ import annotations
import json
from pathlib import Path


def merge_into_nodes_json(nodes_path: Path, frameworks_dir: Path) -> dict:
    raw = json.loads(Path(nodes_path).read_text())
    base = raw if isinstance(raw, list) else raw.get("nodes", list(raw.values()))
    by_id: dict[str, dict] = {n["node_id"]: n for n in base}
    base_count = len(by_id)

    added = 0
    for p in sorted(Path(frameworks_dir).glob("*.json")):
        for n in json.loads(p.read_text()):
            nid = n["node_id"]
            if nid not in by_id:
                by_id[nid] = n
                added += 1

    merged = list(by_id.values())
    Path(nodes_path).write_text(json.dumps(merged, indent=2))
    return {"base": base_count, "added": added, "total": len(merged)}
```

- [ ] **Step 5: Run — expect pass**

```bash
pytest classifier/tests/test_merge_nodes.py -v
```

- [ ] **Step 6: Merge real per-framework files into nodes.json**

```bash
python -c "
from pathlib import Path
from classifier.data.frameworks.merge_nodes import merge_into_nodes_json
result = merge_into_nodes_json(
    Path('data/processed/nodes.json'),
    Path('data/processed/frameworks'),
)
print(result)
"
```
Expected: prints `{'base': <original count>, 'added': <≈1100-1200>, 'total': <sum>}`. The added count comes from DSGAI (21) + NIST 800-53 (~1000) + EU AI Act (~110) ≈ ~1130.

- [ ] **Step 7: Update FRAMEWORKS and FRAMEWORK_PAIRS in candidates.py**

Replace the `FRAMEWORKS` and `FRAMEWORK_PAIRS` constants in `classifier/data/candidates.py` with:

```python
FRAMEWORKS: list[str] = [
    # Existing 9
    "aiuc_1", "csa_aicm", "mitre_atlas", "nist_rmf",
    "owasp_llm", "owasp_agentic", "owasp_ai_exchange",
    "eu_gpai_cop", "cosai_rm",
    # New (Plan 1-B Tier B)
    "owasp_dsgai", "nist_800_53", "eu_ai_act",
]

FRAMEWORK_PAIRS: list[tuple[str, str]] = [
    # Original 12 (preserved for continuity with frozen test)
    ("aiuc_1",             "owasp_agentic"),    # 1
    ("aiuc_1",             "owasp_llm"),        # 2
    ("csa_aicm",           "owasp_agentic"),    # 3
    ("csa_aicm",           "mitre_atlas"),      # 4
    ("mitre_atlas",        "owasp_llm"),        # 5
    ("nist_rmf",           "owasp_agentic"),    # 6
    ("nist_rmf",           "eu_gpai_cop"),      # 7
    ("owasp_ai_exchange",  "owasp_llm"),        # 8
    ("eu_gpai_cop",        "owasp_ai_exchange"),# 9
    ("cosai_rm",           "mitre_atlas"),      # 10
    ("cosai_rm",           "owasp_agentic"),    # 11
    ("aiuc_1",             "nist_rmf"),         # 12
    # DSGAI as source against existing targets
    ("owasp_dsgai",        "aiuc_1"),           # 13
    ("owasp_dsgai",        "csa_aicm"),         # 14
    ("owasp_dsgai",        "nist_rmf"),         # 15
    ("owasp_dsgai",        "mitre_atlas"),      # 16
    # New targets against existing sources
    ("owasp_llm",          "nist_800_53"),      # 17
    ("owasp_agentic",      "nist_800_53"),      # 18
    ("owasp_dsgai",        "nist_800_53"),      # 19
    ("owasp_llm",          "eu_ai_act"),        # 20
    ("owasp_agentic",      "eu_ai_act"),        # 21
    ("owasp_dsgai",        "eu_ai_act"),        # 22
]
assert len(FRAMEWORK_PAIRS) == 22
# Coverage check: every framework appears in >=2 pairs
from collections import Counter
_counts = Counter(fw for pair in FRAMEWORK_PAIRS for fw in pair)
assert all(c >= 2 for c in _counts.values()), f"coverage violation: {_counts}"
```

- [ ] **Step 8: Run candidates test against the new matrix**

```bash
pytest classifier/tests/test_candidates.py -v
```
Expected: existing tests still pass (the test_build_candidate_pool_one_pair test uses an `aiuc_1` / `owasp_agentic` pair which is still valid).

- [ ] **Step 9: Commit**

```bash
git add classifier/data/candidates.py classifier/data/frameworks/merge_nodes.py classifier/tests/test_merge_nodes.py data/processed/nodes.json data/processed/nodes.json.bak.20260408
git commit -m "plan1b: Tier-B framework matrix (13 frameworks, 25 pairs) + nodes.json merge"
```

---

## Task 14: Build candidate pool + retrieval floor on Tier-B matrix (final artifacts)

**Files:**
- Output: `data/candidates/pool_v1.jsonl`
- Output: `data/candidates/retrieval_floor_report.json`

This is the actual run of Tasks 2 and 3's scripts against the Tier-B matrix.

- [ ] **Step 1: Build the candidate pool**

```bash
python -m classifier.scripts.build_candidates
```
Expected runtime: 15-40 minutes on Jetson CPU (was 5-20 min for 12 pairs; now 25 pairs with ~2x more nodes per pair on average). Output: `data/candidates/pool_v1.jsonl`.

- [ ] **Step 2: Verify pool shape**

```bash
wc -l data/candidates/pool_v1.jsonl
python -c "
import json, collections
pairs = collections.Counter()
with open('data/candidates/pool_v1.jsonl') as f:
    for line in f:
        pairs[json.loads(line)['framework_pair']] += 1
print(f'distinct pairs: {len(pairs)}')
for p, c in sorted(pairs.items()):
    print(f'  {p}: {c} source rows')
"
```
Expected: 25 distinct framework_pair keys, each with at least one source row. Total lines should be ~1500-2500.

- [ ] **Step 3: Run retrieval floor against frozen test**

```bash
python -m classifier.scripts.run_retrieval_floor
cat data/candidates/retrieval_floor_report.json
```
Expected: `frozen_total: 400`, `coverage_at_20` ideally ≥ 0.95, `coverage_at_k_used` should reach 1.0 by k_used ≤ 50. Note the actual coverage values for the commit message.

- [ ] **Step 4: Run the retrieval floor test (now no longer skipped)**

```bash
pytest classifier/tests/test_retrieval_floor.py -v
```
Expected: 1 passed.

- [ ] **Step 5: Re-run the full Plan 1-B test suite end-to-end**

```bash
pytest classifier/tests/ -v
```
Expected: all tests pass. Specifically the contamination test from Task 8 must still be green.

- [ ] **Step 6: Re-compute hashes.json with the new artifacts**

```bash
python <<'PY'
import hashlib, json
from pathlib import Path
HASHES = Path("data/splits/hashes.json")
current = json.loads(HASHES.read_text())
plan1b_artifacts = {
    "data/candidates/pool_v1.jsonl",
    "data/candidates/retrieval_floor_report.json",
    "data/processed/nodes.json",
}
section = {}
for rel in plan1b_artifacts:
    p = Path(rel)
    section[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
current["plan1b_v1"] = section
HASHES.write_text(json.dumps(current, indent=2, sort_keys=True))
print("appended plan1b_v1 section")
PY
```

- [ ] **Step 7: Commit the final artifacts**

```bash
git add data/candidates/pool_v1.jsonl data/candidates/retrieval_floor_report.json data/splits/hashes.json
git commit -m "plan1b: build pool_v1 + retrieval floor on Tier-B 25-pair matrix (coverage_at_20=<value>)"
```

---

## Task 15: Open PR and unblock Phase 0 orchestrator

- [ ] **Step 1: Push the branch**

```bash
git push -u origin plan1b/upstream-integration
```

- [ ] **Step 2: Open the PR**

```bash
gh pr create --title "Plan 1-B: upstream crosswalk integration + Tier-B framework matrix" --body "$(cat <<'EOF'
## Summary

- Finishes leftover Plan 1 Task C-3 / C-4 / C-5 (build_candidate_pool, build_candidates.py, retrieval_floor.py) that never landed in the original 2026-04-07 plan
- Vendors GenAI-Data-Security-Initiative crosswalk repo as a pinned read-only dependency under `third_party/genai-crosswalk/`
- Adds upstream loader producing `data/upstream/{mappings_v1,crossrefs_v1}.jsonl`
- Adds strict source-id-level contamination partition + pre-registered honesty-firewall test (`classifier/tests/test_contamination.py`)
- Adds DSGAI as a 3rd source list (21 nodes) and two new target frameworks: NIST SP 800-53 rev5 and EU AI Act
- Expands FRAMEWORK_PAIRS from 12 → 25 covering all 13 frameworks with ≥2 appearances each
- Builds `data/candidates/pool_v1.jsonl` and retrieval floor report on the new matrix
- Adds THIRD_PARTY_NOTICES.md and extends data/splits/hashes.json with upstream + plan1b sections
- Frozen test (`human_test_frozen.jsonl`) is byte-identical; pre-registered thresholds untouched

## Test plan

- [ ] All `classifier/tests/` pass on CI
- [ ] `data/upstream/contamination_report.json` shows held_out_count > 0 (proves the firewall is firing)
- [ ] `data/candidates/pool_v1.jsonl` exists with 25 distinct framework_pair keys
- [ ] `retrieval_floor_report.json` shows coverage_at_20 ≥ 0.95 (or coverage_at_k_used = 1.0)
- [ ] `data/splits/hashes.json` retains all original sections plus new `upstream_v1` and `plan1b_v1` sections
EOF
)"
```

- [ ] **Step 3: Wait for CI green, then merge**

(Maintainer / orchestrator handles the merge per Phase 0's branch hygiene rules.)

- [ ] **Step 4: After merge, verify orchestrator pre-flight passes**

```bash
git checkout main && git pull --ff-only
ls data/splits/hashes.json data/candidates/pool_v1.jsonl
test -f data/upstream/partition.json
pytest classifier/tests/test_contamination.py -v
```
Expected: all four checks succeed. The Phase 0 orchestrator's Phase 2 pre-flight is now satisfied.

---

## Self-review (run after writing)

Spec coverage check against `2026-04-08-upstream-crosswalk-integration-design.md`:

| Spec section | Plan task |
|---|---|
| §3 architecture (3 filesystem locations) | File Structure section + Tasks 4, 5, 6 |
| §4.1 upstream vendor + MANIFEST | Task 5 |
| §4.2 DSGAI ingester | Task 4 |
| §4.3 upstream loader (with ID normalization) | Task 6 |
| §4.4 contamination auditor + partition rules | Task 7 |
| §4.4 CI gate (pre-registered, non-skippable) | Task 8 |
| §4.5 label provenance & weighted training | Deferred to Plan 5 rewrite (out of scope for Plan 1-B; loader emits provenance_sha so the trainer can consume it) |
| §5.1 source lists (3) | Task 4 + Task 13 |
| §5.2 target frameworks (3 required) | Tasks 10, 11, 12 |
| §5.3 pair matrix growth | Task 13 |
| §6 evaluation strategy (frozen test untouched, upstream benchmark, crossref benchmark) | Frozen test untouched by construction (§4.4 firewall); upstream benchmark and crossref benchmark are *consumed* by Plan 5+ rewrites, but the data files are produced here in Tasks 6 and 7 |
| §10 acceptance criteria 1-8 | Tasks 4-9, 13, 14 |
| §10 acceptance criteria 9-10 (Plan 6 halt removed; Plans 2-8 rewritten) | Out of scope for Plan 1-B; explicitly deferred to follow-on plan-writing sessions |
| Plan 1 leftover C-3/C-4/C-5 | Tasks 1, 2, 3, 14 |

No placeholder violations. No "similar to task N" without code. All file paths are exact. All commands have expected output. The contamination test in Task 8 has no skip/xfail decorators per spec requirement.

Type consistency: `node_id`, `local_id`, `framework`, `title`, `text` are used identically across all four ingesters (Tasks 4, 10, 11, 12) and matched in the merge script (Task 13) and the contamination auditor's `split_node_id` helper (Task 7).

One known caveat to flag for the user before execution: Tasks 10 and 11 download external resources (NIST OSCAL JSON, EUR-Lex HTML). If either URL has shifted since this plan was written, the implementer SHOULD inspect the parent directory pages and adjust the URL — both NIST and EUR-Lex are stable publishers but periodically reorganize.

---

## Out of scope (do not creep into Plan 1-B)

- Anything from spec §7 Plans 2-8 deltas — those get separate follow-on plans
- Schema-format adapters for upstream output (deferred per spec D4)
- Multi-task auxiliary heads for severity/tier/scope
- Re-running build_candidates with `BAAI/bge-large-en-v1.5` on Lambda — that's a Plan 2 prerequisite, not Plan 1-B
- Modifying `data/splits/human_test_frozen.jsonl`, `sme_pool_full.jsonl`, or `human_cal.jsonl`
