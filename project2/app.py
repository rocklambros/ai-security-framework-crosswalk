"""AI Security Crosswalk Explorer - Main application entry point."""

import dash
import dash_bootstrap_components as dbc
from dash import html, dcc

from components.navbar import create_navbar
from components.theme import DARK_THEME_URL  # noqa: F401 - registers callbacks

app = dash.Dash(
    __name__,
    use_pages=True,
    external_stylesheets=[dbc.themes.CYBORG],
    suppress_callback_exceptions=True,
    title="AI Security Crosswalk Explorer",
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)

server = app.server

app.layout = dbc.Container(
    [
        dcc.Store(id="theme-store", data="dark"),
        dcc.Location(id="url", refresh=False),
        create_navbar(),
        html.Div(
            dash.page_container,
            className="pt-3 px-3",
        ),
    ],
    fluid=True,
    className="px-0",
)

if __name__ == "__main__":
    app.run(debug=True, port=8050)
