"""Graph-structural features for crosswalk pair classification.

Feature layout (301 features per pair):
  [0:32]    GAT source embedding
  [32:64]   GAT target embedding
  [64:96]   GAT element-wise abs difference
  [96:100]  GAT scalar: cosine similarity, L2 distance, dot product, hadamard sum
  [100:164] Node2Vec source embedding
  [164:228] Node2Vec target embedding
  [228:292] Node2Vec element-wise abs difference
  [292:296] Node2Vec scalar: cosine, L2, dot, hadamard sum
  [296]     Shortest path length (undirected; 0 if unreachable)
  [297]     Common neighbors count
  [298]     Same framework (binary)
  [299]     Has direct edge (binary)
  [300]     Jaccard coefficient
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

import networkx as nx
import numpy as np

# ---------------------------------------------------------------------------
# Paths (relative to project root, resolved at import time)
# ---------------------------------------------------------------------------
_ROOT = Path(__file__).resolve().parents[2]
_GAT_PATH = _ROOT / "data" / "features" / "gat_embeddings.npz"
_N2V_EMB_PATH = _ROOT / "data" / "processed" / "node2vec_embeddings.npy"
_N2V_VOC_PATH = _ROOT / "data" / "processed" / "node2vec_vocab.json"
_NODES_PATH = _ROOT / "data" / "processed" / "nodes.json"
_EDGES_PATH = _ROOT / "data" / "processed" / "edges.json"

# Embedding dimensions — validated on load
_GAT_DIM = 32
_N2V_DIM = 64


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------

def load_embeddings() -> tuple[Dict[str, np.ndarray], Dict[str, np.ndarray]]:
    """Load GAT and Node2Vec embeddings.

    Returns
    -------
    gat_dict : dict[str, np.ndarray]
        Maps node_id -> float32 array of shape (32,).
    n2v_dict : dict[str, np.ndarray]
        Maps node_id -> float32 array of shape (64,).
    """
    # GAT embeddings
    gat_data = np.load(_GAT_PATH)
    node_ids: np.ndarray = gat_data["node_ids"]
    embeddings: np.ndarray = gat_data["embeddings"].astype(np.float32)
    gat_dict: Dict[str, np.ndarray] = {
        str(nid): embeddings[i] for i, nid in enumerate(node_ids)
    }

    # Node2Vec embeddings — vocab is a dict mapping node_id -> int index
    n2v_emb = np.load(_N2V_EMB_PATH).astype(np.float32)
    with open(_N2V_VOC_PATH) as fh:
        n2v_vocab: Dict[str, int] = json.load(fh)
    n2v_dict: Dict[str, np.ndarray] = {
        node_id: n2v_emb[idx] for node_id, idx in n2v_vocab.items()
    }

    return gat_dict, n2v_dict


def load_graph() -> nx.DiGraph:
    """Build a directed graph from nodes.json + edges.json.

    Returns
    -------
    nx.DiGraph
        Nodes carry ``framework`` and ``name`` attributes.
        Edges carry ``rationale_code`` and ``confidence`` attributes.
    """
    with open(_NODES_PATH) as fh:
        nodes: List[dict] = json.load(fh)
    with open(_EDGES_PATH) as fh:
        edges: List[dict] = json.load(fh)

    G = nx.DiGraph()

    for node in nodes:
        G.add_node(
            node["node_id"],
            framework=node.get("framework", ""),
            name=node.get("name", ""),
        )

    for edge in edges:
        G.add_edge(
            edge["source_node_id"],
            edge["target_node_id"],
            rationale_code=edge.get("rationale_code", ""),
            confidence=edge.get("confidence", ""),
        )

    return G


# ---------------------------------------------------------------------------
# Feature helpers
# ---------------------------------------------------------------------------

def _scalar_features(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Return [cosine_sim, L2_distance, dot_product, hadamard_sum] for two vectors."""
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a > 0 and norm_b > 0:
        cosine = float(np.dot(a, b) / (norm_a * norm_b))
    else:
        cosine = 0.0
    l2 = float(np.linalg.norm(a - b))
    dot = float(np.dot(a, b))
    hadamard_sum = float(np.sum(a * b))
    return np.array([cosine, l2, dot, hadamard_sum], dtype=np.float32)


