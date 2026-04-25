"""Run v_final ensemble inference on Project 2 edges.

Loads the best checkpoint for each of 3 models, runs forward pass on all
edges, averages softmax probabilities, and writes edge_predictions.json.

Usage (on GPU pod):
    python scripts/predict_edges.py
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import torch
from scipy.special import softmax

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

TIER_NAMES = ["UNRELATED", "PARTIAL", "RELATED", "EQUIVALENT"]
MODELS = [
    {"name": "roberta", "type": "cross_encoder"},
    {"name": "deberta_base", "type": "cross_encoder"},
    {"name": "bge", "type": "bi_encoder"},
]


def build_edge_texts(edges: list[dict], nodes: dict[str, dict]) -> list[dict]:
    """Build text pairs from edges + nodes."""
    pairs = []
    for e in edges:
        src = nodes.get(e["source_node_id"], {})
        tgt = nodes.get(e["target_node_id"], {})
        src_text = src.get("name", "")
        if src.get("description"):
            src_text += " — " + src["description"]
        tgt_text = tgt.get("name", "")
        if tgt.get("description"):
            tgt_text += " — " + tgt["description"]
        pairs.append({
            "edge_id": e["edge_id"],
            "source_text": src_text,
            "target_text": tgt_text,
        })
    return pairs


def run_inference(model, pairs: list[dict], device, is_bi: bool, batch_size: int = 64):
    """Run model inference, return logits array (N, 4)."""
    model.eval()
    all_logits = []
    with torch.no_grad():
        for i in range(0, len(pairs), batch_size):
            batch = pairs[i:i + batch_size]
            texts_a = [p["source_text"] for p in batch]
            texts_b = [p["target_text"] for p in batch]
            tokens = model.tokenize_batch(texts_a, texts_b)
            tokens = {k: v.to(device) for k, v in tokens.items()}

            with torch.amp.autocast("cuda", enabled=True, dtype=torch.bfloat16):
                if is_bi:
                    logits, _ = model.forward(
                        tokens["input_ids_a"], tokens["attention_mask_a"],
                        tokens["input_ids_b"], tokens["attention_mask_b"],
                    )
                else:
                    logits, _ = model.forward(
                        tokens["input_ids"], tokens["attention_mask"]
                    )
            all_logits.append(logits.float().cpu().numpy())

            if (i // batch_size) % 10 == 0:
                print(f"    {i + len(batch)}/{len(pairs)}", flush=True)

    return np.concatenate(all_logits)


def main():
    t0 = time.time()

    edges = json.loads((ROOT / "project2" / "data" / "edges.json").read_text())
    nodes_list = json.loads((ROOT / "project2" / "data" / "nodes.json").read_text())
    nodes = {n["node_id"]: n for n in nodes_list}
    print(f"Loaded {len(edges)} edges, {len(nodes)} nodes")

    pairs = build_edge_texts(edges, nodes)
    print(f"Built {len(pairs)} text pairs")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")

    from classifier.ensemble.cross_encoder import CrossEncoderClassifier
    from classifier.ensemble.bi_encoder import BiEncoderClassifier

    BEST_RUNS = {
        "roberta": "ounfajaa",
        "deberta_base": "ux5wt9hz",
        "bge": "5e3003m8",
    }

    all_probas = []

    for m in MODELS:
        name = m["name"]
        is_bi = m["type"] == "bi_encoder"
        print(f"\n--- {name} ---")

        best_dir = ROOT / "runs" / "vfinal" / "ce" / name / BEST_RUNS[name] / "best"
        if not best_dir.exists():
            print(f"  ERROR: No checkpoint at {best_dir}")
            sys.exit(1)

        print(f"  Loading from {best_dir}")
        if is_bi:
            model = BiEncoderClassifier.load(best_dir)
        else:
            model = CrossEncoderClassifier.load(best_dir)

        model = model.to(device)
        logits = run_inference(model, pairs, device, is_bi)
        probas = softmax(logits, axis=1)
        all_probas.append(probas)
        print(f"  Logits: {logits.shape}, mean prob: {probas.mean(axis=0).round(4)}")

        del model
        torch.cuda.empty_cache()

    avg_proba = np.mean(all_probas, axis=0)
    preds = np.argmax(avg_proba, axis=1)
    confidences = np.max(avg_proba, axis=1)

    predictions = {}
    for pair, pred, conf, proba in zip(pairs, preds, confidences, avg_proba):
        predictions[pair["edge_id"]] = {
            "tier": int(pred),
            "tier_name": TIER_NAMES[int(pred)],
            "confidence": round(float(conf), 4),
            "probabilities": [round(float(p), 4) for p in proba],
        }

    out_path = ROOT / "runs" / "vfinal" / "edge_predictions.json"
    out_path.write_text(json.dumps(predictions, indent=2))
    print(f"\nSaved {len(predictions)} predictions to {out_path}")

    from collections import Counter
    dist = Counter(int(p) for p in preds)
    print(f"Distribution: {dict(sorted(dist.items()))}")
    print(f"Mean confidence: {confidences.mean():.4f}")
    print(f"Total time: {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
