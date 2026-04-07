"""S2: Re-baseline the discriminative metric with cosai_rm pairs included.

Session 7.5 S3 shipped ``data/processed/discriminative_baseline.json``
under a known bug: both cosai_rm expanded pairs reported n_anc=0 because
their pair YAMLs declared source_entry_types that excluded every anchor
(see Session 7.6 S1 fix). Now that S1 has fixed the YAMLs, re-running
the harness should pick up cosai_rm__mitre_atlas as a newly scorable
non-frozen pair. cosai_rm__owasp_llm remains the Phase A frozen test
pair and is NOT scored here.

Writes ``data/processed/discriminative_baseline_s7_6.json`` alongside
(but NOT replacing) the Session 7.5 file, so downstream gates in S4..S13
can compare against the post-S1 baseline.
"""

from __future__ import annotations

import json
from pathlib import Path

from mapping_engine.calibration.discriminative_metric import bootstrap_ci, score
from mapping_engine.engine.graph import load_graph
from mapping_engine.scripts.eval_discriminative_baseline import (
    N_PER_ANCHOR,
    RNG_SEED,
    _collect_pair,
)
from mapping_engine.scripts.learn_weights_b2 import _expanded_pair_configs

REPO = Path(__file__).resolve().parents[2]


def main() -> None:
    G = load_graph(
        REPO / "data/processed/nodes.json", REPO / "data/processed/edges.json"
    )
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
        "session": "7.6",
        "post_task": "S2",
        "n_per_anchor": N_PER_ANCHOR,
        "rng_seed": RNG_SEED,
        "aggregate": {"score": agg.to_dict(), "ci": agg_ci},
        "per_pair": per_pair,
        "scores": {"positive": all_pos, "distractors": all_dist},
    }
    out_path = REPO / "data/processed/discriminative_baseline_s7_6.json"
    out_path.write_text(json.dumps(out, indent=2, default=str))
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
