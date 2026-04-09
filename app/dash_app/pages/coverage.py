"""Page 2 — Coverage Dashboard.

Four charts:
  1. Coverage Heatmap    — source framework × target framework, coverage fraction
  2. Per-Framework Bars  — coverage % per framework, traffic-light colours
  3. Mapping Flow Sankey — source frameworks → tiers → target frameworks
  4. Summary KPI cards   — framework count, mapping count, control count

Public surface:
    layout()                  → Dash component tree
    register_callbacks(app)   → wires the theme-toggle callback
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any

import plotly.graph_objects as go
from dash import Input, Output, callback, dcc, html
import dash_bootstrap_components as dbc

from app.dash_app.data.loader import load_all_mappings, load_framework_metadata
from app.dash_app.data.frameworks import FRAMEWORK_LABELS, TIER_COLORS

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_HEATMAP_COLORSCALE = [
    [0.0, "#da3633"],
    [0.5, "#d29922"],
    [1.0, "#3fb950"],
]

_COVERAGE_THRESHOLDS = {
    "high": 0.60,    # >= 60 % → green
    "medium": 0.30,  # >= 30 % → yellow
}

_TRANSPARENT = "rgba(0,0,0,0)"

_FONT = {"family": "Inter, system-ui, sans-serif", "color": "#e6edf3"}
_FONT_LIGHT = {"family": "Inter, system-ui, sans-serif", "color": "#1f2328"}


# ---------------------------------------------------------------------------
# Internal data helpers
# ---------------------------------------------------------------------------


def _label(fw: str) -> str:
    """Return the human-readable label for a framework slug."""
    return FRAMEWORK_LABELS.get(fw, fw)


def _hex_to_rgba(hex_color: str, alpha: float) -> str:
    """Convert a 6-digit hex colour to an rgba() string for Plotly compatibility."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha:.2f})"


def _coverage_color(fraction: float) -> str:
    if fraction >= _COVERAGE_THRESHOLDS["high"]:
        return "#3fb950"
    if fraction >= _COVERAGE_THRESHOLDS["medium"]:
        return "#d29922"
    return "#da3633"


def _compute_pair_coverage(
    mappings: list[dict[str, Any]],
) -> dict[tuple[str, str], int]:
    """Return mapping count keyed by (source_framework, target_framework)."""
    counts: dict[tuple[str, str], int] = defaultdict(int)
    for row in mappings:
        src = row.get("source_framework", "")
        tgt = row.get("target_framework", "")
        if src and tgt and src != tgt:
            counts[(src, tgt)] += 1
    return dict(counts)


def _all_frameworks(pair_counts: dict[tuple[str, str], int]) -> list[str]:
    """Sorted list of all frameworks that appear in at least one pair."""
    seen: set[str] = set()
    for src, tgt in pair_counts:
        seen.add(src)
        seen.add(tgt)
    return sorted(seen)


# ---------------------------------------------------------------------------
# Chart builders
# ---------------------------------------------------------------------------


def _build_heatmap(template: str = "plotly_dark") -> go.Figure:
    """Source × target coverage heatmap."""
    mappings = load_all_mappings()
    pair_counts = _compute_pair_coverage(mappings)
    frameworks = _all_frameworks(pair_counts)

    if not frameworks:
        fig = go.Figure()
        fig.update_layout(
            title="Coverage Heatmap",
            template=template,
            paper_bgcolor=_TRANSPARENT,
            plot_bgcolor=_TRANSPARENT,
        )
        return fig

    # Normalise to a fraction of the maximum count across all pairs
    max_count = max(pair_counts.values(), default=1)

    z: list[list[float | None]] = []
    hover: list[list[str]] = []
    sources = [fw for fw in frameworks if any(src == fw for src, _ in pair_counts)]
    targets = [fw for fw in frameworks if any(tgt == fw for _, tgt in pair_counts)]

    for src in sources:
        row: list[float | None] = []
        hover_row: list[str] = []
        for tgt in targets:
            cnt = pair_counts.get((src, tgt))
            if cnt is None:
                row.append(None)
                hover_row.append(f"{_label(src)} → {_label(tgt)}<br>No mappings")
            else:
                frac = cnt / max_count
                row.append(frac)
                hover_row.append(
                    f"{_label(src)} → {_label(tgt)}"
                    f"<br>{cnt} mapping{'s' if cnt != 1 else ''}"
                    f"<br>{frac:.0%} of max"
                )
        z.append(row)
        hover.append(hover_row)

    fig = go.Figure(
        data=go.Heatmap(
            z=z,
            x=[_label(t) for t in targets],
            y=[_label(s) for s in sources],
            hovertext=hover,
            hoverinfo="text",
            colorscale=_HEATMAP_COLORSCALE,
            colorbar=dict(
                title="Coverage",
                tickformat=".0%",
                len=0.8,
            ),
            zmin=0,
            zmax=1,
        )
    )
    fig.update_layout(
        title=dict(text="Source × Target Coverage Heatmap", x=0.5),
        xaxis=dict(title="Target Framework", tickangle=-40),
        yaxis=dict(title="Source Framework", autorange="reversed"),
        height=520,
        margin=dict(l=20, r=20, t=60, b=20),
        template=template,
        paper_bgcolor=_TRANSPARENT,
        plot_bgcolor=_TRANSPARENT,
    )
    return fig


