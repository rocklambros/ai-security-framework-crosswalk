"""Page 1: Framework Landscape -- bird's-eye view of the AI security ecosystem."""

import dash
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from dash import Input, Output, State, callback, dcc, html

from components.badge_tooltips import badge_with_tooltip
from components.classifier_badge import (
    TIER_COLORS,
    TIER_FILTER_OPTIONS,
    TIER_NAMES,
    classifier_badge,
    filter_edges_by_tier,
)
from components.data_loader import get_edges_df, get_framework_stats, get_nodes_df, get_pairwise_reachability
from components.framework_colors import (
    FRAMEWORK_KEYS,
    get_color,
    get_display_name,
    get_short_name,
)
from components.plot_theme import get_template

dash.register_page(__name__, path="/", name="Landscape", order=0)

# --- Narrative ---
INTRO_TEXT = (
    "Organizations adopting AI systems must navigate overlapping security standards "
    "from OWASP, NIST, MITRE, CSA, and others, with no machine-readable crosswalks "
    "between them. This tool bridges that gap. Nine frameworks, 983 controls, "
    "6,154 relationship edges. Node size encodes framework breadth; edge width encodes "
    "cross-framework mapping density."
)

LEARN_MORE_CONTENT = [
    html.H6("Why Nine Frameworks?", className="mt-2 mb-1", style={"color": "#00d4ff"}),
    html.P(
        "AI security standards are fragmented. OWASP publishes two separate top-ten risk lists "
        "(one for LLM applications, one for agentic systems). MITRE maintains ATLAS, a tactic-and-technique "
        "catalogue modeled on ATT&CK. NIST publishes an outcome-oriented Risk Management Framework. CSA and "
        "AIUC-1 publish detailed control catalogues. The EU publishes policy commitments. Each is useful, each "
        "overlaps with the others, and none reference each other in a machine-readable way. "
        "This tool bridges that gap.",
        style={"fontSize": "0.85rem", "lineHeight": "1.7", "color": "#9eaab8"},
    ),
    html.H6("Reading the Network Graph", className="mt-2 mb-1", style={"color": "#00d4ff"}),
    html.P([
        "Each circle represents one framework. ",
        html.Strong("Size", style={"color": "#c9d1d9"}),
        " encodes node count (AIUC-1 has 189 controls, OWASP LLM has 10). ",
        html.Strong("Edge width", style={"color": "#c9d1d9"}),
        " encodes the number of cross-framework mappings between a pair. Thick edges (like AIUC-1 to CSA AICM) "
        "indicate dense overlap; thin or missing edges indicate sparse or no coverage. Hover over any node or "
        "edge for details.",
    ], style={"fontSize": "0.85rem", "lineHeight": "1.7", "color": "#9eaab8"}),
    html.H6("Reading the Heatmap", className="mt-2 mb-1", style={"color": "#00d4ff"}),
    html.P([
        "The 9x9 matrix shows bidirectional mapping counts. Use the ",
        html.Strong("Mapping Scope", style={"color": "#c9d1d9"}),
        " toggle to switch views: ",
        html.Strong("Direct edges", style={"color": "#c9d1d9"}),
        " counts only explicit mapped relationships (matching the research notebook Figure 4.1). ",
        html.Strong("All reachability", style={"color": "#c9d1d9"}),
        " counts unique node pairs reachable via direct or transitive (2-hop) paths through "
        "bridge frameworks. Some framework pairs (e.g., ATLAS and CSA AICM) have zero direct "
        "edges but hundreds of transitive connections via AIUC-1 or other bridges.",
    ], style={"fontSize": "0.85rem", "lineHeight": "1.7", "color": "#9eaab8"}),
    html.H6("Using the Filters", className="mt-2 mb-1", style={"color": "#00d4ff"}),
    html.P([
        html.Strong("Confidence: ", style={"color": "#c9d1d9"}),
        "Authoritative mappings come from official source documents. Expert mappings are validated by domain "
        "review. Suggestive mappings are inferred from shared categories or semantic similarity. Filtering to "
        "'Expert+' removes lower-confidence edges and shows a more conservative view of framework relationships.",
        html.Br(), html.Br(),
        html.Strong("Relationship type: ", style={"color": "#c9d1d9"}),
        "'Rationale-coded' shows only edges with specific security rationale (SCOPE, DETECT, GOVERN, etc.). "
        "'Category links' shows edges that connect controls sharing a topical category.",
    ], style={"fontSize": "0.85rem", "lineHeight": "1.7", "color": "#9eaab8"}),
]


