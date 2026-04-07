"""Benchmark the cross-encoder reranker on AIUC-1 → OWASP Agentic.

Computes composite scores using the four signals + composer, applies the
reranker, and reports tier-change counts plus anchor accuracy. If the
reranker degrades anchor accuracy, prints a warning recommending
``reranker.enabled=false`` in ``defaults.yaml``.

Usage::

    python -m mapping_engine.scripts.benchmark_reranker
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from mapping_engine.config import load_pair_config
from mapping_engine.engine.bridge import graph_bridge_scores
from mapping_engine.engine.composer import (
    TIER_DIRECT,
    TIER_NONE,
    TIER_RELATED,
    TIER_TANGENTIAL,
    compose_scores,
)
from mapping_engine.engine.function_match import compute_function_match
from mapping_engine.engine.graph import get_framework_nodes, load_graph
from mapping_engine.engine.keyword import compute_keyword_similarity
from mapping_engine.engine.reranker import rerank_candidates
from mapping_engine.engine.semantic import compute_semantic_similarity

REPO = Path(__file__).resolve().parents[2]

CONFIG = {
    "weights": {"bridge": 0.45, "semantic": 0.35, "keyword": 0.20, "boost": 0.50},
    "thresholds": {
        "direct": 0.55, "related_primary": 0.35, "related_secondary": 0.50,
        "gov_floor": 0.22, "tangential": 0.20,
    },
}

TIER_NAMES = {
    TIER_NONE: "None",
    TIER_TANGENTIAL: "Tangential",
    TIER_RELATED: "Related",
    TIER_DIRECT: "Direct",
}


def _tier_for_score(s: float) -> int:
    if s >= 0.55:
        return TIER_DIRECT
    if s >= 0.35:
        return TIER_RELATED
    if s >= 0.20:
        return TIER_TANGENTIAL
    return TIER_NONE


def _anchor_accuracy(scores: np.ndarray, sources, targets, anchors) -> float:
    hits = 0
    n = 0
    for ap in anchors:
        if ap.source in sources and ap.target in targets:
            i, j = sources.index(ap.source), targets.index(ap.target)
            pred = TIER_NAMES[_tier_for_score(float(scores[i, j]))]
            if pred == ap.expected_tier:
                hits += 1
            n += 1
    return hits / n if n else 0.0


def main() -> None:
    G = load_graph(REPO / "data/processed/nodes.json", REPO / "data/processed/edges.json")
    cfg = load_pair_config("aiuc_1__owasp_agentic", validate_anchors_in=G)
    sources = sorted(get_framework_nodes(G, cfg.source_framework, ["control"]))
    targets = sorted(get_framework_nodes(G, cfg.target_framework, ["risk"]))

    print(f"Sources: {len(sources)}  Targets: {len(targets)}")
    bridge = graph_bridge_scores(G, sources, targets)
    semantic = compute_semantic_similarity(G, sources, targets)
    keyword = compute_keyword_similarity(G, sources, targets)
    fm = compute_function_match(G, sources, targets)

    composite, tiers_before = compose_scores(bridge, semantic, keyword, fm, CONFIG)

    reranked = rerank_candidates(
        G, sources, targets, composite,
        {"reranker": {"top_k": 10, "blend_weight": 0.30}},
    )
    tiers_after = np.vectorize(_tier_for_score)(reranked)

    changed = int((tiers_before != tiers_after).sum())
    promotions = int((tiers_after > tiers_before).sum())
    demotions = int((tiers_after < tiers_before).sum())

    acc_before = _anchor_accuracy(composite, sources, targets, cfg.anchors.pairs)
    acc_after = _anchor_accuracy(reranked, sources, targets, cfg.anchors.pairs)

    print(f"Tier changes: {changed} (promotions={promotions}, demotions={demotions})")
    print(f"Anchor accuracy: before={acc_before:.3f}  after={acc_after:.3f}")

    if acc_after < acc_before:
        print("WARNING: reranker degrades anchor accuracy. Set reranker.enabled=false in defaults.yaml.")

    out = {
        "n_sources": len(sources),
        "n_targets": len(targets),
        "tier_changes": changed,
        "promotions": promotions,
        "demotions": demotions,
        "anchor_accuracy_before": acc_before,
        "anchor_accuracy_after": acc_after,
    }
    out_path = REPO / "data" / "processed" / "reranker_benchmark.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
