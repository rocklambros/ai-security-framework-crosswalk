#!/usr/bin/env python3
"""Build crosswalk graph from all framework source data.

Reads framework data from data/frameworks/ and produces:
- data/processed/nodes.json
- data/processed/edges.json
- data/processed/graph_stats.json

Usage: python scripts/build_graph.py
"""

import json
import logging
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone

try:
    import yaml
except ImportError:
    yaml = None
    print("WARNING: pyyaml not installed. CoSAI YAML parsing will be skipped.", file=sys.stderr)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRAMEWORKS_DIR = os.path.join(BASE_DIR, "data", "frameworks")
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "processed")

# Framework key mapping for AIUC-1 framework_references
AIUC1_FWREF_MAP = {
    "eu_ai_act": "eu_gpai_cop",
    "nist_ai_rmf": "nist_rmf",
    "csa_aicm": "csa_aicm",
    "owasp_llm_top10": "owasp_llm",
    "mitre_atlas": "mitre_atlas",
    # Skipped:
    # "iso_42001": not in our registry
    # "owasp_aivss": not a separate framework
}

CONFIDENCE_RANK = {"authoritative": 4, "expert": 3, "inferred": 2, "unvalidated": 1}

# Regex for valid node_id local part: only [A-Za-z0-9._-]
_SANITIZE_RE = re.compile(r"[^A-Za-z0-9._-]")


def sanitize_local_id(s):
    """Replace invalid chars in local_id portion of node_id with dashes."""
    return _SANITIZE_RE.sub("-", s)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_node(**kw):
    """Create a node dict matching schema/node.schema.json."""
    desc = kw.get("description") or ""
    return {
        "node_id": kw["node_id"],
        "framework": kw["framework"],
        "local_id": kw["local_id"],
        "name": kw.get("name", kw["local_id"]),
        "entry_type": kw.get("entry_type", "control"),
        "parent_node_id": kw.get("parent_node_id"),
        "domain": kw.get("domain") or "",
        "description": desc[:2000],
        "function_class": kw.get("function_class"),
        "classification": kw.get("classification"),
        "control_type": kw.get("control_type"),
        "frequency": kw.get("frequency"),
        "applicable_capabilities": kw.get("applicable_capabilities") or [],
        "keywords": kw.get("keywords") or [],
        "url": kw.get("url"),
        "retired": kw.get("retired", False),
    }


def make_edge(**kw):
    """Create an edge dict matching schema/edge.schema.json."""
    src = kw["source_node_id"]
    tgt = kw["target_node_id"]
    rc = kw.get("rationale_code")
    prov = kw.get("provenance", "")
    edge_id = f"{src}--{tgt}--{rc or 'none'}--{prov}"
    return {
        "edge_id": edge_id,
        "source_node_id": src,
        "target_node_id": tgt,
        "source_framework": src.split(":")[0] if ":" in src else "",
        "target_framework": tgt.split(":")[0] if ":" in tgt else "",
        "rationale_code": rc,
        "rationale_label": kw.get("rationale_label"),
        "relevance": kw.get("relevance"),
        "confidence": kw.get("confidence", "unvalidated"),
        "provenance": prov,
        "score": None,
        "signals": None,
        "notes": None,
    }


def edge_key(e):
    """Dedup key: (source, target, rationale_code)."""
    return (e["source_node_id"], e["target_node_id"], e.get("rationale_code"))


def add_node(nodes, node):
    """Add node to dict, merging if exists (prefer non-null values)."""
    nid = node["node_id"]
    if nid in nodes:
        existing = nodes[nid]
        for k, v in node.items():
            if v is not None and existing.get(k) is None:
                existing[k] = v
    else:
        nodes[nid] = node


def add_edge(edges, edge):
    """Add edge, preferring higher confidence on collision."""
    key = edge_key(edge)
    if key in edges:
        existing = edges[key]
        if CONFIDENCE_RANK.get(edge["confidence"], 0) > CONFIDENCE_RANK.get(existing["confidence"], 0):
            edges[key] = edge
    else:
        edges[key] = edge


def normalize_atlas_id(ref_id):
    """AML-M0020 -> AML.M0020 (normalize dash to dot)."""
    if ref_id and ref_id.startswith("AML-"):
        return "AML." + ref_id[4:]
    return ref_id


def normalize_nist_id(ref_id):
    """'MEASURE 2.10' -> 'MEASURE-2.10' (sanitize for node_id pattern)."""
    return sanitize_local_id(ref_id.strip())


def load_json(path):
    """Load JSON file, return None on failure."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        log.warning("Failed to load %s: %s", path, exc)
        return None


def load_yaml(path):
    """Load YAML file, return None on failure."""
    if yaml is None:
        log.warning("pyyaml not installed, skipping %s", path)
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except (FileNotFoundError, yaml.YAMLError) as exc:
        log.warning("Failed to load %s: %s", path, exc)
        return None


def read_text(path):
    """Read text file, return None on failure."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        log.warning("File not found: %s", path)
        return None


# ---------------------------------------------------------------------------
# Task 1: Parse AIUC-1 standard JSON
# ---------------------------------------------------------------------------

