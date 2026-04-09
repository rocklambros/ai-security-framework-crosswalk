from __future__ import annotations
import json
from pathlib import Path
from .schemas import GapTuple

DEFAULT_FROZEN_TUPLES = Path("data/splits/frozen_tuples.json")


def _train_eligible(row: dict, held_out: set[str]) -> bool:
    if row.get("target_id_unresolved", True):
        return False
    if row.get("target_node_id") in (None, ""):
        return False
    if row.get("provenance_sha") in held_out:
        return False
    return True


def _pair_key(row: dict) -> tuple[str, str, str, str]:
    tgt = row["target_node_id"]
    # target_node_id may be fully qualified ("mitre_atlas:AML.T0001") -- strip prefix
    if isinstance(tgt, str) and ":" in tgt:
        _, _, tgt = tgt.partition(":")
    return (
        row["source_framework"],
        row["source_id"],
        row["target_framework"],
        tgt,
    )


def _load_frozen_sets(frozen_path: Path) -> tuple[set[tuple[str, str]], set[tuple[str, str]], set[tuple[str, str, str, str]]]:
    if not frozen_path.exists():
        raise FileNotFoundError(
            f"frozen_tuples.json missing at {frozen_path} — run scripts/build_frozen_tuples.py. "
            "Gap selector REFUSES to run without the honesty firewall artifact."
        )
    data = json.loads(Path(frozen_path).read_text())
    src = {tuple(t) for t in data.get("source_tuples", [])}
    tgt = {tuple(t) for t in data.get("target_tuples", [])}
    pair = {tuple(t) for t in data.get("pair_tuples", [])}
    if not src and not tgt:
        raise RuntimeError("frozen_tuples.json is empty — refusing to run")
    return src, tgt, pair


def select_gap_tuples(
    pool_path: Path,
    mappings_path: Path,
    partition_path: Path,
    frozen_tuples_path: Path = DEFAULT_FROZEN_TUPLES,
) -> list[GapTuple]:
    # Layer 0: honesty firewall — load frozen tuple sets. REFUSES to run if missing.
    frozen_src, frozen_tgt, frozen_pair = _load_frozen_sets(Path(frozen_tuples_path))

    # Layer 1: upstream train-eligible coverage (gap = not covered)
    partition = json.loads(Path(partition_path).read_text())
    held_out: set[str] = set(partition.get("held_out", []))
    covered: set[tuple[str, str, str, str]] = set()
    with Path(mappings_path).open() as fh:
        for line in fh:
            if not line.strip():
                continue
            row = json.loads(line)
            if _train_eligible(row, held_out):
                covered.add(_pair_key(row))

    gaps: list[GapTuple] = []
    seen: set[tuple[str, str, str, str]] = set()
    with Path(pool_path).open() as fh:
        for line in fh:
            if not line.strip():
                continue
            row = json.loads(line)
            key = _pair_key(row)
            src_tup = (key[0], key[1])
            tgt_tup = (key[2], key[3])
            # Layer 0 firewall: reject if either endpoint OR the pair touches frozen test
            if src_tup in frozen_src:
                continue
            if tgt_tup in frozen_tgt:
                continue
            if key in frozen_pair:
                continue
            # Layer 1: skip upstream-covered + dedupe
            if key in covered or key in seen:
                continue
            seen.add(key)
            gaps.append(
                GapTuple(
                    source_framework=row["source_framework"],
                    source_id=row["source_id"],
                    target_framework=row["target_framework"],
                    target_node_id=row["target_node_id"],
                )
            )
    return gaps
