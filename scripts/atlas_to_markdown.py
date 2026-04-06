#!/usr/bin/env python3
"""
Generate a structured markdown reference from MITRE ATLAS data.

Output: data/frameworks/mitre-atlas/mitre_atlas_techniques.md
"""

import yaml
from pathlib import Path

ATLAS_DIR = Path("data/frameworks/mitre-atlas")
OUTPUT = ATLAS_DIR / "mitre_atlas_techniques.md"


def load_yaml(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def clean_description(desc):
    """Clean up description text: collapse whitespace, strip template tags."""
    if not desc:
        return "No description available."
    # Collapse excessive whitespace but preserve paragraph breaks
    lines = desc.strip().split("\n")
    cleaned = []
    for line in lines:
        cleaned.append(" ".join(line.split()))
    return "\n".join(cleaned)


def write_tactic(f, item):
    """Write a tactic entry."""
    item_id = item.get("id", "UNKNOWN")
    name = item.get("name", "Untitled")
    desc = clean_description(item.get("description", ""))

    f.write(f"## {item_id}: {name}\n\n")
    f.write("**Type:** Tactic\n\n")
    f.write(f"### Description\n\n{desc}\n\n")
    f.write("---\n\n")


def write_technique(f, item, is_subtechnique=False):
    """Write a technique or subtechnique entry."""
    item_id = item.get("id", "UNKNOWN")
    name = item.get("name", "Untitled")
    desc = clean_description(item.get("description", ""))

    entry_type = "Subtechnique" if is_subtechnique else "Technique"
    f.write(f"## {item_id}: {name}\n\n")
    f.write(f"**Type:** {entry_type}\n")

    # Parent technique for subtechniques
    if is_subtechnique:
        parent = item_id.rsplit(".", 1)[0]
        f.write(f"**Parent Technique:** {parent}\n")

    # Tactic references (template format like {{reconnaissance.id}})
    tactics = item.get("tactics", [])
    if tactics:
        # Clean template syntax: {{name.id}} -> name
        cleaned = []
        for t in tactics:
            if isinstance(t, str):
                t_clean = t.replace("{{", "").replace("}}", "").replace(".id", "")
                cleaned.append(t_clean)
            else:
                cleaned.append(str(t))
        f.write(f"**Tactics:** {', '.join(cleaned)}\n")

    # ATT&CK reference
    attck_ref = item.get("ATT&CK-reference", {})
    if attck_ref and isinstance(attck_ref, dict):
        ref_id = attck_ref.get("id", "")
        if ref_id:
            f.write(f"**ATT&CK Reference:** {ref_id}\n")

    f.write(f"\n### Description\n\n{desc}\n\n")

    # Mitigations
    mits = item.get("mitigations", [])
    if mits:
        f.write("### Mitigations\n\n")
        for m in mits:
            if isinstance(m, dict):
                m_id = m.get("id", "")
                m_use = m.get("use", "")
                # Clean template syntax
                m_id_clean = m_id.replace("{{", "").replace("}}", "").replace(".id", "")
                if m_use:
                    f.write(f"- **{m_id_clean}**: {' '.join(m_use.split())}\n")
                else:
                    f.write(f"- {m_id_clean}\n")
            else:
                f.write(f"- {m}\n")
        f.write("\n")

    f.write("---\n\n")


def write_mitigation(f, item):
    """Write a mitigation entry."""
    item_id = item.get("id", "UNKNOWN")
    name = item.get("name", "Untitled")
    desc = clean_description(item.get("description", ""))

    f.write(f"## {item_id}: {name}\n\n")
    f.write("**Type:** Mitigation\n")

    category = item.get("category", "")
    if category:
        f.write(f"**Category:** {category}\n")

    lifecycle = item.get("ml-lifecycle", [])
    if lifecycle:
        f.write(f"**ML Lifecycle:** {', '.join(str(l) for l in lifecycle)}\n")

    f.write(f"\n### Description\n\n{desc}\n\n")

    # Techniques mitigated
    techs = item.get("techniques", [])
    if techs:
        f.write("### Techniques Mitigated\n\n")
        for t in techs:
            if isinstance(t, dict):
                t_id = t.get("id", "")
                t_use = t.get("use", "")
                t_id_clean = t_id.replace("{{", "").replace("}}", "").replace(".id", "")
                if t_use:
                    f.write(f"- **{t_id_clean}**: {' '.join(t_use.split())}\n")
                else:
                    f.write(f"- {t_id_clean}\n")
            else:
                f.write(f"- {t}\n")
        f.write("\n")

    f.write("---\n\n")


def main():
    tactics = load_yaml(ATLAS_DIR / "tactics.yaml")
    techniques = load_yaml(ATLAS_DIR / "techniques.yaml")
    mitigations = load_yaml(ATLAS_DIR / "mitigations.yaml")

    # Separate parent techniques from subtechniques
    parent_techniques = [t for t in techniques if t.get("id", "").count(".") == 1]
    subtechniques = [t for t in techniques if t.get("id", "").count(".") > 1]

    warnings = []
    for item in tactics + techniques + mitigations:
        if not isinstance(item, dict):
            warnings.append(f"Non-dict entry found: {type(item)}")
        elif "id" not in item:
            warnings.append(f"Entry missing 'id' field: {list(item.keys())[:5]}")

    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write("# MITRE ATLAS: Adversarial Threat Landscape for AI Systems\n\n")
        f.write("Source: https://github.com/mitre-atlas/atlas-data\n")
        f.write("License: Apache-2.0\n")
        f.write("Retrieved: 2026-04-05\n\n")
        f.write(f"Tactics: {len(tactics)} | ")
        f.write(f"Techniques: {len(parent_techniques)} (+{len(subtechniques)} subtechniques) | ")
        f.write(f"Mitigations: {len(mitigations)}\n\n")
        f.write("---\n\n")

        # Tactics
        f.write("# Tactics\n\n")
        for item in tactics:
            if isinstance(item, dict):
                write_tactic(f, item)
            else:
                warnings.append(f"Skipped non-dict tactic: {item}")

        # Parent Techniques
        f.write("# Techniques\n\n")
        for item in parent_techniques:
            write_technique(f, item, is_subtechnique=False)

        # Subtechniques
        f.write("# Subtechniques\n\n")
        for item in subtechniques:
            write_technique(f, item, is_subtechnique=True)

        # Mitigations
        f.write("# Mitigations\n\n")
        for item in mitigations:
            if isinstance(item, dict):
                write_mitigation(f, item)
            else:
                warnings.append(f"Skipped non-dict mitigation: {item}")

    size = OUTPUT.stat().st_size
    print(f"Wrote {OUTPUT} ({size:,} bytes)")
    print(f"  Tactics:            {len(tactics)}")
    print(f"  Parent Techniques:  {len(parent_techniques)}")
    print(f"  Subtechniques:      {len(subtechniques)}")
    print(f"  Mitigations:        {len(mitigations)}")

    if warnings:
        print(f"\nWARNINGS ({len(warnings)}):")
        for w in warnings:
            print(f"  - {w}")
    else:
        print("\nNo warnings.")


if __name__ == "__main__":
    main()
