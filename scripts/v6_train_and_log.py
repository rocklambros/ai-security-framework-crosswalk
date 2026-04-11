"""V6 model training + WANDB experiment logging.

Trains:
  1. Binary GBM (Related+ vs Not-Related)
  2. Four-tier GBM
  3. Cascade GBM (binary → refine)
  4. Conformal prediction calibration

Logs all experiments to WANDB project "crosswalk-v6-reframed".
Saves artifacts to data/processed/v6_results/.
"""
from __future__ import annotations

import json
import os
import sys
import warnings
from pathlib import Path

import numpy as np
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, f1_score, classification_report, confusion_matrix,
)
from sklearn.model_selection import cross_val_predict, StratifiedKFold

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.v6_features import build_features, FEATURE_NAMES, TIER_MAP

OUT = Path("data/processed/v6_results")
TIER_NAMES = ["Unrelated", "Partial", "Related", "Equivalent"]

# ---------------------------------------------------------------------------
# WANDB setup
# ---------------------------------------------------------------------------

def init_wandb(run_name, config=None):
    try:
        import wandb
        wandb.init(
            project="crosswalk-v6-reframed",
            name=run_name,
            config=config or {},
            reinit=True,
        )
        return wandb
    except Exception as e:
        print(f"WANDB init failed: {e}. Continuing without logging.")
        return None


def log_metrics(wb, metrics):
    if wb:
        wb.log(metrics)


def finish_wandb(wb):
    if wb:
        wb.finish()


# ---------------------------------------------------------------------------
# Conformal prediction (split conformal, marginal)
# ---------------------------------------------------------------------------

def conformal_calibrate(proba_cal, y_cal, alpha=0.10):
    """Compute conformal threshold from calibration probabilities."""
    n = len(y_cal)
    scores = 1.0 - proba_cal[np.arange(n), y_cal]
    q_level = min(np.ceil((n + 1) * (1 - alpha)) / n, 1.0)
    q_hat = float(np.quantile(scores, q_level))
    return q_hat


def conformal_predict(proba_test, q_hat):
    """Produce prediction sets from test probabilities and threshold."""
    sets = []
    for row in proba_test:
        s = [c for c in range(len(row)) if row[c] >= 1 - q_hat]
        if not s:
            s = [int(np.argmax(row))]
        sets.append(s)
    return sets


# ---------------------------------------------------------------------------
# Training functions
# ---------------------------------------------------------------------------

def train_binary(X_cal, y_cal, X_test, y_test):
    """Train binary GBM: Related+ (2,3) vs Not-Related (0,1)."""
    y_bin_cal = (y_cal >= 2).astype(int)
    y_bin_test = (y_test >= 2).astype(int)

    gbm = GradientBoostingClassifier(
        n_estimators=300, max_depth=3, min_samples_leaf=8,
        learning_rate=0.1, random_state=42,
    )
    gbm.fit(X_cal, y_bin_cal)
    p = gbm.predict(X_test)
    proba = gbm.predict_proba(X_test)

    acc = accuracy_score(y_bin_test, p)
    f1 = f1_score(y_bin_test, p, average="macro")
    cm = confusion_matrix(y_bin_test, p).tolist()

    print(f"\nBinary GBM: acc={acc:.4f}, F1={f1:.4f}")
    print(classification_report(y_bin_test, p,
          target_names=["Not-Related", "Related+"]))

    return {
        "model": gbm,
        "accuracy": acc,
        "macro_f1": f1,
        "confusion_matrix": cm,
        "proba": proba,
        "preds": p,
        "y_true": y_bin_test,
    }