def parse_aiuc1_standard(nodes, edges, warnings):
    """Parse aiuc-1-standard.json for domains, controls, activities, and framework_references."""
    path = os.path.join(FRAMEWORKS_DIR, "aiuc-1", "aiuc-1-standard.json")
    data = load_json(path)
    if not data:
        warnings.append("AIUC-1 standard JSON not found or invalid")
        return

    for domain in data.get("domains", []):
        dom_id = domain["id"]
        dom_node_id = f"aiuc_1:domain_{dom_id}"
        add_node(nodes, make_node(
            node_id=dom_node_id,
            framework="aiuc_1",
            local_id=f"domain_{dom_id}",
            name=domain.get("name", dom_id),
            entry_type="function",
            parent_node_id=None,
            domain=domain.get("name"),
            description=domain.get("description"),
            url=domain.get("url"),
        ))

        for control in domain.get("controls", []):
            ctrl_id = control["id"]
            ctrl_node_id = f"aiuc_1:{ctrl_id}"
            is_retired = "RETIRED" in (control.get("description") or "").upper()

            add_node(nodes, make_node(
                node_id=ctrl_node_id,
                framework="aiuc_1",
                local_id=ctrl_id,
                name=control.get("title", ctrl_id),
                entry_type="control",
                parent_node_id=dom_node_id,
                domain=domain.get("name"),
                description=control.get("description"),
                function_class=None,  # Will be set in Task 2
                classification=control.get("classification"),
                control_type=control.get("type"),
                frequency=control.get("frequency"),
                applicable_capabilities=control.get("applicable_capabilities"),
                keywords=control.get("keywords"),
                url=control.get("url"),
                retired=is_retired,
            ))

            # PARENT edge: domain -> control
            add_edge(edges, make_edge(
                source_node_id=dom_node_id,
                target_node_id=ctrl_node_id,
                rationale_code="PARENT",
                rationale_label="Parent-child hierarchy",
                confidence="authoritative",
                provenance="aiuc-1-standard.json",
            ))

            # Activities
            for activity in control.get("activities", []):
                act_id = activity["id"]
                act_node_id = f"aiuc_1:{act_id}"
                add_node(nodes, make_node(
                    node_id=act_node_id,
                    framework="aiuc_1",
                    local_id=act_id,
                    name=activity.get("description", act_id)[:120],
                    entry_type="activity",
                    parent_node_id=ctrl_node_id,
                    domain=domain.get("name"),
                    description=activity.get("description"),
                ))

                # PARENT edge: control -> activity
                add_edge(edges, make_edge(
                    source_node_id=ctrl_node_id,
                    target_node_id=act_node_id,
                    rationale_code="PARENT",
                    rationale_label="Parent-child hierarchy",
                    confidence="authoritative",
                    provenance="aiuc-1-standard.json",
                ))

            # Framework references -> edges
            for fw_key, ref_ids in control.get("framework_references", {}).items():
                target_fw = AIUC1_FWREF_MAP.get(fw_key)
                if not target_fw or not ref_ids:
                    continue
                for ref_id in ref_ids:
                    if not ref_id:
                        continue
                    # Normalize IDs
                    if target_fw == "mitre_atlas":
                        norm_id = normalize_atlas_id(ref_id)
                    elif target_fw == "nist_rmf":
                        norm_id = normalize_nist_id(ref_id)
                    else:
                        norm_id = sanitize_local_id(ref_id.strip())

                    target_node_id = f"{target_fw}:{norm_id}"
                    add_edge(edges, make_edge(
                        source_node_id=ctrl_node_id,
                        target_node_id=target_node_id,
                        rationale_code=None,
                        confidence="authoritative",
                        provenance="aiuc-1-standard.json",
                    ))

    log.info("Task 1: AIUC-1 standard parsed. Nodes=%d, Edges=%d", len(nodes), len(edges))


# ---------------------------------------------------------------------------
# Task 2: Parse AIUC-1 Agentic Top 10 mapping v2 JSON
# ---------------------------------------------------------------------------

def parse_aiuc1_agentic_mapping_v2(nodes, edges, warnings):
    """Parse v2 mapping: edges from source_to_owasp, OWASP Agentic nodes, function_class updates."""
    path = os.path.join(FRAMEWORKS_DIR, "aiuc-1", "aiuc_owasp_agentic_top10_mapping_v2.json")
    data = load_json(path)
    if not data:
        warnings.append("AIUC-1 agentic mapping v2 JSON not found or invalid")
        return

    ctl = data.get("control_level", {})

    # Extract edges from source_to_owasp and update function_class
    for entry in ctl.get("source_to_owasp", []):
        ctrl_id = entry["control_id"]
        ctrl_node_id = f"aiuc_1:{ctrl_id}"
        fc = entry.get("function_class")

        # Update function_class on the AIUC-1 control node
        if fc and ctrl_node_id in nodes:
            nodes[ctrl_node_id]["function_class"] = fc

        for mapping in entry.get("mappings", []):
            owasp_id = mapping["owasp_id"]
            target_node_id = f"owasp_agentic:{owasp_id}"
            add_edge(edges, make_edge(
                source_node_id=ctrl_node_id,
                target_node_id=target_node_id,
                rationale_code=mapping.get("rationale_code"),
                rationale_label=mapping.get("rationale_label"),
                relevance=mapping.get("relevance"),
                confidence="expert",
                provenance="aiuc_owasp_agentic_top10_mapping_v2.json",
            ))

    # Create OWASP Agentic Top 10 nodes from owasp_to_source
    for entry in ctl.get("owasp_to_source", []):
        owasp_id = entry["owasp_id"]
        add_node(nodes, make_node(
            node_id=f"owasp_agentic:{owasp_id}",
            framework="owasp_agentic",
            local_id=owasp_id,
            name=entry.get("owasp_title", owasp_id),
            entry_type="risk",
        ))

    log.info("Task 2: AIUC-1 agentic mapping v2 parsed. Nodes=%d, Edges=%d", len(nodes), len(edges))


