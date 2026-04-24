"""Bi-encoder classifier for sentence-transformer models (BGE, E5, etc).

Encodes source and target texts independently, then combines embeddings
via [a; b; |a-b|; a*b] for ordinal classification.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import torch
import torch.nn as nn
from transformers import AutoModel, AutoTokenizer


class BiEncoderClassifier(nn.Module):

    def __init__(
        self,
        model_name: str = "BAAI/bge-large-en-v1.5",
        n_classes: int = 4,
        max_length: int = 256,
        dropout: float = 0.1,
        head_type: str = "kl",
    ):
        super().__init__()
        self.model_name = model_name
        self.n_classes = n_classes
        self.max_length = max_length
        self.head_type = head_type

        self.encoder = AutoModel.from_pretrained(model_name)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)

        hidden_size = self.encoder.config.hidden_size
        combined_dim = hidden_size * 4  # [a; b; |a-b|; a*b]
        out_dim = n_classes if head_type == "kl" else n_classes - 1

        self.classifier = nn.Sequential(
            nn.Dropout(dropout),
            nn.Linear(combined_dim, hidden_size),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_size, out_dim),
        )

    def _mean_pool(self, last_hidden: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
        mask = attention_mask.unsqueeze(-1).float()
        return (last_hidden * mask).sum(1) / mask.sum(1).clamp(min=1e-8)

    def _encode(self, input_ids: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
        out = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
        return self._mean_pool(out.last_hidden_state, attention_mask)

    def tokenize_batch(self, texts_a: List[str], texts_b: List[str]) -> Dict[str, torch.Tensor]:
        enc_a = self.tokenizer(
            texts_a, max_length=self.max_length, truncation=True,
            padding=True, return_tensors="pt",
        )
        enc_b = self.tokenizer(
            texts_b, max_length=self.max_length, truncation=True,
            padding=True, return_tensors="pt",
        )
        return {
            "input_ids_a": enc_a["input_ids"],
            "attention_mask_a": enc_a["attention_mask"],
            "input_ids_b": enc_b["input_ids"],
            "attention_mask_b": enc_b["attention_mask"],
        }

    def forward(
        self,
        input_ids_a: torch.Tensor, attention_mask_a: torch.Tensor,
        input_ids_b: torch.Tensor, attention_mask_b: torch.Tensor,
        **kwargs,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        emb_a = self._encode(input_ids_a, attention_mask_a)
        emb_b = self._encode(input_ids_b, attention_mask_b)

        combined = torch.cat([
            emb_a, emb_b,
            (emb_a - emb_b).abs(),
            emb_a * emb_b,
        ], dim=1)

        logits = self.classifier(combined)
        cls_emb = (emb_a + emb_b) / 2
        return logits, cls_emb

    def forward_from_tokens(self, tokens: Dict[str, torch.Tensor]) -> Tuple[torch.Tensor, torch.Tensor]:
        device = next(self.parameters()).device
        return self.forward(
            tokens["input_ids_a"].to(device),
            tokens["attention_mask_a"].to(device),
            tokens["input_ids_b"].to(device),
            tokens["attention_mask_b"].to(device),
        )

    def predict_proba(self, texts_a: List[str], texts_b: List[str], batch_size: int = 32) -> np.ndarray:
        self.eval()
        all_probs = []
        with torch.no_grad():
            for i in range(0, len(texts_a), batch_size):
                tokens = self.tokenize_batch(
                    texts_a[i:i + batch_size], texts_b[i:i + batch_size]
                )
                logits, _ = self.forward_from_tokens(tokens)
                if self.head_type == "kl":
                    probs = torch.softmax(logits, dim=1)
                else:
                    from classifier.ensemble.corn_loss import corn_proba_from_logits
                    probs = corn_proba_from_logits(logits, self.n_classes)
                all_probs.append(probs.cpu().numpy())
        return np.concatenate(all_probs, axis=0)

    def save(self, path: Path) -> None:
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        self.encoder.save_pretrained(path / "encoder")
        self.tokenizer.save_pretrained(path / "encoder")
        torch.save({
            "classifier_state": self.classifier.state_dict(),
            "n_classes": self.n_classes,
            "max_length": self.max_length,
            "head_type": self.head_type,
        }, path / "head.pt")

    @classmethod
    def load(cls, path: Path) -> "BiEncoderClassifier":
        path = Path(path)
        head_data = torch.load(path / "head.pt", map_location="cpu", weights_only=False)
        obj = cls(
            model_name=str(path / "encoder"),
            n_classes=head_data["n_classes"],
            max_length=head_data["max_length"],
            head_type=head_data.get("head_type", "kl"),
        )
        obj.classifier.load_state_dict(head_data["classifier_state"])
        return obj
