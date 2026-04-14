#!/usr/bin/env python3
"""Merge LLM scorer output with split pair data to produce v2/labels.jsonl.

Reads:
  - data/processed/llm_scores_v4/human_cal.jsonl (scored pairs)
  - data/splits/human_cal.jsonl (pair metadata)

Writes:
  - data/labels/llm_sme/v2/labels.jsonl (freeze-compatible format)

The output format matches v1/labels.jsonl so freeze_and_split() works unchanged.
"""
from __future__ import annotations

import json
from pathlib import Path

SCORES_DIR = Path("data/processed/llm_scores_v4")
SPLITS_DIR = Path("data/splits")
V2_DIR = Path("data/labels/llm_sme/v2")

TIER_TO_RELATION = {3: "equivalent", 2: "related", 1: "partial", 0: "unrelated"}

# Confidence-to-weight mapping (same heuristic as v1)
TIER_TO_WEIGHT = {3: 0.9, 2: 0.6, 1: 0.4, 0: 0.3}


def _load_jsonl(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def main():
    # Load scored output (from LLM scoring)
    scores_path = SCORES_DIR / "human_cal.jsonl"
    if not scores_path.exists():
        raise FileNotFoundError(f"LLM scores not found: {scores_path}")
    scores = _load_jsonl(scores_path)

    # Load split pair metadata
    pairs_path = SPLITS_DIR / "human_cal.jsonl"
    pairs = _load_jsonl(pairs_path)

    if len(scores) != len(pairs):
        raise ValueError(
            f"Score/pair count mismatch: {len(scores)} scores vs {len(pairs)} pairs. "
            f"Re-run LLM scoring on the current splits."
        )

    # Build lookup from (source_id, target_id) -> score record
    score_by_key = {}
    for s in scores:
        key = (s["source_id"], s["target_id"])
        score_by_key[key] = s

    labels = []
    matched = 0
    for pair in pairs:
        src_nid = pair["source_node_id"]
        tgt_nid = pair["target_node_id"]
        key = (src_nid, tgt_nid)

        if key not in score_by_key:
            print(f"  WARN: no score for {key}, skipping")
            continue

        sc = score_by_key[key]
        tier = sc["final_tier"]
        relation = TIER_TO_RELATION.get(tier, "unrelated")

        # Split node_id into framework + local_id
        src_fw, src_id = src_nid.split(":", 1)
        tgt_fw = tgt_nid.split(":", 1)[0]

        labels.append({
            "source_framework": src_fw,
            "source_id": src_id,
            "target_framework": tgt_fw,
            "target_node_id": tgt_nid,
            "relation": relation,
            "confidence": sc["confidence"],
            "weight": TIER_TO_WEIGHT.get(tier, 0.3),
            "provenance_tag": "llm_sme_v2",
            "model_version": "claude-sonnet-4-20250514",
            "prompt_sha": "",
            "rationale": "",
        })
        matched += 1

    V2_DIR.mkdir(parents=True, exist_ok=True)
    out_path = V2_DIR / "labels.jsonl"
    dumper = lambda r: json.dumps(r, sort_keys=True, ensure_ascii=True)
    with out_path.open("w") as f:
        for r in labels:
            f.write(dumper(r) + "\n")

    print(f"Merged {matched}/{len(pairs)} pairs into {out_path}")
    print(f"  Relation distribution: ", end="")
    from collections import Counter
    dist = Counter(r["relation"] for r in labels)
    print(dict(sorted(dist.items())))


if __name__ == "__main__":
    main()
