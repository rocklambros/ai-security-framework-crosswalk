"""Contrastive fine-tuning of the base embedding model.

Uses ``MultipleNegativesRankingLoss`` on (anchor, positive, negative)
triplets produced by ``build_finetune_data.py``. Evaluates on the held-
out NIST cosine pairs each epoch and saves the model into
``mapping_engine/models/finetuned-crosswalk-v1/``.

Trainer note: sentence-transformers >= 3 removed ``model.fit``; we use
``SentenceTransformerTrainer`` (HF Trainer wrapper).

Usage::

    python -m mapping_engine.scripts.finetune_embedding [--epochs N]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from datasets import Dataset

REPO = Path(__file__).resolve().parents[2]
BASE_MODEL = "BAAI/bge-large-en-v1.5"
OUTPUT_DIR = REPO / "mapping_engine" / "models" / "finetuned-crosswalk-v1"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=2)
    parser.add_argument("--batch_size", type=int, default=8)
    parser.add_argument("--lr", type=float, default=2e-5)
    args = parser.parse_args()

    from sentence_transformers import (
        SentenceTransformer,
        SentenceTransformerTrainer,
        losses,
    )
    from sentence_transformers.evaluation import EmbeddingSimilarityEvaluator
    from sentence_transformers.training_args import SentenceTransformerTrainingArguments

    triplets = json.loads((REPO / "data/processed/finetune_train.json").read_text())
    val_pairs = json.loads((REPO / "data/processed/finetune_val.json").read_text())
    print(f"Train triplets: {len(triplets)}  Val pairs: {len(val_pairs)}")

    train_ds = Dataset.from_dict(
        {
            "anchor": [t["anchor"] for t in triplets],
            "positive": [t["positive"] for t in triplets],
            "negative": [t["negative"] for t in triplets],
        }
    )

    evaluator = EmbeddingSimilarityEvaluator(
        sentences1=[p["sentence1"] for p in val_pairs],
        sentences2=[p["sentence2"] for p in val_pairs],
        scores=[p["score"] for p in val_pairs],
        name="nist-val",
    )

    print(f"Loading base model: {BASE_MODEL}")
    model = SentenceTransformer(BASE_MODEL)

    loss = losses.MultipleNegativesRankingLoss(model=model)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    targs = SentenceTransformerTrainingArguments(
        output_dir=str(OUTPUT_DIR / "checkpoints"),
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        learning_rate=args.lr,
        warmup_ratio=0.10,
        fp16=True,
        logging_steps=10,
        save_strategy="no",
        eval_strategy="epoch",
        report_to="none",
        run_name="crosswalk-finetune-v1",
        seed=42,
    )

    trainer = SentenceTransformerTrainer(
        model=model,
        args=targs,
        train_dataset=train_ds,
        loss=loss,
        evaluator=evaluator,
    )
    trainer.train()

    final_path = OUTPUT_DIR
    model.save(str(final_path))
    print(f"\nSaved fine-tuned model to {final_path}")

    # Final evaluator metric
    final = evaluator(model)
    (OUTPUT_DIR / "final_eval.json").write_text(json.dumps(final, indent=2, default=str))
    print(f"Final NIST eval: {final}")


if __name__ == "__main__":
    main()
