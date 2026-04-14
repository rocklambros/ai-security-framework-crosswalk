"""Test that build_expert_training produces soft-labeled rows."""
import json
from pathlib import Path


def test_soft_labels_expand_upstream_rows():
    """Each upstream positive should produce 3 rows (one per soft prior)."""
    real_train = Path("data/splits/expert_train.jsonl")
    if not real_train.exists():
        return  # skip if no data

    rows = [json.loads(l) for l in real_train.read_text().splitlines() if l.strip()]
    upstream_rows = [r for r in rows if r.get("data_source") == "expert_upstream"]
    neg_rows = [r for r in rows if r.get("data_source") == "hard_negative"]

    # With soft labels, upstream rows should be ~3x the unique pairs
    unique_upstream_pairs = len({r["pair_key"] for r in upstream_rows})
    assert len(upstream_rows) >= unique_upstream_pairs * 2, (
        f"Expected soft label expansion: {len(upstream_rows)} rows for "
        f"{unique_upstream_pairs} unique pairs"
    )

    # Every upstream row should have sample_weight
    for r in upstream_rows:
        assert "sample_weight" in r, f"Missing sample_weight in {r['pair_key']}"
        assert 0 < r["sample_weight"] <= 1.0

    # Hard negatives should have sample_weight
    for r in neg_rows:
        assert "sample_weight" in r


def test_soft_labels_tier_distribution():
    """Soft labels should produce RELATED, EQUIVALENT, and PARTIAL for upstream."""
    real_train = Path("data/splits/expert_train.jsonl")
    if not real_train.exists():
        return

    rows = [json.loads(l) for l in real_train.read_text().splitlines() if l.strip()]
    upstream_rows = [r for r in rows if r.get("data_source") == "expert_upstream"]
    tiers = {r["tier_label"] for r in upstream_rows}

    # Should have tiers 1, 2, 3 (PARTIAL, RELATED, EQUIVALENT)
    assert 1 in tiers, "No PARTIAL labels in upstream rows"
    assert 2 in tiers, "No RELATED labels in upstream rows"
    assert 3 in tiers, "No EQUIVALENT labels in upstream rows"
    # Should NOT have tier 0 (UNRELATED) in upstream positive rows
    assert 0 not in tiers, "UNRELATED should not appear in upstream positive rows"
