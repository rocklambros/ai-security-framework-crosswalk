"""CLI: run the full mapping pipeline for a single pair config.

Usage::

    python -m mapping_engine.scripts.run_pair aiuc_1__owasp_agentic [flags]

Flags:
    --no-rerank       Force-disable the cross-encoder reranker.
    --hand-tuned      Use hand-tuned weights from defaults.yaml (skip learned weights).
    --output-dir DIR  Where to write outputs (default: mapping_engine/output/results).
    --no-merge        Skip merging edges into data/processed/edges.json.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from mapping_engine.config import load_pair_config
from mapping_engine.engine.graph import load_graph
from mapping_engine.engine.mapper import PairMapper
from mapping_engine.output.excel_writer import write_excel
from mapping_engine.output.graph_writer import merge_edges
from mapping_engine.output.json_writer import write_json

REPO = Path(__file__).resolve().parents[2]
DEFAULT_NODES = REPO / "data" / "processed" / "nodes.json"
DEFAULT_EDGES = REPO / "data" / "processed" / "edges.json"
DEFAULT_OUT = REPO / "mapping_engine" / "output" / "results"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pair_name")
    ap.add_argument("--no-rerank", action="store_true")
    ap.add_argument("--hand-tuned", action="store_true")
    ap.add_argument("--output-dir", default=str(DEFAULT_OUT))
    ap.add_argument("--no-merge", action="store_true")
    args = ap.parse_args(argv)

    G = load_graph(DEFAULT_NODES, DEFAULT_EDGES)
    pair_cfg = load_pair_config(args.pair_name, validate_anchors_in=G)

    enable_rerank: bool | None = False if args.no_rerank else None
    mapper = PairMapper(
        G,
        pair_cfg,
        use_learned_weights=not args.hand_tuned,
        enable_reranker=enable_rerank,
    )
    result = mapper.run()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"{args.pair_name}.json"
    xlsx_path = out_dir / f"{args.pair_name}.xlsx"

    write_json(result, G, pair_cfg, json_path)
    write_excel(result, G, pair_cfg, xlsx_path)

    if not args.no_merge:
        merge_edges(result, G, pair_cfg, DEFAULT_EDGES)

    n_direct = sum(1 for m in result.mappings if m["tier"] == "Direct")
    n_related = sum(1 for m in result.mappings if m["tier"] == "Related")
    holdout_acc = result.anchor_validation["holdout_accuracy"]
    print(f"[run_pair] {args.pair_name}: {len(result.mappings)} mappings "
          f"(Direct={n_direct}, Related={n_related})")
    print(f"[run_pair] anchor holdout accuracy: {holdout_acc:.2f}")
    print(f"[run_pair] json: {json_path}")
    print(f"[run_pair] xlsx: {xlsx_path}")

    if holdout_acc < 1.0:
        print(f"[run_pair] ERROR: holdout accuracy {holdout_acc:.2f} < 1.0", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
