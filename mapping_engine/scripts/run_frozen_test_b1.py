"""B1.10: B-1 frozen test set evaluation (aiuc_1 -> mitre_atlas).

Touched ONCE. NO retuning afterwards. Since no B-1 structural feature
survived its anti-overfit gate (see docs/diagnostics/b1_ablation.md),
the B-1 model is identical to the B-2 baseline.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from mapping_engine.calibration.metrics import (
    bootstrap_metric_ci,
    ndcg_at_k,
    tier_accuracy,
)
from mapping_engine.config import load_pair_config
from mapping_engine.engine.graph import load_graph
from mapping_engine.engine.mapper import PairMapper
from mapping_engine.scripts.learn_weights_b2 import TIER_GRADE

REPO = Path(__file__).resolve().parents[2]
PAIR = "aiuc_1__mitre_atlas"


def main() -> None:
    G = load_graph(REPO / "data/processed/nodes.json", REPO / "data/processed/edges.json")
    cfg = load_pair_config(PAIR + "__expanded", validate_anchors_in=G)
    mapper = PairMapper(G, cfg, enable_reranker=None)
    result = mapper.run()
    av = result.anchor_validation
    records: dict = {}
    records.update(av.get("training_anchors", {}))
    records.update(av.get("holdout_anchors", {}))
    expected_lookup = {f"{p.source}__{p.target}": p.expected_tier for p in cfg.anchors.pairs}

    scores, grades, pred, expected = [], [], [], []
    for key, rec in records.items():
        scores.append(float(rec.get("score", 0.0)))
        exp = expected_lookup.get(key, "None")
        expected.append(exp)
        grades.append(TIER_GRADE.get(exp, 0.0))
        pred.append(rec.get("predicted_tier") or rec.get("assigned_tier") or "None")
    g = np.asarray(grades, dtype=float)
    s = np.asarray(scores, dtype=float)
    e = np.asarray(expected, dtype=object)
    p = np.asarray(pred, dtype=object)

    ndcg = bootstrap_metric_ci(
        lambda gg, ss: ndcg_at_k(gg, ss, k=10), g, s, n_resamples=1000, rng=42
    )
    acc = bootstrap_metric_ci(tier_accuracy, e, p, n_resamples=1000, rng=42)

    print(f"B-1 frozen test: {PAIR}  n={len(g)}")
    print(f"  NDCG@10:        {ndcg['point']:.4f} [{ndcg['lo']:.4f}, {ndcg['hi']:.4f}]")
    print(f"  tier_accuracy:  {acc['point']:.4f} [{acc['lo']:.4f}, {acc['hi']:.4f}]")

    out = {
        "pair": PAIR,
        "n_anchors": int(len(g)),
        "ndcg_at_10": ndcg,
        "tier_accuracy": acc,
        "phase": "B-1",
        "frozen": True,
        "note": "B-1 = B-2 baseline (no structural features survived gates)",
    }
    out_path = REPO / "data" / "processed" / "frozen_test_b1.json"
    out_path.write_text(json.dumps(out, indent=2, default=str))
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
