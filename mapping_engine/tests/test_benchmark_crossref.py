"""Smoke test for the crossref ranking benchmark math."""
from __future__ import annotations

import math

from mapping_engine.scripts.benchmark_crossref import rank_metrics


def test_perfect_ranker() -> None:
    ranks = [1, 1, 1]
    m = rank_metrics(ranks)
    assert m["mrr"] == 1.0
    assert m["hit_at_1"] == 1.0
    assert m["hit_at_5"] == 1.0


def test_inverse_ranker() -> None:
    ranks = [10, 10, 10]
    m = rank_metrics(ranks)
    assert math.isclose(m["mrr"], 0.1, abs_tol=1e-9)
    assert m["hit_at_1"] == 0.0
    assert m["hit_at_5"] == 0.0


def test_mixed() -> None:
    ranks = [1, 2, 10]
    m = rank_metrics(ranks)
    assert math.isclose(m["mrr"], (1.0 + 0.5 + 0.1) / 3, abs_tol=1e-9)
    assert math.isclose(m["hit_at_1"], 1 / 3, abs_tol=1e-9)
    assert math.isclose(m["hit_at_5"], 2 / 3, abs_tol=1e-9)


def test_empty() -> None:
    m = rank_metrics([])
    assert m["n"] == 0
    assert m["mrr"] == 0.0
