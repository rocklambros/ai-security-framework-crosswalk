"""A7: Phase A learning curve and reliability diagram.

Reranker_v2 was DROPPED in A5 (paired delta +0.0000), so the Phase A
"model" is identical to the B-1 baseline, which is identical to the B-2
baseline. This script reuses the B-2 collection logic and writes the
diagnostics under a_*.png with a title noting the equivalence.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from sklearn.linear_model import LogisticRegression

from mapping_engine.calibration.diagnostics import learning_curve, reliability_curve
from mapping_engine.scripts.diagnostics_b2 import _collect

REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "docs" / "diagnostics"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    scores, grades = _collect()
    y = (grades > 0).astype(np.int64)
    proba = np.clip(scores, 0.0, 1.0)

    rel = reliability_curve(y, proba, n_bins=10)
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.plot([0, 1], [0, 1], "k--", alpha=0.4, label="perfect")
    ax.plot(rel["predicted_mean"], rel["observed_mean"], "o-", label="A (= B-1 = B-2)")
    ax.set_xlabel("predicted score (binned)")
    ax.set_ylabel("observed positive rate")
    ax.set_title(
        f"Phase A reliability diagram (n={len(y)})\n"
        f"reranker_v2 DROPPED in A5; A = B-1 = B-2 baseline"
    )
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.legend()
    fig.tight_layout()
    rel_path = OUT_DIR / "a_reliability.png"
    fig.savefig(rel_path, dpi=120)
    plt.close(fig)
    print(f"Wrote {rel_path}")

    rng_neg = np.random.default_rng(42)
    n_pos = int(y.sum())
    min_pos = float(scores.min()) if n_pos > 0 else 0.5
    n_neg = max(20, n_pos)
    neg_scores = rng_neg.uniform(0.0, max(0.05, min_pos * 0.8), size=n_neg)
    Xc = np.concatenate([scores, neg_scores]).reshape(-1, 1)
    yc = np.concatenate(
        [np.ones(len(scores), dtype=np.int64), np.zeros(n_neg, dtype=np.int64)]
    )
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
        f"Phase A learning curve (= B-1 = B-2; reranker_v2 dropped)\n"
        f"{len(scores)} positives + {n_neg} synthetic uniform negatives"
    )
    ax.set_ylim(0.0, 1.05)
    ax.legend()
    fig.tight_layout()
    lc_path = OUT_DIR / "a_learning_curve.png"
    fig.savefig(lc_path, dpi=120)
    plt.close(fig)
    print(f"Wrote {lc_path}")


if __name__ == "__main__":
    main()
