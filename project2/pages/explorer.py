"""Page 3: Crosswalk Explorer -- pick a control, see all cross-framework mappings."""

import math

import dash
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from dash import ALL, Input, Output, State, callback, ctx, dcc, html

from components.data_loader import (
    get_mappings_for_node,
    get_node_by_id,
    get_nodes_for_framework,
)
from components.framework_colors import (
    CONFIDENCE_COLORS,
    CONFIDENCE_LABELS,
    FRAMEWORK_KEYS,
    RATIONALE_LABELS,
    get_color,
    get_display_name,
    get_short_name,
)
from components.plot_theme import get_template

dash.register_page(__name__, path="/explorer", name="Explorer", order=2)

INTRO_TEXT = (
    "Select a framework and control to see all its cross-framework mappings. "
    "Direct mappings are shown first, followed by transitive mappings "
    "that are reached through a bridge control in another framework. "
    "Click any card to expand the full control text and see the bridge path."
)


def _framework_options():
    from components.data_loader import get_framework_stats
    stats = get_framework_stats()
    return [
        {"label": f"{get_display_name(fw)} ({stats[fw]['node_count']})", "value": fw}
        for fw in FRAMEWORK_KEYS
        if fw in stats
    ]


def _build_sankey(mappings, source_node, theme="dark"):
    """Build Sankey: source -> [confidence level] -> target frameworks."""
    direct = mappings.get("direct", [])
    transitive = mappings.get("transitive", [])

    if not direct and not transitive:
        fig = go.Figure()
        fig.update_layout(template=get_template(theme), height=400)
        fig.add_annotation(text="No mappings found for this control", showarrow=False)
        return fig

    # Nodes: source | confidence levels | target frameworks
    all_targets = {}
    for d in direct:
        fw = d["target_framework"]
        all_targets[fw] = all_targets.get(fw, 0) + 1
    for t in transitive:
        fw = t["target_framework"]
        all_targets[fw] = all_targets.get(fw, 0) + 1

    target_fws = sorted(all_targets.keys(), key=lambda fw: all_targets[fw], reverse=True)

    labels = [f"{source_node['local_id']}: {source_node['name'][:30]}"]
    colors = [get_color(source_node["framework"])]
    labels += ["Direct", "Transitive"]
    colors += ["rgba(0,212,255,0.6)", "rgba(143,209,143,0.6)"]
    for fw in target_fws:
        labels.append(get_short_name(fw))
        colors.append(get_color(fw))

    # Links: source -> direct/transitive -> target frameworks
    source_idx = 0
    direct_idx = 1
    trans_idx = 2
    fw_start_idx = 3

    links_src, links_tgt, links_val, links_color = [], [], [], []

    # Count direct per framework
    direct_by_fw = {}
    for d in direct:
        fw = d["target_framework"]
        direct_by_fw[fw] = direct_by_fw.get(fw, 0) + 1

    trans_by_fw = {}
    for t in transitive:
        fw = t["target_framework"]
        trans_by_fw[fw] = trans_by_fw.get(fw, 0) + 1

    # Source -> Direct
    total_direct = sum(direct_by_fw.values())
    if total_direct > 0:
        links_src.append(source_idx)
        links_tgt.append(direct_idx)
        links_val.append(total_direct)
        links_color.append("rgba(0,212,255,0.2)")

    # Source -> Transitive
    total_trans = sum(trans_by_fw.values())
    if total_trans > 0:
        links_src.append(source_idx)
        links_tgt.append(trans_idx)
        links_val.append(total_trans)
        links_color.append("rgba(143,209,143,0.2)")

    # Direct -> target frameworks
    for fw, count in direct_by_fw.items():
        if fw in target_fws:
            links_src.append(direct_idx)
            links_tgt.append(fw_start_idx + target_fws.index(fw))
            links_val.append(count)
            links_color.append("rgba(0,212,255,0.15)")

    # Transitive -> target frameworks
    for fw, count in trans_by_fw.items():
        if fw in target_fws:
            links_src.append(trans_idx)
            links_tgt.append(fw_start_idx + target_fws.index(fw))
            links_val.append(count)
            links_color.append("rgba(143,209,143,0.15)")

    fig = go.Figure(go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            label=labels,
            color=colors,
        ),
        link=dict(
            source=links_src,
            target=links_tgt,
            value=links_val,
            color=links_color,
        ),
    ))
    fig.update_layout(
        template=get_template(theme),
        height=400,
        title=dict(text="Mapping Flow", font=dict(size=14)),
    )
    return fig


