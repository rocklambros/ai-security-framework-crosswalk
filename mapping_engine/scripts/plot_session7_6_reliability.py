"""S14: post-hardening reliability diagram.

Plots positive vs distractor composite-score distributions for the
non-frozen pairs from `discriminative_baseline_s7_6.json`. The legacy
diagrams in `docs/diagnostics/` were generated under the saturated
NDCG@10 regime and no longer reflect the post-S7.6 pipeline.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
SRC = REPO / "data/processed/discriminative_baseline_s7_6.json"
OUT = REPO / "docs/diagnostics/session7_6_reliability.png"


def main() -> None:
    data = json.loads(SRC.read_text())
    pos = data["scores"]["positive"]
    dist_nested = data["scores"]["distractors"]
    dist_flat = [d for row in dist_nested for d in row]

    fig, ax = plt.subplots(figsize=(8, 5))
    bins = [i / 50 for i in range(51)]
    ax.hist(dist_flat, bins=bins, color="#888", alpha=0.55,
            label=f"distractors (n={len(dist_flat)})", density=True)
    ax.hist(pos, bins=bins, color="#1f77b4", alpha=0.7,
            label=f"positives (n={len(pos)})", density=True)
    ax.set_xlabel("composite score")
    ax.set_ylabel("density")
    ax.set_title("Session 7.6 reliability — non-frozen pairs (n=410 anchors)")
    ax.legend()
    fig.tight_layout()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=140)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
