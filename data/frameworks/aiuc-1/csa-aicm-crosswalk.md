# AIUC-1 × CSA AICM Crosswalk

## Overview

AIUC-1 aligns with the Cloud Security Alliance's AI Controls Matrix (CSA AICM). The certification addresses key controls including adversarial robustness, system transparency, and documentation of criteria for cloud & on-prem processing while maintaining a significantly lower compliance burden than CSA AICM's broader scope.

The framework avoids duplicating controls in areas where CSA leads, such as data center infrastructure, physical server security, and other domains outside of the AIUC-1 scope.

---

## Audit & Assurance (A&A)

| CSA Control ID | Control Name | AIUC-1 Requirements | Gap Status |
|---|---|---|---|
| A&A-01 | Audit and Assurance Policy and Procedures | E008: Review internal processes | Partial Gap |
| A&A-02 | Independent Assessments | C010, C012, E008 | Full Gap |
| A&A-03 | Risk Based Planning Assessment | E008 | Full Gap |
| A&A-04 | Requirements Compliance | E012: Document regulatory compliance | No Gap |
| A&A-05 | Audit Management Process | C001, E008, E013 | Partial Gap |
| A&A-06 | Remediation | C001, E008, E014 | Partial Gap |

## Application & Interface Security (AIS)

| CSA Control ID | Control Name | AIUC-1 Requirements | Gap Status |
|---|---|---|---|
| AIS-01 | Application and Interface Security Policy | E004, E007, E008, E013 | No Gap |
| AIS-02 | Application Security Baseline Requirements | B008, E008 | Partial Gap |
| AIS-03 | Application Security Metrics | E013 | Partial Gap |
| AIS-04 | Secure Application Development Lifecycle | C002, E004 | Partial Gap |
| AIS-05 | Application Security Testing | C002, D002, D004, E005 | No Gap |
| AIS-06 | Secure Application Deployment | B008, C002, D003 | No Gap |
| AIS-07 | Application Vulnerability Remediation | B001, C002, C006 | Partial Gap |
| AIS-08 | Input Validation | B001, B002, B005 | No Gap |
| AIS-09 | Output Validation | A007, B003, B009, C003, C004, C006, D001, D002 | No Gap |
| AIS-10 | API Security | B002, B004, D003, E009 | No Gap |
| AIS-11 | Agents Security Boundaries | A003, B006, D003 | No Gap |
| AIS-12 | Source Code Management | C002 | No Gap |
| AIS-13 | AI Sandboxing | D003 | Partial Gap |
| AIS-14 | AI Cache Protection | B008 | Partial Gap |
| AIS-15 | Prompt Differentiation | B003, B005 | Full Gap |

## Business Continuity & Resilience (BCR)

| CSA Control ID | Control Name | AIUC-1 Requirements | Gap Status |
|---|---|---|---|
| BCR-01 | Business Continuity Management Policy | E008 | Full Gap |
| BCR-02 | Risk Assessment and Impact Analysis | C001, E013 | Partial Gap |
| BCR-03 | Business Continuity Strategy | None | Full Gap |
| BCR-04 | Business Continuity Planning | None | Full Gap |
| BCR-05 | Documentation | None | Full Gap |
| BCR-06 | Business Continuity Exercises | None | Full Gap |
| BCR-07 | Communication | None | Full Gap |
| BCR-08 | Backup | None | Full Gap |
| BCR-09 | Disaster Response Plan | E001, E002, E003 | Full Gap |
| BCR-10 | Response Plan Exercise | E001, E002, E003 | Partial Gap |
| BCR-11 | Equipment Redundancy | None | Full Gap |

## Change & Configuration Control (CCC)

| CSA Control ID | Control Name | AIUC-1 Requirements | Gap Status |
|---|---|---|---|
| CCC-01 | Change Management Policy and Procedures | E004, E007 | Partial Gap |
| CCC-02 | Quality Testing | C002, E013 | Partial Gap |
| CCC-03 | Change Management Technology | C001, E004, E007 | No Gap |
| CCC-04 | Change Authorization | E007 | No Gap |
| CCC-05 | Change Agreements | E004, E007 | Partial Gap |
| CCC-06 | Change Management Baseline | E007 | Full Gap |
| CCC-07 | Detection of Baseline Deviation | None | Full Gap |
| CCC-08 | Exception Management | None | Full Gap |
| CCC-09 | Change Restoration | E008 | No Gap |