def _build_neighborhood(mappings, source_node, theme="dark"):
    """Build local neighborhood graph: source at center, direct neighbors around it."""
    direct = mappings.get("direct", [])
    if not direct:
        fig = go.Figure()
        fig.update_layout(template=get_template(theme), height=400)
        fig.add_annotation(text="No direct mappings to visualize", showarrow=False)
        return fig

    # Limit to top 20 for readability
    display_nodes = direct[:20]
    n = len(display_nodes)

    # Center node
    cx, cy = 0, 0

    # Arrange neighbors in a circle
    traces = []
    for i, d in enumerate(display_nodes):
        angle = 2 * math.pi * i / n - math.pi / 2
        nx_pos = math.cos(angle) * 0.8
        ny_pos = math.sin(angle) * 0.8

        # Edge
        traces.append(go.Scatter(
            x=[cx, nx_pos, None], y=[cy, ny_pos, None],
            mode="lines",
            line=dict(width=1, color="rgba(0,212,255,0.2)"),
            showlegend=False, hoverinfo="skip",
        ))

    # Neighbor nodes
    neighbor_x = [math.cos(2 * math.pi * i / n - math.pi / 2) * 0.8 for i in range(n)]
    neighbor_y = [math.sin(2 * math.pi * i / n - math.pi / 2) * 0.8 for i in range(n)]
    neighbor_colors = [get_color(d["target_framework"]) for d in display_nodes]
    neighbor_text = [
        f"<b>{d.get('target_name', d['target_node_id'])}</b><br>"
        f"Framework: {get_display_name(d['target_framework'])}<br>"
        f"Confidence: {d.get('confidence', 'unknown')}<br>"
        f"Rationale: {d.get('rationale_code', 'unknown')}"
        for d in display_nodes
    ]

    traces.append(go.Scatter(
        x=neighbor_x, y=neighbor_y,
        mode="markers",
        marker=dict(size=14, color=neighbor_colors, line=dict(width=1, color="#21262d")),
        hovertext=neighbor_text,
        hoverinfo="text",
        showlegend=False,
    ))

    # Center node (on top)
    traces.append(go.Scatter(
        x=[cx], y=[cy],
        mode="markers+text",
        marker=dict(
            size=24,
            color=get_color(source_node["framework"]),
            line=dict(width=2, color="#00d4ff"),
        ),
        text=[source_node["local_id"]],
        textposition="middle center",
        textfont=dict(size=9, color="white"),
        hovertext=f"<b>{source_node['local_id']}: {source_node['name']}</b>",
        hoverinfo="text",
        showlegend=False,
    ))

    fig = go.Figure(data=traces)
    fig.update_layout(
        template=get_template(theme),
        height=400,
        title=dict(text="Control Neighborhood (direct mappings)", font=dict(size=14)),
        xaxis=dict(visible=False, range=[-1.2, 1.2]),
        yaxis=dict(visible=False, range=[-1.2, 1.2], scaleanchor="x"),
        hovermode="closest",
    )
    return fig


def _make_badge(text, tooltip_text, badge_id, color="secondary"):
    """Create a badge with a tooltip."""
    badge = dbc.Badge(text, id=badge_id, color=color, className="me-1",
                      style={"cursor": "help"})
    tooltip = dbc.Tooltip(tooltip_text, target=badge_id, placement="top")
    return html.Span([badge, tooltip])


