"""Page 3: Crosswalk Explorer -- pick a control, see all cross-framework mappings."""

import math

import dash
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from dash import ALL, Input, Output, State, callback, ctx, dcc, html

from components.badge_tooltips import badge_with_tooltip
from components.data_loader import (
    get_mappings_for_node,
    get_node_by_id,
    get_nodes_for_framework,
)
from components.framework_colors import (
    FRAMEWORK_KEYS,
    RATIONALE_LABELS,
    get_color,
    get_display_name,
    get_short_name,
)
from components.plot_theme import get_template

dash.register_page(__name__, path="/explorer", name="Explorer", order=2)

INTRO_TEXT = (
    "Pick any control from any framework and instantly see every related control, "
    "risk, or technique across all nine standards. The Sankey diagram on the left shows "
    "mapping flow; the neighborhood graph on the right shows the control's local connectivity."
)

LEARN_MORE_CONTENT = [
    html.H6("How Crosswalk Mapping Works", className="mt-2 mb-1", style={"color": "#00d4ff"}),
    html.P(
        "Each control in a security framework addresses a specific concern: preventing unauthorized access, "
        "detecting adversarial inputs, governing model deployment. When two controls in different frameworks "
        "address the same concern, a cross-framework edge connects them. These edges carry two metadata signals: "
        "a confidence level (how rigorously the mapping was validated) and a rationale code (the type of "
        "relationship: SCOPE, DETECT, ISOLATE, GOVERN, etc.).",
        style={"fontSize": "0.85rem", "lineHeight": "1.7", "color": "#9eaab8"},
    ),
    html.H6("Direct vs. Transitive Mappings", className="mt-2 mb-1", style={"color": "#00d4ff"}),
    html.P([
        html.Strong("Direct (1-hop): ", style={"color": "#c9d1d9"}),
        "A direct edge exists between two controls. For example, OWASP Agentic ASI02 (Tool Misuse) maps directly "
        "to 11 AIUC-1 controls that address tool security. These are the highest-confidence mappings.",
        html.Br(), html.Br(),
        html.Strong("Transitive (2-hop): ", style={"color": "#c9d1d9"}),
        "No direct edge exists, but a path goes through a bridge control in a third framework. "
        "ASI02 maps to AIUC-1 B006, and B006 maps to CSA AICM CSA-AIS-04. So ASI02 reaches CSA-AIS-04 "
        "transitively through B006. This is analogous to finding connecting flights between airports that "
        "have no direct route. The bridge path is shown when you expand any transitive card.",
    ], style={"fontSize": "0.85rem", "lineHeight": "1.7", "color": "#9eaab8"}),
    html.H6("Reading the Visualizations", className="mt-2 mb-1", style={"color": "#00d4ff"}),
    html.P([
        html.Strong("Sankey diagram: ", style={"color": "#c9d1d9"}),
        "Flow width encodes mapping count. The source control feeds into Direct and Transitive tiers, "
        "which then fan out to each target framework. Wider flows mean more mappings to that framework.",
        html.Br(), html.Br(),
        html.Strong("Neighborhood graph: ", style={"color": "#c9d1d9"}),
        "Circles on the inner ring are direct mappings. Diamonds on the outer ring are representative transitive "
        "mappings (one per target framework). Colors match the framework color palette used throughout the app.",
    ], style={"fontSize": "0.85rem", "lineHeight": "1.7", "color": "#9eaab8"}),
]


def _framework_options():
    from components.data_loader import get_framework_stats
    stats = get_framework_stats()
    return [
        {"label": f"{get_display_name(fw)} ({stats[fw]['node_count']})", "value": fw}
        for fw in FRAMEWORK_KEYS
        if fw in stats
    ]


