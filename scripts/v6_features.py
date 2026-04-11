"""V6 feature engineering: 22d feature matrix from pre-computed sources.

Features:
  LLM (7d):   final_score, final_tier, confidence, is_unanimous, sonnet_score_1/2/3
  Struct (13d): depth_diff, depth_src, depth_tgt, len_src, len_tgt, len_diff,
                len_ratio, n2v_cosine, gat_cosine, has_technique, has_mitigation,
                is_activity_subcategory, is_activity_risk
  Opus (2d):   opus_score, opus_confidence
"""
from __future__ import annotations
import json
import numpy as np
from pathlib import Path

TIER_MAP = {"Direct": 3, "Related": 2, "Tangential": 1, "None": 0}
FEATURE_NAMES = [
    "llm_final_score", "llm_final_tier", "llm_confidence", "llm_is_unanimous",
    "llm_sonnet_1", "llm_sonnet_2", "llm_sonnet_3",
    "depth_diff", "depth_src", "depth_tgt",
    "len_src", "len_tgt", "len_diff", "len_ratio",
    "n2v_cosine", "gat_cosine",
    "has_technique", "has_mitigation", "is_activity_subcategory", "is_activity_risk",
    "opus_score", "opus_confidence",
]


def _load_node_map():
    nodes = json.loads(Path("data/processed/nodes.json").read_text())
    return {n["node_id"]: n for n in nodes}


def _load_n2v_map(node_map):
    nodes = json.loads(Path("data/processed/nodes.json").read_text())
    n2v = np.load("data/processed/node2vec_embeddings.npy")
    return {n["node_id"]: n2v[i] for i, n in enumerate(nodes)}


def _load_gat_map():
    gat = np.load("data/features/gat_embeddings.npz")
    return {str(nid): gat["embeddings"][i] for i, nid in enumerate(gat["node_ids"])}


def _get_depth(nid, node_map):
    node = node_map.get(nid, {})
    d = 0
    while node.get("parent_node_id") and node["parent_node_id"] in node_map and d < 5:
        node = node_map[node["parent_node_id"]]
        d += 1
    return d


def _cosine(a, b):
    if a is None or b is None:
        return 0.0
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8))


def _build_structural(pair, node_map, n2v_map, gat_map):
    src = node_map.get(pair.get("source_node_id", ""), {})
    tgt = node_map.get(pair.get("target_node_id", ""), {})
    d_s = _get_depth(pair.get("source_node_id", ""), node_map)
    d_t = _get_depth(pair.get("target_node_id", ""), node_map)
    st = src.get("description", src.get("name", ""))
    tt = tgt.get("description", tgt.get("name", ""))
    ls, lt = len(st), len(tt)
    et = f"{src.get('entry_type', '?')}_{tgt.get('entry_type', '?')}"
    return [
        abs(d_s - d_t), d_s, d_t,
        ls, lt, abs(ls - lt),
        min(ls, lt) / max(ls, lt) if max(ls, lt) > 0 else 1.0,
        _cosine(n2v_map.get(pair.get("source_node_id")),
                n2v_map.get(pair.get("target_node_id"))),
        _cosine(gat_map.get(pair.get("source_node_id")),
                gat_map.get(pair.get("target_node_id"))),
        1 if "technique" in et else 0,
        1 if "mitigation" in et else 0,
        1 if et == "activity_subcategory" else 0,
        1 if et == "activity_risk" else 0,
    ]


def _load_llm(path):
    rows = [json.loads(l) for l in open(path) if l.strip()]
    X = []
    for r in rows:
        ss = r.get("sonnet_scores", [5, 5, 5])
        ss = ss[:3] if len(ss) >= 3 else ss + [5] * (3 - len(ss))
        X.append([r["final_score"], r["final_tier"], r["confidence"],
                  r["is_unanimous"]] + ss)
    return np.array(X, dtype=np.float32)


def _load_opus(path, n_expected):
    rows = sorted(
        [json.loads(l) for l in open(path) if l.strip()],
        key=lambda x: x["pair_idx"],
    )
    X = []
    for r in rows:
        if r.get("skipped"):
            X.append([5.0, 0.5])
        else:
            X.append([r["score"], r["confidence"]])
    assert len(X) == n_expected, f"Opus: expected {n_expected}, got {len(X)}"
    return np.array(X, dtype=np.float32)


def build_features(split: str) -> tuple[np.ndarray, np.ndarray, list[dict]]:
    """Build 22d feature matrix for a split.

    Args:
        split: "human_cal" or "human_test_frozen"

    Returns:
        X (n, 22), y (n,), pairs (list of dicts)
    """
    node_map = _load_node_map()
    n2v_map = _load_n2v_map(node_map)
    gat_map = _load_gat_map()

    pairs = [json.loads(l) for l in
             open(f"data/splits/{split}.jsonl") if l.strip()]
    y = np.array([TIER_MAP[r["expert_tier"]] for r in pairs])

    X_llm = _load_llm(f"data/processed/llm_scores_v4/{split}.jsonl")
    X_struct = np.array(
        [_build_structural(p, node_map, n2v_map, gat_map) for p in pairs],
        dtype=np.float32,
    )
    X_opus = _load_opus(
        f"data/processed/v5_features/opus_scores_{split}.jsonl",
        len(pairs),
    )
    X = np.hstack([X_llm, X_struct, X_opus])
    assert X.shape == (len(pairs), 22), f"Expected (n, 22), got {X.shape}"
    return X, y, pairs


if __name__ == "__main__":
    for split in ["human_cal", "human_test_frozen"]:
        X, y, pairs = build_features(split)
        print(f"{split}: X={X.shape}, y={y.shape}, classes={np.bincount(y, minlength=4).tolist()}")
