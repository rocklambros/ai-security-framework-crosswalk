"""Page 2: Framework Deep Dive -- explore a single framework's structure."""

import math

import dash
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from dash import Input, Output, State, callback, ctx, dcc, html

from components.badge_tooltips import badge_with_tooltip
from components.classifier_badge import classifier_badge
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
    "Drill into any single framework to see how its controls, risks, or techniques are "
    "organized internally. Click domain nodes to expand and explore individual controls; "
    "the bar chart shows where this framework's mappings point."
)

LEARN_MORE_CONTENT = [
    html.H6("Understanding Framework Structure", className="mt-2 mb-1", style={"color": "#00d4ff"}),
    html.P(
        "Each framework organizes its entries differently. AIUC-1 groups controls by security domain "
        "(Accountability, Security, Safety, etc.). MITRE ATLAS uses a tactic-technique hierarchy "
        "borrowed from ATT&CK. CSA AICM follows a traditional control-family structure. NIST AI RMF organizes "
        "by function (Govern, Map, Measure, Manage). The network graph normalizes these different organizational "
        "schemes into a navigable, interactive format.",
        style={"fontSize": "0.85rem", "lineHeight": "1.7", "color": "#9eaab8"},
    ),
    html.H6("Navigating the Network", className="mt-2 mb-1", style={"color": "#00d4ff"}),
    html.P([
        "The center node represents the framework. ",
        html.Strong("Domain nodes", style={"color": "#c9d1d9"}),
        " (the inner ring) represent top-level categories like Security, Accountability, or Govern. "
        "The number on each domain node shows how many controls it contains. ",
        html.Strong("Click any domain", style={"color": "#00d4ff"}),
        " to expand it and see its individual controls fan out in the outer ring. Click the same domain "
        "again to collapse it. Click any individual control to see its full description, entry type, "
        "and cross-framework mapping count.",
    ], style={"fontSize": "0.85rem", "lineHeight": "1.7", "color": "#9eaab8"}),
    html.H6("Reading the Bar Chart", className="mt-2 mb-1", style={"color": "#00d4ff"}),
    html.P([
        "The stacked horizontal bars show how this framework's controls map outward to each target framework, "
        "broken down by confidence level. ",
        html.Strong("Source-heavy frameworks", style={"color": "#c9d1d9"}),
        " (AIUC-1, CSA AICM) have outbound bars showing where their controls map. ",
        html.Strong("Target-only frameworks", style={"color": "#c9d1d9"}),
        " (NIST, OWASP LLM Top 10, OWASP Agentic Top 10) show inbound bars instead, since other frameworks map into them "
        "but they do not map outward.",
    ], style={"fontSize": "0.85rem", "lineHeight": "1.7", "color": "#9eaab8"}),
    html.H6("Entry Type Filters", className="mt-2 mb-1", style={"color": "#00d4ff"}),
    html.P(
        "The checklist filters let you isolate specific entry types. Controls are actionable safeguards. "
        "Risks describe threat scenarios. Techniques describe adversarial methods. Mitigations are "
        "countermeasures. Activities are governance actions. Filtering by type helps you focus on the "
        "aspect of the framework most relevant to your role.",
        style={"fontSize": "0.85rem", "lineHeight": "1.7", "color": "#9eaab8"},
    ),
]



def _framework_options():
    stats = get_framework_stats()
    return [
        {"label": f"{get_display_name(fw)} ({stats[fw]['node_count']} nodes)", "value": fw}
        for fw in FRAMEWORK_KEYS
        if fw in stats
    ]


def _get_domain_data(framework, entry_types):
    """Get domain-grouped hierarchy data, optionally filtered by entry types."""
    hierarchy = get_hierarchy()
    if framework not in hierarchy:
        return {}

    h = hierarchy[framework]
    ids, labels, parents, values = h["ids"], h["labels"], h["parents"], h["values"]

    domains = {}
    for i in range(len(ids)):
        if "::" in ids[i]:
            domains[ids[i]] = {"label": labels[i], "count": values[i], "children": []}

    allowed_ids = None
    if entry_types:
        nodes_df = get_nodes_df()
        fw_nodes = nodes_df[nodes_df["framework"] == framework]
        allowed_ids = set(fw_nodes[fw_nodes["entry_type"].isin(entry_types)]["node_id"])

    for i in range(len(ids)):
        parent = parents[i]
        if parent in domains:
            if allowed_ids is None or ids[i] in allowed_ids:
                domains[parent]["children"].append({"id": ids[i], "label": labels[i]})

    if allowed_ids is not None:
        for d in domains.values():
            d["count"] = len(d["children"])

    return domains


