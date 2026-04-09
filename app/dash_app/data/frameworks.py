"""Framework metadata: colors, labels, tiers, and categories for the Dash app."""

FRAMEWORK_COLORS: dict[str, str] = {
    "mitre_atlas": "#d62728",
    "owasp_llm": "#ff7f0e",
    "nist_ai_rmf": "#1f77b4",
    "nist_800_53": "#2ca02c",
    "nist_ai_600_1": "#17becf",
    "eu_ai_act": "#9467bd",
    "eu_gpai": "#8c564b",
    "csa_aicm": "#e377c2",
    "cosai": "#bcbd22",
    "aiuc": "#7f7f7f",
    "owasp_agentic": "#aec7e8",
    "owasp_ai_exchange": "#ffbb78",
    "owasp_dsgai": "#98df8a",
    "maestro": "#ff9896",
}

FRAMEWORK_LABELS: dict[str, str] = {
    "mitre_atlas": "MITRE ATLAS",
    "owasp_llm": "OWASP LLM Top 10",
    "nist_ai_rmf": "NIST AI RMF",
    "nist_800_53": "NIST 800-53",
    "nist_ai_600_1": "NIST AI 600-1",
    "eu_ai_act": "EU AI Act",
    "eu_gpai": "EU GPAI Code of Practice",
    "csa_aicm": "CSA AI Control Matrix",
    "cosai": "CoSAI",
    "aiuc": "AI Use Cases",
    "owasp_agentic": "OWASP Agentic Top 10",
    "owasp_ai_exchange": "OWASP AI Exchange",
    "owasp_dsgai": "OWASP DSG AI",
    "maestro": "MAESTRO",
}

TIER_LABELS: dict[str, str] = {
    "equivalent": "Equivalent",
    "related": "Related",
    "partial": "Partial",
    "unrelated": "Unrelated",
}

TIER_COLORS: dict[str, str] = {
    "equivalent": "#2ca02c",
    "related": "#1f77b4",
    "partial": "#ff7f0e",
    "unrelated": "#d62728",
}

FRAMEWORK_CATEGORIES: dict[str, list[str]] = {
    "Threat & Attack": [
        "mitre_atlas",
        "owasp_llm",
        "owasp_agentic",
        "owasp_ai_exchange",
    ],
    "Governance & Risk": [
        "nist_ai_rmf",
        "nist_800_53",
        "nist_ai_600_1",
        "eu_ai_act",
        "eu_gpai",
    ],
    "Controls & Practices": [
        "csa_aicm",
        "cosai",
        "maestro",
    ],
    "Data & Domain": [
        "aiuc",
        "owasp_dsgai",
    ],
}
