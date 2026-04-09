"""Page 3 — Mapping Browser.

Renders a filterable, sortable DataTable of all crosswalk mappings with
CSV and JSON export.  ML-predicted rows are highlighted in amber italic.
"""

from __future__ import annotations

import json

import pandas as pd
from dash import Input, Output, State, callback, dcc, html
from dash.dash_table import DataTable
from dash.dash_table.Format import Format, Scheme

from app.dash_app.data.frameworks import FRAMEWORK_LABELS
from app.dash_app.data.loader import load_all_mappings

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PAGE_SIZE = 25

_TIER_ORDER = ["Foundational", "Hardening", "Advanced"]

_DISPLAY_COLS = [
    {"id": "source_id", "name": "Source Control"},
    {"id": "target_control_id", "name": "Target Control"},
    {"id": "tier", "name": "Tier"},
    {
        "id": "confidence",
        "name": "Confidence",
        "type": "numeric",
        "format": Format(precision=2, scheme=Scheme.fixed),
    },
    {"id": "source_type", "name": "Source Type"},
]

_COL_IDS = [c["id"] for c in _DISPLAY_COLS]

# Amber highlight for ML-predicted rows
_ML_STYLE = {
    "backgroundColor": "rgba(245, 158, 11, 0.15)",
    "fontStyle": "italic",
    "color": "var(--text-primary)",
}

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _prepare_table_data(df: pd.DataFrame) -> list[dict]:
    """Convert raw loader DataFrame into display-ready records.

    Only the columns used by the DataTable are kept so the payload stays
    small.  Confidence is rounded to two decimal places.
    """
    out = df[_COL_IDS].copy()
    out["confidence"] = out["confidence"].round(2)
    return out.to_dict("records")


def _framework_options(column: str) -> list[dict]:
    df = load_all_mappings()
    values = sorted(df[column].dropna().unique())
    return [{"label": FRAMEWORK_LABELS.get(v, v), "value": v} for v in values]


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------


