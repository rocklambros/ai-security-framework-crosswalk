from pathlib import Path
from classifier.data.frameworks.dsgai import ingest_dsgai

REPO = Path(__file__).resolve().parents[2]
DSGAI_TXT = REPO / "data" / "frameworks" / "owasp-dsgai" / "OWASP-GenAI-Data-Security-Risks-and-Mitigations-2026-v1.0.txt"


def test_ingest_dsgai_returns_21_nodes():
    nodes = ingest_dsgai(DSGAI_TXT)
    assert len(nodes) == 21
    ids = [n["local_id"] for n in nodes]
    assert ids == [f"DSGAI{i:02d}" for i in range(1, 22)]


def test_ingest_dsgai_nodes_have_required_fields():
    nodes = ingest_dsgai(DSGAI_TXT)
    for n in nodes:
        assert n["framework"] == "owasp_dsgai"
        assert n["node_id"].startswith("owasp_dsgai:DSGAI")
        assert n["title"] and isinstance(n["title"], str)
        assert n["text"] and len(n["text"]) > 200, f"node {n['local_id']} has too-short body"


def test_wrapped_titles_rejoined():
    nodes = ingest_dsgai(DSGAI_TXT)
    by_id = {n["local_id"]: n for n in nodes}
    # These titles span two lines in the layout extraction.
    assert "Multimodal" in by_id["DSGAI09"]["title"] and "Leakage" in by_id["DSGAI09"]["title"]
    assert "Synthetic Data" in by_id["DSGAI10"]["title"] and "Pitfalls" in by_id["DSGAI10"]["title"]
    assert "SQL" in by_id["DSGAI12"]["title"] or "Graph" in by_id["DSGAI12"]["title"]
    assert "Sharing" in by_id["DSGAI15"]["title"]
    assert "Pipelines" in by_id["DSGAI17"]["title"]
    assert "Poisoning" in by_id["DSGAI21"]["title"]
