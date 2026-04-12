"""Page 1: Framework Landscape -- bird's-eye view of the AI security ecosystem."""

import dash
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from dash import Input, Output, callback, dcc, html

from components.data_loader import get_edges_df, get_framework_stats, get_graph_metrics, get_nodes_df
from components.framework_colors import (
    FRAMEWORK_KEYS,
    get_color,
    get_display_name,
    get_short_name,
    CONFIDENCE_LABELS,
)
from components.plot_theme import get_template

dash.register_page(__name__, path="/", name="Landscape", order=0)

# --- Narrative ---
INTRO_TEXT = (
    "Nine major AI security standards mapped to each other. "
    "This view shows how frameworks relate at the ecosystem level. "
    "Node size reflects the number of controls in each framework. "
    "Edge width reflects the density of cross-framework mappings. "
    "Use the filters below to focus on specific confidence levels or relationship types."
)


def _build_network_figure(edges_df, stats, theme="dark"):
    """Build the framework supernode network graph."""
    import math

    fw_list = [fw for fw in FRAMEWORK_KEYS if fw in stats]
    n = len(fw_list)

    # Circular layout
    positions = {}
    for i, fw in enumerate(fw_list):
        angle = 2 * math.pi * i / n - math.pi / 2
        positions[fw] = (math.cos(angle), math.sin(angle))

    # Edge traces
    edge_traces = []
    pair_counts = {}
    for _, row in edges_df.iterrows():
        src_fw = row["source_framework"]
        tgt_fw = row["target_framework"]
        if src_fw != tgt_fw:
            key = tuple(sorted([src_fw, tgt_fw]))
            pair_counts[key] = pair_counts.get(key, 0) + 1

    for (fw1, fw2), count in pair_counts.items():
        if fw1 in positions and fw2 in positions:
            x0, y0 = positions[fw1]
            x1, y1 = positions[fw2]
            width = max(1, min(count / 100, 12))
            edge_traces.append(go.Scatter(
                x=[x0, x1, None],
                y=[y0, y1, None],
                mode="lines",
                line=dict(width=width, color="rgba(0, 212, 255, 0.15)"),
                hoverinfo="text",
                text=f"{get_short_name(fw1)} - {get_short_name(fw2)}: {count} mappings",
                showlegend=False,
            ))

    # Node trace
    node_x = [positions[fw][0] for fw in fw_list]
    node_y = [positions[fw][1] for fw in fw_list]
    node_sizes = [max(20, stats[fw]["node_count"] / 3) for fw in fw_list]
    node_colors = [get_color(fw) for fw in fw_list]
    node_text = [
        f"<b>{get_display_name(fw)}</b><br>"
        f"Nodes: {stats[fw]['node_count']}<br>"
        f"Edges out: {stats[fw]['edge_count_out']}<br>"
        f"Edges in: {stats[fw]['edge_count_in']}"
        for fw in fw_list
    ]

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers+text",
        marker=dict(size=node_sizes, color=node_colors, line=dict(width=2, color="rgba(0,212,255,0.3)")),
        text=[get_short_name(fw) for fw in fw_list],
        textposition="top center",
        textfont=dict(size=11),
        hovertext=node_text,
        hoverinfo="text",
        customdata=fw_list,
        showlegend=False,
    )

    fig = go.Figure(data=edge_traces + [node_trace])
    fig.update_layout(
        template=get_template(theme),
        xaxis=dict(visible=False, range=[-1.5, 1.5]),
        yaxis=dict(visible=False, range=[-1.5, 1.5], scaleanchor="x"),
        height=500,
        title=dict(
            text="Framework Relationship Network",
            font=dict(size=14),
        ),
        hovermode="closest",
    )
    return fig


def _build_heatmap_figure(edges_df, theme="dark"):
    """Build the 9x9 pairwise mapping density heatmap."""
    fw_list = FRAMEWORK_KEYS
    short_names = [get_short_name(fw) for fw in fw_list]

    # Count cross-framework edges
    matrix = [[0] * len(fw_list) for _ in range(len(fw_list))]
    fw_idx = {fw: i for i, fw in enumerate(fw_list)}

    for _, row in edges_df.iterrows():
        src_fw = row["source_framework"]
        tgt_fw = row["target_framework"]
        if src_fw in fw_idx and tgt_fw in fw_idx and src_fw != tgt_fw:
            matrix[fw_idx[src_fw]][fw_idx[tgt_fw]] += 1

    fig = go.Figure(data=go.Heatmap(
        z=matrix,
        x=short_names,
        y=short_names,
        colorscale=[[0, "#0d1117"], [0.5, "#1f6feb"], [1, "#00d4ff"]],
        hovertemplate=(
            "<b>%{y}</b> to <b>%{x}</b><br>"
            "Mappings: %{z}<br>"
            "<extra></extra>"
        ),
    ))
    fig.update_layout(
        template=get_template(theme),
        height=500,
        title=dict(text="Pairwise Mapping Density", font=dict(size=14)),
        xaxis=dict(side="bottom", tickangle=45),
        yaxis=dict(autorange="reversed"),
    )
    return fig


