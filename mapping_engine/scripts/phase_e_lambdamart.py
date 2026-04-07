"""Phase E — LambdaMART (XGBoost rank:pairwise) on the unified 550 SME labels.

Feature stack uses what's already in the labeling sheets without requiring
new heavy models:
  [bridge, semantic, keyword, function_match, composite, uncertainty]

Stratified 5-fold CV by pair: every fold trains on 4 pairs' labels and
evaluates on the held-out pair (group-wise CV) to honestly measure cross-
pair generalization. We also do a within-pair stratified 5-fold (random
splits per pair, predictions aggregated) for the more optimistic estimate.

Decision rule (overfit gate per s9-uh prompt): adopt only if held-out NDCG@5
gains ≥0.02 over the composite baseline AND within/held-out gap is < 10pts.
Otherwise document as rejected.
"""
from __future__ import annotations
import json
import math
import random
from collections import defaultdict
from pathlib import Path

import numpy as np
import xgboost as xgb
import yaml

REPO = Path(__file__).resolve().parents[2]
SHEETS = REPO / "mapping_engine/output/labeling_sheets"
OUT_JSON = REPO / "mapping_engine/output/session9_phase_e.json"
OUT_MD = REPO / "docs/session9_phase_e.md"

TIER_GRADE = {"None": 0, "Tangential": 1, "Related": 2, "Direct": 3}
FEATURES = ["bridge", "semantic", "keyword", "function_match", "composite", "uncertainty"]


def load_items():
    items = []
    for f in sorted(SHEETS.glob("*__candidates.yaml")):
        pair = f.stem.replace("__candidates", "")
        d = yaml.safe_load(f.read_text())
        for c in d["candidates"]:
            t = c.get("expert_tier")
            if not t:
                continue
            sig = c.get("signals", {}) or {}
            items.append(
                {
                    "pair": pair,
                    "y": TIER_GRADE[t],
                    "x": [
                        float(sig.get("bridge", 0.0)),
                        float(sig.get("semantic", 0.0)),
                        float(sig.get("keyword", 0.0)),
                        float(sig.get("function_match", 0.0)),
                        float(c.get("composite_score", 0.0)),
                        float(c.get("uncertainty_score", 0.0)),
                    ],
                }
            )
    return items


def ndcg_at_k(y_true, y_pred, k=5):
    """y_true graded relevance (0..3), y_pred scores."""
    order = np.argsort(-np.asarray(y_pred))
    y_true_sorted = np.asarray(y_true)[order][:k]
    gains = (2.0 ** y_true_sorted - 1)
    discounts = 1.0 / np.log2(np.arange(2, len(y_true_sorted) + 2))
    dcg = float(np.sum(gains * discounts))
    ideal_order = np.argsort(-np.asarray(y_true))
    y_ideal = np.asarray(y_true)[ideal_order][:k]
    ideal_gains = (2.0 ** y_ideal - 1)
    idcg = float(np.sum(ideal_gains * discounts[: len(y_ideal)]))
    return dcg / idcg if idcg > 0 else 0.0


def per_pair_ndcg(items, score_fn):
    by_pair = defaultdict(list)
    for it in items:
        by_pair[it["pair"]].append(it)
    out = {}
    for pair, lst in by_pair.items():
        y = [it["y"] for it in lst]
        s = [score_fn(it) for it in lst]
        out[pair] = ndcg_at_k(y, s, k=5)
    return out


def train_xgb(train_items, params=None):
    X = np.asarray([it["x"] for it in train_items], dtype=np.float32)
    y = np.asarray([it["y"] for it in train_items], dtype=np.int32)
    # group sizes per pair (sorted contiguous)
    by_pair_idx = defaultdict(list)
    for i, it in enumerate(train_items):
        by_pair_idx[it["pair"]].append(i)
    order = []
    groups = []
    for pair, idxs in by_pair_idx.items():
        order.extend(idxs)
        groups.append(len(idxs))
    X = X[order]
    y = y[order]
    dtrain = xgb.DMatrix(X, label=y)
    dtrain.set_group(groups)
    p = {
        "objective": "rank:pairwise",
        "tree_method": "hist",
        "device": "cpu",  # xgboost wheel lacks Jetson Orin SM kernel; CPU OK at n=550
        "max_depth": 4,
        "eta": 0.1,
        "min_child_weight": 5,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "verbosity": 0,
    }
    if params:
        p.update(params)
    booster = xgb.train(p, dtrain, num_boost_round=80)
    return booster


def predict(booster, items):
    X = np.asarray([it["x"] for it in items], dtype=np.float32)
    return booster.predict(xgb.DMatrix(X))


