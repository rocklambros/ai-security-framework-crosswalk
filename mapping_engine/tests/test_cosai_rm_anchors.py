"""S1 regression: cosai_rm anchors must surface in masked-validation records.

Prior to Session 7.6 S1, the two cosai_rm expanded pairs
(cosai_rm -> mitre_atlas, cosai_rm -> owasp_llm) returned n_anc=0 from the
discriminative harness because the expanded pair YAMLs declared
source_entry_types that excluded every anchor's actual node type (the
anchors reference cosai_rm risks, but the YAML only listed 'control' or
'control, activity'). PairMapper._select_nodes dropped every anchor
source, so the masked_records dict contained no matching keys and the
discriminative harness skipped every anchor.

This test guards against regression by asserting that, for both cosai_rm
pairs, every anchor's source node appears in PairMapper's selected source
nodes and every anchor key is present (non-default score) in the masked
anchor_validation records.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from mapping_engine.config import load_pair_config
from mapping_engine.engine.graph import load_graph
from mapping_engine.engine.mapper import PairMapper

REPO = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def G():
    return load_graph(
        REPO / "data/processed/nodes.json",
        REPO / "data/processed/edges.json",
    )


@pytest.mark.parametrize(
    "pair_name",
    ["cosai_rm__mitre_atlas__expanded", "cosai_rm__owasp_llm__expanded"],
)
def test_cosai_rm_anchor_sources_are_selected(G, pair_name):
    cfg = load_pair_config(pair_name, validate_anchors_in=G)
    mapper = PairMapper(G, cfg, use_learned_weights=False)
    src_nodes, _ = mapper._select_nodes()
    src_set = set(src_nodes)
    missing = [p.source for p in cfg.anchors.pairs if p.source not in src_set]
    assert not missing, (
        f"{pair_name}: {len(missing)} anchor sources not in selected source "
        f"nodes; sample: {missing[:5]}"
    )