# ---------------------------------------------------------------------------
# Task 3: Parse AIUC-1 markdown crosswalks
# ---------------------------------------------------------------------------

def _parse_owasp_llm_crosswalk(text, nodes, edges, warnings):
    """Parse owasp-top-10-crosswalk.md: ## LLM{NN}:25 headings + bullet items."""
    prov = "owasp-top-10-crosswalk.md"
    # Pattern: ## LLM01:25 - Title
    sections = re.split(r"^## (LLM\d{2}):25\s*[-–]\s*(.+)$", text, flags=re.MULTILINE)
    # sections[0] is preamble, then groups of (id, title, body)
    for i in range(1, len(sections) - 2, 3):
        llm_id = sections[i].strip()
        llm_title = sections[i + 1].strip()
        body = sections[i + 2]

        target_nid = f"owasp_llm:{llm_id}"
        add_node(nodes, make_node(
            node_id=target_nid,
            framework="owasp_llm",
            local_id=llm_id,
            name=llm_title,
            entry_type="risk",
        ))

        # Extract AIUC-1 control references: - B001: Title or - A003: Title
        for m in re.finditer(r"-\s+([A-F]\d{3}):\s+(.+)", body):
            aiuc_id = m.group(1)
            src_nid = f"aiuc_1:{aiuc_id}"
            add_edge(edges, make_edge(
                source_node_id=src_nid,
                target_node_id=target_nid,
                rationale_code=None,
                confidence="unvalidated",
                provenance=prov,
            ))


def _parse_mitre_atlas_crosswalk(text, nodes, edges, warnings):
    """Parse mitre-atlas-crosswalk.md: table rows with | AML-MXXXX | ... | AIUC mapping |."""
    prov = "mitre-atlas-crosswalk.md"
    # Table rows: | AML-M0000 | name | description | AIUC mapping |
    for m in re.finditer(
        r"\|\s*(AML-M\d{4})\s*\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|",
        text,
    ):
        atlas_raw = m.group(1).strip()
        atlas_name = m.group(2).strip()
        aiuc_text = m.group(4).strip()

        atlas_id = normalize_atlas_id(atlas_raw)
        target_nid = f"mitre_atlas:{atlas_id}"
        add_node(nodes, make_node(
            node_id=target_nid,
            framework="mitre_atlas",
            local_id=atlas_id,
            name=atlas_name,
            entry_type="mitigation",
        ))

        if "No directly mapped" in aiuc_text or not aiuc_text:
            continue

        # Extract AIUC-1 IDs: B001, C002, etc.
        for ctrl_m in re.finditer(r"([A-F]\d{3})", aiuc_text):
            aiuc_id = ctrl_m.group(1)
            src_nid = f"aiuc_1:{aiuc_id}"
            add_edge(edges, make_edge(
                source_node_id=src_nid,
                target_node_id=target_nid,
                rationale_code=None,
                confidence="unvalidated",
                provenance=prov,
            ))


def _parse_nist_rmf_crosswalk(text, nodes, edges, warnings):
    """Parse nist-ai-rmf-crosswalk.md: table rows with | **GOVERN 1.1** | desc | reqs |."""
    prov = "nist-ai-rmf-crosswalk.md"
    # Match table rows: | **GOVERN 1.1** | description | AIUC reqs |
    pattern = r"\|\s*\*?\*?(GOVERN|MAP|MEASURE|MANAGE)\s+(\d+\.\d+)\*?\*?\s*\|\s*([^|]+)\|\s*([^|]+)\|"
    for m in re.finditer(pattern, text):
        func = m.group(1).strip()
        num = m.group(2).strip()
        nist_id = f"{func}-{num}"
        nist_desc = m.group(3).strip()
        aiuc_text = m.group(4).strip()

        target_nid = f"nist_rmf:{nist_id}"
        add_node(nodes, make_node(
            node_id=target_nid,
            framework="nist_rmf",
            local_id=nist_id,
            name=nist_desc[:120] if nist_desc else nist_id,
            entry_type="subcategory",
        ))

        if "No directly mapped" in aiuc_text or not aiuc_text:
            continue

        for ctrl_m in re.finditer(r"([A-F]\d{3})", aiuc_text):
            aiuc_id = ctrl_m.group(1)
            add_edge(edges, make_edge(
                source_node_id=f"aiuc_1:{aiuc_id}",
                target_node_id=target_nid,
                rationale_code=None,
                confidence="unvalidated",
                provenance=prov,
            ))


def _parse_csa_aicm_crosswalk(text, nodes, edges, warnings):
    """Parse csa-aicm-crosswalk.md: table rows with | CSA-ID | name | AIUC reqs | gap |."""
    prov = "csa-aicm-crosswalk.md"
    # Match: | AIS-01 | name | E004, E007, ... | gap |
    pattern = r"\|\s*([A-Z&]+[-]\d{2})\s*\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]*)\|"
    for m in re.finditer(pattern, text):
        csa_id_raw = m.group(1).strip()
        csa_id = sanitize_local_id(csa_id_raw)
        csa_name = m.group(2).strip()
        aiuc_text = m.group(3).strip()

        target_nid = f"csa_aicm:{csa_id}"
        add_node(nodes, make_node(
            node_id=target_nid,
            framework="csa_aicm",
            local_id=csa_id,
            name=csa_name,
            entry_type="control",
        ))

        if "None" in aiuc_text or not aiuc_text.strip():
            continue

        for ctrl_m in re.finditer(r"([A-F]\d{3})", aiuc_text):
            aiuc_id = ctrl_m.group(1)
            add_edge(edges, make_edge(
                source_node_id=f"aiuc_1:{aiuc_id}",
                target_node_id=target_nid,
                rationale_code=None,
                confidence="unvalidated",
                provenance=prov,
            ))


