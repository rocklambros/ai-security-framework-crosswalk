"""Semantic similarity signal (sentence-transformer embeddings).

Pair-agnostic port of v1 ``aiuc.signals.compute_semantic_similarity``.

Design decisions (sequential-thinking, see SESSION_CONTEXT.md):

* Default model: ``BAAI/bge-large-en-v1.5`` (335M, 1024 dims). Chosen over
  ``intfloat/e5-large-v2`` because (a) bge is symmetric — no awkward
  ``query:`` / ``passage:`` prefixing needed for control↔risk pairs that
  are conceptually peers, not query/document; (b) bge tops MTEB STS for
  this size class; (c) memory footprint (~1.3 GB FP32) fits comfortably
  on the Jetson AGX Orin's shared 64 GB.
* Z-score normalize per source row, then sigmoid → [0, 1]. Fixes the
  high-baseline-similarity problem (all AI-security texts are ~0.5+).
* Prevention boost: for risk-typed targets whose description contains a
  prevention/mitigation section, embed that subtext separately and take
  the elementwise max with the full-text similarity. Framework-agnostic
  detection: regex on the description.
"""

from __future__ import annotations

import re
from typing import Any, Sequence

import networkx as nx
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from mapping_engine.engine.graph import get_node_text

DEFAULT_MODEL = "BAAI/bge-large-en-v1.5"

# Module-level embedding cache: {(model_name, node_id): np.ndarray}
_EMBEDDING_CACHE: dict[tuple[str, str], np.ndarray] = {}

# Cache loaded models so repeated calls don't re-download/re-init.
_MODEL_CACHE: dict[str, Any] = {}

_PREVENTION_RE = re.compile(
    r"(?is)(prevention|mitigation|remediation|countermeasures?)\s*[:\-]?\s*(.+)"
)


def _load_model(model_name: str) -> Any:
    """Load (and cache) a SentenceTransformer on GPU if available."""
    if model_name in _MODEL_CACHE:
        return _MODEL_CACHE[model_name]
    import torch
    from sentence_transformers import SentenceTransformer

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = SentenceTransformer(model_name, device=device)
    _MODEL_CACHE[model_name] = model
    return model


def _extract_prevention_text(description: str) -> str | None:
    """Return the prevention/mitigation subtext if present, else None."""
    if not description:
        return None
    m = _PREVENTION_RE.search(description)
    if not m:
        return None
    sub = m.group(2).strip()
    return sub or None


def compute_embeddings(
    G: nx.DiGraph,
    node_ids: Sequence[str],
    model: Any,
) -> np.ndarray:
    """Encode each node's text via ``model``, caching by (model_name, node_id).

    Returns
    -------
    np.ndarray
        Matrix of shape ``(len(node_ids), embedding_dim)``.
    """
    model_name = getattr(model, "_model_name", None) or model.__class__.__name__
    # SentenceTransformer doesn't expose name reliably; reach into config dict.
    try:
        model_name = model[0].auto_model.config._name_or_path  # type: ignore[index]
    except Exception:
        pass

    missing_idx: list[int] = []
    missing_texts: list[str] = []
    out: list[np.ndarray | None] = [None] * len(node_ids)
    for i, nid in enumerate(node_ids):
        key = (model_name, nid)
        if key in _EMBEDDING_CACHE:
            out[i] = _EMBEDDING_CACHE[key]
        else:
            missing_idx.append(i)
            missing_texts.append(get_node_text(G, nid))
    if missing_texts:
        encoded = model.encode(missing_texts, show_progress_bar=False, normalize_embeddings=False)
        for k, i in enumerate(missing_idx):
            vec = np.asarray(encoded[k], dtype=np.float64)
            _EMBEDDING_CACHE[(model_name, node_ids[i])] = vec
            out[i] = vec
    return np.vstack([o for o in out if o is not None])


def _zscore_sigmoid(M: np.ndarray) -> np.ndarray:
    row_means = M.mean(axis=1, keepdims=True)
    row_stds = M.std(axis=1, keepdims=True)
    row_stds = np.where(row_stds < 1e-8, 1.0, row_stds)
    z = (M - row_means) / row_stds
    return 1.0 / (1.0 + np.exp(-z))


def compute_semantic_similarity(
    G: nx.DiGraph,
    source_nodes: Sequence[str],
    target_nodes: Sequence[str],
    config: dict | None = None,
) -> np.ndarray:
    """Cosine similarity between source and target embeddings, row-normalized.

    Parameters
    ----------
    G : nx.DiGraph
        Crosswalk graph.
    source_nodes, target_nodes : sequence of node_id strings.
    config : dict, optional
        ``{"model": str, "z_normalize": bool, "prevention_boost": bool}``.
        Defaults pulled from ``defaults.yaml`` semantic block.

    Returns
    -------
    np.ndarray
        Matrix of shape ``(len(source_nodes), len(target_nodes))`` with
        values in ``[0, 1]`` after Z-score sigmoid normalization.
    """
    cfg = config or {}
    model_name = cfg.get("model", DEFAULT_MODEL)
    do_zscore = cfg.get("z_normalize", True)
    do_prev = cfg.get("prevention_boost", True)

    model = _load_model(model_name)

    src_emb = compute_embeddings(G, list(source_nodes), model)
    tgt_emb = compute_embeddings(G, list(target_nodes), model)
    raw = cosine_similarity(src_emb, tgt_emb).astype(np.float64)

    if do_prev:
        prev_texts: list[str] = []
        prev_idx: list[int] = []
        for j, nid in enumerate(target_nodes):
            d = G.nodes[nid]
            if d.get("entry_type") != "risk":
                continue
            sub = _extract_prevention_text(str(d.get("description") or ""))
            if sub:
                prev_texts.append(sub)
                prev_idx.append(j)
        if prev_texts:
            prev_emb = model.encode(prev_texts, show_progress_bar=False)
            prev_emb = np.asarray(prev_emb, dtype=np.float64)
            prev_sim = cosine_similarity(src_emb, prev_emb).astype(np.float64)
            for k, j in enumerate(prev_idx):
                raw[:, j] = np.maximum(raw[:, j], prev_sim[:, k])

    if do_zscore:
        return _zscore_sigmoid(raw)
    # Without z-norm, clip to [0, 1].
    return np.clip(raw, 0.0, 1.0)