def layout() -> html.Div:
    """Return the full page layout for the Mapping Browser."""
    src_opts = _framework_options("source_framework")
    tgt_opts = _framework_options("target_framework")
    tier_opts = [{"label": t, "value": t} for t in _TIER_ORDER]

    filter_bar = html.Div(
        className="mapping-filter-bar",
        style={
            "display": "flex",
            "flexWrap": "wrap",
            "gap": "12px",
            "alignItems": "center",
            "padding": "16px 0 8px 0",
        },
        children=[
            dcc.Input(
                id="mapping-search",
                type="text",
                placeholder="Search controls or notes…",
                debounce=True,
                style={
                    "flex": "1 1 220px",
                    "minWidth": "180px",
                    "padding": "8px 12px",
                    "background": "var(--bg-tertiary)",
                    "border": "1px solid var(--border)",
                    "color": "var(--text-primary)",
                    "borderRadius": "6px",
                    "fontSize": "14px",
                    "outline": "none",
                },
            ),
            dcc.Dropdown(
                id="mapping-source-fw",
                options=src_opts,
                placeholder="Source framework",
                clearable=True,
                multi=False,
                style={
                    "flex": "1 1 200px",
                    "minWidth": "160px",
                    "fontSize": "14px",
                },
            ),
            dcc.Dropdown(
                id="mapping-target-fw",
                options=tgt_opts,
                placeholder="Target framework",
                clearable=True,
                multi=False,
                style={
                    "flex": "1 1 200px",
                    "minWidth": "160px",
                    "fontSize": "14px",
                },
            ),
            dcc.Dropdown(
                id="mapping-tier-filter",
                options=tier_opts,
                placeholder="Tier",
                clearable=True,
                multi=True,
                style={
                    "flex": "1 1 200px",
                    "minWidth": "160px",
                    "fontSize": "14px",
                },
            ),
        ],
    )

    export_bar = html.Div(
        style={
            "display": "flex",
            "gap": "10px",
            "justifyContent": "flex-end",
            "padding": "4px 0 12px 0",
        },
        children=[
            html.Button(
                "Export CSV",
                id="mapping-export-csv-btn",
                n_clicks=0,
                style={
                    "padding": "7px 18px",
                    "background": "var(--bg-tertiary)",
                    "border": "1px solid var(--border)",
                    "color": "var(--text-primary)",
                    "borderRadius": "6px",
                    "cursor": "pointer",
                    "fontSize": "13px",
                    "fontWeight": "500",
                    "letterSpacing": "0.02em",
                    "transition": "background 0.15s",
                },
            ),
            html.Button(
                "Export JSON",
                id="mapping-export-json-btn",
                n_clicks=0,
                style={
                    "padding": "7px 18px",
                    "background": "var(--bg-tertiary)",
                    "border": "1px solid var(--border)",
                    "color": "var(--text-primary)",
                    "borderRadius": "6px",
                    "cursor": "pointer",
                    "fontSize": "13px",
                    "fontWeight": "500",
                    "letterSpacing": "0.02em",
                    "transition": "background 0.15s",
                },
            ),
            dcc.Download(id="mapping-download-csv"),
            dcc.Download(id="mapping-download-json"),
        ],
    )

    summary_bar = html.Div(
        id="mapping-summary",
        style={
            "fontSize": "13px",
            "color": "var(--text-secondary, #9ca3af)",
            "padding": "0 0 8px 0",
        },
    )

    table = DataTable(
        id="mapping-table",
        columns=_DISPLAY_COLS,
        data=[],
        page_size=PAGE_SIZE,
        page_action="native",
        sort_action="native",
        sort_mode="multi",
        filter_action="native",
        filter_options={"case": "insensitive"},
        style_table={
            "overflowX": "auto",
            "borderRadius": "8px",
            "border": "1px solid var(--border)",
        },
        style_header={
            "backgroundColor": "var(--bg-tertiary)",
            "color": "var(--text-primary)",
            "fontWeight": "600",
            "fontSize": "13px",
            "border": "none",
            "borderBottom": "1px solid var(--border)",
            "padding": "10px 14px",
            "letterSpacing": "0.04em",
            "textTransform": "uppercase",
        },
        style_cell={
            "backgroundColor": "var(--bg-secondary, #1e2330)",
            "color": "var(--text-primary)",
            "border": "none",
            "borderBottom": "1px solid var(--border)",
            "padding": "10px 14px",
            "fontSize": "13px",
            "fontFamily": "inherit",
            "overflow": "hidden",
            "textOverflow": "ellipsis",
            "maxWidth": "260px",
            "whiteSpace": "normal",
        },
        style_cell_conditional=[
            {"if": {"column_id": "source_id"}, "fontFamily": "monospace", "fontSize": "12px"},
            {"if": {"column_id": "target_control_id"}, "fontFamily": "monospace", "fontSize": "12px"},
            {"if": {"column_id": "confidence"}, "textAlign": "right"},
            {"if": {"column_id": "tier"}, "minWidth": "110px"},
        ],
        style_data_conditional=[
            {
                "if": {"filter_query": '{source_type} = "ml_predicted"'},
                **_ML_STYLE,
            },
            # Alternating row shading for expert rows
            {
                "if": {
                    "filter_query": '{source_type} = "expert"',
                    "row_index": "odd",
                },
                "backgroundColor": "var(--bg-tertiary)",
            },
        ],
        style_filter={
            "backgroundColor": "var(--bg-tertiary)",
            "color": "var(--text-primary)",
            "border": "none",
            "borderBottom": "1px solid var(--border)",
            "fontSize": "12px",
        },
        tooltip_data=[],
        tooltip_duration=None,
    )

    return html.Div(
        style={
            "padding": "24px 32px",
            "background": "var(--bg-primary, #0f1117)",
            "minHeight": "100vh",
            "color": "var(--text-primary)",
        },
        children=[
            html.H2(
                "Mapping Browser",
                style={
                    "margin": "0 0 4px 0",
                    "fontSize": "22px",
                    "fontWeight": "700",
                    "color": "var(--text-primary)",
                },
            ),
            html.P(
                "Browse, filter, and export all crosswalk mappings. "
                "Amber italic rows are ML-predicted (needs review).",
                style={
                    "margin": "0 0 16px 0",
                    "fontSize": "14px",
                    "color": "var(--text-secondary, #9ca3af)",
                },
            ),
            filter_bar,
            summary_bar,
            export_bar,
            table,
        ],
    )


# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------


def register_callbacks(app) -> None:  # noqa: ANN001
    """Register all callbacks for the Mapping Browser page."""

    @app.callback(
        Output("mapping-table", "data"),
        Output("mapping-table", "tooltip_data"),
        Output("mapping-summary", "children"),
        Input("mapping-search", "value"),
        Input("mapping-source-fw", "value"),
        Input("mapping-target-fw", "value"),
        Input("mapping-tier-filter", "value"),
    )
    def update_table(
        search: str | None,
        source_fw: str | None,
        target_fw: str | None,
        tiers: list[str] | None,
    ) -> tuple[list[dict], list[dict], str]:
        df = load_all_mappings()

        if source_fw:
            df = df[df["source_framework"] == source_fw]

        if target_fw:
            df = df[df["target_framework"] == target_fw]

        if tiers:
            df = df[df["tier"].isin(tiers)]

        if search and search.strip():
            q = search.strip().lower()
            mask = (
                df["source_id"].str.lower().str.contains(q, na=False)
                | df["target_control_id"].str.lower().str.contains(q, na=False)
                | df["target_control_name"].str.lower().str.contains(q, na=False)
                | df.get("notes", pd.Series(dtype=str)).str.lower().str.contains(q, na=False)
            )
            df = df[mask]

        records = _prepare_table_data(df)

        tooltip_data = [
            {
                col: {
                    "value": str(row.get("target_control_name", ""))
                    if col == "target_control_id"
                    else str(row.get("notes", "") or ""),
                    "type": "markdown",
                }
                for col in _COL_IDS
            }
            for row in df.to_dict("records")
        ]

        total = len(records)
        ml_count = sum(1 for r in records if r.get("source_type") == "ml_predicted")
        expert_count = total - ml_count
        summary = (
            f"{total:,} mapping{'s' if total != 1 else ''} shown"
            f" — {expert_count:,} expert, {ml_count:,} ML-predicted"
        )

        return records, tooltip_data, summary

    @app.callback(
        Output("mapping-download-csv", "data"),
        Input("mapping-export-csv-btn", "n_clicks"),
        State("mapping-search", "value"),
        State("mapping-source-fw", "value"),
        State("mapping-target-fw", "value"),
        State("mapping-tier-filter", "value"),
        prevent_initial_call=True,
    )
    def export_csv(
        _n: int,
        search: str | None,
        source_fw: str | None,
        target_fw: str | None,
        tiers: list[str] | None,
    ) -> dict:
        df = _apply_filters(search, source_fw, target_fw, tiers)
        return dcc.send_data_frame(df.to_csv, "mappings_export.csv", index=False)

    @app.callback(
        Output("mapping-download-json", "data"),
        Input("mapping-export-json-btn", "n_clicks"),
        State("mapping-search", "value"),
        State("mapping-source-fw", "value"),
        State("mapping-target-fw", "value"),
        State("mapping-tier-filter", "value"),
        prevent_initial_call=True,
    )
    def export_json(
        _n: int,
        search: str | None,
        source_fw: str | None,
        target_fw: str | None,
        tiers: list[str] | None,
    ) -> dict:
        df = _apply_filters(search, source_fw, target_fw, tiers)
        payload = json.dumps(df.to_dict("records"), indent=2, default=str)
        return dict(content=payload, filename="mappings_export.json")


def _apply_filters(
    search: str | None,
    source_fw: str | None,
    target_fw: str | None,
    tiers: list[str] | None,
) -> pd.DataFrame:
    """Re-apply the same filter logic used by update_table, returning a full DataFrame."""
    df = load_all_mappings()

    if source_fw:
        df = df[df["source_framework"] == source_fw]
    if target_fw:
        df = df[df["target_framework"] == target_fw]
    if tiers:
        df = df[df["tier"].isin(tiers)]
    if search and search.strip():
        q = search.strip().lower()
        mask = (
            df["source_id"].str.lower().str.contains(q, na=False)
            | df["target_control_id"].str.lower().str.contains(q, na=False)
            | df["target_control_name"].str.lower().str.contains(q, na=False)
            | df.get("notes", pd.Series(dtype=str)).str.lower().str.contains(q, na=False)
        )
        df = df[mask]

    return df
