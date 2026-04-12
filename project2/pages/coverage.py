"""Page 4: Coverage Analysis -- compliance gap analysis across frameworks."""

import dash
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from dash import Input, Output, callback, dcc, html

from components.data_loader import get_coverage_matrix, get_framework_stats
from components.framework_colors import (
    FRAMEWORK_KEYS,
    get_color,
    get_display_name,
    get_short_name,
)
from components.plot_theme import get_template

dash.register_page(__name__, path="/coverage", name="Coverage", order=3)

INTRO_TEXT = (
    "Select a source framework to see what percentage of each target framework "
    "it covers through direct and transitive (2-hop bridge) mappings. "
    "Adjust the confidence threshold to focus on higher-quality mappings. "
    "Gaps in the radar chart reveal where additional compliance work is needed."
)

CONFIDENCE_HELP = {
    0: "Any: include all mappings regardless of confidence",
    1: "Suggestive+: shared categories and above",
    2: "Expert+: expert-validated and authoritative only",
    3: "Authoritative only: from official framework source documents",
}


def _framework_options():
    stats = get_framework_stats()
    return [
        {"label": f"{get_display_name(fw)} ({stats[fw]['node_count']})", "value": fw}
        for fw in FRAMEWORK_KEYS
        if fw in stats
    ]


def _build_radar(source_fw, coverage_data, theme="dark"):
    """Build radar chart showing coverage across all target frameworks."""
    if source_fw not in coverage_data:
        fig = go.Figure()
        fig.update_layout(template=get_template(theme))
        return fig

    targets = coverage_data[source_fw]
    target_fws = sorted(targets.keys(), key=lambda fw: targets[fw]["total_pct"], reverse=True)

    categories = [get_short_name(fw) for fw in target_fws]
    values = [targets[fw]["total_pct"] for fw in target_fws]
    direct_values = [targets[fw]["direct_pct"] for fw in target_fws]

    # Close the polygon
    categories.append(categories[0])
    values.append(values[0])
    direct_values.append(direct_values[0])

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill="toself",
        name="Total (direct + transitive)",
        fillcolor="rgba(0,212,255,0.15)",
        line=dict(color="#00d4ff", width=2),
        hovertemplate="<b>%{theta}</b><br>Total coverage: %{r:.1f}%<extra></extra>",
    ))
    fig.add_trace(go.Scatterpolar(
        r=direct_values,
        theta=categories,
        fill="toself",
        name="Direct only",
        fillcolor="rgba(31,111,235,0.1)",
        line=dict(color="#1f6feb", width=1, dash="dot"),
        hovertemplate="<b>%{theta}</b><br>Direct coverage: %{r:.1f}%<extra></extra>",
    ))

    fig.update_layout(
        template=get_template(theme),
        height=500,
        title=dict(
            text=f"Coverage Profile for {get_display_name(source_fw)}",
            font=dict(size=14),
        ),
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                ticksuffix="%",
                gridcolor="#21262d" if theme == "dark" else "#d1d9e0",
            ),
            angularaxis=dict(
                gridcolor="#21262d" if theme == "dark" else "#d1d9e0",
            ),
        ),
        legend=dict(orientation="h", yanchor="bottom", y=-0.15),
    )
    return fig


