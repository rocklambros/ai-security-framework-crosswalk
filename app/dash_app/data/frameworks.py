"""Framework display labels and tier colour palette for the Coverage Dashboard."""
from __future__ import annotations

FRAMEWORK_LABELS: dict[str, str] = {
    "owasp_llm": "OWASP LLM Top 10 (2025)",
    "owasp_agentic": "OWASP Agentic Top 10 (2026)",
    "owasp_dsgai": "OWASP DSGAI 2026",
    "aiuc_1": "AIUC-1",
    "csa_aicm": "CSA AICM",
    "mitre_atlas": "MITRE ATLAS",
    "nist_rmf": "NIST AI RMF",
    "nist_800_53": "NIST SP 800-53 rev5",
    "iso_iec_42001": "ISO/IEC 42001:2023",
    "eu_gpai_cop": "EU GPAI Code of Practice",
    "nist_ssdf": "NIST SSDF",
    "eu_ai_act": "EU AI Act",
    "cosai_rm": "COSAI Risk Map",
    "owasp_ai_exchange": "OWASP AI Exchange",
    "eu_gpai_cop": "EU GPAI Code of Practice",
}

# Traffic-light palette: green = well covered, yellow = partial, red = sparse.
TIER_COLORS: dict[str, str] = {
    "Foundational": "#3fb950",
    "Advanced": "#d29922",
    "Hardening": "#da3633",
    # Fallback for unknown tiers
    "Unknown": "#8b949e",
}
