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


def compute_structural_features(
    G: nx.DiGraph,
    source_nodes: list[str],
    target_nodes: list[str],
    mask_pairs: Iterable[tuple[str, str]] | None = None,
) -> dict[str, np.ndarray]:
    """Compute the full set of B-1 structural features for a pair of node lists.

    Returns a dict keyed by feature name. The skeleton (B1.0) returns an
    empty dict; B1.1+ will populate it incrementally as each feature
    passes its anti-overfit gate.
    """
    _ = (G, source_nodes, target_nodes, set(mask_pairs or ()))
    return {}
