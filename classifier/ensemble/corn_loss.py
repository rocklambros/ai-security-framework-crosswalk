"""CORN ordinal loss for multi-class ordinal regression.

References:
    Shi et al. (2022) "Deep Neural Networks for Rank-Consistent Ordinal
    Regression based on Conditional Probabilities"
    https://arxiv.org/abs/2111.08851
"""
from __future__ import annotations

import torch
import torch.nn.functional as F


def corn_loss(
    logits: torch.Tensor,
    labels: torch.Tensor,
    n_classes: int,
) -> torch.Tensor:
    """CORN pairwise ordinal cross-entropy loss.

    Parameters
    ----------
    logits:
        Raw classifier outputs, shape (batch, n_classes - 1).
    labels:
        Integer class labels in [0, n_classes - 1], shape (batch,).
    n_classes:
        Total number of ordinal classes.

    Returns
    -------
    Scalar loss tensor.
    """
    n_tasks = n_classes - 1
    loss = torch.zeros(1, device=logits.device, dtype=logits.dtype)

    for task in range(n_tasks):
        # Keep only samples whose true label >= task (i.e., still "in play")
        mask = labels > (task - 1)
        if mask.sum() == 0:
            continue
        task_logits = logits[mask, task]
        # Binary label: 1 if the sample's class is strictly > task threshold
        task_labels = (labels[mask] > task).float()
        loss += F.binary_cross_entropy_with_logits(task_logits, task_labels)

    return loss / n_tasks


def corn_label_from_logits(logits: torch.Tensor) -> torch.Tensor:
    """Predicted ordinal class from CORN logits.

    Parameters
    ----------
    logits:
        Shape (batch, n_classes - 1).

    Returns
    -------
    Integer class predictions, shape (batch,).
    """
    probs = torch.sigmoid(logits)
    # Predicted class = number of binary tasks where p >= 0.5
    return probs.ge(0.5).sum(dim=1)


def corn_proba_from_logits(
    logits: torch.Tensor,
    n_classes: int,
) -> torch.Tensor:
    """Full class probability distribution from CORN logits.

    Parameters
    ----------
    logits:
        Shape (batch, n_classes - 1).
    n_classes:
        Total number of ordinal classes.

    Returns
    -------
    Probability matrix, shape (batch, n_classes), rows sum to 1.
    """
    probs = torch.sigmoid(logits)  # (batch, n_classes-1)
    batch = logits.shape[0]
    class_probs = torch.zeros(batch, n_classes, device=logits.device, dtype=logits.dtype)

    # P(Y = 0) = 1 - P(Y > 0)
    class_probs[:, 0] = 1.0 - probs[:, 0]

    # P(Y = k) = P(Y > k-1) * (1 - P(Y > k))  for 1 <= k < n_classes-1
    for k in range(1, n_classes - 1):
        class_probs[:, k] = probs[:, k - 1] * (1.0 - probs[:, k])

    # P(Y = n_classes-1) = P(Y > n_classes-2)
    class_probs[:, n_classes - 1] = probs[:, n_classes - 2]

    return class_probs
