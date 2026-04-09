"""Control text enrichment for improved retrieval and classification.

Provides:
    enrich_control_text()  — enrich a single control's text representation
    enrich_all_controls()  — batch-enrich a collection of controls
"""
from __future__ import annotations

from typing import Any, Dict, List


def enrich_control_text(
    node_id: str,
    text: str,
    *,
    framework: str = "",
    extra_fields: Dict[str, Any] | None = None,
) -> str:
    """Return an enriched text string for a control node.

    Concatenates available metadata fields into a single string
    suitable for embedding or BM25 indexing.

    Parameters
    ----------
    node_id:
        The node identifier (e.g. ``mitre_atlas:AML.T0001``).
    text:
        Primary text (name/title/description).
    framework:
        Framework name, prepended as a context prefix.
    extra_fields:
        Additional metadata dict; string-valued fields are appended.

    Returns
    -------
    Enriched text string.
    """
    parts: List[str] = []
    if framework:
        parts.append(framework)
    if text:
        parts.append(text)
    if extra_fields:
        for v in extra_fields.values():
            if isinstance(v, str) and v:
                parts.append(v)
    return " | ".join(parts)


def enrich_all_controls(
    controls: List[Dict[str, Any]],
    *,
    id_field: str = "node_id",
    text_field: str = "text",
    framework_field: str = "framework",
) -> Dict[str, str]:
    """Enrich a list of control dicts, returning a node_id → enriched_text mapping.

    Parameters
    ----------
    controls:
        List of control dicts (each must contain ``id_field`` and ``text_field``).
    id_field:
        Key in each dict used as the node identifier.
    text_field:
        Key in each dict used as the primary text.
    framework_field:
        Key in each dict used as the framework name.

    Returns
    -------
    Dict mapping node_id to enriched text.
    """
    result: Dict[str, str] = {}
    for ctrl in controls:
        nid = ctrl.get(id_field, "")
        if not nid:
            continue
        text = ctrl.get(text_field, "") or ctrl.get("description", "")
        framework = ctrl.get(framework_field, "")
        extra = {k: v for k, v in ctrl.items() if k not in (id_field, text_field, framework_field)}
        result[nid] = enrich_control_text(nid, text, framework=framework, extra_fields=extra)
    return result
