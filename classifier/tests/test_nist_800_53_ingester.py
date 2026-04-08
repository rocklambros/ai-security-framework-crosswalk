from pathlib import Path
from classifier.data.frameworks.nist_800_53 import ingest_nist_800_53

REPO = Path(__file__).resolve().parents[2]
CATALOG = REPO / "data" / "frameworks" / "nist-800-53" / "NIST_SP-800-53_rev5_catalog.json"


def test_ingest_returns_at_least_300_controls():
    nodes = ingest_nist_800_53(CATALOG)
    assert len(nodes) >= 300, f"expected >=300 controls, got {len(nodes)}"


def test_ingest_node_shape():
    nodes = ingest_nist_800_53(CATALOG)
    n = nodes[0]
    assert n["framework"] == "nist_800_53"
    assert n["node_id"].startswith("nist_800_53:")
    assert n["local_id"]
    assert n["title"]
    assert len(n["text"]) > 30