## Cryptography, Encryption & Key Management (CEK)

| CSA Control ID | Control Name | AIUC-1 Requirements | Gap Status |
|---|---|---|---|
| CEK-01 | Encryption and Key Management Policy | B008 | Partial Gap |
| CEK-02 | CEK Roles and Responsibilities | E004 | No Gap |
| CEK-03 | Data Encryption | B008 | No Gap |
| CEK-04 | Encryption Algorithm | B008 | Partial Gap |
| CEK-05 | Encryption Change Management | None | No Gap |
| CEK-06 | Encryption Change Cost Benefit Analysis | None | Full Gap |
| CEK-07 | Encryption Risk Management | C001 | Partial Gap |
| CEK-08 | Customer Key Management Capability | None | Full Gap |
| CEK-09 | Encryption and Key Management Audit | E008 | Partial Gap |
| CEK-10 | Key Generation | B008 | Partial Gap |
| CEK-11 | Key Purpose | B008 | Partial Gap |
| CEK-12 | Key Rotation | B008 | Partial Gap |
| CEK-13 | Key Revocation | B008 | Partial Gap |
| CEK-14 | Key Destruction | B008 | Partial Gap |
| CEK-15 | Key Activation | B008 | Partial Gap |
| CEK-16 | Key Suspension | B008 | Partial Gap |
| CEK-17 | Key Deactivation | B008 | Partial Gap |
| CEK-18 | Key Archival | B008 | Partial Gap |
| CEK-19 | Key Compromise | B008 | Partial Gap |
| CEK-20 | Key Recovery | B008 | Partial Gap |
| CEK-21 | Key Inventory Management | B008 | Partial Gap |

## Data Center & Site Security (DCS)

| CSA Control ID | Control Name | AIUC-1 Requirements | Gap Status |
|---|---|---|---|
| DCS-01 | Off-Site Equipment Disposal Policy | E005 | Full Gap |
| DCS-02 | Off-Site Transfer Authorization Policy | E005 | Full Gap |
| DCS-03 | Secure Area Policy and Procedures | E005 | Full Gap |
| DCS-04 | Secure Media Transportation Policy | E005 | Full Gap |
| DCS-05 | Assets Classification | E005 | Full Gap |
| DCS-06 | Assets Cataloguing and Tracking | E005 | Full Gap |
| DCS-07 | Controlled Physical Access Points | E005 | Full Gap |
| DCS-08 | Equipment Identification | E005 | Full Gap |
| DCS-09 | Secure Area Authorization | E005 | Full Gap |
| DCS-10 | Surveillance System | E005 | Full Gap |
| DCS-11 | Adverse Event Response Training | E005 | Full Gap |
| DCS-12 | Cabling Security | E005 | Full Gap |
| DCS-13 | Environmental Systems | E005 | Full Gap |
| DCS-14 | Secure Utilities | E005 | Full Gap |
| DCS-15 | Equipment Location | E005 | Full Gap |

## Data Security & Privacy (DSP)

