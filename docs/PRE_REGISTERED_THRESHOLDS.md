# Pre-Registered Success Thresholds

**Committed:** $(git rev-parse HEAD ≤ this commit) on 2026-04-07
**Purpose:** Protect against p-hacking by declaring paper framings before any training run.

## Primary headline: Recall@3 on `human_test_frozen` (400 pairs)

| Threshold | Paper framing |
|---|---|
| Recall@3 ≥ 0.80 | State of the art — full best-in-class framing |
| 0.70 ≤ Recall@3 < 0.80 | Competitive — strong baseline + honest limitations paper |
| 0.55 ≤ Recall@3 < 0.70 | Partial success — error analysis as main contribution |
| Recall@3 < 0.55 | Negative result — blog post only, no arXiv |

## Co-headline: Precision@80% coverage (Mondrian conformal)

Reported jointly with Recall@3. No pre-registered threshold — reported as-is with bootstrap CI.

## Independent verification: `human_test_fresh` (75 pairs)

If fresh-75 metrics fall more than 10 pp below frozen-400 metrics on Recall@3, paper reports the gap and adjusts framing.

## The sacred-run rule

`human_test_frozen` is touched exactly once. No retries. If results disappoint, reframe; do not retune.

## Non-negotiable reporting

1. Sonnet↔Opus κ on tier labels (whatever it is)
2. Raw vs calibrated LLM label metrics in appendix
3. Retrieval-floor coverage
4. Every failed ablation
5. Budget + wall-clock in appendix