def _build_coverage_bars(template: str = "plotly_dark") -> go.Figure:
    """Per-framework coverage bar chart with traffic-light colouring."""
    mappings = load_all_mappings()
    pair_counts = _compute_pair_coverage(mappings)
    frameworks = _all_frameworks(pair_counts)

    if not frameworks:
        fig = go.Figure()
        fig.update_layout(
            title="Per-Framework Coverage",
            template=template,
            paper_bgcolor=_TRANSPARENT,
            plot_bgcolor=_TRANSPARENT,
        )
        return fig

    # For each framework: fraction = its total mappings / global max
    fw_total: dict[str, int] = defaultdict(int)
    for (src, tgt), cnt in pair_counts.items():
        fw_total[src] += cnt
        fw_total[tgt] += cnt

    max_total = max(fw_total.values(), default=1)

    labels = [_label(fw) for fw in frameworks]
    fracs = [fw_total.get(fw, 0) / max_total for fw in frameworks]
    colors = [_coverage_color(f) for f in fracs]

    fig = go.Figure(
        data=go.Bar(
            x=labels,
            y=[round(f * 100, 1) for f in fracs],
            marker_color=colors,
            hovertemplate="%{x}<br>Coverage: %{y:.1f}%<extra></extra>",
        )
    )
    fig.update_layout(
        title=dict(text="Per-Framework Coverage (%)", x=0.5),
        xaxis=dict(title="Framework", tickangle=-40),
        yaxis=dict(title="Coverage %", range=[0, 105]),
        height=400,
        margin=dict(l=20, r=20, t=60, b=20),
        template=template,
        paper_bgcolor=_TRANSPARENT,
        plot_bgcolor=_TRANSPARENT,
        showlegend=False,
    )
    return fig


def _build_sankey(template: str = "plotly_dark") -> go.Figure:
    """Mapping flow: source frameworks → tiers → target frameworks."""
    mappings = load_all_mappings()

    if not mappings:
        fig = go.Figure()
        fig.update_layout(
            title="Mapping Flow",
            template=template,
            paper_bgcolor=_TRANSPARENT,
            plot_bgcolor=_TRANSPARENT,
        )
        return fig

    # Build node list: sources, then tiers, then targets
    sources_set: set[str] = set()
    targets_set: set[str] = set()
    tiers_set: set[str] = set()

    for row in mappings:
        src = row.get("source_framework", "")
        tgt = row.get("target_framework", "")
        tier = row.get("tier", "Unknown") or "Unknown"
        if src and tgt and src != tgt:
            sources_set.add(src)
            targets_set.add(tgt)
            tiers_set.add(tier)

    # Node order: source frameworks, tier nodes, target frameworks
    source_nodes = sorted(sources_set)
    tier_nodes = sorted(tiers_set)
    target_nodes = sorted(targets_set)

    all_nodes = source_nodes + tier_nodes + target_nodes
    node_index = {n: i for i, n in enumerate(all_nodes)}

    # Build flow aggregates: src→tier counts and tier→tgt counts
    src_tier_counts: dict[tuple[str, str], int] = defaultdict(int)
    tier_tgt_counts: dict[tuple[str, str], int] = defaultdict(int)

    for row in mappings:
        src = row.get("source_framework", "")
        tgt = row.get("target_framework", "")
        tier = row.get("tier", "Unknown") or "Unknown"
        if src and tgt and src != tgt:
            src_tier_counts[(src, tier)] += 1
            tier_tgt_counts[(tier, tgt)] += 1

    link_src: list[int] = []
    link_tgt: list[int] = []
    link_val: list[int] = []
    link_color: list[str] = []

    for (src, tier), cnt in src_tier_counts.items():
        link_src.append(node_index[src])
        link_tgt.append(node_index[tier])
        link_val.append(cnt)
        tier_hex = TIER_COLORS.get(tier, TIER_COLORS.get("Unknown", "#8b949e"))
        link_color.append(_hex_to_rgba(tier_hex, 0.55))

    for (tier, tgt), cnt in tier_tgt_counts.items():
        link_src.append(node_index[tier])
        link_tgt.append(node_index[tgt])
        link_val.append(cnt)
        tier_hex = TIER_COLORS.get(tier, TIER_COLORS.get("Unknown", "#8b949e"))
        link_color.append(_hex_to_rgba(tier_hex, 0.35))

    # Node colours
    node_colors: list[str] = []
    for n in all_nodes:
        if n in sources_set:
            node_colors.append("#1f6feb")
        elif n in tiers_set:
            node_colors.append(TIER_COLORS.get(n, "#8b949e"))
        else:
            node_colors.append("#388bfd")

    node_labels = [_label(n) if n not in tiers_set else n for n in all_nodes]

    fig = go.Figure(
        data=go.Sankey(
            node=dict(
                pad=12,
                thickness=18,
                line=dict(color="rgba(0,0,0,0)", width=0),
                label=node_labels,
                color=node_colors,
                hovertemplate="%{label}<br>%{value} mappings<extra></extra>",
            ),
            link=dict(
                source=link_src,
                target=link_tgt,
                value=link_val,
                color=link_color,
                hovertemplate=(
                    "%{source.label} → %{target.label}"
                    "<br>%{value} mappings<extra></extra>"
                ),
            ),
        )
    )
    fig.update_layout(
        title=dict(text="Mapping Flow: Source → Tier → Target", x=0.5),
        height=540,
        margin=dict(l=20, r=20, t=60, b=20),
        template=template,
        paper_bgcolor=_TRANSPARENT,
        plot_bgcolor=_TRANSPARENT,
        font=dict(size=11),
    )
    return fig


