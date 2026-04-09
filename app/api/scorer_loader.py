"""Load the LightGBM stacker, conformal wrapper, and router from a run directory."""
from __future__ import annotations

from pathlib import Path

import numpy as np

from classifier.ensemble.stacker import LGBMStacker, FEATURE_COLS, N_CLASSES
from classifier.ensemble.conformal import MondrianConformal
from classifier.ensemble.router import DisagreementRouter

TIER_LABELS = {0: "unrelated", 1: "partial", 2: "related", 3: "equivalent"}


class Scorer:
    """Thin wrapper around stacker + conformal + router for single-pair prediction."""

    def __init__(
        self,
        stacker: LGBMStacker,
        conformal: MondrianConformal,
        router: DisagreementRouter,
    ):
        self.stacker = stacker
        self.conformal = conformal
        self.router = router
        self.feature_cols = FEATURE_COLS

    def predict(self, features_dict: dict) -> dict:
        """Predict tier, confidence, and conformal set for a single pair.

        Args:
            features_dict: mapping of feature name -> float value.
                           Missing features default to 0.0.

        Returns:
            {"tier": str, "confidence": float, "conformal_set": list[str],
             "needs_review": bool}
        """
        x = np.array(
            [[features_dict.get(col, 0.0) for col in self.feature_cols]]
        )
        proba = self.stacker.predict_proba(x)  # (1, N_CLASSES)
        pred_class = int(np.argmax(proba[0]))
        confidence = float(proba[0, pred_class])

        conformal_sets = self.conformal.predict_sets(proba)
        conformal_labels = sorted(
            [TIER_LABELS[c] for c in conformal_sets[0]]
        )

        needs_review = bool(self.router.route(proba)[0])

        return {
            "tier": TIER_LABELS[pred_class],
            "confidence": round(confidence, 4),
            "conformal_set": conformal_labels,
            "needs_review": needs_review,
        }


def load_scorer(run_dir: str | Path) -> Scorer:
    """Load a Scorer from a stacker run directory.

    Expects the directory to contain: model.txt, conformal.json, router.json.
    """
    run_dir = Path(run_dir)
    stacker = LGBMStacker.load(run_dir / "model.txt")
    conformal = MondrianConformal.load(run_dir / "conformal.json")
    router = DisagreementRouter.load(run_dir / "router.json")
    return Scorer(stacker, conformal, router)
