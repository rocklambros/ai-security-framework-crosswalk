"""WANDB project and sweep configurations for crosswalk-v7."""
from __future__ import annotations

WANDB_PROJECT = "crosswalk-v7"
WANDB_ENTITY = None

CE_SWEEP_CONFIG = {
    "method": "bayes",
    "metric": {"name": "combined_f1", "goal": "maximize"},
    "parameters": {
        "learning_rate": {"distribution": "log_uniform_values", "min": 5e-7, "max": 5e-5},
        "batch_size": {"values": [8, 16]},
        "epochs": {"values": [5, 8, 10, 15]},
        "warmup_ratio": {"distribution": "uniform", "min": 0.0, "max": 0.2},
        "weight_decay": {"distribution": "log_uniform_values", "min": 1e-4, "max": 1e-1},
        "dropout": {"distribution": "uniform", "min": 0.1, "max": 0.3},
        "loss_type": {"values": ["kl"]},
        "sigma": {"distribution": "uniform", "min": 0.3, "max": 0.8},
        "human_cal_weight": {"values": [5, 10, 15, 20, 30]},
        "frozen_epochs": {"values": [1, 2, 3]},
        "encoder_lr_factor": {"values": [0.1, 0.2, 0.5]},
    },
    "early_terminate": {"type": "hyperband", "min_iter": 3, "eta": 3},
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
