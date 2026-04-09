"""UI framework enumeration for the Dash app."""

UI_SOURCE_LISTS = ("owasp_llm", "owasp_agentic", "owasp_dsgai")

UI_TARGET_FRAMEWORKS = (
    "aiuc_1", "csa_aicm", "mitre_atlas", "nist_rmf",
    "owasp_llm", "owasp_agentic", "owasp_dsgai",
    "iso_iec_42001", "eu_gpai_cop", "nist_ssdf",
    "nist_sp_800_53", "eu_ai_act",
)

DISPLAY_LABELS = {
    "owasp_llm": "OWASP LLM Top 10 (2025)",
    "owasp_agentic": "OWASP Agentic Top 10 (2026)",
    "owasp_dsgai": "OWASP DSGAI 2026",
    "aiuc_1": "AIUC-1",
    "csa_aicm": "CSA AICM",
    "mitre_atlas": "MITRE ATLAS",
    "nist_rmf": "NIST AI RMF",
    "iso_iec_42001": "ISO/IEC 42001:2023",
    "eu_gpai_cop": "EU GPAI Code of Practice",
    "nist_ssdf": "NIST SSDF",
    "nist_sp_800_53": "NIST SP 800-53 rev5",
    "eu_ai_act": "EU AI Act",
}

# 26 framework pairs (3 sources x 9 targets, minus owasp_dsgai->nist_ssdf)
FRAMEWORK_PAIRS = (
    ("owasp_llm", "aiuc_1"),
    ("owasp_llm", "csa_aicm"),
    ("owasp_llm", "mitre_atlas"),
    ("owasp_llm", "nist_rmf"),
    ("owasp_llm", "iso_iec_42001"),
    ("owasp_llm", "eu_gpai_cop"),
    ("owasp_llm", "nist_ssdf"),
    ("owasp_llm", "nist_sp_800_53"),
    ("owasp_llm", "eu_ai_act"),
    ("owasp_agentic", "aiuc_1"),
    ("owasp_agentic", "csa_aicm"),
    ("owasp_agentic", "mitre_atlas"),
    ("owasp_agentic", "nist_rmf"),
    ("owasp_agentic", "iso_iec_42001"),
    ("owasp_agentic", "eu_gpai_cop"),
    ("owasp_agentic", "nist_ssdf"),
    ("owasp_agentic", "nist_sp_800_53"),
    ("owasp_agentic", "eu_ai_act"),
    ("owasp_dsgai", "aiuc_1"),
    ("owasp_dsgai", "csa_aicm"),
    ("owasp_dsgai", "mitre_atlas"),
    ("owasp_dsgai", "nist_rmf"),
    ("owasp_dsgai", "iso_iec_42001"),
    ("owasp_dsgai", "eu_gpai_cop"),
    ("owasp_dsgai", "nist_sp_800_53"),
    ("owasp_dsgai", "eu_ai_act"),
)
