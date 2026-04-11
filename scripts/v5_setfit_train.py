"""v5 SetFit + Cross-Encoder Fine-Tuning on Lambda GPU.

Two training stages:
  1. SetFit: Few-shot contrastive learning on 150 human_cal pairs
     → Produces fine-tuned sentence embeddings (1024-d)
  2. Cross-encoder: DeBERTa-v3-base NLI fine-tuning on 150 human_cal pairs
     → Produces 4-class logits per pair

Both track to WANDB project "crosswalk-v5-finetune".

Usage:
    python scripts/v5_setfit_train.py --stage setfit     # SetFit only
    python scripts/v5_setfit_train.py --stage ce          # Cross-encoder only
    python scripts/v5_setfit_train.py --stage all         # Both
    python scripts/v5_setfit_train.py --stage extract     # Extract features from trained models
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import torch
from sklearn.metrics import f1_score, accuracy_score, classification_report
from sklearn.model_selection import StratifiedKFold

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TIER_MAP = {"Direct": 3, "Related": 2, "Tangential": 1, "None": 0}
TIER_NAMES = ["Unrelated", "Partial", "Related", "Equivalent"]
CAL_PATH = Path("data/splits/human_cal.jsonl")
TEST_PATH = Path("data/splits/human_test_frozen.jsonl")
OUT_DIR = Path("data/processed/v5_features")
MODELS_DIR = Path("runs/v5")

SETFIT_BASE = "BAAI/bge-large-en-v1.5"
CE_BASE = "cross-encoder/nli-deberta-v3-base"

WANDB_PROJECT = "crosswalk-v5-finetune"


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_pairs(path: Path) -> list[dict]:
    rows = []
    with open(path) as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def enrich_text(pair: dict, node_map: dict) -> tuple[str, str]:
    """Build rich text from node metadata."""
    src = node_map.get(pair.get("source_node_id", ""), {})
    tgt = node_map.get(pair.get("target_node_id", ""), {})

    def _build(node, fallback):
        parts = []
        if node.get("framework"):
            parts.append(f"[{node['framework']}]")
        if node.get("domain"):
            parts.append(f"({node['domain']})")
        if node.get("name"):
            parts.append(node["name"])
        desc = node.get("description", "")
        if desc and desc != node.get("name", ""):
            parts.append(desc)
        return " ".join(parts) if parts else fallback

    return _build(src, pair.get("source_text", "")), _build(tgt, pair.get("target_text", ""))


def load_all_data():
    """Load cal and test pairs with enriched text."""
    nodes = json.loads(Path("data/processed/nodes.json").read_text())
    node_map = {n["node_id"]: n for n in nodes}

    cal = load_pairs(CAL_PATH)
    test = load_pairs(TEST_PATH)

    cal_texts = [enrich_text(p, node_map) for p in cal]
    test_texts = [enrich_text(p, node_map) for p in test]

    y_cal = np.array([TIER_MAP[r["expert_tier"]] for r in cal])
    y_test = np.array([TIER_MAP[r["expert_tier"]] for r in test])

    return cal, test, cal_texts, test_texts, y_cal, y_test


# ---------------------------------------------------------------------------
# Stage 1: SetFit
# ---------------------------------------------------------------------------

def train_setfit(cal_texts, y_cal, test_texts, y_test):
    """Train SetFit model on human_cal pairs."""
    import wandb
    from datasets import Dataset

    wandb.init(project=WANDB_PROJECT, name="setfit-bge-large", tags=["setfit"])

    # Monkey-patch SetFit model_card bug (Column.sort not available in newer datasets)
    import setfit.model_card as _mc
    _orig_set_widget = _mc.SetFitModelCardData.set_widget_examples
    def _patched_set_widget(self, dataset):
        try:
            _orig_set_widget(self, dataset)
        except AttributeError:
            pass  # Skip widget examples on incompatible datasets versions
    _mc.SetFitModelCardData.set_widget_examples = _patched_set_widget

    from setfit import SetFitModel, Trainer, TrainingArguments

    # Build training dataset — SetFit expects "text" and "label"
    # For pair classification, concatenate with [SEP]
    train_texts = [f"{a} [SEP] {b}" for a, b in cal_texts]
    test_texts_flat = [f"{a} [SEP] {b}" for a, b in test_texts]

    train_ds = Dataset.from_dict({"text": train_texts, "label": y_cal.tolist()})

    model = SetFitModel.from_pretrained(
        SETFIT_BASE,
        labels=TIER_NAMES,
    )

    args = TrainingArguments(
        batch_size=16,
        num_epochs=3,
        num_iterations=20,  # contrastive pairs per class
        logging_steps=10,
        output_dir=str(MODELS_DIR / "setfit"),
    )

    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=train_ds,
    )

    trainer.train()

    # Evaluate — SetFit returns label names, map back to ints
    preds = model.predict(test_texts_flat)
    label_to_int = {name: i for i, name in enumerate(TIER_NAMES)}
    preds_np = np.array([label_to_int.get(str(p), p) if isinstance(p, str) else int(p) for p in preds])
    acc = accuracy_score(y_test, preds_np)
    f1 = f1_score(y_test, preds_np, average="macro")

    print(f"\nSetFit Results:")
    print(f"  Accuracy: {acc:.4f}")
    print(f"  Macro F1: {f1:.4f}")
    print(classification_report(y_test, preds_np, target_names=TIER_NAMES))

    wandb.log({"test_accuracy": acc, "test_macro_f1": f1})
    wandb.finish()

    # Save model — use checkpoint if main save fails
    best_dir = MODELS_DIR / "setfit" / "best"
    model.save_pretrained(str(best_dir))
    print(f"Saved SetFit model to {best_dir}")

    return model


# ---------------------------------------------------------------------------
# Stage 2: Cross-Encoder Fine-Tuning
# ---------------------------------------------------------------------------

def train_cross_encoder(cal_texts, y_cal, test_texts, y_test):
    """Fine-tune cross-encoder on human_cal pairs for 4-class classification."""
    import wandb
    from sentence_transformers import CrossEncoder

    wandb.init(project=WANDB_PROJECT, name="ce-deberta-v3-finetune", tags=["cross-encoder"])

    # CrossEncoder expects list of (text_a, text_b) tuples and integer labels
    train_pairs = list(cal_texts)
    test_pairs = list(test_texts)

    # Also add pair-swapped augmentation (A,B → B,A with same label)
    aug_pairs = [(b, a) for a, b in cal_texts]
    aug_labels = y_cal.tolist()

    all_train_pairs = train_pairs + aug_pairs
    all_train_labels = y_cal.tolist() + aug_labels
    print(f"  Training on {len(all_train_pairs)} pairs (150 original + 150 swapped)")

    # Fine-tune
    model = CrossEncoder(
        CE_BASE,
        num_labels=4,
        max_length=256,
        automodel_args={"ignore_mismatched_sizes": True},
    )

    model.fit(
        train_dataloader=_make_dataloader(all_train_pairs, all_train_labels, batch_size=16),
        epochs=10,
        warmup_steps=30,
        output_path=str(MODELS_DIR / "ce_finetuned"),
        optimizer_params={"lr": 2e-5},
        weight_decay=0.01,
        show_progress_bar=True,
    )

    # Final evaluation
    logits = model.predict(test_pairs)
    preds = np.argmax(logits, axis=1)
    acc = accuracy_score(y_test, preds)
    f1 = f1_score(y_test, preds, average="macro")

    print(f"\nCross-Encoder Results:")
    print(f"  Accuracy: {acc:.4f}")
    print(f"  Macro F1: {f1:.4f}")
    print(classification_report(y_test, preds, target_names=TIER_NAMES))

    wandb.log({"test_accuracy": acc, "test_macro_f1": f1})
    wandb.finish()

    # Save
    model.save(str(MODELS_DIR / "ce_finetuned" / "best"))
    print(f"Saved cross-encoder to {MODELS_DIR / 'ce_finetuned' / 'best'}")

    return model


def _make_dataloader(pairs, labels, batch_size=16):
    """Create a DataLoader for CrossEncoder training."""
    from sentence_transformers import InputExample
    from torch.utils.data import DataLoader

    examples = []
    for (a, b), label in zip(pairs, labels):
        examples.append(InputExample(texts=[a, b], label=label))

    return DataLoader(examples, shuffle=True, batch_size=batch_size)


# ---------------------------------------------------------------------------
# Stage 3: Feature Extraction
# ---------------------------------------------------------------------------

def extract_features(cal_texts, test_texts):
    """Extract features from trained SetFit and CE models."""
    all_texts = list(cal_texts) + list(test_texts)
    n_cal = len(cal_texts)

    features = {}

    # SetFit embeddings — try best, fall back to checkpoint
    setfit_path = MODELS_DIR / "setfit" / "best"
    if not setfit_path.exists():
        # Fall back to last checkpoint
        ckpt_dir = MODELS_DIR / "setfit"
        ckpts = sorted(ckpt_dir.glob("checkpoint-*"))
        if ckpts:
            setfit_path = ckpts[-1]
            print(f"  Using checkpoint: {setfit_path}")
    if setfit_path.exists():
        from setfit import SetFitModel
        model = SetFitModel.from_pretrained(str(setfit_path))
        texts_flat = [f"{a} [SEP] {b}" for a, b in all_texts]

        # Get embeddings from the sentence transformer body
        embeddings = model.model_body.encode(texts_flat, show_progress_bar=True)
        features["setfit_embeddings"] = embeddings.astype(np.float32)

        # Get predictions (logits/probabilities)
        preds = model.predict_proba(texts_flat)
        features["setfit_proba"] = np.array(preds, dtype=np.float32)

        print(f"  SetFit embeddings: {embeddings.shape}")
        print(f"  SetFit probas: {features['setfit_proba'].shape}")
    else:
        print(f"  WARNING: No SetFit model at {setfit_path}")

    # Cross-encoder logits
    ce_path = MODELS_DIR / "ce_finetuned" / "best"
    if ce_path.exists():
        from sentence_transformers import CrossEncoder
        model = CrossEncoder(str(ce_path))
        logits = model.predict(all_texts)
        features["ce_finetuned_logits"] = np.array(logits, dtype=np.float32)
        print(f"  CE logits: {features['ce_finetuned_logits'].shape}")
    else:
        print(f"  WARNING: No CE model at {ce_path}")

    # Save
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if features:
        np.savez(OUT_DIR / "v5_finetuned_features.npz", n_cal=n_cal, **features)
        print(f"  Saved features to {OUT_DIR / 'v5_finetuned_features.npz'}")

    return features


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", default="all", choices=["setfit", "ce", "all", "extract"])
    args = parser.parse_args()

    cal, test, cal_texts, test_texts, y_cal, y_test = load_all_data()
    print(f"Loaded: {len(cal)} cal pairs, {len(test)} test pairs")
    print(f"Class distribution (cal): {np.bincount(y_cal, minlength=4).tolist()}")
    print(f"Class distribution (test): {np.bincount(y_test, minlength=4).tolist()}")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Device: {device}")

    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    if args.stage in ("setfit", "all"):
        print("\n" + "=" * 60)
        print("Stage 1: SetFit Fine-Tuning")
        print("=" * 60)
        train_setfit(cal_texts, y_cal, test_texts, y_test)

    if args.stage in ("ce", "all"):
        print("\n" + "=" * 60)
        print("Stage 2: Cross-Encoder Fine-Tuning")
        print("=" * 60)
        train_cross_encoder(cal_texts, y_cal, test_texts, y_test)

    if args.stage in ("extract", "all"):
        print("\n" + "=" * 60)
        print("Stage 3: Feature Extraction")
        print("=" * 60)
        extract_features(cal_texts, test_texts)


if __name__ == "__main__":
    main()
