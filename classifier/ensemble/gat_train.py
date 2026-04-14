"""Train GATv2 on the densified crosswalk graph via link prediction.

Converts the NetworkX densified graph to a PyG Data object, trains a GATv2
encoder with negative-sampling link prediction, and saves the learned
node embeddings.

Contract 5: Only reads frozen labels (v1_frozen or v2_frozen) via build_densified_graph.
"""
from __future__ import annotations

import json
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from pathlib import Path

from classifier.ensemble.graph import build_densified_graph
from classifier.ensemble.gat_model import GATEncoder


GAT_EMBEDDINGS_PATH = Path("data/features/gat_embeddings.npz")


def graph_to_pyg(G) -> dict:
    """Convert a NetworkX DiGraph to PyG-compatible tensors.

    Returns dict with:
      - node_ids: list of node_id strings (index → node_id mapping)
      - x: (n_nodes, feat_dim) initial features (one-hot framework + degree)
      - edge_index: (2, n_edges) tensor
    """
    node_ids = sorted(G.nodes())
    node_to_idx = {nid: i for i, nid in enumerate(node_ids)}

    # Build edge_index
    src_list, tgt_list = [], []
    for u, v in G.edges():
        if u in node_to_idx and v in node_to_idx:
            src_list.append(node_to_idx[u])
            tgt_list.append(node_to_idx[v])
    edge_index = torch.tensor([src_list, tgt_list], dtype=torch.long)

    # Build initial node features: one-hot framework encoding + log(degree+1)
    frameworks = sorted(set(G.nodes[n].get("framework", "") for n in node_ids))
    fw_to_idx = {fw: i for i, fw in enumerate(frameworks)}
    n_nodes = len(node_ids)
    n_fw = len(frameworks)

    x = torch.zeros(n_nodes, n_fw + 1)  # +1 for degree feature
    for i, nid in enumerate(node_ids):
        fw = G.nodes[nid].get("framework", "")
        if fw in fw_to_idx:
            x[i, fw_to_idx[fw]] = 1.0
        x[i, -1] = np.log1p(G.degree(nid))

    return {
        "node_ids": node_ids,
        "node_to_idx": node_to_idx,
        "x": x,
        "edge_index": edge_index,
        "n_nodes": n_nodes,
        "in_dim": x.shape[1],
    }


