"""Page 4: Model Performance — Confusion matrix, radar, ablations, conformal, calibration."""
from __future__ import annotations

import dash
import numpy as np
import plotly.graph_objects as go
from dash import Input, Output, dcc, html

from app.dash_app.data.frameworks import TIER_COLORS
from app.dash_app.data.loader import load_ablations, load_sacred_results


def _build_confusion_matrix(sacred: dict, template: str = "plotly_dark") -> go.Figure:
    """Build 4×4 confusion matrix heatmap."""
    cm = sacred.get("confusion_matrix", [[0] * 4] * 4)
    labels = ["Unrelated", "Partial", "Related", "Equivalent"]

    cm_array = np.array(cm)
    row_sums = cm_array.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1
    cm_pct = (cm_array / row_sums * 100).round(1)

    text = [[f"{cm_array[i][j]}<br>({cm_pct[i][j]}%)" for j in range(4)] for i in range(4)]

    fig = go.Figure(data=go.Heatmap(
        z=cm_array, x=labels, y=labels,
        colorscale="Blues", text=text, texttemplate="%{text}",
        textfont={"size": 10},
        hovertemplate="Actual: %{y}<br>Predicted: %{x}<br>Count: %{z}<extra></extra>",
    ))
    fig.update_layout(
        template=template,
        title={"text": "Confusion Matrix", "font": {"size": 13}},
        xaxis={"title": "Predicted"},
        yaxis={"title": "Actual", "autorange": "reversed"},
        margin=dict(l=10, r=10, t=40, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def _build_radar(sacred: dict, template: str = "plotly_dark") -> go.Figure:
    """Build per-class F1 radar chart."""
    per_class = sacred.get("per_class", {})
    categories = ["Equivalent", "Related", "Partial", "Unrelated"]
    values = [
        per_class.get("equivalent", {}).get("f1", 0),
        per_class.get("related", {}).get("f1", 0),
        per_class.get("partial", {}).get("f1", 0),
        per_class.get("unrelated", {}).get("f1", 0),
    ]
    values.append(values[0])  # Close the polygon
    categories.append(categories[0])

    fig = go.Figure(data=go.Scatterpolar(
        r=values, theta=categories, fill="toself",
        fillcolor="rgba(88,166,255,0.2)",
        line={"color": "#58a6ff", "width": 2},
        name="Per-Class F1",
    ))
    fig.update_layout(
        template=template,
        title={"text": "Per-Class F1 Scores", "font": {"size": 13}},
        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
        margin=dict(l=40, r=40, t=40, b=40),
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def _build_ablation_bars(ablations: dict, template: str = "plotly_dark") -> go.Figure:
    """Build ablation comparison grouped horizontal bar chart."""
    if not ablations:
        return go.Figure().update_layout(
            template=template,
            title={"text": "Ablation Comparison", "font": {"size": 13}},
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )

    configs = sorted(ablations.keys())
    tier_accs = [ablations[c].get("tier_accuracy", 0) for c in configs]
    macro_f1s = [ablations[c].get("macro_f1", 0) for c in configs]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=configs, x=tier_accs, name="Tier Accuracy",
        orientation="h", marker_color="#58a6ff",
    ))
    fig.add_trace(go.Bar(
        y=configs, x=macro_f1s, name="Macro F1",
        orientation="h", marker_color="#3fb950",
    ))
    fig.update_layout(
        template=template,
        title={"text": "Ablation Comparison", "font": {"size": 13}},
        barmode="group",
        xaxis={"range": [0, 1], "title": "Score"},
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def _build_conformal_bars(sacred: dict, template: str = "plotly_dark") -> go.Figure:
    """Build conformal coverage bar chart with 90% target hline."""
    conformal = sacred.get("conformal", {})
    coverage = conformal.get("marginal_coverage", 0)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=["Coverage"], y=[coverage],
        name="Marginal Coverage",
        marker_color="#58a6ff",
        text=[f"{coverage:.1%}"],
        textposition="outside",
    ))
    fig.add_hline(
        y=0.9, line_dash="dash", line_color="#da3633",
        annotation_text="90% target", annotation_position="top right",
    )
    fig.update_layout(
        template=template,
        title={"text": "Conformal Coverage", "font": {"size": 13}},
        yaxis={"range": [0, 1.1], "title": "Coverage"},
        margin=dict(l=10, r=10, t=40, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def _build_calibration(sacred: dict, template: str = "plotly_dark") -> go.Figure:
    """Build calibration reliability diagram with perfect-calibration diagonal."""
    fig = go.Figure()
    # Perfect calibration diagonal
    fig.add_trace(go.Scatter(
        x=[0, 1], y=[0, 1], mode="lines",
        line={"dash": "dash", "color": "gray"},
        name="Perfect Calibration",
    ))
    # Populate from calibration_bins if present
    cal_bins = sacred.get("calibration_bins", [])
    if cal_bins:
        pred_probs = [b.get("mean_predicted", 0) for b in cal_bins]
        actual_freqs = [b.get("fraction_positive", 0) for b in cal_bins]
        fig.add_trace(go.Scatter(
            x=pred_probs, y=actual_freqs, mode="markers+lines",
            marker={"color": "#58a6ff", "size": 8},
            line={"color": "#58a6ff", "width": 1.5},
            name="Model",
        ))
    fig.update_layout(
        template=template,
        title={"text": "Calibration Reliability", "font": {"size": 13}},
        xaxis={"title": "Predicted Probability", "range": [0, 1]},
        yaxis={"title": "Actual Frequency", "range": [0, 1]},
        margin=dict(l=10, r=10, t=40, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def layout() -> html.Div:
    """Build the Model Performance page layout."""
    sacred = load_sacred_results() or {}
    ablations = load_ablations() or {}

    tier_acc = sacred.get("tier_accuracy", "\u2014")
    macro_f1 = sacred.get("macro_f1", "\u2014")
    if isinstance(tier_acc, float):
        tier_acc = f"{tier_acc:.1%}"
    if isinstance(macro_f1, float):
        macro_f1 = f"{macro_f1:.3f}"

    return html.Div(style={"padding": "20px"}, children=[
        # Headline KPI metrics
        html.Div(
            style={"display": "flex", "gap": "16px", "marginBottom": "16px"},
            children=[
                html.Div(className="panel", style={"flex": 1, "textAlign": "center"}, children=[
                    html.Div(str(tier_acc), className="kpi-value",
                             style={"color": "var(--accent-blue)"}),
                    html.Div("Tier Accuracy", className="kpi-label"),
                ]),
                html.Div(className="panel", style={"flex": 1, "textAlign": "center"}, children=[
                    html.Div(str(macro_f1), className="kpi-value",
                             style={"color": "var(--accent-green)"}),
                    html.Div("Macro F1", className="kpi-label"),
                ]),
            ],
        ),

        # Top row: 3 charts (confusion matrix, radar, ablations)
        html.Div(
            style={
                "display": "grid",
                "gridTemplateColumns": "1fr 1fr 1fr",
                "gap": "16px",
            },
            children=[
                html.Div(className="panel", children=[
                    dcc.Graph(
                        id="model-confusion",
                        figure=_build_confusion_matrix(sacred),
                        config={"displayModeBar": False},
                        style={"height": "280px"},
                    ),
                ]),
                html.Div(className="panel", children=[
                    dcc.Graph(
                        id="model-radar",
                        figure=_build_radar(sacred),
                        config={"displayModeBar": False},
                        style={"height": "280px"},
                    ),
                ]),
                html.Div(className="panel", children=[
                    dcc.Graph(
                        id="model-ablations",
                        figure=_build_ablation_bars(ablations),
                        config={"displayModeBar": False},
                        style={"height": "280px"},
                    ),
                ]),
            ],
        ),

        # Bottom row: 2 charts (conformal coverage, calibration reliability)
        html.Div(
            style={
                "display": "grid",
                "gridTemplateColumns": "1fr 1fr",
                "gap": "16px",
                "marginTop": "16px",
            },
            children=[
                html.Div(className="panel", children=[
                    dcc.Graph(
                        id="model-conformal",
                        figure=_build_conformal_bars(sacred),
                        config={"displayModeBar": False},
                        style={"height": "250px"},
                    ),
                ]),
                html.Div(className="panel", children=[
                    dcc.Graph(
                        id="model-calibration",
                        figure=_build_calibration(sacred),
                        config={"displayModeBar": False},
                        style={"height": "250px"},
                    ),
                ]),
            ],
        ),
    ])


def register_callbacks(app: dash.Dash) -> None:
    """Register Model Performance page callbacks."""

    @app.callback(
        [
            Output("model-confusion", "figure"),
            Output("model-radar", "figure"),
            Output("model-ablations", "figure"),
            Output("model-conformal", "figure"),
            Output("model-calibration", "figure"),
        ],
        Input("theme-toggle", "value"),
    )
    def update_theme(dark_mode: bool):
        template = "plotly_dark" if dark_mode else "plotly_white"
        sacred = load_sacred_results() or {}
        ablations = load_ablations() or {}
        return (
            _build_confusion_matrix(sacred, template),
            _build_radar(sacred, template),
            _build_ablation_bars(ablations, template),
            _build_conformal_bars(sacred, template),
            _build_calibration(sacred, template),
        )
