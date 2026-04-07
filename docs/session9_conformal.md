# Session 9 — Phase C Mondrian Conformal Calibration

alpha=0.1 target coverage=0.90

- n_train=330 n_cal=110 n_test=110
- test coverage = 0.864 (target ≥ 0.90)
- avg prediction-set size = 3.13
- needs_review (set size > 1) rate = 0.873

## Per-class centroids (mean composite score on train)

| Tier | centroid | qhat |
|---|---:|---:|
| None | 0.270 | 0.081 |
| Tangential | 0.283 | 0.084 |
| Related | 0.289 | 0.090 |
| Direct | 0.322 | 0.033 |

This layer replaces the ad-hoc ±0.05 needs_review heuristic with a
Mondrian split-conformal predictor whose per-class non-conformity
quantile gives class-conditional coverage guarantees on the held-out
test slice. Frozen tier_acc is unaffected — the conformal layer
wraps the existing composite score; it does not modify it.

