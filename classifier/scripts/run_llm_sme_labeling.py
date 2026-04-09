from __future__ import annotations
import json
import os
import subprocess
from pathlib import Path
import anthropic
from classifier.labeling.bulk import label_gap_tuples
from classifier.labeling.client import LabelerClient
from classifier.labeling.schemas import GapTuple
from classifier.labeling.writer import write_labels


GAPS = Path("data/labels/llm_sme/v1/gap_tuples.jsonl")
LABELS = Path("data/labels/llm_sme/v1/labels.jsonl")
CACHE = Path("data/labels/llm_sme/v1/cache")
LEDGER = Path("data/cost_ledger.jsonl")
NODES = Path("data/processed/nodes.json")
MODEL = os.environ.get("LLM_SME_MODEL", "claude-3-haiku-20240307")


def _get_api_key() -> str:
    key = os.environ.get("ANTHROPIC_API_KEY")
    if key:
        return key
    try:
        return subprocess.check_output(
            ["pass", "show", "ANTHROPIC_API_KEY"], text=True
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        raise RuntimeError(
            "ANTHROPIC_API_KEY not found in env or pass store"
        )


def _text_lookup_factory():
    nodes = json.loads(NODES.read_text())
    index: dict[tuple[str, str], str] = {}
    for n in nodes:
        fw = n.get("framework", "")
        local = n.get("local_id") or n.get("node_id", "").split(":", 1)[-1]
        text = n.get("description") or n.get("name") or ""
        index[(fw, local)] = text
    def lookup(framework: str, node_id: str) -> str:
        local = node_id.split(":", 1)[-1] if ":" in node_id else node_id
        return index.get((framework, local), "")
    return lookup


def main() -> None:
    gaps = [GapTuple(**json.loads(l)) for l in GAPS.read_text().splitlines() if l.strip()]
    print(f"loaded {len(gaps)} gap tuples")
    client = LabelerClient(
        anthropic_client=anthropic.Anthropic(api_key=_get_api_key()),
        cache_dir=CACHE,
        ledger_path=LEDGER,
        model=MODEL,
    )
    labels = label_gap_tuples(gaps, _text_lookup_factory(), client)
    write_labels(labels, LABELS)
    print(f"wrote {len(labels)} silver labels -> {LABELS}")


if __name__ == "__main__":
    main()
