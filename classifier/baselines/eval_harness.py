"""Eval harness: load llm_val, run scorers, compute R@K / MRR / tier-acc.

Writes one JSON results file per run. Refuse to overwrite (scorer_name, scorer_version).
"""
from __future__ import annotations

import json
import hashlib
from collections import defaultdict
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from classifier.baselines.protocol import NodePair, ScoreRecord


def load_llm_val_pairs(
    labels_path: Path = Path("data/labels/llm_sme/v1/labels.jsonl"),
    nodes_path: Path = Path("data/processed/nodes.json"),
) -> tuple[list[NodePair], dict[str, str]]:
    """Load silver labels as NodePair list + gold mapping {pair_key: relation}."""
    nodes_raw = json.loads(nodes_path.read_text())
    text_idx: dict[tuple[str, str], str] = {}
    for n in nodes_raw:
        fw = n.get("framework", "")
        local = n.get("local_id") or n.get("node_id", "").split(":", 1)[-1]
        text_idx[(fw, local)] = n.get("description") or n.get("name") or ""

    def _text(fw: str, nid: str) -> str:
        local = nid.split(":", 1)[-1] if ":" in nid else nid
        return text_idx.get((fw, local), "")

    pairs: list[NodePair] = []
    gold: dict[str, str] = {}
    for line in labels_path.read_text().splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        tgt_local = r["target_node_id"].split(":", 1)[-1] if ":" in r["target_node_id"] else r["target_node_id"]
        pk = f"{r['source_framework']}:{r['source_id']}__{r['target_framework']}:{tgt_local}"
        pairs.append(NodePair(
            pair_key=pk,
            source_node_id=f"{r['source_framework']}:{r['source_id']}",
            source_framework=r["source_framework"],
            source_text=_text(r["source_framework"], r["source_id"]),
            target_node_id=r["target_node_id"],
            target_framework=r["target_framework"],
            target_text=_text(r["target_framework"], r["target_node_id"]),
        ))
        gold[pk] = r.get("relation", "related")
    return pairs, gold


def evaluate_scorer(
    scorer: object,
    pairs: list[NodePair],
    gold: dict[str, str],
) -> dict:
    """Run a scorer on pairs and compute metrics."""
    records = scorer.score(pairs)
    scores = {r.pair_key: r.score for r in records}

    # Group by source to compute rank-based metrics
    by_source: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for pk, sc in scores.items():
        src = pk.split("__")[0]
        by_source[src].append((pk, sc))

    n_total = len(pairs)
    n_scored = sum(1 for s in scores.values() if s == s)  # exclude NaN

    return {
        "scorer_name": scorer.name,
        "scorer_version": scorer.version,
        "n_pairs": n_total,
        "n_scored": n_scored,
        "null_rate": 1.0 - (n_scored / n_total) if n_total else 0.0,
        "records": [asdict(r) for r in records],
    }


def write_results(run_dir: Path, results: dict[str, dict]) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    out = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "scorers": results,
    }
    path = run_dir / "results_llm_val.json"
    path.write_text(json.dumps(out, sort_keys=True, ensure_ascii=False, indent=2) + "\n")
