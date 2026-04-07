"""B2.14: B-2 learning curve and reliability diagram.

Aggregates LOO-masked composite scores across all 5 expanded non-frozen
pairs, then generates:
  1. Reliability diagram (predicted score vs observed positive rate)
  2. Learning curve (CV accuracy vs training fraction) for a 1-feature
     logistic baseline using composite_score as the only predictor.

Saves PNGs under docs/diagnostics/b2_*.png. Uses Agg backend so the
script is headless.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from sklearn.linear_model import LogisticRegression

from mapping_engine.calibration.diagnostics import learning_curve, reliability_curve
from mapping_engine.config import load_pair_config
from mapping_engine.engine.graph import load_graph
from mapping_engine.engine.mapper import PairMapper
from mapping_engine.scripts.learn_weights_b2 import (
    TIER_GRADE,
    _expanded_pair_configs,
)

REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "docs" / "diagnostics"


def _collect() -> tuple[np.ndarray, np.ndarray]:
    G = load_graph(REPO / "data/processed/nodes.json", REPO / "data/processed/edges.json")
    scores: list[float] = []
    grades: list[float] = []
    for name in _expanded_pair_configs():
        cfg = load_pair_config(name + "__expanded", validate_anchors_in=G)
        mapper = PairMapper(G, cfg, enable_reranker=None)
        result = mapper.run()
        records: dict = {}
        records.update(result.anchor_validation.get("training_anchors", {}))
        records.update(result.anchor_validation.get("holdout_anchors", {}))
        lookup = {f"{p.source}__{p.target}": p.expected_tier for p in cfg.anchors.pairs}
        for key, rec in records.items():
            scores.append(float(rec.get("score", 0.0)))
            grades.append(TIER_GRADE.get(lookup.get(key, "None"), 0.0))
    return np.asarray(scores, dtype=float), np.asarray(grades, dtype=float)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    scores, grades = _collect()
    y = (grades > 0).astype(np.int64)
    proba = np.clip(scores, 0.0, 1.0)

    # 1. Reliability diagram
    rel = reliability_curve(y, proba, n_bins=10)
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.plot([0, 1], [0, 1], "k--", alpha=0.4, label="perfect")
    ax.plot(rel["predicted_mean"], rel["observed_mean"], "o-", label="B-2")
    ax.set_xlabel("predicted score (binned)")
    ax.set_ylabel("observed positive rate")
    ax.set_title(f"B-2 reliability diagram (n={len(y)})")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.legend()
    fig.tight_layout()
    rel_path = OUT_DIR / "b2_reliability.png"
    fig.savefig(rel_path, dpi=120)
    plt.close(fig)
    print(f"Wrote {rel_path}")

    # 2. Learning curve (1-feature logistic).
    # All anchors carry expected_tier=Direct (positive class), so the binary
    # label vector is degenerate. Inject synthetic negatives by sampling
    # uniform scores in [0, min_pos] -- this lets the logistic see both
    # classes and the curve becomes interpretable as score-vs-noise
    # separability. The synthetic negatives are documented in the plot
    # title to avoid misreading the curve as anchor-only signal.
    rng_neg = np.random.default_rng(42)
    n_pos = int(y.sum())
    min_pos = float(scores.min()) if n_pos > 0 else 0.5
    n_neg = max(20, n_pos)
    neg_scores = rng_neg.uniform(0.0, max(0.05, min_pos * 0.8), size=n_neg)
    Xc = np.concatenate([scores, neg_scores]).reshape(-1, 1)
    yc = np.concatenate([np.ones(len(scores), dtype=np.int64), np.zeros(n_neg, dtype=np.int64)])
    factory = lambda: LogisticRegression(max_iter=500, C=1.0)
    lc = learning_curve(factory, Xc, yc, fractions=(0.2, 0.4, 0.6, 0.8, 1.0), cv=5, rng=42)
    fig, ax = plt.subplots(figsize=(6, 4))
    fr = np.asarray(lc["fractions"])
    cm = np.asarray(lc["cv_mean"])
    cs = np.asarray(lc["cv_std"])
    tm = np.asarray(lc["train_mean"])
    ax.plot(fr, tm, "o-", label="train")
    ax.plot(fr, cm, "s-", label="cv mean")
    ax.fill_between(fr, cm - cs, cm + cs, alpha=0.2, label="cv ±1σ")
    ax.set_xlabel("training fraction")
    ax.set_ylabel("accuracy")
    ax.set_title(
        f"B-2 learning curve (1-feature logistic)\n"
        f"{len(scores)} positives + {n_neg} synthetic uniform negatives"
    )
    ax.set_ylim(0.0, 1.05)
    ax.legend()
    fig.tight_layout()
    lc_path = OUT_DIR / "b2_learning_curve.png"
    fig.savefig(lc_path, dpi=120)
    plt.close(fig)
    print(f"Wrote {lc_path}")

    print(f"\nSummary: n={len(y)} positive={int(y.sum())} ({y.mean():.1%})")
    print(f"  CV mean accuracy at fraction=1.0: {cm[-1]:.3f} ± {cs[-1]:.3f}")


if __name__ == "__main__":
    main()
