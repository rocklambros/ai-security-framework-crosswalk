"""Candidate-pool generation for the 26-pair, 12-framework coverage matrix."""
from __future__ import annotations

FRAMEWORKS: list[str] = [
    # Existing 9
    "aiuc_1", "csa_aicm", "mitre_atlas", "nist_rmf",
    "owasp_llm", "owasp_agentic", "owasp_ai_exchange",
    "eu_gpai_cop", "cosai_rm",
    # New (Plan 1-B Tier B)
    "owasp_dsgai", "nist_800_53", "eu_ai_act",
]

FRAMEWORK_PAIRS: list[tuple[str, str]] = [
    # Original 12 (preserved for continuity with frozen test)
    ("aiuc_1",             "owasp_agentic"),    # 1
    ("aiuc_1",             "owasp_llm"),        # 2
    ("csa_aicm",           "owasp_agentic"),    # 3
    ("csa_aicm",           "mitre_atlas"),      # 4
    ("mitre_atlas",        "owasp_llm"),        # 5
    ("nist_rmf",           "owasp_agentic"),    # 6
    ("nist_rmf",           "eu_gpai_cop"),      # 7
    ("owasp_ai_exchange",  "owasp_llm"),        # 8
    ("eu_gpai_cop",        "owasp_ai_exchange"),# 9
    ("cosai_rm",           "mitre_atlas"),      # 10
    ("cosai_rm",           "owasp_agentic"),    # 11
    ("aiuc_1",             "nist_rmf"),         # 12
    # DSGAI as source against existing targets
    ("owasp_dsgai",        "aiuc_1"),           # 13
    ("owasp_dsgai",        "csa_aicm"),         # 14
    ("owasp_dsgai",        "nist_rmf"),         # 15
    ("owasp_dsgai",        "mitre_atlas"),      # 16
    # New targets against existing sources
    ("owasp_llm",          "nist_800_53"),      # 17
    ("owasp_agentic",      "nist_800_53"),      # 18
    ("owasp_dsgai",        "nist_800_53"),      # 19
    ("owasp_llm",          "eu_ai_act"),        # 20
    ("owasp_agentic",      "eu_ai_act"),        # 21
    ("owasp_dsgai",        "eu_ai_act"),        # 22
    # Missing-from-original-12 pairs that the frozen test references
    # (Sessions 1-8 labeled against these but they were never in candidates.py)
    ("aiuc_1",             "csa_aicm"),         # 23
    ("aiuc_1",             "eu_gpai_cop"),      # 24
    ("aiuc_1",             "mitre_atlas"),      # 25
    ("cosai_rm",           "owasp_llm"),        # 26
]
assert len(FRAMEWORK_PAIRS) == 26
# Coverage check: every framework appears in >=2 pairs
from collections import Counter
_counts = Counter(fw for pair in FRAMEWORK_PAIRS for fw in pair)
assert all(c >= 2 for c in _counts.values()), f"coverage violation: {_counts}"


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
    """Rich text representation for embedding.

    Joins title/name, section/category path, and full body text so the
    embedding captures both the identifier and the prose. Falls back
    gracefully when optional fields are missing.
    """
    title = n.get("title") or n.get("name") or ""
    section = n.get("section") or n.get("category") or n.get("section_path") or ""
    body = (
        n.get("text")
        or n.get("description")
        or n.get("summary")
        or n.get("body")
        or ""
    )
    parts: list[str] = []
    if title:
        parts.append(title.strip())
    if section and section not in title:
        parts.append(f"[{section.strip()}]")
    if body:
        parts.append(body.strip())
    out = " — ".join(p for p in parts if p)
    return out or n.get("node_id") or n.get("id") or ""


def build_candidate_pool(
    pairs: list[tuple[str, str]],
    k: int = 20,
    model_name: str = "BAAI/bge-base-en-v1.5",
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
