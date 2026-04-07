"""PairMapper: orchestrate signals, composer, taxonomy, reranker, anchors.

The ``PairMapper`` class wires every signal module together into a single
pipeline and emits a ``MappingResult`` dataclass containing everything the
output writers need. It is framework-agnostic: all pair-specific behavior
comes from the ``PairConfig``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import networkx as nx
import numpy as np

from mapping_engine.config import PairConfig
from mapping_engine.engine.bridge import graph_bridge_scores
from mapping_engine.engine.composer import (
    TIER_DIRECT,
    TIER_NONE,
    TIER_RELATED,
    TIER_TANGENTIAL,
    assign_tiers,
)
from mapping_engine.engine.function_match import compute_function_match
from mapping_engine.engine.graph import get_framework_nodes
from mapping_engine.engine.keyword import compute_keyword_similarity
from mapping_engine.engine.node2vec_signal import compute_node2vec_similarity
from mapping_engine.engine.reranker import rerank_candidates
from mapping_engine.engine.semantic import compute_semantic_similarity
from mapping_engine.engine.taxonomy import classify_function, classify_relevance

REPO = Path(__file__).resolve().parents[2]
LEARNED_WEIGHTS_PATH = REPO / "data" / "processed" / "learned_weights.json"

TIER_NAMES = {
    TIER_NONE: "None",
    TIER_TANGENTIAL: "Tangential",
    TIER_RELATED: "Related",
    TIER_DIRECT: "Direct",
}

RATIONALE_LABELS = {
    "PREV": "Prevent",
    "SCOPE": "Constrain scope",
    "GATE": "Human gate",
    "DETECT": "Detect and trace",
    "VALID": "Validate and test",
    "GOVERN": "Policy and governance",
    "ISOLATE": "Isolate and contain",
    "DISCLOSE": "Disclose and calibrate",
}


@dataclass
class MappingResult:
    """Full output of ``PairMapper.run``."""

    source_nodes: list[str]
    target_nodes: list[str]
    composite_scores: np.ndarray
    tier_matrix: np.ndarray
    signal_matrices: dict[str, np.ndarray]
    rationale_codes: list[str]
    relevance: np.ndarray
    anchor_validation: dict[str, Any]
    metadata: dict[str, Any]
    mappings: list[dict[str, Any]] = field(default_factory=list)


def _load_learned_weights() -> dict[str, float] | None:
    if not LEARNED_WEIGHTS_PATH.exists():
        return None
    try:
        data = json.loads(LEARNED_WEIGHTS_PATH.read_text())
    except Exception:
        return None
    # Respect the calibration verdict: if hand-tuned is best, don't override.
    if str(data.get("best_model", "")).lower().startswith("hand"):
        return None
    coefs = data.get("logistic_coefficients") or {}
    mapping = {
        "bridge": max(0.0, float(coefs.get("bridge_score", 0.0))),
        "semantic": max(0.0, float(coefs.get("semantic_score", 0.0))),
        "keyword": max(0.0, float(coefs.get("keyword_score", 0.0))),
    }
    total = sum(mapping.values())
    if total <= 1e-9:
        return None
    return {k: v / total for k, v in mapping.items()}


class PairMapper:
    """Run the full signal pipeline for a single framework pair."""

    def __init__(
        self,
        G: nx.DiGraph,
        pair_config: PairConfig,
        use_learned_weights: bool = True,
        enable_reranker: bool | None = None,
    ) -> None:
        self.G = G
        self.pair_config = pair_config
        self.use_learned_weights = use_learned_weights
        self.enable_reranker = enable_reranker

        self.config: dict[str, Any] = {
            "weights": dict(pair_config.weights or {}),
            "thresholds": dict(pair_config.thresholds or {}),
            "semantic": dict(pair_config.semantic or {}),
            "bridge": dict(pair_config.bridge or {}),
            "function_match": dict(pair_config.function_match or {}),
            "reranker": dict(pair_config.reranker or {}),
        }

        if use_learned_weights:
            learned = _load_learned_weights()
            if learned:
                merged = dict(self.config["weights"])
                merged.update(learned)
                self.config["weights"] = merged

    def _select_nodes(self) -> tuple[list[str], list[str]]:
        src = get_framework_nodes(
            self.G,
            self.pair_config.source_framework,
            entry_types=self.pair_config.source_entry_types or None,
        )
        tgt = get_framework_nodes(
            self.G,
            self.pair_config.target_framework,
            entry_types=self.pair_config.target_entry_types or None,
        )
        return sorted(src), sorted(tgt)

    def run(self) -> MappingResult:
        source_nodes, target_nodes = self._select_nodes()
        n_src, n_tgt = len(source_nodes), len(target_nodes)

        bridge = graph_bridge_scores(self.G, source_nodes, target_nodes, self.config.get("bridge"))
        semantic = compute_semantic_similarity(
            self.G, source_nodes, target_nodes, self.config.get("semantic")
        )
        keyword = compute_keyword_similarity(self.G, source_nodes, target_nodes, self.config)
        fn_match = compute_function_match(
            self.G, source_nodes, target_nodes, self.config.get("function_match")
        )

        w = self.config.get("weights", {})
        wb = float(w.get("bridge", 0.45))
        ws = float(w.get("semantic", 0.35))
        wk = float(w.get("keyword", 0.20))
        wn = float(w.get("node2vec", 0.0) or 0.0)
        boost = float(w.get("boost", 0.50))

        node2vec: np.ndarray | None = None
        if wn > 0.0:
            try:
                node2vec = np.clip(
                    compute_node2vec_similarity(source_nodes, target_nodes), 0.0, 1.0
                )
            except Exception:
                node2vec = None

        composite = wb * bridge + ws * semantic + wk * keyword
        if node2vec is not None and wn > 0.0:
            composite = composite + wn * node2vec
        composite = composite * (1.0 + boost * fn_match)
        composite = np.clip(composite, 0.0, 1.0)

        relevance = np.zeros((n_src, n_tgt), dtype=np.int8)
        rationale_codes: list[str] = []
        func_classes: list[str] = []
        for i, s in enumerate(source_nodes):
            fc = classify_function(self.G, s) or "GOVERN"
            func_classes.append(fc)
            rationale_codes.append(fc)
            for j, t in enumerate(target_nodes):
                rel = classify_relevance(self.G, s, t, function_class=fc)
                relevance[i, j] = 1 if rel == "Primary" else 0

        tier_matrix = assign_tiers(
            composite,
            relevance,
            self.config,
            function_match=fn_match,
            function_classes=func_classes,
        )

        rer_cfg = self.config.get("reranker") or {}
        rer_on = bool(rer_cfg.get("enabled", False))
        if self.enable_reranker is not None:
            rer_on = bool(self.enable_reranker)
        if rer_on:
            composite = rerank_candidates(
                self.G, source_nodes, target_nodes, composite, self.config
            )
            tier_matrix = assign_tiers(
                composite,
                relevance,
                self.config,
                function_match=fn_match,
                function_classes=func_classes,
            )

        signal_matrices: dict[str, np.ndarray] = {
            "bridge": bridge,
            "semantic": semantic,
            "keyword": keyword,
            "function_match": fn_match,
        }
        if node2vec is not None:
            signal_matrices["node2vec"] = node2vec

        anchor_validation = self._validate_anchors(
            source_nodes, target_nodes
        )

        mappings = self._flatten_mappings(
            source_nodes, target_nodes, composite, tier_matrix,
            relevance, rationale_codes, signal_matrices,
        )

        metadata = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "methodology": "multi-signal-hybrid-v2",
            "source_framework": self.pair_config.source_framework,
            "target_framework": self.pair_config.target_framework,
            "n_source_nodes": n_src,
            "n_target_nodes": n_tgt,
            "weights": dict(self.config.get("weights", {})),
            "thresholds": dict(self.config.get("thresholds", {})),
            "semantic_model": (self.config.get("semantic") or {}).get(
                "model", "BAAI/bge-large-en-v1.5"
            ),
            "reranker_enabled": rer_on,
            "use_learned_weights": self.use_learned_weights,
        }

        return MappingResult(
            source_nodes=source_nodes,
            target_nodes=target_nodes,
            composite_scores=composite,
            tier_matrix=tier_matrix,
            signal_matrices=signal_matrices,
            rationale_codes=rationale_codes,
            relevance=relevance,
            anchor_validation=anchor_validation,
            metadata=metadata,
            mappings=mappings,
        )

    def _build_masked_graph(self) -> nx.DiGraph:
        """Return a copy of ``self.G`` with authoritative/expert edges removed
        for every anchor pair (both directions). Used exclusively by
        ``_validate_anchors`` to prevent anchor-label leakage through curated
        edges that feed bridge / rationale_code signals.
        """
        pairs = self.pair_config.anchors.pairs
        H = self.G.copy()
        for p in pairs:
            for a, b in ((p.source, p.target), (p.target, p.source)):
                if H.has_edge(a, b):
                    data = H.get_edge_data(a, b) or {}
                    if data.get("confidence") in ("authoritative", "expert"):
                        H.remove_edge(a, b)
        return H

    def _run_with_masked_anchors(
        self, source_nodes: list[str], target_nodes: list[str]
    ) -> tuple[np.ndarray, np.ndarray]:
        """Rebuild composite + tiers on a graph with anchor expert edges masked."""
        H = self._build_masked_graph()
        n_src, n_tgt = len(source_nodes), len(target_nodes)

        bridge = graph_bridge_scores(H, source_nodes, target_nodes, self.config.get("bridge"))
        semantic = compute_semantic_similarity(
            H, source_nodes, target_nodes, self.config.get("semantic")
        )
        keyword = compute_keyword_similarity(H, source_nodes, target_nodes, self.config)
        fn_match = compute_function_match(
            H, source_nodes, target_nodes, self.config.get("function_match")
        )

        w = self.config.get("weights", {})
        wb = float(w.get("bridge", 0.45))
        ws = float(w.get("semantic", 0.35))
        wk = float(w.get("keyword", 0.20))
        wn = float(w.get("node2vec", 0.0) or 0.0)
        boost = float(w.get("boost", 0.50))

        node2vec = None
        if wn > 0.0:
            try:
                node2vec = np.clip(
                    compute_node2vec_similarity(source_nodes, target_nodes), 0.0, 1.0
                )
            except Exception:
                node2vec = None

        composite = wb * bridge + ws * semantic + wk * keyword
        if node2vec is not None and wn > 0.0:
            composite = composite + wn * node2vec
        composite = composite * (1.0 + boost * fn_match)
        composite = np.clip(composite, 0.0, 1.0)

        relevance = np.zeros((n_src, n_tgt), dtype=np.int8)
        func_classes: list[str] = []
        for i, s in enumerate(source_nodes):
            fc = classify_function(H, s) or "GOVERN"
            func_classes.append(fc)
            for j, t in enumerate(target_nodes):
                rel = classify_relevance(H, s, t, function_class=fc)
                relevance[i, j] = 1 if rel == "Primary" else 0

        tiers = assign_tiers(
            composite,
            relevance,
            self.config,
            function_match=fn_match,
            function_classes=func_classes,
        )
        return composite, tiers

    def _flatten_mappings(
        self,
        source_nodes: list[str],
        target_nodes: list[str],
        composite: np.ndarray,
        tiers: np.ndarray,
        relevance: np.ndarray,
        rationale_codes: list[str],
        signal_matrices: dict[str, np.ndarray],
    ) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for i, s in enumerate(source_nodes):
            for j, t in enumerate(target_nodes):
                tier = int(tiers[i, j])
                if tier < TIER_RELATED:
                    continue
                rc = rationale_codes[i]
                out.append({
                    "source_node_id": s,
                    "target_node_id": t,
                    "source_framework": self.G.nodes[s].get("framework"),
                    "target_framework": self.G.nodes[t].get("framework"),
                    "score": float(composite[i, j]),
                    "tier": TIER_NAMES[tier],
                    "tier_int": tier,
                    "relevance": "Primary" if relevance[i, j] == 1 else "Secondary",
                    "rationale_code": rc,
                    "rationale_label": RATIONALE_LABELS.get(rc, rc),
                    "signals": {k: float(M[i, j]) for k, M in signal_matrices.items()},
                })
        return out

    def _validate_anchors(
        self,
        source_nodes: list[str],
        target_nodes: list[str],
    ) -> dict[str, Any]:
        composite, tiers = self._run_with_masked_anchors(source_nodes, target_nodes)
        pairs = self.pair_config.anchors.pairs
        holdout_idx = set(self.pair_config.anchors.holdout_indices or [])
        src_idx = {s: i for i, s in enumerate(source_nodes)}
        tgt_idx = {t: j for j, t in enumerate(target_nodes)}

        training: dict[str, Any] = {}
        holdout: dict[str, Any] = {}
        t_match = h_match = 0
        for k, p in enumerate(pairs):
            i = src_idx.get(p.source)
            j = tgt_idx.get(p.target)
            if i is None or j is None:
                predicted, score = "None", 0.0
            else:
                predicted = TIER_NAMES[int(tiers[i, j])]
                score = float(composite[i, j])
            rec = {
                "predicted": predicted,
                "expected": p.expected_tier,
                "match": predicted == p.expected_tier,
                "score": score,
            }
            key = f"{p.source}__{p.target}"
            if k in holdout_idx:
                holdout[key] = rec
                h_match += int(rec["match"])
            else:
                training[key] = rec
                t_match += int(rec["match"])

        return {
            "training_anchors": training,
            "holdout_anchors": holdout,
            "training_accuracy": t_match / max(1, len(training)),
            "holdout_accuracy": h_match / max(1, len(holdout)),
            "overall_accuracy": (t_match + h_match) / max(1, len(pairs)),
            "masked": True,
        }