def _build_level0(framework, entry_types, theme="dark"):
    """Level 0: Framework overview with domain nodes around center.

    Encoding: categorical framework color for nominal identity (Borner et al.
    2019). Node size encodes domain breadth via area (Cleveland rank 4),
    acceptable for navigational drill-down where the task is selection, not
    precise comparison. Count labels inside nodes provide direct readout.
    """
    domains = _get_domain_data(framework, entry_types)
    fw_color = get_color(framework)
    domain_list = sorted(domains.keys())
    n_domains = len(domain_list)

    if n_domains == 0:
        fig = go.Figure()
        fig.update_layout(template=get_template(theme), height=500)
        fig.add_annotation(text="No domains found", showarrow=False)
        return fig

    traces = []
    domain_radius = 0.65

    # Edges from center to domains
    edge_x, edge_y = [], []
    for i, did in enumerate(domain_list):
        angle = 2 * math.pi * i / n_domains - math.pi / 2
        dx = math.cos(angle) * domain_radius
        dy = math.sin(angle) * domain_radius
        edge_x.extend([0, dx, None])
        edge_y.extend([0, dy, None])

    traces.append(go.Scatter(
        x=edge_x, y=edge_y, mode="lines",
        line=dict(width=1.5, color="rgba(0,212,255,0.2)"),
        showlegend=False, hoverinfo="skip",
    ))

    # Domain nodes
    for i, did in enumerate(domain_list):
        angle = 2 * math.pi * i / n_domains - math.pi / 2
        dx = math.cos(angle) * domain_radius
        dy = math.sin(angle) * domain_radius
        d = domains[did]
        size = max(22, min(50, d["count"] / 2 + 15))

        traces.append(go.Scatter(
            x=[dx], y=[dy], mode="markers+text",
            marker=dict(size=size, color=fw_color,
                        line=dict(width=2, color="rgba(0,212,255,0.4)")),
            text=[str(d["count"])],
            textposition="middle center",
            textfont=dict(size=9, color="white"),
            hovertext=f"<b>{d['label']}</b><br>{d['count']} entries<br><i>Click to drill in</i>",
            hoverinfo="text", showlegend=False,
            customdata=[{"type": "domain", "id": d["label"]}],
        ))

        # Label outside node
        label_r = domain_radius + 0.18
        lx = math.cos(angle) * label_r
        ly = math.sin(angle) * label_r
        traces.append(go.Scatter(
            x=[lx], y=[ly], mode="text",
            text=[d["label"]],
            textfont=dict(size=10, color="#8b949e"),
            textposition="middle center",
            showlegend=False, hoverinfo="skip",
        ))

    # Center node
    total = sum(d["count"] for d in domains.values())
    traces.append(go.Scatter(
        x=[0], y=[0], mode="markers+text",
        marker=dict(size=35, color=fw_color, line=dict(width=3, color="#00d4ff")),
        text=[get_short_name(framework)],
        textposition="middle center",
        textfont=dict(size=10, color="white", family="Arial Black"),
        hovertext=f"<b>{get_display_name(framework)}</b><br>{total} entries",
        hoverinfo="text", showlegend=False,
        customdata=[{"type": "root", "id": framework}],
    ))

    fig = go.Figure(data=traces)
    fig.update_layout(
        template=get_template(theme), height=550,
        title=dict(text=f"{get_display_name(framework)} Structure", font=dict(size=14)),
        xaxis=dict(visible=False, range=[-1.1, 1.1]),
        yaxis=dict(visible=False, range=[-1.1, 1.1], scaleanchor="x"),
        hovermode="closest", dragmode="pan",
        margin=dict(t=50, b=10, l=10, r=10),
    )
    return fig


def _build_level1(framework, domain_name, entry_types, theme="dark"):
    """Level 1: Domain zoom -- domain at center, controls radiating out.

    Encoding: same radial network as Level 0. Uniform node size (12px) because
    all children are peers at this level; position encodes identity only.
    Categorical framework color maintained for consistency (Graze & Schwabish
    2024). Hover text provides full control name and click affordance.
    """
    domains = _get_domain_data(framework, entry_types)
    fw_color = get_color(framework)

    # Find the target domain
    target = None
    for did, d in domains.items():
        if d["label"] == domain_name:
            target = d
            break

    if not target or not target["children"]:
        fig = go.Figure()
        fig.update_layout(template=get_template(theme), height=500)
        fig.add_annotation(text=f"No controls in {domain_name}", showarrow=False)
        return fig

    children = target["children"]
    n = len(children)
    traces = []
    radius = 0.8

    # Edges from center to controls
    edge_x, edge_y = [], []
    for i in range(n):
        angle = 2 * math.pi * i / n - math.pi / 2
        cx = math.cos(angle) * radius
        cy = math.sin(angle) * radius
        edge_x.extend([0, cx, None])
        edge_y.extend([0, cy, None])

    traces.append(go.Scatter(
        x=edge_x, y=edge_y, mode="lines",
        line=dict(width=1, color="rgba(0,212,255,0.15)"),
        showlegend=False, hoverinfo="skip",
    ))

    # Control nodes
    c_x, c_y, c_hover, c_customdata, c_colors = [], [], [], [], []
    for i, child in enumerate(children):
        angle = 2 * math.pi * i / n - math.pi / 2
        cx = math.cos(angle) * radius
        cy = math.sin(angle) * radius
        c_x.append(cx)
        c_y.append(cy)
        # Extract short ID from label
        child["label"].split(":")[0] if ":" in child["label"] else child["id"]
        c_hover.append(f"<b>{child['label']}</b><br><i>Click for cross-framework mappings</i>")
        c_customdata.append({"type": "control", "id": child["id"]})
        c_colors.append(fw_color)

    traces.append(go.Scatter(
        x=c_x, y=c_y, mode="markers",
        marker=dict(size=12, color=c_colors, line=dict(width=1, color="#21262d")),
        hovertext=c_hover, hoverinfo="text", showlegend=False,
        customdata=c_customdata,
    ))

    # Control labels (outside)
    for i, child in enumerate(children):
        angle = 2 * math.pi * i / n - math.pi / 2
        lx = math.cos(angle) * (radius + 0.15)
        ly = math.sin(angle) * (radius + 0.15)
        short_label = child["label"][:20] + "..." if len(child["label"]) > 20 else child["label"]
        traces.append(go.Scatter(
            x=[lx], y=[ly], mode="text",
            text=[short_label],
            textfont=dict(size=8, color="#8b949e"),
            textposition="middle center",
            showlegend=False, hoverinfo="skip",
        ))

    # Center domain node
    traces.append(go.Scatter(
        x=[0], y=[0], mode="markers+text",
        marker=dict(size=30, color="#00d4ff", line=dict(width=3, color=fw_color)),
        text=[domain_name[:15]],
        textposition="middle center",
        textfont=dict(size=9, color="white"),
        hovertext=f"<b>{domain_name}</b><br>{n} entries<br><i>Click to go back to overview</i>",
        hoverinfo="text", showlegend=False,
        customdata=[{"type": "back_to_0", "id": domain_name}],
    ))

    fig = go.Figure(data=traces)
    fig.update_layout(
        template=get_template(theme), height=550,
        title=dict(
            text=f"{get_short_name(framework)} / {domain_name} ({n} controls)",
            font=dict(size=14),
        ),
        xaxis=dict(visible=False, range=[-1.3, 1.3]),
        yaxis=dict(visible=False, range=[-1.3, 1.3], scaleanchor="x"),
        hovermode="closest", dragmode="pan",
        margin=dict(t=50, b=10, l=10, r=10),
    )
    return fig