def _build_kpi_cards() -> list:
    """Four KPI cards: framework count, mapping count, control count, pair count."""
    mappings = load_all_mappings()
    meta = load_framework_metadata()

    pair_counts = _compute_pair_coverage(mappings)
    framework_count = len(_all_frameworks(pair_counts)) or len(meta)
    mapping_count = len(mappings)
    control_count = sum(v.get("control_count", 0) for v in meta.values())
    pair_count = len(pair_counts)

    def _card(label: str, value: str, icon: str, color: str) -> dbc.Col:
        return dbc.Col(
            dbc.Card(
                dbc.CardBody([
                    html.Div(
                        icon,
                        className="display-6 mb-1",
                        style={"color": color},
                    ),
                    html.H2(
                        value,
                        className="fw-bold mb-0",
                        style={"color": color},
                    ),
                    html.P(
                        label,
                        className="text-muted mb-0 small",
                    ),
                ]),
                className="text-center h-100 border-0",
                style={"background": "rgba(255,255,255,0.04)"},
            ),
            xs=6, md=3,
            className="mb-3",
        )

    return [
        _card("Frameworks", str(framework_count), "🗂", "#58a6ff"),
        _card("Mappings", f"{mapping_count:,}", "🔗", "#3fb950"),
        _card("Controls", f"{control_count:,}", "🛡", "#d29922"),
        _card("Framework Pairs", str(pair_count), "↔", "#bc8cff"),
    ]


# ---------------------------------------------------------------------------
# Public layout
# ---------------------------------------------------------------------------


def layout() -> html.Div:
    """Return the full Coverage Dashboard layout."""
    return html.Div(
        id="coverage-page",
        children=[
            # ----------------------------------------------------------------
            # Header
            # ----------------------------------------------------------------
            dbc.Row(
                dbc.Col(
                    html.H2(
                        "Coverage Dashboard",
                        className="mb-0 fw-bold",
                    ),
                    width=12,
                ),
                className="mb-2",
            ),
            # ----------------------------------------------------------------
            # KPI row
            # ----------------------------------------------------------------
            dbc.Row(
                id="coverage-kpi-row",
                children=_build_kpi_cards(),
                className="mb-3 g-2",
            ),
            # ----------------------------------------------------------------
            # Chart row 1: heatmap + bars
            # ----------------------------------------------------------------
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                dcc.Graph(
                                    id="coverage-heatmap",
                                    figure=_build_heatmap(),
                                    config={"displayModeBar": False},
                                )
                            ),
                            className="border-0 h-100",
                            style={"background": "rgba(255,255,255,0.03)"},
                        ),
                        md=7,
                        className="mb-3",
                    ),
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                dcc.Graph(
                                    id="coverage-bars",
                                    figure=_build_coverage_bars(),
                                    config={"displayModeBar": False},
                                )
                            ),
                            className="border-0 h-100",
                            style={"background": "rgba(255,255,255,0.03)"},
                        ),
                        md=5,
                        className="mb-3",
                    ),
                ],
                className="g-2",
            ),
            # ----------------------------------------------------------------
            # Chart row 2: Sankey full-width
            # ----------------------------------------------------------------
            dbc.Row(
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            dcc.Graph(
                                id="coverage-sankey",
                                figure=_build_sankey(),
                                config={"displayModeBar": False},
                            )
                        ),
                        className="border-0",
                        style={"background": "rgba(255,255,255,0.03)"},
                    ),
                    width=12,
                ),
                className="g-2",
            ),
        ],
        style={"padding": "1rem"},
    )


# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------


def register_callbacks(app) -> None:  # noqa: ANN001
    """Wire the theme-toggle callback to redraw all four charts."""

    @app.callback(
        Output("coverage-heatmap", "figure"),
        Output("coverage-bars", "figure"),
        Output("coverage-sankey", "figure"),
        Input("theme-store", "data"),
    )
    def update_theme(theme_data: dict | None) -> tuple:
        template = "plotly_dark"
        if isinstance(theme_data, dict):
            template = theme_data.get("template", "plotly_dark")
        return (
            _build_heatmap(template),
            _build_coverage_bars(template),
            _build_sankey(template),
        )
