"""Uncertainty-based active learning loop.

Selects the highest-uncertainty candidate pairs for expert labeling,
exports a YAML labeling sheet, and re-imports completed labels back into
the training data.

Design decisions (Session 4)
----------------------------
* Uncertainty = distance to the nearest tier threshold (Direct,
  Related, Tangential), normalized to [0, 1] inside ``uncertainty_band``.
  Pairs further than the band from every threshold get uncertainty 0.
* Tie-break = signal disagreement: ``max(signals) - min(signals)`` over
  the four signal values. High disagreement = high uncertainty.
* Surface ``max_candidates`` (default 20) per round.
* Output: a YAML file with one entry per pair containing the source/
  target IDs, names, descriptions, raw signal scores, and a blank
  ``expert_tier`` field for the labeler to fill in.
* Feedback loop: ``import_labels`` merges labeled pairs into
  ``training_data.csv`` and overwrites their ``is_mapped`` /
  ``expert_tier`` columns.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

import networkx as nx
import numpy as np
import pandas as pd
import yaml

DEFAULT_THRESHOLDS = (0.20, 0.35, 0.55)  # tangential, related_primary, direct
DEFAULT_BAND = 0.05
DEFAULT_MAX = 20

_TIER_BY_NAME = {"None": 0, "Tangential": 1, "Related": 2, "Direct": 3}


def _uncertainty(score: float, thresholds: Sequence[float], band: float) -> float:
    """Closer to a threshold (within ``band``) → higher uncertainty in [0, 1]."""
    nearest = min(abs(score - t) for t in thresholds)
    if nearest >= band:
        return 0.0
    return float(1.0 - nearest / band)


def select_uncertain_pairs(
    composite_scores: np.ndarray,
    signal_matrices: dict[str, np.ndarray],
    source_nodes: Sequence[str],
    target_nodes: Sequence[str],
    config: dict | None = None,
) -> list[dict[str, Any]]:
    """Return up to ``max_candidates`` highest-uncertainty pairs.

    Parameters
    ----------
    composite_scores : np.ndarray
        Final composite score matrix shape ``(n_src, n_tgt)``.
    signal_matrices : dict[str, np.ndarray]
        Same shape, keyed by signal name (``bridge``, ``semantic``,
        ``keyword``, ``function_match``).
    config : dict, optional
        Keys: ``thresholds`` (list of float), ``uncertainty_band``,
        ``max_candidates``.
    """
    cfg = config or {}
    thresholds = list(cfg.get("thresholds", DEFAULT_THRESHOLDS))
    band = float(cfg.get("uncertainty_band", DEFAULT_BAND))
    max_n = int(cfg.get("max_candidates", DEFAULT_MAX))

    n_src, n_tgt = composite_scores.shape
    rows: list[dict[str, Any]] = []
    for i in range(n_src):
        for j in range(n_tgt):
            s = float(composite_scores[i, j])
            unc = _uncertainty(s, thresholds, band)
            if unc <= 0.0:
                continue
            sigs = {k: float(M[i, j]) for k, M in signal_matrices.items()}
            disagreement = max(sigs.values()) - min(sigs.values())
            rows.append(
                {
                    "source_node_id": source_nodes[i],
                    "target_node_id": target_nodes[j],
                    "composite_score": s,
                    **sigs,
                    "uncertainty_score": float(unc * (1.0 + disagreement)),
                }
            )

    rows.sort(key=lambda r: r["uncertainty_score"], reverse=True)
    return rows[:max_n]


def export_labeling_sheet(
    candidates: list[dict[str, Any]],
    output_path: str | Path,
    G: nx.DiGraph | None = None,
) -> Path:
    """Write a YAML labeling sheet with one entry per candidate."""
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    items = []
    for c in candidates:
        item = {
            "source_node_id": c["source_node_id"],
            "target_node_id": c["target_node_id"],
            "composite_score": round(c["composite_score"], 4),
            "uncertainty_score": round(c["uncertainty_score"], 4),
            "signals": {k: round(c[k], 4) for k in c
                        if k in ("bridge", "semantic", "keyword", "function_match")},
            "expert_tier": "",  # to be filled by reviewer (Direct/Related/Tangential/None)
            "expert_relevance": "",  # Primary/Secondary
            "notes": "",
        }
        if G is not None:
            for side, nid in (("source", c["source_node_id"]), ("target", c["target_node_id"])):
                d = G.nodes.get(nid, {})
                item[f"{side}_name"] = d.get("name") or d.get("title") or ""
                item[f"{side}_description"] = d.get("description") or ""
        items.append(item)
    out_path.write_text(yaml.safe_dump({"candidates": items}, sort_keys=False))
    return out_path


def import_labels(
    labeling_sheet_path: str | Path,
    training_data_path: str | Path,
) -> pd.DataFrame:
    """Merge a completed labeling sheet into the training CSV.

    Pairs whose ``expert_tier`` is non-empty overwrite the existing rows;
    otherwise the candidate is skipped. Returns the updated DataFrame
    *and* writes it back to ``training_data_path``.
    """
    sheet = yaml.safe_load(Path(labeling_sheet_path).read_text()) or {}
    items = sheet.get("candidates", [])
    df = pd.read_csv(training_data_path, keep_default_na=False, na_values=[""])
    for col in ("expert_tier", "relevance", "rationale"):
        if col in df.columns:
            df[col] = df[col].astype(object)
    idx_by_pair = {
        (r.source_node_id, r.target_node_id): k
        for k, r in df.iterrows()
    }
    for item in items:
        tier = (item.get("expert_tier") or "").strip()
        if not tier:
            continue
        key = (item["source_node_id"], item["target_node_id"])
        rel = (item.get("expert_relevance") or "").strip() or (
            "Primary" if tier == "Direct" else "Secondary" if tier == "Related" else "None"
        )
        is_mapped = 1 if tier in ("Direct", "Related") else 0
        if key in idx_by_pair:
            k = idx_by_pair[key]
            df.at[k, "is_mapped"] = is_mapped
            df.at[k, "expert_tier"] = tier
            df.at[k, "relevance"] = rel
    df.to_csv(training_data_path, index=False)
    return df
