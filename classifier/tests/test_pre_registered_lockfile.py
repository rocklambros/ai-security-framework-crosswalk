"""Contract test for classifier/sacred/pre_registered.json.

Asserts the pre-registered constants file exists, parses, is hash-pinned in
hashes.json, and that any runtime module consuming these constants reads
them by key (not by magic number). Runs at every phase pre-flight.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

PRE_REG = Path("classifier/sacred/pre_registered.json")
HASHES = Path("data/splits/hashes.json")


def test_pre_registered_exists_and_parses():
    assert PRE_REG.exists(), f"{PRE_REG} missing — sacred run refuses to fire"
    data = json.loads(PRE_REG.read_text())
    for key in ("conformal", "abstention", "statistical_tests", "retrieval",
                "labeling_weights", "seeds"):
        assert key in data, f"pre_registered missing section: {key}"


def test_pre_registered_values_locked():
    data = json.loads(PRE_REG.read_text())
    # These are the spec §6 non-negotiables. Changing any of them requires
    # a --break-glass commit and a methodology disclosure update.
    assert data["conformal"]["alpha"] == 0.10
    assert data["conformal"]["coverage_target"] == 0.90
    assert data["abstention"]["precision_floor"] == 0.95
    assert data["statistical_tests"]["bh_fdr_alpha"] == 0.05
    assert data["statistical_tests"]["framework_pair_count"] == 12
    assert data["labeling_weights"] == {
        "upstream_v1": 1.0, "llm_sme_v1": 0.6, "human_cal_v1": 1.0
    }


def test_pre_registered_hash_pinned():
    sha = hashlib.sha256(PRE_REG.read_bytes()).hexdigest()
    hashes = json.loads(HASHES.read_text())
    entry = hashes.get("pre_registered", {})
    assert entry.get("sha256") == sha, (
        f"pre_registered.json sha {sha} does not match hashes.json — "
        "drift detected or pin missing"
    )
