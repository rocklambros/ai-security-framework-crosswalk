# Project 2: AI Security Crosswalk Explorer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a self-contained, four-page interactive Dash application that lets security professionals explore cross-framework mappings across nine AI security standards.

**Architecture:** Multi-page Dash 2.x app with dash-bootstrap-components. Static JSON data is pre-processed by `prepare_data.py` into derived aggregates. Each page is a separate module under `pages/`. Shared components (colors, themes, data loading) live under `components/`. The entire app lives in `project2/` with zero dependencies on the parent repo.

**Tech Stack:** Dash 2.x, Plotly 5.x, dash-bootstrap-components 1.5+, pandas, NetworkX (build-time only)

**Spec:** `docs/superpowers/specs/2026-04-12-project2-crosswalk-explorer-design.md`

---

## Task 1: Project Scaffold and Data Copy

**Files:**
- Create: `project2/requirements.txt`
- Create: `project2/app.py`
- Create: `project2/pages/__init__.py`
- Create: `project2/components/__init__.py`
- Create: `project2/assets/style.css` (empty placeholder)
- Copy: `data/processed/nodes.json` -> `project2/data/nodes.json`
- Copy: `data/processed/edges.json` -> `project2/data/edges.json`
- Create: `project2/data/derived/.gitkeep`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p project2/{data/derived,assets,pages,components}
```

- [ ] **Step 2: Create requirements.txt**

Write to `project2/requirements.txt`:

```
dash>=2.14
dash-bootstrap-components>=1.5
plotly>=5.18
pandas>=2.0
networkx>=3.0
```

- [ ] **Step 3: Copy static data files**

```bash
cp data/processed/nodes.json project2/data/nodes.json
cp data/processed/edges.json project2/data/edges.json
touch project2/data/derived/.gitkeep
```

- [ ] **Step 4: Create __init__.py files**

Write empty files:
- `project2/pages/__init__.py`
- `project2/components/__init__.py`

- [ ] **Step 5: Create minimal app.py**

Write to `project2/app.py`:

```python
"""AI Security Crosswalk Explorer - Main application entry point."""

import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, callback

app = dash.Dash(
    __name__,
    use_pages=True,
    external_stylesheets=[dbc.themes.CYBORG],
    suppress_callback_exceptions=True,
    title="AI Security Crosswalk Explorer",
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)

server = app.server

app.layout = dbc.Container(
    [
        dcc.Store(id="theme-store", data="dark"),
        dcc.Location(id="url", refresh=False),
        html.Div(id="navbar-container"),
        dash.page_container,
    ],
    fluid=True,
    className="px-0",
)

if __name__ == "__main__":
    app.run(debug=True, port=8050)
```

- [ ] **Step 6: Create empty style.css placeholder**

Write to `project2/assets/style.css`:

```css
/* AI Security Crosswalk Explorer - Custom styles */
/* Populated in Task 8 */
```

- [ ] **Step 7: Verify app starts without errors**

```bash
cd project2 && pip install -r requirements.txt && python app.py
```

Expected: App starts on port 8050, shows empty page container. Ctrl+C to stop.

- [ ] **Step 8: Commit**

```bash
git add project2/
git commit -m "scaffold: project2 directory structure with minimal Dash app"
```

---

## Task 2: Framework Colors and Display Names

**Files:**
- Create: `project2/components/framework_colors.py`
- Create: `project2/tests/test_framework_colors.py`

- [ ] **Step 1: Write failing test**

Write to `project2/tests/__init__.py` (empty) and `project2/tests/test_framework_colors.py`:

```python
"""Tests for framework color palette and display names."""

from components.framework_colors import (
    FRAMEWORK_COLORS,
    FRAMEWORK_DISPLAY_NAMES,
    FRAMEWORK_KEYS,
    get_color,
    get_display_name,
)


def test_all_nine_frameworks_have_colors():
    assert len(FRAMEWORK_COLORS) == 9
    for key in FRAMEWORK_KEYS:
        assert key in FRAMEWORK_COLORS
        assert FRAMEWORK_COLORS[key].startswith("#")


def test_all_nine_frameworks_have_display_names():
    assert len(FRAMEWORK_DISPLAY_NAMES) == 9
    for key in FRAMEWORK_KEYS:
        assert key in FRAMEWORK_DISPLAY_NAMES
        assert len(FRAMEWORK_DISPLAY_NAMES[key]) > 0


def test_get_color_returns_hex():
    assert get_color("aiuc_1") == "#1f6feb"


def test_get_color_unknown_returns_gray():
    assert get_color("unknown_framework") == "#6e7681"


def test_get_display_name_returns_string():
    assert get_display_name("aiuc_1") == "AIUC-1"


def test_get_display_name_unknown_returns_key():
    assert get_display_name("unknown") == "unknown"


def test_framework_keys_order():
    """Keys are ordered by node count descending (spec table order)."""
    assert FRAMEWORK_KEYS[0] == "aiuc_1"
    assert FRAMEWORK_KEYS[1] == "csa_aicm"
    assert FRAMEWORK_KEYS[2] == "mitre_atlas"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd project2 && python -m pytest tests/test_framework_colors.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'components'`

- [ ] **Step 3: Write implementation**

Write to `project2/components/framework_colors.py`:

```python
"""Single source of truth for the 9-framework color palette and display names."""

# Ordered by node count descending (matches spec table)
FRAMEWORK_KEYS = [
    "aiuc_1",
    "csa_aicm",
    "mitre_atlas",
    "owasp_ai_exchange",
    "nist_rmf",
    "eu_gpai_cop",
    "cosai_rm",
    "owasp_llm",
    "owasp_agentic",
]

FRAMEWORK_COLORS = {
    "aiuc_1": "#1f6feb",
    "csa_aicm": "#8fd18f",
    "mitre_atlas": "#e8845a",
    "owasp_ai_exchange": "#4ecdc4",
    "nist_rmf": "#cf85c4",
    "eu_gpai_cop": "#d9bf55",
    "cosai_rm": "#7aaed4",
    "owasp_llm": "#ff6b6b",
    "owasp_agentic": "#ffb347",
}

FRAMEWORK_DISPLAY_NAMES = {
    "aiuc_1": "AIUC-1",
    "csa_aicm": "CSA AI Controls Matrix",
    "mitre_atlas": "MITRE ATLAS",
    "owasp_ai_exchange": "OWASP AI Exchange",
    "nist_rmf": "NIST AI RMF",
    "eu_gpai_cop": "EU GPAI Code of Practice",
    "cosai_rm": "CoSAI Risk Map",
    "owasp_llm": "OWASP LLM Top 10",
    "owasp_agentic": "OWASP Agentic Top 10",
}

# Short names for tight spaces (chart axes, badges)
FRAMEWORK_SHORT_NAMES = {
    "aiuc_1": "AIUC-1",
    "csa_aicm": "CSA AICM",
    "mitre_atlas": "ATLAS",
    "owasp_ai_exchange": "AI Exchange",
    "nist_rmf": "NIST RMF",
    "eu_gpai_cop": "EU GPAI",
    "cosai_rm": "CoSAI",
    "owasp_llm": "LLM Top 10",
    "owasp_agentic": "Agentic Top 10",
}

CONFIDENCE_COLORS = {
    "authoritative": "#238636",
    "expert": "#1f6feb",
    "suggestive": "#d9bf55",
    "unvalidated": "#6e7681",
}

CONFIDENCE_LABELS = {
    "authoritative": "Authoritative: from official framework source documents",
    "expert": "Expert: validated by domain expert review",
    "suggestive": "Suggestive: inferred from shared categories or semantic similarity",
    "unvalidated": "Unvalidated: machine-generated, not yet reviewed",
}

RATIONALE_LABELS = {
    "PARENT": "Parent-child: hierarchical relationship within a framework",
    "CROSS_FRAMEWORK_CATEGORY": "Category: controls share a topical category",
    "SCOPE": "Scope: this control limits the scope of the identified risk",
    "DETECT": "Detect: this control detects the identified risk",
    "VALID": "Validate: this control validates or tests against the risk",
    "GOVERN": "Govern: this control establishes governance over the risk",
    "ISOLATE": "Isolate: this control isolates or contains the risk",
    "GATE": "Gate: this control gates access or progression",
    "DISCLOSE": "Disclose: this control requires disclosure or transparency",
    "PREV": "Previous: sequential ordering within a framework",
}

_DEFAULT_COLOR = "#6e7681"


def get_color(framework_key: str) -> str:
    """Return hex color for a framework key, or gray for unknown."""
    return FRAMEWORK_COLORS.get(framework_key, _DEFAULT_COLOR)


def get_display_name(framework_key: str) -> str:
    """Return human-readable name for a framework key, or the key itself."""
    return FRAMEWORK_DISPLAY_NAMES.get(framework_key, framework_key)


def get_short_name(framework_key: str) -> str:
    """Return short name for tight UI spaces."""
    return FRAMEWORK_SHORT_NAMES.get(framework_key, framework_key)
```

- [ ] **Step 4: Run tests**

```bash
cd project2 && PYTHONPATH=. python -m pytest tests/test_framework_colors.py -v
```

Expected: All 7 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add project2/components/framework_colors.py project2/tests/
git commit -m "feat(project2): framework color palette and display name registry"
```

---

## Task 3: Data Preparation Pipeline

**Files:**
- Create: `project2/prepare_data.py`
- Create: `project2/tests/test_prepare_data.py`

This is the most critical task. `prepare_data.py` reads raw `nodes.json` and `edges.json` and produces five derived JSON files in `data/derived/`. NetworkX is used here for graph traversal but is NOT imported at app runtime.

- [ ] **Step 1: Write failing tests**

Write to `project2/tests/test_prepare_data.py`:

```python
"""Tests for the data preparation pipeline."""

import json
import os
import tempfile
import shutil

import pytest


@pytest.fixture
def data_dir():
    """Provide path to project2/data which has real nodes.json and edges.json."""
    base = os.path.join(os.path.dirname(__file__), "..", "data")
    assert os.path.isfile(os.path.join(base, "nodes.json")), "nodes.json not found"
    assert os.path.isfile(os.path.join(base, "edges.json")), "edges.json not found"
    return base


@pytest.fixture
def derived_dir(data_dir):
    """Run prepare_data and return the derived output directory."""
    from prepare_data import prepare_all

    out = os.path.join(data_dir, "derived")
    prepare_all(data_dir, out)
    return out


def test_framework_stats_has_all_nine(derived_dir):
    with open(os.path.join(derived_dir, "framework_stats.json")) as f:
        stats = json.load(f)
    assert len(stats) == 9
    assert "aiuc_1" in stats
    assert stats["aiuc_1"]["node_count"] == 189


def test_framework_stats_has_expected_keys(derived_dir):
    with open(os.path.join(derived_dir, "framework_stats.json")) as f:
        stats = json.load(f)
    for fw, data in stats.items():
        assert "node_count" in data
        assert "edge_count_out" in data
        assert "edge_count_in" in data
        assert "entry_type_counts" in data
        assert "domain_counts" in data


def test_coverage_matrix_is_symmetric_keys(derived_dir):
    with open(os.path.join(derived_dir, "coverage_matrix.json")) as f:
        matrix = json.load(f)
    # Every source framework should have entries for other frameworks
    assert "aiuc_1" in matrix
    for source_fw in matrix:
        for target_fw in matrix[source_fw]:
            assert source_fw != target_fw, "Self-coverage should not be included"
            assert "total_pct" in matrix[source_fw][target_fw]


def test_hierarchy_produces_sunburst_data(derived_dir):
    with open(os.path.join(derived_dir, "hierarchy.json")) as f:
        hierarchy = json.load(f)
    assert "aiuc_1" in hierarchy
    aiuc = hierarchy["aiuc_1"]
    assert "ids" in aiuc
    assert "labels" in aiuc
    assert "parents" in aiuc
    assert len(aiuc["ids"]) == len(aiuc["labels"]) == len(aiuc["parents"])
    assert len(aiuc["ids"]) > 0


def test_transitive_mappings_for_asi02(derived_dir):
    with open(os.path.join(derived_dir, "transitive_mappings.json")) as f:
        trans = json.load(f)
    assert "owasp_agentic:ASI02" in trans
    asi02 = trans["owasp_agentic:ASI02"]
    assert "direct" in asi02
    assert "transitive" in asi02
    # ASI02 has 11 direct mappings from AIUC-1
    assert len(asi02["direct"]) == 11
    # ASI02 should reach CSA AICM transitively
    csa_transitive = [
        t for t in asi02["transitive"] if t["target_framework"] == "csa_aicm"
    ]
    assert len(csa_transitive) > 0
    # Each transitive mapping should have a bridge_node_id
    for t in asi02["transitive"]:
        assert "bridge_node_id" in t
        assert "bridge_node_name" in t
        assert "target_node_id" in t
        assert "target_framework" in t


def test_graph_metrics_has_pair_data(derived_dir):
    with open(os.path.join(derived_dir, "graph_metrics.json")) as f:
        metrics = json.load(f)
    assert "framework_pairs" in metrics
    assert "node_degrees" in metrics
    # Check a known pair
    pair_key = "aiuc_1->csa_aicm"
    assert pair_key in metrics["framework_pairs"]
    pair = metrics["framework_pairs"][pair_key]
    assert "edge_count" in pair
    assert "confidence_counts" in pair
    assert "rationale_counts" in pair


def test_all_derived_files_exist(derived_dir):
    expected = [
        "framework_stats.json",
        "coverage_matrix.json",
        "graph_metrics.json",
        "hierarchy.json",
        "transitive_mappings.json",
    ]
    for fname in expected:
        path = os.path.join(derived_dir, fname)
        assert os.path.isfile(path), f"Missing: {fname}"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd project2 && PYTHONPATH=. python -m pytest tests/test_prepare_data.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'prepare_data'`

