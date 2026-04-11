# Spec 2: AI Security Framework Crosswalk — Dash Visualization App

## Summary

Build a deployment-ready interactive Dash application with a network-graph-centric design. The app visualizes cross-framework security control mappings from 14 AI security frameworks (3,210 expert-curated mappings + ML-predicted extensions). Five pages: Network Explorer, Coverage Dashboard, Mapping Browser, Model Performance, and About. Dark/light mode toggle. 7 DCC components, 7+ Plotly/Cytoscape plot types, cross-filtering callbacks. Deployed to HuggingFace Spaces.

This is the COMP 4433 Project 2 deliverable.

## Migration Note

This spec replaces the existing 3-tab Dash app (`app/dash_app/tabs/tab1_lookup.py`, `tab4_matrix.py`, `tab5_ablations.py`). The existing app is a minimal prototype; this is a full redesign with 5 pages, network graph, theming, and cross-filtering. Existing tab files will be removed and replaced by the new `pages/` structure.

## Data Sources

The app consumes two categories of data:

1. **Expert-curated mappings** (static, high confidence):
   - `data/upstream/mappings_v1.jsonl` — 3,210 expert-verified control mappings
   - `data/upstream/crossrefs_v1.jsonl` — 363 cross-reference edges
   - `data/frameworks/` — 14 framework definitions with control hierarchies

2. **ML predictions** (from Spec 1 pipeline, loaded at app startup):
   - Stacker predictions with 4-class probabilities for candidate pairs
   - Conformal prediction sets per pair
   - Router needs_review flags
   - Model metadata (sacred run metrics, ablation results)

Expert mappings are displayed with solid styling and a checkmark badge. ML predictions are displayed with dashed/faded styling and a warning badge + confidence score.

## Pages

### Page 1: Network Explorer (Home)

**Layout:** Three-column — left filter sidebar (260px) | center network graph (flex) | right detail panel (300px)