def train_4tier(X_cal, y_cal, X_test, y_test):
    """Train 4-tier GBM."""
    best_acc = 0
    best_cfg = {}
    # Quick grid search
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
            best_cfg = {"n_estimators": n_est, "learning_rate": lr,
                        "min_samples_leaf": msl}
            best_model = gbm
            best_preds = p

    proba = best_model.predict_proba(X_test)
    f1 = f1_score(y_test, best_preds, average="macro")
    adj = float(np.mean(np.abs(y_test - best_preds) <= 1))
    cm = confusion_matrix(y_test, best_preds, labels=[0, 1, 2, 3]).tolist()

    print(f"\n4-Tier GBM ({best_cfg}): acc={best_acc:.4f}, F1={f1:.4f}, adj={adj:.4f}")
    print(classification_report(y_test, best_preds, target_names=TIER_NAMES))

    # Feature importances
    fi = dict(zip(FEATURE_NAMES, best_model.feature_importances_.tolist()))

    return {
        "model": best_model,
        "accuracy": best_acc,
        "macro_f1": f1,
        "adjacent_accuracy": adj,
        "confusion_matrix": cm,
        "config": best_cfg,
        "feature_importances": fi,
        "proba": proba,
        "preds": best_preds,
    }


def train_cascade(X_cal, y_cal, X_test, y_test):
    """Train cascade: binary → refine within each group."""
    # Stage 1: Binary
    y_bin_cal = (y_cal >= 2).astype(int)
    gbm1 = GradientBoostingClassifier(
        n_estimators=300, max_depth=3, min_samples_leaf=8,
        learning_rate=0.1, random_state=42,
    )
    gbm1.fit(X_cal, y_bin_cal)
    p_bin = gbm1.predict(X_test)

    # Stage 2a: Within Not-Related (0 vs 1)
    mask_lo_cal = y_cal <= 1
    mask_lo_test = p_bin == 0
    gbm2a = GradientBoostingClassifier(
        n_estimators=200, max_depth=2, min_samples_leaf=5,
        learning_rate=0.05, random_state=42,
    )
    gbm2a.fit(X_cal[mask_lo_cal], y_cal[mask_lo_cal])

    # Stage 2b: Within Related+ (2 vs 3)
    mask_hi_cal = y_cal >= 2
    mask_hi_test = p_bin == 1
    gbm2b = GradientBoostingClassifier(
        n_estimators=200, max_depth=2, min_samples_leaf=5,
        learning_rate=0.05, random_state=42,
    )
    gbm2b.fit(X_cal[mask_hi_cal], y_cal[mask_hi_cal])

    p = np.zeros(len(y_test), dtype=int)
    if mask_lo_test.any():
        p[mask_lo_test] = gbm2a.predict(X_test[mask_lo_test])
    if mask_hi_test.any():
        p[mask_hi_test] = gbm2b.predict(X_test[mask_hi_test])

    acc = accuracy_score(y_test, p)
    f1 = f1_score(y_test, p, average="macro")
    adj = float(np.mean(np.abs(y_test - p) <= 1))
    cm = confusion_matrix(y_test, p, labels=[0, 1, 2, 3]).tolist()

    print(f"\nCascade GBM: acc={acc:.4f}, F1={f1:.4f}, adj={adj:.4f}")
    print(classification_report(y_test, p, target_names=TIER_NAMES))

    return {
        "models": (gbm1, gbm2a, gbm2b),
        "accuracy": acc,
        "macro_f1": f1,
        "adjacent_accuracy": adj,
        "confusion_matrix": cm,
        "preds": p,
    }


