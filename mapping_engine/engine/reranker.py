"""Cross-encoder reranker (precision second stage).

The first-stage signals (bridge / semantic / keyword / function_match)
produce a candidate composite score for every (source, target) pair.
For each source row we take the top-k targets by composite score and
re-score those pairs with a sentence-pair cross-encoder
(``cross-encoder/ms-marco-MiniLM-L-6-v2`` by default), then linearly
blend the cross-encoder score back into the composite::

    final[i,j] = (1 - bw) * composite[i,j] + bw * sigmoid(ce[i,j])

Pairs outside the per-row top-k keep their original composite score.
The model loads on CUDA when available and is cached process-wide.
"""

from __future__ import annotations

from typing import Any, Sequence

import networkx as nx
import numpy as np

from mapping_engine.engine.graph import get_node_text

DEFAULT_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
DEFAULT_TOP_K = 50
DEFAULT_BLEND_WEIGHT = 0.30

_CE_CACHE: dict[str, Any] = {}


def load_cross_encoder(model_name: str = DEFAULT_MODEL, device: str | None = None):
    """Lazy-load (and cache) a sentence-transformers ``CrossEncoder``."""
    if model_name in _CE_CACHE:
        return _CE_CACHE[model_name]
    from sentence_transformers import CrossEncoder
    import torch

    dev = device or ("cuda" if torch.cuda.is_available() else "cpu")
    model = CrossEncoder(model_name, device=dev)
    _CE_CACHE[model_name] = model
    return model


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


def rerank_candidates(
    G: nx.DiGraph,
    source_nodes: Sequence[str],
    target_nodes: Sequence[str],
    composite_scores: np.ndarray,
    config: dict | None = None,
) -> np.ndarray:
    """Return a reranked score matrix the same shape as ``composite_scores``.

    Parameters
    ----------
    config : dict, optional
        Keys (under ``reranker``): ``model``, ``top_k``, ``blend_weight``.
        Either flat or nested under ``reranker`` is accepted.
    """
    cfg = (config or {}).get("reranker", config or {})
    model_name = str(cfg.get("model", DEFAULT_MODEL))
    top_k = int(cfg.get("top_k", DEFAULT_TOP_K))
    bw = float(cfg.get("blend_weight", DEFAULT_BLEND_WEIGHT))

    out = composite_scores.astype(np.float64).copy()
    n_src, n_tgt = out.shape
    if n_src == 0 or n_tgt == 0:
        return out

    model = load_cross_encoder(model_name)
    src_texts = [get_node_text(G, s) for s in source_nodes]
    tgt_texts = [get_node_text(G, t) for t in target_nodes]

    k = min(top_k, n_tgt)
    for i in range(n_src):
        row = out[i]
        if k >= n_tgt:
            top_idx = np.argsort(-row)
        else:
            top_idx = np.argpartition(-row, k - 1)[:k]
        pairs = [(src_texts[i], tgt_texts[j]) for j in top_idx]
        if not pairs:
            continue
        ce_raw = model.predict(pairs, show_progress_bar=False, convert_to_numpy=True)
        ce_norm = _sigmoid(np.asarray(ce_raw, dtype=np.float64))
        out[i, top_idx] = (1.0 - bw) * row[top_idx] + bw * ce_norm

    return np.clip(out, 0.0, 1.0)

