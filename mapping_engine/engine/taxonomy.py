"""Generalized control-function taxonomy.

Ports the AIUC-1 + OWASP ASI logic from
``AIUC_2_OWASP_Agentic_Top_10/aiuc/taxonomy.py`` into a framework-agnostic
form. AIUC-specific lookups (control function, control titles,
specific/generic DETECT, overrides) are moved into
``mapping_engine/config/function_profiles.yaml`` so other framework pairs
can plug in their own profiles.
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import networkx as nx
import yaml

from mapping_engine.engine.graph import get_node_text

DEFAULT_PROFILES_PATH = Path(__file__).resolve().parents[1] / "config" / "function_profiles.yaml"

FUNCTION_KEYWORDS: dict[str, list[str]] = {
    "PREV":    ["prevent", "block", "filter", "restrict input", "detect adversarial"],
    "SCOPE":   ["limit", "constrain", "minimize", "least privilege", "access control",
                "unauthorized", "restrict", "scope", "data distribution"],
    "GATE":    ["human review", "approval", "intervention", "feedback", "flag",
                "pause", "stop", "override", r"human.*oversight", "appeal"],
    "DETECT":  ["log", "monitor", "audit", "trace", "detect", "alert",
                "observe", "measurement", r"post-deployment.*monitor"],
    "VALID":   ["test", "assess", "evaluate", "verify", "red team",
                "penetration", "due diligence", "tevv", "assurance criteria"],
    "GOVERN":  ["policy", "plan", "accountability", "process", "compliance",
                "acceptable use", "change approval", "quality management",
                "inventory", "regulatory", "decommission", "lifecycle"],
    "ISOLATE": ["isolate", "contain", "sandbox", "segment", "separate",
                "deployment environment", "tenant"],
    "DISCLOSE":["disclose", "transparency", "provenance", "label", "watermark",
                "model card", "interpretability"],
}


@lru_cache(maxsize=1)
def load_function_profiles(path: str | None = None) -> dict[str, Any]:
    p = Path(path) if path else DEFAULT_PROFILES_PATH
    if not p.exists():
        return {}
    return yaml.safe_load(p.read_text()) or {}


def _local_id(G: nx.DiGraph, node_id: str) -> str:
    return G.nodes[node_id].get("local_id") or node_id.split(":", 1)[-1]


def _classify_by_keywords(text: str) -> str | None:
    t = (text or "").lower()
    for func, patterns in FUNCTION_KEYWORDS.items():
        for p in patterns:
            if re.search(p, t):
                return func
    return None


def classify_function(G: nx.DiGraph, node_id: str) -> str | None:
    """Return the function class for ``node_id``.

    Resolution order:
    1. ``function_class`` attribute already on the node, if present.
    2. AIUC-1 lookup table from ``function_profiles.yaml``.
    3. Keyword classification on the node text.
    """
    data = G.nodes[node_id]
    fc = data.get("function_class")
    if fc:
        return fc

    framework = data.get("framework")
    profiles = load_function_profiles()
    fw_block = (profiles.get("frameworks") or {}).get(framework, {})
    lookup = fw_block.get("control_functions") or {}
    if lookup:
        lid = _local_id(G, node_id)
        if lid in lookup:
            return lookup[lid]

    return _classify_by_keywords(get_node_text(G, node_id))


def classify_rationale(G: nx.DiGraph, source_id: str) -> str:
    """Return the rationale code (defaults to the function class)."""
    return classify_function(G, source_id) or "GOVERN"


def classify_relevance(
    G: nx.DiGraph,
    source_id: str,
    target_id: str,
    function_class: str | None = None,
) -> str:
    """Classify a (source, target) pair as ``"Primary"`` or ``"Secondary"``.

    For AIUC-1 → OWASP Agentic this applies the full v1 ``THREAT_PROFILES``
    logic loaded from ``function_profiles.yaml``. For other framework pairs
    a simplified rule is used: Primary iff the function class is in the
    target's ``primary_functions`` set, else Secondary.
    """
    func = function_class or classify_function(G, source_id) or "GOVERN"
    profiles = load_function_profiles()

    src_fw = G.nodes[source_id].get("framework")
    tgt_fw = G.nodes[target_id].get("framework")
    src_lid = _local_id(G, source_id)
    tgt_lid = _local_id(G, target_id)

    if src_fw == "aiuc_1" and tgt_fw == "owasp_agentic":
        aiuc = (profiles.get("frameworks") or {}).get("aiuc_1", {})
        overrides = {tuple(k.split("__")): v for k, v in (aiuc.get("overrides") or {}).items()}
        if (src_lid, tgt_lid) in overrides:
            return overrides[(src_lid, tgt_lid)]
        threat_block = ((profiles.get("threat_profiles") or {}).get("owasp_agentic") or {})
        prof = threat_block.get(tgt_lid, {})
        title = (G.nodes[source_id].get("name") or "").lower()
        specific_detect = set(aiuc.get("specific_detect") or [])
        generic_detect = set(aiuc.get("generic_detect") or [])

        if func == "DETECT":
            rule = prof.get("detect_rule", "never")
            if rule == "all":
                return "Primary"
            if rule == "generic_only" and src_lid in generic_detect:
                return "Primary"
            if rule == "specific_only" and src_lid in specific_detect:
                return "Primary"
            return "Secondary"

        if func == "DISCLOSE":
            return "Primary" if src_lid in (prof.get("disclose_primary") or []) else "Secondary"

        if func in set(prof.get("primary_functions") or []):
            return "Primary"
        for pat in prof.get("primary_topics") or []:
            if re.search(pat, title):
                return "Primary"
        return "Secondary"

    threat_block = ((profiles.get("threat_profiles") or {}).get(tgt_fw) or {})
    prof = threat_block.get(tgt_lid, {})
    if func in set(prof.get("primary_functions") or []):
        return "Primary"
    return "Secondary"

