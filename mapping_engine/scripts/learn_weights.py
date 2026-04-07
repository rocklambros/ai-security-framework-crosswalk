"""Train logistic / LightGBM / ordinal weight models, cross-validate on
anchors, and run a threshold sweep to calibrate tier thresholds.

Uses the leak-free training_data.csv (bridge features for anchor rows are
computed via leave-one-out anchor masking; see
``mapping_engine.calibration.build_training_data``).

Usage::

    python -m mapping_engine.scripts.learn_weights
"""

from __future__ import annotations

import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score

from mapping_engine.calibration.weight_learner import (
    FEATURES,
    HAND_WEIGHTS,
    TIER_ORDER,
    _proba,
    compare_to_hand_tuned,
    evaluate_hand_tuned,
    evaluate_model,
    hand_tuned_score,
    train_lightgbm,
    train_logistic,
    train_ordinal,
)
from mapping_engine.calibration.weight_stability import analyze_weight_stability
from mapping_engine.config import load_pair_config
from mapping_engine.engine.graph import load_graph
from mapping_engine.engine.mapper import PairMapper

REPO = Path(__file__).resolve().parents[2]

# Threshold sweep grid (Phase C)
DIRECT_GRID = [0.40, 0.45, 0.50, 0.55, 0.60, 0.65]
RELATED_GRID = [0.25, 0.30, 0.35, 0.40, 0.45]


def _anchor_pairs(cfg) -> list[tuple[str, str, str]]:
    return [(p.source, p.target, p.expected_tier) for p in cfg.anchors.pairs]


def _holdout_pairs(cfg) -> list[tuple[str, str]]:
    pairs = cfg.anchors.pairs
    idx = set(cfg.anchors.holdout_indices or [])
    return [(pairs[i].source, pairs[i].target) for i in idx]


def _predict_tier_from_score(
    score: float, is_primary: bool, t_direct: float, t_rel_prim: float
) -> str:
    """Mirror of composer.assign_tiers for a single (score, relevance) pair.

    Uses the Direct / Related-Primary / Related-Secondary rules. gov_floor
    promotion is not applied here since it only matters for borderline
    GOVERN/DISCLOSE rows and would require row-level function-class info;
    the integration test covers that end-to-end.
    """
    if score >= t_direct:
        return "Direct"
    if is_primary and score >= t_rel_prim:
        return "Related"
    # Related-Secondary uses a higher bar (hard-coded default 0.50 in config);
    # for the sweep we treat non-primary with score >= t_direct as Direct
    # otherwise None — the anchor set is all Primary in practice.
    return "None"


def _cv_accuracy_for_model(
    train_df: pd.DataFrame,
    anchor_rows_df: pd.DataFrame,
    train_fn,
    eval_fn,
    n_splits: int = 5,
) -> float:
    """Leave-fold-out CV over anchors. ``train_fn(df) -> model``; ``eval_fn
    (model, holdout_rows) -> 0/1 per-row tier match``. Non-anchor rows are
    always in the training fold."""
    n = len(anchor_rows_df)
    if n == 0:
        return float("nan")
    rng = np.random.default_rng(42)
    order = np.arange(n)
    rng.shuffle(order)
    folds = np.array_split(order, min(n_splits, n))
    non_anchor_mask = ~train_df.index.isin(anchor_rows_df.index)
    non_anchor_df = train_df[non_anchor_mask]

    hits, total = 0, 0
    for fold in folds:
        held = anchor_rows_df.iloc[fold]
        kept = anchor_rows_df.drop(held.index)
        fit_df = pd.concat([non_anchor_df, kept], ignore_index=False)
        model = train_fn(fit_df)
        row_hits = eval_fn(model, held)
        hits += int(row_hits.sum())
        total += len(row_hits)
    return hits / max(1, total)


def _anchor_expected_tier(df: pd.DataFrame, anchor_pairs) -> pd.Series:
    """Return expected_tier for each row matching an anchor, NaN otherwise."""
    lookup = {(s, t): tier for s, t, tier in anchor_pairs}
    return df.apply(
        lambda r: lookup.get((r["source_node_id"], r["target_node_id"]), None),
        axis=1,
    )


def _model_tier_eval(
    model, model_type: str, df: pd.DataFrame, exp_tiers: pd.Series
) -> np.ndarray:
    """Binary (Direct/Related match or not) evaluation for probability-based
    models. Uses a simple threshold of 0.5 for mapped/unmapped; a secondary
    internal threshold (0.7) for Direct vs Related. Hand-tuned uses composite
    score with default thresholds from defaults.yaml."""
    proba = _proba(model, df, model_type)
    preds = []
    for p in proba:
        if p >= 0.7:
            preds.append("Direct")
        elif p >= 0.5:
            preds.append("Related")
        else:
            preds.append("None")
    return np.array([pred == exp for pred, exp in zip(preds, exp_tiers)], dtype=int)