def _parse_eu_ai_act_crosswalk(text, nodes, edges, warnings):
    """Parse www_aiuc-1_com_crosswalks_eu-ai-act.md: Article headings."""
    prov = "www_aiuc-1_com_crosswalks_eu-ai-act.md"
    # The EU AI Act crosswalk is prose, not structured.
    # Extract Article references mentioned in the text
    # Articles mentioned: Article 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, etc.
    # We create stub nodes for each Article mentioned
    articles = set()
    for m in re.finditer(r"Article\s+(\d+)", text):
        articles.add(m.group(1))

    for art_num in sorted(articles):
        art_id = f"Article-{art_num}"
        target_nid = f"eu_gpai_cop:{art_id}"
        add_node(nodes, make_node(
            node_id=target_nid,
            framework="eu_gpai_cop",
            local_id=art_id,
            name=f"EU AI Act Article {art_num}",
            entry_type="requirement",
        ))
    # Note: The EU AI Act crosswalk is prose and doesn't have clear AIUC-1 control
    # mappings in a structured format. The edges from AIUC-1 to EU AI Act articles
    # are already captured via framework_references in Task 1.


def parse_aiuc1_markdown_crosswalks(nodes, edges, warnings):
    """Parse all 5 markdown crosswalk files."""
    aiuc_dir = os.path.join(FRAMEWORKS_DIR, "aiuc-1")

    parsers = [
        ("owasp-top-10-crosswalk.md", _parse_owasp_llm_crosswalk),
        ("mitre-atlas-crosswalk.md", _parse_mitre_atlas_crosswalk),
        ("nist-ai-rmf-crosswalk.md", _parse_nist_rmf_crosswalk),
        ("csa-aicm-crosswalk.md", _parse_csa_aicm_crosswalk),
        ("www_aiuc-1_com_crosswalks_eu-ai-act.md", _parse_eu_ai_act_crosswalk),
    ]

    for filename, parser in parsers:
        text = read_text(os.path.join(aiuc_dir, filename))
        if text:
            parser(text, nodes, edges, warnings)
        else:
            warnings.append(f"Markdown crosswalk not found: {filename}")

    log.info("Task 3: Markdown crosswalks parsed. Nodes=%d, Edges=%d", len(nodes), len(edges))


# ---------------------------------------------------------------------------
# Task 4: Parse MITRE ATLAS JSON
# ---------------------------------------------------------------------------

def parse_mitre_atlas(nodes, edges, warnings):
    """Parse ATLAS_compiled.json for tactics, techniques, mitigations."""
    # Prefer compiled JSON (resolved template refs)
    path = os.path.join(FRAMEWORKS_DIR, "mitre-atlas", "ATLAS_compiled.json")
    data = load_json(path)
    if not data:
        warnings.append("MITRE ATLAS compiled JSON not found")
        return

    matrix = data.get("matrices", [{}])[0] if data.get("matrices") else {}
    if not matrix:
        warnings.append("MITRE ATLAS matrix not found in compiled JSON")
        return

    # Tactics
    for tactic in matrix.get("tactics", []):
        tid = tactic["id"]
        add_node(nodes, make_node(
            node_id=f"mitre_atlas:{tid}",
            framework="mitre_atlas",
            local_id=tid,
            name=tactic.get("name", tid),
            entry_type="tactic",
            description=tactic.get("description"),
        ))

    # Techniques (and subtechniques)
    for tech in matrix.get("techniques", []):
        tid = tech["id"]
        parent_tech = tech.get("subtechnique-of")
        parent_nid = f"mitre_atlas:{parent_tech}" if parent_tech else None

        add_node(nodes, make_node(
            node_id=f"mitre_atlas:{tid}",
            framework="mitre_atlas",
            local_id=tid,
            name=tech.get("name", tid),
            entry_type="technique",
            parent_node_id=parent_nid,
            description=tech.get("description"),
        ))

        # Subtechnique -> parent technique PARENT edge
        if parent_tech:
            add_edge(edges, make_edge(
                source_node_id=f"mitre_atlas:{parent_tech}",
                target_node_id=f"mitre_atlas:{tid}",
                rationale_code="PARENT",
                rationale_label="Parent-child hierarchy",
                confidence="authoritative",
                provenance="ATLAS_compiled.json",
            ))

        # Technique -> tactic edges
        for tactic_id in tech.get("tactics", []):
            if isinstance(tactic_id, str):
                add_edge(edges, make_edge(
                    source_node_id=f"mitre_atlas:{tactic_id}",
                    target_node_id=f"mitre_atlas:{tid}",
                    rationale_code="PARENT",
                    rationale_label="Tactic contains technique",
                    confidence="authoritative",
                    provenance="ATLAS_compiled.json",
                ))

    # Mitigations
    for mit in matrix.get("mitigations", []):
        mid = mit["id"]
        add_node(nodes, make_node(
            node_id=f"mitre_atlas:{mid}",
            framework="mitre_atlas",
            local_id=mid,
            name=mit.get("name", mid),
            entry_type="mitigation",
            description=mit.get("description"),
        ))

        # Mitigation -> technique edges (PREV: mitigations prevent techniques)
        for tech_ref in mit.get("techniques", []):
            tech_id = tech_ref.get("id") if isinstance(tech_ref, dict) else tech_ref
            if tech_id and isinstance(tech_id, str):
                add_edge(edges, make_edge(
                    source_node_id=f"mitre_atlas:{mid}",
                    target_node_id=f"mitre_atlas:{tech_id}",
                    rationale_code="PREV",
                    rationale_label="Mitigates technique",
                    confidence="authoritative",
                    provenance="ATLAS_compiled.json",
                ))

    log.info("Task 4: MITRE ATLAS parsed. Nodes=%d, Edges=%d", len(nodes), len(edges))


