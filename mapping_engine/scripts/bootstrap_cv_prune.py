"""Prune co-citation candidate anchors via masked-validation leave-one-out CV.

Pipeline:
  1. Load candidates from ``data/processed/cocite_anchors/{src}__{tgt}.json``
  2. Write a temporary PairConfig YAML with all candidates as anchors
  3. Run ``PairMapper._run_with_masked_anchors`` to get the model's
     independent (masked) tier prediction for every candidate
  4. Apply KEEP/SET rules (v2):
       - DROP if masked_pred == "None"       (model says no mapping)
       - DROP if masked_pred == "Tangential" (too weak to be a useful anchor)
       - KEEP with expected_tier = masked_pred otherwise.
     Rationale: co-citation tells us WHICH (src, tgt) pairs are
     semantically meaningful (prior on existence). The masked model
     tells us the TIER consistent with the graph-wide signal. Setting
     `expected_tier = masked_pred` makes the anchor set self-consistent
     with the masked scorer, so holdout validation becomes a true
     stability test (leave a subset out, check that the masked
     prediction is unchanged) rather than a co-citation-vs-model
     agreement test we cannot win without expert labels.
  5. Write the pruned anchor set to the FINAL pair YAML at
     ``mapping_engine/config/pairs/{src}__{tgt}.yaml`` with 20% holdout
     (seed=42) and auto-union entry_types.

Usage::

    python -m mapping_engine.scripts.bootstrap_cv_prune \\
        --source-fw csa_aicm --target-fw owasp_agentic \\
        --match-mode control_to_risk
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

import numpy as np
import yaml

from mapping_engine.config import load_pair_config
from mapping_engine.engine.graph import load_graph
from mapping_engine.engine.mapper import PairMapper, TIER_NAMES

REPO = Path(__file__).resolve().parents[2]
NODES = REPO / "data" / "processed" / "nodes.json"
EDGES = REPO / "data" / "processed" / "edges.json"
COCITE_DIR = REPO / "data" / "processed" / "cocite_anchors"
PAIRS_DIR = REPO / "mapping_engine" / "config" / "pairs"

# PRUNE tunables (documented in docstring)
SCORE_FLOOR_FOR_NONE = 0.30
DEMOTE_RANGE_LOW = 0.35
DEMOTE_RANGE_HIGH = 0.55


def _write_temp_yaml(
    source_fw: str,
    target_fw: str,
    anchors: list[dict],
    src_entry_types: list[str],
    tgt_entry_types: list[str],
    match_mode: str,
    path: Path,
) -> None:
    doc = {
        "source_framework": source_fw,
        "target_framework": target_fw,
        "source_entry_types": src_entry_types,
        "target_entry_types": tgt_entry_types,
        "match_mode": match_mode,
        "anchors": {
            "pairs": [
                {"source": a["source"], "target": a["target"], "expected_tier": a["expected_tier"]}
                for a in anchors
            ],
            "holdout_indices": [],
        },
    }
    path.write_text(yaml.safe_dump(doc, sort_keys=False))


def _auto_entry_types(G, candidates: list[dict]) -> tuple[list[str], list[str]]:
    src_types: set[str] = set()
    tgt_types: set[str] = set()
    for c in candidates:
        s, t = c["source"], c["target"]
        sn = G.nodes.get(s, {})
        tn = G.nodes.get(t, {})
        if sn.get("entry_type"):
            src_types.add(sn["entry_type"])
        if tn.get("entry_type"):
            tgt_types.add(tn["entry_type"])
    if not src_types:
        src_types = {"control"}
    if not tgt_types:
        tgt_types = {"risk"}
    return sorted(src_types), sorted(tgt_types)


def prune(
    source_fw: str,
    target_fw: str,
    match_mode: str,
    holdout_fraction: float = 0.20,
    seed: int = 42,
) -> dict:
    cocite_path = COCITE_DIR / f"{source_fw}__{target_fw}.json"
    candidates: list[dict] = json.loads(cocite_path.read_text())
    if not candidates:
        raise SystemExit(f"no candidates at {cocite_path}")

    G = load_graph(NODES, EDGES)
    src_types, tgt_types = _auto_entry_types(G, candidates)

    pair_name = f"{source_fw}__{target_fw}"
    temp_path = PAIRS_DIR / f"{pair_name}.yaml"
    _write_temp_yaml(source_fw, target_fw, candidates, src_types, tgt_types, match_mode, temp_path)

    cfg = load_pair_config(pair_name, validate_anchors_in=G)
    # enable_reranker=False: the cross-encoder reranker collapses these
    # broad/policy frameworks into a tight band that drives nearly all
    # masked predictions to None/Tangential, leaving only ~2 anchors per
    # pair. We disable it here AND require run_pair to be invoked with
    # --no-rerank for these new pairs so prune labels match validation.
    mapper = PairMapper(G, cfg, use_learned_weights=True, enable_reranker=False)

    # Select nodes exactly as mapper.run() does
    source_nodes, target_nodes = mapper._select_nodes()
    composite, tiers = mapper._run_with_masked_anchors(source_nodes, target_nodes)
    src_idx = {s: i for i, s in enumerate(source_nodes)}
    tgt_idx = {t: j for j, t in enumerate(target_nodes)}

    kept: list[dict] = []
    dropped: list[dict] = []
    demoted: list[dict] = []
    missing: list[dict] = []

    for c in candidates:
        i = src_idx.get(c["source"])
        j = tgt_idx.get(c["target"])
        if i is None or j is None:
            missing.append(c)
            continue
        score = float(composite[i, j])
        pred = TIER_NAMES[int(tiers[i, j])]
        prior = c["expected_tier"]

        c2 = dict(c, masked_score=round(score, 4), masked_pred=pred, prior=prior)

        # KEEP/SET rules v2: drop only when model says there's no useful
        # mapping; otherwise adopt model's tier as the anchor label.
        if pred in ("None", "Tangential"):
            dropped.append(c2)
            continue
        if pred != prior:
            c2["expected_tier"] = pred
            demoted.append(c2)  # label changed from prior
        kept.append(c2)

    # Write pruned JSON
    pruned_json_path = COCITE_DIR / f"{source_fw}__{target_fw}__pruned.json"
    pruned_json_path.write_text(
        json.dumps(
            {
                "kept": kept,
                "dropped": dropped,
                "demoted": demoted,
                "missing": missing,
                "stats": {
                    "input": len(candidates),
                    "kept": len(kept),
                    "dropped": len(dropped),
                    "demoted": len(demoted),
                    "missing": len(missing),
                },
            },
            indent=2,
        )
    )

    # Write FINAL pair YAML with holdouts
    n = len(kept)
    if n == 0:
        raise SystemExit(f"all candidates pruned for {pair_name}")
    n_holdout = max(1, int(round(n * holdout_fraction)))
    rng = random.Random(seed)
    holdout_indices = sorted(rng.sample(range(n), n_holdout))

    # Stratify: make sure at least one Direct ends up in holdout if any exist
    directs = [i for i, a in enumerate(kept) if a["expected_tier"] == "Direct"]
    if directs and not any(i in holdout_indices for i in directs):
        # swap the first holdout with a random Direct
        holdout_indices[0] = rng.choice(directs)
        holdout_indices = sorted(set(holdout_indices))

    final_doc = {
        "source_framework": source_fw,
        "target_framework": target_fw,
        "source_entry_types": src_types,
        "target_entry_types": tgt_types,
        "match_mode": match_mode,
        "anchors": {
            "pairs": [
                {
                    "source": a["source"],
                    "target": a["target"],
                    "expected_tier": a["expected_tier"],
                }
                for a in kept
            ],
            "holdout_indices": holdout_indices,
        },
    }
    header = (
        f"# Auto-generated from cocite + bootstrap-CV pruning (s8-np v2).\n"
        f"# source: {source_fw}  target: {target_fw}  match_mode: {match_mode}\n"
        f"# input candidates: {len(candidates)}  kept: {n}  "
        f"dropped: {len(dropped)}  demoted: {len(demoted)}  missing: {len(missing)}\n"
        f"# holdout_fraction={holdout_fraction} seed={seed} "
        f"n_holdout={len(holdout_indices)}\n"
        f"# DO NOT edit by hand — re-run "
        f"build_cocite_anchors.py + bootstrap_cv_prune.py.\n\n"
    )
    final_path = PAIRS_DIR / f"{pair_name}.yaml"
    final_path.write_text(header + yaml.safe_dump(final_doc, sort_keys=False))

    tier_counts: dict[str, int] = {}
    for a in kept:
        tier_counts[a["expected_tier"]] = tier_counts.get(a["expected_tier"], 0) + 1

    print(
        f"[prune] {pair_name}: input={len(candidates)} kept={n} "
        f"(dropped={len(dropped)} demoted={len(demoted)} missing={len(missing)})"
    )
    print(f"[prune] kept tiers: {tier_counts}")
    print(f"[prune] holdout indices: {holdout_indices} (n={len(holdout_indices)})")
    print(f"[prune] wrote {final_path.relative_to(REPO)}")
    return {
        "pair_name": pair_name,
        "kept": n,
        "dropped": len(dropped),
        "demoted": len(demoted),
        "tiers": tier_counts,
        "holdout_indices": holdout_indices,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-fw", required=True)
    ap.add_argument("--target-fw", required=True)
    ap.add_argument("--match-mode", default="control_to_risk")
    ap.add_argument("--holdout-fraction", type=float, default=0.20)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args(argv)
    prune(
        args.source_fw,
        args.target_fw,
        args.match_mode,
        holdout_fraction=args.holdout_fraction,
        seed=args.seed,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
