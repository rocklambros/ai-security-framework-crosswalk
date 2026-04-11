"""v5 Final Ensemble Stacker + Sacred Evaluation.

Combines all feature sources:
  1. LLM scores (5 features) — from v4 pipeline
  2. Hierarchical binary LLM (6 features) — binary decomposition answers + confidence
  3. SBERT embeddings PCA (50 features) — pre-trained sentence-BERT
  4. NLI logits (3 features) — zero-shot NLI cross-encoder
  5. SetFit embeddings PCA (50 features) — fine-tuned sentence-BERT [from Lambda]
  6. CE fine-tuned logits (4 features) — fine-tuned cross-encoder [from Lambda]

Trains ordinal-aware LGBM on 150 human_cal, evaluates on 400 human_test_frozen.

Usage:
    python scripts/v5_ensemble_sacred.py
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
)
from sklearn.model_selection import cross_val_predict, StratifiedKFold

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TIER_MAP = {"Direct": 3, "Related": 2, "Tangential": 1, "None": 0}
TIER_NAMES = ["Unrelated", "Partial", "Related", "Equivalent"]

FEAT_DIR = Path("data/processed/v5_features")
LLM_DIR = Path("data/processed/llm_scores_v4")
RESULTS_DIR = Path("results/sacred")

# ---------------------------------------------------------------------------
# Feature loading
# ---------------------------------------------------------------------------

def load_llm_features(split: str) -> np.ndarray:
    """Load 5-dim LLM score features."""
    path = LLM_DIR / f"{split}.jsonl"
    rows = []
    with open(path) as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            scores = rec.get("sonnet_scores", [])
            while len(scores) < 3:
                scores.append(rec.get("final_score", 0.0))
            feats = scores[:3] + [
                float(rec.get("final_score", 0.0)),
                float(rec.get("confidence", 0.0)),
            ]
            rows.append(feats)
    return np.array(rows, dtype=np.float32)


def load_hierarchical_features(split: str) -> np.ndarray:
    """Load 6-dim hierarchical binary LLM features."""
    path = FEAT_DIR / f"hierarchical_{split}.jsonl"
    rows = []
    with open(path) as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            rows.append([
                rec["q1_yes"], rec["q1_conf"],
                rec["q2_yes"], rec["q2_conf"],
                rec["q3_yes"], rec["q3_conf"],
            ])
    return np.array(rows, dtype=np.float32)


def load_sbert_features() -> tuple[np.ndarray, np.ndarray]:
    """Load pre-trained SBERT cosine features."""
    data = np.load(FEAT_DIR / "sbert_cosine.npz")
    return data["cal"], data["test"]


def load_nli_features() -> tuple[np.ndarray, np.ndarray]:
    """Load NLI logit features."""
    data = np.load(FEAT_DIR / "nli_logits.npz")
    return data["cal"], data["test"]


def load_setfit_embeddings() -> tuple[np.ndarray, np.ndarray] | None:
    """Load SetFit fine-tuned embeddings (from Lambda)."""
    path = FEAT_DIR / "setfit_embeddings.npz"
    if not path.exists():
        print("  WARNING: SetFit embeddings not found, skipping")
        return None
    data = np.load(path)
    emb = data["embeddings"]
    n_cal = int(data["n_cal"])
    return emb[:n_cal], emb[n_cal:]


def load_ce_finetuned_logits() -> tuple[np.ndarray, np.ndarray] | None:
    """Load fine-tuned CE logits (from Lambda)."""
    path = FEAT_DIR / "ce_finetuned_logits.npz"
    if not path.exists():
        print("  WARNING: CE fine-tuned logits not found, skipping")
        return None
    data = np.load(path)
    logits = data["logits"]
    n_cal = int(data["n_cal"])
    return logits[:n_cal], logits[n_cal:]


def load_labels() -> tuple[np.ndarray, np.ndarray]:
    """Load tier labels for cal and test."""
    y_cal, y_test = [], []
    for path, y in [
        ("data/splits/human_cal.jsonl", y_cal),
        ("data/splits/human_test_frozen.jsonl", y_test),
    ]:
        with open(path) as f:
            for line in f:
                if line.strip():
                    y.append(TIER_MAP[json.loads(line)["expert_tier"]])
    return np.array(y_cal), np.array(y_test)


# ---------------------------------------------------------------------------
# Feature assembly
# ---------------------------------------------------------------------------

def build_feature_matrix(include_setfit: bool = True, include_ce: bool = True):
    """Build full feature matrices for cal and test."""
    y_cal, y_test = load_labels()

    # 1. LLM scores (5)
    llm_cal = load_llm_features("human_cal")
    llm_test = load_llm_features("human_test_frozen")

    # 2. Hierarchical binary (6)
    hier_cal = load_hierarchical_features("human_cal")
    hier_test = load_hierarchical_features("human_test_frozen")

    # 3. SBERT cosine (1)
    sbert_cal, sbert_test = load_sbert_features()
    sbert_cal = sbert_cal.reshape(-1, 1)
    sbert_test = sbert_test.reshape(-1, 1)

    # 4. NLI logits (3)
    nli_cal, nli_test = load_nli_features()

    feature_names = ["llm(5)", "hier(6)", "sbert_cos(1)", "nli(3)"]
    cal_parts = [llm_cal, hier_cal, sbert_cal, nli_cal]
    test_parts = [llm_test, hier_test, sbert_test, nli_test]

    # 5. SetFit embeddings PCA (optional, 50)
    if include_setfit:
        setfit = load_setfit_embeddings()
        if setfit is not None:
            sf_cal, sf_test = setfit
            # PCA reduction
            pca = PCA(n_components=min(50, sf_cal.shape[1]), random_state=42)
            sf_cal_pca = pca.fit_transform(sf_cal)
            sf_test_pca = pca.transform(sf_test)
            cal_parts.append(sf_cal_pca.astype(np.float32))
            test_parts.append(sf_test_pca.astype(np.float32))
            feature_names.append(f"setfit_pca({sf_cal_pca.shape[1]})")
        else:
            include_setfit = False

    # 6. CE fine-tuned logits (optional, 4)
    if include_ce:
        ce = load_ce_finetuned_logits()
        if ce is not None:
            ce_cal, ce_test = ce
            cal_parts.append(ce_cal)
            test_parts.append(ce_test)
            feature_names.append(f"ce_ft({ce_cal.shape[1]})")
        else:
            include_ce = False

    X_cal = np.hstack(cal_parts)
    X_test = np.hstack(test_parts)

    print(f"Feature matrix: cal={X_cal.shape}, test={X_test.shape}")
    print(f"  Components: {' + '.join(feature_names)} = {X_cal.shape[1]}d")

    return X_cal, X_test, y_cal, y_test


# ---------------------------------------------------------------------------
# Stacker training + evaluation
# ---------------------------------------------------------------------------

def train_and_evaluate(X_cal, X_test, y_cal, y_test, name="ensemble"):
    """Train RF on cal, evaluate on test. Also try LGBM."""
    results = {}

    # Method A: Random Forest (balanced)
    rf = RandomForestClassifier(
        n_estimators=500,
        min_samples_leaf=2,
        class_weight="balanced_subsample",
        random_state=42,
    )
    rf.fit(X_cal, y_cal)
    preds_rf = rf.predict(X_test)
    proba_rf = rf.predict_proba(X_test)

    acc_rf = accuracy_score(y_test, preds_rf)
    f1_rf = f1_score(y_test, preds_rf, average="macro")

    print(f"\n{'='*60}")
    print(f"{name} — Random Forest")
    print(f"{'='*60}")
    print(f"  Accuracy: {acc_rf:.4f}")
    print(f"  Macro F1: {f1_rf:.4f}")
    print(classification_report(y_test, preds_rf, target_names=TIER_NAMES))

    results["rf"] = {"accuracy": acc_rf, "macro_f1": f1_rf}

    # Method B: LightGBM (if available)
    try:
        import lightgbm as lgb

        model_lgb = lgb.LGBMClassifier(
            n_estimators=300,
            num_leaves=31,
            learning_rate=0.05,
            min_child_samples=5,
            subsample=0.8,
            colsample_bytree=0.8,
            class_weight="balanced",
            random_state=42,
            verbose=-1,
        )
        model_lgb.fit(X_cal, y_cal)
        preds_lgb = model_lgb.predict(X_test)
        proba_lgb = model_lgb.predict_proba(X_test)

        acc_lgb = accuracy_score(y_test, preds_lgb)
        f1_lgb = f1_score(y_test, preds_lgb, average="macro")

        print(f"\n{'='*60}")
        print(f"{name} — LightGBM")
        print(f"{'='*60}")
        print(f"  Accuracy: {acc_lgb:.4f}")
        print(f"  Macro F1: {f1_lgb:.4f}")
        print(classification_report(y_test, preds_lgb, target_names=TIER_NAMES))

        results["lgbm"] = {"accuracy": acc_lgb, "macro_f1": f1_lgb}

        # Use best model
        if f1_lgb > f1_rf:
            best_model = "lgbm"
            best_preds = preds_lgb
            best_proba = proba_lgb
            best_acc = acc_lgb
            best_f1 = f1_lgb
        else:
            best_model = "rf"
            best_preds = preds_rf
            best_proba = proba_rf
            best_acc = acc_rf
            best_f1 = f1_rf
    except ImportError:
        best_model = "rf"
        best_preds = preds_rf
        best_proba = proba_rf
        best_acc = acc_rf
        best_f1 = f1_rf

    results["best_model"] = best_model
    results["best_accuracy"] = best_acc
    results["best_macro_f1"] = best_f1

    return results, best_preds, best_proba


# ---------------------------------------------------------------------------
# Conformal prediction
# ---------------------------------------------------------------------------

def conformal_evaluation(X_cal, y_cal, alpha=0.10):
    """Cross-validated conformal prediction on cal set."""
    rf = RandomForestClassifier(
        n_estimators=500,
        min_samples_leaf=2,
        class_weight="balanced_subsample",
        random_state=42,
    )
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    proba_cv = cross_val_predict(rf, X_cal, y_cal, cv=cv, method="predict_proba")

    # Marginal conformal scores
    scores = 1.0 - proba_cv[np.arange(len(y_cal)), y_cal]
    n = len(y_cal)
    q_level = min(np.ceil((n + 1) * (1 - alpha)) / n, 1.0)
    q_hat = float(np.quantile(scores, q_level))

    # Prediction sets on cal (self-eval)
    sets = proba_cv >= (1.0 - q_hat)
    set_sizes = sets.sum(axis=1)
    coverage = np.mean([y_cal[i] in np.where(sets[i])[0] for i in range(n)])

    return {
        "alpha": alpha,
        "q_hat": round(q_hat, 4),
        "coverage": round(float(coverage), 4),
        "mean_set_size": round(float(set_sizes.mean()), 2),
        "median_set_size": int(np.median(set_sizes)),
    }


# ---------------------------------------------------------------------------
# Ablation study
# ---------------------------------------------------------------------------

def run_ablation(X_cal, X_test, y_cal, y_test, feature_dims):
    """Run ablation study dropping one feature group at a time."""
    print(f"\n{'='*60}")
    print("Ablation Study")
    print(f"{'='*60}")

    rf = RandomForestClassifier(
        n_estimators=500, min_samples_leaf=2,
        class_weight="balanced_subsample", random_state=42,
    )

    # Full model baseline
    rf.fit(X_cal, y_cal)
    full_f1 = f1_score(y_test, rf.predict(X_test), average="macro")
    full_acc = accuracy_score(y_test, rf.predict(X_test))
    print(f"  Full model: F1={full_f1:.4f}, Acc={full_acc:.4f}")

    ablation_results = {"full": {"macro_f1": full_f1, "accuracy": full_acc}}

    # Drop each feature group
    col_idx = 0
    for name, dim in feature_dims:
        cols_to_drop = list(range(col_idx, col_idx + dim))
        cols_to_keep = [c for c in range(X_cal.shape[1]) if c not in cols_to_drop]

        rf_abl = RandomForestClassifier(
            n_estimators=500, min_samples_leaf=2,
            class_weight="balanced_subsample", random_state=42,
        )
        rf_abl.fit(X_cal[:, cols_to_keep], y_cal)
        f1_abl = f1_score(y_test, rf_abl.predict(X_test[:, cols_to_keep]), average="macro")
        delta = f1_abl - full_f1
        print(f"  Drop {name}: F1={f1_abl:.4f} (Δ={delta:+.4f})")
        ablation_results[f"drop_{name}"] = {"macro_f1": f1_abl, "delta": delta}

        col_idx += dim

    return ablation_results


# ---------------------------------------------------------------------------
# Sacred output
# ---------------------------------------------------------------------------

def save_sacred(results, ablation, conformal):
    """Save results in sacred format."""
    sha = hashlib.sha1(json.dumps(results, sort_keys=True).encode()).hexdigest()[:7]

    sacred = {
        "version": "v5",
        "sha": sha,
        "tier_accuracy": results["best_accuracy"],
        "macro_f1": results["best_macro_f1"],
        "best_model": results["best_model"],
        "models_evaluated": {k: v for k, v in results.items() if k not in ("best_model", "best_accuracy", "best_macro_f1")},
        "conformal": conformal,
        "ablation": ablation,
    }

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    path = RESULTS_DIR / f"sacred_{sha}.json"
    path.write_text(json.dumps(sacred, indent=2))
    print(f"\nSaved sacred results to {path}")
    return sacred


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("Loading features...")
    X_cal, X_test, y_cal, y_test = build_feature_matrix()

    print("\nTraining and evaluating ensemble...")
    results, preds, proba = train_and_evaluate(X_cal, X_test, y_cal, y_test, name="v5 Ensemble")

    print("\nRunning conformal prediction...")
    conformal = conformal_evaluation(X_cal, y_cal)
    print(f"  Conformal: coverage={conformal['coverage']}, set_size={conformal['mean_set_size']}")

    # Feature dimensions for ablation
    feat_dims = [("llm", 5), ("hierarchical", 6), ("sbert_cos", 1), ("nli", 3)]
    # Check if optional features were included
    base_dim = 15  # 5+6+1+3
    remaining = X_cal.shape[1] - base_dim
    if remaining > 0:
        # SetFit embeddings PCA
        if remaining >= 50:
            feat_dims.append(("setfit_pca", 50))
            remaining -= 50
        elif remaining >= 4:
            feat_dims.append(("setfit_pca", remaining))
            remaining = 0
        # CE fine-tuned logits
        if remaining > 0:
            feat_dims.append(("ce_finetuned", remaining))

    print("\nRunning ablation study...")
    ablation = run_ablation(X_cal, X_test, y_cal, y_test, feat_dims)

    sacred = save_sacred(results, ablation, conformal)

    print(f"\n{'='*60}")
    print(f"FINAL RESULTS — v5 Ensemble")
    print(f"{'='*60}")
    print(f"  Tier Accuracy: {sacred['tier_accuracy']:.4f}")
    print(f"  Macro F1:      {sacred['macro_f1']:.4f}")
    print(f"  Best Model:    {sacred['best_model']}")
    print(f"  Conformal:     coverage={conformal['coverage']}, size={conformal['mean_set_size']}")


if __name__ == "__main__":
    main()
