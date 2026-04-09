"""Before-and-after bridge benchmark on the non-frozen calibration split.

Runs the bridge benchmark twice against the currently built graph:
    1. Baseline -- strip upstream_crossref edges in memory
    2. Enriched -- keep them

Appends one row to ``results/plan4_bridge_lift.json``.

Honesty:
    * Asserts ``human_test_frozen`` never appears in argv.
    * Calls ``verify_hashes()`` before reading data.
    * Reads only ``data/processed/nodes.json`` + ``edges.json`` and the
      non-frozen calibration split.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

assert "human_test_frozen" not in ",".join(sys.argv), "Contract 2: frozen test is off limits"

import numpy as np

from classifier.data.splits import verify_hashes
from mapping_engine.engine.graph import load_graph
from mapping_engine.engine.bridge import graph_bridge_scores


RESULTS_PATH = Path("results/plan4_bridge_lift.json")
CAL_SPLIT = Path("data/splits/human_cal.jsonl")


def _sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _git_sha() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"


def _strip_upstream_crossref_edges(G):
    import networkx as nx
    H = G.copy()
    to_remove = [
        (u, v, k) for u, v, k, d in H.edges(data=True, keys=True)
        if d.get("edge_type") == "upstream_crossref"
    ] if H.is_multigraph() else [
        (u, v) for u, v, d in H.edges(data=True)
        if d.get("edge_type") == "upstream_crossref"
    ]
    H.remove_edges_from(to_remove)
    return H


def _load_pairs(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]


def _metrics_for_graph(G, pairs: list[dict]) -> dict:
    """Compute MRR and Hit@{1,5,20} using bridge_scores as the ranker."""
    by_tgt_fw: dict[str, list[str]] = defaultdict(list)
    for nid, d in G.nodes(data=True):
        fw = d.get("framework")
        if fw:
            by_tgt_fw[fw].append(nid)

    reciprocal_ranks: list[float] = []
    hits = {1: 0, 5: 0, 20: 0}
    considered = 0
    for row in pairs:
        src = row["source_node_id"]
        gold = row["target_node_id"]
        tgt_fw = row.get("target_framework") or gold.split(":")[0]
        tgt_nodes = by_tgt_fw.get(tgt_fw, [])
        if src not in G or gold not in tgt_nodes:
            continue
        bridge = graph_bridge_scores(G, [src], tgt_nodes, {})
        scores = list(zip(tgt_nodes, bridge[0]))
        scores.sort(key=lambda t: t[1], reverse=True)
        rank = next((i + 1 for i, (n, _) in enumerate(scores) if n == gold), None)
        if rank is None:
            continue
        considered += 1
        reciprocal_ranks.append(1.0 / rank)
        for k in hits:
            if rank <= k:
                hits[k] += 1

    n = max(considered, 1)
    return {
        "n_pairs_scored": considered,
        "mrr": sum(reciprocal_ranks) / n,
        "hit_at_1": hits[1] / n,
        "hit_at_5": hits[5] / n,
        "hit_at_20": hits[20] / n,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--val", default=str(CAL_SPLIT))
    args = parser.parse_args()

    verify_hashes()

    nodes_path = Path("data/processed/nodes.json")
    edges_path = Path("data/processed/edges.json")
    val_path = Path(args.val)

    G_enriched = load_graph(nodes_path, edges_path)
    G_baseline = _strip_upstream_crossref_edges(G_enriched)
    pairs = _load_pairs(val_path)

    print(f"Benchmarking bridge on {len(pairs)} pairs...")
    enriched = _metrics_for_graph(G_enriched, pairs)
    baseline = _metrics_for_graph(G_baseline, pairs)

    row = {
        "run_id": str(uuid.uuid4()),
        "utc": datetime.now(timezone.utc).isoformat(),
        "git_sha": _git_sha(),
        "input_hashes": {
            "nodes.json": _sha256(nodes_path),
            "edges.json": _sha256(edges_path),
            "val_split": _sha256(val_path),
        },
        "val_path": str(val_path),
        "baseline": baseline,
        "enriched": enriched,
        "delta": {k: enriched[k] - baseline[k] for k in ("mrr", "hit_at_1", "hit_at_5", "hit_at_20")},
        "upstream_crossref_edges_in_graph": sum(
            1 for _, _, d in G_enriched.edges(data=True)
            if d.get("edge_type") == "upstream_crossref"
        ),
    }
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with RESULTS_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, sort_keys=True) + "\n")
    print(json.dumps(row, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
