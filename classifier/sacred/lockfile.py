"""Sacred run lockfile mechanism.

The lockfile prevents a second sacred run. Once written, it cannot be
overwritten without --break-glass. This is the enforcement mechanism
for the one-shot rule (Contract 10).
"""
from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


LOCKFILE_DIR = Path("data/sacred")


def _git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True
        ).strip()
    except subprocess.CalledProcessError:
        return "unknown"


def _git_clean() -> bool:
    try:
        out = subprocess.check_output(
            ["git", "status", "--porcelain"], text=True
        ).strip()
        return len(out) == 0
    except subprocess.CalledProcessError:
        return False


def _git_branch() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], text=True
        ).strip()
    except subprocess.CalledProcessError:
        return "unknown"


def check_lockfile() -> Path | None:
    """Return path to existing lockfile if one exists, else None."""
    LOCKFILE_DIR.mkdir(parents=True, exist_ok=True)
    locks = list(LOCKFILE_DIR.glob("lock_*.json"))
    return locks[0] if locks else None


def write_lockfile(results: dict, break_glass: bool = False) -> Path:
    """Write the sacred run lockfile.

    Raises if a lockfile already exists (unless break_glass=True).
    """
    existing = check_lockfile()
    if existing and not break_glass:
        raise RuntimeError(
            f"Contract 10: Sacred run already executed. Lockfile at {existing}. "
            f"Use --break-glass to override (requires committed justification)."
        )

    sha = _git_sha()
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    lockfile = LOCKFILE_DIR / f"lock_{sha[:8]}_{ts}.json"

    data = {
        "git_sha": sha,
        "git_branch": _git_branch(),
        "git_clean": _git_clean(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "break_glass": break_glass,
        "results_summary": results,
    }

    lockfile.parent.mkdir(parents=True, exist_ok=True)
    lockfile.write_text(json.dumps(data, indent=2, sort_keys=True))
    return lockfile


def verify_environment(allow_unpushed: bool = False) -> None:
    """Contract 10: Verify environment is clean for sacred run.

    Checks:
      1. git status --porcelain is empty (no uncommitted changes)
      2. Current branch is main
      3. No existing lockfile
    """
    if not _git_clean():
        raise RuntimeError(
            "Contract 10: Working tree is not clean. "
            "Commit or stash all changes before the sacred run."
        )

    branch = _git_branch()
    if branch != "main":
        raise RuntimeError(
            f"Contract 10: Must be on 'main' branch, currently on '{branch}'."
        )

    existing = check_lockfile()
    if existing:
        raise RuntimeError(
            f"Contract 10: Sacred run already executed. Lockfile at {existing}."
        )
