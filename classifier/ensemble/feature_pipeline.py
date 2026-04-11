"""PCA + probability + agreement feature pipeline for the stacker.

Replaces raw 3,081-dim CLS embeddings with principled features:
- PCA-reduced CLS embeddings (retain 95% variance, typically ~80-128 dims)
- Softmax probabilities per model (3×4 = 12 features)
- Model agreement features (pairwise CLS cosine, prediction entropy, pred std)
"""
from __future__ import annotations

import json
import pickle
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
from sklearn.decomposition import PCA


MODEL_NAMES = ["deberta", "roberta", "electra"]


def _corn_proba(logits: np.ndarray, n_classes: int = 4) -> np.ndarray:
    """Convert CORN logits (n, n_classes-1) to probabilities (n, n_classes).

    For KL-trained models, logits are already (n, n_classes) — apply softmax.
    For CORN-trained models, logits are (n, n_classes-1) — use conditional probs.
    """
    if logits.shape[1] == n_classes:
        exp = np.exp(logits - logits.max(axis=1, keepdims=True))
        return exp / exp.sum(axis=1, keepdims=True)
    elif logits.shape[1] == n_classes - 1:
        sigmoid = 1.0 / (1.0 + np.exp(-logits))
        proba = np.zeros((logits.shape[0], n_classes))
        for k in range(n_classes):
            if k == 0:
                proba[:, k] = 1.0 - sigmoid[:, 0]
            elif k < n_classes - 1:
                proba[:, k] = sigmoid[:, k - 1] * (1.0 - sigmoid[:, k])
            else:
                proba[:, k] = sigmoid[:, k - 1]
        proba = np.clip(proba, 1e-10, None)
        proba /= proba.sum(axis=1, keepdims=True)
        return proba
    else:
        raise ValueError(f"Unexpected logits shape: {logits.shape}")


def _cosine_sim(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Row-wise cosine similarity between two (n, d) matrices."""
    norm_a = np.linalg.norm(a, axis=1, keepdims=True)
    norm_b = np.linalg.norm(b, axis=1, keepdims=True)
    norm_a = np.where(norm_a == 0, 1, norm_a)
    norm_b = np.where(norm_b == 0, 1, norm_b)
    return (a * b).sum(axis=1) / (norm_a.squeeze() * norm_b.squeeze())


class FeaturePipeline:
    """Transform raw CE features into stacker-ready feature matrix."""

    def __init__(self, pca_variance: float = 0.95, n_classes: int = 4):
        self.pca_variance = pca_variance
        self.n_classes = n_classes
        self.pca: Optional[PCA] = None
        self._feature_names: List[str] = []

    def fit_transform(
        self, ce_features: Dict[str, np.ndarray], n_train: int
    ) -> np.ndarray:
        """Fit PCA on training data, return features for training rows."""
        cls_parts = []
        for name in MODEL_NAMES:
            key = f"{name}_cls_emb"
            if key in ce_features:
                cls_parts.append(ce_features[key])
        cls_all = np.hstack(cls_parts) if cls_parts else np.empty((n_train, 0))

        if cls_all.shape[1] > 0:
            self.pca = PCA(n_components=self.pca_variance, random_state=42)
            self.pca.fit(cls_all[:n_train])

        return self.transform(ce_features)[:n_train]

    def transform(self, ce_features: Dict[str, np.ndarray]) -> np.ndarray:
        """Transform CE features into stacker feature matrix."""
        n = None
        features = []
        self._feature_names = []

        # 1. Softmax probabilities per model (3×4 = 12 features)
        all_probas = []
        for name in MODEL_NAMES:
            key = f"{name}_logits"
            if key in ce_features:
                logits = ce_features[key]
                if n is None:
                    n = logits.shape[0]
                proba = _corn_proba(logits, self.n_classes)
                features.append(proba)
                all_probas.append(proba)
                for c in range(self.n_classes):
                    self._feature_names.append(f"{name}_prob_{c}")

        # 2. PCA-reduced CLS embeddings
        cls_parts = []
        for name in MODEL_NAMES:
            key = f"{name}_cls_emb"
            if key in ce_features:
                cls_parts.append(ce_features[key])
        if cls_parts and self.pca is not None:
            cls_all = np.hstack(cls_parts)
            pca_feats = self.pca.transform(cls_all)
            features.append(pca_feats)
            for i in range(pca_feats.shape[1]):
                self._feature_names.append(f"pca_{i:03d}")

        # 3. Model agreement features
        if len(all_probas) >= 2:
            stacked = np.stack(all_probas, axis=0)
            pred_std = stacked.std(axis=0).mean(axis=1, keepdims=True)
            features.append(pred_std)
            self._feature_names.append("agreement_pred_std")

            entropies = []
            for proba in all_probas:
                ent = -(proba * np.log(proba + 1e-10)).sum(axis=1, keepdims=True)
                entropies.append(ent)
            avg_entropy = np.mean(entropies, axis=0)
            features.append(avg_entropy)
            self._feature_names.append("agreement_avg_entropy")

            for i, name_i in enumerate(MODEL_NAMES):
                for j, name_j in enumerate(MODEL_NAMES):
                    if j <= i:
                        continue
                    key_i = f"{name_i}_cls_emb"
                    key_j = f"{name_j}_cls_emb"
                    if key_i in ce_features and key_j in ce_features:
                        cos = _cosine_sim(
                            ce_features[key_i], ce_features[key_j]
                        ).reshape(-1, 1)
                        features.append(cos)
                        self._feature_names.append(f"cosine_{name_i}_{name_j}")

        return np.hstack(features)

    def feature_names(self) -> List[str]:
        return list(self._feature_names)

    def save(self, path: Path) -> None:
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        if self.pca is not None:
            with (path / "pca.pkl").open("wb") as f:
                pickle.dump(self.pca, f)
        with (path / "config.json").open("w") as f:
            json.dump({
                "pca_variance": self.pca_variance,
                "n_classes": self.n_classes,
                "n_pca_components": int(self.pca.n_components_) if self.pca else 0,
            }, f)

    @classmethod
    def load(cls, path: Path) -> "FeaturePipeline":
        path = Path(path)
        with (path / "config.json").open() as f:
            config = json.load(f)
        obj = cls(
            pca_variance=config["pca_variance"],
            n_classes=config["n_classes"],
        )
        pca_path = path / "pca.pkl"
        if pca_path.exists():
            with pca_path.open("rb") as f:
                obj.pca = pickle.load(f)
        return obj
