"""Anchors-vs-distractors sampler for the discriminative gating metric.

For each anchor (source, target) in a pair YAML, draws ``n_per_anchor``
distractor target nodes from the same target framework that are NOT
connected to ``source`` by an expert/authoritative edge in either
direction. Sampling is stratified by target framework so that when a
pair YAML's target framework has too few non-mapped candidates we can
fall back to other frameworks of the same entry-type bucket.

Why this exists
---------------
The B-2/B-1/A rebuild gating harness saturated NDCG@10 at 1.0 because
every expanded anchor's expected_tier defaulted to ``Direct`` (rationale
codes were unpopulated for non-owasp_agentic targets). Under uniform
graded relevance the ideal-DCG-equals-actual-DCG identity made the
metric incapable of detecting score improvements.

Anchors-vs-distractors converts the gate into a discriminative ranking
question: given a positive anchor and N sampled negatives, can the
mapper rank the positive at the top? That gate is informative even
when the positive label is uniformly Direct.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import networkx as nx
import numpy as np
import yaml


@dataclass(frozen=True)
class DistractorSet:
    """A single anchor's positive target plus its sampled distractors."""

    source: str
    positive: str
    distractors: tuple[str, ...]
    target_framework: str

    def __post_init__(self) -> None:  # pragma: no cover - dataclass invariant
        if self.positive in self.distractors:
            raise ValueError("positive must not appear in distractors")


def _load_pair_yaml(pair_yaml_path: str | Path) -> dict:
    with open(pair_yaml_path) as fh:
        return yaml.safe_load(fh)


def _expert_partners(G: nx.DiGraph, node: str) -> set[str]:
    """All nodes connected to ``node`` by an expert/authoritative edge in
    either direction. Used to mask the ground-truth from distractor
    sampling so we never label a real positive as a negative.
    """
    partners: set[str] = set()
    for _, v, d in G.out_edges(node, data=True):
        if d.get("confidence") in ("authoritative", "expert"):
            partners.add(v)
    for u, _, d in G.in_edges(node, data=True):
        if d.get("confidence") in ("authoritative", "expert"):
            partners.add(u)
    return partners


def _candidate_targets(
    G: nx.DiGraph,
    target_framework: str,
    target_entry_types: Iterable[str] | None,
) -> list[str]:
    types = set(target_entry_types) if target_entry_types else None
    out: list[str] = []
    for n, data in G.nodes(data=True):
        if data.get("framework") != target_framework:
            continue
        if types and data.get("entry_type") not in types:
            continue
        out.append(n)
    return sorted(out)


def sample_distractors(
    pair_yaml_path: str | Path,
    G: nx.DiGraph,
    n_per_anchor: int = 20,
    rng_seed: int = 20260407,
) -> list[DistractorSet]:
    """Return a list of ``DistractorSet`` objects, one per anchor.

    Parameters
    ----------
    pair_yaml_path:
        Path to an expanded pair YAML (e.g.
        ``mapping_engine/config/pairs/aiuc_1__owasp_agentic__expanded.yaml``).
    G:
        Loaded crosswalk graph (typically from ``load_graph``).
    n_per_anchor:
        Number of distractor targets to draw per anchor. If the
        candidate pool is smaller than this after exclusions, the full
        pool is returned (no resampling with replacement).
    rng_seed:
        Deterministic seed. Per-anchor RNG is derived from this seed
        plus the anchor index so that adding/removing anchors at the
        end of the YAML does not perturb earlier draws.
    """
    cfg = _load_pair_yaml(pair_yaml_path)
    target_framework = cfg["target_framework"]
    target_types = cfg.get("target_entry_types")
    anchors = cfg["anchors"]["pairs"]

    candidates = _candidate_targets(G, target_framework, target_types)
    if not candidates:
        raise ValueError(
            f"no candidate targets for framework={target_framework} "
            f"types={target_types}"
        )

    base_rng = np.random.default_rng(rng_seed)
    out: list[DistractorSet] = []
    for i, a in enumerate(anchors):
        src = a["source"]
        pos = a["target"]
        if src not in G or pos not in G:
            # Anchor refers to a node not in the current graph; skip
            # rather than fail so the harness is robust to graph drift.
            continue
        excluded = _expert_partners(G, src)
        excluded.add(pos)
        pool = [c for c in candidates if c not in excluded]
        if not pool:
            continue
        rng = np.random.default_rng(base_rng.integers(0, 2**32 - 1) + i)
        k = min(n_per_anchor, len(pool))
        idx = rng.choice(len(pool), size=k, replace=False)
        distractors = tuple(pool[j] for j in idx)
        out.append(
            DistractorSet(
                source=src,
                positive=pos,
                distractors=distractors,
                target_framework=target_framework,
            )
        )
    return out
