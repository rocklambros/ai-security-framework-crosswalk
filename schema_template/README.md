# Crosswalk mapping schemas

JSON Schema definitions for the OWASP Agentic Top 10 crosswalk mapping output.

## crosswalk-mapping-v2.schema.json

The canonical schema for bi-directional mappings between any source standard and the OWASP Top 10 for Agentic Applications (ASI01-ASI10).

Designed for reuse across source frameworks: AIUC-1, NIST AI RMF, ISO 42001, EU AI Act, and others.

### Key design decisions

**Standard-agnostic field names.** The schema uses `control_id` and `domain` rather than `aiuc_id` and `aiuc_domain`. This allows the same schema to validate NIST AI RMF mappings (where `control_id` is `GV.3.2`) and ISO 42001 mappings (where `control_id` is `A.8.22`) without modification.

**Rationale and relevance are required. Scores are optional.** Every mapping must carry a `rationale_code` (PREV, SCOPE, GATE, DETECT, VALID, GOVERN, ISOLATE, DISCLOSE) and a `relevance` level (Primary, Secondary). The `score` and `signals` fields are optional: include them in diagnostic output for methodology auditing, omit them in published crosswalks where they add noise without actionable value.

**Function coverage per threat.** Each OWASP entry carries `function_coverage` (count of mapped controls per rationale code) and `uncovered_functions` (rationale codes with zero coverage). This surfaces defense-in-depth gaps that are invisible when you only list individual mappings.

**Gap analysis is a first-class section.** Unmapped controls are reported explicitly with a `gap_reason` field. This prevents both false "unmapped = unimportant" assumptions and missed pipeline limitations.

### Validation

```bash
# Using jsonschema (Python)
pip install jsonschema
python -c "
import json, jsonschema
with open('schemas/crosswalk-mapping-v2.schema.json') as s:
    schema = json.load(s)
with open('mapping/aiuc_owasp_mapping.json') as d:
    data = json.load(d)
jsonschema.validate(data, schema)
print('Valid')
"

# Using ajv (Node.js)
npx ajv validate -s schemas/crosswalk-mapping-v2.schema.json -d mapping/aiuc_owasp_mapping.json
```

### Rationale taxonomy

| Code | Label | Definition |
|------|-------|------------|
| PREV | Prevent | Directly blocks the core attack mechanism before it succeeds |
| SCOPE | Constrain scope | Limits blast radius after compromise (least privilege, data minimization) |
| GATE | Human gate | Enforces human approval, review, or intervention |
| DETECT | Detect and trace | Runtime detection, behavioral monitoring, or forensic traceability |
| VALID | Validate and test | Tests, audits, or validates that other controls function effectively |
| GOVERN | Policy and governance | Organizational policy, accountability, process framework, or response plan |
| ISOLATE | Isolate and contain | Architectural separation preventing propagation across agents or systems |
| DISCLOSE | Disclose and calibrate | Transparency, provenance, or disclosure enabling trust calibration |

### Relevance classification

Primary vs Secondary is determined by threat context, not rationale code alone.

PREV and SCOPE controls tend to be Primary. DETECT and GOVERN tend to be Secondary. The threat determines the final call: DETECT is Primary for ASI06 (memory poisoning is invisible without logging) but Secondary for ASI01 (where preventive controls are the frontline).

See `aiuc/taxonomy.py` for the complete classification rules and `tests/test_classification.py` for the test harness.

### Schema version history

| Version | Date | Changes |
|---------|------|---------|
| 2.0 | 2026-04-06 | Initial v2 schema. Adds rationale taxonomy, relevance classification, function coverage, gap analysis. Renames aiuc-specific fields to standard-agnostic names. Makes score/signals optional. |
| 1.0 | 2026-03-03 | Original schema with 3-signal composite scores, confidence tiers, and relationship types. |
