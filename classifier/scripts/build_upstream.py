"""Build data/upstream/{mappings_v1,crossrefs_v1}.jsonl from the pinned snapshot."""
from __future__ import annotations
import json
from pathlib import Path

from classifier.data.upstream_loader import load_all_entries, load_all_crossrefs

REPO = Path(__file__).resolve().parents[2]
THIRD = REPO / "third_party" / "genai-crosswalk"
OUT_DIR = REPO / "data" / "upstream"


def main() -> None:
    manifest = json.loads((THIRD / "MANIFEST.json").read_text())
    sha = manifest["upstream_commit_sha"]
    entries_dir = THIRD / "crosswalk" / "data" / "entries"

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    mappings = load_all_entries(entries_dir, sha)
    with (OUT_DIR / "mappings_v1.jsonl").open("w") as f:
        for r in mappings:
            f.write(json.dumps(r) + "\n")

    crossrefs = load_all_crossrefs(entries_dir, sha)
    with (OUT_DIR / "crossrefs_v1.jsonl").open("w") as f:
        for r in crossrefs:
            f.write(json.dumps(r) + "\n")

    unknown_targets = sorted({r["target_framework"] for r in mappings if r["target_framework_unknown"]})
    print(f"[upstream] mappings={len(mappings)} crossrefs={len(crossrefs)}")
    print(f"[upstream] unknown target frameworks ({len(unknown_targets)}): {unknown_targets}")


if __name__ == "__main__":
    main()
