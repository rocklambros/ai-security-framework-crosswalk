"""Load crosswalk data for the Dash app.

Handles two data categories:
  1. Expert-curated mappings (static, always available)
  2. ML predictions (optional, loaded if artifacts exist)
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

_DATA_ROOT = Path(__file__).resolve().parents[3]  # repo root
_UPSTREAM = _DATA_ROOT / "data" / "upstream"
_RESULTS = _DATA_ROOT / "results"
_FRAMEWORKS = _DATA_ROOT / "data" / "frameworks"


def load_mappings(path: Optional[str] = None) -> pd.DataFrame:
    """Load upstream expert mappings as a DataFrame."""
    p = Path(path) if path else _UPSTREAM / "mappings_v1.jsonl"
    rows = []
    with p.open() as f:
        for line in f:
            row = json.loads(line)
            if not row.get("target_id_unresolved", False):
                row["data_source"] = "expert"
                rows.append(row)
    return pd.DataFrame(rows)


def load_ml_predictions(run_dir: Optional[str] = None) -> Optional[pd.DataFrame]:
    """Load ML-predicted mappings if available."""
    if run_dir is None:
        runs_dir = _DATA_ROOT / "runs" / "stacker"
        if not runs_dir.exists():
            return None
        run_dirs = sorted(runs_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
        if not run_dirs:
            return None
        run_dir = str(run_dirs[0])

    pred_path = Path(run_dir) / "predictions.jsonl"
    if not pred_path.exists():
        return None

    rows = []
    with pred_path.open() as f:
        for line in f:
            row = json.loads(line)
            row["data_source"] = "ml_predicted"
            rows.append(row)
    return pd.DataFrame(rows) if rows else None


def load_all_mappings() -> pd.DataFrame:
    """Load expert + ML predictions combined."""
    expert = load_mappings()
    ml = load_ml_predictions()
    if ml is not None:
        return pd.concat([expert, ml], ignore_index=True)
    return expert


def load_sacred_results() -> Optional[Dict[str, Any]]:
    """Load the latest sacred run results."""
    sacred_dir = _RESULTS / "sacred"
    if not sacred_dir.exists():
        return None
    files = sorted(sacred_dir.glob("sacred_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        return None
    with files[0].open() as f:
        return json.load(f)


def load_ablations() -> Optional[Dict[str, Any]]:
    """Load ablation results."""
    path = _RESULTS / "ablations.json"
    if not path.exists():
        return None
    with path.open() as f:
        return json.load(f)


def load_framework_metadata() -> Dict[str, Dict[str, Any]]:
    """Load MANIFEST.json from each framework directory."""
    meta = {}
    if not _FRAMEWORKS.exists():
        return meta
    for fw_dir in _FRAMEWORKS.iterdir():
        if not fw_dir.is_dir():
            continue
        manifest = fw_dir / "MANIFEST.json"
        if manifest.exists():
            with manifest.open() as f:
                data = json.load(f)
                meta[data.get("framework_id", fw_dir.name)] = data
    return meta


def load_crossrefs() -> pd.DataFrame:
    """Load cross-reference edges."""
    path = _UPSTREAM / "crossrefs_v1.jsonl"
    if not path.exists():
        return pd.DataFrame()
    rows = []
    with path.open() as f:
        for line in f:
            rows.append(json.loads(line))
    return pd.DataFrame(rows)
