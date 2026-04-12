# Project 2: AI Security Crosswalk Explorer

**Date:** 2026-04-12
**Course:** COMP 4433 Data Visualization, University of Denver, Spring 2026
**Dual purpose:** Course deliverable + open-source community tool for AI security practitioners

## 1. Purpose

An interactive Dash application that lets security architects, auditors, and researchers explore how nine major AI security frameworks relate to each other. The app answers three questions:

1. **What does the landscape look like?** A bird's-eye view of the nine frameworks and the density of mappings between them.
2. **What is inside a specific framework?** Its internal hierarchy, entry types, and where its controls map outward.
3. **If I have control X, what does it map to everywhere else?** Full cross-framework reachability, including transitive (2-hop) mappings through bridge frameworks, with the actual control language visible at every level.
4. **If I use Framework X, how much of Framework Y do I cover?** Coverage percentages and gap identification across all target frameworks.

## 2. Isolation Constraints

- Project 2 lives in a self-contained `project2/` directory at the repo root.
- Zero imports from any existing module (`mapping_engine/`, `classifier/`, `app/`, etc.).
- Static copies of `nodes.json` and `edges.json` bundled in `project2/data/`.
- Its own `requirements.txt`, `README.md`, and all necessary assets.
- Someone can clone the repo, `cd project2 && pip install -r requirements.txt && python app.py`, and the app runs.
- Nothing in the existing codebase references or depends on `project2/`.
- As part of this work, the existing Project 1 notebook submission will be reorganized into a `project1/` directory with its own self-contained structure, and the root README will be updated to reference both.

## 3. Data

### 3.1 Source Data

- `data/nodes.json` -- 983 nodes across 9 frameworks. Each node has: `node_id`, `framework`, `local_id`, `name`, `entry_type`, `parent_node_id`, `domain`, `description`, `function_class`, `keywords`, `mitigation_text`, `url`, and other framework-specific fields.
- `data/edges.json` -- 5,813 edges. Each edge has: `source_node_id`, `target_node_id`, `source_framework`, `target_framework`, `rationale_code` (PARENT, CROSS_FRAMEWORK_CATEGORY, SCOPE, DETECT, VALID, GOVERN, ISOLATE, GATE, DISCLOSE, PREV), `confidence` (authoritative, expert, suggestive, unvalidated), and `provenance`.
- 4,723 of 5,813 edges are cross-framework.

### 3.2 Frameworks

| Framework | Key | Nodes | Role |
|---|---|---:|---|
| AIUC-1 | `aiuc_1` | 189 | Comprehensive control catalogue, densest source |
| CSA AI Controls Matrix | `csa_aicm` | 261 | Second-largest control catalogue, bidirectional hub |
| MITRE ATLAS | `mitre_atlas` | 218 | Adversarial ML tactics and techniques |
| OWASP AI Exchange | `owasp_ai_exchange` | 88 | Curated risk and mitigation encyclopedia |
| NIST AI RMF | `nist_rmf` | 76 | Outcome-oriented, target-only |
| EU GPAI Code of Practice | `eu_gpai_cop` | 70 | Policy commitments from EU GPAI working groups |
| CoSAI Risk Map | `cosai_rm` | 61 | Coalition for Secure AI risk taxonomy |
| OWASP LLM Top 10 | `owasp_llm` | 10 | Target-only, 10 headline risks |
| OWASP Agentic Top 10 | `owasp_agentic` | 10 | Target-only, 10 headline risks |

### 3.3 Pre-Computed Derived Data

A `prepare_data.py` script runs once at setup time and produces `data/derived/`:

- **`coverage_matrix.json`** -- For every ordered pair of frameworks (source, target), the percentage of target nodes reachable from the source via 1-hop and 2-hop paths, broken down by confidence level (authoritative, expert, suggestive, unvalidated).
- **`framework_stats.json`** -- Per-framework summary: node count, edge count (in/out), entry type distribution, domain distribution, function class distribution.
- **`graph_metrics.json`** -- Per-framework-pair: total cross-framework edge count, confidence distribution, rationale code distribution. Also per-node: degree, cross-framework degree.
- **`hierarchy.json`** -- Per-framework: the parent-child tree derived from `parent_node_id` edges, suitable for direct consumption by Plotly sunburst/treemap.
- **`transitive_mappings.json`** -- For every node, its full 2-hop reachability: direct targets (1-hop) and transitive targets (2-hop) with the bridge node that connects them. Grouped by target framework.

