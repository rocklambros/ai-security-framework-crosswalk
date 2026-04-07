"""Structural features over the unified framework graph (B-1).

Each feature is a function that takes the graph ``G``, a list of source
node IDs, a list of target node IDs, and an optional ``mask_pairs`` set
of (source, target) tuples whose contributions must be excluded (used by
the leave-one-out anchor masking pipeline).

Returned matrices are dense numpy arrays of shape ``(len(source_nodes),
len(target_nodes))``. Features are added incrementally in B1.1+, gated
individually by the anti-overfit protocol.
"""

from __future__ import annotations

from typing import Iterable

import networkx as nx
import numpy as np

# Confidence weights mirror config/rationale_to_tier.yaml's confidence_weight
# block but at the edge-confidence-tag level rather than rationale-code level.
_CONF_WEIGHT = {
    "authoritative": 1.00,
    "expert": 0.90,
    "derived": 0.60,
    "heuristic": 0.40,
    None: 0.30,
}


def _edge_conf(G: nx.DiGraph, u: str, v: str) -> float:
    """Return the confidence weight of the (u,v) edge in either direction.

    Returns 0.0 if no edge exists.
    """
    if G.has_edge(u, v):
        c = G[u][v].get("confidence")
    elif G.has_edge(v, u):
        c = G[v][u].get("confidence")
    else:
        return 0.0
    return float(_CONF_WEIGHT.get(c, _CONF_WEIGHT[None]))


def _masked_neighbors(
    G: nx.DiGraph, u: str, mask: set[tuple[str, str]]
) -> set[str]:
    """Undirected neighbor set for ``u``, excluding any edge in ``mask``
    (checked in both orientations)."""
    out: set[str] = set()
    for v in G.successors(u):
        if (u, v) in mask or (v, u) in mask:
            continue
        out.add(v)
    for v in G.predecessors(u):
        if (u, v) in mask or (v, u) in mask:
            continue
        out.add(v)
    return out


def shared_parent_centrality(
    G: nx.DiGraph,
    source_nodes: list[str],
    target_nodes: list[str],
    mask_pairs: Iterable[tuple[str, str]] | None = None,
) -> np.ndarray:
    """Confidence-weighted count of shared neighbors between each (source, target).

    For each (s, t), sums ``conf(s,n) * conf(t,n)`` over every node ``n``
    that is a (masked) neighbor of both. ``mask_pairs`` is a set of
    (u, v) edges to exclude from neighbor lookups (used by leave-one-out
    anchor masking — pass the held-out anchor's edge so its own
    contribution is dropped from the feature).
    """
    mask = set(mask_pairs or ())
    s_nbrs = {s: _masked_neighbors(G, s, mask) for s in source_nodes}
    t_nbrs = {t: _masked_neighbors(G, t, mask) for t in target_nodes}
    M = np.zeros((len(source_nodes), len(target_nodes)), dtype=float)
    for i, s in enumerate(source_nodes):
        sn = s_nbrs[s]
        if not sn:
            continue
        for j, t in enumerate(target_nodes):
            common = sn & t_nbrs[t]
            if not common:
                continue
            score = 0.0
            for n in common:
                score += _edge_conf(G, s, n) * _edge_conf(G, t, n)
            M[i, j] = score
    return M


def compute_structural_features(
    G: nx.DiGraph,
    source_nodes: list[str],
    target_nodes: list[str],
    mask_pairs: Iterable[tuple[str, str]] | None = None,
) -> dict[str, np.ndarray]:
    """Compute the full set of B-1 structural features for a pair of node lists.

    Returns a dict keyed by feature name. As each B-1 feature passes its
    anti-overfit gate it gets added to this dict.
    """
    mask = set(mask_pairs or ())
    return {
        "shared_parent_centrality": shared_parent_centrality(
            G, source_nodes, target_nodes, mask
        ),
    }