| CSA Control ID | Control Name | AIUC-1 Requirements | Gap Status |
|---|---|---|---|
| DSP-01 | Security and Privacy Policy and Procedures | A004 | Partial Gap |
| DSP-02 | Secure Disposal | A004 | Partial Gap |
| DSP-03 | Data Inventory | None | Full Gap |
| DSP-04 | Data Classification | None | Full Gap |
| DSP-05 | Data Flow Documentation | None | Full Gap |
| DSP-06 | Data Ownership and Stewardship | None | Full Gap |
| DSP-07 | Data Protection by Design and Default | A003, A004, B006, B007, B008 | No Gap |
| DSP-08 | Data Privacy by Design and Default | A002, A003, A004, B007 | Partial Gap |
| DSP-09 | Data Protection Impact Assessment | A001, C001, E008, E013 | Partial Gap |
| DSP-10 | Sensitive Data Transfer | A004, A006, E012 | No Gap |
| DSP-11 | Personal Data Access, Reversal, Rectification and Deletion | A001 | No Gap |
| DSP-12 | Limitation of Purpose in Personal Data Processing | A001, A004, A006 | No Gap |
| DSP-13 | Personal Data Sub-processing | A001, A006, E011 | No Gap |
| DSP-14 | Disclosure of Data Sub-processors | A001 | No Gap |
| DSP-15 | Limitation of Production Data Use | A001 | No Gap |
| DSP-16 | Data Retention and Deletion | A001, A002, A004 | No Gap |
| DSP-17 | Sensitive Data Protection | A006 | No Gap |
| DSP-18 | Disclosure Notification | E012 | No Gap |
| DSP-19 | Data Location | E011 | No Gap |
| DSP-20 | Data Provenance and Transparency | A001, E017 | Partial Gap |
| DSP-21 | Data Poisoning Prevention & Detection | None | No Gap |
| DSP-22 | Privacy Enhancing Technologies | A003, A005 | Partial Gap |
| DSP-23 | Data Integrity Check | A001 | Partial Gap |
| DSP-24 | Data Differentiation and Relevance | None | Partial Gap |

## Governance & Risk Compliance (GRC)

| CSA Control ID | Control Name | AIUC-1 Requirements | Gap Status |
|---|---|---|---|
| GRC-01 | Governance Program Policy and Procedures | None | Full Gap |
| GRC-02 | Risk Management Program | C001, C008, E013, F001, F002 | No Gap |
| GRC-03 | Organizational Policy Reviews | E008 | No Gap |
| GRC-04 | Policy Exception Process | None | Full Gap |
| GRC-05 | Information Security Program | None | Full Gap |
| GRC-06 | Governance Responsibility Model | E004 | Full Gap |
| GRC-07 | Information System Regulatory Mapping | E012 | No Gap |
| GRC-08 | Special Interest Groups | None | Full Gap |
| GRC-09 | Acceptable Use of the AI Service | C003, C004, C005, E010, F001, F002 | No Gap |
| GRC-10 | AI Impact Assessment | E013, F001, F002 | Full Gap |
| GRC-11 | Bias and Fairness Assessment | C003, C010 | No Gap |
| GRC-12 | Ethics Committee | F001, F002 | Full Gap |
| GRC-13 | Explainability Requirement | E017 | Partial Gap |
| GRC-14 | Explainability Evaluation | E014, E017 | No Gap |
| GRC-15 | Human Supervision | C007, C009, E016 | No Gap |

## Human Resources Security (HRS)

| CSA Control ID | Control Name | AIUC-1 Requirements | Gap Status |
|---|---|---|---|
| HRS-01 | Background Screening Policy and Procedures | None | Full Gap |
| HRS-02 | Acceptable Use of Technology Policy and Procedures | None | Full Gap |
| HRS-03 | Clean Desk Policy and Procedures | None | Full Gap |
| HRS-04 | Remote and Home Working Policy and Procedures | None | Full Gap |
| HRS-05 | Asset Returns | None | Full Gap |
| HRS-06 | Employment Termination | None | Full Gap |
| HRS-07 | Employment Agreement Process | None | Full Gap |
| HRS-08 | Employment Agreement Content | None | Full Gap |
| HRS-09 | Personnel Roles and Responsibilities | None | Full Gap |
| HRS-10 | Non-Disclosure Agreements | E012 | Full Gap |
| HRS-11 | Security Awareness Training | None | Full Gap |
| HRS-12 | Personal and Sensitive Data Awareness and Training | A006 | Full Gap |
| HRS-13 | Compliance User Responsibility | None | Full Gap |
| HRS-14 | AI Competency Training | None | Full Gap |
| HRS-15 | AI Acceptable Use | None | Full Gap |

## Infrastructure & Virtualization Security (I&S)

