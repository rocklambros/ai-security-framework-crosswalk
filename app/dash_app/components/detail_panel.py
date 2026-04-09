"""Right-side detail panel for selected node information."""
from __future__ import annotations

from dash import html


def detail_panel() -> html.Div:
    """Build the right detail panel (populated by callbacks)."""
    return html.Div(className="detail-panel", id="detail-panel", children=[
        html.Div(className="filter-label", children="Selected Node"),
        html.Div(id="detail-content", children=[
            html.P("Click a node in the graph to see details.",
                   style={"color": "var(--text-muted)", "fontSize": "12px"}),
        ]),
    ])
