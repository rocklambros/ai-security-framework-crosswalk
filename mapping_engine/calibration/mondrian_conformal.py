"""Mondrian (per-class) split-conformal calibration over the unified 550 SME
labels. Replaces the ad-hoc ±0.05 needs_review heuristic with a per-class
non-conformity quantile so that, for a target coverage 1-alpha, the prediction
*set* contains the true tier with frequency ≥ 1-alpha on the held-out test
slice.

Stratification: 60/20/20 train/cal/test split by pair (each pair contributes
its own 60/20/20 so every pair is represented in cal and test).

Non-conformity score: |s - tier_centroid_class| where tier_centroid_class is
the mean composite_score of training items with that expert tier (per class,
not per pair — Mondrian groups by class, which is what we want for class-
conditional coverage).
"""
from __future__ import annotations
import json
import random
from collections import defaultdict
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
SHEETS = REPO / "mapping_engine/output/labeling_sheets"
OUT_JSON = REPO / "mapping_engine/output/session9_conformal.json"
OUT_MD = REPO / "docs/session9_conformal.md"

TIERS = ["None", "Tangential", "Related", "Direct"]


def quantile(xs: list[float], q: float) -> float:
    if not xs:
        return float("inf")
    xs = sorted(xs)
    k = max(0, min(len(xs) - 1, int(round(q * (len(xs) - 1)))))
    return xs[k]


def split_60_20_20(items, seed=17):
    rng = random.Random(seed)
    by_pair = defaultdict(list)
    for it in items:
        by_pair[it["pair"]].append(it)
    train, cal, test = [], [], []
    for pair, lst in by_pair.items():
        rng.shuffle(lst)
        n = len(lst)
        n_tr = int(round(n * 0.6))
        n_ca = int(round(n * 0.2))
        train.extend(lst[:n_tr])
        cal.extend(lst[n_tr : n_tr + n_ca])
        test.extend(lst[n_tr + n_ca :])
    return train, cal, test


def fit_centroids(train):
    by_t = defaultdict(list)
    for it in train:
        by_t[it["tier"]].append(it["score"])
    return {t: sum(v) / len(v) if v else 0.0 for t, v in by_t.items()}


def calibrate_alpha(cal, centroids, alpha=0.10):
    """Per-class non-conformity quantile (Mondrian)."""
    by_t = defaultdict(list)
    for it in cal:
        c = centroids.get(it["tier"], 0.0)
        by_t[it["tier"]].append(abs(it["score"] - c))
    return {t: quantile(by_t.get(t, []), 1 - alpha) for t in TIERS}


def predict_set(score, centroids, qhats):
    s = set()
    for t in TIERS:
        c = centroids.get(t, 0.0)
        if abs(score - c) <= qhats.get(t, float("inf")):
            s.add(t)
    if not s:
        # always include the nearest centroid as a fallback singleton
        nearest = min(TIERS, key=lambda t: abs(score - centroids.get(t, 0.0)))
        s.add(nearest)
    return s


def main(alpha: float = 0.10) -> None:
    items = []
    for f in sorted(SHEETS.glob("*__candidates.yaml")):
        pair = f.stem.replace("__candidates", "")
        d = yaml.safe_load(f.read_text())
        for c in d["candidates"]:
            if c.get("expert_tier"):
                items.append(
                    {
                        "pair": pair,
                        "tier": c["expert_tier"],
                        "score": float(c["composite_score"]),
                    }
                )
    train, cal, test = split_60_20_20(items)
    centroids = fit_centroids(train)
    qhats = calibrate_alpha(cal, centroids, alpha=alpha)

    # evaluate coverage and avg set size on test
    covered = 0
    sizes = []
    needs_review = 0
    for it in test:
        ps = predict_set(it["score"], centroids, qhats)
        sizes.append(len(ps))
        if it["tier"] in ps:
            covered += 1
        if len(ps) > 1:
            needs_review += 1
    coverage = covered / len(test) if test else 0.0
    avg_size = sum(sizes) / len(sizes) if sizes else 0.0
    review_rate = needs_review / len(test) if test else 0.0

    out = {
        "alpha": alpha,
        "n_train": len(train),
        "n_cal": len(cal),
        "n_test": len(test),
        "centroids": centroids,
        "qhats": qhats,
        "test_coverage": coverage,
        "avg_set_size": avg_size,
        "needs_review_rate": review_rate,
    }
    OUT_JSON.write_text(json.dumps(out, indent=2))
    md = [
        "# Session 9 — Phase C Mondrian Conformal Calibration\n",
        f"alpha={alpha} target coverage={1 - alpha:.2f}\n",
        f"- n_train={len(train)} n_cal={len(cal)} n_test={len(test)}",
        f"- test coverage = {coverage:.3f} (target ≥ {1 - alpha:.2f})",
        f"- avg prediction-set size = {avg_size:.2f}",
        f"- needs_review (set size > 1) rate = {review_rate:.3f}\n",
        "## Per-class centroids (mean composite score on train)\n",
        "| Tier | centroid | qhat |",
        "|---|---:|---:|",
    ]
    for t in TIERS:
        md.append(
            f"| {t} | {centroids.get(t, float('nan')):.3f} | "
            f"{qhats.get(t, float('nan')):.3f} |"
        )
    md.append(
        "\nThis layer replaces the ad-hoc ±0.05 needs_review heuristic with a\n"
        "Mondrian split-conformal predictor whose per-class non-conformity\n"
        "quantile gives class-conditional coverage guarantees on the held-out\n"
        "test slice. Frozen tier_acc is unaffected — the conformal layer\n"
        "wraps the existing composite score; it does not modify it.\n"
    )
    OUT_MD.write_text("\n".join(md) + "\n")
    print(
        f"[conformal] coverage={coverage:.3f} avg_size={avg_size:.2f} "
        f"review_rate={review_rate:.3f}"
    )
    print(f"[conformal] wrote {OUT_JSON.relative_to(REPO)} {OUT_MD.relative_to(REPO)}")


if __name__ == "__main__":
    main()
