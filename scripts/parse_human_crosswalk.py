#!/usr/bin/env python3
"""Parse AIUC-1-Crosswalks-for-Rock.txt into graph-ready edge dicts.

Usage:
    python scripts/parse_human_crosswalk.py          # dry-run, print stats
    python scripts/parse_human_crosswalk.py --emit    # print JSON edges to stdout
"""
from __future__ import annotations

import csv
import json
import os
import re
import sys

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from scripts.build_graph import sanitize_local_id, normalize_atlas_id, normalize_nist_id

TSV_PATH = os.path.join(
    _PROJECT_ROOT, "data", "frameworks", "aiuc-1",
    "AIUC-1-Crosswalks-for-Rock.txt",
)

# Map TSV framework names to our registry keys
FW_MAP = {
    "CSA AICM": "csa_aicm",
    "NIST AI RMF": "nist_rmf",
    "OWASP Top 10 LLM": "owasp_llm",
    "MITRE ATLAS": "mitre_atlas",
    # ISO 42001: not in our registry -- skip
    # EU AI Act: deferred per user decision -- skip
}

# Regex to extract the control ID prefix before the colon or description
# Examples: "DSP-09: Data Protection..." -> "DSP-09"
#           "MEASURE 2.10: Privacy..." -> "MEASURE 2.10"
#           "AML.T0054: LLM Jailbreak" -> "AML.T0054"
_ID_RE = re.compile(r"^([A-Z][A-Z0-9._\-& ]+?):\s")

# OWASP IDs use "LLM06:25 - Excessive Agency" format (year suffix after colon)
_OWASP_ID_RE = re.compile(r"^(LLM\d+):\d+\s*-\s*")


def _extract_target_id(target_fw_key: str, raw_control: str) -> str | None:
    """Extract and normalize a target control ID from the TSV field."""
    raw = raw_control.strip()

    # OWASP has a special format: "LLM06:25 - Excessive Agency"
    if target_fw_key == "owasp_llm":
        m = _OWASP_ID_RE.match(raw)
        if m:
            return m.group(1)  # e.g. "LLM06"
        # Fall through to generic regex

    m = _ID_RE.match(raw)
    if not m:
        return None
    raw_id = m.group(1).strip()
    if target_fw_key == "mitre_atlas":
        return normalize_atlas_id(raw_id)
    if target_fw_key == "nist_rmf":
        return normalize_nist_id(raw_id)
    return sanitize_local_id(raw_id)


def parse_human_crosswalk() -> list[dict]:
    """Parse the TSV and return a list of edge-ready dicts.

    Each dict has: source_node_id, target_node_id, target_fw,
    requirement_text, target_description.
    """
    edges = []
    with open(TSV_PATH, "r", encoding="latin-1") as f:
        reader = csv.reader(f, delimiter="\t")
        header = next(reader)  # skip header
        for row in reader:
            if len(row) < 5:
                continue
            aiuc_ctrl = row[0].strip()        # e.g. "A001"
            requirement = row[1].strip()       # e.g. "Establish input data policy"
            target_fw_name = row[2].strip()    # e.g. "CSA AICM"
            target_ctrl_raw = row[3].strip()   # e.g. "DSP-09: Data Protection..."
            target_desc = row[4].strip()       # full description

            target_fw = FW_MAP.get(target_fw_name)
            if not target_fw:
                continue  # skip ISO 42001, EU AI Act, unknowns

            local_id = _extract_target_id(target_fw, target_ctrl_raw)
            if not local_id:
                continue

            source_nid = f"aiuc_1:{aiuc_ctrl}"
            target_nid = f"{target_fw}:{local_id}"

            edges.append({
                "source_node_id": source_nid,
                "target_node_id": target_nid,
                "target_fw": target_fw,
                "requirement_text": requirement,
                "target_description": target_desc,
            })
    return edges


def main():
    edges = parse_human_crosswalk()
    print(f"Parsed {len(edges)} edges from human review TSV")

    # Stats by target framework
    from collections import Counter
    fw_counts = Counter(e["target_fw"] for e in edges)
    for fw, n in fw_counts.most_common():
        print(f"  {fw}: {n}")

    # Unique source controls
    src = set(e["source_node_id"] for e in edges)
    print(f"Unique AIUC-1 source controls: {len(src)}")

    # Unique pairs
    pairs = set((e["source_node_id"], e["target_node_id"]) for e in edges)
    print(f"Unique (source, target) pairs: {len(pairs)}")

    if "--emit" in sys.argv:
        for e in edges:
            print(json.dumps(e))


if __name__ == "__main__":
    main()
