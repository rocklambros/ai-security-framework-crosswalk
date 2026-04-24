"""Focal loss for class-imbalanced classification.

Downweights easy (well-classified) examples and focuses on hard ones.
With gamma=0, reduces to standard cross-entropy.

Reference: Lin et al. "Focal Loss for Dense Object Detection" (2017)
"""
from __future__ import annotations

import torch
import torch.nn.functional as F


def focal_loss(
    logits: torch.Tensor,
    labels: torch.Tensor,
    n_classes: int = 4,
    gamma: float = 2.0,
    alpha: torch.Tensor | None = None,
) -> torch.Tensor:
    probs = F.softmax(logits, dim=1)
    labels_onehot = F.one_hot(labels, num_classes=n_classes).float()
    pt = (probs * labels_onehot).sum(dim=1)
    pt = pt.clamp(min=1e-8)

    focal_weight = (1.0 - pt) ** gamma
    ce = -torch.log(pt)

    loss = focal_weight * ce

    if alpha is not None:
        if not isinstance(alpha, torch.Tensor):
            alpha = torch.tensor(alpha, device=logits.device, dtype=torch.float32)
        alpha = alpha.to(logits.device)
        alpha_t = alpha[labels]
        loss = alpha_t * loss

    return loss.mean()
