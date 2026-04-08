"""Run the retrieval-floor check and write the report."""
from __future__ import annotations
import json
from classifier.config import CANDIDATES_DIR
from classifier.data.retrieval_floor import check_floor


def main() -> None:
    CANDIDATES_DIR.mkdir(parents=True, exist_ok=True)
    report = check_floor(k_initial=20, k_max=100)
    out = CANDIDATES_DIR / "retrieval_floor_report.json"
    out.write_text(json.dumps(report, indent=2))
    print(json.dumps({k: v for k, v in report.items() if k != "miss_rows"}, indent=2))
    print(f"misses shown: {len(report['miss_rows'])}  (first 100)")


if __name__ == "__main__":
    main()