# ---------------------------------------------------------------------------
# Task 5: Parse CoSAI Risk Map YAML
# ---------------------------------------------------------------------------

def parse_cosai_risk_map(nodes, edges, warnings):
    """Parse CoSAI Risk Map YAML files: risks, controls, and cross-framework mappings."""
    if yaml is None:
        warnings.append("pyyaml not installed, skipping CoSAI")
        return

    cosai_dir = os.path.join(FRAMEWORKS_DIR, "cosai", "risk-map")

    # Parse controls
    controls_data = load_yaml(os.path.join(cosai_dir, "controls.yaml"))
    if controls_data:
        for cat in controls_data.get("categories", []):
            cat_id = cat["id"]
            add_node(nodes, make_node(
                node_id=f"cosai_rm:{cat_id}",
                framework="cosai_rm",
                local_id=cat_id,
                name=cat.get("title", cat_id),
                entry_type="function",
            ))

        for ctrl in controls_data.get("controls", []):
            cid = ctrl["id"]
            cat = ctrl.get("category")
            parent_nid = f"cosai_rm:{cat}" if cat else None
            desc_parts = ctrl.get("description", [])
            desc = " ".join(desc_parts) if isinstance(desc_parts, list) else str(desc_parts)

            add_node(nodes, make_node(
                node_id=f"cosai_rm:{cid}",
                framework="cosai_rm",
                local_id=cid,
                name=ctrl.get("title", cid),
                entry_type="control",
                parent_node_id=parent_nid,
                description=desc[:500] if desc else None,
            ))

            if parent_nid:
                add_edge(edges, make_edge(
                    source_node_id=parent_nid,
                    target_node_id=f"cosai_rm:{cid}",
                    rationale_code="PARENT",
                    rationale_label="Parent-child hierarchy",
                    confidence="authoritative",
                    provenance="controls.yaml",
                ))

    # Parse risks and their framework mappings
    risks_data = load_yaml(os.path.join(cosai_dir, "risks.yaml"))
    if risks_data:
        for risk in risks_data.get("risks", []):
            rid = risk["id"]
            short_desc = risk.get("shortDescription", [])
            desc = " ".join(short_desc) if isinstance(short_desc, list) else str(short_desc)

            add_node(nodes, make_node(
                node_id=f"cosai_rm:{rid}",
                framework="cosai_rm",
                local_id=rid,
                name=risk.get("title", rid),
                entry_type="risk",
                description=desc[:500] if desc else None,
            ))

            # Risk -> control edges (internal)
            for ctrl_id in risk.get("controls", []):
                add_edge(edges, make_edge(
                    source_node_id=f"cosai_rm:{rid}",
                    target_node_id=f"cosai_rm:{ctrl_id}",
                    rationale_code=None,
                    rationale_label="Risk mitigated by control",
                    confidence="authoritative",
                    provenance="risks.yaml",
                ))

            # Cross-framework mappings
            mappings = risk.get("mappings", {})
            if isinstance(mappings, dict):
                # mitre-atlas -> mitre_atlas
                for atlas_id in mappings.get("mitre-atlas", []):
                    add_edge(edges, make_edge(
                        source_node_id=f"cosai_rm:{rid}",
                        target_node_id=f"mitre_atlas:{atlas_id}",
                        rationale_code=None,
                        rationale_label="CoSAI risk maps to ATLAS technique",
                        confidence="authoritative",
                        provenance="risks.yaml",
                    ))

                # owasp-top10-llm -> owasp_llm
                for llm_id in mappings.get("owasp-top10-llm", []):
                    add_edge(edges, make_edge(
                        source_node_id=f"cosai_rm:{rid}",
                        target_node_id=f"owasp_llm:{llm_id}",
                        rationale_code=None,
                        rationale_label="CoSAI risk maps to OWASP LLM entry",
                        confidence="authoritative",
                        provenance="risks.yaml",
                    ))

                # nist-ai-rmf entries (if present)
                for nist_id in mappings.get("nist-ai-rmf", []):
                    add_edge(edges, make_edge(
                        source_node_id=f"cosai_rm:{rid}",
                        target_node_id=f"nist_rmf:{nist_id}",
                        rationale_code=None,
                        rationale_label="CoSAI risk maps to NIST RMF",
                        confidence="authoritative",
                        provenance="risks.yaml",
                    ))

    log.info("Task 5: CoSAI Risk Map parsed. Nodes=%d, Edges=%d", len(nodes), len(edges))


