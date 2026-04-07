"""Function-class match signal (3 modes).

Generalizes the v1 ``THREAT_FUNCTION_PROFILES`` lookup to support:

- ``control_to_risk``  : source has function_class, target is a risk → look up
                         which function classes are relevant for that risk.
- ``control_to_control``: both have function_class → same class match or
                          complementary pair (handled by composer's boost).
- ``technique_to_risk`` : source is an attack technique → tactic-to-risk lookup.

Returned matrix is binary (0.0 / 1.0); composer.py multiplies by the
configured boost.

Function profiles for OWASP ASI risks are migrated from
``aiuc/taxonomy.py:THREAT_FUNCTION_PROFILES``. For nodes from frameworks that
don't carry a ``function_class`` attribute, we classify on the fly via
``FUNCTION_KEYWORDS`` keyword matching against the node text.
"""

from __future__ import annotations

import re
from typing import Sequence

import networkx as nx
import numpy as np

from mapping_engine.engine.graph import get_node_text

# ── Profiles migrated from v1 ────────────────────────────────────────────────

THREAT_FUNCTION_PROFILES: dict[str, set[str]] = {
    "ASI01": {"PREV", "SCOPE", "GATE", "VALID", "DETECT", "GOVERN"},
    "ASI02": {"SCOPE", "VALID", "DETECT", "GATE", "ISOLATE"},
    "ASI03": {"SCOPE", "ISOLATE", "DETECT", "VALID", "GOVERN"},
    "ASI04": {"ISOLATE", "VALID", "DETECT", "SCOPE", "GOVERN"},
    "ASI05": {"SCOPE", "ISOLATE", "PREV", "VALID", "DETECT"},
    "ASI06": {"PREV", "SCOPE", "ISOLATE", "VALID", "DETECT"},
    "ASI07": {"SCOPE", "ISOLATE", "DETECT"},
    "ASI08": {"PREV", "SCOPE", "GOVERN", "DETECT", "GATE", "VALID"},
    "ASI09": {"PREV", "GATE", "VALID", "DISCLOSE", "SCOPE", "DETECT"},
    "ASI10": {"SCOPE", "ISOLATE", "VALID", "GOVERN", "DETECT", "GATE", "PREV", "DISCLOSE"},
}

FUNCTION_KEYWORDS: dict[str, list[str]] = {
    "PREV": ["prevent", "block", "filter", "restrict input", "detect adversarial"],
    "SCOPE": ["limit", "constrain", "minimize", "least privilege", "access control",
              "unauthorized", "restrict", "scope", "data distribution"],
    "GATE": ["human review", "approval", "intervention", "feedback", "flag",
             "pause", "stop", "override", r"human.*oversight", "appeal"],
    "DETECT": ["log", "monitor", "audit", "trace", "detect", "alert",
               "observe", "measurement", r"post-deployment.*monitor"],
    "VALID": ["test", "assess", "evaluate", "verify", "red team",
              "penetration", "due diligence", "tevv", "assurance criteria"],
    "GOVERN": ["policy", "plan", "accountability", "process", "compliance",
               "acceptable use", "change approval", "quality management",
               "inventory", "regulatory", "decommission", "lifecycle"],
    "ISOLATE": ["isolate", "contain", "sandbox", "segment", "separate",
                "deployment environment", "tenant"],
    "DISCLOSE": ["disclose", "transparency", "provenance", "label", "watermark",
                 "model card", "interpretability"],
}

COMPLEMENTARY_PAIRS: set[tuple[str, str]] = set()
for a, b in [("PREV", "DETECT"), ("SCOPE", "ISOLATE"), ("GATE", "GOVERN"), ("VALID", "DETECT")]:
    COMPLEMENTARY_PAIRS.add((a, b))
    COMPLEMENTARY_PAIRS.add((b, a))


def _classify_by_keywords(text: str) -> str | None:
    t = text.lower()
    for func, patterns in FUNCTION_KEYWORDS.items():
        for p in patterns:
            if re.search(p, t):
                return func
    return None


def _function_class(G: nx.DiGraph, node_id: str) -> str | None:
    fc = G.nodes[node_id].get("function_class")
    if fc:
        return fc
    return _classify_by_keywords(get_node_text(G, node_id))


def _local_id(G: nx.DiGraph, node_id: str) -> str:
    return G.nodes[node_id].get("local_id") or node_id.split(":", 1)[-1]


def _detect_mode(G: nx.DiGraph, src: str, tgt: str) -> str:
    s_et = G.nodes[src].get("entry_type")
    t_et = G.nodes[tgt].get("entry_type")
    if s_et == "technique" and t_et == "risk":
        return "technique_to_risk"
    if t_et == "risk":
        return "control_to_risk"
    return "control_to_control"


def compute_function_match(
    G: nx.DiGraph,
    source_nodes: Sequence[str],
    target_nodes: Sequence[str],
    config: dict | None = None,
) -> np.ndarray:
    """Return a binary (0.0/1.0) function-match matrix.

    Mode is auto-detected per (source, target) pair from the graph node
    ``entry_type`` attributes. The composer multiplies hits by the
    mode-specific boost from ``defaults.yaml``.
    """
    M = np.zeros((len(source_nodes), len(target_nodes)), dtype=np.float64)
    for i, s in enumerate(source_nodes):
        s_func = _function_class(G, s)
        for j, t in enumerate(target_nodes):
            mode = _detect_mode(G, s, t)
            if mode == "control_to_risk":
                if not s_func:
                    continue
                profile = THREAT_FUNCTION_PROFILES.get(_local_id(G, t))
                if profile is None:
                    # Heuristic for non-OWASP-ASI risks: any function class counts
                    M[i, j] = 1.0
                elif s_func in profile:
                    M[i, j] = 1.0
            elif mode == "control_to_control":
                t_func = _function_class(G, t)
                if not s_func or not t_func:
                    continue
                if s_func == t_func or (s_func, t_func) in COMPLEMENTARY_PAIRS:
                    M[i, j] = 1.0
            else:  # technique_to_risk
                # Without an ATT&CK→ASI tactic table yet, fall back to: any technique
                # node maps to any risk by default. Real lookup table comes later.
                M[i, j] = 1.0
    return M
