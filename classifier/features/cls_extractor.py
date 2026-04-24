"""CLS embedding extraction from trained cross-encoder checkpoints.

Extracted from v7 inline Phase 4 in train_all.py.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import torch


def extract_cls_features(
    model_dir: str,
    output_path: str,
    data_splits: list[str] | None = None,
    batch_size: int = 64,
) -> dict[str, np.ndarray]:
    """Extract CLS embeddings and logits from a saved cross-encoder.

    Loads data from multiple JSONL splits, runs each pair through the
    model, and saves logits + CLS embeddings as an npz file.
    """
    from classifier.ensemble.cross_encoder import CrossEncoderClassifier

    if data_splits is None:
        data_splits = [
            "data/splits/expert_train.jsonl",
            "data/splits/expert_val.jsonl",
            "data/splits/human_cal.jsonl",
            "data/splits/human_test_frozen.jsonl",
        ]

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    all_pairs = []
    for split_path in data_splits:
        p = Path(split_path)
        if p.exists():
            with p.open() as f:
                for line in f:
                    all_pairs.append(json.loads(line))

    print(f"  [cls_extractor] {len(all_pairs)} pairs from {len(data_splits)} splits")

    model = CrossEncoderClassifier.load(Path(model_dir)).to(device)
    model.eval()
    head_type = getattr(model, "head_type", "corn")
    print(f"  [cls_extractor] model loaded, head_type={head_type}")

    logits_all = []
    cls_embs_all = []

    with torch.no_grad():
        for i in range(0, len(all_pairs), batch_size):
            batch = all_pairs[i : i + batch_size]
            texts_a = [r.get("source_text", "") for r in batch]
            texts_b = [r.get("target_text", "") for r in batch]

            encoding = model.tokenize_batch(texts_a, texts_b)
            encoding = {k: v.to(device) for k, v in encoding.items()}

            batch_logits, batch_cls = model.forward(
                encoding["input_ids"], encoding["attention_mask"]
            )
            logits_all.append(batch_logits.cpu().numpy())
            cls_embs_all.append(batch_cls.cpu().numpy())

    features = {
        "logits": np.concatenate(logits_all, axis=0),
        "cls_emb": np.concatenate(cls_embs_all, axis=0),
        "head_type": head_type,
    }

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    np.savez(str(out), **features)
    print(f"  [cls_extractor] saved {features['logits'].shape} logits + {features['cls_emb'].shape} cls_emb -> {out}")

    del model
    torch.cuda.empty_cache()

    return features