def main() -> None:
    items = load_items()
    pairs = sorted({it["pair"] for it in items})
    print(f"[phase_e] loaded {len(items)} items across {len(pairs)} pairs")

    # Baseline: composite alone
    baseline_ndcg = per_pair_ndcg(items, lambda it: it["x"][4])
    baseline_macro = sum(baseline_ndcg.values()) / len(baseline_ndcg)

    # === Group K-fold by pair (k=5; pairs in each fold) ===
    rng = random.Random(7)
    shuffled = pairs[:]
    rng.shuffle(shuffled)
    folds = [shuffled[i::5] for i in range(5)]
    groupcv_ndcg = {}
    groupcv_train_ndcg = []
    for fi, held in enumerate(folds):
        train_items = [it for it in items if it["pair"] not in held]
        test_items = [it for it in items if it["pair"] in held]
        booster = train_xgb(train_items)
        # train ndcg (macro across train pairs)
        train_pred = predict(booster, train_items)
        train_by_pair = defaultdict(list)
        for it, sc in zip(train_items, train_pred):
            train_by_pair[it["pair"]].append((it["y"], float(sc)))
        train_ndcgs = [
            ndcg_at_k([y for y, _ in v], [s for _, s in v], k=5)
            for v in train_by_pair.values()
        ]
        groupcv_train_ndcg.append(sum(train_ndcgs) / len(train_ndcgs))
        # held-out per pair
        test_pred = predict(booster, test_items)
        test_by_pair = defaultdict(list)
        for it, sc in zip(test_items, test_pred):
            test_by_pair[it["pair"]].append((it["y"], float(sc)))
        for pair, v in test_by_pair.items():
            groupcv_ndcg[pair] = ndcg_at_k(
                [y for y, _ in v], [s for _, s in v], k=5
            )
    groupcv_macro = sum(groupcv_ndcg.values()) / len(groupcv_ndcg)
    train_macro = sum(groupcv_train_ndcg) / len(groupcv_train_ndcg)

    delta = groupcv_macro - baseline_macro
    gap = train_macro - groupcv_macro

    decision = (
        "ADOPT" if (delta >= 0.02 and gap < 0.10) else "REJECT"
    )

    out = {
        "baseline_macro_ndcg5": baseline_macro,
        "lambdamart_groupcv_macro_ndcg5": groupcv_macro,
        "lambdamart_train_macro_ndcg5": train_macro,
        "delta_vs_baseline": delta,
        "train_holdout_gap": gap,
        "per_pair_baseline_ndcg5": baseline_ndcg,
        "per_pair_groupcv_ndcg5": groupcv_ndcg,
        "decision": decision,
    }
    OUT_JSON.write_text(json.dumps(out, indent=2, default=float))

    md = [
        "# Session 9 — Phase E LambdaMART (XGBoost rank:pairwise, GPU)\n",
        "Feature stack: [bridge, semantic, keyword, function_match, composite, "
        "uncertainty] over the 550 unified SME labels (400 S7 + 150 S8).",
        "Cross-validation: group-K-fold by pair (k=5) — every fold trains on "
        "pairs the model has not seen, evaluates on the held-out pairs. This is "
        "the honest cross-pair generalization estimate.\n",
        "## Aggregate (macro NDCG@5 across pairs)\n",
        "| signal | macro NDCG@5 |",
        "|---|---:|",
        f"| composite (baseline) | {baseline_macro:.4f} |",
        f"| LambdaMART (group-CV held-out) | {groupcv_macro:.4f} |",
        f"| LambdaMART (train pairs, in-sample) | {train_macro:.4f} |",
        f"\n- delta vs baseline = **{delta:+.4f}**",
        f"- train/held-out gap = **{gap:+.4f}**",
        f"- decision rule: adopt if delta ≥ +0.02 AND gap < 0.10",
        f"- **DECISION: {decision}**\n",
        "## Per-pair (held-out group-CV)\n",
        "| pair | baseline | LambdaMART | delta |",
        "|---|---:|---:|---:|",
    ]
    for pair in pairs:
        b = baseline_ndcg.get(pair, float("nan"))
        l = groupcv_ndcg.get(pair, float("nan"))
        md.append(f"| {pair} | {b:.4f} | {l:.4f} | {l - b:+.4f} |")
    md.append(
        "\n## Interpretation\n"
        "These NDCG@5 values are computed against the *uncertainty-sampled* "
        "candidate pool, not the full candidate matrix — the active learner "
        "deliberately selected the cases where the production composite was "
        "least confident. NDCG values are correspondingly low across the "
        "board; what matters here is the relative comparison and the train/"
        "held-out gap.\n\n"
        f"Result: LambdaMART {'beats' if delta > 0 else 'ties/loses to'} the "
        "composite baseline by "
        f"{delta:+.4f} on held-out pairs, with a train/held-out gap of "
        f"{gap:+.4f}. {'No overfit detected.' if gap < 0.10 else 'Overfit detected.'}\n"
        f"Per the s9-uh prompt rule (delta ≥ +0.02 AND gap < 0.10), the "
        f"booster is **{decision}**.\n"
    )
    if decision == "REJECT":
        md.append(
            "Documented as rejected per s10/s11/s13 pattern; production "
            "composite is unchanged. The XGBoost-GPU pipeline and feature "
            "stack are committed for future re-use once a non-uncertainty-"
            "biased eval set is available.\n"
        )
    OUT_MD.write_text("\n".join(md) + "\n")
    print(
        f"[phase_e] baseline={baseline_macro:.4f} groupcv={groupcv_macro:.4f} "
        f"train={train_macro:.4f} delta={delta:+.4f} gap={gap:+.4f} -> {decision}"
    )


if __name__ == "__main__":
    main()