def _build_level2(framework, node_id, theme="dark", expanded_fw=None):
    """Level 2: Control zoom -- control at center, cross-framework mappings radiating out.

    Encoding: categorical framework colors (Borner et al. 2019) for target
    framework identity. Node size encodes mapping count via area (Cleveland
    rank 4); count labels inside nodes provide direct readout. Shape encodes
    mapping type: circles = direct, diamonds = transitive (Borner: shape for
    categorical distinction). Edge width proportional to total mappings.
    """
    from collections import defaultdict

    from components.data_loader import get_mappings_for_node

    node = get_node_by_id(node_id)
    if not node:
        fig = go.Figure()
        fig.update_layout(template=get_template(theme), height=500)
        return fig

    mappings = get_mappings_for_node(node_id)
    direct = mappings.get("direct", [])
    transitive = mappings.get("transitive", [])

    fw_color = get_color(framework)
    traces = []

    # Group mappings by target framework
    by_fw = defaultdict(lambda: {"direct": [], "transitive": []})
    for d in direct:
        by_fw[d["target_framework"]]["direct"].append(d)
    for t in transitive:
        by_fw[t["target_framework"]]["transitive"].append(t)

    fw_list = sorted(by_fw.keys(), key=lambda fw: len(by_fw[fw]["direct"]) + len(by_fw[fw]["transitive"]), reverse=True)
    n_fws = len(fw_list)

    # Expand axis range when a framework is expanded to fit fan-out nodes
    axis_range = [-1.6, 1.6] if expanded_fw else [-1.2, 1.2]

    if n_fws == 0:
        # No mappings -- show isolated node
        traces.append(go.Scatter(
            x=[0], y=[0], mode="markers+text",
            marker=dict(size=30, color=fw_color, line=dict(width=3, color="#00d4ff")),
            text=[node["local_id"]],
            textposition="middle center",
            textfont=dict(size=9, color="white"),
            hovertext=f"<b>{node['local_id']}: {node['name']}</b><br>No cross-framework mappings<br><i>Click to go back</i>",
            hoverinfo="text", showlegend=False,
            customdata=[{"type": "back_to_1", "id": node_id}],
        ))
    else:
        # Framework target nodes around center
        radius = 0.7
        for i, tgt_fw in enumerate(fw_list):
            angle = 2 * math.pi * i / n_fws - math.pi / 2
            tx = math.cos(angle) * radius
            ty = math.sin(angle) * radius
            d_count = len(by_fw[tgt_fw]["direct"])
            t_count = len(by_fw[tgt_fw]["transitive"])
            total = d_count + t_count
            size = max(18, min(40, total / 2 + 12))

            is_expanded = (tgt_fw == expanded_fw)

            # Edge from center
            edge_width = max(1, min(5, total / 10))
            traces.append(go.Scatter(
                x=[0, tx, None], y=[0, ty, None], mode="lines",
                line=dict(width=edge_width, color=f"rgba({','.join(str(int(get_color(tgt_fw)[k:k+2], 16)) for k in (1,3,5))},0.3)"),
                showlegend=False, hoverinfo="skip",
            ))

            parts = []
            if d_count:
                parts.append(f"{d_count} direct")
            if t_count:
                parts.append(f"{t_count} transitive")

            hover_action = "Click to collapse" if is_expanded else "Click to expand controls"
            border_color = "#00d4ff" if is_expanded else "#21262d"
            border_width = 3 if is_expanded else 1.5

            traces.append(go.Scatter(
                x=[tx], y=[ty], mode="markers+text",
                marker=dict(size=size, color=get_color(tgt_fw),
                            line=dict(width=border_width, color=border_color)),
                text=[str(total)],
                textposition="middle center",
                textfont=dict(size=9, color="white"),
                hovertext=f"<b>{get_display_name(tgt_fw)}</b><br>{', '.join(parts)}<br><i>{hover_action}</i>",
                hoverinfo="text", showlegend=False,
                customdata=[{"type": "target_fw", "id": tgt_fw}],
            ))

            # Framework label
            lx = math.cos(angle) * (radius + 0.18)
            ly = math.sin(angle) * (radius + 0.18)
            traces.append(go.Scatter(
                x=[lx], y=[ly], mode="text",
                text=[get_short_name(tgt_fw)],
                textfont=dict(size=9, color="#8b949e"),
                textposition="middle center",
                showlegend=False, hoverinfo="skip",
            ))

            # Fan out individual mapped controls when this framework is expanded
            if is_expanded:
                fw_direct = by_fw[tgt_fw]["direct"]
                fw_trans = by_fw[tgt_fw]["transitive"]
                max_show = 15
                all_mapped = (fw_direct + fw_trans)[:max_show]
                n_mapped = len(all_mapped)
                n_total = len(fw_direct) + len(fw_trans)

                if n_mapped > 0:
                    arc_radius = 0.35 if n_mapped > 8 else 0.28
                    arc_spread = min(math.pi * 1.2, n_mapped * 0.25)
                    arc_start = angle - arc_spread / 2

                    fw_rgb = ",".join(str(int(get_color(tgt_fw)[k:k+2], 16)) for k in (1, 3, 5))

                    for j, m in enumerate(all_mapped):
                        if n_mapped > 1:
                            m_angle = arc_start + (arc_spread * j / (n_mapped - 1))
                        else:
                            m_angle = angle
                        mx = tx + math.cos(m_angle) * arc_radius
                        my = ty + math.sin(m_angle) * arc_radius

                        target_node = get_node_by_id(m["target_node_id"])
                        m_label = target_node["local_id"] if target_node else m["target_node_id"].split(":")[-1]
                        m_name = (target_node["name"][:40] if target_node else "")
                        is_direct = m in fw_direct

                        # Edge from framework node to control
                        traces.append(go.Scatter(
                            x=[tx, mx, None], y=[ty, my, None],
                            mode="lines",
                            line=dict(width=1, color=f"rgba({fw_rgb},0.3)"),
                            showlegend=False, hoverinfo="skip",
                        ))

                        # Control node
                        traces.append(go.Scatter(
                            x=[mx], y=[my],
                            mode="markers",
                            marker=dict(
                                size=10,
                                color=get_color(tgt_fw),
                                line=dict(width=1, color="#21262d"),
                                symbol="circle" if is_direct else "diamond",
                            ),
                            hovertext=f"<b>{m_label}: {m_name}</b><br>{'Direct' if is_direct else 'Transitive'} mapping",
                            hoverinfo="text",
                            showlegend=False,
                            customdata=[{"type": "expanded_control", "id": m["target_node_id"]}],
                        ))

                        # Label just beyond the control node
                        label_r = arc_radius + 0.08
                        lbx = tx + math.cos(m_angle) * label_r
                        lby = ty + math.sin(m_angle) * label_r
                        traces.append(go.Scatter(
                            x=[lbx], y=[lby],
                            mode="text",
                            text=[m_label],
                            textfont=dict(size=7, color="#8b949e"),
                            textposition="middle center",
                            showlegend=False, hoverinfo="skip",
                        ))

                    # "+N more" indicator when truncated
                    if n_total > max_show:
                        extra_angle = arc_start + arc_spread + 0.15
                        ex = tx + math.cos(extra_angle) * (arc_radius + 0.05)
                        ey = ty + math.sin(extra_angle) * (arc_radius + 0.05)
                        traces.append(go.Scatter(
                            x=[ex], y=[ey], mode="text",
                            text=[f"+{n_total - max_show} more"],
                            textfont=dict(size=8, color="#d9bf55"),
                            textposition="middle center",
                            showlegend=False, hoverinfo="skip",
                        ))

        # Center control node
        traces.append(go.Scatter(
            x=[0], y=[0], mode="markers+text",
            marker=dict(size=30, color=fw_color, line=dict(width=3, color="#00d4ff")),
            text=[node["local_id"]],
            textposition="middle center",
            textfont=dict(size=9, color="white"),
            hovertext=(
                f"<b>{node['local_id']}: {node['name']}</b><br>"
                f"{len(direct)} direct + {len(transitive)} transitive mappings<br>"
                f"<i>Click to go back</i>"
            ),
            hoverinfo="text", showlegend=False,
            customdata=[{"type": "back_to_1", "id": node_id}],
        ))

    fig = go.Figure(data=traces)
    fig.update_layout(
        template=get_template(theme), height=550,
        title=dict(
            text=f"{node['local_id']}: {node['name'][:40]} -- Cross-Framework Mappings",
            font=dict(size=13),
        ),
        xaxis=dict(visible=False, range=axis_range),
        yaxis=dict(visible=False, range=axis_range, scaleanchor="x"),
        hovermode="closest", dragmode="pan",
        margin=dict(t=50, b=10, l=10, r=10),
    )
    return fig


