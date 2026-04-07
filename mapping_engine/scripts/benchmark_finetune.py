"""Benchmark fine-tuned vs base embedding model on AIUC and NIST.

Reports anchor scores, mean separation between mapped and unmapped
pairs, and retrieval precision@5 for both AIUC-1 → OWASP and NIST →
OWASP. The decision rule from the spec: if the fine-tuned model does
not improve NIST precision@5 by >5 points, keep the base model.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from mapping_engine.config import load_pair_config
from mapping_engine.engine.graph import get_framework_nodes, load_graph
from mapping_engine.engine.semantic import (
    _EMBEDDING_CACHE,
    compute_semantic_similarity,
)

REPO = Path(__file__).resolve().parents[2]
BASE_MODEL = "BAAI/bge-large-en-v1.5"
FT_MODEL = str(REPO / "mapping_engine" / "models" / "finetuned-crosswalk-v1")


def _precision_at_k(sim: np.ndarray, sources, targets, mapped: set[tuple[str, str]], k: int = 5) -> float:
    if sim.shape[1] < k:
        k = sim.shape[1]
    hits = 0
    n_rows_with_gt = 0
    for i, s in enumerate(sources):
        gts = {t for t in targets if (s, t) in mapped}
        if not gts:
            continue
        n_rows_with_gt += 1
        top = np.argsort(-sim[i])[:k]
        if any(targets[j] in gts for j in top):
            hits += 1
    return hits / n_rows_with_gt if n_rows_with_gt else 0.0


def _separation(sim: np.ndarray, sources, targets, mapped: set[tuple[str, str]]) -> dict:
    pos, neg = [], []
    for i, s in enumerate(sources):
        for j, t in enumerate(targets):
            (pos if (s, t) in mapped else neg).append(float(sim[i, j]))
    return {
        "mapped_mean": float(np.mean(pos)) if pos else 0.0,
        "unmapped_mean": float(np.mean(neg)) if neg else 0.0,
        "delta": float(np.mean(pos) - np.mean(neg)) if pos and neg else 0.0,
    }


def _benchmark(G, model_name: str, df: pd.DataFrame, sources, targets) -> dict:
    _EMBEDDING_CACHE.clear()
    sim = compute_semantic_similarity(G, sources, targets, {"model": model_name})
    mapped = {(r.source_node_id, r.target_node_id) for r in df[df.is_mapped == 1].itertuples()}
    return {
        "precision_at_5": _precision_at_k(sim, sources, targets, mapped, k=5),
        "separation": _separation(sim, sources, targets, mapped),
    }


def main() -> None:
    G = load_graph(REPO / "data/processed/nodes.json", REPO / "data/processed/edges.json")
    cfg = load_pair_config("aiuc_1__owasp_agentic", validate_anchors_in=G)

    aiuc = sorted(get_framework_nodes(G, "aiuc_1", entry_types=["control"]))
    nist = sorted(get_framework_nodes(G, "nist_rmf", entry_types=["subcategory"]))
    owasp = sorted(get_framework_nodes(G, "owasp_agentic", entry_types=["risk"]))

    train_df = pd.read_csv(REPO / "data/processed/training_data.csv")
    nist_df = pd.read_csv(REPO / "data/processed/nist_validation_data.csv")

    out = {}
    for tag, mname in (("base", BASE_MODEL), ("finetuned", FT_MODEL)):
        print(f"\n=== {tag}: {mname} ===")
        aiuc_metrics = _benchmark(G, mname, train_df, aiuc, owasp)
        nist_metrics = _benchmark(G, mname, nist_df, nist, owasp)
        # anchor scores
        _EMBEDDING_CACHE.clear()
        sim = compute_semantic_similarity(G, aiuc, owasp, {"model": mname})
        anchors = []
        for ap in cfg.anchors.pairs:
            if ap.source in aiuc and ap.target in owasp:
                i, j = aiuc.index(ap.source), owasp.index(ap.target)
                anchors.append({
                    "source": ap.source, "target": ap.target,
                    "expected": ap.expected_tier, "score": float(sim[i, j]),
                })
        out[tag] = {
            "model": mname,
            "aiuc": aiuc_metrics,
            "nist": nist_metrics,
            "anchors": anchors,
        }
        print(f"  AIUC P@5: {aiuc_metrics['precision_at_5']:.3f}  "
              f"sep={aiuc_metrics['separation']['delta']:+.3f}")
        print(f"  NIST P@5: {nist_metrics['precision_at_5']:.3f}  "
              f"sep={nist_metrics['separation']['delta']:+.3f}")

    base_p5 = out["base"]["nist"]["precision_at_5"]
    ft_p5 = out["finetuned"]["nist"]["precision_at_5"]
    delta = ft_p5 - base_p5
    out["decision"] = {
        "base_nist_p5": base_p5,
        "finetuned_nist_p5": ft_p5,
        "delta": delta,
        "winner": "finetuned" if delta > 0.05 else "base",
    }
    print(f"\nNIST P@5: base={base_p5:.3f}  finetuned={ft_p5:.3f}  Δ={delta:+.3f}")
    print(f"Decision: {out['decision']['winner']}")

    out_path = REPO / "data" / "processed" / "finetune_benchmark.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
