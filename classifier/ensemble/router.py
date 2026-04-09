"""KL-disagreement abstention router.

Emits needs_review when the stacker's class distribution disagrees with
a reference distribution (uniform or prior) beyond a threshold tau.

Tau is tuned on llm_val for >= 95% precision on the reviewed subset.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np


def kl_divergence(p: np.ndarray, q: np.ndarray, eps: float = 1e-10) -> np.ndarray:
    """KL(p || q) per row. p, q: (n, k)."""
    p = np.clip(p, eps, 1.0)
    q = np.clip(q, eps, 1.0)
    return np.sum(p * np.log(p / q), axis=1)


class DisagreementRouter:
    """KL-divergence abstention router."""

    def __init__(self, tau: float = 1.0, reference: str = "uniform"):
        self.tau = tau
        self.reference = reference
        self.n_classes = 4

    def _ref_dist(self, n: int) -> np.ndarray:
        if self.reference == "uniform":
            return np.full((n, self.n_classes), 1.0 / self.n_classes)
        raise ValueError(f"Unknown reference: {self.reference}")

    def score(self, proba: np.ndarray) -> np.ndarray:
        """Disagreement score: KL(proba || reference). Higher = more confident."""
        ref = self._ref_dist(len(proba))
        return kl_divergence(proba, ref)

    def route(self, proba: np.ndarray) -> np.ndarray:
        """Return boolean mask: True = needs_review (low confidence)."""
        scores = self.score(proba)
        return scores < self.tau

    def tune_tau(
        self,
        proba: np.ndarray,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        target_precision: float = 0.95,
    ) -> float:
        """Find tau that achieves >= target_precision on non-abstained predictions.

        Sweeps tau from high to low. At each threshold, predictions below tau
        are abstained. Precision is computed on the non-abstained subset.
        """
        scores = self.score(proba)
        correct = (y_pred == y_true).astype(float)

        # Sort by score descending (most confident first)
        order = np.argsort(-scores)
        sorted_correct = correct[order]
        sorted_scores = scores[order]

        best_tau = float(np.min(scores))  # default: abstain nothing
        cumsum = np.cumsum(sorted_correct)
        for i in range(1, len(sorted_correct) + 1):
            precision = cumsum[i - 1] / i
            if precision >= target_precision:
                best_tau = float(sorted_scores[i - 1])

        self.tau = best_tau
        return best_tau

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {"tau": self.tau, "reference": self.reference, "n_classes": self.n_classes}
        path.write_text(json.dumps(data, sort_keys=True, indent=2))

    @classmethod
    def load(cls, path: Path) -> "DisagreementRouter":
        data = json.loads(path.read_text())
        obj = cls(tau=data["tau"], reference=data["reference"])
        obj.n_classes = data.get("n_classes", 4)
        return obj
