from pathlib import Path
from classifier.data.frameworks.eu_ai_act import ingest_eu_ai_act

REPO = Path(__file__).resolve().parents[2]
HTML = REPO / "data" / "frameworks" / "eu-ai-act" / "eu_ai_act_2024_1689.html"


def test_ingest_returns_articles():
    nodes = ingest_eu_ai_act(HTML)
    assert len(nodes) >= 100, f"expected >=100 article nodes, got {len(nodes)}"
    assert all(n["framework"] == "eu_ai_act" for n in nodes)
    assert any("Article 1" in n["title"] for n in nodes)


def test_node_shape():
    nodes = ingest_eu_ai_act(HTML)
    for n in nodes[:5]:
        assert n["node_id"].startswith("eu_ai_act:Art")
        assert n["local_id"].startswith("Art")
        assert n["title"]
        assert len(n["text"]) > 20
