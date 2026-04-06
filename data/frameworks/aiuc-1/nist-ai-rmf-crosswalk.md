# AIUC-1 × NIST AI RMF Complete Crosswalk

## Overview

This document maps AIUC-1 requirements to the NIST AI Risk Management Framework (AI RMF), which organizes governance around four core functions: **Govern**, **Map**, **Measure**, and **Manage**.

AIUC-1 operationalizes the NIST AI RMF by translating high-level actions into specific, auditable controls and providing concrete implementation guidance for key areas such as harmful output prevention, third-party testing and risk management practices.

---

## NIST AI RMF GOVERN Function Mappings

### GOVERN 1: Foundational, Policy-Based Activities

| NIST Reference | Description | AIUC-1 Requirements |
|---|---|---|
| **GOVERN 1.1** | Legal and regulatory requirements involving AI are understood, managed, and documented. | E012: Document regulatory compliance |
| **GOVERN 1.2** | Trustworthy AI characteristics integrated into organizational policies, processes, and procedures. | E010: Establish AI acceptable use policy; E017: Document system transparency policy |
| **GOVERN 1.3** | Processes and procedures in place to determine needed level of risk management activities based on organizational risk tolerance. | C001: Define AI risk taxonomy; E013: Implement quality management system |
| **GOVERN 1.4** | Risk management process and outcomes established through transparent policies, procedures, and controls based on organizational risk priorities. | C001: Define AI risk taxonomy; E013: Implement quality management system |
| **GOVERN 1.5** | Ongoing monitoring and periodic review of risk management process and outcomes; roles and responsibilities defined. | B002: Detect adversarial input; C008: Monitor AI risk categories; E009: Monitor third-party access |
| **GOVERN 1.6** | Mechanisms in place to inventory AI systems, resourced according to organizational risk priorities. | E011: Record processing locations; E017: Document system transparency policy |
| **GOVERN 1.7** | Processes and procedures for decommissioning and phasing out AI systems safely without increasing risks. | E008: Review internal processes; E012: Document regulatory compliance |

### GOVERN 2: Risk Management and Accountability

| NIST Reference | Description | AIUC-1 Requirements |
|---|---|---|
| **GOVERN 2.1** | Roles, responsibilities, and lines of communication related to mapping, measuring, and managing AI risks documented and clear throughout organization. | E004: Assign accountability; E007: Document system change approvals |
| **GOVERN 2.2** | Personnel and partners receive AI risk management training to perform duties consistent with policies and procedures. | *(No directly mapped AIUC-1 requirement)* |
| **GOVERN 2.3** | Executive leadership takes responsibility for decisions about risks associated with AI system development and deployment. | E004: Assign accountability; E007: Document system change approvals |

### GOVERN 3: Cross-Functional Risk Considerations

| NIST Reference | Description | AIUC-1 Requirements |
|---|---|---|
| **GOVERN 3.1** | Decision-making informed by diverse team reflecting demographic, disciplinary, and experiential diversity. | *(No directly mapped AIUC-1 requirement)* |
| **GOVERN 3.2** | Policies and procedures define and differentiate roles for human-AI configurations and system oversight. | C007: Flag high risk outputs; C009: Enable real-time feedback and intervention |

### GOVERN 4: Organizational Practices and Culture

| NIST Reference | Description | AIUC-1 Requirements |
|---|---|---|
| **GOVERN 4.1** | Organizational policies and practices foster critical thinking and safety-first mindset in AI design, development, deployment, and use. | *(No directly mapped AIUC-1 requirement)* |
| **GOVERN 4.2** | Teams document risks and potential impacts of AI technology; communicate impacts broadly. | C001: Define AI risk taxonomy |
| **GOVERN 4.3** | Organizational practices enable AI testing, incident identification, and information sharing. | B001: Third-party testing of adversarial robustness; C002: Conduct pre-deployment testing; C010: Third-party testing for harmful outputs; C011: Third-party testing for out-of-scope outputs; C012: Third-party testing for customer-defined risk; D002: Third-party testing for hallucinations; D004: Third-party testing of tool calls; E001: AI failure plan for security breaches; E002: AI failure plan for harmful outputs; E003: AI failure plan for hallucinations |

### GOVERN 5: External Feedback Integration

| NIST Reference | Description | AIUC-1 Requirements |
|---|---|---|
| **GOVERN 5.1** | Policies and practices in place to collect, consider, prioritize, and integrate external feedback regarding potential individual and societal impacts. | E008: Review internal processes |
| **GOVERN 5.2** | Mechanisms established to regularly incorporate adjudicated feedback from relevant AI actors into system design and implementation. | E008: Review internal processes |

### GOVERN 6: Third-Party Risk Management