def _build_network_figure(edges_df, stats, theme="dark", selected_fw=None):
    """Build the framework supernode network graph.

    When selected_fw is set, highlight that framework's connections and dim others.

    Encoding: categorical framework colors for nominal identity (Borner et al.
    2019). Node size encodes framework breadth via area (Cleveland & McGill 1984,
    rank 4), acceptable for navigational networks where the primary task is
    exploration, not precise comparison. Edge width encodes mapping density.
    """
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

    # Build separate pair counts by edge type
    rationale_counts = {}
    category_counts = {}
    for _, row in edges_df.iterrows():
        src_fw = row["source_framework"]
        tgt_fw = row["target_framework"]
        if src_fw != tgt_fw:
            key = tuple(sorted([src_fw, tgt_fw]))
            if row.get("rationale_code") == "CROSS_FRAMEWORK_CATEGORY":
                category_counts[key] = category_counts.get(key, 0) + 1
            else:
                rationale_counts[key] = rationale_counts.get(key, 0) + 1

    # Combined totals for connected-framework logic
    all_pair_counts = {}
    for key in set(list(rationale_counts.keys()) + list(category_counts.keys())):
        all_pair_counts[key] = rationale_counts.get(key, 0) + category_counts.get(key, 0)

    # Determine which frameworks are connected to selected
    connected_fws = set()
    if selected_fw:
        connected_fws.add(selected_fw)
        for (fw1, fw2) in all_pair_counts:
            if fw1 == selected_fw:
                connected_fws.add(fw2)
            elif fw2 == selected_fw:
                connected_fws.add(fw1)

    # Draw rationale edges (solid cyan)
    for (fw1, fw2), count in rationale_counts.items():
        if fw1 in positions and fw2 in positions:
            x0, y0 = positions[fw1]
            x1, y1 = positions[fw2]
            width = max(1, min(count / 100, 12))

            if selected_fw:
                is_connected = fw1 == selected_fw or fw2 == selected_fw
                if is_connected:
                    edge_color = "rgba(0, 212, 255, 0.80)"
                    width = max(2, width * 1.3)
                else:
                    edge_color = "rgba(0, 212, 255, 0.06)"
                    width = max(0.5, width * 0.5)
            else:
                edge_color = "rgba(0, 212, 255, 0.50)"

            edge_traces.append(go.Scatter(
                x=[x0, x1, None],
                y=[y0, y1, None],
                mode="lines",
                line=dict(width=width, color=edge_color),
                hoverinfo="text",
                text=f"{get_short_name(fw1)} - {get_short_name(fw2)}: {count} rationale mappings",
                showlegend=False,
            ))

    # Draw category edges (dashed gold/amber)
    for (fw1, fw2), count in category_counts.items():
        if fw1 in positions and fw2 in positions:
            x0, y0 = positions[fw1]
            x1, y1 = positions[fw2]
            width = max(1, min(count / 100, 8))

            if selected_fw:
                is_connected = fw1 == selected_fw or fw2 == selected_fw
                if is_connected:
                    edge_color = "rgba(217, 191, 85, 0.80)"
                    width = max(2, width * 1.3)
                else:
                    edge_color = "rgba(217, 191, 85, 0.06)"
                    width = max(0.5, width * 0.5)
            else:
                edge_color = "rgba(217, 191, 85, 0.50)"

            edge_traces.append(go.Scatter(
                x=[x0, x1, None],
                y=[y0, y1, None],
                mode="lines",
                line=dict(width=width, color=edge_color, dash="dot"),
                hoverinfo="text",
                text=f"{get_short_name(fw1)} - {get_short_name(fw2)}: {count} category links",
                showlegend=False,
            ))

    # Node trace
    node_x = [positions[fw][0] for fw in fw_list]
    node_y = [positions[fw][1] for fw in fw_list]
    node_sizes = [max(20, stats[fw]["node_count"] / 3) for fw in fw_list]

    if selected_fw:
        node_colors = [
            get_color(fw) if fw in connected_fws else "rgba(110,118,129,0.3)"
            for fw in fw_list
        ]
        node_opacities = [1.0 if fw in connected_fws else 0.3 for fw in fw_list]
        border_colors = [
            "#00d4ff" if fw == selected_fw else "rgba(0,212,255,0.3)"
            for fw in fw_list
        ]
        border_widths = [4 if fw == selected_fw else 2 for fw in fw_list]
    else:
        node_colors = [get_color(fw) for fw in fw_list]
        node_opacities = [1.0] * n
        border_colors = ["rgba(0,212,255,0.3)"] * n
        border_widths = [2] * n

    node_text = [
        f"<b>{get_display_name(fw)}</b><br>"
        f"Nodes: {stats[fw]['node_count']}<br>"
        f"Edges out: {stats[fw]['edge_count_out']}<br>"
        f"Edges in: {stats[fw]['edge_count_in']}<br>"
        f"<i>{'Click to deselect' if fw == selected_fw else 'Click to highlight connections'}</i>"
        for fw in fw_list
    ]

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers+text",
        marker=dict(
            size=node_sizes, color=node_colors, opacity=node_opacities,
            line=dict(width=border_widths, color=border_colors),
        ),
        text=[get_short_name(fw) for fw in fw_list],
        textposition="top center",
        textfont=dict(size=11),
        hovertext=node_text,
        hoverinfo="text",
        customdata=fw_list,
        showlegend=False,
    )

    # Add edge count labels at midpoints for significant edges
    for pair_key in set(list(rationale_counts.keys()) + list(category_counts.keys())):
        fw1, fw2 = pair_key
        total = all_pair_counts.get(pair_key, 0)
        if fw1 in positions and fw2 in positions and total >= 25:
            x0, y0 = positions[fw1]
            x1, y1 = positions[fw2]
            mx, my = (x0 + x1) / 2, (y0 + y1) / 2
            label_opacity = 0.9
            if selected_fw:
                is_connected = fw1 == selected_fw or fw2 == selected_fw
                label_opacity = 0.9 if is_connected else 0.15
            r_count = rationale_counts.get(pair_key, 0)
            c_count = category_counts.get(pair_key, 0)
            if r_count and c_count:
                label = f"{r_count}+{c_count}"
            else:
                label = str(total)
            edge_traces.append(go.Scatter(
                x=[mx], y=[my],
                mode="text",
                text=[label],
                textfont=dict(size=8, color=f"rgba(201,209,217,{label_opacity})"),
                hoverinfo="skip",
                showlegend=False,
            ))

    title_text = "Framework Relationship Network"
    if selected_fw:
        title_text += f" (highlighting {get_short_name(selected_fw)})"

    fig = go.Figure(data=edge_traces + [node_trace])
    fig.update_layout(
        template=get_template(theme),
        xaxis=dict(visible=False, range=[-1.5, 1.5]),
        yaxis=dict(visible=False, range=[-1.5, 1.5], scaleanchor="x"),
        height=550,
        title=dict(text=title_text, font=dict(size=14)),
        hovermode="closest",
        dragmode="pan",
    )
    fig.add_annotation(
        x=0.5,
        y=-0.06,
        xref="paper",
        yref="paper",
        text=(
            "<span style='color:rgba(0,212,255,0.85)'>&#9135;&#9135;</span> Rationale-coded "
            "&nbsp;&nbsp;"
            "<span style='color:rgba(217,191,85,0.85)'>&#183;&#183;&#183;</span> Category links"
        ),
        showarrow=False,
        font=dict(size=11, color="#9eaab8"),
        align="center",
        xanchor="center",
        yanchor="top",
    )
    return fig