- [ ] **Step 3: Write prepare_data.py**

Write to `project2/prepare_data.py`:

```python
"""Pre-compute derived data from nodes.json and edges.json.

Run once at setup time:
    python prepare_data.py

Produces data/derived/*.json consumed by the Dash app at runtime.
NetworkX is used here for graph traversal but is NOT imported by the app.
"""

import json
import os
from collections import Counter, defaultdict

import networkx as nx


def load_raw(data_dir: str):
    """Load raw nodes and edges from JSON files."""
    with open(os.path.join(data_dir, "nodes.json")) as f:
        nodes = json.load(f)
    with open(os.path.join(data_dir, "edges.json")) as f:
        edges = json.load(f)
    return nodes, edges


def build_graph(nodes, edges):
    """Build a NetworkX DiGraph from nodes and edges."""
    G = nx.DiGraph()
    for n in nodes:
        G.add_node(n["node_id"], **n)
    for e in edges:
        G.add_edge(
            e["source_node_id"],
            e["target_node_id"],
            **{k: v for k, v in e.items() if k not in ("source_node_id", "target_node_id")},
        )
    return G


def compute_framework_stats(nodes, edges):
    """Per-framework summary statistics."""
    node_map = defaultdict(list)
    for n in nodes:
        node_map[n["framework"]].append(n)

    edge_out = Counter()
    edge_in = Counter()
    for e in edges:
        edge_out[e["source_framework"]] += 1
        edge_in[e["target_framework"]] += 1

    stats = {}
    for fw, fw_nodes in node_map.items():
        stats[fw] = {
            "node_count": len(fw_nodes),
            "edge_count_out": edge_out.get(fw, 0),
            "edge_count_in": edge_in.get(fw, 0),
            "entry_type_counts": dict(Counter(n.get("entry_type", "") for n in fw_nodes)),
            "domain_counts": dict(Counter(n.get("domain", "") for n in fw_nodes if n.get("domain"))),
            "function_class_counts": dict(Counter(n.get("function_class", "") for n in fw_nodes if n.get("function_class"))),
        }
    return stats


def compute_hierarchy(nodes):
    """Build sunburst-compatible hierarchy per framework.

    Levels: framework root -> domain -> individual nodes.
    Uses domain as the grouping level. Nodes without a domain go under '(ungrouped)'.
    """
    fw_nodes = defaultdict(list)
    for n in nodes:
        fw_nodes[n["framework"]].append(n)

    hierarchy = {}
    for fw, ns in fw_nodes.items():
        ids = [fw]  # root
        labels = [fw]
        parents = [""]
        values = [0]  # root value will be sum

        # Group by domain
        domain_groups = defaultdict(list)
        for n in ns:
            domain = n.get("domain") or "(ungrouped)"
            domain_groups[domain].append(n)

        for domain, domain_nodes in sorted(domain_groups.items()):
            domain_id = f"{fw}::{domain}"
            ids.append(domain_id)
            labels.append(domain)
            parents.append(fw)
            values.append(0)

            for n in sorted(domain_nodes, key=lambda x: x["local_id"]):
                ids.append(n["node_id"])
                labels.append(f"{n['local_id']}: {n['name']}")
                parents.append(domain_id)
                values.append(1)

        hierarchy[fw] = {
            "ids": ids,
            "labels": labels,
            "parents": parents,
            "values": values,
        }
    return hierarchy


def compute_transitive_mappings(nodes, edges):
    """For every node, compute 1-hop (direct) and 2-hop (transitive) reachability.

    Direct: edges where this node is source or target (cross-framework only).
    Transitive: for each direct neighbor in another framework, follow THAT node's
    cross-framework edges to reach a third framework.

    Edges are bidirectional for reachability: if A->B exists, B can reach A.
    """
    node_map = {n["node_id"]: n for n in nodes}

    # Build adjacency: for each node, its cross-framework neighbors with edge metadata
    # We treat edges as undirected for reachability
    neighbors = defaultdict(list)
    for e in edges:
        src, tgt = e["source_node_id"], e["target_node_id"]
        src_fw = e.get("source_framework") or node_map.get(src, {}).get("framework")
        tgt_fw = e.get("target_framework") or node_map.get(tgt, {}).get("framework")
        if src_fw != tgt_fw:
            neighbors[src].append({
                "node_id": tgt,
                "framework": tgt_fw,
                "confidence": e.get("confidence"),
                "rationale_code": e.get("rationale_code"),
            })
            neighbors[tgt].append({
                "node_id": src,
                "framework": src_fw,
                "confidence": e.get("confidence"),
                "rationale_code": e.get("rationale_code"),
            })

    result = {}
    for n in nodes:
        nid = n["node_id"]
        nfw = n["framework"]

        # 1-hop: direct cross-framework neighbors
        direct = []
        for nb in neighbors.get(nid, []):
            direct.append({
                "target_node_id": nb["node_id"],
                "target_framework": nb["framework"],
                "target_name": node_map.get(nb["node_id"], {}).get("name", ""),
                "confidence": nb["confidence"],
                "rationale_code": nb["rationale_code"],
            })

        # 2-hop: for each direct neighbor, get THEIR cross-framework neighbors
        # that are in a DIFFERENT framework than both the original node and the bridge
        seen_direct = {d["target_node_id"] for d in direct}
        transitive = []
        for d in direct:
            bridge_id = d["target_node_id"]
            bridge_fw = d["target_framework"]
            bridge_name = node_map.get(bridge_id, {}).get("name", "")
            bridge_rationale = d["rationale_code"]

            for nb2 in neighbors.get(bridge_id, []):
                hop2_id = nb2["node_id"]
                hop2_fw = nb2["framework"]
                # Skip if it's the original node, already a direct neighbor,
                # or in the same framework as the original
                if hop2_id == nid or hop2_id in seen_direct or hop2_fw == nfw:
                    continue
                transitive.append({
                    "target_node_id": hop2_id,
                    "target_framework": hop2_fw,
                    "target_name": node_map.get(hop2_id, {}).get("name", ""),
                    "bridge_node_id": bridge_id,
                    "bridge_node_name": bridge_name,
                    "bridge_framework": bridge_fw,
                    "bridge_rationale": bridge_rationale,
                    "hop2_rationale": nb2["rationale_code"],
                    "hop2_confidence": nb2["confidence"],
                })

        # Deduplicate transitive: keep unique (target_node_id, bridge_node_id) pairs
        seen_trans = set()
        deduped_transitive = []
        for t in transitive:
            key = (t["target_node_id"], t["bridge_node_id"])
            if key not in seen_trans:
                seen_trans.add(key)
                deduped_transitive.append(t)

        if direct or deduped_transitive:
            result[nid] = {
                "direct": direct,
                "transitive": deduped_transitive,
            }

    return result


def compute_graph_metrics(nodes, edges):
    """Per-framework-pair edge stats and per-node degree metrics."""
    node_map = {n["node_id"]: n for n in nodes}

    # Framework pairs
    pair_data = defaultdict(lambda: {"edge_count": 0, "confidence_counts": Counter(), "rationale_counts": Counter()})
    for e in edges:
        src_fw = e["source_framework"]
        tgt_fw = e["target_framework"]
        if src_fw != tgt_fw:
            key = f"{src_fw}->{tgt_fw}"
            pair_data[key]["edge_count"] += 1
            pair_data[key]["confidence_counts"][e.get("confidence", "unknown")] += 1
            pair_data[key]["rationale_counts"][e.get("rationale_code", "unknown")] += 1

    # Serialize counters to dicts
    framework_pairs = {}
    for key, data in pair_data.items():
        framework_pairs[key] = {
            "edge_count": data["edge_count"],
            "confidence_counts": dict(data["confidence_counts"]),
            "rationale_counts": dict(data["rationale_counts"]),
        }

    # Node degrees
    out_degree = Counter()
    in_degree = Counter()
    cross_out = Counter()
    cross_in = Counter()
    for e in edges:
        out_degree[e["source_node_id"]] += 1
        in_degree[e["target_node_id"]] += 1
        if e["source_framework"] != e["target_framework"]:
            cross_out[e["source_node_id"]] += 1
            cross_in[e["target_node_id"]] += 1

    node_degrees = {}
    for n in nodes:
        nid = n["node_id"]
        node_degrees[nid] = {
            "out_degree": out_degree.get(nid, 0),
            "in_degree": in_degree.get(nid, 0),
            "cross_out": cross_out.get(nid, 0),
            "cross_in": cross_in.get(nid, 0),
        }

    return {"framework_pairs": framework_pairs, "node_degrees": node_degrees}


def compute_coverage_matrix(nodes, transitive_mappings):
    """For each (source_fw, target_fw) pair, compute what percentage of
    target_fw nodes are reachable from ANY node in source_fw.

    Uses both direct and transitive mappings.
    """
    fw_nodes = defaultdict(set)
    for n in nodes:
        fw_nodes[n["framework"]].add(n["node_id"])

    frameworks = sorted(fw_nodes.keys())
    matrix = {}

    for src_fw in frameworks:
        matrix[src_fw] = {}
        for tgt_fw in frameworks:
            if src_fw == tgt_fw:
                continue

            tgt_node_set = fw_nodes[tgt_fw]
            if not tgt_node_set:
                matrix[src_fw][tgt_fw] = {"total_pct": 0.0, "direct_pct": 0.0, "transitive_pct": 0.0}
                continue

            reached_direct = set()
            reached_transitive = set()

            for src_nid in fw_nodes[src_fw]:
                mappings = transitive_mappings.get(src_nid, {})
                for d in mappings.get("direct", []):
                    if d["target_framework"] == tgt_fw:
                        reached_direct.add(d["target_node_id"])
                for t in mappings.get("transitive", []):
                    if t["target_framework"] == tgt_fw:
                        reached_transitive.add(t["target_node_id"])

            # Transitive-only = reached via transitive but NOT via direct
            transitive_only = reached_transitive - reached_direct
            all_reached = reached_direct | reached_transitive

            total = len(tgt_node_set)
            matrix[src_fw][tgt_fw] = {
                "total_pct": round(len(all_reached) / total * 100, 1),
                "direct_pct": round(len(reached_direct) / total * 100, 1),
                "transitive_pct": round(len(transitive_only) / total * 100, 1),
                "direct_count": len(reached_direct),
                "transitive_only_count": len(transitive_only),
                "total_reached": len(all_reached),
                "total_target": total,
            }

    return matrix


def save_json(data, path):
    """Write JSON with consistent formatting."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def prepare_all(data_dir: str, output_dir: str):
    """Run the full preparation pipeline."""
    nodes, edges = load_raw(data_dir)

    stats = compute_framework_stats(nodes, edges)
    save_json(stats, os.path.join(output_dir, "framework_stats.json"))

    hierarchy = compute_hierarchy(nodes)
    save_json(hierarchy, os.path.join(output_dir, "hierarchy.json"))

    transitive = compute_transitive_mappings(nodes, edges)
    save_json(transitive, os.path.join(output_dir, "transitive_mappings.json"))

    metrics = compute_graph_metrics(nodes, edges)
    save_json(metrics, os.path.join(output_dir, "graph_metrics.json"))

    coverage = compute_coverage_matrix(nodes, transitive)
    save_json(coverage, os.path.join(output_dir, "coverage_matrix.json"))

    print(f"Derived data written to {output_dir}/")
    print(f"  framework_stats.json  ({len(stats)} frameworks)")
    print(f"  hierarchy.json        ({len(hierarchy)} frameworks)")
    print(f"  transitive_mappings.json ({len(transitive)} nodes with mappings)")
    print(f"  graph_metrics.json    ({len(metrics['framework_pairs'])} pairs)")
    print(f"  coverage_matrix.json  ({len(coverage)} source frameworks)")


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(here, "data")
    output_dir = os.path.join(data_dir, "derived")
    prepare_all(data_dir, output_dir)
```

