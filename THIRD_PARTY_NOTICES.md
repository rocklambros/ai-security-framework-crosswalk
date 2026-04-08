# Third-Party Notices

This project incorporates the following third-party content. Each is used
under its own license; see individual entries for terms.

## OWASP GenAI Data Security Risks and Mitigations 2026 (v1.0)

- **Source:** https://genai.owasp.org/
- **Files:**
  - `data/frameworks/owasp-dsgai/OWASP-GenAI-Data-Security-Risks-and-Mitigations-2026-v1.0.pdf` (vendored PDF)
  - `data/frameworks/owasp-dsgai/OWASP-GenAI-Data-Security-Risks-and-Mitigations-2026-v1.0.txt` (extracted via `pdftotext -layout`)
- **License:** Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)
- **Attribution:** © OWASP GenAI Data Security Project. Licensed under CC BY-SA 4.0.
- **Modifications:** PDF vendored verbatim; text extraction is mechanical (`pdftotext -layout`). Derived node-list file `data/processed/frameworks/owasp_dsgai.json` is an extraction and remains CC BY-SA 4.0.

## GenAI Security Project — GenAI Data Security Initiative crosswalk

- **Source:** https://github.com/GenAI-Security-Project/GenAI-Data-Security-Initiative
- **Pinned at:** see `third_party/genai-crosswalk/MANIFEST.json` (`upstream_commit_sha`)
- **Files:** `third_party/genai-crosswalk/crosswalk/data/entries/*.json`,
  `third_party/genai-crosswalk/crosswalk/data/schema.json`,
  `third_party/genai-crosswalk/LICENSE.md`
- **License:** Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)
- **Attribution:** © GenAI Security Project. Licensed under CC BY-SA 4.0.
- **Modifications:** None. Files are vendored verbatim. Derived flattened files under `data/upstream/` are transformations and remain CC BY-SA 4.0.

## Derived data files inheriting CC BY-SA 4.0

- `data/upstream/mappings_v1.jsonl`
- `data/upstream/crossrefs_v1.jsonl`
- `data/upstream/partition.json`
- `data/upstream/contamination_report.json`
- `data/processed/frameworks/owasp_dsgai.json`
