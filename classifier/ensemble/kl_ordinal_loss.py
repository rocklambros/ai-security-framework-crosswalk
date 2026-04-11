"""KL-divergence loss with Gaussian ordinal soft targets.

Instead of predicting hard class labels, the model predicts a probability
distribution over the ordinal scale. The target distribution is a Gaussian
centered on the true label, which provides implicit supervision for adjacent
classes — crucially including classes with few or zero training examples.

Reference: Gao et al. 2017, "Deep Label Distribution Learning with
Label Ambiguity" (adapted for ordinal regression).
"""
from __future__ import annotations

import torch
import torch.nn.functional as F


def ordinal_soft_targets(
    labels: torch.Tensor,
    n_classes: int = 4,
    sigma: float = 0.75,
) -> torch.Tensor:
    """Build soft ordinal target distributions from integer labels.

    For label y, the target probability for class k is:
        t_k = exp(-(k - y)^2 / (2 * sigma^2)) / Z

    Args:
        labels: (batch_size,) integer labels in [0, n_classes)
        n_classes: number of ordinal classes
        sigma: Gaussian width controlling label smoothness

    Returns:
        (batch_size, n_classes) soft target probability matrix
    """
    device = labels.device
    k = torch.arange(n_classes, device=device, dtype=torch.float32).unsqueeze(0)
    y = labels.unsqueeze(1).float()
    log_probs = -((k - y) ** 2) / (2 * sigma ** 2)
    return F.softmax(log_probs, dim=1)


def kl_ordinal_loss(
    logits: torch.Tensor,
    labels: torch.Tensor,
    n_classes: int = 4,
    sigma: float = 0.75,
) -> torch.Tensor:
    """KL-divergence between predicted log-probs and ordinal soft targets.

    Args:
        logits: (batch_size, n_classes) raw model logits
        labels: (batch_size,) integer labels in [0, n_classes)
        n_classes: number of ordinal classes
        sigma: Gaussian width for soft targets

    Returns:
        Scalar loss (mean over batch)
    """
    targets = ordinal_soft_targets(labels, n_classes=n_classes, sigma=sigma)
    log_probs = F.log_softmax(logits, dim=1)
    return F.kl_div(log_probs, targets, reduction="batchmean")
