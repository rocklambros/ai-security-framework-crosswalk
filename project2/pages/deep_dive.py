"""Page 2: Framework Deep Dive -- explore a single framework's structure."""

import dash
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from dash import Input, Output, State, callback, ctx, dcc, html

from components.data_loader import (
    get_edges_df,
    get_framework_stats,
    get_hierarchy,
    get_node_by_id,
    get_nodes_df,
)
from components.framework_colors import (
    CONFIDENCE_COLORS,
    FRAMEWORK_KEYS,
    get_color,
    get_display_name,
    get_short_name,
)
from components.plot_theme import get_template

dash.register_page(__name__, path="/deep-dive", name="Deep Dive", order=1)

INTRO_TEXT = (
    "Select a framework to explore its internal structure. "
    "The sunburst shows how controls are organized by domain. "
    "Click any segment to see the full control text. "
    'Use "View in Explorer" to trace that control\'s cross-framework mappings.'
)


def _framework_options():
    stats = get_framework_stats()
    return [
        {"label": f"{get_display_name(fw)} ({stats[fw]['node_count']} nodes)", "value": fw}
        for fw in FRAMEWORK_KEYS
        if fw in stats
    ]


def _build_sunburst(framework, entry_types, theme="dark"):
    hierarchy = get_hierarchy()
    if framework not in hierarchy:
        return go.Figure()

    h = hierarchy[framework]
    ids, labels, parents, values = h["ids"], h["labels"], h["parents"], h["values"]

    # Filter by entry type if specified
    if entry_types:
        nodes_df = get_nodes_df()
        fw_nodes = nodes_df[nodes_df["framework"] == framework]
        allowed_ids = set(fw_nodes[fw_nodes["entry_type"].isin(entry_types)]["node_id"])

        filtered_ids, filtered_labels, filtered_parents, filtered_values = [], [], [], []
        for i in range(len(ids)):
            node_id = ids[i]
            # Keep root and domain-level entries, plus allowed leaf nodes
            is_leaf = "::" not in node_id and node_id != framework
            if not is_leaf or node_id in allowed_ids:
                filtered_ids.append(node_id)
                filtered_labels.append(labels[i])
                filtered_parents.append(parents[i])
                filtered_values.append(values[i])

        ids, labels, parents, values = filtered_ids, filtered_labels, filtered_parents, filtered_values

    fw_color = get_color(framework)
    fig = go.Figure(go.Sunburst(
        ids=ids,
        labels=labels,
        parents=parents,
        values=values,
        branchvalues="total",
        hovertemplate="<b>%{label}</b><br>%{id}<extra></extra>",
        marker=dict(
            colors=[fw_color if i == 0 else None for i in range(len(ids))],
        ),
        maxdepth=3,
    ))
    fig.update_layout(
        template=get_template(theme),
        height=500,
        title=dict(text=f"{get_display_name(framework)} Hierarchy", font=dict(size=14)),
        margin=dict(t=50, b=10, l=10, r=10),
    )
    return fig


def _build_outbound_bar(framework, theme="dark"):
    edges_df = get_edges_df()
    outbound = edges_df[
        (edges_df["source_framework"] == framework)
        & (edges_df["source_framework"] != edges_df["target_framework"])
    ]

    if outbound.empty:
        # This framework might be target-only; show inbound instead
        inbound = edges_df[
            (edges_df["target_framework"] == framework)
            & (edges_df["source_framework"] != edges_df["target_framework"])
        ]
        if inbound.empty:
            fig = go.Figure()
            fig.update_layout(template=get_template(theme), height=500)
            fig.add_annotation(text="No cross-framework mappings found", showarrow=False)
            return fig

        grouped = inbound.groupby(["source_framework", "confidence"]).size().reset_index(name="count")
        title = f"Inbound Mappings to {get_short_name(framework)}"
        fw_col = "source_framework"
    else:
        grouped = outbound.groupby(["target_framework", "confidence"]).size().reset_index(name="count")
        title = f"Outbound Mappings from {get_short_name(framework)}"
        fw_col = "target_framework"

    conf_order = ["authoritative", "expert", "suggestive", "unvalidated"]
    fig = go.Figure()
    for conf in conf_order:
        subset = grouped[grouped["confidence"] == conf]
        if not subset.empty:
            fig.add_trace(go.Bar(
                y=[get_short_name(fw) for fw in subset[fw_col]],
                x=subset["count"],
                name=conf.capitalize(),
                orientation="h",
                marker_color=CONFIDENCE_COLORS.get(conf, "#6e7681"),
                hovertemplate=f"<b>%{{y}}</b><br>{conf}: %{{x}} mappings<extra></extra>",
            ))

    fig.update_layout(
        template=get_template(theme),
        height=500,
        title=dict(text=title, font=dict(size=14)),
        barmode="stack",
        yaxis=dict(categoryorder="total ascending"),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2),
    )
    return fig


