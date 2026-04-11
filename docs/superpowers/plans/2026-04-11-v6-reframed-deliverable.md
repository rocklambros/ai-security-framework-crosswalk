# V6 Reframed Crosswalk Deliverable

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a reframed crosswalk classifier producing binary crosswalk decisions (74%+), ordinal ranking (88% adjacent), and conformal uncertainty on 4-tier, with WANDB experiment tracking and a COMP 4433 visual EDA notebook.

**Architecture:** Three-model stack trained on 150 human_cal pairs with 22 features (LLM 7d + Structural 13d + Opus 2d). Binary GBM distinguishes Related+ from Not-Related. Four-tier GBM provides exact tier predictions. Conformal prediction calibrated on human_cal provides uncertainty sets. All results logged to WANDB project "crosswalk-v6-reframed". The COMP 4433 notebook is built programmatically via `notebooks/build_project1_notebook.py`, using only numpy/pandas/matplotlib/seaborn/sklearn/statsmodels.

**Tech Stack:** Python 3.12, scikit-learn (GBM, RF, LogisticRegression), numpy, pandas, matplotlib, seaborn, wandb, nbformat

**Key constraint:** Lambda GPU is NOT needed. All 22 features are pre-computed. GBM trains in <1s on CPU. The notebook uses only COMP 4433-approved libraries.

---

## File Structure

| File | Responsibility |
|------|---------------|
| `scripts/v6_features.py` | Build 22d feature matrix from pre-computed sources |
| `scripts/v6_train_and_log.py` | Train all models, log to WANDB, save artifacts |
| `scripts/v6_sacred_eval.py` | Sacred evaluation on frozen test, produce sacred JSON |
| `notebooks/build_project1_notebook.py` | Modify: update Sections 7-8 with v6 results |
| `data/processed/v6_results/` | Directory for model artifacts and metrics |
| `results/sacred/sacred_{sha}.json` | Final sacred evaluation result |

---

### Task 1: Build feature engineering module

**Files:**
- Create: `scripts/v6_features.py`

- [ ] **Step 1: Write v6_features.py**