def _build_heatmap_figure(edges_df, theme="dark", scope="direct"):
    """Build the 9x9 pairwise mapping density heatmap (direction-agnostic).

    Both modes count unique unordered node pairs so values are directly
    comparable when toggling scope.

    scope="direct": unique node pairs connected by at least one direct edge.
    scope="reachable": unique node pairs reachable via direct OR transitive
    (2-hop) paths from pre-computed reachability data.

    Encoding: sequential single-hue luminance ramp for ratio data (Borland &
    Taylor 2007; Borner et al. 2019). Cell-value annotations provide direct
    labeling to supplement color saturation (Cleveland rank 6) with precise
    numeric readout. Dark theme uses a blue luminance ramp; light theme uses
    a complementary blue ramp.
    """
    fw_list = FRAMEWORK_KEYS
    short_names = [get_short_name(fw) for fw in fw_list]
    fw_idx = {fw: i for i, fw in enumerate(fw_list)}

    matrix = [[0] * len(fw_list) for _ in range(len(fw_list))]

    if scope == "reachable":
        # Use pre-computed pairwise reachability (direct + transitive)
        reachability = get_pairwise_reachability()
        for fw_a in fw_list:
            if fw_a not in reachability:
                continue
            for fw_b in fw_list:
                if fw_b == fw_a or fw_b not in reachability[fw_a]:
                    continue
                i, j = fw_idx[fw_a], fw_idx[fw_b]
                matrix[i][j] = reachability[fw_a][fw_b]["total"]
        title_text = "Pairwise Reachability (direct + transitive)"
    else:
        # Count unique unordered node pairs with direct cross-framework edges.
        # This deduplicates bidirectional edges (A->B and B->A for the same
        # node pair count as 1) so values are comparable with reachable mode.
        from collections import defaultdict
        pair_sets = defaultdict(set)
        for _, row in edges_df.iterrows():
            src_fw = row["source_framework"]
            tgt_fw = row["target_framework"]
            if src_fw in fw_idx and tgt_fw in fw_idx and src_fw != tgt_fw:
                fw_pair = tuple(sorted([src_fw, tgt_fw]))
                node_pair = tuple(sorted([row["source_node_id"], row["target_node_id"]]))
                pair_sets[fw_pair].add(node_pair)
        for (fw_a, fw_b), pairs in pair_sets.items():
            i, j = fw_idx[fw_a], fw_idx[fw_b]
            matrix[i][j] = len(pairs)
            matrix[j][i] = len(pairs)
        title_text = "Pairwise Mapping Density (unique node pairs, direct edges)"

    # Sequential single-hue blue luminance ramp (Borland & Taylor 2007).
    # Monotonically increasing luminance so density magnitude is perceptually
    # ordered. Avoids the multi-hue rainbow problem.
    if theme == "dark":
        colorscale = [
            [0, "#0d1117"],      # Near-black (zero density recedes)
            [0.25, "#0d2847"],   # Very dark blue
            [0.5, "#1a4f7a"],    # Medium blue
            [0.75, "#2878ad"],   # Bright blue
            [1, "#3aa5de"],      # Light blue (highest density)
        ]
    else:
        colorscale = [[0, "#f6f8fa"], [0.3, "#a8d8f0"], [0.6, "#1f6feb"], [1, "#0550ae"]]

    # Build hover text with breakdown when showing reachability
    if scope == "reachable":
        reachability = get_pairwise_reachability()
        hover_text = [[None] * len(fw_list) for _ in range(len(fw_list))]
        for i, fw_a in enumerate(fw_list):
            for j, fw_b in enumerate(fw_list):
                if fw_a == fw_b:
                    hover_text[i][j] = ""
                    continue
                r = reachability.get(fw_a, {}).get(fw_b, {})
                d = r.get("direct", 0)
                t = r.get("transitive", 0)
                hover_text[i][j] = (
                    f"<b>{short_names[i]}</b> - <b>{short_names[j]}</b><br>"
                    f"Total: {d + t} node pairs<br>"
                    f"Direct: {d} / Transitive: {t}"
                )
        fig = go.Figure(data=go.Heatmap(
            z=matrix,
            x=short_names,
            y=short_names,
            colorscale=colorscale,
            colorbar=dict(title="Node pairs"),
            hovertext=hover_text,
            hovertemplate="%{hovertext}<extra></extra>",
        ))
    else:
        fig = go.Figure(data=go.Heatmap(
            z=matrix,
            x=short_names,
            y=short_names,
            colorscale=colorscale,
            colorbar=dict(title="Node pairs"),
            hovertemplate=(
                "<b>%{y}</b> - <b>%{x}</b><br>"
                "Unique node pairs: %{z}<br>"
                "<extra></extra>"
            ),
        ))

    # Add text annotations showing counts in each cell
    for i in range(len(fw_list)):
        for j in range(len(fw_list)):
            val = matrix[i][j]
            if val > 0:
                fig.add_annotation(
                    x=short_names[j], y=short_names[i],
                    text=str(val),
                    showarrow=False,
                    font=dict(size=9, color="#ffffff" if val > 50 else "#c9d1d9"),
                )

    fig.update_layout(
        template=get_template(theme),
        height=550,
        title=dict(text=title_text, font=dict(size=14)),
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
            html.P(INTRO_TEXT, className="text-muted mb-2", style={"fontSize": "0.9rem"}),
            html.A("Learn more about the landscape view", id="landscape-learn-toggle",
                   style={"fontSize": "0.85rem", "cursor": "pointer", "color": "#00d4ff",
                          "textDecoration": "none"}),
            dbc.Collapse(html.Div(LEARN_MORE_CONTENT, className="mt-2"),
                         id="landscape-learn-more", is_open=False),
        ]), className="mb-3 border-0",
        style={"backgroundColor": "rgba(22,27,34,0.5)"}),
    )),

    # Filters
    dbc.Row([
        dbc.Col([
            dbc.Label([
                "Confidence Level ",
                html.I(className="bi bi-info-circle", id="confidence-tooltip-target",
                       style={"cursor": "pointer", "color": "#00d4ff"}),
            ], html_for="landscape-confidence",
                      className="text-muted", style={"fontSize": "0.8rem"}),
            dbc.Tooltip(
                [
                    html.Div([html.Strong("Any"), ": Include all mappings regardless of confidence."], style={"marginBottom": "4px"}),
                    html.Div([html.Strong("Suggestive+"), ": Include suggestive (inferred from shared categories), expert, and authoritative mappings."], style={"marginBottom": "4px"}),
                    html.Div([html.Strong("Expert+"), ": Include only expert-validated and authoritative mappings. More conservative view."], style={"marginBottom": "4px"}),
                    html.Div([html.Strong("Authoritative"), ": Only mappings from official framework source documents."]),
                ],
                target="confidence-tooltip-target",
                placement="bottom",
                style={"maxWidth": "350px", "textAlign": "left"},
            ),
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
            dbc.Label([
                "Relationship Type ",
                html.I(className="bi bi-info-circle", id="reltype-tooltip-target",
                       style={"cursor": "pointer", "color": "#00d4ff"}),
            ], html_for="landscape-edge-type",
                      className="text-muted", style={"fontSize": "0.8rem"}),
            dbc.Tooltip(
                "Rationale-coded: edges with a specific security rationale "
                "(SCOPE, DETECT, GOVERN, ISOLATE, etc.). "
                "Category links: edges connecting controls that share a topical category "
                "(e.g., both tagged 'privacy' or 'access control').",
                target="reltype-tooltip-target",
                placement="bottom",
            ),
            dbc.RadioItems(
                id="landscape-edge-type",
                options=[
                    {"label": html.Span([
                        "All",
                        html.Span(" \u24d8", id="edge-type-all-tip", style={"cursor": "help", "color": "#6e7681", "fontSize": "0.75rem"}),
                        dbc.Tooltip("Show all cross-framework edges regardless of type.", target="edge-type-all-tip", placement="top"),
                    ]), "value": "all"},
                    {"label": html.Span([
                        "Rationale-coded",
                        html.Span(" \u24d8", id="edge-type-rationale-tip", style={"cursor": "help", "color": "#6e7681", "fontSize": "0.75rem"}),
                        dbc.Tooltip("Edges with a specific security rationale: SCOPE, DETECT, GOVERN, ISOLATE, PREV, GATE, etc. These represent validated semantic relationships between controls.", target="edge-type-rationale-tip", placement="top"),
                    ]), "value": "rationale"},
                    {"label": html.Span([
                        "Category links",
                        html.Span(" \u24d8", id="edge-type-category-tip", style={"cursor": "help", "color": "#6e7681", "fontSize": "0.75rem"}),
                        dbc.Tooltip("Edges connecting controls that share a topical category (e.g., both tagged 'privacy' or 'access control'). Shown as gold dashed lines on the network.", target="edge-type-category-tip", placement="top"),
                    ]), "value": "category"},
                ],
                value="all",
                inline=True,
                className="mb-2",
                inputStyle={"marginRight": "4px"},
                labelStyle={"marginRight": "16px", "fontSize": "0.85rem"},
            ),
        ], md=8),
    ], className="mb-3"),

    # Classifier tier filter row
    dbc.Row([
        dbc.Col([
            dbc.Label([
                "ML Classifier Tier ",
                html.I(className="bi bi-info-circle", id="classifier-tier-tooltip-target",
                       style={"cursor": "pointer", "color": "#d4a017"}),
            ], html_for="landscape-classifier-tier",
                      className="text-muted", style={"fontSize": "0.8rem"}),
            dbc.Tooltip(
                [
                    html.Div("A fine-tuned transformer ensemble (RoBERTa + DeBERTa + BGE) classifies "
                             "each edge into one of four semantic similarity tiers.", style={"marginBottom": "6px"}),
                    html.Div([html.Strong("Equivalent"), ": Controls address the same concern with the same scope."], style={"marginBottom": "3px"}),
                    html.Div([html.Strong("Related"), ": Controls address overlapping concerns."], style={"marginBottom": "3px"}),
                    html.Div([html.Strong("Partial"), ": One control partially covers the other."], style={"marginBottom": "3px"}),
                    html.Div([html.Strong("Unrelated"), ": No meaningful semantic overlap."]),
                ],
                target="classifier-tier-tooltip-target",
                placement="bottom",
                style={"maxWidth": "380px", "textAlign": "left"},
            ),
            dbc.RadioItems(
                id="landscape-classifier-tier",
                options=TIER_FILTER_OPTIONS,
                value="any",
                inline=True,
                className="mb-2",
                inputStyle={"marginRight": "4px"},
                labelStyle={"marginRight": "16px", "fontSize": "0.85rem"},
            ),
        ], md=12),
    ], className="mb-3"),

    # Selected framework state for network highlighting
    dcc.Store(id="landscape-selected-fw", data=None),

    # Network graph (full width, zoomable/pannable)
    dbc.Row(dbc.Col(dcc.Loading(dcc.Graph(
        id="landscape-network",
        config={
            "scrollZoom": True,
            "displayModeBar": True,
            "modeBarButtonsToRemove": ["select2d", "lasso2d", "autoScale2d"],
            "displaylogo": False,
        },
    )))),

    # Heatmap scope toggle + chart
    dbc.Row(dbc.Col([
        dbc.Label([
            "Mapping Scope ",
            html.I(className="bi bi-info-circle", id="heatmap-scope-tooltip-target",
                   style={"cursor": "pointer", "color": "#00d4ff"}),
        ], html_for="landscape-heatmap-scope",
                  className="text-muted mt-3", style={"fontSize": "0.8rem"}),
        dbc.Tooltip(
            "Direct edges: counts only explicit mapped relationships between framework pairs. "
            "All reachability: counts unique node pairs reachable via direct or transitive "
            "(2-hop) paths through bridge frameworks.",
            target="heatmap-scope-tooltip-target",
            placement="right",
        ),
        dbc.RadioItems(
            id="landscape-heatmap-scope",
            options=[
                {"label": "Direct edges", "value": "direct"},
                {"label": "All reachability (direct + transitive)", "value": "reachable"},
            ],
            value="direct",
            inline=True,
            className="mb-2",
            inputStyle={"marginRight": "4px"},
            labelStyle={"marginRight": "16px", "fontSize": "0.85rem"},
        ),
        dcc.Loading(dcc.Graph(
            id="landscape-heatmap",
            config={"displayModeBar": False},
        )),
    ])),

    # Heatmap cell detail panel (shown on click)
    dbc.Row(dbc.Col(
        html.Div(id="landscape-heatmap-detail", className="mt-3"),
    )),

    # Store for heatmap pair state (fw_y, fw_x, shown count)
    dcc.Store(id="landscape-heatmap-pair", data=None),

    # Summary stats
    dbc.Row(dbc.Col(
        html.Div(id="landscape-stats", className="mt-3"),
    )),

    # ML Classifier Analysis (collapsible)
    dbc.Row(dbc.Col([
        html.Hr(style={"borderColor": "#21262d", "margin": "1.5rem 0 0.5rem"}),
        html.A([
            html.H5([
                "ML Classifier Analysis ",
                html.Small("(click to expand)", className="text-muted",
                           style={"fontSize": "0.75rem"}),
            ], className="mb-0", style={"color": "#d4a017"}),
        ], id="landscape-classifier-toggle",
           style={"cursor": "pointer", "textDecoration": "none"}),
        html.P(
            "A fine-tuned ensemble of three transformer models (RoBERTa-large, DeBERTa-base, "
            "BGE-large-v1.5) classifies each mapping edge into four semantic similarity tiers. "
            "The classifier achieves 80% tier accuracy and 0.56 macro F1 on expert-labeled test pairs.",
            className="text-muted mb-2",
            style={"fontSize": "0.85rem"},
        ),
        dbc.Collapse([
            dbc.Row([
                dbc.Col(dcc.Loading(dcc.Graph(
                    id="landscape-classifier-histogram",
                    config={"displayModeBar": False},
                )), md=6),
                dbc.Col(dcc.Loading(dcc.Graph(
                    id="landscape-classifier-tier-bar",
                    config={"displayModeBar": False},
                )), md=6),
            ]),
        ], id="landscape-classifier-collapse", is_open=False),
    ])),

], fluid=True)


