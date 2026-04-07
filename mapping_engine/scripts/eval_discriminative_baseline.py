"""S3: Freeze the B-2 baseline under the anchors-vs-distractors metric.

For each non-frozen expanded pair we:
  1. Sample distractors via the S1 sampler (n_per_anchor=20, seed=20260407).
  2. Run PairMapper with the current B-2 hand-tuned weights and current
     calibrated thresholds (no special configuration — production path).
  3. For each anchor, take its masked composite score from
     ``result.anchor_validation`` (LOO masking, B2.7 protocol). For each
     of its distractors, take the unmasked composite score from
     ``result.composite_scores[source_idx, target_idx]``. Distractors are
     not anchors so masking does not apply to them.
  4. Compute aggregate MRR / Recall@5 / ROC-AUC + 1000-resample bootstrap
     CI per pair and across all pairs.

Persisted to ``data/processed/discriminative_baseline.json``. Subsequent
gates (S4 thresholds, S5 features, S6 reranker) read this file as the
fixed comparison point so the baseline is computed exactly once.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from mapping_engine.calibration.discriminative_metric import bootstrap_ci, score
from mapping_engine.calibration.distractor_sampler import sample_distractors
from mapping_engine.config import load_pair_config
from mapping_engine.engine.graph import load_graph
from mapping_engine.engine.mapper import PairMapper
from mapping_engine.scripts.learn_weights_b2 import _expanded_pair_configs

REPO = Path(__file__).resolve().parents[2]
PAIRS_DIR = REPO / "mapping_engine/config/pairs"
N_PER_ANCHOR = 20
RNG_SEED = 20260407


def _collect_pair(G, name: str):
    cfg = load_pair_config(name + "__expanded", validate_anchors_in=G)
    mapper = PairMapper(G, cfg, use_learned_weights=False)
    result = mapper.run()
    src_idx = {n: i for i, n in enumerate(result.source_nodes)}
    tgt_idx = {n: i for i, n in enumerate(result.target_nodes)}

    av = result.anchor_validation
    masked_records: dict = {}
    masked_records.update(av.get("training_anchors", {}))
    masked_records.update(av.get("holdout_anchors", {}))

    pair_yaml = PAIRS_DIR / f"{name}__expanded.yaml"
    distractor_sets = sample_distractors(
        pair_yaml, G, n_per_anchor=N_PER_ANCHOR, rng_seed=RNG_SEED
    )

    pos_scores: list[float] = []
    dist_scores: list[list[float]] = []
    skipped = 0
    for ds in distractor_sets:
        key = f"{ds.source}__{ds.positive}"
        rec = masked_records.get(key)
        if rec is None or ds.source not in src_idx:
            skipped += 1
            continue
        pos = float(rec.get("score", 0.0))
        si = src_idx[ds.source]
        d_row = []
        for d in ds.distractors:
            if d not in tgt_idx:
                continue
            d_row.append(float(result.composite_scores[si, tgt_idx[d]]))
        if not d_row:
            skipped += 1
            continue
        pos_scores.append(pos)
        dist_scores.append(d_row)

    return pos_scores, dist_scores, skipped


def main() -> None:
    G = load_graph(REPO / "data/processed/nodes.json", REPO / "data/processed/edges.json")
    per_pair = []
    all_pos: list[float] = []
    all_dist: list[list[float]] = []
    for name in _expanded_pair_configs():
        pos, dist, skipped = _collect_pair(G, name)
        s = score(pos, dist)
        ci = bootstrap_ci(pos, dist, n_resamples=1000, rng_seed=RNG_SEED)
        per_pair.append(
            {
                "pair": name,
                "n_anchors_scored": len(pos),
                "n_skipped": skipped,
                "score": s.to_dict(),
                "ci": ci,
            }
        )
        all_pos.extend(pos)
        all_dist.extend(dist)
        print(
            f"  {name}: n={len(pos)} mrr={s.mrr:.4f} "
            f"recall@5={s.recall_at_5:.4f} auc={s.roc_auc:.4f}"
        )

    agg = score(all_pos, all_dist)
    agg_ci = bootstrap_ci(all_pos, all_dist, n_resamples=1000, rng_seed=RNG_SEED)
    print(
        f"AGG n={agg.n_anchors} mrr={agg.mrr:.4f} "
        f"recall@5={agg.recall_at_5:.4f} auc={agg.roc_auc:.4f}"
    )
    print(
        f"  CI mrr={agg_ci['mrr']} recall@5={agg_ci['recall_at_5']} "
        f"auc={agg_ci['roc_auc']}"
    )

    out = {
        "n_per_anchor": N_PER_ANCHOR,
        "rng_seed": RNG_SEED,
        "aggregate": {
            "score": agg.to_dict(),
            "ci": agg_ci,
        },
        "per_pair": per_pair,
        "scores": {
            "positive": all_pos,
            "distractors": all_dist,
        },
    }
    out_path = REPO / "data/processed/discriminative_baseline.json"
    out_path.write_text(json.dumps(out, indent=2, default=str))
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
