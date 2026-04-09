"""Cross-source-list mapping benchmark on held-out upstream crossrefs.

Measures whether the crosswalk engine can recover upstream LLM<->Agentic<->DSGAI
gold edges that were held out by the frozen-tuple firewall. Evaluation
uses the bridge score as the ranker on the enriched graph -- the enriched
graph is free of held-out rows by construction.

Honesty:
    * Asserts ``human_test_frozen`` never appears in argv.
    * Calls ``verify_hashes`` before any reads.
    * Never opens any ``data/splits/human_*`` files.
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

from classifier.data.splits import verify_hashes
from mapping_engine.engine.graph import load_graph
from mapping_engine.engine.bridge import graph_bridge_scores
from mapping_engine.engine.upstream_prior_edges import load_upstream_prior_edges


RESULTS_PATH = Path("results/plan4_crossref_benchmark.json")


def rank_metrics(ranks: list[int]) -> dict:
    if not ranks:
        return {"n": 0, "mrr": 0.0, "hit_at_1": 0.0, "hit_at_5": 0.0, "hit_at_20": 0.0}
    n = len(ranks)
    mrr = sum(1.0 / r for r in ranks) / n
    return {
        "n": n,
        "mrr": mrr,
        "hit_at_1": sum(1 for r in ranks if r <= 1) / n,
        "hit_at_5": sum(1 for r in ranks if r <= 5) / n,
        "hit_at_20": sum(1 for r in ranks if r <= 20) / n,
    }


def _sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _git_sha() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--crossrefs", default="data/upstream/crossrefs_v1.jsonl")
    parser.add_argument("--partition", default="data/upstream/partition.json")
    parser.add_argument("--frozen-tuples", default="data/splits/frozen_tuples.json")
    args = parser.parse_args()

    verify_hashes()

    nodes_path = Path("data/processed/nodes.json")
    edges_path = Path("data/processed/edges.json")
    crossrefs_path = Path(args.crossrefs)
    partition_path = Path(args.partition)
    frozen_tuples_path = Path(args.frozen_tuples)

    G = load_graph(nodes_path, edges_path)

    by_fw: dict[str, list[str]] = defaultdict(list)
    for nid, d in G.nodes(data=True):
        fw = d.get("framework")
        if fw:
            by_fw[fw].append(nid)

    # Get the firewalled crossref edges as our benchmark set
    present = set(G.nodes())
    _, firewall_out = load_upstream_prior_edges(
        crossrefs_path, partition_path, present,
        frozen_tuples_path=frozen_tuples_path,
    )

    # Also get partition held-out rows directly
    partition = json.loads(partition_path.read_text())
    held_out_shas = set(partition.get("held_out") or [])
    crossref_rows = [
        json.loads(l) for l in crossrefs_path.read_text().splitlines() if l.strip()
    ]
    partition_held = [r for r in crossref_rows if r.get("provenance_sha") in held_out_shas]

    # Union of firewall_out + partition_held (deduplicated by provenance_sha)
    benchmark_set: dict[str, dict] = {}
    for row in firewall_out + partition_held:
        sha = row.get("provenance_sha", "")
        if sha not in benchmark_set:
            benchmark_set[sha] = row

    print(f"[benchmark_crossref] {len(firewall_out)} firewalled + "
          f"{len(partition_held)} partition-held = {len(benchmark_set)} benchmark rows (deduped)")

    ranks: list[int] = []
    skipped = 0
    for row in benchmark_set.values():
        if row.get("target_id_unresolved"):
            skipped += 1
            continue
        src_fw = row["source_framework"]
        src_id = row["source_id"]
        src = f"{src_fw}:{src_id}"
        gold = row.get("target_node_id") or f"{row['target_framework']}:{row.get('target_id', '')}"
        tgt_fw = row["target_framework"]
        candidates = by_fw.get(tgt_fw, [])
        if src not in G or gold not in candidates:
            skipped += 1
            continue
        bridge = graph_bridge_scores(G, [src], candidates, {})
        scored = sorted(zip(candidates, bridge[0]), key=lambda t: t[1], reverse=True)
        rank = next((i + 1 for i, (n, _) in enumerate(scored) if n == gold), None)
        if rank is None:
            skipped += 1
            continue
        ranks.append(rank)

    metrics = rank_metrics(ranks)
    metrics["skipped"] = skipped

    row_out = {
        "run_id": str(uuid.uuid4()),
        "utc": datetime.now(timezone.utc).isoformat(),
        "git_sha": _git_sha(),
        "input_hashes": {
            "nodes.json": _sha256(nodes_path),
            "edges.json": _sha256(edges_path),
            "crossrefs_v1.jsonl": _sha256(crossrefs_path),
            "partition.json": _sha256(partition_path),
        },
        "benchmark_source": {
            "firewalled": len(firewall_out),
            "partition_held": len(partition_held),
            "total_deduped": len(benchmark_set),
        },
        "metrics": metrics,
    }
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with RESULTS_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row_out, sort_keys=True) + "\n")
    print(json.dumps(row_out, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
