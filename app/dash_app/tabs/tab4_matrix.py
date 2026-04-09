"""Coverage heatmap tab: framework-pair coverage matrix from sacred results."""
from __future__ import annotations

import json
from pathlib import Path

from dash import html, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from dash import dcc

from app.dash_app.frameworks import (
    UI_SOURCE_LISTS,
    UI_TARGET_FRAMEWORKS,
    DISPLAY_LABELS,
    FRAMEWORK_PAIRS,
)

SACRED_PATH = Path("results/sacred/sacred_ca388cbc.json")
ABLATIONS_PATH = Path("results/ablations.json")


def _load_sacred_metrics() -> dict | None:
    if SACRED_PATH.exists():
        return json.loads(SACRED_PATH.read_text())
    return None


def _load_ablation_metrics() -> dict | None:
    if ABLATIONS_PATH.exists():
        return json.loads(ABLATIONS_PATH.read_text())
    return None


def _build_heatmap():
    """Build a coverage heatmap showing which framework pairs are in the crosswalk."""
    sources = list(UI_SOURCE_LISTS)
    targets = [t for t in UI_TARGET_FRAMEWORKS if t not in UI_SOURCE_LISTS]

    pair_set = set(FRAMEWORK_PAIRS)
    z = []
    hover = []
    for src in sources:
        row = []
        hover_row = []
        for tgt in targets:
            if (src, tgt) in pair_set:
                row.append(1)
                hover_row.append(
                    f"{DISPLAY_LABELS[src]} -> {DISPLAY_LABELS[tgt]}<br>Covered"
                )
            else:
                row.append(0)
                hover_row.append(
                    f"{DISPLAY_LABELS[src]} -> {DISPLAY_LABELS[tgt]}<br>Not covered"
                )
        z.append(row)
        hover.append(hover_row)

    fig = go.Figure(data=go.Heatmap(
        z=z,
        x=[DISPLAY_LABELS[t] for t in targets],
        y=[DISPLAY_LABELS[s] for s in sources],
        hovertext=hover,
        hoverinfo="text",
        colorscale=[[0, "#f0f0f0"], [1, "#2c7fb8"]],
        showscale=False,
    ))
    fig.update_layout(
        title="Framework Pair Coverage Matrix",
        xaxis_title="Target Framework",
        yaxis_title="Source Framework",
        height=350,
        margin=dict(l=20, r=20, t=50, b=20),
    )
    return fig


def _build_metrics_table():
    """Summary metrics from the sacred run."""
    sacred = _load_sacred_metrics()
    if sacred is None:
        return html.P("No sacred run results found.")

    rows = []
    rows.append(html.Tr([
        html.Td("Macro F1"),
        html.Td(f"{sacred.get('macro_f1', 0):.4f}"),
    ]))
    rows.append(html.Tr([
        html.Td("N pairs evaluated"),
        html.Td(str(sacred.get("n_pairs", "?"))),
    ]))
    ci = sacred.get("bootstrap_ci_95", {})
    if ci:
        rows.append(html.Tr([
            html.Td("Bootstrap 95% CI"),
            html.Td(f"[{ci.get('lower', 0):.4f}, {ci.get('upper', 0):.4f}]"),
        ]))
    conf = sacred.get("conformal", {})
    if conf:
        rows.append(html.Tr([
            html.Td("Marginal Coverage"),
            html.Td(f"{conf.get('marginal_coverage', 0):.4f}"),
        ]))
        rows.append(html.Tr([
            html.Td("Avg Set Size"),
            html.Td(f"{conf.get('avg_set_size', 0):.2f}"),
        ]))

    return dbc.Table(
        [html.Thead(html.Tr([html.Th("Metric"), html.Th("Value")])),
         html.Tbody(rows)],
        bordered=True, striped=True, size="sm",
    )


def layout():
    return dbc.Card(dbc.CardBody([
        html.H3("Coverage Heatmap"),
        dcc.Graph(id="coverage-heatmap", figure=_build_heatmap()),
        html.Hr(),
        html.H4("Sacred Run Metrics"),
        html.Div(id="sacred-metrics", children=_build_metrics_table()),
    ]))


def register_callbacks(app):
    """No dynamic callbacks needed; heatmap is static."""
    pass