## 4. Tech Stack

| Layer | Choice | Notes |
|---|---|---|
| Core | Dash 2.x, Plotly 5.x | Multi-page app via `dash.page_registry` |
| Layout | dash-bootstrap-components (DBC) | CYBORG theme (dark), FLATLY theme (light) |
| Graph ops | NetworkX | Used only in `prepare_data.py`, not at runtime |
| Data | pandas | DataFrames for filtering/aggregation at runtime |
| Styling | Custom CSS on top of DBC | Framework color palette, cyber accent highlights |

### 4.1 Dependencies (`requirements.txt`)

```
dash>=2.14
dash-bootstrap-components>=1.5
plotly>=5.18
pandas>=2.0
networkx>=3.0
```

## 5. Visual Design

### 5.1 Theme

- **Dark mode default** using DBC CYBORG as the base.
- **Light mode toggle** switching to DBC FLATLY.
- Professional core layout (clean typography, muted backgrounds, readable contrast) with cyber accent moments: electric blue (`#00d4ff`) on interactive elements, subtle glow on hover states, neon highlights on active selections.

### 5.2 Framework Color Palette

A consistent 9-color palette used everywhere (plots, badges, borders, dots):

| Framework | Color | Hex |
|---|---|---|
| AIUC-1 | Blue | `#1f6feb` |
| CSA AICM | Green | `#8fd18f` |
| MITRE ATLAS | Orange | `#e8845a` |
| OWASP AI Exchange | Teal | `#4ecdc4` |
| NIST AI RMF | Purple | `#cf85c4` |
| EU GPAI | Gold | `#d9bf55` |
| CoSAI | Steel blue | `#7aaed4` |
| OWASP LLM Top 10 | Coral | `#ff6b6b` |
| OWASP Agentic Top 10 | Amber | `#ffb347` |

### 5.3 Tooltip and Narrative Requirements

Every non-text UI element must be self-explaining:

1. **All icons** get a `title` attribute (native tooltip) AND a text label. No icon-only elements.
2. **All badges** get `dbc.Tooltip` components:
   - Confidence badges (e.g., "expert") explain the confidence level meaning.
   - Rationale badges (e.g., "SCOPE") explain the rationale code meaning.
   - Hop badges (e.g., "transitive", "via B006") explain the mapping path.
3. **All chart elements** use Plotly `hovertemplate` with formatted, human-readable hover text. No raw field names.
4. **All section headers** get a subtle info icon (with tooltip) explaining the section's purpose.
5. **Framework color indicators** are always paired with the framework name (never color-only).
6. **Each page** has an introductory narrative block explaining what the page shows, why it matters, and how to interact with it.

## 6. Pages

### 6.1 Page 1: Framework Landscape (Landing Page)

**Purpose:** Bird's-eye view of the AI security framework ecosystem.

**Layout:** Two-column grid with summary stats bar below.

**Visualizations:**
- **Network graph** (Plotly scatter + shapes): 9 framework supernodes, sized by node count, with weighted edges showing cross-framework mapping density. Interactive: hover shows framework stats, click navigates to Deep Dive for that framework.
- **Heatmap** (Plotly `go.Heatmap`): 9x9 matrix of pairwise mapping counts. Hover shows exact count and confidence breakdown.

**Dash Components:**
- `dcc.Dropdown` -- confidence level filter (Any, Suggestive+, Expert+, Authoritative only)
- `dcc.RadioItems` -- edge type filter (All, PARENT, CROSS_FRAMEWORK_CATEGORY, rationale-coded)

**Callbacks:**
- Confidence/edge-type filter updates both network graph and heatmap.
- Click on network node navigates to Page 2 with that framework pre-selected.

**Narrative:** Intro paragraph explaining the crosswalk concept, the nine frameworks, and how to read the visualizations. Summary stats bar showing total frameworks, nodes, edges, and cross-framework edges.

### 6.2 Page 2: Framework Deep Dive

**Purpose:** Explore a single framework's internal structure and outbound connections.

**Layout:** Control bar at top, two-column grid below, control detail card at bottom (hidden until sunburst click).