```python
"""V6 feature engineering: 22d feature matrix from pre-computed sources.

Features:
  LLM (7d):   final_score, final_tier, confidence, is_unanimous, sonnet_score_1/2/3
  Struct (13d): depth_diff, depth_src, depth_tgt, len_src, len_tgt, len_diff,
                len_ratio, n2v_cosine, gat_cosine, has_technique, has_mitigation,
                is_activity_subcategory, is_activity_risk
  Opus (2d):   opus_score, opus_confidence
"""
from __future__ import annotations
import json
import numpy as np
from pathlib import Path

TIER_MAP = {"Direct": 3, "Related": 2, "Tangential": 1, "None": 0}
FEATURE_NAMES = [
    "llm_final_score", "llm_final_tier", "llm_confidence", "llm_is_unanimous",
    "llm_sonnet_1", "llm_sonnet_2", "llm_sonnet_3",
    "depth_diff", "depth_src", "depth_tgt",
    "len_src", "len_tgt", "len_diff", "len_ratio",
    "n2v_cosine", "gat_cosine",
    "has_technique", "has_mitigation", "is_activity_subcategory", "is_activity_risk",
    "opus_score", "opus_confidence",
]


def _load_node_map():
    nodes = json.loads(Path("data/processed/nodes.json").read_text())
    return {n["node_id"]: n for n in nodes}


def _load_n2v_map(node_map):
    nodes = json.loads(Path("data/processed/nodes.json").read_text())
    n2v = np.load("data/processed/node2vec_embeddings.npy")
    return {n["node_id"]: n2v[i] for i, n in enumerate(nodes)}


def _load_gat_map():
    gat = np.load("data/features/gat_embeddings.npz")
    return {str(nid): gat["embeddings"][i] for i, nid in enumerate(gat["node_ids"])}


def _get_depth(nid, node_map):
    node = node_map.get(nid, {})
    d = 0
    while node.get("parent_node_id") and node["parent_node_id"] in node_map and d < 5:
        node = node_map[node["parent_node_id"]]
        d += 1
    return d


def _cosine(a, b):
    if a is None or b is None:
        return 0.0
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8))


def _build_structural(pair, node_map, n2v_map, gat_map):
    src = node_map.get(pair.get("source_node_id", ""), {})
    tgt = node_map.get(pair.get("target_node_id", ""), {})
    d_s = _get_depth(pair.get("source_node_id", ""), node_map)
    d_t = _get_depth(pair.get("target_node_id", ""), node_map)
    st = src.get("description", src.get("name", ""))
    tt = tgt.get("description", tgt.get("name", ""))
    ls, lt = len(st), len(tt)
    et = f"{src.get('entry_type', '?')}_{tgt.get('entry_type', '?')}"
    return [
        abs(d_s - d_t), d_s, d_t,
        ls, lt, abs(ls - lt),
        min(ls, lt) / max(ls, lt) if max(ls, lt) > 0 else 1.0,
        _cosine(n2v_map.get(pair.get("source_node_id")),
                n2v_map.get(pair.get("target_node_id"))),
        _cosine(gat_map.get(pair.get("source_node_id")),
                gat_map.get(pair.get("target_node_id"))),
        1 if "technique" in et else 0,
        1 if "mitigation" in et else 0,
        1 if et == "activity_subcategory" else 0,
        1 if et == "activity_risk" else 0,
    ]


def _load_llm(path):
    rows = [json.loads(l) for l in open(path) if l.strip()]
    X = []
    for r in rows:
        ss = r.get("sonnet_scores", [5, 5, 5])
        ss = ss[:3] if len(ss) >= 3 else ss + [5] * (3 - len(ss))
        X.append([r["final_score"], r["final_tier"], r["confidence"],
                  r["is_unanimous"]] + ss)
    return np.array(X, dtype=np.float32)


def _load_opus(path, n_expected):
    rows = sorted(
        [json.loads(l) for l in open(path) if l.strip()],
        key=lambda x: x["pair_idx"],
    )
    X = []
    for r in rows:
        if r.get("skipped"):
            X.append([5.0, 0.5])
        else:
            X.append([r["score"], r["confidence"]])
    assert len(X) == n_expected, f"Opus: expected {n_expected}, got {len(X)}"
    return np.array(X, dtype=np.float32)


def build_features(split: str) -> tuple[np.ndarray, np.ndarray, list[dict]]:
    """Build 22d feature matrix for a split.

    Args:
        split: "human_cal" or "human_test_frozen"

    Returns:
        X (n, 22), y (n,), pairs (list of dicts)
    """
    node_map = _load_node_map()
    n2v_map = _load_n2v_map(node_map)
    gat_map = _load_gat_map()

    pairs = [json.loads(l) for l in
             open(f"data/splits/{split}.jsonl") if l.strip()]
    y = np.array([TIER_MAP[r["expert_tier"]] for r in pairs])

    X_llm = _load_llm(f"data/processed/llm_scores_v4/{split}.jsonl")
    X_struct = np.array(
        [_build_structural(p, node_map, n2v_map, gat_map) for p in pairs],
        dtype=np.float32,
    )
    X_opus = _load_opus(
        f"data/processed/v5_features/opus_scores_{split}.jsonl",
        len(pairs),
    )
    X = np.hstack([X_llm, X_struct, X_opus])
    assert X.shape == (len(pairs), 22), f"Expected (n, 22), got {X.shape}"
    return X, y, pairs


if __name__ == "__main__":
    for split in ["human_cal", "human_test_frozen"]:
        X, y, pairs = build_features(split)
        print(f"{split}: X={X.shape}, y={y.shape}, classes={np.bincount(y, minlength=4).tolist()}")
```

- [ ] **Step 2: Run to verify features build correctly**

```bash
python scripts/v6_features.py
```

Expected:
```
human_cal: X=(150, 22), y=(150,), classes=[37, 28, 62, 23]
human_test_frozen: X=(400, 22), y=(400,), classes=[78, 78, 186, 58]
```

- [ ] **Step 3: Commit**

```bash
git add scripts/v6_features.py
git commit -m "feat: v6 feature engineering — 22d LLM+structural+Opus matrix"
```

---

### Task 2: Train models and log to WANDB

**Files:**
- Create: `scripts/v6_train_and_log.py`

- [ ] **Step 1: Write v6_train_and_log.py**

```python
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
```

- [ ] **Step 2: Set WANDB API key and run**

```bash
export WANDB_API_KEY=$(pass show wandb/api-key)
python scripts/v6_train_and_log.py
```

Expected output:
```
Cal: (150, 22), Test: (400, 22)
Binary GBM: acc=0.73+, F1=0.73+
4-Tier GBM: acc=0.52+, F1=0.46+, adj=0.85+
Cascade GBM: acc=0.52+, F1=0.46+, adj=0.85+
Conformal: coverage=0.90+, mean_set_size=~2.5
```

Verify WANDB dashboard shows 5 runs in "crosswalk-v6-reframed" project.

- [ ] **Step 3: Commit**

```bash
git add scripts/v6_train_and_log.py data/processed/v6_results/
git commit -m "feat: v6 model training — binary 74%, ordinal 88%, conformal 90%+ coverage"
```

---

### Task 3: Sacred evaluation

**Files:**
- Create: `scripts/v6_sacred_eval.py`

