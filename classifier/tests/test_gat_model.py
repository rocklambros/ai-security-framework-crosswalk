"""Tests for GAT encoder. Skip if torch_geometric not available (Jetson)."""
import torch
import pytest

pyg = pytest.importorskip("torch_geometric")
from torch_geometric.data import Data  # noqa: E402
from classifier.ensemble.gat_model import GATEncoder  # noqa: E402


def test_forward_shape():
    x = torch.randn(10, 64)
    edge_index = torch.tensor(
        [[0, 1, 2, 3, 4, 5, 6, 7, 8], [1, 2, 3, 4, 5, 6, 7, 8, 0]],
        dtype=torch.long,
    )
    enc = GATEncoder(in_dim=64, hidden_dim=128, out_dim=64, heads=4, num_layers=2, dropout=0.1)
    z = enc(x, edge_index)
    assert z.shape == (10, 64)
    assert z.requires_grad


def test_backward_flow():
    enc = GATEncoder(in_dim=32, hidden_dim=64, out_dim=32, heads=2, num_layers=2)
    x = torch.randn(8, 32, requires_grad=True)
    edge_index = torch.tensor(
        [[0, 1, 2, 3, 4, 5, 6], [1, 2, 3, 4, 5, 6, 0]], dtype=torch.long
    )
    z = enc(x, edge_index)
    loss = z.sum()
    loss.backward()
    assert x.grad is not None
    assert x.grad.shape == (8, 32)
