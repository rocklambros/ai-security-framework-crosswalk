"""Load upstream crossref rows as high-confidence prior edges for the graph.

Consumes ``data/upstream/crossrefs_v1.jsonl`` and ``data/upstream/partition.json``.

Held-out rows (per the strict contamination partition) and rows touching
frozen-tuple endpoints are filtered out before any edges are emitted.
Every emitted edge carries ``edge_type="upstream_crossref"``,
``provenance="upstream_crossref_v1"``, ``confidence="authoritative"``.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable


def _iter_jsonl(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def load_upstream_prior_edges(
    crossrefs_path: str | Path,
    partition_path: str | Path,
    present_node_ids: Iterable[str],
    frozen_tuples_path: str | Path | None = None,
    warnings: list[str] | None = None,
) -> tuple[list[dict], list[dict]]:
    """Return (injected_edges, firewall_held_out_rows).

    Parameters
    ----------
    crossrefs_path : Path
        Path to ``crossrefs_v1.jsonl``.
    partition_path : Path
        Path to ``partition.json`` with ``held_out`` provenance_sha list.
    present_node_ids : Iterable[str]
        Node IDs currently in the graph.
    frozen_tuples_path : Path | None
        Path to ``frozen_tuples.json``. If provided, rows touching frozen
        source/target tuples are firewalled into the held-out set.
    warnings : list[str] | None
        Optional accumulator for skip reasons.
    """
    present = set(present_node_ids)
    partition = json.loads(Path(partition_path).read_text())
    held_out_shas = set(partition.get("held_out") or [])

    # Load frozen-tuple firewall if available
    frozen_src: set[tuple[str, str]] = set()
    frozen_tgt: set[tuple[str, str]] = set()
    if frozen_tuples_path is not None:
        ft_path = Path(frozen_tuples_path)
        if not ft_path.exists():
            raise RuntimeError(
                f"frozen_tuples.json missing at {ft_path}. "
                "Refusing to inject upstream crossref edges."
            )
        frozen = json.loads(ft_path.read_text())
        frozen_src = {tuple(t) for t in frozen.get("source_tuples", [])}
        frozen_tgt = {tuple(t) for t in frozen.get("target_tuples", [])}

    rows = _iter_jsonl(Path(crossrefs_path))
    injected: list[dict] = []
    firewall_out: list[dict] = []

    for line_no, row in enumerate(rows, start=1):
        sha = row.get("provenance_sha") or ""

        # Layer 0: frozen-tuple firewall
        src_fw = row["source_framework"]
        src_id = row["source_id"]
        src_node = f"{src_fw}:{src_id}"
        tgt_node = row.get("target_node_id") or f"{row['target_framework']}:{row.get('target_id', '')}"
        tgt_fw = row.get("target_framework", "")
        tgt_id = tgt_node.split(":", 1)[-1] if ":" in tgt_node else ""

        if (src_fw, src_id) in frozen_src or (tgt_fw, tgt_id) in frozen_tgt:
            firewall_out.append(row)
            continue

        # Layer 1: partition held-out
        if sha in held_out_shas:
            firewall_out.append(row)
            continue

        # Drop unresolved
        if row.get("target_id_unresolved"):
            if warnings is not None:
                warnings.append(
                    f"[upstream_prior_edges] line {line_no}: target_id_unresolved "
                    f"{tgt_fw}:{row.get('target_id')}"
                )
            continue

        # Drop if either endpoint missing from graph
        if src_node not in present:
            if warnings is not None:
                warnings.append(
                    f"[upstream_prior_edges] line {line_no}: source node "
                    f"{src_node} not present in graph"
                )
            continue
        if tgt_node not in present:
            if warnings is not None:
                warnings.append(
                    f"[upstream_prior_edges] line {line_no}: target node "
                    f"{tgt_node} not present in graph"
                )
            continue

        injected.append(
            {
                "source_node_id": src_node,
                "target_node_id": tgt_node,
                "source_framework": src_fw,
                "target_framework": tgt_fw,
                "rationale_code": "upstream_crossref",
                "rationale_label": "Upstream source-list crossref",
                "relevance": "related",
                "confidence": "authoritative",
                "provenance": "upstream_crossref_v1",
                "edge_type": "upstream_crossref",
                "notes": f"provenance_sha={sha}",
                "score": None,
                "signals": None,
            }
        )

    return injected, firewall_out
