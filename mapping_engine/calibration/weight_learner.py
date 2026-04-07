"""Learned signal weights: logistic regression, LightGBM, ordinal regression.

Replaces the hand-tuned composite weights (bridge 0.45, semantic 0.35,
keyword 0.20 in defaults.yaml) with weights fit on the AIUC-1 expert
crosswalk. Models are evaluated against an in-sample baseline plus the
held-out NIST RMF validation set to detect overfitting.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

FEATURES = ["bridge_score", "semantic_score", "keyword_score", "function_match", "node2vec_score"]
TIER_ORDER = {"None": 0, "Tangential": 1, "Related": 2, "Direct": 3}
HAND_WEIGHTS = {"bridge": 0.467, "semantic": 0.333, "keyword": 0.200}


def _xy(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    return df[FEATURES].to_numpy(dtype=np.float64), df["is_mapped"].to_numpy(dtype=np.int64)


def train_logistic(train_df: pd.DataFrame) -> tuple[LogisticRegression, dict[str, float]]:
    """Fit an L2-regularized, class-balanced logistic regression."""
    X, y = _xy(train_df)
    model = LogisticRegression(
        penalty="l2", C=1.0, class_weight="balanced", max_iter=1000, solver="lbfgs"
    )
    model.fit(X, y)
    coefs = {f: float(c) for f, c in zip(FEATURES, model.coef_[0])}
    coefs["intercept"] = float(model.intercept_[0])
    return model, coefs


def train_lightgbm(train_df: pd.DataFrame) -> tuple[Any, dict[str, float]]:
    """Fit a LightGBM binary classifier with early stopping."""
    import lightgbm as lgb

    X, y = _xy(train_df)
    rng = np.random.default_rng(42)
    idx = np.arange(len(X))
    rng.shuffle(idx)
    cut = int(len(idx) * 0.8)
    tr, va = idx[:cut], idx[cut:]
    dtrain = lgb.Dataset(X[tr], label=y[tr])
    dval = lgb.Dataset(X[va], label=y[va], reference=dtrain)
    params = {
        "objective": "binary",
        "metric": "binary_logloss",
        "learning_rate": 0.05,
        "num_leaves": 15,
        "min_data_in_leaf": 5,
        "verbosity": -1,
        "is_unbalance": True,
    }
    booster = lgb.train(
        params, dtrain, num_boost_round=500,
        valid_sets=[dval],
        callbacks=[lgb.early_stopping(stopping_rounds=20, verbose=False)],
    )
    importance = booster.feature_importance(importance_type="gain")
    feat_imp = {f: float(v) for f, v in zip(FEATURES, importance)}
    return booster, feat_imp


def train_ordinal(train_df: pd.DataFrame) -> tuple[Any, dict[str, float]]:
    """Fit an ordinal regression on the 4-level expert_tier label."""
    from statsmodels.miscmodels.ordinal_model import OrderedModel

    X = train_df[FEATURES].to_numpy(dtype=np.float64)
    y = train_df["expert_tier"].map(TIER_ORDER).to_numpy(dtype=np.int64)
    model = OrderedModel(y, X, distr="logit")
    res = model.fit(method="bfgs", disp=False, maxiter=200)
    coefs: dict[str, float] = {}
    for f, c in zip(FEATURES, res.params[: len(FEATURES)]):
        coefs[f] = float(c)
    return res, coefs


def _logistic_proba(model: LogisticRegression, df: pd.DataFrame) -> np.ndarray:
    return model.predict_proba(df[FEATURES].to_numpy(dtype=np.float64))[:, 1]


def _lightgbm_proba(model: Any, df: pd.DataFrame) -> np.ndarray:
    return model.predict(df[FEATURES].to_numpy(dtype=np.float64))


def _ordinal_proba(model: Any, df: pd.DataFrame) -> np.ndarray:
    """Return P(tier >= Related) as a binary proxy for is_mapped."""
    X = df[FEATURES].to_numpy(dtype=np.float64)
    probs = model.model.predict(model.params, exog=X)
    related_idx = TIER_ORDER["Related"]
    return probs[:, related_idx:].sum(axis=1)


def _proba(model: Any, df: pd.DataFrame, model_type: str) -> np.ndarray:
    if model_type == "logistic":
        return _logistic_proba(model, df)
    if model_type == "lightgbm":
        return _lightgbm_proba(model, df)
    if model_type == "ordinal":
        return _ordinal_proba(model, df)
    raise ValueError(f"unknown model_type: {model_type}")


def evaluate_model(
    model: Any, test_df: pd.DataFrame, model_type: str, threshold: float = 0.5
) -> dict[str, float]:
    """Return accuracy / precision / recall / F1 / ROC-AUC for ``test_df``.

    For ``model_type='ordinal'`` an additional ``tier_accuracy`` key is
    returned (multi-class accuracy on the 4-level tier label).
    """
    y_true = test_df["is_mapped"].to_numpy(dtype=np.int64)
    proba = _proba(model, test_df, model_type)
    y_pred = (proba >= threshold).astype(np.int64)
    metrics = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_true, proba)) if len(set(y_true)) > 1 else float("nan"),
    }
    if model_type == "ordinal":
        X = test_df[FEATURES].to_numpy(dtype=np.float64)
        probs = model.model.predict(model.params, exog=X)
        tier_pred = probs.argmax(axis=1)
        tier_true = test_df["expert_tier"].map(TIER_ORDER).to_numpy(dtype=np.int64)
        metrics["tier_accuracy"] = float(accuracy_score(tier_true, tier_pred))
    return metrics


def hand_tuned_score(df: pd.DataFrame, weights: dict[str, float] | None = None) -> np.ndarray:
    w = weights or HAND_WEIGHTS
    return (
        w["bridge"] * df["bridge_score"].to_numpy()
        + w["semantic"] * df["semantic_score"].to_numpy()
        + w["keyword"] * df["keyword_score"].to_numpy()
    )


def evaluate_hand_tuned(test_df: pd.DataFrame, threshold: float = 0.4) -> dict[str, float]:
    y_true = test_df["is_mapped"].to_numpy(dtype=np.int64)
    proba = hand_tuned_score(test_df)
    y_pred = (proba >= threshold).astype(np.int64)
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_true, proba)) if len(set(y_true)) > 1 else float("nan"),
    }


def compare_to_hand_tuned(
    test_df: pd.DataFrame,
    hand_weights: dict[str, float],
    model: Any,
    model_type: str,
    threshold: float = 0.5,
) -> dict[str, Any]:
    """Tier-agreement comparison between hand-tuned scoring and a learned model."""
    learned_proba = _proba(model, test_df, model_type)
    hand_proba = hand_tuned_score(test_df, hand_weights)
    learned_pred = (learned_proba >= threshold).astype(np.int64)
    hand_pred = (hand_proba >= 0.4).astype(np.int64)
    agree = float((learned_pred == hand_pred).mean())
    confusion = (
        pd.crosstab(
            pd.Series(hand_pred, name="hand"),
            pd.Series(learned_pred, name="learned"),
        )
        .to_dict()
    )
    return {"agreement_rate": agree, "confusion": confusion}

