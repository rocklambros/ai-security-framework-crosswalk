"""CLI: post-pipeline sanity checks on ``nodes.json`` / ``edges.json``.

* Every edge endpoint must exist in nodes.
* No duplicate (source, target, rationale_code, provenance) tuples.
* Orphan node report (no inbound or outbound edges).
* Refresh ``data/processed/graph_stats.json``.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
NODES = REPO / "data" / "processed" / "nodes.json"
EDGES = REPO / "data" / "processed" / "edges.json"
STATS = REPO / "data" / "processed" / "graph_stats.json"


def main(argv: list[str] | None = None) -> int:
    nodes = json.loads(NODES.read_text())
    edges = json.loads(EDGES.read_text())
    node_ids = {n["node_id"] for n in nodes}

    missing_endpoints: list[str] = []
    dup_counts: Counter = Counter()
    for e in edges:
        s, t = e.get("source_node_id"), e.get("target_node_id")
        if s not in node_ids:
            missing_endpoints.append(f"missing source: {s}")
        if t not in node_ids:
            missing_endpoints.append(f"missing target: {t}")
        dup_counts[(s, t, e.get("rationale_code"), e.get("provenance"))] += 1
    dups = [k for k, v in dup_counts.items() if v > 1]

    inbound = Counter()
    outbound = Counter()
    for e in edges:
        outbound[e.get("source_node_id")] += 1
        inbound[e.get("target_node_id")] += 1
    orphans = [nid for nid in node_ids if inbound[nid] == 0 and outbound[nid] == 0]

    fw_stats: dict[str, dict[str, int]] = {}
    for n in nodes:
        fw = n.get("framework", "unknown")
        fw_stats.setdefault(fw, {"nodes": 0, "outbound_edges": 0, "inbound_edges": 0})
        fw_stats[fw]["nodes"] += 1
    for e in edges:
        sfw = e.get("source_framework")
        tfw = e.get("target_framework")
        if sfw and sfw in fw_stats:
            fw_stats[sfw]["outbound_edges"] += 1
        if tfw and tfw in fw_stats:
            fw_stats[tfw]["inbound_edges"] += 1

    stats = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "node_count": len(nodes),
        "edge_count": len(edges),
        "frameworks": fw_stats,
        "orphan_count": len(orphans),
        "duplicate_edge_count": len(dups),
        "missing_endpoint_count": len(missing_endpoints),
    }
    STATS.write_text(json.dumps(stats, indent=2))

    print(f"[validate_graph] nodes={len(nodes)} edges={len(edges)}")
    print(f"[validate_graph] orphans={len(orphans)} "
          f"duplicates={len(dups)} missing_endpoints={len(missing_endpoints)}")

    if missing_endpoints:
        print("[validate_graph] ERROR: missing endpoints", file=sys.stderr)
        for msg in missing_endpoints[:10]:
            print(f"  {msg}", file=sys.stderr)
        return 1
    if dups:
        print(f"[validate_graph] WARN: {len(dups)} duplicate edge keys")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