def _build_sankey(mappings, source_node, theme="dark"):
    """Build Sankey: source -> [confidence level] -> target frameworks.

    Encoding: flow width encodes mapping count (conventional Sankey).
    Two-category color (cyan = direct, green = transitive) distinguishes
    mapping types. Per-framework target colors use the global categorical
    palette (Graze & Schwabish 2024). Sankey is the standard chart type
    for showing flow between discrete categories.
    """
    direct = mappings.get("direct", [])
    transitive = mappings.get("transitive", [])

    if not direct and not transitive:
        fig = go.Figure()
        fig.update_layout(template=get_template(theme), height=550)
        fig.add_annotation(
            text="No cross-framework mappings exist for this control in the dataset.<br>"
                 "<span style='font-size:11px;color:#6e7681'>This control may not have been mapped to other frameworks yet.</span>",
            showarrow=False,
            font=dict(size=13, color="#9eaab8"),
        )
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

    labels = [f"{source_node['local_id']}: {source_node['name'][:50]}"]
    colors = [get_color(source_node["framework"])]
    customdata = [source_node["framework"]]
    labels += ["Direct", "Transitive"]
    colors += ["rgba(0,212,255,0.6)", "rgba(143,209,143,0.6)"]
    customdata += ["__direct__", "__transitive__"]
    for fw in target_fws:
        labels.append(get_short_name(fw))
        colors.append(get_color(fw))
        customdata.append(fw)

    # Links: source -> direct/transitive -> target frameworks
    source_idx = 0
    direct_idx = 1
    trans_idx = 2
    fw_start_idx = 3

    links_src, links_tgt, links_val, links_color, links_customdata = [], [], [], [], []

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
        links_customdata.append(None)

    # Source -> Transitive
    total_trans = sum(trans_by_fw.values())
    if total_trans > 0:
        links_src.append(source_idx)
        links_tgt.append(trans_idx)
        links_val.append(total_trans)
        links_color.append("rgba(143,209,143,0.2)")
        links_customdata.append(None)

    # Direct -> target frameworks
    for fw, count in direct_by_fw.items():
        if fw in target_fws:
            links_src.append(direct_idx)
            links_tgt.append(fw_start_idx + target_fws.index(fw))
            links_val.append(count)
            links_color.append("rgba(0,212,255,0.15)")
            links_customdata.append(fw)

    # Transitive -> target frameworks
    for fw, count in trans_by_fw.items():
        if fw in target_fws:
            links_src.append(trans_idx)
            links_tgt.append(fw_start_idx + target_fws.index(fw))
            links_val.append(count)
            links_color.append("rgba(143,209,143,0.15)")
            links_customdata.append(fw)

    fig = go.Figure(go.Sankey(
        arrangement="fixed",
        node=dict(
            pad=15,
            thickness=20,
            label=labels,
            color=colors,
            customdata=customdata,
        ),
        link=dict(
            source=links_src,
            target=links_tgt,
            value=links_val,
            color=links_color,
            customdata=links_customdata,
        ),
    ))
    fig.update_layout(
        template=get_template(theme),
        height=550,
        title=dict(text="Mapping Flow", font=dict(size=14)),
    )
    return fig


