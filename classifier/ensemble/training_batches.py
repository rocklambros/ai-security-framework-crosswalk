"""Provenance-tagged training batch loader with Contract 10 runtime firewall.

Two-layer contamination defense:
  Layer 0: Frozen-tuple firewall (provenance-agnostic)
  Layer 1: Upstream held-out provenance_sha check

Every row yielded by iter_weighted_rows is checked against both layers.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator

DEFAULT_LABEL_WEIGHTS = {
    "upstream_v1": 1.0,
    "llm_sme_v1": 0.6,
    "human_cal_v1": 1.0,
}

FROZEN_TUPLES_PATH = Path("data/splits/frozen_tuples.json")
PARTITION_PATH = Path("data/upstream/partition.json")


def _load_frozen_endpoints(path: Path) -> tuple[frozenset, frozenset, frozenset]:
    ft = json.loads(path.read_text())
    frozen_src = frozenset(tuple(s) for s in ft["source_tuples"])
    frozen_tgt = frozenset(tuple(t) for t in ft["target_tuples"])
    frozen_pairs = frozenset(tuple(p) for p in ft["pair_tuples"])
    return frozen_src, frozen_tgt, frozen_pairs


def _load_held_out_shas(path: Path) -> frozenset:
    part = json.loads(path.read_text())
    return frozenset(part.get("held_out", []))


def _extract_endpoints(row: dict) -> tuple[tuple, tuple]:
    src_nid = row.get("source_node_id", "")
    if not src_nid:
        src_fw = row["source_framework"]
        src_id = row["source_id"]
    else:
        src_fw = src_nid.split(":")[0]
        src_id = src_nid.split(":", 1)[1] if ":" in src_nid else src_nid

    tgt_nid = row.get("target_node_id", "")
    tgt_fw = row.get("target_framework") or (tgt_nid.split(":")[0] if ":" in tgt_nid else "")
    tgt_id = tgt_nid.split(":", 1)[1] if ":" in tgt_nid else tgt_nid

    return (src_fw, src_id), (tgt_fw, tgt_id)


def iter_weighted_rows(
    labels_path: str | Path,
    weight_map: dict[str, float] | None = None,
    frozen_tuples_path: str | Path = FROZEN_TUPLES_PATH,
    partition_path: str | Path = PARTITION_PATH,
) -> Iterator[tuple[dict, float]]:
    """Yield (row, weight) tuples from a labels JSONL file.

    Contract 10: Two-layer runtime contamination assertion.
    Layer 0: Frozen-tuple firewall (fires on any provenance source).
    Layer 1: Upstream held-out provenance_sha check.

    Raises RuntimeError if any row violates either layer.
    Raises FileNotFoundError if frozen_tuples.json is missing.
    """
    frozen_tuples_path = Path(frozen_tuples_path)
    if not frozen_tuples_path.exists():
        raise FileNotFoundError(
            f"Contract 10: frozen_tuples.json missing at {frozen_tuples_path}. "
            f"No silent fallback."
        )

    weights = {**DEFAULT_LABEL_WEIGHTS, **(weight_map or {})}
    frozen_src, frozen_tgt, frozen_pairs = _load_frozen_endpoints(frozen_tuples_path)
    held_out_shas = _load_held_out_shas(Path(partition_path))

    labels_path = Path(labels_path)
    for i, line in enumerate(labels_path.read_text().splitlines()):
        if not line.strip():
            continue
        row = json.loads(line)
        src_ep, tgt_ep = _extract_endpoints(row)

        # Layer 0: Frozen-tuple firewall
        if src_ep in frozen_src:
            raise RuntimeError(
                f"Contract 10 Layer 0: frozen source tuple {src_ep} in row {i}"
            )
        if tgt_ep in frozen_tgt:
            raise RuntimeError(
                f"Contract 10 Layer 0: frozen target tuple {tgt_ep} in row {i}"
            )
        pair = (*src_ep, *tgt_ep)
        if pair in frozen_pairs:
            raise RuntimeError(
                f"Contract 10 Layer 0: frozen pair tuple {pair} in row {i}"
            )

        # Layer 1: Upstream held-out SHA check
        prov_sha = row.get("provenance_sha", "")
        if prov_sha and prov_sha in held_out_shas:
            raise RuntimeError(
                f"Contract 10 Layer 1: held-out provenance_sha {prov_sha[:16]}... in row {i}"
            )

        # Apply per-tag weight
        tag = row.get("provenance_tag", "llm_sme_v1")
        w = weights.get(tag, 1.0)

        yield row, w
