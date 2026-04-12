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