def _build_neighborhood(mappings, source_node, theme="dark"):
    """Build local neighborhood graph: source at center, neighbors radiating outward.

    Shows both direct (inner ring, solid edges) and transitive (outer ring, dashed edges).

    Encoding: categorical framework colors for nominal identity (Borner et al.
    2019). Shape encodes mapping type: circles = direct, diamonds = transitive
    (Borner: shape for categorical distinction). Dual-ring layout separates
    direct (inner, solid edges) from transitive (outer, dashed edges) using
    both position and line style as redundant channels.
    """
    direct = mappings.get("direct", [])
    transitive = mappings.get("transitive", [])

    if not direct and not transitive:
        fig = go.Figure()
        fig.update_layout(template=get_template(theme), height=550)
        fig.add_annotation(
            text="No cross-framework mappings exist for this control in the dataset.<br>"
                 "<span style='font-size:11px;color:#6e7681'>This control may not have been mapped to other frameworks yet.</span>",
            showarrow=False,
            font=dict(size=13, color="#9eaab8"),
        )
        return fig

    traces = []
    cx, cy = 0, 0

    # --- Direct neighbors: inner ring at radius 0.55 ---
    direct_nodes = direct[:20]
    n_direct = len(direct_nodes)
    if n_direct > 0:
        for i, d in enumerate(direct_nodes):
            angle = 2 * math.pi * i / n_direct - math.pi / 2
            nx_pos = math.cos(angle) * 0.55
            ny_pos = math.sin(angle) * 0.55
            traces.append(go.Scatter(
                x=[cx, nx_pos, None], y=[cy, ny_pos, None],
                mode="lines",
                line=dict(width=1.5, color="rgba(0,212,255,0.3)"),
                showlegend=False, hoverinfo="skip",
            ))

        d_x = [math.cos(2 * math.pi * i / n_direct - math.pi / 2) * 0.55 for i in range(n_direct)]
        d_y = [math.sin(2 * math.pi * i / n_direct - math.pi / 2) * 0.55 for i in range(n_direct)]
        traces.append(go.Scatter(
            x=d_x, y=d_y,
            mode="markers",
            marker=dict(size=14, color=[get_color(d["target_framework"]) for d in direct_nodes],
                        line=dict(width=1, color="#21262d")),
            hovertext=[
                f"<b>{d.get('target_name', d['target_node_id'])}</b><br>"
                f"Framework: {get_display_name(d['target_framework'])}<br>"
                f"Confidence: {d.get('confidence', 'unknown')}<br>"
                f"Rationale: {d.get('rationale_code', 'unknown')}<br>"
                f"<i>Click to view detail</i>"
                for d in direct_nodes
            ],
            hoverinfo="text",
            customdata=[d["target_node_id"] for d in direct_nodes],
            showlegend=False,
            name="Direct",
        ))

    # --- Transitive neighbors: outer ring at radius 1.0 ---
    # Deduplicate by target framework, show up to 16
    seen_trans_fws = {}
    for t in transitive:
        fw = t["target_framework"]
        if fw not in seen_trans_fws:
            seen_trans_fws[fw] = t
        if len(seen_trans_fws) >= 16:
            break

    trans_nodes = list(seen_trans_fws.values())
    n_trans = len(trans_nodes)
    if n_trans > 0:
        for i, t in enumerate(trans_nodes):
            angle = 2 * math.pi * i / n_trans - math.pi / 2
            nx_pos = math.cos(angle) * 1.0
            ny_pos = math.sin(angle) * 1.0
            traces.append(go.Scatter(
                x=[cx, nx_pos, None], y=[cy, ny_pos, None],
                mode="lines",
                line=dict(width=1, color="rgba(143,209,143,0.2)", dash="dot"),
                showlegend=False, hoverinfo="skip",
            ))

        t_x = [math.cos(2 * math.pi * i / n_trans - math.pi / 2) * 1.0 for i in range(n_trans)]
        t_y = [math.sin(2 * math.pi * i / n_trans - math.pi / 2) * 1.0 for i in range(n_trans)]
        traces.append(go.Scatter(
            x=t_x, y=t_y,
            mode="markers",
            marker=dict(size=10, color=[get_color(t["target_framework"]) for t in trans_nodes],
                        line=dict(width=1, color="#21262d"), symbol="diamond"),
            hovertext=[
                f"<b>{t.get('target_name', t['target_node_id'])}</b><br>"
                f"Framework: {get_display_name(t['target_framework'])}<br>"
                f"Via bridge: {t.get('bridge_node_name', '')[:40]}<br>"
                f"<i>Click to view detail</i>"
                for t in trans_nodes
            ],
            hoverinfo="text",
            customdata=[t["target_node_id"] for t in trans_nodes],
            showlegend=False,
            name="Transitive",
        ))

    # --- Center node (on top) ---
    traces.append(go.Scatter(
        x=[cx], y=[cy],
        mode="markers+text",
        marker=dict(size=24, color=get_color(source_node["framework"]),
                    line=dict(width=2, color="#00d4ff")),
        text=[source_node["local_id"]],
        textposition="middle center",
        textfont=dict(size=9, color="white"),
        hovertext=f"<b>{source_node['local_id']}: {source_node['name']}</b>",
        hoverinfo="text",
        showlegend=False,
    ))

    # Title reflects what's shown
    parts = []
    if direct_nodes:
        parts.append(f"{len(direct_nodes)} direct")
    if trans_nodes:
        parts.append(f"{len(trans_nodes)} transitive")
    title_text = f"Control Neighborhood ({', '.join(parts)})"

    fig = go.Figure(data=traces)
    fig.update_layout(
        template=get_template(theme),
        height=550,
        title=dict(text=title_text, font=dict(size=14)),
        xaxis=dict(visible=False, range=[-1.4, 1.4]),
        yaxis=dict(visible=False, range=[-1.4, 1.4], scaleanchor="x"),
        hovermode="closest",
        dragmode="pan",
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
                badge_with_tooltip(node.get("entry_type", ""), color="secondary", class_name="ms-2"),
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
                    badge_with_tooltip(
                        conf,
                        color={"authoritative": "success", "expert": "primary",
                               "suggestive": "warning", "unvalidated": "secondary"}.get(conf, "secondary"),
                        class_name="ms-auto me-1",
                    ),
                    badge_with_tooltip(rationale, color="dark") if rationale else None,
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
                    badge_with_tooltip(
                        "transitive",
                        color="dark",
                        class_name="ms-auto me-1",
                        style={"color": get_color(fw)},
                    ),
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
            html.P(INTRO_TEXT, className="text-muted mb-2", style={"fontSize": "0.9rem"}),
            html.A("Learn more about crosswalk mapping", id="explorer-learn-toggle",
                   style={"fontSize": "0.85rem", "cursor": "pointer", "color": "#00d4ff",
                          "textDecoration": "none"}),
            dbc.Collapse(html.Div(LEARN_MORE_CONTENT, className="mt-2"),
                         id="explorer-learn-more", is_open=False),
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

    # Sankey click filter store
    dcc.Store(id="explorer-sankey-fw-filter", data=None),

    # Raw Sankey click events (from assets/sankey_click.js, includes counter for repeated clicks)
    dcc.Store(id="explorer-sankey-click-store", data=None),

    # Pending control from URL params (set by handle_url_params, consumed by apply_pending_control)
    dcc.Store(id="explorer-pending-control", data=None),

    # Charts (full-width stacked)
    dbc.Row(dbc.Col(dcc.Loading(dcc.Graph(
        id="explorer-sankey",
        config={"displayModeBar": False},
    )))),

    # Framework filter (reliable alternative to Sankey click)
    dbc.Row(dbc.Col([
        dbc.Label([
            "Filter by target framework ",
            html.Small("(or click a framework in the Sankey above)", className="text-muted"),
        ], className="text-muted", style={"fontSize": "0.8rem"}),
        dcc.Dropdown(
            id="explorer-fw-filter",
            options=[],
            value=[],
            multi=True,
            clearable=True,
            placeholder="All frameworks (click Sankey flows to filter)",
        ),
    ], md=6), className="mb-3 mt-2"),

    dbc.Row(dbc.Col(dcc.Loading(dcc.Graph(
        id="explorer-neighborhood",
        config={
            "scrollZoom": True,
            "displayModeBar": True,
            "modeBarButtonsToRemove": ["select2d", "lasso2d", "autoScale2d"],
            "displaylogo": False,
        },
    ))), className="mt-2"),

    # Neighborhood click detail
    html.Div(id="explorer-neighborhood-detail", className="mt-3"),

    # Status counter
    html.Div(id="explorer-status", className="mb-3"),

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
    Output("explorer-framework", "value", allow_duplicate=True),
    Output("explorer-pending-control", "data"),
    Input("url", "search"),
    prevent_initial_call="initial_duplicate",
)
def handle_url_params(search):
    """Read URL query parameters to pre-select framework and control."""
    if not search:
        return dash.no_update, dash.no_update
    from urllib.parse import parse_qs
    params = parse_qs(search.lstrip("?"))
    framework = params.get("framework", [None])[0]
    control = params.get("control", [None])[0]
    if not framework:
        return dash.no_update, dash.no_update
    return framework, control


