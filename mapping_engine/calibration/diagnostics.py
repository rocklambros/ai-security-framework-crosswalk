"""Anti-overfit diagnostics: bootstrap CIs, permutation importance, learning curves, reliability.

Implements the four primitives required by ``docs/anti_overfit_methodology.md``:

- ``bootstrap_ci`` — percentile CI on any metric over resampled (y_true, y_pred) pairs.
- ``permutation_importance_ci`` — per-feature importance with percentile CI from sklearn's
  ``permutation_importance`` repeats matrix.
- ``learning_curve`` — train and CV mean+std at varying training fractions.
- ``reliability_curve`` — predicted vs observed binning for calibration plots.

All four return plain Python data structures (no plotting). Plots are produced separately
from the ``docs/diagnostics/`` rendering scripts so this module stays import-light.
"""

from __future__ import annotations

from typing import Any, Callable, Sequence

import numpy as np
from sklearn.inspection import permutation_importance as _sk_permutation_importance
from sklearn.model_selection import learning_curve as _sk_learning_curve

ArrayLike = Sequence[float] | np.ndarray


def bootstrap_ci(
    metric_fn: Callable[[np.ndarray, np.ndarray], float],
    y_true: ArrayLike,
    y_pred: ArrayLike,
    n_resamples: int = 1000,
    alpha: float = 0.05,
    rng: np.random.Generator | int | None = None,
) -> dict[str, float]:
    """Percentile bootstrap CI on a scalar metric.

    Returns ``{"point": ..., "lo": ..., "hi": ..., "n_resamples": ..., "alpha": ...}``.
    The point estimate is computed on the full sample; ``lo``/``hi`` are the
    ``alpha/2`` and ``1 - alpha/2`` percentiles of the bootstrap distribution.

    A one-sided improvement is "real" only when ``lo > 0`` for a delta metric.
    """
    y_true_a = np.asarray(y_true)
    y_pred_a = np.asarray(y_pred)
    if y_true_a.shape[0] != y_pred_a.shape[0]:
        raise ValueError("y_true and y_pred must have the same length")
    n = y_true_a.shape[0]
    if n == 0:
        raise ValueError("cannot bootstrap an empty sample")

    generator = np.random.default_rng(rng)
    point = float(metric_fn(y_true_a, y_pred_a))

    samples = np.empty(n_resamples, dtype=np.float64)
    for i in range(n_resamples):
        idx = generator.integers(0, n, size=n)
        samples[i] = float(metric_fn(y_true_a[idx], y_pred_a[idx]))

    lo = float(np.percentile(samples, 100.0 * (alpha / 2.0)))
    hi = float(np.percentile(samples, 100.0 * (1.0 - alpha / 2.0)))
    return {
        "point": point,
        "lo": lo,
        "hi": hi,
        "n_resamples": n_resamples,
        "alpha": alpha,
    }


def permutation_importance_ci(
    model: Any,
    X: np.ndarray,
    y: np.ndarray,
    feature_names: Sequence[str] | None = None,
    scoring: str | Callable | None = None,
    n_repeats: int = 20,
    alpha: float = 0.05,
    rng: np.random.Generator | int | None = None,
) -> dict[str, dict[str, float]]:
    """Permutation importance with percentile CI per feature.

    Wraps ``sklearn.inspection.permutation_importance`` and computes the CI from
    the ``n_repeats`` per-feature scores using the percentile method. Returns a
    dict keyed by feature name (or ``"f{i}"`` if no names) with values
    ``{"mean": ..., "std": ..., "lo": ..., "hi": ..., "ci_excludes_zero": bool}``.

    The decision rule per the methodology: drop features where
    ``ci_excludes_zero`` is False.
    """
    X_a = np.asarray(X, dtype=np.float64)
    y_a = np.asarray(y)
    seed = rng if isinstance(rng, int) else None
    result = _sk_permutation_importance(
        model, X_a, y_a, n_repeats=n_repeats, scoring=scoring, random_state=seed
    )
    importances = result.importances  # shape (n_features, n_repeats)
    n_features = importances.shape[0]
    if feature_names is None:
        feature_names = [f"f{i}" for i in range(n_features)]
    out: dict[str, dict[str, float]] = {}
    lo_q = 100.0 * (alpha / 2.0)
    hi_q = 100.0 * (1.0 - alpha / 2.0)
    for i, name in enumerate(feature_names):
        row = importances[i]
        lo = float(np.percentile(row, lo_q))
        hi = float(np.percentile(row, hi_q))
        out[name] = {
            "mean": float(row.mean()),
            "std": float(row.std()),
            "lo": lo,
            "hi": hi,
            "ci_excludes_zero": bool(lo > 0 or hi < 0),
        }
    return out