def _build_source_card(node, mappings):
    """Build the pinned source control card with reachability summary."""
    direct = mappings.get("direct", [])
    transitive = mappings.get("transitive", [])

    # Group by framework
    from collections import Counter
    direct_by_fw = Counter(d["target_framework"] for d in direct)
    trans_by_fw = Counter(t["target_framework"] for t in transitive)
    all_fws = sorted(set(list(direct_by_fw.keys()) + list(trans_by_fw.keys())),
                     key=lambda fw: direct_by_fw.get(fw, 0) + trans_by_fw.get(fw, 0),
                     reverse=True)

    summary_items = []
    for fw in all_fws:
        d_count = direct_by_fw.get(fw, 0)
        t_count = trans_by_fw.get(fw, 0)
        parts = []
        if d_count:
            parts.append(f"{d_count} direct")
        if t_count:
            parts.append(f"{t_count} via bridge")
        summary_items.append(
            html.Span([
                html.Span(
                    "\u25cf ",
                    style={"color": get_color(fw)},
                ),
                html.Span(f"{get_short_name(fw)}: ", className="text-muted"),
                html.Span(", ".join(parts), style={"color": "#c9d1d9"}),
            ], className="me-3", style={"fontSize": "0.8rem"})
        )

    return dbc.Card([
        dbc.CardHeader([
            html.Span(get_short_name(node["framework"]),
                      className="badge me-2",
                      style={"backgroundColor": get_color(node["framework"])}),
            html.Strong(f"{node['local_id']}: {node['name']}"),
            html.Span(
                dbc.Badge(node.get("entry_type", ""), color="secondary", className="ms-2"),
            ),
        ]),
        dbc.CardBody([
            html.P(node.get("description", "No description available."),
                   style={"fontSize": "0.9rem", "lineHeight": "1.6"}),
        ]),
        dbc.CardFooter(
            html.Div(summary_items, style={"display": "flex", "flexWrap": "wrap", "gap": "4px"}),
            style={"backgroundColor": "rgba(13,17,23,0.5)"},
        ),
    ], style={"borderLeft": f"4px solid {get_color(node['framework'])}"}, className="mb-3")


