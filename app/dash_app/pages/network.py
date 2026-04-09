# app/dash_app/pages/network.py
"""Page 1: Network Explorer — Interactive force-directed graph of framework mappings."""
from __future__ import annotations

import dash_cytoscape as cyto
from dash import callback, dcc, html, Input, Output, State
import dash

from app.dash_app.components.filters import filter_sidebar
from app.dash_app.components.detail_panel import detail_panel
from app.dash_app.components.graph_builder import build_cytoscape_elements
from app.dash_app.data.loader import load_all_mappings
from app.dash_app.data.frameworks import FRAMEWORK_LABELS, TIER_COLORS

cyto.load_extra_layouts()

_CYTO_STYLESHEET = [
    {"selector": ".framework-node", "style": {
        "label": "data(label)", "text-valign": "center", "text-halign": "center",
        "font-size": "10px", "font-weight": "bold", "color": "#fff",
        "text-outline-width": 2, "text-outline-color": "data(background-color)",
        "width": 60, "height": 60, "opacity": 0.9,
    }},
    {"selector": ".control-node", "style": {
        "label": "data(label)", "font-size": "7px",
        "width": 12, "height": 12, "opacity": 0.8, "background-color": "#8b949e",
    }},
    {"selector": ".tier-equivalent", "style": {
        "line-color": TIER_COLORS["equivalent"], "width": 2, "opacity": 0.6, "curve-style": "bezier",
    }},
    {"selector": ".tier-related", "style": {
        "line-color": TIER_COLORS["related"], "width": 1.5, "opacity": 0.5, "curve-style": "bezier",
    }},
    {"selector": ".tier-partial", "style": {
        "line-color": TIER_COLORS["partial"], "width": 1, "opacity": 0.4, "curve-style": "bezier",
    }},
    {"selector": ".ml-predicted", "style": {"line-style": "dashed", "opacity": 0.3}},
    {"selector": ":selected", "style": {"border-width": 3, "border-color": "#58a6ff", "opacity": 1}},
    {"selector": ".dimmed", "style": {"opacity": 0.15}},
]


def layout() -> html.Div:
    df = load_all_mappings()
    elements = build_cytoscape_elements(df)
    n_frameworks = df["source_framework"].nunique() + df["target_framework"].nunique()
    n_mappings = len(df)

    return html.Div(
        style={"display": "flex", "height": "calc(100vh - 56px)"},
        children=[
            filter_sidebar(),
            html.Div(style={"flex": 1, "position": "relative", "background": "var(--bg-primary)"}, children=[
                cyto.Cytoscape(
                    id="network-graph", elements=elements, stylesheet=_CYTO_STYLESHEET,
                    layout={"name": "cose-bilkent", "animate": False, "nodeDimensionsIncludeLabels": True},
                    style={"width": "100%", "height": "100%"}, responsive=True,
                ),
                html.Div(className="stats-badge", children=[
                    f"{n_frameworks} frameworks \u2022 {n_mappings:,} mappings"
                ]),
            ]),
            detail_panel(),
            dcc.Store(id="filter-state", data={}),
        ],
    )


def register_callbacks(app: dash.Dash) -> None:
    @app.callback(
        Output("detail-content", "children"),
        Input("network-graph", "tapNodeData"),
    )
    def update_detail_panel(node_data):
        if not node_data:
            return html.P("Click a node to see details.",
                          style={"color": "var(--text-muted)", "fontSize": "12px"})
        node_id = node_data.get("id", "")
        label = node_data.get("label", node_id)
        framework = node_data.get("framework", "")
        description = node_data.get("description", "")
        fw_label = FRAMEWORK_LABELS.get(framework, framework)
        return html.Div([
            html.Div(className="panel", children=[
                html.Div(label, style={"fontSize": "14px", "fontWeight": 600, "color": "var(--text-primary)"}),
                html.Div(fw_label, style={"fontSize": "11px", "color": "var(--accent-blue)", "marginTop": "2px"}),
                html.P(description, style={"fontSize": "11px", "color": "var(--text-secondary)",
                                           "marginTop": "8px", "lineHeight": "1.5"}) if description else None,
            ]),
        ])

    @app.callback(
        Output("network-graph", "elements"),
        [Input("filter-frameworks", "value"), Input("filter-tier", "value"),
         Input("filter-confidence", "value"), Input("filter-search", "value"),
         Input("filter-data-source", "value"), Input("filter-source-fw", "value")],
    )
    def filter_graph(frameworks, tier, confidence, search, data_source, source_fw):
        df = load_all_mappings()
        if frameworks:
            df = df[df["source_framework"].isin(frameworks) | df["target_framework"].isin(frameworks)]
        if tier and tier != "all":
            tier_map = {"equivalent": "Foundational", "related": "Foundational", "partial": "Expanded"}
            df = df[df["tier"] == tier_map.get(tier, tier)]
        if confidence and confidence > 0:
            if "confidence" in df.columns:
                df = df[df["confidence"] >= confidence]
        if data_source and data_source != "both":
            if "data_source" in df.columns:
                df = df[df["data_source"] == data_source]
        if source_fw:
            df = df[df["source_framework"] == source_fw]
        elements = build_cytoscape_elements(df)
        if search:
            search_lower = search.lower()
            for el in elements:
                data = el.get("data", {})
                if "source" not in data:
                    label = data.get("label", "").lower()
                    desc = data.get("description", "").lower()
                    if search_lower not in label and search_lower not in desc:
                        el.setdefault("classes", "")
                        el["classes"] += " dimmed"
        return elements