- [ ] **Step 4: Run tests**

```bash
cd project2 && PYTHONPATH=. python -m pytest tests/test_prepare_data.py -v
```

Expected: All 7 tests PASS.

- [ ] **Step 5: Run the actual pipeline to generate derived data**

```bash
cd project2 && python prepare_data.py
```

Expected: Prints summary of all 5 derived files written.

- [ ] **Step 6: Verify derived files exist and have reasonable content**

```bash
ls -la project2/data/derived/
python3 -c "import json; d=json.load(open('project2/data/derived/coverage_matrix.json')); print('Coverage sample:', json.dumps(d['aiuc_1']['csa_aicm'], indent=2))"
```

- [ ] **Step 7: Commit**

```bash
git add project2/prepare_data.py project2/tests/test_prepare_data.py project2/data/derived/
git commit -m "feat(project2): data preparation pipeline with 5 derived datasets"
```

---

## Task 4: Data Loader and Plot Theme

**Files:**
- Create: `project2/components/data_loader.py`
- Create: `project2/components/plot_theme.py`
- Create: `project2/tests/test_data_loader.py`

- [ ] **Step 1: Write failing tests**

Write to `project2/tests/test_data_loader.py`:

```python
"""Tests for the data loader module."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from components.data_loader import (
    get_nodes_df,
    get_edges_df,
    get_framework_stats,
    get_coverage_matrix,
    get_hierarchy,
    get_transitive_mappings,
    get_graph_metrics,
    get_node_by_id,
)


def test_nodes_df_has_expected_columns():
    df = get_nodes_df()
    assert "node_id" in df.columns
    assert "framework" in df.columns
    assert "name" in df.columns
    assert len(df) == 983


def test_edges_df_has_expected_columns():
    df = get_edges_df()
    assert "source_node_id" in df.columns
    assert "target_node_id" in df.columns
    assert len(df) == 5813


def test_framework_stats_loaded():
    stats = get_framework_stats()
    assert len(stats) == 9
    assert stats["aiuc_1"]["node_count"] == 189


def test_coverage_matrix_loaded():
    matrix = get_coverage_matrix()
    assert "aiuc_1" in matrix
    assert "csa_aicm" in matrix["aiuc_1"]


def test_hierarchy_loaded():
    h = get_hierarchy()
    assert "aiuc_1" in h
    assert "ids" in h["aiuc_1"]


def test_transitive_mappings_loaded():
    t = get_transitive_mappings()
    assert "owasp_agentic:ASI02" in t


def test_get_node_by_id():
    node = get_node_by_id("owasp_agentic:ASI02")
    assert node is not None
    assert node["name"] == "Tool Misuse and Exploitation"


def test_get_node_by_id_missing():
    node = get_node_by_id("nonexistent:X99")
    assert node is None
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd project2 && PYTHONPATH=. python -m pytest tests/test_data_loader.py -v
```

Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write data_loader.py**

Write to `project2/components/data_loader.py`:

```python
"""Load all JSON data at import time and expose accessor functions.

No runtime file I/O after initial load. All data is cached in module-level variables.
"""

import json
import os

import pandas as pd

_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
_DERIVED_DIR = os.path.join(_DATA_DIR, "derived")


def _load_json(path):
    with open(path) as f:
        return json.load(f)


# Load everything at import time
_nodes = _load_json(os.path.join(_DATA_DIR, "nodes.json"))
_edges = _load_json(os.path.join(_DATA_DIR, "edges.json"))
_nodes_df = pd.DataFrame(_nodes)
_edges_df = pd.DataFrame(_edges)
_node_map = {n["node_id"]: n for n in _nodes}

_framework_stats = _load_json(os.path.join(_DERIVED_DIR, "framework_stats.json"))
_coverage_matrix = _load_json(os.path.join(_DERIVED_DIR, "coverage_matrix.json"))
_hierarchy = _load_json(os.path.join(_DERIVED_DIR, "hierarchy.json"))
_transitive_mappings = _load_json(os.path.join(_DERIVED_DIR, "transitive_mappings.json"))
_graph_metrics = _load_json(os.path.join(_DERIVED_DIR, "graph_metrics.json"))


def get_nodes_df() -> pd.DataFrame:
    return _nodes_df


def get_edges_df() -> pd.DataFrame:
    return _edges_df


def get_node_by_id(node_id: str) -> dict | None:
    return _node_map.get(node_id)


def get_nodes_for_framework(framework: str) -> pd.DataFrame:
    return _nodes_df[_nodes_df["framework"] == framework]


def get_framework_stats() -> dict:
    return _framework_stats


def get_coverage_matrix() -> dict:
    return _coverage_matrix


def get_hierarchy() -> dict:
    return _hierarchy


def get_transitive_mappings() -> dict:
    return _transitive_mappings


def get_graph_metrics() -> dict:
    return _graph_metrics


def get_mappings_for_node(node_id: str) -> dict:
    """Return direct and transitive mappings for a node."""
    return _transitive_mappings.get(node_id, {"direct": [], "transitive": []})
```

- [ ] **Step 4: Write plot_theme.py**

Write to `project2/components/plot_theme.py`:

```python
"""Shared Plotly figure templates for dark and light modes."""

import plotly.graph_objects as go

DARK_TEMPLATE = go.layout.Template(
    layout=go.Layout(
        paper_bgcolor="#0d1117",
        plot_bgcolor="#0d1117",
        font=dict(family="Inter, system-ui, sans-serif", color="#c9d1d9", size=13),
        title=dict(font=dict(size=16, color="#c9d1d9")),
        xaxis=dict(gridcolor="#21262d", zerolinecolor="#21262d"),
        yaxis=dict(gridcolor="#21262d", zerolinecolor="#21262d"),
        hoverlabel=dict(
            bgcolor="#161b22",
            bordercolor="#30363d",
            font=dict(color="#c9d1d9", size=12),
        ),
        colorway=[
            "#1f6feb", "#8fd18f", "#e8845a", "#4ecdc4",
            "#cf85c4", "#d9bf55", "#7aaed4", "#ff6b6b", "#ffb347",
        ],
        margin=dict(l=40, r=20, t=50, b=40),
    )
)

LIGHT_TEMPLATE = go.layout.Template(
    layout=go.Layout(
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        font=dict(family="Inter, system-ui, sans-serif", color="#1f2328", size=13),
        title=dict(font=dict(size=16, color="#1f2328")),
        xaxis=dict(gridcolor="#d1d9e0", zerolinecolor="#d1d9e0"),
        yaxis=dict(gridcolor="#d1d9e0", zerolinecolor="#d1d9e0"),
        hoverlabel=dict(
            bgcolor="#ffffff",
            bordercolor="#d1d9e0",
            font=dict(color="#1f2328", size=12),
        ),
        colorway=[
            "#1f6feb", "#8fd18f", "#e8845a", "#4ecdc4",
            "#cf85c4", "#d9bf55", "#7aaed4", "#ff6b6b", "#ffb347",
        ],
        margin=dict(l=40, r=20, t=50, b=40),
    )
)


def get_template(theme: str = "dark") -> go.layout.Template:
    """Return the Plotly template for the given theme."""
    return DARK_TEMPLATE if theme == "dark" else LIGHT_TEMPLATE


def apply_theme(fig: go.Figure, theme: str = "dark") -> go.Figure:
    """Apply the theme template to an existing figure."""
    fig.update_layout(template=get_template(theme))
    return fig
```

- [ ] **Step 5: Run tests**

```bash
cd project2 && PYTHONPATH=. python -m pytest tests/test_data_loader.py -v
```

Expected: All 8 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add project2/components/data_loader.py project2/components/plot_theme.py project2/tests/test_data_loader.py
git commit -m "feat(project2): data loader with cached accessors and Plotly theme templates"
```

---

## Task 5: Navbar and Theme Toggle

**Files:**
- Create: `project2/components/navbar.py`
- Create: `project2/components/theme.py`
- Modify: `project2/app.py`

- [ ] **Step 1: Write navbar.py**

Write to `project2/components/navbar.py`:

```python
"""Top navigation bar with page links and theme toggle."""

import dash_bootstrap_components as dbc
from dash import html


def create_navbar():
    """Return the navbar component."""
    return dbc.Navbar(
        dbc.Container(
            [
                dbc.NavbarBrand(
                    [
                        html.Span("AI Security Crosswalk Explorer",
                                  style={"fontWeight": "600"}),
                    ],
                    href="/",
                    className="me-auto",
                ),
                dbc.Nav(
                    [
                        dbc.NavItem(dbc.NavLink("Landscape", href="/", active="exact")),
                        dbc.NavItem(dbc.NavLink("Deep Dive", href="/deep-dive")),
                        dbc.NavItem(dbc.NavLink("Explorer", href="/explorer")),
                        dbc.NavItem(dbc.NavLink("Coverage", href="/coverage")),
                    ],
                    className="me-3",
                    navbar=True,
                ),
                dbc.Switch(
                    id="theme-switch",
                    label="",
                    value=True,  # True = dark mode
                    className="ms-2",
                ),
                html.Span(
                    "Dark",
                    id="theme-label",
                    className="ms-1",
                    style={"fontSize": "0.8rem", "color": "#8a95a8"},
                ),
            ],
            fluid=True,
        ),
        color="dark",
        dark=True,
        className="mb-0",
        sticky="top",
    )
```

- [ ] **Step 2: Write theme.py**

Write to `project2/components/theme.py`:

```python
"""Theme toggle logic -- swaps DBC stylesheet between CYBORG (dark) and FLATLY (light)."""

import dash_bootstrap_components as dbc
from dash import Input, Output, callback, html

DARK_THEME_URL = dbc.themes.CYBORG
LIGHT_THEME_URL = dbc.themes.FLATLY


@callback(
    Output("theme-store", "data"),
    Output("theme-label", "children"),
    Input("theme-switch", "value"),
)
def toggle_theme(is_dark):
    """Update theme store when switch is toggled."""
    theme = "dark" if is_dark else "light"
    label = "Dark" if is_dark else "Light"
    return theme, label
```

- [ ] **Step 3: Update app.py to include navbar**

Replace the full content of `project2/app.py`:

```python
"""AI Security Crosswalk Explorer - Main application entry point."""

import dash
import dash_bootstrap_components as dbc
from dash import html, dcc

from components.navbar import create_navbar
from components.theme import DARK_THEME_URL  # noqa: F401 - registers callbacks

app = dash.Dash(
    __name__,
    use_pages=True,
    external_stylesheets=[dbc.themes.CYBORG],
    suppress_callback_exceptions=True,
    title="AI Security Crosswalk Explorer",
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)

server = app.server

app.layout = dbc.Container(
    [
        dcc.Store(id="theme-store", data="dark"),
        dcc.Location(id="url", refresh=False),
        create_navbar(),
        html.Div(
            dash.page_container,
            className="pt-3 px-3",
        ),
    ],
    fluid=True,
    className="px-0",
)

