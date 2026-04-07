"""Generalized graph-neighborhood bridge signal (2-hop weighted Jaccard).

Design notes (Session 1, sequential-thinking summary)
-----------------------------------------------------
The v1 pipeline computed a brittle Jaccard over a tiny shared vocabulary
(OWASP LLM Top 10 references cited in both source and target). v2 generalizes
that to **the full crosswalk graph**: every neighbor reachable within
``max_hops`` becomes a vocabulary token, with weights derived from edge
confidence and an inverse-distance hop penalty.

Decisions:

1. **Undirected neighborhood.** Cross-framework rationale codes are
   semantically symmetric for similarity purposes. We BFS on
   ``H.to_undirected()`` so that an inbound MAPS_TO and an outbound
   REFERENCES both contribute.
2. **PARENT exclusion.** PARENT edges encode within-framework document
   hierarchy and would create artificial "shared parent" overlap between
   sibling controls. They are removed before BFS via
   ``exclude_edge_types`` (default ``["PARENT"]``).
3. **Confidence × hop decay.** A 1-hop neighbor is weighted by its edge
   confidence (authoritative=1.0, expert=0.8, inferred=0.4, unvalidated=0.2);
   a 2-hop neighbor is weighted by ``min(c1, c2) * 0.5`` (weakest-link
   confidence times the hop decay). When multiple paths reach the same
   neighbor, the **maximum** weight wins (1-hop always beats 2-hop).
4. **Weighted Jaccard.** ``sim = sum_n min(wA[n], wB[n]) / sum_n max(wA[n], wB[n])``.
   Returns 0.0 when either neighborhood is empty.
5. **Why not include the target itself in source's neighborhood?** Direct
   edges still contribute via *mutual* third-party neighbors and via the
   reciprocal weights both nodes assign — the algorithm rewards them
   correctly without trivial self-inclusion.
"""

from __future__ import annotations

from collections import deque
from typing import Iterable, Sequence

import networkx as nx
import numpy as np

DEFAULT_CONFIDENCE_WEIGHTS: dict[str, float] = {
    "authoritative": 1.0,
    "expert": 0.8,
    "inferred": 0.4,
    "unvalidated": 0.2,
}
DEFAULT_EXCLUDE_EDGE_TYPES: tuple[str, ...] = ("PARENT",)


def _filtered_undirected(G: nx.DiGraph, exclude_edge_types: Iterable[str]) -> nx.Graph:
    """Return an undirected view of G with edges whose rationale_code is excluded removed.

    Parallel directed edges collapse: we keep the **max** confidence weight tag
    on the resulting undirected edge so BFS sees the strongest path.
    """
    excl = set(exclude_edge_types)
    H: nx.Graph = nx.Graph()
    H.add_nodes_from(G.nodes(data=True))
    for u, v, data in G.edges(data=True):
        if data.get("rationale_code") in excl:
            continue
        # confidence label preserved; if duplicate, keep the higher weight one
        if H.has_edge(u, v):
            existing = H[u][v].get("confidence")
            existing_w = DEFAULT_CONFIDENCE_WEIGHTS.get(existing, 0.0)
            new_w = DEFAULT_CONFIDENCE_WEIGHTS.get(data.get("confidence"), 0.0)
            if new_w > existing_w:
                H[u][v]["confidence"] = data.get("confidence")
        else:
            H.add_edge(u, v, confidence=data.get("confidence"))
    return H


def _neighborhood(
    H: nx.Graph,
    start: str,
    max_hops: int,
    confidence_weights: dict[str, float],
) -> dict[str, float]:
    """BFS-weighted neighborhood: {neighbor_id -> max weight reachable}.

    Hop decay = 0.5 ** (hop_distance - 1). Edge weight = confidence_weights[label].
    On a 2-hop path the weakest edge confidence is used (min).
    """
    if start not in H:
        return {}
    weights: dict[str, float] = {}
    # queue items: (node, hop, min_conf_weight_along_path)
    visited: dict[str, int] = {start: 0}
    q: deque[tuple[str, int, float]] = deque([(start, 0, 1.0)])
    while q:
        node, hop, path_min_w = q.popleft()
        if hop == max_hops:
            continue
        for nbr in H.neighbors(node):
            edge_w = confidence_weights.get(H[node][nbr].get("confidence"), 0.0)
            if edge_w <= 0.0:
                continue
            new_min = min(path_min_w, edge_w) if hop > 0 else edge_w
            new_hop = hop + 1
            decay = 0.5 ** (new_hop - 1)
            cand = new_min * decay
            if nbr == start:
                continue
            prev = weights.get(nbr, -1.0)
            if cand > prev:
                weights[nbr] = cand
            # only enqueue if we haven't visited at a shallower depth
            if nbr not in visited or visited[nbr] > new_hop:
                visited[nbr] = new_hop
                if new_hop < max_hops:
                    q.append((nbr, new_hop, new_min))
    return weights


def _weighted_jaccard(a: dict[str, float], b: dict[str, float]) -> float:
    if not a or not b:
        return 0.0
    keys = set(a) | set(b)
    inter = 0.0
    union = 0.0
    for k in keys:
        wa = a.get(k, 0.0)
        wb = b.get(k, 0.0)
        inter += min(wa, wb)
        union += max(wa, wb)
    return inter / union if union > 0 else 0.0


def graph_bridge_scores(
    G: nx.DiGraph,
    source_nodes: Sequence[str],
    target_nodes: Sequence[str],
    config: dict | None = None,
) -> np.ndarray:
    """Compute the 2-hop weighted-Jaccard bridge matrix.

    Parameters
    ----------
    G : nx.DiGraph
        The full crosswalk graph.
    source_nodes, target_nodes : sequences of node_id
        Rows / columns of the returned matrix.
    config : dict, optional
        Keys: ``max_hops`` (int, default 2), ``confidence_weights`` (dict),
        ``exclude_edge_types`` (iterable, default ``["PARENT"]``).

    Returns
    -------
    np.ndarray of shape (len(source_nodes), len(target_nodes))
    """
    cfg = config or {}
    max_hops: int = int(cfg.get("max_hops", 2))
    cw: dict[str, float] = dict(cfg.get("confidence_weights", DEFAULT_CONFIDENCE_WEIGHTS))
    excl = cfg.get("exclude_edge_types", DEFAULT_EXCLUDE_EDGE_TYPES)

    H = _filtered_undirected(G, excl)

    src_nbrs = {s: _neighborhood(H, s, max_hops, cw) for s in source_nodes}
    tgt_nbrs = {t: _neighborhood(H, t, max_hops, cw) for t in target_nodes}

    M = np.zeros((len(source_nodes), len(target_nodes)), dtype=np.float64)
    for i, s in enumerate(source_nodes):
        a = src_nbrs[s]
        if not a:
            continue
        for j, t in enumerate(target_nodes):
            M[i, j] = _weighted_jaccard(a, tgt_nbrs[t])
    return M