@callback(
    Output("landscape-network", "figure"),
    Output("landscape-heatmap", "figure"),
    Output("landscape-stats", "children"),
    Input("landscape-confidence", "value"),
    Input("landscape-edge-type", "value"),
    Input("landscape-selected-fw", "data"),
    Input("theme-store", "data"),
    Input("landscape-heatmap-scope", "value"),
    Input("landscape-classifier-tier", "value"),
)
def update_landscape(confidence, edge_type, selected_fw, theme, heatmap_scope, classifier_tier):
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

    edges_df = filter_edges_by_tier(edges_df, classifier_tier or "any")

    cross = edges_df[edges_df["source_framework"] != edges_df["target_framework"]]

    network_fig = _build_network_figure(edges_df, stats, theme, selected_fw=selected_fw)
    heatmap_fig = _build_heatmap_figure(edges_df, theme, scope=heatmap_scope or "direct")

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


@callback(
    Output("landscape-selected-fw", "data"),
    Input("landscape-network", "clickData"),
    State("landscape-selected-fw", "data"),
    prevent_initial_call=True,
)
def handle_network_click(click_data, current_selected):
    """Toggle framework highlight on network node click."""
    if not click_data or "points" not in click_data:
        return dash.no_update
    point = click_data["points"][0]
    clicked_fw = point.get("customdata")
    if not clicked_fw:
        return dash.no_update
    # Toggle: click same framework again to deselect
    if clicked_fw == current_selected:
        return None
    return clicked_fw