| CSA Control ID | Control Name | AIUC-1 Requirements | Gap Status |
|---|---|---|---|
| I&S-01 | Infrastructure and Virtualization Security Policy | None | Full Gap |
| I&S-02 | Capacity and Resource Planning | E013 | Full Gap |
| I&S-03 | Network Security | None | Full Gap |
| I&S-04 | OS Hardening and Base Controls | None | Full Gap |
| I&S-05 | Production and Non-Production Environments | None | Full Gap |
| I&S-06 | Segmentation and Segregation | A005 | Full Gap |
| I&S-07 | Migration to Hosted Environments | None | Full Gap |
| I&S-08 | Network Architecture Documentation | None | Full Gap |
| I&S-09 | Network Defense | None | Full Gap |

## Identity & Access Management (IAM)

| CSA Control ID | Control Name | AIUC-1 Requirements | Gap Status |
|---|---|---|---|
| IAM-01 | Identity and Access Management Policy and Procedures | B007 | Partial Gap |
| IAM-02 | Strong Password Policy and Procedures | B007 | Full Gap |
| IAM-03 | Identity Inventory | B007, E008 | No Gap |
| IAM-04 | Separation of Duties | B007, B008 | No Gap |
| IAM-05 | Least Privilege | B007 | No Gap |
| IAM-06 | User Access Provisioning | B007 | No Gap |
| IAM-07 | User Access Changes and Revocation | B007 | No Gap |
| IAM-08 | User Access Review | B007, E008 | No Gap |
| IAM-09 | Segregation of Privileged Access Roles | B007 | Partial Gap |
| IAM-10 | Management of Privileged Access Roles | B007 | Partial Gap |
| IAM-11 | Customers' Approval for Agreed Privileged Access Roles | None | Full Gap |
| IAM-12 | Safeguard Logs Integrity | None | Full Gap |
| IAM-13 | Uniquely Identifiable Users | B007 | Partial Gap |
| IAM-14 | Strong Authentication | B007, B008 | Partial Gap |
| IAM-15 | Passwords and Secrets Management | B007 | Full Gap |
| IAM-16 | Authorization Mechanisms | B007 | Partial Gap |
| IAM-17 | Knowledge Access Control - Need to Know | A003, B007 | Partial Gap |
| IAM-18 | Output Modification and Special Authorization | B007 | Partial Gap |
| IAM-19 | Agent Access Restriction | A003, B006 | No Gap |

## Interoperability & Portability (IPY)

| CSA Control ID | Control Name | AIUC-1 Requirements | Gap Status |
|---|---|---|---|
| IPY-01 | Interoperability and Portability Policy and Procedures | None | Full Gap |
| IPY-02 | Application Interface Availability | None | Full Gap |
| IPY-03 | Secure Interoperability and Portability Management | None | Full Gap |
| IPY-04 | Data Portability Contractual Obligations | None | Full Gap |

## Logging & Monitoring (LOG)

| CSA Control ID | Control Name | AIUC-1 Requirements | Gap Status |
|---|---|---|---|
| LOG-01 | Logging and Monitoring Policy and Procedures | E015 | Partial Gap |
| LOG-02 | Audit Logs Protection | None | Partial Gap |
| LOG-03 | Security Monitoring and Alerting | E015 | Partial Gap |
| LOG-04 | Audit Logs Access and Accountability | B007, E015 | No Gap |
| LOG-05 | Audit Logs Monitoring and Response | E009, E015 | Partial Gap |
| LOG-06 | Clock Synchronization | E015 | Full Gap |
| LOG-07 | Logging Scope | E008, E015 | No Gap |
| LOG-08 | Log Records | E015 | No Gap |
| LOG-09 | Log Protection | B007, E015 | No Gap |
| LOG-10 | Encryption Monitoring and Reporting | E014, E015 | Partial Gap |
| LOG-11 | Transaction / Activity Logging | E015 | Partial Gap |
| LOG-12 | Access Control Logs | B007, E015 | Full Gap |
| LOG-13 | Failures and Anomalies Reporting | E014, E015 | Full Gap |
| LOG-14 | Input Monitoring | B002, B005, E015 | Partial Gap |
| LOG-15 | Output Monitoring | C003, C004, C005, E015 | No Gap |

## Model Development & Security (MDS)

