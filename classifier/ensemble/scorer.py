"""EnsembleScorer — wraps stacker + conformal + router into Plan 3 Scorer protocol.

This is the single registered scorer consumed by Plan 6 (sacred run) and
Plan 7 (Dash app). It scores a batch of NodePairs and returns ScoreRecords
with tier predictions, conformal sets, and needs_review flags.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from classifier.baselines.protocol import NodePair, ScoreRecord, Scorer
from classifier.ensemble.stacker import LGBMStacker, FEATURE_COLS
from classifier.ensemble.conformal import MondrianConformal
from classifier.ensemble.router import DisagreementRouter


TIER_NAMES = {0: "unrelated", 1: "partial", 2: "related", 3: "equivalent"}


class EnsembleScorer:
    """Plan 3 Scorer implementation wrapping the Plan 5 ensemble."""

    name = "ensemble_v1"

    def __init__(
        self,
        stacker: LGBMStacker,
        conformal: MondrianConformal,
        router: DisagreementRouter,
        version: str = "0.0.0",
        feature_fn=None,
    ):
        self.stacker = stacker
        self.conformal = conformal
        self.router = router
        self.version = version
        self._feature_fn = feature_fn

    def score(self, pairs: list[NodePair]) -> list[ScoreRecord]:
        """Score pairs per Plan 3 Scorer protocol.

        Requires self._feature_fn to be set — a callable that takes
        a list of NodePairs and returns (n, len(FEATURE_COLS)) array.
        """
        if self._feature_fn is None:
            raise ValueError(
                "EnsembleScorer requires a feature_fn. Set it via "
                "scorer._feature_fn = your_feature_extractor"
            )
        X = self._feature_fn(pairs)
        return self._score_from_features(pairs, X)

    def _score_from_features(
        self, pairs: list[NodePair], X: np.ndarray
    ) -> list[ScoreRecord]:
        """Score from a pre-built feature matrix."""
        proba = self.stacker.predict_proba(X)
        pred_classes = np.argmax(proba, axis=1)
        max_probs = proba[np.arange(len(proba)), pred_classes]
        conf_sets = self.conformal.predict_sets(proba)
        review_mask = self.router.route(proba)

        records = []
        for i, pair in enumerate(pairs):
            tier_probs = {
                TIER_NAMES[c]: float(proba[i, c]) for c in range(proba.shape[1])
            }
            records.append(ScoreRecord(
                pair_key=pair.pair_key,
                scorer_name=self.name,
                scorer_version=self.version,
                score=float(max_probs[i]),
                tier_pred=TIER_NAMES[int(pred_classes[i])],
                tier_probs=tier_probs,
                extras={
                    "conformal_set": [TIER_NAMES[c] for c in sorted(conf_sets[i])],
                    "needs_review": bool(review_mask[i]),
                },
            ))
        return records

    def score_features(self, pairs: list[NodePair], X: np.ndarray) -> list[ScoreRecord]:
        """Public convenience for scoring from pre-built features."""
        return self._score_from_features(pairs, X)

    @classmethod
    def from_run_dir(cls, run_dir: str | Path) -> "EnsembleScorer":
        """Load from a saved ensemble run directory."""
        run_dir = Path(run_dir)
        config = json.loads((run_dir / "scorer.json").read_text())
        stacker = LGBMStacker.load(Path(config["stacker_path"]))
        conformal = MondrianConformal.load(Path(config["conformal_path"]))
        router = DisagreementRouter.load(Path(config["router_path"]))
        return cls(
            stacker=stacker,
            conformal=conformal,
            router=router,
            version=config.get("version", "0.0.0"),
        )