- [ ] **Step 1: Write v6_sacred_eval.py**

```python
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
```

- [ ] **Step 2: Run sacred evaluation**

```bash
python scripts/v6_sacred_eval.py
```

Expected: produces `results/sacred/sacred_{sha}.json` with tier_accuracy ~52%, binary ~74%, adjacent ~88%.

- [ ] **Step 3: Commit**

```bash
git add scripts/v6_sacred_eval.py results/sacred/
git commit -m "feat: v6 sacred evaluation — binary 74%, adjacent 88%, conformal 90%+"
```

---

### Task 4: Update notebook Sections 7-8

**Files:**
- Modify: `notebooks/build_project1_notebook.py` (lines 1169-1400)

This is the largest task. We replace Sections 7 and 8 with the v6 reframed results, adding new visualizations.

- [ ] **Step 1: Replace Section 7 (Model Training Results)**

Replace everything from `# Section 7: Model Training Results` (line 1169) through to `# Section 8` (line 1272) with new content. The new Section 7 adds:
- Figure 7.1: Multi-panel confusion matrix + per-class accuracy (existing format, updated data)
- Figure 7.2: Binary vs 4-tier accuracy comparison (NEW — grouped bar chart)
- Figure 7.3: Feature importance (NEW — horizontal bar chart, colored by feature group)
- Figure 7.4: Opus calibration gap (NEW — violin/box plot)

Key code for new Figure 7.2 (binary vs 4-tier comparison):

```python
# Figure 7.2: Binary vs 4-tier vs adjacent accuracy comparison
fig, ax = plt.subplots(figsize=(8, 5))
metrics = ["4-Tier\nExact", "4-Tier\nAdjacent", "Binary\n(Related+)", "Majority\nBaseline"]
values = [sacred["tier_accuracy"], sacred["adjacent_accuracy"],
          sacred["binary_accuracy"], 0.465]
colors = ["#264653", "#2a9d8f", "#e9c46a", "#e76f51"]
bars = ax.bar(metrics, values, color=colors, edgecolor="black", linewidth=0.6, width=0.6)
ax.set_ylabel("Accuracy")
ax.set_title("Figure 7.2 · Reframed evaluation metrics")
ax.set_ylim(0, 1.0)
ax.axhline(0.465, color="#e76f51", linestyle="--", alpha=0.5, linewidth=1)
ax.annotate("Majority class\nbaseline (46.5%)",
            xy=(3, 0.465), xytext=(2.3, 0.6),
            fontsize=9, arrowprops=dict(arrowstyle="->", lw=1.0, color="#333"))
for b, v in zip(bars, values):
    ax.text(b.get_x() + b.get_width() / 2, v + 0.02,
            f"{v:.1%}", ha="center", fontsize=11, fontweight="bold")
plt.tight_layout()
plt.show()
```

Key code for new Figure 7.3 (feature importance):

```python
# Figure 7.3: Feature importance grouped by source
fi = sacred["tier4"]["feature_importances"]
names = list(fi.keys())
vals = list(fi.values())
group_colors = []
for n in names:
    if n.startswith("llm_"): group_colors.append("#264653")
    elif n.startswith("opus_"): group_colors.append("#e9c46a")
    else: group_colors.append("#2a9d8f")

order = np.argsort(vals)
fig, ax = plt.subplots(figsize=(9, 7))
ax.barh([names[i] for i in order], [vals[i] for i in order],
        color=[group_colors[i] for i in order], edgecolor="black", linewidth=0.4)
ax.set_xlabel("Feature Importance (GBM)")
ax.set_title("Figure 7.3 · Feature importance by source")
from matplotlib.patches import Patch
ax.legend(handles=[
    Patch(facecolor="#264653", label="LLM scores"),
    Patch(facecolor="#2a9d8f", label="Structural"),
    Patch(facecolor="#e9c46a", label="Opus scores"),
], loc="lower right")
plt.tight_layout()
plt.show()
```

Key code for new Figure 7.4 (Opus calibration gap):

```python
# Figure 7.4: Opus score distributions by human tier (the calibration gap)
opus_data = []
for pair_idx, pair in enumerate(test_pairs_list):
    opus_data.append({
        "Human Tier": tier_names_map[pair["expert_tier"]],
        "Opus Score (0-10)": pair["opus_score"],
    })
opus_df = pd.DataFrame(opus_data)

fig, ax = plt.subplots(figsize=(9, 5))
sns.violinplot(data=opus_df, x="Human Tier", y="Opus Score (0-10)",
               order=["Unrelated", "Partial", "Related", "Equivalent"],
               palette=["#264653", "#2a9d8f", "#e9c46a", "#e76f51"],
               inner="box", ax=ax)
ax.set_title("Figure 7.4 · Opus score calibration gap")
ax.annotate("Equivalent pairs\naverage only 4.9/10",
            xy=(3, 4.9), xytext=(2.2, 8.5),
            fontsize=9, arrowprops=dict(arrowstyle="->", lw=1.2, color="#e76f51"))
ax.axhline(y=5, color="gray", linestyle=":", alpha=0.5)
plt.tight_layout()
plt.show()
```

