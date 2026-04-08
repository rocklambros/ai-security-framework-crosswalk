"""NIST SP 800-53 rev5 OSCAL JSON catalog → node list ingester.

OSCAL structure (simplified):
  catalog
    groups[]
      groups[]              (optional sub-groups)
      controls[]
        id          e.g. "ac-1"
        title       e.g. "Policy and Procedures"
        parts[]     prose statements
        controls[]  enhancements (optional)

We emit one node per control AND one node per enhancement.
"""
from __future__ import annotations
import json
from pathlib import Path


def _extract_text(parts: list[dict]) -> str:
    chunks: list[str] = []
    for part in parts or []:
        if "prose" in part and part["prose"]:
            chunks.append(part["prose"])
        if "parts" in part:
            chunks.append(_extract_text(part["parts"]))
    return "\n".join(c for c in chunks if c).strip()


def _walk(group: dict, out: list[dict]) -> None:
    for ctrl in group.get("controls", []) or []:
        _emit(ctrl, out)
    for sub in group.get("groups", []) or []:
        _walk(sub, out)


def _emit(ctrl: dict, out: list[dict]) -> None:
    local_id = ctrl["id"].upper()
    title = ctrl.get("title", "")
    text = _extract_text(ctrl.get("parts", []))
    out.append({
        "node_id": f"nist_800_53:{local_id}",
        "local_id": local_id,
        "framework": "nist_800_53",
        "title": title,
        "text": text or title,
    })
    for enh in ctrl.get("controls", []) or []:
        _emit(enh, out)


def ingest_nist_800_53(catalog_path: Path) -> list[dict]:
    raw = json.loads(Path(catalog_path).read_text())
    catalog = raw.get("catalog", raw)
    out: list[dict] = []
    for group in catalog.get("groups", []) or []:
        _walk(group, out)
    return out
