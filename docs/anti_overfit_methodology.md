# Anti-Overfit Methodology

This document codifies the methodology used to prevent overfitting during the B-2 / B-1 / A rebuild of the mapping engine. Every feature added, model trained, or threshold tuned must satisfy these gates before being merged. The plan that drives this work lives at `~/.claude/projects/-home-rock-github-projects-ai-security-framework-crosswalk/memory/project_b2_b1_a_rebuild_plan.md`.

## Why this exists

Earlier phases of the rebuild discovered that the integration test was passing at 1.0 holdout accuracy via a label lookup (the now-deleted `_apply_expert_edge_floor`). After removing the leakage, honest holdout accuracy dropped to 0.667 with N=10 anchors. At that sample size, every "improvement" risks being noise. This methodology exists so we can tell signal from noise, and so we never again ship a model that looks good for the wrong reason.

## The 10 principles

### 1. Pre-registration

Before running cross-validation on any new feature or model change, write a hypothesis to `docs/anti_overfit_hypotheses.md` containing:

- **Direction of effect.** Which metric will move, and which way?
- **Minimum effect size.** What absolute delta on the chosen metric counts as a "real" improvement (not just noise)?
- **Metric.** Aggregate CV NDCG@10, per-pair tier accuracy, etc.
- **Decision rule.** What outcome causes the feature to be kept vs dropped?

Pre-registration prevents post-hoc rationalization. If the result doesn't match the hypothesis, the feature gets dropped or the hypothesis was wrong — both are honest outcomes. Re-running CV until you get the answer you wanted is forbidden.

### 2. Bootstrap 95% CI on every reported metric

Every metric — CV accuracy, NDCG@10, Spearman, tier accuracy, anchor holdout — gets a 1000-resample bootstrap confidence interval. Implementation lives in `mapping_engine/calibration/diagnostics.py::bootstrap_ci`.

**Decision rule for improvements:** an improvement only counts if the bootstrap CI on the *delta* (new − baseline) excludes 0. A point estimate that's higher but with a CI that crosses 0 is noise.

### 3. Permutation importance with CI

After fitting any model, compute permutation importance per feature with `n_repeats=20` and bootstrap CI. Implementation: `mapping_engine/calibration/diagnostics.py::permutation_importance_ci`.

**Decision rule:** drop any feature whose importance CI overlaps zero. Such a feature is not contributing signal beyond what other features already provide; keeping it adds variance without value.

### 4. Per-fold variance reported alongside means

Every CV report includes the standard deviation across folds, not just the mean. High variance (stddev > 0.1 on a 0–1 metric) is a warning that the result is unreliable regardless of how good the mean looks.

### 5. Learning curve at phase end

Plot CV score vs training fraction (e.g., 20%, 40%, 60%, 80%, 100%). Implementation: `mapping_engine/calibration/diagnostics.py::learning_curve`.

Diagnoses:
- **Still rising at 100%:** underfit / data-limited regime. More data would help.
- **Flat and high:** good fit.
- **Large train-vs-CV gap:** overfit. Need regularization, fewer features, or more data.

### 6. Reliability diagram at phase end

Plot predicted-tier vs observed-tier on CV in `n_bins=10` bins. Implementation: `mapping_engine/calibration/diagnostics.py::reliability_curve`.

A diagonal means the model is well-calibrated. Skew (predicted > observed or vice versa) indicates miscalibration that may need isotonic or Platt scaling — but adding a calibration layer is itself a feature change and gets the same gates.

### 7. Compare to baselines

Every change is compared against four baselines:
- **Random.** Uniform-random tier assignment.
- **Majority class.** Always predict the most common tier.
- **Hand-tuned.** The original `defaults.yaml` weights and thresholds.
- **Previous-phase model.** The current best model before this change.

A change that doesn't beat all four baselines (with CI) is rejected.

### 8. Ablation matrix

At the end of B-1, evaluate all 2^k feature subsets where k is the number of structural features added. Report the best subset by aggregate CV NDCG@10 with paired bootstrap CI vs the full feature set.

If the best subset is significantly smaller than the full set, the larger model is overparameterized — prune `FEATURES` to the winning subset.

### 9. Frozen test set discipline

Three framework pairs are reserved as single-shot test sets, one per phase:

- **Phase B-2:** `aiuc_1` → `csa_aicm`
- **Phase B-1:** `aiuc_1` → `mitre_atlas`
- **Phase A:** `aiuc_1` → `cosai_rm`

These pairs are off-limits to any feature/threshold/model decision during their phase. They are touched exactly once, at the end of the phase, and the result is recorded in `docs/frozen_test_results.md` regardless of whether it's good or bad.

**No retuning after seeing the frozen test.** If a frozen test fails, document the failure and stop. Do NOT loop back and tune until it passes — that's data leakage with extra steps.

### 10. Regularization defaults

To bias every model toward simplicity:

- **Logistic regression.** L2 penalty `C=1.0` by default. If CV variance is high (stddev > 0.1), increase regularization to `C=0.5` or `C=0.1`.
- **LightGBM.** `num_leaves ≤ 15`, `min_data_in_leaf ≥ 5`, `max_depth ≤ 4`. Early stopping on validation logloss.
- **Cross-encoder fine-tune.** Early stopping on validation NDCG@10 with `patience=2`. Save the best epoch checkpoint.
- **Threshold sweep.** Coarse grid (5–6 points per dimension), not fine. Fine-grained sweeps overfit the training anchors.

## Anti-patterns to refuse

1. **"Just one more retune."** If you've already evaluated against CV and the result is what it is, do not re-run with different hyperparameters until it improves. That's manual hyperparameter tuning on the validation set and it overfits.
2. **"This pair is special."** If a single anchor pair is the difference between passing and failing, the gate is wrong, not the data. A gate that depends on one pair is brittle.
3. **"The CI just barely crosses zero."** If the CI crosses zero, the improvement is not statistically significant. Period. "Almost significant" is not significant.
4. **"Let's see what happens if we look at the frozen test before we're done."** Never. The frozen test exists precisely so we cannot tune to it.
5. **"It's only a small change to the threshold."** Even small changes get the full gate treatment. Death by a thousand cuts is the most common form of overfitting in calibration work.

## What to do when a gate fails

A failed gate is a successful experiment, not a failure. The protocol:

1. Record the negative result in the commit body.
2. Drop the feature / revert the change.
3. Mark the corresponding plan task as complete (`[x]`) — the work was done, the answer was "no".
4. Move on. Do not re-run with tweaked parameters trying to flip the result.

This is the discipline that distinguishes "model that works" from "model that looks like it works."