def _build_mapping_bar(framework, theme="dark"):
    """Build bidirectional mapping bar chart showing both outbound and inbound.

    Encoding: position along a common scale (Cleveland & McGill 1984, rank 1).
    Diverging layout (negative left, positive right) uses two-category color
    (blue outbound, green inbound) with sufficient hue and luminance separation
    for colorblind accessibility (Graze & Schwabish 2024).
    """
    edges_df = get_edges_df()
    cross = edges_df[edges_df["source_framework"] != edges_df["target_framework"]]

    outbound = cross[cross["source_framework"] == framework]
    inbound = cross[cross["target_framework"] == framework]

    if outbound.empty and inbound.empty:
        fig = go.Figure()
        fig.update_layout(template=get_template(theme), height=500)
        fig.add_annotation(text="No cross-framework mappings found", showarrow=False)
        return fig

    # Collect all peer frameworks
    peers = set()
    if not outbound.empty:
        peers.update(outbound["target_framework"].unique())
    if not inbound.empty:
        peers.update(inbound["source_framework"].unique())

    # Compute bidirectional totals per peer for sorting
    peer_totals = {}
    for peer in peers:
        out_n = len(outbound[outbound["target_framework"] == peer])
        in_n = len(inbound[inbound["source_framework"] == peer])
        peer_totals[peer] = out_n + in_n
    sorted_peers = sorted(peers, key=lambda p: peer_totals[p])

    peer_labels = [get_short_name(p) for p in sorted_peers]

    # Outbound bars (positive, right)
    out_counts = [len(outbound[outbound["target_framework"] == p]) for p in sorted_peers]
    # Inbound bars (negative, left)
    in_counts = [-len(inbound[inbound["source_framework"] == p]) for p in sorted_peers]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=peer_labels,
        x=out_counts,
        name="Outbound",
        orientation="h",
        marker_color="#1f6feb",
        hovertemplate="<b>%{y}</b><br>Outbound: %{x} mappings<extra></extra>",
        customdata=sorted_peers,
    ))
    fig.add_trace(go.Bar(
        y=peer_labels,
        x=in_counts,
        name="Inbound",
        orientation="h",
        marker_color="#39d353",
        hovertemplate="<b>%{y}</b><br>Inbound: %{customdata[1]} mappings<extra></extra>",
        customdata=list(zip(sorted_peers, [-v for v in in_counts])),
    ))

    fig.update_layout(
        template=get_template(theme),
        height=500,
        title=dict(
            text=f"Cross-Framework Mappings: {get_short_name(framework)}",
            font=dict(size=14),
        ),
        barmode="relative",
        xaxis=dict(title="Edge count (left=inbound, right=outbound)"),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2),
    )
    return fig


