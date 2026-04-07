"""JSON writer conforming to ``schema_template/crosswalk-mapping-v2.schema.json``."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jsonschema
import networkx as nx

from mapping_engine.config import PairConfig
from mapping_engine.engine.mapper import MappingResult, RATIONALE_LABELS

REPO = Path(__file__).resolve().parents[2]
SCHEMA_PATH = REPO / "schema_template" / "crosswalk-mapping-v2.schema.json"

FRAMEWORK_INFO: dict[str, dict[str, Any]] = {
    "aiuc_1": {"name": "AIUC-1", "version": "1.0", "url": "https://www.aiuc-1.com"},
    "owasp_agentic": {
        "name": "OWASP Top 10 for Agentic Applications",
        "version": "2026",
        "url": "https://owasp.org/",
    },
}

# OWASP Agentic titles used for target_standard metadata when the target is OWASP.
OWASP_RANKS: dict[str, int] = {f"ASI{i:02d}": i for i in range(1, 11)}


def _load_schema() -> dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text())


def _std_info(framework: str, node_count: int, *, as_source: bool) -> dict[str, Any]:
    base = FRAMEWORK_INFO.get(framework, {"name": framework, "version": "unknown"})
    info = dict(base)
    if as_source:
        info["controls"] = max(1, node_count)
    else:
        info["entries"] = max(1, node_count)
    return info


def _source_entries(
    result: MappingResult, G: nx.DiGraph
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Build the source_to_target array and rationale distribution."""
    # Group mappings by source
    by_src: dict[str, list[dict[str, Any]]] = {}
    for m in result.mappings:
        by_src.setdefault(m["source_node_id"], []).append(m)

    entries: list[dict[str, Any]] = []
    rationale_dist: dict[str, int] = {}

    for s in result.source_nodes:
        node = G.nodes[s]
        fc = node.get("function_class") or "GOVERN"
        ms = by_src.get(s, [])
        ms_sorted = sorted(ms, key=lambda x: -x["score"])
        v2_mappings: list[dict[str, Any]] = []
        for m in ms_sorted:
            t_node = G.nodes[m["target_node_id"]]
            t_local = t_node.get("local_id") or m["target_node_id"].split(":", 1)[-1]
            rc = m["rationale_code"]
            rationale_dist[rc] = rationale_dist.get(rc, 0) + 1
            entry = {
                "owasp_id": t_local,
                "owasp_title": t_node.get("name") or t_local,
                "relevance": m["relevance"],
                "rationale_code": rc,
                "rationale_label": m["rationale_label"],
                "score": round(float(m["score"]), 4),
                "signals": {
                    k: round(float(v), 4)
                    for k, v in m["signals"].items()
                    if 0.0 <= float(v) <= 1.0
                },
            }
            v2_mappings.append(entry)

        primary = sum(1 for vm in v2_mappings if vm["relevance"] == "Primary")
        entries.append({
            "control_id": node.get("local_id") or s.split(":", 1)[-1],
            "control_title": node.get("name") or s,
            "domain": node.get("domain") or "",
            "function_class": fc if fc in RATIONALE_LABELS else "GOVERN",
            "mapping_count": len(v2_mappings),
            "primary_count": primary,
            "secondary_count": len(v2_mappings) - primary,
            "mappings": v2_mappings,
        })

    return entries, rationale_dist


def _target_entries(
    result: MappingResult, G: nx.DiGraph
) -> list[dict[str, Any]]:
    """Build the target_to_source array (exactly 10 for OWASP Agentic)."""
    by_tgt: dict[str, list[dict[str, Any]]] = {}
    for m in result.mappings:
        by_tgt.setdefault(m["target_node_id"], []).append(m)

    entries: list[dict[str, Any]] = []
    for t in result.target_nodes:
        node = G.nodes[t]
        t_local = node.get("local_id") or t.split(":", 1)[-1]
        ms = sorted(by_tgt.get(t, []), key=lambda x: -x["score"])
        v2_mappings: list[dict[str, Any]] = []
        coverage: dict[str, int] = {}
        for m in ms:
            s_node = G.nodes[m["source_node_id"]]
            fc = s_node.get("function_class") or m["rationale_code"] or "GOVERN"
            if fc not in RATIONALE_LABELS:
                fc = "GOVERN"
            rc = m["rationale_code"]
            coverage[rc] = coverage.get(rc, 0) + 1
            v2_mappings.append({
                "control_id": s_node.get("local_id") or m["source_node_id"].split(":", 1)[-1],
                "control_title": s_node.get("name") or m["source_node_id"],
                "domain": s_node.get("domain") or "",
                "function_class": fc,
                "relevance": m["relevance"],
                "rationale_code": rc,
                "rationale_label": m["rationale_label"],
                "score": round(float(m["score"]), 4),
                "signals": {
                    k: round(float(v), 4)
                    for k, v in m["signals"].items()
                    if 0.0 <= float(v) <= 1.0
                },
            })
        all_codes = set(RATIONALE_LABELS.keys())
        uncovered = sorted(all_codes - set(coverage.keys()))
        primary = sum(1 for vm in v2_mappings if vm["relevance"] == "Primary")
        entries.append({
            "owasp_id": t_local,
            "owasp_title": node.get("name") or t_local,
            "owasp_rank": OWASP_RANKS.get(t_local, 1),
            "mapping_count": len(v2_mappings),
            "primary_count": primary,
            "secondary_count": len(v2_mappings) - primary,
            "function_coverage": coverage,
            "uncovered_functions": uncovered,
            "mappings": v2_mappings,
        })
    return entries


