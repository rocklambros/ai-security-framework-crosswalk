"""Pair-config anchor validation gate.

Runs the full signal pipeline on the anchor pairs declared in a pair
config and reports per-anchor and overall agreement with the expected
tier. The ``holdout_indices`` field of the pair config separates training
anchors from held-out anchors.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from mapping_engine.calibration.weight_learner import (
    FEATURES,
    TIER_ORDER,
    _proba,
)
from mapping_engine.engine.bridge import graph_bridge_scores
from mapping_engine.engine.function_match import compute_function_match
from mapping_engine.engine.keyword import compute_keyword_similarity
from mapping_engine.engine.semantic import compute_semantic_similarity

TIER_NAMES = {v: k for k, v in TIER_ORDER.items()}


def _predict_tier(p: float) -> str:
    if p >= 0.65:
        return "Direct"
    if p >= 0.40:
        return "Related"
    if p >= 0.20:
        return "Tangential"
    return "None"


def validate_anchors(
    G,
    pair_config: Any,
    model: Any,
    model_type: str,
) -> dict[str, Any]:
    """Score the anchor pairs and compare to ``expected_tier``.

    ``pair_config`` may be a ``PairConfig`` dataclass or a dict; we duck-type
    on ``.anchors.pairs`` then fall back to dict access.
    """
    anchors = getattr(pair_config, "anchors", None) or pair_config.get("anchors", {})
    pairs = getattr(anchors, "pairs", None) or anchors.get("pairs", [])
    holdout_idx = set(getattr(anchors, "holdout_indices", None) or anchors.get("holdout_indices", []) or [])

    sources, targets, expected = [], [], []
    for p in pairs:
        sources.append(getattr(p, "source", None) or p["source"])
        targets.append(getattr(p, "target", None) or p["target"])
        expected.append(getattr(p, "expected_tier", None) or p["expected_tier"])

    bridge = graph_bridge_scores(G, sources, targets)
    semantic = compute_semantic_similarity(G, sources, targets)
    keyword = compute_keyword_similarity(G, sources, targets)
    fm = compute_function_match(G, sources, targets)

    rows = []
    for i in range(len(pairs)):
        rows.append(
            {
                "bridge_score": float(bridge[i, i]),
                "semantic_score": float(semantic[i, i]),
                "keyword_score": float(keyword[i, i]),
                "function_match": float(fm[i, i]),
            }
        )
    df = pd.DataFrame(rows)
    proba = _proba(model, df, model_type)

    train_results, hold_results = {}, {}
    train_match, hold_match = 0, 0
    for i, (s, t, exp) in enumerate(zip(sources, targets, expected)):
        pred = _predict_tier(float(proba[i]))
        rec = {"predicted": pred, "expected": exp, "match": pred == exp, "proba": float(proba[i])}
        key = f"{s}__{t}"
        if i in holdout_idx:
            hold_results[key] = rec
            hold_match += int(rec["match"])
        else:
            train_results[key] = rec
            train_match += int(rec["match"])

    n_train = max(1, len(train_results))
    n_hold = max(1, len(hold_results))
    return {
        "training_anchors": train_results,
        "holdout_anchors": hold_results,
        "training_accuracy": train_match / n_train,
        "holdout_accuracy": hold_match / n_hold,
        "overall_accuracy": (train_match + hold_match) / max(1, len(pairs)),
    }

