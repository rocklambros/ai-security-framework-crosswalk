"""Declarative ablation registry for Plan 6 ablation matrix.

Each AblationConfig specifies which feature groups to disable. The ablation
runner uses these configs to re-evaluate the stacker with subsets of features.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class AblationConfig:
    name: str
    disable: tuple[str, ...]
    description: str


# Feature groups that can be ablated
# "gat" = score_gat + gat_l2 + gat_dot + gat_diff_*
# "bridge" = score_bridge
# "bge" = score_bge_cosine
# "bm25" = score_bm25
# "gat_diff" = gat_diff_* only (keep gat scalars)

ABLATIONS = {
    c.name: c for c in [
        AblationConfig("full", (), "Full ensemble (baseline)"),
        AblationConfig("no_gat", ("gat",), "Drop all GAT features"),
        AblationConfig("no_gat_diff", ("gat_diff",), "Drop GAT diff features, keep scalars"),
        AblationConfig("no_bridge", ("bridge",), "Drop bridge score"),
        AblationConfig("no_bge", ("bge",), "Drop BGE cosine score"),
        AblationConfig("no_bm25", ("bm25",), "Drop BM25 score"),
        AblationConfig("gat_only", ("bge", "bm25", "bridge"), "Only GAT features"),
        AblationConfig("baseline_only", ("gat",), "Only baseline features (BM25, BGE, bridge)"),
        AblationConfig("lexical_only", ("gat", "bge", "bridge"), "Only BM25"),
        AblationConfig("no_conformal", ("conformal",), "Drop conformal wrapper; raw argmax"),
        AblationConfig("no_router", ("router",), "Drop abstention router"),
        AblationConfig("single_feature_bge", ("bm25", "bridge", "gat"), "BGE only"),
    ]
}
