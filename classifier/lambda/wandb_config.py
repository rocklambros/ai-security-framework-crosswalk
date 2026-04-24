"""WANDB project and sweep configurations for crosswalk-v7."""
from __future__ import annotations

WANDB_PROJECT = "crosswalk-v7b"
WANDB_ENTITY = "rockcyber"

CE_SWEEP_CONFIG = {
    "method": "bayes",
    "metric": {"name": "combined_f1", "goal": "maximize"},
    "parameters": {
        "learning_rate": {"distribution": "log_uniform_values", "min": 1e-5, "max": 5e-5},
        "batch_size": {"values": [8]},
        "epochs": {"values": [15, 20]},
        "warmup_ratio": {"distribution": "uniform", "min": 0.05, "max": 0.2},
        "weight_decay": {"distribution": "log_uniform_values", "min": 1e-4, "max": 1e-1},
        "dropout": {"distribution": "uniform", "min": 0.1, "max": 0.3},
        "loss_type": {"values": ["kl"]},
        "sigma": {"distribution": "uniform", "min": 0.35, "max": 0.50},
        "human_cal_weight": {"values": [2, 5, 10]},
        "encoder_lr_factor": {"values": [0.05, 0.1, 0.2]},
    },
    "early_terminate": {"type": "hyperband", "min_iter": 5, "eta": 3},
}

STACKER_SWEEP_CONFIG = {
    "method": "bayes",
    "metric": {"name": "oof_macro_f1", "goal": "maximize"},
    "parameters": {
        "n_estimators": {"values": [100, 200, 300, 500]},
        "max_depth": {"values": [3, 5, 7, -1]},
        "learning_rate": {"distribution": "log_uniform_values", "min": 0.01, "max": 0.3},
        "min_child_samples": {"values": [15, 20, 30, 50]},
        "num_leaves": {"values": [8, 16, 24, 31]},
        "reg_alpha": {"distribution": "log_uniform_values", "min": 1e-4, "max": 10},
        "reg_lambda": {"distribution": "log_uniform_values", "min": 1e-4, "max": 10},
        "subsample": {"distribution": "uniform", "min": 0.6, "max": 1.0},
        "colsample_bytree": {"distribution": "uniform", "min": 0.5, "max": 1.0},
    },
}

CROSS_ENCODER_MODELS = [
    {"name": "deberta", "model_id": "microsoft/deberta-v3-large", "group": "ce-deberta-sweep"},
    {"name": "roberta", "model_id": "roberta-large", "group": "ce-roberta-sweep"},
    {"name": "deberta_base", "model_id": "microsoft/deberta-v3-base", "group": "ce-deberta-base-sweep"},
]

# ---------------------------------------------------------------------------
# v8 additions — OpenCRE integration
# ---------------------------------------------------------------------------

WANDB_PROJECT_V8 = "crosswalk-v8b"

V8_CE_SWEEP_CONFIG = {
    "method": "bayes",
    "metric": {"name": "combined_f1", "goal": "maximize"},
    "parameters": {
        "learning_rate": {"distribution": "log_uniform_values", "min": 1e-5, "max": 5e-5},
        "batch_size": {"values": [8]},
        "epochs": {"values": [15, 20, 25]},
        "warmup_ratio": {"distribution": "uniform", "min": 0.05, "max": 0.2},
        "weight_decay": {"distribution": "log_uniform_values", "min": 1e-4, "max": 1e-1},
        "dropout": {"distribution": "uniform", "min": 0.1, "max": 0.3},
        "loss_type": {"values": ["kl"]},
        "sigma": {"distribution": "uniform", "min": 0.30, "max": 0.50},
        "human_cal_weight": {"values": [2, 5, 10]},
        "encoder_lr_factor": {"values": [0.05, 0.1, 0.2]},
        "opencre_weight": {"values": [0.2, 0.3, 0.5]},
    },
    "early_terminate": {"type": "hyperband", "min_iter": 5, "eta": 3},
}

V8_CE_SWEEP_CONFIG_DEBERTA_LARGE = {
    "method": "bayes",
    "metric": {"name": "combined_f1", "goal": "maximize"},
    "parameters": {
        "learning_rate": {"distribution": "log_uniform_values", "min": 2e-5, "max": 5e-5},
        "batch_size": {"values": [8]},
        "epochs": {"values": [15, 20]},
        "warmup_ratio": {"distribution": "uniform", "min": 0.05, "max": 0.15},
        "weight_decay": {"distribution": "log_uniform_values", "min": 1e-4, "max": 1e-1},
        "dropout": {"distribution": "uniform", "min": 0.1, "max": 0.3},
        "loss_type": {"values": ["kl"]},
        "sigma": {"distribution": "uniform", "min": 0.30, "max": 0.50},
        "human_cal_weight": {"values": [2, 5, 10]},
        "encoder_lr_factor": {"values": [0.15, 0.2, 0.3]},
        "opencre_weight": {"values": [0.2, 0.3, 0.5]},
    },
    "early_terminate": {"type": "hyperband", "min_iter": 3, "eta": 3},
}

V8_STACKER_SWEEP_CONFIG = {
    "method": "bayes",
    "metric": {"name": "oof_macro_f1", "goal": "maximize"},
    "parameters": {
        "n_estimators": {"values": [100, 200, 300, 500]},
        "max_depth": {"values": [3, 5, 7, -1]},
        "learning_rate": {"distribution": "log_uniform_values", "min": 0.01, "max": 0.3},
        "min_child_samples": {"values": [15, 20, 30, 50]},
        "num_leaves": {"values": [8, 16, 24, 31]},
        "reg_alpha": {"distribution": "log_uniform_values", "min": 1e-4, "max": 10},
        "reg_lambda": {"distribution": "log_uniform_values", "min": 1e-4, "max": 10},
        "subsample": {"distribution": "uniform", "min": 0.6, "max": 1.0},
        "colsample_bytree": {"distribution": "uniform", "min": 0.5, "max": 1.0},
    },
}

V8_MONITORING = {
    "collapse_guard": {
        "metric": "val_macro_f1",
        "condition": "min_threshold",
        "threshold": 0.20,
        "alert": "val_macro_f1 dropped below 0.20 — possible label collapse or training failure",
    },
    "overfitting_guard": {
        "metric_train": "train_acc",
        "metric_val": "val_acc",
        "condition": "max_gap",
        "threshold": 0.30,
        "alert": "train_acc vs val_acc gap exceeds 30pp — likely overfitting",
    },
    "leakage_guard": {
        "metric": "val_acc",
        "condition": "max_threshold",
        "threshold": 0.98,
        "alert": "val_acc suspiciously high (>= 0.98) — possible data leakage",
    },
}