| NIST Reference | Description | AIUC-1 Requirements |
|---|---|---|
| **GOVERN 6.1** | Policies and procedures address AI risks associated with third-party entities, including intellectual property infringement risks. | A007: Prevent IP violations; C001: Define AI risk taxonomy; D003: Restrict unsafe tool calls; D004: Third-party testing of tool calls |
| **GOVERN 6.2** | Contingency processes in place to handle failures or incidents in high-risk third-party data or AI systems. | *(No directly mapped AIUC-1 requirement)* |

---

## NIST AI RMF MAP Function Mappings

### MAP 1: Context and Stakeholder Understanding

| NIST Reference | Description | AIUC-1 Requirements |
|---|---|---|
| **MAP 1.1** | Intended purpose, beneficial uses, context-specific laws, norms, expectations, and deployment settings understood and documented. | E012: Document regulatory compliance |
| **MAP 1.2** | Interdisciplinary AI actors with diverse competencies and documentation of their participation. | *(No directly mapped AIUC-1 requirement)* |
| **MAP 1.3** | Organization's mission and relevant goals for the AI technology understood and documented. | *(No directly mapped AIUC-1 requirement)* |
| **MAP 1.4** | Business value or context of business use clearly defined or re-evaluated. | *(No directly mapped AIUC-1 requirement)* |
| **MAP 1.5** | Organizational risk tolerances determined and documented. | C001: Define AI risk taxonomy |
| **MAP 1.6** | System requirements elicited from and understood by relevant AI actors; design decisions consider socio-technical implications. | E010: Establish AI acceptable use policy; E014: Share transparency reports; E017: Document system transparency policy |

### MAP 2: Task Understanding and System Capability Assessment

| NIST Reference | Description | AIUC-1 Requirements |
|---|---|---|
| **MAP 2.1** | Specific task and implementation methods that the AI system will support are defined. | A003: Limit AI agent data collection; B006: Prevent unauthorized AI agent actions |
| **MAP 2.2** | Information about AI system's knowledge limits and how output may be utilized and overseen by humans documented. | C004: Prevent out-of-scope outputs; C011: Third-party testing for out-of-scope outputs; E016: Implement AI disclosure mechanisms |
| **MAP 2.3** | Scientific integrity and Test, Evaluation, Validation, and Verification (TEVV) considerations identified and documented. | *(No directly mapped AIUC-1 requirement)* |

### MAP 3: Impact and Risk Analysis

| NIST Reference | Description | AIUC-1 Requirements |
|---|---|---|
| **MAP 3.1** | Potential benefits of intended AI system functionality and performance examined and documented. | *(No directly mapped AIUC-1 requirement)* |
| **MAP 3.2** | Potential costs (including non-monetary) resulting from expected or realized AI errors examined and documented. | *(No directly mapped AIUC-1 requirement)* |
| **MAP 3.3** | Targeted application scope specified and documented based on system capability and established context. | E010: Establish AI acceptable use policy |
| **MAP 3.4** | Processes for operator and practitioner proficiency with AI system performance defined, assessed, and documented. | C004: Prevent out-of-scope outputs; E010: Establish AI acceptable use policy; E016: Implement AI disclosure mechanisms |
| **MAP 3.5** | Processes for human oversight defined, assessed, and documented in accordance with organizational policies. | C007: Flag high risk outputs; C009: Enable real-time feedback and intervention; E004: Assign accountability; E007: Document system change approvals |

### MAP 4: Legal and Compliance Review

| NIST Reference | Description | AIUC-1 Requirements |
|---|---|---|
| **MAP 4.1** | Approaches for mapping AI technology and legal risks of components in place, followed, and documented, including third-party intellectual property risks. | A007: Prevent IP violations; E012: Document regulatory compliance |
| **MAP 4.2** | Internal risk controls for AI system components, including third-party technologies, identified and documented. | C002: Conduct pre-deployment testing; E005: Assess cloud vs on-prem processing; E006: Conduct vendor due diligence |

### MAP 5: Impact and Benefit Assessment

| NIST Reference | Description | AIUC-1 Requirements |
|---|---|---|
| **MAP 5.1** | Likelihood and magnitude of each identified impact examined and documented based on expected use, similar contexts, public incidents, external feedback, or other data. | C001: Define AI risk taxonomy |
| **MAP 5.2** | Practices and personnel supporting regular engagement with relevant AI actors and integrating feedback about positive, negative, and unanticipated impacts. | E014: Share transparency reports |

---

## NIST AI RMF MEASURE Function Mappings

### MEASURE 1: Metrics and Risk Selection

