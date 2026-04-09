from __future__ import annotations
import json
import tempfile
from pathlib import Path
from classifier.labeling.gap_selector import select_gap_tuples


POOL = Path("data/candidates/pool_v1.jsonl")
MAPPINGS = Path("data/upstream/mappings_v1.jsonl")
PARTITION = Path("data/upstream/partition.json")
OUT = Path("data/labels/llm_sme/v1/gap_tuples.jsonl")
TOP_K = 3  # label top-3 retrieval candidates per source (budget constraint)


def _flatten_pool(pool_path: Path, flat_path: Path, top_k: int = TOP_K) -> int:
    """Flatten hierarchical pool (source + candidates[]) to flat tuples.

    Only takes the top-k candidates per source node to stay within the
    Plan 2 LLM budget (~$100). Candidates are already sorted by retrieval
    score descending.
    """
    n = 0
    with pool_path.open() as fin, flat_path.open("w") as fout:
        for line in fin:
            if not line.strip():
                continue
            row = json.loads(line)
            fp = row["framework_pair"]
            src_fw, tgt_fw = fp.split("__", 1)
            src_node = row["source_node_id"]
            src_id = src_node.split(":", 1)[-1] if ":" in src_node else src_node
            for cand in row.get("candidates", [])[:top_k]:
                flat = {
                    "source_framework": src_fw,
                    "source_id": src_id,
                    "target_framework": tgt_fw,
                    "target_node_id": cand["target_node_id"],
                }
                fout.write(json.dumps(flat, sort_keys=True) + "\n")
                n += 1
    return n


def main() -> None:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    n_flat = _flatten_pool(POOL, tmp_path)
    print(f"flattened {n_flat} candidate tuples from pool")
    gaps = select_gap_tuples(tmp_path, MAPPINGS, PARTITION)
    tmp_path.unlink(missing_ok=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w") as fh:
        for g in gaps:
            fh.write(json.dumps(g.model_dump(), sort_keys=True) + "\n")
    print(f"wrote {len(gaps)} gap tuples -> {OUT}")


if __name__ == "__main__":
    main()