def _build_control_card(node_id):
    """Build detail card for a leaf-level control/technique/risk."""
    node = get_node_by_id(node_id)
    if not node:
        return html.Div()

    badges = []
    if node.get("entry_type"):
        badges.append(badge_with_tooltip(node["entry_type"], color="secondary"))
    if node.get("function_class"):
        badges.append(badge_with_tooltip(node["function_class"], color="info"))
    if node.get("domain"):
        badges.append(badge_with_tooltip(node["domain"], color="dark"))

    # Count cross-framework mappings for this node
    edges_df = get_edges_df()
    outbound = edges_df[
        (edges_df["source_node_id"] == node_id)
        & (edges_df["source_framework"] != edges_df["target_framework"])
    ]
    inbound = edges_df[
        (edges_df["target_node_id"] == node_id)
        & (edges_df["source_framework"] != edges_df["target_framework"])
    ]
    mapping_count = len(outbound) + len(inbound)

    body_items = [
        html.P(node.get("description", "No description available."),
               style={"fontSize": "0.9rem", "lineHeight": "1.6"}),
    ]

    # Mapping summary
    if mapping_count > 0:
        target_fws = set(outbound["target_framework"].tolist() + inbound["source_framework"].tolist())
        body_items.append(html.P([
            html.Strong(f"{mapping_count}", style={"color": "#00d4ff"}),
            f" cross-framework mappings across {len(target_fws)} frameworks",
        ], className="text-muted mb-1", style={"fontSize": "0.85rem"}))

    meta_items = []
    if node.get("frequency"):
        meta_items.append(html.Small(f"Frequency: {node['frequency']}", className="text-muted me-3"))
    if node.get("url"):
        meta_items.append(html.Small(
            html.A("View source", href=node["url"], target="_blank", className="text-info"),
            className="me-3",
        ))
    if meta_items:
        body_items.append(html.Div(meta_items))

    body_items.append(
        dcc.Link(
            dbc.Button("View in Crosswalk Explorer", color="info", size="sm",
                       className="mt-2", outline=True),
            href=f"/explorer?framework={node['framework']}&control={node_id}",
        )
    )

    return dbc.Card([
        dbc.CardHeader([
            html.Span(get_short_name(node["framework"]),
                      className="badge me-2",
                      style={"backgroundColor": get_color(node["framework"])}),
            html.Strong(f"{node['local_id']}: {node['name']}"),
            html.Div(badges, className="mt-1"),
        ]),
        dbc.CardBody(body_items),
    ], className="mt-3", style={"borderLeft": f"4px solid {get_color(node['framework'])}"})


def _build_domain_card(framework, domain_name):
    """Build summary card for a domain-level sunburst click."""
    nodes_df = get_nodes_df()
    edges_df = get_edges_df()

    domain_nodes = nodes_df[
        (nodes_df["framework"] == framework) & (nodes_df["domain"] == domain_name)
    ]
    if domain_nodes.empty:
        return html.Div()

    node_count = len(domain_nodes)
    type_counts = domain_nodes["entry_type"].value_counts().to_dict()

    # Count outbound cross-framework edges from this domain's nodes
    domain_node_ids = set(domain_nodes["node_id"])
    outbound = edges_df[
        edges_df["source_node_id"].isin(domain_node_ids)
        & (edges_df["source_framework"] != edges_df["target_framework"])
    ]
    inbound = edges_df[
        edges_df["target_node_id"].isin(domain_node_ids)
        & (edges_df["source_framework"] != edges_df["target_framework"])
    ]

    # Target framework breakdown
    target_fw_counts = {}
    for fw in outbound["target_framework"].value_counts().to_dict():
        target_fw_counts[fw] = target_fw_counts.get(fw, 0) + outbound["target_framework"].value_counts()[fw]
    for fw in inbound["source_framework"].value_counts().to_dict():
        target_fw_counts[fw] = target_fw_counts.get(fw, 0) + inbound["source_framework"].value_counts()[fw]

    # Type badges
    type_badges = [
        dbc.Badge(f"{count} {etype}", color="secondary", className="me-1")
        for etype, count in sorted(type_counts.items(), key=lambda x: -x[1])
    ]

    # Framework mapping pills
    fw_pills = []
    for fw, count in sorted(target_fw_counts.items(), key=lambda x: -x[1])[:6]:
        fw_pills.append(html.Span([
            html.Span("\u25cf ", style={"color": get_color(fw)}),
            html.Span(f"{get_short_name(fw)}: ", className="text-muted"),
            html.Span(f"{count}", style={"color": "#c9d1d9"}),
        ], className="me-3", style={"fontSize": "0.8rem"}))

    body_items = [
        html.Div(type_badges, className="mb-2"),
    ]
    if fw_pills:
        body_items.append(html.P([
            html.Strong(f"{len(outbound) + len(inbound)} ", style={"color": "#00d4ff"}),
            "cross-framework mappings:",
        ], className="mb-1", style={"fontSize": "0.85rem"}))
        body_items.append(html.Div(fw_pills, style={"display": "flex", "flexWrap": "wrap", "gap": "4px"}))
    else:
        body_items.append(html.P("No cross-framework mappings from this domain.",
                                 className="text-muted", style={"fontSize": "0.85rem"}))

    # List first few controls in this domain
    sample = domain_nodes.head(5)
    control_list = [
        html.Li(
            f"{row['local_id']}: {row['name'][:80]}",
            style={"fontSize": "0.8rem", "color": "#9eaab8"},
        )
        for _, row in sample.iterrows()
    ]
    if node_count > 5:
        control_list.append(html.Li(
            f"... and {node_count - 5} more",
            style={"fontSize": "0.8rem", "color": "#6e7681", "fontStyle": "italic"},
        ))
    body_items.append(html.Ul(control_list, className="mt-2 mb-0", style={"paddingLeft": "1.2rem"}))

    return dbc.Card([
        dbc.CardHeader([
            html.Span(get_short_name(framework),
                      className="badge me-2",
                      style={"backgroundColor": get_color(framework)}),
            html.Strong(domain_name),
            html.Span(f" ({node_count} entries)", className="text-muted ms-2",
                      style={"fontSize": "0.85rem"}),
        ]),
        dbc.CardBody(body_items),
    ], className="mt-3", style={"borderLeft": f"4px solid {get_color(framework)}"})


