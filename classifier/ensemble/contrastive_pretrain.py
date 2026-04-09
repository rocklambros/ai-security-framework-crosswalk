"""Supervised SimCSE contrastive pre-training for cross-encoders."""
from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any, Dict, List

import numpy as np


def build_contrastive_pairs(
    mappings: List[Dict[str, Any]],
    n_negatives: int = 3,
    seed: int = 42,
) -> List[Dict[str, Any]]:
    """Build contrastive training pairs from expert-labeled mappings."""
    random.seed(seed)
    pairs: List[Dict[str, Any]] = []

    all_targets = [(m["target_text"], m["tier_label"]) for m in mappings]

    for m in mappings:
        pairs.append({
            "anchor": m["source_text"],
            "positive": m["target_text"],
            "label": 1,
            "tier": m["tier_label"],
        })

        neg_candidates = [
            (text, tier) for text, tier in all_targets
            if tier != m["tier_label"] and text != m["target_text"]
        ]
        if neg_candidates:
            chosen = random.sample(neg_candidates, min(n_negatives, len(neg_candidates)))
            for neg_text, neg_tier in chosen:
                pairs.append({
                    "anchor": m["source_text"],
                    "negative": neg_text,
                    "label": 0,
                    "tier": m["tier_label"],
                })

    return pairs


def train_contrastive(
    model_name: str,
    train_path: str,
    output_dir: str,
    wandb_project: str = "crosswalk-v2",
    wandb_group: str = "contrastive-pretrain",
    epochs: int = 5,
    batch_size: int = 64,
    lr: float = 2e-5,
    temperature: float = 0.05,
) -> Dict[str, Any]:
    """Train contrastive model (requires torch + transformers, runs on Lambda)."""
    import torch
    import torch.nn.functional as F
    from transformers import AutoModel, AutoTokenizer

    try:
        import wandb
        wandb.init(project=wandb_project, group=wandb_group, config={
            "model_name": model_name, "epochs": epochs,
            "batch_size": batch_size, "lr": lr, "temperature": temperature,
        })
        use_wandb = True
    except ImportError:
        use_wandb = False

    with Path(train_path).open() as f:
        data = [json.loads(line) for line in f]
    pairs = build_contrastive_pairs(data)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr)

    model.train()
    avg_loss = 0.0
    for epoch in range(epochs):
        random.shuffle(pairs)
        epoch_loss = 0.0
        n_batches = 0

        for i in range(0, len(pairs), batch_size):
            batch = pairs[i : i + batch_size]
            anchors = [p["anchor"] for p in batch]
            others = [p.get("positive", p.get("negative", "")) for p in batch]
            labels = torch.tensor([p["label"] for p in batch], device=device).float()

            tok_a = tokenizer(anchors, padding=True, truncation=True,
                              max_length=256, return_tensors="pt").to(device)
            tok_b = tokenizer(others, padding=True, truncation=True,
                              max_length=256, return_tensors="pt").to(device)

            emb_a = model(**tok_a).last_hidden_state[:, 0, :]
            emb_b = model(**tok_b).last_hidden_state[:, 0, :]

            emb_a = F.normalize(emb_a, dim=1)
            emb_b = F.normalize(emb_b, dim=1)
            sim = torch.sum(emb_a * emb_b, dim=1) / temperature

            loss = F.binary_cross_entropy_with_logits(sim, labels)

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            epoch_loss += loss.item()
            n_batches += 1

        avg_loss = epoch_loss / max(n_batches, 1)
        if use_wandb:
            wandb.log({"epoch": epoch, "contrastive_loss": avg_loss})
        print(f"Epoch {epoch+1}/{epochs} — loss: {avg_loss:.4f}")

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(out)
    tokenizer.save_pretrained(out)

    if use_wandb:
        wandb.finish()

    return {"model_name": model_name, "output_dir": str(out), "final_loss": avg_loss}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--data", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--wandb-project", default="crosswalk-v2")
    parser.add_argument("--wandb-group", default="contrastive-pretrain")
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--lr", type=float, default=2e-5)
    args = parser.parse_args()
    result = train_contrastive(
        model_name=args.model, train_path=args.data, output_dir=args.output,
        wandb_project=args.wandb_project, wandb_group=args.wandb_group,
        epochs=args.epochs, batch_size=args.batch_size, lr=args.lr,
    )
    print(json.dumps(result, indent=2))
