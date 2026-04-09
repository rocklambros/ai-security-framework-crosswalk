"""Ablation results tab: horizontal bar chart comparing ablation configs."""
from __future__ import annotations

import json
from pathlib import Path

from dash import html, Input, Output, dcc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

ABLATIONS_PATH = Path("results/ablations.json")


def _load_ablations() -> dict:
    if ABLATIONS_PATH.exists():
        return json.loads(ABLATIONS_PATH.read_text())
    return {}


def _build_bar_chart():
    ablations = _load_ablations()
    if not ablations:
        return go.Figure()

    # Sort by tier_accuracy descending
    items = sorted(
        ablations.items(),
        key=lambda kv: kv[1].get("tier_accuracy", 0),
        reverse=True,
    )
    names = [name for name, _ in items]
    accuracies = [v.get("tier_accuracy", 0) for _, v in items]
    f1_scores = [v.get("macro_f1", 0) for _, v in items]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=names,
        x=accuracies,
        name="Tier Accuracy",
        orientation="h",
        marker_color="#2c7fb8",
    ))
    fig.add_trace(go.Bar(
        y=names,
        x=f1_scores,
        name="Macro F1",
        orientation="h",
        marker_color="#41b6c4",
    ))
    fig.update_layout(
        title="Ablation Study: Tier Accuracy and Macro F1",
        xaxis_title="Score",
        yaxis_title="Configuration",
        barmode="group",
        height=max(400, len(names) * 45),
        margin=dict(l=20, r=20, t=50, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    return fig


def _build_detail_table():
    ablations = _load_ablations()
    if not ablations:
        return html.P("No ablation results found.")

    items = sorted(
        ablations.items(),
        key=lambda kv: kv[1].get("tier_accuracy", 0),
        reverse=True,
    )
    header = html.Thead(html.Tr([
        html.Th("Config"),
        html.Th("Description"),
        html.Th("Features"),
        html.Th("Tier Acc"),
        html.Th("Macro F1"),
    ]))
    rows = []
    for name, v in items:
        rows.append(html.Tr([
            html.Td(name),
            html.Td(v.get("description", "")),
            html.Td(str(v.get("n_features", "?"))),
            html.Td(f"{v.get('tier_accuracy', 0):.4f}"),
            html.Td(f"{v.get('macro_f1', 0):.4f}"),
        ]))

    return dbc.Table(
        [header, html.Tbody(rows)],
        bordered=True, striped=True, hover=True, size="sm",
    )


def layout():
    return dbc.Card(dbc.CardBody([
        html.H3("Ablation Results"),
        dcc.Graph(id="ablation-chart", figure=_build_bar_chart()),
        html.Hr(),
        html.H4("Detail Table"),
        html.Div(id="ablation-table", children=_build_detail_table()),
    ]))


def register_callbacks(app):
    """No dynamic callbacks needed; chart and table are static."""
    pass
