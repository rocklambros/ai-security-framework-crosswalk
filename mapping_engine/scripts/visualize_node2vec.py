"""Project Node2Vec embeddings to 2D for the Project 1 notebook.

Tries UMAP first, falls back to scikit-learn t-SNE if UMAP isn't
available. Writes a CSV with columns ``x, y, framework, node_id, name``
that the notebook can scatter-plot directly.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from mapping_engine.engine.graph import load_graph

REPO = Path(__file__).resolve().parents[2]


def _project(M: np.ndarray) -> np.ndarray:
    try:
        import umap

        reducer = umap.UMAP(n_components=2, random_state=42, n_neighbors=15, min_dist=0.1)
        return reducer.fit_transform(M)
    except Exception as e:
        print(f"UMAP unavailable ({e!s}); falling back to t-SNE")
        from sklearn.manifold import TSNE

        return TSNE(
            n_components=2, random_state=42, perplexity=30, init="pca"
        ).fit_transform(M)


def main() -> None:
    M = np.load(REPO / "data/processed/node2vec_embeddings.npy")
    vocab = json.loads((REPO / "data/processed/node2vec_vocab.json").read_text())
    G = load_graph(REPO / "data/processed/nodes.json", REPO / "data/processed/edges.json")

    print(f"Projecting {M.shape[0]} embeddings of dim {M.shape[1]} to 2D...")
    coords = _project(M.astype(np.float32))

    rows = []
    inv_vocab = {i: nid for nid, i in vocab.items()}
    for i in range(M.shape[0]):
        nid = inv_vocab[i]
        d = G.nodes.get(nid, {})
        rows.append(
            {
                "node_id": nid,
                "x": float(coords[i, 0]),
                "y": float(coords[i, 1]),
                "framework": d.get("framework", "unknown"),
                "entry_type": d.get("entry_type", ""),
                "name": (d.get("name") or "")[:120],
            }
        )
    df = pd.DataFrame(rows)
    out_path = REPO / "data" / "processed" / "node2vec_projection.csv"
    df.to_csv(out_path, index=False)
    print(f"Wrote {out_path}: {len(df)} points across {df.framework.nunique()} frameworks")


if __name__ == "__main__":
    main()
