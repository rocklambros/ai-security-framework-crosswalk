# AI Security Crosswalk Explorer

An interactive Dash application for exploring cross-framework mappings across nine major AI security standards. Built as a course deliverable for COMP 4433 Data Visualization (University of Denver, Spring 2026) and designed as a reusable tool for the AI security community.

## What this does

Security architects working with AI systems face a fragmented standards landscape. OWASP, NIST, MITRE, CSA, and others each publish overlapping frameworks, but none reference each other in a machine-readable way. This tool bridges that gap.

The application visualizes a knowledge graph of **983 controls, risks, and techniques** across **9 frameworks**, connected by **4,342 relationship edges** (including 341 upstream-sourced mappings). It lets you:

- **Explore the landscape** -- see how frameworks relate at the ecosystem level via an interactive network graph and a 9x9 pairwise mapping heatmap with a toggle between direct edges and transitive reachability
- **Deep dive** into any framework's internal hierarchy and cross-framework connections at the individual control level
- **Trace mappings** from any control to its cross-framework equivalents, including transitive (2-hop) relationships through bridge frameworks, with Sankey diagrams and expandable control cards
- **Analyze coverage** -- if you comply with Framework X, what percentage of Framework Y do you cover through direct and transitive mappings?

## Frameworks included

| Framework | Nodes | Description |
|---|---:|---|
| AIUC-1 | 189 | Comprehensive AI use case control catalogue |
| CSA AI Controls Matrix | 261 | Cloud Security Alliance AI control framework |
| MITRE ATLAS | 218 | Adversarial ML tactics and techniques |
| OWASP AI Exchange | 88 | Curated risk and mitigation encyclopedia |
| NIST AI RMF 1.0 | 76 | AI Risk Management Framework |
| EU GPAI Code of Practice | 70 | EU General-Purpose AI policy commitments |
| CoSAI Risk Map | 61 | Coalition for Secure AI risk taxonomy |
| OWASP LLM Top 10 | 10 | Top 10 risks for LLM applications |
| OWASP Agentic Top 10 | 10 | Top 10 risks for agentic AI systems |

## Setup

### Prerequisites

- Python 3.10+
- pip

### Installation

```bash
cd project2
pip install -r requirements.txt
python prepare_data.py   # Pre-compute derived data (takes ~30 seconds)
python app.py            # Start the app at http://localhost:8050
```

### Requirements

All dependencies are pinned in `requirements.txt`. Core libraries: Dash, Plotly, dash-bootstrap-components, pandas, NetworkX, PyYAML.

## Application pages

### 1. Framework Landscape (landing page)

Bird's-eye view of the AI security ecosystem. The page has three main elements:

- **Network graph** -- Nine framework nodes arranged in a radial layout. Node size encodes framework breadth (node count). Edge width encodes cross-framework mapping density. Two edge types are visually distinguished: rationale-coded edges (solid cyan) and category links (dashed gold). Hover for details; click a node to highlight its connections.
- **Pairwise heatmap** -- A 9x9 symmetric matrix of cross-framework mapping counts. A **Mapping Scope** toggle switches between "Direct edges" (unique node pairs connected by explicit edges) and "All reachability" (unique node pairs reachable via direct or 2-hop transitive paths through bridge frameworks). For example, MITRE ATLAS and CSA AICM have zero direct edges but 629 reachable pairs via bridges like AIUC-1. Click any cell for a detail panel showing individual mappings.
- **Filters** -- Confidence level (Any / Suggestive+ / Expert+ / Authoritative) and relationship type (All / Rationale-coded / Category links) filter the network and heatmap in real time.

### 2. Framework Deep Dive

Select a framework to drill into its internal structure:

- **Level 0** -- Framework overview: domain nodes sized by child count
- **Level 1** -- Click a domain to see its top-level controls
- **Level 2** -- Click a control to see its cross-framework mappings as a radial network, with a bidirectional bar chart showing inbound and outbound mapping counts per target framework

### 3. Crosswalk Explorer

The core mapping tool. Pick a framework and control to see:

- **Sankey diagram** -- Flow from the source control through mapping tiers (direct/transitive) to target frameworks
- **Neighborhood graph** -- Radial network with direct neighbors (inner ring, solid edges, circles) and transitive neighbors (outer ring, dashed edges, diamonds)
- **Control cards** -- Expandable cards with full control text, confidence badges, rationale codes, and bridge path visualization for transitive mappings

Controls can be reached via URL parameters (`?framework=aiuc_1&node=aiuc_1:B001`) or by clicking through the Deep Dive.

### 4. Coverage Analysis

Compliance gap analyzer. Select a source framework to see:

- **Radar chart** -- Coverage percentages across all target frameworks, with separate traces for total and direct-only coverage
- **Stacked bar chart** -- Direct coverage, transitive coverage, and gap as segments summing to 100%. Percentage annotations use ordinal blue luminance to encode coverage quality.

## Data pipeline

The application uses two source JSON files in `data/`:

- `nodes.json` -- 983 framework entries (controls, risks, techniques, etc.)
- `edges.json` -- 4,001 base relationship edges with confidence and rationale metadata

Running `python prepare_data.py` reads these files (plus any upstream enrichments) and generates derived aggregates in `data/derived/`:

| File | Description |
|---|---|
| `nodes_enriched.json` | Nodes with domain assignments |
| `edges_enriched.json` | Edges merged with upstream sources (4,342 total) |
| `framework_stats.json` | Per-framework summary counts |
| `coverage_matrix.json` | Pairwise direct and transitive coverage percentages |
| `hierarchy.json` | Sunburst-compatible hierarchy (ids, labels, parents, values) |
| `transitive_mappings.json` | Per-node direct and transitive (2-hop) mapping lists |
| `graph_metrics.json` | Network topology metrics (degree, betweenness, etc.) |
| `pairwise_reachability.json` | 9x9 matrix of unique node pairs reachable per framework pair |

These files are included in the repository and do not need to be regenerated unless the source data changes.

## Visualization design

Every Plotly chart follows principles from four assigned readings on data visualization best practices. The full rationale is documented in [VISUALIZATION_DESIGN.md](VISUALIZATION_DESIGN.md). Key design decisions:

- **Framework palette** -- 9 distinct categorical colors with maximum hue and luminance separation, tested against deuteranopia/protanopia simulation (Graze & Schwabish 2024)
- **Heatmap colorscale** -- Single-hue blue luminance ramp avoiding the rainbow colormap pitfall (Borland & Taylor 2007)
- **Coverage labels** -- Ordinal blue luminance (bright = good, dark = poor) rather than traffic-light colors (Borner et al. 2019)
- **Bar charts** -- Position along a common scale wherever possible (Cleveland & McGill 1984, rank 1)
- **Redundant encoding** -- Direct/transitive distinction encoded by ring position, line style, and marker shape simultaneously

## Architecture

```
project2/
  app.py              # Entry point, multi-page Dash app with dark/light toggle
  prepare_data.py     # Data pipeline: reads source JSONs, writes derived/
  requirements.txt    # Python dependencies
  data/
    nodes.json        # 983 framework entries
    edges.json        # 4,001 base edges
    derived/          # Pre-computed aggregates (8 JSON files)
  pages/
    landscape.py      # Framework Landscape (network + heatmap)
    deep_dive.py      # Framework Deep Dive (hierarchy + control detail)
    explorer.py       # Crosswalk Explorer (Sankey + neighborhood + cards)
    coverage.py       # Coverage Analysis (radar + stacked bar)
  components/
    framework_colors.py  # 9-color categorical palette + confidence colors
    data_loader.py       # Module-level data cache, accessor functions
    plot_theme.py        # Dark/light Plotly templates
    navbar.py            # Navigation bar with theme toggle
    badge_tooltips.py    # Reusable badge + tooltip components
  assets/
    custom.css        # Dark/light theme CSS
  VISUALIZATION_DESIGN.md  # Per-figure design rationale
```

## See also

- [Root README](../README.md) -- Full project context and system architecture
- [Project 1 README](../project1/README.md) -- Scientific notebook with 24 figures
- [Visualization Design Rationale](VISUALIZATION_DESIGN.md) -- Per-figure design decisions citing dataviz readings
