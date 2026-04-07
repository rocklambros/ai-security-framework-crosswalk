"""Unit tests for the discriminative metric module."""

from __future__ import annotations

import numpy as np
import pytest

from mapping_engine.calibration.discriminative_metric import (
    bootstrap_ci,
    paired_bootstrap_delta,
    score,
)


def test_perfect_separation_yields_mrr_one_and_auc_one():
    pos = [0.9, 0.8, 0.7]
    dist = [[0.1, 0.2, 0.3], [0.05, 0.1], [0.0, 0.1, 0.2]]
    s = score(pos, dist)
    assert s.mrr == pytest.approx(1.0)
    assert s.recall_at_5 == pytest.approx(1.0)
    assert s.roc_auc == pytest.approx(1.0)
    assert s.n_anchors == 3


def test_inverted_separation_yields_low_mrr_and_zero_auc():
    pos = [0.1, 0.05]
    dist = [[0.9, 0.8, 0.7], [0.6, 0.7, 0.8]]
    s = score(pos, dist)
    # Positive ranks last among 4 candidates, so RR = 1/4 each
    assert s.mrr == pytest.approx(0.25)
    assert s.recall_at_5 == pytest.approx(1.0)  # 4 candidates fits in top 5
    assert s.roc_auc == pytest.approx(0.0)


def test_pessimistic_tie_break():
    # Positive ties with one distractor; pessimistic = positive ranks below.
    pos = [0.5]
    dist = [[0.5, 0.1, 0.1]]
    s = score(pos, dist)
    # 1 distractor tied -> rank = 1 + 0 above + 1 tied = 2 -> RR = 0.5
    assert s.mrr == pytest.approx(0.5)


def test_random_uniform_auc_near_half():
    rng = np.random.default_rng(0)
    n = 200
    pos = rng.uniform(size=n).tolist()
    dist = [rng.uniform(size=20).tolist() for _ in range(n)]
    s = score(pos, dist)
    assert 0.4 < s.roc_auc < 0.6


def test_recall_at_5_threshold():
    # Positive must rank in top 5 to count.
    pos = [0.5, 0.5]
    dist = [
        [0.9, 0.8, 0.7, 0.6, 0.55, 0.4],  # 5 above -> rank 6 -> miss
        [0.9, 0.8, 0.7, 0.6, 0.4],         # 4 above -> rank 5 -> hit
    ]
    s = score(pos, dist)
    assert s.recall_at_5 == pytest.approx(0.5)


def test_bootstrap_ci_width_shrinks_with_more_anchors():
    rng = np.random.default_rng(1)
    short_pos = rng.uniform(0.6, 1.0, size=10).tolist()
    short_dist = [rng.uniform(0.0, 0.4, size=20).tolist() for _ in range(10)]
    long_pos = rng.uniform(0.6, 1.0, size=200).tolist()
    long_dist = [rng.uniform(0.0, 0.4, size=20).tolist() for _ in range(200)]
    short_ci = bootstrap_ci(short_pos, short_dist, n_resamples=300, rng_seed=2)
    long_ci = bootstrap_ci(long_pos, long_dist, n_resamples=300, rng_seed=2)
    short_w = short_ci["mrr"][2] - short_ci["mrr"][1]
    long_w = long_ci["mrr"][2] - long_ci["mrr"][1]
    assert long_w <= short_w


def test_bootstrap_ci_returns_n_resamples_field():
    pos = [0.9]
    dist = [[0.1, 0.2]]
    out = bootstrap_ci(pos, dist, n_resamples=100, rng_seed=3)
    assert out["n_resamples"] == 100
    assert "mrr" in out and "recall_at_5" in out and "roc_auc" in out


def test_paired_delta_detects_real_improvement():
    rng = np.random.default_rng(4)
    n = 100
    # pos_b sits inside the distractor cloud; pos_a is lifted above it.
    pos_b = rng.uniform(0.3, 0.5, size=n).tolist()
    pos_a = (np.array(pos_b) + 0.5).tolist()
    dist_b = [rng.uniform(0.2, 0.7, size=10).tolist() for _ in range(n)]
    dist_a = dist_b
    out = paired_bootstrap_delta(pos_a, dist_a, pos_b, dist_b, n_resamples=300, rng_seed=5)
    assert out["delta_mrr_mean"] > 0
    assert out["ci_excludes_zero"] is True


def test_paired_delta_zero_under_identity():
    pos = [0.5, 0.6, 0.7]
    dist = [[0.1, 0.2], [0.1, 0.3], [0.4, 0.5]]
    out = paired_bootstrap_delta(pos, dist, pos, dist, n_resamples=200, rng_seed=6)
    assert out["delta_mrr_mean"] == pytest.approx(0.0)
    assert out["ci_excludes_zero"] is False


def test_score_length_mismatch_raises():
    with pytest.raises(ValueError):
        score([0.5, 0.6], [[0.1, 0.2]])
