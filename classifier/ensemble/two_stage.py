# classifier/ensemble/two_stage.py
"""Two-stage classifier: binary filter -> ordinal classifier.

Stage 1: Binary (mapped vs unmapped) with high-recall threshold
Stage 2: Ordinal (equivalent/partial/related) on positives only
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import lightgbm as lgb
import numpy as np
from sklearn.metrics import precision_recall_curve


class TwoStageClassifier:
    """Two-stage LightGBM classifier with high-recall binary filter."""

    def __init__(
        self,
        stage1_recall_target: float = 0.95,
        stage1_params: Optional[dict] = None,
        stage2_params: Optional[dict] = None,
    ):
        self.stage1_recall_target = stage1_recall_target
        self.stage1_params = stage1_params or {
            "objective": "binary", "metric": "binary_logloss",
            "num_leaves": 31, "learning_rate": 0.05, "n_estimators": 200, "verbose": -1,
        }
        self.stage2_params = stage2_params or {
            "objective": "multiclass", "num_class": 3, "metric": "multi_logloss",
            "num_leaves": 31, "learning_rate": 0.05, "n_estimators": 200, "verbose": -1,
        }
        self.stage1_model: Optional[lgb.LGBMClassifier] = None
        self.stage2_model: Optional[lgb.LGBMClassifier] = None
        self.stage1_threshold: float = 0.5

    def fit(self, X: np.ndarray, y: np.ndarray) -> "TwoStageClassifier":
        y_binary = (y > 0).astype(int)
        self.stage1_model = lgb.LGBMClassifier(**self.stage1_params)
        self.stage1_model.fit(X, y_binary)

        proba_binary = self.stage1_model.predict_proba(X)[:, 1]
        precision, recall, thresholds = precision_recall_curve(y_binary, proba_binary)
        for i, r in enumerate(recall):
            if r >= self.stage1_recall_target and i < len(thresholds):
                self.stage1_threshold = float(thresholds[i])
                break
        else:
            self.stage1_threshold = 0.1

        mapped_mask = y > 0
        X_mapped = X[mapped_mask]
        y_mapped = y[mapped_mask] - 1

        self.stage2_model = lgb.LGBMClassifier(**self.stage2_params)
        self.stage2_model.fit(X_mapped, y_mapped)
        return self

    def predict_stage1(self, X: np.ndarray) -> np.ndarray:
        proba = self.stage1_model.predict_proba(X)[:, 1]
        return (proba >= self.stage1_threshold).astype(int)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        n = X.shape[0]
        proba_binary = self.stage1_model.predict_proba(X)
        p_unmapped = proba_binary[:, 0]
        p_mapped = proba_binary[:, 1]

        proba_ordinal = self.stage2_model.predict_proba(X)

        result = np.zeros((n, 4))
        result[:, 0] = p_unmapped
        result[:, 1] = p_mapped * proba_ordinal[:, 0]
        result[:, 2] = p_mapped * proba_ordinal[:, 1]
        result[:, 3] = p_mapped * proba_ordinal[:, 2]

        row_sums = result.sum(axis=1, keepdims=True)
        row_sums = np.where(row_sums == 0, 1, row_sums)
        result = result / row_sums
        return result

    def predict(self, X: np.ndarray) -> np.ndarray:
        return self.predict_proba(X).argmax(axis=1)

    def save(self, path: Path) -> None:
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        self.stage1_model.booster_.save_model(str(path / "stage1.txt"))
        self.stage2_model.booster_.save_model(str(path / "stage2.txt"))
        with (path / "config.json").open("w") as f:
            json.dump({"stage1_threshold": self.stage1_threshold,
                       "stage1_recall_target": self.stage1_recall_target}, f)

    @classmethod
    def load(cls, path: Path) -> "TwoStageClassifier":
        path = Path(path)
        with (path / "config.json").open() as f:
            config = json.load(f)
        obj = cls(stage1_recall_target=config["stage1_recall_target"])
        obj.stage1_threshold = config["stage1_threshold"]
        obj.stage1_model = lgb.LGBMClassifier()
        obj.stage1_model._Booster = lgb.Booster(model_file=str(path / "stage1.txt"))
        obj.stage2_model = lgb.LGBMClassifier()
        obj.stage2_model._Booster = lgb.Booster(model_file=str(path / "stage2.txt"))
        return obj
