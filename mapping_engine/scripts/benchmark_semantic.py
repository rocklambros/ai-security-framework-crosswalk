"""Benchmark v1 (all-MiniLM-L6-v2) vs v2 (BAAI/bge-large-en-v1.5) embeddings.

Loads the crosswalk graph, runs both models on the AIUC-1 → OWASP Agentic
risk slice, and reports inference time, raw cosine spread, normalized
spread, and per-anchor scores.

Usage::

    python -m mapping_engine.scripts.benchmark_semantic
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np

from mapping_engine.config import load_pair_config
from mapping_engine.engine.graph import get_framework_nodes, load_graph
from mapping_engine.engine.semantic import (
    _load_model,
    _zscore_sigmoid,
    compute_embeddings,
)
from sklearn.metrics.pairwise import cosine_similarity

REPO = Path(__file__).resolve().parents[2]

MODELS = [
    ("v1_minilm", "sentence-transformers/all-MiniLM-L6-v2"),
    ("v2_bge_large", "BAAI/bge-large-en-v1.5"),
]


def _bench_one(G, all_nodes, sources, targets, model_name):
    model = _load_model(model_name)
    t0 = time.perf_counter()
    _ = compute_embeddings(G, all_nodes, model)
    t_all = time.perf_counter() - t0

    src_emb = compute_embeddings(G, sources, model)
    tgt_emb = compute_embeddings(G, targets, model)
    raw = cosine_similarity(src_emb, tgt_emb).astype(np.float64)
    norm = _zscore_sigmoid(raw)
    return {
        "model": model_name,
        "encode_time_sec_983": float(t_all),
        "raw_mean": float(raw.mean()),
        "raw_std": float(raw.std()),
        "norm_mean": float(norm.mean()),
        "norm_std": float(norm.std()),
        "raw_matrix": raw,
        "norm_matrix": norm,
    }


def main() -> None:
    G = load_graph(REPO / "data/processed/nodes.json", REPO / "data/processed/edges.json")
    cfg = load_pair_config("aiuc_1__owasp_agentic", validate_anchors_in=G)

    sources = sorted(get_framework_nodes(G, cfg.source_framework, cfg.source_entry_types or None))
    targets = sorted(get_framework_nodes(G, cfg.target_framework, cfg.target_entry_types or None))
    all_nodes = sorted({n for n, _ in G.nodes(data=True)})

    print(f"Sources: {len(sources)}  Targets: {len(targets)}  All: {len(all_nodes)}\n")

    out_payload: dict = {"models": []}
    for tag, model_name in MODELS:
        print(f"=== {tag}: {model_name} ===")
        try:
            r = _bench_one(G, all_nodes, sources, targets, model_name)
        except Exception as ex:
            print(f"  [skipped] {ex}")
            out_payload["models"].append({"tag": tag, "model": model_name, "error": str(ex)})
            continue
        anchors = []
        for ap in cfg.anchors.pairs:
            if ap.source in sources and ap.target in targets:
                i = sources.index(ap.source)
                j = targets.index(ap.target)
                anchors.append({
                    "source": ap.source, "target": ap.target,
                    "expected_tier": ap.expected_tier,
                    "raw": float(r["raw_matrix"][i, j]),
                    "norm": float(r["norm_matrix"][i, j]),
                })
        print(f"  encode 983 nodes: {r['encode_time_sec_983']:.2f}s")
        print(f"  raw  μ={r['raw_mean']:.4f}  σ={r['raw_std']:.4f}")
        print(f"  norm μ={r['norm_mean']:.4f}  σ={r['norm_std']:.4f}")
        print(f"  anchor avg norm: {np.mean([a['norm'] for a in anchors]):.4f}")
        out_payload["models"].append({
            "tag": tag,
            "model": model_name,
            "encode_time_sec_983": r["encode_time_sec_983"],
            "raw_mean": r["raw_mean"], "raw_std": r["raw_std"],
            "norm_mean": r["norm_mean"], "norm_std": r["norm_std"],
            "anchors": anchors,
        })

    out_path = REPO / "data" / "processed" / "semantic_benchmark.json"
    out_path.write_text(json.dumps(out_payload, indent=2))
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
