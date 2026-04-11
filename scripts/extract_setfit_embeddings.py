"""Extract SetFit embeddings from trained checkpoint."""
import json
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

TIER_MAP = {"Direct": 3, "Related": 2, "Tangential": 1, "None": 0}


def enrich_text(pair, node_map):
    src = node_map.get(pair.get("source_node_id", ""), {})
    tgt = node_map.get(pair.get("target_node_id", ""), {})

    def _build(node, fallback):
        parts = []
        fw = node.get("framework")
        if fw:
            parts.append(f"[{fw}]")
        dom = node.get("domain")
        if dom:
            parts.append(f"({dom})")
        name = node.get("name")
        if name:
            parts.append(name)
        desc = node.get("description", "")
        if desc and desc != node.get("name", ""):
            parts.append(desc)
        return " ".join(parts) if parts else fallback

    return _build(src, pair.get("source_text", "")), _build(tgt, pair.get("target_text", ""))


def load_pairs(path):
    rows = []
    with open(path) as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def main():
    nodes = json.loads(Path("data/processed/nodes.json").read_text())
    node_map = {n["node_id"]: n for n in nodes}

    cal = load_pairs("data/splits/human_cal.jsonl")
    test = load_pairs("data/splits/human_test_frozen.jsonl")
    cal_texts = [enrich_text(p, node_map) for p in cal]
    test_texts = [enrich_text(p, node_map) for p in test]

    # Load SetFit model body from checkpoint
    model = SentenceTransformer("runs/v5/setfit/checkpoint-1125")
    print(f"Loaded SetFit body")

    # Encode all pairs
    all_texts = [f"{a} [SEP] {b}" for a, b in cal_texts + test_texts]
    embeddings = model.encode(all_texts, show_progress_bar=True, batch_size=32)
    print(f"Embeddings: {embeddings.shape}")

    # Save
    Path("data/processed/v5_features").mkdir(parents=True, exist_ok=True)
    np.savez(
        "data/processed/v5_features/setfit_embeddings.npz",
        embeddings=embeddings.astype(np.float32),
        n_cal=len(cal),
    )
    print("Saved setfit_embeddings.npz")


if __name__ == "__main__":
    main()