@callback(
    Output("explorer-control", "value", allow_duplicate=True),
    Input("explorer-control", "options"),
    State("explorer-pending-control", "data"),
    prevent_initial_call=True,
)
def apply_pending_control(options, pending_control):
    """After control options are populated, select the pending control from URL params."""
    if not pending_control or not options:
        return dash.no_update
    available = {opt["value"] for opt in options}
    if pending_control in available:
        return pending_control
    return dash.no_update


@callback(
    Output("explorer-sankey", "figure"),
    Output("explorer-neighborhood", "figure"),
    Output("explorer-status", "children"),
    Output("explorer-source-card", "children"),
    Output("explorer-mapping-cards", "children"),
    Output("explorer-mitigation", "children"),
    Output("explorer-sankey-fw-filter", "data"),
    Output("explorer-fw-filter", "options"),
    Output("explorer-fw-filter", "value"),
    Input("explorer-control", "value"),
    Input("explorer-mapping-filter", "value"),
    Input("explorer-search", "value"),
    Input("theme-store", "data"),
)
def update_explorer(node_id, mapping_filter, search_text, theme):
    if not node_id:
        empty = go.Figure()
        return empty, empty, html.Div(), html.Div(), html.Div(), html.Div(), None, [], []

    node = get_node_by_id(node_id)
    if not node:
        empty = go.Figure()
        return empty, empty, html.Div(), html.Div(), html.Div(), html.Div(), None, [], []

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

    n_direct = len(filtered["direct"])
    n_trans = len(filtered["transitive"])
    total = n_direct + n_trans

    # Status counter
    status_parts = []
    if n_direct:
        status_parts.append(html.Span([
            html.Strong(f"{n_direct}", style={"color": "#00d4ff"}),
            html.Span(" direct", className="text-muted"),
        ]))
    if n_trans:
        if status_parts:
            status_parts.append(html.Span(" + ", className="text-muted"))
        status_parts.append(html.Span([
            html.Strong(f"{n_trans}", style={"color": "#8fd18f"}),
            html.Span(" transitive", className="text-muted"),
        ]))
    status_parts.append(html.Span(f" = {total} mapped controls", className="text-muted"))

    filter_label = {"all": "All mappings", "direct": "Direct only", "transitive": "Transitive only"}
    status = html.Div([
        html.Span(filter_label.get(mapping_filter, "All"), className="badge me-2",
                  style={"backgroundColor": "#30363d", "color": "#c9d1d9", "fontSize": "0.75rem"}),
        *status_parts,
    ], style={"fontSize": "0.85rem", "padding": "8px 12px",
              "backgroundColor": "rgba(22,27,34,0.5)", "borderRadius": "6px",
              "border": "1px solid #21262d"})

    sankey = _build_sankey(filtered, node, theme)
    neighborhood = _build_neighborhood(filtered, node, theme)
    source_card = _build_source_card(node, filtered)
    mapping_cards = _build_mapping_cards(filtered, node)
    mitigation = _build_mitigation_section(node)

    # Compute target framework options for the filter dropdown
    target_fw_set = set()
    for d in filtered["direct"]:
        target_fw_set.add(d["target_framework"])
    for t in filtered["transitive"]:
        target_fw_set.add(t["target_framework"])
    fw_filter_options = [
        {"label": get_display_name(fw), "value": fw}
        for fw in sorted(target_fw_set, key=lambda fw: get_display_name(fw))
    ]

    return sankey, neighborhood, status, source_card, mapping_cards, mitigation, None, fw_filter_options, []


