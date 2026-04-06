# Unified Crosswalk Graph Schema v1.0

Graph-native data model for mapping relationships across AI security frameworks.

## Files

| File | Purpose |
|------|---------|
| `node.schema.json` | JSON Schema for graph vertices (controls, risks, techniques, etc.) |
| `edge.schema.json` | JSON Schema for graph edges (mapping relationships between any two nodes) |

## Design rationale

### Why a graph, not pairwise crosswalk files

The `schema_template/crosswalk-mapping-v2.schema.json` in this repo is the right format for a single pairwise crosswalk: one source framework mapped to one target framework. It captures rationale taxonomy, relevance levels, function coverage, and gap analysis for that pair.

The crosswalk project maps 10 frameworks to each other. Pairwise files would require up to 45 documents (10 choose 2). Querying across framework pairs (e.g., "show me every framework that addresses prompt injection") means joining across files. That's painful for the Dash app and impossible for network-level statistics in the EDA notebook.

The graph schema solves this by decomposing every pairwise crosswalk into two flat tables: nodes and edges. A NetworkX graph loads from these two files in 3 lines of Python. Pandas DataFrames filter edges by framework pair, rationale code, or relevance level with standard boolean indexing. No joins across files. No 45-document maintenance burden.

### Relationship to the v2 pairwise schema

The v2 schema (`schema_template/crosswalk-mapping-v2.schema.json`) remains the provenance format. When a new expert crosswalk is produced (e.g., AIUC-1 to OWASP Agentic Top 10), it validates against the v2 schema and gets committed as a standalone JSON file. The build script then decomposes it into nodes and edges in the graph.

The graph schema carries every field from the v2 schema that matters for visualization and querying. What it drops: the v2 schema's `summary` and `gap_analysis` sections become computed properties of the graph (degree counts, missing edge types). They don't need to be stored because NetworkX computes them instantly.

### Node design decisions

**Globally unique node_id.** Format: `{framework_key}:{local_id}`. The framework key is a short, stable string (aiuc_1, owasp_llm, mitre_atlas). The local_id preserves the original identifier from the source framework exactly as published. This means AIUC-1 control B006 is `aiuc_1:B006` and MITRE ATLAS technique AML.T0051 is `mitre_atlas:AML.T0051`.

**entry_type distinguishes what a node represents.** Controls (AIUC-1, CSA AICM), risks (OWASP Top 10 entries, CoSAI risks), techniques (MITRE ATLAS), mitigations (MITRE ATLAS), functions and subcategories (NIST AI RMF hierarchy), commitments and measures (EU GPAI Code of Practice), activities (AIUC-1 sub-tasks). This field drives icon selection and color coding in the Dash app.

**parent_node_id models hierarchy.** AIUC-1 activities point to their parent control. NIST subcategories point to their parent function. MITRE subtechniques point to their parent technique. This enables treemap and sunburst visualizations without a separate hierarchy file. An edge with `rationale_code: PARENT` is also created for each parent-child relationship, so the hierarchy is queryable from the edges table too.

**function_class from the v2 rationale taxonomy.** The 8 codes (PREV, SCOPE, GATE, DETECT, VALID, GOVERN, ISOLATE, DISCLOSE) classify a node's primary defensive function. Required for AIUC-1 controls (where it's been validated). Optional for other frameworks. This field drives the function coverage heatmap: for any target risk, count how many source controls exist per function class.

**Framework-specific fields are nullable.** Fields like `classification` (Mandatory/Optional), `control_type` (Preventative/Detective), `frequency`, and `applicable_capabilities` come from AIUC-1's rich control metadata. Other frameworks don't have these fields. They're set to null or empty arrays for non-AIUC-1 nodes. The schema allows this rather than forcing a lowest-common-denominator model that loses AIUC-1's depth.

### Edge design decisions

**Directional edges.** Every edge has a source and a target. AIUC-1 control B006 "maps to" OWASP Agentic ASI01. The direction matters for Sankey diagrams and for computing in-degree (how many controls map to a risk) vs out-degree (how many risks a control addresses).

**rationale_code is nullable.** The AIUC-1 Agentic mapping v2 provides rationale codes for every mapping. The markdown crosswalks and the AIUC-1 standard's embedded framework_references do not. Rather than forcing a guess, null means "no rationale data available." The Dash app can filter to show only edges with rationale data, or show all edges with quality indicators.

