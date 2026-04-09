"""Tests for CORN (Conditional Ordinal Regression Network) loss."""
import torch
import pytest
from classifier.ensemble.corn_loss import corn_loss, corn_label_from_logits


def test_corn_loss_shape():
    logits = torch.randn(8, 3)  # batch=8, n_classes-1=3 binary tasks
    labels = torch.tensor([0, 1, 2, 3, 0, 1, 2, 3])
    loss = corn_loss(logits, labels, n_classes=4)
    assert loss.shape == ()
    assert loss.item() > 0


def test_corn_loss_perfect_predictions():
    logits = torch.tensor([[10.0, 10.0, 10.0]])  # predict class 3
    labels = torch.tensor([3])
    loss_correct = corn_loss(logits, labels, n_classes=4)

    logits_wrong = torch.tensor([[-10.0, -10.0, -10.0]])  # predict class 0
    loss_wrong = corn_loss(logits_wrong, labels, n_classes=4)

    assert loss_correct < loss_wrong


def test_corn_label_from_logits():
    logits = torch.tensor([[10.0, 10.0, 10.0]])
    labels = corn_label_from_logits(logits, n_classes=4)
    assert labels[0].item() == 3

    logits = torch.tensor([[-10.0, -10.0, -10.0]])
    labels = corn_label_from_logits(logits, n_classes=4)
    assert labels[0].item() == 0

    logits = torch.tensor([[10.0, -10.0, -10.0]])
    labels = corn_label_from_logits(logits, n_classes=4)
    assert labels[0].item() == 1