**Center: Interactive Network Graph (dash-cytoscape)**
- Frameworks as colored supernodes (larger circles, labeled)
- Individual controls as smaller nodes clustered around their framework
- Mappings as edges: color-coded by tier (equivalent=#3fb950, related=#58a6ff, partial=#d29922)
- Edge thickness proportional to confidence score
- Expert-verified edges: solid lines. ML-predicted edges: dashed lines.
- Layout: `cose-bilkent` (force-directed with compound node support)
- Interactions: click node to select, hover for tooltip, zoom/pan, box-select
- Graph controls overlay: zoom in/out, reset, fit-to-screen buttons
- Stats badge (top-right): "14 frameworks, 3,210 mappings, 983 controls"

**Left Sidebar: Filters (7 DCC Components)**

1. **Framework multi-select checklist** (`dcc.Checklist`): toggle frameworks on/off in the graph. Grouped by category (OWASP, NIST, MITRE, etc.)
2. **Tier radio buttons** (`dcc.RadioItems`): filter edges by mapping tier (All / Equivalent / Related / Partial)
3. **Confidence threshold slider** (`dcc.Slider`): min=0.0, max=1.0, step=0.05, default=0.0. Hides edges below threshold.
4. **Search text input** (`dcc.Input`): full-text search across control IDs and descriptions. Matching nodes highlighted in graph.
5. **Source framework dropdown** (`dcc.Dropdown`): filter to show only mappings FROM selected framework
6. **Data source toggle** (`dcc.RadioItems`): Expert Only / ML Predicted Only / Both
7. **Dark mode toggle** (`dbc.Switch`): toggles CSS custom properties between dark and light themes. Persists to localStorage via clientside callback.

**Right Panel: Node Detail**
- Shows when a node is selected in the graph
- Control ID + name + framework
- Full description text
- Connected mappings list: sorted by confidence, showing tier badge, confidence score, source (Expert/ML), link to target control
- Click a mapping to navigate to that node in the graph

**Callbacks:**
- Filter changes → update graph elements (nodes/edges visibility)
- Search input → highlight matching nodes, dim others
- Click node → populate detail panel
- Click mapping in detail panel → select target node, re-center graph
- Confidence slider → filter edges
- Dark mode toggle → clientside callback swaps CSS variables

### Page 2: Coverage Dashboard

**Layout:** 2x2 grid top + 1x2 grid bottom

**Top-Left: Framework-Pair Coverage Heatmap** (`plotly.graph_objects.Heatmap`)
- Source frameworks (rows) x Target frameworks (columns)
- Color scale: red (0%) → yellow (50%) → green (100%)
- Hover: shows exact coverage %, number of mapped controls, number of total controls
- Click cell → filters Mapping Browser to that framework pair

**Top-Right: Per-Framework Coverage Bars** (`plotly.graph_objects.Bar`)
- Horizontal bars, sorted descending by coverage score
- Color gradient matching coverage (red→green)
- Annotation: coverage % at end of each bar

**Bottom-Left: Mapping Flow Sankey** (`plotly.graph_objects.Sankey`)
- Left nodes: source frameworks
- Middle nodes: mapping tiers (equivalent, related, partial)
- Right nodes: target frameworks
- Link width proportional to number of mappings
- Color-coded by tier

**Bottom-Right: Summary Statistics Cards**
- Total frameworks, total mappings, total controls, average coverage
- Styled as large number + label (dashboard KPI style)

**Callbacks:**
- All plots respond to the same framework filter state (shared via `dcc.Store`)
- Click heatmap cell → cross-filter other plots to that framework pair

### Page 3: Mapping Browser

**Layout:** Search/filter bar (top) + data table (main)

**Filter Bar:**
- Full-text search input
- Source framework dropdown
- Target framework dropdown
- Tier dropdown (multi-select)
- Data source filter (Expert/ML/Both)

**Data Table** (`dash.dash_table.DataTable`):
- Columns: Source Control, Target Control, Tier, Confidence, Data Source, Conformal Set, Needs Review
- Sortable by any column
- Pagination: 25 rows per page
- Row styling: Expert rows = normal, ML rows = italic with amber highlight
- Export buttons: CSV, JSON (machine-readable)

**Callbacks:**
- Filter changes → update table data
- Search → full-text filter across source and target control text
- Click row → navigate to Network Explorer with that mapping highlighted

### Page 4: Model Performance

**Layout:** 3-column top + 2-column bottom

**Top-Left: Confusion Matrix** (`plotly.graph_objects.Heatmap`)
- 4x4 predicted vs actual on human_test_frozen
- Annotated with counts and percentages
- Color scale: blues

**Top-Center: Per-Class F1 Radar** (`plotly.graph_objects.Scatterpolar`)
- 4 axes: equivalent, partial, related, unrelated
- Filled area showing F1 per class
- Overlay: old pipeline vs new pipeline (two traces)

**Top-Right: Ablation Comparison** (`plotly.graph_objects.Bar`)
- Grouped horizontal bars: tier_acc and macro_F1 by config
- Sorted descending by tier_acc
- Annotations: delta from baseline

**Bottom-Left: Conformal Coverage** (`plotly.graph_objects.Bar`)
- Per-tier coverage bars vs 90% target line (`add_hline`)
- Average set size as secondary y-axis line

**Bottom-Right: Calibration Reliability Diagram** (`plotly.graph_objects.Scatter`)
- Predicted probability vs actual frequency, per tier
- Perfect calibration diagonal line
- Histograms of predicted probabilities (subplot below)

**Callbacks:**
- Ablation config dropdown → update all plots to show selected config's results
- Toggle: show old pipeline vs new pipeline comparison

### Page 5: About

- Project description and purpose
- Methodology overview (plain language)
- Data sources and attribution (CC BY-SA 4.0 for OWASP DSGAI corpus; GenAI Security Project crosswalk)
- How to interpret mapping tiers (equivalent, related, partial, unrelated)
- How to interpret confidence scores and conformal sets
- Link to GitHub repo
- Link to paper/notebook
- Contact/attribution

## Theming: Dark/Light Mode

**Implementation:** CSS custom properties with two sets of values.

**Dark theme (default):**
```
--bg-primary: #0d1117
--bg-secondary: #161b22
--bg-tertiary: #21262d
--border: #30363d
--text-primary: #c9d1d9
--text-secondary: #8b949e
--text-muted: #484f58
--accent-blue: #58a6ff
--accent-green: #3fb950
--accent-yellow: #d29922
--accent-red: #da3633
--accent-purple: #bc8cff
--accent-pink: #f778ba
--accent-orange: #f0883e
```

**Light theme:**
```
--bg-primary: #ffffff
--bg-secondary: #f6f8fa
--bg-tertiary: #eaeef2
--border: #d0d7de
--text-primary: #1f2328
--text-secondary: #656d76
--text-muted: #8b949e
--accent-blue: #0969da
--accent-green: #1a7f37
--accent-yellow: #9a6700
--accent-red: #cf222e
--accent-purple: #8250df
--accent-pink: #bf3989
--accent-orange: #bc4c00
```

**Toggle:** `dbc.Switch` in the top nav bar. Uses `clientside_callback` to swap a `data-theme` attribute on the body element. Plotly chart templates update via callback (dark: `plotly_dark`, light: `plotly_white`). Persists to `localStorage`.

## DCC Components (7, need 4)

1. Framework multi-select checklist (`dcc.Checklist`)
2. Tier radio buttons (`dcc.RadioItems`)
3. Confidence threshold slider (`dcc.Slider`)
4. Search text input (`dcc.Input`)
5. Source/Target framework dropdowns (`dcc.Dropdown` x2)
6. Data source toggle (`dcc.RadioItems`)
7. Dark mode toggle (`dbc.Switch`)

## Plot Types (7, need 3)

1. Network graph (dash-cytoscape)
2. Coverage heatmap (`go.Heatmap`)
3. Sankey diagram (`go.Sankey`)
4. Horizontal bar chart (`go.Bar`)
5. Radar/spider chart (`go.Scatterpolar`)
6. Confusion matrix heatmap (`go.Heatmap`)
7. Calibration scatter + line (`go.Scatter`)

## Callbacks

- **Cross-filter:** Shared `dcc.Store` holds current filter state. All pages read from it.
- **Graph interaction:** Node click → detail panel, edge click → mapping info
- **Search:** Debounced text input → filter graph nodes, table rows
- **Theme toggle:** Clientside callback, zero server round-trip
- **Navigation:** Click heatmap cell → go to Mapping Browser filtered to that pair
- **Export:** CSV/JSON download callbacks on Mapping Browser

## Technology Stack

- **Dash** 2.x + **dash-bootstrap-components** (FLATLY/DARKLY themes as base)
- **dash-cytoscape** for network graph
- **Plotly** for all other charts
- **pandas** for data loading/filtering
- Python 3.10+

## Deployment

- **Local:** `python -m app.dash_app.app` on port 8050, host 0.0.0.0
- **Docker:** Multi-stage build, supervisord, exposed on 8050
- **HuggingFace Spaces:** Via `app/scripts/deploy_hf_space.py` with attribution checks
- **GitHub repo:** README with setup instructions, requirements.txt, sample data

## COMP 4433 Project 2 Requirements Checklist

- [x] Real-world data (not built-in): crosswalk data from 14 AI security frameworks
- [x] At least 4 DCC components: 7 provided
- [x] At least 1 callback decorator: 10+ callbacks (cross-filter, search, theme, navigation, export)
- [x] At least 3 different Plotly plots: 7 plot types
- [x] Narrative/instructional info: About page + per-page headers + tooltips
- [x] Deployment-ready: Docker + HF Spaces + GitHub with README
- [x] Explanatory/purposeful: community resource for visualizing cross-framework security mappings

## File Structure

```
app/
  dash_app/
    app.py                  # Dash app factory, theme setup, navigation
    assets/
      style.css             # CSS custom properties (dark/light themes)
      custom.js             # localStorage theme persistence
    pages/
      network.py            # Page 1: Network Explorer
      coverage.py           # Page 2: Coverage Dashboard
      mappings.py           # Page 3: Mapping Browser
      model.py              # Page 4: Model Performance
      about.py              # Page 5: About
    components/
      filters.py            # Shared filter sidebar component
      detail_panel.py       # Node detail panel component
      theme_toggle.py       # Dark mode toggle component
      graph_builder.py      # Build cytoscape elements from data
    data/
      loader.py             # Load mappings, predictions, metrics
      frameworks.py         # Framework metadata and display labels
  deploy/
    Dockerfile
    THIRD_PARTY_NOTICES.md
  scripts/
    deploy_hf_space.py
```

## Success Criteria

1. All 5 pages render correctly in both dark and light themes
2. Network graph handles 3,210+ edges without visible lag (<2s initial load)
3. Cross-filtering works across all pages via shared state
4. Search returns results within 200ms
5. All 7 DCC components functional
6. All 7 plot types render correctly
7. CSV/JSON export produces valid files
8. Playwright tests pass for all pages in both themes
9. Deploys successfully to HuggingFace Spaces
10. Meets all COMP 4433 Project 2 requirements

## Dependencies

- Spec 1 model artifacts for ML predictions (app can run without them, showing only expert mappings)
- dash-cytoscape library
- Upstream data files in `data/upstream/`
