"""Expand anchors for a framework pair from expert/authoritative edges.

For a given (source_framework, target_framework) pair, reads all
expert/authoritative cross-framework edges, derives ``expected_tier`` for each
via ``mapping_engine/config/rationale_to_tier.yaml``, and writes a new pair
config to ``mapping_engine/config/pairs/<pair>__expanded.yaml``.

Hand-curated configs (e.g. ``aiuc_1__owasp_agentic.yaml``) are NOT overwritten.
The expanded configs sit alongside as a higher-N alternative for calibration.

Holdout indices are auto-selected as 20% of the anchors, sampled with a fixed
seed (42) so the split is reproducible across runs.

Usage:
    python -m mapping_engine.scripts.expand_anchors aiuc_1 owasp_agentic
    python -m mapping_engine.scripts.expand_anchors aiuc_1 csa_aicm \\
        --source-entry-types control activity --target-entry-types control
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
EDGES = REPO / "data" / "processed" / "edges.json"
NODES = REPO / "data" / "processed" / "nodes.json"
PAIRS_DIR = REPO / "mapping_engine" / "config" / "pairs"
RATIONALE_TABLE = REPO / "mapping_engine" / "config" / "rationale_to_tier.yaml"

DEFAULT_HOLDOUT_FRACTION = 0.20
DEFAULT_SEED = 42


def _load_rationale_table() -> dict[str, dict]:
    return yaml.safe_load(RATIONALE_TABLE.read_text())


def _expert_edges_for_pair(
    edges: list[dict],
    node_fw: dict[str, str],
    source_fw: str,
    target_fw: str,
) -> list[dict]:
    out: list[dict] = []
    for e in edges:
        if e.get("confidence") not in ("expert", "authoritative"):
            continue
        src = e.get("source_node_id")
        tgt = e.get("target_node_id")
        if node_fw.get(src) != source_fw or node_fw.get(tgt) != target_fw:
            continue
        out.append(e)
    return out


def expand_pair(
    source_fw: str,
    target_fw: str,
    source_entry_types: list[str] | None = None,
    target_entry_types: list[str] | None = None,
    match_mode: str = "control_to_risk",
    holdout_fraction: float = DEFAULT_HOLDOUT_FRACTION,
    seed: int = DEFAULT_SEED,
) -> tuple[Path, dict]:
    """Build and write the expanded pair config. Returns (path, config_dict)."""
    edges = json.loads(EDGES.read_text())
    nodes = json.loads(NODES.read_text())
    node_fw = {n["node_id"]: n.get("framework") for n in nodes}
    node_et = {n["node_id"]: n.get("entry_type") for n in nodes}

    pair_edges = _expert_edges_for_pair(edges, node_fw, source_fw, target_fw)
    if not pair_edges:
        raise ValueError(
            f"no expert/authoritative edges found for {source_fw} -> {target_fw}"
        )

    table = _load_rationale_table()
    rc_to_tier = table["rationale_to_tier"]
    rc_to_weight = table.get("confidence_weight", {})

    # Deterministic ordering of anchors by (source, target) so the holdout
    # split is reproducible regardless of edges.json ordering.
    pair_edges.sort(key=lambda e: (e.get("source_node_id", ""), e.get("target_node_id", "")))

    # Emit only the 3 fields PairConfig.AnchorPair accepts. The rationale_code
    # and per-anchor confidence weight live in a sidecar block (anchor_metadata)
    # so the calibration loop in B2.7 can recover them without needing to
    # extend the PairConfig schema. The sidecar key is "source->target".
    anchors: list[dict] = []
    sidecar: dict[str, dict] = {}
    for e in pair_edges:
        rc = e.get("rationale_code") or "?"
        tier = rc_to_tier.get(rc, rc_to_tier.get("?", "Direct"))
        weight = rc_to_weight.get(rc, rc_to_weight.get("?", 1.0))
        src, tgt = e["source_node_id"], e["target_node_id"]
        anchors.append({"source": src, "target": tgt, "expected_tier": tier})
        sidecar[f"{src}->{tgt}"] = {
            "rationale_code": rc,
            "anchor_weight": float(weight),
        }

    n = len(anchors)
    n_holdout = max(1, int(round(n * holdout_fraction)))
    rng = random.Random(seed)
    holdout_indices = sorted(rng.sample(range(n), n_holdout))

    # Auto-union entry_types from the actual anchors so every anchor's
    # source/target node is selectable by PairMapper._select_nodes. Without
    # this, anchors referencing e.g. cosai_rm risks while source_entry_types
    # defaulted to ["control", "activity"] were silently dropped from the
    # masked-validation records (Session 7.6 S1 bug fix).
    src_types_base = list(source_entry_types or ["control", "activity"])
    tgt_types_base = list(target_entry_types or ["risk"])
    src_types = sorted(set(src_types_base) | {
        node_et.get(a["source"]) for a in anchors if node_et.get(a["source"])
    })
    tgt_types = sorted(set(tgt_types_base) | {
        node_et.get(a["target"]) for a in anchors if node_et.get(a["target"])
    })

    config: dict = {
        "source_framework": source_fw,
        "target_framework": target_fw,
        "source_entry_types": src_types,
        "target_entry_types": tgt_types,
        "match_mode": match_mode,
        "anchors": {
            "pairs": anchors,
            "holdout_indices": holdout_indices,
        },
    }
    # The sidecar is written to a sibling JSON file so the YAML stays valid
    # against PairConfig's strict schema.
    sidecar_path = PAIRS_DIR / f"{source_fw}__{target_fw}__expanded.metadata.json"
    sidecar_path.write_text(json.dumps(sidecar, indent=2, sort_keys=True))

    out_path = PAIRS_DIR / f"{source_fw}__{target_fw}__expanded.yaml"
    header = (
        f"# Auto-expanded anchor set for {source_fw} -> {target_fw}\n"
        f"# Generated by mapping_engine.scripts.expand_anchors\n"
        f"# {n} anchors derived from expert/authoritative edges; "
        f"holdout_fraction={holdout_fraction}, seed={seed}\n"
        f"# expected_tier values come from config/rationale_to_tier.yaml\n"
        f"# (an APPROXIMATE prior; CV is what actually decides whether they generalize).\n"
        f"# DO NOT EDIT BY HAND — re-run the script to regenerate.\n\n"
    )
    out_path.write_text(header + yaml.safe_dump(config, sort_keys=False))
    return out_path, config


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("source_framework")
    p.add_argument("target_framework")
    p.add_argument("--source-entry-types", nargs="*", default=None)
    p.add_argument("--target-entry-types", nargs="*", default=None)
    p.add_argument("--match-mode", default="control_to_risk")
    p.add_argument("--holdout-fraction", type=float, default=DEFAULT_HOLDOUT_FRACTION)
    p.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = p.parse_args()

    out_path, config = expand_pair(
        args.source_framework,
        args.target_framework,
        source_entry_types=args.source_entry_types,
        target_entry_types=args.target_entry_types,
        match_mode=args.match_mode,
        holdout_fraction=args.holdout_fraction,
        seed=args.seed,
    )
    n = len(config["anchors"]["pairs"])
    h = len(config["anchors"]["holdout_indices"])
    print(f"wrote {out_path.relative_to(REPO)}: {n} anchors, {h} holdout")
    tier_counts: dict[str, int] = {}
    for a in config["anchors"]["pairs"]:
        tier_counts[a["expected_tier"]] = tier_counts.get(a["expected_tier"], 0) + 1
    print(f"tier distribution: {tier_counts}")


if __name__ == "__main__":
    main()