@callback(
    Output("explorer-fw-filter", "value", allow_duplicate=True),
    Input("explorer-sankey-click-store", "data"),
    State("explorer-fw-filter", "value"),
    State("explorer-control", "value"),
    prevent_initial_call=True,
)
def sankey_click_toggle_filter(click_event, current_selection, node_id):
    """Toggle a framework in/out of the filter when the user clicks a Sankey flow or node.

    Uses explorer-sankey-click-store (written by assets/sankey_click.js) instead
    of clickData so that repeated clicks on the same element still fire.
    """
    if not click_event or not node_id:
        return dash.no_update

    current_selection = current_selection or []

    # Extract framework key from the click event
    clicked_fw = None

    # Link click: customdata or targetCustomdata hold the fw key
    for key in ("customdata", "targetCustomdata"):
        val = click_event.get(key)
        if val and val in FRAMEWORK_KEYS:
            clicked_fw = val
            break

    # Node click: label matches a framework short name
    if not clicked_fw:
        label = click_event.get("label", "")
        if label and label not in ("Direct", "Transitive"):
            short_to_fw = {get_short_name(fw): fw for fw in FRAMEWORK_KEYS}
            clicked_fw = short_to_fw.get(label)

    if not clicked_fw:
        return dash.no_update

    # Toggle: remove if already selected, add if not
    if clicked_fw in current_selection:
        return [fw for fw in current_selection if fw != clicked_fw]
    else:
        return current_selection + [clicked_fw]