# ---------------------------------------------------------------------------
# Task 6: Parse CSA AICM JSON
# ---------------------------------------------------------------------------

def parse_csa_aicm(nodes, edges, warnings):
    """Parse csa_aicm.json for domains and controls."""
    path = os.path.join(FRAMEWORKS_DIR, "csa-aicm", "csa_aicm.json")
    data = load_json(path)
    if not data:
        warnings.append("CSA AICM JSON not found or invalid")
        return

    # Create domain nodes
    for dom in data.get("domains", []):
        dom_name = dom["name"]
        # Domain ID from first control's prefix, or sanitize name
        dom_ids = dom.get("control_ids", [])
        if dom_ids:
            prefix = sanitize_local_id(dom_ids[0].rsplit("-", 1)[0])
        else:
            prefix = sanitize_local_id(dom_name[:20])
        dom_nid = f"csa_aicm:domain_{prefix}"

        add_node(nodes, make_node(
            node_id=dom_nid,
            framework="csa_aicm",
            local_id=f"domain_{prefix}",
            name=dom_name,
            entry_type="function",
        ))

    # Create control nodes with parent linkage
    domain_prefix_map = {}
    for dom in data.get("domains", []):
        dom_ids = dom.get("control_ids", [])
        if dom_ids:
            prefix = sanitize_local_id(dom_ids[0].rsplit("-", 1)[0])
            dom_nid = f"csa_aicm:domain_{prefix}"
            for cid in dom_ids:
                domain_prefix_map[cid] = dom_nid

    for ctrl in data.get("controls", []):
        cid_raw = ctrl["id"]
        cid = sanitize_local_id(cid_raw)
        parent_nid = domain_prefix_map.get(cid_raw)

        add_node(nodes, make_node(
            node_id=f"csa_aicm:{cid}",
            framework="csa_aicm",
            local_id=cid,
            name=ctrl.get("title", cid),
            entry_type="control",
            parent_node_id=parent_nid,
            domain=ctrl.get("domain_full", ctrl.get("domain")),
            description=ctrl.get("specification"),
        ))

        if parent_nid:
            add_edge(edges, make_edge(
                source_node_id=parent_nid,
                target_node_id=f"csa_aicm:{cid}",
                rationale_code="PARENT",
                rationale_label="Parent-child hierarchy",
                confidence="authoritative",
                provenance="csa_aicm.json",
            ))

    log.info("Task 6: CSA AICM parsed. Nodes=%d, Edges=%d", len(nodes), len(edges))


# ---------------------------------------------------------------------------
# Task 7: Create stub nodes for remaining frameworks
# ---------------------------------------------------------------------------

def _create_owasp_llm_nodes(nodes, warnings):
    """Create OWASP LLM Top 10 nodes if they don't exist."""
    llm_entries = {
        "LLM01": "Prompt Injection",
        "LLM02": "Sensitive Information Disclosure",
        "LLM03": "Supply Chain",
        "LLM04": "Data and Model Poisoning",
        "LLM05": "Improper Output Handling",
        "LLM06": "Excessive Agency",
        "LLM07": "System Prompt Leakage",
        "LLM08": "Vector and Embedding Weaknesses",
        "LLM09": "Misinformation",
        "LLM10": "Unbounded Consumption",
    }
    for lid, name in llm_entries.items():
        nid = f"owasp_llm:{lid}"
        if nid not in nodes:
            add_node(nodes, make_node(
                node_id=nid, framework="owasp_llm", local_id=lid,
                name=name, entry_type="risk",
            ))


def _create_owasp_agentic_nodes(nodes, warnings):
    """Ensure OWASP Agentic Top 10 nodes exist (should already from Task 2)."""
    agentic_entries = {
        "ASI01": "Agent Goal Hijack",
        "ASI02": "Tool Misuse and Exploitation",
        "ASI03": "Identity and Privilege Abuse",
        "ASI04": "Agentic Supply Chain Vulnerabilities",
        "ASI05": "Unexpected Code Execution (RCE)",
        "ASI06": "Memory & Context Poisoning",
        "ASI07": "Insecure Inter-Agent Communication",
        "ASI08": "Cascading Failures",
        "ASI09": "Human-Agent Trust Exploitation",
        "ASI10": "Rogue Agents",
    }
    for lid, name in agentic_entries.items():
        nid = f"owasp_agentic:{lid}"
        if nid not in nodes:
            add_node(nodes, make_node(
                node_id=nid, framework="owasp_agentic", local_id=lid,
                name=name, entry_type="risk",
            ))