@callback(
    Output("landscape-learn-more", "is_open"),
    Input("landscape-learn-toggle", "n_clicks"),
    State("landscape-learn-more", "is_open"),
    prevent_initial_call=True,
)
def toggle_landscape_learn_more(n_clicks, is_open):
    return not is_open


@callback(
    Output("landscape-classifier-collapse", "is_open"),
    Input("landscape-classifier-toggle", "n_clicks"),
    State("landscape-classifier-collapse", "is_open"),
    prevent_initial_call=True,
)
def toggle_classifier_section(n_clicks, is_open):
    return not is_open


def _build_confidence_histogram(edges_df, theme="dark"):
    """Histogram of classifier confidence scores, colored by predicted tier."""
    fig = go.Figure()
    for tier in [3, 2, 1, 0]:
        name = TIER_NAMES[tier]
        color = TIER_COLORS[tier]
        subset = edges_df[edges_df["classifier_tier"] == tier]
        if subset.empty:
            continue
        fig.add_trace(go.Histogram(
            x=subset["classifier_confidence"],
            name=name,
            marker_color=color,
            opacity=0.75,
            nbinsx=30,
        ))
    fig.update_layout(
        template=get_template(theme),
        barmode="overlay",
        height=400,
        title=dict(text="Confidence Distribution by Tier", font=dict(size=13)),
        xaxis_title="Classifier Confidence",
        yaxis_title="Edge Count",
        legend=dict(orientation="h", yanchor="bottom", y=-0.25),
        margin=dict(t=40, b=60),
    )
    return fig


