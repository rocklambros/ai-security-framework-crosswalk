"""Tests for mapping_engine.calibration.active_learning."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from mapping_engine.calibration.active_learning import (
    DEFAULT_THRESHOLDS,
    export_labeling_sheet,
    import_labels,
    select_uncertain_pairs,
)


def _signals(shape):
    rng = np.random.default_rng(0)
    return {
        "bridge": rng.uniform(0, 1, shape),
        "semantic": rng.uniform(0, 1, shape),
        "keyword": rng.uniform(0, 1, shape),
        "function_match": rng.choice([0.0, 1.0], shape),
    }


def test_select_returns_at_most_max_candidates():
    n_src, n_tgt = 8, 8
    composite = np.linspace(0.0, 1.0, n_src * n_tgt).reshape(n_src, n_tgt)
    sources = [f"src:{i}" for i in range(n_src)]
    targets = [f"tgt:{j}" for j in range(n_tgt)]
    out = select_uncertain_pairs(
        composite, _signals(composite.shape), sources, targets,
        {"max_candidates": 5, "uncertainty_band": 0.10},
    )
    assert len(out) <= 5
    for r in out:
        nearest = min(abs(r["composite_score"] - t) for t in DEFAULT_THRESHOLDS)
        assert nearest <= 0.10


def test_export_import_round_trip(tmp_path):
    csv = tmp_path / "training.csv"
    df = pd.DataFrame(
        [
            {"source_node_id": "src:1", "target_node_id": "tgt:1",
             "bridge_score": 0.3, "semantic_score": 0.4, "keyword_score": 0.2,
             "function_match": 0.0, "is_mapped": 0,
             "expert_tier": "None", "relevance": "None", "rationale": "None"},
        ]
    )
    df.to_csv(csv, index=False)

    candidates = [
        {
            "source_node_id": "src:1", "target_node_id": "tgt:1",
            "composite_score": 0.36, "uncertainty_score": 0.9,
            "bridge": 0.3, "semantic": 0.4, "keyword": 0.2, "function_match": 0.0,
        }
    ]
    sheet = tmp_path / "labels.yaml"
    export_labeling_sheet(candidates, sheet)
    data = yaml.safe_load(sheet.read_text())
    assert "candidates" in data
    # fill in a label
    data["candidates"][0]["expert_tier"] = "Related"
    sheet.write_text(yaml.safe_dump(data))

    new_df = import_labels(sheet, csv)
    row = new_df.iloc[0]
    assert row["expert_tier"] == "Related"
    assert int(row["is_mapped"]) == 1
