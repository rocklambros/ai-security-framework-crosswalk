"""Merge mapper-generated edges back into ``data/processed/edges.json``.

Edges conform to ``schema/edge.schema.json`` with:

* ``confidence = "inferred"``
* ``provenance = "mapping_engine_v2"``
* ``score`` + ``signals`` populated from the pipeline

Dedup rule: for the same (source, target, rationale_code, provenance) tuple,
keep the existing edge unless the new one has *higher* confidence, with
``score`` as the tie-breaker.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import networkx as nx

from mapping_engine.config import PairConfig
from mapping_engine.engine.mapper import MappingResult

CONFIDENCE_RANK = {
    "unvalidated": 0,
    "inferred": 1,
    "expert": 2,
    "authoritative": 3,
}
PROVENANCE = "mapping_engine_v2"
DEFAULT_CONFIDENCE = "inferred"


def _edge_id(source: str, target: str, rationale: str, provenance: str) -> str:
    return f"{source}--{target}--{rationale}--{provenance}"


def _build_edges(result: MappingResult, G: nx.DiGraph) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for m in result.mappings:
        rc = m["rationale_code"]
        e = {
            "edge_id": _edge_id(m["source_node_id"], m["target_node_id"], rc, PROVENANCE),
            "source_node_id": m["source_node_id"],
            "target_node_id": m["target_node_id"],
            "source_framework": m.get("source_framework"),
            "target_framework": m.get("target_framework"),
            "rationale_code": rc,
            "rationale_label": m["rationale_label"],
            "relevance": m["relevance"],
            "confidence": DEFAULT_CONFIDENCE,
            "provenance": PROVENANCE,
            "score": round(float(m["score"]), 4),
            "signals": {k: round(float(v), 4) for k, v in m["signals"].items()},
            "notes": f"tier={m['tier']}",
        }
        out.append(e)
    return out


def merge_edges(
    result: MappingResult,
    G: nx.DiGraph,
    pair_config: PairConfig,
    edges_path: str | Path,
) -> dict[str, int]:
    """Merge newly-computed edges into ``edges_path`` in place.

    Returns a ``{added, updated, unchanged}`` dict and prints the same.
    """
    path = Path(edges_path)
    existing: list[dict[str, Any]] = []
    if path.exists():
        existing = json.loads(path.read_text())

    # Index existing by dedup key
    def key(e: dict[str, Any]) -> tuple[str, str, str, str]:
        return (
            e.get("source_node_id", ""),
            e.get("target_node_id", ""),
            e.get("rationale_code") or "",
            e.get("provenance", ""),
        )

    idx: dict[tuple[str, str, str, str], int] = {key(e): i for i, e in enumerate(existing)}
    new_edges = _build_edges(result, G)

    added = updated = unchanged = 0
    for e in new_edges:
        k = key(e)
        if k not in idx:
            existing.append(e)
            idx[k] = len(existing) - 1
            added += 1
            continue
        prev = existing[idx[k]]
        prev_rank = CONFIDENCE_RANK.get(prev.get("confidence", ""), 0)
        new_rank = CONFIDENCE_RANK.get(e.get("confidence", ""), 0)
        if new_rank > prev_rank or (
            new_rank == prev_rank and float(e.get("score") or 0.0) > float(prev.get("score") or 0.0)
        ):
            existing[idx[k]] = e
            updated += 1
        else:
            unchanged += 1

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(existing, indent=2, default=str))

    counts = {"added": added, "updated": updated, "unchanged": unchanged}
    print(f"[graph_writer] edges merged: added={added} updated={updated} unchanged={unchanged}")
    return counts
