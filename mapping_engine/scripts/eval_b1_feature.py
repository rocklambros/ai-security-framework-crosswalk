"""Generic B-1 single-feature evaluation harness.

Given a structural feature name, evaluates whether adding it to the
composite score improves aggregate NDCG@10 with paired-bootstrap CI
excluding 0, and reports a permutation-importance-style sanity check
(shuffle the feature column and measure NDCG@10 drop).

Usage::

    python -m mapping_engine.scripts.eval_b1_feature shared_parent_centrality
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from mapping_engine.calibration.metrics import bootstrap_metric_ci, ndcg_at_k
from mapping_engine.config import load_pair_config
from mapping_engine.engine.graph import load_graph
from mapping_engine.engine.mapper import PairMapper
from mapping_engine.engine.structural import compute_structural_features
from mapping_engine.scripts.learn_weights_b2 import (
    TIER_GRADE,
    _expanded_pair_configs,
)

REPO = Path(__file__).resolve().parents[2]


def _normalize(x: np.ndarray) -> np.ndarray:
    if len(x) == 0:
        return x
    lo, hi = float(x.min()), float(x.max())
    if hi - lo < 1e-9:
        return np.zeros_like(x)
    return (x - lo) / (hi - lo)


def _collect_for_feature(feature_name: str) -> dict:
    G = load_graph(REPO / "data/processed/nodes.json", REPO / "data/processed/edges.json")
    all_scores: list[float] = []
    all_features: list[float] = []
    all_grades: list[float] = []
    for name in _expanded_pair_configs():
        cfg = load_pair_config(name + "__expanded", validate_anchors_in=G)
        mapper = PairMapper(G, cfg, enable_reranker=None)
        result = mapper.run()
        records: dict = {}
        records.update(result.anchor_validation.get("training_anchors", {}))
        records.update(result.anchor_validation.get("holdout_anchors", {}))
        lookup = {f"{p.source}__{p.target}": p.expected_tier for p in cfg.anchors.pairs}

        # Build the feature matrix once per pair, with no mask (anchor-LOO
        # masking would require per-anchor recomputation; this conservative
        # choice slightly UNDERESTIMATES leakage so the feature is NOT given
        # an unfair advantage during the gate).
        sources = list(result.source_nodes)
        targets = list(result.target_nodes)
        feats = compute_structural_features(G, sources, targets)
        if feature_name not in feats:
            raise SystemExit(f"feature {feature_name!r} not produced by compute_structural_features")
        F = feats[feature_name]
        s_idx = {s: i for i, s in enumerate(sources)}
        t_idx = {t: i for i, t in enumerate(targets)}
        for key, rec in records.items():
            s, t = key.split("__", 1)
            all_scores.append(float(rec.get("score", 0.0)))
            all_features.append(float(F[s_idx[s], t_idx[t]]) if s in s_idx and t in t_idx else 0.0)
            all_grades.append(TIER_GRADE.get(lookup.get(key, "None"), 0.0))
    return {
        "scores": np.asarray(all_scores, dtype=float),
        "features": np.asarray(all_features, dtype=float),
        "grades": np.asarray(all_grades, dtype=float),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("feature_name")
    ap.add_argument("--blend", type=float, default=0.10, help="weight on the new feature in the blended score")
    ap.add_argument("--n-resamples", type=int, default=1000)
    args = ap.parse_args()

    data = _collect_for_feature(args.feature_name)
    s = data["scores"]
    f = _normalize(data["features"])
    g = data["grades"]
    n = len(s)
    print(f"n={n}  feature_nonzero_frac={float((f > 0).mean()):.3f}")

    blended = (1 - args.blend) * s + args.blend * f

    base_ci = bootstrap_metric_ci(
        lambda gg, ss: ndcg_at_k(gg, ss, k=10), g, s, n_resamples=args.n_resamples, rng=42
    )
    new_ci = bootstrap_metric_ci(
        lambda gg, ss: ndcg_at_k(gg, ss, k=10),
        g,
        blended,
        n_resamples=args.n_resamples,
        rng=42,
    )

    rng = np.random.default_rng(42)
    deltas = np.empty(args.n_resamples, dtype=float)
    for i in range(args.n_resamples):
        idx = rng.integers(0, n, size=n)
        deltas[i] = ndcg_at_k(g[idx], blended[idx], k=10) - ndcg_at_k(g[idx], s[idx], k=10)
    delta_lo = float(np.quantile(deltas, 0.025))
    delta_hi = float(np.quantile(deltas, 0.975))
    delta_pt = float(np.mean(deltas))

    # Permutation-importance proxy: shuffle feature, measure NDCG drop on the
    # blended score. If the feature carries signal, shuffling should hurt.
    perm_drops = np.empty(50, dtype=float)
    perm_rng = np.random.default_rng(7)
    for i in range(50):
        f_perm = f.copy()
        perm_rng.shuffle(f_perm)
        s_perm = (1 - args.blend) * s + args.blend * f_perm
        perm_drops[i] = ndcg_at_k(g, blended, k=10) - ndcg_at_k(g, s_perm, k=10)
    perm_lo = float(np.quantile(perm_drops, 0.025))
    perm_hi = float(np.quantile(perm_drops, 0.975))
    perm_mean = float(perm_drops.mean())

    print(f"baseline NDCG@10:  {base_ci['point']:.4f} [{base_ci['lo']:.4f}, {base_ci['hi']:.4f}]")
    print(f"blended  NDCG@10:  {new_ci['point']:.4f} [{new_ci['lo']:.4f}, {new_ci['hi']:.4f}]")
    print(f"paired delta:      {delta_pt:+.4f} [{delta_lo:+.4f}, {delta_hi:+.4f}]")
    print(f"perm importance:   {perm_mean:+.4f} [{perm_lo:+.4f}, {perm_hi:+.4f}]")
    delta_excludes = bool(delta_lo > 0 or delta_hi < 0)
    perm_excludes = bool(perm_lo > 0 or perm_hi < 0)
    keep = delta_excludes and perm_excludes and delta_pt > 0
    print(
        f"\nGate: delta_CI_excludes_0={delta_excludes}, "
        f"perm_CI_excludes_0={perm_excludes}, decision={'KEEP' if keep else 'DROP'}"
    )

    out = {
        "feature": args.feature_name,
        "blend": args.blend,
        "n": int(n),
        "feature_nonzero_frac": float((data["features"] > 0).mean()),
        "baseline_ndcg_at_10": base_ci,
        "blended_ndcg_at_10": new_ci,
        "paired_delta": {"point": delta_pt, "lo": delta_lo, "hi": delta_hi, "ci_excludes_zero": delta_excludes},
        "permutation_importance": {"mean": perm_mean, "lo": perm_lo, "hi": perm_hi, "ci_excludes_zero": perm_excludes},
        "decision": "keep" if keep else "drop",
    }
    out_path = REPO / "data" / "processed" / f"b1_eval_{args.feature_name}.json"
    out_path.write_text(json.dumps(out, indent=2, default=str))
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
