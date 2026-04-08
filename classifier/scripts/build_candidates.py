"""Run top-20 retrieval across all framework pairs in classifier.data.candidates.FRAMEWORK_PAIRS.
Emits one JSONL row per (pair, source_node)."""
from __future__ import annotations
import json
from classifier.config import CANDIDATES_DIR
from classifier.data.candidates import FRAMEWORK_PAIRS, build_candidate_pool


def main() -> None:
    CANDIDATES_DIR.mkdir(parents=True, exist_ok=True)
    pool = build_candidate_pool(pairs=FRAMEWORK_PAIRS, k=20)
    out_path = CANDIDATES_DIR / "pool_v1.jsonl"
    with out_path.open("w") as f:
        for pair_key, rows in pool.items():
            for row in rows:
                record = {"framework_pair": pair_key, **row}
                f.write(json.dumps(record) + "\n")
    total = sum(len(r) for r in pool.values())
    print(f"[candidates] wrote {out_path}  pairs={len(pool)}  source_rows={total}")


if __name__ == "__main__":
    main()
