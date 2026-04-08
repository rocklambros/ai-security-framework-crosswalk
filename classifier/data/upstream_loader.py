"""Flatten upstream GenAI-Data-Security-Initiative crosswalk entries
into row-oriented mappings and crossrefs JSONL.

Spec: docs/superpowers/specs/2026-04-08-upstream-crosswalk-integration-design.md §4.3
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

SOURCE_LIST_TO_FRAMEWORK: dict[str, str] = {
    "LLM-Top10-2025": "owasp_llm",
    "Agentic-Top10-2026": "owasp_agentic",
    "DSGAI-2026": "owasp_dsgai",
}

TARGET_FRAMEWORK_TABLE: dict[str, str] = {
    "MITRE ATLAS": "mitre_atlas",
    "MITRE-ATLAS": "mitre_atlas",
    "NIST AI RMF 1.0": "nist_rmf",
    "NIST AI RMF": "nist_rmf",
    "NIST-AI-RMF": "nist_rmf",
    "AIUC-1": "aiuc_1",
    "CSA AICM": "csa_aicm",
    "CSA-AICM": "csa_aicm",
    "MAESTRO": "csa_aicm",
    "OWASP AI Exchange": "owasp_ai_exchange",
    "OWASP-AI-Exchange": "owasp_ai_exchange",
    "EU GPAI Code of Practice": "eu_gpai_cop",
    "CoSAI": "cosai_rm",
    "COSAI": "cosai_rm",
    "NIST SP 800-53": "nist_800_53",
    "NIST SP 800-53 Rev 5": "nist_800_53",
    "NIST-800-53": "nist_800_53",
    "EU AI Act": "eu_ai_act",
    "EU-AI-Act": "eu_ai_act",
}


def _provenance_sha(upstream_commit_sha: str, entry_id: str, mapping_index: int) -> str:
    h = hashlib.sha256()
    h.update(upstream_commit_sha.encode())
    h.update(b"|")
    h.update(entry_id.encode())
    h.update(b"|")
    h.update(str(mapping_index).encode())
    return h.hexdigest()


def flatten_entry(entry: dict, upstream_commit_sha: str) -> list[dict]:
    src_list = entry.get("source_list", "")
    src_framework = SOURCE_LIST_TO_FRAMEWORK.get(src_list)
    if src_framework is None:
        raise ValueError(
            f"unknown source_list {src_list!r} in entry {entry.get('id')}; "
            f"extend SOURCE_LIST_TO_FRAMEWORK"
        )
    src_id = entry["id"]

    rows: list[dict] = []
    for idx, m in enumerate(entry.get("mappings", [])):
        upstream_target = (m.get("framework") or "").strip()
        target_framework = TARGET_FRAMEWORK_TABLE.get(upstream_target)
        rows.append({
            "source_framework": src_framework,
            "source_id": src_id,
            "source_list": src_list,
            "target_framework": target_framework or upstream_target,
            "target_framework_unknown": target_framework is None,
            "target_control_id": m.get("control_id"),
            "target_control_name": m.get("control_name"),
            "tier": m.get("tier"),
            "scope": m.get("scope"),
            "url": m.get("url"),
            "notes": m.get("notes"),
            "provenance_sha": _provenance_sha(upstream_commit_sha, src_id, idx),
        })
    return rows


def flatten_crossrefs(entry: dict, upstream_commit_sha: str) -> list[dict]:
    src_list = entry.get("source_list", "")
    src_framework = SOURCE_LIST_TO_FRAMEWORK.get(src_list, "")
    src_id = entry["id"]
    cx = entry.get("crossrefs", {}) or {}
    out: list[dict] = []
    for target_list, target_ids in cx.items():
        target_framework = {
            "agentic_top10": "owasp_agentic",
            "llm_top10": "owasp_llm",
            "dsgai_2026": "owasp_dsgai",
        }.get(target_list, target_list)
        for idx, t_id in enumerate(target_ids or []):
            out.append({
                "source_framework": src_framework,
                "source_id": src_id,
                "target_framework": target_framework,
                "target_id": t_id,
                "provenance_sha": _provenance_sha(
                    upstream_commit_sha, f"{src_id}::xref::{target_list}", idx
                ),
            })
    return out


def load_all_entries(entries_dir: Path, upstream_commit_sha: str) -> list[dict]:
    rows: list[dict] = []
    for p in sorted(Path(entries_dir).glob("*.json")):
        entry = json.loads(p.read_text())
        rows.extend(flatten_entry(entry, upstream_commit_sha))
    return rows


def load_all_crossrefs(entries_dir: Path, upstream_commit_sha: str) -> list[dict]:
    rows: list[dict] = []
    for p in sorted(Path(entries_dir).glob("*.json")):
        entry = json.loads(p.read_text())
        rows.extend(flatten_crossrefs(entry, upstream_commit_sha))
    return rows
