"""Cross-encoder classifier with ordinal head (KL or CORN).

Wraps a HuggingFace transformer model as a pair classifier.
Input: (source_text, target_text) pair
Output: ordinal logits + CLS embedding
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
from transformers import AutoModel, AutoTokenizer


class CrossEncoderClassifier(nn.Module):
    """Cross-encoder with ordinal head (KL or CORN) for pair classification."""

    def __init__(
        self,
        model_name: str = "microsoft/deberta-v3-large",
        n_classes: int = 4,
        max_length: int = 512,
        dropout: float = 0.1,
        head_type: str = "corn",
    ):
        super().__init__()
        self.model_name = model_name
        self.n_classes = n_classes
        self.max_length = max_length
        self.head_type = head_type

        self.encoder = AutoModel.from_pretrained(model_name)
        if "deberta" in model_name.lower():
            from transformers import DebertaV2Tokenizer
            self.tokenizer = DebertaV2Tokenizer.from_pretrained(model_name)
        else:
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)

        hidden_size = self.encoder.config.hidden_size
        self.dropout = nn.Dropout(dropout)
        out_dim = n_classes if head_type == "kl" else n_classes - 1
        self.classifier = nn.Linear(hidden_size, out_dim)

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
        self.eval()
        all_probs = []

        with torch.no_grad():
            for i in range(0, len(texts_a), batch_size):
                batch_a = texts_a[i : i + batch_size]
                batch_b = texts_b[i : i + batch_size]
                tokens = self.tokenize_batch(batch_a, batch_b)
                tokens = {k: v.to(next(self.parameters()).device) for k, v in tokens.items()}
                logits, _ = self.forward(tokens["input_ids"], tokens["attention_mask"])
                if self.head_type == "kl":
                    probs = torch.softmax(logits, dim=1)
                else:
                    from classifier.ensemble.corn_loss import corn_proba_from_logits
                    probs = corn_proba_from_logits(logits, self.n_classes)
                all_probs.append(probs.cpu().numpy())

        return np.concatenate(all_probs, axis=0)

    def save(self, path: Path) -> None:
        """Save model weights, tokenizer, and config."""
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        self.encoder.save_pretrained(path / "encoder")
        self.tokenizer.save_pretrained(path / "encoder")
        torch.save({
            "classifier_state": self.classifier.state_dict(),
            "dropout_p": self.dropout.p,
            "n_classes": self.n_classes,
            "max_length": self.max_length,
            "head_type": self.head_type,
        }, path / "head.pt")

    @classmethod
    def load(cls, path: Path) -> "CrossEncoderClassifier":
        """Load a saved cross-encoder."""
        path = Path(path)
        head_data = torch.load(path / "head.pt", map_location="cpu", weights_only=False)
        obj = cls(
            model_name=str(path / "encoder"),
            n_classes=head_data["n_classes"],
            max_length=head_data["max_length"],
            dropout=head_data["dropout_p"],
            head_type=head_data.get("head_type", "corn"),
        )
        obj.classifier.load_state_dict(head_data["classifier_state"])
        return obj