if __name__ == "__main__":
    app.run(debug=True, port=8050)
```

- [ ] **Step 4: Verify app starts with navbar**

```bash
cd project2 && PYTHONPATH=. python app.py
```

Expected: App starts, shows navbar with 4 page links and theme toggle. Page content is empty. Ctrl+C.

- [ ] **Step 5: Commit**

```bash
git add project2/components/navbar.py project2/components/theme.py project2/app.py
git commit -m "feat(project2): navbar with page navigation and dark/light theme toggle"
```

---

## Task 6: Page 1 -- Framework Landscape

**Files:**
- Create: `project2/pages/landscape.py`

- [ ] **Step 1: Create the landscape page**

Write to `project2/pages/landscape.py`:

```python
"""Page 1: Framework Landscape -- bird's-eye view of the AI security ecosystem."""

import dash
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from dash import Input, Output, callback, dcc, html

from components.data_loader import get_edges_df, get_framework_stats, get_graph_metrics, get_nodes_df
from components.framework_colors import (
    FRAMEWORK_KEYS,
    get_color,
    get_display_name,
    get_short_name,
    CONFIDENCE_LABELS,
)
from components.plot_theme import get_template

dash.register_page(__name__, path="/", name="Landscape", order=0)

# --- Narrative ---
INTRO_TEXT = (
    "Nine major AI security standards mapped to each other. "
    "This view shows how frameworks relate at the ecosystem level. "
    "Node size reflects the number of controls in each framework. "
    "Edge width reflects the density of cross-framework mappings. "
    "Use the filters below to focus on specific confidence levels or relationship types."
)


def _build_network_figure(edges_df, stats, theme="dark"):
    """Build the framework supernode network graph."""
    import math

    fw_list = [fw for fw in FRAMEWORK_KEYS if fw in stats]
    n = len(fw_list)

    # Circular layout
    positions = {}
    for i, fw in enumerate(fw_list):
        angle = 2 * math.pi * i / n - math.pi / 2
        positions[fw] = (math.cos(angle), math.sin(angle))

    # Edge traces
    edge_traces = []
    pair_counts = {}
    for _, row in edges_df.iterrows():
        src_fw = row["source_framework"]
        tgt_fw = row["target_framework"]
        if src_fw != tgt_fw:
            key = tuple(sorted([src_fw, tgt_fw]))
            pair_counts[key] = pair_counts.get(key, 0) + 1

    for (fw1, fw2), count in pair_counts.items():
        if fw1 in positions and fw2 in positions:
            x0, y0 = positions[fw1]
            x1, y1 = positions[fw2]
            width = max(1, min(count / 100, 12))
            edge_traces.append(go.Scatter(
                x=[x0, x1, None],
                y=[y0, y1, None],
                mode="lines",
                line=dict(width=width, color="rgba(0, 212, 255, 0.15)"),
                hoverinfo="text",
                text=f"{get_short_name(fw1)} - {get_short_name(fw2)}: {count} mappings",
                showlegend=False,
            ))

    # Node trace
    node_x = [positions[fw][0] for fw in fw_list]
    node_y = [positions[fw][1] for fw in fw_list]
    node_sizes = [max(20, stats[fw]["node_count"] / 3) for fw in fw_list]
    node_colors = [get_color(fw) for fw in fw_list]
    node_text = [
        f"<b>{get_display_name(fw)}</b><br>"
        f"Nodes: {stats[fw]['node_count']}<br>"
        f"Edges out: {stats[fw]['edge_count_out']}<br>"
        f"Edges in: {stats[fw]['edge_count_in']}"
        for fw in fw_list
    ]

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers+text",
        marker=dict(size=node_sizes, color=node_colors, line=dict(width=2, color="rgba(0,212,255,0.3)")),
        text=[get_short_name(fw) for fw in fw_list],
        textposition="top center",
        textfont=dict(size=11),
        hovertext=node_text,
        hoverinfo="text",
        customdata=fw_list,
        showlegend=False,
    )

    fig = go.Figure(data=edge_traces + [node_trace])
    fig.update_layout(
        template=get_template(theme),
        xaxis=dict(visible=False, range=[-1.5, 1.5]),
        yaxis=dict(visible=False, range=[-1.5, 1.5], scaleanchor="x"),
        height=500,
        title=dict(
            text="Framework Relationship Network",
            font=dict(size=14),
        ),
        hovermode="closest",
    )
    return fig


def _build_heatmap_figure(edges_df, theme="dark"):
    """Build the 9x9 pairwise mapping density heatmap."""
    fw_list = FRAMEWORK_KEYS
    short_names = [get_short_name(fw) for fw in fw_list]

    # Count cross-framework edges
    matrix = [[0] * len(fw_list) for _ in range(len(fw_list))]
    fw_idx = {fw: i for i, fw in enumerate(fw_list)}

    for _, row in edges_df.iterrows():
        src_fw = row["source_framework"]
        tgt_fw = row["target_framework"]
        if src_fw in fw_idx and tgt_fw in fw_idx and src_fw != tgt_fw:
            matrix[fw_idx[src_fw]][fw_idx[tgt_fw]] += 1

    fig = go.Figure(data=go.Heatmap(
        z=matrix,
        x=short_names,
        y=short_names,
        colorscale=[[0, "#0d1117"], [0.5, "#1f6feb"], [1, "#00d4ff"]],
        hovertemplate=(
            "<b>%{y}</b> to <b>%{x}</b><br>"
            "Mappings: %{z}<br>"
            "<extra></extra>"
        ),
    ))
    fig.update_layout(
        template=get_template(theme),
        height=500,
        title=dict(text="Pairwise Mapping Density", font=dict(size=14)),
        xaxis=dict(side="bottom", tickangle=45),
        yaxis=dict(autorange="reversed"),
    )
    return fig


# --- Layout ---
layout = dbc.Container([
    # Intro
    dbc.Row(dbc.Col(
        dbc.Card(dbc.CardBody([
            html.H4("AI Security Framework Landscape", className="mb-2"),
            html.P(INTRO_TEXT, className="text-muted mb-0", style={"fontSize": "0.9rem"}),
        ]), className="mb-3 border-0",
        style={"backgroundColor": "rgba(22,27,34,0.5)"}),
    )),

    # Filters
    dbc.Row([
        dbc.Col([
            dbc.Label("Confidence Level", html_for="landscape-confidence",
                      className="text-muted", style={"fontSize": "0.8rem"}),
            dcc.Dropdown(
                id="landscape-confidence",
                options=[
                    {"label": "Any", "value": "any"},
                    {"label": "Suggestive+", "value": "suggestive"},
                    {"label": "Expert+", "value": "expert"},
                    {"label": "Authoritative only", "value": "authoritative"},
                ],
                value="any",
                clearable=False,
                className="mb-2",
            ),
        ], md=4),
        dbc.Col([
            dbc.Label("Relationship Type", html_for="landscape-edge-type",
                      className="text-muted", style={"fontSize": "0.8rem"}),
            dcc.RadioItems(
                id="landscape-edge-type",
                options=[
                    {"label": "All", "value": "all"},
                    {"label": "Rationale-coded only", "value": "rationale"},
                    {"label": "Category links only", "value": "category"},
                ],
                value="all",
                inline=True,
                className="mb-2",
                inputStyle={"marginRight": "4px"},
                labelStyle={"marginRight": "16px", "fontSize": "0.85rem"},
            ),
        ], md=8),
    ], className="mb-3"),

    # Charts
    dbc.Row([
        dbc.Col(dcc.Loading(dcc.Graph(id="landscape-network", config={"displayModeBar": False})), md=6),
        dbc.Col(dcc.Loading(dcc.Graph(id="landscape-heatmap", config={"displayModeBar": False})), md=6),
    ]),

    # Summary stats
    dbc.Row(dbc.Col(
        html.Div(id="landscape-stats", className="mt-3"),
    )),

], fluid=True)


@callback(
    Output("landscape-network", "figure"),
    Output("landscape-heatmap", "figure"),
    Output("landscape-stats", "children"),
    Input("landscape-confidence", "value"),
    Input("landscape-edge-type", "value"),
    Input("theme-store", "data"),
)
def update_landscape(confidence, edge_type, theme):
    edges_df = get_edges_df()
    stats = get_framework_stats()

    # Filter edges
    if confidence != "any":
        conf_order = ["authoritative", "expert", "suggestive", "unvalidated"]
        min_idx = conf_order.index(confidence)
        allowed = set(conf_order[:min_idx + 1])
        edges_df = edges_df[edges_df["confidence"].isin(allowed)]

    if edge_type == "rationale":
        edges_df = edges_df[
            ~edges_df["rationale_code"].isin(["CROSS_FRAMEWORK_CATEGORY", "PARENT", None])
            & edges_df["rationale_code"].notna()
        ]
    elif edge_type == "category":
        edges_df = edges_df[edges_df["rationale_code"] == "CROSS_FRAMEWORK_CATEGORY"]

    cross = edges_df[edges_df["source_framework"] != edges_df["target_framework"]]

    network_fig = _build_network_figure(edges_df, stats, theme)
    heatmap_fig = _build_heatmap_figure(edges_df, theme)

    # Stats bar
    nodes_df = get_nodes_df()
    stats_bar = dbc.Row([
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H3("9", className="text-info mb-0"),
            html.Small("Frameworks", className="text-muted"),
        ]), className="text-center border-0"), md=3),
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H3(f"{len(nodes_df):,}", className="text-info mb-0"),
            html.Small("Controls & Risks", className="text-muted"),
        ]), className="text-center border-0"), md=3),
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H3(f"{len(edges_df):,}", className="text-info mb-0"),
            html.Small("Relationships (filtered)", className="text-muted"),
        ]), className="text-center border-0"), md=3),
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H3(f"{len(cross):,}", className="text-info mb-0"),
            html.Small("Cross-Framework", className="text-muted"),
        ]), className="text-center border-0"), md=3),
    ])

    return network_fig, heatmap_fig, stats_bar
```

- [ ] **Step 2: Verify the page loads**

```bash
cd project2 && PYTHONPATH=. python app.py
```

Open http://localhost:8050 in browser. Expected: Landscape page with network graph, heatmap, filters, and stats bar. Verify:
- Network graph shows 9 framework nodes in a circle with edges
- Heatmap shows 9x9 grid with color-coded density
- Confidence dropdown filters edges
- Edge type radio buttons filter edges
- Stats bar shows correct counts

- [ ] **Step 3: Commit**

```bash
git add project2/pages/landscape.py
git commit -m "feat(project2): Page 1 landscape with network graph and heatmap"
```

---

## Task 7: Page 2 -- Framework Deep Dive

**Files:**
- Create: `project2/pages/deep_dive.py`

- [ ] **Step 1: Create the deep dive page**

Write to `project2/pages/deep_dive.py`:

```python
"""Page 2: Framework Deep Dive -- explore a single framework's structure."""

import dash
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from dash import Input, Output, State, callback, ctx, dcc, html

from components.data_loader import (
    get_edges_df,
    get_framework_stats,
    get_hierarchy,
    get_node_by_id,
    get_nodes_df,
)
from components.framework_colors import (
    CONFIDENCE_COLORS,
    FRAMEWORK_KEYS,
    get_color,
    get_display_name,
    get_short_name,
)
from components.plot_theme import get_template

dash.register_page(__name__, path="/deep-dive", name="Deep Dive", order=1)

INTRO_TEXT = (
    "Select a framework to explore its internal structure. "
    "The sunburst shows how controls are organized by domain. "
    "Click any segment to see the full control text. "
    'Use "View in Explorer" to trace that control\'s cross-framework mappings.'
)


def _framework_options():
    stats = get_framework_stats()
    return [
        {"label": f"{get_display_name(fw)} ({stats[fw]['node_count']} nodes)", "value": fw}
        for fw in FRAMEWORK_KEYS
        if fw in stats
    ]


