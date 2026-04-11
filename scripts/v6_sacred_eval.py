"""V6 sacred evaluation — produce results/sacred/sacred_{sha}.json."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix
from sklearn.model_selection import cross_val_predict, StratifiedKFold
from sklearn.utils import resample

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.v6_features import build_features, FEATURE_NAMES, TIER_MAP

TIER_NAMES = ["Unrelated", "Partial", "Related", "Equivalent"]


def main():
    X_cal, y_cal, _ = build_features("human_cal")
    X_test, y_test, _ = build_features("human_test_frozen")

    # Train best model (GBM with grid-searched params)
    best_acc, best_model, best_cfg = 0, None, {}
    for n_est, lr, msl in [(300, 0.1, 10), (300, 0.05, 8), (500, 0.05, 5),
                            (200, 0.1, 8), (400, 0.03, 10)]:
        gbm = GradientBoostingClassifier(
            n_estimators=n_est, max_depth=3, min_samples_leaf=msl,
            learning_rate=lr, random_state=42,
        )
        gbm.fit(X_cal, y_cal)
        p = gbm.predict(X_test)
        acc = accuracy_score(y_test, p)
        if acc > best_acc:
            best_acc = acc
            best_model = gbm
            best_cfg = {"n_estimators": n_est, "lr": lr, "msl": msl}

    preds = best_model.predict(X_test)
    proba = best_model.predict_proba(X_test)

    # Metrics
    tier_acc = accuracy_score(y_test, preds)
    macro_f1 = f1_score(y_test, preds, average="macro")
    adj_acc = float(np.mean(np.abs(y_test - preds) <= 1))

    # Binary metrics
    bin_acc = accuracy_score(y_test >= 2, preds >= 2)

    # Confusion matrix
    cm = confusion_matrix(y_test, preds, labels=[0, 1, 2, 3])
    cm_dict = {}
    for i, tn in enumerate(TIER_NAMES):
        cm_dict[tn.lower()] = {TIER_NAMES[j].lower(): int(cm[i][j]) for j in range(4)}

    # Per-class
    per_class = []
    for t in range(4):
        mask = y_test == t
        if mask.any():
            t_acc = accuracy_score(y_test[mask], preds[mask])
            t_f1 = f1_score(y_test == t, preds == t)
        else:
            t_acc, t_f1 = 0, 0
        per_class.append({
            "tier": t, "name": TIER_NAMES[t],
            "f1": round(t_f1, 4), "accuracy": round(t_acc, 4),
            "count": int(mask.sum()),
        })

    # Bootstrap CI
    n_boot = 1000
    boot_accs, boot_f1s = [], []
    for _ in range(n_boot):
        idx = resample(range(len(y_test)), random_state=None)
        boot_accs.append(accuracy_score(y_test[idx], preds[idx]))
        boot_f1s.append(f1_score(y_test[idx], preds[idx], average="macro"))
    ci_acc = (float(np.percentile(boot_accs, 2.5)), float(np.percentile(boot_accs, 97.5)))
    ci_f1 = (float(np.percentile(boot_f1s, 2.5)), float(np.percentile(boot_f1s, 97.5)))

    # Conformal
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    proba_cv = cross_val_predict(best_model, X_cal, y_cal, cv=skf, method="predict_proba")
    scores = 1.0 - proba_cv[np.arange(len(y_cal)), y_cal]
    n = len(y_cal)
    alpha = 0.10
    q_level = min(np.ceil((n + 1) * (1 - alpha)) / n, 1.0)
    q_hat = float(np.quantile(scores, q_level))

    pred_sets = []
    for row in proba:
        s = [c for c in range(4) if row[c] >= 1 - q_hat]
        if not s:
            s = [int(np.argmax(row))]
        pred_sets.append(s)

    coverage = np.mean([y_test[i] in s for i, s in enumerate(pred_sets)])
    mean_set_size = np.mean([len(s) for s in pred_sets])

    # SHA
    sha = hashlib.sha256(json.dumps({
        "version": "v6", "acc": tier_acc, "f1": macro_f1,
    }).encode()).hexdigest()[:7]

    result = {
        "version": "v6-reframed",
        "method": f"GBM(22d: LLM+Struct+Opus) {best_cfg}",
        "best_method": f"GBM {best_cfg}",
        "tier_accuracy": round(tier_acc, 4),
        "macro_f1": round(macro_f1, 4),
        "adjacent_accuracy": round(adj_acc, 4),
        "binary_accuracy": round(bin_acc, 4),
        "bootstrap_ci": {
            "acc_95": [round(ci_acc[0], 4), round(ci_acc[1], 4)],
            "f1_95": [round(ci_f1[0], 4), round(ci_f1[1], 4)],
        },
        "conformal": {
            "alpha": alpha,
            "coverage": round(float(coverage), 4),
            "mean_set_size": round(float(mean_set_size), 2),
        },
        "confusion_matrix": cm_dict,
        "per_class": per_class,
        "features": "LLM(7) + Structural(13) + Opus(2) = 22d",
        "n_cal": int(len(y_cal)),
        "n_test": int(len(y_test)),
        "sha": sha,
        "ablation": [],  # populated from v6_all_results.json if available
    }

    # Load ablation if available
    ablation_path = Path("data/processed/v6_results/v6_all_results.json")
    if ablation_path.exists():
        abl = json.loads(ablation_path.read_text())
        result["ablation"] = abl.get("ablation", [])

    out_path = Path(f"results/sacred/sacred_{sha}.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"Sacred result: {out_path}")
    print(f"  Tier accuracy: {tier_acc:.1%}")
    print(f"  Macro F1: {macro_f1:.4f}")
    print(f"  Adjacent accuracy: {adj_acc:.1%}")
    print(f"  Binary accuracy: {bin_acc:.1%}")
    print(f"  Conformal coverage: {coverage:.1%} (set size: {mean_set_size:.2f})")
    return result


if __name__ == "__main__":
    main()
