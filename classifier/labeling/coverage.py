from __future__ import annotations
import json
from collections import defaultdict
from pathlib import Path
from .schemas import CoverageRow


class CoverageError(RuntimeError):
    pass


def _iter_jsonl(path: Path):
    with Path(path).open() as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)


def audit_coverage(
    pairs: list[tuple[str, str]],
    mappings_path: Path,
    labels_path: Path,
    partition_path: Path,
    manifest_path: Path,
    strict: bool = True,
) -> list[CoverageRow]:
    held_out = set(json.loads(Path(partition_path).read_text()).get("held_out", []))
    gold: dict[tuple[str, str], int] = defaultdict(int)
    for row in _iter_jsonl(mappings_path):
        if row.get("target_id_unresolved", True):
            continue
        if not row.get("target_node_id"):
            continue
        if row.get("provenance_sha") in held_out:
            continue
        gold[(row["source_framework"], row["target_framework"])] += 1

    silver: dict[tuple[str, str], int] = defaultdict(int)
    for row in _iter_jsonl(labels_path):
        if row.get("provenance_tag") != "llm_sme_v1":
            continue
        silver[(row["source_framework"], row["target_framework"])] += 1

    rows: list[CoverageRow] = []
    empties: list[tuple[str, str]] = []
    for src, tgt in pairs:
        r = CoverageRow(
            source_framework=src,
            target_framework=tgt,
            upstream_gold=gold.get((src, tgt), 0),
            llm_sme_silver=silver.get((src, tgt), 0),
        )
        rows.append(r)
        if r.empty:
            empties.append((src, tgt))

    manifest_path = Path(manifest_path)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(
            {"pairs": [r.model_dump() for r in rows]},
            sort_keys=True, indent=2,
        ) + "\n"
    )
    if empties:
        msg = f"{len(empties)} pair(s) have zero training signal: {empties}"
        if strict:
            raise CoverageError(msg)
        import sys
        print(f"WARNING: {msg}", file=sys.stderr)
    return rows
