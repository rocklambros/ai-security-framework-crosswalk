"""Assemble v8b training data from CRE hierarchy gap penalties.

Pipeline:
  1. Load all OpenCRE pairs
  2. Run contamination firewall (Rules 1-3)
  3. Map gap_penalty directly to tier soft targets via map_opencre_tier()
  4. Apply per-class caps (max 25% of expert class count, minimum 250)
  5. Merge with existing expert_train data
  6. Write v8b training set
"""
from __future__ import annotations

import json
import time
from collections import Counter
from pathlib import Path

from classifier.data.tier_mapper import TierLabel, map_opencre_tier
from classifier.data.contamination import check_cre_bridge_contamination

OPENCRE_PAIRS = Path("data/opencre/opencre_pairs.jsonl")
FROZEN_TEST = Path("data/splits/human_test_frozen.jsonl")
EXPERT_TRAIN = Path("data/splits/expert_train.jsonl")
V8_TRAIN_OUT = Path("data/splits/v8b_train.jsonl")
V8_REPORT_OUT = Path("runs/v8b_diagnosis/v8b_data_assembly.json")

OPENCRE_WEIGHT = 0.3


def load_jsonl(path: Path) -> list[dict]:
    with open(path) as f:
        return [json.loads(line) for line in f]


def build_frozen_node_ids() -> set[str]:
    frozen = load_jsonl(FROZEN_TEST)
    ids = set()
    for row in frozen:
        ids.add(row["source_node_id"])
        ids.add(row["target_node_id"])
    return ids


def assemble_v8_training() -> dict:
    """Full v8b training data assembly pipeline.

    Uses CRE hierarchy gap_penalty directly as tier labels -- no model
    inference needed.  gap=0 -> EQUIVALENT, gap=1 -> RELATED, gap>=2 -> PARTIAL.
    """
    t0 = time.time()

    # -- 1. Load OpenCRE pairs ------------------------------------------------
    print("Loading OpenCRE pairs...")
    opencre_pairs = load_jsonl(OPENCRE_PAIRS)
    print(f"  {len(opencre_pairs)} total OpenCRE pairs")

    # -- 2. Contamination firewall --------------------------------------------
    print("Running contamination firewall...")
    frozen_ids = build_frozen_node_ids()
    contaminated_shas = set(check_cre_bridge_contamination(opencre_pairs, frozen_ids))
    clean_pairs = [p for p in opencre_pairs if p.get("provenance_sha") not in contaminated_shas]
    print(f"  {len(opencre_pairs) - len(clean_pairs)} contaminated, {len(clean_pairs)} clean")

    # -- 3. Load expert_train for class caps ----------------------------------
    expert_rows = load_jsonl(EXPERT_TRAIN)
    expert_label_counts = Counter(r["tier_label"] for r in expert_rows)
    class_caps = {
        tier: max(250, int(count * 0.25))
        for tier, count in expert_label_counts.items()
    }

    # -- 4. Map each clean pair via gap_penalty -> tier -----------------------
    print("Mapping OpenCRE pairs via gap_penalty (class-capped)...")
    v8_rows = []
    label_dist = Counter()
    class_added = Counter()
    skipped = 0

    for pair in clean_pairs:
        is_bridge = (
            pair.get("fw_class_a") != pair.get("fw_class_b")
            and "other" not in (pair.get("fw_class_a", ""), pair.get("fw_class_b", ""))
        )
        expert_dist = map_opencre_tier(
            gap_penalty=pair.get("gap_penalty", 0),
            bridge_pair=is_bridge,
        )
        argmax_label = max(expert_dist, key=expert_dist.get)
        tier_int = int(argmax_label)

        if class_added[tier_int] >= class_caps.get(tier_int, 500):
            skipped += 1
            continue

        class_added[tier_int] += 1
        label_dist[TierLabel(argmax_label).name] += 1

        soft_target = [float(expert_dist.get(TierLabel(i), 0.0)) for i in range(4)]

        v8_rows.append({
            "source_node_id": pair["source_node_id"],
            "target_node_id": pair["target_node_id"],
            "source_text": pair.get("source_text", ""),
            "target_text": pair.get("target_text", ""),
            "source_framework": pair.get("source_framework", ""),
            "target_framework": pair.get("target_framework", ""),
            "tier_label": tier_int,
            "soft_target": soft_target,
            "sample_weight": OPENCRE_WEIGHT,
            "provenance": "opencre_hierarchy",
            "provenance_sha": pair.get("provenance_sha", ""),
            "gap_penalty": pair.get("gap_penalty", 0),
            "cre_id": pair.get("cre_id", ""),
        })

    if skipped:
        print(f"  Class cap skipped {skipped} pairs (caps: {dict(class_caps)})")
    print(f"  Added: {dict(class_added)}")

    # -- 5. Merge with expert_train -> write v8b_train.jsonl ------------------
    print("Merging with existing expert_train...")
    print(f"  Existing expert_train: {len(expert_rows)} rows")
    print(f"  New OpenCRE rows: {len(v8_rows)} (from {len(clean_pairs)} clean pairs)")

    all_rows = expert_rows + v8_rows

    V8_TRAIN_OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(V8_TRAIN_OUT, "w") as f:
        for row in all_rows:
            f.write(json.dumps(row, ensure_ascii=True) + "\n")

    elapsed = time.time() - t0
    report = {
        "elapsed_seconds": elapsed,
        "opencre_total": len(opencre_pairs),
        "contaminated": len(opencre_pairs) - len(clean_pairs),
        "clean": len(clean_pairs),
        "v8_rows_added": len(v8_rows),
        "skipped_by_cap": skipped,
        "expert_train_original": len(expert_rows),
        "v8_train_total": len(all_rows),
        "label_distribution": dict(label_dist),
        "class_caps": {str(k): v for k, v in class_caps.items()},
        "output_path": str(V8_TRAIN_OUT),
    }

    V8_REPORT_OUT.parent.mkdir(parents=True, exist_ok=True)
    V8_REPORT_OUT.write_text(json.dumps(report, indent=2))
    print(f"\nv8b training data written to {V8_TRAIN_OUT}")
    print(f"Report: {V8_REPORT_OUT}")
    print(f"Total rows: {len(all_rows)} (expert: {len(expert_rows)}, opencre: {len(v8_rows)})")
    return report


if __name__ == "__main__":
    assemble_v8_training()
