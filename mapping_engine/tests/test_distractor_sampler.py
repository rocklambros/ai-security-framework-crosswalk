"""Unit tests for the anchors-vs-distractors sampler."""

from __future__ import annotations

import yaml
import networkx as nx
import pytest

from mapping_engine.calibration.distractor_sampler import (
    DistractorSet,
    sample_distractors,
)


def _toy_graph() -> nx.DiGraph:
    G = nx.DiGraph()
    # source framework
    G.add_node("src:S1", framework="src", entry_type="control")
    G.add_node("src:S2", framework="src", entry_type="control")
    # target framework — 6 risks, of which S1->T1 and S2->T2 are positives
    for i in range(1, 7):
        G.add_node(f"tgt:T{i}", framework="tgt", entry_type="risk")
    G.add_edge("src:S1", "tgt:T1", confidence="expert")
    G.add_edge("src:S2", "tgt:T2", confidence="authoritative")
    # one inferred edge that should NOT be excluded
    G.add_edge("src:S1", "tgt:T3", confidence="inferred")
    return G


def _toy_pair_yaml(tmp_path) -> str:
    cfg = {
        "source_framework": "src",
        "target_framework": "tgt",
        "target_entry_types": ["risk"],
        "anchors": {
            "pairs": [
                {"source": "src:S1", "target": "tgt:T1", "expected_tier": "Direct"},
                {"source": "src:S2", "target": "tgt:T2", "expected_tier": "Direct"},
            ]
        },
    }
    p = tmp_path / "pair.yaml"
    p.write_text(yaml.safe_dump(cfg))
    return str(p)


def test_sampler_excludes_positive_and_expert_partners(tmp_path):
    G = _toy_graph()
    sets = sample_distractors(_toy_pair_yaml(tmp_path), G, n_per_anchor=10, rng_seed=7)
    assert len(sets) == 2
    for s in sets:
        assert isinstance(s, DistractorSet)
        assert s.positive not in s.distractors
        # The positive itself is the only expert partner of each source
        # in the toy graph, so 5 distractors should be available (T2..T6 minus pos)
        assert len(s.distractors) == 5
        # T3 is reachable via an inferred (not expert) edge, so it MUST
        # remain in the candidate pool.
        if s.source == "src:S1":
            assert "tgt:T3" in s.distractors


def test_sampler_is_deterministic_under_same_seed(tmp_path):
    G = _toy_graph()
    a = sample_distractors(_toy_pair_yaml(tmp_path), G, n_per_anchor=3, rng_seed=42)
    b = sample_distractors(_toy_pair_yaml(tmp_path), G, n_per_anchor=3, rng_seed=42)
    assert [(s.source, s.distractors) for s in a] == [
        (s.source, s.distractors) for s in b
    ]


def test_sampler_changes_with_different_seed(tmp_path):
    G = _toy_graph()
    # 4 candidates per anchor, draw 2 — different seed should produce a
    # different draw with very high probability.
    a = sample_distractors(_toy_pair_yaml(tmp_path), G, n_per_anchor=2, rng_seed=1)
    b = sample_distractors(_toy_pair_yaml(tmp_path), G, n_per_anchor=2, rng_seed=999)
    assert any(s_a.distractors != s_b.distractors for s_a, s_b in zip(a, b))


def test_sampler_caps_at_pool_size(tmp_path):
    G = _toy_graph()
    sets = sample_distractors(
        _toy_pair_yaml(tmp_path), G, n_per_anchor=100, rng_seed=0
    )
    for s in sets:
        # 6 risks total minus the positive = 5
        assert len(s.distractors) == 5


def test_sampler_skips_missing_nodes(tmp_path):
    G = _toy_graph()
    cfg = {
        "source_framework": "src",
        "target_framework": "tgt",
        "target_entry_types": ["risk"],
        "anchors": {
            "pairs": [
                {"source": "src:S1", "target": "tgt:T1", "expected_tier": "Direct"},
                {"source": "src:GHOST", "target": "tgt:T2", "expected_tier": "Direct"},
            ]
        },
    }
    p = tmp_path / "pair.yaml"
    p.write_text(yaml.safe_dump(cfg))
    sets = sample_distractors(str(p), G, n_per_anchor=3, rng_seed=1)
    assert len(sets) == 1
    assert sets[0].source == "src:S1"


def test_sampler_raises_on_empty_candidate_pool(tmp_path):
    G = _toy_graph()
    cfg = {
        "source_framework": "src",
        "target_framework": "tgt",
        "target_entry_types": ["nonexistent_type"],
        "anchors": {"pairs": [{"source": "src:S1", "target": "tgt:T1"}]},
    }
    p = tmp_path / "pair.yaml"
    p.write_text(yaml.safe_dump(cfg))
    with pytest.raises(ValueError):
        sample_distractors(str(p), G, n_per_anchor=3, rng_seed=1)
