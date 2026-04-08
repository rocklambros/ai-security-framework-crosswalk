"""Strict source-id-level contamination partition for upstream labels.

Spec: docs/superpowers/specs/2026-04-08-upstream-crosswalk-integration-design.md §4.4

Partition rules (strict):
  Rule 1: If a (source_framework, source_id) tuple appears anywhere in the
          frozen test, ALL upstream rows with that tuple are held_out.
  Rule 2: Additionally, any upstream row whose full
          (source_framework, source_id, target_framework, target_id) 4-tuple
          exactly matches a frozen-test row is held_out regardless of Rule 1.
"""
from __future__ import annotations
import json
from pathlib import Path

import pandas as pd


def compute_partition(
    frozen_test_path: Path,
    upstream_mappings_path: Path,
) -> dict:
    frozen = pd.read_json(frozen_test_path, lines=True)

    def split_node_id(nid: str) -> tuple[str, str]:
        if ":" in nid:
            fw, local = nid.split(":", 1)
            return fw, local
        return "", nid

    frozen_src_tuples: set[tuple[str, str]] = set()
    frozen_full_tuples: set[tuple[str, str, str, str]] = set()
    for _, row in frozen.iterrows():
        src_fw, src_id = split_node_id(row["source_node_id"])
        tgt_fw, tgt_id = split_node_id(row["target_node_id"])
        frozen_src_tuples.add((src_fw, src_id))
        frozen_src_tuples.add((tgt_fw, tgt_id))  # both sides — see spec §4.4
        frozen_full_tuples.add((src_fw, src_id, tgt_fw, tgt_id))

    upstream_rows: list[dict] = []
    with open(upstream_mappings_path) as f:
        for line in f:
            upstream_rows.append(json.loads(line))

    held_out: list[str] = []
    train_eligible: list[str] = []
    rule1_hits = 0
    rule2_hits = 0

    for r in upstream_rows:
        src_tuple = (r["source_framework"], r["source_id"])
        # Rule 2 uses the canonicalized target_node_id so the firewall actually
        # matches against the frozen test's (src_fw, src_id, tgt_fw, tgt_local)
        # tuples. Rows with target_id_unresolved=True cannot evaluate Rule 2
        # and fall through to Rule 1 only.
        tgt_node_id = r.get("target_node_id")
        tgt_local = tgt_node_id.split(":", 1)[1] if tgt_node_id and ":" in tgt_node_id else ""
        full_tuple = (
            r["source_framework"],
            r["source_id"],
            r["target_framework"],
            tgt_local,
        )
        rule1 = src_tuple in frozen_src_tuples
        rule2 = bool(tgt_local) and full_tuple in frozen_full_tuples
        if rule1:
            rule1_hits += 1
        if rule2:
            rule2_hits += 1
        if rule1 or rule2:
            held_out.append(r["provenance_sha"])
        else:
            train_eligible.append(r["provenance_sha"])

    return {
        "upstream_total": len(upstream_rows),
        "train_eligible_count": len(train_eligible),
        "held_out_count": len(held_out),
        "rule1_hits": rule1_hits,
        "rule2_hits": rule2_hits,
        "frozen_src_tuples_count": len(frozen_src_tuples),
        "frozen_full_tuples_count": len(frozen_full_tuples),
        "train_eligible": train_eligible,
        "held_out": held_out,
    }


def write_partition_and_report(
    partition: dict,
    partition_path: Path,
    report_path: Path,
) -> None:
    partition_path.write_text(json.dumps(partition, indent=2))

    summary = {k: v for k, v in partition.items() if k not in ("train_eligible", "held_out")}
    summary["held_out_pct"] = (
        partition["held_out_count"] / partition["upstream_total"] if partition["upstream_total"] else 0.0
    )
    summary["projection"] = (
        "Strict partitioning per spec §4.4. Held-out rows are reserved for the "
        "upstream benchmark (spec §6) and MUST NOT enter training batches."
    )
    report_path.write_text(json.dumps(summary, indent=2))