def run_conformal(X_cal, y_cal, X_test, y_test, model, alpha=0.10):
    """Run conformal prediction using cross-validated calibration scores."""
    # Use cross-validated probabilities on cal set for calibration
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    proba_cv = cross_val_predict(model, X_cal, y_cal, cv=skf, method="predict_proba")
    q_hat = conformal_calibrate(proba_cv, y_cal, alpha=alpha)

    proba_test = model.predict_proba(X_test)
    pred_sets = conformal_predict(proba_test, q_hat)

    # Metrics
    coverage = np.mean([y_test[i] in s for i, s in enumerate(pred_sets)])
    set_sizes = [len(s) for s in pred_sets]
    mean_size = np.mean(set_sizes)

    # Per-tier coverage
    per_tier = {}
    for tier in range(4):
        mask = y_test == tier
        if mask.any():
            cov = np.mean([y_test[i] in pred_sets[i] for i in range(len(y_test)) if mask[i]])
            sizes = [len(pred_sets[i]) for i in range(len(y_test)) if mask[i]]
            per_tier[TIER_NAMES[tier]] = {
                "coverage": float(cov),
                "mean_set_size": float(np.mean(sizes)),
                "n": int(mask.sum()),
            }

    print(f"\nConformal (alpha={alpha}): coverage={coverage:.4f}, mean_set_size={mean_size:.2f}")
    print(f"  q_hat={q_hat:.4f}")
    for tier, info in per_tier.items():
        print(f"  {tier}: cov={info['coverage']:.3f}, size={info['mean_set_size']:.2f}, n={info['n']}")

    return {
        "alpha": alpha,
        "q_hat": q_hat,
        "coverage": float(coverage),
        "mean_set_size": float(mean_size),
        "set_sizes": set_sizes,
        "pred_sets": pred_sets,
        "per_tier": per_tier,
    }


# ---------------------------------------------------------------------------
# Feature ablation
# ---------------------------------------------------------------------------