def _build_tier_by_fw_pair(edges_df, theme="dark"):
    """Stacked bar: tier counts for each cross-framework pair."""
    from collections import Counter

    cross = edges_df[
        (edges_df["source_framework"] != edges_df["target_framework"])
        & (edges_df["classifier_tier"] >= 0)
    ]
    pair_tier_counts: dict[tuple, Counter] = {}
    for _, row in cross.iterrows():
        pair = tuple(sorted([row["source_framework"], row["target_framework"]]))
        tier = int(row["classifier_tier"])
        if pair not in pair_tier_counts:
            pair_tier_counts[pair] = Counter()
        pair_tier_counts[pair][tier] += 1

    pairs_sorted = sorted(
        pair_tier_counts.keys(),
        key=lambda p: sum(pair_tier_counts[p][t] for t in [1, 2, 3]),
        reverse=True,
    )[:15]
    pair_labels = [f"{get_short_name(p[0])} × {get_short_name(p[1])}" for p in pairs_sorted]

    fig = go.Figure()
    for tier in [3, 2, 1, 0]:
        counts = [pair_tier_counts[p].get(tier, 0) for p in pairs_sorted]
        fig.add_trace(go.Bar(
            y=pair_labels,
            x=counts,
            name=TIER_NAMES[tier],
            orientation="h",
            marker_color=TIER_COLORS[tier],
        ))
    fig.update_layout(
        template=get_template(theme),
        barmode="stack",
        height=400,
        title=dict(text="Tier Distribution by Framework Pair", font=dict(size=13)),
        xaxis_title="Edge Count",
        yaxis=dict(categoryorder="array", categoryarray=list(reversed(pair_labels))),
        legend=dict(orientation="h", yanchor="bottom", y=-0.25),
        margin=dict(t=40, b=60),
    )
    return fig


