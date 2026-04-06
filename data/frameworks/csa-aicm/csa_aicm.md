# CSA AI Controls Matrix (AICM) v1.0.3

Source: https://cloudsecurityalliance.org/artifacts/ai-controls-matrix
License: CSA License (free download)
Retrieved: 2026-04-05
Total Controls: 243
Total Domains: 18

---

# Domains

1. Audit & Assurance (6 controls)
2. Application & Interface Security (15 controls)
3. Business Continuity Management and Operational Resilience (11 controls)
4. Change Control and Configuration Management (9 controls)
5. Cryptography, Encryption & Key Management (21 controls)
6. Datacenter Security (15 controls)
7. Data Security and Privacy Lifecycle Management (24 controls)
8. Governance, Risk and Compliance (15 controls)
9. Human Resources (15 controls)
10. Identity & Access Management (19 controls)
11. Interoperability & Portability (4 controls)
12. Infrastructure Security (9 controls)
13. Logging and Monitoring (15 controls)
14. Model Security (13 controls)
15. Security Incident Management, E-Discovery, & Cloud Forensics (9 controls)
16. Supply Chain Management, Transparency, and Accountability (16 controls)
17. Threat & Vulnerability Management (13 controls)
18. Universal Endpoint Management (14 controls)

---

# Domain: Audit & Assurance

## A&A-01: Audit and Assurance Policy and Procedures

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared across the supply chain
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Owned by the Orchestrated Service Provider (OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data collection, Data curation, Data storage
- Development: Design, Guardrails, Training
- Evaluation/Validation: Evaluation, Validation/Red Teaming, Re-evaluation
- Deployment: AI Services supply chain
- Delivery: Continuous improvement
- Service Retirement: Data deletion, Archiving, Model disposal

### Specification

Establish, document, approve, communicate, apply, evaluate and maintain audit and assurance policies and procedures and standards. Review and update the policies and procedures at least annually or upon significant changes.

### Cross-References

- **bsi_aic4**: COM-02
SP-01
SP-02 (Gap: No Gap)
- **eu_ai_act**: Recital 81
Recital 123
Recital 125
Article 17 (1) (a)
Article 43 (1), (2 - 4)
Annex VI (1 - 4)
Annex VII (1 -5) (Gap: No Gap)
- **iso_42001**: 42001: 9.2.1 General - Internal audit
42001: 9.2.2 Internal audit program
42001: 9.3 Management Review
42001: A.2.2 AI policy
42001: A.2.3 Alignment with other organizational policies
42001: A.2.4 Review of the AI policy
27001: 9.3 Management Review
27001: 9.2.1 General - Internal Audit
27001: 9.2.2 Internal audit programme
27001: A.5.1 Policies for information security
27002: 5.1 Policies for information security (Gap: No Gap)
- **nist_ai_600_1**: GV-1.1-001
GV-4.1-001
GV-4.2-001 (Gap: Partial Gap)

### CAIQ Questions

- **A&A-01.1**: Are audit and assurance policies, procedures, and standards 
established, documented, approved, communicated, applied, 
evaluated, and maintained?
- **A&A-01.2**: Are audit and assurance policies, procedures, and standards 
reviewed and updated at least annually or upon significant changes?

---

## A&A-02: Independent Assessments

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared across the supply chain
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Owned by the Orchestrated Service Provider (OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data collection, Data curation, Data storage
- Development: Design, Training, Guardrails
- Evaluation/Validation: Evaluation, Validation/Red Teaming, Re-evaluation
- Deployment: AI Services supply chain, AI applications, Orchestration
- Delivery: Continuous monitoring, Continuous improvement, Operations, Maintenance
- Service Retirement: Data deletion, Model disposal, Archiving

### Specification

Conduct independent audit and assurance assessments according to relevant standards at least annually.

### Cross-References

- **bsi_aic4**: COM-03
OIS-01 Additional Criteria (Gap: No Gap)
- **eu_ai_act**: Article 21 (1)
Article 43 (2)
Article 43 (3)
Article 93 (1) (Gap: Partial Gap)
- **iso_42001**: 42001: 9.2.1 General  -  Internal audit
42001: 9.2.2 Internal audit program
27001: A.5.35 Independent review of information security
27001: A.5.36 Compliance with policies
rules and standards for information security
27002: 5.35 Independent review of information security
27002: 5.36 Compliance with policies
rules and standards for information security (Gap: No Gap)
- **nist_ai_600_1**: MP-5.1-005
GV-3.2-001 (Gap: No Gap)

### CAIQ Questions

- **A&A-02.1**: Are independent audit and assurance assessments conducted according to relevant standards at least annually?

---

## A&A-03: Risk Based Planning Assessment

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Owned by the Orchestrated Service Provider (OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data collection, Data curation, Data storage
- Development: Design, Training, Guardrails
- Evaluation/Validation: Evaluation, Validation/Red Teaming, Re-evaluation
- Deployment: AI Services supply chain, AI applications
- Delivery: Continuous improvement
- Service Retirement: Archiving, Data deletion, Model disposal

### Specification

Perform independent audit and assurance assessments in response to significant changes or emerging risks and according to risk-based plans and policies.

### Cross-References

- **bsi_aic4**: COM-02
COM-03 (Gap: Partial Gap)
- **eu_ai_act**: Article 9 (2)
Article 9 (6)
Article 43 (1)
Article 43 (4)
Article 93
Article 17 (Gap: Partial Gap)
- **iso_42001**: 42001: 9.2.1 General - Internal audit
42001: 9.2.2 Internal audit program
42001: 10.2 Nonconformity
27001: 9.2.1 General - Internal audit
27001: 9.2.2 Internal audit programme
27001: A.5.35 Independent review of information security
27001: A.5.36 Compliance with policies
rules and standards for
information security
27002: 5.35 Independent review of information security
27002: 5.36 Compliance with policies
rules and standards for information
security (Gap: Partial Gap)
- **nist_ai_600_1**: GV-2.2-004
GV-6.1-006
MGP-1.1-003
MGP-1.2-004 (Gap: Partial Gap)

### CAIQ Questions

- **A&A-03.1**: Are independent audit and assurance assessments performed in response to significant changes or emerging risks and according to risk-based plans and policies?

---

## A&A-04: Requirements Compliance

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Owned by the Orchestrated Service Provider (OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data collection, Data curation, Data storage
- Development: Design, Training, Guardrails
- Evaluation/Validation: Evaluation, Validation/Red Teaming, Re-evaluation
- Deployment: AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous improvement
- Service Retirement: Archiving, Data deletion, Model disposal

### Specification

Verify compliance with all relevant standards, regulations, legal/contractual, and statutory requirements applicable to the audit.

### Cross-References

- **bsi_aic4**: COM-01 (Gap: No Gap)
- **eu_ai_act**: Article 8
Article 43
Article 53
Article 55 (Gap: No Gap)
- **iso_42001**: 42001: 8.2.1(a) Compliance with legal and regulatory requirements
42001: 9.2.1 General
27001: 9.2.1 General
27001: A 5.31 Legal
statutory
regulatory and contractual requirements
27002: 5.31 Legal
statutory
regulatory and contractual requirements (Gap: No Gap)
- **nist_ai_600_1**: GV-1.1-001 (Gap: No Gap)

### CAIQ Questions

- **A&A-04.1**: Is compliance verified with all relevant standards, regulations, legal/contractual, and statutory requirements applicable to the audit?

---

## A&A-05: Audit Management Process

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Owned by the Orchestrated Service Provider (OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: N/A
- Development: Guardrails
- Evaluation/Validation: Evaluation, Validation/Red Teaming, Re-evaluation
- Deployment: AI Services supply chain, AI applications
- Delivery: Continuous improvement, Operations, Maintenance, Continuous monitoring
- Service Retirement: Archiving, Data deletion, Model disposal

### Specification

Define and implement an Audit Management process aligned with global auditing standards, to support audit planning, risk analysis, security control assessment, conclusion, remediation schedules, report generation, and review of past reports and supporting evidence.

### Cross-References

- **bsi_aic4**: COM-02
COM-03 (Gap: No Gap)
- **eu_ai_act**: Article 17 (1)
Annex VI (Gap: Partial Gap)
- **iso_42001**: 42001: 9.2.1 General
42001: 9.2.2 Internal Audit Programme
42001: 10.1 Non-Conformity and Corrective Action
42001: 10.2 Continual Improvement
27001: 9.2.1 General
27001: 9.2.2 Internal audit programme (Gap: No Gap)
- **nist_ai_600_1**: GV-4.3-002
MP-1.1-003 (Gap: Partial Gap)

### CAIQ Questions

- **A&A-05.1**: Are Audit Management processes aligned with global auditing standards, defined and implemented to support audit planning, risk analysis, security control assessment, conclusion, remediation schedules, report generation, review of past reports and supporting evidence?

---

## A&A-06: Remediation

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Owned by the Orchestrated Service Provider (OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: N/A
- Development: Design, Training, Guardrails
- Evaluation/Validation: Re-evaluation, Validation/Red Teaming, Evaluation
- Deployment: AI applications, AI Services supply chain
- Delivery: Continuous improvement
- Service Retirement: Model disposal, Data deletion, Archiving

### Specification

Establish, document, approve, communicate, apply, evaluate and maintain a risk-based corrective action plan to remediate audit findings, regularly review and report remediation status to relevant stakeholders.

### Cross-References

- **bsi_aic4**: COM-03
COM-04 (Gap: No Gap)
- **eu_ai_act**: Article 20 (1)
Article 20 (2)
Article 53
Article 55 (Gap: No Gap)
- **iso_42001**: 42001: 9.2.1 General
42001: 9.2.2 Internal audit programme
42001: 9.3.2 Management Review Inputs
42001: 9.3.3 Management Review Results
42001: 10.2: Non-conformity and Corrective action
27001: 9.2.2 Internal audit programme
27001: 10.2 Nonconformity and corrective action (Gap: No Gap)
- **nist_ai_600_1**: GV-1.3-007
MG-4.2-002
MG-1.3-001 (Gap: Partial Gap)

### CAIQ Questions

- **A&A-06.1**: Is a risk-based corrective action plan established, documented, approved, communicated, applied, evaluated, and maintained to remediate audit findings, regularly review, and report remediation status to relevant stakeholders?

---

# Domain: Application & Interface Security

## AIS-01: Application and Interface Security Policy and Procedures

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Network, Compute, Storage, Application, Data
**Threat Categories:** Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Orchestrated Service Provider-Application Provider (Shared OSP-AP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data collection, Data curation, Data storage
- Development: Training, Design, Guardrails
- Evaluation/Validation: Evaluation, Validation/Red Teaming, Re-evaluation
- Deployment: AI Services supply chain, AI applications, Orchestration
- Delivery: Continuous monitoring, Continuous improvement, Maintenance, Operations
- Service Retirement: Archiving, Model disposal, Data deletion

### Specification

Establish, document, approve, communicate, apply, evaluate and maintain policies and procedures for application security. Review and update the policies and procedures at least annually or after significant system changes.

### Cross-References

- **bsi_aic4**: DEV-01
DEV-03
OPS-04
OPS-06
OPS-10
OPS-11
OPS-18
PS-01 (Gap: No Gap)
- **eu_ai_act**: Article 15 (1)
Article 15 (2)
Article 15 (3)
Article 15 (4)
Article 15 (5)
Article 17 (1)
Article 53 (1) (c)
Article 55 (1) (d)
Article 56 (Gap: Partial Gap)
- **iso_42001**: 42001: B.6.1.3
42001: A.6.2.1
42001: Clause A.6
27001: A.5.1
27001: A.8.25 (Gap: Partial Gap)
- **nist_ai_600_1**: GV-2.1-001
MP-4.1-003
GV-6.1-005 (Gap: Partial Gap)

### CAIQ Questions

- **AIS-01.1**: Are policies and procedures for application security established, documented, approved, communicated, applied, evaluated, and maintained?
- **AIS-01.2**: Are the policies and procedures for application security reviewed and updated at least annually or upon significant system changes?

---

## AIS-02: Application Security Baseline Requirements

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Orchestrated Service Provider-Application Provider (Shared OSP-AP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data storage, Data curation, Data collection
- Development: Design, Guardrails, Supply Chain, Training
- Evaluation/Validation: Validation/Red Teaming, Evaluation, Re-evaluation
- Deployment: AI Services supply chain, AI applications
- Delivery: Continuous monitoring, Continuous improvement, Maintenance, Operations
- Service Retirement: Archiving

### Specification

Establish, document and maintain baseline requirements for securing applications."

### Cross-References

- **bsi_aic4**: DEV-01
DEV-03
OPS-04
OPS-06
OPS-10
OPS-11
OPS-18
OPS-23
PS-01 (Gap: No Gap)
- **eu_ai_act**: Article 11
Article 15 (1)
Article 53 and Annex XI
Article 55 (Gap: No Gap)
- **iso_42001**: 42001: 6.1.2
42001: B.6.2.2
42001: B.7.2
27001:6.1.2
27001:6.1.3
27001: A.8.26 (Gap: Partial Gap)
- **nist_ai_600_1**: GV-6.1-004
GV-6.1-005 (Gap: Partial Gap)

### CAIQ Questions

- **AIS-02.1**: Are baseline requirements for securing applications established, documented, and maintained?

---

## AIS-03: Application Security Metrics

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Network, Compute, Storage, Application, Data
**Threat Categories:** Sensitive data disclosure, Model/Service Failure, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Orchestrated Service Provider-Application Provider (Shared OSP-AP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Resource provisioning
- Development: Guardrails, Design
- Evaluation/Validation: Validation/Red Teaming, Evaluation, Re-evaluation
- Deployment: AI applications, AI Services supply chain
- Delivery: Continuous monitoring, Continuous improvement, Operations
- Service Retirement: Archiving

### Specification

Define and implement technical and operational metrics in alignment with business objectives, security requirements, and compliance obligations.

### Cross-References

- **bsi_aic4**: COM-04 (Gap: Partial Gap)
- **eu_ai_act**: Article 15 (2)
Article 15 (3)
Article 53 and Annex XI
Article 55
Article 74
Article 75 (Gap: No Gap)
- **iso_42001**: 42001: 9.1
42001: B.6.2.6
27001: 9.1
27701: 5.7.1 (Gap: No Gap)
- **nist_ai_600_1**: MS-2.7-002
MS-2.7-004
MEASURE 3.2
MEASURE 3.3
MEASURE 4.2
MG-3.1-002
MS-2.11-002
MS-2.7-002
MS-2.7-004
MG-3.1-002
MS-2.11-002 (Gap: Partial Gap)

### CAIQ Questions

- **AIS-03.1**: Are technical and operational metrics defined and implemented in alignment with business objectives, security requirements, and compliance obligations?

---

## AIS-04: Secure Application Development Lifecycle

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Owned by the Orchestrated Service Provider (OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Resource provisioning, Team and expertise
- Development: Guardrails, Supply Chain, Design
- Evaluation/Validation: Validation/Red Teaming, Evaluation, Re-evaluation
- Deployment: AI applications, AI Services supply chain, Orchestration
- Delivery: Continuous monitoring, Continuous improvement, Operations, Maintenance
- Service Retirement: Archiving

### Specification

Define and implement a secure software development lifecycle (SDLC) process for application requirements analysis, planning, design, development, testing, deployment, and operation in accordance with security requirements defined by the organization.

### Cross-References

- **bsi_aic4**: DEV-01 (Gap: No Gap)
- **eu_ai_act**: Article 9 (6)
Article 9 (7)
Article 9 (8)
Article 17 (1)
Annex XI (Section 1) (2)
Annex XI (Section 2) (Gap: No Gap)
- **iso_42001**: 42001: B.6.1.3
42001: B.6.2.3
42001: A.6.2.4
42001: A.6.2.5
42001: A.6.2.6
27001: A.8.25
27001: A.8.27
27001: A.8.28
27001: A.8.29
27001: A.8.30 (Gap: Partial Gap)
- **nist_ai_600_1**: GOVERN 4.1
GOVERN 4.2
MANAGE 3.2
MEASURE 2.8
MEASURE 2.9 (Gap: Partial Gap)

### CAIQ Questions

- **AIS-04.1**: Is a secure software development lifecycle (SDLC) process defined and implemented for application requirements analysis, planning, design, development, testing, deployment, and operation in accordance with security requirements defined by the organization?

---

## AIS-05: Application Security Testing

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Resource provisioning, Team and expertise
- Development: Guardrails, Training, Supply Chain
- Evaluation/Validation: Validation/Red Teaming, Re-evaluation
- Deployment: AI applications, AI Services supply chain
- Delivery: Continuous improvement, Operations, Maintenance
- Service Retirement: N/A

### Specification

Implement a testing strategy, including criteria for acceptance of new  information systems, upgrades and new versions, which provides  application security assurance and maintains compliance while meeting  organizational delivery goals.  Automate when applicable and possible.

### Cross-References

- **bsi_aic4**: DEV-01
DEV-03
DEV-06
PSS-02
PSS-05
PSS-09
PSS-10 (Gap: No Gap)
- **eu_ai_act**: Article 17 (d)
Article 17 (h)
Article 53
Article 54
Article 55
Article 60
Annex XI (Section 1) (2)
Annex XI (Section 2) (Gap: No Gap)
- **iso_42001**: 42001: B.6.2.4
27001: A.8.29
27001: A.8.26
27001: A.8.33
27001: A.5.10
27002: A.8.29 & A.8.33 (Gap: Partial Gap)
- **nist_ai_600_1**: MEASURE 2.3
MEASURE 2.5
MEASURE 2.6 (Gap: No Gap)

### CAIQ Questions

- **AIS-05.1**: Is a testing strategy implemented, including criteria for acceptance of new information systems, upgrades, and new versions, to provide application security assurance, maintain compliance, and meet organizational delivery goals?
- **AIS-05.2**: Is automation applied where applicable and possible?

---

## AIS-06: Secure Application Deployment

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Resource provisioning, Team and expertise
- Development: Guardrails, Design
- Evaluation/Validation: Validation/Red Teaming
- Deployment: AI applications, Orchestration
- Delivery: Maintenance, Continuous improvement, Operations, Continuous monitoring
- Service Retirement: N/A

### Specification

Establish and implement strategies and capabilities for secure, standardized, and compliant application deployment. Automate where possible.

### Cross-References

- **bsi_aic4**: DEV-01
DEV-03
DEV-08
DEV-09
PSS-02
PSS-05
PSS-09
PSS-10 (Gap: No Gap)
- **eu_ai_act**: Article 9 (6)
Article 9 (7)
Article 9 (8)
Article 26
Article 50
Article 53 and Annex XI
Article 55 (Gap: No Gap)
- **iso_42001**: 42001: 8.2
42001: 8.3
42001: 8.4
42001: B.6.2.5
42001: B.6.2.6
27001: A.8.9
27001: A.5.31
27001: A.5.32
27001: A.8.32 (Gap: Partial Gap)
- **nist_ai_600_1**: MEASURE 2.9
MEASURE 2.10 (Gap: No Gap)

### CAIQ Questions

- **AIS-06.1**: Are strategies and capabilities established and implemented for secure, standardized, and compliant application deployment?

---

## AIS-07: Application Vulnerability Remediation

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Orchestrated Service Provider-Application Provider (Shared OSP-AP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Resource provisioning, Team and expertise
- Development: Guardrails, Supply Chain, Design
- Evaluation/Validation: Validation/Red Teaming
- Deployment: AI applications, AI Services supply chain, Orchestration
- Delivery: Continuous improvement, Maintenance
- Service Retirement: N/A

### Specification

Define and implement a process to remediate application security vulnerabilities, automating remediation when possible.

### Cross-References

- **bsi_aic4**: PSS-02 (Gap: No Gap)
- **eu_ai_act**: Article 15 (4)
Article 15 (5)
Article 53
Article 55 (1) (Gap: No Gap)
- **iso_42001**: 42001: B.6.2.4
42001: A.6.2.6
42001: A.8.4
27001: A.8.8 (Gap: Partial Gap)
- **nist_ai_600_1**: MG-2.4-003
MS-2.7-001 (Gap: No Gap)

### CAIQ Questions

- **AIS-07.1**: Are processes defined and implemented to remediate application security vulnerabilities, automating remediation when possible?

---

## AIS-08: Input Validation

**Type:** control
**Control Type:** AI-Specific
**Architectural Relevance:** Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model/Service Failure, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data collection, Data curation
- Development: Guardrails, Training
- Evaluation/Validation: Validation/Red Teaming
- Deployment: Orchestration, AI applications
- Delivery: Continuous monitoring, Operations
- Service Retirement: N/A

### Specification

Validate, filter, modify or block, as necessary, input against adversarial patterns, failure patterns and unwanted behaviour according to organisational policies and applicable laws and regulations.

### Cross-References

- **bsi_aic4**: DQ-01
DQ-03
DQ-06 (Gap: No Gap)
- **eu_ai_act**: Recital 76
Recital 77
Article 9 (2)
Article 10 (2) (b)
Article 10 (2) (f)
Article 10 (2) (g)
Article 10 (3)
Article 15 (Gap: Partial Gap)
- **iso_42001**: 42001:  A.6.2.4 / B.6.2.4 – AI system verification and validation
42001: A.7.4 / B.7.4 – Quality of data for AI systems
42001: A7.6 – Data preparation
42001: B6.2.3 Technical measures for AI reliability and resilience
42001: A8.26 – Application security requirements (Gap: Partial Gap)
- **nist_ai_600_1**: MP-2.3-002
MS-1.1-007
MS-2.6-006
MS-1.1-002 (Gap: Partial Gap)

### CAIQ Questions

- **AIS-08.1**: Is the input against adversarial patterns, failure patterns and unwanted behaviour, validated, filtered, modified, or blocked as necessary, according to organisational policies, applicable laws and regulations?

---

## AIS-09: Output Validation

**Type:** control
**Control Type:** AI-Specific
**Architectural Relevance:** Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure apps/plugins, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: N/A
- Development: Guardrails, Design
- Evaluation/Validation: Validation/Red Teaming
- Deployment: Orchestration, AI applications
- Delivery: Operations, Continuous monitoring
- Service Retirement: N/A

### Specification

Validate, filter, modify or block, as necessary, output against adversarial patterns, failure patterns and unwanted behaviour according to organisational policies and applicable laws and regulations.

### Cross-References

- **bsi_aic4**: SR-05
SR-06
RE-04 (Gap: No Gap)
- **eu_ai_act**: Article 15 (4)
Article 15 (5)
Article 53
Article 55 (1) (Gap: No Gap)
- **iso_42001**: 42001: A.6.2.4 / B.6.2.4 - AI system verification and validation
42001: A.6.2.6 – AI system operation and monitoring
42001: B.6.2.6 – Monitoring and evaluation
42001: B.6.2.1 – Technical robustness & security
42001: A.7.4 / B.7.4 - Quality of data for AI systems
27001: A.8.11 Data masking
27001: A.8.26 – Application security requirements
27001: A.8.29 – Security testing (Gap: No Gap)
- **nist_ai_600_1**: MP-2.3-001
MP-2.3-003
MP-2.3-005
MS-2.6-004
MS-2.6-005
MS-2.6-006
MS-4.2-001
MG-2.2-001
MG-2.2-005
MG-4.1-004 (Gap: No Gap)

### CAIQ Questions

- **AIS-09.1**: Is the output against adversarial patterns, failure patterns and unwanted behaviour, validated, filtered, modified, or blocked as necessary, according to organisational policies, applicable laws and regulations?

---

## AIS-10: API Security

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Team and expertise, Resource provisioning
- Development: Guardrails, Design
- Evaluation/Validation: Validation/Red Teaming
- Deployment: AI applications, Orchestration
- Delivery: Continuous monitoring, Maintenance, Operations
- Service Retirement: Archiving

### Specification

Define and implement processes, procedures, and technical measures to secure APIs. Review and update for any improvements at least annually  or after significant system changes.

### Cross-References

- **bsi_aic4**: Not Applicable (Gap: Full Gap)
- **eu_ai_act**: Article 15 (5)
Article 53 and Annex XI
Article 55 (Gap: No Gap)
- **iso_42001**: 42001: 6.1 - Actions to address risks and opportunities
27001: 6.1 - Actions to address risks and opportunities
27001: A.5.15 - Access control
27001: A.5.20 - Addressing information security within supplier agreements
27001: A.5.21 Managing information security in the information and communication technology (ICT) supply
chain
27001: A.8.21 - Security of network services
27001: A.8.24 - Use of cryptography
27001: A.8.26 - Application security requirements (Gap: Partial Gap)
- **nist_ai_600_1**: GV-6.1-009
MS-2.6-006
MS-2.7-007
MS-2.10-001
MS-2.7-009 (Gap: Partial Gap)

### CAIQ Questions

- **AIS-10.1**: Are processes, procedures and technical measures to secure APIs, including authorization flaws, API key management, regular security testing, defined, implemented and evaluated?
- **AIS-10.2**: Are technical measures for any improvements reviewed and updated at least annually or after significant system changes?

---

## AIS-11: Agents Security Boundaries

**Type:** control
**Control Type:** AI-Specific
**Architectural Relevance:** Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Insecure apps/plugins, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared across the supply chain
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data collection, Data storage, Resource provisioning
- Development: Training
- Evaluation/Validation: Validation/Red Teaming
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Continuous monitoring
- Service Retirement: Data deletion

### Specification

Establish security boundaries for agents.

### Cross-References

- **bsi_aic4**: C4 PF-4
C5 PSS-08 (Gap: Partial Gap)
- **eu_ai_act**: No Mapping (Gap: Full Gap)
- **iso_42001**: 42001: A.6.1.3 Processes for responsible AI system design and development
42001: A.6.2.2 AI system requirements and specification
42001: A.6.2.3 Documentation of AI system design and development
42001: A.6.2.5 AI system deployment
42001: A.6.2.7 AI system technical documentation
27001: 8.26 Application security requirements
27001: 8.27 Secure system architecture and engineering principles
27001: A.5.18 Access rights (Gap: Partial Gap)
- **nist_ai_600_1**: MS-2.7-001 (Gap: No Gap)

### CAIQ Questions

- **AIS-11.1**: Are the security boundaries for agents established?

---

## AIS-12: Source Code Managemement

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Owned by the Orchestrated Service Provider (OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Team and expertise
- Development: Design, Supply Chain, Guardrails
- Evaluation/Validation: Validation/Red Teaming, Re-evaluation
- Deployment: N/A
- Delivery: Maintenance
- Service Retirement: N/A

### Specification

Implement source code management practices, such as version control, code review & static code analysis, aligning with the SDLC process.

### Cross-References

- **bsi_aic4**: C4 DM-01
SR-01
C5 DEV-01
DEV-03 (Gap: No Gap)
- **eu_ai_act**: Article 17 (1) (c)
Article 17 (1) (d)
Annex IV 1 (a)
Annex IV 1 (c) (Gap: Partial Gap)
- **iso_42001**: 42001: A.4.4 - Tooling resources
42001: A 6.2.3 - AI system design
42001: A 6.2.4 - AI system verification and validation
27001: A.5.18 - Access rights
27001: A.8.4 - Access to source code
27001: A.8.25 - Secure development life cycle
27001: A.8.28 - Secure coding (Gap: Partial Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **AIS-12.1**: Are source code management practices, such as version control, code review and static code analysis, implemented and aligning with the SDLC process?

---

## AIS-13: AI Sandboxing

**Type:** control
**Control Type:** AI-Specific
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Orchestrated Service Provider-Application Provider (Shared OSP-AP)
- Application: Shared Application Provider-AI Customer (Shared AP-AIC)

**Lifecycle Relevance:**
- Preparation: Resource provisioning, Team and expertise
- Development: Design, Guardrails, Training
- Evaluation/Validation: Evaluation, Validation/Red Teaming, Re-evaluation
- Deployment: Orchestration, AI applications
- Delivery: Operations, Continuous monitoring
- Service Retirement: Archiving, Data deletion, Model disposal

### Specification

Implement sandboxing techniques to execute AI tools and  plugins in isolated environments to prevent unintended  interactions with critical systems or data and limit the  possibility of lateral movement.

### Cross-References

- **bsi_aic4**: SR-06 (Gap: Partial Gap)
- **eu_ai_act**: No Mapping (Gap: Full Gap)
- **iso_42001**: 42001: 5.2 - AI policy
42001: A 6.2.2
42001: A.6.2.3
42001: B.6.2.5 - AI system deployment
42001: B.6.2.6 - AI system operation and monitoring
27001: A.8.9 - Configuration management
27001: A.5.15 - Access control
27001: A.8.8 - Management of technical vulnerabilities
27001: A.8.15 - Logging
27001: A.8.16 - Monitoring activities
27001: A.8.31 - Separation of development
test and production environments (Gap: Partial Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **AIS-13.1**: Are sandboxing techniques implemented to execute AI tools and plugins in isolated environments to prevent unintended interactions with critical systems or data and to limit the possibility of lateral movement?

---

## AIS-14: AI Cache Protection

**Type:** control
**Control Type:** AI-Specific
**Architectural Relevance:** Network, Compute, Storage, Application, Data
**Threat Categories:** Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Orchestrated Service Provider-Application Provider (Shared OSP-AP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: N/A
- Development: Design, Guardrails
- Evaluation/Validation: Validation/Red Teaming
- Deployment: Orchestration, AI applications
- Delivery: Operations, Maintenance
- Service Retirement: Data deletion

### Specification

Implement security measures to protect caches in GenAI systems and  services.

### Cross-References

- **bsi_aic4**: C4 DM-02
C5 COS-01 (Gap: No Gap)
- **eu_ai_act**: No Mapping (Gap: Full Gap)
- **iso_42001**: 42001: 5.2 - AI policy
42001: B.2.2 - AI policy
42001: B.2.3 - Alignment with other organizational policies
42001: A.6.2 - AI System life cycle
27001: A.8.10 Information deletion
27001: A.8.12 Data leakage prevention
27001: A.8.24 Use of cryptography
27001: A.8.26 Application security requirements
27001: A.8.27 - Secure system architecture and engineering principles (Gap: Partial Gap)
- **nist_ai_600_1**: MS-2.7-001 (Gap: No Gap)

### CAIQ Questions

- **AIS-14.1**: Are security measures implemented to protect cache systems in GenAI systems and services?

---

## AIS-15: Prompt Differentation

**Type:** control
**Control Type:** AI-Specific
**Architectural Relevance:** Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Orchestrated Service Provider-Application Provider (Shared OSP-AP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: N/A
- Development: Design, Guardrails
- Evaluation/Validation: Validation/Red Teaming
- Deployment: Orchestration, AI applications
- Delivery: Operations, Continuous monitoring
- Service Retirement: N/A

### Specification

Implement mechanisms enabling the model to clearly distinguish user-provided input instructions from data and system instructions (e.g., system prompts).

### Cross-References

- **bsi_aic4**: C4 SR-06 (Gap: Partial Gap)
- **eu_ai_act**: No Mapping (Gap: Full Gap)
- **iso_42001**: ISO 42001: A.6.2.3 - Documentation of AI system design
and development
ISO 27001: A.8.27 - Secure system architecture and engineering principles (Gap: Partial Gap)
- **nist_ai_600_1**: GV-4.1-001 (Gap: Partial Gap)

### CAIQ Questions

- **AIS-15.1**: Are mechanisms implemented to enable the model to clearly distinguish user-provided input instructions from data and system instructions (e.g., system prompts)?

---

# Domain: Business Continuity Management and Operational Resilience

## BCR-01: Business Continuity Management Policy and Procedures

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared across the supply chain
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Owned by the Orchestrated Service Provider (OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data storage, Resource provisioning, Team and expertise
- Development: N/A
- Evaluation/Validation: N/A
- Deployment: AI applications, Orchestration
- Delivery: Operations, Continuous monitoring, Maintenance
- Service Retirement: Archiving, Data deletion, Model disposal

### Specification

Establish, document, approve, communicate, apply, evaluate and maintain business continuity management and operational resilience policies and procedures. Review and update the policies and procedures at least annually, or when significant changes occur that could impact risk exposure.

### Cross-References

- **bsi_aic4**: C4 PC-01
C5 BCM-02 (Gap: No Gap)
- **eu_ai_act**: Article 15 (4),
Article 17,
Annex VII,
Recital 51,
Recital 15 (Gap: Partial Gap)
- **iso_42001**: 42001: A.2.2
42001: A.2.3
42001: A.2.4
27001: A.5.30 (Gap: No Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **BCR-01.1**: Are business continuity management and operational resilience policies and procedures established, documented, approved, communicated, applied, evaluated, and maintained?
- **BCR-01.2**: Are policies and procedures reviewed and updated at least annually, or when significant changes occur that could impact risk exposure?

---

## BCR-02: Risk Assessment and Impact Analysis

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Sensitive data disclosure, Model/Service Failure, Insecure supply chain, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Owned by the Cloud Service Provider (CSP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data collection, Data curation, Data storage, Resource provisioning, Team and expertise
- Development: N/A
- Evaluation/Validation: N/A
- Deployment: AI applications, Orchestration
- Delivery: Operations, Maintenance, Continuous monitoring
- Service Retirement: Archiving, Model disposal, Data deletion

### Specification

Determine the impact of business disruptions and risks to establish criteria for developing business continuity and operational resilience  strategies and capabilities. Review and update the risk assessment and impact analysis at least  annually or upon significant changes.

### Cross-References

- **bsi_aic4**: C4 PC-01
SR-02
SR-03
C5 BCM-02 (Gap: No Gap)
- **eu_ai_act**: Article 9 (Gap: Partial Gap)
- **iso_42001**: 42001: All A.10 (to ensure feedback of stakeholders on risks)
42001: A.2.2 AI policy
42001: A.2.3 Alignment with other organizational policies
42001: A.2.4 Review of the AI policy
42001: 5.1 Leadership and commitment
42001: 7.1 Resources
42001: 8.2 AI risk assessment (Gap: Partial Gap)
- **nist_ai_600_1**: GV-4.2-003
MS-2.6-005 (Gap: Partial Gap)

### CAIQ Questions

- **BCR-02.1**: Is the impact of business disruptions and risks determined to establish criteria for developing business continuity and operational resilience strategies and capabilities?
- **BCR-02.2**: Is the risk assessment and impact analysis, reviewed and updated at least annually or upon significant changes?

---

## BCR-03: Business Continuity Strategy

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Sensitive data disclosure, Model/Service Failure, Insecure supply chain, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Owned by the Cloud Service Provider (CSP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data storage, Resource provisioning, Team and expertise
- Development: N/A
- Evaluation/Validation: N/A
- Deployment: AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring
- Service Retirement: Archiving, Data deletion, Model disposal

### Specification

Establish strategies to reduce the impact of business disruptions, and improve resiliency and recovery from business disruptions.

### Cross-References

- **bsi_aic4**: C4 PC-01
C5 BCM-02
BCM-03 (Gap: No Gap)
- **eu_ai_act**: Article 9 (2) (d)
Article 9 (5) (Gap: Partial Gap)
- **iso_42001**: 42001: A.4.2 Documented Information Resources
42001 A.4.5 System and computing resources
27001: A.5.30 - ICT readiness for business continuity
27001: A.7.5 - Protecting against physical and environmental threats (Gap: Partial Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **BCR-03.1**: Are strategies established to reduce the impact of business disruptions, and improve resiliency and recovery from business disruptions?

---

## BCR-04: Business Continuity Planning

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Sensitive data disclosure, Model/Service Failure, Insecure supply chain, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Owned by the Cloud Service Provider (CSP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data storage, Resource provisioning, Team and expertise
- Development: N/A
- Evaluation/Validation: N/A
- Deployment: AI applications, Orchestration
- Delivery: Operations, Maintenance, Continuous monitoring
- Service Retirement: Archiving, Data deletion, Model disposal

### Specification

Establish, document, approve, communicate, apply, evaluate and  maintain a business continuity plan based on the results of the  operational resilience strategies and capabilities.

### Cross-References

- **bsi_aic4**: BCM-03 (Gap: No Gap)
- **eu_ai_act**: Article 9 (risk management),
Article 15 (technical robustness),
Article 17 (quality system),
Article 16 (organizational responsibility),
Article 93 (post-market monitoring) (Gap: Partial Gap)
- **iso_42001**: 42001: A.4 Resources for AI systems
27001: A.5.30 ICT readiness for business continuity (Gap: No Gap)
- **nist_ai_600_1**: MG-2.3-001 (Gap: Partial Gap)

### CAIQ Questions

- **BCR-04.1**: Is a business continuity plan - based on the results of operational resilience strategies and capabilities - established, documented, approved, communicated, applied, evaluated and maintained?

---

## BCR-05: Documentation

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Owned by the Cloud Service Provider (CSP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data storage, Resource provisioning, Team and expertise
- Development: N/A
- Evaluation/Validation: N/A
- Deployment: AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring
- Service Retirement: Archiving, Data deletion, Model disposal

### Specification

Develop, identify, and acquire documentation,  both internally and from external parties,  that is relevant to support the business continuity and operational resilience programs. Make the documentation available to authorized stakeholders and review at least annually or upon significant changes.

### Cross-References

- **bsi_aic4**: BCM-03 (Gap: No Gap)
- **eu_ai_act**: Article 15 (4)
Article 9 (6)
Article 17
Annex IV (Gap: Partial Gap)
- **iso_42001**: ISO 42001: A.4.2 (Resource documentation)
ISO 42001: A.4.3 (Data resources)
ISO 42001: A.4.4 (Tooling resources) (Gap: No Gap)
- **nist_ai_600_1**: MP-2.3-002
GV-4.2-003 (Gap: Partial Gap)

### CAIQ Questions

- **BCR-05.1**: Is relevant documentation, both internal and from external parties,  for supporting the business continuity and operational resilience programs, developed, identified, and acquired?
- **BCR-05.2**: Is the documentation available to authorized stakeholders and reviewed at least annually or upon significant changes.?

---

## BCR-06: Business Continuity Exercises

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Sensitive data disclosure, Model/Service Failure, Insecure supply chain, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared across the supply chain
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data storage, Resource provisioning, Team and expertise
- Development: N/A
- Evaluation/Validation: N/A
- Deployment: AI applications, Orchestration
- Delivery: Operations, Maintenance, Continuous monitoring
- Service Retirement: Archiving, Data deletion, Model disposal

### Specification

Follow a structured approach to evaluate the effectiveness of the business continuity and operational resilience plans at planned intervals or upon significant changes.

### Cross-References

- **bsi_aic4**: BCM-04 (Gap: No Gap)
- **eu_ai_act**: Article 16
Article 17(1) (d) (Gap: Partial Gap)
- **iso_42001**: ISO 27001 A.5.30 (ICT readiness for business continuity) (Gap: Partial Gap)
- **nist_ai_600_1**: MS-2.7-007
MP-5.1-005
GV-6.2-003 (Gap: Partial Gap)

### CAIQ Questions

- **BCR-06.1**: Is a structured approach to evaluate the effectiveness of the business continuity and operational resilience plans, followed at planned intervals or upon significant changes?

---

## BCR-07: Communication

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Sensitive data disclosure, Model/Service Failure, Insecure supply chain, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Owned by the Cloud Service Provider (CSP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data storage, Resource provisioning, Team and expertise
- Development: N/A
- Evaluation/Validation: N/A
- Deployment: AI applications, Orchestration
- Delivery: Operations, Maintenance, Continuous monitoring
- Service Retirement: Archiving, Data deletion, Model disposal

### Specification

Establish and maintain communication channels with all relevant  stakeholders in the course of business continuity and resilience  procedures.

### Cross-References

- **bsi_aic4**: C4 PC-01
BCM-01
BCM-03 (Gap: No Gap)
- **eu_ai_act**: Article 17 (i) (procedures for reporting serious incidents)
Article 55 (c) (reporting serious incidents)
Article 73 (reporting serious incidents) (Gap: Partial Gap)
- **iso_42001**: All 42001: A.8.5
All 42001: A.10 (Gap: No Gap)
- **nist_ai_600_1**: GV-2.1-001
GV-6.2-003 (Gap: Partial Gap)

### CAIQ Questions

- **BCR-07.1**: Are communication channels with all relevant stakeholders established and maintained in the course of business continuity and resilience procedures?

---

## BCR-08: Backup

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Sensitive data disclosure, Model theft, Model/Service Failure, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Owned by the Cloud Service Provider (CSP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data storage, Resource provisioning, Team and expertise
- Development: N/A
- Evaluation/Validation: N/A
- Deployment: AI applications, Orchestration
- Delivery: Operations, Maintenance, Continuous monitoring
- Service Retirement: Archiving

### Specification

Periodically perform backups. Ensure the confidentiality, integrity  and availability of the backup, and verify restoration from backup for resiliency.

### Cross-References

- **bsi_aic4**: C4 RE-06
C5 OPS-06
OPS-07
OPS-08 (Gap: No Gap)
- **eu_ai_act**: Article 15 (1)
Article 9 (2)
Article 9 (6)
Article 17
Annex IV
Recital 51 (Gap: Partial Gap)
- **iso_42001**: 42001: A.4.3 (Data resources)
27001: A.8.13 (Information backup) (Gap: No Gap)
- **nist_ai_600_1**: GV-1.5-003
GV-6.2-006 (Gap: Partial Gap)

### CAIQ Questions

- **BCR-08.1**: Are backups periodically performed?
- **BCR-08.2**: Is the confidentiality, integrity and availability of the backup, ensured and data restoration from backup verified for resiliency?

---

## BCR-09: Disaster Response Plan

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Owned by the Cloud Service Provider (CSP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data storage, Resource provisioning, Team and expertise
- Development: N/A
- Evaluation/Validation: N/A
- Deployment: AI applications, Orchestration
- Delivery: Operations, Maintenance, Continuous monitoring
- Service Retirement: Archiving, Data deletion, Model disposal

### Specification

Establish, document, approve, communicate, apply, evaluate and maintain a disaster response plan to recover from natural and man-made disasters. Update the plan at least annually or upon significant changes.

### Cross-References

- **bsi_aic4**: BCM-03 (Gap: No Gap)
- **eu_ai_act**: Article 15 (4) (accuracy, robustness, and cybersecurity) (Gap: Partial Gap)
- **iso_42001**: ISO 42001: A.4.2 (Resource documentation)
ISO 42001: A.4.3 (Data resources)
ISO 42001: A.4.4 (Tooling resources)
ISO 27001 A.5.30 (ICT readiness for business continuity) (Gap: No Gap)
- **nist_ai_600_1**: GV-1.5-002
MG-2.3-001 (Gap: Partial Gap)

### CAIQ Questions

- **BCR-09.1**: Is a disaster response plan to recover from natural and man-made disasters established, documented, approved, communicated, applied, evaluated, and maintained?
- **BCR-09.2**: Is the Disaster Response Plan updated at least annually or upon significant changes?

---

## BCR-10: Response Plan Exercise

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Sensitive data disclosure, Model/Service Failure, Insecure supply chain, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Owned by the Cloud Service Provider (CSP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data storage, Resource provisioning, Team and expertise
- Development: N/A
- Evaluation/Validation: N/A
- Deployment: AI applications, Orchestration
- Delivery: Operations, Maintenance, Continuous monitoring
- Service Retirement: Archiving

### Specification

Exercise the disaster response plan annually or upon significant changes, including, if possible, participation of local emergency authorities.

### Cross-References

- **bsi_aic4**: C4 RE-06
C5 BCM-04 (Gap: No Gap)
- **eu_ai_act**: Article 9 (2)
Article 9 (6)
Article 15 (1)
Article 17 (1) (d)
Article 93 (Gap: Partial Gap)
- **iso_42001**: ISO 42001: A.10.2 (Allocating responsibilities)
ISO 27001: A.5.30 (ICT readiness for business continuity)
ISO 27001: A.5.5 (Contact with authorities) (Gap: No Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **BCR-10.1**: Is a structured approach to evaluate the effectiveness of the disaster response plan followed at planned intervals or upon significant changes, including, if possible, participation of local emergency authorities?

---

## BCR-11: Equipment Redundancy

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage

**Ownership:**
- GenAI OPS/PI: Owned by the Cloud Service Provider (CSP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Resource provisioning
- Development: N/A
- Evaluation/Validation: N/A
- Deployment: AI applications, Orchestration
- Delivery: Operations, Maintenance, Continuous monitoring
- Service Retirement: Archiving

### Specification

Supplement business-critical equipment with both locally redundant and geographically dispersed equipment located at a reasonable minimum distance in accordance with applicable industry standards.

### Cross-References

- **bsi_aic4**: PS-02
PS-06
OPS-09 (Gap: No Gap)
- **eu_ai_act**: Article 15 (4) (accuracy, robustness, and cybersecurity) (Gap: Partial Gap)
- **iso_42001**: No ISO 42001 mapping.
27001: A.8.14 (Redundancy of information processing facilities) (Gap: Partial Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **BCR-11.1**: Are business-critical equipment supplemented with both locally redundant and geographically dispersed equipment located at a reasonable minimum distance in accordance with applicable industry standards?

---

# Domain: Change Control and Configuration Management

## CCC-01: Change Management Policy and Procedures

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Network, Compute, Storage, Application
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared across the supply chain
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data storage, Resource provisioning
- Development: Design, Training, Guardrails
- Evaluation/Validation: Evaluation, Validation/Red Teaming, Re-evaluation
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Data deletion, Model disposal

### Specification

Establish, document, approve, communicate, apply, evaluate and  maintain policies and procedures for managing the risks  associated with applying changes to assets owned, controlled or  used by the organization. Review and update the policies and  procedures at least annually, or upon significant changes.

### Cross-References

- **bsi_aic4**: C4 PC-02
C5 DEV-01
DEV-02
DEV-03 (Gap: No Gap)
- **eu_ai_act**: Article 17 (Gap: Partial Gap)
- **iso_42001**: 42001: A.6.2.3 Documentation of AI system
design and development
42001: Clause 6.3 Planning changes
42001: Clause 8.1 Operational planning and
control
42001: B.6 AI system life cycle
42001: B.6.1.3 Processes for responsible
design and development of AI systems
42001: B.6.2.7 AI system technical
documentation
42001: A.6.2.6 AI system operation and
monitoring
27001: A.5.1 Policies for information
security
27001: A.8.32 Change management (Gap: No Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **CCC-01.1**: Are policies and procedures for managing the risks associated with applying changes to assets owned, controlled or used by the organization, established, documented, approved, communicated, applied, evaluated, and maintained?
- **CCC-01.2**: Are the policies and procedures reviewed and updated at least annually or upon significant changes?

---

## CCC-02: Quality Testing

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared across the supply chain
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Owned by the Orchestrated Service Provider (OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data collection, Data curation, Data storage, Resource provisioning, Team and expertise
- Development: Training, Design, Guardrails, Supply Chain
- Evaluation/Validation: Evaluation, Validation/Red Teaming, Re-evaluation
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Continuous monitoring, Continuous improvement, Maintenance, Operations
- Service Retirement: Archiving, Data deletion, Model disposal

### Specification

Establish, maintain and implement a defined quality change  control, approval and testing process incorporating baselines,  testing, and release standards.

### Cross-References

- **bsi_aic4**: C4 PF-06
C5 DEV-03
DEV-05
DEV-06
DEV-07
DEV-08
DEV-09
DEV-10 (Gap: No Gap)
- **eu_ai_act**: Article 17 (Gap: Partial Gap)
- **iso_42001**: 42001: A.6.2.4 - AI system verification and validation
42001: A.6.2.3 - Documentation of AI system design and development
42001: A.6.2.7 - AI system technical documentation
42001: A.6.2.5 - AI system deployment
42001: B.6.1.3 - Processes for responsible design and development of AI systems (Gap: No Gap)
- **nist_ai_600_1**: GV-1.3-002
MP-2.3-005
MS-2.3-003
MG-3.2-002
MS-2.7-008
MP-2.3-001
GV-1.5-003
GV-1.3-003
MP-2.1-002 (Gap: Partial Gap)

### CAIQ Questions

- **CCC-02.1**: Is a defined quality change control, approval and testing process incorporating baselines, testing and release standards, established, maintained and implemented?

---

## CCC-03: Change Management Technology

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared across the supply chain
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data collection, Data curation, Data storage, Resource provisioning
- Development: Design, Training, Guardrails
- Evaluation/Validation: Evaluation, Validation/Red Teaming, Re-evaluation
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Archiving, Data deletion, Model disposal

### Specification

Implement a change management procedure to manage the risks associated with applying changes to assets owned, controlled or used by the organization.

### Cross-References

- **bsi_aic4**: DEV-05 (Gap: Partial Gap)
- **eu_ai_act**: Article 17 (Gap: Partial Gap)
- **iso_42001**: 42001: Clause 6.3 Planning of changes
42001: Clause 8.1 Operational planning and control
42001: A.10.2 Allocating responsibilities (Gap: Partial Gap)
- **nist_ai_600_1**: GV-6.1-005
GV-6.1-008
MG-4.1-006
GV-1.1-001
MS-2.7-001 (Gap: Partial Gap)

### CAIQ Questions

- **CCC-03.1**: Is a change management procedure implemented to manage the risks associated with applying changes to assets owned, controlled or used by the organization?

---

## CCC-04: Change Authorization

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared across the supply chain
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data collection, Data curation, Data storage, Resource provisioning, Team and expertise
- Development: Training, Design, Guardrails, Supply Chain
- Evaluation/Validation: Evaluation, Validation/Red Teaming, Re-evaluation
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Archiving, Data deletion, Model disposal

### Specification

Implement and enforce a procedure to authorize addition, removal, update, and management of assets, owned, controlled or used by the organization.

### Cross-References

- **bsi_aic4**: DEV-07
DEV-09
DEV-10
AM-03
AM-04 (Gap: No Gap)
- **eu_ai_act**: No Mapping (Gap: Full Gap)
- **iso_42001**: 42001: Clause 8.1 Operational planning and control
42001: A.10.2 Allocating responsibilities
27001: A.5.15 Access control
27001: A.7.2 Physical entry
27001: A.8.9 Configuration management
27001: A.8.19 Installation of software on operational systems
27001: A.8.20 Networks security
27001: A.8.32 Change management (Gap: No Gap)
- **nist_ai_600_1**: MS-2.7-001
MS-2.7-009
GV-6.1-005
GV-6.1-007 (Gap: Partial Gap)

### CAIQ Questions

- **CCC-04.1**: Are procedures implemented and enforced to authorize the addition, removal, update, and management of assets owned, controlled, or used by the organization?

---

## CCC-05: Change Agreements

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data storage, Resource provisioning
- Development: Training
- Evaluation/Validation: Evaluation, Validation/Red Teaming, Re-evaluation
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Archiving, Data deletion, Model disposal

### Specification

Include provisions limiting changes directly impacting customer owned environments/tenants to explicitly authorized requests within  service level agreements.

### Cross-References

- **bsi_aic4**: DEV-03
DEV-09 (Gap: No Gap)
- **eu_ai_act**: No Mapping (Gap: Full Gap)
- **iso_42001**: 42001: Clause 8.1 Operational planning and control
42001: A.10.2 Allocating responsibilities
42001: A.10.4 Customers (Gap: Partial Gap)
- **nist_ai_600_1**: GV-6.1-004 (Gap: Partial Gap)

### CAIQ Questions

- **CCC-05.1**: Are provisions included that limit changes directly impacting  customer owned environments/tenants to explicitly authorized requests within service level agreements?

---

## CCC-06: Change Management Baseline

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared across the supply chain
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Orchestrated Service Provider-Application Provider (Shared OSP-AP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data storage, Resource provisioning
- Development: Design, Training, Guardrails, Supply Chain
- Evaluation/Validation: Validation/Red Teaming, Evaluation, Re-evaluation
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Archiving, Data deletion, Model disposal

### Specification

Establish change management baselines for all relevant authorized changes on organization assets. Review and update the change management baseline at least annually or upon significant changes.

### Cross-References

- **bsi_aic4**: DEV-03 (Gap: No Gap)
- **eu_ai_act**: No Mapping (Gap: Full Gap)
- **iso_42001**: 42001: Clause 6.3 Planning of changes
42001: Clause 8.1 Operational planning and control
42001: A.6.2.2 AI system requirements and specification
42001: 6.2.3 – Risk treatment
42001: 6.2.6 – Operation & monitoring
27001: A.8.32 Change management
27001: A.8.9 Configuration Management (Gap: Partial Gap)
- **nist_ai_600_1**: MS-2.9-002
MG-3.2-002
GV-1.6-001
GV-1.6-002
GV-6.1-008
MP-2.1-001
GV-6.1-008
MG-2.2-002
MG-3.2-003
GV-1.3-002
MS-2.8-003
GV-1.6-001 (Gap: Partial Gap)

### CAIQ Questions

- **CCC-06.1**: Are change management baselines established for all relevant authorized changes on organization assets?
- **CCC-06.2**: Is the change management baseline reviewed an updated at least annually or upon significant changes?

---

## CCC-07: Detection of Baseline Deviation

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared across the supply chain
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data collection, Data curation, Data storage
- Development: Design, Training, Guardrails
- Evaluation/Validation: Evaluation, Validation/Red Teaming, Re-evaluation
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Archiving, Data deletion, Model disposal

### Specification

Implement detection measures with proactive notification in case of changes deviating from the established baseline.

### Cross-References

- **bsi_aic4**: OPS-23 Additional Criteria
DEV-07
DEV-08 (Gap: No Gap)
- **eu_ai_act**: No Mapping (Gap: Full Gap)
- **iso_42001**: 42001: Clause 9.1 - monitoring
including deviating changes from baseline
42001: Clause 7.4 - for notification of deviated changes
42001: A.6.2.6 AI system operation and monitoring
42001: B.7.1.1 - Monitoring and review of AI system behavior
27001: A.8.32 Change management
27001: A.8.9 Establish & maintain baseline configuration (Gap: Partial Gap)
- **nist_ai_600_1**: MS-5.1-005
MS-2.7-007
MG-4.1-006
MG-4.1-002
MS-2.6-005
MS-2.7-009
GV-6.2-004
GV-1.5-002
MS-1.1-002
MS-1.3-002 (Gap: Partial Gap)

### CAIQ Questions

- **CCC-07.1**: Are detection measures with proactive notification implemented in case of changes deviating from the established baseline?

---

## CCC-08: Exception Management

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared across the supply chain
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Shared Orchestrated Service Provider-Application Provider (Shared OSP-AP)

**Lifecycle Relevance:**
- Preparation: Data collection, Data curation, Data storage, Resource provisioning, Team and expertise
- Development: Design, Training, Guardrails
- Evaluation/Validation: Evaluation, Validation/Red Teaming, Re-evaluation
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Archiving, Data deletion, Model disposal

### Specification

Implement a procedure for the management of exceptions, including emergencies, in the change and configuration process. Align the procedure with the requirements of GRC-04: Policy Exception Process.

### Cross-References

- **bsi_aic4**: DEV-03
SIM-01
DEV-08
SP-03 (Gap: No Gap)
- **eu_ai_act**: No Mapping (Gap: Full Gap)
- **iso_42001**: 42001: Clause 6.3 Planning of changes
42001: Clause 8.1 Operational planning and control
42001: Clause 10.2 Nonconformity and corrective action (Gap: No Gap)
- **nist_ai_600_1**: GV-1.3-007
GV-6.2-003
GV-2.3-001
MG-2.4-002
MG-4.3-001
GV-1.5-002
GV-2.1-002
GV-6.2-006 (Gap: Partial Gap)

### CAIQ Questions

- **CCC-08.1**: Is a procedure implemented (aligning with the requirements of GRC-04: Policy Exception Process) for the management of exceptions, including emergencies, in the change and configuration process?

---

## CCC-09: Change Restoration

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared across the supply chain
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Shared Orchestrated Service Provider-Application Provider (Shared OSP-AP)

**Lifecycle Relevance:**
- Preparation: Data curation, Data storage, Resource provisioning
- Development: Training, Guardrails
- Evaluation/Validation: Re-evaluation
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Maintenance, Continuous improvement
- Service Retirement: Archiving, Data deletion, Model disposal

### Specification

Define and implement a process to proactively roll back changes to a previous known good state in case of errors or security concerns.

### Cross-References

- **bsi_aic4**: DEV-08 (Gap: No Gap)
- **eu_ai_act**: No Mapping (Gap: Full Gap)
- **iso_42001**: 42001: Clause 6.3 Planning of changes
42001: Clause 8.1 Operational planning and control
42001: Clause 10.2 Nonconformity and corrective action (Gap: No Gap)
- **nist_ai_600_1**: GV-6.2-006 (Gap: No Gap)

### CAIQ Questions

- **CCC-09.1**: Is a process defined and implemented to proactively roll back changes to a previous known good state in case of errors or security concerns?

---

# Domain: Cryptography, Encryption & Key Management

## CEK-01: Encryption and Key Management Policy and Procedures

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Network, Compute, Storage, Application, Data
**Threat Categories:** Sensitive data disclosure, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared across the supply chain
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data storage
- Development: N/A
- Evaluation/Validation: N/A
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring
- Service Retirement: Archiving, Data deletion, Model disposal

### Specification

Establish, document, approve, communicate, apply, evaluate and maintain policies and procedures for Cryptography, Encryption and Key Management.  Review and update the policies and procedures at least annually or upon significant changes.

### Cross-References

- **bsi_aic4**: CRY-01
CRY-04 (Gap: No Gap)
- **eu_ai_act**: Article 17 (Gap: Partial Gap)
- **iso_42001**: No Mapping for ISO 42001
27001: Annex A Control A.8.24
27001: A.8.24 (Gap: Partial Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **CEK-01.1**: Are cryptography, encryption, and key management policies and procedures established, documented, approved, communicated, applied, evaluated, and maintained?
- **CEK-01.2**: Are cryptography, encryption, and key management policies and procedures reviewed and updated at least annually or upon significant changes?

---

## CEK-02: CEK Roles and Responsibilities

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Network, Compute, Storage, Application, Data
**Threat Categories:** Sensitive data disclosure, Insecure supply chain, Insecure apps/plugins, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Orchestrated Service Provider-Application Provider (Shared OSP-AP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data curation, Data storage, Team and expertise
- Development: N/A
- Evaluation/Validation: N/A
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Archiving, Data deletion, Model disposal

### Specification

Define and implement cryptographic, encryption and key management roles and responsibilities.

### Cross-References

- **bsi_aic4**: CRY-04
CRY-04 (Gap: No Gap)
- **eu_ai_act**: Article 17 (Gap: Partial Gap)
- **iso_42001**: No Mapping for ISO 42001
ISO 27002: 5.2
8.24 (Gap: Partial Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **CEK-02.1**: Are cryptography, encryption, and key management roles and responsibilities defined and implemented?

---

## CEK-03: Data Encryption

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Shared Orchestrated Service Provider-Application Provider (Shared OSP-AP)

**Lifecycle Relevance:**
- Preparation: Data curation, Data storage
- Development: Training
- Evaluation/Validation: Evaluation, Validation/Red Teaming, Re-evaluation
- Deployment: AI Services supply chain, AI applications
- Delivery: Maintenance, Continuous improvement
- Service Retirement: Archiving, Data deletion

### Specification

Provide data protection at-rest, in-transit and, where applicable, in-use by using cryptographic libraries certified to approved standards.

### Cross-References

- **bsi_aic4**: CRY-02
CRY-03 (Gap: No Gap)
- **eu_ai_act**: Recital 69, page 20/144 (Gap: Partial Gap)
- **iso_42001**: No Mapping for ISO 42001
ISO 27001:2022  A.8.24
ISO 27002:2022  A.8.24 (Gap: Partial Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **CEK-03.1**: Is data protection, at-rest, in-transit and where applicable in-use, provided by using cryptographic libraries certified to approved standards?

---

## CEK-04: Encryption Algorithm

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Orchestrated Services: Shared Orchestrated Service Provider-Application Provider (Shared OSP-AP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data collection, Data curation, Data storage
- Development: Training
- Evaluation/Validation: Evaluation, Validation/Red Teaming, Re-evaluation
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Archiving, Data deletion

### Specification

Utilize encryption algorithms following industry standards for protecting data, based on the data classification and associated risks.

### Cross-References

- **bsi_aic4**: CRY-01
CRY-02
CRY-03
COS-08 (Gap: Partial Gap)
- **eu_ai_act**: Recital 69, page 20/144 (Gap: No Gap)
- **iso_42001**: No Mapping for ISO 42001
ISO 27001:2022  A.8.24
ISO 27002:2022  A.8.24 (Gap: Partial Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **CEK-04.1**: Are encryption algorithms utilized following industry standards for protecting data, based on the data classification and associated risks?

---

## CEK-05: Encryption Change Management

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared across the supply chain
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Shared Orchestrated Service Provider-Application Provider (Shared OSP-AP)

**Lifecycle Relevance:**
- Preparation: Data storage, Resource provisioning
- Development: Guardrails
- Evaluation/Validation: N/A
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Archiving, Data deletion, Model disposal

### Specification

Establish a standard change management procedure, to accommodate changes from internal and external sources, for review, approval, implementation and communication of cryptographic, encryption and key management technology changes.

### Cross-References

- **bsi_aic4**: CRY-01
CRY-04
DEV-03 (Gap: No Gap)
- **eu_ai_act**: Article 17 (1) (a) (Gap: Partial Gap)
- **iso_42001**: No Mapping for ISO 42001
ISO 27001: A.8.32
ISO 27002: 8.32
8.24 (Gap: Partial Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **CEK-05.1**: Are standard change management procedures established to review, approve, implement, and communicate cryptography, encryption, and key management technology changes that accommodate internal and external sources?

---

## CEK-06: Encryption Change Cost Benefit Analysis

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Owned by the Orchestrated Service Provider (OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data storage, Resource provisioning
- Development: Guardrails
- Evaluation/Validation: Re-evaluation
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Data deletion, Model disposal

### Specification

Manage and adopt changes to cryptography-, encryption-, and key management-related systems (including policies and procedures) that fully account for downstream effects of proposed changes, including residual risk, cost, and benefits analysis.

### Cross-References

- **bsi_aic4**: CRY-01
CRY-04
DEV-03
DEV-07 (Gap: Partial Gap)
- **eu_ai_act**: No Mapping (Gap: Full Gap)
- **iso_42001**: No Mapping for ISO 42001
ISO 27001: A.8.32
ISO 27002: 8.32
8.24 (Gap: Partial Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **CEK-06.1**: Are changes to cryptography-, encryption- and key management-related systems, policies, and procedures, managed and adopted in a manner that fully accounts for downstream effects of proposed changes, including residual risk, cost, and benefits analysis?

---

## CEK-07: Encryption Risk Management

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Shared Orchestrated Service Provider-Application Provider (Shared OSP-AP)

**Lifecycle Relevance:**
- Preparation: Data storage
- Development: Guardrails
- Evaluation/Validation: N/A
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Data deletion, Model disposal

### Specification

Establish and maintain an encryption and key management risk program that includes provisions for risk assessment, risk treatment, risk context, monitoring, and feedback.

### Cross-References

- **bsi_aic4**: CRY-01
CRY-04
OIS-06
OIS-07 (Gap: No Gap)
- **eu_ai_act**: Article 9 (1)
Article 9 (2) (a), (b), (c), (d) (Gap: Partial Gap)
- **iso_42001**: No Mapping for ISO 42001
ISO 27001: A.8.24
Clause 6.1
ISO 27002: 8.24
5.1
5.7 (Gap: Partial Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **CEK-07.1**: Is a cryptography, encryption, and key management risk program established and maintained that includes risk assessment, risk treatment, risk context, monitoring,
 and feedback provisions?

---

## CEK-08: Customer Key Management Capability

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Compute, Storage, Application, Data
**Threat Categories:** Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Owned by the Cloud Service Provider (CSP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared across the supply chain
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data storage
- Development: N/A
- Evaluation/Validation: N/A
- Deployment: N/A
- Delivery: N/A
- Service Retirement: Data deletion

### Specification

Providers must provide the capability for customers to manage their  own data encryption keys.

### Cross-References

- **bsi_aic4**: C4 DM-04
C5 CRY-03 (Gap: No Gap)
- **eu_ai_act**: No Mapping (Gap: Full Gap)
- **iso_42001**: No Mapping for ISO 42001
ISO 27001: A.8.24
ISO 27002: 8.24 (Gap: Partial Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **CEK-08.1**: Are providers providing customers with the capability to manage their own data encryption keys?

---

## CEK-09: Encryption and Key Management Audit

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Shared Orchestrated Service Provider-Application Provider (Shared OSP-AP)

**Lifecycle Relevance:**
- Preparation: Data storage
- Development: Guardrails
- Evaluation/Validation: Re-evaluation
- Deployment: AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Data deletion

### Specification

Audit encryption and key management systems, policies, and processes with a frequency that is proportional to the risk exposure of the system  with audit occurring preferably continuously but at least annually and after  any security event(s).

### Cross-References

- **bsi_aic4**: CRY-01
CRY-04
OIS-06
OIS-07 (Gap: No Gap)
- **eu_ai_act**: Annex VII 5.3 (Gap: Partial Gap)
- **iso_42001**: No Mapping for ISO 42001
ISO 27001: A.8.24
A.12.7.1
Clause 9.2
ISO 27002: 8.24
12.7.1
8.34 (Gap: Partial Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **CEK-09.1**: Are encryption and key management systems, policies, and processes audited with a frequency proportional to the system's risk exposure?
- **CEK-09.2**: Are encryption and key management systems, policies, and processes audited preferably continuously but at least annually and after any security event?

---

## CEK-10: Key Generation

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Compute, Application
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data storage
- Development: N/A
- Evaluation/Validation: N/A
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Maintenance, Continuous monitoring
- Service Retirement: Data deletion

### Specification

Generate Cryptographic keys using industry accepted cryptographic libraries specifying the algorithm strength and the random number  generator used.

### Cross-References

- **bsi_aic4**: CRY-02
CRY-03
CRY-04 (Gap: No Gap)
- **eu_ai_act**: No Mapping (Gap: Full Gap)
- **iso_42001**: No Mapping for ISO 42001
ISO 27001: A.8.24
ISO 27002: 8.24 (Gap: Partial Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **CEK-10.1**: Are cryptographic keys generated using industry-accepted and approved cryptographic libraries that specify algorithm strength and random number generator specifications?

---

## CEK-11: Key Purpose

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Shared Orchestrated Service Provider-Application Provider (Shared OSP-AP)

**Lifecycle Relevance:**
- Preparation: Data storage
- Development: Guardrails
- Evaluation/Validation: N/A
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Archiving, Data deletion, Model disposal

### Specification

Manage cryptographic secret and private keys that are provisioned for a unique purpose.

### Cross-References

- **bsi_aic4**: CRY-04 (Gap: No Gap)
- **eu_ai_act**: No Mapping (Gap: Full Gap)
- **iso_42001**: No Mapping for ISO 42001
ISO 27001: A.8.24
ISO 27002: 8.24 (Gap: Partial Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **CEK-11.1**: Are cryptographic secrets and private keys that are provisioned for a unique purpose properly managed?

---

## CEK-12: Key Rotation

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Shared Orchestrated Service Provider-Application Provider (Shared OSP-AP)

**Lifecycle Relevance:**
- Preparation: Data storage
- Development: N/A
- Evaluation/Validation: N/A
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring
- Service Retirement: Archiving, Data deletion, Model disposal

### Specification

Rotate cryptographic keys in accordance with the calculated cryptoperiod, which includes provisions for considering the risk of information disclosure and legal and regulatory requirements.

### Cross-References

- **bsi_aic4**: CRY-04 (Gap: No Gap)
- **eu_ai_act**: No Mapping (Gap: Full Gap)
- **iso_42001**: No Mapping for ISO 42001
ISO 27001: No Mapping
ISO 27002: Control 8.24 (Gap: Partial Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **CEK-12.1**: Are cryptographic keys rotated based on a cryptoperiod calculated while considering information disclosure risks, and legal and regulatory requirements?

---

## CEK-13: Key Revocation

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Orchestrated Service Provider-Application Provider (Shared OSP-AP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data storage
- Development: Guardrails
- Evaluation/Validation: N/A
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Archiving, Data deletion, Model disposal

### Specification

Define, implement and evaluate processes, procedures and technical measures to revoke and remove cryptographic keys prior to the end of its established cryptoperiod, when a key is compromised, or an entity is no longer part of the organization, which include provisions for legal and regulatory requirements.

### Cross-References

- **bsi_aic4**: CRY-04 (Gap: No Gap)
- **eu_ai_act**: No Mapping (Gap: Full Gap)
- **iso_42001**: No Mapping for ISO 42001
ISO 27001: A.8.24
ISO 27002: 8.24 (Gap: Partial Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **CEK-13.1**: Are cryptographic keys revoked and removed before the end of the established cryptoperiod (when a key is compromised, or an entity is no longer part of the organization) per defined, implemented, and evaluated processes, procedures, and technical measures which include legal and regulatory requirement provisions?

---

## CEK-14: Key Destruction

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared across the supply chain
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Shared Application Provider-AI Customer (Shared AP-AIC)

**Lifecycle Relevance:**
- Preparation: Data storage
- Development: N/A
- Evaluation/Validation: N/A
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring
- Service Retirement: Archiving, Data deletion, Model disposal

### Specification

Define, implement, and evaluate processes, procedures, and technical measures to securely destroy cryptographic keys when they are no longer needed, which include provisions for legal and regulatory requirements.

### Cross-References

- **bsi_aic4**: CRY-04
AM-04 (Gap: No Gap)
- **eu_ai_act**: No Mapping (Gap: Full Gap)
- **iso_42001**: No Mapping for ISO 42001
ISO 27001: A.8.24
ISO 27002: 8.24 (Gap: Partial Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **CEK-14.1**: Are processes, procedures, and technical measures which include provisions for legal and regulatory requirements, defined, implemented and evaluated, to securely destroy cryptographic keys when they are no longer needed?

---

## CEK-15: Key Activation

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Compute, Storage, Application
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Owned by the Cloud Service Provider (CSP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data storage
- Development: N/A
- Evaluation/Validation: N/A
- Deployment: N/A
- Delivery: Maintenance
- Service Retirement: Archiving, Model disposal

### Specification

Define, implement and evaluate processes, procedures and technical measures to create keys in a pre-activated state when they have been generated but not authorized for use, which include provisions for legal and regulatory requirements.

### Cross-References

- **bsi_aic4**: CRY-04 (Gap: No Gap)
- **eu_ai_act**: No Mapping (Gap: Full Gap)
- **iso_42001**: No Mapping for ISO 42001
ISO 27001: A.8.24
ISO 27002: 8.24 (Gap: Partial Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **CEK-15.1**: Are processes, procedures, and technical measures to create keys in a pre-activated state (i.e., when they have been generated but not authorized for use) defined, implemented, and evaluated, including provisions for legal and regulatory requirements?

---

## CEK-16: Key Suspension

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Orchestrated Service Provider-Application Provider (Shared OSP-AP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data storage
- Development: N/A
- Evaluation/Validation: N/A
- Deployment: AI Services supply chain
- Delivery: Operations, Maintenance, Continuous monitoring
- Service Retirement: Archiving

### Specification

Define, implement and evaluate processes, procedures and technical measures to monitor, review and approve key transitions from any  state to/from suspension, which include provisions for legal and regulatory  requirements.

### Cross-References

- **bsi_aic4**: CRY-04 (Gap: No Gap)
- **eu_ai_act**: No Mapping (Gap: Full Gap)
- **iso_42001**: No Mapping for ISO 42001
ISO 27001: A.8.24
ISO 27002: 8.24 (Gap: Partial Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **CEK-16.1**: Are processes, procedures, and technical measures to monitor, review, and approve key transitions (e.g., from any state to/from suspension) defined, implemented, and evaluated including provisions for legal and regulatory requirements?

---

## CEK-17: Key Deactivation

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared across the supply chain
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Shared Orchestrated Service Provider-Application Provider (Shared OSP-AP)

**Lifecycle Relevance:**
- Preparation: Data storage
- Development: Training
- Evaluation/Validation: N/A
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Archiving, Data deletion, Model disposal

### Specification

Define, implement and evaluate processes, procedures and technical measures to deactivate keys at the time of their expiration date, which  include provisions for legal and regulatory requirements.

### Cross-References

- **bsi_aic4**: CRY-04 (Gap: No Gap)
- **eu_ai_act**: No Mapping (Gap: Full Gap)
- **iso_42001**: No Mapping for ISO 42001
ISO 27001: A.8.24
ISO 27002: 8.24 (Gap: Partial Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **CEK-17.1**: Are processes, procedures, and technical measures to deactivate keys (at the time of their expiration date) defined, implemented, and evaluated including provisions for legal and regulatory requirements?

---

## CEK-18: Key Archival

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Owned by the Cloud Service Provider (CSP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data storage
- Development: N/A
- Evaluation/Validation: N/A
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring
- Service Retirement: Archiving, Model disposal

### Specification

Define, implement and evaluate processes, procedures and technical measures to manage archived keys in a secure repository requiring least  privilege access, which include provisions for legal and regulatory  requirements.

### Cross-References

- **bsi_aic4**: CRY-01
CRY-04
PSS-08 (Gap: No Gap)
- **eu_ai_act**: No Mapping (Gap: Full Gap)
- **iso_42001**: No Mapping for ISO 42001
ISO 27001: A.8.24
A.8.2.1
ISO 27002: 8.24
8.4 (Gap: Partial Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **CEK-18.1**: Are processes, procedures, and technical measures to manage archived keys in a secure repository (requiring least privilege access) defined, implemented, and evaluated including provisions for legal and regulatory requirements?

---

## CEK-19: Key Compromise

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Shared Orchestrated Service Provider-Application Provider (Shared OSP-AP)

**Lifecycle Relevance:**
- Preparation: Data storage
- Development: N/A
- Evaluation/Validation: N/A
- Deployment: N/A
- Delivery: Maintenance
- Service Retirement: Data deletion

### Specification

Define, implement and evaluate processes, procedures and technical measures to use compromised keys to encrypt information only in  controlled circumstance, and thereafter exclusively for decrypting data  and never for encrypting data, which include provisions for legal and  regulatory requirements.

### Cross-References

- **bsi_aic4**: CRY-01
CRY-03
CRY-04 (Gap: No Gap)
- **eu_ai_act**: No Mapping (Gap: Full Gap)
- **iso_42001**: No Mapping for ISO 42001
ISO 27001: A.8.24
ISO 27002: 8.24 (Gap: Partial Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **CEK-19.1**: Are processes, procedures, and technical measures to use compromised keys to encrypt information in specific scenarios (e.g., only in controlled circumstances and thereafter only for data decryption and never for encryption) defined  implemented, and evaluated including provisions for legal and regulatory requirement?

---

## CEK-20: Key Recovery

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Owned by the Orchestrated Service Provider (OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data storage
- Development: N/A
- Evaluation/Validation: N/A
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring
- Service Retirement: Archiving, Data deletion, Model disposal

### Specification

Define, implement and evaluate processes, procedures and technical measures to assess the risk to operational continuity versus the risk of  the keying material and the information it protects being exposed if  control of the keying material is lost, which include provisions for legal  and regulatory requirements.

### Cross-References

- **bsi_aic4**: OIS-06
CRY-04
OPS-18 (Gap: No Gap)
- **eu_ai_act**: No Mapping (Gap: Full Gap)
- **iso_42001**: No Mapping for ISO 42001
ISO 27001: A.8.24
Clause 6.1.2
ISO 27002: 8.24
5.7 (Gap: Partial Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **CEK-20.1**: Are processes, procedures, and technical measures to assess operational continuity risks (versus the risk of losing control of keying material and exposing protected data) defined, implemented, and evaluated, including provisions for legal and regulatory requirement provisions?

---

## CEK-21: Key Inventory Management

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Orchestrated Service Provider-Application Provider (Shared OSP-AP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data collection, Data curation, Data storage
- Development: Training
- Evaluation/Validation: Evaluation, Validation/Red Teaming, Re-evaluation
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Archiving, Data deletion, Model disposal

### Specification

Define, implement and evaluate processes, procedures and technical measures in order for the key management system to track and report  all cryptographic materials and changes in status, which include provisions  for legal and regulatory requirements.

### Cross-References

- **bsi_aic4**: CRY-04 (Gap: No Gap)
- **eu_ai_act**: No Mapping (Gap: Full Gap)
- **iso_42001**: No Mapping for ISO 42001
ISO 27001: A.8.24
A.12.4.1
ISO 27002: 8.24
12.4.1 (Gap: Full Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **CEK-21.1**: Are key management system processes, procedures, and technical measures defined, implemented, and evaluated to track and report all cryptographic materials and status changes including provisions for legal and regulatory requirements?

---

# Domain: Datacenter Security

## DCS-01: Off-Site Equipment Disposal Policy and Procedures

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Sensitive data disclosure, Model theft, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Owned by the Cloud Service Provider (CSP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Shared Orchestrated Service Provider-Application Provider (Shared OSP-AP)

**Lifecycle Relevance:**
- Preparation: Data collection, Data curation, Data storage
- Development: Design, Training, Supply Chain
- Evaluation/Validation: Evaluation, Re-evaluation, Validation/Red Teaming
- Deployment: AI Services supply chain
- Delivery: Operations, Maintenance
- Service Retirement: Data deletion, Model disposal

### Specification

Establish, document, approve, communicate, apply, evaluate and maintain policies and procedures for the secure disposal of equipment used outside  the organization's premises. If the equipment is not physically destroyed  a data destruction procedure that renders recovery of information  impossible must be applied. Review and update the policies and  procedures at least annually, or upon significant changes.

### Cross-References

- **bsi_aic4**: AM-02
AM-04 (Gap: No Gap)
- **eu_ai_act**: No Mapping (Gap: Full Gap)
- **iso_42001**: 42001: A.2.2 AI Policy
42001: A.2.4 Review of AI Policy
42001: A.4.2 Resource documentation
42001: A.4.3 Data Resources
42001: A.4.4 Tooling Resources
42001: A.2.3 Alignment with other organizational policies
27001: 7.5 (7.5.1 to 7.5.3) Documentation Information
27001: A.5.1 Policies for information security
27001: A.5.4 Management responsibilities
27001: A.5.11 Return of assets
27001: A.5.37 Documented operating procedures
27001: A.6.7 Remote working
27001: A.7.10 - Storage media
27001: A.7.14 - Secure disposal or re-use of equipment
27001: A.8.10 - Information deletion
27002: 5.1 Policies for information security
27002: 5.4 Management responsibilities
27002: 5.11 Return of assets
27002: 7.10 - Storage media
27002: 7.14 - Secure disposal or re-use of equipment (Gap: Partial Gap)
- **nist_ai_600_1**: GV-1.7-002
GV-4.1-003 (Gap: Partial Gap)

### CAIQ Questions

- **DCS-01.1**: Are policies and procedures for the secure disposal of equipment used outside the organization's premises established, documented, approved, communicated, enforced, and maintained?
- **DCS-01.2**: Is a data destruction procedure applied that renders information recovery  information impossible if equipment is not physically destroyed?
- **DCS-01.3**: Are all policies and procedures for the secure disposal of equipment used outside the organization's premises reviewed and updated at least annually, or upon significant changes?

---

## DCS-02: Off-Site Transfer Authorization Policy and Procedures

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Owned by the Cloud Service Provider (CSP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Shared Orchestrated Service Provider-Application Provider (Shared OSP-AP)

**Lifecycle Relevance:**
- Preparation: Data storage, Resource provisioning
- Development: N/A
- Evaluation/Validation: N/A
- Deployment: AI Services supply chain, AI applications
- Delivery: Operations, Maintenance
- Service Retirement: Archiving, Data deletion, Model disposal

### Specification

Establish, document, approve, communicate, apply, evaluate and maintain policies and procedures for the relocation or transfer of hardware, software, or data/information to an offsite or alternate location. The relocation or transfer request requires the written or cryptographically verifiable authorization. Review and update the policies and procedures at least annually, or upon significant changes.

### Cross-References

- **bsi_aic4**: AM-02
AM-04
AM-05 (Gap: No Gap)
- **eu_ai_act**: No Mapping (Gap: Full Gap)
- **iso_42001**: 42001: A.2.3 Alignment with other organizational policies
42001: A.4.2 Resource Documentation
27001: 5.1 Leadership and Commitment
27001: 5.2 Policy
27001: 7.3 Awareness
27001: 7.4 Communication
27001: 7.5 (7.5.1 to 7.5.3) Documentation Information
27001: 9.1 Monitoring
measurement
analysis and evaluation
27001: 9.3 Management review
27001: A.5.1 Policies for information security
27001: A.5.4 Management responsibilities
27001: A.5.14 Information transfer
27001: A.5.36 Compliance with policies
rules and standards for information security
27001: A.5.37 Documented operating procedures
27001: A.7.8 Equipment siting and protection
27001: A.7.9 Security of assets off-premises
27001: A.7.10 Storage media
27001: A7.13 Equipment maintenance
27001: A7.14 Secure disposal or re-use of equipment
27002: 5.1 Policies for information security
27002: 5.4 Management responsibilities
27002: 5.14 Information transfer
27002: 5.36 Compliance with policies
rules and standards for information security
27002: 5.37 Documented operating procedures
27002: 7.8 Equipment siting and protection
27002: 7.9 Security of assets off-premises
27002: 7.10 Storage media
27002: 7.13 Equipment maintenance
27002: 7.14 Secure disposal or re-use of equipment (Gap: Partial Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **DCS-02.1**: Are policies and procedures for the relocation or transfer of hardware, software, or data/information to an offsite or alternate location established, documented, approved, communicated, implemented, enforced, maintained?
- **DCS-02.2**: Are the written or cryptographically verifiable authorization required for relocation or transfer request?
- **DCS-02.3**: Are policies and procedures for the relocation or transfer of hardware, software, or data/information to an offsite or alternate location reviewed and updated at least annually, or upon significant changes?

---

## DCS-03: Secure Area Policy and Procedures

**Type:** control
**Control Type:** Cloud-Specific
**Architectural Relevance:** Physical, Network
**Threat Categories:** Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Owned by the Cloud Service Provider (CSP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Shared Orchestrated Service Provider-Application Provider (Shared OSP-AP)

**Lifecycle Relevance:**
- Preparation: Data storage, Resource provisioning, Team and expertise
- Development: N/A
- Evaluation/Validation: N/A
- Deployment: Orchestration, AI Services supply chain
- Delivery: Operations, Maintenance
- Service Retirement: Archiving, Data deletion, Model disposal

### Specification

Establish, document, approve, communicate, apply, evaluate and maintain policies and procedures for maintaining a safe and secure working environment in offices, rooms, and facilities. Review and update the policies and procedures at least annually, or upon significant changes.

### Cross-References

- **bsi_aic4**: AM-02
PS-01 (Gap: No Gap)
- **eu_ai_act**: No Mapping (Gap: Full Gap)
- **iso_42001**: 42001: A.2.2 AI Policy
42001: A.2.3 Alignment with other organizational policies
42001: A.2.4 Review of the AI Policy
27001: 5.1 Leadership and Commitment
27001: 5.2 Policy
27001: 7.3 Awareness
27001: 7.4 Communication
27001: 7.5 (7.5.1 to 7.5.3) Documentation Information
27001: 9.1 Monitoring
measurement
analysis and evaluation
27001: 9.3 Management review
27001: A.5.1 Policies for information security
27001: A.5.4 Management responsibilities
27001: A.7.1 Physical security perimeters
27001: A.7.2 Physical entry
27001: A.7.1 Securing offices
rooms and facilities
27001: A.7.4 Physical security monitoring
27002: 7.1 Physical Security perimeters
27002: 7.2 Physical entry
27002: 7.3 Securing offices
rooms and facilities
27002: 7.4 Physical security monitoring (Gap: Partial Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **DCS-03.1**: Are policies and procedures for maintaining a safe and secure working environment (in offices, rooms, and facilities) established, documented, approved, communicated, applied, evaluated and maintained?
- **DCS-03.2**: Are policies and procedures for maintaining safe, secure working environments (e.g., offices, rooms, and facilities) reviewed and updated at least annually, or upon significant changes?

---

## DCS-04: Secure Media Transportation Policy and Procedures

**Type:** control
**Control Type:** Cloud-Specific
**Architectural Relevance:** Physical
**Threat Categories:** Sensitive data disclosure, Model theft, Insecure supply chain

**Ownership:**
- GenAI OPS/PI: Owned by the Cloud Service Provider (CSP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Shared Orchestrated Service Provider-Application Provider (Shared OSP-AP)

**Lifecycle Relevance:**
- Preparation: Data storage
- Development: N/A
- Evaluation/Validation: N/A
- Deployment: AI Services supply chain
- Delivery: N/A
- Service Retirement: Archiving

### Specification

Establish, document, approve, communicate, apply, evaluate and maintain policies and procedures for the secure transportation of physical media. Review and update the policies and procedures at least annually, or upon significant changes.

### Cross-References

- **bsi_aic4**: AM-02 (Gap: No Gap)
- **eu_ai_act**: Article 9 (Risk Management)
Article 15 (Gap: Partial Gap)
- **iso_42001**: 42001: A.2.3 Alignment with other organizational policies
42001: A.4.2 Resource Documentation
27001: 5.1 Leadership and Commitment
27001: 5.2 Policy
27001: 7.3 Awareness
27001: 7.4 Communication
27001: 7.5 (7.5.1 to 7.5.3) Documentation Information
27001: 9.1 Monitoring
measurement
analysis and evaluation
27001: 9.3 Management review
27001: A.5.1 Policies for information security
27001: A.5.4 Management responsibilities
27001: A.5.14 Information Transfer
27001: A.5.36 Compliance with policies
rules and standards for
information security
27001: A.5.37 Documented operating procedures
27001: A.7.10 - Storage media
27002: 5.1 - Policies for Information Security
27002: 5.14 - Information transfer
27002: 5.36 Compliance with policies
rules and standards for
information security
27002: 5.37 Documented Operating procedures
27002: 7.10 Storage Media
27002: 7.9 – Equipment security (Gap: Partial Gap)
- **nist_ai_600_1**: GV-4.1-003 (Gap: Partial Gap)

### CAIQ Questions

- **DCS-04.1**: Are policies and procedures for the secure transportation of physical media  established, documented, approved, communicated, applied, evaluated, and maintained?
- **DCS-04.2**: Are policies and procedures for the secure transportation of physical media reviewed and updated at least annually, or upon significant changes?

---

## DCS-05: Assets Classification

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Owned by the Cloud Service Provider (CSP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data curation, Resource provisioning
- Development: N/A
- Evaluation/Validation: N/A
- Deployment: N/A
- Delivery: Operations
- Service Retirement: N/A

### Specification

Classify and document the physical, and logical assets (e.g., applications) based on the organizational business risk. Review and update the assets’ classification at least annually or upon significant changes.

### Cross-References

- **bsi_aic4**: AM-02 (Gap: No Gap)
- **eu_ai_act**: No Mapping (Gap: Full Gap)
- **iso_42001**: 42001: 6.1.2 AI Risk Assessment
42001: A.4.2 Resource documentation
42001: A.4.3 Data resources
42001: A.4.4 Tooling resources
42001: A.4.5 System and computing resources
42001: A.2.3 Alignment with other organizational policies
27001: 6.1.2 Information security risk assessment
27001: A.5.9 Inventory of information and other associated assets
27001: A.5.12 - Classification of information
27001: A.5.37 - Documented operating procedures
27001: A.5.29 - Information security during disruption
27002: 5.9 Inventory of information and other associated assets
27002: 5.12 - Classification of information
27002: 5.37 - Documented operating procedures
27002: 5.29 - Information Security during disruption (Gap: No Gap)
- **nist_ai_600_1**: GV-1.6-001
GV-1.6-002
GV-1.6-003 (Gap: Partial Gap)

### CAIQ Questions

- **DCS-05.1**: Are the physical and logical assets (e.g. applications) classified and documented based on the organizational business risk?
- **DCS-05.2**: Is the assets' classification reviewed and updated at least annually or upon significant changes?

---

## DCS-06: Assets Cataloguing and Tracking

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Owned by the Cloud Service Provider (CSP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Resource provisioning
- Development: N/A
- Evaluation/Validation: N/A
- Deployment: AI Services supply chain, AI applications
- Delivery: Operations
- Service Retirement: N/A

### Specification

Catalogue and track all relevant physical and logical assets located at all of the service providers sites within a secured system.  Review and update the catalogue at least annually or upon significant changes.

### Cross-References

- **bsi_aic4**: AM-01 (Gap: No Gap)
- **eu_ai_act**: No Mapping (Gap: Full Gap)
- **iso_42001**: 42001: A.4.2 Resource documentation
42001: A.4.3 Data resources
42001: A.4.4 Tooling resources
42001: A.4.5 System and computing resources
42001: A.2.3 Alignment with other organizational policies
27001: A.5.9 - inventory of information and other associated assets
27002: 5.9 - Inventory of information and other associated assets (Gap: No Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **DCS-06.1**: Are all relevant physical and logical assets located at service provider sites catalogued and tracked within a secured system?
- **DCS-06.2**: Are catalogues reviewed and updated at least annually or upon significant changes?

---

## DCS-07: Controlled Physical Access Points

**Type:** control
**Control Type:** Cloud-Specific
**Architectural Relevance:** Physical
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Owned by the Cloud Service Provider (CSP)
- Model: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data storage
- Development: N/A
- Evaluation/Validation: N/A
- Deployment: N/A
- Delivery: Operations
- Service Retirement: N/A

### Specification

Design and implement physical security perimeters to safeguard personnel, data, and information systems.

### Cross-References

- **bsi_aic4**: PS-03 (Gap: No Gap)
- **eu_ai_act**: No Mapping (Gap: Full Gap)
- **iso_42001**: 42001: A.2.3 Alignment with other organizational policies
42001: A.4.2 Resource Documentation
27001: A.7.1 - Physical security perimeters
27001: A.7.2 Physical entry
27001: A.7.1 Securing offices
rooms and facilities
27001: A.7.4 Physical security monitoring
27002: 7.1 - Physical security perimeters
27002: 7.2 Physical entry
27002: 7.3 Securing offices
rooms and facilities
27002: 7.4 Physical security monitoring (Gap: No Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **DCS-07.1**: Are physical security perimeters designed and implemented to safeguard personnel, data, and information systems?

---

## DCS-08: Equipment Identification

**Type:** control
**Control Type:** Cloud-Specific
**Architectural Relevance:** Physical, Network, Compute, Storage, Application
**Threat Categories:** Sensitive data disclosure, Model theft

**Ownership:**
- GenAI OPS/PI: Owned by the Cloud Service Provider (CSP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: N/A
- Development: N/A
- Evaluation/Validation: N/A
- Deployment: N/A
- Delivery: Operations
- Service Retirement: N/A

### Specification

Use equipment identification as a method for connection authentication.

### Cross-References

- **bsi_aic4**: AM-06 (Gap: Partial Gap)
- **eu_ai_act**: No Mapping (Gap: Full Gap)
- **iso_42001**: 42001: A.2.3 Alignment with other organizational policies
42001: A.6.2.6 AI System Operation and Monitoring
27001: A.8.1 - User endpoint devices
27001: A.8.5 - Secure authentication
27001: A.8.16 - Monitoring activities
27001: A.8.20 - Network security
27002: 8.1 - User endpoint devices
27002: 8.5 - Secure Authentication
27002: 8.16 - Monitoring activities
27002: 8.20 - Network security (Gap: No Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **DCS-08.1**: Is equipment identification used as a method for connection authentication?

---

## DCS-09: Secure Area Authorization

**Type:** control
**Control Type:** Cloud-Specific
**Architectural Relevance:** Physical
**Threat Categories:** Sensitive data disclosure, Model theft

**Ownership:**
- GenAI OPS/PI: Owned by the Cloud Service Provider (CSP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: N/A
- Development: N/A
- Evaluation/Validation: N/A
- Deployment: N/A
- Delivery: Operations
- Service Retirement: N/A

### Specification

Allow only authorized personnel access to secure areas, with all ingress and egress points restricted, documented, and monitored by  physical access control mechanisms. Retain access control records on a  periodic basis as deemed appropriate by the organization.

### Cross-References

- **bsi_aic4**: PS-04 (Gap: No Gap)
- **eu_ai_act**: No Mapping (Gap: Full Gap)
- **iso_42001**: 42001: 42001: 8.1 Operational Planning and Control
42001: A.2.3 Alignment with other organizational policies
27001: A.7.1 Physical security perimeters
27001: A.7.2 - Physical entry
27001: A.7.3 Securing offices
rooms and facilities
27001: A.7.4 Physical security monitoring
27002: 7.1 Physical Security perimeters
27002: 7.2 (a
b) - Physical entry
27002: 7.3 Securing offices
rooms and facilities
27002: 7.4 Physical security monitoring (Gap: No Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **DCS-09.1**: Are solely authorized personnel able to access secure areas, with all ingress and egress areas restricted, documented, and monitored by physical access control mechanisms?
- **DCS-09.2**: Are access control records retained periodically, as deemed appropriate by the organization?

---

## DCS-10: Surveillance System

**Type:** control
**Control Type:** Cloud-Specific
**Architectural Relevance:** Physical
**Threat Categories:** Model theft, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Owned by the Cloud Service Provider (CSP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: N/A
- Development: N/A
- Evaluation/Validation: N/A
- Deployment: N/A
- Delivery: Operations
- Service Retirement: N/A

### Specification

Implement, maintain, and operate datacenter surveillance systems at the external perimeter and at all the ingress and egress points to  detect unauthorized ingress and egress attempts.

### Cross-References

- **bsi_aic4**: PS-03 (Gap: No Gap)
- **eu_ai_act**: No Mapping (Gap: Full Gap)
- **iso_42001**: 42001: 8.1 Operational Planning and Control
42001: A.2.3 Alignment with other organizational policies
27001: A.7.4 - Physical security monitoring
27002: 7.4 - Physical security monitoring (Gap: No Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **DCS-10.1**: Are datacenter surveillance systems at the external perimeter and at all the ingress and egress points, implemented, maintained, and operated to detect unauthorized ingress and egress attempts?

---

## DCS-11: Adverse Event Response Training

**Type:** control
**Control Type:** Cloud-Specific
**Architectural Relevance:** Physical
**Threat Categories:** Sensitive data disclosure, Model theft, Denial of Service

**Ownership:**
- GenAI OPS/PI: Owned by the Cloud Service Provider (CSP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Team and expertise
- Development: N/A
- Evaluation/Validation: N/A
- Deployment: N/A
- Delivery: Operations
- Service Retirement: N/A

### Specification

Train datacenter personnel to safely manage adverse events, including but not limited to unauthorized ingress and egress attempts.

### Cross-References

- **bsi_aic4**: HR-03 (Gap: No Gap)
- **eu_ai_act**: No Mapping (Gap: Full Gap)
- **iso_42001**: 42001: A.4.6 Human Resource
42001: A.2.3 Alignment with other organizational policies
27001: 7.5 Protecting against physical and environmental threats
27001: A.5.24 - Information security incident management planning and preparation
27001: A.6.3 - Information security awareness
education and training
27001: A.6.8 - Information security event reporting
27002: 5.24 (d
e) - Information security incident management planning and preparation
27002: A.6.3 Information security awareness
education and training
27002: 6.8 (e) - Information security event reporting
27002: 7.5 Protecting against physical and environmental threats (Gap: No Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **DCS-11.1**: Are data center personnel trained to safely manage adverse events, including but not limited to unauthorized ingress and egress attempts?

---

## DCS-12: Cabling Security

**Type:** control
**Control Type:** Cloud-Specific
**Architectural Relevance:** Physical, Network, Compute, Storage
**Threat Categories:** Sensitive data disclosure, Model/Service Failure, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Owned by the Cloud Service Provider (CSP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: N/A
- Development: N/A
- Evaluation/Validation: N/A
- Deployment: N/A
- Delivery: Operations
- Service Retirement: N/A

### Specification

Define, implement and evaluate processes, procedures and technical measures that ensure a risk-based protection of power and telecommunication cables from a threat of interception, interference or damage at all facilities, offices and rooms.

### Cross-References

- **bsi_aic4**: PS-06 (Gap: No Gap)
- **eu_ai_act**: No Mapping (Gap: Full Gap)
- **iso_42001**: 42001: A.2.3 Alignment with other organizational policies
42001: 6.1.3 AI Risk Treatment
42001: A.4.5 System and computing resources
27001: A.5.1 Policies for information security
27001: A.5.36 Compliance with policies
rules and standards for information security
27001: A.5.37 Documented operating procedures
27001: A.7.12 Cabling Security
27001: A.5.1 Policies for information security
27002: 5.36 Compliance with policies
rules and standards for information security
27001: A.5.37 Documented operating procedures
27002: 7.12 - Cabling Security (Gap: No Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **DCS-12.1**: Are processes, procedures, and technical measures defined, implemented, and evaluated to ensure risk-based protection of power and telecommunication cables from interception, interference, or damage threats at all facilities, offices, and rooms?

---

## DCS-13: Environmental Systems

**Type:** control
**Control Type:** Cloud-Specific
**Architectural Relevance:** Physical
**Threat Categories:** Model/Service Failure, Denial of Service

**Ownership:**
- GenAI OPS/PI: Owned by the Cloud Service Provider (CSP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: N/A
- Development: N/A
- Evaluation/Validation: N/A
- Deployment: N/A
- Delivery: Operations
- Service Retirement: N/A

### Specification

Implement and maintain data center environmental control systems that monitor, maintain and test for continual effectiveness the temperature and humidity conditions within accepted industry standards.

### Cross-References

- **bsi_aic4**: PS-07 (Gap: No Gap)
- **eu_ai_act**: No Mapping (Gap: Full Gap)
- **iso_42001**: 42001: B.4.5 System and computing resources
42001: A.2.3 Alignment with other organizational policies
27001: A.7.5 Protecting against physical and environmental threats
27001: A.7.8 - Equipment siting and protection
27001: A.7.9 - Security of assets off-premises
27002: 7.5 Protecting against physical and environmental threats
27002: 7.8 (c
e) - Equipment siting and protection
27002: 7.9 (b) - Security of assets off-premises (Gap: No Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **DCS-13.1**: Are data center environmental control systems designed to implement and maintain, and test for continual effectiveness of temperature and humidity conditions within accepted industry standards?

---

## DCS-14: Secure Utilities

**Type:** control
**Control Type:** Cloud-Specific
**Architectural Relevance:** Physical, Network
**Threat Categories:** Model/Service Failure, Denial of Service

**Ownership:**
- GenAI OPS/PI: Owned by the Cloud Service Provider (CSP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: N/A
- Development: N/A
- Evaluation/Validation: N/A
- Deployment: N/A
- Delivery: Operations
- Service Retirement: N/A

### Specification

Secure, monitor, maintain, and test utilities services for continual effectiveness at planned intervals.

### Cross-References

- **bsi_aic4**: PS-06
BCM-04 (Gap: No Gap)
- **eu_ai_act**: No Mapping (Gap: Full Gap)
- **iso_42001**: 42001: 8.1 Operational Planning and Control
42001: 8.2 AI Risk Assessment
42001: 8.3 AI Risk Treatment
42001: 8.4 AI System Impact Assessment
42001: 9.1 Monitoring
Measurement
Analysis
and Evaluation
42001: A.4.5 System and computing resources
42001: A.2.3 Alignment with other organizational policies
27001: A.7.11 Supporting utilities
27002: 7.11 Supporting utilities (Gap: No Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **DCS-14.1**: Are utility services secured, monitored, maintained, and tested at planned intervals for continual effectiveness?

---

## DCS-15: Equipment Location

**Type:** control
**Control Type:** Cloud-Specific
**Architectural Relevance:** Physical, Network, Compute, Storage
**Threat Categories:** Model/Service Failure, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Owned by the Cloud Service Provider (CSP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: N/A
- Development: N/A
- Evaluation/Validation: N/A
- Deployment: N/A
- Delivery: Operations
- Service Retirement: N/A

### Specification

Keep business-critical equipment away from locations subject to high probability for environmental risk events.

### Cross-References

- **bsi_aic4**: PS-01 (Gap: No Gap)
- **eu_ai_act**: No Mapping (Gap: Full Gap)
- **iso_42001**: 42001: A.4.2 Resource Documentation
42001: A.4.5 System and computing resources
42001: A.5.4 Assessing AI Systems Impact on Individuals or Groups of individuals
42001: A.5.5 Assessing societal impacts of AI systems
42001: A.2.3 Alignment with other organizational policies
27001: A.7.5 - Protecting against physical and environmental threats
27001: A.7.8 - Equipment siting and protection
27002: 7.5 - Protecting against physical and environmental threats
27002: 7.8 - Equipment siting and protection (Gap: No Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **DCS-15.1**: Is business-critical equipment segregated from locations subject to a high probability of environmental risk events?

---

# Domain: Data Security and Privacy Lifecycle Management

## DSP-01: Security and Privacy Policy and Procedures

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Storage, Application, Data
**Threat Categories:** Sensitive data disclosure, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Owned by the Customer (AIC)
- Model: Owned by the Customer (AIC)
- Orchestrated Services: Shared across the supply chain
- Application: Shared Application Provider-AI Customer (Shared AP-AIC)

**Lifecycle Relevance:**
- Preparation: Data curation, Data storage, Team and expertise
- Development: Design, Guardrails
- Evaluation/Validation: Evaluation, Validation/Red Teaming
- Deployment: Orchestration, AI Services supply chain
- Delivery: Operations, Continuous monitoring, Continuous improvement
- Service Retirement: Data deletion, Model disposal

### Specification

Establish, document, approve, communicate, apply, evaluate and maintain policies and procedures for the classification, protection, preparation and handling of data throughout its lifecycle, and according to all applicable laws and regulations,standards, and risk level. Review and update the policies and procedures at least annually.

### Cross-References

- **bsi_aic4**: COS-08
AM-06
SP-02
AM-02
OPS-10
OPS-11
COM-01 (Gap: No Gap)
- **eu_ai_act**: Article 10
Article 17 (Gap: Partial Gap)
- **iso_42001**: 42001: A.2.2 AI Policy
42001: A.2.4 Review of AI Policy
42001: A.2.3 Alignment with other organizational policies
42001: A.4.3 Data Resources
42001: A.7.2 Data for development and enhancement of AI system
42001: A.7.2 Acquisition of data
27001: 5.1 Policies for information security
27001: 7.3 Awareness
27001: 7.4 Communication
27001: 7.5 Documented Information (7.5.1 to 7.5.3)
27001: 9.1 Monitoring
measurement
analysis and evaluation
27001: 9.3 Management review (9.3.1 to 9.3.3)
27001: A.5.1 Policies for information security
27001: A.5.4 - Management responsibilities
27001: A.5.10 - Acceptable use of information and other associated assets
27001: A.5.12 - Classification of information
27001: A.5.34 - Privacy and protection of personal identifiable information
27001: A.5.37 - Documented operating procedures
27002: 5.1 - Policies for information security
27002: 5.4 - Management responsibilities
27002: 5.10 - Acceptable use of information and other associated assets
27002: 5.12 - Classification of information
27002: 5.34 - Privacy and protection of personal identifiable information
27002: 5.37 - Documented operating procedures (Gap: No Gap)
- **nist_ai_600_1**: GV-1.1-001
GV-1.2-001
GV-4.1-001
MP-2.3-002
MP-4.1-003 (Gap: No Gap)

### CAIQ Questions

- **DSP-01.1**: Are Security and Privacy Policies and Procedures established, documented, approved, communicated, applied, evaluated, and maintained for the classification, protection, preparation, and handling of data throughout its lifecycle, and according to all applicable laws and regulations, standards, and risk level?
- **DSP-01.2**: Are Security and Privacy Policies and Procedures reviewed and updated at least annually?

---

## DSP-02: Secure Disposal

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Data
**Threat Categories:** Sensitive data disclosure, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Orchestrated Services: Shared Orchestrated Service Provider-Application Provider (Shared OSP-AP)
- Application: Shared Application Provider-AI Customer (Shared AP-AIC)

**Lifecycle Relevance:**
- Preparation: Data storage
- Development: Guardrails
- Evaluation/Validation: Evaluation
- Deployment: AI Services supply chain
- Delivery: Operations, Maintenance
- Service Retirement: Data deletion, Model disposal

### Specification

Apply industry accepted methods for the secure disposal of data from storage media such that data is not recoverable by any forensic means.

### Cross-References

- **bsi_aic4**: PI-03 (Gap: No Gap)
- **eu_ai_act**: Article 10
Article 18 (Gap: Partial Gap)
- **iso_42001**: 42001: A.4.3 Data Resources
42001: A.2.3 Alignment with other organizational policies
27001: A.7.10 - Storage media
27001: A.7.14 - Secure disposal or re-use of equipment
27001: A.8.10 - Information deletion
27002: 7.10 Secure reuse or disposal
27002: 7.14 - Secure disposal or re-use of equipment
27002: 8.10 - Information deletion (Gap: Partial Gap)
- **nist_ai_600_1**: GV-1.7-002 (Gap: Partial Gap)

### CAIQ Questions

- **DSP-02.1**: Are industry-accepted methods applied for securely disposing of data from storage media so that it is not recoverable by any forensic means?

---

## DSP-03: Data Inventory

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Storage, Application, Data
**Threat Categories:** Sensitive data disclosure, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Owned by the Customer (AIC)
- Model: Owned by the Customer (AIC)
- Orchestrated Services: Owned by the Customer (AIC)
- Application: Owned by the Customer (AIC)

**Lifecycle Relevance:**
- Preparation: Data storage, Data collection
- Development: Design
- Evaluation/Validation: Evaluation
- Deployment: Orchestration, AI Services supply chain
- Delivery: Operations, Maintenance, Continuous monitoring
- Service Retirement: Data deletion

### Specification

Create and maintain a data inventory, at least for any sensitive, regulated  and personal data. Review and update the inventory at least annually or upon significant changes.

### Cross-References

- **bsi_aic4**: DM-01 (Gap: No Gap)
- **eu_ai_act**: Article 10 (2)
Article 11 (1) (d) (Gap: No Gap)
- **iso_42001**: 42001: A.4.3 Data Resources
42001: A.7.3 Acquisition of Data
42001: A.2.3 Alignment with other organizational policies
27001: A.5.9 - Inventory use of information and other associated assets
27001: A.8.12 - Data leakage prevention (DLP)
27002: 5.9 - Inventory use of information and other associated assets
27002: 8.12 - Data leakage prevention (DLP) (Gap: No Gap)
- **nist_ai_600_1**: MP-2.3-002 (Gap: Partial Gap)

### CAIQ Questions

- **DSP-03.1**: Are data inventories created and maintained at least for any sensitive, regulated, and personal data?
- **DSP-03.2**: Are inventories reviewed and updated at least annually or upon significant changes?

---

## DSP-04: Data Classification

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Storage, Application, Data
**Threat Categories:** Sensitive data disclosure, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Owned by the Customer (AIC)
- Model: Owned by the Customer (AIC)
- Orchestrated Services: Owned by the Customer (AIC)
- Application: Owned by the Customer (AIC)

**Lifecycle Relevance:**
- Preparation: Data collection, Data storage
- Development: Design, Guardrails
- Evaluation/Validation: Evaluation
- Deployment: Orchestration, AI Services supply chain
- Delivery: Operations, Maintenance, Continuous monitoring
- Service Retirement: Data deletion, Archiving

### Specification

Classify data according to its type and sensitivity level.

### Cross-References

- **bsi_aic4**: COS-08
AM-06 (Gap: No Gap)
- **eu_ai_act**: Article 10 (2)
Article 11 (Gap: Partial Gap)
- **iso_42001**: 42001: A.4.3 Data Resources
42001: A.2.3 Alignment with other organizational policies
42001: A.5.2 AI system impact assessment process
42001: A.7.3 Acquisition of data
27001: A.5.12 - Classification of information
27002: 5.12 - Classification of information (Gap: No Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **DSP-04.1**: Are data classified according to its type and sensitivity level?

---

## DSP-05: Data Flow Documentation

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Network, Compute, Storage, Application, Data
**Threat Categories:** Sensitive data disclosure, Insecure supply chain, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Owned by the Customer (AIC)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data collection, Resource provisioning
- Development: Design
- Evaluation/Validation: Evaluation
- Deployment: Orchestration, AI Services supply chain
- Delivery: Operations, Maintenance, Continuous monitoring
- Service Retirement: Archiving, Data deletion

### Specification

Create data flow documentation to identify what data is processed, stored or transmitted where. Review data flow documentation at defined intervals, at least annually, and after any change.

### Cross-References

- **bsi_aic4**: DM-03
DM-04
PC-02
BC-05 (Gap: No Gap)
- **eu_ai_act**: Article 11 (1)
Article 10 (2) (e) (Gap: No Gap)
- **iso_42001**: 42001: 7.5.2 Creating and updating documented information
42001: A.4.2 Resource Documentation
42001: A.4.3 Data Resources
42001: A.7.2 Data for development and enhancement of AI system
42001: A.7.3 Acquisition of data
42001: A.7.5 Data provenance
27001: 7.5.2 Creating and Updating (Gap: Partial Gap)
- **nist_ai_600_1**: GV-6.1-003 (Gap: Partial Gap)

### CAIQ Questions

- **DSP-05.1**: Are data flow documentation created to identify what data is processed, stored, or transmitted where?
- **DSP-05.2**: Are data flow documentation reviewed at defined intervals, at least annually, and after any change?

---

## DSP-06: Data Ownership and Stewardship

**Type:** control
**Control Type:** Cloud & AI Related
**Threat Categories:** Sensitive data disclosure, Insecure supply chain, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Team and expertise
- Development: Guardrails
- Evaluation/Validation: Evaluation
- Deployment: Orchestration, AI Services supply chain
- Delivery: Operations, Maintenance, Continuous monitoring
- Service Retirement: Data deletion, Model disposal

### Specification

Document ownership and stewardship of all relevant documented personal and sensitive data. Perform review at least annually.

### Cross-References

- **bsi_aic4**: DM-03
DM-04
PC-02
BC-05 (Gap: No Gap)
- **eu_ai_act**: Article 10 (2)
Article 11 (Gap: Partial Gap)
- **iso_42001**: 42001: 7.5.2 Creating and updating documented information
42001: A.4.3 Data resources
42001: A.2.3 Alignment with other organizational policies
27001 A.5.1
27001: A.5.9 - Inventory of information and other associated assets
27002: 5.9 - Inventory of information and other associated assets (Gap: Partial Gap)
- **nist_ai_600_1**: GV-1.6-003 (Gap: No Gap)

### CAIQ Questions

- **DSP-06.1**: Are ownership and stewardship of all relevant personal and sensitive data documented?
- **DSP-06.2**: Are reviews performed at least annually for the documented ownership and stewardship of all relevant personal and sensitive data?

---

## DSP-07: Data Protection by Design and Default

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Owned by the Customer (AIC)
- Model: Owned by the Customer (AIC)
- Orchestrated Services: Owned by the Customer (AIC)
- Application: Owned by the Customer (AIC)

**Lifecycle Relevance:**
- Preparation: Resource provisioning, Team and expertise
- Development: Design, Guardrails
- Evaluation/Validation: Evaluation, Validation/Red Teaming
- Deployment: Orchestration, AI Services supply chain
- Delivery: Operations, Maintenance, Continuous monitoring
- Service Retirement: Model disposal

### Specification

Develop systems, products, and business practices based upon a principle of security by design and industry best practices.

### Cross-References

- **bsi_aic4**: DEV-01
SR-06
PC-01 (Gap: No Gap)
- **eu_ai_act**: Article 10 (2) (a)
Article 14 (Gap: No Gap)
- **iso_42001**: 42001: A.2.3 Alignment with other organizational policies
42001: A.6.1.3 Processes for trustworthy AI system design and development
42001: A.6.2.2 AI system requirements and specification
42001: A.6.2.5 AI system deployment
42001: A.6.2.7 AI system technical documentation
42001: A.7.2 Data for development and enhancement of AI system
42001: A.7.5 Data provenance
27001: A.5.8 Information security in project management
27001: A.5.21 Managing information security in the information and communication (ICT) supply chain
27001: A.8.25  Secure development life cycle
27001: A.8.26 Application security requirements
27001: A.8.27 Secure system architecture and engineering principles
27001: A.8.28 Secure coding
27001: A.8.29 Security testing in development and acceptance
27001: A.8.30 Outsourced development
27001: A.8.31 Separation of development
test and production environment
27001: A.8.32 Change management
27001: A.8.33 Test information
27002: 5.8 Information security in project management
27002: 5.21 Managing information security in the information and communication (ICT) supply chain
27002: 8.25  Secure development life cycle
27002: 8.26 Application security requirements
27002: 8.27 Secure system architecture and engineering principles
27002: 8.28 Secure coding
27002: 8.29 Security testing in development and acceptance
27002: 8.30 Outsourced development
27002: 8.31 Separation of development
test and production environment
27002: 8.32 Change management
27002: 8.33 Test information (Gap: No Gap)
- **nist_ai_600_1**: GV-4.1-003
GV-5.1-001
MG-2.2-009
MP-2.3-002
MP-2.3-005
MS-1.3-003 (Gap: Partial Gap)

### CAIQ Questions

- **DSP-07.1**: Are systems, products, and business practices developed based upon a principle of security by design and industry best practices?

---

## DSP-08: Data Privacy by Design and Default

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Network, Compute, Storage, Application, Data
**Threat Categories:** Sensitive data disclosure, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Owned by the Customer (AIC)
- Model: Owned by the Customer (AIC)
- Orchestrated Services: Owned by the Customer (AIC)
- Application: Owned by the Customer (AIC)

**Lifecycle Relevance:**
- Preparation: Data collection, Resource provisioning
- Development: Design, Guardrails
- Evaluation/Validation: Evaluation
- Deployment: Orchestration, AI Services supply chain
- Delivery: Operations, Maintenance, Continuous monitoring
- Service Retirement: Data deletion, Model disposal

### Specification

Develop systems, products, and business practices based upon a principle of privacy by design and industry best practices. Ensure that systems' privacy settings are configured by default, according to all applicable laws and regulations.

### Cross-References

- **eu_ai_act**: Article 10
Article 52 (1) (Gap: Partial Gap)
- **iso_42001**: 42001: A.2.3 Alignment with other organizational policies
42001: A.5.4 Assessing AI system impact on individuals or groups of individuals
42001: A.6.1.3 Processes for trustworthy AI system design and development
42001: A.6.2.2 AI system requirements and specification
42001: A.6.2.5 AI system deployment
42001: A.6.2.7 AI system technical documentation
42001: A.7.2 Data for development and enhancement of AI system
42001: A.9.3 Objectives for responsible use of AI system
42001: A.7.3 Acquisition of data
27001: A.5.34 - Privacy and protection of personal identifiable information (PII)
27001: A.8.11 - Data masking
27002: 5.34 - Privacy and protection of personal identifiable information (PII)
27002: 8.11 - Data masking (Gap: No Gap)
- **nist_ai_600_1**: GV-1.1-001
MS-2.2-002
MS-2.2-003
MS-2.2-004 (Gap: Partial Gap)

### CAIQ Questions

- **DSP-08.1**: Are systems, products, and business practices developed based upon a principle of privacy by design and industry best practices?
- **DSP-08.2**: Are systems' privacy settings configured by default, according to all applicable laws and regulations?

---

## DSP-09: Data Protection Impact Assessment

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Network, Compute, Data
**Threat Categories:** Sensitive data disclosure, Insecure supply chain, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Owned by the Customer (AIC)
- Model: Owned by the Customer (AIC)
- Orchestrated Services: Owned by the Customer (AIC)
- Application: Owned by the Customer (AIC)

**Lifecycle Relevance:**
- Preparation: Data collection, Data curation, Team and expertise
- Development: Design, Guardrails
- Evaluation/Validation: Evaluation, Validation/Red Teaming
- Deployment: Orchestration, AI Services supply chain
- Delivery: Operations, Maintenance, Continuous monitoring
- Service Retirement: Data deletion, Archiving

### Specification

Conduct a Data Protection Impact Assessment (DPIA) to evaluate the origin, nature, particularity and severity of the risks upon the processing of personal data, according to any applicable laws, regulations and industry best practices.

### Cross-References

- **bsi_aic4**: BC-06 (Gap: No Gap)
- **eu_ai_act**: Article 9
Article 27 (Gap: No Gap)
- **iso_42001**: 42001: A.2.3 Alignment with other organizational policies
42001: A.5.2 AI system impact assessment process
42001: A.5.3 Documentation of AI system impact assessments
42001: A.5.4 Assessing AI system impact on individuals or groups of individuals
42001: A.7.5 Data Provenance
27001: 6.1.1 General - Planning
27001: 8.2 - Information security risk assessment
27001: 8.3 - Information security risk treatment
27001: A.5.34 - Privacy and protection of personal identifiable information (PII)
27002: 5.34 - Privacy and protection of personal identifiable information (PII) (Gap: No Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **DSP-09.1**: Are Data Protection Impact Assessments (DPIAs) conducted to evaluate the origin, nature, particularity, and severity of the risks upon the processing of personal data, according to any applicable laws, regulations, and industry best practices?

---

## DSP-10: Sensitive Data Transfer

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Network, Compute, Application, Data
**Threat Categories:** Sensitive data disclosure, Insecure supply chain, Insecure apps/plugins, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Owned by the Customer (AIC)
- Model: Owned by the Customer (AIC)
- Orchestrated Services: Owned by the Customer (AIC)
- Application: Owned by the Customer (AIC)

**Lifecycle Relevance:**
- Preparation: Resource provisioning, Team and expertise
- Development: Design, Guardrails
- Evaluation/Validation: Evaluation, Validation/Red Teaming
- Deployment: Orchestration, AI Services supply chain
- Delivery: Operations, Maintenance, Continuous monitoring
- Service Retirement: Data deletion, Archiving

### Specification

Define, implement and evaluate processes, procedures and technical measures that ensure any transfer of personal or sensitive data is protected from unauthorized access and only processed within scope as permitted by the respective laws and regulations.

### Cross-References

- **bsi_aic4**: COS-08 (Gap: No Gap)
- **eu_ai_act**: Article 10 (2) (e)
Article 23 (Gap: Partial Gap)
- **iso_42001**: 42001: A.2.2 AI Policy
42001: A.2.4. Review of AI Policy
42001: A.2.3 Alignment with other organizational policies
42001: A.7.3 Acquisition of data
27001: A.5.1 Policies for information security
27001: A.5.14 - Information transfer
27001: A.5.36 - Monitor Compliance
27001: A.5.37 Documented operating procedures
27001: A.7.10 - Storage media
27002: 5.1 Policies for information security
27002: 5.14 - Information transfer
27002: 5.37 Documented operating procedures
27002: 7.10 - Storage media (Gap: No Gap)
- **nist_ai_600_1**: MP-4.1-001
MP-4.1-009 (Gap: Partial Gap)

### CAIQ Questions

- **DSP-10.1**: Are processes, procedures, and technical measures defined, implemented, and evaluated that ensure any transfer of personal or sensitive data is protected from unauthorized access and only processed within scope as permitted by the respective laws and regulations?

---

## DSP-11: Personal Data Access, Reversal, Rectification and Deletion

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Storage, Application, Data
**Threat Categories:** Sensitive data disclosure, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Owned by the Customer (AIC)
- Model: Owned by the Customer (AIC)
- Orchestrated Services: Owned by the Customer (AIC)
- Application: Owned by the Customer (AIC)

**Lifecycle Relevance:**
- Preparation: Team and expertise, Data curation
- Development: Design, Guardrails
- Evaluation/Validation: Evaluation, Validation/Red Teaming
- Deployment: Orchestration, AI Services supply chain
- Delivery: Operations, Maintenance, Continuous monitoring
- Service Retirement: Data deletion

### Specification

Define and implement, processes, procedures and technical measures to enable data subjects to request access to, modification, or deletion of their personal data, according to any applicable laws and regulations.

### Cross-References

- **bsi_aic4**: COM-01
COM-04
IDM-01
AM-02 (Gap: Partial Gap)
- **eu_ai_act**: Article 10 (2)
Article 52 (2) (Gap: No Gap)
- **iso_42001**: 42001: A.2.3 Alignment with other organizational policies
42001: A.8.2 System documentation and information for users
27001: A.5.34 Privacy and protection of personal identifiable information (PII)
27002: 5.34 Privacy and protection of personal identifiable information (PII) (Gap: No Gap)
- **nist_ai_600_1**: GV-6.1-004
MS-2.2-003 (Gap: Partial Gap)

### CAIQ Questions

- **DSP-11.1**: Are processes, procedures, and technical measures defined and implemented to enable data subjects to request access to, modify, or delete their personal data according to applicable laws and regulations?

---

## DSP-12: Limitation of Purpose in Personal Data Processing

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Network, Compute, Storage, Application, Data
**Threat Categories:** Sensitive data disclosure, Insecure supply chain, Insecure apps/plugins, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Owned by the Customer (AIC)
- Model: Owned by the Customer (AIC)
- Orchestrated Services: Owned by the Customer (AIC)
- Application: Owned by the Customer (AIC)

**Lifecycle Relevance:**
- Preparation: Data collection, Resource provisioning
- Development: Design, Guardrails
- Evaluation/Validation: Evaluation, Validation/Red Teaming
- Deployment: Orchestration, AI Services supply chain
- Delivery: Operations, Maintenance, Continuous monitoring
- Service Retirement: Data deletion, Archiving

### Specification

Define, implement and evaluate processes, procedures and technical measures to ensure that personal data is processed according to any applicable laws and regulations and for the purposes declared to the data subject.

### Cross-References

- **bsi_aic4**: OPS-10
OPS-11 (Gap: Partial Gap)
- **eu_ai_act**: Article 10 (2)
Article 52 (Gap: No Gap)
- **iso_42001**: 42001: A.7.2 Data for development and enhancement of AI system
42001: A.7.4 Quality of data for AI systems
42001: A.2.3 Alignment with other organizational policies
27001: A.5.34 - Privacy and protection of personal identifiable information (PII)
27002: 5.34 - Privacy and protection of personal identifiable information (PII) (Gap: No Gap)
- **nist_ai_600_1**: GV-1.1-001
GV-6.1-004
MP-4.1-010 (Gap: No Gap)

### CAIQ Questions

- **DSP-12.1**: Are processes, procedures, and technical measures defined, implemented, and evaluated to ensure that personal data is processed according to applicable laws and regulations and for the purposes declared to the data subject?

---

## DSP-13: Personal Data Sub-processing

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Application, Data
**Threat Categories:** Sensitive data disclosure, Insecure supply chain, Insecure apps/plugins, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Owned by the Customer (AIC)
- Model: Owned by the Customer (AIC)
- Orchestrated Services: Owned by the Customer (AIC)
- Application: Owned by the Customer (AIC)

**Lifecycle Relevance:**
- Preparation: Resource provisioning, Team and expertise
- Development: Design, Guardrails
- Evaluation/Validation: Evaluation, Validation/Red Teaming
- Deployment: Orchestration, AI Services supply chain
- Delivery: Operations, Maintenance, Continuous monitoring
- Service Retirement: Data deletion

### Specification

Define, implement and evaluate processes, procedures and technical measures for the transfer and sub-processing of personal data within the service supply chain, according to any applicable laws and regulations.

### Cross-References

- **bsi_aic4**: SSO-01
SSO-02
BC-06 (Gap: Partial Gap)
- **eu_ai_act**: Article 10
Article 23
Article 24 (Gap: Partial Gap)
- **iso_42001**: 42001: A.10.2 Allocating responsibilities
42001: A.2.3 Alignment with other organizational policies
42001: 9.1 – Monitoring and measurement
42001: 10.2 – Corrective action for deviations in data supply chains
27001:  A.5.14 - Information transfer
27001: A.5.20 - Addressing information security within supplier agreement
27001: A.8.23 – Information masking
27001: A.5.10 – Acceptable use of information
27001: A.5.15 – Access control
27002: 5.14 - Information transfer
27002: 5.20 - Addressing information security within supplier agreement
27002: 9.4 – Access control enforcement
27002: 8.10 – Data handling policies (Gap: No Gap)
- **nist_ai_600_1**: GV-1.1-001
GV-6.1-004 (Gap: Partial Gap)

### CAIQ Questions

- **DSP-13.1**: Are processes, procedures, and technical measures defined, implemented, and evaluated for transferring and sub-processing personal data within the service supply chain according to applicable laws and regulations?

---

## DSP-14: Disclosure of Data Sub-processors

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Application, Data
**Threat Categories:** Sensitive data disclosure, Insecure supply chain, Insecure apps/plugins

**Ownership:**
- GenAI OPS/PI: Owned by the Customer (AIC)
- Model: Owned by the Customer (AIC)
- Orchestrated Services: Owned by the Customer (AIC)
- Application: Owned by the Customer (AIC)

**Lifecycle Relevance:**
- Preparation: Resource provisioning, Team and expertise
- Development: Design, Guardrails
- Evaluation/Validation: Evaluation, Validation/Red Teaming
- Deployment: Orchestration, AI Services supply chain
- Delivery: Operations, Maintenance, Continuous monitoring
- Service Retirement: Data deletion

### Specification

Define, implement and evaluate processes, procedures and technical measures to disclose the details of any personal or sensitive data access by sub-processors to the data owner prior to initiation of that processing.

### Cross-References

- **bsi_aic4**: SSO-01
SSO-02
BC-06 (Gap: Partial Gap)
- **eu_ai_act**: Article 23
Article 24
Article 25
Article 28 (Gap: Partial Gap)
- **iso_42001**: 42001: A.10.3 Suppliers
42001: A.2.3 Alignment with other organizational policies
27001: A.5.20 - Addressing information security within supplier agreement
27001: A.5.21 Managing information security in the information and communication technology (ICT) supply chain
27002: 5.20 - Addressing information security within supplier agreement
27002: 5.21 Managing information security in the information and communication technology (ICT) supply chain (Gap: No Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **DSP-14.1**: Are processes, procedures, and technical measures defined, implemented, and evaluated to disclose the details of any personal or sensitive data access by sub-processors to the data owner before initiating that processing?

---

## DSP-15: Limitation of Production Data Use

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Compute, Storage, Application, Data
**Threat Categories:** Sensitive data disclosure, Insecure supply chain, Insecure apps/plugins, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Owned by the Customer (AIC)
- Model: Owned by the Customer (AIC)
- Orchestrated Services: Owned by the Customer (AIC)
- Application: Owned by the Customer (AIC)

**Lifecycle Relevance:**
- Preparation: Team and expertise
- Development: Design, Guardrails
- Evaluation/Validation: Evaluation, Validation/Red Teaming
- Deployment: Orchestration, AI Services supply chain
- Delivery: Operations, Maintenance, Continuous monitoring
- Service Retirement: Data deletion, Archiving

### Specification

Obtain authorization from data owners, and manage associated risk before replicating or using production data in non-production environments.

### Cross-References

- **bsi_aic4**: BC-06 (Gap: Partial Gap)
- **eu_ai_act**: Article 10
Article 16
Article 17
Article 28
Article 29 (Gap: Partial Gap)
- **iso_42001**: 42001: A.6.1.2 Objectives for responsible development of AI system
42001: A.6.1.3 Processes for responsible design and development of AI systems
42001: 6.3.2 – AI control planning must consider environment sensitivity.
42001: A.7.2 Data for development and enhancement of AI system.
42001: A.7.4 Quality of data for AI systems
42001: A.2.3 Alignment with other organizational policies
27001: A.8.31 - Separation of development
test and production environments
27001: A.8.33 - Test information
27001:  A.8.27 – Segregation of environments.
27001:  A.5.11 – Protection against misuse of systems.
27002: 8.31 Separation of development
test and production environments
27002: 8.33 Test Information
27002: 8.28 – Environment segregation implementation.
27002: 5.9 – Protection against misuse or unintentional data disclosure. (Gap: No Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **DSP-15.1**: Are authorizations obtained from data owners and associated risks managed before replicating or using production data in non-production environments?

---

## DSP-16: Data Retention and Deletion

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Application, Data
**Threat Categories:** Sensitive data disclosure, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Owned by the Customer (AIC)
- Model: Owned by the Customer (AIC)
- Orchestrated Services: Owned by the Customer (AIC)
- Application: Owned by the Customer (AIC)

**Lifecycle Relevance:**
- Preparation: Data collection, Data storage
- Development: Design, Guardrails
- Evaluation/Validation: Evaluation, Validation/Red Teaming
- Deployment: Orchestration, AI Services supply chain
- Delivery: Operations, Maintenance, Continuous monitoring
- Service Retirement: Archiving, Data deletion

### Specification

Data retention, archiving and deletion is managed in accordance with business requirements, applicable laws and regulations.

### Cross-References

- **bsi_aic4**: COM-01
PI-03
OPS-09
OPS-10
OPS-12 (Gap: No Gap)
- **eu_ai_act**: Article 18
Article 19
Article 53 (Gap: Partial Gap)
- **iso_42001**: 42001: A.2.3 Alignment with other organizational policies
42001: A.4.3 Data resources
42001: A.5.3 Documentation of AI system impact assessments
42001: A.6.2.8 AI system recording of event logs
42001: A.7.4 Quality of data for AI systems
42001: A.9.4 Intended use of the AI system
42001: 7.5.3 Control of documented information
27001: A.5.33 - Protection of records
27001: A.8.10 - Information deletion
27002: 5.33 (b) - Protection of records (Gap: No Gap)
- **nist_ai_600_1**: GV-1.1-001
GV-1.7-002
MP-4.1-005 (Gap: Partial Gap)

### CAIQ Questions

- **DSP-16.1**: Are data retention, archiving, and deletion managed per business requirements, applicable laws, and regulations?

---

## DSP-17: Sensitive Data Protection

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Network, Compute, Storage, Application, Data
**Threat Categories:** Sensitive data disclosure, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Owned by the Customer (AIC)
- Model: Owned by the Customer (AIC)
- Orchestrated Services: Owned by the Customer (AIC)
- Application: Owned by the Customer (AIC)

**Lifecycle Relevance:**
- Preparation: Data collection, Data storage
- Development: Design, Guardrails
- Evaluation/Validation: Evaluation, Validation/Red Teaming
- Deployment: Orchestration, AI Services supply chain
- Delivery: Operations, Maintenance, Continuous monitoring
- Service Retirement: Data deletion, Archiving

### Specification

Define and implement, processes, procedures and technical measures to protect sensitive data throughout its lifecycle.

### Cross-References

- **bsi_aic4**: AM-02
AM-05
AM-06
CRY-02
CRY-03
OPS-12
OPS-14
PI-03
PSS-09
PSS-12 (Gap: No Gap)
- **eu_ai_act**: Article 10 (2)
Article 15 (Gap: Partial Gap)
- **iso_42001**: 42001: A.4.3 Data Resources
42001: A.5.4 Assessing AI system impact on individuals or groups of individuals
42001: A.5.5 Assessing Societal Impacts of AI Systems
42001: A.7.2 Data for development and enhancement of AI system
42001: B.7.3 Acquisition of data
42001: A.7.4 Quality of Data for AI Systems
42001: A.7.5 Data Provenance
42001: A.2.3 Alignment with other organizational policies
27001: A.5.12 Classification of information
27001: A.5.13 Labelling of information
27001: A.5.14 Information transfer
27001: A.5.15 Access control
27001: A.5.16 Identity management
27001: A.5.17 Authentication information
27001: A.5.18 Access rights
27001: A.7.7 Clear desk and clear screen
27001: A.7.10 Storage Media
27001: A.8.11 Data masking
27001: A.8.12 Data leakage prevention
27002: 5.12 Classification of information
27002: 5.13 Labelling of information
27002: 5.14 Information transfer
27002: 5.15 Access control
27002: 5.16 Identity management
27002: 5.17 Authentication information
27002: 5.18 Access rights
27002: 7.7 Clear desk and clear screen
27002: 7.10 Storage Media
27002: 8.3 Information Access Restrictions
27002: 8.11 Data masking
27002: 8.12 Data leakage prevention (Gap: No Gap)
- **nist_ai_600_1**: MP-4.1-001
MP-4.1-009 (Gap: Partial Gap)

### CAIQ Questions

- **DSP-17.1**: Are processes, procedures, and technical measures defined and implemented to protect sensitive data throughout its lifecycle?

---

## DSP-18: Disclosure Notification

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Application, Data
**Threat Categories:** Sensitive data disclosure, Insecure supply chain, Insecure apps/plugins, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Owned by the Cloud Service Provider (CSP)
- Model: Owned by the Cloud Service Provider (CSP)
- Orchestrated Services: Owned by the Cloud Service Provider (CSP)
- Application: Owned by the Cloud Service Provider (CSP)

**Lifecycle Relevance:**
- Preparation: Team and expertise
- Development: Design, Guardrails
- Evaluation/Validation: Evaluation, Validation/Red Teaming
- Deployment: Orchestration, AI Services supply chain
- Delivery: Operations, Maintenance, Continuous monitoring
- Service Retirement: Data deletion, Archiving

### Specification

The providers should implement and describe to customers the procedure to manage and respond to requests for disclosure of Personal Data by Law Enforcement Authorities according to applicable laws and regulations.

### Cross-References

- **bsi_aic4**: INQ-01
INQ-02
INQ-03
INQ-04
BC-06 (Gap: No Gap)
- **eu_ai_act**: Article 21
Article 64 (Gap: Partial Gap)
- **iso_42001**: 42001: A.2.3 Alignment with other organizational policies
42001: A.8.4 Communication of incidents
42001: A.8.5 Information for interested parties
27001: A.5.34 - Privacy and protection of personal identifiable information (PII)
27002: 5.34 - Privacy and protection of personal identifiable information (PII) (Gap: No Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **DSP-18.1**: Are the procedures to manage and respond to requests for disclosure of Personal Data by Law Enforcement Authorities according to applicable laws and regulations, implemented and described to the customers by the providers?

---

## DSP-19: Data Location

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Storage, Data
**Threat Categories:** Sensitive data disclosure, Model/Service Failure, Insecure supply chain, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Owned by the Customer (AIC)
- Model: Owned by the Customer (AIC)
- Orchestrated Services: Owned by the Customer (AIC)
- Application: Owned by the Customer (AIC)

**Lifecycle Relevance:**
- Preparation: Data collection, Data storage, Resource provisioning
- Development: Design, Guardrails
- Evaluation/Validation: Evaluation, Validation/Red Teaming
- Deployment: Orchestration, AI Services supply chain
- Delivery: Operations, Maintenance, Continuous monitoring
- Service Retirement: Data deletion, Archiving

### Specification

Define and implement, processes, procedures and technical measures to specify and document the physical locations of data, including any locations in which data is processed or backed up.

### Cross-References

- **bsi_aic4**: PSS-12 (Gap: No Gap)
- **eu_ai_act**: Article 11 (1)
Article 10 (2) (Gap: Partial Gap)
- **iso_42001**: 42001: A.4.2 Resource Documentation
42001: A.4.5 System and Computing Resources
42001: A.7.5 Data provenance
42001: A.2.3 Alignment with other organizational policies
27001: A.5.9 - Inventory of information and other associated assets
27001: A.8.12 - Data leakage prevention
27001: A.8.13 - Information backup
27002: 5.9 - Inventory of information and other associated assets
27002: 8.12 - Data leakage prevention
27002: 8.13 - Information backup (Gap: No Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **DSP-19.1**: Are processes, procedures, and technical measures defined and implemented to specify and document the physical locations of data, including any locations where data is processed or backed up?

---

## DSP-20: Data Provenance and Transparency

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Network, Compute, Storage, Application, Data
**Threat Categories:** Data poisoning, Sensitive data disclosure, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared across the supply chain
- Model: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Shared Application Provider-AI Customer (Shared AP-AIC)

**Lifecycle Relevance:**
- Preparation: Data collection, Data curation, Data storage
- Development: Design
- Evaluation/Validation: Validation/Red Teaming
- Deployment: Orchestration
- Delivery: Operations, Continuous improvement
- Service Retirement: Archiving, Data deletion

### Specification

Define, implement and evaluate processes, procedures and technical measures to:  1) Document and trace data sources, and 2) Make the data source available according to legal and regulatory requirements

### Cross-References

- **bsi_aic4**: BC-05
DM-03
DQ-02 (Gap: No Gap)
- **eu_ai_act**: Article 10 (2)
Article 11 (1) (Gap: No Gap)
- **iso_42001**: 42001: A.2.3 Alignment with other organizational policies
42001: A.4.3 Data Resources
42001: A.5.4 Assessing AI system impact on individuals or groups of individuals
42001: A.7.5 Data Provenance
42001: A.8.2 System documentation and information for users
42001: A.9.3 Objectives for responsible use of AI system
27001: A.5.9 Inventory of Information and Other Associated Assets
27001: A.5.12 Classification of Information
27001: A.5.13 Labelling of Information
27001: A.5.14 Information Transfer
27001: A.5.19 Information Security in Supplier Relationships
27001: A.5.28 Collection of Evidence
27001: A.5.15 Access Control
27001: A.8.11 Data masking
27001: A.8.12 Data leakage prevention
27001: A.8.15 Logging
27001: A.8.16 Monitoring Activities
27002: 5.9 Inventory of Information and Other Associated Assets
27002: 5.12 Classification of Information
27002: 5.13 Labelling of Information
27002: 5.14 Information Transfer
27002: 5.19 Information Security in Supplier Relationships
27002: 5.28 Collection of Evidence
27002: 5.15 Access Control
27002: 8.11 Data masking
27002: 8.12 Data leakage prevention
27002: 8.15 Logging
27002: 8.16 Monitoring Activities (Gap: No Gap)
- **nist_ai_600_1**: GV-1.1-001
GV-1.6-003
MP-2.2-001
MG-2.2-002
MG-3.2-003 (Gap: Partial Gap)

### CAIQ Questions

- **DSP-20.1**: Are processes, procedures, and technical measures defined, implemented, and evaluated to: 
1) Document and trace data sources, and 2) Make the data source available according to legal and regulatory requirements

---

## DSP-21: Data Poisoning Prevention & Detection

**Type:** control
**Control Type:** AI-Specific
**Architectural Relevance:** Network, Compute, Storage, Application, Data
**Threat Categories:** Data poisoning, Model/Service Failure, Insecure supply chain, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared across the supply chain
- Model: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Shared Application Provider-AI Customer (Shared AP-AIC)

**Lifecycle Relevance:**
- Preparation: Data collection, Data curation
- Development: Training, Supply Chain
- Evaluation/Validation: Validation/Red Teaming, Re-evaluation
- Deployment: AI Services supply chain
- Delivery: Continuous improvement
- Service Retirement: N/A

### Specification

Define, implement and evaluate processes, procedures and technical measures to prevent data poisoning in AI models and continuously detect such.

### Cross-References

- **bsi_aic4**: PF-01
PF-02
DQ-03
SR-06 (Gap: No Gap)
- **eu_ai_act**: Article 9
Article 10 (2)
Article 15 (Gap: No Gap)
- **iso_42001**: 42001: A.6.1.2 Objectives for responsible development of AI system
42001: A.6.2.3 Documentation of AI system design and development
42001: A.6.2.6 AI system operation and monitoring
42001: A.6.2.4 AI system verification and validation
42001: A.7.3 Acquisition of data
42001: A.7.4 Quality of data for AI system (Gap: No Gap)
- **nist_ai_600_1**: MP-2.3-001
MP-2.3-003
MG-3.2-006 (Gap: Partial Gap)

### CAIQ Questions

- **DSP-21.1**: Are processes, procedures and technical measures to prevent data poisoning in AI models and continuously detect such, defined, implemented and evaluated?

---

## DSP-22: Privacy Enhancing Technologies

**Type:** control
**Control Type:** AI-Specific
**Architectural Relevance:** Network, Compute, Storage, Application, Data
**Threat Categories:** Sensitive data disclosure, Insecure supply chain, Insecure apps/plugins, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared across the supply chain
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Shared Application Provider-AI Customer (Shared AP-AIC)

**Lifecycle Relevance:**
- Preparation: Data collection, Data storage
- Development: Design, Training
- Evaluation/Validation: Validation/Red Teaming
- Deployment: AI Services supply chain, AI applications
- Delivery: Operations, Continuous improvement
- Service Retirement: N/A

### Specification

Use Privacy Enhancing Technologies for training data, informed by risk and privacy impact analysis and business use cases.

### Cross-References

- **bsi_aic4**: SR-06 (Gap: No Gap)
- **eu_ai_act**: Article 10 (2) (f)
Article 15 (Gap: Partial Gap)
- **iso_42001**: 42001: 4.1 Understanding the organization and its context
42001: 6.1.4  AI System Impact Assessment
42001: A.4.2 Resource documentation
42001: A.4.4 Tooling resources
42001: A.2.3 Alignment with other organizational policies
27001: A.5.15 - Access Control
27001: A.5.34 -Privacy and protection of personal identifiable information (PII)
27001: A.8.5 - Secure Authentication
27001: A.8.11 - Data masking
27001: A.8.12 - Data leakage prevention
27001: A.8.20 - Networks security
27001: A.8.24 - Use of cryptography
27002: 5.15 - Access Control
27002: 5.34 -Privacy and protection of personal identifiable information (PII)
27002: 8.5 - Secure Authentication
27002: 8.11 - Data masking
27002: 8.12 - Data leakage prevention
27002: 8.20 - Networks security
27002: 8.24 - Use of cryptography (Gap: No Gap)
- **nist_ai_600_1**: MS-2.2-004 (Gap: Partial Gap)

### CAIQ Questions

- **DSP-22.1**: Are Privacy Enhancing Technologies (PET) used for training data informed by risk and privacy impact analysis and business use cases?

---

## DSP-23: Data Integrity Check

**Type:** control
**Control Type:** AI-Specific
**Architectural Relevance:** Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Model/Service Failure, Insecure supply chain, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Owned by the Customer (AIC)
- Model: Owned by the Customer (AIC)
- Orchestrated Services: Owned by the Customer (AIC)
- Application: Owned by the Customer (AIC)

**Lifecycle Relevance:**
- Preparation: Data curation, Data storage
- Development: Training, Guardrails
- Evaluation/Validation: Validation/Red Teaming
- Deployment: Orchestration, AI Services supply chain
- Delivery: Operations, Continuous monitoring
- Service Retirement: Data deletion, Archiving

### Specification

Regularly validate the consistency and conformity of training, fine-tuning or augmentation data. Implement dataset versioning to ensure traceability and enforce restrictions to prevent unauthorized changes.

### Cross-References

- **bsi_aic4**: DQ-03 (Gap: No Gap)
- **eu_ai_act**: Article 10 (2)
Article 11 (1)
Article 15
Recital 67 (Gap: No Gap)
- **iso_42001**: 42001: A.5.2 AI system impact assessment process
42001: A.6.1.3 Processes for responsible design and development of AI systems
42001: 6.3 Planning of changes
42001: A.7.2 Data for development and enhancement of AI system
42001: A.7.3 Acquisition of data
42001: 7.5.3 Control of documented information (Gap: No Gap)
- **nist_ai_600_1**: GV-6.1-008
MS-2.5-005
MS-2.8-003
MG-4.1-006 (Gap: No Gap)

### CAIQ Questions

- **DSP-23.1**: Is the consistency and conformity of training, fine-tuning or augmentation data regularly validated?
- **DSP-23.2**: Is dataset versioning to ensure traceability implemented and are restrictions to prevent unauthorized changes, enforced?

---

## DSP-24: Data Differentiation
and Relevance

**Type:** control
**Control Type:** AI-Specific
**Architectural Relevance:** Compute, Storage, Application, Data
**Threat Categories:** Data poisoning, Model/Service Failure, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Owned by the Customer (AIC)
- Model: Owned by the Customer (AIC)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Owned by the Customer (AIC)

**Lifecycle Relevance:**
- Preparation: Data collection, Data storage, Data curation
- Development: Design, Training, Guardrails
- Evaluation/Validation: Evaluation, Validation/Red Teaming, Re-evaluation
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Continuous monitoring, Continuous improvement
- Service Retirement: Data deletion, Archiving

### Specification

Ensure training-data differentiation and relevance to the intended use of the AI Model.

### Cross-References

- **bsi_aic4**: DQ-01
DQ-02
DQ-03 (Gap: No Gap)
- **eu_ai_act**: Article 10 (2)
Article 10 (3)
Article 15 (Gap: No Gap)
- **iso_42001**: 42001: A.4.3 Data Resource
42001: A.5.5 Assessing societal impacts of AI systems
42001: A.6.1.3 Processes for responsible design and development of AI systems
42001: A.7.2 Data for development and enhancement of AI system
42001: A.7.3 Acquisition of data
42001: A.7.4 Quality of data for AI systems (Gap: No Gap)
- **nist_ai_600_1**: GV-1.1-001
MG-2.2-004
MP-4.1-004
MS-1.1-007
MS-2.2-001
MS-2.5-005
MS-2.10-003
MS-2.11-005 (Gap: No Gap)

### CAIQ Questions

- **DSP-24.1**: Is training-data differentiation and relevance to the intended use of the AI Model, ensured?

---

# Domain: Governance, Risk and Compliance

## GRC-01: Governance Program Policy and Procedures

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Storage, Application, Data
**Threat Categories:** Sensitive data disclosure, Insecure supply chain, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Owned by the Orchestrated Service Provider (OSP)
- Application: Owned by the Customer (AIC)

**Lifecycle Relevance:**
- Preparation: Team and expertise
- Development: Guardrails
- Evaluation/Validation: Evaluation, Validation/Red Teaming
- Deployment: Orchestration, AI Services supply chain
- Delivery: Operations, Continuous monitoring, Continuous improvement
- Service Retirement: Archiving, Data deletion

### Specification

Establish, document, approve, communicate, apply, evaluate and maintain policies and procedures for an information governance program, which is sponsored by the leadership of the organization and related to AI systems as well. Review and update the policies and procedures at least annually.

### Cross-References

- **bsi_aic4**: SP-01
SP-02 (Gap: No Gap)
- **eu_ai_act**: Article 9 (Risk Management System)
Article 16 (Obligations of Providers)
Article 17 (Quality Management System)
Article 19 (QMS Documentation) (Gap: Partial Gap)
- **iso_42001**: 42001: B.2.2 (AI policy)
42001; B.2.4 (Review of the AI policy)
42001: A.2.2 (AI policy)
42001: A.2.4 (Review of the AI policy)
42001: 5.2 (Assessing impacts of AI systems) (Gap: No Gap)
- **nist_ai_600_1**: GV-1.1-001
GV-4.1-001
GV-4.1-002
GV-4.1-003 (Gap: No Gap)

### CAIQ Questions

- **GRC-01.1**: Are policies and procedures established, documented, approved, communicated, applied, evaluated, and maintained for an information governance program that is sponsored by the leadership of the organization and related to AI systems as well?
- **GRC-01.2**: Are policies and procedures for information governance program and related to AI systems reviewed and updated at least annually?

---

## GRC-02: Risk Management Program

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Sensitive data disclosure, Insecure supply chain, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Owned by the Orchestrated Service Provider (OSP)
- Application: Owned by the Customer (AIC)

**Lifecycle Relevance:**
- Preparation: Team and expertise
- Development: Guardrails
- Evaluation/Validation: Validation/Red Teaming, Evaluation
- Deployment: Orchestration, AI Services supply chain
- Delivery: Continuous monitoring, Continuous improvement, Operations, Maintenance
- Service Retirement: Data deletion

### Specification

Establish and maintain a formal, documented, and leadership-sponsored  AI Risk Management (AIRM) program that includes policies and  procedures for identification, evaluation, ownership, treatment, and  acceptance of risks.

### Cross-References

- **bsi_aic4**: C4 PC-02
C5 OIS-01
OIS-06
OIS-07
SSO-02
BCM-02 (Gap: Partial Gap)
- **eu_ai_act**: Article 9
Article 15 (4)
Article 15 (5)
Article 16 (c)
Article 17 (1[g])
Article 17(1[m])
Article 27 (1)
Article 27 (3) (Gap: Partial Gap)
- **iso_42001**: 42001 6.1.1 (planning for the AI management system)
42001 6.1.2 (AI risk assessment)
42001 6.1.3 (AI risk treatment)
42001 6.1.4 (AI system impact assessment)
42001 8.2 (AI risk assessment)
42001 8.3 (AI risk treatment)
42001 8.4 (AI system impact assessment)
42001: B.5.2 (AI system impact assessment process)
42001 A.5.3 (Documentation of AI system impact assessments)
42001 A.5.4 (Assessing AI system impact on individuals or groups of individuals)
42001 B.5.3 (Documentation of AI system impact assessments)
42001 B.5.4 (Assessing AI system impact on individuals or groups of individuals) (Gap: No Gap)
- **nist_ai_600_1**: GV-1.3-001
GV-1.3-002
MG-3.2-009 (Gap: Partial Gap)

### CAIQ Questions

- **GRC-02.1**: Is a formal, documented, and leadership-sponsored AI risk management (AIRM) program that includes policies and procedures for identification, evaluation, ownership, treatment, and acceptance of risks, established and maintained?

---

## GRC-03: Organizational Policy Reviews

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Network, Compute, Storage, Application, Data
**Threat Categories:** Sensitive data disclosure, Insecure supply chain, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Owned by the Orchestrated Service Provider (OSP)
- Application: Owned by the Customer (AIC)

**Lifecycle Relevance:**
- Preparation: Team and expertise
- Development: Guardrails
- Evaluation/Validation: Evaluation
- Deployment: Orchestration, AI Services supply chain
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Archiving, Data deletion

### Specification

Review all relevant organizational policies and associated procedures at least annually or when a substantial change occurs within the organization.

### Cross-References

- **bsi_aic4**: SP-02 (Gap: No Gap)
- **eu_ai_act**: Article 17
Article 53 (Gap: No Gap)
- **iso_42001**: 42001: A.2.4 (Review of the AI policy)
42001: B.2.4  (Review of the AI policy)
42001: 7.5.2 (Creating and updating documented information) (Gap: No Gap)
- **nist_ai_600_1**: GV-4.1-002
MG-2.3-001 (Gap: No Gap)

### CAIQ Questions

- **GRC-03.1**: Are relevant organizational policies and associated procedures reviewed at least annually or when a substantial change within the organization, occurs?

---

## GRC-04: Policy Exception Process

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Network, Compute, Storage, Application, Data
**Threat Categories:** Sensitive data disclosure, Insecure supply chain, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Owned by the Orchestrated Service Provider (OSP)
- Application: Owned by the Customer (AIC)

**Lifecycle Relevance:**
- Preparation: Team and expertise
- Development: Guardrails
- Evaluation/Validation: Evaluation
- Deployment: Orchestration, AI Services supply chain
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Archiving, Data deletion

### Specification

Establish and follow an approved exception process as mandated by the governance program whenever a deviation from an established policy occurs.

### Cross-References

- **bsi_aic4**: SP-03 (Gap: No Gap)
- **eu_ai_act**: Article 9
Article 17 (4)
Article 25
Article 28 (Gap: Partial Gap)
- **iso_42001**: 42001: A.2.3 (Alignment with other organizational policies)
42001: B.2.3 (Alignment with other organizational policies) (Gap: No Gap)
- **nist_ai_600_1**: GV-1.3-007
GV-4.1-003 (Gap: No Gap)

### CAIQ Questions

- **GRC-04.1**: Is an approved exception process mandated by the governance program established
and followed whenever a deviation from an established policy occurs?

---

## GRC-05: Information Security Program

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Network, Compute, Storage, Application, Data
**Threat Categories:** Sensitive data disclosure, Insecure supply chain, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Owned by the Orchestrated Service Provider (OSP)
- Application: Owned by the Customer (AIC)

**Lifecycle Relevance:**
- Preparation: Team and expertise
- Development: Guardrails, Design
- Evaluation/Validation: Evaluation, Validation/Red Teaming
- Deployment: Orchestration, AI Services supply chain
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Archiving, Data deletion

### Specification

Develop and implement an Information Security Program, which includes programs for all the relevant domains of the AICM.

### Cross-References

- **bsi_aic4**: C4 PC-02
C5 OIS-01 (Gap: Partial Gap)
- **eu_ai_act**: Article 15 (Gap: Partial Gap)
- **iso_42001**: 42001: B.6.1.2 (Objectives for responsible development of AI system)
42001: B.9.3 (Objectives for responsible use of AI system)
42001: D.2 (Integration of AI management system with other management system standards)
42001: C.2.10 (Security)
42001: B.8.4 (Communication of incidents) (Gap: No Gap)
- **nist_ai_600_1**: GV-1.1-001
GV-1.2-001
GV-3.1-001
GV-5.1-001
GV-6.1-004 (Gap: Partial Gap)

### CAIQ Questions

- **GRC-05.1**: Is an Information Security Program that includes programs for all the relevant domains of the AICM developed and implemented?

---

## GRC-06: Governance Responsibility Model

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Application, Data
**Threat Categories:** Sensitive data disclosure, Insecure supply chain, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Owned by the Orchestrated Service Provider (OSP)
- Application: Owned by the Customer (AIC)

**Lifecycle Relevance:**
- Preparation: Team and expertise
- Development: Guardrails
- Evaluation/Validation: Validation/Red Teaming, Evaluation
- Deployment: Orchestration, AI Services supply chain
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Archiving, Data deletion

### Specification

Define and document roles and responsibilities for planning, implementing, operating, assessing, and improving governance programs.

### Cross-References

- **bsi_aic4**: OIS-01
OIS-02
COM-01
COM-02
COM-03
COM-04 (Gap: No Gap)
- **eu_ai_act**: Article 16
Article 23
Article 24
Article 25
Article 26
Article 27
Article 28
Article 29 (Gap: No Gap)
- **iso_42001**: 42001: B.3.2 (AI roles and responsibilities)
42001: A.3.2 (AI roles and responsibilities) (Gap: No Gap)
- **nist_ai_600_1**: GV-2.1-001
GV-2.1-002 (Gap: Partial Gap)

### CAIQ Questions

- **GRC-06.1**: Are roles and responsibilities defined and documented for planning, implementing, operating, assessing, and improving governance programs?

---

## GRC-07: Information System Regulatory Mapping

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Sensitive data disclosure, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Owned by the Orchestrated Service Provider (OSP)
- Application: Owned by the Customer (AIC)

**Lifecycle Relevance:**
- Preparation: Team and expertise
- Development: Guardrails
- Evaluation/Validation: Evaluation, Validation/Red Teaming
- Deployment: Orchestration, AI Services supply chain
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Archiving, Data deletion

### Specification

Identify and document all relevant standards, regulations,  legal/contractual, and statutory requirements, which are applicable to  your organization.  Review at least annually or when a substantial change occurs within  the organization.

### Cross-References

- **bsi_aic4**: COM-01 (Gap: No Gap)
- **eu_ai_act**: Article 11
Annex IV
Article 16 (Gap: Partial Gap)
- **iso_42001**: 42001: 4.1 Note 2 (Understanding the organization and its context)
42001: B.6.2.6 (AI system operation and monitoring)
42001: B.7.3 (Acquisition of data)
42001: B.8.5 (Information for interested parties)
42001: B.9.2 (Processes for responsible use of AI systems)
27001: A.5.31 (Legal
statutory
regulatory and contractual requirements) (Gap: No Gap)
- **nist_ai_600_1**: MP-4.1-003 (Gap: No Gap)

### CAIQ Questions

- **GRC-07.1**: Are all relevant standards, regulations, legal/contractual, and statutory
requirements, applicable to your organization, identified and documented?
- **GRC-07.2**: Are all relevant standards,regulations, legal/contractual and statutory requirements reviewed and updated at least annually or when a substantial change occurs within the organization?

---

## GRC-08: Special Interest Groups

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Application, Data

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Owned by the Orchestrated Service Provider (OSP)
- Application: Owned by the Customer (AIC)

**Lifecycle Relevance:**
- Preparation: Team and expertise
- Development: Design, Guardrails
- Evaluation/Validation: Evaluation, Validation/Red Teaming
- Deployment: Orchestration, AI Services supply chain
- Delivery: Continuous monitoring, Maintenance
- Service Retirement: Data deletion, Archiving

### Specification

Establish and maintain contact with related special interest groups and  other relevant entities in line with business context.

### Cross-References

- **bsi_aic4**: OIS-05 (Gap: No Gap)
- **eu_ai_act**: Article 72 (Gap: Partial Gap)
- **iso_42001**: 42001: B.4.6 (Human resources)
27001: A.5.6 (Contact with special interest groups) (Gap: No Gap)
- **nist_ai_600_1**: GV-6.1-001
GV-6.1-002
MP-5.2-002 (Gap: No Gap)

### CAIQ Questions

- **GRC-08.01**: Is contact established and maintained with related special interest groups and other relevant entities in line with business context?

---

## GRC-09: Acceptable Use of the AI Service

**Type:** control
**Control Type:** AI-Specific
**Architectural Relevance:** Application, Data
**Threat Categories:** Sensitive data disclosure, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service

**Ownership:**
- GenAI OPS/PI: Owned by the Customer (AIC)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Owned by the Orchestrated Service Provider (OSP)
- Application: Owned by the Customer (AIC)

**Lifecycle Relevance:**
- Preparation: Resource provisioning, Data collection
- Development: Design, Guardrails
- Evaluation/Validation: Re-evaluation, Validation/Red Teaming
- Deployment: Orchestration, AI Services supply chain
- Delivery: Continuous improvement, Continuous monitoring, Operations, Maintenance
- Service Retirement: Data deletion, Archiving

### Specification

Define, document and enforce policies and procedures on the acceptable use of AI services offered by the organization. Ensure effectiveness by continuous risk assessments, reviews and human oversight.

### Cross-References

- **bsi_aic4**: PF-10
SR-01 (Gap: No Gap)
- **eu_ai_act**: Article 29
Article 52 (Gap: Partial Gap)
- **iso_42001**: 42001: A.9.2 (Processes for responsible use of AI systems)
42001: A.9.3 (Objectives for responsible use of AI system)
42001: A.9.4 (Intended use of the AI system)
42001: B.9.4 (Intended use of the AI system)
42001: B.6.2.6 (AI system operation and monitoring) (Gap: No Gap)
- **nist_ai_600_1**: GV-3.2-003
GV-4.1-001 (Gap: No Gap)

### CAIQ Questions

- **GRC-09.1**: Are policies and procedures defined, documented, and enforced for the acceptable use of AI services offered by the organization?
- **GRC-09.2**: Is effectiveness of the acceptable use of AI services policies and procedures evaluated by continuous risk assessments, reviews, and human oversight?

---

## GRC-10: AI Impact Assessment

**Type:** control
**Control Type:** AI-Specific
**Architectural Relevance:** Application, Data
**Threat Categories:** Sensitive data disclosure, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Owned by the Customer (AIC)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Owned by the Orchestrated Service Provider (OSP)
- Application: Owned by the Customer (AIC)

**Lifecycle Relevance:**
- Preparation: Team and expertise
- Development: Guardrails
- Evaluation/Validation: Evaluation, Validation/Red Teaming
- Deployment: Orchestration, AI Services supply chain
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Archiving, Data deletion, Model disposal

### Specification

Establish, document, and communicate to all relevant stakeholders an AI Impact Assessment process and its criteria to regularly evaluate the ethical, societal, operational, legal, and security impacts of the AI system throughout its lifecycle.

### Cross-References

- **bsi_aic4**: BC-03
PF-01
PF-02
PF-05 (Gap: No Gap)
- **eu_ai_act**: Article 9
Article 27
Article 55 (Gap: No Gap)
- **iso_42001**: 42001: B.5.2 (AI system impact assessment process)
42001: B.5.4 (Assessing AI system impact on individuals or groups of individuals) (Gap: No Gap)
- **nist_ai_600_1**: MP-5.1-002
MP-5.1-004
MS-1.3-002
MS-3.3-001 (Gap: No Gap)

### CAIQ Questions

- **GRC-10.1**: Is an AI Impact Assessment process  and its criteria to regularly evaluate the ethical, societal, operational, legal, and security impacts of the AI system throughout its lifecycle, established, documented, and communicated to all relevant stakeholders?

---

## GRC-11: Bias and Fairness Assessment

**Type:** control
**Control Type:** AI-Specific
**Architectural Relevance:** Application, Data
**Threat Categories:** Sensitive data disclosure, Insecure supply chain, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Owned by the Customer (AIC)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Owned by the Orchestrated Service Provider (OSP)
- Application: Owned by the Customer (AIC)

**Lifecycle Relevance:**
- Preparation: Team and expertise
- Development: Guardrails
- Evaluation/Validation: Evaluation, Validation/Red Teaming, Re-evaluation
- Deployment: AI applications, Orchestration
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Data deletion, Archiving

### Specification

Regularly evaluate AI systems, models, datasets & algorithms for bias and fairness to ensure compliance with ethical standards.

### Cross-References

- **bsi_aic4**: BI-01
DQ-03 (Gap: Partial Gap)
- **eu_ai_act**: Article 10 (2) (f) (Gap: No Gap)
- **iso_42001**: 42001: B.5.4 (Assessing AI system impact on individuals or groups of individuals) (Gap: No Gap)
- **nist_ai_600_1**: MG-3.2-004
GV-1.2-002
MS-2.11-002
MS-2.11-004
MS-2.6-002
MS-3.3-003 (Gap: No Gap)

### CAIQ Questions

- **GRC-11.1**: Are AI systems, models, datasets & algorithms regularly evaluated for bias and fairness to ensure compliance with ethical standards?

---

## GRC-12: Ethics Committee

**Type:** control
**Control Type:** AI-Specific
**Architectural Relevance:** Application, Data
**Threat Categories:** Sensitive data disclosure, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Owned by the Customer (AIC)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Owned by the Orchestrated Service Provider (OSP)
- Application: Owned by the Customer (AIC)

**Lifecycle Relevance:**
- Preparation: Team and expertise
- Development: Guardrails
- Evaluation/Validation: Evaluation, Validation/Red Teaming
- Deployment: Orchestration, AI Services supply chain
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Archiving, Data deletion, Model disposal

### Specification

Establish an ethics committee to review AI applications, ensuring alignment with ethical standards and organizational values.

### Cross-References

- **bsi_aic4**: BI-01
BI-02 (Gap: Partial Gap)
- **eu_ai_act**: Article 14
Article 47
Article 63 (Gap: Partial Gap)
- **iso_42001**: 42001: B.6.1.2 (Objectives for responsible development of AI system) (Gap: Partial Gap)
- **nist_ai_600_1**: GV-2.1-002
MP-3.4-006 (Gap: Partial Gap)

### CAIQ Questions

- **GRC-12.1**: Is an ethics committee established to review AI applications, ensuring alignment with ethical standards and organizational values?

---

## GRC-13: Explainability Requirement

**Type:** control
**Control Type:** AI-Specific
**Architectural Relevance:** Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Owned by the Cloud Service Provider (CSP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Owned by the Orchestrated Service Provider (OSP)
- Application: Owned by the Customer (AIC)

**Lifecycle Relevance:**
- Preparation: Data collection, Data curation, Data storage, Team and expertise
- Development: Design, Training, Guardrails, Supply Chain
- Evaluation/Validation: Evaluation, Validation/Red Teaming, Re-evaluation
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Archiving, Data deletion, Model disposal

### Specification

Establish, document, and communicate the degree of explainability needed for the AI Services.

### Cross-References

- **bsi_aic4**: EX-01 (Gap: No Gap)
- **eu_ai_act**: Article 13
Article 52 (Gap: Partial Gap)
- **iso_42001**: 42001: B.8.2 (System documentation and information for users)
42001 B.9.3 (Objectives for responsible use of AI system) (Gap: No Gap)
- **nist_ai_600_1**: MP-2.3-003
MS-4.2-003 (Gap: No Gap)

### CAIQ Questions

- **GRC-13.1**: Is the degree of explainability required for the AI Services established, documented, and communicated?

---

## GRC-14: Explainability Evaluation

**Type:** control
**Control Type:** AI-Specific
**Architectural Relevance:** Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Owned by the Orchestrated Service Provider (OSP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Shared Application Provider-AI Customer (Shared AP-AIC)

**Lifecycle Relevance:**
- Preparation: Data collection, Data curation, Data storage, Team and expertise
- Development: Design, Training, Guardrails, Supply Chain
- Evaluation/Validation: Evaluation, Validation/Red Teaming, Re-evaluation
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Archiving, Data deletion, Model disposal

### Specification

Evaluate, document, and communicate the degree of explainability of the AI Services, including possible limitations and exceptions.

### Cross-References

- **bsi_aic4**: EX-01 (Gap: No Gap)
- **eu_ai_act**: Article 11 (1)
Article 13
Article 52 (Gap: Partial Gap)
- **iso_42001**: 42001: B.8.3 (External reporting)
42001 B.9.3 (Objectives for responsible use of AI system) (Gap: No Gap)
- **nist_ai_600_1**: MG-3.2-001
GV-4.1-001 (Gap: No Gap)

### CAIQ Questions

- **GRC-14.1**: Is the degree of explainability of the AI Services evaluated, documented, and communicated, including possible limitations and exceptions?

---

## GRC-15: Human supervision

**Type:** control
**Control Type:** AI-Specific
**Architectural Relevance:** Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Sensitive data disclosure, Model theft, Model/Service Failure, Denial of Service

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data storage
- Development: Guardrails
- Evaluation/Validation: Validation/Red Teaming, Re-evaluation
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: N/A

### Specification

Establish, execute, and assess processes, procedures, and technical measures to ensure human oversight and control of the AI system in compliance with regulatory requirements and organizational risk management.

### Cross-References

- **bsi_aic4**: C4 PC-02
RE-01
RE-04
C5 PSS-03 (Gap: No Gap)
- **eu_ai_act**: Article 14
Article 15
Article 17 (Gap: No Gap)
- **iso_42001**: 42001: B.5.1 AI system risk assessment and treatment
42001: B.5.3 (Documentation of AI system impact assessments)
42001: B.6.1.3 (Processes for responsible design and development of AI systems)
42001: B.5.3 Documentation of AI system impact assessments
42001: B.6.1.4 Accountability and human oversight mechanisms
42001: B.6.2.1 Technical robustness and security
42001: B.7.1.1 Monitoring and review of AI system behavior
42001: B.7.1.2 Incident management for AI systems
42001: B.8.2.1 Compliance with legal and regulatory requirements (Gap: No Gap)
- **nist_ai_600_1**: GV-3.2-001
GV-4.1-003
MG-2.2-003
MP-2.3-001 (Gap: No Gap)

### CAIQ Questions

- **GRC-15.1**: Are processes, procedures, and technical measures to ensure human oversight and control of the AI system in compliance with regulatory requirements and organizational risk management, established, executed and assessed?

---

# Domain: Human Resources

## HRS-01: Background Screening Policy and Procedures

**Type:** control
**Control Type:** Cloud & AI Related
**Threat Categories:** Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Application: Shared across the supply chain

**Lifecycle Relevance:**
- Preparation: Team and expertise
- Development: Supply Chain
- Evaluation/Validation: N/A
- Deployment: AI Services supply chain
- Delivery: N/A
- Service Retirement: N/A

### Specification

Establish, document, approve, communicate, apply, evaluate and maintain policies and procedures for background verification of all new employees (including but not limited to remote employees, contractors, and third parties) according to local laws, regulations, ethics, and contractual constraints and proportional to the data classification to be accessed, the business requirements, and acceptable risk. Review and update the policies and procedures at least annually.

### Cross-References

- **bsi_aic4**: HR-01 (Gap: No Gap)
- **eu_ai_act**: No Mapping (Gap: Full Gap)
- **iso_42001**: 42001: A.2.2 AI Policy
42001: A.2.3 Alignment with other organizational policies
42001: A.2.4 Review of AI Policy
27001: 5.1 Leadership and commitment
27001: 5.2 Policy
27001: 7.3 Awareness
27001: 7.4 Communication
27001: 7.5 Documented Information
27001: 9.1 Monitoring
measurement
analysis and evaluation
27001: 9.3 Management Review
27001: A.5.1 Policies for information security
27001: A.5.4 Management responsibilities
27001: A.5.10 Acceptable use of information and other associated assets
27001: A.5.37 Documented operating procedures
27001: A.6.1 Screening27001: A.5.1 Policies for information security
27001: 5.1 Policies for information security
27002: 5.4 Management responsibilities
27001: 5.10 Acceptable use of information and other associated assets
27001: 5.37 Documented operating procedures
27001: 6.1 Screening (Gap: No Gap)
- **nist_ai_600_1**: MP-4.1-003 (Gap: No Gap)

### CAIQ Questions

- **HRS-01.1**: Are new employee background verification policies and procedures (including but not limited to remote employees, contractors, and third parties) established, documented, approved, communicated, applied, evaluated, and maintained?
- **HRS-01.2**: Are background verification policies and procedures designed according to local laws, regulations, ethics, and contractual constraints and proportional to the data classification to be accessed, business requirements, and acceptable risk?
- **HRS-01.3**: Are background verification policies and procedures reviewed and updated at least annually?

---

## HRS-02: Acceptable Use of Technology Policy and Procedures

**Type:** control
**Control Type:** Cloud & AI Related
**Threat Categories:** Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Application: Shared across the supply chain

**Lifecycle Relevance:**
- Preparation: Team and expertise
- Development: Supply Chain
- Evaluation/Validation: N/A
- Deployment: AI Services supply chain
- Delivery: N/A
- Service Retirement: N/A

### Specification

Establish, document, approve, communicate, apply, evaluate and maintain policies and procedures for defining allowances and conditions for the acceptable use of organizationally-owned or managed assets. Review and update the policies and procedures at least annually.

### Cross-References

- **bsi_aic4**: HR-02
AM-05 (Gap: No Gap)
- **eu_ai_act**: Article 53 (1)
Annex XI
Annex XII (Gap: Partial Gap)
- **iso_42001**: 42001: A.2.2 AI Policy
42001: A.2.3 Alignment with other organizational policies
42001: A.2.4 Review of AI Policy
27001: 5.1 Leadership and commitment
27001: 5.2 Policy
27001: 7.3 Awareness
27001: 7.4 Communication
27001: 7.5 Documented Information
27001: 9.1 Monitoring
measurement
analysis and evaluation
27001: 9.3 Management Review
27001: A.5.1 Policies for information security
27001: A.5.4 Management responsibilities
27001: A.5.10 Acceptable use of information and other associated assets
27001: A.5.37 Documented operating procedures
27002: 5.1 Policies for information security
27002: 5.4 Management responsibilities
27002: 5.10 Acceptable use of information and other associated assets
27002: 5.37 Documented operating procedures (Gap: No Gap)
- **nist_ai_600_1**: GV-6.1-010
GV-1.4-002
GV-3.2-003
GV-1.3-004
A.1.2 (Gap: No Gap)

### CAIQ Questions

- **HRS-02.1**: Are policies and procedures for defining allowances and conditions for the  acceptable use of organizationally-owned or managed assets established, documented, approved, communicated, applied, evaluated, and maintained?
- **HRS-02.2**: Are the policies and procedures for defining allowances and conditions for the acceptable use of organizationally-owned or managed assets reviewed and updated at least annually?

---

## HRS-03: Clean Desk Policy and Procedures

**Type:** control
**Control Type:** Cloud & AI Related
**Threat Categories:** Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Application: Shared across the supply chain

**Lifecycle Relevance:**
- Preparation: Team and expertise
- Development: Supply Chain
- Evaluation/Validation: N/A
- Deployment: AI Services supply chain
- Delivery: N/A
- Service Retirement: N/A

### Specification

Establish, document, approve, communicate, apply, evaluate and maintain policies and procedures that require unattended workspaces to not have openly visible confidential data. Review and update the policies and procedures at least annually.

### Cross-References

- **bsi_aic4**: No mapping (Gap: Full Gap)
- **eu_ai_act**: No Mapping (Gap: Full Gap)
- **iso_42001**: 42001: A.2.2 AI Policy
42001: A.2.3 Alignment with other organizational policies
42001: A.2.4 Review of AI Policy
27001: 5.1 Leadership and commitment
27001: 5.2 Policy
27001: 7.3 Awareness
27001: 7.4 Communication
27001: 7.5 Documented Information
27001: 9.1 Monitoring
measurement
analysis and evaluation
27001: 9.3 Management Review
27001: A.5.1 Policies for information security
27001: A.5.4 Management responsibilities
27001: A.5.37 Documented operating procedures
27001: A.7.7 Clear desk and clear screen
27002: 5.1 Policies for information security
27002: 5.4 Management responsibilities
27002: 5.37 Documented operating procedures
27002: 7.7 Clear desk and clear screen (Gap: No Gap)
- **nist_ai_600_1**: MP-4.1-003 (Gap: No Gap)

### CAIQ Questions

- **HRS-03.1**: Are policies and procedures requiring unattended workspaces to conceal confidential data established, documented, approved, communicated, applied, evaluated, and maintained?
- **HRS-03.2**: Are policies and procedures requiring unattended workspaces to conceal confidential data reviewed and updated at least annually?

---

## HRS-04: Remote and Home Working Policy and Procedures

**Type:** control
**Control Type:** Cloud & AI Related
**Threat Categories:** Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Application: Shared across the supply chain

**Lifecycle Relevance:**
- Preparation: Team and expertise
- Development: Supply Chain
- Evaluation/Validation: N/A
- Deployment: AI Services supply chain
- Delivery: N/A
- Service Retirement: N/A

### Specification

Establish, document, approve, communicate, apply, evaluate and maintain policies and procedures to protect information accessed, processed or stored at remote sites and locations. Review and update the policies and procedures at least annually.

### Cross-References

- **bsi_aic4**: AM-02
PS-01
SSO-01 (Gap: No Gap)
- **eu_ai_act**: No Mapping (Gap: Full Gap)
- **iso_42001**: 42001: A.2.2 AI Policy
42001: A.2.3 Alignment with other organizational policies
42001: A.2.4 Review of AI Policy
27001: 5.1 Leadership and commitment
27001: 5.2 Policy
27001: 7.3 Awareness
27001: 7.4 Communication
27001: 7.5 Documented Information
27001: 9.1 Monitoring
measurement
analysis and evaluation
27001: 9.3 Management Review
27001: A.5.1 Policies for information security
27001: A.5.4 Management responsibilities
27001: A.5.37 Documented operating procedures
27001: A.6.7 Remote working
27001: A.7.9 Security of assets off-premises
27002: 5.1 Policies for information security
27002: 5.4 Management responsibilities
27002: 5.37 Documented operating procedures
27002: 6.7 Remote working
27002: 7.9 Security of assets off-premises (Gap: No Gap)
- **nist_ai_600_1**: MP-4.1-003 (Gap: No Gap)

### CAIQ Questions

- **HRS-04.1**: Are policies and procedures to protect information accessed, processed, or stored at remote sites and locations established, documented, approved, communicated, applied, evaluated, and maintained?
- **HRS-04.2**: Are policies and procedures to protect information accessed, processed, or stored at remote sites and locations reviewed and updated at least annually?

---

## HRS-05: Asset returns

**Type:** control
**Control Type:** Cloud & AI Related
**Threat Categories:** Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Application: Shared across the supply chain

**Lifecycle Relevance:**
- Preparation: Team and expertise
- Development: Supply Chain
- Evaluation/Validation: N/A
- Deployment: AI Services supply chain
- Delivery: N/A
- Service Retirement: N/A

### Specification

Establish and document procedures for the return of organization-owned assets by terminated employees.

### Cross-References

- **bsi_aic4**: AM-05 (Gap: No Gap)
- **eu_ai_act**: No Mapping (Gap: Full Gap)
- **iso_42001**: 42001: A.2.3 Alignment with other organizational policies
27001: A.5.11 Return of assets
27002: 5.11 Return of assets (Gap: No Gap)
- **nist_ai_600_1**: GV-1.7-002
MP-4.1-003 (Gap: No Gap)

### CAIQ Questions

- **HRS-05.1**: Are return procedures of organizationally-owned assets by terminated employees established and documented?

---

## HRS-06: Employment Termination

**Type:** control
**Control Type:** Cloud & AI Related
**Threat Categories:** Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Application: Shared across the supply chain

**Lifecycle Relevance:**
- Preparation: Team and expertise
- Development: Supply Chain
- Evaluation/Validation: N/A
- Deployment: AI Services supply chain
- Delivery: N/A
- Service Retirement: N/A

### Specification

Establish, document, and communicate to all personnel the procedures outlining the roles and responsibilities concerning changes in employment.

### Cross-References

- **bsi_aic4**: HR-05 (Gap: No Gap)
- **eu_ai_act**: No Mapping (Gap: Full Gap)
- **iso_42001**: 42001: A.2.3 Alignment with other organizational policies
27001: A.6.5 Responsibilities after termination or change of employment
27002: 6.5 Responsibilities after termination or change of employment (Gap: No Gap)
- **nist_ai_600_1**: MP-4.1-003 (Gap: No Gap)

### CAIQ Questions

- **HRS-06.1**: Are procedures outlining the roles and responsibilities concerning changes in employment established, documented, and communicated to all personnel?

---

## HRS-07: Employment Agreement Process

**Type:** control
**Control Type:** Cloud & AI Related
**Threat Categories:** Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Application: Shared across the supply chain

**Lifecycle Relevance:**
- Preparation: Team and expertise
- Development: Supply Chain
- Evaluation/Validation: N/A
- Deployment: AI Services supply chain
- Delivery: N/A
- Service Retirement: N/A

### Specification

Employees sign the employee agreement prior to being granted access to organizational information systems, resources and assets.

### Cross-References

- **bsi_aic4**: HR-02 (Gap: No Gap)
- **eu_ai_act**: No Mapping (Gap: Full Gap)
- **iso_42001**: 42001: A.2.3 Alignment with other organizational policies
27001: A.6.2 Terms and conditions of employment
27002: 6.2 Terms and conditions of employment (Gap: No Gap)
- **nist_ai_600_1**: MP-4.1-003 (Gap: No Gap)

### CAIQ Questions

- **HRS-07.1**: Are employees required to sign an employment agreement before gaining access to organizational information systems, resources, and assets?

---

## HRS-08: Employment Agreement Content

**Type:** control
**Control Type:** Cloud & AI Related
**Threat Categories:** Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Application: Shared across the supply chain

**Lifecycle Relevance:**
- Preparation: Team and expertise
- Development: Supply Chain
- Evaluation/Validation: N/A
- Deployment: AI Services supply chain
- Delivery: N/A
- Service Retirement: N/A

### Specification

The organization includes within the employment agreements provisions and/or terms for adherence to established information governance and security policies.

### Cross-References

- **bsi_aic4**: HR-02 (Gap: No Gap)
- **eu_ai_act**: No Mapping (Gap: Full Gap)
- **iso_42001**: 42001: A.2.3 Alignment with other organizational policies
27001: A.6.2 Terms and conditions of employment
27001: A.6.6 Confidentiality or non-disclosure agreements
27002: 6.2 Terms and conditions of employment
27002: 6.6 Confidentiality or non-disclosure agreements (Gap: No Gap)
- **nist_ai_600_1**: MP-4.1-003 (Gap: No Gap)

### CAIQ Questions

- **HRS-08.1**: Are provisions and/or terms for adherence to established information governance and security policies included within employment agreements?

---

## HRS-09: Personnel Roles and Responsibilities

**Type:** control
**Control Type:** Cloud & AI Related
**Threat Categories:** Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Application: Shared across the supply chain

**Lifecycle Relevance:**
- Preparation: Team and expertise
- Development: Supply Chain
- Evaluation/Validation: N/A
- Deployment: AI Services supply chain
- Delivery: N/A
- Service Retirement: N/A

### Specification

Document and communicate roles and responsibilities of employees, as they relate to information assets and security.

### Cross-References

- **bsi_aic4**: HR-02
HR-03
AM-05 (Gap: No Gap)
- **eu_ai_act**: Article 17 (1) (m)
Article 4 (Gap: Partial Gap)
- **iso_42001**: 42001: A.2.3 Alignment with other organizational policies
27001: 5.3 Organizational roles
responsibilities and authorities
27001: A.5.2 Information security roles and responsibilities
27002: 5.2 Information security roles and responsibilities (Gap: No Gap)
- **nist_ai_600_1**: GV-2.1-001
GV-1.5-001
GV-1.6-003
GV-3.2-003
GV-6.1-010
MP-4.1-003 (Gap: No Gap)

### CAIQ Questions

- **HRS-09.1**: Are employee roles and responsibilities relating to information assets and security documented and communicated?

---

## HRS-10: Non-Disclosure Agreements

**Type:** control
**Control Type:** Cloud & AI Related
**Threat Categories:** Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Application: Shared across the supply chain

**Lifecycle Relevance:**
- Preparation: Team and expertise
- Development: Supply Chain
- Evaluation/Validation: N/A
- Deployment: AI Services supply chain
- Delivery: N/A
- Service Retirement: N/A

### Specification

Identify, document, and review, at planned intervals, requirements for non-disclosure/confidentiality agreements reflecting the organization's needs for the protection of data and operational details.

### Cross-References

- **bsi_aic4**: HR-06 (Gap: No Gap)
- **eu_ai_act**: No Mapping (Gap: Full Gap)
- **iso_42001**: 42001: A.2.3 Alignment with other organizational policies
27001: A.6.2 Terms and conditions of employment
27001: A.6.6 Confidentiality or non-disclosure agreements Control
27002: 6.2 Terms and conditions of employment
27002: 6.6 Confidentiality or non-disclosure agreements Control (Gap: No Gap)
- **nist_ai_600_1**: MP-4.1-003 (Gap: No Gap)

### CAIQ Questions

- **HRS-10.1**: Are requirements for non-disclosure/confidentiality agreements reflecting organizational data protection needs and operational details identified, documented, and reviewed at planned intervals?

---

## HRS-11: Security Awareness Training

**Type:** control
**Control Type:** Cloud & AI Related
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Application: Shared across the supply chain

**Lifecycle Relevance:**
- Preparation: Team and expertise
- Development: Supply Chain
- Evaluation/Validation: N/A
- Deployment: AI Services supply chain
- Delivery: N/A
- Service Retirement: N/A

### Specification

Establish, document, approve, communicate, apply, evaluate and maintain a security awareness training program for all employees of the organization and provide regular training updates.

### Cross-References

- **bsi_aic4**: HR-03
DEV-04 (Gap: No Gap)
- **eu_ai_act**: Article 4
Article 17 (Gap: Partial Gap)
- **iso_42001**: 42001: A.2.3 Alignment with other organizational policies
42001: 5.3 Roles
responsibilities and authorities
42001: 7.3 Awareness
42001: A.4.6 Human Resource
27001: 7.3 Awareness
27001: A.5.1 Policies for Information Security
27001: A.5.36 Compliance with policies
rules and standards for information security
27001: A.6.3 Information security awareness
education and training
27002: 5.1 Policies for Information Security
27002: 5.36 Compliance with policies
rules and standards for information security
27002: 6.3 Information security awareness
education and training (Gap: No Gap)
- **nist_ai_600_1**: MP-4.1-003 (Gap: No Gap)

### CAIQ Questions

- **HRS-11.1**: Is a security awareness training program for all employees of the organization established, documented, approved, communicated, applied, evaluated and maintained?
- **HRS-11.2**: Are regular security awareness training updates provided?

---

## HRS-12: Personal and Sensitive Data Awareness and Training

**Type:** control
**Control Type:** Cloud & AI Related
**Threat Categories:** Sensitive data disclosure, Insecure supply chain, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Application: Shared across the supply chain

**Lifecycle Relevance:**
- Preparation: Team and expertise
- Development: Supply Chain
- Evaluation/Validation: N/A
- Deployment: AI Services supply chain
- Delivery: N/A
- Service Retirement: N/A

### Specification

Provide employees with access to sensitive organizational and personal data with appropriate security awareness training and regular  updates in organizational procedures, processes, and policies relating  to their professional function relative to the organization.

### Cross-References

- **bsi_aic4**: HR-03 (Gap: No Gap)
- **eu_ai_act**: Article 4
Article 17 (Gap: Partial Gap)
- **iso_42001**: 42001: A.2.3 Alignment with other organizational policies
42001: 5.3 Roles
responsibilities and authorities
42001: 7.3 Awareness
42001: A.3.2 AI Roles and responsibilities
42001: A.4.6 Human Resource
27001: 7.3 Awareness
27001: A.5.1 Policies for information security
27001: A.5.10 Acceptable use of information and other associated assets
27001: A.6.3 Information security awareness
education and training
27002: 5.1 Policies for Information Security
27002: 5.10 Acceptable use of information and other associated assets
27002: 6.3 Information security awareness
education and training (Gap: No Gap)
- **nist_ai_600_1**: MP-4.1-003 (Gap: No Gap)

### CAIQ Questions

- **HRS-12.1**: Are employees with access to sensitive organizational and personal data, provided with appropriate security awareness training and regular updates in organizational procedures, processes, and policies, relating to their professional function relative to the organization?

---

## HRS-13: Compliance User Responsibility

**Type:** control
**Control Type:** Cloud & AI Related
**Threat Categories:** Sensitive data disclosure, Insecure supply chain, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Application: Shared across the supply chain

**Lifecycle Relevance:**
- Preparation: Team and expertise
- Development: Supply Chain
- Evaluation/Validation: N/A
- Deployment: AI Services supply chain
- Delivery: N/A
- Service Retirement: N/A

### Specification

Make employees aware of their roles and responsibilities for maintaining awareness and compliance with established policies and procedures and applicable legal, statutory, or regulatory compliance obligations.

### Cross-References

- **bsi_aic4**: HR-03 (Gap: No Gap)
- **eu_ai_act**: Article 17 (1) (m) (Gap: Partial Gap)
- **iso_42001**: 42001: A.2.3 Alignment with other organizational policies
42001: 5.3 Roles
responsibilities and authorities
42001: 7.3 Awareness
42001: A.3.2 AI Roles and responsibilities
42001: A.4.6 Human Resource
27001: 5.1 Leadership Commitment
27001: 5.3 Organization Roles
Responsibilities and Authorities
27001: 7.3 Awareness
27001: A.5.4 Management responsibilities
27001: A.6.2 Terms and conditions of employment
27001: A.6.3 Information security awareness
education and training
27002: 5.4 Management responsibilities
27002: 6.2 Terms and conditions of employment
27002: 6.3 Information security awareness
education and training (Gap: No Gap)
- **nist_ai_600_1**: GV-4.1-003
MP-4.1-003
MG-4.3-003 (Gap: No Gap)

### CAIQ Questions

- **HRS-13.1**: Are employees notified of their roles and responsibilities to maintain awareness and compliance with established policies, 
procedures, and applicable legal, statutory, or regulatory compliance obligations?

---

## HRS-14: AI Competency Training

**Type:** control
**Control Type:** AI-Specific
**Threat Categories:** Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Owned by the Customer (AIC)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Application: Shared across the supply chain

**Lifecycle Relevance:**
- Preparation: Team and expertise
- Development: Supply Chain
- Evaluation/Validation: N/A
- Deployment: AI Services supply chain
- Delivery: N/A
- Service Retirement: N/A

### Specification

Establish, document, approve, communicate, apply, evaluate and maintain policies and procedures defining the AI training program for all relevant personnel of the organization based on their roles and provide regular training updates.

### Cross-References

- **bsi_aic4**: C5 HR-03 (Gap: Partial Gap)
- **eu_ai_act**: Recital 91
Article 4 (Gap: Partial Gap)
- **iso_42001**: 42001: 5.3 Roles
responsibilities and authorities
42001: 7.2 Competence
42001: 7.3 Awareness
42001: A.3.2 AI Roles and responsibilities
42001: A.4.6 Human Resource (Gap: No Gap)
- **nist_ai_600_1**: GV-2.1-003
MP-1.2-001
MP-3.4-003
MP-4.1-003 (Gap: No Gap)

### CAIQ Questions

- **HRS-14.1**: Are the policies and procedures defining the AI training program for all relevant personnel of the organization established, documented, approved, communicated, applied, evaluated, and maintained?
- **HRS-14.2**: Are regular training updates given to personnel based on their roles?

---

## HRS-15: AI Acceptable Use

**Type:** control
**Control Type:** AI-Specific
**Threat Categories:** Sensitive data disclosure, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Owned by the Customer (AIC)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Application: Shared across the supply chain

**Lifecycle Relevance:**
- Preparation: Team and expertise
- Development: Supply Chain
- Evaluation/Validation: N/A
- Deployment: AI Services supply chain
- Delivery: N/A
- Service Retirement: N/A

### Specification

Establish, document, and communicate to all personnel the policies and procedures on the acceptable use of AI technologies within the organization.

### Cross-References

- **bsi_aic4**: C5 HR-03
C5 AM-02 (Gap: Partial Gap)
- **eu_ai_act**: Article 11
Article 53 (1) (Gap: Partial Gap)
- **iso_42001**: 42001: 5.3 Roles
responsibilities and authorities
42001: 7.3 Awareness
42001: A.3.2 AI Roles and responsibilities
42001: A.9.2 Processes for responsible use of AI systems
42001: A.9.3 Objectives for responsible use of AI systems (Gap: No Gap)
- **nist_ai_600_1**: GV-6.1-010
GV-1.4-002
GV-3.2-003
GV-1.3-004
A.1.2
MP-4.1-003 (Gap: No Gap)

### CAIQ Questions

- **HRS-15.1**: Are the policies and procedures on the acceptable use of AI technologies within the organization established, documented, and communicated to all personnel?

---

# Domain: Identity & Access Management

## IAM-01: Identity and Access Management Policy and Procedures

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Owned by the Orchestrated Service Provider (OSP)
- Application: Shared Application Provider-AI Customer (Shared AP-AIC)

**Lifecycle Relevance:**
- Preparation: Data collection, Data storage, Team and expertise
- Development: Design, Supply Chain
- Evaluation/Validation: Evaluation
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous improvement
- Service Retirement: Archiving, Data deletion, Model disposal

### Specification

Establish, document, approve, communicate, implement, apply, evaluate and maintain policies and procedures for identity and access management. Review and update the policies and procedures at least annually, or upon significant changes.

### Cross-References

- **bsi_aic4**: C4 PC-02
C5 IDM-01 (Gap: No Gap)
- **eu_ai_act**: Article 9
Article 10
Article 12 (Gap: Partial Gap)
- **iso_42001**: 42001 A.2.3 - Alignment with other organizational policies
42001 A.2.4 - Review of the AI policy
27001 A.5.1 - Policies for information security
27001 A.5.36 - Compliance with policies
rules and standards for information security
27001 A.5.15 - Access control (Gap: No Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **IAM-01.1**: Are Identity and Access Management policies and procedures established, documented, approved, communicated, implemented, applied, evaluated, and maintained for identity and access management?
- **IAM-01.2**: Are Identity and Access Management Policies and Procedures reviewed and updated at least annually, or upon significant changes?

---

## IAM-02: Strong Password Policy and Procedures

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Sensitive data disclosure, Model theft, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Owned by the Orchestrated Service Provider (OSP)
- Application: Shared Application Provider-AI Customer (Shared AP-AIC)

**Lifecycle Relevance:**
- Preparation: Data collection, Data storage, Team and expertise
- Development: Design, Supply Chain
- Evaluation/Validation: Evaluation, Validation/Red Teaming
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous improvement
- Service Retirement: Archiving, Data deletion, Model disposal

### Specification

Establish, document, approve, communicate, implement, apply, evaluate and maintain strong password policies and procedures. Review and update the policies and procedures at least annually.

### Cross-References

- **bsi_aic4**: C4 PC-02
C5 IDM-01
C5 IDM-02 (Gap: No Gap)
- **eu_ai_act**: Annex IV,
Article 8,
Article 9,
Article 15 (Gap: Partial Gap)
- **iso_42001**: 42001: A.2.3 - Alignment with other organizational policies
42001: A.2.4 - Review of the AI policy
27001: A.5.1 - Policies for information security
27001: A.5.17 - Authentication information (Gap: No Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **IAM-02.1**: Are strong password policies and procedures established, documented, approved, communicated, implemented, applied, evaluated, and maintained?
- **IAM-02.2**: Are strong password policies and procedures reviewed and updated at least annually?

---

## IAM-03: Identity Inventory

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Sensitive data disclosure, Model theft, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared across the supply chain
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Owned by the Orchestrated Service Provider (OSP)
- Application: Shared Application Provider-AI Customer (Shared AP-AIC)

**Lifecycle Relevance:**
- Preparation: Data collection, Data storage, Team and expertise
- Development: Design, Training, Guardrails, Supply Chain
- Evaluation/Validation: Evaluation, Re-evaluation
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous improvement
- Service Retirement: Archiving, Data deletion, Model disposal

### Specification

Manage, store, and regularly review the inventory of identities, and monitor their level of access.

### Cross-References

- **bsi_aic4**: C4 DM-01
C4 DM-02
C5 IDM-02
C5 IDM-03
C5 IDM-04
C5 IDM-05 (Gap: No Gap)
- **eu_ai_act**: Article 8
Article 9
Article 10 (Gap: Partial Gap)
- **iso_42001**: 42001: A.2.3 - Alignment with other organizational policies
42001: A.2.4 - Review of the AI policy
27001: A.5.1 - Policies for information security
27001: A.5.16 - Identity management (Gap: No Gap)
- **nist_ai_600_1**: GV-1.6-003 (Gap: No Gap)

### CAIQ Questions

- **IAM-03.1**: Is the inventory of identities managed, stored and regularly reviewed, and is their level of access monitored?

---

## IAM-04: Separation of Duties

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Insecure supply chain, Insecure apps/plugins, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared across the supply chain
- Application: Shared Application Provider-AI Customer (Shared AP-AIC)

**Lifecycle Relevance:**
- Preparation: Team and expertise, Resource provisioning
- Development: Design, Supply Chain, Guardrails
- Evaluation/Validation: Evaluation, Validation/Red Teaming, Re-evaluation
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous improvement, Continuous monitoring
- Service Retirement: Archiving, Data deletion

### Specification

Employ the separation of duties principle when implementing information system access.

### Cross-References

- **bsi_aic4**: C4 DM-01
C4 DM-02
C5 IDM-02
C5 OIS-02 (Gap: No Gap)
- **eu_ai_act**: Article 9
Article 10
Article 14
Article 15 (Gap: Partial Gap)
- **iso_42001**: 42001 B.3.2 - AI roles and responsibilities
27001 A.5.3 - Segregation of duties
27001 A.5.15 - Access control
27001 A.5.18 - Access rights (Gap: No Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **IAM-04.1**: Are separation of duties principles employed when implementing information system access?

---

## IAM-05: Least Privilege

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Insecure supply chain, Insecure apps/plugins, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared across the supply chain
- Model: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Shared Orchestrated Service Provider-Application Provider (Shared OSP-AP)

**Lifecycle Relevance:**
- Preparation: Data storage, Resource provisioning, Team and expertise
- Development: Design, Supply Chain, Guardrails
- Evaluation/Validation: Evaluation, Validation/Red Teaming, Re-evaluation
- Deployment: AI Services supply chain, Orchestration, AI applications
- Delivery: Operations, Maintenance
- Service Retirement: Archiving, Data deletion, Model disposal

### Specification

Employ the least privilege principle when implementing information system access.

### Cross-References

- **bsi_aic4**: C4 DM-01
C4 DM-02
C5 IDM-02
C5 OIS-02 (Gap: No Gap)
- **eu_ai_act**: Article 9
Article 10
Article 15 (Gap: Partial Gap)
- **iso_42001**: 42001 B.3.2 - AI roles and responsibilities
27001 A.5.15 - Access control
27001 A.5.18 - Access rights
27001 A.8.2 - Privileged access rights (Gap: No Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **IAM-05.1**: Are least privilege principles employed when implementing information system access?

---

## IAM-06: User Access Provisioning

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Insecure supply chain, Insecure apps/plugins, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Shared Orchestrated Service Provider-Application Provider (Shared OSP-AP)

**Lifecycle Relevance:**
- Preparation: Data storage, Resource provisioning, Team and expertise
- Development: Training, Guardrails, Supply Chain
- Evaluation/Validation: Evaluation, Validation/Red Teaming, Re-evaluation
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance
- Service Retirement: Archiving, Data deletion, Model disposal

### Specification

Define and implement an identity access provisioning process which  authorizes, records, and communicates access changes to data and assets.

### Cross-References

- **bsi_aic4**: C4 DM-01
C4 DM-02
C4 RE-02
C5 IDM-02 (Gap: No Gap)
- **eu_ai_act**: Article 8
Article 9
Article 10
Article 12 (Gap: Partial Gap)
- **iso_42001**: 42001: A.2.3 - Alignment with other organizational policies
42001: A.2.4 - Review of the AI policy
27001: A.5.1 - Policies for information security
27001 A.5.18 - Access rights
27001 A.5.15 - Access control (Gap: No Gap)
- **nist_ai_600_1**: MG-2.4-001 (Gap: Partial Gap)

### CAIQ Questions

- **IAM-06.1**: Is an identity access provisioning process which authorizes, records, and communicates access changes to data and assets, defined and implemented?

---

## IAM-07: User Access Changes and Revocation

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Insecure supply chain, Insecure apps/plugins, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Application: Shared Orchestrated Service Provider-Application Provider (Shared OSP-AP)

**Lifecycle Relevance:**
- Preparation: Team and expertise, Data storage, Resource provisioning, Data curation
- Development: Training, Guardrails, Supply Chain
- Evaluation/Validation: Evaluation, Validation/Red Teaming, Re-evaluation
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance
- Service Retirement: Archiving, Data deletion, Model disposal

### Specification

De-provision or modify identity access in a timely manner.

### Cross-References

- **bsi_aic4**: C4 DM-01
C4 DM-02
C5 IDM-03
C5 IDM-04 (Gap: No Gap)
- **eu_ai_act**: Article 8
Article 9
Article 10
Article 13
Article 20 (Gap: Partial Gap)
- **iso_42001**: 42001: A.2.3 - Alignment with other organizational policies
42001: A.2.4 - Review of the AI policy
27001: A.5.1 - Policies for information security
27001: A.5.18  - Access rights (Gap: No Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **IAM-07.1**: Is identity access de-provisioned or modified, in a timely manner?

---

## IAM-08: User Access Review

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Insecure supply chain, Insecure apps/plugins, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Application: Shared Orchestrated Service Provider-Application Provider (Shared OSP-AP)

**Lifecycle Relevance:**
- Preparation: Data storage, Resource provisioning, Team and expertise, Data curation
- Development: Training, Guardrails, Supply Chain
- Evaluation/Validation: Evaluation, Validation/Red Teaming, Re-evaluation
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance
- Service Retirement: Archiving, Data deletion, Model disposal

### Specification

Review and revalidate user access for least privilege and separation of duties with a frequency that is commensurated with organizational risk  tolerance and at least annually, or upon significant changes.

### Cross-References

- **bsi_aic4**: C4 DM-01
C4 DM-02
C5 IDM-05 (Gap: No Gap)
- **eu_ai_act**: Article 8
Article 9
Article 14
Article 15 (Gap: Partial Gap)
- **iso_42001**: 42001 B.3.2 - AI roles and responsibilities
27001 A.5.18 - Access rights
27001 A.5.15 - access control (Gap: No Gap)
- **nist_ai_600_1**: MP-3.4-005 (Gap: Partial Gap)

### CAIQ Questions

- **IAM-08.1**: Are user access for least privilege and separation of duties reviewed and revalidated with a frequency commensurated with organizational risk tolerance and at least annually or upon significant changes?

---

## IAM-09: Segregation of Privileged Access Roles

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Insecure supply chain, Insecure apps/plugins, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Shared Orchestrated Service Provider-Application Provider (Shared OSP-AP)

**Lifecycle Relevance:**
- Preparation: Data curation, Data storage, Resource provisioning, Team and expertise
- Development: Training, Guardrails, Supply Chain
- Evaluation/Validation: Evaluation, Validation/Red Teaming, Re-evaluation
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance
- Service Retirement: Archiving, Data deletion, Model disposal

### Specification

Define, implement and evaluate processes, procedures and technical measures for the segregation of privileged access roles.

### Cross-References

- **bsi_aic4**: C4 DM-01
C4 DM-02
C4 RE-02
C5 IDM-06
C5 OPS-10
C5 OPS-12
C5 CRY-04 (Gap: Partial Gap)
- **eu_ai_act**: Article 11
Article 13
Article 14 (Gap: Partial Gap)
- **iso_42001**: 42001: A.2.3 - Alignment with other organizational policies
42001: A.2.4 - Review of the AI policy
27001: A.5.1 - Policies for information security
27001: A.5.18 - Access rights
27001:A.8.2 - Privileged access rights
27001:A.8.3 - Information access restriction
27001:A.8.4 - Access to source code
27001.A.8.18 - Use of privileged utility programs (Gap: No Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **IAM-09.1**: Are processes, procedures, and technical measures for the segregation of privileged access roles, defined, implemented, and evaluated?

---

## IAM-10: Management of Privileged Access Roles

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Insecure supply chain, Insecure apps/plugins, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Orchestrated Service Provider-Application Provider (Shared OSP-AP)
- Application: Shared Application Provider-AI Customer (Shared AP-AIC)

**Lifecycle Relevance:**
- Preparation: Data storage, Resource provisioning
- Development: Design, Supply Chain
- Evaluation/Validation: Validation/Red Teaming
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Archiving, Data deletion, Model disposal

### Specification

Define and implement an access process to ensure privileged access roles and rights are granted for a time limited period, and implement procedures to prevent the accumulation of segregated privileged access.

### Cross-References

- **bsi_aic4**: C4 DM-01
C4 DM-02
C5 IMD-06 (Gap: No Gap)
- **eu_ai_act**: Article 9
Article 10
Article 14 (1)
Article 14 (4)
Article 15
Article 26 (2)
Annex IV (Gap: Partial Gap)
- **iso_42001**: 42001: A.2.3 - Alignment with other organizational policies
42001: A.2.4 - Review of the AI policy
27001: A.5.1 - Policies for information security
27001: A.8.2 - Privileged access rights
27001.A.8.18 - Use of privileged utility programs (Gap: No Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **IAM-10.1**: Is an access process defined and implemented to ensure privileged access roles and rights are granted for a time-limited period?
- **IAM-10.2**: Are procedures implemented to prevent the accumulation of segregated privileged access?

---

## IAM-11: Customers' Approval for Agreed Privileged Access Roles

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Insecure supply chain, Insecure apps/plugins, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Application Provider-AI Customer (Shared AP-AIC)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data storage, Data collection
- Development: Design, Supply Chain
- Evaluation/Validation: Validation/Red Teaming
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance
- Service Retirement: Archiving, Data deletion, Model disposal

### Specification

Define, implement and evaluate processes and procedures for  customers to participate, where applicable, in the granting of access  for agreed, high risk (as defined by the organizational risk assessment)  privileged access roles.

### Cross-References

- **bsi_aic4**: C5 IMD-06 (Gap: Partial Gap)
- **eu_ai_act**: Article 9
Article 10
Article 23
Annex IV (Gap: Partial Gap)
- **iso_42001**: 42001: A.2.3 - Alignment with other organizational policies
42001: A.2.4 - Review of the AI policy
27001: A.5.1 - Policies for information security
27001: 6.1 - Actions to address risks and opportunities
27001: 8.1 - Operational planning and control
27001: A.5.15 - Access control
27001: A.5.19 - Information security in supplier
relationships (Gap: No Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **IAM-11.1**: Are processes and procedures defined, implemented, and evaluated for customers to participate, where applicable, in granting access for agreed high-risk (as defined by the organizational risk assessment) privileged access roles?

---

## IAM-12: Safeguard Logs Integrity

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Owned by the Cloud Service Provider (CSP)
- Model: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Orchestrated Services: Shared across the supply chain
- Application: Shared Orchestrated Service Provider-Application Provider (Shared OSP-AP)

**Lifecycle Relevance:**
- Preparation: Data storage, Resource provisioning, Team and expertise
- Development: Design, Supply Chain
- Evaluation/Validation: Validation/Red Teaming
- Deployment: AI Services supply chain, Orchestration, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring
- Service Retirement: Archiving, Data deletion, Model disposal

### Specification

Define, implement and evaluate processes, procedures and technical measures to ensure the logging infrastructure is read-only for all with  write access, including privileged access roles, and that the ability to  disable it is controlled through a procedure that ensures the segregation of  duties and break glass procedures.

### Cross-References

- **bsi_aic4**: C4 SR-06
C5 OPS-10
C5 OPS-12 (Gap: No Gap)
- **eu_ai_act**: Article 12 (d)
Article 21 (2)
Article 22 (3c)
Article 59 (1)(h) (Gap: Partial Gap)
- **iso_42001**: 42001: A.2.3 - Alignment with other organizational policies
42001: A.2.4 - Review of the AI policy
27001: A.5.1 - Policies for information security
27001 A.8.3 - Information access restriction
27001 A.5.18 - Access rights
27001.A.5.33 - Protection of records (Gap: No Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **IAM-12.1**: Are processes, procedures, and technical measures defined, implemented, evaluated to ensure the logging infrastructure is read-only for all with write access, including privileged access roles, and that the ability to disable it, is controlled through a procedure that ensures the segregation of duties and break glass procedures?

---

## IAM-13: Uniquely Identifiable Users

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Data poisoning, Sensitive data disclosure, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Owned by the Cloud Service Provider (CSP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Application: Shared Application Provider-AI Customer (Shared AP-AIC)

**Lifecycle Relevance:**
- Preparation: Data collection, Resource provisioning
- Development: Design, Supply Chain
- Evaluation/Validation: Validation/Red Teaming
- Deployment: AI Services supply chain
- Delivery: Operations, Maintenance
- Service Retirement: Archiving, Data deletion, Model disposal

### Specification

Define, implement and evaluate processes, procedures and technical measures, that ensure identities’ activities are identifiable through uniquely associated IDs.

### Cross-References

- **bsi_aic4**: C4 DM-02
C5 IDM-01
C5 ISM-02 (Gap: No Gap)
- **eu_ai_act**: Article 9
Article 14
Article 15
Article 17
Annex IV (Gap: Partial Gap)
- **iso_42001**: 42001: A.2.3 - Alignment with other organizational policies
42001: A.2.4 - Review of the AI policy
27001: A.5.1 - Policies for information security
27001:A.5.16 - Identity management (Gap: No Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **IAM-13.1**: Are processes, procedures, and technical measures, that ensure identities’ activities are identifiable through uniquely associated IDs, defined, implemented, and evaluated?

---

## IAM-14: Strong Authentication

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Sensitive data disclosure, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Owned by the Cloud Service Provider (CSP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Application: Shared Application Provider-AI Customer (Shared AP-AIC)

**Lifecycle Relevance:**
- Preparation: Data collection, Resource provisioning
- Development: Design, Supply Chain, Guardrails
- Evaluation/Validation: Validation/Red Teaming
- Deployment: Orchestration, AI Services supply chain
- Delivery: Operations, Maintenance
- Service Retirement: Archiving, Data deletion, Model disposal

### Specification

Define, implement and evaluate processes, procedures and technical measures for authenticating access to systems, application and data assets, including multifactor authentication for at least privileged user and sensitive data access. Adopt digital certificates or alternatives which achieve an equivalent level of security for system identities.

### Cross-References

- **bsi_aic4**: C4 SR-06
C5 IDM-09
C5 PSS-05 (Gap: No Gap)
- **eu_ai_act**: Article 9
Article 10
Article 15
Article 17
Annex IV (Gap: Partial Gap)
- **iso_42001**: 42001: A.2.3 - Alignment with other organizational policies
42001: A.2.4 - Review of the AI policy
27001: A.5.1 - Policies for information security
27001:A.5.17 - Authentication information (Gap: No Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **IAM-14.1**: Are processes, procedures, and technical measures defined, implemented, and evaluated for authenticating access to systems, applications, and data assets, including multifactor authentication for at least privileged user and sensitive data access?
- **IAM-14.2**: Are digital certificates or alternatives adopted that achieve an equivalent level of security for system identities?

---

## IAM-15: Passwords and Secrets Management

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Sensitive data disclosure, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Owned by the Cloud Service Provider (CSP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Shared Application Provider-AI Customer (Shared AP-AIC)

**Lifecycle Relevance:**
- Preparation: Data collection, Resource provisioning
- Development: Design, Guardrails, Supply Chain
- Evaluation/Validation: Validation/Red Teaming
- Deployment: AI Services supply chain, Orchestration
- Delivery: Maintenance, Operations
- Service Retirement: N/A

### Specification

Define, implement and evaluate processes, procedures and technical measures for the secure management of passwords and other secrets.

### Cross-References

- **bsi_aic4**: C4 SR-06
C5 IDM-08
C5 IDM-09 (Gap: No Gap)
- **eu_ai_act**: Article 9
Article 11
Article 15
Article 16
Article 29 (Gap: No Gap)
- **iso_42001**: 42001: A.2.3 - Alignment with other organizational policies
42001: A.2.4 - Review of the AI policy
27001: A.5.1 - Policies for information security
27001: A.8.5 - Secure authentication (Gap: No Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **IAM-15.1**: Are processes, procedures, and technical measures defined, implemented, and evaluated for the secure management of passwords and other secrets?

---

## IAM-16: Authorization Mechanisms

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Shared Application Provider-AI Customer (Shared AP-AIC)

**Lifecycle Relevance:**
- Preparation: Resource provisioning, Team and expertise
- Development: Design, Supply Chain, Training, Guardrails
- Evaluation/Validation: Validation/Red Teaming, Evaluation
- Deployment: AI Services supply chain, Orchestration, AI applications
- Delivery: Operations, Maintenance
- Service Retirement: Archiving, Data deletion, Model disposal

### Specification

Define, implement and evaluate processes, procedures and technical measures to verify access to data and system functions is authorized.

### Cross-References

- **bsi_aic4**: C4 DM-02
C4 SR-06
C5 PSS-09 (Gap: No Gap)
- **eu_ai_act**: Article 9
Article 15
Article 16
Article 17
Article 29 (Gap: Partial Gap)
- **iso_42001**: 42001: A.2.3 - Alignment with other organizational policies
42001: A.2.4 - Review of the AI policy
27001: A.5.1 - Policies for information security
27001: A.5.15 - Access control (Gap: No Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **IAM-16.1**: Are processes, procedures, and technical measures defined, implemented, and evaluated to verify access to data and system functions are authorized?

---

## IAM-17: Knowledge Access Control - Need to Know

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared across the supply chain
- Model: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Shared Application Provider-AI Customer (Shared AP-AIC)

**Lifecycle Relevance:**
- Preparation: Data collection, Data curation, Data storage, Resource provisioning
- Development: Design, Supply Chain
- Evaluation/Validation: Validation/Red Teaming, Evaluation, Re-evaluation
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Archiving, Data deletion, Model disposal

### Specification

Define policy and procedure for "need to know" access to knowledge, information and data within the organization and in the context of the AI system to be applied when regulating access to resources.

### Cross-References

- **bsi_aic4**: C4 DM-01
C4 DM-02
C5 PSS-08 (Gap: No Gap)
- **eu_ai_act**: Article 9
Article 11
Article 15
Article 16
Article 29 (Gap: Partial Gap)
- **iso_42001**: 42001 B.3.2 - AI roles and responsibilities
27001 A.8.3 - Information access restriction (Gap: No Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **IAM-17.1**: Are policies and procedures defined for "need to know" access to knowledge, information and data within the organization and in the context of the AI system to be applied when regulating access to resources?

---

## IAM-18: Output Modification and Special Authorization

**Type:** control
**Control Type:** AI-Specific
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Insecure supply chain, Insecure apps/plugins, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Owned by the Cloud Service Provider (CSP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Owned by the Orchestrated Service Provider (OSP)
- Application: Shared Application Provider-AI Customer (Shared AP-AIC)

**Lifecycle Relevance:**
- Preparation: Resource provisioning, Data collection
- Development: Supply Chain, Design
- Evaluation/Validation: Evaluation, Validation/Red Teaming
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance
- Service Retirement: Archiving, Data deletion, Model disposal

### Specification

When allowing model output modification of AI generated output, establish a role for this access and allow changes only by authorized identities.

### Cross-References

- **bsi_aic4**: C4 DM-02
C4 RE-02 (Gap: No Gap)
- **eu_ai_act**: Article 9
Article 14
Article 15
Article 16
Article 17
Annex IV (Gap: Partial Gap)
- **iso_42001**: 42001:  A.3.2 / B.3.2
42001:  A.2.4 / B.2.4
27001: A.5.18
27001: A.8.3
27001: A.8.32 (Gap: No Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **IAM-18.1**: Are role for access when allowing model output modification of AI-generated output established to ensure changes are made only by authorized identities?

---

## IAM-19: Agent Access Restriction

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Sensitive data disclosure, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Orchestrated Service Provider-Application Provider (Shared OSP-AP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: N/A
- Development: Design, Guardrails
- Evaluation/Validation: Validation/Red Teaming
- Deployment: Orchestration, AI applications
- Delivery: Operations, Continuous monitoring
- Service Retirement: N/A

### Specification

Restrict agents' access to the tools and plugins necessary for the activity or use case at hand, ensuring adherence to the principles of need-to-know and least privilege.

### Cross-References

- **bsi_aic4**: C4 DM-01
DM-02 (Gap: Partial Gap)
- **eu_ai_act**: No Mapping (Gap: Full Gap)
- **iso_42001**: 27001: A.5.15 — Access Control Policy
27001: A.5.18 — Access Rights
27002: 8.1 – User Access Management
27002: 8.2 – Privileged Access Rights
27002: 8.3 – Information Access Restriction
27002: 5.15 – Segregation of Duties
42001: 8.5 – Operational Control of AI Systems
42001: 8.6 – AI System Access Control
42001: 6.2 – Risk Identification for AI (Gap: No Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **IAM-19.1**: Are agents' access to the tools and plugins necessary for the activity or use case at hand, restricted to ensure adherence to the principles of need-to-know and least privilege?

---

# Domain: Interoperability & Portability

## IPY-01: Interoperability and Portability Policy and Procedures

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Network, Compute, Storage, Application, Data
**Threat Categories:** Sensitive data disclosure, Insecure apps/plugins, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Orchestrated Service Provider-Application Provider (Shared OSP-AP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data collection, Data curation, Data storage
- Development: Design, Training
- Evaluation/Validation: Validation/Red Teaming
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: N/A

### Specification

Establish, document, approve, communicate, apply, evaluate and maintain policies and procedures for interoperability and portability including requirements for: a. Communications between application interfaces b. Information processing interoperability c. Application development portability d. Information/Data exchange, usage, portability, integrity, and persistence Review and update the policies and procedures at least annually or upon significant changes.

### Cross-References

- **bsi_aic4**: C4 PC-02
C5 PI-01 (Gap: No Gap)
- **eu_ai_act**: Article 11 (1)
Annex IV (1) (b)
Article 50 (2)
Article 53 (1) (b)
Annex XI (2) (3) (Gap: Partial Gap)
- **iso_42001**: 42001: B.8.2 (Gap: No Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **IPY-01.1**: Are interoperability and portability policies and procedures established, documented, approved, communicated, evaluated, and maintained, including requirements for:

a. Communications between application interfaces
b. Information processing interoperability
c. Application development portability
d. Information/Data exchange, usage, portability, integrity, and persistence?
- **IPY-01.2**: Are interoperability and portability policies and procedures reviewed and updated at least annually or upon significant changes?

---

## IPY-02: Application Interface Availability

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Network, Compute, Storage, Application, Data
**Threat Categories:** Sensitive data disclosure, Insecure apps/plugins, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data storage
- Development: N/A
- Evaluation/Validation: N/A
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring
- Service Retirement: Data deletion

### Specification

Provide application interface(s) to AICs so that they programmatically retrieve their data to enable interoperability and portability.

### Cross-References

- **bsi_aic4**: C4 PC-02
C5 PI-01 (Gap: Partial Gap)
- **eu_ai_act**: No Mapping (Gap: Full Gap)
- **iso_42001**: 42001: B.8.2 (Gap: Partial Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **IPY-02.1**: Are application interface(s) to AICs provided so that they programmatically retrieve their data to enable interoperability and portability?

---

## IPY-03: Secure Interoperability and Portability Management

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Network, Storage, Data
**Threat Categories:** Data poisoning, Sensitive data disclosure, Insecure apps/plugins, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Orchestrated Service Provider-Application Provider (Shared OSP-AP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data collection, Data curation, Data storage
- Development: Training
- Evaluation/Validation: Evaluation, Validation/Red Teaming, Re-evaluation
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Data deletion

### Specification

Implement cryptographically secure and standardized network protocols for the management, import and export of data, according to industry standards.

### Cross-References

- **bsi_aic4**: C4 SR-06
C5 PI-01
C5 CRY-02 (Gap: No Gap)
- **eu_ai_act**: No Mapping (Gap: Full Gap)
- **iso_42001**: 42001: Annex A
42001: A.7
42001: B.7.3 (Gap: Partial Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **IPY-03.1**: Are cryptographically secure and standardized network protocols implemented for the management, import, and export of data, according to industry standards?

---

## IPY-04: Data Portability Contractual Obligations

**Type:** control
**Control Type:** Cloud-Specific
**Architectural Relevance:** Network, Storage, Data
**Threat Categories:** Insecure apps/plugins, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Owned by the Cloud Service Provider (CSP)
- Model: Owned by the Cloud Service Provider (CSP)
- Orchestrated Services: Owned by the Orchestrated Service Provider (OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data storage
- Development: N/A
- Evaluation/Validation: N/A
- Deployment: N/A
- Delivery: N/A
- Service Retirement: Data deletion

### Specification

Agreements must include provisions specifying AICs access to data upon contract termination and will include: a. Data format b. Length of time the data will be stored c. Scope of the data retained and made available to the AICs d. Data deletion policy

### Cross-References

- **bsi_aic4**: C4 DM-02
C4 PF-03
C5 PI-02 (Gap: Partial Gap)
- **eu_ai_act**: Article 11 (1)
Annex IV
Article 17 (1) (f)
Article 25 (4)
Article 50 (2)
Article 53 (1) (b)
Annex XII
Annex XI Section 1 (1) (e)
Annex XII (1) (g) (Gap: Partial Gap)
- **iso_42001**: 42001: A.10.2 - Allocating responsibilities
42001: B.10.2 - Allocating responsibilities
42001: A.10.4  - customers
42001: B.10.4  - customers (Gap: Partial Gap)
- **nist_ai_600_1**: GV-6.1-004
GV-6.2-007 (Gap: Partial Gap)

### CAIQ Questions

- **IPY-04.1**: Are agreements including provisions specifying AICs access to data upon contract termination, including:
a. Data format
b. Length of time the data will be stored
c. Scope of the data retained and made available to the AICs
d. Data deletion policy?

---

# Domain: Infrastructure Security

## I&S-01: Infrastructure and Virtualization Security Policy and Procedures

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage
**Threat Categories:** Sensitive data disclosure, Model/Service Failure, Insecure supply chain, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared across the supply chain
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Shared Orchestrated Service Provider-Application Provider (Shared OSP-AP)

**Lifecycle Relevance:**
- Preparation: Data storage, Resource provisioning
- Development: Training
- Evaluation/Validation: N/A
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring
- Service Retirement: Data deletion

### Specification

Establish, document, approve, communicate, apply, evaluate and maintain policies and procedures for infrastructure and virtualization security. Review and update the policies and procedures at least annually,  or upon significant changes.

### Cross-References

- **bsi_aic4**: C4 SR-06
C5 SP-01
C5 SP-02 (Gap: No Gap)
- **eu_ai_act**: No Mapping (Gap: Full Gap)
- **iso_42001**: ISO/IEC 42001:2023 - B.2.2
B.2.4
ISO/IEC 42001:2023 - 8.3.1
ISO/IEC 42001:2023 - 9.1
ISO/IEC 42001:2023 - 10.1
ISO/IEC 27001:2022 - A.5.1
A.8.27
A.8.9
ISO/IEC 27002 - 8.28 (Gap: No Gap)
- **nist_ai_600_1**: GV-4.1-001
Appendix A.1.2 (Gap: Partial Gap)

### CAIQ Questions

- **I&S-01.1**: Has the organization established, documented, approved, communicated, applied, evaluated, and maintained policies and procedures for infrastructure and virtualization security?
- **I&S-01.2**: Are these policies and procedures reviewed and updated at least annually, or upon significant changes?

---

## I&S-02: Capacity and Resource Planning

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage
**Threat Categories:** Model/Service Failure, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Shared Orchestrated Service Provider-Application Provider (Shared OSP-AP)

**Lifecycle Relevance:**
- Preparation: Data storage, Resource provisioning
- Development: Training
- Evaluation/Validation: Re-evaluation, Evaluation
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Continuous monitoring, Continuous improvement
- Service Retirement: N/A

### Specification

Plan and monitor the availability, quality, and adequate capacity of resources in order to deliver the required system performance as determined by the business.

### Cross-References

- **bsi_aic4**: C4 RE-01
C4 BC-03
C4 PF-01
C5 OPS-01
C5 OPS-02 (Gap: No Gap)
- **eu_ai_act**: No Mapping (Gap: Full Gap)
- **iso_42001**: ISO/IEC 42001:2023 - B.4.2 (Gap: No Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **I&S-02.1**: Are availability, quality and the adequate capacity of resources, being planned and monitored in order to deliver the required system performance as determined by the business?

---

## I&S-03: Network Security

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Network, Application
**Threat Categories:** Sensitive data disclosure, Model/Service Failure, Insecure supply chain, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared across the supply chain
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Shared Orchestrated Service Provider-Application Provider (Shared OSP-AP)

**Lifecycle Relevance:**
- Preparation: Data storage, Resource provisioning
- Development: Guardrails
- Evaluation/Validation: N/A
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring
- Service Retirement: N/A

### Specification

Monitor, encrypt and restrict communications between environments to only authenticated and authorized connections, as justified by the  business. Review these configurations at least annually, and support them by a  documented justification of all allowed services, protocols, ports, and  compensating controls.

### Cross-References

- **bsi_aic4**: C4 SR-06
C5 COS-02 (Gap: No Gap)
- **eu_ai_act**: No Mapping (Gap: Full Gap)
- **iso_42001**: ISO/IEC 27001: A.5.15
A.8.24
A.8.27
A.5.35
ISO/IEC 27002: 8.28
8.7
9.4
5.17
10.1 (Gap: Partial Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **I&S-03.1**: Are communications between environments being monitored, encrypted, and restricted to only authenticated and authorized connections, as justified by the business?
- **I&S-03.2**: Are these configurations reviewed at least annually and supported by a documented justification of all allowed services, protocols, ports, and compensating controls?

---

## I&S-04: OS Hardening and Base Controls

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Compute, Storage, Application
**Threat Categories:** Sensitive data disclosure, Model/Service Failure, Insecure supply chain, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared across the supply chain
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Shared Orchestrated Service Provider-Application Provider (Shared OSP-AP)

**Lifecycle Relevance:**
- Preparation: Data storage, Resource provisioning
- Development: Training
- Evaluation/Validation: N/A
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Data deletion

### Specification

Harden host and guest OS, hypervisor or infrastructure control plane, according to their respective best practices, and supported by  technical controls, as part of a security baseline.

### Cross-References

- **bsi_aic4**: C4 SR-06
C5 OPS-23 (Gap: No Gap)
- **eu_ai_act**: Article 15 (Gap: Partial Gap)
- **iso_42001**: No Mapping for ISO 42001
ISO/IEC 27001:2022 - A.8.9 (Configuration management) (Gap: Partial Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **I&S-04.1**: Are the host and guest OS, hypervisor, or infrastructure control plane, being hardened according to their respective best practices and supported by technical controls as part of a security baseline?

---

## I&S-05: Production and Non-Production Environments

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Sensitive data disclosure, Model/Service Failure, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Orchestrated Service Provider-Application Provider (Shared OSP-AP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data storage, Resource provisioning
- Development: Training, Design, Guardrails
- Evaluation/Validation: Validation/Red Teaming, Re-evaluation
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Data deletion

### Specification

Separate production and non-production environments.

### Cross-References

- **bsi_aic4**: C4 PF-05
C4 DQ-06
C4 SR-06
C5 DEV-10 (Gap: No Gap)
- **eu_ai_act**: No Mapping (Gap: Full Gap)
- **iso_42001**: ISO/IEC 42001:2023 - No mapping
ISO/IEC 27001:2022 - A.8.31
ISO/IEC 27001:2022 - 8.27
ISO/IEC 27002 - 8.28 (Gap: Partial Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **I&S-05.1**: Are production and non-production environments kept separate?

---

## I&S-06: Segmentation and Segregation

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Network, Compute, Storage, Application, Data
**Threat Categories:** Sensitive data disclosure, Model/Service Failure, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Shared Orchestrated Service Provider-Application Provider (Shared OSP-AP)

**Lifecycle Relevance:**
- Preparation: Data storage, Resource provisioning
- Development: Design, Guardrails
- Evaluation/Validation: Validation/Red Teaming, Re-evaluation
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: N/A

### Specification

Design, develop, deploy and configure applications and infrastructures  such that tenant access is appropriately segmented and segregated,  monitored and restricted.

### Cross-References

- **bsi_aic4**: C4 DM-02
C4 SR-06
C5 OPS-24
C5 COS-06 (Gap: No Gap)
- **eu_ai_act**: Article 15 (Gap: Partial Gap)
- **iso_42001**: 42001: 6.3.2 – Planning of AI-specific controls
42001: 8.2.2 – Operational control
42001: 9.1 / 10.2 – Monitoring and corrective action
ISO/IEC 27001:2022 - A.8.22
ISO/IEC 27001:2022 - A.8.27 – Segregation of environments
27002: 8.28 – Secure development and test environments
27002: 9.4 – Access control
27002: 5.9 – Segregation in networks
27002: 5.17 / 5.18 – Monitoring and logging
27002: 5.13 / 5.14 – Infrastructure hardening (Gap: Partial Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **I&S-06.1**: Are applications and infrastructures designed, developed, deployed and configured such that tenant access is appropriately segmented, segregated, monitored, and restricted from other tenants?

---

## I&S-07: Migration to Hosted Environments

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Network, Compute, Storage, Application, Data
**Threat Categories:** Sensitive data disclosure, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Owned by the Cloud Service Provider (CSP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data storage, Resource provisioning
- Development: Design
- Evaluation/Validation: N/A
- Deployment: Orchestration, AI applications
- Delivery: Operations
- Service Retirement: N/A

### Specification

Use secure and encrypted communication channels when migrating  servers, services, applications, or data to hosted environments.  Such channels must include only up-to-date and approved protocols.

### Cross-References

- **bsi_aic4**: C4 SR-06
C5 CRY-02
C5 COS-05 (Gap: No Gap)
- **eu_ai_act**: No Mapping (Gap: Full Gap)
- **iso_42001**: No Mapping for ISO 42001
ISO/IEC 27001:2022 - A.5.23
27002: 8.25
27002: 8.9
27002: 10.1 (Gap: Partial Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **I&S-07.1**: Are secure and encrypted communication channels used when migrating servers, services, applications or data to hosted environments?
- **I&S-07.2**: Are such channels including only up-to-date and approved protocols?

---

## I&S-08: Network Architecture Documentation

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Network, Compute, Application, Data
**Threat Categories:** Sensitive data disclosure, Model/Service Failure, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Owned by the Cloud Service Provider (CSP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Resource provisioning, Data storage
- Development: N/A
- Evaluation/Validation: N/A
- Deployment: Orchestration, AI applications, AI Services supply chain
- Delivery: Operations, Continuous monitoring, Maintenance
- Service Retirement: N/A

### Specification

Identify and document high-risk environments.

### Cross-References

- **bsi_aic4**: C4 SR-02
C5 AM-06
C5 COS-07
C5 BCM-02 (Gap: No Gap)
- **eu_ai_act**: Article 11 (Gap: No Gap)
- **iso_42001**: ISO/IEC 42001:2023 - B.6.2.3
ISO/IEC 42001:2023  A.5.12 / 5.13
ISO/IEC 42001:2023 A.8.22
ISO/IEC 42001:2023  9.1
ISO/IEC 42001:2023 Clause 6.1.2;
27001 A.5.4
27001 A.5.9
A.8.9; Inventory and classification of environments
27001 A.5.35
27002 5.9
27002 8.28
27002 5.17 Documentation and review of controls for sensitive or critical areas (Gap: No Gap)
- **nist_ai_600_1**: Appendix A.1.2 (Gap: Partial Gap)

### CAIQ Questions

- **I&S-08.1**: Are high-risk environments identified and documented?

---

## I&S-09: Network Defense

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Network, Compute, Application, Data
**Threat Categories:** Sensitive data disclosure, Model/Service Failure, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared across the supply chain
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data storage, Resource provisioning
- Development: Training
- Evaluation/Validation: Validation/Red Teaming
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Data deletion

### Specification

Define, implement and evaluate processes, procedures and  defense-in-depth techniques for protection, detection, and timely  response to network-based attacks.

### Cross-References

- **bsi_aic4**: C4 SR-06
C4 SR-07
C5 COS-01 (Gap: No Gap)
- **eu_ai_act**: Article 15 (Gap: Partial Gap)
- **iso_42001**: No Mapping for ISO 42001
ISO/IEC 27001:2022 - A.8.16
A.8.20 (Gap: Partial Gap)
- **nist_ai_600_1**: MP-2.3-005
MP-2.2-002 (Gap: Partial Gap)

### CAIQ Questions

- **I&S-09.1**: Are processes, procedures, and defense-in-depth techniques for the protection, detection, and timely response to network-based attacks, defined, implemented and evaluated?

---

# Domain: Logging and Monitoring

## LOG-01: Logging and Monitoring Policy and Procedures

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Sensitive data disclosure, Model/Service Failure, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data collection, Data curation, Data storage, Resource provisioning, Team and expertise
- Development: Training
- Evaluation/Validation: Evaluation, Validation/Red Teaming, Re-evaluation
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Archiving, Data deletion

### Specification

Establish, document, approve, communicate, apply, evaluate and  maintain policies and procedures for logging and monitoring. Review  and update the policies and procedures at least annually, or upon significant changes.

### Cross-References

- **bsi_aic4**: C4 PC-02
C5 OPS-10 (Gap: No Gap)
- **eu_ai_act**: Article 17 (1) (Gap: Partial Gap)
- **iso_42001**: ISO 42001 A.2.2
ISO 42001 A.2.4
ISO 27001 A.5.1 (Gap: Partial Gap)
- **nist_ai_600_1**: GV-4.1-001
MG-4.1-002
MG-4.3-002
MG-3.2-006 (Gap: No Gap)

### CAIQ Questions

- **LOG-01.1**: Are logging and monitoring policies and procedures established, documented, approved, communicated, applied, evaluated, and maintained?
- **LOG-01.2**: Are policies and procedures reviewed, approved and updated at least annually, or upon significant changes?

---

## LOG-02: Audit Logs Protection

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Sensitive data disclosure, Model/Service Failure, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data storage
- Development: Training
- Evaluation/Validation: Evaluation, Validation/Red Teaming, Re-evaluation
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Archiving, Data deletion, Model disposal

### Specification

Define, implement and evaluate processes, procedures and technical measures to ensure the security and retention of audit logs.

### Cross-References

- **bsi_aic4**: C4 PC-02
C4 CM-02
C5 OPS-12
C5 OPS-13
C5 OPS-14 (Gap: No Gap)
- **eu_ai_act**: Article 12
Article 13
Article 26 (Gap: Partial Gap)
- **iso_42001**: ISO 42001 A.6.2.8
ISO 27001 A.8.15 (Gap: No Gap)
- **nist_ai_600_1**: MP-2.3-003
GV-1.5-003
MP-4.1-005
MG-2.2-007 (Gap: Partial Gap)

### CAIQ Questions

- **LOG-02.1**: Are processes, procedures, and technical measures defined, implemented, and evaluated to ensure audit log security and retention?

---

## LOG-03: Security Monitoring and Alerting

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Sensitive data disclosure, Model/Service Failure, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data storage, Resource provisioning
- Development: Guardrails
- Evaluation/Validation: Validation/Red Teaming, Re-evaluation
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Archiving, Data deletion

### Specification

Identify and monitor security-related events within applications,  the underlying infrastructure, supply chain, and consider logging  other events based on risk evaluation. Define and implement a  system to generate alerts to responsible stakeholders based on such  events and corresponding metrics.

### Cross-References

- **bsi_aic4**: C4 RE-01
C4 RE-02
C4 BC-04
C5 OPS-13
C5 OPS-15 (Gap: No Gap)
- **eu_ai_act**: Article 15
Article 72 (1)
Article 72 (2) (Gap: No Gap)
- **iso_42001**: ISO 42001 A.6.2.6
ISO 27001 A.8.16 (Gap: No Gap)
- **nist_ai_600_1**: MG-3.2-006
MG-4.1-002
GV-1.5-001
GV-6.2-004
MP-4.1-001 (Gap: No Gap)

### CAIQ Questions

- **LOG-03.1**: Are security-related events within applications, the underlying infrastructure, and the supply chain being identified and monitored, and are other events being logged based on risk evaluation?
- **LOG-03.2**: Is a system to generate alerts, defined and implemented, to responsible stakeholders based on security-related events and corresponding metrics?

---

## LOG-04: Audit Logs Access and Accountability

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Sensitive data disclosure, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data storage, Team and expertise
- Development: Guardrails
- Evaluation/Validation: Re-evaluation, Validation/Red Teaming
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring
- Service Retirement: Archiving, Data deletion

### Specification

Restrict access to audit logs and maintain records of access to logs.

### Cross-References

- **bsi_aic4**: C4 DM-02
C5 OPS-12 (Gap: No Gap)
- **eu_ai_act**: Article 17 (1) (Gap: Partial Gap)
- **iso_42001**: No Mapping for ISO 42001
ISO 27001 A.5.33 (Gap: Partial Gap)
- **nist_ai_600_1**: GV-3.2-003 (Gap: Full Gap)

### CAIQ Questions

- **LOG-04.1**: Is access to audit logs restricted and are the records of access logs maintained?

---

## LOG-05: Audit Logs Monitoring and Response

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Sensitive data disclosure, Model/Service Failure, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data storage, Resource provisioning
- Development: Guardrails
- Evaluation/Validation: Re-evaluation, Validation/Red Teaming
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Continuous monitoring, Continuous improvement
- Service Retirement: N/A

### Specification

Monitor security audit logs to detect activity outside of typical or expected patterns. Establish and follow a defined process to review and take appropriate and timely actions on detected anomalies.

### Cross-References

- **bsi_aic4**: C4 SR-06
C5 OPS-13 (Gap: No Gap)
- **eu_ai_act**: Article 14 (4)
Article 72 (1)
Article 72 (2) (Gap: Partial Gap)
- **iso_42001**: No Mapping for ISO 42001
ISO 27001 A.8.16 (Gap: Partial Gap)
- **nist_ai_600_1**: GV-2.1-001
GV-6.1-005
GV-6.1-009
GV-6.2-004
MP-4.1-001
MS-2.6-005
MG-4.1-006
MG-4.1-007 (Gap: Partial Gap)

### CAIQ Questions

- **LOG-05.1**: Are security audit logs monitored to detect activity outside of typical or expected patterns?
- **LOG-05.2**: Is a process, on reviewing and taking appropriate and timely actions on detected anomalies, defined, established and followed?

---

## LOG-06: Clock Synchronization

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Model/Service Failure, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared across the supply chain
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Shared Orchestrated Service Provider-Application Provider (Shared OSP-AP)

**Lifecycle Relevance:**
- Preparation: Data collection, Data curation, Data storage, Resource provisioning
- Development: Design, Training
- Evaluation/Validation: Evaluation, Validation/Red Teaming, Re-evaluation
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Archiving, Data deletion, Model disposal

### Specification

Use a reliable time source across all relevant information processing systems.

### Cross-References

- **bsi_aic4**: C4 PC-02
C5 OPS-10 (Gap: Partial Gap)
- **eu_ai_act**: No Mapping (Gap: Full Gap)
- **iso_42001**: No Mapping for ISO 42001
ISO 27001 A.8.17 (Gap: Partial Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **LOG-06.1**: Is a reliable time source being used across all relevant information processing systems?

---

## LOG-07: Logging Scope

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Sensitive data disclosure, Model/Service Failure, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data collection, Data curation, Data storage, Resource provisioning
- Development: Design, Training, Guardrails
- Evaluation/Validation: Evaluation, Validation/Red Teaming, Re-evaluation
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Data deletion

### Specification

Establish, document and implement which information meta/data  system events should be logged. Review and update the scope at  least annually or whenever there is a change in the threat environment.

### Cross-References

- **bsi_aic4**: C4 PC-02
C5 OPS-10
C5 OPS-11 (Gap: No Gap)
- **eu_ai_act**: Article 12 (Gap: Partial Gap)
- **iso_42001**: ISO 42001 A.6.2.8 (Gap: Partial Gap)
- **nist_ai_600_1**: GV-1.5-001
MG-4.2-001 (Gap: Partial Gap)

### CAIQ Questions

- **LOG-07.1**: Are information metadata system events that should be logged, established, documented, and implemented?
- **LOG-07.2**: Is the scope reviewed and updated at least annually, or whenever there is a change in the threat environment?

---

## LOG-08: Log Records

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Sensitive data disclosure, Model/Service Failure, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data storage
- Development: Training, Guardrails
- Evaluation/Validation: Evaluation, Validation/Red Teaming, Re-evaluation
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Archiving, Data deletion, Model disposal

### Specification

Generate audit records containing relevant security information.

### Cross-References

- **bsi_aic4**: C4 RE-02
C5 OPS-15 (Gap: No Gap)
- **eu_ai_act**: Article 12 (2) (Gap: No Gap)
- **iso_42001**: ISO 42001 A.6.2.6
ISO 27001 A.8.16 (Gap: No Gap)
- **nist_ai_600_1**: MP-2.3-003 (Gap: Partial Gap)

### CAIQ Questions

- **LOG-08.1**: Are audit records generated, and do they contain relevant security information?

---

## LOG-09: Log Protection

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Sensitive data disclosure, Model/Service Failure, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data storage
- Development: Training
- Evaluation/Validation: Evaluation, Validation/Red Teaming, Re-evaluation
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Archiving, Data deletion, Model disposal

### Specification

Protect audit records from unauthorized access, modification, and  deletion.

### Cross-References

- **bsi_aic4**: C4 DM-02
C4 SR-06
C5 OPS-12
C5 OPS-14
C5 OPS-16 (Gap: No Gap)
- **eu_ai_act**: No Mapping (Gap: Full Gap)
- **iso_42001**: ISO 42001 7.5.3
ISO 42001 B.6.2.8
ISO 27001 A.5.37
ISO 27002 A.8.15 (Gap: No Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **LOG-09.1**: Is the audit records protected from unauthorized access, modification, and deletion?

---

## LOG-10: Encryption Monitoring and Reporting

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Sensitive data disclosure, Insecure apps/plugins, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data storage
- Development: Training
- Evaluation/Validation: Re-evaluation
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Archiving, Data deletion, Model disposal

### Specification

Establish and maintain a monitoring and internal reporting capability over the operations of cryptographic, encryption and key management  policies, processes, procedures, and controls.

### Cross-References

- **bsi_aic4**: C4 PC-02
C5 CRY-01 (Gap: No Gap)
- **eu_ai_act**: No Mapping (Gap: Full Gap)
- **iso_42001**: No Mapping for ISO 42001
ISO 27001 8.24
ISO 27001 9.1
ISO 27001 9.2 (Gap: Partial Gap)
- **nist_ai_600_1**: MG-3.2-002 (Gap: Full Gap)

### CAIQ Questions

- **LOG-10.1**: Are monitoring and internal reporting capabilities established to report on  cryptographic operations, encryption, and key management policies, processes,  procedures, and controls?

---

## LOG-11: Transaction/Activity Logging

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Sensitive data disclosure, Model/Service Failure, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Shared Orchestrated Service Provider-Application Provider (Shared OSP-AP)

**Lifecycle Relevance:**
- Preparation: Data storage
- Development: Training
- Evaluation/Validation: Re-evaluation
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Archiving

### Specification

Log and monitor key lifecycle management events to enable auditing and reporting on usage of cryptographic keys.

### Cross-References

- **bsi_aic4**: C4 DM-03
C4 RE-02
C5 CRY-04 (Gap: No Gap)
- **eu_ai_act**: No Mapping (Gap: Full Gap)
- **iso_42001**: No Mapping for ISO 42001
ISO 27001 8.24
ISO 27001 9.1
ISO 27001 9.2 (Gap: Partial Gap)
- **nist_ai_600_1**: MP-2.3-003 (Gap: Partial Gap)

### CAIQ Questions

- **LOG-11.1**: Are key lifecycle management events logged and monitored to enable auditing and reporting on cryptographic keys' usage?

---

## LOG-12: Access Control Logs

**Type:** control
**Control Type:** Cloud-Specific
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Sensitive data disclosure, Model/Service Failure, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Owned by the Cloud Service Provider (CSP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Shared Orchestrated Service Provider-Application Provider (Shared OSP-AP)

**Lifecycle Relevance:**
- Preparation: Data storage, Resource provisioning
- Development: Design, Training, Guardrails, Supply Chain
- Evaluation/Validation: Evaluation, Validation/Red Teaming, Re-evaluation
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Archiving, Data deletion, Model disposal

### Specification

Monitor and log physical access using an auditable access  control system.

### Cross-References

- **bsi_aic4**: C4 DM-02
C5 PS-04 (Gap: No Gap)
- **eu_ai_act**: No Mapping (Gap: Full Gap)
- **iso_42001**: No Mapping for ISO 42001
ISO 27001 A.7 (Gap: Partial Gap)
- **nist_ai_600_1**: MG-3.2-008 (Gap: Full Gap)

### CAIQ Questions

- **LOG-12.1**: Is physical access logged and monitored using an auditable access control system?

---

## LOG-13: Failures and Anomalies Reporting

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Application, Data
**Threat Categories:** Model/Service Failure, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Shared Orchestrated Service Provider-Application Provider (Shared OSP-AP)

**Lifecycle Relevance:**
- Preparation: Data collection, Data curation, Data storage, Resource provisioning, Team and expertise
- Development: Design, Training, Guardrails, Supply Chain
- Evaluation/Validation: Evaluation, Validation/Red Teaming, Re-evaluation
- Deployment: AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Archiving, Data deletion, Model disposal

### Specification

Define, implement and evaluate processes, procedures and technical measures for the reporting of anomalies and failures of the monitoring  system and provide immediate notification to the accountable party.

### Cross-References

- **bsi_aic4**: C4 SR-06
C5 OPS-17 (Gap: No Gap)
- **eu_ai_act**: No Mapping (Gap: Full Gap)
- **iso_42001**: ISO 42001 B.8.4
ISO 42001 B.8.5
ISO 27001 9.1
ISO 27001 9.2
ISO 27001 A.5.27 (Gap: No Gap)
- **nist_ai_600_1**: GV-4.3-002 (Gap: No Gap)

### CAIQ Questions

- **LOG-13.1**: Are processes and technical measures for reporting monitoring system anomalies and failures defined, implemented, and evaluated?
- **LOG-13.2**: Are accountable parties immediately notified about anomalies and failures?

---

## LOG-14: Input Monitoring

**Type:** control
**Control Type:** AI-Specific
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Sensitive data disclosure, Model/Service Failure, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Orchestrated Service Provider-Application Provider (Shared OSP-AP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data collection, Data curation, Data storage
- Development: Training
- Evaluation/Validation: Evaluation, Validation/Red Teaming, Re-evaluation
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Continuous monitoring, Continuous improvement
- Service Retirement: Data deletion

### Specification

Log and monitor all input events (content and metadata) to enable auditing and reporting on the usage of AI models.

### Cross-References

- **bsi_aic4**: C4 BC-03
C4 RE-02
C4 RE-03
C5 OPS-11
C5 PI-01 (Gap: No Gap)
- **eu_ai_act**: Article 13 (3)
Article 15 (5)
Article 26 (1)
Article 26 (4) (Gap: Partial Gap)
- **iso_42001**: ISO 42001 B.6.2.8
ISO 27001 A.5.37 (Gap: No Gap)
- **nist_ai_600_1**: MP-5.1-001 (Gap: No Gap)

### CAIQ Questions

- **LOG-14.1**: Are all input events (content and metadata) logged and monitored to enable auditing and reporting on the usage of AI models?

---

## LOG-15: Output Monitoring

**Type:** control
**Control Type:** AI-Specific
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Sensitive data disclosure, Model/Service Failure, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data storage
- Development: Guardrails
- Evaluation/Validation: Evaluation, Validation/Red Teaming, Re-evaluation
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Archiving, Data deletion

### Specification

Log and monitor all output events (content and metadata) to enable auditing and reporting on usage of AI models.

### Cross-References

- **bsi_aic4**: C4 BC-03
C4 RE-02
C4 RE-03
C5 OPS-11
C5 PI-01 (Gap: No Gap)
- **eu_ai_act**: Article 15 (5) (Gap: Partial Gap)
- **iso_42001**: ISO 42001 B.6.2.8
ISO 27001 A.5.37 (Gap: No Gap)
- **nist_ai_600_1**: MP-5.1-002 (Gap: No Gap)

### CAIQ Questions

- **LOG-15.1**: Are all output events (content and metadata) logged and monitored to enable auditing and reporting on the usage of AI models?

---

# Domain: Model Security

## MDS-01: Training Pipeline Security

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Owned by the Cloud Service Provider (CSP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data collection, Data curation, Data storage, Resource provisioning
- Development: Training, Supply Chain, Design
- Evaluation/Validation: Validation/Red Teaming
- Deployment: Orchestration
- Delivery: Operations, Maintenance
- Service Retirement: N/A

### Specification

Define, implement, and evaluate policies, procedures, and technical measures that ensure the security of the Training Pipeline. Regularly review and update policies, procedures and technical measures to address new security threats and best practices.

### Cross-References

- **bsi_aic4**: C4 PC-01
C4 SR-04
C4 SR-05
C5 SP-01
C5 SP-02 (Gap: No Gap)
- **eu_ai_act**: Article 15 (1)
Article 15 (5) (Gap: No Gap)
- **iso_42001**: ISO 42001 A.6.1.2 - Objectives for responsible development of AI system
ISO 42001 A.6.1.3 - Processes for responsible AI system design and development
IOS 42001 B.6.1.2 - Objectives for responsible development of AI system
IOS 42001 B.6.1.3 Processes for responsible design and development of AI system
IOS 42001 B.6.2.3 Documentation of AI system design and development (Gap: No Gap)
- **nist_ai_600_1**: MP-4.1-004
MS-1.1-007
MS-2.5-005
MS-2.10-003
MS-2.11-005 (Gap: No Gap)

### CAIQ Questions

- **MDS-01.1**: Are processes, procedures, and technical measures defined, implemented, and evaluated to ensure the security of the Training Pipeline?
- **MDS-01.2**: Are policies, procedures and technical measures to address new security threats and best practices regularly review and update?

---

## MDS-02: Model Artifact Scanning

**Type:** control
**Control Type:** AI-Specific
**Architectural Relevance:** Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Team and expertise
- Development: Design, Training, Supply Chain
- Evaluation/Validation: Evaluation, Validation/Red Teaming, Re-evaluation
- Deployment: AI Services supply chain, AI applications
- Delivery: Operations, Maintenance
- Service Retirement: Model disposal

### Specification

Define, implement, and evaluate policies, procedures, and technical measures for the scanning of model artifacts for vulnerabilities and attacks, at each step of the service lifecycle and at each hand over point. Regularly review and update policies, procedures and technical measures to address model artifact scanning.

### Cross-References

- **bsi_aic4**: C4 PC-01
C4 SR-05
C5 OPS-18
C5 SP-01
C5 SP-02 (Gap: No Gap)
- **eu_ai_act**: Article 15 (5) (Gap: No Gap)
- **iso_42001**: No Mapping for ISO 42001
27002 - 8.8 Management of technical vulnerabilities (Gap: Partial Gap)
- **nist_ai_600_1**: MP-2.3-005 (Gap: Partial Gap)

### CAIQ Questions

- **MDS-02.1**: Are processes, procedures, and technical measures defined, implemented, and evaluated for the periodic scanning of model artifacts for vulnerabilities and attacks at each step of the service lifecycle and at each handover point?
- **MDS-02.2**: Are policies, procedures and technical measures to address model artifact scanning regularly reviewed and updated?

---

## MDS-03: Model Documentation

**Type:** control
**Control Type:** AI-Specific
**Architectural Relevance:** Storage, Application, Data
**Threat Categories:** Data poisoning, Sensitive data disclosure, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Team and expertise
- Development: Design, Supply Chain
- Evaluation/Validation: Evaluation, Validation/Red Teaming, Re-evaluation
- Deployment: AI Services supply chain, AI applications
- Delivery: Operations, Continuous improvement
- Service Retirement: Model disposal

### Specification

Define, implement, enforce, approve, document, communicate, maintain and evaluate processes and procedures for model documentation. Regularly review and update the model documentation.

### Cross-References

- **bsi_aic4**: C4 PC-02
C5 SP-01
C5 SP-02 (Gap: No Gap)
- **eu_ai_act**: Article 11 (1)
Article 11 (2)
Article 13 (Gap: No Gap)
- **iso_42001**: 42001 A.6.2.7 - AI system technical documentation
42001 B.6.2.7 - AI system technical documentation (Gap: No Gap)
- **nist_ai_600_1**: GV-1.2-001
MG-2.2-002
MP-1.1-002
MP-2.2-001
MS-2.9-002
MG-3.2-003 (Gap: Partial Gap)

### CAIQ Questions

- **MDS-03.1**: Are processes and procedures defined, implemented, enforced, and evaluated for documenting, approving, communicating, evaluating, and maintaining model documentation?
- **MDS-03.2**: Is the model documentation regularly reviewed and updated?

---

## MDS-04: Model Documentation Requirements

**Type:** control
**Control Type:** AI-Specific
**Architectural Relevance:** Storage, Application, Data
**Threat Categories:** Data poisoning, Sensitive data disclosure, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Team and expertise
- Development: Design, Supply Chain
- Evaluation/Validation: Validation/Red Teaming, Re-evaluation
- Deployment: AI Services supply chain, AI applications
- Delivery: Operations, Continuous improvement
- Service Retirement: Model disposal

### Specification

Establish and implement baseline requirements for Model documentation.

### Cross-References

- **bsi_aic4**: C4 BC-01
C4 BC-02
C4 BC-03
C4 BC-04
C4 BC-05
C4 BC-06
C4 PF-05
C4 PC-02 (Gap: No Gap)
- **eu_ai_act**: Article 13 (2)
Article 13 (3) (Gap: No Gap)
- **iso_42001**: 42001 A.6.2.7 - AI system technical documentation
42001 A.6.2.2 - AI system requirements and specification
42001 A.6.2.6 - AI system operation and monitoring (Gap: No Gap)
- **nist_ai_600_1**: MS-2.9-002 (Gap: No Gap)

### CAIQ Questions

- **MDS-04.1**: Are baseline requirements for Model documentation established and implemented?

---

## MDS-05: Model Documentation Validation

**Type:** control
**Control Type:** AI-Specific
**Architectural Relevance:** Compute, Storage, Application, Data
**Threat Categories:** Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Shared Orchestrated Service Provider-Application Provider (Shared OSP-AP)

**Lifecycle Relevance:**
- Preparation: Data collection, Data curation
- Development: Design, Training
- Evaluation/Validation: Evaluation, Validation/Red Teaming, Re-evaluation
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous improvement
- Service Retirement: N/A

### Specification

Define, implement, and evaluate processes, procedures, and technical measures for the validation of the Model documentation aligned with the current model.

### Cross-References

- **bsi_aic4**: C4 PC-02
C5 SP-01 (Gap: No Gap)
- **eu_ai_act**: Article 13 (2)
Article 13 (3) (Gap: No Gap)
- **iso_42001**: 42001: A.6.2.4 - AI System Verification and Validation
42001: A.4.2 - Resource Documentation
42001: A.2.2 - AI Policy and A.6.2.1 - AI System Requirements (Gap: Partial Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **MDS-05.1**: Are processes, procedures, and technical measures defined, implemented, and evaluated for the validation of the model documentation aligned with the current model?

---

## MDS-06: Adversarial Attack Analysis

**Type:** control
**Control Type:** AI-Specific
**Architectural Relevance:** Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Owned by the Cloud Service Provider (CSP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Shared Orchestrated Service Provider-Application Provider (Shared OSP-AP)

**Lifecycle Relevance:**
- Preparation: Data collection, Data curation, Data storage, Team and expertise
- Development: Design, Training, Guardrails
- Evaluation/Validation: Evaluation, Validation/Red Teaming, Re-evaluation
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous improvement, Continuous monitoring
- Service Retirement: Data deletion, Model disposal

### Specification

Define, implement, and evaluate processes and technical measures to assess adversarial threats specific to each AI model.

### Cross-References

- **bsi_aic4**: C4 SR-01
C4 SR-02 (Gap: No Gap)
- **eu_ai_act**: Article 15 (1)
Article 15 (5) (Gap: No Gap)
- **iso_42001**: ISO 42001 A.6.2.3 - Documentation of AI system design and development
ISO 42001 B.6.2.3 - Documentation of AI system design and development
ISO 42001 A.6.2.6 - AI system operation and monitoring
ISO 42001 B.6.2.6 - AI system operation and monitoring
ISO 42001 B.6.2.7 - AI system technical documentation
ISO 42001 B.6.2.7 - AI system technical documentation (Gap: No Gap)
- **nist_ai_600_1**: GV-3.2-002
GV-3.2-005
MP-5.1-005
MP-5.1-006
MS-1.1-008 (Gap: No Gap)

### CAIQ Questions

- **MDS-06.1**: Are processes and technical measures defined, implemented, and evaluated to regularly assess adversarial threats specific to each AI model?

---

## MDS-07: Robustness against Adversarial Attack  / Model Hardening

**Type:** control
**Control Type:** AI-Specific
**Architectural Relevance:** Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Owned by the Cloud Service Provider (CSP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Shared Orchestrated Service Provider-Application Provider (Shared OSP-AP)

**Lifecycle Relevance:**
- Preparation: Data collection, Data curation, Data storage, Team and expertise
- Development: Design, Training
- Evaluation/Validation: Evaluation, Validation/Red Teaming, Re-evaluation
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous improvement
- Service Retirement: Model disposal, Data deletion

### Specification

Define, implement, and evaluate processes, procedures, and technical measures for Model Hardening to mitigate relevant adversarial attacks as identified in the Threat Analysis and Adversarial Threat Analysis.

### Cross-References

- **bsi_aic4**: C4 SR-04
C4 SR-05
C4 SR-06
C4 SR-07 (Gap: No Gap)
- **eu_ai_act**: Article 15 (5) (Gap: No Gap)
- **iso_42001**: ISO 42001 A.6.2.3 - Documentation of AI system design and development
ISO 42001 B.6.2.3 - Documentation of AI system design and development (Gap: Partial Gap)
- **nist_ai_600_1**: MS-2.3-001
MS-4.2-001 (Gap: Partial Gap)

### CAIQ Questions

- **MDS-07.1**: Are processes, procedures, and technical measures defined, implemented, and evaluated for Model Hardening to mitigate relevant adversarial attacks as identified in the Threat Analysis and Adversarial Threat Analysis?

---

## MDS-08: Model Integrity Checks

**Type:** control
**Control Type:** AI-Specific
**Architectural Relevance:** Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Shared Orchestrated Service Provider-Application Provider (Shared OSP-AP)

**Lifecycle Relevance:**
- Preparation: Data collection, Data curation, Data storage
- Development: Training, Design
- Evaluation/Validation: Validation/Red Teaming, Evaluation, Re-evaluation
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring
- Service Retirement: Archiving, Model disposal

### Specification

Regularly calculate and compare checksums using cryptographic hashes of model checkpoints to detect unauthorized modifications. Apply at least annually based on the level of risk, or after any change of hands.

### Cross-References

- **bsi_aic4**: C4 DQ-03
C4 DM-02
C5 PSS-07 (Gap: No Gap)
- **eu_ai_act**: Article 15 (5) (Gap: No Gap)
- **iso_42001**: No Mapping for ISO 42001
27002: 8.26 Application security requirements (Gap: Partial Gap)
- **nist_ai_600_1**: GV-4.3-001
MS-2.7-005 (Gap: Partial Gap)

### CAIQ Questions

- **MDS-08.1**: Are checksums regularly calculated and compared using cryptographic hashes of model checkpoints to detect unauthorized modifications?
- **MDS-08.2**: Are these measures applied at least annually based on the level of risk, or after any change of hands?

---

## MDS-09: Model Signing/Ownership Verification

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Network, Compute, Storage, Application
**Threat Categories:** Model manipulation, Sensitive data disclosure, Model theft, Insecure supply chain, Insecure apps/plugins, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Owned by the Cloud Service Provider (CSP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Shared Orchestrated Service Provider-Application Provider (Shared OSP-AP)

**Lifecycle Relevance:**
- Preparation: Team and expertise
- Development: Training
- Evaluation/Validation: Validation/Red Teaming
- Deployment: AI Services supply chain, Orchestration, AI applications
- Delivery: Operations, Maintenance
- Service Retirement: Model disposal

### Specification

Sign models cryptographically and verify signatures to ensure model provenance and ownership, any time the model changes hands or is loaded from storage.

### Cross-References

- **bsi_aic4**: C4 DM-03
C4 DM-04 (Gap: Partial Gap)
- **eu_ai_act**: Article 15 (1)
Article 15 (5) (Gap: No Gap)
- **iso_42001**: No Mapping for ISO 42001
ISO 27002: 8.26 Application security requirements (Gap: Partial Gap)
- **nist_ai_600_1**: MS-2.7-005 (Gap: No Gap)

### CAIQ Questions

- **MDS-09.1**: Are models signed cryptographically and are signatures verified to ensure model provenance and ownership any time the model changes hands or is loaded from storage?

---

## MDS-10: Model Continuous Monitoring

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Shared Orchestrated Service Provider-Application Provider (Shared OSP-AP)

**Lifecycle Relevance:**
- Preparation: Resource provisioning
- Development: Design
- Evaluation/Validation: Re-evaluation, Evaluation
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Data deletion

### Specification

Define, implement, and evaluate processes, procedures, and technical measures for continuous monitoring of model performance metrics over time to identify sudden shifts or unexpected changes in predictions that could degrade model performance.

### Cross-References

- **bsi_aic4**: C4 BC-03
C4 PF-01
C4 PF-02
C4 PF-07 (Gap: No Gap)
- **eu_ai_act**: Article 15 (2)
Article 15 (3) (Gap: No Gap)
- **iso_42001**: ISO 42001 A.6.2.6 - AI system operation and monitoring
ISO 42001 B.6.2.6 - AI system operation and monitoring
ISO 42001 9.3.2 - Management review inputs (Gap: No Gap)
- **nist_ai_600_1**: MG-4.1-007
MG-4.2-001
GV-1.3-001
GV-1.3-002
MS-2.3-001 (Gap: No Gap)

### CAIQ Questions

- **MDS-10.1**: Are processes, procedures, and technical measures defined, implemented, and evaluated for continuous monitoring of model performance metrics over time to identify sudden shifts or unexpected changes in predictions that could degrade model performance?

---

## MDS-11: Model Failure

**Type:** control
**Control Type:** AI-Specific
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Shared Orchestrated Service Provider-Application Provider (Shared OSP-AP)

**Lifecycle Relevance:**
- Preparation: Data storage, Resource provisioning
- Development: Design, Training
- Evaluation/Validation: Evaluation, Validation/Red Teaming, Re-evaluation
- Deployment: Orchestration, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Archiving, Model disposal

### Specification

Perform a risk-based evaluation of the model and model serving infrastructure for model failure. Define and implement measures to mitigate model and model serving infrastructure failures, and regularly evaluate throughout the AI system's lifecycle.

### Cross-References

- **bsi_aic4**: C4 BC-04
C4 SR-01
C4 SR-02
C4 SR-06
C5 BC-03
C5 BC-04
C5 OPS-05
C5 OPS-18 (Gap: No Gap)
- **eu_ai_act**: Article 15 (4) (Gap: No Gap)
- **iso_42001**: ISO 42001 A.4.5 - System and computing resources
ISO 42001 B.4.5 System and computing resources
ISO 27001 6.1.2 - Information security risk assessment
ISO 27001 A.8.13 - Information backup
ISO 27001 A.8.14 - Redundancy of information processing facilities => disagree => I would expect the use of the cloud
and therefore
ensuring that redundant availability zones/regions are selected. (Gap: No Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **MDS-11.1**: Are risk-based evaluation of the model and model serving infrastructure for model failure performed?
- **MDS-11.2**: Are measures defined and implemented to mitigate model and model serving infrastructure failures, and are they regularly evaluated throughout the AI system's lifecycle?

---

## MDS-12: Open Model Risk Assessment

**Type:** control
**Control Type:** AI-Specific
**Architectural Relevance:** Network, Compute, Storage, Application
**Threat Categories:** Model manipulation, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Shared Orchestrated Service Provider-Application Provider (Shared OSP-AP)

**Lifecycle Relevance:**
- Preparation: Resource provisioning, Team and expertise
- Development: Training, Guardrails
- Evaluation/Validation: Evaluation, Validation/Red Teaming
- Deployment: AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous improvement
- Service Retirement: Archiving, Model disposal

### Specification

Establish a process to evaluate risk associated with open models. Periodically review these risk factors, and implement a process to monitor and mitigate any determined vulnerabilities.

### Cross-References

- **bsi_aic4**: SR-01
SR-02
SR-03
SR-06
PF-07 (Gap: No Gap)
- **eu_ai_act**: Article 9 (Gap: No Gap)
- **iso_42001**: ISO 42001 6.1.2 AI risk assessment
ISO 42001 6.1.3 AI risk treatment
ISO 42001 A.6.2.6 - AI system operation and monitoring
ISO 42001 B.6.2.6 - AI system operation and monitoring (Gap: Partial Gap)
- **nist_ai_600_1**: MS-2.7-001 (Gap: Partial Gap)

### CAIQ Questions

- **MDS-12.1**: Are processes established to evaluate the risk associated with open models?
- **MDS-12.2**: Are risk factors periodically reviewed, and is a process implemented to monitor and mitigate any determined vulnerabilities?

---

## MDS-13: Secure Model Format

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Network, Compute, Storage, Application, Data
**Threat Categories:** Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Shared Orchestrated Service Provider-Application Provider (Shared OSP-AP)

**Lifecycle Relevance:**
- Preparation: Team and expertise
- Development: Design, Guardrails
- Evaluation/Validation: Validation/Red Teaming
- Deployment: Orchestration, AI Services supply chain
- Delivery: Maintenance
- Service Retirement: Model disposal

### Specification

Adopt secure model formats and processes for AI model serialization where applicable.

### Cross-References

- **bsi_aic4**: C4 SR-06
C4 SR-07 (Gap: No Gap)
- **eu_ai_act**: Article 15 (1)
Article 15 (4)
Article 15 (5) (Gap: No Gap)
- **iso_42001**: ISO 42001 A.6.1.3 - Processes for responsible AI system design and development
ISO 42001 B.6.1.3 - Processes for responsible design and development of AI systems
ISO 42001 B.6.2.3 - Documentation of AI system design and development (Gap: No Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **MDS-13.1**: Are secure model formats and processes for AI model serialization adopted where applicable?

---

# Domain: Security Incident Management, E-Discovery, & Cloud Forensics

## SEF-01: Security Incident Management Policy and Procedures

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared across the supply chain
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data storage
- Development: Guardrails, Supply Chain
- Evaluation/Validation: Re-evaluation
- Deployment: AI applications, Orchestration
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Archiving, Data deletion, Model disposal

### Specification

Establish, document, approve, communicate, apply, evaluate and maintain policies and procedures for Security Incident Management, E-Discovery,  and Forensics. Review and update the policies and procedures at least  annually or upon significant changes.

### Cross-References

- **bsi_aic4**: C4 PC-02
C5 SIM-01
C5 OPS-11 (Gap: No Gap)
- **eu_ai_act**: Article 15
Article 17
Article 26
Article 72
Article 73 (Gap: Partial Gap)
- **iso_42001**: 42001: 5.2
42001: A.2.2
42001: A.2.3
42001: A.2.4
42001: B.2.1
42001: B.2.2
42001: B.2.3
42001: B.2.4
42001: B.6.2.6 AI system operation and monitoring
42001: B.8.4 Communication of incidents
42001: A.8.4 Communication of incidents
27001: 5.1
27001: 5.2
27001: 7.3
27001: 7.4
27001: 7.5
27001: 9.1
27001: 9.3
27002: 5 (Gap: No Gap)
- **nist_ai_600_1**: GV-1.5-002
MG-2.3-001
MG-2.4-002
MG-2.4-003 (Gap: Partial Gap)

### CAIQ Questions

- **SEF-01.1**: Are policies and procedures established, documented, approved, communicated, applied, evaluated, and maintained for Security Incident Management, E-Discovery, and Forensics?
- **SEF-01.2**: Are policies and procedures for Security Incident Management, E-Discovery, and Forensics reviewed and updated at least annually or upon significant changes?

---

## SEF-02: Service Management Policy and Procedures

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared across the supply chain
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Shared Application Provider-AI Customer (Shared AP-AIC)

**Lifecycle Relevance:**
- Preparation: Data storage
- Development: Guardrails, Supply Chain
- Evaluation/Validation: Validation/Red Teaming, Re-evaluation
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Data deletion, Archiving, Model disposal

### Specification

Establish, document, approve, communicate, apply, evaluate and  maintain policies and procedures for the timely management of  security incidents. Review and update the policies and procedures at  least annually, or upon significant  changes.

### Cross-References

- **bsi_aic4**: C4 PC-02
C5 SIM-01
C5 SP-02 (Gap: No Gap)
- **eu_ai_act**: No Mapping (Gap: Full Gap)
- **iso_42001**: 42001: 5.2
42001: A.2.2
42001: A.2.3
42001: A.2.4
42001: A.8.4
42001: B.2.1
42001: B.2.2
42001: B.2.3
42001: B.2.4
42001: B.8.4
27001: 5.1
27001: 5.2
27001: 7.3
27001: 7.4
27001: 7.5
27001: 9.1
27001: 9.3
27001: A.5
27002: 5
27001: A.16.1.2
27002: 16.1.2
27001: A.16.1.5
27002: 16.1.5 (Gap: Partial Gap)
- **nist_ai_600_1**: GV-1.5-002
MG-2.3-001
MG-2.4-002
MG-2.4-003 (Gap: No Gap)

### CAIQ Questions

- **SEF-02.1**: Are Service Management Policies and Procedures established, documented, approved, communicated, applied, evaluated, and maintained for the timely management of security incidents?
- **SEF-02.2**: Are Service Management Policies and Procedures reviewed and updated at least annually, or upon significant  changes?

---

## SEF-03: Incident Response Plans

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared across the supply chain
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Shared Orchestrated Service Provider-Application Provider (Shared OSP-AP)

**Lifecycle Relevance:**
- Preparation: Data storage
- Development: Guardrails, Supply Chain
- Evaluation/Validation: Validation/Red Teaming
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Archiving, Data deletion, Model disposal

### Specification

Establish, document, approve, communicate, apply, evaluate and  maintain a security incident response plan, which includes but is not  limited to: a communication strategy for notifying relevant internal departments, impacted AICs, and other  business critical relationships (such as supply-chain) that may be  impacted.

### Cross-References

- **bsi_aic4**: C4 RE-05
C4 BC-04
C5 SIM-01
C5 OPS-21
C5 INQ-04 (Gap: No Gap)
- **eu_ai_act**: No Mapping (Gap: Full Gap)
- **iso_42001**: 42001: B.8.4
27001: A.5.24
27001: A.16.1.2
27001: A.16.1.5
27002: 16.1.2 and 16.1.5 (Gap: Partial Gap)
- **nist_ai_600_1**: MG-2.3-001
MG-2.4-002
MG-2.4-003
MG-4.2-002
GV-4.1-003 (Gap: No Gap)

### CAIQ Questions

- **SEF-03.1**: Is a security incident response plans which includes but is not limited to a communication strategy for notifying relevant internal departments, impacted AICs, and other business critical relationships (such as supply-chain) that may be impacted, established, documented, approved, communicated, applied, evaluated, and maintained?

---

## SEF-04: Incident Response Testing

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared across the supply chain
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Shared Orchestrated Service Provider-Application Provider (Shared OSP-AP)

**Lifecycle Relevance:**
- Preparation: Data storage, Resource provisioning, Team and expertise
- Development: Guardrails
- Evaluation/Validation: Evaluation, Validation/Red Teaming, Re-evaluation
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Archiving

### Specification

Follow a structured approach to evaluate the effectiveness of incident response plans at planned intervals or upon significant changes.

### Cross-References

- **bsi_aic4**: C4 RE-05
C5 SIM-05 (Gap: No Gap)
- **eu_ai_act**: No Mapping (Gap: Full Gap)
- **iso_42001**: 42001: A.6.2.4 / B.6.2.4
42001: A.6.2.4 / B.6.2.6
42001: Clause 9.1
27001: A.5.27
27002: 5.27 (Gap: Partial Gap)
- **nist_ai_600_1**: GV-1.5-002
MG-4.2-002
MG-4.3-001 (Gap: No Gap)

### CAIQ Questions

- **SEF-04.1**: Is a structured approach followed, to evaluate the effectiveness of incident response plans at planned intervals or upon significant changes?

---

## SEF-05: Incident Response Metrics

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared across the supply chain
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Shared Orchestrated Service Provider-Application Provider (Shared OSP-AP)

**Lifecycle Relevance:**
- Preparation: Data storage
- Development: Guardrails
- Evaluation/Validation: Re-evaluation
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Data deletion

### Specification

Establish, monitor and report information security incident metrics.

### Cross-References

- **bsi_aic4**: C4 RE-05
C5 SIM-05 (Gap: No Gap)
- **eu_ai_act**: No Mapping (Gap: Full Gap)
- **iso_42001**: 42001: A.6.2.6
42001: B.6.2.6
27001: A.5.24
27001: A.5.27
27001: Clause 9.3
27002: 5.24 (b) (Gap: Partial Gap)
- **nist_ai_600_1**: MS-2.7-004
MS-2.7-006 (Gap: No Gap)

### CAIQ Questions

- **SEF-05.1**: Are information security incident metrics established, monitored and reported?

---

## SEF-06: Event Triage Processes

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared across the supply chain
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Shared Orchestrated Service Provider-Application Provider (Shared OSP-AP)

**Lifecycle Relevance:**
- Preparation: Data storage
- Development: Guardrails
- Evaluation/Validation: Re-evaluation
- Deployment: AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Archiving, Data deletion, Model disposal

### Specification

Define, implement and evaluate processes, procedures and technical measures supporting business processes to triage security-related events.

### Cross-References

- **bsi_aic4**: C4 RE-05
C5 SIM-02
C5 OPS-15 (Gap: No Gap)
- **eu_ai_act**: No Mapping (Gap: Full Gap)
- **iso_42001**: No Mapping for ISO 42001
27001: A.5.25
27001: A.5.26
27002: 5.25
27002: 5.26 (Gap: Full Gap)
- **nist_ai_600_1**: GV-2.1-001
GV-2.1-002 (Gap: Partial Gap)

### CAIQ Questions

- **SEF-06.1**: Are security-related event triage processes, procedures and technical measures supporting business processes, defined, implemented and evaluated?
Alternative formulation: Are processes procedures and technical measures supporting business processes to triage security-related events, defined, implemented and evaluated?

---

## SEF-07: Security Breach Notification

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared across the supply chain
- Model: Shared across the supply chain
- Orchestrated Services: Shared across the supply chain
- Application: Shared across the supply chain

**Lifecycle Relevance:**
- Preparation: Data collection, Data curation, Data storage
- Development: Training, Guardrails
- Evaluation/Validation: Evaluation, Validation/Red Teaming, Re-evaluation
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Data deletion

### Specification

Define and implement, processes, procedures and technical measures for security breach notifications. Report material security breaches and  assumed security breaches including any relevant supply chain  breaches, as per applicable SLAs, laws and regulations.

### Cross-References

- **bsi_aic4**: C4 RE-05
C5 SIM-01
C5 SIM-03
C5 SIM-04 (Gap: No Gap)
- **eu_ai_act**: Article 20
Article 24 (4)
Article 55 (1) (c)
Article 73 (1)
Article 73 (2)
Article 73 (3)
Article 73 (7)
Article 73 (6) (Gap: Partial Gap)
- **iso_42001**: 42001: A.8.3
42001: A.8.4
42001: A.8.5
42001: A.10.2
42001: A.10.3
42001: A.10.4
42001: B.8.3
42001: B.8.4
42001: B.8.5
42001: B.10.1
42001: B.10.2
42001: B.10.3
42001: B.10.4 (Gap: No Gap)
- **nist_ai_600_1**: GV-2.1-001
GV-2.1-002
MG-2.3-001
MG-4.3-002
MG-4.3-003 (Gap: Partial Gap)

### CAIQ Questions

- **SEF-07.1**: Are processes, procedures and technical measures for security breach notifications defined and implemented?
- **SEF-07.2**: Are material security breaches and assumed security breaches, including any relevant supply chain breaches, reported as per applicable SLAs, laws and regulations?

---

## SEF-08: Points of Contact Maintenance

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared across the supply chain
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data collection, Data curation, Data storage, Resource provisioning, Team and expertise
- Development: Supply Chain, Guardrails, Training, Design
- Evaluation/Validation: Evaluation, Validation/Red Teaming, Re-evaluation
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Continuous monitoring
- Service Retirement: Archiving, Data deletion, Model disposal

### Specification

Maintain points of contact for applicable regulation authorities, national and local law enforcement, and other legal jurisdictional authorities.  Review and update the points of contact at least annually.

### Cross-References

- **bsi_aic4**: C4 PC-01
C5 OIS-05 (Gap: No Gap)
- **eu_ai_act**: No Mapping (Gap: Full Gap)
- **iso_42001**: 42001: A.8.4
42001: A.8.5
42001: B.8.4
42001: B.8.5 (Gap: No Gap)
- **nist_ai_600_1**: MG-2.3-001
MG-4.3-003 (Gap: No Gap)

### CAIQ Questions

- **SEF-08.1**: Are points of contact maintained for applicable regulation authorities, national and local law enforcement, and other legal jurisdictional authorities?
- **SEF-08.2**: Are the points of contacts reviewed and updated at least annually?

---

## SEF-09: Incident Response

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared across the supply chain
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data storage
- Development: Guardrails
- Evaluation/Validation: Re-evaluation
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Data deletion

### Specification

Define incident categories and severity levels for AI systems, and determine response procedures for each, including automated response where applicable.

### Cross-References

- **bsi_aic4**: C4 RE-05
C5 SIM-01 (Gap: No Gap)
- **eu_ai_act**: No Mapping (Gap: Full Gap)
- **iso_42001**: 42001: A.8.4
42001: A.8.5
42001: B.8.4
42001: B.8.5
27001: A.5.25
27002: A.5.26 (Gap: Partial Gap)
- **nist_ai_600_1**: MG-2.4-002
MG-2.4-003
MG-2.4-004 (Gap: Partial Gap)

### CAIQ Questions

- **SEF-09.1**: Are incident categories and severity levels defined for AI systems, and response procedures determined for each, including automated response where applicable?

---

# Domain: Supply Chain Management, Transparency, and Accountability

## STA-01: Supply Chain Risk 
Management Policies 
and Procedures

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared across the supply chain
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Owned by the Orchestrated Service Provider (OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data storage, Resource provisioning, Team and expertise
- Development: Design, Training, Guardrails
- Evaluation/Validation: Evaluation, Validation/Red Teaming, Re-evaluation
- Deployment: AI applications, AI Services supply chain, Orchestration
- Delivery: Operations, Maintenance, Continuous monitoring
- Service Retirement: Archiving, Data deletion, Model disposal

### Specification

Establish, document, approve, communicate, apply, evaluate, and maintain policies and procedures for supply chain risk management. Review and update the policies and procedures at least annually or upon significant changes.

### Cross-References

- **bsi_aic4**: C4 PC-02
C5 SSO-01
C5 OIS-03
C5 OIS-04
C5 PSS-01 (Gap: No Gap)
- **eu_ai_act**: Article 17 (1) (l)
Article 25
Article 53
Article 55
Article 56
Article 72 (Gap: Partial Gap)
- **iso_42001**: 42001: D.2 - Integration of AI management system with other management system standards
42001: B.10.3 - Suppliers
27001: A.5.19 - Information security in supplier relationships
27001: A.5.21 - Managing information security in the information and communication technology (ICT) supply chain
27001: A.5.1 - Policies for information security (Gap: No Gap)
- **nist_ai_600_1**: GV-4.1-001
GV-4.1-003
GV-6.1-004 (Gap: No Gap)

### CAIQ Questions

- **STA-01.1**: Are policies and procedures for supply chain risk management established, documented, approved, communicated, applied, evaluated, and maintained?
- **STA-01.2**: Are the policies and procedures reviewed and updated at least annually or upon significant changes?

---

## STA-02: SSRM Policy and Procedures

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared across the supply chain
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Shared Application Provider-AI Customer (Shared AP-AIC)

**Lifecycle Relevance:**
- Preparation: Data storage, Team and expertise
- Development: Guardrails
- Evaluation/Validation: Re-evaluation
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Archiving, Data deletion, Model disposal

### Specification

Establish, document, approve, communicate, apply, evaluate and  maintain policies and procedures for the application of the Shared  Security Responsibility Model (SSRM) within the organization.  Review and update the policies and procedures at least annually, or upon significant changes.

### Cross-References

- **bsi_aic4**: C4 PC-02
C5 SSO-01
C5 OIS-03
C5 OIS-04
C5 PSS-01 (Gap: No Gap)
- **eu_ai_act**: Article 17 (1) (l)
Annex VII (5.3)
Article 25 (Gap: Partial Gap)
- **iso_42001**: 42001: A.2.2 AI Policy
42001: A.2.3 Alignment with other organizational policies
42001: A.2.4 Review of AI Policy
42001: A.10.2 Allocating Responsibilities
27001: 5.1 Leadership Commitment
27001: 5.2 Policy
27001: 5.3 Organizational roles
responsibilities and authorities
27001: 7.3 Awareness
27001: 7.4 Communication
27001: 7.5 Documented Information
27001: 9.1 Monitoring
measurement
analysis and evaluation
27001: 9.3 Management Review
27001: A.5.1 Policies for information security
27001: A.5.2 Information security roles and responsibilities
27001: A.5.19 Information security in supplier relationships
27001: A.5.20 Addressing information security within supplier agreements
27001: A.5.22 Monitoring
review and change management of supplier services
27001: A 5.23 Information security for use of cloud services
27001: A.5.37 Documented operating procedures
27001: 5.1 Policies for information security
27002: 5.2 Information security roles and responsibilities
27002: 5.19 Information security in supplier relationships
27002: 5.20 Addressing information security within supplier agreements
27002: 5.22 Monitoring
review and change management of supplier services
27002: 5.23 Information security for use of cloud services
27002: 5.37 Documented operating procedures (Gap: No Gap)
- **nist_ai_600_1**: GV-4.1-001
GV-4.1-003
GV-6.1-004 (Gap: No Gap)

### CAIQ Questions

- **STA-02.1**: Are policies and procedures established, documented, approved, communicated, applied, evaluated, and maintained for applying the Shared Security Responsibility Model (SSRM) within the organization?
- **STA-02.2**: Are policies and procedures for applying the Shared Security Responsibility Model (SSRM) within the organization reviewed and updated at least annually, or upon significant changes?

---

## STA-03: SSRM Supply Chain

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared across the supply chain
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Owned by the Orchestrated Service Provider (OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data collection, Data curation, Data storage, Resource provisioning
- Development: Guardrails, Supply Chain
- Evaluation/Validation: Evaluation, Validation/Red Teaming, Re-evaluation
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Archiving, Data deletion, Model disposal

### Specification

Apply, document, implement and manage the SSRM throughout the  supply chain.

### Cross-References

- **bsi_aic4**: C4 BC-01
C5 BC-01 (Gap: No Gap)
- **eu_ai_act**: Article 17
Article 25 (Gap: Partial Gap)
- **iso_42001**: 42001: A.2.3 Alignment with other organizational policies
42001: A.10.2 Allocating Responsibilities
27001: A.5.2 Information security roles and responsibilities
27001: A.5.19 Information security in supplier relationships
27001: A.5.20 Addressing information security within supplier agreements
27001: A.5.22 Monitoring
review and change management of supplier services
27001: A 5.23 Information security for use of cloud services
27002: 5.2 Information security roles and responsibilities
27002: 5.19 Information security in supplier relationships
27002: 5.20 Addressing information security within supplier agreements
27002: 5.22 Monitoring
review and change management of supplier services
27002: 5.23 Information security for use of cloud services (Gap: No Gap)
- **nist_ai_600_1**: GV-6.1-004
GV-3.1-001
MP-1.1-001
GV-5.1-001 (Gap: No Gap)

### CAIQ Questions

- **STA-03.1**: Is the SSRM applied, documented, implemented and managed throughout the supply chain?

---

## STA-04: SSRM Guidance

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Owned by the Cloud Service Provider (CSP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data collection, Data curation, Data storage
- Development: Guardrails, Supply Chain
- Evaluation/Validation: Evaluation, Validation/Red Teaming, Re-evaluation
- Deployment: AI Services supply chain, AI applications, Orchestration
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Data deletion, Model disposal, Archiving

### Specification

Provide SSRM Guidance to the Customer detailing information about the SSRM applicability throughout the supply chain.

### Cross-References

- **bsi_aic4**: C4 PC-02
C5 PSS-01 (Gap: No Gap)
- **eu_ai_act**: Article 13(1)
Article 13 (2)
Article 13 (3)
Article 25 (4) (Gap: Partial Gap)
- **iso_42001**: 42001: A.2.3 Alignment with other organizational policies
42001: A.10.2 Allocating Responsibilities
27001: 7.4 Communication
27001: 9.1 General - Internal Audit
27001: A.5.20 Addressing information security within supplier agreements
27001: A.5.21 Managing information security in the information and communication technology (ICT) supply chain
27001: A.5.23 Information security for use of cloud services
27002: 5.20 (a-z) Addressing information security within supplier agreements
27002: 5.21 (a-m) Managing information security in the information and communication technology (ICT) supply chain
27002: 5.23 (d) Information security for use of cloud services (Gap: No Gap)
- **nist_ai_600_1**: GV-6.1-002 (Gap: Partial Gap)

### CAIQ Questions

- **STA-04.1**: Are customers provided with SSRM guidance detailing its applicability throughout the supply chain?

---

## STA-05: SSRM Control Ownership

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared across the supply chain
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Owned by the Orchestrated Service Provider (OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data collection, Data curation, Data storage, Resource provisioning
- Development: Supply Chain
- Evaluation/Validation: Evaluation, Validation/Red Teaming, Re-evaluation
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Archiving, Data deletion, Model disposal

### Specification

Delineate the shared ownership and applicability of all CSA AICM  controls according to the SSRM.

### Cross-References

- **bsi_aic4**: C4 BC-01
C5 BC-01 (Gap: No Gap)
- **eu_ai_act**: Article 17
Article 25
Article 28 (Gap: Partial Gap)
- **iso_42001**: 42001: A.2.3 Alignment with other organizational policies
42001: A.10.2 Allocating Responsibilities
27001: A.5.23 Information security for use of cloud services
27002: 5.23 Information security for use of cloud services (Gap: No Gap)
- **nist_ai_600_1**: GV-6.1-004 (Gap: No Gap)

### CAIQ Questions

- **STA-05.1**: Is the shared ownership and applicability of all CSA AICM controls delineated according to the SSRM?

---

## STA-06: SSRM Documentation Review

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared across the supply chain
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data storage, Resource provisioning
- Development: Supply Chain
- Evaluation/Validation: Evaluation, Validation/Red Teaming, Re-evaluation
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Archiving, Data deletion, Model disposal

### Specification

Review and validate SSRM documentation.

### Cross-References

- **bsi_aic4**: C4 PC-01
C5 SSO-04
C5 OIS-03
C5 OIS-04 (Gap: No Gap)
- **eu_ai_act**: Article 15
Article 17
Article 28
Annex IV (2) (f)
Annex VII (5.3) (Gap: Full Gap)
- **iso_42001**: 42001: A.2.3 Alignment with other organizational policies
42001: A.10.2 Allocating Responsibilities
27001: 9.1 Monitoring
measurement
analysis and evaluation
27001: 9.3 Management review
27001: A.5.20 Addressing information security within supplier agreements
27001: A.5.23  Information security for use of cloud services
27002: A.5.20 Addressing information security within supplier agreements
27002: 5.23 Information security for use of cloud services (Gap: No Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **STA-06.1**: Are the  SSRM documentation reviewed and validated?

---

## STA-07: SSRM Control Implementation

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data storage
- Development: Supply Chain
- Evaluation/Validation: Evaluation, Validation/Red Teaming, Re-evaluation
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Archiving, Data deletion, Model disposal

### Specification

Implement, operate, and audit or assess the portions of the SSRM which the organization is responsible for.

### Cross-References

- **bsi_aic4**: C4 PC-01
C4 SR-06
C5 OPS-20
C5 OPS-21
C5 COM-02
C5 SSO-04 (Gap: No Gap)
- **eu_ai_act**: Article 15
Article(s) 16 to 27 (Section 3)
Article 17
Annex VI, VII (Gap: Partial Gap)
- **iso_42001**: 42001: A.2.3 Alignment with other organizational policies
42001: A.10.2 Allocating Responsibilities
27001: 8.1 Operational planning and control
27001: A.5.20 Addressing information security within supplier agreements
27001: A.5.21 Managing information security in the information and communication technology (ICT) supply chain
27001: A.5.22 Monitoring
review and change management of supplier services
27001: A.5.23 Information security for use of cloud services
27001: 5.20 Addressing information security within supplier agreements
27001: 5.21 Managing information security in the information and communication technology (ICT) supply chain
27001: 5.22 Monitoring
review and change management of supplier services
27001: 5.23 Information security for use of cloud services (Gap: No Gap)
- **nist_ai_600_1**: MG-3.1-002 (Gap: Partial Gap)

### CAIQ Questions

- **STA-07.1**: Are the portions of the SSRM the organization is responsible for implemented, operated, audited, or assessed?

---

## STA-08: Supply Chain Inventory

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared across the supply chain
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data storage, Resource provisioning
- Development: Supply Chain
- Evaluation/Validation: Evaluation, Validation/Red Teaming, Re-evaluation
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Maintenance
- Service Retirement: Data deletion

### Specification

Develop and maintain an inventory of all supply chain relationships.

### Cross-References

- **bsi_aic4**: C4 BC-01 (4th bullet)
C5 SSO-03 (Gap: No Gap)
- **eu_ai_act**: No Mapping (Gap: Full Gap)
- **iso_42001**: 42001: A.2.3 Alignment with other organizational policies
42001: A.10.3 Suppliers
27001: A.5.20 Addressing information security within supplier agreements
27001: A.5.21 Managing information security in the information and communication technology (ICT) supply chain
27002: 5.20 (Guidance last paragraph) Addressing information security within supplier agreements
27002: 5.21 (g-h) Managing information security in the information and communication technology (ICT) supply chain (Gap: No Gap)
- **nist_ai_600_1**: GV-6.1-007 (Gap: No Gap)

### CAIQ Questions

- **STA-08.1**: Is an inventory of all supply chain relationships maintained and developed?

---

## STA-09: Supply Chain Risk Management

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Owned by the Cloud Service Provider (CSP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data collection, Data curation, Data storage, Resource provisioning, Team and expertise
- Development: Supply Chain
- Evaluation/Validation: Re-evaluation, Validation/Red Teaming, Evaluation
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Data deletion

### Specification

Periodically review risk factors associated with supply chain relationships.

### Cross-References

- **bsi_aic4**: C4 SR-03
C4 SR-04
C5 SSO-02
C5 SSO-04 (Gap: No Gap)
- **eu_ai_act**: Article 9 (Gap: Partial Gap)
- **iso_42001**: 42001: A.2.3 Alignment with other organizational policies
42001: A.10.3 Suppliers
27001: A.5.19 Information security in supplier relationships
27001: A.5.21 Managing information security in the information and communication technology (ICT) supply chain
27001: A.5.23 Information security for use of cloud services
27002: 5.19 Information security in supplier relationships
27002: 5.21 Managing information security in the information and communication technology (ICT) supply chain
27002: 5.23 Information security for use of cloud services (Gap: No Gap)
- **nist_ai_600_1**: GV-6.1-005
RM-1.2-002 (Gap: No Gap)

### CAIQ Questions

- **STA-09.1**: Are risk factors associated with the supply chain relationships periodically reviewed?

---

## STA-10: Primary Service and Contractual Agreement

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared across the supply chain
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Orchestrated Service Provider-Application Provider (Shared OSP-AP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data storage
- Development: Supply Chain
- Evaluation/Validation: Validation/Red Teaming
- Deployment: AI Services supply chain
- Delivery: Operations, Continuous monitoring, Continuous improvement
- Service Retirement: Data deletion

### Specification

Service agreements must incorporate at least the following mutually-agreed upon provisions and/or terms: • Scope, characteristics and location of business relationship and services offered • Information security requirements (including SSRM) • Change management process • Logging and monitoring capability • Incident management and communication procedures • Right to audit and third party assessment • Service termination • Interoperability and portability requirements • Data privacy

### Cross-References

- **bsi_aic4**: C4 PC-01
C4 PC-02
C5 SSO-01
C5 SSO-03
C5 SSO-05 (Gap: No Gap)
- **eu_ai_act**: Article 9
Article 13 & Annex IV
Article 15
Article 17
Article 25 (4)
Article 53 (1) (e) (Gap: Partial Gap)
- **iso_42001**: 42001: A.2.3 Alignment with other organizational policies
42001: A.10.4 Customers
42001: A.6.1 Risk assessment for AI systems
42001: A.6.3.2 Planning of AI-specific controls
42001: A.8.2.2 Operational planning and control
42001: A.8.3.1 Data governance
27001: A.5.19 Information security in supplier relationships
27001: A.5.20 Addressing information security within supplier agreements
27001: A.5.23 Information security for use of cloud services
27001: A.8.30 Outsourced Development
27002: 5.19 Information security in supplier relationships
27002: 5.20 Addressing information security within supplier agreements
27002: 5.23 Information security for use of cloud services (Gap: Partial Gap)
- **nist_ai_600_1**: GV-6.1-004 (Gap: No Gap)

### CAIQ Questions

- **STA-10.1**: Are service agreements required to include at least the following mutually agreed upon provisions and/or terms?
• Scope, characteristics and location of business relationship and services offered
• Information security requirements (including SSRM)
• Change management process
• Logging and monitoring capability
• Incident management and communication procedures
• Right to audit and third party assessment
• Service termination
• Interoperability and portability requirements
• Data privacy

---

## STA-11: Supply Chain Agreement Review

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared across the supply chain
- Model: Shared across the supply chain
- Orchestrated Services: Owned by the Orchestrated Service Provider (OSP)
- Application: Shared Orchestrated Service Provider-Application Provider (Shared OSP-AP)

**Lifecycle Relevance:**
- Preparation: Data storage, Resource provisioning
- Development: Supply Chain
- Evaluation/Validation: Evaluation, Validation/Red Teaming, Re-evaluation
- Deployment: Orchestration, AI Services supply chain
- Delivery: Operations, Maintenance, Continuous monitoring
- Service Retirement: Data deletion

### Specification

Review supply chain agreements at least annually, or upon significant changes.

### Cross-References

- **bsi_aic4**: C4 PF-03
C5 SSO-04 (Gap: No Gap)
- **eu_ai_act**: Article 9 (6)
Article 16
Article 17
Article 25 (Gap: Partial Gap)
- **iso_42001**: 42001: A.2.3 Alignment with other organizational policies
42001: A 10.3 Supply Chain
27001: A.5.19 Information security in supplier relationships
27001: A.5.20 Addressing information security within supplier agreements
27001: A.5.22 Monitoring
review and change management of supplier
services
27002: 5.20 Addressing information security within supplier agreements
27002: 5.22 Monitoring
review and change management of supplier
services (Gap: Partial Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **STA-11.1**: Are supply chain agreements reviewed at least annually or upon significant changes?

---

## STA-12: Supply Chain 
Compliance 
Assessment

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared across the supply chain
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data storage, Resource provisioning, Team and expertise
- Development: Design, Training, Guardrails
- Evaluation/Validation: Evaluation, Validation/Red Teaming, Re-evaluation
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Archiving, Data deletion, Model disposal

### Specification

Define and implement a process for conducting internal assessments to confirm conformance and effectiveness of standards, policies,  procedures, and service level agreement activities at least annually.

### Cross-References

- **bsi_aic4**: C4 PC-01
C4 Section 4 (4.4.2.1)
C5 SSO-04
C5 COM-02
C5 COM-03 (Gap: No Gap)
- **eu_ai_act**: Article 9 (2)
Article 17
Annex VII 5.3 (Gap: Partial Gap)
- **iso_42001**: 42001: A.2.3 Alignment with other organizational policies
42001: A.10.3 Suppliers
27001: A.5.22 Monitoring
review and change management of supplier services
27002: 5.22 Monitoring
review and change management of supplier services (Gap: No Gap)
- **nist_ai_600_1**: GV-6.1-005 (Gap: No Gap)

### CAIQ Questions

- **STA-12.1**: Is there a process for conducting internal assessments at least annually to confirm the conformance and effectiveness of standards, policies, procedures, and SLA activities?

---

## STA-13: Supply Chain Service Agreement Compliance

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared across the supply chain
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Owned by the Orchestrated Service Provider (OSP)
- Application: Shared Application Provider-AI Customer (Shared AP-AIC)

**Lifecycle Relevance:**
- Preparation: Data collection, Data curation, Data storage, Resource provisioning
- Development: Design, Training, Guardrails
- Evaluation/Validation: Evaluation, Validation/Red Teaming, Re-evaluation
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Archiving, Data deletion, Model disposal

### Specification

Implement policies requiring all service providers throughout the  supply chain to comply with information security, confidentiality,  access control, privacy, audit, personnel policy and service level  requirements and standards.

### Cross-References

- **bsi_aic4**: C4 PC-01
C5 SSO-01 (Gap: No Gap)
- **eu_ai_act**: Article 16
Article 17
Article 22
Article 23
Article 24
Article 25
Article 26
Article 53
Article 54
Article 55 (Gap: Partial Gap)
- **iso_42001**: 42001: A.2.2 AI policy
42001: A.2.3 Alignment with other organizational policies
42001 A.2.4 Review of the AI policy
42001: A.10.2 Allocating Responsibilities
42001: A.10.4 Customers
27001: A.5.19 Information security in supplier relationships
27001: A.5.20 Addressing information security within supplier agreements
27001: A.5.21 Managing information security in the information and communication technology (ICT) supply chain
27001: A.5.22 Monitoring
review and change management of supplier services
27001: A.5.23 Information security for use of cloud services
27002: 5.19 Information security in supplier relationships
27002: 5.20 Addressing information security within supplier agreements
27002: 5.21 Managing information security in the information and communication technology (ICT) supply chain
27002: 5.22 Monitoring
review and change management of supplier services
27002: 5.23 Information security for use of cloud services (Gap: No Gap)
- **nist_ai_600_1**: GV-6.1-009
GV-6.1-004 (Gap: Partial Gap)

### CAIQ Questions

- **STA-13.1**: Are policies implemented requiring all service providers throughout the supply chain to comply with information security, confidentiality, access control, privacy, audit, personnel policy and service level requirements and standards?

---

## STA-14: Supply Chain Governance Review

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Shared Application Provider-AI Customer (Shared AP-AIC)

**Lifecycle Relevance:**
- Preparation: Data collection, Data curation, Data storage, Resource provisioning
- Development: Design, Training, Guardrails
- Evaluation/Validation: Evaluation, Validation/Red Teaming, Re-evaluation
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Archiving, Data deletion, Model disposal

### Specification

Periodically review the organization's supply chain partners' IT governance policies and procedures.

### Cross-References

- **bsi_aic4**: C4 PC-01
C5 SSO-04 (Gap: No Gap)
- **eu_ai_act**: Article 17
Article 25 (1)
Article 28 (1)
Annex VII 5.3 (Gap: Partial Gap)
- **iso_42001**: 42001: A.2.3 Alignment with other organizational policies
42001: A.10.3 Suppliers
27001: A.5.22 Monitoring
review and change management of supplier services
27002: 5.22 Monitoring
review and change management of supplier services (Gap: No Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **STA-14.1**: Are the IT governance policies and procedures for organization's supply chain partners periodically reviewed?

---

## STA-15: Supply Chain Data Security Assessment

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared across the supply chain
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data collection, Data curation, Data storage, Resource provisioning
- Development: Guardrails
- Evaluation/Validation: Validation/Red Teaming, Re-evaluation
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Archiving, Data deletion, Model disposal

### Specification

Define and implement a process for conducting security assessments periodically for all organizations within the supply chain.

### Cross-References

- **bsi_aic4**: C4 SR-03
C4 SR-04
C5 SSO-04 (Gap: No Gap)
- **eu_ai_act**: Article 15
Article 17
Annex VII 5.3 (Gap: Partial Gap)
- **iso_42001**: 42001: A.2.3 Alignment with other organizational policies
42001: A.10.3 Suppliers
27001: A.5.19 Information security in supplier relationships
27001: A.5.21 Managing information security in the information and communication technology (ICT) supply chain
27001: A.5.23 Information security for use of cloud services
27002: 5.19 Information security in supplier relationships
27002: 5.21 Managing information security in the information and communication technology (ICT) supply chain
27002: 5.23 Information security for use of cloud services (Gap: No Gap)
- **nist_ai_600_1**: GV-6.1-005
GV-6.1-006 (Gap: No Gap)

### CAIQ Questions

- **STA-15.1**: Is a process for conducting periodic security assessments for all organizations within the supply chain defined and implemented?

---

## STA-16: Service Bill of Material (BOM)

**Type:** control
**Control Type:** AI-Specific
**Architectural Relevance:** Application, Data
**Threat Categories:** Sensitive data disclosure, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Owned by the Customer (AIC)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Owned by the Orchestrated Service Provider (OSP)
- Application: Owned by the Customer (AIC)

**Lifecycle Relevance:**
- Preparation: Resource provisioning
- Development: Design, Guardrails
- Evaluation/Validation: Evaluation, Validation/Red Teaming
- Deployment: Orchestration, AI Services supply chain
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Archiving, Data deletion, Model disposal

### Specification

Define, implement, and enforce a process for establishing a Bill of Material for the service supply chain. Review and update the Bill of Material at least annually or upon significant changes.

### Cross-References

- **bsi_aic4**: BC-01
DM-03
PF-05
PF-10
EX-01 (Gap: Partial Gap)
- **eu_ai_act**: Article 11
Article 13
Article 25
Article 51
Article 52 (Gap: Partial Gap)
- **iso_42001**: 42001: D.2 - Integration of AI management system with other management system standards
42001: B.10.3 - Suppliers
27001: A.5.20 - Addressing information security within supplier agreements
27001: A.5.22 - Monitoring
review and change management of supplier services (Gap: Partial Gap)
- **nist_ai_600_1**: GV-6.1-005 (Gap: No Gap)

### CAIQ Questions

- **STA-16.1**: Are processes defined, implemented, enforced, and evaluated for establishing a Bill of Material for the entire AI service supply chain, including the model, orchestrated services, and AI applications?

---

# Domain: Threat & Vulnerability Management

## TVM-01: Threat and Vulnerability Management Policy and Procedures

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared across the supply chain
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data storage, Resource provisioning
- Development: Training
- Evaluation/Validation: Validation/Red Teaming, Re-evaluation
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Data deletion

### Specification

Establish, document, approve, communicate, apply, evaluate and maintain policies and procedures to identify, report and prioritize the remediation of vulnerabilities and threats, in order to protect systems against vulnerability exploitation. Review and update the policies and procedures at least annually or upon significant changes.

### Cross-References

- **bsi_aic4**: C4 PC-02
C4 SR-01
C5 OPS-18 (Gap: No Gap)
- **eu_ai_act**: Article 15 (4)
Article 15 (5) (Gap: Partial Gap)
- **iso_42001**: A.2.4 Review of AI Policy (42001)
6.1.1 General (42001 - Actions to address risks and opportunities)
6.1.3 AI risk treatment (42001)
7.4 Communication (42001)
7.5 Documented Information (42001) (Gap: No Gap)
- **nist_ai_600_1**: MG-2.4-003 (Gap: Partial Gap)

### CAIQ Questions

- **TVM-01.1**: Are policies and procedures that identify, report, and prioritize the remediation of vulnerabilities and threats in order to protect systems against vulnerability exploitation, established, documented, approved, communicated, applied, evaluated, and maintained?
- **TVM-01.2**: Are threats and vulnerabilities policies and procedures reviewed and updated at least annually or upon significant changes?

---

## TVM-02: Malware and Malicious Instructions Protection Policy and Procedures

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Shared Application Provider-AI Customer (Shared AP-AIC)

**Lifecycle Relevance:**
- Preparation: Data storage, Resource provisioning
- Development: Training
- Evaluation/Validation: Re-evaluation
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Archiving, Data deletion, Model disposal

### Specification

Establish, document, approve, communicate, apply, evaluate and maintain policies and procedures to protect against malware and malicious instructions. Review and update the policies and procedures at least annually or upon significant changes.

### Cross-References

- **bsi_aic4**: C4 PC-02
C5 OPS-04 (Gap: No Gap)
- **eu_ai_act**: Article 15 (4)
Article 15 (5) (Gap: Partial Gap)
- **iso_42001**: 5.2 AI Policy (42001)
A.5.2.1 Policies for information security (27001)
6.1.2 AI risk Assessment (42001)
A.8.7 Protection against Malware (27001)
7.5 Documented information (42001)
8.1 Operational planning and control (42001)
9.1 Monitoring
measurement .... (42001)
10.1 Continual improvement ... (42001) (Gap: No Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **TVM-02.1**: Are policies and procedures to protect against malware and malicious instructions, established, documented, approved, communicated, applied, evaluated, and maintained?
- **TVM-02.2**: Are malware and malicious instructions protection policies and procedures, reviewed and updated at least annually or upon significant changes?

---

## TVM-03: Vulnerability Identification

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared across the supply chain
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Orchestrated Service Provider-Application Provider (Shared OSP-AP)
- Application: Shared Application Provider-AI Customer (Shared AP-AIC)

**Lifecycle Relevance:**
- Preparation: Data storage, Resource provisioning
- Development: Training
- Evaluation/Validation: Evaluation, Validation/Red Teaming, Re-evaluation
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Data deletion, Model disposal

### Specification

Define, implement and evaluate processes, procedures and technical measures to enable both scheduled and emergency responses to vulnerability identifications, based on the identified risk.

### Cross-References

- **bsi_aic4**: C4 SR-06
C4 RE-05
C5 OPS-18 (Gap: No Gap)
- **eu_ai_act**: Article 15 (5) (Gap: Partial Gap)
- **iso_42001**: 42001: 6.1.2 AI risk assessment
42001: 8.1 Operational planning and control
42001: 9.1 Monitoring
measure.
27001: 8.1 Operational Planning and Control
27001: A.5.26 Response to information security incidents
27001: A.8.8 Management of technical vulnerabilities (Gap: No Gap)
- **nist_ai_600_1**: GV-1.3-003
MG-2.3-001
MG-4.2-002 (Gap: No Gap)

### CAIQ Questions

- **TVM-03.1**: Are processes, procedures, and technical measures defined, implemented, and evaluated to enable scheduled and emergency responses to vulnerability identifications based on the identified risk?

---

## TVM-04: Detection Updates

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared across the supply chain
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Shared Orchestrated Service Provider-Application Provider (Shared OSP-AP)

**Lifecycle Relevance:**
- Preparation: N/A
- Development: Guardrails
- Evaluation/Validation: Evaluation, Validation/Red Teaming, Re-evaluation
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Data deletion, Model disposal

### Specification

Define, implement and evaluate processes, procedures and technical measures to update detection tools, threat signatures, and indicators  of compromise on a weekly, or more frequent basis.

### Cross-References

- **bsi_aic4**: C4 SR-01
C5 OPS-05 (Gap: Partial Gap)
- **eu_ai_act**: Article 15 (5) (Gap: Partial Gap)
- **iso_42001**: 42001: A.6.2.6 AI System operation and monitoring
27001: A.8.7 Protection against malware
27001: A.8.8 Management of technical vulnerabilities
27001: A.8.16 Monitoring activities
27002: 5.7 Threat intelligence
27002: 5.17 / 5.18 Monitoring and event logging (Gap: Partial Gap)
- **nist_ai_600_1**: MS-2.6-005
MS-2.7-009 (Gap: Partial Gap)

### CAIQ Questions

- **TVM-04.1**: Are processes, procedures, and technical measures defined, implemented, and evaluated to update detection tools, threat signatures, and indicators of compromise weekly or more frequently?

---

## TVM-05: External Library Vulnerabilities

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Sensitive data disclosure, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Owned by the Orchestrated Service Provider (OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: N/A
- Development: Guardrails
- Evaluation/Validation: Evaluation, Validation/Red Teaming, Re-evaluation
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Data deletion, Model disposal

### Specification

Define, implement and evaluate processes, procedures and technical measures to identify updates for applications which use third party or  open source libraries according to the organization's vulnerability  management policy.

### Cross-References

- **bsi_aic4**: C4 DQ-01
C4 SR-02
C5 DEV-01
C5 DEV-02
C5 DEV-05 (Gap: No Gap)
- **eu_ai_act**: Article 15
Annex IV (1) (c) (Gap: No Gap)
- **iso_42001**: 42001: A.10.3 Supply Chain
27001: 6.1.2 Identifying risks from third party libraries
27001: A.8.8 Management of technical vulnerabilities
27002: 8.8 Technical vulnerability management
27002: 8.12 Secure software development
27002: 8.9 Configuration management
27002: 5.7 Threat intelligence (Gap: Partial Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **TVM-05.1**: Are processes, procedures, and technical measures defined, implemented, and evaluated to identify updates for applications that use third party or open source libraries according to the organization's vulnerability management policy?

---

## TVM-06: Penetration Testing

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Shared Orchestrated Service Provider-Application Provider (Shared OSP-AP)

**Lifecycle Relevance:**
- Preparation: Data storage, Resource provisioning
- Development: Guardrails
- Evaluation/Validation: Evaluation, Validation/Red Teaming, Re-evaluation
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Data deletion, Model disposal

### Specification

Define, implement and evaluate processes, procedures and technical measures for the periodic performance of penetration testing by  independent third parties.

### Cross-References

- **bsi_aic4**: C4 SR-05
C5 OPS-19 (Gap: Partial Gap)
- **eu_ai_act**: Article 43 (Gap: No Gap)
- **iso_42001**: 6. Planning  (27001)
9. Performance Evaluation (27001)
A.8.8 Management of technical vulnerabilities (27001)
A.6.2.6 AI System Operation and Monitoring (42001) (Gap: Partial Gap)
- **nist_ai_600_1**: MP-5.1-005
MS-4.2-001 (Gap: No Gap)

### CAIQ Questions

- **TVM-06.1**: Are processes, procedures, and technical measures defined, implemented, and evaluated for the periodic performance of penetration testing by independent third parties?

---

## TVM-07: Vulnerability Remediation Schedule

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared across the supply chain
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Shared Application Provider-AI Customer (Shared AP-AIC)

**Lifecycle Relevance:**
- Preparation: Data collection, Data curation, Data storage, Resource provisioning
- Development: Design, Training
- Evaluation/Validation: Evaluation, Validation/Red Teaming, Re-evaluation
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Archiving, Data deletion, Model disposal

### Specification

Define, implement and evaluate processes, procedures and technical measures based on identified risks to support scheduled and emergency responses to vulnerability identification.

### Cross-References

- **bsi_aic4**: C4 SR-01
C5 OPS-22 (Gap: Partial Gap)
- **eu_ai_act**: Article 9 (2)
Article 72
Annex IV (3) (Gap: No Gap)
- **iso_42001**: 8.8 Management of technical vulnerabilities (27001)
A.6.2.6 AI system operation and monitoring (42001) (Gap: No Gap)
- **nist_ai_600_1**: MP-5.1-005
MS-4.2-001 (Gap: No Gap)

### CAIQ Questions

- **TVM-07.1**: Are processes, procedures, and technical measures defined, implemented, and evaluated based on identified risks to support scheduled and emergency responses to vulnerability identification?

---

## TVM-08: Vulnerability Prioritization

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Orchestrated Service Provider-Application Provider (Shared OSP-AP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Resource provisioning
- Development: Design, Training
- Evaluation/Validation: Re-evaluation
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Archiving, Data deletion, Model disposal

### Specification

Use a risk-based model for effective prioritization of vulnerability remediation using an industry recognized framework.

### Cross-References

- **bsi_aic4**: C4 SR-02
C5 OPS-18 (Gap: No Gap)
- **eu_ai_act**: Article 3 (49) (b)
Article 9 (1)
Article 41 (Gap: No Gap)
- **iso_42001**: 8.8 Management of technical vulnerabilities (27001)
A.6.2.6 AI system Operation and monitoring (42001) (Gap: No Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **TVM-08.1**: Are risk-based models utilized to prioritize vulnerability remediation using an industry-recognized framework effectively?

---

## TVM-09: Vulnerability Management Reporting

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data storage, Resource provisioning
- Development: Training
- Evaluation/Validation: Evaluation, Validation/Red Teaming, Re-evaluation
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Archiving, Data deletion, Model disposal

### Specification

Define and implement a process for tracking and reporting  vulnerability identification and remediation activities that includes  stakeholder notification.

### Cross-References

- **bsi_aic4**: C4 SR-02
C4 SR-03
C5 COM-04 (Gap: No Gap)
- **eu_ai_act**: Article 72 (2) (d)
Article 73 (Gap: No Gap)
- **iso_42001**: 42001: A.6.2.6 AI system operation and monitoring
42001: A.8.4 Reporting and stakeholder notification
42001: A.6.1 / A.6.3.2 Risk and control planning
27001: 5.26 Response to information sec. inc
27001: 8.8 Management of technical vulnerabilities
27002: 8.8 Technical vulnerability management
27002: 5.7: Threat intelligence (Gap: Partial Gap)
- **nist_ai_600_1**: GV-2.1-001
GV-4.3-002
MG-2.4-003
MS-2.7-001 (Gap: Partial Gap)

### CAIQ Questions

- **TVM-09.1**: Are processes defined and implemented for tracking and reporting vulnerability identification and remediation activities that include stakeholder notification?

---

## TVM-10: Vulnerability Management Metrics

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Orchestrated Service Provider-Application Provider (Shared OSP-AP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data collection, Data curation, Data storage, Resource provisioning
- Development: Design, Training
- Evaluation/Validation: Evaluation, Validation/Red Teaming, Re-evaluation
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Data deletion, Model disposal

### Specification

Establish, monitor and report metrics for vulnerability identification and remediation at defined intervals.

### Cross-References

- **bsi_aic4**: C4 SR-02
C4 SR-03
C5 COM-04 (Gap: No Gap)
- **eu_ai_act**: Article 72
Article 15 (1)
Article 15 (2)
Article 15 (3)
Annex IV (2) (g) (3) (9)
Annex XI (2) (1) (Gap: No Gap)
- **iso_42001**: 42001: A.6.2.6 AI system Operation and monitoring
27001: 8.8 Management of technical vulnerabilities.
27001: 9.1 Monitoring
measurement
analysis and evaluation (Gap: No Gap)
- **nist_ai_600_1**: MS-2.7-004 (Gap: Partial Gap)

### CAIQ Questions

- **TVM-10.1**: Are metrics established, monitored, and reported for vulnerability identification and remediation at defined intervals?

---

## TVM-11: Guardrails

**Type:** control
**Control Type:** AI-Specific
**Architectural Relevance:** Compute, Storage, Application, Data
**Threat Categories:** Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data storage
- Development: Guardrails
- Evaluation/Validation: Validation/Red Teaming, Re-evaluation
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: N/A

### Specification

Define and implement processes, procedures and technical measures to  apply guardrails to the AI system. Continuously evaluate guardrails for changes in regulatory requirements  and risk scenarios.

### Cross-References

- **bsi_aic4**: C4 SR-02
C4 SR-05
C4 SR-06 (Gap: No Gap)
- **eu_ai_act**: Article 9 (5) (a)
Article 15 (1)
Article 15 (2) (Gap: No Gap)
- **iso_42001**: 42001: A.6.1 Risk assessment for AI systems
42001: A.6.2.6 AI system Operation and monitoring
42001: A.6.3.2 Planning of AI-specific controls
42001: A.7.4 Quality of data for AI Systems
42001: A.8.3 AI system impact assessment
27001: 5.7 Threat Intelligence
27001: 8.8 Management of technical vulnerabilities
27001: 9.1 Monitoring
measurement
analysis and evaluation
27002: 8.12 Secure software development (Gap: No Gap)
- **nist_ai_600_1**: MS-2.5-006 (Gap: No Gap)

### CAIQ Questions

- **TVM-11.1**: Are processes, procedures, and technical measures to apply guardrails to the AI system defined and implemented?
- **TVM-11.2**: Are guardrails continuously evaluated for changes in regulatory requirements and risk scenarios?

---

## TVM-12: Threat Analysis and Modelling

**Type:** control
**Control Type:** AI-Specific
**Architectural Relevance:** Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data collection, Data curation, Data storage
- Development: Design, Training, Guardrails
- Evaluation/Validation: Evaluation, Validation/Red Teaming, Re-evaluation
- Deployment: AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Data deletion

### Specification

Define implement and evaluate threat analysis process and procedures to identify, assess and review the threat landscape for Cloud and AI systems. Build threat models according to industry best practices to inform the risk mitigation strategy.

### Cross-References

- **bsi_aic4**: C4 SR-01
C4 SR-02
C4 SR-03
C4 SR-04
C4 SR-05
C4 SR-06
C4 RE-05
C5 OPS-18 (Gap: No Gap)
- **eu_ai_act**: Article 9 (1)
Article 9 (2)
Article 15 (1)
Annex IV (2) (f) (Gap: Partial Gap)
- **iso_42001**: 42001: A.6.2.3/B.6.2.3 - Documentation of AI system design and development
42001: A/6.2.6/B.6.2.6 - AI system operation and monitoring
42001: A.7.2/B.7.2 - Data for development and enhancement of AI system
27001: A.5.7 - Threat intelligence (Gap: Partial Gap)
- **nist_ai_600_1**: MS-2.7-001
GV-1.1-001
GV-6.1-004 (Gap: Partial Gap)

### CAIQ Questions

- **TVM-12.1**: Are threat analysis processes and procedures defined, implemented, and evaluated to identify, assess, and review the threat landscape for Cloud and AI systems?
- **TVM-12.2**: Are threat models built according to industry best practices to inform the risk mitigation strategy?

---

## TVM-13: Threat Response

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Owned by the Cloud Service Provider (CSP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Shared Orchestrated Service Provider-Application Provider (Shared OSP-AP)

**Lifecycle Relevance:**
- Preparation: Data curation, Data storage, Resource provisioning, Team and expertise
- Development: Design, Training, Guardrails
- Evaluation/Validation: Evaluation, Validation/Red Teaming, Re-evaluation
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring
- Service Retirement: Data deletion, Model disposal

### Specification

Use a risk-based method for the prioritization and mitigation of threats, leveraging an industry-recognized framework to guide threat decision-making and protection measures.

### Cross-References

- **bsi_aic4**: C4 SR-02
C5 OPS-18 (Gap: No Gap)
- **eu_ai_act**: Article 9 (2) (Gap: Partial Gap)
- **iso_42001**: 27001: 8.8 Management of technical vulnerabilities
42001: A.6.2.6 AI system Operation and monitoring (Gap: No Gap)
- **nist_ai_600_1**: GV-1.1-001
MP-1.1-001 to
MP-3.2-003
MG-1.1-001 to
MG-3.3-002 (Gap: Partial Gap)

### CAIQ Questions

- **TVM-13.1**: Is a risk-based method for the prioritization and mitigation of threats,  used, leveraging an industry-recognized framework to guide threat decision-making and protection measures?

---

# Domain: Universal Endpoint Management

## UEM-01: Endpoint Devices Policy and Procedures

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared across the supply chain
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Orchestrated Service Provider-Application Provider (Shared OSP-AP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Resource provisioning
- Development: Design, Training, Guardrails, Supply Chain
- Evaluation/Validation: N/A
- Deployment: Orchestration, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring
- Service Retirement: Data deletion, Model disposal, Archiving

### Specification

Establish, document, approve, communicate, apply, evaluate and  maintain policies and procedures for all endpoints. Review and  update the policies and procedures at least annually or upon significant system changes.

### Cross-References

- **bsi_aic4**: C4 PC-02 (Gap: No Gap)
- **eu_ai_act**: No Mapping (Gap: Full Gap)
- **iso_42001**: 42001-A.2.2
42001-A.2.4
27001-A.5.1 (Gap: No Gap)
- **nist_ai_600_1**: GV-1.4-001
GV-4.1-001 (Gap: Partial Gap)

### CAIQ Questions

- **UEM-01.1**: Are policies and procedures established, documented, approved, communicated, applied, evaluated, and maintained for all endpoints?
- **UEM-01.2**: Are the policies and procedures reviewed and updated at least annually or upon significant system changes?

---

## UEM-02: Application and Service Approval

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Insecure supply chain, Insecure apps/plugins, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared across the supply chain
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Shared Application Provider-AI Customer (Shared AP-AIC)

**Lifecycle Relevance:**
- Preparation: Data storage
- Development: Guardrails
- Evaluation/Validation: N/A
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Data deletion

### Specification

Define, document, apply and evaluate a list of approved services, applications and sources of applications (stores) acceptable for use by  endpoints when accessing or storing organization-managed data.

### Cross-References

- **bsi_aic4**: C4 SR-06
C5 AM-02 (Gap: No Gap)
- **eu_ai_act**: No Mapping (Gap: Full Gap)
- **iso_42001**: ISO 42001 - A.4.3
ISO 42001 - A.4.4
ISO 42001 - A.9.4
ISO 27001 - A.5.9
ISO 27001 - A.5.10
ISO 27001 - A.8.1 (Gap: No Gap)
- **nist_ai_600_1**: GV-1.4-001
GV-1.4-002
GV-3.2-003 (Gap: Partial Gap)

### CAIQ Questions

- **UEM-02.1**: Is there a defined, documented, applicable and evaluated list containing approved services, applications, and the sources of applications (stores) acceptable for use by endpoints when accessing or storing organization-managed data?

---

## UEM-03: Compatibility

**Type:** control
**Control Type:** Cloud & AI Related
**Threat Categories:** Insecure supply chain, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared across the supply chain
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: N/A
- Development: N/A
- Evaluation/Validation: Validation/Red Teaming
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Continuous monitoring
- Service Retirement: N/A

### Specification

Define and implement a process for the validation of the endpoint device's compatibility with operating systems and applications.

### Cross-References

- **bsi_aic4**: C4 SR-02
C5 AM-05 (Gap: No Gap)
- **eu_ai_act**: No Mapping (Gap: Full Gap)
- **iso_42001**: ISO 42001 - A.4.5
ISO 42001 - 6.2.4
ISO 27001 - A.8.19
ISO 27001 - A.8.26 (Gap: No Gap)
- **nist_ai_600_1**: MS-2.6-005 (Gap: Partial Gap)

### CAIQ Questions

- **UEM-03.1**: Is a process defined and implemented to validate endpoint device compatibility with operating systems and applications?

---

## UEM-04: Endpoint Inventory

**Type:** control
**Control Type:** Cloud & AI Related
**Threat Categories:** Insecure supply chain, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared across the supply chain
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Owned by the Customer (AIC)

**Lifecycle Relevance:**
- Preparation: Data storage
- Development: Design, Guardrails
- Evaluation/Validation: N/A
- Deployment: Orchestration, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring
- Service Retirement: Data deletion

### Specification

Maintain an inventory of all endpoints used to store and process  company data.

### Cross-References

- **bsi_aic4**: C4 DM-03
C5 AM-01
C5 AM-05 (Gap: No Gap)
- **eu_ai_act**: Article 11
Annex IV (1), (4) (Gap: Partial Gap)
- **iso_42001**: ISO 42001 - A.4.5
ISO 27001 - A.5.9 (Gap: No Gap)
- **nist_ai_600_1**: GV-1.6-001 (Gap: No Gap)

### CAIQ Questions

- **UEM-04.1**: Is an inventory of all endpoints used to store and process company data maintained?

---

## UEM-05: Endpoint Management

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared across the supply chain
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Orchestrated Service Provider-Application Provider (Shared OSP-AP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data collection, Data curation, Data storage, Resource provisioning
- Development: Design, Training, Guardrails
- Evaluation/Validation: Evaluation, Validation/Red Teaming, Re-evaluation
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Archiving, Data deletion, Model disposal

### Specification

Define, implement and evaluate processes, procedures and technical measures to enforce policies and controls for all endpoints permitted  to access systems and/or store, transmit, or process organizational  data.

### Cross-References

- **bsi_aic4**: C4 SR-06
C5 AM-05 (Gap: No Gap)
- **eu_ai_act**: No Mapping (Gap: Full Gap)
- **iso_42001**: No Mapping for ISO 42001
ISO 27001 - A.8.1
ISO 27001 - A.8.26 (Gap: Partial Gap)
- **nist_ai_600_1**: MG-2.2-001
MS-2.7-001
MG-2.4-004 (Gap: No Gap)

### CAIQ Questions

- **UEM-05.1**: Are processes, procedures, and technical measures defined, implemented and evaluated, to enforce policies and controls for all endpoints permitted to access systems and/or store, transmit, or process organizational data?

---

## UEM-06: Automatic Lock Screen

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Sensitive data disclosure, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared across the supply chain
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: N/A
- Development: N/A
- Evaluation/Validation: N/A
- Deployment: N/A
- Delivery: N/A
- Service Retirement: N/A

### Specification

Configure all relevant interactive-use endpoints to require an  automatic lock screen.

### Cross-References

- **bsi_aic4**: C4 SR-06
C5 AM-05 (Gap: No Gap)
- **eu_ai_act**: No Mapping (Gap: Full Gap)
- **iso_42001**: No Mapping for ISO 42001
ISO 27001 - A.8.1 (Gap: Partial Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **UEM-06.1**: Are all relevant interactive-use endpoints configured to require an automatic lock screen?

---

## UEM-07: Operating Systems

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Compute, Application
**Threat Categories:** Model manipulation, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Orchestrated Service Provider-Application Provider (Shared OSP-AP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Resource provisioning
- Development: Training
- Evaluation/Validation: Validation/Red Teaming, Re-evaluation
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: N/A

### Specification

Manage changes to endpoint operating systems, patch levels, and/or applications through the company's change management processes.

### Cross-References

- **bsi_aic4**: C4 PF-07
C5 AM-02
C5 AM-05
C5 DEV-03 (Gap: Partial Gap)
- **eu_ai_act**: No Mapping (Gap: Full Gap)
- **iso_42001**: ISO 42001 - A.6.2.6
ISO 27001 - A.8.32 (Gap: No Gap)
- **nist_ai_600_1**: MG-3.1-003 (Gap: Partial Gap)

### CAIQ Questions

- **UEM-07.1**: Are changes to endpoint operating systems, patch levels, and/or applications managed through the organizational change management process?

---

## UEM-08: Storage Encryption

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Compute, Storage, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Insecure supply chain, Insecure apps/plugins, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared across the supply chain
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Shared Orchestrated Service Provider-Application Provider (Shared OSP-AP)

**Lifecycle Relevance:**
- Preparation: Data storage, Resource provisioning
- Development: Training
- Evaluation/Validation: Evaluation, Validation/Red Teaming, Re-evaluation
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Archiving, Data deletion, Model disposal

### Specification

Protect information from unauthorized disclosure on managed  endpoint devices with storage encryption.

### Cross-References

- **bsi_aic4**: C4 SR-06
C5 AM-06
C5 CRY-03 (Gap: No Gap)
- **eu_ai_act**: Recital 69 (pg.20)
Article 10
Article 15
Article 17 (Gap: Partial Gap)
- **iso_42001**: No Mapping for ISO 42001
ISO 27001 A.8.1
ISO 27001 A.8.5 (Gap: Partial Gap)
- **nist_ai_600_1**: MP-4.1-009
MS-2.7-005 (Gap: No Gap)

### CAIQ Questions

- **UEM-08.1**: Is information protected from unauthorized disclosure on managed endpoints with storage encryption?

---

## UEM-09: Anti-Malware Detection and Prevention

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Compute, Application
**Threat Categories:** Model/Service Failure, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Shared Orchestrated Service Provider-Application Provider (Shared OSP-AP)

**Lifecycle Relevance:**
- Preparation: Resource provisioning
- Development: Guardrails
- Evaluation/Validation: Evaluation
- Deployment: Orchestration, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring
- Service Retirement: N/A

### Specification

Configure managed endpoints with anti-malware detection and  prevention technology and services.

### Cross-References

- **bsi_aic4**: C4 SR-06
C5 OPS-04
C5 OPS-05 (Gap: No Gap)
- **eu_ai_act**: Recital 76 (pg.22)
Article 15 (Gap: Partial Gap)
- **iso_42001**: No Mapping for ISO 42001
ISO 27001 A.8.7 (Gap: Partial Gap)
- **nist_ai_600_1**: MG-3.2-005 (Gap: No Gap)

### CAIQ Questions

- **UEM-09.1**: Are anti-malware detection and prevention technology services configured on managed endpoints?

---

## UEM-10: Software Firewall

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Application
**Threat Categories:** Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared across the supply chain
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Shared Orchestrated Service Provider-Application Provider (Shared OSP-AP)

**Lifecycle Relevance:**
- Preparation: Resource provisioning
- Development: N/A
- Evaluation/Validation: N/A
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring
- Service Retirement: N/A

### Specification

Configure managed endpoints with properly configured software firewalls.

### Cross-References

- **bsi_aic4**: C4 SR-06
C5 AM-05 (Gap: No Gap)
- **eu_ai_act**: Recital 76 (pg.22)
Article 9 (Risk management)
Article 15
Article 17 (Quality management)
Annex IV (Technical documentation) (Gap: Partial Gap)
- **iso_42001**: No Mapping for ISO 42001
ISO 27001 A.8.1
ISO 27001 A.8.16 (Gap: Partial Gap)
- **nist_ai_600_1**: MG-3.2-005 (Gap: No Gap)

### CAIQ Questions

- **UEM-10.1**: Are software firewalls properly configured on managed endpoints?

---

## UEM-11: Data Loss Prevention

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Compute, Storage, Application, Data
**Threat Categories:** Sensitive data disclosure, Model theft, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data storage
- Development: Guardrails
- Evaluation/Validation: N/A
- Deployment: AI applications
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Data deletion

### Specification

Configure managed endpoints with Data Loss Prevention (DLP)  technologies and rules in accordance with a risk assessment.

### Cross-References

- **bsi_aic4**: C4 DM-02
C5 AM-05 (Gap: No Gap)
- **eu_ai_act**: No Mapping (Gap: Full Gap)
- **iso_42001**: No Mapping for ISO 42001
ISO 27001 A.8.1 (Gap: Partial Gap)
- **nist_ai_600_1**: MG-3.2-005 (Gap: No Gap)

### CAIQ Questions

- **UEM-11.1**: Are managed endpoints configured with data loss prevention (DLP) technologies and rules in accordance with a risk assessment?

---

## UEM-12: Remote Locate

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Application
**Threat Categories:** Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared Cloud Service Provider-Model Provider (Shared CSP-MP)
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Shared Orchestrated Service Provider-Application Provider (Shared OSP-AP)

**Lifecycle Relevance:**
- Preparation: Data collection
- Development: Design, Training, Guardrails, Supply Chain
- Evaluation/Validation: Evaluation, Validation/Red Teaming, Re-evaluation
- Deployment: AI applications
- Delivery: Continuous monitoring
- Service Retirement: N/A

### Specification

Enable remote geo-location capabilities for all managed mobile endpoints,  according to all applicable laws and regulations.

### Cross-References

- **bsi_aic4**: C4 SR-06
C5 AM-05 (Gap: No Gap)
- **eu_ai_act**: No Mapping (Gap: Full Gap)
- **iso_42001**: No Mapping for ISO 42001
ISO 27001 A.8.12 (Gap: Partial Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **UEM-12.1**: Are remote geolocation capabilities enabled for all managed mobile endpoints, according to all applicable laws and regulations?

---

## UEM-13: Remote Wipe

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Storage, Application, Data
**Threat Categories:** Sensitive data disclosure, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared across the supply chain
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Owned by the Orchestrated Service Provider (OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data storage
- Development: N/A
- Evaluation/Validation: N/A
- Deployment: AI applications
- Delivery: Operations, Maintenance, Continuous monitoring
- Service Retirement: Data deletion

### Specification

Define, implement and evaluate processes, procedures and technical measures to enable the deletion of company data remotely on managed endpoint devices.

### Cross-References

- **bsi_aic4**: C4 SR-06
C5 AM-05 (Gap: No Gap)
- **eu_ai_act**: No Mapping (Gap: Full Gap)
- **iso_42001**: No Mapping for ISO 42001
ISO 27001 A.8.1 (Gap: Partial Gap)
- **nist_ai_600_1**: No Mapping (Gap: Full Gap)

### CAIQ Questions

- **UEM-13.1**: Are processes, procedures, and technical measures defined, implemented, and evaluated to enable remote company data deletion on managed endpoint devices?

---

## UEM-14: Third-Party Endpoint Security Posture

**Type:** control
**Control Type:** Cloud & AI Related
**Architectural Relevance:** Physical, Network, Compute, Storage, Application, Data
**Threat Categories:** Model manipulation, Data poisoning, Sensitive data disclosure, Model theft, Model/Service Failure, Insecure supply chain, Insecure apps/plugins, Denial of Service, Loss of governance/compliance

**Ownership:**
- GenAI OPS/PI: Shared across the supply chain
- Model: Owned by the Model Provider (MP)
- Orchestrated Services: Shared Model Provider-Orchestrated Service Provider (Shared MP-OSP)
- Application: Owned by the Application Provider (AP)

**Lifecycle Relevance:**
- Preparation: Data collection, Data curation, Data storage, Resource provisioning
- Development: Training
- Evaluation/Validation: Evaluation, Validation/Red Teaming, Re-evaluation
- Deployment: Orchestration, AI Services supply chain, AI applications
- Delivery: Operations, Maintenance, Continuous monitoring, Continuous improvement
- Service Retirement: Archiving, Data deletion, Model disposal

### Specification

Define, implement and evaluate processes, procedures and technical and/or contractual measures to maintain proper security of third-party endpoints with access to organizational assets.

### Cross-References

- **bsi_aic4**: C4 SR-06
C5 AM-05 (Gap: No Gap)
- **eu_ai_act**: Article 25 (Gap: Partial Gap)
- **iso_42001**: ISO 42001 B.10.2
ISO 27001 A.5.21 (Gap: No Gap)
- **nist_ai_600_1**: GV-6.1-004
MG-3.1-001 (Gap: No Gap)

### CAIQ Questions

- **UEM-14.1**: Are processes, procedures, and technical and/or contractual measures defined, implemented, and evaluated to maintain proper security of third-party endpoints with access to organizational assets?

---