def learning_curve(
    model_factory: Callable[[], Any],
    X: np.ndarray,
    y: np.ndarray,
    fractions: Sequence[float] = (0.2, 0.4, 0.6, 0.8, 1.0),
    scoring: str = "accuracy",
    cv: int = 5,
    rng: int | None = 42,
) -> dict[str, list[float]]:
    """Train and CV mean+std at varying training fractions.

    Wraps ``sklearn.model_selection.learning_curve``. ``model_factory`` is a
    zero-arg callable that returns a fresh estimator (sklearn's API requires
    an estimator instance, not a factory, but we use the callable to make the
    contract explicit and to allow per-fold cloning if a future caller needs it).

    Returns ``{"fractions": [...], "train_mean": [...], "train_std": [...],
    "cv_mean": [...], "cv_std": [...]}`` — diagnoses underfitting (still rising)
    vs overfitting (large train-vs-CV gap).
    """
    estimator = model_factory()
    sizes_arr = np.asarray(fractions, dtype=np.float64)
    sizes, train_scores, cv_scores = _sk_learning_curve(
        estimator,
        np.asarray(X, dtype=np.float64),
        np.asarray(y),
        train_sizes=sizes_arr,
        cv=cv,
        scoring=scoring,
        random_state=rng,
        shuffle=True,
    )
    return {
        "fractions": [float(s / sizes[-1]) for s in sizes],
        "train_sizes": [int(s) for s in sizes],
        "train_mean": [float(v) for v in train_scores.mean(axis=1)],
        "train_std": [float(v) for v in train_scores.std(axis=1)],
        "cv_mean": [float(v) for v in cv_scores.mean(axis=1)],
        "cv_std": [float(v) for v in cv_scores.std(axis=1)],
    }


def reliability_curve(
    y_true: ArrayLike,
    y_proba: ArrayLike,
    n_bins: int = 10,
) -> dict[str, list[float]]:
    """Equal-width binning of predicted probabilities vs observed positive rate.

    Returns ``{"bin_centers": [...], "predicted_mean": [...],
    "observed_mean": [...], "counts": [...]}``. A perfectly-calibrated model
    has ``predicted_mean[i] == observed_mean[i]`` (diagonal). Empty bins are
    omitted from the output.
    """
    y_true_a = np.asarray(y_true, dtype=np.float64)
    y_proba_a = np.asarray(y_proba, dtype=np.float64)
    if y_true_a.shape[0] != y_proba_a.shape[0]:
        raise ValueError("y_true and y_proba must have the same length")
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    bin_centers: list[float] = []
    predicted_mean: list[float] = []
    observed_mean: list[float] = []
    counts: list[int] = []
    for i in range(n_bins):
        lo, hi = edges[i], edges[i + 1]
        if i == n_bins - 1:
            mask = (y_proba_a >= lo) & (y_proba_a <= hi)
        else:
            mask = (y_proba_a >= lo) & (y_proba_a < hi)
        n = int(mask.sum())
        if n == 0:
            continue
        bin_centers.append(float((lo + hi) / 2.0))
        predicted_mean.append(float(y_proba_a[mask].mean()))
        observed_mean.append(float(y_true_a[mask].mean()))
        counts.append(n)
    return {
        "bin_centers": bin_centers,
        "predicted_mean": predicted_mean,
        "observed_mean": observed_mean,
        "counts": counts,
    }
