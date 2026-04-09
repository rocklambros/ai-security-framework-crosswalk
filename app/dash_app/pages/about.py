"""Page 5: About — Project description, methodology, attribution."""
from __future__ import annotations

from dash import dcc, html


def layout() -> html.Div:
    """Build the About page with narrative and instructional content."""
    return html.Div(style={"padding": "20px", "maxWidth": "900px", "margin": "0 auto"}, children=[
        html.Div(className="panel", style={"padding": "32px"}, children=[
            dcc.Markdown("""
## AI Security Framework Crosswalk

A community resource for visualizing calibrated cross-framework mappings across
14 AI security and governance frameworks.

### Purpose

As the AI security landscape rapidly evolves, organizations must navigate multiple
overlapping frameworks — OWASP, NIST, MITRE, EU regulations, and more. This tool
provides a unified view of how controls map across these frameworks, helping security
practitioners identify equivalent protections, coverage gaps, and areas of overlap.

### How to Use This App

**Network Explorer** — The interactive network graph shows frameworks as large colored
nodes and individual controls as smaller nodes clustered around them. Edges represent
mappings between controls. Use the filters on the left to narrow by framework, tier,
or confidence level. Click any node to see its details and connected mappings.

**Coverage Dashboard** — See which framework pairs have the strongest mapping coverage
and where gaps exist. The heatmap shows pairwise coverage, while the Sankey diagram
shows the flow of mappings through different tiers.

**Mapping Browser** — Search and filter the complete mapping database. Export results
as CSV or JSON for integration with your own tools.

**Model Performance** — View the ML model's accuracy, per-class performance, and
calibration metrics. The ablation comparison shows which model components contribute
most to prediction quality.

### Understanding Mapping Tiers

| Tier | Meaning |
|------|---------|
| **Equivalent** | Controls address the same security concern with the same scope |
| **Related** | Controls address overlapping concerns but with different scope or depth |
| **Partial** | Controls are tangentially related — one touches on the other's domain |
| **Unrelated** | Controls address fundamentally different security concerns |

### Understanding Confidence Scores

Each mapping includes a confidence score (0–1) from the ML ensemble. Higher scores
indicate stronger model agreement. **Expert-verified** mappings (marked with checkmark) are
curated by domain experts and are authoritative. **ML-predicted** mappings (marked
with warning) are model extensions to uncovered framework pairs — treat these as
suggestions requiring human review.

**Conformal prediction sets** indicate which tiers are plausible for a given mapping.
A set of {Related, Equivalent} means the model is confident the mapping is at least
Related but uncertain whether it rises to Equivalent.

### Data Sources & Attribution

- **Expert mappings**: 3,210 curated by the [GenAI Security Project](https://github.com/GenAI-Security-Project/GenAI-Data-Security-Initiative)
  crosswalk community under CC BY-SA 4.0.
- **OWASP DSGAI 2026 corpus**: CC BY-SA 4.0. Full third-party attribution in
  [THIRD_PARTY_NOTICES.md](/attribution).
- **ML predictions**: Multi-encoder ensemble (DeBERTa + RoBERTa + ELECTRA) with
  GATv2 graph features, LightGBM stacker, and Mondrian conformal calibration.

### Contact

Rock Lambros — [GitHub Repository](https://github.com/yourusername/ai-security-framework-crosswalk)
            """, style={"color": "var(--text-primary)", "lineHeight": "1.7"}),
        ]),
    ])
