"""Contrastive negative-signal: catch high-semantic / low-overlap false positives.

Idea: when two nodes have high embedding similarity (>0.6) but their
distinctive *domain* keywords (proper nouns, technique names, framework
identifiers) don't overlap, the semantic similarity is likely a generic
"AI security" baseline and the pair is a false positive.

The penalty matrix returned here is multiplied into the composite score
by the composer as ``composite *= (1 - 0.3 * penalty)``.
"""

from __future__ import annotations

import re
from typing import Sequence

import networkx as nx
import numpy as np

from mapping_engine.engine.graph import get_node_text

# Tokens to drop when extracting "distinctive" keywords
_GENERIC = {
    "ai", "system", "model", "data", "use", "control", "policy", "process",
    "risk", "the", "and", "for", "with", "of", "to", "in", "on", "or", "a",
    "an", "is", "be", "are", "by", "from", "as", "that", "this", "it",
    "ensure", "should", "must", "may", "include", "provide", "manage",
}

_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9\-/]{2,}")


def _domain_terms(text: str) -> set[str]:
    """Return distinctive lowercased terms (>=3 chars, not generic)."""
    if not text:
        return set()
    toks = {t.lower() for t in _TOKEN_RE.findall(text)}
    return {t for t in toks if t not in _GENERIC and not t.isdigit()}


def detect_domain_conflicts(G: nx.DiGraph, source_id: str, target_id: str) -> float:
    """Return a per-pair conflict score in [0, 1].

    1.0 = the two nodes share *no* distinctive domain terms.
    0.0 = the two share enough that a confident overlap exists.
    """
    s = _domain_terms(get_node_text(G, source_id))
    t = _domain_terms(get_node_text(G, target_id))
    if not s or not t:
        return 0.0
    union = s | t
    jacc = len(s & t) / len(union) if union else 0.0
    return float(max(0.0, 1.0 - 4.0 * jacc))


def compute_contrastive_penalty(
    G: nx.DiGraph,
    source_nodes: Sequence[str],
    target_nodes: Sequence[str],
    semantic_scores: np.ndarray,
    config: dict | None = None,
) -> np.ndarray:
    """Penalty matrix in [0, 1]; nonzero only where semantic > threshold."""
    cfg = config or {}
    sem_thresh = float(cfg.get("semantic_threshold", 0.6))
    M = np.zeros_like(semantic_scores, dtype=np.float64)
    if M.size == 0:
        return M
    high = semantic_scores > sem_thresh
    if not high.any():
        return M
    src_terms = [_domain_terms(get_node_text(G, s)) for s in source_nodes]
    tgt_terms = [_domain_terms(get_node_text(G, t)) for t in target_nodes]
    for i, j in zip(*np.where(high)):
        s, t = src_terms[i], tgt_terms[j]
        if not s or not t:
            continue
        union = s | t
        if not union:
            continue
        jacc = len(s & t) / len(union)
        M[i, j] = max(0.0, 1.0 - 4.0 * jacc)
    return np.clip(M, 0.0, 1.0)