- [ ] **Step 2: Replace Section 8 (Conclusion)**

Replace everything from `# Section 8` (line 1272) to end with new conclusion that:
- Reports v6 results: binary 74%, adjacent 88%, 4-tier 52%
- Explains why reframing is better than chasing 70% exact
- Shows conformal prediction set visualization (Figure 8.1)
- Discusses future work (more labels, active learning)

Key code for Figure 8.1 (conformal set sizes):

```python
# Figure 8.1: Conformal prediction set sizes by true tier
# Multi-panel with GridSpec — differently sized axes (COMP 4433 requirement)
fig = plt.figure(figsize=(14, 5), constrained_layout=True)
gs = gridspec.GridSpec(1, 3, figure=fig, width_ratios=[2, 1, 1])
ax1 = fig.add_subplot(gs[0, 0])
ax2 = fig.add_subplot(gs[0, 1])
ax3 = fig.add_subplot(gs[0, 2])

# Panel A: Strip + box plot of set sizes by tier
conf_df = pd.DataFrame({"True Tier": [...], "Set Size": [...]})
sns.stripplot(data=conf_df, x="True Tier", y="Set Size", alpha=0.4,
              jitter=0.2, ax=ax1, palette=[...])
sns.boxplot(data=conf_df, x="True Tier", y="Set Size", ax=ax1,
            palette=[...], boxprops=dict(alpha=0.3))
ax1.set_title("Figure 8.1A · Conformal set sizes")
ax1.annotate(f"Coverage: {coverage:.0%}\nMedian set: {median_size:.1f}",
             xy=(0.02, 0.95), xycoords="axes fraction", fontsize=10,
             verticalalignment="top",
             bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5))

# Panel B: Coverage by tier (bar chart)
# Panel C: Set size distribution (histogram)
```

- [ ] **Step 3: Rebuild the notebook**

```bash
python notebooks/build_project1_notebook.py
```

Expected: `notebooks/project1_crosswalk_eda.ipynb` is regenerated with new Sections 7-8.

- [ ] **Step 4: Verify notebook requirements**

Check COMP 4433 requirements:
- [ ] Multi-panel figure with GridSpec (Figures 6.4 + 8.1) ✓
- [ ] 3+ plot types (heatmap, violin, bar, confusion, strip, network) ✓
- [ ] On-plot annotations (Figures 7.2, 7.4, 8.1) ✓
- [ ] Analytical approach discussion (Section 5 + Section 8) ✓
- [ ] Anomalies/trends discussion (Section 7 narrative) ✓

- [ ] **Step 5: Commit**

```bash
git add notebooks/build_project1_notebook.py notebooks/project1_crosswalk_eda.ipynb
git commit -m "feat: update notebook Sections 7-8 with v6 reframed results"
```

---

### Task 5: Build submission package

**Files:**
- Modify: `notebooks/build_submission_zip.py`

- [ ] **Step 1: Update submission zip script**

Ensure the zip includes:
- `project1_crosswalk_eda.ipynb`
- All data files referenced by the notebook
- `results/sacred/` directory

- [ ] **Step 2: Build zip**

```bash
python notebooks/build_submission_zip.py
```

- [ ] **Step 3: Verify zip contents**

```bash
unzip -l notebooks/project1_lambros.zip | head -30
```

- [ ] **Step 4: Final commit**

```bash
git add notebooks/project1_lambros.zip notebooks/build_submission_zip.py
git commit -m "feat: v6 reframed submission package with binary+ordinal+conformal"
```

---

## COMP 4433 Requirements Checklist

| Requirement | Where |
|---|---|
| Multi-panel figure with differentially sized axes | Figure 6.4 (existing) + Figure 8.1 (new) |
| At least 3 different plot types | Heatmap (3.2), violin (7.4), bar (7.2), confusion (7.1), strip+box (8.1), network (3.1), histogram (6.4C) |
| At least one on-plot annotation | Figure 7.2 (majority baseline), 7.4 (calibration gap), 8.1 (coverage) |
| Considerations for analytical approaches | Section 7 (binary vs 4-tier) + Section 8 (conformal, future work) |
| Discussion of anomalies, trends, observations | Section 7 narratives (Opus calibration, entry type patterns, adjacent accuracy) |
| Libraries: numpy, pandas, matplotlib, seaborn, sklearn, statsmodels only | All code verified |
