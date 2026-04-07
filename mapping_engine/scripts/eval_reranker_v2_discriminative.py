"""S6: Re-evaluate the fine-tuned reranker_v2 under the discriminative metric.

For each non-frozen expanded pair we run PairMapper twice:
  1. Baseline = post-S5 pipeline (no reranker_v2; mitigation_lexical_match
     blended in via the production path).
  2. Reranker_v2 = same pipeline but cfg.reranker swapped to point at
     ``mapping_engine/models/reranker_v2/`` and enable_reranker=True.

For each anchor we score the positive (masked-graph composite) and the
20 sampled distractors (unmasked composite from the appropriate matrix)
under each model, then compute paired-bootstrap MRR delta with sign
shuffling and permutation importance.

Decision rule: ADOPT only if paired CI excludes 0 AND direction positive.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from mapping_engine.calibration.discriminative_metric import (
    bootstrap_ci,
    paired_bootstrap_delta,
    score,
)
from mapping_engine.calibration.distractor_sampler import sample_distractors
from mapping_engine.config import load_pair_config
from mapping_engine.engine.graph import load_graph
from mapping_engine.engine.mapper import PairMapper
from mapping_engine.scripts.learn_weights_b2 import _expanded_pair_configs

REPO = Path(__file__).resolve().parents[2]
PAIRS_DIR = REPO / "mapping_engine/config/pairs"
RERANKER_DIR = REPO / "mapping_engine/models/reranker_v2"
OUT_PATH = REPO / "data/processed/reranker_v2_discriminative_eval.json"
N_PER_ANCHOR = 20
RNG_SEED = 20260407


def _collect(G, name: str, *, use_reranker: bool):
    cfg = load_pair_config(name + "__expanded", validate_anchors_in=G)
    if use_reranker:
        rer = dict(cfg.reranker or {})
        rer["enabled"] = True
        rer["model"] = str(RERANKER_DIR)
        cfg.reranker = rer
    mapper = PairMapper(
        G, cfg, use_learned_weights=False, enable_reranker=use_reranker
    )
    result = mapper.run()
    src_idx = {n: i for i, n in enumerate(result.source_nodes)}
    tgt_idx = {n: i for i, n in enumerate(result.target_nodes)}

    av = result.anchor_validation
    masked_records: dict = {}
    masked_records.update(av.get("training_anchors", {}))
    masked_records.update(av.get("holdout_anchors", {}))

    ds_list = sample_distractors(
        PAIRS_DIR / f"{name}__expanded.yaml", G,
        n_per_anchor=N_PER_ANCHOR, rng_seed=RNG_SEED,
    )
    pos_scores: list[float] = []
    dist_scores: list[list[float]] = []
    keys: list[str] = []
    for ds in ds_list:
        key = f"{ds.source}__{ds.positive}"
        rec = masked_records.get(key)
        if rec is None or ds.source not in src_idx:
            continue
        si = src_idx[ds.source]
        d_row = [
            float(result.composite_scores[si, tgt_idx[d]])
            for d in ds.distractors
            if d in tgt_idx
        ]
        if not d_row:
            continue
        pos_scores.append(float(rec.get("score", 0.0)))
        dist_scores.append(d_row)
        keys.append(key)
    return keys, pos_scores, dist_scores


def main() -> None:
    G = load_graph(REPO / "data/processed/nodes.json", REPO / "data/processed/edges.json")
    base_pos: list[float] = []
    base_dist: list[list[float]] = []
    rer_pos: list[float] = []
    rer_dist: list[list[float]] = []
    per_pair = []
    for name in _expanded_pair_configs():
        kb, pb, db = _collect(G, name, use_reranker=False)
        kr, pr, dr = _collect(G, name, use_reranker=True)
        # Align by anchor key (the masked-validation set is identical
        # across both runs because anchor masking is deterministic).
        rer_lookup = {k: (p, d) for k, p, d in zip(kr, pr, dr)}
        ab_pos, ab_dist, ar_pos, ar_dist = [], [], [], []
        for k, p, d in zip(kb, pb, db):
            if k not in rer_lookup:
                continue
            ab_pos.append(p)
            ab_dist.append(d)
            ar_pos.append(rer_lookup[k][0])
            ar_dist.append(rer_lookup[k][1])
        base_pos.extend(ab_pos)
        base_dist.extend(ab_dist)
        rer_pos.extend(ar_pos)
        rer_dist.extend(ar_dist)
        if ab_pos:
            sb = score(ab_pos, ab_dist)
            sr = score(ar_pos, ar_dist)
            per_pair.append(
                {
                    "pair": name,
                    "n": len(ab_pos),
                    "baseline_mrr": sb.mrr,
                    "reranker_mrr": sr.mrr,
                }
            )
            print(f"  {name}: n={len(ab_pos)} base={sb.mrr:.4f} rer={sr.mrr:.4f}")

    base_s = score(base_pos, base_dist)
    rer_s = score(rer_pos, rer_dist)
    base_ci = bootstrap_ci(base_pos, base_dist, n_resamples=1000, rng_seed=RNG_SEED)
    rer_ci = bootstrap_ci(rer_pos, rer_dist, n_resamples=1000, rng_seed=RNG_SEED)
    paired = paired_bootstrap_delta(
        rer_pos, rer_dist, base_pos, base_dist,
        n_resamples=1000, rng_seed=RNG_SEED,
    )
    decision = "ADOPT" if (paired["ci_excludes_zero"] and paired["delta_mrr_mean"] > 0) else "DROP"
    print(f"\naggregate n={base_s.n_anchors}")
    print(f"  baseline mrr:    {base_s.mrr:.4f}  CI {base_ci['mrr']}")
    print(f"  reranker_v2 mrr: {rer_s.mrr:.4f}  CI {rer_ci['mrr']}")
    print(f"  paired delta:    {paired['delta_mrr_mean']:+.4f} {paired['delta_mrr_ci']}")
    print(f"  decision: {decision}")

    out = {
        "n_per_anchor": N_PER_ANCHOR,
        "rng_seed": RNG_SEED,
        "n_anchors": base_s.n_anchors,
        "baseline": base_s.to_dict() | {"ci": base_ci},
        "reranker_v2": rer_s.to_dict() | {"ci": rer_ci},
        "paired_delta": paired,
        "decision": decision,
        "per_pair": per_pair,
    }
    OUT_PATH.write_text(json.dumps(out, indent=2, default=str))
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
