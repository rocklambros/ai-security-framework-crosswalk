"""Shared filter sidebar used across pages."""
from __future__ import annotations

from dash import dcc, html
import dash_bootstrap_components as dbc

from app.dash_app.data.frameworks import FRAMEWORK_LABELS, FRAMEWORK_CATEGORIES


def filter_sidebar() -> html.Div:
    """Build the left filter sidebar with all 7 DCC components."""
    framework_options = []
    for category, fw_ids in FRAMEWORK_CATEGORIES.items():
        for fw_id in fw_ids:
            label = FRAMEWORK_LABELS.get(fw_id, fw_id)
            framework_options.append({"label": f"  {label}", "value": fw_id})

    return html.Div(className="filter-sidebar", children=[
        html.Div(className="filter-label", children="Filters"),

        # 1. Framework multi-select checklist
        html.Div(className="filter-section", children=[
            html.Div("Frameworks", style={"fontSize": "12px", "marginBottom": "4px"}),
            dcc.Checklist(
                id="filter-frameworks",
                options=[{"label": FRAMEWORK_LABELS.get(fw, fw), "value": fw}
                         for fw in FRAMEWORK_LABELS],
                value=list(FRAMEWORK_LABELS.keys()),
                style={"fontSize": "11px", "maxHeight": "200px", "overflowY": "auto"},
            ),
        ]),

        # 2. Tier radio buttons
        html.Div(className="filter-section", children=[
            html.Div("Mapping Tier", style={"fontSize": "12px", "marginBottom": "4px"}),
            dcc.RadioItems(
                id="filter-tier",
                options=[
                    {"label": "All", "value": "all"},
                    {"label": "● Equivalent", "value": "equivalent"},
                    {"label": "● Related", "value": "related"},
                    {"label": "● Partial", "value": "partial"},
                ],
                value="all",
                style={"fontSize": "11px"},
            ),
        ]),

        # 3. Confidence threshold slider
        html.Div(className="filter-section", children=[
            html.Div("Confidence ≥", style={"fontSize": "12px", "marginBottom": "4px"}),
            dcc.Slider(
                id="filter-confidence",
                min=0.0, max=1.0, step=0.05, value=0.0,
                marks={0: "0", 0.5: "0.5", 1: "1.0"},
                tooltip={"placement": "bottom", "always_visible": True},
            ),
        ]),

        # 4. Search text input
        html.Div(className="filter-section", children=[
            html.Div("Search Controls", style={"fontSize": "12px", "marginBottom": "4px"}),
            dcc.Input(
                id="filter-search",
                type="text",
                placeholder='e.g. "prompt injection"',
                debounce=True,
                style={
                    "width": "100%", "fontSize": "11px",
                    "background": "var(--bg-tertiary)",
                    "border": "1px solid var(--border)",
                    "borderRadius": "6px", "padding": "8px",
                    "color": "var(--text-primary)",
                },
            ),
        ]),

        # 5. Source framework dropdown
        html.Div(className="filter-section", children=[
            html.Div("Source Framework", style={"fontSize": "12px", "marginBottom": "4px"}),
            dcc.Dropdown(
                id="filter-source-fw",
                options=[{"label": v, "value": k} for k, v in FRAMEWORK_LABELS.items()],
                value=None,
                placeholder="All sources",
                clearable=True,
                style={"fontSize": "12px"},
            ),
        ]),

        # 6. Data source toggle
        html.Div(className="filter-section", children=[
            html.Div("Data Source", style={"fontSize": "12px", "marginBottom": "4px"}),
            dcc.RadioItems(
                id="filter-data-source",
                options=[
                    {"label": "Expert", "value": "expert"},
                    {"label": "ML Predicted", "value": "ml"},
                    {"label": "Both", "value": "both"},
                ],
                value="both",
                inline=True,
                style={"fontSize": "11px"},
            ),
        ]),
    ])