class LinkPredHead(nn.Module):
    """Simple dot-product link prediction head."""

    def forward(self, z: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        src, dst = edge_index
        return (z[src] * z[dst]).sum(dim=1)


def negative_sample(edge_index: torch.Tensor, n_nodes: int, n_neg: int) -> torch.Tensor:
    """Sample n_neg negative edges (not in edge_index)."""
    edge_set = set(zip(edge_index[0].tolist(), edge_index[1].tolist()))
    neg_src, neg_dst = [], []
    while len(neg_src) < n_neg:
        s = torch.randint(0, n_nodes, (n_neg * 2,))
        d = torch.randint(0, n_nodes, (n_neg * 2,))
        for si, di in zip(s.tolist(), d.tolist()):
            if si != di and (si, di) not in edge_set:
                neg_src.append(si)
                neg_dst.append(di)
                if len(neg_src) >= n_neg:
                    break
    return torch.tensor([neg_src[:n_neg], neg_dst[:n_neg]], dtype=torch.long)


def train_gat(
    hidden_dim: int = 64,
    out_dim: int = 32,
    heads: int = 4,
    num_layers: int = 2,
    dropout: float = 0.3,
    lr: float = 0.005,
    epochs: int = 200,
    seed: int = 20260408,
    device: str = "cuda" if torch.cuda.is_available() else "cpu",
) -> tuple[np.ndarray, list[str]]:
    """Train GATv2 and return (embeddings, node_ids).

    Returns:
        embeddings: (n_nodes, out_dim) numpy array
        node_ids: list of node_id strings
    """
    torch.manual_seed(seed)
    np.random.seed(seed)

    print("Building densified graph...")
    G = build_densified_graph()
    print(f"  Nodes: {G.number_of_nodes()}, Edges: {G.number_of_edges()}")

    print("Converting to PyG format...")
    data = graph_to_pyg(G)
    x = data["x"].to(device)
    edge_index = data["edge_index"].to(device)

    print(f"  Features: {data['in_dim']}, Nodes: {data['n_nodes']}, Edges: {edge_index.shape[1]}")

    # Build model
    encoder = GATEncoder(
        in_dim=data["in_dim"],
        hidden_dim=hidden_dim,
        out_dim=out_dim,
        heads=heads,
        num_layers=num_layers,
        dropout=dropout,
    ).to(device)
    pred_head = LinkPredHead().to(device)
    optimizer = torch.optim.Adam(encoder.parameters(), lr=lr, weight_decay=1e-4)

    print(f"\nTraining GAT ({epochs} epochs, device={device})...")
    encoder.train()
    best_loss = float("inf")
    patience_counter = 0
    patience = 30

    for epoch in range(1, epochs + 1):
        optimizer.zero_grad()

        z = encoder(x, edge_index)

        # Positive edges
        pos_score = pred_head(z, edge_index)
        pos_label = torch.ones_like(pos_score)

        # Negative sampling
        neg_edge = negative_sample(edge_index, data["n_nodes"], edge_index.shape[1]).to(device)
        neg_score = pred_head(z, neg_edge)
        neg_label = torch.zeros_like(neg_score)

        # Binary cross-entropy loss
        scores = torch.cat([pos_score, neg_score])
        labels = torch.cat([pos_label, neg_label])
        loss = F.binary_cross_entropy_with_logits(scores, labels)

        loss.backward()
        optimizer.step()

        if epoch % 20 == 0 or epoch == 1:
            with torch.no_grad():
                acc = ((scores > 0).float() == labels).float().mean().item()
            print(f"  Epoch {epoch:3d}: loss={loss.item():.4f}, acc={acc:.4f}")

        # Early stopping
        if loss.item() < best_loss - 1e-4:
            best_loss = loss.item()
            patience_counter = 0
        else:
            patience_counter += 1
            if patience_counter >= patience:
                print(f"  Early stopping at epoch {epoch}")
                break

    # Extract embeddings
    encoder.eval()
    with torch.no_grad():
        embeddings = encoder(x, edge_index).cpu().numpy()

    print(f"\nEmbeddings shape: {embeddings.shape}")
    return embeddings, data["node_ids"]


def save_embeddings(
    embeddings: np.ndarray,
    node_ids: list[str],
    path: Path = GAT_EMBEDDINGS_PATH,
) -> None:
    """Save node embeddings to npz file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        path,
        embeddings=embeddings,
        node_ids=np.array(node_ids),
    )
    print(f"Saved embeddings to {path}")


def load_embeddings(path: Path = GAT_EMBEDDINGS_PATH) -> tuple[np.ndarray, list[str]]:
    """Load node embeddings from npz file."""
    data = np.load(path, allow_pickle=True)
    return data["embeddings"], data["node_ids"].tolist()


def compute_pair_gat_scores(
    pairs: list[dict],
    embeddings: np.ndarray,
    node_ids: list[str],
) -> np.ndarray:
    """Compute cosine similarity between source and target GAT embeddings.

    Returns (n_pairs,) array of cosine similarities.
    """
    node_to_idx = {nid: i for i, nid in enumerate(node_ids)}
    scores = np.zeros(len(pairs))

    for i, r in enumerate(pairs):
        src = f"{r['source_framework']}:{r['source_id']}"
        tgt = r["target_node_id"]

        if src in node_to_idx and tgt in node_to_idx:
            emb_src = embeddings[node_to_idx[src]]
            emb_tgt = embeddings[node_to_idx[tgt]]
            norm_src = np.linalg.norm(emb_src)
            norm_tgt = np.linalg.norm(emb_tgt)
            if norm_src > 0 and norm_tgt > 0:
                scores[i] = float(np.dot(emb_src, emb_tgt) / (norm_src * norm_tgt))

    return scores


if __name__ == "__main__":
    embeddings, node_ids = train_gat()
    save_embeddings(embeddings, node_ids)
    print("Done.")
