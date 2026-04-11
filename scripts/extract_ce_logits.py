"""Extract logits from fine-tuned cross-encoder."""
import json
from pathlib import Path

import numpy as np
from sentence_transformers import CrossEncoder

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

    # Load fine-tuned cross-encoder
    model = CrossEncoder("runs/v5/ce_finetuned/best")
    print("Loaded CE model")

    # Get logits
    all_texts = list(cal_texts) + list(test_texts)
    logits = model.predict(all_texts, show_progress_bar=True)
    logits = np.array(logits, dtype=np.float32)
    print(f"Logits: {logits.shape}")

    # Save
    Path("data/processed/v5_features").mkdir(parents=True, exist_ok=True)
    np.savez(
        "data/processed/v5_features/ce_finetuned_logits.npz",
        logits=logits,
        n_cal=len(cal),
    )
    print("Saved ce_finetuned_logits.npz")


if __name__ == "__main__":
    main()
