"""Composite scoring + tier assignment.

Combines bridge / semantic / keyword signals into a single composite score
and assigns a discrete tier per pair using configured thresholds.

Tiers
-----
* ``3`` — Direct        (composite ≥ ``thresholds.direct``)
* ``2`` — Related       (Primary ≥ ``related_primary``;
                          Secondary ≥ ``related_secondary``;
                          GOVERN/DISCLOSE Primary ≥ ``gov_floor`` w/ fn match)
* ``1`` — Tangential    (composite ≥ ``thresholds.tangential``)
* ``0`` — None
"""

from __future__ import annotations

from typing import Any

import numpy as np

TIER_NONE = 0
TIER_TANGENTIAL = 1
TIER_RELATED = 2
TIER_DIRECT = 3


def compose_scores(
    bridge: np.ndarray,
    semantic: np.ndarray,
    keyword: np.ndarray,
    function_match: np.ndarray,
    config: dict[str, Any],
) -> tuple[np.ndarray, np.ndarray]:
    """Combine signals into composite score + tier matrix.

    Parameters
    ----------
    bridge, semantic, keyword, function_match : np.ndarray
        Same-shape ``(n_src, n_tgt)`` matrices in ``[0, 1]``. ``function_match``
        is the binary 0/1 matrix from ``engine.function_match``.
    config : dict
        Merged config; expects ``weights`` and ``thresholds`` blocks.

    Returns
    -------
    composite : np.ndarray
        Final score per pair, capped at 1.0.
    tiers : np.ndarray
        Integer tier matrix (0..3). Caller may pass a relevance matrix to
        ``assign_tiers`` for the Primary/Secondary distinction; this helper
        uses a default relevance of all-Primary.
    """
    w = config.get("weights", {})
    wb = float(w.get("bridge", 0.45))
    ws = float(w.get("semantic", 0.35))
    wk = float(w.get("keyword", 0.20))
    boost = float(w.get("boost", 0.50))

    composite = wb * bridge + ws * semantic + wk * keyword
    composite = composite * (1.0 + boost * function_match)
    composite = np.clip(composite, 0.0, 1.0)

    relevance = np.ones_like(composite, dtype=np.int8)  # default Primary
    tiers = assign_tiers(composite, relevance, config, function_match=function_match)
    return composite, tiers


def assign_tiers(
    composite: np.ndarray,
    relevance: np.ndarray,
    config: dict[str, Any],
    function_match: np.ndarray | None = None,
    function_classes: list[str] | None = None,
) -> np.ndarray:
    """Assign discrete tiers given composite scores and per-pair relevance.

    Parameters
    ----------
    composite : np.ndarray
        Composite scores in ``[0, 1]``.
    relevance : np.ndarray
        Same shape; ``1`` = Primary, ``0`` = Secondary.
    config : dict
        Expects ``thresholds`` block with ``direct``, ``related_primary``,
        ``related_secondary``, ``gov_floor``, ``tangential``.
    function_match : np.ndarray, optional
        Binary fn-match matrix; required for gov_floor promotion.
    function_classes : list[str], optional
        Source-row function classes (length n_src). gov_floor promotion only
        applies to rows whose class is GOVERN or DISCLOSE.
    """
    th = config.get("thresholds", {})
    t_direct = float(th.get("direct", 0.55))
    t_rel_prim = float(th.get("related_primary", 0.35))
    t_rel_sec = float(th.get("related_secondary", 0.50))
    t_gov = float(th.get("gov_floor", 0.22))
    t_tang = float(th.get("tangential", 0.20))

    tiers = np.zeros_like(composite, dtype=np.int8)
    primary = relevance == 1

    # Tangential floor
    tiers[composite >= t_tang] = TIER_TANGENTIAL
    # Related: Secondary needs higher bar than Primary
    tiers[primary & (composite >= t_rel_prim)] = TIER_RELATED
    tiers[(~primary) & (composite >= t_rel_sec)] = TIER_RELATED
    # Direct
    tiers[composite >= t_direct] = TIER_DIRECT

    # gov_floor promotion: GOVERN/DISCLOSE Primary controls with fn match
    if function_match is not None and function_classes is not None:
        gov_rows = np.array(
            [fc in ("GOVERN", "DISCLOSE") for fc in function_classes],
            dtype=bool,
        )
        if gov_rows.any():
            promote = (
                gov_rows[:, None]
                & primary
                & (function_match >= 1.0)
                & (composite >= t_gov)
                & (tiers < TIER_RELATED)
            )
            tiers[promote] = TIER_RELATED

    return tiers