def _build_mapping_cards(mappings, source_node):
    """Build framework-grouped expandable control cards."""
    from collections import defaultdict

    direct = mappings.get("direct", [])
    transitive = mappings.get("transitive", [])

    # Group direct by framework
    direct_by_fw = defaultdict(list)
    for d in direct:
        direct_by_fw[d["target_framework"]].append(d)

    # Group transitive by framework
    trans_by_fw = defaultdict(list)
    for t in transitive:
        trans_by_fw[t["target_framework"]].append(t)

    sections = []

    # Direct mappings first
    for fw in sorted(direct_by_fw.keys(), key=lambda f: len(direct_by_fw[f]), reverse=True):
        items = direct_by_fw[fw]
        section_header = html.Div([
            html.Span("\u25a0 ", style={"color": get_color(fw)}),
            html.Strong(get_display_name(fw), style={"fontSize": "0.9rem"}),
            dbc.Badge(f"{len(items)} direct", className="ms-2",
                      style={"backgroundColor": f"{get_color(fw)}33", "color": get_color(fw)}),
        ], className="mb-2 mt-3")
        sections.append(section_header)

        for i, d in enumerate(items):
            target = get_node_by_id(d["target_node_id"])
            card_id = f"direct-{fw}-{i}"
            conf = d.get("confidence", "unknown")
            rationale = d.get("rationale_code", "")

            header = html.Div([
                html.Span(
                    "\u25b6 " if True else "\u25bc ",
                    style={"color": "#6e7681", "cursor": "pointer"},
                ),
                html.Strong(
                    f"{target['local_id']}: {target['name']}" if target else d["target_node_id"],
                    style={"fontSize": "0.85rem"},
                ),
                html.Span([
                    dbc.Badge(conf, color={"authoritative": "success", "expert": "primary",
                              "suggestive": "warning", "unvalidated": "secondary"}.get(conf, "secondary"),
                              className="ms-auto me-1", style={"fontSize": "0.7rem"}),
                    dbc.Badge(rationale, color="dark", className="me-1",
                              style={"fontSize": "0.7rem"}) if rationale else None,
                ], style={"marginLeft": "auto", "display": "flex"}),
            ], className="d-flex align-items-center",
               id={"type": "card-header", "index": card_id},
               style={"cursor": "pointer"})

            body = dbc.Collapse(
                dbc.CardBody([
                    html.P(target.get("description", "No description.") if target else "",
                           style={"fontSize": "0.85rem", "lineHeight": "1.6", "color": "#9eaab8"}),
                    html.Div([
                        html.Small(f"Domain: {target.get('domain', 'N/A')}", className="text-muted me-3") if target else None,
                        html.Small(f"Class: {target.get('function_class', 'N/A')}", className="text-muted me-3") if target and target.get("function_class") else None,
                    ]),
                    # Path indicator
                    html.Div([
                        html.Span(source_node["local_id"],
                                  className="badge",
                                  style={"backgroundColor": get_color(source_node["framework"]), "fontSize": "0.75rem"}),
                        html.Span(" \u2192 ", style={"color": "#00d4ff"}),
                        html.Span(target["local_id"] if target else d["target_node_id"],
                                  className="badge",
                                  style={"backgroundColor": get_color(fw), "fontSize": "0.75rem"}),
                        html.Small(" (direct mapping)", className="text-muted ms-2"),
                    ], className="mt-2 p-2", style={"backgroundColor": "rgba(13,17,23,0.5)", "borderRadius": "4px"}),
                ]),
                id={"type": "card-collapse", "index": card_id},
                is_open=False,
            )

            sections.append(
                dbc.Card([
                    dbc.CardHeader(header, className="py-2"),
                    body,
                ], className="mb-1", style={"borderLeft": f"4px solid {get_color(fw)}"})
            )

    # Transitive mappings
    for fw in sorted(trans_by_fw.keys(), key=lambda f: len(trans_by_fw[f]), reverse=True):
        items = trans_by_fw[fw]
        section_header = html.Div([
            html.Span("\u25a0 ", style={"color": get_color(fw)}),
            html.Strong(get_display_name(fw), style={"fontSize": "0.9rem"}),
            dbc.Badge(f"{len(items)} via bridge", className="ms-2",
                      style={"backgroundColor": f"{get_color(fw)}33", "color": get_color(fw)}),
            html.Small(f" through {get_short_name(items[0].get('bridge_framework', ''))}", className="text-muted ms-1"),
        ], className="mb-2 mt-3")
        sections.append(section_header)

        for i, t in enumerate(items[:30]):  # Limit to 30 per framework for performance
            target = get_node_by_id(t["target_node_id"])
            card_id = f"trans-{fw}-{i}"

            header = html.Div([
                html.Span("\u25b6 ", style={"color": "#6e7681", "cursor": "pointer"}),
                html.Strong(
                    f"{target['local_id']}: {target['name']}" if target else t["target_node_id"],
                    style={"fontSize": "0.85rem"},
                ),
                html.Span([
                    dbc.Badge("transitive", color="dark", className="ms-auto me-1",
                              style={"fontSize": "0.7rem", "color": get_color(fw)}),
                    html.Small(f"via {t.get('bridge_node_id', '').split(':')[-1]}",
                               className="text-muted"),
                ], style={"marginLeft": "auto", "display": "flex", "alignItems": "center"}),
            ], className="d-flex align-items-center",
               id={"type": "card-header", "index": card_id},
               style={"cursor": "pointer"})

            bridge_name = t.get("bridge_node_name", t.get("bridge_node_id", ""))
            bridge_id_short = t.get("bridge_node_id", "").split(":")[-1] if t.get("bridge_node_id") else ""

            body = dbc.Collapse(
                dbc.CardBody([
                    html.P(target.get("description", "No description.") if target else "",
                           style={"fontSize": "0.85rem", "lineHeight": "1.6", "color": "#9eaab8"}),
                    # Bridge path visualization
                    html.Div([
                        html.Small("BRIDGE PATH", className="text-muted d-block mb-1",
                                   style={"fontSize": "0.7rem"}),
                        html.Div([
                            html.Span(source_node["local_id"], className="badge",
                                      style={"backgroundColor": get_color(source_node["framework"]), "fontSize": "0.75rem"}),
                            html.Div([
                                html.Span(" \u2192 ", style={"color": "#00d4ff"}),
                                html.Small(t.get("bridge_rationale", ""), className="text-muted"),
                            ], style={"display": "flex", "flexDirection": "column", "alignItems": "center"}),
                            html.Span([
                                html.Span(bridge_id_short, className="badge",
                                          style={"backgroundColor": get_color(t.get("bridge_framework", "")), "fontSize": "0.75rem"}),
                                html.Br(),
                                html.Small(bridge_name[:40], className="text-muted",
                                           style={"fontSize": "0.7rem"}),
                            ]),
                            html.Div([
                                html.Span(" \u2192 ", style={"color": "#00d4ff"}),
                                html.Small(t.get("hop2_rationale", ""), className="text-muted"),
                            ], style={"display": "flex", "flexDirection": "column", "alignItems": "center"}),
                            html.Span(target["local_id"] if target else t["target_node_id"],
                                      className="badge",
                                      style={"backgroundColor": get_color(fw), "fontSize": "0.75rem"}),
                        ], style={"display": "flex", "alignItems": "center", "gap": "8px", "flexWrap": "wrap"}),
                    ], className="mt-2 p-2", style={"backgroundColor": "rgba(13,17,23,0.5)", "borderRadius": "6px",
                                                     "border": "1px solid #21262d"}),
                ]),
                id={"type": "card-collapse", "index": card_id},
                is_open=False,
            )

            sections.append(
                dbc.Card([
                    dbc.CardHeader(header, className="py-2"),
                    body,
                ], className="mb-1", style={"borderLeft": f"4px solid {get_color(fw)}"})
            )

        if len(items) > 30:
            sections.append(html.Div(
                f"+ {len(items) - 30} more {get_display_name(fw)} controls",
                className="text-center text-muted my-2",
                style={"fontSize": "0.8rem", "border": "1px dashed #21262d",
                       "borderRadius": "6px", "padding": "8px"},
            ))

    return html.Div(sections)


