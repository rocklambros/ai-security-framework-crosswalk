"""Classifier tier badge and confidence indicator components."""

from dash import html
import dash_bootstrap_components as dbc

TIER_NAMES = {
    0: "UNRELATED",
    1: "PARTIAL",
    2: "RELATED",
    3: "EQUIVALENT",
    -1: "N/A",
}

TIER_COLORS = {
    3: "#d4a017",
    2: "#00d4ff",
    1: "#d9bf55",
    0: "#6e7681",
    -1: "#484f58",
}

TIER_FILTER_OPTIONS = [
    {"label": "Any", "value": "any"},
    {"label": "Equivalent", "value": "3"},
    {"label": "Related+", "value": "2"},
    {"label": "Partial+", "value": "1"},
]


def classifier_badge(tier, confidence=None):
    """Render a classifier tier badge with optional confidence micro-bar."""
    if tier is None:
        return html.Span()

    tier = int(tier)
    name = TIER_NAMES.get(tier, "N/A")
    color = TIER_COLORS.get(tier, "#484f58")

    parts = [
        dbc.Badge(
            name,
            style={
                "backgroundColor": f"{color}22",
                "color": color,
                "border": f"1px solid {color}44",
                "fontSize": "0.68rem",
                "fontWeight": "500",
            },
            className="me-1",
        ),
    ]

    if confidence is not None and tier != -1:
        conf_pct = float(confidence) * 100
        parts.append(
            html.Span(
                html.Span(
                    style={
                        "display": "inline-block",
                        "width": f"{conf_pct}%",
                        "height": "100%",
                        "backgroundColor": color,
                        "borderRadius": "2px",
                    },
                ),
                style={
                    "display": "inline-block",
                    "width": "32px",
                    "height": "4px",
                    "backgroundColor": "rgba(110,118,129,0.2)",
                    "borderRadius": "2px",
                    "verticalAlign": "middle",
                },
                title=f"Classifier confidence: {confidence:.0%}",
            ),
        )

    return html.Span(parts, className="ms-1")


def filter_edges_by_tier(edges_df, tier_value):
    """Filter edges DataFrame by classifier tier threshold.

    tier_value: "any", "1" (Partial+), "2" (Related+), "3" (Equivalent only)
    """
    if tier_value == "any":
        return edges_df
    min_tier = int(tier_value)
    return edges_df[edges_df["classifier_tier"] >= min_tier]
