"""S7: One-shot frozen-test pass under the discriminative metric.

Re-runs the three frozen pairs (B-2: aiuc_1__csa_aicm, B-1:
aiuc_1__mitre_atlas, A: cosai_rm__owasp_llm) with the post-S5 production
pipeline (mitigation_lexical_match blended in; reranker_v2 dropped per
S6; thresholds unchanged at 0.45/0.20 per S4). For each pair we sample
distractors via the S1 sampler, score positives + distractors, and
report MRR / Recall@5 / ROC-AUC + 1000-resample bootstrap CI plus the
tier-classification accuracy at the calibrated thresholds.

This script is intended to be run EXACTLY ONCE per phase. The frozen
results are appended to docs/frozen_test_results.md verbatim and never
re-tuned, regardless of outcome.
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

REPO = Path(__file__).resolve().parents[2]
PAIRS_DIR = REPO / "mapping_engine/config/pairs"
OUT_PATH = REPO / "data/processed/frozen_tests_discriminative.json"
DIRECT_THRESHOLD = 0.45
RELATED_THRESHOLD = 0.20
N_PER_ANCHOR = 20
RNG_SEED = 20260407

FROZEN_PAIRS = [
    ("B-2", "aiuc_1__csa_aicm"),
    ("B-1", "aiuc_1__mitre_atlas"),
    ("A",   "cosai_rm__owasp_llm"),
]


def _eval_pair(G, name: str):
    cfg = load_pair_config(name + "__expanded", validate_anchors_in=G)
    mapper = PairMapper(G, cfg, use_learned_weights=False)
    result = mapper.run()
    src_idx = {n: i for i, n in enumerate(result.source_nodes)}
    tgt_idx = {n: i for i, n in enumerate(result.target_nodes)}
    av = result.anchor_validation
    masked: dict = {}
    masked.update(av.get("training_anchors", {}))
    masked.update(av.get("holdout_anchors", {}))

    ds_list = sample_distractors(
        PAIRS_DIR / f"{name}__expanded.yaml", G,
        n_per_anchor=N_PER_ANCHOR, rng_seed=RNG_SEED,
    )
    pos_scores: list[float] = []
    dist_scores: list[list[float]] = []
    for ds in ds_list:
        key = f"{ds.source}__{ds.positive}"
        rec = masked.get(key)
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

    pos_arr = np.asarray(pos_scores)
    dist_flat = np.concatenate([np.asarray(d) for d in dist_scores]) if dist_scores else np.array([])
    n_pos = len(pos_arr)
    n_dist = len(dist_flat)
    pos_direct = int((pos_arr >= DIRECT_THRESHOLD).sum())
    pos_related = int(((pos_arr >= RELATED_THRESHOLD) & (pos_arr < DIRECT_THRESHOLD)).sum())
    pos_none = int((pos_arr < RELATED_THRESHOLD).sum())
    dist_nontop = int((dist_flat < RELATED_THRESHOLD).sum())
    tier_acc = (pos_direct + pos_related) / max(1, n_pos)  # positives correctly mapped
    tnr = dist_nontop / max(1, n_dist)
    s = score(pos_scores, dist_scores)
    ci = bootstrap_ci(pos_scores, dist_scores, n_resamples=1000, rng_seed=RNG_SEED)
    return {
        "n_anchors_scored": n_pos,
        "n_distractors_total": n_dist,
        "score": s.to_dict(),
        "ci": ci,
        "tier_classification": {
            "positive_direct": pos_direct,
            "positive_related": pos_related,
            "positive_none": pos_none,
            "tier_accuracy": tier_acc,
            "true_negative_rate": tnr,
        },
    }


def main() -> None:
    G = load_graph(REPO / "data/processed/nodes.json", REPO / "data/processed/edges.json")
    out = {
        "rng_seed": RNG_SEED,
        "n_per_anchor": N_PER_ANCHOR,
        "thresholds": {"direct": DIRECT_THRESHOLD, "related_primary": RELATED_THRESHOLD},
        "pairs": {},
    }
    for phase, name in FROZEN_PAIRS:
        print(f"=== {phase}: {name} ===")
        r = _eval_pair(G, name)
        out["pairs"][name] = {"phase": phase, **r}
        s = r["score"]
        ci = r["ci"]
        tc = r["tier_classification"]
        print(
            f"  n={s['n_anchors']}  mrr={s['mrr']:.4f} {ci['mrr']}  "
            f"recall@5={s['recall_at_5']:.4f}  auc={s['roc_auc']:.4f}"
        )
        print(
            f"  tier_acc={tc['tier_accuracy']:.4f}  TNR={tc['true_negative_rate']:.4f}  "
            f"(pos D/R/N = {tc['positive_direct']}/{tc['positive_related']}/{tc['positive_none']})"
        )
    OUT_PATH.write_text(json.dumps(out, indent=2, default=str))
    print(f"\nWrote {OUT_PATH}")


if __name__ == "__main__":
    main()
