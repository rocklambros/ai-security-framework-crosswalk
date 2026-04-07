"""Node2Vec structural-similarity signal (optional 5th signal).

Loads pre-trained Node2Vec embeddings from
``data/processed/node2vec_embeddings.npy`` and computes a per-pair
cosine similarity matrix shaped like every other signal module so it
can be plugged into the composer behind a feature flag.

Nodes that aren't in the trained vocabulary (orphans, frameworks added
after the embedding was trained) get a similarity of 0.0 — explicit
"no information" rather than a random vector.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Sequence

import numpy as np

REPO = Path(__file__).resolve().parents[2]
DEFAULT_EMB_PATH = REPO / "data" / "processed" / "node2vec_embeddings.npy"
DEFAULT_VOCAB_PATH = REPO / "data" / "processed" / "node2vec_vocab.json"


@lru_cache(maxsize=4)
def _load(emb_path: str, vocab_path: str) -> tuple[np.ndarray, dict[str, int]]:
    M = np.load(emb_path).astype(np.float64)
    vocab = json.loads(Path(vocab_path).read_text())
    # L2 normalize so dot product == cosine similarity
    norms = np.linalg.norm(M, axis=1, keepdims=True)
    norms = np.where(norms < 1e-12, 1.0, norms)
    return M / norms, vocab


def compute_node2vec_similarity(
    source_nodes: Sequence[str],
    target_nodes: Sequence[str],
    embeddings_path: str | Path = DEFAULT_EMB_PATH,
    vocab_path: str | Path = DEFAULT_VOCAB_PATH,
) -> np.ndarray:
    """Cosine similarity matrix between source and target node embeddings.

    Returns a ``(len(source_nodes), len(target_nodes))`` matrix in
    ``[-1, 1]``. Pairs where either side is not in the trained vocabulary
    get ``0.0``.
    """
    M, vocab = _load(str(embeddings_path), str(vocab_path))
    n_src, n_tgt = len(source_nodes), len(target_nodes)
    out = np.zeros((n_src, n_tgt), dtype=np.float64)
    src_idx = [vocab.get(s, -1) for s in source_nodes]
    tgt_idx = [vocab.get(t, -1) for t in target_nodes]
    for i, si in enumerate(src_idx):
        if si < 0:
            continue
        sv = M[si]
        for j, tj in enumerate(tgt_idx):
            if tj < 0:
                continue
            out[i, j] = float(sv @ M[tj])
    return out