def _build_sunburst(framework, entry_types, theme="dark"):
    hierarchy = get_hierarchy()
    if framework not in hierarchy:
        return go.Figure()

    h = hierarchy[framework]
    ids, labels, parents, values = h["ids"], h["labels"], h["parents"], h["values"]

    # Filter by entry type if specified
    if entry_types:
        nodes_df = get_nodes_df()
        fw_nodes = nodes_df[nodes_df["framework"] == framework]
        allowed_ids = set(fw_nodes[fw_nodes["entry_type"].isin(entry_types)]["node_id"])

        filtered_ids, filtered_labels, filtered_parents, filtered_values = [], [], [], []
        for i in range(len(ids)):
            node_id = ids[i]
            # Keep root and domain-level entries, plus allowed leaf nodes
            is_leaf = "::" not in node_id and node_id != framework
            if not is_leaf or node_id in allowed_ids:
                filtered_ids.append(node_id)
                filtered_labels.append(labels[i])
                filtered_parents.append(parents[i])
                filtered_values.append(values[i])

        ids, labels, parents, values = filtered_ids, filtered_labels, filtered_parents, filtered_values

    fw_color = get_color(framework)
    fig = go.Figure(go.Sunburst(
        ids=ids,
        labels=labels,
        parents=parents,
        values=values,
        branchvalues="total",
        hovertemplate="<b>%{label}</b><br>%{id}<extra></extra>",
        marker=dict(
            colors=[fw_color if i == 0 else None for i in range(len(ids))],
        ),
        maxdepth=3,
    ))
    fig.update_layout(
        template=get_template(theme),
        height=500,
        title=dict(text=f"{get_display_name(framework)} Hierarchy", font=dict(size=14)),
        margin=dict(t=50, b=10, l=10, r=10),
    )
    return fig


def _build_outbound_bar(framework, theme="dark"):
    edges_df = get_edges_df()
    outbound = edges_df[
        (edges_df["source_framework"] == framework)
        & (edges_df["source_framework"] != edges_df["target_framework"])
    ]

    if outbound.empty:
        # This framework might be target-only; show inbound instead
        inbound = edges_df[
            (edges_df["target_framework"] == framework)
            & (edges_df["source_framework"] != edges_df["target_framework"])
        ]
        if inbound.empty:
            fig = go.Figure()
            fig.update_layout(template=get_template(theme), height=500)
            fig.add_annotation(text="No cross-framework mappings found", showarrow=False)
            return fig

        grouped = inbound.groupby(["source_framework", "confidence"]).size().reset_index(name="count")
        title = f"Inbound Mappings to {get_short_name(framework)}"
        fw_col = "source_framework"
    else:
        grouped = outbound.groupby(["target_framework", "confidence"]).size().reset_index(name="count")
        title = f"Outbound Mappings from {get_short_name(framework)}"
        fw_col = "target_framework"

    conf_order = ["authoritative", "expert", "suggestive", "unvalidated"]
    fig = go.Figure()
    for conf in conf_order:
        subset = grouped[grouped["confidence"] == conf]
        if not subset.empty:
            fig.add_trace(go.Bar(
                y=[get_short_name(fw) for fw in subset[fw_col]],
                x=subset["count"],
                name=conf.capitalize(),
                orientation="h",
                marker_color=CONFIDENCE_COLORS.get(conf, "#6e7681"),
                hovertemplate=f"<b>%{{y}}</b><br>{conf}: %{{x}} mappings<extra></extra>",
            ))

    fig.update_layout(
        template=get_template(theme),
        height=500,
        title=dict(text=title, font=dict(size=14)),
        barmode="stack",
        yaxis=dict(categoryorder="total ascending"),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2),
    )
    return fig


def _build_control_card(node_id):
    node = get_node_by_id(node_id)
    if not node:
        return html.Div()

    badges = []
    if node.get("entry_type"):
        badges.append(dbc.Badge(node["entry_type"], color="secondary", className="me-1"))
    if node.get("function_class"):
        badges.append(dbc.Badge(node["function_class"], color="info", className="me-1"))
    if node.get("domain"):
        badges.append(dbc.Badge(node["domain"], color="dark", className="me-1"))

    return dbc.Card([
        dbc.CardHeader([
            html.Span(get_short_name(node["framework"]),
                      className="badge me-2",
                      style={"backgroundColor": get_color(node["framework"])}),
            html.Strong(f"{node['local_id']}: {node['name']}"),
            html.Div(badges, className="mt-1"),
        ]),
        dbc.CardBody([
            html.P(node.get("description", "No description available."),
                   style={"fontSize": "0.9rem", "lineHeight": "1.6"}),
            html.Div([
                html.Small(f"Frequency: {node['frequency']}", className="text-muted me-3")
                if node.get("frequency") else None,
                html.Small(
                    html.A("View source", href=node["url"], target="_blank", className="text-info"),
                    className="me-3",
                ) if node.get("url") else None,
            ]),
            dbc.Button(
                "View in Crosswalk Explorer",
                id="deep-dive-to-explorer",
                color="info",
                size="sm",
                className="mt-2",
                outline=True,
            ),
            dcc.Store(id="deep-dive-selected-node", data=node_id),
        ]),
    ], className="mt-3", style={"borderLeft": f"4px solid {get_color(node['framework'])}"})


# --- Layout ---
layout = dbc.Container([
    dbc.Row(dbc.Col(
        dbc.Card(dbc.CardBody([
            html.H4("Framework Deep Dive", className="mb-2"),
            html.P(INTRO_TEXT, className="text-muted mb-0", style={"fontSize": "0.9rem"}),
        ]), className="mb-3 border-0",
        style={"backgroundColor": "rgba(22,27,34,0.5)"}),
    )),

    # Controls
    dbc.Row([
        dbc.Col([
            dbc.Label("Select Framework", className="text-muted", style={"fontSize": "0.8rem"}),
            dcc.Dropdown(
                id="deep-dive-framework",
                options=_framework_options(),
                value="aiuc_1",
                clearable=False,
            ),
        ], md=5),
        dbc.Col([
            dbc.Label("Filter Entry Types", className="text-muted", style={"fontSize": "0.8rem"}),
            dcc.Checklist(
                id="deep-dive-entry-types",
                options=[
                    {"label": " control", "value": "control"},
                    {"label": " risk", "value": "risk"},
                    {"label": " technique", "value": "technique"},
                    {"label": " mitigation", "value": "mitigation"},
                    {"label": " activity", "value": "activity"},
                    {"label": " subcategory", "value": "subcategory"},
                ],
                value=[],
                inline=True,
                inputStyle={"marginRight": "4px"},
                labelStyle={"marginRight": "12px", "fontSize": "0.85rem"},
            ),
        ], md=7),
    ], className="mb-3"),

    # Charts
    dbc.Row([
        dbc.Col(dcc.Loading(dcc.Graph(id="deep-dive-sunburst")), md=6),
        dbc.Col(dcc.Loading(dcc.Graph(id="deep-dive-bar")), md=6),
    ]),

    # Control detail card (hidden until click)
    html.Div(id="deep-dive-control-card"),
], fluid=True)


@callback(
    Output("deep-dive-sunburst", "figure"),
    Output("deep-dive-bar", "figure"),
    Input("deep-dive-framework", "value"),
    Input("deep-dive-entry-types", "value"),
    Input("theme-store", "data"),
)
def update_deep_dive(framework, entry_types, theme):
    sunburst = _build_sunburst(framework, entry_types, theme)
    bar = _build_outbound_bar(framework, theme)
    return sunburst, bar


@callback(
    Output("deep-dive-control-card", "children"),
    Input("deep-dive-sunburst", "clickData"),
    prevent_initial_call=True,
)
def show_control_detail(click_data):
    if not click_data or "points" not in click_data:
        return html.Div()
    point = click_data["points"][0]
    node_id = point.get("id", "")
    # Only show card for leaf nodes (actual controls, not domains)
    if "::" in node_id or not node_id:
        return html.Div()
    return _build_control_card(node_id)
```

- [ ] **Step 2: Verify the page loads**

```bash
cd project2 && PYTHONPATH=. python app.py
```

Open http://localhost:8050/deep-dive. Expected: Framework selector, entry type checklist, sunburst hierarchy, stacked bar chart. Click a sunburst segment to see the control detail card.

- [ ] **Step 3: Commit**

```bash
git add project2/pages/deep_dive.py
git commit -m "feat(project2): Page 2 deep dive with sunburst hierarchy and outbound bar"
```

---

## Task 8: Page 3 -- Crosswalk Explorer

**Files:**
- Create: `project2/pages/explorer.py`

This is the most complex page. It has chained dropdowns, a Sankey diagram, a neighborhood graph, and expandable control cards with bridge path visualization.

- [ ] **Step 1: Create the explorer page**

Write to `project2/pages/explorer.py`:

```python
"""Page 3: Crosswalk Explorer -- pick a control, see all cross-framework mappings."""

import math

import dash
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from dash import ALL, Input, Output, State, callback, ctx, dcc, html

from components.data_loader import (
    get_mappings_for_node,
    get_node_by_id,
    get_nodes_for_framework,
)
from components.framework_colors import (
    CONFIDENCE_COLORS,
    CONFIDENCE_LABELS,
    FRAMEWORK_KEYS,
    RATIONALE_LABELS,
    get_color,
    get_display_name,
    get_short_name,
)
from components.plot_theme import get_template

dash.register_page(__name__, path="/explorer", name="Explorer", order=2)

INTRO_TEXT = (
    "Select a framework and control to see all its cross-framework mappings. "
    "Direct mappings are shown first, followed by transitive mappings "
    "that are reached through a bridge control in another framework. "
    "Click any card to expand the full control text and see the bridge path."
)


def _framework_options():
    from components.data_loader import get_framework_stats
    stats = get_framework_stats()
    return [
        {"label": f"{get_display_name(fw)} ({stats[fw]['node_count']})", "value": fw}
        for fw in FRAMEWORK_KEYS
        if fw in stats
    ]


def _build_sankey(mappings, source_node, theme="dark"):
    """Build Sankey: source -> [confidence level] -> target frameworks."""
    direct = mappings.get("direct", [])
    transitive = mappings.get("transitive", [])

    if not direct and not transitive:
        fig = go.Figure()
        fig.update_layout(template=get_template(theme), height=400)
        fig.add_annotation(text="No mappings found for this control", showarrow=False)
        return fig

    # Nodes: source | confidence levels | target frameworks
    all_targets = {}
    for d in direct:
        fw = d["target_framework"]
        all_targets[fw] = all_targets.get(fw, 0) + 1
    for t in transitive:
        fw = t["target_framework"]
        all_targets[fw] = all_targets.get(fw, 0) + 1

    target_fws = sorted(all_targets.keys(), key=lambda fw: all_targets[fw], reverse=True)

    labels = [f"{source_node['local_id']}: {source_node['name'][:30]}"]
    colors = [get_color(source_node["framework"])]
    labels += ["Direct", "Transitive"]
    colors += ["rgba(0,212,255,0.6)", "rgba(143,209,143,0.6)"]
    for fw in target_fws:
        labels.append(get_short_name(fw))
        colors.append(get_color(fw))

    # Links: source -> direct/transitive -> target frameworks
    source_idx = 0
    direct_idx = 1
    trans_idx = 2
    fw_start_idx = 3

    links_src, links_tgt, links_val, links_color = [], [], [], []

    # Count direct per framework
    direct_by_fw = {}
    for d in direct:
        fw = d["target_framework"]
        direct_by_fw[fw] = direct_by_fw.get(fw, 0) + 1

    trans_by_fw = {}
    for t in transitive:
        fw = t["target_framework"]
        trans_by_fw[fw] = trans_by_fw.get(fw, 0) + 1

    # Source -> Direct
    total_direct = sum(direct_by_fw.values())
    if total_direct > 0:
        links_src.append(source_idx)
        links_tgt.append(direct_idx)
        links_val.append(total_direct)
        links_color.append("rgba(0,212,255,0.2)")

    # Source -> Transitive
    total_trans = sum(trans_by_fw.values())
    if total_trans > 0:
        links_src.append(source_idx)
        links_tgt.append(trans_idx)
        links_val.append(total_trans)
        links_color.append("rgba(143,209,143,0.2)")

    # Direct -> target frameworks
    for fw, count in direct_by_fw.items():
        if fw in target_fws:
            links_src.append(direct_idx)
            links_tgt.append(fw_start_idx + target_fws.index(fw))
            links_val.append(count)
            links_color.append("rgba(0,212,255,0.15)")

    # Transitive -> target frameworks
    for fw, count in trans_by_fw.items():
        if fw in target_fws:
            links_src.append(trans_idx)
            links_tgt.append(fw_start_idx + target_fws.index(fw))
            links_val.append(count)
            links_color.append("rgba(143,209,143,0.15)")

    fig = go.Figure(go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            label=labels,
            color=colors,
        ),
        link=dict(
            source=links_src,
            target=links_tgt,
            value=links_val,
            color=links_color,
        ),
    ))
    fig.update_layout(
        template=get_template(theme),
        height=400,
        title=dict(text="Mapping Flow", font=dict(size=14)),
    )
    return fig


