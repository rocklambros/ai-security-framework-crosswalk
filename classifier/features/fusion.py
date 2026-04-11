"""Feature fusion module — combines LLM scores, CE logits, and graph features.

Feature layout per pair:
  LLM features (always, 5):
    [0:4]  vote distribution — count_per_tier / n_votes for tiers 0..3
    [4]    confidence score

  CE logits (optional, 8):
    [0:4]  deberta_logits
    [4:8]  roberta_logits

  Graph features (optional, 301):
    see classifier/features/graph_features.py for full layout
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import numpy as np

_ROOT = Path(__file__).resolve().parents[2]
_LLM_DIR = _ROOT / "data" / "processed" / "llm_scores_v4"
_CE_DEFAULT = _ROOT / "data" / "processed" / "ce_features_v2.npz"

# ---------------------------------------------------------------------------
# LLM features
# ---------------------------------------------------------------------------

def load_llm_features(split_name: str) -> np.ndarray:
    """Load LLM score features for a split.

    Parameters
    ----------
    split_name:
        Name of the split, e.g. ``"human_cal"``, ``"human_test_frozen"``.
        Resolved to ``data/processed/llm_scores_v4/{split_name}.jsonl``.

    Returns
    -------
    np.ndarray of shape (n_pairs, 5):
        Columns 0-2: individual Sonnet scores (0-10 scale).
        Column 3:    mean score (final_score).
        Column 4:    confidence score.
    """
    path = _LLM_DIR / f"{split_name}.jsonl"
    rows = []
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            scores = rec.get("sonnet_scores", [])
            # Pad/truncate to exactly 3 scores
            while len(scores) < 3:
                scores.append(rec.get("final_score", 0.0))
            feats = scores[:3] + [
                float(rec.get("final_score", 0.0)),
                float(rec.get("confidence", 0.0)),
            ]
            rows.append(feats)
    return np.array(rows, dtype=np.float32)


# ---------------------------------------------------------------------------
# CE features
# ---------------------------------------------------------------------------

def load_ce_features(
    start: int,
    n: int,
    path: str | Path = _CE_DEFAULT,
) -> np.ndarray:
    """Load cross-encoder logit features for a contiguous slice of pairs.

    Parameters
    ----------
    start:
        Index of the first pair in the full CE array.
    n:
        Number of pairs to return.
    path:
        Path to the ``.npz`` file (default: ``data/processed/ce_features_v2.npz``).
        Accepts a string so callers can substitute a newer version, e.g. v4.

    Returns
    -------
    np.ndarray of shape (n, 8):
        Columns 0-3: deberta logits.
        Columns 4-7: roberta logits.
    """
    data = np.load(path)
    deberta = data["deberta_logits"][start : start + n]  # (n, 4)
    roberta = data["roberta_logits"][start : start + n]  # (n, 4)
    return np.hstack([deberta, roberta]).astype(np.float32)


# ---------------------------------------------------------------------------
# Fusion matrix
# ---------------------------------------------------------------------------

def build_fusion_matrix(
    split_name: str,
    ce_start: int,
    n_pairs: int,
    pairs: Optional[list] = None,
    graph_features: Optional[np.ndarray] = None,
    include_ce: bool = True,
    include_graph: bool = True,
    ce_path: str | Path = _CE_DEFAULT,
) -> np.ndarray:
    """Build the fused feature matrix for a set of pairs.

    Parameters
    ----------
    split_name:
        Split name passed to :func:`load_llm_features`.
    ce_start:
        Start index into the CE feature array.
    n_pairs:
        Expected number of pairs; shapes are asserted against this.
    pairs:
        Optional list of pair dicts (reserved for future use; not consumed
        internally but accepted so callers can pass it without error).
    graph_features:
        Pre-computed graph features, shape ``(n_pairs, 301)``.  Required when
        ``include_graph=True``.
    include_ce:
        Whether to append CE logits (8 columns).
    include_graph:
        Whether to append graph features (301 columns).
    ce_path:
        Forwarded to :func:`load_ce_features`.

    Returns
    -------
    np.ndarray of shape ``(n_pairs, D)`` where D depends on enabled blocks:
        - LLM only:             D = 5
        - LLM + CE:             D = 13
        - LLM + graph:          D = 306
        - LLM + CE + graph:     D = 314
    """
    # --- LLM features (always) ---
    llm = load_llm_features(split_name)
    assert llm.shape[0] == n_pairs, (
        f"LLM features have {llm.shape[0]} rows; expected {n_pairs}"
    )

    parts = [llm]

    # --- CE logits (optional) ---
    if include_ce:
        ce = load_ce_features(ce_start, n_pairs, path=ce_path)
        assert ce.shape == (n_pairs, 8), (
            f"CE features shape {ce.shape}; expected ({n_pairs}, 8)"
        )
        parts.append(ce)

    # --- Graph features (optional) ---
    if include_graph:
        if graph_features is None:
            raise ValueError(
                "graph_features must be provided when include_graph=True"
            )
        gf = np.asarray(graph_features, dtype=np.float32)
        assert gf.shape[0] == n_pairs, (
            f"Graph features have {gf.shape[0]} rows; expected {n_pairs}"
        )
        parts.append(gf)

    return np.hstack(parts).astype(np.float32)