@callback(
    Output("landscape-classifier-histogram", "figure"),
    Output("landscape-classifier-tier-bar", "figure"),
    Input("landscape-classifier-collapse", "is_open"),
    Input("landscape-confidence", "value"),
    Input("landscape-edge-type", "value"),
    Input("theme-store", "data"),
)
def update_classifier_charts(is_open, confidence, edge_type, theme):
    if not is_open:
        empty = go.Figure()
        empty.update_layout(height=100)
        return empty, empty

    edges_df = get_edges_df()
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

    return (
        _build_confidence_histogram(edges_df, theme),
        _build_tier_by_fw_pair(edges_df, theme),
    )


def _render_heatmap_detail(fw_y, fw_x, pair_df, shown_count):
    """Render the heatmap detail card showing up to shown_count edges.

    Returns (card_component, updated_pair_data_dict).
    """
    total_count = len(pair_df)
    fw_y_display = get_display_name(fw_y)
    fw_x_display = get_display_name(fw_x)

    if total_count == 0:
        card = dbc.Card(
            dbc.CardBody(html.P(
                f"No mappings found between {get_short_name(fw_y)} and {get_short_name(fw_x)} "
                "under current filters.",
                className="text-muted mb-0",
                style={"fontSize": "0.85rem"},
            )),
            className="mt-2",
            style={
                "backgroundColor": "rgba(22,27,34,0.5)",
                "borderLeft": "3px solid #00d4ff",
                "border": "1px solid rgba(0,212,255,0.2)",
            },
        )
        return card

    conf_color_map = {
        "authoritative": "success",
        "expert": "info",
        "suggestive": "warning",
        "unvalidated": "secondary",
    }

    sample = pair_df.head(shown_count)
    edge_rows = []
    for _, row in sample.iterrows():
        src_id = str(row.get("source_node_id", ""))
        tgt_id = str(row.get("target_node_id", ""))
        src_short_id = src_id.split("/")[-1] if "/" in src_id else src_id
        tgt_short_id = tgt_id.split("/")[-1] if "/" in tgt_id else tgt_id

        conf_val = str(row.get("confidence", "")).lower()
        conf_badge_color = conf_color_map.get(conf_val, "secondary")

        rationale = str(row.get("rationale_code", "")) if row.get("rationale_code") else ""
        rationale_badge = (
            badge_with_tooltip(rationale, color="secondary", class_name="ms-1",
                               style={"opacity": "0.85"})
            if rationale else None
        )

        edge_rows.append(html.Div([
            html.Span(src_short_id, style={"color": get_color(row.get("source_framework", "")),
                                           "fontFamily": "monospace", "fontSize": "0.8rem"}),
            html.Span(" -> ", style={"color": "#9eaab8", "fontSize": "0.8rem"}),
            html.Span(tgt_short_id, style={"color": get_color(row.get("target_framework", "")),
                                           "fontFamily": "monospace", "fontSize": "0.8rem"}),
            html.Span(" "),
            badge_with_tooltip(conf_val, color=conf_badge_color, class_name="ms-1"),
            rationale_badge,
            classifier_badge(row.get("classifier_tier"), row.get("classifier_confidence")),
        ], className="mb-1"))

    remaining = total_count - shown_count
    show_more_btn = None
    if remaining > 0:
        load_next = min(10, remaining)
        show_more_btn = html.Div(
            dbc.Button(
                f"Show {load_next} more ({remaining} remaining)",
                id="landscape-show-more-btn",
                color="info",
                outline=True,
                size="sm",
                className="mt-2",
                style={"fontSize": "0.78rem"},
            ),
            className="mt-1",
        )

    card = dbc.Card(
        dbc.CardBody([
            html.Div([
                html.Span(
                    fw_y_display,
                    style={"color": get_color(fw_y), "fontWeight": "600", "fontSize": "0.95rem"},
                ),
                html.Span(" x ", style={"color": "#9eaab8", "fontSize": "0.95rem"}),
                html.Span(
                    fw_x_display,
                    style={"color": get_color(fw_x), "fontWeight": "600", "fontSize": "0.95rem"},
                ),
                dbc.Badge(
                    f"{total_count} mapping{'s' if total_count != 1 else ''}",
                    color="info",
                    className="ms-2",
                    style={"fontSize": "0.78rem", "verticalAlign": "middle"},
                ),
            ], className="mb-2"),
            html.Hr(style={"borderColor": "rgba(0,212,255,0.2)", "margin": "0.4rem 0 0.6rem"}),
            html.Div(edge_rows),
            show_more_btn,
        ]),
        className="mt-2",
        style={
            "backgroundColor": "rgba(22,27,34,0.5)",
            "borderLeft": f"3px solid {get_color(fw_y)}",
            "border": "1px solid rgba(0,212,255,0.2)",
        },
    )

    return card