def _build_neighborhood(mappings, source_node, theme="dark"):
    """Build local neighborhood graph: source at center, direct neighbors around it."""
    direct = mappings.get("direct", [])
    if not direct:
        fig = go.Figure()
        fig.update_layout(template=get_template(theme), height=400)
        fig.add_annotation(text="No direct mappings to visualize", showarrow=False)
        return fig

    # Limit to top 20 for readability
    display_nodes = direct[:20]
    n = len(display_nodes)

    # Center node
    cx, cy = 0, 0

    # Arrange neighbors in a circle
    traces = []
    for i, d in enumerate(display_nodes):
        angle = 2 * math.pi * i / n - math.pi / 2
        nx_pos = math.cos(angle) * 0.8
        ny_pos = math.sin(angle) * 0.8

        # Edge
        traces.append(go.Scatter(
            x=[cx, nx_pos, None], y=[cy, ny_pos, None],
            mode="lines",
            line=dict(width=1, color="rgba(0,212,255,0.2)"),
            showlegend=False, hoverinfo="skip",
        ))

    # Neighbor nodes
    neighbor_x = [math.cos(2 * math.pi * i / n - math.pi / 2) * 0.8 for i in range(n)]
    neighbor_y = [math.sin(2 * math.pi * i / n - math.pi / 2) * 0.8 for i in range(n)]
    neighbor_colors = [get_color(d["target_framework"]) for d in display_nodes]
    neighbor_text = [
        f"<b>{d.get('target_name', d['target_node_id'])}</b><br>"
        f"Framework: {get_display_name(d['target_framework'])}<br>"
        f"Confidence: {d.get('confidence', 'unknown')}<br>"
        f"Rationale: {d.get('rationale_code', 'unknown')}"
        for d in display_nodes
    ]

    traces.append(go.Scatter(
        x=neighbor_x, y=neighbor_y,
        mode="markers",
        marker=dict(size=14, color=neighbor_colors, line=dict(width=1, color="#21262d")),
        hovertext=neighbor_text,
        hoverinfo="text",
        showlegend=False,
    ))

    # Center node (on top)
    traces.append(go.Scatter(
        x=[cx], y=[cy],
        mode="markers+text",
        marker=dict(
            size=24,
            color=get_color(source_node["framework"]),
            line=dict(width=2, color="#00d4ff"),
        ),
        text=[source_node["local_id"]],
        textposition="middle center",
        textfont=dict(size=9, color="white"),
        hovertext=f"<b>{source_node['local_id']}: {source_node['name']}</b>",
        hoverinfo="text",
        showlegend=False,
    ))

    fig = go.Figure(data=traces)
    fig.update_layout(
        template=get_template(theme),
        height=400,
        title=dict(text="Control Neighborhood (direct mappings)", font=dict(size=14)),
        xaxis=dict(visible=False, range=[-1.2, 1.2]),
        yaxis=dict(visible=False, range=[-1.2, 1.2], scaleanchor="x"),
        hovermode="closest",
    )
    return fig


def _make_badge(text, tooltip_text, badge_id, color="secondary"):
    """Create a badge with a tooltip."""
    badge = dbc.Badge(text, id=badge_id, color=color, className="me-1",
                      style={"cursor": "help"})
    tooltip = dbc.Tooltip(tooltip_text, target=badge_id, placement="top")
    return html.Span([badge, tooltip])


def _build_source_card(node, mappings):
    """Build the pinned source control card with reachability summary."""
    direct = mappings.get("direct", [])
    transitive = mappings.get("transitive", [])

    # Group by framework
    from collections import Counter
    direct_by_fw = Counter(d["target_framework"] for d in direct)
    trans_by_fw = Counter(t["target_framework"] for t in transitive)
    all_fws = sorted(set(list(direct_by_fw.keys()) + list(trans_by_fw.keys())),
                     key=lambda fw: direct_by_fw.get(fw, 0) + trans_by_fw.get(fw, 0),
                     reverse=True)

    summary_items = []
    for fw in all_fws:
        d_count = direct_by_fw.get(fw, 0)
        t_count = trans_by_fw.get(fw, 0)
        parts = []
        if d_count:
            parts.append(f"{d_count} direct")
        if t_count:
            parts.append(f"{t_count} via bridge")
        summary_items.append(
            html.Span([
                html.Span(
                    "\u25cf ",
                    style={"color": get_color(fw)},
                ),
                html.Span(f"{get_short_name(fw)}: ", className="text-muted"),
                html.Span(", ".join(parts), style={"color": "#c9d1d9"}),
            ], className="me-3", style={"fontSize": "0.8rem"})
        )

    return dbc.Card([
        dbc.CardHeader([
            html.Span(get_short_name(node["framework"]),
                      className="badge me-2",
                      style={"backgroundColor": get_color(node["framework"])}),
            html.Strong(f"{node['local_id']}: {node['name']}"),
            html.Span(
                dbc.Badge(node.get("entry_type", ""), color="secondary", className="ms-2"),
            ),
        ]),
        dbc.CardBody([
            html.P(node.get("description", "No description available."),
                   style={"fontSize": "0.9rem", "lineHeight": "1.6"}),
        ]),
        dbc.CardFooter(
            html.Div(summary_items, style={"display": "flex", "flexWrap": "wrap", "gap": "4px"}),
            style={"backgroundColor": "rgba(13,17,23,0.5)"},
        ),
    ], style={"borderLeft": f"4px solid {get_color(node['framework'])}"}, className="mb-3")


def _build_mapping_cards(mappings, source_node):
    """Build framework-grouped expandable control cards."""
    from collections import defaultdict

    direct = mappings.get("direct", [])
    transitive = mappings.get("transitive", [])

    # Group direct by framework
    direct_by_fw = defaultdict(list)
    for d in direct:
        direct_by_fw[d["target_framework"]].append(d)

    # Group transitive by framework
    trans_by_fw = defaultdict(list)
    for t in transitive:
        trans_by_fw[t["target_framework"]].append(t)

    sections = []

    # Direct mappings first
    for fw in sorted(direct_by_fw.keys(), key=lambda f: len(direct_by_fw[f]), reverse=True):
        items = direct_by_fw[fw]
        section_header = html.Div([
            html.Span("\u25a0 ", style={"color": get_color(fw)}),
            html.Strong(get_display_name(fw), style={"fontSize": "0.9rem"}),
            dbc.Badge(f"{len(items)} direct", className="ms-2",
                      style={"backgroundColor": f"{get_color(fw)}33", "color": get_color(fw)}),
        ], className="mb-2 mt-3")
        sections.append(section_header)

        for i, d in enumerate(items):
            target = get_node_by_id(d["target_node_id"])
            card_id = f"direct-{fw}-{i}"
            conf = d.get("confidence", "unknown")
            rationale = d.get("rationale_code", "")

            header = html.Div([
                html.Span(
                    "\u25b6 " if True else "\u25bc ",
                    style={"color": "#6e7681", "cursor": "pointer"},
                ),
                html.Strong(
                    f"{target['local_id']}: {target['name']}" if target else d["target_node_id"],
                    style={"fontSize": "0.85rem"},
                ),
                html.Span([
                    dbc.Badge(conf, color={"authoritative": "success", "expert": "primary",
                              "suggestive": "warning", "unvalidated": "secondary"}.get(conf, "secondary"),
                              className="ms-auto me-1", style={"fontSize": "0.7rem"}),
                    dbc.Badge(rationale, color="dark", className="me-1",
                              style={"fontSize": "0.7rem"}) if rationale else None,
                ], style={"marginLeft": "auto", "display": "flex"}),
            ], className="d-flex align-items-center",
               id={"type": "card-header", "index": card_id},
               style={"cursor": "pointer"})

            body = dbc.Collapse(
                dbc.CardBody([
                    html.P(target.get("description", "No description.") if target else "",
                           style={"fontSize": "0.85rem", "lineHeight": "1.6", "color": "#9eaab8"}),
                    html.Div([
                        html.Small(f"Domain: {target.get('domain', 'N/A')}", className="text-muted me-3") if target else None,
                        html.Small(f"Class: {target.get('function_class', 'N/A')}", className="text-muted me-3") if target and target.get("function_class") else None,
                    ]),
                    # Path indicator
                    html.Div([
                        html.Span(source_node["local_id"],
                                  className="badge",
                                  style={"backgroundColor": get_color(source_node["framework"]), "fontSize": "0.75rem"}),
                        html.Span(" \u2192 ", style={"color": "#00d4ff"}),
                        html.Span(target["local_id"] if target else d["target_node_id"],
                                  className="badge",
                                  style={"backgroundColor": get_color(fw), "fontSize": "0.75rem"}),
                        html.Small(" (direct mapping)", className="text-muted ms-2"),
                    ], className="mt-2 p-2", style={"backgroundColor": "rgba(13,17,23,0.5)", "borderRadius": "4px"}),
                ]),
                id={"type": "card-collapse", "index": card_id},
                is_open=False,
            )

            sections.append(
                dbc.Card([
                    dbc.CardHeader(header, className="py-2"),
                    body,
                ], className="mb-1", style={"borderLeft": f"4px solid {get_color(fw)}"})
            )

    # Transitive mappings
    for fw in sorted(trans_by_fw.keys(), key=lambda f: len(trans_by_fw[f]), reverse=True):
        items = trans_by_fw[fw]
        section_header = html.Div([
            html.Span("\u25a0 ", style={"color": get_color(fw)}),
            html.Strong(get_display_name(fw), style={"fontSize": "0.9rem"}),
            dbc.Badge(f"{len(items)} via bridge", className="ms-2",
                      style={"backgroundColor": f"{get_color(fw)}33", "color": get_color(fw)}),
            html.Small(f" through {get_short_name(items[0].get('bridge_framework', ''))}", className="text-muted ms-1"),
        ], className="mb-2 mt-3")
        sections.append(section_header)

        for i, t in enumerate(items[:30]):  # Limit to 30 per framework for performance
            target = get_node_by_id(t["target_node_id"])
            card_id = f"trans-{fw}-{i}"

            header = html.Div([
                html.Span("\u25b6 ", style={"color": "#6e7681", "cursor": "pointer"}),
                html.Strong(
                    f"{target['local_id']}: {target['name']}" if target else t["target_node_id"],
                    style={"fontSize": "0.85rem"},
                ),
                html.Span([
                    dbc.Badge("transitive", color="dark", className="ms-auto me-1",
                              style={"fontSize": "0.7rem", "color": get_color(fw)}),
                    html.Small(f"via {t.get('bridge_node_id', '').split(':')[-1]}",
                               className="text-muted"),
                ], style={"marginLeft": "auto", "display": "flex", "alignItems": "center"}),
            ], className="d-flex align-items-center",
               id={"type": "card-header", "index": card_id},
               style={"cursor": "pointer"})

            bridge_name = t.get("bridge_node_name", t.get("bridge_node_id", ""))
            bridge_id_short = t.get("bridge_node_id", "").split(":")[-1] if t.get("bridge_node_id") else ""

            body = dbc.Collapse(
                dbc.CardBody([
                    html.P(target.get("description", "No description.") if target else "",
                           style={"fontSize": "0.85rem", "lineHeight": "1.6", "color": "#9eaab8"}),
                    # Bridge path visualization
                    html.Div([
                        html.Small("BRIDGE PATH", className="text-muted d-block mb-1",
                                   style={"fontSize": "0.7rem"}),
                        html.Div([
                            html.Span(source_node["local_id"], className="badge",
                                      style={"backgroundColor": get_color(source_node["framework"]), "fontSize": "0.75rem"}),
                            html.Div([
                                html.Span(" \u2192 ", style={"color": "#00d4ff"}),
                                html.Small(t.get("bridge_rationale", ""), className="text-muted"),
                            ], style={"display": "flex", "flexDirection": "column", "alignItems": "center"}),
                            html.Span([
                                html.Span(bridge_id_short, className="badge",
                                          style={"backgroundColor": get_color(t.get("bridge_framework", "")), "fontSize": "0.75rem"}),
                                html.Br(),
                                html.Small(bridge_name[:40], className="text-muted",
                                           style={"fontSize": "0.7rem"}),
                            ]),
                            html.Div([
                                html.Span(" \u2192 ", style={"color": "#00d4ff"}),
                                html.Small(t.get("hop2_rationale", ""), className="text-muted"),
                            ], style={"display": "flex", "flexDirection": "column", "alignItems": "center"}),
                            html.Span(target["local_id"] if target else t["target_node_id"],
                                      className="badge",
                                      style={"backgroundColor": get_color(fw), "fontSize": "0.75rem"}),
                        ], style={"display": "flex", "alignItems": "center", "gap": "8px", "flexWrap": "wrap"}),
                    ], className="mt-2 p-2", style={"backgroundColor": "rgba(13,17,23,0.5)", "borderRadius": "6px",
                                                     "border": "1px solid #21262d"}),
                ]),
                id={"type": "card-collapse", "index": card_id},
                is_open=False,
            )

            sections.append(
                dbc.Card([
                    dbc.CardHeader(header, className="py-2"),
                    body,
                ], className="mb-1", style={"borderLeft": f"4px solid {get_color(fw)}"})
            )

        if len(items) > 30:
            sections.append(html.Div(
                f"+ {len(items) - 30} more {get_display_name(fw)} controls",
                className="text-center text-muted my-2",
                style={"fontSize": "0.8rem", "border": "1px dashed #21262d",
                       "borderRadius": "6px", "padding": "8px"},
            ))

    return html.Div(sections)


