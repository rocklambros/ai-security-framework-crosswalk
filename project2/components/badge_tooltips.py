"""Centralized tooltip registry and helper for all badges/tags in the Dash app."""

import uuid

import dash_bootstrap_components as dbc
from dash import html

# ---------------------------------------------------------------------------
# Tooltip text registry
# ---------------------------------------------------------------------------

BADGE_TOOLTIPS = {
    # Confidence levels
    "authoritative": "Authoritative: Mapping derived from official framework source documents with explicit cross-references.",
    "expert": "Expert: Mapping validated by domain experts through structured review.",
    "suggestive": "Suggestive: Mapping inferred from shared categories or semantic similarity. Lower confidence.",
    "unvalidated": "Unvalidated: Mapping not yet reviewed. Use with caution.",

    # Rationale codes
    "SCOPE": "SCOPE: The source control defines the operational boundary for the target control.",
    "DETECT": "DETECT: The source control addresses detection capabilities referenced by the target.",
    "GOVERN": "GOVERN: The source control provides governance structure for the target.",
    "ISOLATE": "ISOLATE: The source control addresses isolation or containment referenced by the target.",
    "VALID": "VALID: The source control validates or verifies requirements of the target.",
    "MONITOR": "MONITOR: The source control addresses monitoring capabilities for the target.",
    "PREV": "PREV: The source control addresses prevention measures referenced by the target.",
    "GATE": "GATE: The source control provides gating or approval checkpoints for the target.",
    "DISCLOSE": "DISCLOSE: The source control addresses disclosure or reporting obligations of the target.",
    "CROSS_FRAMEWORK_CATEGORY": "Category Link: Controls share a topical category (e.g., both tagged 'privacy' or 'access control').",
    "CROSS_FRAMEWORK_MAPPING": "Cross-Framework Mapping: A direct mapping between controls in different frameworks.",
    "CROSS_FRAMEWORK_XREF": "Cross-Framework Cross-Reference: A cross-reference link between frameworks from upstream data.",
    "EXPERT_ANCHOR": "Expert Anchor: An expert-validated anchor mapping used as a ground-truth reference.",
    "PARENT": "Parent: Hierarchical relationship within the same framework.",

    # Entry types
    "control": "Control: An actionable safeguard or countermeasure defined by the framework.",
    "risk": "Risk: A threat scenario or vulnerability description.",
    "technique": "Technique: An adversarial method or attack pattern (e.g., from MITRE ATLAS).",
    "mitigation": "Mitigation: A recommended countermeasure against a specific technique.",
    "activity": "Activity: A governance or operational action (e.g., from NIST AI RMF).",
    "subcategory": "Subcategory: A subdivision within a framework's organizational structure.",
    "commitment": "Commitment: A policy commitment (e.g., from EU GPAI Code of Practice).",

    # Mapping types
    "direct": "Direct Mapping: A one-hop edge exists between the two controls in the mapping graph.",
    "transitive": "Transitive Mapping: Reachable through a two-hop path via a bridge control in a third framework.",
    "via bridge": "Via Bridge: This mapping is transitive, reaching the target through an intermediate control.",

    # Domain / function names
    "Safety": "Safety Domain: Controls addressing AI system safety, robustness, and harm prevention.",
    "Security": "Security Domain: Controls addressing cybersecurity, access control, and threat protection.",
    "Accountability": "Accountability Domain: Controls addressing transparency, auditability, and responsibility.",
    "Govern": "Govern Function (NIST): Establishing policies, processes, and structures for AI risk management.",
    "Map": "Map Function (NIST): Identifying and understanding AI risks in context.",
    "Measure": "Measure Function (NIST): Quantifying and monitoring identified AI risks.",
    "Manage": "Manage Function (NIST): Prioritizing and acting on AI risks.",
    "Transparency": "Transparency Domain: Controls addressing explainability and disclosure of AI systems.",
    "Privacy": "Privacy Domain: Controls addressing data protection and privacy preservation.",
    "Fairness": "Fairness Domain: Controls addressing bias, discrimination, and equitable outcomes.",
}


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def badge_with_tooltip(text, color="secondary", class_name="me-1", style=None, prefix="badge"):
    """Create a badge with an auto-generated tooltip from the registry.

    If the badge text (case-insensitive lookup) is present in BADGE_TOOLTIPS,
    a dbc.Tooltip is attached.  Otherwise a plain badge is returned.

    Parameters
    ----------
    text : str
        Label to display inside the badge.
    color : str
        Bootstrap color name passed to dbc.Badge.
    class_name : str
        CSS class string passed to dbc.Badge.
    style : dict | None
        Extra inline style rules merged on top of the default font-size rule.
    prefix : str
        Prefix used when constructing the unique element id.
    """
    if not text:
        return None

    tooltip_text = BADGE_TOOLTIPS.get(text) or BADGE_TOOLTIPS.get(text.lower())

    # Unique ID so that multiple instances of the same badge on one page each
    # get their own tooltip target.
    safe_text = str(text).replace(" ", "-").replace("_", "-").lower()
    badge_id = f"{prefix}-{safe_text}-{uuid.uuid4().hex[:6]}"

    badge_style = {"fontSize": "0.7rem"}
    if style:
        badge_style = {**badge_style, **style}

    badge = dbc.Badge(
        text,
        id=badge_id,
        color=color,
        className=class_name,
        style={**badge_style, "cursor": "help" if tooltip_text else "default"},
    )

    if tooltip_text:
        tooltip = dbc.Tooltip(
            tooltip_text,
            target=badge_id,
            placement="top",
            style={"fontSize": "0.78rem", "maxWidth": "300px"},
        )
        return html.Span([badge, tooltip])

    return badge