| CSA Control ID | Control Name | AIUC-1 Requirements | Gap Status |
|---|---|---|---|
| MDS-01 | Training Pipeline Security | B008 | Partial Gap |
| MDS-02 | Model Artifact Scanning | B008, E013 | Partial Gap |
| MDS-03 | Model Documentation | E017 | No Gap |
| MDS-04 | Model Documentation Requirements | A003, E017 | No Gap |
| MDS-05 | Model Documentation Validation | E017 | Partial Gap |
| MDS-06 | Adversarial Attack Analysis | B001, D002 | No Gap |
| MDS-07 | Robustness against Adversarial Attack / Model Hardening | B001, B002, D002 | No Gap |
| MDS-08 | Model Integrity Checks | B008 | No Gap |
| MDS-09 | Model Signing/Ownership Verification | B008, E004 | Partial Gap |
| MDS-10 | Model Continuous Monitoring | D001, D003, E015 | No Gap |
| MDS-11 | Model Failure | C001, C008, D001, D003 | No Gap |
| MDS-12 | Open Model Risk Assessment | C001, C008 | Partial Gap |
| MDS-13 | Secure Model Format | None | Full Gap |

## Security, Incident & Forensics (SEF)

| CSA Control ID | Control Name | AIUC-1 Requirements | Gap Status |
|---|---|---|---|
| SEF-01 | Security Incident Management Policy and Procedures | E001, E013 | No Gap |
| SEF-02 | Service Management Policy and Procedures | E001 | No Gap |
| SEF-03 | Incident Response Plans | E001 | No Gap |
| SEF-04 | Incident Response Testing | E001 | Full Gap |
| SEF-05 | Incident Response Metrics | E001, E014, E015 | Full Gap |
| SEF-06 | Event Triage Processes | None | Full Gap |
| SEF-07 | Security Breach Notification | E001, E014, E015 | No Gap |
| SEF-08 | Points of Contact Maintenance | E001 | Partial Gap |
| SEF-09 | Incident Response | E001, E002, E003 | No Gap |

## Supply Chain & Third-Party (STA)

| CSA Control ID | Control Name | AIUC-1 Requirements | Gap Status |
|---|---|---|---|
| STA-01 | Supply Chain Risk Management Policies and Procedures | E006 | Partial Gap |
| STA-02 | SSRM Policy and Procedures | None | Full Gap |
| STA-03 | SSRM Supply Chain | None | Full Gap |
| STA-04 | SSRM Guidance | None | Full Gap |
| STA-05 | SSRM Control Ownership | None | Full Gap |
| STA-06 | SSRM Documentation Review | None | Full Gap |
| STA-07 | SSRM Control Implementation | None | Full Gap |
| STA-08 | Supply Chain Inventory | E006 | Full Gap |
| STA-09 | Supply Chain Risk Management | E006 | Partial Gap |
| STA-10 | Primary Service and Contractual Agreement | A002, C005, E006 | Full Gap |
| STA-11 | Supply Chain Agreement Review | E006 | Full Gap |
| STA-12 | Supply Chain Compliance Assessment | E006 | Partial Gap |
| STA-13 | Supply Chain Service Agreement Compliance | E006, E009 | Partial Gap |
| STA-14 | Third Party Risk Management | E006 | Partial Gap |

## Threat & Vulnerability Management (TVM)

| CSA Control ID | Control Name | AIUC-1 Requirements | Gap Status |
|---|---|---|---|
| TVM-01 | Threat and Vulnerability Management Policy and Procedures | C001, E008 | Full Gap |
| TVM-02 | Vulnerability Assessment and Reporting | C002, E013 | Partial Gap |
| TVM-03 | Vulnerability Remediation | B001, B002 | Partial Gap |

---

## Gap Analysis Summary

- **No Gap:** Controls fully addressed (~70+ controls)
- **Partial Gap:** AIUC-1 less prescriptive or narrower scope (~100+ controls)
- **Full Gap:** Not covered in AIUC-1 (~70+ controls)

**Key areas of full coverage:** Identity/access management for AI systems, model security controls, incident response for AI failures, acceptable use policies.

**Key gaps:** Classic IT security infrastructure, physical security, human resources controls, business continuity infrastructure, governance frameworks.

---

*Source: [AIUC-1 × CSA AICM Crosswalk](https://www.aiuc-1.com/crosswalks/csa-aicm)*
*Last updated: July 22, 2025*