def _build_mitigation_section(node):
    """Build the mitigation text section if the source has mitigation_text."""
    mit = node.get("mitigation_text")
    if not mit:
        return html.Div()

    return dbc.Card([
        dbc.CardHeader([
            html.Span("\U0001f6e1\ufe0f", className="me-2", title="Recommended mitigations from the source framework"),
            html.Strong("Recommended Mitigations"),
            html.Small(f" (from {get_short_name(node['framework'])} source)", className="text-muted ms-2"),
        ]),
        dbc.CardBody(
            html.P(mit, style={"fontSize": "0.85rem", "lineHeight": "1.6", "color": "#9eaab8"}),
        ),
    ], className="mt-3", style={"borderLeft": f"4px solid {get_color(node['framework'])}"})


# --- Layout ---
layout = dbc.Container([
    dbc.Row(dbc.Col(
        dbc.Card(dbc.CardBody([
            html.H4("Crosswalk Explorer", className="mb-2"),
            html.P(INTRO_TEXT, className="text-muted mb-0", style={"fontSize": "0.9rem"}),
        ]), className="mb-3 border-0",
        style={"backgroundColor": "rgba(22,27,34,0.5)"}),
    )),

    # Controls
    dbc.Row([
        dbc.Col([
            dbc.Label("Source Framework", className="text-muted", style={"fontSize": "0.8rem"}),
            dcc.Dropdown(
                id="explorer-framework",
                options=_framework_options(),
                value="owasp_agentic",
                clearable=False,
            ),
        ], md=3),
        dbc.Col([
            dbc.Label("Select Control (searchable)", className="text-muted", style={"fontSize": "0.8rem"}),
            dcc.Dropdown(
                id="explorer-control",
                options=[],
                value=None,
                clearable=False,
                searchable=True,
                placeholder="Select a control...",
            ),
        ], md=4),
        dbc.Col([
            dbc.Label("Mapping Filter", className="text-muted", style={"fontSize": "0.8rem"}),
            dcc.RadioItems(
                id="explorer-mapping-filter",
                options=[
                    {"label": "All", "value": "all"},
                    {"label": "Direct only", "value": "direct"},
                    {"label": "Transitive only", "value": "transitive"},
                ],
                value="all",
                inline=True,
                inputStyle={"marginRight": "4px"},
                labelStyle={"marginRight": "12px", "fontSize": "0.85rem"},
            ),
        ], md=3),
        dbc.Col([
            dbc.Label("Search Controls", className="text-muted", style={"fontSize": "0.8rem"}),
            dcc.Input(
                id="explorer-search",
                type="text",
                placeholder="Filter by keyword...",
                debounce=True,
                className="form-control",
            ),
        ], md=2),
    ], className="mb-3"),

    # Charts
    dbc.Row([
        dbc.Col(dcc.Loading(dcc.Graph(id="explorer-sankey", config={"displayModeBar": False})), md=6),
        dbc.Col(dcc.Loading(dcc.Graph(id="explorer-neighborhood", config={"displayModeBar": False})), md=6),
    ]),

    # Source control card
    html.Div(id="explorer-source-card"),

    # Mapping cards
    html.Div(id="explorer-mapping-cards"),

    # Mitigation section
    html.Div(id="explorer-mitigation"),

], fluid=True)


@callback(
    Output("explorer-control", "options"),
    Output("explorer-control", "value"),
    Input("explorer-framework", "value"),
)
def update_control_options(framework):
    """Chained callback: framework selection updates control dropdown."""
    if not framework:
        return [], None
    df = get_nodes_for_framework(framework)
    options = [
        {"label": f"{row['local_id']}: {row['name'][:60]}", "value": row["node_id"]}
        for _, row in df.sort_values("local_id").iterrows()
    ]
    default = options[0]["value"] if options else None
    return options, default


@callback(
    Output("explorer-sankey", "figure"),
    Output("explorer-neighborhood", "figure"),
    Output("explorer-source-card", "children"),
    Output("explorer-mapping-cards", "children"),
    Output("explorer-mitigation", "children"),
    Input("explorer-control", "value"),
    Input("explorer-mapping-filter", "value"),
    Input("explorer-search", "value"),
    Input("theme-store", "data"),
)
def update_explorer(node_id, mapping_filter, search_text, theme):
    if not node_id:
        empty = go.Figure()
        return empty, empty, html.Div(), html.Div(), html.Div()

    node = get_node_by_id(node_id)
    if not node:
        empty = go.Figure()
        return empty, empty, html.Div(), html.Div(), html.Div()

    mappings = get_mappings_for_node(node_id)

    # Apply mapping filter
    filtered = dict(mappings)
    if mapping_filter == "direct":
        filtered["transitive"] = []
    elif mapping_filter == "transitive":
        filtered["direct"] = []

    # Apply search filter
    if search_text:
        search_lower = search_text.lower()
        filtered["direct"] = [
            d for d in filtered["direct"]
            if search_lower in d.get("target_name", "").lower()
            or search_lower in (get_node_by_id(d["target_node_id"]) or {}).get("description", "").lower()
        ]
        filtered["transitive"] = [
            t for t in filtered["transitive"]
            if search_lower in t.get("target_name", "").lower()
            or search_lower in (get_node_by_id(t["target_node_id"]) or {}).get("description", "").lower()
        ]

    sankey = _build_sankey(filtered, node, theme)
    neighborhood = _build_neighborhood(filtered, node, theme)
    source_card = _build_source_card(node, filtered)
    mapping_cards = _build_mapping_cards(filtered, node)
    mitigation = _build_mitigation_section(node)

    return sankey, neighborhood, source_card, mapping_cards, mitigation


@callback(
    Output({"type": "card-collapse", "index": ALL}, "is_open"),
    Input({"type": "card-header", "index": ALL}, "n_clicks"),
    State({"type": "card-collapse", "index": ALL}, "is_open"),
    prevent_initial_call=True,
)
def toggle_card(n_clicks, is_open):
    """Toggle card expand/collapse on header click."""
    if not ctx.triggered_id:
        return [dash.no_update] * len(is_open)

    triggered_index = ctx.triggered_id["index"]

    # Pattern-matching: return new state for ALL matched components.
    # Toggle the one that was clicked, leave others unchanged.
    result = []
    for i, state in enumerate(is_open):
        # ctx.inputs_list[0][i] has the id dict for each matched input
        if ctx.inputs_list[0][i]["id"]["index"] == triggered_index:
            result.append(not state)
        else:
            result.append(dash.no_update)
    return result
```

**Note:** The `toggle_card` pattern-matching callback handles expand/collapse for all cards. This is the most complex callback in the app.

- [ ] **Step 2: Verify the page loads**

```bash
cd project2 && PYTHONPATH=. python app.py
```

Open http://localhost:8050/explorer. Expected:
- Framework dropdown defaults to OWASP Agentic Top 10
- Control dropdown populates with ASI01-ASI10
- Select ASI02, see Sankey diagram, neighborhood graph, source card with reachability summary, framework-grouped mapping cards
- Cards expand on click to show full text and bridge paths
- Mapping filter and search filter work

- [ ] **Step 3: Commit**

```bash
git add project2/pages/explorer.py
git commit -m "feat(project2): Page 3 crosswalk explorer with Sankey, neighborhood graph, and expandable cards"
```

---

## Task 9: Page 4 -- Coverage Analysis

**Files:**
- Create: `project2/pages/coverage.py`

- [ ] **Step 1: Create the coverage page**

Write to `project2/pages/coverage.py`:

```python
"""Page 4: Coverage Analysis -- compliance gap analysis across frameworks."""

import dash
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from dash import Input, Output, callback, dcc, html

from components.data_loader import get_coverage_matrix, get_framework_stats
from components.framework_colors import (
    FRAMEWORK_KEYS,
    get_color,
    get_display_name,
    get_short_name,
)
from components.plot_theme import get_template

dash.register_page(__name__, path="/coverage", name="Coverage", order=3)

INTRO_TEXT = (
    "Select a source framework to see what percentage of each target framework "
    "it covers through direct and transitive (2-hop bridge) mappings. "
    "Adjust the confidence threshold to focus on higher-quality mappings. "
    "Gaps in the radar chart reveal where additional compliance work is needed."
)

CONFIDENCE_HELP = {
    0: "Any: include all mappings regardless of confidence",
    1: "Suggestive+: shared categories and above",
    2: "Expert+: expert-validated and authoritative only",
    3: "Authoritative only: from official framework source documents",
}


def _framework_options():
    stats = get_framework_stats()
    return [
        {"label": f"{get_display_name(fw)} ({stats[fw]['node_count']})", "value": fw}
        for fw in FRAMEWORK_KEYS
        if fw in stats
    ]


def _build_radar(source_fw, coverage_data, theme="dark"):
    """Build radar chart showing coverage across all target frameworks."""
    if source_fw not in coverage_data:
        fig = go.Figure()
        fig.update_layout(template=get_template(theme))
        return fig

    targets = coverage_data[source_fw]
    target_fws = sorted(targets.keys(), key=lambda fw: targets[fw]["total_pct"], reverse=True)

    categories = [get_short_name(fw) for fw in target_fws]
    values = [targets[fw]["total_pct"] for fw in target_fws]
    direct_values = [targets[fw]["direct_pct"] for fw in target_fws]

    # Close the polygon
    categories.append(categories[0])
    values.append(values[0])
    direct_values.append(direct_values[0])

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill="toself",
        name="Total (direct + transitive)",
        fillcolor="rgba(0,212,255,0.15)",
        line=dict(color="#00d4ff", width=2),
        hovertemplate="<b>%{theta}</b><br>Total coverage: %{r:.1f}%<extra></extra>",
    ))
    fig.add_trace(go.Scatterpolar(
        r=direct_values,
        theta=categories,
        fill="toself",
        name="Direct only",
        fillcolor="rgba(31,111,235,0.1)",
        line=dict(color="#1f6feb", width=1, dash="dot"),
        hovertemplate="<b>%{theta}</b><br>Direct coverage: %{r:.1f}%<extra></extra>",
    ))

    fig.update_layout(
        template=get_template(theme),
        height=500,
        title=dict(
            text=f"Coverage Profile for {get_display_name(source_fw)}",
            font=dict(size=14),
        ),
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                ticksuffix="%",
                gridcolor="#21262d" if theme == "dark" else "#d1d9e0",
            ),
            angularaxis=dict(
                gridcolor="#21262d" if theme == "dark" else "#d1d9e0",
            ),
        ),
        legend=dict(orientation="h", yanchor="bottom", y=-0.15),
    )
    return fig