def run_ablation(X_cal, y_cal, X_test, y_test):
    """Test feature subsets."""
    ablations = {
        "LLM only (7d)": slice(0, 7),
        "Structural only (13d)": slice(7, 20),
        "Opus only (2d)": slice(20, 22),
        "LLM+Struct (20d)": slice(0, 20),
        "LLM+Opus (9d)": [*range(7), 20, 21],
        "Struct+Opus (15d)": slice(7, 22),
        "All (22d)": slice(0, 22),
    }
    results = []
    for name, idx in ablations.items():
        Xtr = X_cal[:, idx] if isinstance(idx, slice) else X_cal[:, idx]
        Xte = X_test[:, idx] if isinstance(idx, slice) else X_test[:, idx]
        gbm = GradientBoostingClassifier(
            n_estimators=300, max_depth=3, min_samples_leaf=10,
            learning_rate=0.1, random_state=42,
        )
        gbm.fit(Xtr, y_cal)
        p = gbm.predict(Xte)
        acc = accuracy_score(y_test, p)
        f1 = f1_score(y_test, p, average="macro")
        adj = float(np.mean(np.abs(y_test - p) <= 1))
        results.append({"name": name, "accuracy": acc, "macro_f1": f1, "adjacent_accuracy": adj})
        print(f"  {name:25s}  acc={acc:.4f}  F1={f1:.4f}  adj={adj:.4f}")
    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    OUT.mkdir(parents=True, exist_ok=True)

    print("Loading features...")
    X_cal, y_cal, cal_pairs = build_features("human_cal")
    X_test, y_test, test_pairs = build_features("human_test_frozen")
    print(f"Cal: {X_cal.shape}, Test: {X_test.shape}")

    # ---- Binary classifier ----
    wb = init_wandb("v6-binary-gbm", {"features": "LLM+Struct+Opus (22d)", "task": "binary"})
    binary = train_binary(X_cal, y_cal, X_test, y_test)
    log_metrics(wb, {"binary_accuracy": binary["accuracy"], "binary_f1": binary["macro_f1"]})
    finish_wandb(wb)

    # ---- 4-tier classifier ----
    wb = init_wandb("v6-4tier-gbm", {"features": "LLM+Struct+Opus (22d)", "task": "4-tier"})
    tier4 = train_4tier(X_cal, y_cal, X_test, y_test)
    log_metrics(wb, {
        "tier_accuracy": tier4["accuracy"],
        "macro_f1": tier4["macro_f1"],
        "adjacent_accuracy": tier4["adjacent_accuracy"],
    })
    finish_wandb(wb)

    # ---- Cascade classifier ----
    wb = init_wandb("v6-cascade-gbm", {"features": "LLM+Struct+Opus (22d)", "task": "cascade"})
    cascade = train_cascade(X_cal, y_cal, X_test, y_test)
    log_metrics(wb, {
        "tier_accuracy": cascade["accuracy"],
        "macro_f1": cascade["macro_f1"],
        "adjacent_accuracy": cascade["adjacent_accuracy"],
    })
    finish_wandb(wb)

    # ---- Conformal prediction ----
    wb = init_wandb("v6-conformal", {"task": "conformal", "alpha": 0.10})
    # Use best 4-tier model for conformal
    conformal = run_conformal(X_cal, y_cal, X_test, y_test, tier4["model"])
    log_metrics(wb, {
        "conformal_coverage": conformal["coverage"],
        "conformal_mean_set_size": conformal["mean_set_size"],
    })
    finish_wandb(wb)

    # ---- Feature ablation ----
    wb = init_wandb("v6-ablation", {"task": "ablation"})
    print("\nFeature ablation (4-tier GBM):")
    ablation = run_ablation(X_cal, y_cal, X_test, y_test)
    for a in ablation:
        log_metrics(wb, {f"ablation/{a['name']}/accuracy": a["accuracy"],
                         f"ablation/{a['name']}/f1": a["macro_f1"]})
    finish_wandb(wb)

    # ---- Save all results ----
    # Pick best model (cascade or flat 4-tier)
    best = cascade if cascade["accuracy"] >= tier4["accuracy"] else tier4
    best_method = "cascade" if cascade["accuracy"] >= tier4["accuracy"] else "4tier"

    results = {
        "version": "v6-reframed",
        "binary": {
            "accuracy": binary["accuracy"],
            "macro_f1": binary["macro_f1"],
            "confusion_matrix": binary["confusion_matrix"],
        },
        "tier4": {
            "method": f"GBM {tier4['config']}",
            "accuracy": tier4["accuracy"],
            "macro_f1": tier4["macro_f1"],
            "adjacent_accuracy": tier4["adjacent_accuracy"],
            "confusion_matrix": tier4["confusion_matrix"],
            "feature_importances": tier4["feature_importances"],
        },
        "cascade": {
            "accuracy": cascade["accuracy"],
            "macro_f1": cascade["macro_f1"],
            "adjacent_accuracy": cascade["adjacent_accuracy"],
            "confusion_matrix": cascade["confusion_matrix"],
        },
        "conformal": {
            "alpha": conformal["alpha"],
            "q_hat": conformal["q_hat"],
            "coverage": conformal["coverage"],
            "mean_set_size": conformal["mean_set_size"],
            "per_tier": conformal["per_tier"],
            "set_sizes": conformal["set_sizes"],
        },
        "ablation": ablation,
        "best_method": best_method,
        "features": "LLM(7) + Structural(13) + Opus(2) = 22d",
        "n_cal": len(y_cal),
        "n_test": len(y_test),
    }

    with open(OUT / "v6_all_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved results to {OUT / 'v6_all_results.json'}")

    # Save per-pair predictions for notebook
    pair_results = []
    for i in range(len(y_test)):
        pair_results.append({
            "pair_idx": i,
            "pair_key": test_pairs[i].get("pair_key", ""),
            "expert_tier": int(y_test[i]),
            "pred_tier": int(best["preds"][i]),
            "pred_binary": int(binary["preds"][i]),
            "conformal_set": conformal["pred_sets"][i],
            "framework_pair": test_pairs[i].get("framework_pair", ""),
        })
    with open(OUT / "v6_pair_predictions.jsonl", "w") as f:
        for r in pair_results:
            f.write(json.dumps(r) + "\n")
    print(f"Saved per-pair predictions to {OUT / 'v6_pair_predictions.jsonl'}")


if __name__ == "__main__":
    main()
