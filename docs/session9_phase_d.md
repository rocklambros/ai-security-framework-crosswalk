# Session 9 — Phase D BGE-reranker-v2-m3 vs ms-marco-MiniLM (per-pair A/B)

GPU scoring of 550 SME-labeled candidates with both cross-encoders, blended into the composite at production weight 0.1, evaluated by per-pair tier_acc.

## Per-pair tier_acc

| pair | baseline | MiniLM (blend) | BGE-v2-m3 (blend) | decision |
|---|---:|---:|---:|---|
| aiuc_1__csa_aicm | 0.340 | 0.380 | 0.340 | KEEP_MiniLM |
| aiuc_1__eu_gpai_cop | 0.600 | 0.540 | 0.520 | KEEP_MiniLM |
| aiuc_1__mitre_atlas | 0.320 | 0.300 | 0.240 | KEEP_MiniLM |
| aiuc_1__nist_rmf | 0.700 | 0.600 | 0.580 | KEEP_MiniLM |
| aiuc_1__owasp_agentic | 0.460 | 0.380 | 0.400 | ADOPT_v2_m3 |
| aiuc_1__owasp_llm | 0.540 | 0.600 | 0.380 | KEEP_MiniLM |
| cosai_rm__mitre_atlas | 0.440 | 0.360 | 0.340 | KEEP_MiniLM |
| cosai_rm__owasp_llm | 0.440 | 0.600 | 0.340 | KEEP_MiniLM |
| csa_aicm__owasp_agentic | 0.220 | 0.220 | 0.240 | ADOPT_v2_m3 |
| mitre_atlas__owasp_llm | 0.200 | 0.200 | 0.200 | ADOPT_v2_m3 |
| nist_rmf__owasp_agentic | 0.300 | 0.160 | 0.440 | ADOPT_v2_m3 |

**Macro**: baseline=0.415 MiniLM=0.395 BGE-v2-m3=0.365

**Adoption**: 4/11 pairs would switch to BGE-reranker-v2-m3 under non-inferiority rule (v2 ≥ MiniLM − 0.01).

## Note on the labels
The 550 SME labels are uncertainty-sampled — the active learner deliberately picked the cases where the production composite was least confident. tier_acc on this pool is correspondingly low and should not be read as overall mapper accuracy. What matters here is the *relative* per-pair comparison, which is what drives the per-pair toggle decision.

