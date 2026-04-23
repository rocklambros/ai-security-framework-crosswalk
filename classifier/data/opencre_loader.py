"""Load OpenCRE expert-curated framework mappings as pairwise training signal.

Fetches all CREs from the live opencre.org REST API, extracts LinkedTo links
between standards (skipping AutomaticallyLinkedTo), and generates pairwise
framework pairs from standards that share a CRE.

Cache: data/opencre/opencre_all_cres.json
Output: data/opencre/opencre_pairs.jsonl

Usage (offline):
    python -m classifier.data.opencre_loader   # writes both output files
"""
from __future__ import annotations

import hashlib
import itertools
import json
import logging
import time
from pathlib import Path
from typing import Any, Iterator

import requests

from classifier.config import DATA_DIR

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
OPENCRE_DIR = DATA_DIR / "opencre"
CACHE_PATH = OPENCRE_DIR / "opencre_all_cres.json"
OUTPUT_PATH = OPENCRE_DIR / "opencre_pairs.jsonl"

# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------
API_BASE = "https://opencre.org/rest/v1"
PAGE_SIZE = 50
REQUEST_DELAY = 0.25  # seconds between requests to be polite

# ---------------------------------------------------------------------------
# Gap penalties by link type
# ---------------------------------------------------------------------------
GAP_PENALTIES: dict[str, int] = {
    "LinkedTo": 0,
    "Linked To": 0,
    "AutomaticallyLinkedTo": 0,  # skipped during extraction but included for completeness
    "Contains": 1,
    "Is Part Of": 2,
    "Related": 2,
}

# ---------------------------------------------------------------------------
# Framework name -> canonical key mapping
# ---------------------------------------------------------------------------
FRAMEWORK_TABLE: dict[str, str] = {
    # AI / ML frameworks
    "MITRE ATLAS": "mitre_atlas",
    "MITRE-ATLAS": "mitre_atlas",
    "OWASP AI Exchange": "owasp_ai_exchange",
    "OWASP AI Security and Privacy Guide": "owasp_ai_exchange",
    "NIST AI RMF": "nist_rmf",
    "NIST AI RMF 1.0": "nist_rmf",
    "NIST AI 100-1": "nist_ai_100_1",
    "NIST Artificial Intelligence": "nist_ai_100_1",
    "ENISA Multilayer Framework": "enisa_mlf",
    "ENISA": "enisa",
    "ETSI": "etsi",
    # Traditional / cross-cutting frameworks
    "ASVS": "owasp_asvs",
    "OWASP ASVS": "owasp_asvs",
    "OWASP ASVS 4.0.3": "owasp_asvs",
    "NIST 800-53": "nist_800_53",
    "NIST SP 800-53": "nist_800_53",
    "NIST SP 800-53 Rev 5": "nist_800_53",
    "CWE": "cwe",
    "ISO 27001": "iso_27001",
    "ISO/IEC 27001": "iso_27001",
    "ISO/IEC 27001:2022": "iso_27001",
    "PCI DSS": "pci_dss",
    "PCI DSS v4.0": "pci_dss",
    "WSTG": "owasp_wstg",
    "OWASP WSTG": "owasp_wstg",
    "OWASP Proactive Controls": "owasp_proactive_controls",
    "OWASP Cheat Sheets": "owasp_cheat_sheets",
    "Cloud Controls Matrix": "csa_ccm",
    "CCM": "csa_ccm",
    "OWASP SAMM": "owasp_samm",
    "OWASP SAMM v2.0": "owasp_samm",
    "SSDF": "nist_ssdf",
    "NIST SP 800-218": "nist_ssdf",
    "OWASP Top 10 2021": "owasp_top10_2021",
    "OWASP Top 10 2017": "owasp_top10_2017",
    "CAPEC": "capec",
    "NIST SP 800-63": "nist_800_63",
}

# ---------------------------------------------------------------------------
# Framework classification
# ---------------------------------------------------------------------------
_AI_KEYWORDS = [
    "atlas",
    "ai exchange",
    "llm",
    "machine learning",
    "biml",
    "ai 100",
    "ai rmf",
    "enisa",
    "etsi",
    "artificial intelligence",
    "top10 for ml",
    "top10 for llm",
]

_TRADITIONAL_KEYWORDS = [
    "asvs",
    "800-53",
    "cwe",
    "27001",
    "pci dss",
    "wstg",
    "proactive controls",
    "cheat sheet",
    "ccm",
    "samm",
    "ssdf",
    "top 10 2021",
    "top 10 2017",
    "capec",
    "800-63",
]