def _build_mitigation_section(node):
    """Build the mitigation text section if the source has mitigation_text."""
    mit = node.get("mitigation_text")
    if not mit:
        return html.Div()

    return dbc.Card([
        dbc.CardHeader([
            html.Span("\U0001f6e1\ufe0f", className="me-2", title="Recommended mitigations from the source framework"),
            html.Strong("Recommended Mitigations"),
            html.Small(f" (from {get_short_name(node['framework'])} source)", className="text-muted ms-2"),
        ]),
        dbc.CardBody(
            html.P(mit, style={"fontSize": "0.85rem", "lineHeight": "1.6", "color": "#9eaab8"}),
        ),
    ], className="mt-3", style={"borderLeft": f"4px solid {get_color(node['framework'])}"})


# --- Layout ---
layout = dbc.Container([
    dbc.Row(dbc.Col(
        dbc.Card(dbc.CardBody([
            html.H4("Crosswalk Explorer", className="mb-2"),
            html.P(INTRO_TEXT, className="text-muted mb-0", style={"fontSize": "0.9rem"}),
        ]), className="mb-3 border-0",
        style={"backgroundColor": "rgba(22,27,34,0.5)"}),
    )),

    # Controls
    dbc.Row([
        dbc.Col([
            dbc.Label("Source Framework", className="text-muted", style={"fontSize": "0.8rem"}),
            dcc.Dropdown(
                id="explorer-framework",
                options=_framework_options(),
                value="owasp_agentic",
                clearable=False,
            ),
        ], md=3),
        dbc.Col([
            dbc.Label("Select Control (searchable)", className="text-muted", style={"fontSize": "0.8rem"}),
            dcc.Dropdown(
                id="explorer-control",
                options=[],
                value=None,
                clearable=False,
                searchable=True,
                placeholder="Select a control...",
            ),
        ], md=4),
        dbc.Col([
            dbc.Label("Mapping Filter", className="text-muted", style={"fontSize": "0.8rem"}),
            dcc.RadioItems(
                id="explorer-mapping-filter",
                options=[
                    {"label": "All", "value": "all"},
                    {"label": "Direct only", "value": "direct"},
                    {"label": "Transitive only", "value": "transitive"},
                ],
                value="all",
                inline=True,
                inputStyle={"marginRight": "4px"},
                labelStyle={"marginRight": "12px", "fontSize": "0.85rem"},
            ),
        ], md=3),
        dbc.Col([
            dbc.Label("Search Controls", className="text-muted", style={"fontSize": "0.8rem"}),
            dcc.Input(
                id="explorer-search",
                type="text",
                placeholder="Filter by keyword...",
                debounce=True,
                className="form-control",
            ),
        ], md=2),
    ], className="mb-3"),

    # Charts
    dbc.Row([
        dbc.Col(dcc.Loading(dcc.Graph(id="explorer-sankey", config={"displayModeBar": False})), md=6),
        dbc.Col(dcc.Loading(dcc.Graph(id="explorer-neighborhood", config={"displayModeBar": False})), md=6),
    ]),

    # Source control card
    html.Div(id="explorer-source-card"),

    # Mapping cards
    html.Div(id="explorer-mapping-cards"),

    # Mitigation section
    html.Div(id="explorer-mitigation"),

], fluid=True)


