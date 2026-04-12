"""Top navigation bar with page links and theme toggle."""

import dash_bootstrap_components as dbc
from dash import html


def create_navbar():
    """Return the navbar component."""
    return dbc.Navbar(
        dbc.Container(
            [
                dbc.NavbarBrand(
                    [
                        html.Span("AI Security Crosswalk Explorer",
                                  style={"fontWeight": "600"}),
                    ],
                    href="/",
                    className="me-auto",
                ),
                dbc.Nav(
                    [
                        dbc.NavItem(dbc.NavLink("Landscape", href="/", active="exact")),
                        dbc.NavItem(dbc.NavLink("Deep Dive", href="/deep-dive")),
                        dbc.NavItem(dbc.NavLink("Explorer", href="/explorer")),
                        dbc.NavItem(dbc.NavLink("Coverage", href="/coverage")),
                    ],
                    className="me-3",
                    navbar=True,
                ),
                dbc.Switch(
                    id="theme-switch",
                    label="",
                    value=True,  # True = dark mode
                    className="ms-2",
                ),
                html.Span(
                    "Dark",
                    id="theme-label",
                    className="ms-1",
                    style={"fontSize": "0.8rem", "color": "#8a95a8"},
                ),
            ],
            fluid=True,
        ),
        color="dark",
        dark=True,
        className="mb-0",
        sticky="top",
    )
