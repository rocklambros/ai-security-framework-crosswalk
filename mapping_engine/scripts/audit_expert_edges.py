"""Audit expert/authoritative cross-framework edges per ordered framework pair.

Prints, for each ordered ``(source_framework, target_framework)`` pair, the count
of edges with confidence in {"expert", "authoritative"} and the rationale_code
distribution. Used by Phase B-2 to size the auto-generated anchor sets.

Usage:
    python -m mapping_engine.scripts.audit_expert_edges
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
EDGES = REPO / "data" / "processed" / "edges.json"
NODES = REPO / "data" / "processed" / "nodes.json"


def main() -> None:
    edges = json.loads(EDGES.read_text())
    nodes = json.loads(NODES.read_text())
    node_fw = {n["node_id"]: n.get("framework") for n in nodes}

    pair_counts: dict[tuple[str, str], int] = defaultdict(int)
    pair_rcs: dict[tuple[str, str], Counter] = defaultdict(Counter)
    pair_confs: dict[tuple[str, str], Counter] = defaultdict(Counter)

    for e in edges:
        conf = e.get("confidence")
        if conf not in ("expert", "authoritative"):
            continue
        src = e.get("source_node_id")
        tgt = e.get("target_node_id")
        sfw = node_fw.get(src)
        tfw = node_fw.get(tgt)
        if not sfw or not tfw or sfw == tfw:
            continue
        key = (sfw, tfw)
        pair_counts[key] += 1
        pair_rcs[key][e.get("rationale_code") or "?"] += 1
        pair_confs[key][conf] += 1

    rows = sorted(pair_counts.items(), key=lambda kv: (-kv[1], kv[0]))
    print(f"{'source_framework':<22} {'target_framework':<22} {'n':>5}  {'auth/exp':<12} rationale_codes")
    print("-" * 110)
    for (sfw, tfw), n in rows:
        confs = pair_confs[(sfw, tfw)]
        ce = f"{confs.get('authoritative', 0)}/{confs.get('expert', 0)}"
        rc_str = ", ".join(f"{k}={v}" for k, v in pair_rcs[(sfw, tfw)].most_common())
        print(f"{sfw:<22} {tfw:<22} {n:>5}  {ce:<12} {rc_str}")
    print("-" * 110)
    print(f"total ordered pairs with expert/authoritative cross-framework edges: {len(rows)}")
    print(f"total edges: {sum(pair_counts.values())}")


if __name__ == "__main__":
    main()