def _build_target_fw_detail(source_node_id, target_fw, source_framework):
    """Build detail card showing all mappings from source control to a specific target framework."""
    from components.data_loader import get_mappings_for_node

    source_node = get_node_by_id(source_node_id)
    if not source_node:
        return html.Div()

    mappings = get_mappings_for_node(source_node_id)
    direct = [d for d in mappings.get("direct", []) if d["target_framework"] == target_fw]
    transitive = [t for t in mappings.get("transitive", []) if t["target_framework"] == target_fw]

    if not direct and not transitive:
        return html.Div()

    items = []

    # Direct mappings
    if direct:
        items.append(html.Div([
            html.Strong(f"{len(direct)} direct mapping{'s' if len(direct) != 1 else ''}",
                        style={"color": "#00d4ff", "fontSize": "0.85rem"}),
        ], className="mb-2"))

        for d in direct:
            target = get_node_by_id(d["target_node_id"])
            conf = d.get("confidence", "unknown")
            rationale = d.get("rationale_code", "")

            items.append(dbc.Card([
                dbc.CardHeader([
                    html.Strong(
                        f"{target['local_id']}: {target['name'][:60]}" if target else d["target_node_id"],
                        style={"fontSize": "0.85rem"},
                    ),
                    html.Span([
                        badge_with_tooltip(conf, color={"authoritative": "success", "expert": "primary",
                                  "suggestive": "warning"}.get(conf, "secondary"), class_name="ms-2"),
                        badge_with_tooltip(rationale, color="dark", class_name="ms-1") if rationale else None,
                        classifier_badge(d.get("classifier_tier"), d.get("classifier_confidence")),
                    ], style={"marginLeft": "auto"}),
                ], className="py-2 d-flex align-items-center"),
                dbc.CardBody([
                    html.P(target.get("description", "No description.") if target else "",
                           style={"fontSize": "0.85rem", "lineHeight": "1.6", "color": "#9eaab8", "marginBottom": "0.5rem"}),
                    html.Div([
                        html.Span(source_node["local_id"], className="badge",
                                  style={"backgroundColor": get_color(source_framework), "fontSize": "0.75rem"}),
                        html.Span(" -> ", style={"color": "#00d4ff"}),
                        html.Span(target["local_id"] if target else d["target_node_id"], className="badge",
                                  style={"backgroundColor": get_color(target_fw), "fontSize": "0.75rem"}),
                    ], style={"backgroundColor": "rgba(13,17,23,0.5)", "borderRadius": "4px", "padding": "6px 10px"}),
                ]),
            ], className="mb-2", style={"borderLeft": f"3px solid {get_color(target_fw)}"}))

    # Transitive mappings
    if transitive:
        items.append(html.Div([
            html.Strong(f"{len(transitive)} transitive mapping{'s' if len(transitive) != 1 else ''}",
                        style={"color": "#8fd18f", "fontSize": "0.85rem"}),
        ], className="mb-2 mt-3"))

        for t in transitive[:20]:  # Limit for performance
            target = get_node_by_id(t["target_node_id"])
            bridge_id = t.get("bridge_node_id", "")
            bridge_short = bridge_id.split(":")[-1] if ":" in bridge_id else bridge_id

            items.append(dbc.Card([
                dbc.CardHeader([
                    html.Strong(
                        f"{target['local_id']}: {target['name'][:60]}" if target else t["target_node_id"],
                        style={"fontSize": "0.85rem"},
                    ),
                    badge_with_tooltip("transitive", color="dark", class_name="ms-auto",
                              style={"color": get_color(target_fw)}),
                ], className="py-2 d-flex align-items-center"),
                dbc.CardBody([
                    html.P(target.get("description", "No description.") if target else "",
                           style={"fontSize": "0.85rem", "lineHeight": "1.6", "color": "#9eaab8", "marginBottom": "0.5rem"}),
                    html.Div([
                        html.Span(source_node["local_id"], className="badge",
                                  style={"backgroundColor": get_color(source_framework), "fontSize": "0.75rem"}),
                        html.Span(" -> ", style={"color": "#00d4ff"}),
                        html.Span(bridge_short, className="badge",
                                  style={"backgroundColor": get_color(t.get("bridge_framework", "")), "fontSize": "0.75rem"}),
                        html.Span(" -> ", style={"color": "#00d4ff"}),
                        html.Span(target["local_id"] if target else t["target_node_id"], className="badge",
                                  style={"backgroundColor": get_color(target_fw), "fontSize": "0.75rem"}),
                    ], style={"backgroundColor": "rgba(13,17,23,0.5)", "borderRadius": "4px", "padding": "6px 10px"}),
                ]),
            ], className="mb-2", style={"borderLeft": f"3px solid {get_color(target_fw)}"}))

        if len(transitive) > 20:
            items.append(html.Div(
                f"+ {len(transitive) - 20} more transitive mappings",
                className="text-center text-muted", style={"fontSize": "0.8rem"}))

    return dbc.Card([
        dbc.CardHeader([
            html.Span(get_short_name(source_framework), className="badge me-2",
                      style={"backgroundColor": get_color(source_framework)}),
            html.Strong(f"{source_node['local_id']} "),
            html.Span("-> ", style={"color": "#6e7681"}),
            html.Span(get_short_name(target_fw), className="badge me-2",
                      style={"backgroundColor": get_color(target_fw)}),
            html.Strong(get_display_name(target_fw)),
            html.Span(f" ({len(direct)} direct, {len(transitive)} transitive)",
                      className="text-muted ms-2", style={"fontSize": "0.85rem"}),
        ]),
        dbc.CardBody(items),
    ], className="mt-3", style={"borderLeft": f"4px solid {get_color(target_fw)}"})


