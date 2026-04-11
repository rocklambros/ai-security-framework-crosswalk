"""Export v6 test/cal feature matrices + pair metadata as CSVs for the notebook.

Produces:
  data/processed/v6_results/v6_test_features.csv   (400 rows x 25 cols)
  data/processed/v6_results/v6_cal_features.csv    (150 rows x 25 cols)

Each CSV has: pair_key, framework_pair, expert_tier (name), expert_label (0-3),
plus the 22 v6 feature columns. Downstream the notebook loads these with
pandas and never touches the raw embedding files.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.v6_features import build_features, FEATURE_NAMES

TIER_NAMES = ["Unrelated", "Partial", "Related", "Equivalent"]
OUT = Path("data/processed/v6_results")


def export(split: str, out_name: str) -> None:
    X, y, pairs = build_features(split)
    df = pd.DataFrame(X, columns=FEATURE_NAMES)
    df.insert(0, "pair_key", [p.get("pair_key", "") for p in pairs])
    df.insert(1, "framework_pair", [p.get("framework_pair", "") for p in pairs])
    df.insert(2, "expert_label", y.astype(int))
    df.insert(3, "expert_tier", [TIER_NAMES[int(v)] for v in y])
    out_path = OUT / out_name
    df.to_csv(out_path, index=False)
    print(f"wrote {out_path}  shape={df.shape}")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    export("human_test_frozen", "v6_test_features.csv")
    export("human_cal", "v6_cal_features.csv")


if __name__ == "__main__":
    main()
