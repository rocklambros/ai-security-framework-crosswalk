"""Pair lookup tab: select source/target frameworks, predict tier."""
from __future__ import annotations

from dash import html, dcc, Input, Output, State, no_update
import dash_bootstrap_components as dbc

from app.dash_app.frameworks import (
    UI_SOURCE_LISTS,
    UI_TARGET_FRAMEWORKS,
    DISPLAY_LABELS,
    FRAMEWORK_PAIRS,
)

TIER_COLORS = {
    "unrelated": "secondary",
    "partial": "warning",
    "related": "info",
    "equivalent": "success",
}


def layout():
    source_options = [
        {"label": DISPLAY_LABELS[k], "value": k} for k in UI_SOURCE_LISTS
    ]
    target_options = [
        {"label": DISPLAY_LABELS[k], "value": k} for k in UI_TARGET_FRAMEWORKS
    ]
    return dbc.Card(dbc.CardBody([
        html.H3("Pair Lookup"),
        html.P("Select a source and target framework to see the predicted mapping tier."),
        dbc.Row([
            dbc.Col([
                dbc.Label("Source Framework"),
                dcc.Dropdown(
                    id="lookup-source",
                    options=source_options,
                    value=UI_SOURCE_LISTS[0],
                    clearable=False,
                ),
            ], md=5),
            dbc.Col([
                dbc.Label("Target Framework"),
                dcc.Dropdown(
                    id="lookup-target",
                    options=target_options,
                    value=UI_TARGET_FRAMEWORKS[0],
                    clearable=False,
                ),
            ], md=5),
            dbc.Col([
                dbc.Label("\u00a0"),  # nbsp spacer
                dbc.Button(
                    "Lookup",
                    id="lookup-btn",
                    color="primary",
                    className="d-block w-100",
                ),
            ], md=2),
        ], className="mb-3"),
        html.Div(id="lookup-result"),
    ]))


def register_callbacks(app):
    @app.callback(
        Output("lookup-result", "children"),
        Input("lookup-btn", "n_clicks"),
        State("lookup-source", "value"),
        State("lookup-target", "value"),
        prevent_initial_call=True,
    )
    def do_lookup(n_clicks, source, target):
        if not source or not target:
            return no_update

        pair = (source, target)
        if pair not in FRAMEWORK_PAIRS:
            return dbc.Alert(
                f"Pair ({DISPLAY_LABELS.get(source, source)}, "
                f"{DISPLAY_LABELS.get(target, target)}) is not in the "
                f"crosswalk coverage.",
                color="warning",
            )

        # Try to load scorer -- falls back gracefully if model unavailable
        try:
            from app.api.scorer_loader import load_scorer
            scorer = load_scorer(
                "runs/stacker/stacker-48d0d19d-20260409T160345"
            )
            # Build a dummy feature vector (zeros) for demonstration.
            # In production, features would come from the pipeline.
            result = scorer.predict({})
            tier = result["tier"]
            conf = result["confidence"]
            cset = ", ".join(result["conformal_set"])
            review = result["needs_review"]

            return dbc.Card(dbc.CardBody([
                html.H5(
                    f"{DISPLAY_LABELS.get(source, source)} -> "
                    f"{DISPLAY_LABELS.get(target, target)}"
                ),
                dbc.Badge(tier.upper(), color=TIER_COLORS.get(tier, "secondary"),
                          className="me-2 fs-6"),
                html.Span(f"Confidence: {conf:.2%}"),
                html.Br(),
                html.Small(f"Conformal set: {{{cset}}}"),
                html.Br(),
                html.Small(
                    f"Needs review: {'Yes' if review else 'No'}",
                    className="text-danger" if review else "text-success",
                ),
            ]), className="mt-3")
        except Exception as exc:
            return dbc.Alert(
                f"Model not available ({type(exc).__name__}: {exc}). "
                f"Pair ({DISPLAY_LABELS.get(source, source)}, "
                f"{DISPLAY_LABELS.get(target, target)}) is a valid "
                f"crosswalk pair but scoring requires the model artifacts.",
                color="info",
            )