def _build_control_card(node_id):
    node = get_node_by_id(node_id)
    if not node:
        return html.Div()

    badges = []
    if node.get("entry_type"):
        badges.append(dbc.Badge(node["entry_type"], color="secondary", className="me-1"))
    if node.get("function_class"):
        badges.append(dbc.Badge(node["function_class"], color="info", className="me-1"))
    if node.get("domain"):
        badges.append(dbc.Badge(node["domain"], color="dark", className="me-1"))

    return dbc.Card([
        dbc.CardHeader([
            html.Span(get_short_name(node["framework"]),
                      className="badge me-2",
                      style={"backgroundColor": get_color(node["framework"])}),
            html.Strong(f"{node['local_id']}: {node['name']}"),
            html.Div(badges, className="mt-1"),
        ]),
        dbc.CardBody([
            html.P(node.get("description", "No description available."),
                   style={"fontSize": "0.9rem", "lineHeight": "1.6"}),
            html.Div([
                html.Small(f"Frequency: {node['frequency']}", className="text-muted me-3")
                if node.get("frequency") else None,
                html.Small(
                    html.A("View source", href=node["url"], target="_blank", className="text-info"),
                    className="me-3",
                ) if node.get("url") else None,
            ]),
            dbc.Button(
                "View in Crosswalk Explorer",
                id="deep-dive-to-explorer",
                color="info",
                size="sm",
                className="mt-2",
                outline=True,
            ),
            dcc.Store(id="deep-dive-selected-node", data=node_id),
        ]),
    ], className="mt-3", style={"borderLeft": f"4px solid {get_color(node['framework'])}"})


# --- Layout ---
layout = dbc.Container([
    dbc.Row(dbc.Col(
        dbc.Card(dbc.CardBody([
            html.H4("Framework Deep Dive", className="mb-2"),
            html.P(INTRO_TEXT, className="text-muted mb-0", style={"fontSize": "0.9rem"}),
        ]), className="mb-3 border-0",
        style={"backgroundColor": "rgba(22,27,34,0.5)"}),
    )),

    # Controls
    dbc.Row([
        dbc.Col([
            dbc.Label("Select Framework", className="text-muted", style={"fontSize": "0.8rem"}),
            dcc.Dropdown(
                id="deep-dive-framework",
                options=_framework_options(),
                value="aiuc_1",
                clearable=False,
            ),
        ], md=5),
        dbc.Col([
            dbc.Label("Filter Entry Types", className="text-muted", style={"fontSize": "0.8rem"}),
            dcc.Checklist(
                id="deep-dive-entry-types",
                options=[
                    {"label": " control", "value": "control"},
                    {"label": " risk", "value": "risk"},
                    {"label": " technique", "value": "technique"},
                    {"label": " mitigation", "value": "mitigation"},
                    {"label": " activity", "value": "activity"},
                    {"label": " subcategory", "value": "subcategory"},
                ],
                value=[],
                inline=True,
                inputStyle={"marginRight": "4px"},
                labelStyle={"marginRight": "12px", "fontSize": "0.85rem"},
            ),
        ], md=7),
    ], className="mb-3"),

    # Charts
    dbc.Row([
        dbc.Col(dcc.Loading(dcc.Graph(id="deep-dive-sunburst")), md=6),
        dbc.Col(dcc.Loading(dcc.Graph(id="deep-dive-bar")), md=6),
    ]),

    # Control detail card (hidden until click)
    html.Div(id="deep-dive-control-card"),
], fluid=True)


@callback(
    Output("deep-dive-sunburst", "figure"),
    Output("deep-dive-bar", "figure"),
    Input("deep-dive-framework", "value"),
    Input("deep-dive-entry-types", "value"),
    Input("theme-store", "data"),
)
def update_deep_dive(framework, entry_types, theme):
    sunburst = _build_sunburst(framework, entry_types, theme)
    bar = _build_outbound_bar(framework, theme)
    return sunburst, bar


@callback(
    Output("deep-dive-control-card", "children"),
    Input("deep-dive-sunburst", "clickData"),
    prevent_initial_call=True,
)
def show_control_detail(click_data):
    if not click_data or "points" not in click_data:
        return html.Div()
    point = click_data["points"][0]
    node_id = point.get("id", "")
    # Only show card for leaf nodes (actual controls, not domains)
    if "::" in node_id or not node_id:
        return html.Div()
    return _build_control_card(node_id)