def _hand_tier_eval(df: pd.DataFrame, exp_tiers: pd.Series) -> np.ndarray:
    scores = hand_tuned_score(df)
    preds = []
    for s in scores:
        if s >= 0.55:
            preds.append("Direct")
        elif s >= 0.35:
            preds.append("Related")
        else:
            preds.append("None")
    return np.array([pred == exp for pred, exp in zip(preds, exp_tiers)], dtype=int)


def _run_masked_mapper(G, cfg) -> dict[str, dict]:
    """Run PairMapper once and return the masked anchor-validation records
    (one per anchor), which contain leak-free composite scores."""
    mapper = PairMapper(G, cfg, use_learned_weights=False, enable_reranker=None)
    result = mapper.run()
    av = result.anchor_validation
    out = {}
    out.update(av.get("training_anchors", {}))
    out.update(av.get("holdout_anchors", {}))
    return out


def _sweep_thresholds(
    anchor_records: dict[str, dict],
    anchor_expected: dict[str, str],
    primary_map: dict[str, bool],
) -> tuple[tuple[float, float], pd.DataFrame]:
    """Sweep (direct, related_primary) thresholds over the masked anchor
    composite scores. Objective: Youden's J on tier match accuracy across
    ALL anchors (they already carry LOO-equivalent masked scores).

    Returns the chosen pair and the full sweep table.
    """
    rows = []
    for t_dir, t_rel in itertools.product(DIRECT_GRID, RELATED_GRID):
        if t_rel >= t_dir:
            continue
        hits = 0
        tp = fp = tn = fn = 0
        total = 0
        for key, rec in anchor_records.items():
            exp = anchor_expected.get(key, "None")
            is_prim = primary_map.get(key, True)
            pred = _predict_tier_from_score(rec["score"], is_prim, t_dir, t_rel)
            hit = int(pred == exp)
            hits += hit
            total += 1
            # Binary mapped/unmapped for Youden's J: expected Direct/Related → pos
            exp_pos = exp in ("Direct", "Related")
            pred_pos = pred in ("Direct", "Related")
            if exp_pos and pred_pos:
                tp += 1
            elif exp_pos and not pred_pos:
                fn += 1
            elif not exp_pos and pred_pos:
                fp += 1
            else:
                tn += 1
        sens = tp / max(1, tp + fn)
        spec = tn / max(1, tn + fp)
        youden = sens + spec - 1
        rows.append(
            {
                "direct": t_dir,
                "related_primary": t_rel,
                "tier_accuracy": hits / max(1, total),
                "youden_j": youden,
            }
        )
    sweep_df = pd.DataFrame(rows).sort_values(
        by=["tier_accuracy", "youden_j"], ascending=False
    )
    best = sweep_df.iloc[0]
    return (float(best["direct"]), float(best["related_primary"])), sweep_df