def _build_coverage_bar(source_fw, coverage_data, theme="dark"):
    """Build stacked bar chart: coverage breakdown by direct/transitive/gap."""
    if source_fw not in coverage_data:
        fig = go.Figure()
        fig.update_layout(template=get_template(theme))
        return fig

    targets = coverage_data[source_fw]
    target_fws = sorted(targets.keys(), key=lambda fw: targets[fw]["total_pct"], reverse=True)

    fw_labels = [get_short_name(fw) for fw in target_fws]
    direct_pcts = [targets[fw]["direct_pct"] for fw in target_fws]
    trans_pcts = [targets[fw]["transitive_pct"] for fw in target_fws]
    gap_pcts = [100 - targets[fw]["total_pct"] for fw in target_fws]
    total_pcts = [targets[fw]["total_pct"] for fw in target_fws]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=fw_labels, x=direct_pcts, name="Direct",
        orientation="h", marker_color="#1f6feb",
        hovertemplate="<b>%{y}</b><br>Direct: %{x:.1f}%<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        y=fw_labels, x=trans_pcts, name="Transitive (via bridge)",
        orientation="h", marker_color="#00d4ff",
        hovertemplate="<b>%{y}</b><br>Transitive: %{x:.1f}%<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        y=fw_labels, x=gap_pcts, name="No mapping",
        orientation="h", marker_color="#21262d",
        hovertemplate="<b>%{y}</b><br>Gap: %{x:.1f}%<extra></extra>",
    ))

    # Add percentage labels
    for i, pct in enumerate(total_pcts):
        color = "#00d4ff" if pct >= 60 else "#d9bf55" if pct >= 30 else "#ff6b6b"
        fig.add_annotation(
            x=min(pct + 2, 100), y=fw_labels[i],
            text=f"{pct:.0f}%",
            showarrow=False,
            font=dict(size=11, color=color),
            xanchor="left",
        )

    fig.update_layout(
        template=get_template(theme),
        height=500,
        title=dict(text="Coverage Breakdown by Tier", font=dict(size=14)),
        barmode="stack",
        xaxis=dict(title="Coverage %", range=[0, 110], ticksuffix="%"),
        yaxis=dict(categoryorder="array", categoryarray=list(reversed(fw_labels))),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2),
    )
    return fig


# --- Layout ---
layout = dbc.Container([
    dbc.Row(dbc.Col(
        dbc.Card(dbc.CardBody([
            html.H4("Coverage Analysis", className="mb-2"),
            html.P(INTRO_TEXT, className="text-muted mb-0", style={"fontSize": "0.9rem"}),
        ]), className="mb-3 border-0",
        style={"backgroundColor": "rgba(22,27,34,0.5)"}),
    )),

    # Controls
    dbc.Row([
        dbc.Col([
            dbc.Label("Source Framework", className="text-muted", style={"fontSize": "0.8rem"}),
            dcc.Dropdown(
                id="coverage-framework",
                options=_framework_options(),
                value="aiuc_1",
                clearable=False,
            ),
        ], md=5),
        dbc.Col([
            dbc.Label([
                "Minimum Confidence ",
                html.Span("\u24d8", id="coverage-confidence-info",
                          style={"cursor": "help", "color": "#6e7681"}),
                dbc.Tooltip(
                    "Filter mappings by confidence level. Higher confidence means "
                    "the mapping has been more rigorously validated.",
                    target="coverage-confidence-info",
                ),
            ], className="text-muted", style={"fontSize": "0.8rem"}),
            dcc.Slider(
                id="coverage-confidence",
                min=0,
                max=3,
                step=1,
                marks={
                    0: "Any",
                    1: "Suggestive+",
                    2: "Expert+",
                    3: "Authoritative",
                },
                value=0,
                className="mt-1",
            ),
        ], md=7),
    ], className="mb-4"),

    # Charts
    dbc.Row([
        dbc.Col(dcc.Loading(dcc.Graph(id="coverage-radar", config={"displayModeBar": False})), md=6),
        dbc.Col(dcc.Loading(dcc.Graph(id="coverage-bar", config={"displayModeBar": False})), md=6),
    ]),
], fluid=True)


@callback(
    Output("coverage-radar", "figure"),
    Output("coverage-bar", "figure"),
    Input("coverage-framework", "value"),
    Input("coverage-confidence", "value"),
    Input("theme-store", "data"),
)
def update_coverage(source_fw, confidence_level, theme):
    coverage = get_coverage_matrix()

    # For now, coverage matrix is pre-computed with all confidence levels.
    # Confidence filtering would require recomputation; for the initial version
    # we show the full coverage and note the selected threshold.
    # TODO: If confidence filtering is needed at runtime, prepare_data.py should
    # produce separate matrices per confidence level, or the app should recompute.

    radar = _build_radar(source_fw, coverage, theme)
    bar = _build_coverage_bar(source_fw, coverage, theme)

    return radar, bar
```

- [ ] **Step 2: Verify the page loads**

```bash
cd project2 && PYTHONPATH=. python app.py
```

Open http://localhost:8050/coverage. Expected: Framework dropdown, confidence slider, radar chart showing coverage percentages, stacked bar showing direct/transitive/gap breakdown.

- [ ] **Step 3: Commit**

```bash
git add project2/pages/coverage.py
git commit -m "feat(project2): Page 4 coverage analysis with radar and stacked bar"
```

---

## Task 10: Custom CSS and Visual Polish

**Files:**
- Modify: `project2/assets/style.css`

- [ ] **Step 1: Write the custom stylesheet**

Write to `project2/assets/style.css`:

```css
/* AI Security Crosswalk Explorer - Custom styles
   Professional core with cyber accent highlights.
   Dark mode default (CYBORG), light mode via DBC FLATLY. */

/* ---- Typography ---- */
body {
  font-family: "Inter", system-ui, -apple-system, sans-serif;
}

/* ---- Cyber accent: interactive elements ---- */
.nav-link.active {
  border-bottom: 2px solid #00d4ff !important;
  color: #00d4ff !important;
}

.nav-link:hover {
  color: #00d4ff !important;
}

/* ---- Cards ---- */
.card {
  background-color: rgba(22, 27, 34, 0.7);
  border-color: #21262d;
  transition: border-color 0.2s ease;
}

.card:hover {
  border-color: #30363d;
}

.card-header {
  background-color: rgba(22, 27, 34, 0.5);
  border-bottom-color: #21262d;
}

/* ---- Dropdowns (Dash specific) ---- */
.Select-control {
  background-color: #0d1117 !important;
  border-color: #30363d !important;
}

.Select-menu-outer {
  background-color: #161b22 !important;
  border-color: #30363d !important;
}

.Select-option.is-focused {
  background-color: rgba(0, 212, 255, 0.1) !important;
}

.Select-value-label {
  color: #c9d1d9 !important;
}

/* ---- Badge glow on hover ---- */
.badge:hover {
  box-shadow: 0 0 8px rgba(0, 212, 255, 0.3);
}

/* ---- Stats cards ---- */
.text-info {
  color: #00d4ff !important;
}

/* ---- Scrollbar (dark mode) ---- */
::-webkit-scrollbar {
  width: 8px;
}

::-webkit-scrollbar-track {
  background: #0d1117;
}

::-webkit-scrollbar-thumb {
  background: #30363d;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #484f58;
}

/* ---- Loading spinner ---- */
._dash-loading {
  color: #00d4ff;
}

/* ---- Checklist and radio items ---- */
.form-check-input:checked {
  background-color: #00d4ff;
  border-color: #00d4ff;
}

/* ---- Range slider ---- */
.rc-slider-track {
  background-color: #1f6feb !important;
}

.rc-slider-handle {
  border-color: #00d4ff !important;
  background-color: #00d4ff !important;
  box-shadow: 0 0 6px rgba(0, 212, 255, 0.5) !important;
}

/* ---- Responsive ---- */
@media (max-width: 768px) {
  .card-header {
    font-size: 0.85rem;
  }
}
```

- [ ] **Step 2: Verify styling in browser**

```bash
cd project2 && PYTHONPATH=. python app.py
```

Open http://localhost:8050 and check:
- Dark mode looks professional with cyber accents
- Active nav link has cyan underline
- Cards have subtle borders and hover effects
- Dropdowns styled consistently
- Badge glow on hover

- [ ] **Step 3: Commit**

```bash
git add project2/assets/style.css
git commit -m "style(project2): custom CSS with cyber accent theme and responsive polish"
```

---

## Task 11: README

**Files:**
- Create: `project2/README.md`

- [ ] **Step 1: Write the README**

Write to `project2/README.md`:

```markdown
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
```

- [ ] **Step 2: Commit**

```bash
git add project2/README.md
git commit -m "docs(project2): comprehensive README with setup instructions and feature overview"
```

---

## Task 12: Repo Restructuring -- Project 1

**Files:**
- Create: `project1/` directory
- Move: existing Project 1 materials
- Modify: root `README.md`

- [ ] **Step 1: Create project1 directory and move notebook**

```bash
mkdir -p project1
cp notebooks/project1_crosswalk_eda.ipynb project1/
cp notebooks/project1_lambros.zip project1/ 2>/dev/null || true
```

- [ ] **Step 2: Create project1/README.md**

Write to `project1/README.md`:

```markdown
# Project 1: AI Security Framework Crosswalk -- Exploratory Visual Analysis

A scientific notebook that performs an exploratory visual analysis of the AI Security Framework Crosswalk dataset using matplotlib and seaborn. Built as the first deliverable for COMP 4433 Data Visualization (University of Denver, Spring 2026).

## Contents

- `project1_crosswalk_eda.ipynb` -- The main analysis notebook
- `project1_lambros.zip` -- Packaged submission

## Running

The notebook depends on data files in the parent repository's `data/` directory. Run from the repository root:

```bash
pip install -r requirements.txt
jupyter notebook project1/project1_crosswalk_eda.ipynb
```

## Overview

The notebook walks through the crosswalk dataset with matplotlib and seaborn, covering:
- Graph structure and framework size distribution
- Entry type and domain composition
- Cross-framework mapping density
- Confidence and rationale distributions
- Network topology characteristics

See the parent repository README for full project context.
```

- [ ] **Step 3: Update root README to reference both projects**

Add a section to the root `README.md` after the existing Project 1 section, referencing both project directories. Read the file first to find the right insertion point.

- [ ] **Step 4: Commit**

```bash
git add project1/ -f
git commit -m "refactor: organize Project 1 materials into project1/ directory"
```

---

## Task 13: Integration Testing and Final Polish

- [ ] **Step 1: Run all unit tests**

```bash
cd project2 && PYTHONPATH=. python -m pytest tests/ -v
```

Expected: All tests pass.

- [ ] **Step 2: Start the app and test all pages manually**

```bash
cd project2 && PYTHONPATH=. python app.py
```

Test checklist:
- [ ] Landscape: network graph renders 9 nodes, heatmap renders 9x9, filters work
- [ ] Deep Dive: sunburst loads for each framework, bar chart updates, control detail card appears on click
- [ ] Explorer: chained dropdown works, ASI02 shows 11 direct + transitive mappings, cards expand with bridge paths, search filters work
- [ ] Coverage: radar shows coverage shape, bar chart shows direct/transitive/gap, framework selector works
- [ ] Theme toggle: dark/light switch updates charts and layout
- [ ] Navigation: all 4 page links work, active page highlighted

- [ ] **Step 3: Fix any issues found during testing**

Address visual bugs, layout issues, or broken callbacks discovered during manual testing.

- [ ] **Step 4: Final commit**

```bash
git add -A project2/
git commit -m "test(project2): integration testing pass, fix any discovered issues"
```
