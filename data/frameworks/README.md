# Framework Source Documents

Place .md files for each framework here. One file per framework, named by short ID.

## Required Documents

### Tier 1 (Core, must have for MVP)

| File | Framework | Where to get it |
|------|-----------|----------------|
| `owasp_llm_top10_2025.md` | OWASP Top 10 for LLM Applications 2025 | [PDF](https://genai.owasp.org/resource/owasp-top-10-for-llm-applications-2025/) - convert to .md |
| `owasp_agentic_top10_2026.md` | OWASP Top 10 for Agentic Applications 2026 | [PDF](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/) - convert to .md |
| `mitre_atlas.md` | MITRE ATLAS Techniques | [GitHub JSON](https://github.com/mitre-atlas/atlas-data) or [atlas.mitre.org](https://atlas.mitre.org/) |

### Tier 2 (Extend coverage for depth)

| File | Framework | Where to get it |
|------|-----------|----------------|
| `nist_ai_rmf.md` | NIST AI RMF 1.0 + Playbook | [NIST AI RMF Playbook](https://airc.nist.gov/AI_RMF_Knowledge_Base/Playbook) |
| `nist_ai_600_1.md` | NIST AI 600-1 (GenAI Profile) | [PDF](https://csrc.nist.gov/pubs/ai/600/1/final) |
| `csa_aicm.md` | CSA AI Controls Matrix | [CSA downloads](https://cloudsecurityalliance.org/research/artifacts/ai-controls-matrix) |
| `aiuc_1.md` | AIUC-1 Standard | [aiuc-1.com](https://www.aiuc-1.com/) - crosswalks section has structured mappings |

### Tier 3 (Stretch, adds unique value)

| File | Framework | Where to get it |
|------|-----------|----------------|
| `owasp_ai_exchange.md` | OWASP AI Exchange | [owaspai.org](https://owaspai.org/) |
| `owasp_compass.md` | OWASP Threat Defense COMPASS | [Google Sheet template](https://genai.owasp.org/resource/owasp-genai-security-project-threat-defense-compass-1-0/) |
| `eu_ai_act.md` | EU AI Act (security-relevant articles) | [EUR-Lex](https://eur-lex.europa.eu/) |
| `cosai.md` | CoSAI frameworks | [cosai.dev](https://www.cosai.dev/) |

## Format Guidelines

Each .md file should preserve:
- The full hierarchy (numbered risk/control IDs)
- Descriptions and definitions
- Any existing cross-references to other frameworks
- Version and date information

The processing scripts in `../scripts/` will parse these into the unified JSON schema.
