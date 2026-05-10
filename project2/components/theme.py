"""Theme toggle logic -- swaps DBC stylesheet between CYBORG (dark) and FLATLY (light)."""

import dash_bootstrap_components as dbc
from dash import Input, Output, callback, clientside_callback

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


clientside_callback(
    f"""
    function(is_dark) {{
        var dark = "{DARK_THEME_URL}";
        var light = "{LIGHT_THEME_URL}";
        var url = is_dark ? dark : light;
        var links = document.querySelectorAll('link[rel="stylesheet"]');
        for (var i = 0; i < links.length; i++) {{
            if (links[i].href.indexOf("bootstrap") !== -1) {{
                links[i].href = url;
                break;
            }}
        }}
        return window.dash_clientside.no_update;
    }}
    """,
    Output("theme-label", "style"),
    Input("theme-switch", "value"),
    prevent_initial_call=True,
)
