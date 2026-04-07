"""Per-feature weight perturbation analysis.

Sanity-checks a learned model by nudging each feature's contribution by
±15% and counting how many pairs cross a tier boundary. >20% churn on a
single feature indicates the model is unstable / overfit.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from mapping_engine.calibration.weight_learner import FEATURES

DEFAULT_THRESHOLD = 0.5


def _predict(model: Any, X: np.ndarray, model_type: str) -> np.ndarray:
    if model_type == "logistic":
        return model.predict_proba(X)[:, 1]
    if model_type == "lightgbm":
        return model.predict(X)
    if model_type == "ordinal":
        probs = model.model.predict(model.params, exog=X)
        return probs[:, 2:].sum(axis=1)
    raise ValueError(f"unknown model_type: {model_type}")


def analyze_weight_stability(
    train_df: pd.DataFrame,
    model: Any,
    model_type: str = "logistic",
    perturbation: float = 0.15,
    threshold: float = DEFAULT_THRESHOLD,
) -> dict[str, dict[str, float]]:
    """Perturb each feature's input by ±perturbation and count tier flips.

    Returns ``{feature: {"+15%": n_changed, "-15%": n_changed,
    "pct_changed": float}}``. ``pct_changed`` is the larger of the two as
    a fraction of total rows.
    """
    X = train_df[FEATURES].to_numpy(dtype=np.float64).copy()
    base = _predict(model, X, model_type)
    base_tier = (base >= threshold).astype(np.int64)
    n = len(train_df)

    out: dict[str, dict[str, float]] = {}
    for k, feat in enumerate(FEATURES):
        Xp = X.copy()
        Xp[:, k] = np.clip(Xp[:, k] * (1.0 + perturbation), 0.0, 1.0)
        pred_p = (_predict(model, Xp, model_type) >= threshold).astype(np.int64)

        Xm = X.copy()
        Xm[:, k] = np.clip(Xm[:, k] * (1.0 - perturbation), 0.0, 1.0)
        pred_m = (_predict(model, Xm, model_type) >= threshold).astype(np.int64)

        n_plus = int((pred_p != base_tier).sum())
        n_minus = int((pred_m != base_tier).sum())
        out[feat] = {
            f"+{int(perturbation*100)}%": n_plus,
            f"-{int(perturbation*100)}%": n_minus,
            "pct_changed": float(max(n_plus, n_minus) / n),
        }
    return out

