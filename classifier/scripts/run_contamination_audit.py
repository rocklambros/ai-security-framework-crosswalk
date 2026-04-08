from __future__ import annotations
from pathlib import Path
from classifier.data.contamination import compute_partition, write_partition_and_report

REPO = Path(__file__).resolve().parents[2]
FROZEN = REPO / "data" / "splits" / "human_test_frozen.jsonl"
UPSTREAM = REPO / "data" / "upstream" / "mappings_v1.jsonl"
PARTITION = REPO / "data" / "upstream" / "partition.json"
REPORT = REPO / "data" / "upstream" / "contamination_report.json"


def main() -> None:
    partition = compute_partition(FROZEN, UPSTREAM)
    write_partition_and_report(partition, PARTITION, REPORT)
    print(f"upstream_total={partition['upstream_total']}")
    print(f"train_eligible={partition['train_eligible_count']}")
    print(f"held_out={partition['held_out_count']} (rule1={partition['rule1_hits']} rule2={partition['rule2_hits']})")


if __name__ == "__main__":
    main()
