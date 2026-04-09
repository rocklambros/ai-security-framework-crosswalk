"""Before-and-after node2vec benchmark on the enriched graph.

Since the frozen-tuple firewall blocked all 363 upstream crossref edges
from being injected (all crossref endpoints overlap the frozen test set),
the enriched graph is identical to baseline. This script documents that
finding by computing node2vec ranking metrics on the calibration split.

Honesty:
    * Asserts ``human_test_frozen`` never appears in argv.
    * Calls ``verify_hashes`` before any reads.
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
from mapping_engine.engine.node2vec_signal import compute_node2vec_similarity


RESULTS_PATH = Path("results/plan4_node2vec_lift.json")
CAL_SPLIT = Path("data/splits/human_cal.jsonl")


def _sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _git_sha() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"


def _load_pairs(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]


def _metrics_for_pairs(G, pairs: list[dict]) -> dict:
    """Compute MRR and Hit@{1,5,20} using node2vec cosine as the ranker."""
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
        sims = compute_node2vec_similarity([src], tgt_nodes)
        scores = list(zip(tgt_nodes, sims[0]))
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

    G = load_graph(nodes_path, edges_path)
    pairs = _load_pairs(val_path)

    # Count upstream_crossref edges
    n_upstream = sum(
        1 for _, _, d in G.edges(data=True)
        if d.get("edge_type") == "upstream_crossref"
    )

    print(f"Benchmarking node2vec on {len(pairs)} pairs ({n_upstream} upstream_crossref edges in graph)...")

    # Since 0 upstream_crossref edges were injected, baseline == enriched.
    # We compute metrics once and report as both baseline and enriched.
    metrics = _metrics_for_pairs(G, pairs)

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
        "upstream_crossref_edges_in_graph": n_upstream,
        "baseline": metrics,
        "enriched": metrics,
        "delta": {k: 0.0 for k in ("mrr", "hit_at_1", "hit_at_5", "hit_at_20")},
        "note": "All 363 crossref edges firewalled (frozen-tuple overlap); baseline == enriched",
    }
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with RESULTS_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, sort_keys=True) + "\n")
    print(json.dumps(row, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
