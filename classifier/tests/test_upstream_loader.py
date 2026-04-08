import json
from pathlib import Path
from classifier.data.upstream_loader import (
    SOURCE_LIST_TO_FRAMEWORK,
    flatten_entry,
    load_all_entries,
)

REPO = Path(__file__).resolve().parents[2]
ENTRIES = REPO / "third_party" / "genai-crosswalk" / "crosswalk" / "data" / "entries"


def test_source_list_normalization_table_is_exhaustive():
    expected = {"LLM-Top10-2025", "Agentic-Top10-2026", "DSGAI-2026"}
    assert expected.issubset(set(SOURCE_LIST_TO_FRAMEWORK.keys()))
    targets = set(SOURCE_LIST_TO_FRAMEWORK.values())
    assert targets == {"owasp_llm", "owasp_agentic", "owasp_dsgai"}


def test_flatten_entry_emits_one_row_per_mapping():
    raw = json.loads((ENTRIES / "LLM01.json").read_text())
    rows = flatten_entry(raw, upstream_commit_sha="deadbeef" * 5)
    assert len(rows) == len(raw["mappings"])
    first = rows[0]
    assert first["source_framework"] == "owasp_llm"
    assert first["source_id"] == "LLM01"
    assert first["source_list"] == "LLM-Top10-2025"
    assert "target_framework" in first
    assert "provenance_sha" in first and len(first["provenance_sha"]) == 64


def test_load_all_entries_covers_41():
    rows = load_all_entries(ENTRIES, upstream_commit_sha="deadbeef" * 5)
    source_ids = {r["source_id"] for r in rows}
    assert len(source_ids) == 41
    assert "LLM01" in source_ids and "ASI10" in source_ids and "DSGAI21" in source_ids
