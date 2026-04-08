"""Candidate-pool generation for the 12-pair coverage requirement.

Per-framework appearance counts across the 12 pairs below:
  aiuc_1: 3 (src 1,2,12)
  csa_aicm: 2 (src 3,4)
  mitre_atlas: 3 (src 5 + tgt 4,10)
  nist_rmf: 3 (src 6,7 + tgt 12)
  owasp_llm: 3 (tgt 2,5,8)
  owasp_agentic: 4 (tgt 1,3,6,11)
  owasp_ai_exchange: 2 (src 8 + tgt 9)
  eu_gpai_cop: 2 (src 9 + tgt 7)
  cosai_rm: 2 (src 10,11)
All 9 frameworks have >=2 appearances.
"""
from __future__ import annotations

FRAMEWORKS: list[str] = [
    "aiuc_1", "csa_aicm", "mitre_atlas", "nist_rmf",
    "owasp_llm", "owasp_agentic", "owasp_ai_exchange",
    "eu_gpai_cop", "cosai_rm",
]

FRAMEWORK_PAIRS: list[tuple[str, str]] = [
    ("aiuc_1",             "owasp_agentic"),   # 1
    ("aiuc_1",             "owasp_llm"),       # 2
    ("csa_aicm",           "owasp_agentic"),   # 3
    ("csa_aicm",           "mitre_atlas"),     # 4
    ("mitre_atlas",        "owasp_llm"),       # 5
    ("nist_rmf",           "owasp_agentic"),   # 6
    ("nist_rmf",           "eu_gpai_cop"),     # 7
    ("owasp_ai_exchange",  "owasp_llm"),       # 8
    ("eu_gpai_cop",        "owasp_ai_exchange"), # 9
    ("cosai_rm",           "mitre_atlas"),     # 10
    ("cosai_rm",           "owasp_agentic"),   # 11
    ("aiuc_1",             "nist_rmf"),        # 12
]
assert len(FRAMEWORK_PAIRS) == 12


import json
from collections import defaultdict
from classifier.config import DATA_DIR

NODES_PATH = DATA_DIR / "processed/nodes.json"


def load_nodes_by_framework() -> dict[str, list[dict]]:
    """Load the 983-node graph and group by framework id."""
    raw = json.loads(NODES_PATH.read_text())
    nodes = raw if isinstance(raw, list) else raw.get("nodes", list(raw.values()))
    out: dict[str, list[dict]] = defaultdict(list)
    for n in nodes:
        fw = (n.get("framework") or n.get("framework_id") or "").replace("-", "_")
        if fw:
            out[fw].append(n)
    return dict(out)


from pathlib import Path
import numpy as np


def _node_text(n: dict) -> str:
    name = n.get("name") or n.get("title") or n.get("id") or ""
    desc = n.get("description") or n.get("text") or n.get("summary") or ""
    return f"{name}. {desc}".strip()


def build_candidate_pool(
    pairs: list[tuple[str, str]],
    k: int = 20,
    model_name: str = "BAAI/bge-small-en-v1.5",
    cache_dir: Path | None = None,
) -> dict[str, list[dict]]:
    """For each (src_fw, tgt_fw) pair, return top-k target nodes per source node by cosine.

    Deterministic given the same model weights. Uses sentence-transformers.
    """
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(model_name, cache_folder=str(cache_dir) if cache_dir else None)
    by_fw = load_nodes_by_framework()
    out: dict[str, list[dict]] = {}

    for src_fw, tgt_fw in pairs:
        src_nodes = by_fw.get(src_fw, [])
        tgt_nodes = by_fw.get(tgt_fw, [])
        if not src_nodes or not tgt_nodes:
            out[f"{src_fw}__{tgt_fw}"] = []
            continue
        src_texts = [_node_text(n) for n in src_nodes]
        tgt_texts = [_node_text(n) for n in tgt_nodes]
        src_emb = model.encode(src_texts, normalize_embeddings=True, show_progress_bar=False)
        tgt_emb = model.encode(tgt_texts, normalize_embeddings=True, show_progress_bar=False)
        sims = np.asarray(src_emb) @ np.asarray(tgt_emb).T

        pair_rows = []
        for i, src in enumerate(src_nodes):
            topk = np.argsort(-sims[i])[:k]
            cands = [
                {
                    "rank": r + 1,
                    "target_node_id": tgt_nodes[j].get("id") or tgt_nodes[j].get("node_id"),
                    "score": float(sims[i, j]),
                }
                for r, j in enumerate(topk)
            ]
            pair_rows.append({
                "source_node_id": src.get("id") or src.get("node_id"),
                "candidates": cands,
            })
        out[f"{src_fw}__{tgt_fw}"] = pair_rows
    return out
