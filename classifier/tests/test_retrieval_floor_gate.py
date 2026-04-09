import json
from classifier.config import CANDIDATES_DIR

BASELINE = {"coverage_at_20": 0.65, "coverage_at_k_used": 0.8825, "k_used": 100}


def test_plan1b_baseline_present():
    report = json.loads((CANDIDATES_DIR / "retrieval_floor_report.json").read_text())
    for k, v in BASELINE.items():
        assert report[k] == v, f"{k}: {report[k]} != {v}"
