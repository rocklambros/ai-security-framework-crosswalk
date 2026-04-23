"""Extract OpenCRE expert edges for Project 2 visualization.

Reads from the cached OpenCRE data (data/opencre/opencre_all_cres.json)
and produces edges compatible with the Project 2 edge schema.
"""
from __future__ import annotations

import json
from collections import defaultdict
from itertools import combinations
from pathlib import Path

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


def extract_opencre_edges() -> list[dict]:
    """Extract edges from OpenCRE data for Project 2."""
    if not CACHE_FILE.exists():
        print(f"Cache not found at {CACHE_FILE}. Run classifier.data.opencre_loader first.")
        return []

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

            edges.append({
                "source_node_id": src,
                "target_node_id": tgt,
                "source_framework": a["framework"] if a["node_id"] == src else b["framework"],
                "target_framework": b["framework"] if b["node_id"] == tgt else a["framework"],
                "confidence": "expert",
                "rationale": "OPENCRE_EXPERT",
                "provenance": "opencre_expert",
                "cre_id": cre_id,
                "cre_name": cre_name,
                "notes": f"Expert-validated via CRE {cre_id}: {cre_name}",
            })

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(edges, f, indent=2)

    print(f"Extracted {len(edges)} OpenCRE expert edges -> {OUTPUT_FILE}")

    fw_pairs = defaultdict(int)
    for e in edges:
        key = tuple(sorted([e["source_framework"], e["target_framework"]]))
        fw_pairs[key] += 1
    print(f"\nFramework pair coverage:")
    for (a, b), count in sorted(fw_pairs.items(), key=lambda x: -x[1]):
        print(f"  {a} <-> {b}: {count}")

    return edges


if __name__ == "__main__":
    extract_opencre_edges()
