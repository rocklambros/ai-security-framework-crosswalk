"""CORN — Conditional Ordinal Regression Network.

Decomposes K-class ordinal classification into K-1 binary classification tasks.
Task k: P(Y > k | Y >= k). This respects the ordinal structure:
  unrelated(0) < partial(1) < related(2) < equivalent(3)

Reference: Shi et al. "CORN — Conditional Ordinal Regression for Neural Networks" (2021)
"""
from __future__ import annotations

import torch
import torch.nn.functional as F


def corn_loss(
    logits: torch.Tensor,
    labels: torch.Tensor,
    n_classes: int = 4,
) -> torch.Tensor:
    """Compute CORN loss for ordinal regression.

    Args:
        logits: (batch, n_classes-1) raw logits for each binary task
        labels: (batch,) integer class labels in [0, n_classes-1]
        n_classes: Number of ordinal classes

    Returns:
        Scalar loss (mean over batch and tasks).
    """
    n_tasks = n_classes - 1
    total_loss = torch.tensor(0.0, device=logits.device)
    n_contributing = 0

    for task_idx in range(n_tasks):
        mask = labels >= task_idx
        if mask.sum() == 0:
            continue

        task_logits = logits[mask, task_idx]
        task_targets = (labels[mask] > task_idx).float()

        task_loss = F.binary_cross_entropy_with_logits(task_logits, task_targets)
        total_loss = total_loss + task_loss
        n_contributing += 1

    if n_contributing == 0:
        return torch.tensor(0.0, device=logits.device, requires_grad=True)

    return total_loss / n_contributing


def corn_label_from_logits(
    logits: torch.Tensor,
    n_classes: int = 4,
) -> torch.Tensor:
    """Convert CORN logits to class predictions."""
    probs = torch.sigmoid(logits)
    predictions = (probs > 0.5).sum(dim=1).long()
    return predictions.clamp(0, n_classes - 1)


def corn_proba_from_logits(
    logits: torch.Tensor,
    n_classes: int = 4,
) -> torch.Tensor:
    """Convert CORN logits to class probabilities.

    P(Y = k) computed from cumulative conditional probabilities.
    """
    probs = torch.sigmoid(logits)  # (batch, n_classes-1)
    batch_size = probs.shape[0]
    class_probs = torch.zeros(batch_size, n_classes, device=logits.device)

    cumulative = torch.ones(batch_size, device=logits.device)

    for k in range(n_classes):
        if k < n_classes - 1:
            class_probs[:, k] = cumulative * (1 - probs[:, k])
            cumulative = cumulative * probs[:, k]
        else:
            class_probs[:, k] = cumulative

    class_probs = class_probs.clamp(min=1e-8)
    class_probs = class_probs / class_probs.sum(dim=1, keepdim=True)

    return class_probs
