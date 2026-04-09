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
    """Compute bridge score for each (source, target) pair.

    Groups by target framework to batch bridge score computation.
    """
    # Group pairs by target framework for batched computation
    from collections import defaultdict
    by_tgt_fw: dict[str, list[tuple[int, str, str]]] = defaultdict(list)
    for i, r in enumerate(pairs):
        src = f"{r['source_framework']}:{r['source_id']}"
        tgt = r["target_node_id"]
        tgt_fw = r.get("target_framework") or tgt.split(":")[0]
        if src in G and tgt in G:
            by_tgt_fw[tgt_fw].append((i, src, tgt))

    scores = np.zeros(len(pairs))

    for tgt_fw, group in by_tgt_fw.items():
        # Get all unique sources and targets for this framework
        indices = [g[0] for g in group]
        srcs = [g[1] for g in group]
        tgts = [g[2] for g in group]

        # Get unique targets in this framework for the bridge
        unique_tgts = sorted(set(tgts))
        tgt_to_col = {t: j for j, t in enumerate(unique_tgts)}

        # Batch compute: bridge_scores shape = (len(srcs), len(unique_tgts))
        # But we need per-pair, so compute in chunks
        batch_size = 50
        for batch_start in range(0, len(srcs), batch_size):
            batch_end = min(batch_start + batch_size, len(srcs))
            batch_srcs = srcs[batch_start:batch_end]
            batch_tgts = tgts[batch_start:batch_end]
            batch_indices = indices[batch_start:batch_end]

            # For small batches, compute individually (bridge is fast per pair)
            for k, (src, tgt, idx) in enumerate(zip(batch_srcs, batch_tgts, batch_indices)):
                s = graph_bridge_scores(G, [src], [tgt], {})
                scores[idx] = float(s[0][0])

    return scores


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