def classify_framework(framework_name: str) -> str:
    """Classify a framework name as 'ai_security', 'traditional', or 'other'.

    Parameters
    ----------
    framework_name:
        Raw framework name string from OpenCRE.

    Returns
    -------
    'ai_security' | 'traditional' | 'other'
    """
    lower = framework_name.lower()
    for kw in _AI_KEYWORDS:
        if kw in lower:
            return "ai_security"
    for kw in _TRADITIONAL_KEYWORDS:
        if kw in lower:
            return "traditional"
    return "other"


# ---------------------------------------------------------------------------
# Provenance
# ---------------------------------------------------------------------------

def _provenance_sha(cre_id: str, src_node_id: str, tgt_node_id: str) -> str:
    """SHA-256 of 'opencre|{cre_id}|{src_id}|{tgt_id}' (canonical order)."""
    a, b = sorted([src_node_id, tgt_node_id])
    raw = f"opencre|{cre_id}|{a}|{b}"
    return hashlib.sha256(raw.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Node ID helpers
# ---------------------------------------------------------------------------

def _make_node_id(framework_key: str, section: str | None, name: str | None) -> str:
    """Build a stable node_id string from framework + section/name."""
    label = (section or name or "").strip().replace(" ", "_")
    return f"{framework_key}:{label}" if label else framework_key


def _canonical_framework_key(raw_name: str) -> str:
    """Return the canonical framework key for *raw_name*, falling back to a slug."""
    if raw_name in FRAMEWORK_TABLE:
        return FRAMEWORK_TABLE[raw_name]
    # Attempt a case-insensitive lookup
    lower = raw_name.lower()
    for k, v in FRAMEWORK_TABLE.items():
        if k.lower() == lower:
            return v
    # Fallback: make a slug from the raw name
    return raw_name.lower().replace(" ", "_").replace("/", "_").replace("-", "_")


# ---------------------------------------------------------------------------
# Pair extraction from a single CRE
# ---------------------------------------------------------------------------

def extract_pairs_from_cre(cre: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract pairwise standard links from a single CRE dict.

    Rules:
    - Only 'LinkedTo' / 'Linked To' links are used (human-curated).
    - 'AutomaticallyLinkedTo' links are skipped.
    - All pairs of standards sharing the CRE are generated (combinations of 2).
    - Canonical ordering (alphabetical by node_id) is used for dedup.

    Parameters
    ----------
    cre:
        A CRE dict from the OpenCRE API (single CRE with 'links' key).

    Returns
    -------
    List of pair dicts; may be empty if fewer than 2 standards qualify.
    """
    cre_id: str = str(cre.get("id", cre.get("doctype", "")))
    cre_name: str = cre.get("name", "")

    # Collect qualifying standard nodes
    standards: list[dict[str, Any]] = []
    for link in cre.get("links", []):
        ltype = link.get("ltype", "")
        # Skip automatically-generated links
        if ltype in ("AutomaticallyLinkedTo", "Automatically Linked To"):
            continue
        # Only include LinkedTo human-curated links
        if ltype not in ("LinkedTo", "Linked To"):
            continue

        node = link.get("document", {})
        if node.get("doctype", "").lower() != "standard":
            continue

        raw_fw = node.get("name", "")
        section = node.get("section") or node.get("sectionID") or node.get("hyperlink")
        display_name = node.get("section") or node.get("name") or ""
        fw_key = _canonical_framework_key(raw_fw)
        node_id = _make_node_id(fw_key, node.get("sectionID") or node.get("section"), raw_fw)

        gap = GAP_PENALTIES.get(ltype, 0)

        standards.append({
            "node_id": node_id,
            "text": display_name,
            "framework": fw_key,
            "raw_framework": raw_fw,
            "gap_penalty": gap,
        })

    if len(standards) < 2:
        return []

    pairs: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()

    for a, b in itertools.combinations(standards, 2):
        # Skip self-pairs (identical node IDs from duplicate links)
        if a["node_id"] == b["node_id"]:
            continue

        # Canonical ordering
        src, tgt = (a, b) if a["node_id"] <= b["node_id"] else (b, a)

        key = (src["node_id"], tgt["node_id"])
        if key in seen:
            continue
        seen.add(key)

        fw_class_a = classify_framework(src["raw_framework"])
        fw_class_b = classify_framework(tgt["raw_framework"])
        psha = _provenance_sha(cre_id, src["node_id"], tgt["node_id"])

        pairs.append(
            build_pair_row(
                source_node_id=src["node_id"],
                target_node_id=tgt["node_id"],
                source_text=src["text"],
                target_text=tgt["text"],
                source_framework=src["framework"],
                target_framework=tgt["framework"],
                cre_id=cre_id,
                cre_name=cre_name,
                gap_penalty=max(src["gap_penalty"], tgt["gap_penalty"]),
                fw_class_a=fw_class_a,
                fw_class_b=fw_class_b,
                provenance="opencre",
                provenance_sha=psha,
            )
        )

    return pairs


# ---------------------------------------------------------------------------
# Pair row schema
# ---------------------------------------------------------------------------

def build_pair_row(
    *,
    source_node_id: str,
    target_node_id: str,
    source_text: str,
    target_text: str,
    source_framework: str,
    target_framework: str,
    cre_id: str,
    cre_name: str,
    gap_penalty: int,
    fw_class_a: str,
    fw_class_b: str,
    provenance: str,
    provenance_sha: str,
) -> dict[str, Any]:
    """Build a canonical pair row dict with the required schema."""
    return {
        "source_node_id": source_node_id,
        "target_node_id": target_node_id,
        "source_text": source_text,
        "target_text": target_text,
        "source_framework": source_framework,
        "target_framework": target_framework,
        "cre_id": cre_id,
        "cre_name": cre_name,
        "gap_penalty": gap_penalty,
        "fw_class_a": fw_class_a,
        "fw_class_b": fw_class_b,
        "provenance": provenance,
        "provenance_sha": provenance_sha,
    }


# ---------------------------------------------------------------------------
# API fetch helpers
# ---------------------------------------------------------------------------

def _fetch_all_cres(session: requests.Session, use_cache: bool = True) -> list[dict[str, Any]]:
    """Fetch all CREs from the API, using disk cache when available.

    Parameters
    ----------
    session:
        Requests session to use.
    use_cache:
        If True and the cache file exists, load from disk without hitting the API.

    Returns
    -------
    List of CRE dicts.
    """
    if use_cache and CACHE_PATH.exists():
        logger.info("Loading CREs from cache: %s", CACHE_PATH)
        return json.loads(CACHE_PATH.read_text())

    logger.info("Fetching all CREs from %s …", API_BASE)
    cres: list[dict[str, Any]] = []

    # Paginate through /rest/v1/all endpoint
    page = 0
    while True:
        url = f"{API_BASE}/all"
        params: dict[str, Any] = {"page": page, "per_page": PAGE_SIZE}
        resp = session.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        # The API may return a dict with 'data' key or a list directly
        items: list[dict] = []
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            items = data.get("data", data.get("cres", []))

        if not items:
            break

        cres.extend(items)
        logger.info("  page %d: %d CREs (total so far: %d)", page, len(items), len(cres))

        if len(items) < PAGE_SIZE:
            break

        page += 1
        time.sleep(REQUEST_DELAY)

    # Persist cache
    OPENCRE_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(cres, indent=2))
    logger.info("Cached %d CREs to %s", len(cres), CACHE_PATH)
    return cres


def _fetch_cre_detail(session: requests.Session, cre_id: str) -> dict[str, Any] | None:
    """Fetch a single CRE by ID to obtain its full link list."""
    url = f"{API_BASE}/id/{cre_id}"
    try:
        resp = session.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, dict):
            return data.get("data", data)
        return None
    except requests.RequestException as exc:
        logger.warning("Failed to fetch CRE %s: %s", cre_id, exc)
        return None


# ---------------------------------------------------------------------------
# Main extraction pipeline
# ---------------------------------------------------------------------------

def run_extraction(use_cache: bool = True) -> list[dict[str, Any]]:
    """Fetch all CREs, extract pairs, write JSONL.

    Parameters
    ----------
    use_cache:
        Use the disk cache for the raw API results if it exists.

    Returns
    -------
    All generated pair dicts.
    """
    OPENCRE_DIR.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers["User-Agent"] = "opencre-loader/1.0 (ai-security-framework-crosswalk)"

    cres = _fetch_all_cres(session, use_cache=use_cache)
    logger.info("Processing %d CREs …", len(cres))

    all_pairs: list[dict[str, Any]] = []
    seen_shas: set[str] = set()

    for cre in cres:
        pairs = extract_pairs_from_cre(cre)
        for p in pairs:
            sha = p["provenance_sha"]
            if sha not in seen_shas:
                seen_shas.add(sha)
                all_pairs.append(p)

    logger.info("Writing %d pairs to %s", len(all_pairs), OUTPUT_PATH)
    with OUTPUT_PATH.open("w") as fh:
        for pair in all_pairs:
            fh.write(json.dumps(pair) + "\n")

    return all_pairs


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    pairs = run_extraction(use_cache=True)
    print(f"Done — {len(pairs)} pairs written to {OUTPUT_PATH}")
