"""LightGBM multiclass meta-stacker with Optuna tuning.

Trains on 5-fold OOF features from Plan 3 baselines + bridge scores.
Outputs class probabilities for {unrelated, partial, related, equivalent}.

Contract 5: Only trains on v1_frozen labels.
Contract 6: Appends to runs/registry.jsonl.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

import lightgbm as lgb
import numpy as np
import optuna
from sklearn.metrics import accuracy_score, f1_score, log_loss
from sklearn.model_selection import StratifiedKFold

optuna.logging.set_verbosity(optuna.logging.WARNING)

BASE_FEATURE_COLS = ["score_bge_cosine", "score_bm25", "score_bridge"]
GAT_SCALAR_COLS = ["score_gat", "gat_l2", "gat_dot"]
GAT_DIFF_COLS = [f"gat_diff_{d:02d}" for d in range(32)]
FEATURE_COLS = BASE_FEATURE_COLS + GAT_SCALAR_COLS + GAT_DIFF_COLS

# V2 features: Multi-encoder ensemble
CE_MODEL_NAMES = ["deberta", "roberta", "electra"]
CE_LOGIT_COLS = [f"{m}_logit_{i}" for m in CE_MODEL_NAMES for i in range(4)]
CE_CLS_SIM_COLS = [f"{m}_cls_sim" for m in CE_MODEL_NAMES]
GAT_V2_DIFF_COLS = [f"gat_diff_{d:02d}" for d in range(64)]
GAT_V2_SCALAR_COLS = ["gat_dot", "gat_cosine"]
BASELINE_V2_COLS = ["score_bm25", "score_bridge"]

FEATURE_COLS_V2 = (
    CE_LOGIT_COLS       # 12 (3 models x 4 logits)
    + CE_CLS_SIM_COLS   # 3
    + GAT_V2_DIFF_COLS  # 64
    + GAT_V2_SCALAR_COLS  # 2
    + BASELINE_V2_COLS  # 2
)  # Total: 83

LABEL_COL = "label"
N_CLASSES = 4
REGISTRY_PATH = Path("runs/registry.jsonl")


class LGBMStacker:
    """LightGBM multiclass stacker."""

    def __init__(self, params: dict | None = None, version: str = "v1"):
        self.params = params or {}
        self.model: lgb.Booster | None = None
        self.run_id: str = ""
        self.version = version
        self.feature_cols = FEATURE_COLS if version == "v1" else FEATURE_COLS_V2

    def fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
        sample_weight: np.ndarray | None = None,
    ) -> "LGBMStacker":
        ds = lgb.Dataset(X, label=y, weight=sample_weight)
        params = {
            "objective": "multiclass",
            "num_class": N_CLASSES,
            "metric": "multi_logloss",
            "verbosity": -1,
            "seed": 42,
            **self.params,
        }
        self.model = lgb.train(
            params,
            ds,
            num_boost_round=self.params.get("n_estimators", 200),
        )
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Return (n, N_CLASSES) probability matrix."""
        if self.model is None:
            raise RuntimeError("Model not fitted")
        return self.model.predict(X)

    def predict(self, X: np.ndarray) -> np.ndarray:
        return np.argmax(self.predict_proba(X), axis=1)

    def save(self, path: Path) -> None:
        if self.model is None:
            raise RuntimeError("Model not fitted")
        path.parent.mkdir(parents=True, exist_ok=True)
        self.model.save_model(str(path))

    @classmethod
    def load(cls, path: Path) -> "LGBMStacker":
        obj = cls()
        obj.model = lgb.Booster(model_file=str(path))
        return obj


def tune_stacker(
    X: np.ndarray,
    y: np.ndarray,
    sample_weight: np.ndarray | None = None,
    n_trials: int = 20,
    n_splits: int = 5,
    seed: int = 42,
) -> dict:
    """Optuna hyperparameter search for the stacker."""

    def objective(trial):
        params = {
            "num_leaves": trial.suggest_int("num_leaves", 8, 64),
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
            "min_child_samples": trial.suggest_int("min_child_samples", 5, 50),
            "subsample": trial.suggest_float("subsample", 0.5, 1.0),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0),
            "reg_alpha": trial.suggest_float("reg_alpha", 1e-8, 10.0, log=True),
            "reg_lambda": trial.suggest_float("reg_lambda", 1e-8, 10.0, log=True),
            "n_estimators": trial.suggest_int("n_estimators", 50, 500),
        }
        skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)
        f1s = []
        for train_idx, val_idx in skf.split(X, y):
            X_tr, X_val = X[train_idx], X[val_idx]
            y_tr, y_val = y[train_idx], y[val_idx]
            w_tr = sample_weight[train_idx] if sample_weight is not None else None
            stacker = LGBMStacker(params)
            stacker.fit(X_tr, y_tr, sample_weight=w_tr)
            preds = stacker.predict(X_val)
            f1s.append(f1_score(y_val, preds, average="macro"))
        return np.mean(f1s)

    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=n_trials)
    return study.best_params


def train_and_evaluate(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    sample_weight: np.ndarray | None = None,
    params: dict | None = None,
    run_dir: Path | None = None,
) -> dict:
    """Train stacker, evaluate on val, save model, return metrics."""
    run_id = f"stacker-{uuid.uuid4().hex[:8]}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}"

    if run_dir is None:
        run_dir = Path(f"runs/stacker/{run_id}")
    if run_dir.exists():
        raise FileExistsError(f"Contract 3: {run_dir} exists")
    run_dir.mkdir(parents=True, exist_ok=True)

    stacker = LGBMStacker(params or {})
    stacker.fit(X_train, y_train, sample_weight=sample_weight)
    stacker.run_id = run_id

    # Eval
    train_proba = stacker.predict_proba(X_train)
    val_proba = stacker.predict_proba(X_val)
    train_pred = np.argmax(train_proba, axis=1)
    val_pred = np.argmax(val_proba, axis=1)

    metrics = {
        "train_acc": float(accuracy_score(y_train, train_pred)),
        "val_acc": float(accuracy_score(y_val, val_pred)),
        "train_logloss": float(log_loss(y_train, train_proba, labels=list(range(N_CLASSES)))),
        "val_logloss": float(log_loss(y_val, val_proba, labels=list(range(N_CLASSES)))),
    }

    # Save model
    model_path = run_dir / "model.txt"
    stacker.save(model_path)

    # Save config + metrics
    row = {
        "run_id": run_id,
        "component": "stacker",
        "utc": datetime.now(timezone.utc).isoformat(),
        "params": params or {},
        "metrics": metrics,
        "model_path": str(model_path),
        "status": "completed",
    }
    config_path = run_dir / "config.json"
    config_path.write_text(json.dumps(row, sort_keys=True, indent=2))

    # Append to registry
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with REGISTRY_PATH.open("a") as f:
        f.write(json.dumps(row, sort_keys=True, ensure_ascii=True) + "\n")

    return {**metrics, "run_id": run_id, "run_dir": str(run_dir), "stacker": stacker}
