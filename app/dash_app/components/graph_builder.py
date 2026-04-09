"""Build cytoscape graph elements from mapping data.

Creates:
  - Framework parent (compound) nodes -- large, colored by framework
  - Control child nodes -- small, clustered under parent
  - Mapping edges -- colored by tier, solid (expert) or dashed (ML)
"""
from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd

from app.dash_app.data.frameworks import FRAMEWORK_COLORS, FRAMEWORK_LABELS

# Tier -> CSS class mapping
_TIER_MAP = {
    "Foundational": "equivalent",
    "Expanded": "partial",
    "Direct": "equivalent",
    "Related": "related",
    "Tangential": "partial",
    "equivalent": "equivalent",
    "related": "related",
    "partial": "partial",
    "unrelated": "unrelated",
}


def build_cytoscape_elements(
    df: pd.DataFrame,
    show_controls: bool = True,
) -> List[Dict[str, Any]]:
    """Convert mapping DataFrame to cytoscape elements."""
    elements: List[Dict[str, Any]] = []
    seen_nodes: set = set()
    seen_frameworks: set = set()

    for _, row in df.iterrows():
        src_fw = row.get("source_framework", "")
        src_id = row.get("source_id", "")
        src_node_id = f"{src_fw}:{src_id}"
        tgt_node_id = row.get("target_node_id", "")
        tgt_fw = row.get("target_framework", "")
        tgt_name = row.get("target_control_name", tgt_node_id)
        tier = row.get("tier", "")
        data_source = row.get("data_source", "expert")

        # Framework parent nodes
        for fw_id in [src_fw, tgt_fw]:
            if fw_id and fw_id not in seen_frameworks:
                seen_frameworks.add(fw_id)
                elements.append({
                    "data": {
                        "id": f"fw:{fw_id}",
                        "label": FRAMEWORK_LABELS.get(fw_id, fw_id),
                        "type": "framework",
                    },
                    "classes": "framework-node",
                    "style": {
                        "background-color": FRAMEWORK_COLORS.get(fw_id, "#888"),
                    },
                })

        if show_controls:
            # Source control node
            if src_node_id and src_node_id not in seen_nodes:
                seen_nodes.add(src_node_id)
                elements.append({
                    "data": {
                        "id": src_node_id,
                        "label": src_id,
                        "parent": f"fw:{src_fw}",
                        "type": "control",
                        "framework": src_fw,
                    },
                    "classes": "control-node",
                })

            # Target control node
            if tgt_node_id and tgt_node_id not in seen_nodes:
                seen_nodes.add(tgt_node_id)
                tgt_label = tgt_node_id.split(":")[-1] if ":" in tgt_node_id else tgt_node_id
                elements.append({
                    "data": {
                        "id": tgt_node_id,
                        "label": tgt_label,
                        "parent": f"fw:{tgt_fw}",
                        "type": "control",
                        "framework": tgt_fw,
                        "description": tgt_name,
                    },
                    "classes": "control-node",
                })

        # Edge
        tier_class = _TIER_MAP.get(tier, "related")
        source_class = "expert" if data_source == "expert" else "ml-predicted"
        confidence = row.get("confidence", 1.0 if data_source == "expert" else 0.5)

        if src_node_id and tgt_node_id:
            edge_source = src_node_id if show_controls else f"fw:{src_fw}"
            edge_target = tgt_node_id if show_controls else f"fw:{tgt_fw}"
            elements.append({
                "data": {
                    "source": edge_source,
                    "target": edge_target,
                    "tier": tier_class,
                    "confidence": confidence,
                    "data_source": data_source,
                },
                "classes": f"tier-{tier_class} {source_class}",
            })

    return elements