@callback(
    Output("explorer-sankey", "figure", allow_duplicate=True),
    Input("explorer-fw-filter", "value"),
    State("explorer-sankey", "figure"),
    prevent_initial_call=True,
)
def highlight_sankey_links(selected_fws, current_figure):
    """Highlight selected framework flows in the Sankey and dim the rest."""
    if not current_figure or "data" not in current_figure:
        return dash.no_update

    selected_fws = selected_fws or []
    trace = current_figure["data"][0] if current_figure["data"] else None
    if not trace or "link" not in trace:
        return dash.no_update

    link = trace["link"]
    node = trace["node"]
    link_customdata = link.get("customdata", [])
    link_sources = link.get("source", [])
    node_customdata = node.get("customdata", [])
    node_colors = node.get("color", [])

    # Determine original link type from source index (1=Direct cyan, 2=Transitive green)
    new_link_colors = []
    for i, fw in enumerate(link_customdata):
        src = link_sources[i] if i < len(link_sources) else 0
        is_cyan = (src != 2)  # Source->Direct or Direct->fw
        base = (0, 212, 255) if is_cyan else (143, 209, 143)

        if not selected_fws:
            # No selection: default opacity
            alpha = 0.2 if fw is None else 0.15
        elif fw is None:
            # Intermediate link (Source->Direct or Source->Transitive): medium
            alpha = 0.12
        elif fw in selected_fws:
            # Selected: bright
            alpha = 0.55
        else:
            # Unselected: very dim
            alpha = 0.03

        new_link_colors.append(f"rgba({base[0]},{base[1]},{base[2]},{alpha})")

    # Update node colors: restore originals when no selection, dim unselected, brighten selected
    new_node_colors = list(node_colors)
    for i, cd in enumerate(node_customdata):
        if i < 3:
            continue  # Source, Direct, Transitive nodes: always keep original
        if cd and cd in FRAMEWORK_KEYS:
            if not selected_fws or cd in selected_fws:
                new_node_colors[i] = get_color(cd)
            else:
                new_node_colors[i] = "rgba(60,60,60,0.3)"

    patched = current_figure.copy()
    patched["data"] = [dict(trace)]
    patched["data"][0]["link"] = dict(link, color=new_link_colors)
    patched["data"][0]["node"] = dict(node, color=new_node_colors)
    return patched


@callback(
    Output("explorer-neighborhood", "figure", allow_duplicate=True),
    Output("explorer-status", "children", allow_duplicate=True),
    Output("explorer-mapping-cards", "children", allow_duplicate=True),
    Input("explorer-fw-filter", "value"),
    State("explorer-control", "value"),
    State("explorer-mapping-filter", "value"),
    State("explorer-search", "value"),
    State("theme-store", "data"),
    prevent_initial_call=True,
)
def filter_by_framework(target_fws, node_id, mapping_filter, search_text, theme):
    """Filter neighborhood graph and mapping cards to selected target frameworks."""
    if not node_id:
        return dash.no_update, dash.no_update, dash.no_update

    node = get_node_by_id(node_id)
    if not node:
        return dash.no_update, dash.no_update, dash.no_update

    target_fws = target_fws or []

    mappings = get_mappings_for_node(node_id)
    filtered = dict(mappings)
    if mapping_filter == "direct":
        filtered["transitive"] = []
    elif mapping_filter == "transitive":
        filtered["direct"] = []
    if search_text:
        search_lower = search_text.lower()
        filtered["direct"] = [d for d in filtered["direct"] if search_lower in d.get("target_name", "").lower() or search_lower in (get_node_by_id(d["target_node_id"]) or {}).get("description", "").lower()]
        filtered["transitive"] = [t for t in filtered["transitive"] if search_lower in t.get("target_name", "").lower() or search_lower in (get_node_by_id(t["target_node_id"]) or {}).get("description", "").lower()]

    # If no filter selected, show all
    if not target_fws:
        n_direct = len(filtered["direct"])
        n_trans = len(filtered["transitive"])
        total = n_direct + n_trans
        status = html.Div([
            html.Span("All frameworks", className="badge me-2",
                      style={"backgroundColor": "#30363d", "color": "#c9d1d9", "fontSize": "0.75rem"}),
            html.Strong(f"{total}", style={"color": "#00d4ff"}),
            html.Span(" mapped controls", className="text-muted"),
        ], style={"fontSize": "0.85rem", "padding": "8px 12px",
                  "backgroundColor": "rgba(22,27,34,0.5)", "borderRadius": "6px",
                  "border": "1px solid #21262d"})
        neighborhood = _build_neighborhood(filtered, node, theme)
        mapping_cards = _build_mapping_cards(filtered, node)
        return neighborhood, status, mapping_cards

    # Filter to selected frameworks
    fw_set = set(target_fws)
    fw_filtered = {
        "direct": [d for d in filtered["direct"] if d["target_framework"] in fw_set],
        "transitive": [t for t in filtered["transitive"] if t["target_framework"] in fw_set],
    }

    n_direct = len(fw_filtered["direct"])
    n_trans = len(fw_filtered["transitive"])
    total = n_direct + n_trans

    # Build status badges for each selected framework
    badges = []
    for fw in target_fws:
        badges.append(html.Span(
            get_short_name(fw), className="badge me-1",
            style={"backgroundColor": get_color(fw), "color": "#fff", "fontSize": "0.7rem"},
        ))

    status = html.Div([
        *badges,
        html.Span(" ", className="me-1"),
        html.Strong(f"{n_direct}", style={"color": "#00d4ff"}),
        html.Span(" direct", className="text-muted"),
        html.Span(" + ", className="text-muted") if n_trans else "",
        html.Strong(f"{n_trans}", style={"color": "#8fd18f"}) if n_trans else "",
        html.Span(" transitive", className="text-muted") if n_trans else "",
        html.Span(f" = {total} total", className="text-muted"),
    ], style={"fontSize": "0.85rem", "padding": "8px 12px",
              "backgroundColor": "rgba(22,27,34,0.5)", "borderRadius": "6px",
              "border": "1px solid #21262d"})

    neighborhood = _build_neighborhood(fw_filtered, node, theme)
    mapping_cards = _build_mapping_cards(fw_filtered, node)
    return neighborhood, status, mapping_cards


