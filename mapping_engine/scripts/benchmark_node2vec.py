"""Benchmark Node2Vec vs the bridge signal on AIUC-1 → OWASP Agentic.

Reports:
* Spearman / Pearson correlation between the two signal matrices
  (high correlation = Node2Vec adds little new information).
* Per-anchor scores for both signals.
* Mean separation of mapped vs unmapped pairs (using the 119 expert
  AIUC labels) for each signal.

Decision rule: if Spearman(node2vec, bridge) > 0.95, mark Node2Vec as
"not worth the complexity" — they're measuring the same thing.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr

from mapping_engine.config import load_pair_config
from mapping_engine.engine.bridge import graph_bridge_scores
from mapping_engine.engine.graph import get_framework_nodes, load_graph
from mapping_engine.engine.node2vec_signal import compute_node2vec_similarity

REPO = Path(__file__).resolve().parents[2]


def main() -> None:
    G = load_graph(REPO / "data/processed/nodes.json", REPO / "data/processed/edges.json")
    cfg = load_pair_config("aiuc_1__owasp_agentic", validate_anchors_in=G)
    src = sorted(get_framework_nodes(G, "aiuc_1", entry_types=["control"]))
    tgt = sorted(get_framework_nodes(G, "owasp_agentic", entry_types=["risk"]))

    bridge = graph_bridge_scores(G, src, tgt)
    n2v = compute_node2vec_similarity(src, tgt)
    # rescale node2vec from [-1,1] to [0,1] for fair comparison/separation
    n2v_01 = (n2v + 1.0) / 2.0

    flat_b = bridge.flatten()
    flat_n = n2v_01.flatten()
    spear, _ = spearmanr(flat_b, flat_n)
    pear, _ = pearsonr(flat_b, flat_n)
    print(f"Bridge vs Node2Vec correlation: spearman={spear:.4f}  pearson={pear:.4f}")

    # Mapped/unmapped separation
    train_df = pd.read_csv(REPO / "data/processed/training_data.csv")
    mapped = {(r.source_node_id, r.target_node_id) for r in train_df[train_df.is_mapped == 1].itertuples()}
    pos_b, neg_b, pos_n, neg_n = [], [], [], []
    for i, s in enumerate(src):
        for j, t in enumerate(tgt):
            (pos_b if (s, t) in mapped else neg_b).append(float(bridge[i, j]))
            (pos_n if (s, t) in mapped else neg_n).append(float(n2v_01[i, j]))
    sep_bridge = float(np.mean(pos_b) - np.mean(neg_b))
    sep_n2v = float(np.mean(pos_n) - np.mean(neg_n))
    print(f"Bridge   separation: {sep_bridge:+.4f}  (pos={np.mean(pos_b):.4f}  neg={np.mean(neg_b):.4f})")
    print(f"Node2Vec separation: {sep_n2v:+.4f}  (pos={np.mean(pos_n):.4f}  neg={np.mean(neg_n):.4f})")

    anchors = []
    for ap in cfg.anchors.pairs:
        if ap.source in src and ap.target in tgt:
            i, j = src.index(ap.source), tgt.index(ap.target)
            anchors.append({
                "source": ap.source, "target": ap.target,
                "expected": ap.expected_tier,
                "bridge": float(bridge[i, j]),
                "node2vec": float(n2v_01[i, j]),
            })
    print("\nAnchor pair scores:")
    for a in anchors:
        print(f"  {a['source']} → {a['target']:30s}  "
              f"bridge={a['bridge']:.3f}  n2v={a['node2vec']:.3f}  ({a['expected']})")

    decision = "not_worth_complexity" if spear > 0.95 else (
        "marginal" if abs(sep_n2v) < abs(sep_bridge) * 0.5 else "useful"
    )
    print(f"\nDecision: {decision}")

    out = {
        "spearman_bridge_node2vec": spear,
        "pearson_bridge_node2vec": pear,
        "bridge_separation": sep_bridge,
        "node2vec_separation": sep_n2v,
        "anchors": anchors,
        "decision": decision,
    }
    out_path = REPO / "data" / "processed" / "node2vec_benchmark.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
