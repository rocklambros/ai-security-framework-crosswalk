"""Framework label registry for the Dash app."""

from __future__ import annotations

FRAMEWORK_LABELS: dict[str, str] = {
    # Source frameworks
    "owasp_agentic": "OWASP Agentic Top 10",
    "owasp_dsgai": "OWASP DSGAI",
    "owasp_llm": "OWASP LLM Top 10",
    # Target frameworks
    "mitre_atlas": "MITRE ATLAS",
    "nist_rmf": "NIST AI RMF",
    "eu_ai_act": "EU AI Act",
    "iso_27001": "ISO 27001",
    "iso_42001": "ISO 42001",
    "cis_controls": "CIS Controls",
    "owasp_asvs": "OWASP ASVS",
    "isa_62443": "ISA/IEC 62443",
    "nist_800_82": "NIST SP 800-82",
    "nist_csf": "NIST CSF",
    "soc_2": "SOC 2",
    "pci_dss": "PCI DSS",
    "enisa_mlf": "ENISA MLF",
    "owasp_samm": "OWASP SAMM",
    "cwe_cve": "CWE/CVE",
    "owasp_ai_testing": "OWASP AI Testing",
    "maestro": "MAESTRO",
    "aiuc_1": "AIUC-1",
    "owasp_nhi": "OWASP NHI",
    "nist_800_218a": "NIST SP 800-218A",
    "fedramp": "FedRAMP",
    "dora": "DORA",
    "stride": "STRIDE",
}