def _filter_edges(edges_df, confidence, edge_type):
    """Apply confidence and edge-type filters to the edges dataframe."""
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

    return edges_df


def _get_pair_df(edges_df, fw_y, fw_x):
    """Return bidirectional edge subset for the given framework pair."""
    pair_mask = (
        ((edges_df["source_framework"] == fw_y) & (edges_df["target_framework"] == fw_x))
        | ((edges_df["source_framework"] == fw_x) & (edges_df["target_framework"] == fw_y))
    )
    return edges_df[pair_mask].copy()


@callback(
    Output("landscape-heatmap-detail", "children", allow_duplicate=True),
    Output("landscape-heatmap-pair", "data"),
    Input("landscape-heatmap", "clickData"),
    State("landscape-confidence", "value"),
    State("landscape-edge-type", "value"),
    State("theme-store", "data"),
    prevent_initial_call=True,
)
def handle_heatmap_click(click_data, confidence, edge_type, theme):
    """Show a detail panel when a heatmap cell is clicked."""
    if not click_data or "points" not in click_data:
        return dash.no_update, dash.no_update

    point = click_data["points"][0]
    x_short = point.get("x")  # target framework short name
    y_short = point.get("y")  # source framework short name

    if not x_short or not y_short or x_short == y_short:
        return dash.no_update, dash.no_update

    # Reverse-map short names to framework keys
    short_to_key = {get_short_name(fw): fw for fw in FRAMEWORK_KEYS}
    fw_x = short_to_key.get(x_short)
    fw_y = short_to_key.get(y_short)

    if not fw_x or not fw_y:
        return dash.no_update, dash.no_update

    edges_df = _filter_edges(get_edges_df(), confidence, edge_type)
    pair_df = _get_pair_df(edges_df, fw_y, fw_x)

    shown_count = 10
    card = _render_heatmap_detail(fw_y, fw_x, pair_df, shown_count)
    pair_data = {"fw_y": fw_y, "fw_x": fw_x, "shown": shown_count}

    return card, pair_data


@callback(
    Output("landscape-heatmap-detail", "children", allow_duplicate=True),
    Output("landscape-heatmap-pair", "data", allow_duplicate=True),
    Input("landscape-show-more-btn", "n_clicks"),
    State("landscape-heatmap-pair", "data"),
    State("landscape-confidence", "value"),
    State("landscape-edge-type", "value"),
    prevent_initial_call=True,
)
def show_more_edges(n_clicks, pair_data, confidence, edge_type):
    """Load 10 more edges in the heatmap detail panel."""
    if not pair_data:
        return dash.no_update, dash.no_update

    fw_y = pair_data.get("fw_y")
    fw_x = pair_data.get("fw_x")
    shown_count = pair_data.get("shown", 10)

    if not fw_y or not fw_x:
        return dash.no_update, dash.no_update

    edges_df = _filter_edges(get_edges_df(), confidence, edge_type)
    pair_df = _get_pair_df(edges_df, fw_y, fw_x)

    shown_count = shown_count + 10
    card = _render_heatmap_detail(fw_y, fw_x, pair_df, shown_count)
    updated_pair_data = {"fw_y": fw_y, "fw_x": fw_x, "shown": shown_count}

    return card, updated_pair_data
