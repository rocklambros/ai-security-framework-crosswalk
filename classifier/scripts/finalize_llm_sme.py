from __future__ import annotations
import hashlib
import json
from pathlib import Path
from classifier.data.candidates import FRAMEWORK_PAIRS
from classifier.labeling.coverage import audit_coverage


MAPPINGS = Path("data/upstream/mappings_v1.jsonl")
LABELS = Path("data/labels/llm_sme/v1/labels.jsonl")
PARTITION = Path("data/upstream/partition.json")
MANIFEST = Path("data/labels/llm_sme/v1/coverage_manifest.json")
HASHES = Path("data/labels/llm_sme/v1/hashes.json")


def main() -> None:
    audit_coverage(FRAMEWORK_PAIRS, MAPPINGS, LABELS, PARTITION, MANIFEST)
    files = [
        "data/labels/llm_sme/v1/gap_tuples.jsonl",
        "data/labels/llm_sme/v1/labels.jsonl",
        "data/labels/llm_sme/v1/coverage_manifest.json",
    ]
    hashes = {
        f: hashlib.sha256(Path(f).read_bytes()).hexdigest()
        for f in files if Path(f).exists()
    }
    HASHES.write_text(json.dumps({"llm_sme_v1": hashes}, sort_keys=True, indent=2) + "\n")
    print(f"coverage OK; hashes -> {HASHES}")


if __name__ == "__main__":
    main()
