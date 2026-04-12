"""Single source of truth for the 9-framework color palette and display names."""

FRAMEWORK_KEYS = [
    "aiuc_1", "csa_aicm", "mitre_atlas", "owasp_ai_exchange",
    "nist_rmf", "eu_gpai_cop", "cosai_rm", "owasp_llm", "owasp_agentic",
]

FRAMEWORK_COLORS = {
    "aiuc_1": "#1f6feb", "csa_aicm": "#8fd18f", "mitre_atlas": "#e8845a",
    "owasp_ai_exchange": "#4ecdc4", "nist_rmf": "#cf85c4", "eu_gpai_cop": "#d9bf55",
    "cosai_rm": "#7aaed4", "owasp_llm": "#ff6b6b", "owasp_agentic": "#ffb347",
}

FRAMEWORK_DISPLAY_NAMES = {
    "aiuc_1": "AIUC-1", "csa_aicm": "CSA AI Controls Matrix",
    "mitre_atlas": "MITRE ATLAS", "owasp_ai_exchange": "OWASP AI Exchange",
    "nist_rmf": "NIST AI RMF", "eu_gpai_cop": "EU GPAI Code of Practice",
    "cosai_rm": "CoSAI Risk Map", "owasp_llm": "OWASP LLM Top 10",
    "owasp_agentic": "OWASP Agentic Top 10",
}

FRAMEWORK_SHORT_NAMES = {
    "aiuc_1": "AIUC-1", "csa_aicm": "CSA AICM", "mitre_atlas": "ATLAS",
    "owasp_ai_exchange": "AI Exchange", "nist_rmf": "NIST RMF",
    "eu_gpai_cop": "EU GPAI", "cosai_rm": "CoSAI",
    "owasp_llm": "LLM Top 10", "owasp_agentic": "Agentic Top 10",
}

CYBER_ACCENT = "#00d4ff"

CONFIDENCE_ORDER = ["authoritative", "expert", "suggestive", "unvalidated"]

CONFIDENCE_COLORS = {
    "authoritative": "#238636", "expert": "#1f6feb",
    "suggestive": "#d29922", "unvalidated": "#6e7681",
}

CONFIDENCE_LABELS = {
    "authoritative": "Authoritative: from official framework source documents",
    "expert": "Expert: validated by domain expert review",
    "suggestive": "Suggestive: inferred from shared categories or semantic similarity",
    "unvalidated": "Unvalidated: machine-generated, not yet reviewed",
}

RATIONALE_LABELS = {
    "PARENT": "Parent-child: hierarchical relationship within a framework",
    "CROSS_FRAMEWORK_CATEGORY": "Category: controls share a topical category",
    "SCOPE": "Scope: this control limits the scope of the identified risk",
    "DETECT": "Detect: this control detects the identified risk",
    "VALID": "Validate: this control validates or tests against the risk",
    "GOVERN": "Govern: this control establishes governance over the risk",
    "ISOLATE": "Isolate: this control isolates or contains the risk",
    "GATE": "Gate: this control gates access or progression",
    "DISCLOSE": "Disclose: this control requires disclosure or transparency",
    "PREV": "Previous: sequential ordering within a framework",
}

_DEFAULT_COLOR = "#6e7681"

def get_color(framework_key: str) -> str:
    return FRAMEWORK_COLORS.get(framework_key, _DEFAULT_COLOR)

def get_display_name(framework_key: str) -> str:
    return FRAMEWORK_DISPLAY_NAMES.get(framework_key, framework_key)

def get_short_name(framework_key: str) -> str:
    return FRAMEWORK_SHORT_NAMES.get(framework_key, framework_key)
