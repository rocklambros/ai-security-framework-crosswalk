"""GAT training wrapper for v8 pipeline integration.

Wraps classifier.ensemble.gat_train.train_gat() with output path arguments.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import numpy as np


def train_gat(
    output_dir: str = "runs/v8/gat",
    embeddings_output: str = "data/features/gat_embeddings_v8.npz",
    hidden_dim: int = 64,
    epochs: int = 200,
    lr: float = 0.005,
) -> Dict[str, Any]:
    """Train GATv2 and save embeddings to the specified output path."""
    from classifier.ensemble.gat_train import train_gat as _train_gat

    embeddings, node_ids = _train_gat(
        hidden_dim=hidden_dim,
        epochs=epochs,
        lr=lr,
    )

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    out_path = Path(embeddings_output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez(str(out_path), embeddings=embeddings, node_ids=node_ids)
    print(f"  [gat_trainer] saved {embeddings.shape} embeddings -> {out_path}")

    return {
        "status": "trained",
        "emb_shape": list(embeddings.shape),
        "n_nodes": len(node_ids),
        "output_path": str(out_path),
    }
