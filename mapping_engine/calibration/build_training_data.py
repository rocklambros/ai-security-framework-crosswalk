"""Build training and held-out NIST validation data for weight learning.

Pulls expert mappings from the AIUC_2_OWASP_Agentic_Top_10 reference repo
(``tests/test_data.json``) and computes the four signal scores
(bridge / semantic / keyword / function_match) for every candidate pair
in the AIUC-1 × OWASP Agentic and NIST RMF × OWASP Agentic spaces.

Outputs::

    data/processed/training_data.csv          (AIUC-1 × OWASP, 510 rows)
    data/processed/nist_validation_data.csv   (NIST RMF × OWASP, held out)

Usage::

    python -m mapping_engine.calibration.build_training_data
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from mapping_engine.engine.bridge import graph_bridge_scores
from mapping_engine.engine.function_match import compute_function_match
from mapping_engine.engine.graph import get_framework_nodes, load_graph
from mapping_engine.engine.keyword import compute_keyword_similarity
from mapping_engine.engine.semantic import compute_semantic_similarity

REPO = Path(__file__).resolve().parents[2]
TEST_DATA = Path.home() / "github_projects" / "AIUC_2_OWASP_Agentic_Top_10" / "tests" / "test_data.json"

# NIST validation IDs use a compact form (GV.3.2) but the graph stores
# local_ids in the long form (GOVERN-3.2). This map normalizes them.
NIST_PREFIX = {"GV": "GOVERN", "MP": "MAP", "MS": "MEASURE", "MG": "MANAGE"}


def _normalize_nist_id(short: str) -> str:
    pre, _, rest = short.partition(".")
    return f"{NIST_PREFIX.get(pre, pre)}-{rest}"


def _expert_tier(rel: str | None) -> str:
    if rel == "Primary":
        return "Direct"
    if rel == "Secondary":
        return "Related"
    return "None"


def _build_pairs(
    G,
    sources: list[str],
    targets: list[str],
    expert: dict[str, dict[str, dict]],
    target_local_id_to_node: dict[str, str],
    source_local_id_to_node: dict[str, str],
) -> pd.DataFrame:
    bridge = graph_bridge_scores(G, sources, targets)
    semantic = compute_semantic_similarity(G, sources, targets)
    keyword = compute_keyword_similarity(G, sources, targets)
    fm = compute_function_match(G, sources, targets)

    # Build expert lookup keyed by (source_node_id, target_node_id)
    expert_map: dict[tuple[str, str], dict] = {}
    for tgt_local, src_dict in expert.items():
        tgt_node = target_local_id_to_node.get(tgt_local)
        if tgt_node is None:
            continue
        for src_local, info in src_dict.items():
            src_node = source_local_id_to_node.get(src_local)
            if src_node is None:
                continue
            expert_map[(src_node, tgt_node)] = info

    rows = []
    for i, s in enumerate(sources):
        for j, t in enumerate(targets):
            info = expert_map.get((s, t))
            rel = info.get("rel") if info else None
            rat = info.get("rat") if info else None
            rows.append(
                {
                    "source_node_id": s,
                    "target_node_id": t,
                    "bridge_score": float(bridge[i, j]),
                    "semantic_score": float(semantic[i, j]),
                    "keyword_score": float(keyword[i, j]),
                    "function_match": float(fm[i, j]),
                    "is_mapped": int(info is not None),
                    "expert_tier": _expert_tier(rel),
                    "relevance": rel or "None",
                    "rationale": rat or "None",
                }
            )
    return pd.DataFrame(rows)


def main() -> None:
    G = load_graph(REPO / "data/processed/nodes.json", REPO / "data/processed/edges.json")
    data = json.loads(TEST_DATA.read_text())

    # ── AIUC-1 × OWASP Agentic ────────────────────────────────────────────
    aiuc_sources = sorted(get_framework_nodes(G, "aiuc_1", entry_types=["control"]))
    owasp_targets = sorted(get_framework_nodes(G, "owasp_agentic", entry_types=["risk"]))
    owasp_lid = {G.nodes[n]["local_id"]: n for n in owasp_targets}
    aiuc_lid = {G.nodes[n]["local_id"]: n for n in aiuc_sources}

    train_df = _build_pairs(
        G, aiuc_sources, owasp_targets,
        data["training"]["mappings"], owasp_lid, aiuc_lid,
    )
    train_path = REPO / "data" / "processed" / "training_data.csv"
    train_df.to_csv(train_path, index=False)
    print(f"Wrote {train_path}: {len(train_df)} rows")
    print("  is_mapped distribution:", dict(train_df["is_mapped"].value_counts()))
    print("  expert_tier distribution:", dict(train_df["expert_tier"].value_counts()))

    # ── NIST RMF × OWASP Agentic (held-out generalization) ───────────────
    nist_sources = sorted(get_framework_nodes(G, "nist_rmf", entry_types=["subcategory"]))
    nist_lid = {G.nodes[n]["local_id"]: n for n in nist_sources}

    # Normalize the validation keys (GV.3.2 → GOVERN-3.2)
    raw_val = data["validation"]["mappings"]
    nist_expert: dict[str, dict[str, dict]] = {}
    for asi, sub_map in raw_val.items():
        norm = {_normalize_nist_id(k): v for k, v in sub_map.items()}
        nist_expert[asi] = norm

    val_df = _build_pairs(
        G, nist_sources, owasp_targets,
        nist_expert, owasp_lid, nist_lid,
    )
    val_path = REPO / "data" / "processed" / "nist_validation_data.csv"
    val_df.to_csv(val_path, index=False)
    print(f"Wrote {val_path}: {len(val_df)} rows")
    print("  is_mapped distribution:", dict(val_df["is_mapped"].value_counts()))


if __name__ == "__main__":
    main()