| NIST Reference | Description | AIUC-1 Requirements |
|---|---|---|
| **MEASURE 1.1** | Approaches and metrics for measurement of enumerated AI risks selected, starting with most significant risks. Risks that cannot be measured properly documented. | C001: Define AI risk taxonomy |
| **MEASURE 1.2** | Appropriateness of AI metrics and effectiveness of existing controls regularly assessed and updated, including error reports and community impact analysis. | E008: Review internal processes |
| **MEASURE 1.3** | Internal experts not serving as front-line developers and/or independent assessors involved in regular assessments. Domain experts and affected communities consulted as necessary. | C010: Third-party testing for harmful outputs; C011: Third-party testing for out-of-scope outputs; C012: Third-party testing for customer-defined risk; D002: Third-party testing for hallucinations; D004: Third-party testing of tool calls |

### MEASURE 2: Evaluation, Assessment, and Testing

| NIST Reference | Description | AIUC-1 Requirements |
|---|---|---|
| **MEASURE 2.1** | Test sets, metrics, and tool details used during TEVV documented. | B001: Third-party testing of adversarial robustness; C002: Conduct pre-deployment testing; C010-C012: Third-party testing for various risks; D002: Third-party testing for hallucinations; D004: Third-party testing of tool calls |
| **MEASURE 2.2** | Evaluations involving human subjects meet applicable requirements and are representative of relevant population. | *(No directly mapped AIUC-1 requirement)* |
| **MEASURE 2.3** | AI system performance or assurance criteria measured qualitatively or quantitatively and demonstrated for deployment-similar conditions. | C002: Conduct pre-deployment testing |
| **MEASURE 2.4** | Functionality and behavior of AI system and components monitored when in production. | B002: Detect adversarial input; C008: Monitor AI risk categories; E010: Establish AI acceptable use policy; E015: Log model activity |
| **MEASURE 2.5** | AI system demonstrated to be valid and reliable; limitations of generalizability documented. | C002: Conduct pre-deployment testing; D001: Prevent hallucinated outputs; D002: Third-party testing for hallucinations |
| **MEASURE 2.6** | AI system regularly evaluated for safety risks; demonstrated to be safe with residual risk not exceeding tolerance; can fail safely. | B001: Third-party testing of adversarial robustness; C010-C012: Third-party safety testing; D004: Third-party testing of tool calls |
| **MEASURE 2.7** | AI system security and resilience evaluated and documented. | B001: Third-party testing of adversarial robustness; B002: Detect adversarial input; B004: Prevent AI endpoint scraping; B005: Implement real-time input filtering; F001: Prevent AI cyber misuse |
| **MEASURE 2.8** | Risks associated with transparency and accountability examined and documented. | E004: Assign accountability; E007: Document system change approvals; E014: Share transparency reports; E015: Log model activity; E016: Implement AI disclosure mechanisms; E017: Document system transparency policy |
| **MEASURE 2.9** | AI model explained, validated, and documented; output interpreted within context to inform responsible use and governance. | E014: Share transparency reports; E017: Document system transparency policy |
| **MEASURE 2.10** | Privacy risk of the AI system examined and documented. | A001: Establish input data policy; A005: Prevent cross-customer data exposure; A006: Prevent PII leakage; B009: Limit output over-exposure; C001: Define AI risk taxonomy |
| **MEASURE 2.11** | Fairness and bias evaluated; results documented. | C001: Define AI risk taxonomy; C003: Prevent harmful outputs; C010: Third-party testing for harmful outputs |
| **MEASURE 2.12** | Environmental impact and sustainability of AI model training and management assessed and documented. | *(No directly mapped AIUC-1 requirement)* |
| **MEASURE 2.13** | Effectiveness of employed TEVV metrics and processes evaluated and documented. | E008: Review internal processes |

### MEASURE 3: Ongoing and Emergent Risk Monitoring

| NIST Reference | Description | AIUC-1 Requirements |
|---|---|---|
| **MEASURE 3.1** | Approaches, personnel, and documentation in place to regularly identify and track existing, unanticipated, and emergent AI risks. | B002: Detect adversarial input; C001: Define AI risk taxonomy |
| **MEASURE 3.2** | Risk tracking approaches considered for settings where AI risks are difficult to assess using current measurement techniques. | *(No directly mapped AIUC-1 requirement)* |
| **MEASURE 3.3** | Feedback processes for end users and impacted communities to report problems and appeal outcomes established and integrated into evaluation metrics. | C009: Enable real-time feedback and intervention |

### MEASURE 4: Performance Metrics and Validation

| NIST Reference | Description | AIUC-1 Requirements |
|---|---|---|
| **MEASURE 4.1** | Measurement approaches for identifying AI risks connected to deployment context(s) and informed through consultation with domain experts and end users. | C010-C012: Third-party context-specific testing; D002: Third-party testing for hallucinations; D004: Third-party testing of tool calls |
| **MEASURE 4.2** | Measurement results regarding AI system trustworthiness validated through input from domain experts and relevant AI actors; results documented. | C010-C012: Third-party validation; D002: Third-party testing for hallucinations; D004: Third-party testing of tool calls; E014: Share transparency reports |
| **MEASURE 4.3** | Measurable performance improvements or declines identified and documented based on relevant actor consultations and field data. | C002: Conduct pre-deployment testing; C008: Monitor AI risk categories; E007: Document system change approvals; E017: Document system transparency policy |

