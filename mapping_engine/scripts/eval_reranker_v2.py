"""A5: Compare reranker_v2 against the B-1 baseline.

For each non-frozen expanded pair, runs PairMapper twice:
  1. Baseline: enable_reranker=False (B-1 = B-2 hand-tuned baseline; no
     B-1 structural features survived gates).
  2. Reranker_v2: enable_reranker=True with reranker.model temporarily
     pointed at mapping_engine/models/reranker_v2/.

Records per-anchor composite scores, then reports aggregate NDCG@10 with
1000-resample bootstrap CI for each model and the paired-bootstrap CI on
the per-anchor delta.

Decision rule: keep reranker_v2 if the paired-bootstrap 95% CI on the
aggregate NDCG@10 delta excludes 0 AND the direction is positive. Drop
otherwise. The defaults.yaml swap is performed only if the gate passes.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from mapping_engine.calibration.metrics import bootstrap_metric_ci, ndcg_at_k
from mapping_engine.config import load_pair_config
from mapping_engine.engine.graph import load_graph
from mapping_engine.engine.mapper import PairMapper
from mapping_engine.scripts.learn_weights_b2 import (
    TIER_GRADE,
    _expanded_pair_configs,
)

REPO = Path(__file__).resolve().parents[2]
RERANKER_DIR = REPO / "mapping_engine/models/reranker_v2"


def _collect(G, cfg, *, use_reranker: bool):
    if use_reranker:
        rer = dict(cfg.reranker or {})
        rer["enabled"] = True
        rer["model"] = str(RERANKER_DIR)
        cfg.reranker = rer
    mapper = PairMapper(G, cfg, use_learned_weights=False, enable_reranker=use_reranker)
    result = mapper.run()
    av = result.anchor_validation
    records: dict = {}
    records.update(av.get("training_anchors", {}))
    records.update(av.get("holdout_anchors", {}))
    expected_lookup = {f"{p.source}__{p.target}": p.expected_tier for p in cfg.anchors.pairs}
    keys, scores, grades = [], [], []
    for key in sorted(records.keys()):
        rec = records[key]
        keys.append(key)
        scores.append(float(rec.get("score", 0.0)))
        grades.append(TIER_GRADE.get(expected_lookup.get(key, "None"), 0.0))
    return keys, np.asarray(scores), np.asarray(grades)


def main() -> None:
    G = load_graph(REPO / "data/processed/nodes.json", REPO / "data/processed/edges.json")
    all_keys, base_s, rer_s, all_g = [], [], [], []
    per_pair = []
    for name in _expanded_pair_configs():
        cfg_b = load_pair_config(name + "__expanded", validate_anchors_in=G)
        cfg_r = load_pair_config(name + "__expanded", validate_anchors_in=G)
        kb, sb, gb = _collect(G, cfg_b, use_reranker=False)
        kr, sr, gr = _collect(G, cfg_r, use_reranker=True)
        # Align by key
        idx = {k: i for i, k in enumerate(kr)}
        sr_aligned = np.asarray([sr[idx[k]] for k in kb])
        per_pair.append(
            {
                "pair": name,
                "n": len(kb),
                "baseline_ndcg": ndcg_at_k(gb, sb, k=10),
                "reranker_ndcg": ndcg_at_k(gb, sr_aligned, k=10),
            }
        )
        all_keys.extend(kb)
        base_s.append(sb)
        rer_s.append(sr_aligned)
        all_g.append(gb)

    base_s = np.concatenate(base_s)
    rer_s = np.concatenate(rer_s)
    all_g = np.concatenate(all_g)

    base_ci = bootstrap_metric_ci(
        lambda gg, ss: ndcg_at_k(gg, ss, k=10), all_g, base_s, n_resamples=1000, rng=42
    )
    rer_ci = bootstrap_metric_ci(
        lambda gg, ss: ndcg_at_k(gg, ss, k=10), all_g, rer_s, n_resamples=1000, rng=42
    )

    # Paired bootstrap on delta of NDCG@10 over resampled indices.
    rng = np.random.default_rng(42)
    n = len(all_g)
    deltas = []
    for _ in range(1000):
        idx = rng.integers(0, n, size=n)
        d = ndcg_at_k(all_g[idx], rer_s[idx], k=10) - ndcg_at_k(all_g[idx], base_s[idx], k=10)
        deltas.append(d)
    deltas = np.asarray(deltas)
    delta_point = float(rer_ci["point"] - base_ci["point"])
    delta_lo, delta_hi = float(np.quantile(deltas, 0.025)), float(np.quantile(deltas, 0.975))

    print(f"n_anchors={n}")
    print(f"  baseline NDCG@10:  {base_ci['point']:.4f} [{base_ci['lo']:.4f}, {base_ci['hi']:.4f}]")
    print(f"  reranker_v2 NDCG:  {rer_ci['point']:.4f} [{rer_ci['lo']:.4f}, {rer_ci['hi']:.4f}]")
    print(f"  paired delta:      {delta_point:+.4f} [{delta_lo:+.4f}, {delta_hi:+.4f}]")
    decision = "KEEP" if (delta_lo > 0 and delta_point > 0) else "DROP"
    print(f"  decision: {decision}")

    out = {
        "n_anchors": int(n),
        "baseline_ndcg_at_10": base_ci,
        "reranker_v2_ndcg_at_10": rer_ci,
        "paired_delta": {"point": delta_point, "lo": delta_lo, "hi": delta_hi},
        "decision": decision,
        "per_pair": per_pair,
    }
    out_path = REPO / "data/processed/reranker_v2_eval.json"
    out_path.write_text(json.dumps(out, indent=2, default=str))
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
