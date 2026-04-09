"""Dash app factory for the AI Security Framework Crosswalk."""
from __future__ import annotations

import dash
from dash import html, dcc, Input, Output, clientside_callback
import dash_bootstrap_components as dbc

from app.dash_app.components.theme_toggle import theme_toggle


def create_app() -> dash.Dash:
    app = dash.Dash(
        __name__,
        external_stylesheets=[dbc.themes.DARKLY],
        suppress_callback_exceptions=True,
    )
    app.title = "AI Security Framework Crosswalk"

    # Navigation bar
    navbar = html.Div(className="navbar", style={
        "display": "flex", "justifyContent": "space-between", "alignItems": "center",
    }, children=[
        html.Div(style={"display": "flex", "alignItems": "center", "gap": "16px"}, children=[
            html.A("AI Security Framework Crosswalk", className="brand", href="/"),
            html.Div(className="nav-tabs", id="nav-tabs", children=[
                html.Button("Network", id="nav-network", className="nav-tab active", n_clicks=0),
                html.Button("Coverage", id="nav-coverage", className="nav-tab", n_clicks=0),
                html.Button("Mappings", id="nav-mappings", className="nav-tab", n_clicks=0),
                html.Button("Model", id="nav-model", className="nav-tab", n_clicks=0),
                html.Button("About", id="nav-about", className="nav-tab", n_clicks=0),
            ]),
        ]),
        theme_toggle(),
    ])

    app.layout = html.Div(id="app-container", children=[
        navbar,
        html.Div(id="page-content"),
        dcc.Store(id="current-page", data="network"),
        dcc.Store(id="filter-state", data={}),
    ])

    # Import pages
    from app.dash_app.pages import network, coverage, mappings, model, about

    # Register page-specific callbacks
    network.register_callbacks(app)
    coverage.register_callbacks(app)
    mappings.register_callbacks(app)
    model.register_callbacks(app)

    # Page navigation callback
    @app.callback(
        [Output("page-content", "children"),
         Output("current-page", "data")],
        [Input("nav-network", "n_clicks"),
         Input("nav-coverage", "n_clicks"),
         Input("nav-mappings", "n_clicks"),
         Input("nav-model", "n_clicks"),
         Input("nav-about", "n_clicks")],
    )
    def navigate(net, cov, maps, mod, abt):
        ctx = dash.callback_context
        if not ctx.triggered:
            return network.layout(), "network"

        trigger = ctx.triggered[0]["prop_id"].split(".")[0]
        page_map = {
            "nav-network": ("network", network.layout),
            "nav-coverage": ("coverage", coverage.layout),
            "nav-mappings": ("mappings", mappings.layout),
            "nav-model": ("model", model.layout),
            "nav-about": ("about", about.layout),
        }
        page_id, layout_fn = page_map.get(trigger, ("network", network.layout))
        return layout_fn(), page_id

    # Theme toggle clientside callback
    clientside_callback(
        """
        function(dark_mode) {
            const theme = dark_mode ? 'dark' : 'light';
            document.documentElement.setAttribute('data-theme', theme);
            localStorage.setItem('crosswalk-theme', theme);
            return theme === 'dark' ? 'Dark' : 'Light';
        }
        """,
        Output("theme-label", "children"),
        Input("theme-toggle", "value"),
    )

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=8050)
