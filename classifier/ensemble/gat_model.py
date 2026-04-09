"""GATv2 encoder for link-prediction on the densified crosswalk graph.

Requires torch_geometric — tests skip on Jetson via importorskip.
Training runs on Lambda A100.
"""
from __future__ import annotations

import torch
import torch.nn as nn

try:
    from torch_geometric.nn import GATv2Conv
    HAS_PYG = True
except ImportError:
    HAS_PYG = False


class GATEncoder(nn.Module):
    """GATv2 encoder producing per-node embeddings.

    Args:
        in_dim: Input feature dimension.
        hidden_dim: Hidden dimension per head.
        out_dim: Output embedding dimension.
        heads: Number of attention heads.
        num_layers: Number of GATv2 layers.
        dropout: Dropout rate.
    """

    def __init__(
        self,
        in_dim: int = 64,
        hidden_dim: int = 128,
        out_dim: int = 64,
        heads: int = 4,
        num_layers: int = 2,
        dropout: float = 0.1,
    ):
        super().__init__()
        if not HAS_PYG:
            raise ImportError(
                "torch_geometric not installed. GAT training requires Lambda A100. "
                "Install: pip install torch-geometric torch-scatter torch-sparse"
            )
        self.dropout = dropout
        self.convs = nn.ModuleList()
        self.norms = nn.ModuleList()

        # First layer
        self.convs.append(GATv2Conv(in_dim, hidden_dim, heads=heads, dropout=dropout, concat=True))
        self.norms.append(nn.LayerNorm(hidden_dim * heads))

        # Middle layers
        for _ in range(num_layers - 2):
            self.convs.append(GATv2Conv(hidden_dim * heads, hidden_dim, heads=heads, dropout=dropout, concat=True))
            self.norms.append(nn.LayerNorm(hidden_dim * heads))

        # Final layer — concat=False to get out_dim
        self.convs.append(GATv2Conv(hidden_dim * heads, out_dim, heads=1, dropout=dropout, concat=False))
        self.norms.append(nn.LayerNorm(out_dim))

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        for i, (conv, norm) in enumerate(zip(self.convs, self.norms)):
            x = conv(x, edge_index)
            x = norm(x)
            if i < len(self.convs) - 1:
                x = torch.relu(x)
                x = torch.dropout(x, p=self.dropout, train=self.training)
        return x
