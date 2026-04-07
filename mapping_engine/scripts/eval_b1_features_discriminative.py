"""S5: Re-evaluate B-1 structural features under the discriminative metric.

Re-runs the three coverage>0 features that previously failed only due to
NDCG@10 saturation:

  - mitigation_lexical_match  (23% non-zero, owasp_agentic only)
  - source_out_degree_ratio   (93% non-zero)
  - mutual_reciprocal_rank    (93% non-zero)

For each feature, blends it into the composite at weight=0.10 and
re-scores positives + distractors via the same arrays the S3 baseline
froze. Reports paired-bootstrap MRR delta vs the B-2 baseline plus a
permutation-importance proxy on the per-anchor reciprocal-rank vector.

A feature is ADOPTED only if both the paired delta CI and the perm
importance CI exclude zero AND direction is positive. Otherwise the
feature stays dropped and the composite remains unchanged.

Reads:  data/processed/discriminative_baseline.json
Writes: data/processed/b1_discriminative_eval.json
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from mapping_engine.calibration.discriminative_metric import (
    _per_anchor_reciprocal_rank,
    bootstrap_ci,
    paired_bootstrap_delta,
    score,
)
from mapping_engine.calibration.distractor_sampler import sample_distractors
from mapping_engine.config import load_pair_config
from mapping_engine.engine.graph import load_graph
from mapping_engine.engine.mapper import PairMapper
from mapping_engine.engine.structural import compute_structural_features
from mapping_engine.scripts.learn_weights_b2 import _expanded_pair_configs

REPO = Path(__file__).resolve().parents[2]
PAIRS_DIR = REPO / "mapping_engine/config/pairs"
BASELINE_PATH = REPO / "data/processed/discriminative_baseline.json"
OUT_PATH = REPO / "data/processed/b1_discriminative_eval.json"

FEATURES = (
    "mitigation_lexical_match",
    "source_out_degree_ratio",
    "mutual_reciprocal_rank",
)
BLEND = 0.10
N_PER_ANCHOR = 20
RNG_SEED = 20260407


def _normalize_2d(M: np.ndarray) -> np.ndarray:
    if M.size == 0:
        return M
    lo, hi = float(M.min()), float(M.max())
    if hi - lo < 1e-9:
        return np.zeros_like(M)
    return (M - lo) / (hi - lo)


def _collect_blended(feature_name: str):
    G = load_graph(REPO / "data/processed/nodes.json", REPO / "data/processed/edges.json")
    per_pair_pos: list[list[float]] = []
    per_pair_dist: list[list[list[float]]] = []
    pair_names = []
    for name in _expanded_pair_configs():
        cfg = load_pair_config(name + "__expanded", validate_anchors_in=G)
        mapper = PairMapper(G, cfg, use_learned_weights=False)
        result = mapper.run()
        sources = list(result.source_nodes)
        targets = list(result.target_nodes)
        s_idx = {s: i for i, s in enumerate(sources)}
        t_idx = {t: i for i, t in enumerate(targets)}
        feats = compute_structural_features(G, sources, targets)
        if feature_name not in feats:
            raise SystemExit(f"feature {feature_name!r} not in compute_structural_features")
        F = _normalize_2d(np.asarray(feats[feature_name], dtype=float))
        comp = np.asarray(result.composite_scores, dtype=float)
        blended_matrix = (1.0 - BLEND) * comp + BLEND * F

        av = result.anchor_validation
        masked_records: dict = {}
        masked_records.update(av.get("training_anchors", {}))
        masked_records.update(av.get("holdout_anchors", {}))

        ds_list = sample_distractors(
            PAIRS_DIR / f"{name}__expanded.yaml", G,
            n_per_anchor=N_PER_ANCHOR, rng_seed=RNG_SEED,
        )
        pair_pos: list[float] = []
        pair_dist: list[list[float]] = []
        for ds in ds_list:
            key = f"{ds.source}__{ds.positive}"
            rec = masked_records.get(key)
            if rec is None or ds.source not in s_idx or ds.positive not in t_idx:
                continue
            si = s_idx[ds.source]
            ti = t_idx[ds.positive]
            # Blend the masked composite with the structural feature value
            # at the anchor's own (src,tgt) cell. The masked score is the
            # production composite without that anchor's expert edge; we
            # blend in the same proportion as the rest of the matrix.
            masked_pos = float(rec.get("score", 0.0))
            pos = (1.0 - BLEND) * masked_pos + BLEND * float(F[si, ti])
            d_row = [
                float(blended_matrix[si, t_idx[d]])
                for d in ds.distractors
                if d in t_idx
            ]
            if not d_row:
                continue
            pair_pos.append(pos)
            pair_dist.append(d_row)
        per_pair_pos.append(pair_pos)
        per_pair_dist.append(pair_dist)
        pair_names.append(name)
    return per_pair_pos, per_pair_dist, pair_names


def _flatten(per_pair_pos, per_pair_dist):
    pos = [s for p in per_pair_pos for s in p]
    dist = [d for p in per_pair_dist for d in p]
    return pos, dist


def _perm_importance(blended_pos, blended_dist, baseline_pos, baseline_dist, n_perms=50):
    """Permutation-importance proxy on the per-anchor RR vector.

    For each permutation, shuffle the per-anchor BLENDED minus BASELINE
    RR delta and measure how often the mean delta survives. If the
    feature is real signal, shuffling shouldn't keep the mean centered
    on the observed delta. Reported as the 95 % CI of the shuffled
    delta means; if that CI excludes zero in the WRONG direction, the
    perm gate fails.
    """
    rrs_blend = np.array(
        [_per_anchor_reciprocal_rank(p, d) for p, d in zip(blended_pos, blended_dist)]
    )
    rrs_base = np.array(
        [_per_anchor_reciprocal_rank(p, d) for p, d in zip(baseline_pos, baseline_dist)]
    )
    diffs = rrs_blend - rrs_base
    rng = np.random.default_rng(11)
    sample_means = np.empty(n_perms)
    for i in range(n_perms):
        signs = rng.choice([-1.0, 1.0], size=len(diffs))
        sample_means[i] = (signs * diffs).mean()
    lo = float(np.quantile(sample_means, 0.025))
    hi = float(np.quantile(sample_means, 0.975))
    obs = float(diffs.mean())
    # Real signal => observed mean should sit OUTSIDE the sign-shuffled
    # null distribution.
    excludes = bool(obs > hi or obs < lo)
    return {"observed_mean": obs, "null_lo": lo, "null_hi": hi, "ci_excludes_zero": excludes}


def main() -> None:
    base = json.loads(BASELINE_PATH.read_text())
    base_pos = base["scores"]["positive"]
    base_dist = base["scores"]["distractors"]
    base_score = score(base_pos, base_dist)
    print(
        f"baseline n={base_score.n_anchors} mrr={base_score.mrr:.4f} "
        f"recall@5={base_score.recall_at_5:.4f} auc={base_score.roc_auc:.4f}"
    )

    out: dict = {
        "blend": BLEND,
        "rng_seed": RNG_SEED,
        "baseline": base_score.to_dict(),
        "features": {},
    }

    for feat in FEATURES:
        print(f"\n=== {feat} ===")
        per_pair_pos, per_pair_dist, _ = _collect_blended(feat)
        blend_pos, blend_dist = _flatten(per_pair_pos, per_pair_dist)
        if len(blend_pos) != len(base_pos):
            print(
                f"  WARN: blended n={len(blend_pos)} != baseline n={len(base_pos)} — "
                "alignment may be off; reporting unaligned aggregate only"
            )
            blend_score = score(blend_pos, blend_dist)
            out["features"][feat] = {
                "n": len(blend_pos),
                "blended_aggregate": blend_score.to_dict(),
                "decision": "drop_unaligned",
            }
            continue
        blend_score = score(blend_pos, blend_dist)
        ci = bootstrap_ci(blend_pos, blend_dist, n_resamples=1000, rng_seed=RNG_SEED)
        paired = paired_bootstrap_delta(
            blend_pos, blend_dist, base_pos, base_dist,
            n_resamples=1000, rng_seed=RNG_SEED,
        )
        perm = _perm_importance(blend_pos, blend_dist, base_pos, base_dist, n_perms=200)
        delta_excl = paired["ci_excludes_zero"]
        perm_excl = perm["ci_excludes_zero"]
        keep = delta_excl and perm_excl and paired["delta_mrr_mean"] > 0
        decision = "KEEP" if keep else "DROP"
        print(
            f"  blended mrr={blend_score.mrr:.4f}  "
            f"delta={paired['delta_mrr_mean']:+.4f} {paired['delta_mrr_ci']}  "
            f"perm_obs={perm['observed_mean']:+.4f} null=[{perm['null_lo']:+.4f},{perm['null_hi']:+.4f}]  "
            f"-> {decision}"
        )
        out["features"][feat] = {
            "n": len(blend_pos),
            "blended_score": blend_score.to_dict(),
            "ci": ci,
            "paired_delta": paired,
            "perm_importance": perm,
            "decision": decision,
        }

    OUT_PATH.write_text(json.dumps(out, indent=2, default=str))
    print(f"\nWrote {OUT_PATH}")
    kept = [k for k, v in out["features"].items() if v.get("decision") == "KEEP"]
    print(f"Adopted features: {kept or 'none'}")


if __name__ == "__main__":
    main()
