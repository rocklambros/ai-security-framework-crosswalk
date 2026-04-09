"""Framework metadata, display labels, and color assignments."""
from __future__ import annotations

from typing import Dict, List

FRAMEWORK_LABELS: Dict[str, str] = {
    "owasp_llm": "OWASP LLM Top 10",
    "owasp_agentic": "OWASP Agentic Top 10",
    "owasp_dsgai": "OWASP DSGAI",
    "mitre_atlas": "MITRE ATLAS",
    "nist_ai_rmf": "NIST AI RMF",
    "nist_ai_600_1": "NIST AI 600-1",
    "nist_800_53": "NIST 800-53",
    "csa_aicm": "CSA AICM",
    "aiuc_1": "AIUC-1",
    "cosai": "CoSAI",
    "eu_ai_act": "EU AI Act",
    "eu_gpai_cop": "EU GPAI CoP",
    "owasp_ai_exchange": "OWASP AI Exchange",
    "genai_dsi": "GenAI-DSI",
}

FRAMEWORK_COLORS: Dict[str, str] = {
    "owasp_llm": "#1f6feb",
    "owasp_agentic": "#bc8cff",
    "owasp_dsgai": "#6e40c9",
    "mitre_atlas": "#3fb950",
    "nist_ai_rmf": "#d29922",
    "nist_ai_600_1": "#f0883e",
    "nist_800_53": "#e74c3c",
    "csa_aicm": "#f778ba",
    "aiuc_1": "#58a6ff",
    "cosai": "#56d364",
    "eu_ai_act": "#da3633",
    "eu_gpai_cop": "#db61a2",
    "owasp_ai_exchange": "#79c0ff",
    "genai_dsi": "#d2a8ff",
}

TIER_LABELS: Dict[str, str] = {
    "equivalent": "Equivalent",
    "related": "Related",
    "partial": "Partial",
    "unrelated": "Unrelated",
    "Foundational": "Foundational",
    "Expanded": "Expanded",
}

TIER_COLORS: Dict[str, str] = {
    "equivalent": "#3fb950",
    "related": "#58a6ff",
    "partial": "#d29922",
    "unrelated": "#484f58",
    "Foundational": "#3fb950",
    "Expanded": "#d29922",
}

FRAMEWORK_CATEGORIES: Dict[str, List[str]] = {
    "OWASP": ["owasp_llm", "owasp_agentic", "owasp_dsgai", "owasp_ai_exchange"],
    "NIST": ["nist_ai_rmf", "nist_ai_600_1", "nist_800_53"],
    "Other": ["mitre_atlas", "csa_aicm", "aiuc_1", "cosai", "eu_ai_act", "eu_gpai_cop", "genai_dsi"],
}