def _build_document(
    result: MappingResult,
    G: nx.DiGraph,
    pair_config: PairConfig,
) -> dict[str, Any]:
    source_entries, rationale_dist = _source_entries(result, G)
    target_entries = _target_entries(result, G)

    total_controls = len(source_entries)
    mapped = sum(1 for s in source_entries if s["mapping_count"] > 0)
    total_mappings = sum(s["mapping_count"] for s in source_entries)
    primary_total = sum(s["primary_count"] for s in source_entries)
    owasp_with = sum(1 for t in target_entries if t["mapping_count"] > 0)

    summary = {
        "controls_mapped": f"{mapped} / {total_controls}",
        "controls_unmapped": total_controls - mapped,
        "owasp_entries_with_matches": min(owasp_with, 10),
        "total_mappings": total_mappings,
        "primary_mappings": primary_total,
        "secondary_mappings": total_mappings - primary_total,
        "rationale_distribution": rationale_dist,
    }

    w = result.metadata.get("weights", {})
    th = result.metadata.get("thresholds", {})
    pipeline = {
        "signals": {
            "bridge": {
                "weight": float(w.get("bridge", 0.45)),
                "technique": "2-hop weighted Jaccard on crosswalk graph",
            },
            "semantic": {
                "weight": float(w.get("semantic", 0.35)),
                "technique": f"Sentence-transformer cosine ({result.metadata.get('semantic_model', 'bge')})",
            },
            "keyword": {
                "weight": float(w.get("keyword", 0.20)),
                "technique": "TF-IDF cosine with synonym expansion",
            },
            "function_match": {
                "weight": float(w.get("boost", 0.50)),
                "technique": "Multiplicative boost when function class matches target profile",
            },
        },
        "thresholds": {
            "direct": float(th.get("direct", 0.55)),
            "related": float(th.get("related_primary", 0.35)),
            "governance_floor": float(th.get("gov_floor", 0.22)),
            "tangential": float(th.get("tangential", 0.20)),
        },
    }

    classification = {
        "rationale_taxonomy": dict(RATIONALE_LABELS),
        "relevance_levels": ["Primary", "Secondary"],
    }

    metadata = {
        "schema_version": "2.0",
        "generated_at": result.metadata["generated_at"],
        "methodology": result.metadata.get("methodology", "multi-signal-hybrid-v2"),
        "source_standard": _std_info(
            pair_config.source_framework, result.metadata["n_source_nodes"], as_source=True
        ),
        "target_standard": _std_info(
            pair_config.target_framework, result.metadata["n_target_nodes"], as_source=False
        ),
        "pipeline": pipeline,
        "classification": classification,
    }

    # Gap analysis: unmapped source controls
    unmapped = [
        {
            "control_id": s["control_id"],
            "control_title": s["control_title"],
            "domain": s["domain"],
            "function_class": s["function_class"],
            "gap_reason": "Below mapping threshold for all target entries",
        }
        for s in source_entries
        if s["mapping_count"] == 0
    ]
    gap = {
        "unmapped_controls": unmapped,
        "unmapped_count": len(unmapped),
        "note": "Unmapped controls did not reach the Related threshold under the current pipeline.",
    }

    return {
        "metadata": metadata,
        "summary": summary,
        "control_level": {
            "source_to_target": source_entries,
            "target_to_source": target_entries,
        },
        "gap_analysis": gap,
    }


def write_json(
    result: MappingResult,
    G: nx.DiGraph,
    pair_config: PairConfig,
    output_path: str | Path,
) -> dict[str, Any]:
    """Build, validate against the v2 schema, and write the JSON document."""
    doc = _build_document(result, G, pair_config)

    schema = _load_schema()
    # The schema uses source_to_owasp/owasp_to_source keys; we emit
    # source_to_target/target_to_source. Adapt a copy for validation.
    doc_for_validation = _adapt_for_schema(doc, schema)
    jsonschema.validate(doc_for_validation, schema)

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, indent=2, default=str))
    return doc


def _adapt_for_schema(doc: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    """Re-key control_level entries to match the published v2 schema which uses
    ``source_to_owasp`` / ``owasp_to_source`` property names. We keep the
    semantic names in the written file but pass a validator-compatible view.
    """
    adapted = json.loads(json.dumps(doc, default=str))
    cl = adapted.get("control_level", {})
    if "source_to_target" in cl:
        cl["source_to_owasp"] = cl.pop("source_to_target")
    if "target_to_source" in cl:
        cl["owasp_to_source"] = cl.pop("target_to_source")
    return adapted
