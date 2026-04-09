"""Derive data/splits/frozen_tuples.json from human_test_frozen.jsonl.

Honesty firewall, layer 0: enumerate the set of (framework, id) tuples that
appear on either side of any frozen-test pair. Downstream producers of
training rows (Plan 2 gap selector, Plan 5 batch loader, Plan 6 calibration
sampler) must load this file and refuse to emit any row whose source or
target tuple intersects either set.

This script reads ONLY the structural identifier fields
(framework_pair, source_node_id, target_node_id) from the frozen file.
It never reads expert_tier or any label field. Running it does not
constitute "looking at" the frozen test.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

FROZEN_PATH = Path("data/splits/human_test_frozen.jsonl")
OUT_PATH = Path("data/splits/frozen_tuples.json")
HASHES_PATH = Path("data/splits/hashes.json")

ALLOWED_FIELDS = {"framework_pair", "source_node_id", "target_node_id"}


def split_node_id(node_id: str) -> tuple[str, str]:
    """Split a fully-qualified node id like 'owasp_llm:LLM02' into (fw, id)."""
    if ":" not in node_id:
        raise ValueError(f"node_id missing framework prefix: {node_id!r}")
    fw, _, rest = node_id.partition(":")
    return fw, rest


def main() -> None:
    source_tuples: set[tuple[str, str]] = set()
    target_tuples: set[tuple[str, str]] = set()
    pair_tuples: set[tuple[str, str, str, str]] = set()
    n_rows = 0

    with FROZEN_PATH.open() as fh:
        for line in fh:
            row = json.loads(line)
            # Structural fields only — never read expert_tier.
            leaked = set(row.keys()) - ALLOWED_FIELDS - {
                "pair_key", "pair_name", "source_text", "target_text", "expert_tier",
            }
            if leaked:
                raise RuntimeError(f"unexpected frozen-test fields: {leaked}")
            src_fw, src_id = split_node_id(row["source_node_id"])
            tgt_fw, tgt_id = split_node_id(row["target_node_id"])
            source_tuples.add((src_fw, src_id))
            target_tuples.add((tgt_fw, tgt_id))
            pair_tuples.add((src_fw, src_id, tgt_fw, tgt_id))
            n_rows += 1

    out = {
        "schema_version": 1,
        "derived_from": str(FROZEN_PATH),
        "n_rows": n_rows,
        "n_source_tuples": len(source_tuples),
        "n_target_tuples": len(target_tuples),
        "n_pair_tuples": len(pair_tuples),
        "source_tuples": sorted([list(t) for t in source_tuples]),
        "target_tuples": sorted([list(t) for t in target_tuples]),
        "pair_tuples": sorted([list(t) for t in pair_tuples]),
    }
    OUT_PATH.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")

    # Refresh hashes.json entry
    sha = hashlib.sha256(OUT_PATH.read_bytes()).hexdigest()
    hashes = json.loads(HASHES_PATH.read_text()) if HASHES_PATH.exists() else {}
    hashes.setdefault("splits", {})["frozen_tuples_json"] = {
        "path": str(OUT_PATH),
        "sha256": sha,
        "n_source_tuples": len(source_tuples),
        "n_target_tuples": len(target_tuples),
        "n_pair_tuples": len(pair_tuples),
    }
    HASHES_PATH.write_text(json.dumps(hashes, indent=2, sort_keys=True) + "\n")
    print(f"wrote {OUT_PATH} ({n_rows} rows → {len(source_tuples)} src / {len(target_tuples)} tgt / {len(pair_tuples)} pair tuples)")
    print(f"sha256={sha}")


if __name__ == "__main__":
    main()