**Visualizations:**
- **Sunburst** (Plotly `go.Sunburst`): Framework hierarchy from `hierarchy.json`. Levels: domain, function_class, individual controls. Click a segment to select that control.
- **Stacked horizontal bar** (Plotly `go.Bar`): Outbound mapping distribution to each target framework, colored by confidence level (authoritative, expert, suggestive, unvalidated).

**Dash Components:**
- `dcc.Dropdown` -- framework selector (populated from the 9 frameworks, shows node count)
- `dcc.Checklist` -- entry type filter (control, risk, technique, mitigation, etc.)

**Control Detail Card** (appears on sunburst click):
- Full control text: name, description, entry type, function class, domain, keywords, frequency, URL (if available).
- "View in Crosswalk Explorer" button that navigates to Page 3 with that control pre-selected.

**Callbacks:**
- Framework dropdown updates sunburst + bar chart.
- Entry type checklist filters both visualizations.
- Sunburst `clickData` populates the control detail card.
- "View in Explorer" button navigates to Page 3 via `dcc.Location`.

### 6.3 Page 3: Crosswalk Explorer

**Purpose:** The core tool. Pick a control, see all its cross-framework mappings with full control language.

**Layout:** Control bar at top, Sankey + neighborhood graph in two-column grid, then framework-grouped expandable control cards below.

**Visualizations:**
- **Sankey diagram** (Plotly `go.Sankey`): Flow from source control through mapping tiers to target controls, grouped by framework. Shows the volume and distribution of mappings.
- **Neighborhood graph** (Plotly scatter + shapes): Selected control at center, 1-2 hop neighbors radiating outward, colored by framework. Interactive: hover shows control name, click selects a different control.

**Dash Components:**
- `dcc.Dropdown` -- source framework selector
- `dcc.Dropdown` -- control selector (chained: filtered by selected framework, searchable, shows control ID + name)
- `dcc.RadioItems` -- mapping filter (All, Direct only, Transitive only)
- `dcc.Input` -- text search to filter mapped controls by keyword

**Control Card Section:**
- **Pinned source control card** at top with full description text, entry type, and reachability summary bar (counts per framework, direct vs. transitive).
- **Framework-grouped sections** below, each with a header showing framework name, color, count, and "direct" or "via bridge" label.
- **Expandable control cards** within each group:
  - Collapsed: control ID, name, confidence badge, rationale badge, hop indicator.
  - Expanded: full description text, metadata (domain, function class, frequency), and **bridge path visualization** for transitive mappings showing: source control, rationale code, bridge node (name), CATEGORY, target control.
- **Mitigation text section** at bottom (when the source control has `mitigation_text`), with a shield icon labeled "Recommended Mitigations" and tooltip: "Countermeasures recommended by the source framework for this risk."

**Callbacks:**
- Source framework dropdown updates control dropdown options (chained callback).
- Control selection updates Sankey, neighborhood graph, source card, and all mapped control cards.
- Mapping filter (All/Direct/Transitive) filters the visible cards and updates Sankey.
- Text search filters cards by keyword match against control name and description.
- Card expand/collapse via callback on card click.
- Neighborhood graph `clickData` selects a new control (updates everything).

### 6.4 Page 4: Coverage Analysis

**Purpose:** Compliance gap analysis. "If I use Framework X, how much of Framework Y do I cover?"

**Layout:** Control bar at top, two-column grid below.

**Visualizations:**
- **Radar chart** (Plotly `go.Scatterpolar`): Coverage percentage for the selected source framework across all target frameworks. The shape immediately shows where coverage is strong and where gaps exist.
- **Stacked bar chart** (Plotly `go.Bar`): Coverage breakdown by confidence level (authoritative, expert, suggestive, unvalidated, no mapping) for each target framework, sorted by total coverage descending. Each bar includes a coverage percentage label.

**Dash Components:**
- `dcc.Dropdown` -- source framework selector
- `dcc.RangeSlider` -- minimum confidence threshold (maps to: Any, Suggestive+, Expert+, Authoritative only). Tooltip on the slider explains each confidence level.

**Callbacks:**
- Source framework + confidence threshold update both radar and stacked bar simultaneously.

## 7. Shared Components

### 7.1 Navigation Bar (`components/navbar.py`)

- Top navbar with page links (Landscape, Deep Dive, Crosswalk Explorer, Coverage Analysis).
- Active page highlighted with `#00d4ff` underline.
- Dark/light mode toggle (`dbc.Switch`) on the right.