def _create_nist_rmf_nodes(nodes, warnings):
    """Create NIST AI RMF function and subcategory nodes."""
    functions = {
        "GOVERN": "Cultivate and enable organizational culture of risk management",
        "MAP": "Contextualize risks related to an AI system",
        "MEASURE": "Employ quantitative and qualitative tools to analyze and assess AI risks",
        "MANAGE": "Allocate resources to mapped and measured risks",
    }
    for func, desc in functions.items():
        nid = f"nist_rmf:{func}"
        if nid not in nodes:
            add_node(nodes, make_node(
                node_id=nid, framework="nist_rmf", local_id=func,
                name=func, entry_type="function", description=desc,
            ))

    # Subcategories (from the NIST RMF markdown and crosswalk)
    subcats = [
        "GOVERN-1.1", "GOVERN-1.2", "GOVERN-1.3", "GOVERN-1.4", "GOVERN-1.5",
        "GOVERN-1.6", "GOVERN-1.7", "GOVERN-2.1", "GOVERN-2.2", "GOVERN-2.3",
        "GOVERN-3.1", "GOVERN-3.2", "GOVERN-4.1", "GOVERN-4.2", "GOVERN-4.3",
        "GOVERN-5.1", "GOVERN-5.2", "GOVERN-6.1", "GOVERN-6.2",
        "MAP-1.1", "MAP-1.2", "MAP-1.3", "MAP-1.4", "MAP-1.5", "MAP-1.6",
        "MAP-2.1", "MAP-2.2", "MAP-2.3", "MAP-3.1", "MAP-3.2", "MAP-3.3",
        "MAP-3.4", "MAP-3.5", "MAP-4.1", "MAP-4.2", "MAP-5.1", "MAP-5.2",
        "MEASURE-1.1", "MEASURE-1.2", "MEASURE-1.3",
        "MEASURE-2.1", "MEASURE-2.2", "MEASURE-2.3", "MEASURE-2.4", "MEASURE-2.5",
        "MEASURE-2.6", "MEASURE-2.7", "MEASURE-2.8", "MEASURE-2.9", "MEASURE-2.10",
        "MEASURE-2.11", "MEASURE-2.12", "MEASURE-2.13",
        "MEASURE-3.1", "MEASURE-3.2", "MEASURE-3.3",
        "MEASURE-4.1", "MEASURE-4.2", "MEASURE-4.3",
        "MANAGE-1.1", "MANAGE-1.2", "MANAGE-1.3", "MANAGE-1.4",
        "MANAGE-2.1", "MANAGE-2.2", "MANAGE-2.3", "MANAGE-2.4",
        "MANAGE-3.1", "MANAGE-3.2", "MANAGE-4.1", "MANAGE-4.2", "MANAGE-4.3",
    ]
    for sc in subcats:
        nid = f"nist_rmf:{sc}"
        func = sc.split("-")[0]
        parent_nid = f"nist_rmf:{func}"
        if nid not in nodes:
            add_node(nodes, make_node(
                node_id=nid, framework="nist_rmf", local_id=sc,
                name=sc.replace("-", " ", 1), entry_type="subcategory", parent_node_id=parent_nid,
            ))
            add_edge(edges_placeholder, make_edge(
                source_node_id=parent_nid,
                target_node_id=nid,
                rationale_code="PARENT",
                rationale_label="Parent-child hierarchy",
                confidence="authoritative",
                provenance="nist_ai_rmf_1.0.md",
            ))


def _create_eu_gpai_cop_nodes(nodes, edges, warnings):
    """Create EU GPAI Code of Practice commitment and measure nodes."""
    path = os.path.join(FRAMEWORKS_DIR, "eu-gpai-code-of-practice", "gpai_cop_safety_and_security.md")
    text = read_text(path)
    if not text:
        return

    # Extract Commitment headings: ## Commitment N Title
    for m in re.finditer(r"^## Commitment (\d+)\s+(.+)$", text, re.MULTILINE):
        cnum = m.group(1)
        title = m.group(2).strip()
        nid = f"eu_gpai_cop:Commitment_{cnum}"
        add_node(nodes, make_node(
            node_id=nid, framework="eu_gpai_cop", local_id=f"Commitment_{cnum}",
            name=f"Commitment {cnum}: {title}", entry_type="commitment",
        ))

    # Extract Measure headings: ### Measure N.M Title
    for m in re.finditer(r"^### Measure (\d+\.\d+)\s+(.+)$", text, re.MULTILINE):
        mnum = m.group(1)
        title = m.group(2).strip()
        cnum = mnum.split(".")[0]
        parent_nid = f"eu_gpai_cop:Commitment_{cnum}"
        nid = f"eu_gpai_cop:Measure_{mnum}"
        add_node(nodes, make_node(
            node_id=nid, framework="eu_gpai_cop", local_id=f"Measure_{mnum}",
            name=f"Measure {mnum}: {title}", entry_type="measure",
            parent_node_id=parent_nid,
        ))
        add_edge(edges, make_edge(
            source_node_id=parent_nid,
            target_node_id=nid,
            rationale_code="PARENT",
            rationale_label="Parent-child hierarchy",
            confidence="authoritative",
            provenance="gpai_cop_safety_and_security.md",
        ))


def create_stub_nodes(nodes, edges, warnings):
    """Task 7: Create stub nodes for frameworks with only markdown sources."""
    _create_owasp_llm_nodes(nodes, warnings)
    _create_owasp_agentic_nodes(nodes, warnings)

    # NIST RMF needs edges dict passed through - use a workaround
    global edges_placeholder
    edges_placeholder = edges
    _create_nist_rmf_nodes(nodes, warnings)

    _create_eu_gpai_cop_nodes(nodes, edges, warnings)

    # NIST AI 600-1: Skip for now - complex prose document
    # OWASP AI Exchange: Skip for now
    warnings.append("TODO: NIST AI 600-1 node extraction from prose markdown")
    warnings.append("TODO: OWASP AI Exchange node extraction skipped")

    log.info("Task 7: Stub nodes created. Nodes=%d, Edges=%d", len(nodes), len(edges))


# ---------------------------------------------------------------------------
# Task 8: Deduplicate, validate, and write output
# ---------------------------------------------------------------------------

