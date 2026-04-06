#!/usr/bin/env python3
"""
Convert MITRE ATLAS YAML source files to JSON.

Reads the individual YAML files (tactics, techniques, mitigations)
and the compiled ATLAS.yaml. Outputs:
  - atlas-data.json: Combined JSON from individual source files
  - ATLAS_compiled.json: Direct conversion of dist/ATLAS.yaml
"""

import json
import yaml
from pathlib import Path
from datetime import date, datetime

ATLAS_DIR = Path("data/frameworks/mitre-atlas")
OUTPUT_DIR = ATLAS_DIR


def load_yaml(filepath):
    """Load a YAML file, return parsed content."""
    with open(filepath, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_yaml_with_includes(filepath):
    """Load a YAML file that may contain !include tags, ignoring them."""

    class IncludeLoader(yaml.SafeLoader):
        pass

    def include_constructor(loader, node):
        return f"!include {loader.construct_scalar(node)}"

    IncludeLoader.add_constructor("!include", include_constructor)

    with open(filepath, "r", encoding="utf-8") as f:
        return yaml.load(f, Loader=IncludeLoader)


def main():
    # Load individual source files
    tactics = load_yaml(ATLAS_DIR / "tactics.yaml")
    techniques = load_yaml(ATLAS_DIR / "techniques.yaml")
    mitigations = load_yaml(ATLAS_DIR / "mitigations.yaml")
    matrix = load_yaml_with_includes(ATLAS_DIR / "matrix.yaml")

    # Combine into a single JSON structure
    combined = {
        "metadata": {
            "source": "https://github.com/mitre-atlas/atlas-data",
            "license": "Apache-2.0",
            "retrieved": "2026-04-05",
            "description": "MITRE ATLAS: Adversarial Threat Landscape for AI Systems",
        },
        "matrix": matrix,
        "tactics": tactics,
        "techniques": techniques,
        "mitigations": mitigations,
    }

    def json_serial(obj):
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")

    # Write combined JSON from source files
    out_combined = OUTPUT_DIR / "atlas-data.json"
    with open(out_combined, "w", encoding="utf-8") as f:
        json.dump(combined, f, indent=2, ensure_ascii=False, default=json_serial)
    print(f"Wrote {out_combined} ({out_combined.stat().st_size:,} bytes)")

    # Also convert the compiled ATLAS.yaml directly
    compiled = load_yaml(ATLAS_DIR / "ATLAS.yaml")
    out_compiled = OUTPUT_DIR / "ATLAS_compiled.json"
    with open(out_compiled, "w", encoding="utf-8") as f:
        json.dump(compiled, f, indent=2, ensure_ascii=False, default=json_serial)
    print(f"Wrote {out_compiled} ({out_compiled.stat().st_size:,} bytes)")

    # Print summary stats
    print(f"\nATLAS Summary:")
    print(f"  Tactics:     {len(tactics)}")
    print(f"  Techniques:  {len(techniques)}")
    print(f"  Mitigations: {len(mitigations)}")

    subtechniques = [t for t in techniques if t.get("id", "").count(".") > 1]
    parent_techniques = [t for t in techniques if t.get("id", "").count(".") == 1]
    print(f"  Parent techniques: {len(parent_techniques)}")
    print(f"  Subtechniques:     {len(subtechniques)}")


if __name__ == "__main__":
    main()
