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


def source_out_degree_ratio(
    G: nx.DiGraph,
    source_nodes: list[str],
    target_nodes: list[str],
    mask_pairs: Iterable[tuple[str, str]] | None = None,
) -> np.ndarray:
    """For each (source, target), the source node's out-degree divided by
    its framework's mean out-degree. Constant across the target axis but
    still emitted as an (n_src, n_tgt) matrix for shape compatibility.

    ``mask_pairs`` excludes specific (u, v) edges from the out-degree
    count so leave-one-out anchor masking can drop the held-out anchor's
    own contribution to the source's degree.
    """
    mask = set(mask_pairs or ())

    def _out_deg(u: str) -> int:
        return sum(1 for v in G.successors(u) if (u, v) not in mask)

    # Group source nodes by framework to compute the per-framework mean.
    by_fw: dict[str, list[str]] = {}
    for s in source_nodes:
        fw = G.nodes[s].get("framework") if s in G else None
        by_fw.setdefault(fw or "_unknown", []).append(s)

    src_deg = {s: _out_deg(s) for s in source_nodes}
    fw_mean: dict[str, float] = {}
    for fw, members in by_fw.items():
        degs = [src_deg[s] for s in members]
        fw_mean[fw] = float(np.mean(degs)) if degs else 0.0

    n_t = len(target_nodes)
    M = np.zeros((len(source_nodes), n_t), dtype=float)
    for i, s in enumerate(source_nodes):
        fw = G.nodes[s].get("framework") if s in G else None
        denom = fw_mean.get(fw or "_unknown", 0.0)
        if denom <= 0:
            ratio = 0.0
        else:
            ratio = src_deg[s] / denom
        M[i, :] = ratio
    return M


_TOKEN_RE = None


def _tokenize(text: str) -> set[str]:
    """Lowercase token set, alphabetic-only, length >= 3, with a tiny stoplist."""
    import re

    global _TOKEN_RE
    if _TOKEN_RE is None:
        _TOKEN_RE = re.compile(r"[A-Za-z]{3,}")
    stop = {
        "the", "and", "for", "with", "that", "this", "are", "not", "you",
        "your", "from", "use", "using", "any", "may", "all", "but", "can",
        "should", "must", "have", "has", "their", "they", "such", "into",
        "across", "based", "via", "non", "per",
    }
    return {t.lower() for t in _TOKEN_RE.findall(text or "") if t.lower() not in stop}


def mitigation_lexical_match(
    G: nx.DiGraph,
    source_nodes: list[str],
    target_nodes: list[str],
    mask_pairs: Iterable[tuple[str, str]] | None = None,
) -> np.ndarray:
    """Token Jaccard between source node's combined text and target's
    ``mitigation_text``. Targets without ``mitigation_text`` contribute 0.

    ``mask_pairs`` is accepted for API uniformity but unused: this feature
    only reads node attributes, not edges, so masking has no effect.
    """
    _ = mask_pairs
    src_tokens: dict[str, set[str]] = {}
    for s in source_nodes:
        if s not in G:
            src_tokens[s] = set()
            continue
        d = G.nodes[s]
        parts = []
        for k in ("name", "title", "description", "objective", "intent", "body"):
            v = d.get(k)
            if v:
                parts.append(str(v))
        src_tokens[s] = _tokenize(" ".join(parts))

    tgt_tokens: dict[str, set[str]] = {}
    for t in target_nodes:
        if t not in G:
            tgt_tokens[t] = set()
            continue
        mt = G.nodes[t].get("mitigation_text") or ""
        tgt_tokens[t] = _tokenize(mt)

    M = np.zeros((len(source_nodes), len(target_nodes)), dtype=float)
    for j, t in enumerate(target_nodes):
        tt = tgt_tokens[t]
        if not tt:
            continue
        for i, s in enumerate(source_nodes):
            st = src_tokens[s]
            if not st:
                continue
            inter = len(st & tt)
            if inter == 0:
                continue
            union = len(st | tt)
            M[i, j] = inter / union
    return M


def confidence_weighted_bridge_depth(
    G: nx.DiGraph,
    source_nodes: list[str],
    target_nodes: list[str],
    mask_pairs: Iterable[tuple[str, str]] | None = None,
) -> np.ndarray:
    """Confidence-weighted 2-hop path count between (source, target).

    For each pair, sums ``conf(source, b) * conf(b, target)`` over every
    intermediate node ``b`` reachable in one hop from source AND in one
    hop to target (in either edge orientation). ``mask_pairs`` excludes
    specific (u, v) edges so the held-out anchor's own edge does not
    contribute via the (source, target) direct path.
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
            tn = t_nbrs[t]
            if not tn:
                continue
            common = sn & tn
            if not common:
                continue
            score = 0.0
            for b in common:
                if b == s or b == t:
                    continue
                score += _edge_conf(G, s, b) * _edge_conf(G, b, t)
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
    # Both shared_parent_centrality (B1.2) and source_out_degree_ratio (B1.3)
    # were dropped after failing their anti-overfit gates. They remain
    # implemented as standalone helpers above so eval_b1_feature can re-test
    # them under future graph topologies, but they are NOT exported via
    # compute_structural_features.
    return {
        "shared_parent_centrality": shared_parent_centrality(
            G, source_nodes, target_nodes, mask
        ),
        "source_out_degree_ratio": source_out_degree_ratio(
            G, source_nodes, target_nodes, mask
        ),
        "mitigation_lexical_match": mitigation_lexical_match(
            G, source_nodes, target_nodes, mask
        ),
        "confidence_weighted_bridge_depth": confidence_weighted_bridge_depth(
            G, source_nodes, target_nodes, mask
        ),
    }
