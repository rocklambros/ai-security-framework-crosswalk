# AIUC-1 × MITRE ATLAS Crosswalk

## Overview

This page maps MITRE ATLAS mitigation strategies to AIUC-1 requirements. MITRE ATLAS provides a knowledge base of adversarial tactics, techniques and mitigation strategies for machine learning systems.

AIUC-1 integrates ATLAS by incorporating its mitigation strategies into requirements while extending beyond security to address safety and reliability concerns.

---

## Complete MITRE ATLAS Mitigation Crosswalk

| ATLAS ID | Mitigation Strategy | Description | AIUC-1 Mapping |
|----------|-------------------|-------------|-----------------|
| AML-M0000 | Limit Public Release of Information | Restrict technical disclosure about AI stack, organizational details that could enable targeted attacks | B003: Manage public release of technical details |
| AML-M0001 | Limit Model Artifact Release | Prevent public release of data, algorithms, architectures, model checkpoints used in production | B003: Manage public release of technical details |
| AML-M0002 | Passive AI Output Obfuscation | Decrease model output fidelity to reduce adversary ability to extract model information | B009: Limit output over-exposure |
| AML-M0003 | Model Hardening | Apply adversarial training and network distillation techniques for robustness | B001: Third-party testing of adversarial robustness; B002: Detect adversarial input; B004: Prevent AI endpoint scraping |
| AML-M0004 | Restrict Number of AI Model Queries | Limit query rate and volume per user | B001: Third-party testing; B004: Prevent endpoint scraping; D003: Restrict unsafe tool calls |
| AML-M0005 | Control Access to AI Models and Data at Rest | Establish access controls on model registries and training data | B007: Enforce user access privileges; B008: Protect model deployment environment |
| AML-M0006 | Use Ensemble Methods | Deploy multiple models for inference to increase adversarial robustness | *(No directly mapped AIUC-1 requirement)* |
| AML-M0007 | Sanitize Training Data | Detect and remove poisoned training data; implement content filters | *(No directly mapped AIUC-1 requirement)* |
| AML-M0008 | Validate AI Model | Test for backdoors, adversarial bias, concept drift, data tampering | *(No directly mapped AIUC-1 requirement)* |
| AML-M0009 | Use Multi-Modal Sensors | Incorporate multiple sensors to avoid single points of failure | *(No directly mapped AIUC-1 requirement)* |
| AML-M0010 | Input Restoration | Preprocess inference data to neutralize adversarial perturbations | *(No directly mapped AIUC-1 requirement)* |
| AML-M0011 | Restrict Library Loading | Prevent untrusted code loading; secure serialized file handling | *(No directly mapped AIUC-1 requirement)* |
| AML-M0012 | Encrypt Sensitive Information | Encrypt AI models and sensitive data | B008: Protect model deployment environment |
| AML-M0013 | Code Signing | Enforce binary/application integrity via digital signatures to prevent supply chain compromise | E004: Assign accountability |
| AML-M0014 | Verify AI Artifacts | Verify cryptographic checksums of AI artifacts | *(No directly mapped AIUC-1 requirement)* |
| AML-M0015 | Adversarial Input Detection | Detect and block adversarial inputs deviating from benign patterns | B002: Detect adversarial input; B005: Implement real-time input filtering |
| AML-M0016 | Vulnerability Scanning | Scan models and artifacts for exploitable vulnerabilities | C002: Conduct pre-deployment testing |
| AML-M0017 | AI Model Distribution Methods | Serve models in cloud vs. edge to reduce attack surface | E005: Assess cloud vs on-prem processing |
| AML-M0018 | User Training | Educate developers on secure coding and AI vulnerabilities | *(No directly mapped AIUC-1 requirement)* |
| AML-M0019 | Control Access to AI Models and Data in Production | Require authentication; monitor production queries | B007: Enforce user access privileges; B008: Protect model deployment environment |
| AML-M0020 | Generative AI Guardrails | Implement safety controls (filters, validators, classifiers) to prevent undesired inputs/outputs | A004: Protect IP & trade secrets; A006: Prevent PII leakage; A007: Prevent IP violations; C006: Prevent output vulnerabilities; C007: Flag high-risk outputs |
| AML-M0021 | Generative AI Guidelines | Use system prompts and instructions to guide safe model behavior | B002: Detect adversarial input; B005: Implement real-time input filtering |
| AML-M0022 | Generative AI Model Alignment | Apply fine-tuning techniques (SFT, RLHF, targeted safety context) to improve safety alignment | *(No directly mapped AIUC-1 requirement)* |
| AML-M0023 | AI Bill of Materials | Maintain comprehensive listing of artifacts, datasets, and provenance | E017: Document system transparency policy |
| AML-M0024 | AI Telemetry Logging | Implement comprehensive input/output logging of deployed models | B002: Detect adversarial input; D003: Restrict unsafe tool calls; E009: Monitor third-party access; E015: Log model activity |
| AML-M0025 | Maintain AI Dataset Provenance | Document detailed history of datasets including sources and modifications | E017: Document system transparency policy |

---

## Key Integration Points

**AIUC-1 extends ATLAS by:**
- Incorporating ATLAS mitigation strategies into formal requirements
- Strengthening robustness against adversarial tactics identified in ATLAS
- Going beyond ATLAS's security-only focus to address safety and reliability

**Coverage Areas:**
- **Security (B-series):** 10 requirements directly map to ATLAS mitigations
- **Data & Privacy (A-series):** 4 requirements integrate ATLAS guardrails
- **Safety (C-series):** 2 requirements map to testing and output controls
- **Accountability (E-series):** 3 requirements address transparency and logging

---

*Source: [AIUC-1 × MITRE ATLAS Crosswalk](https://www.aiuc-1.com/crosswalks/mitre-atlas)*
*Last updated: July 22, 2025*