---

## NIST AI RMF MANAGE Function Mappings

### MANAGE 1: Response Planning and Risk Treatment

| NIST Reference | Description | AIUC-1 Requirements |
|---|---|---|
| **MANAGE 1.1** | Determination made whether AI system achieves intended purpose and stated objectives; whether development or deployment should proceed. | C002: Conduct pre-deployment testing; E007: Document system change approvals |
| **MANAGE 1.2** | Treatment of documented AI risks prioritized based on impact, likelihood, or available resources or methods. | C001: Define AI risk taxonomy |
| **MANAGE 1.3** | Responses to high-priority risks developed, planned, and documented (mitigate, transfer, avoid, or accept). | C001: Define AI risk taxonomy; E001: AI failure plan for security breaches; E002: AI failure plan for harmful outputs; E003: AI failure plan for hallucinations |
| **MANAGE 1.4** | Negative residual risks to downstream acquirers and end users documented. | C001: Define AI risk taxonomy; C005: Prevent customer-defined high risk outputs |

### MANAGE 2: Resource Management and System Sustainment

| NIST Reference | Description | AIUC-1 Requirements |
|---|---|---|
| **MANAGE 2.1** | Resources required to manage AI risks taken into account, along with viable non-AI alternatives. | *(No directly mapped AIUC-1 requirement)* |
| **MANAGE 2.2** | Mechanisms in place and applied to sustain value of deployed AI systems. | C010-C012: Ongoing third-party testing; D002: Third-party testing for hallucinations; D004: Third-party testing of tool calls |
| **MANAGE 2.3** | Procedures followed to respond to and recover from previously unknown risk when identified. | *(No directly mapped AIUC-1 requirement)* |
| **MANAGE 2.4** | Mechanisms in place and responsibilities assigned to supersede, disengage, or deactivate AI systems demonstrating inconsistent performance. | *(No directly mapped AIUC-1 requirement)* |

### MANAGE 3: Third-Party Risk Monitoring

| NIST Reference | Description | AIUC-1 Requirements |
|---|---|---|
| **MANAGE 3.1** | AI risks and benefits from third-party resources regularly monitored; risk controls applied and documented. | C008: Monitor AI risk categories |
| **MANAGE 3.2** | Pre-trained models used for development monitored as part of regular AI system monitoring and maintenance. | *(No directly mapped AIUC-1 requirement)* |

### MANAGE 4: Post-Deployment and Incident Management

| NIST Reference | Description | AIUC-1 Requirements |
|---|---|---|
| **MANAGE 4.1** | Post-deployment monitoring plans implemented, including mechanisms for capturing end-user input, appeal and override, decommissioning, incident response, recovery, and change management. | C008: Monitor AI risk categories; E009: Monitor third-party access |
| **MANAGE 4.2** | Measurable activities for continual improvements integrated into AI system updates; regular engagement with interested parties. | E008: Review internal processes; E014: Share transparency reports |
| **MANAGE 4.3** | Incidents and errors communicated to relevant AI actors including affected communities; processes for tracking, responding, and recovering documented. | E001: AI failure plan for security breaches; E002: AI failure plan for harmful outputs; E003: AI failure plan for hallucinations; E014: Share transparency reports |

---

## Key Observations

1. **Alignment Breadth**: AIUC-1 requirements map across all four NIST AI RMF functions, with the most comprehensive coverage in the GOVERN 4.3 and MEASURE 2 sections focusing on testing and validation.

2. **Testing and Validation Emphasis**: The framework places significant emphasis on third-party testing requirements (B001, C010-C012, D002, D004), directly supporting NIST's MEASURE and GOVERN functions around testing and incident sharing.

3. **Governance Gaps**: Several NIST requirements (particularly around diverse decision-making, training, cultural change, and resource allocation) have no directly mapped AIUC-1 controls, suggesting those areas fall outside AIUC-1's current scope.

4. **Accountability and Documentation**: Strong alignment in requirements around documentation (E-series controls), risk taxonomy definition (C001), and accountability assignment (E004, E007).

5. **Third-Party and Vendor Management**: Comprehensive coverage through GOVERN 6, including IP protection (A007) and vendor due diligence (E006).

---

*Source: [AIUC-1 × NIST AI RMF Crosswalk](https://www.aiuc-1.com/crosswalks/nist-ai-rmf)*
*Last updated: July 22, 2025*
