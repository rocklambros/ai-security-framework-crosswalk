"""Dash app factory for the AI Security Framework Crosswalk."""
from __future__ import annotations

import dash
from dash import html, dcc
import dash_bootstrap_components as dbc


def create_app() -> dash.Dash:
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])
    app.title = "AI Security Framework Crosswalk"

    app.layout = dbc.Container([
        html.H1("AI Security Framework Crosswalk", className="mt-3 mb-3"),
        dbc.Tabs([
            dbc.Tab(label="Pair Lookup", tab_id="tab-lookup"),
            dbc.Tab(label="Coverage Heatmap", tab_id="tab-heatmap"),
            dbc.Tab(label="Ablation Results", tab_id="tab-ablations"),
            dbc.Tab(label="About", tab_id="tab-about"),
        ], id="tabs", active_tab="tab-lookup"),
        html.Div(id="tab-content", className="mt-3"),
    ], fluid=True)

    # Import and register tab callbacks
    from app.dash_app.tabs import tab1_lookup, tab4_matrix, tab5_ablations

    tab1_lookup.register_callbacks(app)
    tab4_matrix.register_callbacks(app)
    tab5_ablations.register_callbacks(app)

    @app.callback(
        dash.Output("tab-content", "children"),
        dash.Input("tabs", "active_tab"),
    )
    def render_tab(active_tab):
        if active_tab == "tab-lookup":
            return tab1_lookup.layout()
        elif active_tab == "tab-heatmap":
            return tab4_matrix.layout()
        elif active_tab == "tab-ablations":
            return tab5_ablations.layout()
        elif active_tab == "tab-about":
            return about_layout()
        return html.P("Select a tab")

    return app


def about_layout():
    return dbc.Card(dbc.CardBody([
        html.H3("About"),
        dcc.Markdown(about_panel_markdown()),
    ]))


def about_panel_markdown() -> str:
    return (
        "### AI Security Framework Crosswalk\n\n"
        "Calibrated cross-framework mappings across 12 AI security and governance "
        "frameworks.\n\n"
        "Calibration data sourced from upstream community labels per spec \u00a77 Plan 6.\n\n"
        "See full third-party attribution at [/attribution](/attribution) "
        "(CC BY-SA 4.0: OWASP DSGAI 2026 corpus; GenAI Security Project crosswalk).\n"
    )


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=8050)
