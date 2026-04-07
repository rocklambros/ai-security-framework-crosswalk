# Anchor rationale: csa_aicm → owasp_agentic

10 anchors selected from the top-15 bridge candidates surfaced by
`add_pair`. Tier vocabulary matches existing pairs (Direct / Related).
Holdout indices `[2, 5, 8]` per repo convention.

| # | source | target | tier | rationale |
|---|---|---|---|---|
| 0 | IAM-04 Separation of Duties | ASI03 Identity & Privilege Abuse | **Direct** | SoD on agent identities directly mitigates privilege escalation along delegation chains |
| 1 | IAM-14 Strong Authentication | ASI03 Identity & Privilege Abuse | **Direct** | Strong auth (MFA, certs) directly mitigates identity abuse and credential replay |
| 2 | IAM-04 Separation of Duties | ASI02 Tool Misuse | **Direct** | *(holdout)* SoD on tool permissions prevents single-actor tool abuse chains |
| 3 | IAM-14 Strong Authentication | ASI02 Tool Misuse | Related | Strong auth on tool endpoints reduces unauthorized tool invocation surface |
| 4 | LOG-05 Audit Log Monitoring | ASI07 Insecure Inter-Agent Comm | Related | Anomaly detection on audit logs catches inter-agent message irregularities |
| 5 | LOG-01 Logging Policy | ASI07 Insecure Inter-Agent Comm | Related | *(holdout)* Logging policy is the substrate for ASI07 detection controls |
| 6 | TVM-12 Threat Modeling | ASI06 Memory & Context Poisoning | Related | Threat modeling identifies memory/RAG attack surfaces; supports but doesn't block |
| 7 | MDS-10 Model Continuous Monitoring | ASI08 Cascading Failures | Related | Continuous monitoring detects drift signatures of cascading failures |
| 8 | MDS-07 Model Hardening | ASI06 Memory & Context Poisoning | Related | *(holdout)* Hardening generally improves robustness to context-injection attacks |
| 9 | DSP-07 Data Protection by Design | ASI02 Tool Misuse | Related | Security-by-design principle encompasses tool-output validation requirements |

**Tier mix:** 3 Direct + 7 Related (matches `aiuc_1__owasp_agentic` style of 7D+3R, inverted ratio reflecting CSA AICM's broader-principle character).

**Coverage:** ASI02, ASI03, ASI06, ASI07, ASI08 (5 of 10 ASI entries). ASI01/04/05/09/10 not anchored — bridge scores didn't surface clear candidates and inventing anchors would risk overfitting.

**Holdouts (`[2, 5, 8]`):** one Direct (IAM-04×ASI02), two Related (LOG-01×ASI07, MDS-07×ASI06). Holdout tests whether the model learns "IAM controls map to identity/tool risks" generalisation without seeing IAM-04×ASI02 specifically.
