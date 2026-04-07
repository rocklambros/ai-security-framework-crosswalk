"""CLI: scaffold a new pair YAML config.

Usage::

    python -m mapping_engine.scripts.add_pair <src_framework> <tgt_framework>
"""

from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from mapping_engine.engine.bridge import graph_bridge_scores
from mapping_engine.engine.graph import get_framework_nodes, load_graph

REPO = Path(__file__).resolve().parents[2]
NODES = REPO / "data" / "processed" / "nodes.json"
EDGES = REPO / "data" / "processed" / "edges.json"
PAIRS_DIR = REPO / "mapping_engine" / "config" / "pairs"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("source")
    ap.add_argument("target")
    args = ap.parse_args(argv)

    G = load_graph(NODES, EDGES)
    src_nodes = sorted(get_framework_nodes(G, args.source))
    tgt_nodes = sorted(get_framework_nodes(G, args.target))
    if not src_nodes or not tgt_nodes:
        raise SystemExit(
            f"no nodes found for source={args.source} ({len(src_nodes)}) "
            f"or target={args.target} ({len(tgt_nodes)})"
        )

    print(f"[add_pair] source={args.source}: {len(src_nodes)} nodes")
    print(f"[add_pair] target={args.target}: {len(tgt_nodes)} nodes")
    print("[add_pair] computing bridge scores for anchor candidates...")

    M = graph_bridge_scores(G, src_nodes, tgt_nodes)
    candidates: list[tuple[float, str, str]] = []
    for i, s in enumerate(src_nodes):
        for j, t in enumerate(tgt_nodes):
            candidates.append((float(M[i, j]), s, t))
    candidates.sort(key=lambda x: -x[0])
    top = candidates[:15]

    anchor_pairs = [
        {"source": s, "target": t, "expected_tier": ""} for _, s, t in top
    ]

    out_path = PAIRS_DIR / f"{args.source}__{args.target}.yaml"
    if out_path.exists():
        raise SystemExit(f"{out_path} already exists; refusing to overwrite")

    doc = {
        "source_framework": args.source,
        "target_framework": args.target,
        "source_entry_types": ["control"],
        "target_entry_types": ["risk"],
        "match_mode": "control_to_risk",
        "anchors": {
            "pairs": anchor_pairs,
            "holdout_indices": [2, 5, 8],
        },
    }
    PAIRS_DIR.mkdir(parents=True, exist_ok=True)
    out_path.write_text(yaml.safe_dump(doc, sort_keys=False))
    print(f"[add_pair] scaffolded {out_path}")
    print("[add_pair] NEXT: edit the file and fill in expected_tier for each anchor "
          "(Direct / Related / Tangential / None).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
