"""Compare v2 graph-bridge against v1 OWASP-LLM-Top-10 Jaccard.

Usage: ``python -m mapping_engine.scripts.validate_bridge``

Computes the bridge matrix for AIUC-1 → OWASP Agentic ASI risks under both
algorithms, prints per-anchor comparison + Spearman rank correlation, and
writes ``data/processed/bridge_comparison.csv``.
"""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

from mapping_engine.config import load_pair_config
from mapping_engine.engine.bridge import graph_bridge_scores
from mapping_engine.engine.graph import get_framework_nodes, load_graph

REPO = Path(__file__).resolve().parents[2]


def _v1_jaccard(G, sources: list[str], targets: list[str]) -> np.ndarray:
    """v1-style Jaccard on shared OWASP_LLM neighbors only."""
    def llm_refs(nid: str) -> set[str]:
        out: set[str] = set()
        for _, t, d in G.out_edges(nid, data=True):
            if d.get("target_framework") == "owasp_llm":
                out.add(t)
        for s, _, d in G.in_edges(nid, data=True):
            if d.get("source_framework") == "owasp_llm":
                out.add(s)
        return out

    src_refs = [llm_refs(s) for s in sources]
    tgt_refs = [llm_refs(t) for t in targets]
    M = np.zeros((len(sources), len(targets)), dtype=np.float64)
    for i, a in enumerate(src_refs):
        for j, b in enumerate(tgt_refs):
            if not a and not b:
                continue
            inter = len(a & b)
            union = len(a | b)
            M[i, j] = inter / union if union else 0.0
    return M


def _spearman(a: np.ndarray, b: np.ndarray) -> float:
    from scipy.stats import spearmanr  # type: ignore

    rho, _ = spearmanr(a.ravel(), b.ravel())
    return float(rho)


def main() -> None:
    G = load_graph(REPO / "data/processed/nodes.json", REPO / "data/processed/edges.json")
    cfg = load_pair_config("aiuc_1__owasp_agentic", validate_anchors_in=G)

    sources = sorted(get_framework_nodes(G, cfg.source_framework, cfg.source_entry_types or None))
    targets = sorted(get_framework_nodes(G, cfg.target_framework, cfg.target_entry_types or None))

    v2 = graph_bridge_scores(G, sources, targets, config=cfg.bridge)
    v1 = _v1_jaccard(G, sources, targets)

    print(f"Sources: {len(sources)}  Targets: {len(targets)}")
    print(f"v1 nonzero: {(v1 > 0).sum()}/{v1.size}")
    print(f"v2 nonzero: {(v2 > 0).sum()}/{v2.size}")
    try:
        rho = _spearman(v1, v2)
        print(f"Spearman(v1, v2) = {rho:.4f}")
    except Exception as ex:
        print(f"[spearman skipped] {ex}")

    print("\nAnchor comparison (10 pairs):")
    print(f"{'source':<14}{'target':<22}{'v1':>10}{'v2':>10}")
    out_rows = [("source", "target", "v1_jaccard", "v2_bridge", "expected_tier")]
    for ap in cfg.anchors.pairs:
        i = sources.index(ap.source) if ap.source in sources else -1
        j = targets.index(ap.target) if ap.target in targets else -1
        if i < 0 or j < 0:
            continue
        s_v1 = v1[i, j]; s_v2 = v2[i, j]
        print(f"{ap.source:<14}{ap.target:<22}{s_v1:>10.4f}{s_v2:>10.4f}")
        out_rows.append((ap.source, ap.target, f"{s_v1:.6f}", f"{s_v2:.6f}", ap.expected_tier))

    out = REPO / "data" / "processed" / "bridge_comparison.csv"
    with out.open("w", newline="") as f:
        csv.writer(f).writerows(out_rows)
    print(f"\nWrote {out}")
    assert (v2 > 0).sum() >= (v1 > 0).sum(), "v2 should cover at least as many pairs as v1"


if __name__ == "__main__":
    main()
