"""Black-box label shift correction (Lipton et al. 2018).

When the class distribution P(Y) changes between training and deployment
but the conditional P(X|Y) stays roughly the same, we can adjust the
predicted probabilities using Bayes' rule:

    P_target(Y=k|X) ∝ P_source(Y=k|X) × [P_target(Y=k) / P_source(Y=k)]

This is the simplest form of domain adaptation that requires only
knowledge of the target class prior (estimable from a small calibration set).
"""
from __future__ import annotations

import numpy as np


def estimate_prior(labels: np.ndarray, n_classes: int = 4) -> np.ndarray:
    """Estimate class prior from label array with Laplace smoothing."""
    counts = np.bincount(labels, minlength=n_classes).astype(float)
    counts += 1.0
    return counts / counts.sum()


def adjust_label_shift(
    proba: np.ndarray,
    source_prior: np.ndarray,
    target_prior: np.ndarray,
    epsilon: float = 1e-6,
) -> np.ndarray:
    """Adjust predicted probabilities for label shift.

    Args:
        proba: (n, n_classes) predicted probabilities from source model
        source_prior: (n_classes,) class prior in source/training domain
        target_prior: (n_classes,) class prior in target/test domain
        epsilon: floor for source prior to avoid division by zero

    Returns:
        (n, n_classes) adjusted probabilities (rows sum to 1)
    """
    source_safe = np.maximum(source_prior, epsilon)
    ratio = target_prior / source_safe

    adjusted = proba * ratio[np.newaxis, :]

    row_sums = adjusted.sum(axis=1, keepdims=True)
    row_sums = np.where(row_sums == 0, 1.0, row_sums)
    return adjusted / row_sums