### 7.2 Theme Engine (`components/theme.py`)

- `dbc.Switch` triggers a callback that swaps the DBC stylesheet between CYBORG and FLATLY.
- All Plotly figures reference a shared template that adapts to the current theme (paper_bgcolor, font color, gridline color).
- Custom CSS variables for the cyber accent colors that work in both modes.

### 7.3 Framework Colors (`components/framework_colors.py`)

- Single source of truth for the 9-framework color palette.
- Provides: `FRAMEWORK_COLORS` dict, `FRAMEWORK_DISPLAY_NAMES` dict, helper functions for Plotly color sequences.

### 7.4 Data Loader (`components/data_loader.py`)

- Loads all JSON files from `data/` and `data/derived/` at import time.
- Converts to pandas DataFrames where appropriate.
- Provides accessor functions used by all pages.
- No runtime file I/O after initial load.

### 7.5 Plot Theme (`components/plot_theme.py`)

- Shared Plotly template (dark and light variants) applied to every figure.
- Standardizes: font family, background colors, gridline colors, hover label styling, margin/padding.
- All plots use `hovertemplate` (never default hover).

## 8. File Structure

```
project2/
  app.py                        # Entry point, theme toggle, multi-page registry
  prepare_data.py               # Pre-compute derived data (run once at setup)
  requirements.txt              # Standalone dependencies
  README.md                     # Setup, usage, screenshots, data provenance
  data/
    nodes.json                  # 983 nodes, static copy
    edges.json                  # 5,813 edges, static copy
    derived/                    # Output of prepare_data.py
      coverage_matrix.json
      framework_stats.json
      graph_metrics.json
      hierarchy.json
      transitive_mappings.json
  assets/
    style.css                   # Custom theme, dark/light overrides, cyber accents
  pages/
    __init__.py
    landscape.py                # Page 1
    deep_dive.py                # Page 2
    explorer.py                 # Page 3
    coverage.py                 # Page 4
  components/
    __init__.py
    navbar.py
    theme.py
    framework_colors.py
    data_loader.py
    plot_theme.py
```

## 9. Assignment Requirements Coverage

| Requirement | How We Exceed It |
|---|---|
| Data of your choice (not built-in) | Original dataset: 983 AI security framework controls across 9 frameworks with 5,813 relationship edges. No other student will have this data. |
| Plotly + Dash | Multi-page Dash 2.x app with DBC, Plotly graph_objects throughout |
| At least 4 Dash Core Components | **7+ types:** Dropdown (x5), RadioItems (x2), Checklist, Input, RangeSlider, Switch, Location (navigation). Plus DBC components: Collapse (expandable cards), Tooltip, Navbar. |
| At least 1 callback | **12+ callbacks** including chained callbacks (framework updates control list), clickData callbacks (sunburst, graph), cross-page navigation, and theme toggle |
| At least 3 different Plotly plots | **7 types:** network graph, heatmap, sunburst, stacked horizontal bar, Sankey diagram, radar (scatterpolar), stacked vertical bar |
| Sufficient narrative/instructional info | Every page has intro text, every icon has a tooltip, every badge has an explanation, every section header has context. Plus full README with screenshots. |
| Aesthetics fine-tuned, best practices | Custom 9-color accessible palette, dark/light toggle, Plotly templates with formatted hovertemplates, consistent typography, cyber accent design language |
| Deployment-ready, GitHub repo | Self-contained directory with requirements.txt, README, static data, `prepare_data.py` pipeline. Clone and run. |

## 10. Repo Restructuring

As part of this work:

1. Move existing Project 1 notebook and submission materials into `project1/` with its own README.
2. Update the root README to reference both `project1/` and `project2/` as separate course deliverables.
3. Verify no existing references or imports break after the move.

## 11. Community Value

After course completion, this tool will be published as an open-source resource for the AI security community:

- **Security architects** can trace controls across frameworks to map compliance posture.
- **Auditors** can verify cross-framework coverage and identify gaps.
- **Researchers** can explore the landscape of AI security standards and their relationships.
- **Policy makers** can see where standards overlap and where coordination is needed.
- **The bridge path visualization** for transitive mappings is unique: no other tool surfaces these indirect relationships with full provenance.
