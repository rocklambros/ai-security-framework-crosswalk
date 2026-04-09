"""Declarative ablation configuration registry for sacred-run ablation matrix."""
from __future__ import annotations

# ---------------------------------------------------------------------------
# V1 ablations — baseline feature-drop configs used in Plan 6 Table 3
# ---------------------------------------------------------------------------
ABLATIONS: dict[str, dict] = {
    "no_gat": {
        "description": "Remove GAT diff features from stacker",
        "features": None,
        "disable": ["gat"],
    },
    "no_bm25": {
        "description": "Remove BM25 score from stacker",
        "features": None,
        "disable": ["bm25"],
    },
    "no_bridge": {
        "description": "Remove bridge-graph features from stacker",
        "features": None,
        "disable": ["bridge"],
    },
    "no_stacker": {
        "description": "Ensemble without stacker (mean-pool logits only)",
        "features": None,
        "disable": ["stacker"],
    },
    "lexical_only": {
        "description": "Lexical features only (mitigation_lexical_match + BM25)",
        "features": ["mitigation_lexical_match", "bm25_score"],
        "disable": [],
    },
    "biencoder_only": {
        "description": "Bi-encoder cosine similarity only",
        "features": ["bge_cosine"],
        "disable": [],
    },
}

# ---------------------------------------------------------------------------
# V2 ablations — cross-encoder and multi-CE ensemble configs for Plan 7/8
# ---------------------------------------------------------------------------
V2_ABLATIONS: dict[str, dict] = {
    "ce_deberta_only": {
        "description": "DeBERTa cross-encoder logits only (argmax)",
        "features": ["deberta_logit_0", "deberta_logit_1", "deberta_logit_2", "deberta_logit_3"],
    },
    "ce_deberta_corn": {
        "description": "DeBERTa with CORN ordinal loss",
        "features": [
            "deberta_logit_0",
            "deberta_logit_1",
            "deberta_logit_2",
            "deberta_logit_3",
            "deberta_cls_sim",
        ],
    },
    "ce_plus_gat": {
        "description": "DeBERTa + GAT diff features in stacker",
        "features": None,
        "disable": ["roberta", "electra", "bm25", "bridge"],
    },
    "multi_ce": {
        "description": "3x cross-encoder ensemble in stacker",
        "features": None,
        "disable": ["gat", "bm25", "bridge"],
    },
    "full_v2": {
        "description": "Full v2 ensemble: 3x CE + GAT + BM25 + bridge",
        "features": None,
        "disable": [],
    },
    "full_v2_two_stage": {
        "description": "Full v2 with two-stage binary->ordinal",
        "features": None,
        "disable": [],
        "two_stage": True,
    },
}

# ---------------------------------------------------------------------------
# Unified view: all known ablation names across v1 and v2
# ---------------------------------------------------------------------------
ALL_ABLATIONS: dict[str, dict] = {**ABLATIONS, **V2_ABLATIONS}


def get_ablation(name: str) -> dict:
    """Return the ablation config for *name*, raising KeyError if not found."""
    if name not in ALL_ABLATIONS:
        raise KeyError(f"Unknown ablation '{name}'. Known: {sorted(ALL_ABLATIONS)}")
    return ALL_ABLATIONS[name]
