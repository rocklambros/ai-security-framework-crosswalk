# Session 9 — Phase E LambdaMART (XGBoost rank:pairwise, GPU)

Feature stack: [bridge, semantic, keyword, function_match, composite, uncertainty] over the 550 unified SME labels (400 S7 + 150 S8).
Cross-validation: group-K-fold by pair (k=5) — every fold trains on pairs the model has not seen, evaluates on the held-out pairs. This is the honest cross-pair generalization estimate.

## Aggregate (macro NDCG@5 across pairs)

| signal | macro NDCG@5 |
|---|---:|
| composite (baseline) | 0.5126 |
| LambdaMART (group-CV held-out) | 0.5902 |
| LambdaMART (train pairs, in-sample) | 0.8989 |

- delta vs baseline = **+0.0776**
- train/held-out gap = **+0.3087**
- decision rule: adopt if delta ≥ +0.02 AND gap < 0.10
- **DECISION: REJECT**

## Per-pair (held-out group-CV)

| pair | baseline | LambdaMART | delta |
|---|---:|---:|---:|
| aiuc_1__csa_aicm | 0.1798 | 0.6258 | +0.4461 |
| aiuc_1__eu_gpai_cop | 0.4286 | 0.5508 | +0.1223 |
| aiuc_1__mitre_atlas | 0.3712 | 0.6992 | +0.3280 |
| aiuc_1__nist_rmf | 0.4286 | 0.7193 | +0.2907 |
| aiuc_1__owasp_agentic | 0.3660 | 0.6489 | +0.2829 |
| aiuc_1__owasp_llm | 0.6775 | 0.5870 | -0.0905 |
| cosai_rm__mitre_atlas | 0.5508 | 0.5255 | -0.0254 |
| cosai_rm__owasp_llm | 0.6608 | 0.8281 | +0.1673 |
| csa_aicm__owasp_agentic | 0.7719 | 0.7537 | -0.0182 |
| mitre_atlas__owasp_llm | 0.5563 | 0.1395 | -0.4168 |
| nist_rmf__owasp_agentic | 0.6469 | 0.4138 | -0.2331 |

## Interpretation
These NDCG@5 values are computed against the *uncertainty-sampled* candidate pool, not the full candidate matrix — the active learner deliberately selected the cases where the production composite was least confident. NDCG values are correspondingly low across the board; what matters here is the relative comparison and the train/held-out gap.

Result: LambdaMART beats the composite baseline by +0.0776 on held-out pairs, with a train/held-out gap of +0.3087. Overfit detected.
Per the s9-uh prompt rule (delta ≥ +0.02 AND gap < 0.10), the booster is **REJECT**.

Documented as rejected per s10/s11/s13 pattern; production composite is unchanged. The XGBoost-GPU pipeline and feature stack are committed for future re-use once a non-uncertainty-biased eval set is available.

