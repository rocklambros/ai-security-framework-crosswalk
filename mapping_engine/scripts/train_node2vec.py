"""Train Node2Vec embeddings on the crosswalk graph.

Design notes (Session 6)
------------------------
The crosswalk graph is small (983 nodes / 1883 edges, avg degree ~3.8)
which is at the lower bound of where Node2Vec produces useful
embeddings. We train it anyway as a *supplementary* signal — the bridge
signal already does 2-hop weighted Jaccard on the same graph and is
likely to capture most of the same structural information.

Choices:
* PARENT edges are excluded — they are within-framework hierarchy and
  produce trivial sibling-equivalence walks that drown out the cross-
  framework MAPS_TO signal we actually care about.
* Treat the remaining graph as **undirected**. A MAPS_TO from
  aiuc_1:B005 → owasp_agentic:ASI01 should put both nodes in each
  other's walk neighborhoods.
* Dimensions: 64 (small graph → small dim).
* Walks: 200 walks of length 30 per node (≈ 196k walks total).
* p=q=1 (balanced DFS/BFS) for the first run. The benchmark will tell
  us if structural-equivalence (p=0.5, q=2) is worth chasing.

Outputs::

    data/processed/node2vec_embeddings.npy   (n_nodes, dim) float32
    data/processed/node2vec_vocab.json       {node_id: row_index}
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import networkx as nx
import numpy as np

from mapping_engine.engine.graph import load_graph

REPO = Path(__file__).resolve().parents[2]
DIM = 64
WALK_LEN = 30
NUM_WALKS = 200
P = 1.0
Q = 1.0
WORKERS = 4
WINDOW = 10
SEED = 42


def _undirected_no_parent(G: nx.DiGraph) -> nx.Graph:
    H: nx.Graph = nx.Graph()
    H.add_nodes_from(G.nodes(data=True))
    for u, v, d in G.edges(data=True):
        if d.get("rationale_code") == "PARENT":
            continue
        if not H.has_edge(u, v):
            H.add_edge(u, v, weight=1.0)
    return H


def main() -> None:
    from node2vec import Node2Vec

    G = load_graph(REPO / "data/processed/nodes.json", REPO / "data/processed/edges.json")
    H = _undirected_no_parent(G)
    print(f"Graph for Node2Vec: {H.number_of_nodes()} nodes, {H.number_of_edges()} edges")

    t0 = time.perf_counter()
    n2v = Node2Vec(
        H,
        dimensions=DIM,
        walk_length=WALK_LEN,
        num_walks=NUM_WALKS,
        p=P,
        q=Q,
        workers=WORKERS,
        seed=SEED,
        quiet=True,
    )
    model = n2v.fit(window=WINDOW, min_count=1, batch_words=512, seed=SEED)
    t_train = time.perf_counter() - t0
    print(f"Training time: {t_train:.1f}s")

    # Build a stable (sorted) vocab and matrix
    vocab = {nid: i for i, nid in enumerate(sorted(H.nodes()))}
    M = np.zeros((len(vocab), DIM), dtype=np.float32)
    missing = 0
    for nid, idx in vocab.items():
        try:
            M[idx] = model.wv[nid]
        except KeyError:
            missing += 1
    print(f"Embeddings: {M.shape}  missing={missing}")
    print(f"  norms: mean={np.linalg.norm(M, axis=1).mean():.3f}  "
          f"std={np.linalg.norm(M, axis=1).std():.3f}")

    out_npy = REPO / "data" / "processed" / "node2vec_embeddings.npy"
    out_vocab = REPO / "data" / "processed" / "node2vec_vocab.json"
    np.save(out_npy, M)
    out_vocab.write_text(json.dumps(vocab))
    print(f"Wrote {out_npy}")
    print(f"Wrote {out_vocab}")


if __name__ == "__main__":
    main()
