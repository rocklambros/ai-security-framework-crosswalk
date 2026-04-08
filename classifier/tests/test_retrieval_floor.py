import json
import pytest
from classifier.config import CANDIDATES_DIR


@pytest.mark.skipif(
    not (CANDIDATES_DIR / "retrieval_floor_report.json").exists(),
    reason="run_retrieval_floor.py has not been executed yet (Task 14)",
)
def test_retrieval_floor_report_shape():
    p = CANDIDATES_DIR / "retrieval_floor_report.json"
    r = json.loads(p.read_text())
    for key in ("k_used", "frozen_total", "hit_at_20", "hit_at_k_used",
                "miss_rows", "coverage_at_20", "coverage_at_k_used"):
        assert key in r, f"missing {key}"
    assert r["frozen_total"] == 400
    assert 20 <= r["k_used"] <= 50
