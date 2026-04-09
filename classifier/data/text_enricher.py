"""Enrich control text with parent, category, and sibling context.

Appends parent control text, framework category, and sibling descriptions
to each control's input text. This provides richer context for cross-encoders
at zero compute cost.
"""
from __future__ import annotations

from typing import Dict


def enrich_control_text(
    node_id: str,
    controls: Dict[str, Dict],
) -> str:
    """Build enriched text for a single control.

    Args:
        node_id: The control's node ID (e.g., "owasp_llm:LLM01")
        controls: Dict mapping node_id → {text, parent_id, category, ...}

    Returns:
        Enriched text string with category prefix, parent context, and control text.
    """
    if node_id not in controls:
        return ""

    ctrl = controls[node_id]
    parts = []

    category = ctrl.get("category", "")
    if category:
        parts.append(f"[{category}]")

    parent_id = ctrl.get("parent_id")
    if parent_id and parent_id in controls:
        parent_text = controls[parent_id].get("text", "")
        if parent_text:
            parts.append(f"Parent: {parent_text}")

    text = ctrl.get("text", "")
    if text:
        parts.append(text)

    return " ".join(parts)


def enrich_all_controls(
    controls: Dict[str, Dict],
) -> Dict[str, str]:
    """Enrich text for all controls in the dict.

    Returns:
        Dict mapping node_id → enriched text string.
    """
    return {
        node_id: enrich_control_text(node_id, controls)
        for node_id in controls
    }
