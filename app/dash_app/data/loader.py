"""Data loaders for the Coverage Dashboard.

Reads from the upstream mappings and processed nodes produced by the
mapping-engine pipeline. Falls back gracefully when files are absent
(e.g. during unit tests or local dev without model artefacts).
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Repo-root relative paths (resolved at import time so tests can patch them)
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parents[3]
_MAPPINGS_PATH = _REPO_ROOT / "data" / "upstream" / "mappings_v1.jsonl"
_NODES_PATH = _REPO_ROOT / "data" / "processed" / "nodes.json"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


@lru_cache(maxsize=1)
def load_all_mappings() -> list[dict[str, Any]]:
    """Return every row from ``mappings_v1.jsonl`` as a list of dicts.

    Returns an empty list when the file is absent so callers do not need
    to guard against ``FileNotFoundError``.
    """
    if not _MAPPINGS_PATH.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in _MAPPINGS_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


@lru_cache(maxsize=1)
def load_framework_metadata() -> dict[str, dict[str, Any]]:
    """Return per-framework metadata keyed by framework slug.

    Each value is a dict with at least ``control_count`` (int) and
    ``name`` (str, human-readable label).  Falls back to an empty dict
    when ``nodes.json`` is absent.
    """
    if not _NODES_PATH.exists():
        return {}

    nodes: list[dict[str, Any]] = json.loads(
        _NODES_PATH.read_text(encoding="utf-8")
    )

    meta: dict[str, dict[str, Any]] = {}
    for node in nodes:
        fw = node.get("framework", "")
        if not fw:
            continue
        if fw not in meta:
            meta[fw] = {"framework": fw, "control_count": 0}
        meta[fw]["control_count"] += 1

    return meta
