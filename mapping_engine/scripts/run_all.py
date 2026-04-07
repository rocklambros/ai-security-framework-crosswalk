"""CLI: discover every pair config and run the pipeline for each."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from mapping_engine.scripts.run_pair import main as run_pair_main

REPO = Path(__file__).resolve().parents[2]
PAIRS_DIR = REPO / "mapping_engine" / "config" / "pairs"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-rerank", action="store_true")
    ap.add_argument("--hand-tuned", action="store_true")
    ap.add_argument("--output-dir", default=None)
    ap.add_argument("--no-merge", action="store_true")
    args = ap.parse_args(argv)

    pair_files = sorted(PAIRS_DIR.glob("*.yaml"))
    if not pair_files:
        print("[run_all] no pair configs found", file=sys.stderr)
        return 1

    exit_code = 0
    for pf in pair_files:
        pair_name = pf.stem
        print(f"\n===== [run_all] {pair_name} =====")
        sub = [pair_name]
        if args.no_rerank:
            sub.append("--no-rerank")
        if args.hand_tuned:
            sub.append("--hand-tuned")
        if args.output_dir:
            sub.extend(["--output-dir", args.output_dir])
        if args.no_merge:
            sub.append("--no-merge")
        rc = run_pair_main(sub)
        if rc != 0:
            exit_code = rc
            print(f"[run_all] {pair_name} failed (exit {rc})", file=sys.stderr)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
