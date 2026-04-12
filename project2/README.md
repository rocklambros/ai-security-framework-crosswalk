# AI Security Crosswalk Explorer

An interactive Dash application for exploring cross-framework mappings across nine major AI security standards. Built as a course deliverable for COMP 4433 Data Visualization (University of Denver, Spring 2026) and designed as a reusable tool for the AI security community.

## What This Does

Security architects working with AI systems face a fragmented standards landscape. OWASP, NIST, MITRE, CSA, and others each publish overlapping frameworks, but none reference each other in a machine-readable way. This tool bridges that gap.

The application visualizes a knowledge graph of **983 controls, risks, and techniques** across **9 frameworks**, connected by **5,813 relationship edges**. It lets you:

- **Explore the landscape** -- see how frameworks relate at the ecosystem level
- **Deep dive** into any framework's internal hierarchy and outbound connections
- **Trace mappings** from any control to its cross-framework equivalents, including transitive (2-hop) relationships through bridge frameworks
- **Analyze coverage** -- if you comply with Framework X, what percentage of Framework Y do you cover?

## Frameworks Included

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
python app.py            # Start the app
```

Open http://localhost:8050 in your browser.

### Requirements

```
dash>=2.14
dash-bootstrap-components>=1.5
plotly>=5.18
pandas>=2.0
networkx>=3.0
```

## Application Pages

### 1. Framework Landscape (Landing Page)
Bird's-eye view with an interactive network graph of framework relationships and a 9x9 mapping density heatmap. Filter by confidence level and relationship type.

### 2. Framework Deep Dive
Select a framework to see its internal hierarchy (sunburst chart) and outbound mapping distribution (stacked bar). Click any control in the sunburst to see its full text and jump to the Explorer.

### 3. Crosswalk Explorer
The core tool. Pick a framework and control to see all cross-framework mappings. Features a Sankey diagram showing mapping flow, a neighborhood graph, and expandable control cards with full text and bridge path visualization for transitive mappings.

### 4. Coverage Analysis
Compliance gap analyzer. Select a source framework to see radar and bar charts showing what percentage of each target framework you cover through direct and transitive mappings.

## Data

The application uses two static JSON files in `data/`:

- `nodes.json` -- 983 framework entries (controls, risks, techniques, etc.)
- `edges.json` -- 5,813 relationship edges with confidence and rationale metadata

The `prepare_data.py` script pre-computes derived aggregates in `data/derived/` for fast app startup. These files are included in the repository and do not need to be regenerated unless the source data changes.

## Architecture

```
project2/
  app.py              # Entry point, multi-page Dash app
  prepare_data.py     # Data pipeline (run once)
  data/               # Static source data + derived aggregates
  pages/              # One module per page
  components/         # Shared: colors, themes, data loader, navbar
  assets/             # Custom CSS
```

## License

This project is part of the AI Security Framework Crosswalk repository. See the root LICENSE file for terms.
