"""Extract OpenCRE expert edges for Project 2 visualization.

Primary source: data/opencre/opencre_pairs.jsonl (v8b hierarchy pairs with
gap_penalty levels 0/1/2).  Falls back to the legacy CRE JSON cache at
data/opencre/opencre_all_cres.json for combinatorial extraction.
"""
from __future__ import annotations

import json
from collections import defaultdict
from itertools import combinations
from pathlib import Path

PAIRS_FILE = Path("data/opencre/opencre_pairs.jsonl")
CACHE_FILE = Path("data/opencre/opencre_all_cres.json")
OUTPUT_FILE = Path("project2/data/opencre_edges.json")

# Map OpenCRE framework names to our canonical keys
FRAMEWORK_MAP = {
    "MITRE ATLAS": "mitre_atlas",
    "OWASP AI Exchange": "owasp_ai_exchange",
    "NIST AI RMF": "nist_rmf",
    "OWASP Top 10 for Large Language Model Applications": "owasp_llm",
    "Cloud Controls Matrix": "csa_aicm",
    "ASVS": "owasp_asvs",
    "OWASP Application Security Verification Standard (ASVS)": "owasp_asvs",
    "CWE": "cwe",
    "NIST 800-53": "nist_800_53",
    "NIST SP 800-53 v5": "nist_800_53",
    "OWASP Top 10 2021": "owasp_top10",
    "OWASP Proactive Controls": "owasp_proactive",
    "OWASP Cheat Sheets": "owasp_cheatsheets",
    "ISO 27001": "iso_27001",
    "PCI DSS": "pci_dss",
    "SAMM": "owasp_samm",
    "CAPEC": "capec",
}

# Frameworks we want in Project 2 (9 AI + 4 traditional anchors)
TARGET_FRAMEWORKS = {
    "aiuc_1", "csa_aicm", "mitre_atlas", "owasp_ai_exchange",
    "nist_rmf", "eu_gpai_cop", "cosai_rm", "owasp_llm", "owasp_agentic",
    "nist_800_53", "cwe", "owasp_asvs", "owasp_top10",
}


def _gap_to_tier(gap: int) -> dict:
    """Map gap_penalty to confidence/rationale metadata.

    gap=0  -> EQUIVALENT (tier 3)
    gap=1  -> RELATED    (tier 2)
    gap>=2 -> PARTIAL    (tier 1)
    Never produces UNRELATED (tier 0).
    """
    if gap == 0:
        return {"confidence": "expert", "rationale_code": "OPENCRE_EQUIVALENT",
                "rationale_label": "Same CRE node (equivalent)", "tier": 3}
    elif gap == 1:
        return {"confidence": "expert", "rationale_code": "OPENCRE_RELATED",
                "rationale_label": "Adjacent CRE nodes (related)", "tier": 2}
    else:
        return {"confidence": "suggestive", "rationale_code": "OPENCRE_PARTIAL",
                "rationale_label": "Distant CRE nodes (partial)", "tier": 1}


def extract_opencre_edges() -> list[dict]:
    """Extract edges from OpenCRE data for Project 2.

    Prefers the v8b hierarchy pairs JSONL (with gap_penalty) over the legacy
    combinatorial extraction from the full CRE cache.
    """
    if PAIRS_FILE.exists():
        return _extract_from_pairs()
    elif CACHE_FILE.exists():
        return _extract_from_cre_cache()
    else:
        print(f"No OpenCRE data found at {PAIRS_FILE} or {CACHE_FILE}.")
        print("Run classifier.data.opencre_loader or build_v8_training first.")
        return []