def validate_and_fix(nodes, edges, warnings):
    """Ensure referential integrity: create stub nodes for missing edge targets."""
    stub_nodes = []
    all_node_ids = set(nodes.keys())

    # Map framework to a reasonable default entry_type for stubs
    fw_default_type = {
        "aiuc_1": "control", "owasp_llm": "risk", "owasp_agentic": "risk",
        "mitre_atlas": "technique", "nist_rmf": "subcategory",
        "csa_aicm": "control", "cosai_rm": "control",
        "eu_gpai_cop": "requirement", "nist_600_1": "control",
    }

    for key, edge in list(edges.items()):
        for field in ("source_node_id", "target_node_id"):
            nid = edge[field]
            if nid not in all_node_ids:
                parts = nid.split(":", 1)
                fw = parts[0] if len(parts) > 1 else "aiuc_1"
                lid = parts[1] if len(parts) > 1 else nid
                etype = fw_default_type.get(fw, "control")
                stub = make_node(
                    node_id=nid, framework=fw, local_id=lid,
                    name=lid, entry_type=etype,
                )
                nodes[nid] = stub
                all_node_ids.add(nid)
                stub_nodes.append(nid)

    if stub_nodes:
        log.info("Created %d stub nodes for missing edge targets", len(stub_nodes))

    return stub_nodes


def compute_stats(nodes, edges, stub_nodes, warnings):
    """Compute graph_stats.json data."""
    fw_stats = defaultdict(lambda: {"nodes": 0, "outbound_edges": 0, "inbound_edges": 0})
    conf_dist = defaultdict(int)
    rat_dist = defaultdict(int)
    cross_fw = defaultdict(int)

    for n in nodes.values():
        fw_stats[n["framework"]]["nodes"] += 1

    node_fw = {n["node_id"]: n["framework"] for n in nodes.values()}

    for e in edges.values():
        src_fw = node_fw.get(e["source_node_id"], "unknown")
        tgt_fw = node_fw.get(e["target_node_id"], "unknown")
        fw_stats[src_fw]["outbound_edges"] += 1
        fw_stats[tgt_fw]["inbound_edges"] += 1
        conf_dist[e.get("confidence", "unvalidated")] += 1
        rc = e.get("rationale_code")
        rat_dist[rc if rc else "null"] += 1
        if src_fw != tgt_fw:
            pair = f"{src_fw} → {tgt_fw}"
            cross_fw[pair] += 1

    # Orphan nodes (zero edges)
    nodes_with_edges = set()
    for e in edges.values():
        nodes_with_edges.add(e["source_node_id"])
        nodes_with_edges.add(e["target_node_id"])
    orphans = [nid for nid in nodes if nid not in nodes_with_edges]

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "node_count": len(nodes),
        "edge_count": len(edges),
        "frameworks": dict(fw_stats),
        "edge_confidence_distribution": dict(conf_dist),
        "rationale_distribution": dict(rat_dist),
        "cross_framework_pairs": dict(sorted(cross_fw.items(), key=lambda x: -x[1])),
        "stub_nodes": sorted(stub_nodes),
        "orphan_nodes": sorted(orphans),
        "validation_warnings": warnings,
    }


def write_output(nodes, edges, warnings):
    """Write nodes.json, edges.json, graph_stats.json."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    stub_nodes = validate_and_fix(nodes, edges, warnings)

    # Sort and write nodes
    nodes_list = sorted(nodes.values(), key=lambda n: n["node_id"])
    with open(os.path.join(OUTPUT_DIR, "nodes.json"), "w", encoding="utf-8") as f:
        json.dump(nodes_list, f, indent=2, ensure_ascii=False)

    # Regenerate edge_ids after dedup and sort
    edges_list = sorted(edges.values(), key=lambda e: (e["source_node_id"], e["target_node_id"]))
    with open(os.path.join(OUTPUT_DIR, "edges.json"), "w", encoding="utf-8") as f:
        json.dump(edges_list, f, indent=2, ensure_ascii=False)

    # Stats
    stats = compute_stats(nodes, edges, stub_nodes, warnings)
    with open(os.path.join(OUTPUT_DIR, "graph_stats.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)

    log.info("Output written: %d nodes, %d edges", len(nodes_list), len(edges_list))
    log.info("Stats written to graph_stats.json")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

# Module-level placeholder for edges (used by _create_nist_rmf_nodes)
edges_placeholder = {}


def main():
    nodes = {}  # node_id -> node dict
    edges = {}  # (src, tgt, rationale_code) -> edge dict
    warnings = []

    log.info("Building crosswalk graph from %s", FRAMEWORKS_DIR)

    # Task 1: AIUC-1 standard
    parse_aiuc1_standard(nodes, edges, warnings)

    # Task 2: AIUC-1 OWASP Agentic mapping v2
    parse_aiuc1_agentic_mapping_v2(nodes, edges, warnings)

    # Task 3: Markdown crosswalks
    parse_aiuc1_markdown_crosswalks(nodes, edges, warnings)

    # Task 4: MITRE ATLAS
    parse_mitre_atlas(nodes, edges, warnings)

    # Task 5: CoSAI Risk Map
    parse_cosai_risk_map(nodes, edges, warnings)

    # Task 6: CSA AICM
    parse_csa_aicm(nodes, edges, warnings)

    # Task 7: Stub nodes for remaining frameworks
    create_stub_nodes(nodes, edges, warnings)

    # Task 8: Write output (includes dedup and validation)
    write_output(nodes, edges, warnings)

    return 0


if __name__ == "__main__":
    sys.exit(main())
