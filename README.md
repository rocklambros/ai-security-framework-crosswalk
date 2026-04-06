# AI Security Framework Crosswalk

Interactive visualization and gap analysis across AI security standards frameworks.

## Purpose

Security architects evaluating AI risk frameworks face a fragmented landscape. OWASP, MITRE, NIST, CSA, and AIUC-1 each address overlapping but distinct risk categories, controls, and mitigations. No unified, interactive tool exists to map relationships between them or highlight coverage gaps.

This project provides:

1. **Exploratory analysis** of the standards ecosystem structure: coverage density, framework overlap, gap identification (matplotlib/seaborn notebook)
2. **Interactive explorer** for navigating cross-framework mappings, filtering by risk category, and identifying coverage gaps (Plotly/Dash application)

## Frameworks Covered

| Framework | Version | Source | License |
|-----------|---------|--------|---------|
| OWASP Top 10 for LLM Applications | 2025 | [genai.owasp.org](https://genai.owasp.org/llm-top-10/) | CC-BY-SA 4.0 |
| OWASP Top 10 for Agentic Applications | 2026 | [genai.owasp.org](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/) | CC-BY-SA 4.0 |
| MITRE ATLAS | Current | [atlas.mitre.org](https://atlas.mitre.org/) | Apache 2.0 |
| NIST AI RMF | 1.0 | [nist.gov](https://www.nist.gov/artificial-intelligence/ai-risk-management-framework) | Public Domain |
| CSA AI Controls Matrix (AICM) | Current | [cloudsecurityalliance.org](https://cloudsecurityalliance.org/) | CSA License |
| AIUC-1 | Current | [aiuc-1.com](https://www.aiuc-1.com/) | Public |
| OWASP AI Exchange | Current | [owaspai.org](https://owaspai.org/) | CC-BY-SA 4.0 |

## Repository Structure

```
├── data/
│   ├── frameworks/          # Source .md files for each framework
│   ├── mappings/            # Cross-mapping relationship files
│   └── processed/           # Generated unified JSON schema
├── notebooks/               # Exploratory analysis (matplotlib/seaborn)
├── app/                     # Dash application
│   ├── app.py
│   ├── callbacks.py
│   ├── layouts.py
│   └── assets/
├── scripts/                 # Data processing and schema generation
├── requirements.txt
└── README.md
```

## Data Schema

Each framework entry follows a unified schema:

```json
{
  "framework": "owasp_llm_top10",
  "id": "LLM01",
  "name": "Prompt Injection",
  "category": "input_manipulation",
  "type": "risk",
  "severity": "critical",
  "description": "...",
  "mapped_to": [
    {"framework": "mitre_atlas", "id": "AML.T0051", "relationship": "technique_for"},
    {"framework": "owasp_agentic", "id": "ASI03", "relationship": "related_risk"},
    {"framework": "nist_ai_rmf", "id": "MANAGE-2.4", "relationship": "addressed_by"}
  ]
}
```

## Setup

```bash
pip install -r requirements.txt
```

### Run the exploratory notebook
```bash
jupyter notebook notebooks/01_framework_landscape_eda.ipynb
```

### Run the Dash app
```bash
python app/app.py
```

## License

Analysis and visualization code: MIT. Framework source content retains original licensing as noted above.