def _extract_from_pairs() -> list[dict]:
    """Extract edges from v8b hierarchy pairs JSONL with gap_penalty levels."""
    edges = []
    seen = set()
    by_gap = {0: 0, 1: 0, 2: 0}

    with open(PAIRS_FILE) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)

            src = rec["source_node_id"]
            tgt = rec["target_node_id"]
            src_fw = rec["source_framework"]
            tgt_fw = rec["target_framework"]

            # Only include cross-framework pairs for our target frameworks
            if src_fw not in TARGET_FRAMEWORKS or tgt_fw not in TARGET_FRAMEWORKS:
                continue
            if src_fw == tgt_fw:
                continue

            edge_key = tuple(sorted([src, tgt]))
            if edge_key in seen:
                continue
            seen.add(edge_key)

            gap = rec.get("gap_penalty", 0)
            tier_info = _gap_to_tier(gap)

            edges.append({
                "source_node_id": src,
                "target_node_id": tgt,
                "source_framework": src_fw,
                "target_framework": tgt_fw,
                "confidence": tier_info["confidence"],
                "rationale_code": tier_info["rationale_code"],
                "rationale_label": tier_info["rationale_label"],
                "provenance": "opencre_hierarchy",
                "gap_penalty": gap,
                "cre_id": rec.get("cre_id", ""),
                "cre_name": rec.get("cre_name", ""),
                "notes": f"OpenCRE hierarchy (gap={gap}, tier={tier_info['tier']})",
            })
            by_gap[min(gap, 2)] = by_gap.get(min(gap, 2), 0) + 1

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(edges, f, indent=2)

    print(f"Extracted {len(edges)} OpenCRE hierarchy edges -> {OUTPUT_FILE}")
    print(f"  gap=0 EQUIVALENT: {by_gap.get(0, 0)}, "
          f"gap=1 RELATED: {by_gap.get(1, 0)}, "
          f"gap>=2 PARTIAL: {by_gap.get(2, 0)}")

    _print_fw_coverage(edges)
    return edges


def _extract_from_cre_cache() -> list[dict]:
    """Legacy extraction: combinatorial pairs from CRE cache (no gap_penalty)."""
    cres = json.loads(CACHE_FILE.read_text())
    edges = []
    seen = set()

    for cre in cres:
        cre_id = cre.get("id", "?")
        cre_name = cre.get("name", "?")

        std_links = []
        for link in cre.get("links", []):
            doc = link.get("document", {})
            ltype = link.get("ltype", "")
            if doc.get("doctype") == "CRE":
                continue
            if "automat" in ltype.lower():
                continue
            fw_name = doc.get("name", "")
            canonical = FRAMEWORK_MAP.get(fw_name)
            if canonical and canonical in TARGET_FRAMEWORKS:
                section_id = doc.get("sectionID", doc.get("section", ""))
                node_id = f"{canonical}:{section_id}"
                std_links.append({
                    "node_id": node_id,
                    "framework": canonical,
                    "section_id": section_id,
                    "section_name": doc.get("section", ""),
                    "link_type": ltype,
                })

        for a, b in combinations(std_links, 2):
            src, tgt = sorted([a["node_id"], b["node_id"]])
            edge_key = (src, tgt)
            if edge_key in seen:
                continue
            seen.add(edge_key)

            # Legacy: all pairs from same CRE are gap=0 (equivalent)
            edges.append({
                "source_node_id": src,
                "target_node_id": tgt,
                "source_framework": a["framework"] if a["node_id"] == src else b["framework"],
                "target_framework": b["framework"] if b["node_id"] == tgt else a["framework"],
                "confidence": "expert",
                "rationale_code": "OPENCRE_EQUIVALENT",
                "rationale_label": "Same CRE node (equivalent)",
                "provenance": "opencre_hierarchy",
                "gap_penalty": 0,
                "cre_id": cre_id,
                "cre_name": cre_name,
                "notes": f"Expert-validated via CRE {cre_id}: {cre_name}",
            })

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(edges, f, indent=2)

    print(f"Extracted {len(edges)} OpenCRE expert edges (legacy) -> {OUTPUT_FILE}")
    _print_fw_coverage(edges)
    return edges


def _print_fw_coverage(edges: list[dict]) -> None:
    """Print framework pair coverage summary."""
    fw_pairs = defaultdict(int)
    for e in edges:
        key = tuple(sorted([e["source_framework"], e["target_framework"]]))
        fw_pairs[key] += 1
    print(f"\nFramework pair coverage:")
    for (a, b), count in sorted(fw_pairs.items(), key=lambda x: -x[1]):
        print(f"  {a} <-> {b}: {count}")


if __name__ == "__main__":
    extract_opencre_edges()