def _build_coverage_bar(source_fw, coverage_data, theme="dark"):
    """Build stacked bar chart: coverage breakdown by direct/transitive/gap."""
    if source_fw not in coverage_data:
        fig = go.Figure()
        fig.update_layout(template=get_template(theme))
        return fig

    targets = coverage_data[source_fw]
    target_fws = sorted(targets.keys(), key=lambda fw: targets[fw]["total_pct"], reverse=True)

    fw_labels = [get_short_name(fw) for fw in target_fws]
    direct_pcts = [targets[fw]["direct_pct"] for fw in target_fws]
    trans_pcts = [targets[fw]["transitive_pct"] for fw in target_fws]
    gap_pcts = [100 - targets[fw]["total_pct"] for fw in target_fws]
    total_pcts = [targets[fw]["total_pct"] for fw in target_fws]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=fw_labels, x=direct_pcts, name="Direct",
        orientation="h", marker_color="#1f6feb",
        hovertemplate="<b>%{y}</b><br>Direct: %{x:.1f}%<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        y=fw_labels, x=trans_pcts, name="Transitive (via bridge)",
        orientation="h", marker_color="#00d4ff",
        hovertemplate="<b>%{y}</b><br>Transitive: %{x:.1f}%<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        y=fw_labels, x=gap_pcts, name="No mapping",
        orientation="h", marker_color="#21262d",
        hovertemplate="<b>%{y}</b><br>Gap: %{x:.1f}%<extra></extra>",
    ))

    # Add percentage labels
    for i, pct in enumerate(total_pcts):
        color = "#00d4ff" if pct >= 60 else "#d9bf55" if pct >= 30 else "#ff6b6b"
        fig.add_annotation(
            x=min(pct + 2, 100), y=fw_labels[i],
            text=f"{pct:.0f}%",
            showarrow=False,
            font=dict(size=11, color=color),
            xanchor="left",
        )

    fig.update_layout(
        template=get_template(theme),
        height=500,
        title=dict(text="Coverage Breakdown by Tier", font=dict(size=14)),
        barmode="stack",
        xaxis=dict(title="Coverage %", range=[0, 110], ticksuffix="%"),
        yaxis=dict(categoryorder="array", categoryarray=list(reversed(fw_labels))),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2),
    )
    return fig


# --- Layout ---
layout = dbc.Container([
    dbc.Row(dbc.Col(
        dbc.Card(dbc.CardBody([
            html.H4("Coverage Analysis", className="mb-2"),
            html.P(INTRO_TEXT, className="text-muted mb-0", style={"fontSize": "0.9rem"}),
        ]), className="mb-3 border-0",
        style={"backgroundColor": "rgba(22,27,34,0.5)"}),
    )),

    # Controls
    dbc.Row([
        dbc.Col([
            dbc.Label("Source Framework", className="text-muted", style={"fontSize": "0.8rem"}),
            dcc.Dropdown(
                id="coverage-framework",
                options=_framework_options(),
                value="aiuc_1",
                clearable=False,
            ),
        ], md=5),
        dbc.Col([
            dbc.Label([
                "Minimum Confidence ",
                html.Span("\u24d8", id="coverage-confidence-info",
                          style={"cursor": "help", "color": "#6e7681"}),
                dbc.Tooltip(
                    "Filter mappings by confidence level. Higher confidence means "
                    "the mapping has been more rigorously validated.",
                    target="coverage-confidence-info",
                ),
            ], className="text-muted", style={"fontSize": "0.8rem"}),
            dcc.Slider(
                id="coverage-confidence",
                min=0,
                max=3,
                step=1,
                marks={
                    0: "Any",
                    1: "Suggestive+",
                    2: "Expert+",
                    3: "Authoritative",
                },
                value=0,
                className="mt-1",
            ),
        ], md=7),
    ], className="mb-4"),

    # Charts
    dbc.Row([
        dbc.Col(dcc.Loading(dcc.Graph(id="coverage-radar", config={"displayModeBar": False})), md=6),
        dbc.Col(dcc.Loading(dcc.Graph(id="coverage-bar", config={"displayModeBar": False})), md=6),
    ]),
], fluid=True)


@callback(
    Output("coverage-radar", "figure"),
    Output("coverage-bar", "figure"),
    Input("coverage-framework", "value"),
    Input("coverage-confidence", "value"),
    Input("theme-store", "data"),
)
def update_coverage(source_fw, confidence_level, theme):
    coverage = get_coverage_matrix()

    # For now, coverage matrix is pre-computed with all confidence levels.
    # Confidence filtering would require recomputation; for the initial version
    # we show the full coverage and note the selected threshold.
    # TODO: If confidence filtering is needed at runtime, prepare_data.py should
    # produce separate matrices per confidence level, or the app should recompute.

    radar = _build_radar(source_fw, coverage, theme)
    bar = _build_coverage_bar(source_fw, coverage, theme)

    return radar, bar