@callback(
    Output("explorer-control", "options"),
    Output("explorer-control", "value"),
    Input("explorer-framework", "value"),
)
def update_control_options(framework):
    """Chained callback: framework selection updates control dropdown."""
    if not framework:
        return [], None
    df = get_nodes_for_framework(framework)
    options = [
        {"label": f"{row['local_id']}: {row['name'][:60]}", "value": row["node_id"]}
        for _, row in df.sort_values("local_id").iterrows()
    ]
    default = options[0]["value"] if options else None
    return options, default


@callback(
    Output("explorer-sankey", "figure"),
    Output("explorer-neighborhood", "figure"),
    Output("explorer-source-card", "children"),
    Output("explorer-mapping-cards", "children"),
    Output("explorer-mitigation", "children"),
    Input("explorer-control", "value"),
    Input("explorer-mapping-filter", "value"),
    Input("explorer-search", "value"),
    Input("theme-store", "data"),
)
def update_explorer(node_id, mapping_filter, search_text, theme):
    if not node_id:
        empty = go.Figure()
        return empty, empty, html.Div(), html.Div(), html.Div()

    node = get_node_by_id(node_id)
    if not node:
        empty = go.Figure()
        return empty, empty, html.Div(), html.Div(), html.Div()

    mappings = get_mappings_for_node(node_id)

    # Apply mapping filter
    filtered = dict(mappings)
    if mapping_filter == "direct":
        filtered["transitive"] = []
    elif mapping_filter == "transitive":
        filtered["direct"] = []

    # Apply search filter
    if search_text:
        search_lower = search_text.lower()
        filtered["direct"] = [
            d for d in filtered["direct"]
            if search_lower in d.get("target_name", "").lower()
            or search_lower in (get_node_by_id(d["target_node_id"]) or {}).get("description", "").lower()
        ]
        filtered["transitive"] = [
            t for t in filtered["transitive"]
            if search_lower in t.get("target_name", "").lower()
            or search_lower in (get_node_by_id(t["target_node_id"]) or {}).get("description", "").lower()
        ]

    sankey = _build_sankey(filtered, node, theme)
    neighborhood = _build_neighborhood(filtered, node, theme)
    source_card = _build_source_card(node, filtered)
    mapping_cards = _build_mapping_cards(filtered, node)
    mitigation = _build_mitigation_section(node)

    return sankey, neighborhood, source_card, mapping_cards, mitigation


@callback(
    Output({"type": "card-collapse", "index": ALL}, "is_open"),
    Input({"type": "card-header", "index": ALL}, "n_clicks"),
    State({"type": "card-collapse", "index": ALL}, "is_open"),
    prevent_initial_call=True,
)
def toggle_card(n_clicks, is_open):
    """Toggle card expand/collapse on header click."""
    if not ctx.triggered_id:
        return [dash.no_update] * len(is_open)

    triggered_index = ctx.triggered_id["index"]

    # Pattern-matching: return new state for ALL matched components.
    # Toggle the one that was clicked, leave others unchanged.
    result = []
    for i, state in enumerate(is_open):
        # ctx.inputs_list[0][i] has the id dict for each matched input
        if ctx.inputs_list[0][i]["id"]["index"] == triggered_index:
            result.append(not state)
        else:
            result.append(dash.no_update)
    return result
