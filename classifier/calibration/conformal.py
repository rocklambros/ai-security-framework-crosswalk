"""Conformal calibration wrapper for v8 pipeline integration.

Wraps the marginal conformal approach from v7 Phase 8 into a standalone function.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import numpy as np


def calibrate_conformal(
    model_dir: str,
    cal_path: str,
    alpha: float = 0.10,
    output_dir: str = "runs/v8/conformal",
) -> Dict[str, Any]:
    """Run marginal conformal calibration on the stacker model.

    Uses the human_cal val split for calibration with label-shift correction.
    """
    from classifier.ensemble.stacker import LGBMStacker
    from classifier.ensemble.feature_pipeline import FeaturePipeline
    from classifier.ensemble.label_shift import adjust_label_shift, estimate_prior
    from classifier.data.split_human_cal import split_human_cal
    from classifier.data.tier_mapper import map_expert_tier

    model_path = Path(model_dir)
    stacker = LGBMStacker.load(model_path)

    pipe_path = model_path.parent / "feature_pipeline"
    if not pipe_path.exists():
        pipe_path = Path("runs/v8/stacker/feature_pipeline")
    pipe = FeaturePipeline.load(pipe_path)

    ce_data = {}
    for name in ["deberta", "roberta", "deberta_base"]:
        p = Path(f"data/processed/ce_features_v8_{name}.npz")
        if p.exists():
            d = dict(np.load(str(p)))
            for k, v in d.items():
                ce_data[f"{name}_{k}"] = v

    _, _, _, cal_val_indices = split_human_cal()

    cal_labels_all = []
    with open(cal_path) as f:
        for line in f:
            row = json.loads(line)
            cal_labels_all.append(int(map_expert_tier(row["expert_tier"])))
    y_cal = np.array([cal_labels_all[i] for i in cal_val_indices])

    n_train = sum(1 for _ in open("data/splits/expert_train.jsonl"))
    n_val = sum(1 for _ in open("data/splits/expert_val.jsonl"))
    n_cal_start = n_train + n_val

    X_all = pipe.transform(ce_data)
    X_cal = X_all[[n_cal_start + i for i in cal_val_indices]]

    proba_cal = stacker.predict_proba(X_cal)

    train_labels = []
    with open("data/splits/expert_train.jsonl") as f:
        for line in f:
            train_labels.append(json.loads(line)["tier_label"])
    source_prior = estimate_prior(np.array(train_labels), n_classes=4)
    target_prior = estimate_prior(y_cal, n_classes=4)
    proba_adjusted = adjust_label_shift(proba_cal, source_prior, target_prior)

    scores = 1.0 - proba_adjusted[np.arange(len(y_cal)), y_cal]
    n_cal = len(y_cal)
    q_level = min(np.ceil((n_cal + 1) * (1 - alpha)) / n_cal, 1.0)
    q_hat = float(np.quantile(scores, q_level))

    covered = int((scores <= q_hat).sum())
    coverage = covered / n_cal

    result = {
        "alpha": alpha,
        "n_cal": n_cal,
        "marginal_coverage": coverage,
        "method": "marginal",
        "q_hat": q_hat,
        "label_shift_applied": True,
        "source_prior": source_prior.tolist(),
        "target_prior": target_prior.tolist(),
    }

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "conformal.json").write_text(json.dumps(result, indent=2))
    print(f"  [conformal] {result}")

    return result
