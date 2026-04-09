"""Dark/light mode toggle component."""
from __future__ import annotations

import dash_bootstrap_components as dbc
from dash import html


def theme_toggle() -> html.Div:
    """Build the dark mode toggle switch."""
    return html.Div(
        style={"display": "flex", "alignItems": "center", "gap": "8px"},
        children=[
            dbc.Switch(
                id="theme-toggle",
                value=True,  # True = dark mode (default)
                style={"marginBottom": "0"},
            ),
            html.Span("Dark", id="theme-label",
                       style={"fontSize": "11px", "color": "var(--text-secondary)"}),
        ],
    )
