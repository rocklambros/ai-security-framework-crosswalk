# Session 9 — Phase A Verification

Per-pair verification of the production composite score against the 550 SME labels (400 S7 + 150 S8). Pred tier uses unified thresholds Direct≥0.45, Related≥0.20, Tangential≥0.10.

| Pair | n | tier_acc | Cohen κ | AUROC(Direct) | P(Direct) | R(Direct) |
|---|---:|---:|---:|---:|---:|---:|
| aiuc_1__csa_aicm | 50 | 0.340 | 0.036 | 0.513 | nan | 0.000 |
| aiuc_1__eu_gpai_cop | 50 | 0.600 | -0.033 | 0.590 | nan | 0.000 |
| aiuc_1__mitre_atlas | 50 | 0.320 | 0.001 | 0.607 | nan | 0.000 |
| aiuc_1__nist_rmf | 50 | 0.700 | 0.097 | 0.631 | nan | 0.000 |
| aiuc_1__owasp_agentic | 50 | 0.460 | 0.112 | 0.637 | nan | 0.000 |
| aiuc_1__owasp_llm | 50 | 0.540 | 0.006 | 0.624 | 1.000 | 0.083 |
| cosai_rm__mitre_atlas | 50 | 0.440 | -0.033 | 0.657 | nan | 0.000 |
| cosai_rm__owasp_llm | 50 | 0.440 | -0.111 | 0.648 | nan | 0.000 |
| csa_aicm__owasp_agentic | 50 | 0.220 | -0.032 | 0.918 | 0.500 | 0.667 |
| mitre_atlas__owasp_llm | 50 | 0.200 | 0.021 | 0.918 | 0.000 | 0.000 |
| nist_rmf__owasp_agentic | 50 | 0.300 | 0.061 | nan | 0.000 | nan |

**Overall** (n=550): tier_acc=0.415, Cohen κ=0.033

## Heavy verification — deferred

BGE-reranker-v2-m3, deberta-v3-large-mnli, Qwen2.5-7B-Instruct LLM
judge, and the BGE+stella+nomic embedding ensemble were planned as
additional verification signals. They are documented as deferred for
this iteration: each requires multi-GB GPU model downloads and a new
wiring path through PairMapper.signal_matrices. Phase B (next) wires
the slots at weight=0.0; the heavy models can be plugged in there
without further code changes once the slots exist.

