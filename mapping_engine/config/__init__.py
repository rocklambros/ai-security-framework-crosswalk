"""Config loaders + Pydantic schemas for mapping_engine.

``load_defaults()`` reads ``defaults.yaml``; ``load_pair_config(name)`` reads
a pair YAML and merges it on top of the defaults. Pair-level keys override
default keys at the top level only (shallow merge for the ``weights`` /
``thresholds`` / ``semantic`` / ``bridge`` blocks is achieved by merging
those nested dicts as well).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

CONFIG_DIR = Path(__file__).resolve().parent
DEFAULTS_PATH = CONFIG_DIR / "defaults.yaml"
PAIRS_DIR = CONFIG_DIR / "pairs"


class AnchorPair(BaseModel):
    source: str
    target: str
    expected_tier: str


class Anchors(BaseModel):
    pairs: list[AnchorPair]
    holdout_indices: list[int] = Field(default_factory=list)


class PairConfig(BaseModel):
    source_framework: str
    target_framework: str
    source_entry_types: list[str] = Field(default_factory=list)
    target_entry_types: list[str] = Field(default_factory=list)
    match_mode: str = "control_to_risk"
    weights: dict[str, float] = Field(default_factory=dict)
    thresholds: dict[str, float] = Field(default_factory=dict)
    semantic: dict[str, Any] = Field(default_factory=dict)
    bridge: dict[str, Any] = Field(default_factory=dict)
    function_match: dict[str, Any] = Field(default_factory=dict)
    reranker: dict[str, Any] = Field(default_factory=dict)
    active_learning: dict[str, Any] = Field(default_factory=dict)
    anchors: Anchors


def load_defaults() -> dict[str, Any]:
    """Load defaults.yaml as a plain dict."""
    return yaml.safe_load(DEFAULTS_PATH.read_text())


def _deep_merge(base: dict, override: dict) -> dict:
    out = dict(base)
    for k, v in override.items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def load_pair_config(pair_name: str, validate_anchors_in: "Any | None" = None) -> PairConfig:
    """Load a pair YAML, deep-merging it on top of defaults.yaml.

    Parameters
    ----------
    pair_name : str
        Filename stem under ``config/pairs/`` (no ``.yaml``).
    validate_anchors_in : networkx.Graph, optional
        If provided, every anchor source/target node_id must exist in the graph.
    """
    pair_path = PAIRS_DIR / f"{pair_name}.yaml"
    pair_data = yaml.safe_load(pair_path.read_text())
    merged = _deep_merge(load_defaults(), pair_data)
    cfg = PairConfig(**merged)

    if validate_anchors_in is not None:
        missing: list[str] = []
        for ap in cfg.anchors.pairs:
            for nid in (ap.source, ap.target):
                if nid not in validate_anchors_in:
                    missing.append(nid)
        if missing:
            raise ValueError(f"Anchor node_ids missing from graph: {missing}")
    return cfg