**confidence is the data quality gradient.** Four levels: authoritative (from the framework's own published data), expert (from a manually curated crosswalk), inferred (from heuristic matching by the build script), unvalidated (from a markdown web scrape). This lets the visualization app show high-confidence edges in bold and low-confidence edges as dashed lines. The EDA notebook can compare edge density across confidence levels.

**provenance traces every edge to its source file.** This is the audit trail. When a user clicks an edge in the Dash app, the provenance field tells them where the mapping came from. When the build script runs, it tags every edge with the filename that produced it.

**PARENT edges encode hierarchy.** Instead of modeling hierarchy only in parent_node_id on nodes, PARENT edges appear in the edges table too. This means a single query on the edges DataFrame can traverse both cross-framework mappings and within-framework hierarchy. A treemap of "NIST AI RMF functions, with controls from all frameworks that map to each subcategory" is one groupby operation.

### Framework registry

The `framework` enum in node.schema.json defines the current set:

| Key | Framework | Version | Nodes expected |
|-----|-----------|---------|----------------|
| aiuc_1 | AIUC-1 | 1.0 | ~51 controls + ~130 activities |
| owasp_llm | OWASP Top 10 for LLM Applications | 2025 | 10 risks |
| owasp_agentic | OWASP Top 10 for Agentic Applications | 2026 | 10 risks |
| mitre_atlas | MITRE ATLAS | 5.0.1 | ~60 techniques + ~30 mitigations + ~15 tactics |
| nist_rmf | NIST AI RMF | 1.0 | 4 functions + ~27 subcategories |
| nist_600_1 | NIST AI 600-1 (GenAI Profile) | 1.0 | TBD |
| csa_aicm | CSA AI Controls Matrix | 1.0 | 243 controls across 18 domains |
| cosai_rm | CoSAI Risk Map | current | ~50 risks + ~40 controls |
| eu_gpai_cop | EU GPAI Code of Practice | 2025 | 12 commitments + ~30 measures |
| owasp_ai_exchange | OWASP AI Exchange | current | TBD |

To add a new framework: add its key to the `framework` enum in node.schema.json, update this table, and run the build script.

### Output files

The build script (`scripts/build_graph.py`) reads all source data under `data/frameworks/` and produces:

```
data/processed/nodes.json       # Array of node objects
data/processed/edges.json       # Array of edge objects
data/processed/graph_stats.json # Computed summary statistics
```

### Loading the graph

```python
import json
import pandas as pd
import networkx as nx

# Load as DataFrames (for EDA, filtering, plotting)
nodes_df = pd.read_json('data/processed/nodes.json')
edges_df = pd.read_json('data/processed/edges.json')

# Load as NetworkX graph (for network analysis)
G = nx.DiGraph()
for _, n in nodes_df.iterrows():
    G.add_node(n['node_id'], **n.to_dict())
for _, e in edges_df.iterrows():
    G.add_edge(e['source_node_id'], e['target_node_id'], **e.to_dict())

# Query: all controls that map to ASI01 (Agent Goal Hijack)
asi01_edges = edges_df[edges_df['target_node_id'] == 'owasp_agentic:ASI01']

# Query: function coverage for ASI01
asi01_coverage = asi01_edges.groupby('rationale_code').size()

# Query: cross-framework edges only (exclude PARENT hierarchy edges)
cross_fw = edges_df[edges_df['source_framework'] != edges_df['target_framework']]
```

### Visualization mapping

| Visualization | Data source | Key fields |
|---------------|-------------|------------|
| Network graph | nodes.json + edges.json | node_id, framework (color), entry_type (shape), relevance (edge weight) |
| Sankey diagram | edges.json filtered by framework pair | source_node_id, target_node_id, rationale_code (link color) |
| Heatmap (coverage) | edges.json grouped by target + rationale_code | target_node_id, rationale_code, count |
| Sunburst / Treemap | nodes.json filtered by parent_node_id | node_id, parent_node_id, domain, framework |
| Radar chart | edges.json grouped by rationale_code per target | 8 rationale codes as axes, count as radius |
| Bar chart (degree) | NetworkX in/out degree | node_id, degree |
| Gap analysis | nodes with degree 0 or missing rationale codes | node_id, framework, function_class |

### Schema version history

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-04-06 | Initial graph schema. Decomposes v2 pairwise crosswalks into nodes + edges. Adds confidence, provenance, PARENT edges, nullable rationale for low-fidelity sources. |
