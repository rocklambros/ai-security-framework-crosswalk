"""Cross-encoder classifier with CORN ordinal head.

Wraps a HuggingFace transformer model as a pair classifier.
Input: (source_text, target_text) pair
Output: CORN logits (n_classes-1 binary tasks) + CLS embedding
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
from transformers import AutoModel, AutoTokenizer


class CrossEncoderClassifier(nn.Module):
    """Cross-encoder with CORN ordinal head for pair classification."""

    def __init__(
        self,
        model_name: str = "microsoft/deberta-v3-large",
        n_classes: int = 4,
        max_length: int = 512,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.model_name = model_name
        self.n_classes = n_classes
        self.max_length = max_length

        self.encoder = AutoModel.from_pretrained(model_name)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)

        hidden_size = self.encoder.config.hidden_size
        self.dropout = nn.Dropout(dropout)
        self.classifier = nn.Linear(hidden_size, n_classes - 1)

    def tokenize_pair(
        self, text_a: str, text_b: str
    ) -> Dict[str, torch.Tensor]:
        """Tokenize a single (source, target) pair."""
        tokens = self.tokenizer(
            text_a,
            text_b,
            max_length=self.max_length,
            truncation=True,
            padding="max_length",
            return_tensors="pt",
        )
        return tokens

    def tokenize_batch(
        self, texts_a: List[str], texts_b: List[str]
    ) -> Dict[str, torch.Tensor]:
        """Tokenize a batch of (source, target) pairs."""
        tokens = self.tokenizer(
            texts_a,
            texts_b,
            max_length=self.max_length,
            truncation=True,
            padding=True,
            return_tensors="pt",
        )
        return tokens

    def forward(
        self, input_ids: torch.Tensor, attention_mask: torch.Tensor, **kwargs
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """Forward pass returning CORN logits and CLS embedding."""
        outputs = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
        cls_emb = outputs.last_hidden_state[:, 0, :]
        logits = self.classifier(self.dropout(cls_emb))
        return logits, cls_emb

    def forward_pair(
        self, tokens: Dict[str, torch.Tensor]
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """Convenience: forward from tokenized pair dict."""
        return self.forward(
            input_ids=tokens["input_ids"],
            attention_mask=tokens["attention_mask"],
        )

    def predict_proba(
        self, texts_a: List[str], texts_b: List[str], batch_size: int = 32
    ) -> np.ndarray:
        """Predict class probabilities for a list of pairs."""
        from classifier.ensemble.corn_loss import corn_proba_from_logits

        self.eval()
        all_probs = []

        with torch.no_grad():
            for i in range(0, len(texts_a), batch_size):
                batch_a = texts_a[i : i + batch_size]
                batch_b = texts_b[i : i + batch_size]
                tokens = self.tokenize_batch(batch_a, batch_b)
                tokens = {k: v.to(next(self.parameters()).device) for k, v in tokens.items()}
                logits, _ = self.forward(tokens["input_ids"], tokens["attention_mask"])
                probs = corn_proba_from_logits(logits, self.n_classes)
                all_probs.append(probs.cpu().numpy())

        return np.concatenate(all_probs, axis=0)

    def save(self, path: Path) -> None:
        """Save model weights, tokenizer, and config."""
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        self.encoder.save_pretrained(path / "encoder")
        self.tokenizer.save_pretrained(path / "encoder")
        torch.save(
            {"classifier": self.classifier.state_dict(), "dropout": self.dropout.p},
            path / "head.pt",
        )

    @classmethod
    def load(cls, path: Path, n_classes: int = 4) -> "CrossEncoderClassifier":
        """Load a saved cross-encoder."""
        path = Path(path)
        ce = cls(model_name=str(path / "encoder"), n_classes=n_classes)
        head_state = torch.load(path / "head.pt", map_location="cpu")
        ce.classifier.load_state_dict(head_state["classifier"])
        return ce
