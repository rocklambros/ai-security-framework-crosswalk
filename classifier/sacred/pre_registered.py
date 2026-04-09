"""Pre-registered constants loader with SHA-256 integrity verification (Contract 15).

All numeric thresholds referenced in the sacred run, conformal wrapper, and
abstention router MUST be read via load() at runtime. Hardcoding them in
runtime modules is a Contract 15 violation.
"""
from __future__ import annotations

import hashlib
import json
from functools import lru_cache
from pathlib import Path

PRE_REG_PATH = Path("classifier/sacred/pre_registered.json")
HASHES_PATH = Path("data/splits/hashes.json")


@lru_cache(maxsize=1)
def load() -> dict:
    if not PRE_REG_PATH.exists():
        raise RuntimeError(f"pre_registered.json missing at {PRE_REG_PATH}")
    sha = hashlib.sha256(PRE_REG_PATH.read_bytes()).hexdigest()
    hashes = json.loads(HASHES_PATH.read_text())
    pinned = hashes.get("pre_registered", {}).get("sha256")
    if not pinned:
        raise RuntimeError("pre_registered.json has no sha256 pin in hashes.json")
    if pinned != sha:
        raise RuntimeError(
            f"Contract 15: pre_registered.json sha {sha[:16]}... != pinned {pinned[:16]}..."
        )
    return json.loads(PRE_REG_PATH.read_text())