# ---------------------------------------------------------------------------
# Main feature computation
# ---------------------------------------------------------------------------

def compute_pair_features(
    pairs: List[dict],
    gat_dict: Dict[str, np.ndarray],
    n2v_dict: Dict[str, np.ndarray],
    graph: nx.DiGraph,
) -> np.ndarray:
    """Compute a (n_pairs, 301) float32 feature matrix.

    Parameters
    ----------
    pairs :
        List of pair dicts, each with at least ``source_id`` / ``source_node_id``
        and ``target_id`` / ``target_node_id`` keys.
    gat_dict :
        Output of :func:`load_embeddings` — GAT vectors keyed by node_id.
    n2v_dict :
        Output of :func:`load_embeddings` — Node2Vec vectors keyed by node_id.
    graph :
        Output of :func:`load_graph`.

    Returns
    -------
    np.ndarray of shape (n_pairs, 301), dtype float32.
    """
    _ZERO_GAT = np.zeros(_GAT_DIM, dtype=np.float32)
    _ZERO_N2V = np.zeros(_N2V_DIM, dtype=np.float32)

    G_undirected = graph.to_undirected()

    n = len(pairs)
    X = np.zeros((n, 301), dtype=np.float32)

    for i, pair in enumerate(pairs):
        src = pair.get("source_id") or pair.get("source_node_id", "")
        tgt = pair.get("target_id") or pair.get("target_node_id", "")

        # -- GAT embeddings --------------------------------------------------
        gat_src = gat_dict.get(src, _ZERO_GAT)
        gat_tgt = gat_dict.get(tgt, _ZERO_GAT)
        X[i, 0:32] = gat_src
        X[i, 32:64] = gat_tgt
        X[i, 64:96] = np.abs(gat_src - gat_tgt)
        X[i, 96:100] = _scalar_features(gat_src, gat_tgt)

        # -- Node2Vec embeddings ---------------------------------------------
        n2v_src = n2v_dict.get(src, _ZERO_N2V)
        n2v_tgt = n2v_dict.get(tgt, _ZERO_N2V)
        X[i, 100:164] = n2v_src
        X[i, 164:228] = n2v_tgt
        X[i, 228:292] = np.abs(n2v_src - n2v_tgt)
        X[i, 292:296] = _scalar_features(n2v_src, n2v_tgt)

        # -- Structural features ---------------------------------------------
        # Shortest path (undirected)
        if G_undirected.has_node(src) and G_undirected.has_node(tgt):
            try:
                sp = nx.shortest_path_length(G_undirected, src, tgt)
            except nx.NetworkXNoPath:
                sp = 0
        else:
            sp = 0
        X[i, 296] = float(sp)

        # Common neighbors
        if G_undirected.has_node(src) and G_undirected.has_node(tgt):
            common = len(
                set(G_undirected.neighbors(src)) & set(G_undirected.neighbors(tgt))
            )
        else:
            common = 0
        X[i, 297] = float(common)

        # Same framework
        src_fw = pair.get("source_framework", "")
        if not src_fw and graph.has_node(src):
            src_fw = graph.nodes[src].get("framework", "")
        tgt_fw = pair.get("target_framework", "")
        if not tgt_fw and graph.has_node(tgt):
            tgt_fw = graph.nodes[tgt].get("framework", "")
        X[i, 298] = float(bool(src_fw and tgt_fw and src_fw == tgt_fw))

        # Has direct edge
        X[i, 299] = float(graph.has_edge(src, tgt) or graph.has_edge(tgt, src))

        # Jaccard coefficient
        if G_undirected.has_node(src) and G_undirected.has_node(tgt):
            nbrs_src = set(G_undirected.neighbors(src))
            nbrs_tgt = set(G_undirected.neighbors(tgt))
            union = len(nbrs_src | nbrs_tgt)
            intersection = len(nbrs_src & nbrs_tgt)
            jaccard = intersection / union if union > 0 else 0.0
        else:
            jaccard = 0.0
        X[i, 300] = float(jaccard)

    return X
