"""Contamination CI. Fails loud if any split file's SHA256 drifts from the
committed manifest, or if pair_keys cross between cal and frozen.
"""
from __future__ import annotations
import hashlib
import json
import pytest
from classifier.config import SPLITS_DIR

MANIFEST = SPLITS_DIR / "hashes.json"
TRACKED = ["sme_pool_full.jsonl", "human_cal.jsonl", "human_test_frozen.jsonl"]


def _sha256(path):
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


@pytest.fixture(scope="module")
def manifest():
    assert MANIFEST.exists(), "hashes.json missing — run build_splits.py"
    return json.loads(MANIFEST.read_text())


@pytest.mark.parametrize("fname", TRACKED)
def test_split_sha256_stable(manifest, fname):
    path = SPLITS_DIR / fname
    assert path.exists(), f"{fname} missing"
    actual = _sha256(path)
    expected = manifest[fname]
    assert actual == expected, (
        f"{fname} SHA256 drifted. Split files are immutable after commit. "
        f"If this is an intentional re-split, delete data/splits/, re-run "
        f"build_splits.py, and open a PR that names the reason."
    )


def test_no_pair_key_leakage():
    import pandas as pd
    cal = pd.read_json(SPLITS_DIR / "human_cal.jsonl", lines=True)
    frozen = pd.read_json(SPLITS_DIR / "human_test_frozen.jsonl", lines=True)
    overlap = set(cal["pair_key"]) & set(frozen["pair_key"])
    assert not overlap, f"{len(overlap)} pair_keys leaked between cal and frozen: {list(overlap)[:5]}"


def test_cal_and_frozen_cover_full_pool():
    import pandas as pd
    pool = pd.read_json(SPLITS_DIR / "sme_pool_full.jsonl", lines=True)
    cal = pd.read_json(SPLITS_DIR / "human_cal.jsonl", lines=True)
    frozen = pd.read_json(SPLITS_DIR / "human_test_frozen.jsonl", lines=True)
    assert len(pool) == 550
    assert set(cal["pair_key"]) | set(frozen["pair_key"]) == set(pool["pair_key"])