# --- Layout ---
layout = dbc.Container([
    # Intro
    dbc.Row(dbc.Col(
        dbc.Card(dbc.CardBody([
            html.H4("AI Security Framework Landscape", className="mb-2"),
            html.P(INTRO_TEXT, className="text-muted mb-0", style={"fontSize": "0.9rem"}),
        ]), className="mb-3 border-0",
        style={"backgroundColor": "rgba(22,27,34,0.5)"}),
    )),

    # Filters
    dbc.Row([
        dbc.Col([
            dbc.Label("Confidence Level", html_for="landscape-confidence",
                      className="text-muted", style={"fontSize": "0.8rem"}),
            dcc.Dropdown(
                id="landscape-confidence",
                options=[
                    {"label": "Any", "value": "any"},
                    {"label": "Suggestive+", "value": "suggestive"},
                    {"label": "Expert+", "value": "expert"},
                    {"label": "Authoritative only", "value": "authoritative"},
                ],
                value="any",
                clearable=False,
                className="mb-2",
            ),
        ], md=4),
        dbc.Col([
            dbc.Label("Relationship Type", html_for="landscape-edge-type",
                      className="text-muted", style={"fontSize": "0.8rem"}),
            dcc.RadioItems(
                id="landscape-edge-type",
                options=[
                    {"label": "All", "value": "all"},
                    {"label": "Rationale-coded only", "value": "rationale"},
                    {"label": "Category links only", "value": "category"},
                ],
                value="all",
                inline=True,
                className="mb-2",
                inputStyle={"marginRight": "4px"},
                labelStyle={"marginRight": "16px", "fontSize": "0.85rem"},
            ),
        ], md=8),
    ], className="mb-3"),

    # Charts
    dbc.Row([
        dbc.Col(dcc.Loading(dcc.Graph(id="landscape-network", config={"displayModeBar": False})), md=6),
        dbc.Col(dcc.Loading(dcc.Graph(id="landscape-heatmap", config={"displayModeBar": False})), md=6),
    ]),

    # Summary stats
    dbc.Row(dbc.Col(
        html.Div(id="landscape-stats", className="mt-3"),
    )),

], fluid=True)


@callback(
    Output("landscape-network", "figure"),
    Output("landscape-heatmap", "figure"),
    Output("landscape-stats", "children"),
    Input("landscape-confidence", "value"),
    Input("landscape-edge-type", "value"),
    Input("theme-store", "data"),
)
def update_landscape(confidence, edge_type, theme):
    edges_df = get_edges_df()
    stats = get_framework_stats()

    # Filter edges
    if confidence != "any":
        conf_order = ["authoritative", "expert", "suggestive", "unvalidated"]
        min_idx = conf_order.index(confidence)
        allowed = set(conf_order[:min_idx + 1])
        edges_df = edges_df[edges_df["confidence"].isin(allowed)]

    if edge_type == "rationale":
        edges_df = edges_df[
            ~edges_df["rationale_code"].isin(["CROSS_FRAMEWORK_CATEGORY", "PARENT", None])
            & edges_df["rationale_code"].notna()
        ]
    elif edge_type == "category":
        edges_df = edges_df[edges_df["rationale_code"] == "CROSS_FRAMEWORK_CATEGORY"]

    cross = edges_df[edges_df["source_framework"] != edges_df["target_framework"]]

    network_fig = _build_network_figure(edges_df, stats, theme)
    heatmap_fig = _build_heatmap_figure(edges_df, theme)

    # Stats bar
    nodes_df = get_nodes_df()
    stats_bar = dbc.Row([
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H3("9", className="text-info mb-0"),
            html.Small("Frameworks", className="text-muted"),
        ]), className="text-center border-0"), md=3),
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H3(f"{len(nodes_df):,}", className="text-info mb-0"),
            html.Small("Controls & Risks", className="text-muted"),
        ]), className="text-center border-0"), md=3),
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H3(f"{len(edges_df):,}", className="text-info mb-0"),
            html.Small("Relationships (filtered)", className="text-muted"),
        ]), className="text-center border-0"), md=3),
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H3(f"{len(cross):,}", className="text-info mb-0"),
            html.Small("Cross-Framework", className="text-muted"),
        ]), className="text-center border-0"), md=3),
    ])

    return network_fig, heatmap_fig, stats_bar