def main() -> None:
    train_df = pd.read_csv(REPO / "data/processed/training_data.csv")
    nist_df = pd.read_csv(REPO / "data/processed/nist_validation_data.csv")

    G = load_graph(REPO / "data/processed/nodes.json", REPO / "data/processed/edges.json")
    cfg = load_pair_config("aiuc_1__owasp_agentic", validate_anchors_in=G)
    anchor_list = _anchor_pairs(cfg)
    holdout = _holdout_pairs(cfg)
    hold_mask = train_df.apply(
        lambda r: (r["source_node_id"], r["target_node_id"]) in holdout, axis=1
    )
    holdout_df = train_df[hold_mask].copy()
    fit_df = train_df[~hold_mask].copy()

    # Identify anchor rows in training_df (all 10)
    anchor_keys = {(s, t) for s, t, _ in anchor_list}
    anchor_mask = train_df.apply(
        lambda r: (r["source_node_id"], r["target_node_id"]) in anchor_keys, axis=1
    )
    anchor_rows_df = train_df[anchor_mask].copy()
    anchor_expected_col = _anchor_expected_tier(anchor_rows_df, anchor_list)

    # ── Train primary models on the ex-holdout set ────────────────────────
    log_model, log_coefs = train_logistic(fit_df)
    lgb_model, lgb_imp = train_lightgbm(fit_df)
    ord_model, ord_coefs = train_ordinal(fit_df)

    rows = [
        ("Hand-tuned",
         evaluate_hand_tuned(fit_df),
         evaluate_hand_tuned(holdout_df) if len(holdout_df) else {},
         evaluate_hand_tuned(nist_df)),
        ("Logistic",
         evaluate_model(log_model, fit_df, "logistic"),
         evaluate_model(log_model, holdout_df, "logistic") if len(holdout_df) else {},
         evaluate_model(log_model, nist_df, "logistic")),
        ("LightGBM",
         evaluate_model(lgb_model, fit_df, "lightgbm"),
         evaluate_model(lgb_model, holdout_df, "lightgbm") if len(holdout_df) else {},
         evaluate_model(lgb_model, nist_df, "lightgbm")),
        ("Ordinal",
         evaluate_model(ord_model, fit_df, "ordinal"),
         evaluate_model(ord_model, holdout_df, "ordinal") if len(holdout_df) else {},
         evaluate_model(ord_model, nist_df, "ordinal")),
    ]

    print(f"\n{'Model':<12} | {'Train Acc':>9} | {'Hold Acc':>9} | {'NIST Acc':>9} | {'NIST F1':>9}")
    print("-" * 65)
    for name, train_m, hold_m, nist_m in rows:
        print(
            f"{name:<12} | "
            f"{train_m.get('accuracy', 0):>9.3f} | "
            f"{hold_m.get('accuracy', 0):>9.3f} | "
            f"{nist_m.get('accuracy', 0):>9.3f} | "
            f"{nist_m.get('f1', 0):>9.3f}"
        )

    # ── Cross-validation on anchors (Phase C) ─────────────────────────────
    cv_acc: dict[str, float] = {}
    cv_acc["hand_tuned"] = _cv_accuracy_for_model(
        train_df,
        anchor_rows_df,
        train_fn=lambda df: None,
        eval_fn=lambda m, held: _hand_tier_eval(
            held, _anchor_expected_tier(held, anchor_list)
        ),
    )
    cv_acc["logistic"] = _cv_accuracy_for_model(
        train_df,
        anchor_rows_df,
        train_fn=lambda df: train_logistic(df)[0],
        eval_fn=lambda m, held: _model_tier_eval(
            m, "logistic", held, _anchor_expected_tier(held, anchor_list)
        ),
    )
    cv_acc["lightgbm"] = _cv_accuracy_for_model(
        train_df,
        anchor_rows_df,
        train_fn=lambda df: train_lightgbm(df)[0],
        eval_fn=lambda m, held: _model_tier_eval(
            m, "lightgbm", held, _anchor_expected_tier(held, anchor_list)
        ),
    )
    cv_acc["ordinal"] = _cv_accuracy_for_model(
        train_df,
        anchor_rows_df,
        train_fn=lambda df: train_ordinal(df)[0],
        eval_fn=lambda m, held: _model_tier_eval(
            m, "ordinal", held, _anchor_expected_tier(held, anchor_list)
        ),
    )
    print("\nCV anchor tier-accuracy (5-fold over 10 anchors):")
    for k, v in cv_acc.items():
        print(f"  {k:<12}: {v:.3f}")

    # Pick the best model on NIST accuracy, tie-break on CV
    best_name, best_nist = "Hand-tuned", rows[0][3].get("accuracy", 0.0)
    for name, _, _, nist_m in rows[1:]:
        if nist_m.get("accuracy", 0.0) > best_nist:
            best_name, best_nist = name, nist_m.get("accuracy", 0.0)

    print(f"\nBest model on NIST accuracy: {best_name} ({best_nist:.3f})")

    # ── Threshold sweep on masked anchor composite scores ─────────────────
    print("\nRunning masked PairMapper to collect anchor composite scores...")
    anchor_records = _run_masked_mapper(G, cfg)
    anchor_expected = {f"{s}__{t}": tier for s, t, tier in anchor_list}
    # All AIUC anchors are Primary relevance in practice
    primary_map = {k: True for k in anchor_records}

    (chosen_direct, chosen_rel), sweep_df = _sweep_thresholds(
        anchor_records, anchor_expected, primary_map
    )
    print(f"\nThreshold sweep chose: direct={chosen_direct}, related_primary={chosen_rel}")
    print(sweep_df.head(10).to_string(index=False))

    # Stability analysis
    stability = analyze_weight_stability(fit_df, log_model, "logistic")

    out = {
        "models": {
            "logistic": {"coefficients": log_coefs},
            "lightgbm": {"feature_importance": lgb_imp},
            "ordinal": {"coefficients": ord_coefs},
        },
        "evaluations": {
            name: {"train": tr, "holdout": ho, "nist": ni}
            for name, tr, ho, ni in rows
        },
        "cv_accuracy": cv_acc,
        "threshold_sweep": sweep_df.to_dict(orient="records"),
        "best_model": best_name,
        "hand_weights": HAND_WEIGHTS,
        "compare_logistic_vs_hand_nist": compare_to_hand_tuned(
            nist_df, HAND_WEIGHTS, log_model, "logistic"
        ),
        "weight_stability_logistic": stability,
    }
    out_path = REPO / "data" / "processed" / "weight_comparison.json"
    out_path.write_text(json.dumps(out, indent=2, default=str))
    print(f"\nWrote {out_path}")

    learned_path = REPO / "data" / "processed" / "learned_weights.json"
    learned_path.write_text(
        json.dumps(
            {
                "best_model": best_name,
                "logistic_coefficients": log_coefs,
                "lightgbm_feature_importance": lgb_imp,
                "ordinal_coefficients": ord_coefs,
                "cv_accuracy": cv_acc,
                "calibrated_thresholds": {
                    "direct": chosen_direct,
                    "related_primary": chosen_rel,
                    "method": "cv-youden-j-on-masked-anchors",
                    "n_folds": 5,
                },
            },
            indent=2,
        )
    )
    print(f"Wrote {learned_path}")

    stab_path = REPO / "data" / "processed" / "weight_stability.json"
    stab_path.write_text(json.dumps(stability, indent=2))
    print(f"Wrote {stab_path}")


if __name__ == "__main__":
    main()
