"""Page 4: Coverage Analysis -- compliance gap analysis across frameworks."""

import dash
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from dash import Input, Output, State, callback, dcc, html

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
    "If you comply with Framework X, how much of Framework Y do you already cover? "
    "The radar chart shows your coverage shape; the bar chart breaks it down by direct "
    "vs. transitive reach. Gaps reveal where additional compliance work is needed."
)

LEARN_MORE_CONTENT = [
    html.H6("What Coverage Means", className="mt-2 mb-1", style={"color": "#00d4ff"}),
    html.P(
        "Coverage is the percentage of a target framework's entries that are reachable from the source "
        "framework through cross-framework mappings. If AIUC-1 covers 74% of CSA AICM, it means 74% of "
        "CSA AICM's controls have at least one mapped equivalent in AIUC-1. The remaining 26% represents "
        "a compliance gap: topics that CSA AICM addresses but AIUC-1 does not.",
        style={"fontSize": "0.85rem", "lineHeight": "1.7", "color": "#9eaab8"},
    ),
    html.H6("Direct vs. Transitive Coverage", className="mt-2 mb-1", style={"color": "#00d4ff"}),
    html.P([
        html.Strong("Direct coverage: ", style={"color": "#c9d1d9"}),
        "Target controls reachable in one hop. These are the strongest coverage claims because "
        "there is a direct mapping between source and target controls.",
        html.Br(), html.Br(),
        html.Strong("Transitive coverage: ", style={"color": "#c9d1d9"}),
        "Target controls reachable only through a bridge in a third framework. For example, "
        "if OWASP Agentic maps to AIUC-1, and AIUC-1 maps to CSA AICM, then OWASP Agentic has "
        "transitive coverage of CSA AICM through AIUC-1. Transitive coverage is weaker because "
        "it depends on two mapping hops, each with its own confidence level.",
    ], style={"fontSize": "0.85rem", "lineHeight": "1.7", "color": "#9eaab8"}),
    html.H6("Reading the Radar Chart", className="mt-2 mb-1", style={"color": "#00d4ff"}),
    html.P(
        "Each axis represents a target framework. The solid cyan line shows total coverage (direct + transitive). "
        "The dotted blue line shows direct-only coverage. When the two lines are close together, most coverage "
        "is direct. When they diverge, transitive paths are doing significant work to bridge the gap. A perfectly "
        "round shape at 100% would mean complete coverage of all frameworks (unrealistic in practice).",
        style={"fontSize": "0.85rem", "lineHeight": "1.7", "color": "#9eaab8"},
    ),
    html.H6("Reading the Bar Chart", className="mt-2 mb-1", style={"color": "#00d4ff"}),
    html.P([
        "Each bar represents a target framework, sorted by total coverage. The three segments are: ",
        html.Strong("blue", style={"color": "#1f6feb"}), " (direct), ",
        html.Strong("cyan", style={"color": "#00d4ff"}), " (transitive), and ",
        html.Strong("dark", style={"color": "#6e7681"}), " (gap/no mapping). ",
        "The percentage label at the end of each bar uses color coding: ",
        "cyan for strong coverage (60%+), gold for moderate (30-59%), red for weak (<30%).",
    ], style={"fontSize": "0.85rem", "lineHeight": "1.7", "color": "#9eaab8"}),
    html.H6("Practical Use", className="mt-2 mb-1", style={"color": "#00d4ff"}),
    html.P(
        "A security architect preparing for an AIUC-1 audit who already complies with CSA AICM can use this "
        "page to see that CSA AICM covers roughly 50% of AIUC-1. The remaining 50% is the audit preparation "
        "backlog. Switching between source frameworks quickly reveals which starting point minimizes total "
        "compliance effort across multiple targets.",
        style={"fontSize": "0.85rem", "lineHeight": "1.7", "color": "#9eaab8"},
    ),
]

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
        mode="lines+markers",
        marker=dict(size=6, color="#00d4ff"),
        customdata=list(target_fws) + [target_fws[0]],
        hovertemplate="<b>%{theta}</b><br>Total coverage: %{r:.1f}%<br><i>Click for details</i><extra></extra>",
    ))
    fig.add_trace(go.Scatterpolar(
        r=direct_values,
        theta=categories,
        fill="toself",
        name="Direct only",
        fillcolor="rgba(31,111,235,0.1)",
        line=dict(color="#1f6feb", width=1, dash="dot"),
        mode="lines+markers",
        marker=dict(size=4, color="#1f6feb"),
        customdata=list(target_fws) + [target_fws[0]],
        hovertemplate="<b>%{theta}</b><br>Direct coverage: %{r:.1f}%<br><i>Click for details</i><extra></extra>",
    ))

    fig.update_layout(
        template=get_template(theme),
        height=550,
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
        customdata=target_fws,
        hovertemplate="<b>%{y}</b><br>Direct: %{x:.1f}%<br><i>Click for details</i><extra></extra>",
    ))
    fig.add_trace(go.Bar(
        y=fw_labels, x=trans_pcts, name="Transitive (via bridge)",
        orientation="h", marker_color="#00d4ff",
        customdata=target_fws,
        hovertemplate="<b>%{y}</b><br>Transitive: %{x:.1f}%<br><i>Click for details</i><extra></extra>",
    ))
    fig.add_trace(go.Bar(
        y=fw_labels, x=gap_pcts, name="No mapping",
        orientation="h", marker_color="#21262d",
        customdata=target_fws,
        hovertemplate="<b>%{y}</b><br>Gap: %{x:.1f}%<br><i>Click for details</i><extra></extra>",
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
        height=550,
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
            html.P(INTRO_TEXT, className="text-muted mb-2", style={"fontSize": "0.9rem"}),
            html.A("Learn more about coverage analysis", id="coverage-learn-toggle",
                   style={"fontSize": "0.85rem", "cursor": "pointer", "color": "#00d4ff",
                          "textDecoration": "none"}),
            dbc.Collapse(html.Div(LEARN_MORE_CONTENT, className="mt-2"),
                         id="coverage-learn-more", is_open=False),
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

    # Charts (full-width stacked)
    dbc.Row(dbc.Col(dcc.Loading(dcc.Graph(
        id="coverage-radar",
        config={
            "scrollZoom": True,
            "displayModeBar": True,
            "modeBarButtonsToRemove": ["select2d", "lasso2d", "autoScale2d"],
            "displaylogo": False,
        },
    )))),
    dbc.Row(dbc.Col(dcc.Loading(dcc.Graph(
        id="coverage-bar",
        config={"displayModeBar": True, "modeBarButtonsToRemove": ["select2d", "lasso2d"]},
    ))), className="mt-2"),

    # Drill-down detail panel (populated on bar/radar click)
    html.Div(id="coverage-drilldown", className="mt-3"),
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


@callback(
    Output("coverage-learn-more", "is_open"),
    Input("coverage-learn-toggle", "n_clicks"),
    State("coverage-learn-more", "is_open"),
    prevent_initial_call=True,
)
def toggle_coverage_learn_more(n_clicks, is_open):
    return not is_open


def _build_drilldown_panel(source_fw, target_fw, coverage_data):
    """Build a detail panel for a source -> target framework pair."""
    if source_fw not in coverage_data or target_fw not in coverage_data[source_fw]:
        return html.Div()

    row = coverage_data[source_fw][target_fw]
    total_pct = row.get("total_pct", 0)
    direct_pct = row.get("direct_pct", 0)
    trans_pct = row.get("transitive_pct", 0)
    gap_pct = max(0, 100 - total_pct)

    direct_count = row.get("direct_count", 0)
    trans_count = row.get("transitive_only_count", 0)
    total_reached = row.get("total_reached", 0)
    total_target = row.get("total_target", 0)
    gap_count = max(0, total_target - total_reached)

    by_conf = row.get("by_confidence", {})

    # Coverage bar color
    bar_color = "#00d4ff" if total_pct >= 60 else "#d9bf55" if total_pct >= 30 else "#ff6b6b"

    # Confidence rows
    conf_labels = [
        ("authoritative", "Authoritative", "#00d4ff"),
        ("expert", "Expert", "#58a6ff"),
        ("suggestive", "Suggestive", "#d9bf55"),
        ("unvalidated", "Unvalidated", "#6e7681"),
    ]
    conf_rows = []
    for key, label, color in conf_labels:
        entry = by_conf.get(key, {})
        count = entry.get("count", 0)
        pct = entry.get("pct", 0)
        if count > 0:
            conf_rows.append(
                dbc.Row([
                    dbc.Col(html.Span(label, style={"fontSize": "0.8rem", "color": color}), width=4),
                    dbc.Col(html.Span(f"{count} controls", style={"fontSize": "0.8rem", "color": "#c9d1d9"}), width=4),
                    dbc.Col(html.Span(f"{pct:.1f}%", style={"fontSize": "0.8rem", "color": "#9eaab8"}), width=4),
                ], className="mb-1")
            )

    if not conf_rows:
        conf_rows = [html.P("No confidence breakdown available.", style={"fontSize": "0.8rem", "color": "#6e7681"})]

    panel = dbc.Card(
        dbc.CardBody([
            # Header
            dbc.Row([
                dbc.Col([
                    html.Span("Coverage Detail", style={"fontSize": "0.75rem", "color": "#6e7681", "textTransform": "uppercase", "letterSpacing": "0.05em"}),
                    html.Div([
                        html.Span(get_display_name(source_fw), style={"color": "#c9d1d9", "fontWeight": "600"}),
                        html.Span("  ->  ", style={"color": "#6e7681", "margin": "0 4px"}),
                        html.Span(get_display_name(target_fw), style={"color": "#00d4ff", "fontWeight": "600"}),
                    ], style={"fontSize": "1rem", "marginTop": "2px"}),
                ]),
                dbc.Col(
                    html.Div(
                        f"{total_pct:.1f}%",
                        style={"fontSize": "2rem", "fontWeight": "700", "color": bar_color, "textAlign": "right"},
                    ),
                    width="auto",
                ),
            ], align="center", className="mb-3"),

            # Visual progress bar
            html.Div([
                html.Div(style={
                    "height": "8px",
                    "borderRadius": "4px",
                    "background": f"linear-gradient(to right, #1f6feb {direct_pct:.1f}%, #00d4ff {direct_pct:.1f}%, #00d4ff {total_pct:.1f}%, #21262d {total_pct:.1f}%)",
                }),
                dbc.Row([
                    dbc.Col(html.Span("Direct", style={"fontSize": "0.7rem", "color": "#1f6feb"}), width="auto"),
                    dbc.Col(html.Span("Transitive", style={"fontSize": "0.7rem", "color": "#00d4ff"}), width="auto"),
                    dbc.Col(html.Span("Gap", style={"fontSize": "0.7rem", "color": "#6e7681"}), width="auto", className="ms-auto"),
                ], className="mt-1"),
            ], className="mb-3"),

            html.Hr(style={"borderColor": "#21262d", "margin": "0.5rem 0"}),

            # Count breakdown
            dbc.Row([
                dbc.Col([
                    html.Div(str(direct_count), style={"fontSize": "1.4rem", "fontWeight": "700", "color": "#1f6feb"}),
                    html.Div("Direct", style={"fontSize": "0.75rem", "color": "#9eaab8"}),
                ], className="text-center"),
                dbc.Col([
                    html.Div(str(trans_count), style={"fontSize": "1.4rem", "fontWeight": "700", "color": "#00d4ff"}),
                    html.Div("Transitive", style={"fontSize": "0.75rem", "color": "#9eaab8"}),
                ], className="text-center"),
                dbc.Col([
                    html.Div(str(gap_count), style={"fontSize": "1.4rem", "fontWeight": "700", "color": "#6e7681"}),
                    html.Div("Gap", style={"fontSize": "0.75rem", "color": "#9eaab8"}),
                ], className="text-center"),
                dbc.Col([
                    html.Div(str(total_target), style={"fontSize": "1.4rem", "fontWeight": "700", "color": "#c9d1d9"}),
                    html.Div("Total Controls", style={"fontSize": "0.75rem", "color": "#9eaab8"}),
                ], className="text-center"),
            ], className="mb-3"),

            html.Hr(style={"borderColor": "#21262d", "margin": "0.5rem 0"}),

            # Confidence breakdown
            html.Div("Confidence Breakdown", style={"fontSize": "0.75rem", "color": "#6e7681", "textTransform": "uppercase", "letterSpacing": "0.05em", "marginBottom": "8px"}),
            *conf_rows,
        ]),
        style={"backgroundColor": "rgba(22,27,34,0.85)", "border": "1px solid #21262d"},
        className="mb-3",
    )
    return panel


@callback(
    Output("coverage-drilldown", "children", allow_duplicate=True),
    Input("coverage-bar", "clickData"),
    State("coverage-framework", "value"),
    prevent_initial_call=True,
)
def drilldown_from_bar(click_data, source_fw):
    if not click_data or not source_fw:
        return html.Div()
    point = click_data["points"][0]
    target_fw = point.get("customdata")
    if not target_fw:
        return html.Div()
    coverage = get_coverage_matrix()
    return _build_drilldown_panel(source_fw, target_fw, coverage)


@callback(
    Output("coverage-drilldown", "children", allow_duplicate=True),
    Input("coverage-radar", "clickData"),
    State("coverage-framework", "value"),
    prevent_initial_call=True,
)
def drilldown_from_radar(click_data, source_fw):
    if not click_data or not source_fw:
        return html.Div()
    try:
        points = click_data.get("points", [])
        if not points:
            return html.Div()
        point = points[0]
        # Try customdata first (framework key), fall back to theta (short name)
        target_fw = point.get("customdata")
        if isinstance(target_fw, list):
            target_fw = target_fw[0] if target_fw else None
        if not target_fw or target_fw not in FRAMEWORK_KEYS:
            short_name = point.get("theta", "")
            short_to_fw = {get_short_name(fw): fw for fw in FRAMEWORK_KEYS}
            target_fw = short_to_fw.get(short_name)
        if not target_fw:
            return html.Div()
        coverage = get_coverage_matrix()
        return _build_drilldown_panel(source_fw, target_fw, coverage)
    except Exception:
        return html.Div()