# --- Layout ---
layout = dbc.Container([
    dbc.Row(dbc.Col(
        dbc.Card(dbc.CardBody([
            html.H4("Framework Deep Dive", className="mb-2"),
            html.P(INTRO_TEXT, className="text-muted mb-2", style={"fontSize": "0.9rem"}),
            html.A("Learn more about framework structure", id="deep-dive-learn-toggle",
                   style={"fontSize": "0.85rem", "cursor": "pointer", "color": "#00d4ff",
                          "textDecoration": "none"}),
            dbc.Collapse(html.Div(LEARN_MORE_CONTENT, className="mt-2"),
                         id="deep-dive-learn-more", is_open=False),
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

    # Zoom state: {level: 0|1|2, domain: str|null, node_id: str|null, expanded_fw: str|null}
    dcc.Store(id="deep-dive-zoom", data={"level": 0, "domain": None, "node_id": None, "expanded_fw": None}),

    # Breadcrumb navigation
    html.Div(id="deep-dive-breadcrumb", className="mb-2"),

    # Charts (full-width stacked)
    dbc.Row(dbc.Col(dcc.Loading(dcc.Graph(
        id="deep-dive-network",
        config={
            "scrollZoom": True,
            "displayModeBar": True,
            "modeBarButtonsToRemove": ["select2d", "lasso2d", "autoScale2d"],
            "displaylogo": False,
        },
    )))),
    dbc.Row(dbc.Col(dcc.Loading(dcc.Graph(
        id="deep-dive-bar",
        config={"displayModeBar": False},
    ))), className="mt-2"),

    # Bar chart peer-pair detail (hidden until bar click)
    html.Div(id="deep-dive-bar-detail", className="mt-3"),

    # Control detail card (hidden until click)
    html.Div(id="deep-dive-control-card"),
], fluid=True)


@callback(
    Output("deep-dive-network", "figure"),
    Output("deep-dive-bar", "figure"),
    Output("deep-dive-breadcrumb", "children"),
    Input("deep-dive-framework", "value"),
    Input("deep-dive-entry-types", "value"),
    Input("deep-dive-zoom", "data"),
    Input("theme-store", "data"),
)
def update_deep_dive(framework, entry_types, zoom, theme):
    zoom = zoom or {"level": 0, "domain": None, "node_id": None}
    level = zoom.get("level", 0)

    # Build breadcrumb navigation
    crumbs = [
        html.Span(
            get_short_name(framework),
            style={"color": "#00d4ff" if level == 0 else "#6e7681",
                   "cursor": "pointer" if level > 0 else "default",
                   "fontSize": "0.85rem"},
            id="breadcrumb-root",
        ),
    ]
    if level >= 1 and zoom.get("domain"):
        crumbs.append(html.Span(" / ", style={"color": "#6e7681", "fontSize": "0.85rem"}))
        crumbs.append(html.Span(
            zoom["domain"],
            style={"color": "#00d4ff" if level == 1 else "#6e7681",
                   "cursor": "pointer" if level > 1 else "default",
                   "fontSize": "0.85rem"},
        ))
    if level >= 2 and zoom.get("node_id"):
        node = get_node_by_id(zoom["node_id"])
        if node:
            crumbs.append(html.Span(" / ", style={"color": "#6e7681", "fontSize": "0.85rem"}))
            crumbs.append(html.Span(
                node["local_id"],
                style={"color": "#00d4ff", "fontSize": "0.85rem"},
            ))
    breadcrumb = html.Div(crumbs, style={
        "padding": "6px 12px", "backgroundColor": "rgba(22,27,34,0.5)",
        "borderRadius": "6px", "border": "1px solid #21262d",
    })

    # Build the appropriate network level
    if level == 0:
        network = _build_level0(framework, entry_types, theme)
    elif level == 1:
        network = _build_level1(framework, zoom.get("domain", ""), entry_types, theme)
    elif level == 2:
        network = _build_level2(framework, zoom.get("node_id", ""), theme, expanded_fw=zoom.get("expanded_fw"))
    else:
        network = _build_level0(framework, entry_types, theme)

    bar = _build_mapping_bar(framework, theme)
    return network, bar, breadcrumb


@callback(
    Output("deep-dive-zoom", "data"),
    Output("deep-dive-control-card", "children"),
    Input("deep-dive-network", "clickData"),
    Input("deep-dive-framework", "value"),
    State("deep-dive-zoom", "data"),
    prevent_initial_call=True,
)
def handle_network_click(click_data, framework, zoom):
    """Handle clicks on the network graph -- navigate zoom levels."""
    triggered = ctx.triggered_id
    zoom = zoom or {"level": 0, "domain": None, "node_id": None, "expanded_fw": None}

    # Framework changed: reset to level 0
    if triggered == "deep-dive-framework":
        return {"level": 0, "domain": None, "node_id": None, "expanded_fw": None}, html.Div()

    if not click_data or "points" not in click_data:
        return dash.no_update, dash.no_update

    point = click_data["points"][0]
    customdata = point.get("customdata")
    if not customdata or not isinstance(customdata, dict):
        return dash.no_update, dash.no_update

    node_type = customdata.get("type")
    node_id = customdata.get("id")

    if node_type == "domain":
        # Drill into domain (level 0 -> 1)
        return {"level": 1, "domain": node_id, "node_id": None, "expanded_fw": None}, html.Div()

    if node_type == "control":
        # Drill into control (level 1 -> 2), also show detail card
        domain = zoom.get("domain")
        card = _build_control_card(node_id)
        return {"level": 2, "domain": domain, "node_id": node_id, "expanded_fw": None}, card

    if node_type in ("back_to_0", "root"):
        # Go back to overview
        return {"level": 0, "domain": None, "node_id": None, "expanded_fw": None}, html.Div()

    if node_type == "back_to_1":
        # Go back to domain view
        domain = zoom.get("domain")
        return {"level": 1, "domain": domain, "node_id": None, "expanded_fw": None}, html.Div()

    if node_type == "target_fw":
        # Toggle expand/collapse: clicking the same fw collapses, clicking a different fw expands
        source_node_id = zoom.get("node_id")
        if source_node_id:
            current_expanded = zoom.get("expanded_fw")
            new_expanded = None if node_id == current_expanded else node_id
            card = _build_target_fw_detail(source_node_id, node_id, framework) if new_expanded else html.Div()
            return {
                "level": 2,
                "domain": zoom.get("domain"),
                "node_id": source_node_id,
                "expanded_fw": new_expanded,
            }, card
        return dash.no_update, dash.no_update

    return dash.no_update, dash.no_update


@callback(
    Output("deep-dive-learn-more", "is_open"),
    Input("deep-dive-learn-toggle", "n_clicks"),
    State("deep-dive-learn-more", "is_open"),
    prevent_initial_call=True,
)
def toggle_deep_dive_learn_more(n_clicks, is_open):
    return not is_open


@callback(
    Output("deep-dive-bar-detail", "children"),
    Input("deep-dive-bar", "clickData"),
    State("deep-dive-framework", "value"),
    prevent_initial_call=True,
)
def handle_bar_click(click_data, framework):
    """Show a detail panel for the clicked peer framework pair in the mapping bar chart."""
    if not click_data or "points" not in click_data:
        return dash.no_update

    point = click_data["points"][0]
    raw_cd = point.get("customdata")

    # Outbound trace: customdata is the peer framework key (a string)
    # Inbound trace: customdata is [peer_key, abs_count] (a list)
    if isinstance(raw_cd, list):
        peer = raw_cd[0]
    elif isinstance(raw_cd, str):
        peer = raw_cd
    else:
        return dash.no_update

    if not peer or peer not in FRAMEWORK_KEYS:
        return dash.no_update

    edges_df = get_edges_df()
    cross = edges_df[edges_df["source_framework"] != edges_df["target_framework"]]

    pair_edges = cross[
        ((cross["source_framework"] == framework) & (cross["target_framework"] == peer))
        | ((cross["source_framework"] == peer) & (cross["target_framework"] == framework))
    ]

    total = len(pair_edges)
    outbound_n = len(pair_edges[pair_edges["source_framework"] == framework])
    inbound_n = len(pair_edges[pair_edges["source_framework"] == peer])

    fw_color = get_color(framework)
    peer_color = get_color(peer)

    # Header summary
    header_parts = [
        html.Span(
            get_short_name(framework),
            className="badge me-1",
            style={"backgroundColor": fw_color, "fontSize": "0.85rem"},
        ),
        html.Span(
            "\u2194",
            style={"color": "#8b949e", "margin": "0 4px"},
        ),
        html.Span(
            get_short_name(peer),
            className="badge me-2",
            style={"backgroundColor": peer_color, "fontSize": "0.85rem"},
        ),
        html.Strong(f"{total} total edges", style={"color": "#c9d1d9"}),
        html.Span(
            f"  ({outbound_n} outbound, {inbound_n} inbound)",
            className="text-muted ms-2",
            style={"fontSize": "0.85rem"},
        ),
    ]

    # Edge sample rows (up to 10)
    sample = pair_edges.head(10)
    rows = []
    for _, row in sample.iterrows():
        src_id = str(row.get("source_node_id", ""))
        tgt_id = str(row.get("target_node_id", ""))

        src_node = get_node_by_id(src_id)
        tgt_node = get_node_by_id(tgt_id)

        src_label = (
            f"{src_node['local_id']}: {src_node['name'][:35]}..."
            if src_node and len(src_node.get("name", "")) > 35
            else (f"{src_node['local_id']}: {src_node['name']}" if src_node else src_id)
        )
        tgt_label = (
            f"{tgt_node['local_id']}: {tgt_node['name'][:35]}..."
            if tgt_node and len(tgt_node.get("name", "")) > 35
            else (f"{tgt_node['local_id']}: {tgt_node['name']}" if tgt_node else tgt_id)
        )

        conf = str(row.get("confidence", "")).lower()
        conf_color = CONFIDENCE_COLORS.get(conf, "#6e7681")
        conf_badge = badge_with_tooltip(
            conf if conf else "unknown",
            color="secondary",
            class_name="ms-1",
            style={"backgroundColor": conf_color, "fontSize": "0.75rem"},
        )

        src_fw = str(row.get("source_framework", ""))
        direction_color = fw_color if src_fw == framework else peer_color

        rows.append(
            html.Div([
                html.Div([
                    html.Span(
                        "\u25b6 ",
                        style={"color": direction_color, "fontSize": "0.7rem"},
                    ),
                    html.Span(src_label, style={"color": "#c9d1d9", "fontSize": "0.82rem"}),
                ], style={"flex": "1", "minWidth": 0, "overflow": "hidden", "textOverflow": "ellipsis", "whiteSpace": "nowrap"}),
                html.Div([
                    html.Span("\u2192 ", style={"color": "#6e7681"}),
                    html.Span(tgt_label, style={"color": "#9eaab8", "fontSize": "0.82rem"}),
                    conf_badge,
                ], style={"flex": "1", "minWidth": 0, "overflow": "hidden", "textOverflow": "ellipsis", "whiteSpace": "nowrap"}),
            ], style={
                "display": "flex",
                "gap": "8px",
                "padding": "5px 8px",
                "borderBottom": "1px solid rgba(33,38,45,0.6)",
                "alignItems": "center",
            })
        )

    if total > 10:
        rows.append(html.Div(
            f"... and {total - 10} more edges",
            style={"fontSize": "0.8rem", "color": "#6e7681", "fontStyle": "italic",
                   "padding": "6px 8px"},
        ))

    return dbc.Card([
        dbc.CardHeader(
            html.Div(header_parts, style={"display": "flex", "alignItems": "center", "flexWrap": "wrap", "gap": "2px"}),
        ),
        dbc.CardBody(
            html.Div(rows, style={"padding": "0"}) if rows else html.P(
                "No edge details available.", className="text-muted mb-0",
            ),
            style={"padding": "0"},
        ),
    ], style={
        "backgroundColor": "rgba(22,27,34,0.5)",
        "borderLeft": f"4px solid {fw_color}",
    })
