"""Shared Plotly figure templates for dark and light modes."""

import plotly.graph_objects as go

DARK_TEMPLATE = go.layout.Template(
    layout=go.Layout(
        paper_bgcolor="#0d1117",
        plot_bgcolor="#0d1117",
        font=dict(family="Inter, system-ui, sans-serif", color="#c9d1d9", size=13),
        title=dict(font=dict(size=16, color="#c9d1d9")),
        xaxis=dict(gridcolor="#21262d", zerolinecolor="#21262d"),
        yaxis=dict(gridcolor="#21262d", zerolinecolor="#21262d"),
        hoverlabel=dict(
            bgcolor="#161b22",
            bordercolor="#30363d",
            font=dict(color="#c9d1d9", size=12),
        ),
        colorway=[
            "#1f6feb", "#8fd18f", "#e8845a", "#4ecdc4",
            "#cf85c4", "#d9bf55", "#7aaed4", "#ff6b6b", "#ffb347",
        ],
        margin=dict(l=40, r=20, t=50, b=40),
    )
)

LIGHT_TEMPLATE = go.layout.Template(
    layout=go.Layout(
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        font=dict(family="Inter, system-ui, sans-serif", color="#1f2328", size=13),
        title=dict(font=dict(size=16, color="#1f2328")),
        xaxis=dict(gridcolor="#d1d9e0", zerolinecolor="#d1d9e0"),
        yaxis=dict(gridcolor="#d1d9e0", zerolinecolor="#d1d9e0"),
        hoverlabel=dict(
            bgcolor="#ffffff",
            bordercolor="#d1d9e0",
            font=dict(color="#1f2328", size=12),
        ),
        colorway=[
            "#1f6feb", "#8fd18f", "#e8845a", "#4ecdc4",
            "#cf85c4", "#d9bf55", "#7aaed4", "#ff6b6b", "#ffb347",
        ],
        margin=dict(l=40, r=20, t=50, b=40),
    )
)


def get_template(theme: str = "dark") -> go.layout.Template:
    """Return the Plotly template for the given theme."""
    return DARK_TEMPLATE if theme == "dark" else LIGHT_TEMPLATE


def apply_theme(fig: go.Figure, theme: str = "dark") -> go.Figure:
    """Apply the theme template to an existing figure."""
    fig.update_layout(template=get_template(theme))
    return fig
