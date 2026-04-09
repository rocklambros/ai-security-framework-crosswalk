"""5-fold out-of-fold feature builder for the stacker.

Builds a wide feature matrix from Plan 3 baselines (BM25, BGE cosine)
plus bridge scores, joining against v1_frozen labels. Each row gets
OOF predictions to prevent leakage into the stacker.

Contract 5: Only reads v1_frozen labels.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold

from mapping_engine.engine.graph import load_graph
from mapping_engine.engine.bridge import graph_bridge_scores


TIER_MAP = {"equivalent": 3, "related": 2, "partial": 1, "unrelated": 0}
FEATURE_CACHE = Path("data/features/baseline_features.parquet")


def _pair_key(row: dict) -> str:
    tgt_local = row["target_node_id"].split(":", 1)[1]
    return f"{row['source_framework']}:{row['source_id']}__{row['target_framework']}:{tgt_local}"


def _compute_bridge_scores(pairs: list[dict], G) -> np.ndarray:
    """Compute bridge score for each (source, target) pair."""
    scores = []
    for r in pairs:
        src = f"{r['source_framework']}:{r['source_id']}"
        tgt = r["target_node_id"]
        if src in G and tgt in G:
            s = graph_bridge_scores(G, [src], [tgt], {})
            scores.append(float(s[0][0]))
        else:
            scores.append(0.0)
    return np.array(scores)


def build_feature_matrix(
    labels_path: str = "data/labels/llm_sme/v1_frozen/llm_train.jsonl",
    feature_cache_path: str = str(FEATURE_CACHE),
    nodes_path: str = "data/processed/nodes.json",
    edges_path: str = "data/processed/edges.json",
) -> pd.DataFrame:
    """Build the wide feature matrix for stacker training.

    Returns DataFrame with columns:
      pair_key, score_bge_cosine, score_bm25, score_bridge, label, weight
    """
    assert "v1_frozen" in str(labels_path), "Contract 5: must use v1_frozen"

    # Load labels
    labels = [json.loads(l) for l in Path(labels_path).read_text().splitlines() if l.strip()]

    # Build pair keys and labels
    rows = []
    for r in labels:
        rows.append({
            "pair_key": _pair_key(r),
            "label": TIER_MAP.get(r["relation"], 0),
            "weight": r.get("weight", 1.0),
            "provenance_tag": r.get("provenance_tag", "unknown"),
        })
    df_labels = pd.DataFrame(rows)

    # Merge Plan 3 features
    df_feats = pd.read_parquet(feature_cache_path)
    df = df_labels.merge(df_feats, on="pair_key", how="left")

    # Fill missing features with 0
    for col in ["score_bge_cosine", "score_bm25"]:
        df[col] = df[col].fillna(0.0)

    # Compute bridge scores
    G = load_graph(Path(nodes_path), Path(edges_path))
    bridge_scores = _compute_bridge_scores(labels, G)
    df["score_bridge"] = bridge_scores

    return df


def build_oof_predictions(
    df: pd.DataFrame,
    n_splits: int = 5,
    seed: int = 42,
) -> pd.DataFrame:
    """Add out-of-fold stacker predictions to prevent leakage.

    For each fold, trains a simple model on in-fold data and predicts
    on the held-out fold. Returns df with added OOF probability columns.

    This is a placeholder — the actual stacker uses LightGBM. Here we
    just return the feature matrix with fold assignments for the stacker
    to use during training.
    """
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    df = df.copy()
    df["fold"] = -1
    for fold_idx, (_, val_idx) in enumerate(skf.split(df, df["label"])):
        df.loc[df.index[val_idx], "fold"] = fold_idx
    return df
