"""TF-IDF keyword similarity signal with synonym expansion.

Pair-agnostic port of v1 ``aiuc.signals.compute_keyword_similarity``.
Synonym groups are loaded from ``mapping_engine/config/synonyms.yaml``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

import networkx as nx
import numpy as np
import yaml
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from mapping_engine.engine.graph import get_node_text

DEFAULT_SYNONYMS_PATH = Path(__file__).resolve().parents[1] / "config" / "synonyms.yaml"


def load_synonyms(path: str | Path | None = None) -> list[set[str]]:
    """Load synonym groups from YAML as a list of sets."""
    p = Path(path) if path else DEFAULT_SYNONYMS_PATH
    raw = yaml.safe_load(p.read_text()) or []
    return [set(g) for g in raw]


def _expand_synonyms(text: str, groups: list[set[str]]) -> str:
    """Append the rest of any synonym group whose member appears in ``text``."""
    text_lower = text.lower()
    expansions: list[str] = []
    for group in groups:
        matched = [term for term in group if term in text_lower]
        if matched:
            expansions.extend(group - set(matched))
    if not expansions:
        return text
    return text + " " + " ".join(expansions)


def compute_keyword_similarity(
    G: nx.DiGraph,
    source_nodes: Sequence[str],
    target_nodes: Sequence[str],
    config: dict | None = None,
) -> np.ndarray:
    """TF-IDF cosine similarity matrix with synonym expansion.

    Parameters
    ----------
    config : dict, optional
        Recognized keys: ``synonyms_path`` (str), ``expand_synonyms`` (bool,
        default True), ``max_features`` (int, default 5000).
    """
    cfg = config or {}
    expand = cfg.get("expand_synonyms", True)
    max_features = int(cfg.get("max_features", 5000))
    groups = load_synonyms(cfg.get("synonyms_path")) if expand else []

    src_texts = [get_node_text(G, nid) for nid in source_nodes]
    tgt_texts = [get_node_text(G, nid) for nid in target_nodes]
    if expand:
        src_texts = [_expand_synonyms(t, groups) for t in src_texts]
        tgt_texts = [_expand_synonyms(t, groups) for t in tgt_texts]

    n_src = len(src_texts)
    all_texts = src_texts + tgt_texts
    vec = TfidfVectorizer(
        ngram_range=(1, 2),
        max_features=max_features,
        stop_words="english",
        sublinear_tf=True,
    )
    M = vec.fit_transform(all_texts)
    sim = cosine_similarity(M[:n_src], M[n_src:])
    return np.clip(np.asarray(sim, dtype=np.float64), 0.0, 1.0)
