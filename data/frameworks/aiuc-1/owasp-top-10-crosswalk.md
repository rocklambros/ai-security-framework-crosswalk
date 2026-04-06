# AIUC-1 × OWASP Top 10 for LLM Applications Crosswalk

## Overview

AIUC-1 integrates OWASP's Top 10 for LLM and Generative AI by addressing these threats in requirements and controls while strengthening robustness and going beyond security-only focus.

---

## LLM01:25 - Prompt Injection

**OWASP Description:** This manipulates a large language model (LLM) through crafty inputs, causing unintended actions by the LLM. Direct injections overwrite system prompts, while indirect ones manipulate inputs from external sources.

**Relevant AIUC-1 Requirements:**
- B001: Third-party testing of adversarial robustness
- B002: Detect adversarial input
- B005: Implement real-time input filtering

---

## LLM02:25 - Sensitive Information Disclosure

**OWASP Description:** Sensitive info in LLMs includes PII, financial, health, business, security, and legal data. Proprietary models face risks with unique training methods and source code, critical in closed or foundation models.

**Relevant AIUC-1 Requirements:**
- A005: Prevent cross-customer data exposure
- A006: Prevent PII leakage
- B003: Manage public release of technical details
- B004: Prevent AI endpoint scraping
- B007: Enforce user access privileges to AI systems
- B009: Limit output over-exposure

---

## LLM03:25 - Supply Chain

**OWASP Description:** LLM supply chains face risks in training data, models, and platforms, causing bias, breaches, or failures. Unlike traditional software, ML risks include third-party pre-trained models and data vulnerabilities.

**Relevant AIUC-1 Requirements:**
- A004: Protect IP & trade secrets
- A007: Prevent IP violations
- E005: Assess cloud vs on-prem processing
- E006: Conduct vendor due diligence
- E009: Monitor third-party access

---

## LLM04:25 - Data and Model Poisoning

**OWASP Description:** Data poisoning manipulates pre-training, fine-tuning, or embedding data, causing vulnerabilities, biases, or backdoors. Risks include degraded performance, harmful outputs, toxic content, and compromised downstream systems.

**Relevant AIUC-1 Requirements:**
- B001: Third-party testing of adversarial robustness
- B005: Implement real-time input filtering

---

## LLM05:25 - Improper Output Handling

**OWASP Description:** Improper Output Handling involves inadequate validation of LLM outputs before downstream use. Exploits include XSS, CSRF, SSRF, privilege escalation, or remote code execution, which differs from Overreliance.

**Relevant AIUC-1 Requirements:**
- A004: Protect IP & trade secrets
- A005: Prevent cross-customer data exposure
- A006: Prevent PII leakage
- A007: Prevent IP violations
- B001: Third-party testing of adversarial robustness
- B004: Prevent AI endpoint scraping
- B009: Limit output over-exposure
- C003: Prevent harmful outputs
- C004: Prevent out-of-scope outputs
- C005: Prevent customer-defined high risk outputs
- C006: Prevent output vulnerabilities
- D001: Prevent hallucinated outputs
- E009: Monitor third-party access

---

## LLM06:25 - Excessive Agency

**OWASP Description:** LLM systems gain agency via extensions, tools, or plugins to act on prompts. Agents dynamically choose extensions and make repeated LLM calls, using prior outputs to guide subsequent actions for dynamic task execution.

**Relevant AIUC-1 Requirements:**
- A003: Limit AI agent data collection
- B007: Enforce user access privileges to AI systems
- D003: Restrict unsafe tool calls
- D004: Third-party testing of tool calls
- E009: Monitor third-party access

---

## LLM07:25 - System Prompt Leakage

**OWASP Description:** System prompt leakage occurs when sensitive info in LLM prompts is unintentionally exposed, enabling attackers to exploit secrets. These prompts guide model behavior but can unintentionally reveal critical data.

**Relevant AIUC-1 Requirements:**
- B003: Manage public release of technical details
- B008: Protect model deployment environment

---

## LLM08:25 - Vector and Embedding Weaknesses

**OWASP Description:** Vectors and embeddings vulnerabilities in RAG with LLMs allow exploits via weak generation, storage, or retrieval. These can inject harmful content, manipulate outputs, or expose sensitive data, posing significant security risks.

**Relevant AIUC-1 Requirements:**
- A003: Limit AI agent data collection
- A004: Protect IP & trade secrets
- A005: Prevent cross-customer data exposure
- A006: Prevent PII leakage
- B001: Third-party testing of adversarial robustness
- B002: Detect adversarial input
- B004: Prevent AI endpoint scraping
- B006: Prevent unauthorized AI agent actions
- B009: Limit output over-exposure
- D003: Restrict unsafe tool calls

---

## LLM09:25 - Misinformation

**OWASP Description:** LLM misinformation occurs when false and credible outputs mislead users, risking security breaches, reputational harm, and legal liability, making it a critical vulnerability for reliant applications.

**Relevant AIUC-1 Requirements:**
- B009: Limit output over-exposure
- C003: Prevent harmful outputs
- D001: Prevent hallucinated outputs
- D002: Third-party testing for hallucinations

---

## LLM10:25 - Unbounded Consumption

**OWASP Description:** Unbounded Consumption occurs when LLMs generate outputs from inputs, relying on inference to apply learned patterns and knowledge for relevant responses or predictions, making it a key function of LLMs.

**Relevant AIUC-1 Requirements:**
- A003: Limit AI agent data collection
- B002: Detect adversarial input
- B004: Prevent AI endpoint scraping
- B005: Implement real-time input filtering
- B006: Prevent unauthorized AI agent actions
- B007: Enforce user access privileges to AI systems
- D003: Restrict unsafe tool calls
- E009: Monitor third-party access
- E010: Establish AI acceptable use policy
- E015: Log model activity

---

*Source: [AIUC-1 × OWASP Top 10 for LLM Applications Crosswalk](https://www.aiuc-1.com/crosswalks/owasp-top-10)*
*Last updated: July 22, 2025*