@callback(
    Output("explorer-neighborhood-detail", "children"),
    Input("explorer-neighborhood", "clickData"),
    State("explorer-control", "value"),
    prevent_initial_call=True,
)
def neighborhood_node_click(click_data, source_node_id):
    """When user clicks a mapped control node in the neighborhood graph, show its detail card."""
    if not click_data or not source_node_id:
        return dash.no_update

    points = click_data.get("points", [])
    if not points:
        return dash.no_update

    target_node_id = points[0].get("customdata")
    if not target_node_id:
        return dash.no_update

    # Ignore clicks on the center node (source itself)
    if target_node_id == source_node_id:
        return dash.no_update

    target = get_node_by_id(target_node_id)
    if not target:
        return dash.no_update

    source = get_node_by_id(source_node_id)
    if not source:
        return dash.no_update

    # Find the specific edge metadata between source and target
    all_mappings = get_mappings_for_node(source_node_id)
    edge_meta = None
    is_transitive = False

    for d in all_mappings.get("direct", []):
        if d["target_node_id"] == target_node_id:
            edge_meta = d
            break

    if edge_meta is None:
        for t in all_mappings.get("transitive", []):
            if t["target_node_id"] == target_node_id:
                edge_meta = t
                is_transitive = True
                break

    target_fw = target.get("framework", "")
    fw_color = get_color(target_fw)

    # --- Framework / identity header ---
    header_items = [
        html.Span(
            get_short_name(target_fw),
            className="badge me-2",
            style={"backgroundColor": fw_color, "fontSize": "0.8rem"},
        ),
        html.Strong(
            f"{target.get('local_id', '')}: {target.get('name', '')}",
            style={"fontSize": "0.95rem"},
        ),
    ]
    if target.get("entry_type"):
        header_items.append(
            dbc.Badge(target["entry_type"], color="secondary", className="ms-2",
                      style={"fontSize": "0.7rem"}),
        )

    # --- Domain badges ---
    domain_badges = []
    if target.get("domain"):
        domain_badges.append(
            dbc.Badge(target["domain"], color="dark", className="me-1",
                      style={"fontSize": "0.7rem", "border": "1px solid #30363d"}),
        )
    if target.get("function_class"):
        domain_badges.append(
            dbc.Badge(target["function_class"], color="dark", className="me-1",
                      style={"fontSize": "0.7rem", "border": "1px solid #30363d"}),
        )

    # --- Edge metadata section ---
    if edge_meta is not None:
        conf = edge_meta.get("confidence", "unknown")
        conf_color = {"authoritative": "success", "expert": "primary",
                      "suggestive": "warning", "unvalidated": "secondary"}.get(conf, "secondary")
        rationale = edge_meta.get("rationale_code", "")
        rationale_label = RATIONALE_LABELS.get(rationale, rationale) if rationale else ""

        if is_transitive:
            bridge_id = edge_meta.get("bridge_node_id", "")
            bridge_short = bridge_id.split(":")[-1] if bridge_id else ""
            bridge_name = edge_meta.get("bridge_node_name", bridge_id)
            bridge_fw = edge_meta.get("bridge_framework", "")
            path_section = html.Div([
                html.Small("BRIDGE PATH", className="text-muted d-block mb-1",
                           style={"fontSize": "0.7rem", "letterSpacing": "0.05em"}),
                html.Div([
                    html.Span(source.get("local_id", ""),
                              className="badge",
                              style={"backgroundColor": get_color(source.get("framework", "")),
                                     "fontSize": "0.75rem"}),
                    html.Span(" \u2192 ", style={"color": "#00d4ff", "margin": "0 4px"}),
                    html.Span([
                        html.Span(bridge_short, className="badge",
                                  style={"backgroundColor": get_color(bridge_fw), "fontSize": "0.75rem"}),
                        html.Br(),
                        html.Small(str(bridge_name)[:40], className="text-muted",
                                   style={"fontSize": "0.68rem"}),
                    ]),
                    html.Span(" \u2192 ", style={"color": "#00d4ff", "margin": "0 4px"}),
                    html.Span(target.get("local_id", ""),
                              className="badge",
                              style={"backgroundColor": fw_color, "fontSize": "0.75rem"}),
                ], style={"display": "flex", "alignItems": "center", "gap": "4px",
                          "flexWrap": "wrap"}),
            ], className="mt-2 p-2",
               style={"backgroundColor": "rgba(13,17,23,0.6)", "borderRadius": "4px",
                      "border": "1px solid #21262d"})
            hop_badge = dbc.Badge("transitive (2-hop)", color="dark", className="me-1",
                                  style={"fontSize": "0.7rem", "color": "#8fd18f"})
        else:
            path_section = html.Div([
                html.Small("MAPPING PATH", className="text-muted d-block mb-1",
                           style={"fontSize": "0.7rem", "letterSpacing": "0.05em"}),
                html.Div([
                    html.Span(source.get("local_id", ""),
                              className="badge",
                              style={"backgroundColor": get_color(source.get("framework", "")),
                                     "fontSize": "0.75rem"}),
                    html.Span(" \u2192 ", style={"color": "#00d4ff", "margin": "0 4px"}),
                    html.Span(target.get("local_id", ""),
                              className="badge",
                              style={"backgroundColor": fw_color, "fontSize": "0.75rem"}),
                    html.Small(" (direct mapping)", className="text-muted ms-2",
                               style={"fontSize": "0.75rem"}),
                ], style={"display": "flex", "alignItems": "center", "flexWrap": "wrap"}),
            ], className="mt-2 p-2",
               style={"backgroundColor": "rgba(13,17,23,0.6)", "borderRadius": "4px",
                      "border": "1px solid #21262d"})
            hop_badge = dbc.Badge("direct", color="primary", className="me-1",
                                  style={"fontSize": "0.7rem"})

        rationale_note = edge_meta.get("rationale_note", "")
        edge_section = html.Div([
            html.Div([
                hop_badge,
                dbc.Badge(conf, color=conf_color, className="me-1",
                          style={"fontSize": "0.7rem"}),
                dbc.Badge(rationale, color="dark", className="me-1",
                          style={"fontSize": "0.7rem"}) if rationale else None,
                html.Small(rationale_label, className="text-muted ms-1",
                           style={"fontSize": "0.75rem"}) if rationale_label else None,
            ], className="d-flex align-items-center flex-wrap gap-1"),
            html.P(rationale_note,
                   className="mt-1 mb-0",
                   style={"fontSize": "0.82rem", "color": "#9eaab8", "lineHeight": "1.5"}) if rationale_note else None,
            path_section,
        ])
    else:
        edge_section = html.Div()

    card = dbc.Card([
        dbc.CardHeader(
            html.Div(header_items, className="d-flex align-items-center flex-wrap gap-1"),
            style={"backgroundColor": "rgba(13,17,23,0.7)",
                   "borderBottom": f"1px solid {fw_color}33"},
        ),
        dbc.CardBody([
            html.P(
                target.get("description", "No description available."),
                style={"fontSize": "0.88rem", "lineHeight": "1.65", "color": "#c9d1d9",
                       "marginBottom": "0.75rem"},
            ),
            html.Div(domain_badges, className="mb-2") if domain_badges else None,
            edge_section,
        ], style={"backgroundColor": "rgba(22,27,34,0.8)"}),
    ], style={
        "borderLeft": f"4px solid {fw_color}",
        "backgroundColor": "rgba(22,27,34,0.8)",
        "border": f"1px solid {fw_color}55",
    })

    return html.Div([
        html.Small(
            "Node detail (click another node to update, or click outside the graph to dismiss)",
            className="text-muted d-block mb-2",
            style={"fontSize": "0.75rem"},
        ),
        card,
    ])


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


@callback(
    Output("explorer-learn-more", "is_open"),
    Input("explorer-learn-toggle", "n_clicks"),
    State("explorer-learn-more", "is_open"),
    prevent_initial_call=True,
)
def toggle_explorer_learn_more(n_clicks, is_open):
    return not is_open
