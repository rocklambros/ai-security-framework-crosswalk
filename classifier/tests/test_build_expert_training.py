"""Tests for end-to-end expert training data construction."""
import json
import tempfile
from pathlib import Path

import pytest
from classifier.data.tier_mapper import TierLabel
from classifier.scripts.build_expert_training import build_expert_training_set


def test_build_produces_valid_jsonl(tmp_path):
    # Create minimal upstream mappings
    mappings_path = tmp_path / "mappings.jsonl"
    with mappings_path.open("w") as f:
        for i in range(5):
            json.dump({
                "source_framework": "owasp_llm",
                "source_id": f"LLM0{i+1}",
                "target_framework": "mitre_atlas",
                "target_control_id": f"AML.T00{i+1}",
                "target_node_id": f"mitre_atlas:AML.T00{i+1}",
                "target_id_unresolved": False,
                "tier": "Foundational",
                "scope": "Direct" if i < 3 else "Broader",
            }, f)
            f.write("\n")

    # Create minimal frozen test (to exclude)
    frozen_path = tmp_path / "frozen.jsonl"
    with frozen_path.open("w") as f:
        json.dump({
            "pair_key": "owasp_llm__mitre_atlas::owasp_llm:LLM01__mitre_atlas:AML.T001",
            "source_node_id": "owasp_llm:LLM01",
            "target_node_id": "mitre_atlas:AML.T001",
            "source_text": "Prompt Injection",
            "target_text": "LLM Prompt Injection",
            "expert_tier": "Direct",
        }, f)
        f.write("\n")

    cal_path = tmp_path / "cal.jsonl"
    cal_path.write_text("")  # Empty cal for this test

    output = tmp_path / "output"
    output.mkdir()

    stats = build_expert_training_set(
        mappings_path=str(mappings_path),
        frozen_path=str(frozen_path),
        cal_path=str(cal_path),
        output_dir=str(output),
        n_negatives_per_source=1,
    )

    assert (output / "expert_train.jsonl").exists()
    assert (output / "expert_val.jsonl").exists()
    assert stats["n_train"] > 0
    assert stats["n_val"] > 0

    # Read and verify schema
    with (output / "expert_train.jsonl").open() as f:
        first = json.loads(f.readline())
    assert "pair_key" in first
    assert "source_node_id" in first
    assert "target_node_id" in first
    assert "source_text" in first
    assert "target_text" in first
    assert "tier_label" in first
    assert first["tier_label"] in [0, 1, 2, 3]
