"""Mondrian split-conformal wrapper.

Per-tier calibration on human_cal at alpha=0.10. Each tier gets its own
q_hat threshold. At inference, the conformal set includes all classes
whose softmax probability exceeds the tier-specific q_hat.

Contract 9: Only calibrates on human_cal.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np


class MondrianConformal:
    """Per-tier Mondrian split-conformal prediction sets."""

    def __init__(self, alpha: float = 0.10):
        self.alpha = alpha
        self.q_hat: dict[int, float] = {}
        self.coverage: dict[int, float] = {}

    def calibrate(
        self,
        proba: np.ndarray,
        y_true: np.ndarray,
    ) -> "MondrianConformal":
        """Calibrate q_hat per tier on calibration data.

        Args:
            proba: (n, n_classes) softmax probabilities from the stacker
            y_true: (n,) true tier labels (0=unrelated, 1=partial, 2=related, 3=equivalent)
        """
        for tier in sorted(set(y_true)):
            mask = y_true == tier
            if mask.sum() == 0:
                continue
            # Nonconformity score = 1 - P(true class)
            scores = 1.0 - proba[mask, tier]
            n_cal = len(scores)
            # Quantile with finite-sample correction
            q_level = np.ceil((n_cal + 1) * (1 - self.alpha)) / n_cal
            q_level = min(q_level, 1.0)
            self.q_hat[int(tier)] = float(np.quantile(scores, q_level))
            # Empirical coverage
            pred_sets = self._predict_sets_single_tier(proba[mask], tier)
            hits = sum(1 for ps, yt in zip(pred_sets, y_true[mask]) if yt in ps)
            self.coverage[int(tier)] = hits / n_cal

        return self

    def _predict_sets_single_tier(self, proba: np.ndarray, tier: int) -> list[set]:
        q = self.q_hat.get(tier, 0.5)
        sets = []
        for row in proba:
            s = {c for c, p in enumerate(row) if 1 - p <= q}
            if not s:
                s = {int(np.argmax(row))}
            sets.append(s)
        return sets

    def predict_sets(self, proba: np.ndarray, tier_hints: np.ndarray | None = None) -> list[set]:
        """Predict conformal sets.

        If tier_hints are provided, use per-tier q_hat.
        Otherwise, use the q_hat for the most-probable class.
        """
        sets = []
        for i, row in enumerate(proba):
            if tier_hints is not None:
                tier = int(tier_hints[i])
            else:
                tier = int(np.argmax(row))
            q = self.q_hat.get(tier, max(self.q_hat.values()) if self.q_hat else 0.5)
            s = {c for c, p in enumerate(row) if 1 - p <= q}
            if not s:
                s = {int(np.argmax(row))}
            sets.append(s)
        return sets

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "alpha": self.alpha,
            "q_hat": {str(k): v for k, v in self.q_hat.items()},
            "coverage": {str(k): v for k, v in self.coverage.items()},
        }
        path.write_text(json.dumps(data, sort_keys=True, indent=2))

    @classmethod
    def load(cls, path: Path) -> "MondrianConformal":
        data = json.loads(path.read_text())
        obj = cls(alpha=data["alpha"])
        obj.q_hat = {int(k): v for k, v in data["q_hat"].items()}
        obj.coverage = {int(k): v for k, v in data.get("coverage", {}).items()}
        return obj

    def check_coverage(self, tolerance: float = 0.03) -> None:
        """Stop-gate: raise if any tier coverage deviates from target by > tolerance."""
        target = 1.0 - self.alpha
        for tier, cov in self.coverage.items():
            if abs(cov - target) > tolerance:
                raise SystemExit(
                    f"conformal coverage OOB for tier {tier}: "
                    f"{cov:.3f} vs target {target:.3f} (tolerance ±{tolerance})"
                )
