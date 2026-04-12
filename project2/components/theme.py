"""Theme toggle logic -- swaps DBC stylesheet between CYBORG (dark) and FLATLY (light)."""

import dash_bootstrap_components as dbc
from dash import Input, Output, callback, html

DARK_THEME_URL = dbc.themes.CYBORG
LIGHT_THEME_URL = dbc.themes.FLATLY


@callback(
    Output("theme-store", "data"),
    Output("theme-label", "children"),
    Input("theme-switch", "value"),
)
def toggle_theme(is_dark):
    """Update theme store when switch is toggled."""
    theme = "dark" if is_dark else "light"
    label = "Dark" if is_dark else "Light"
    return theme, label
