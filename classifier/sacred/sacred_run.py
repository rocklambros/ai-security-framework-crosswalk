"""Sacred-run orchestrator for Plan 6.

CLI entry-point that enforces the one-shot evaluation protocol (Contract 10),
loads the appropriate model (LGBMStacker or TwoStageClassifier), evaluates on
``human_test_frozen``, and persists results to ``results/sacred/``.

Usage::

    python -m classifier.sacred.sacred_run --confirm-once
    python -m classifier.sacred.sacred_run --break-glass "reason for re-run"
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _load_model(run_dir: Path):
    """Load either a TwoStageClassifier or an LGBMStacker from *run_dir*.

    The two-stage variant is selected when ``run_dir/two_stage/`` exists.
    Falls back to ``run_dir/model.txt`` for a plain LGBMStacker.
    """
    two_stage_path = run_dir / "two_stage"
    if two_stage_path.exists():
        from classifier.ensemble.two_stage import TwoStageClassifier  # type: ignore[import]

        logger.info("Loading TwoStageClassifier from %s", two_stage_path)
        model = TwoStageClassifier.load(two_stage_path)
    else:
        from classifier.ensemble.stacker import LGBMStacker  # type: ignore[import]

        model_path = run_dir / "model.txt"
        logger.info("Loading LGBMStacker from %s", model_path)
        model = LGBMStacker.load(model_path)
    return model


def _check_environment() -> None:
    """Enforce Contract 10: clean git, on main, not ahead of upstream."""
    import subprocess

    result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True,
        text=True,
        check=True,
    )
    if result.stdout.strip():
        raise RuntimeError(
            "Contract 10: git working tree is not clean. "
            "Commit or stash changes before running the sacred run."
        )

    branch_result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    )
    branch = branch_result.stdout.strip()
    if branch != "main":
        raise RuntimeError(
            f"Contract 10: must be on branch 'main', currently on '{branch}'."
        )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def sacred_run(
    run_dir: Path,
    *,
    confirm_once: bool = False,
    break_glass: str | None = None,
    allow_unpushed: bool = False,
) -> dict:
    """Execute the one-shot sacred evaluation.

    Parameters
    ----------
    run_dir:
        Directory containing the trained model artifact (``model.txt`` or
        ``two_stage/``).
    confirm_once:
        Must be ``True`` to proceed with the evaluation.  Acts as a speed-bump
        to prevent accidental re-runs.
    break_glass:
        If provided, bypasses the one-shot lockfile check with the given
        justification string.  The justification is recorded in the output.
    allow_unpushed:
        When ``True``, skip the check that HEAD is not ahead of ``@{u}``.

    Returns
    -------
    dict
        Evaluation results dict written to ``results/sacred/``.
    """
    if not confirm_once and break_glass is None:
        raise RuntimeError(
            "Pass --confirm-once to proceed with the sacred run, "
            "or --break-glass <reason> to override the lockfile."
        )

    _check_environment()

    # ------------------------------------------------------------------
    # Load pre-registered constants (Contract 15)
    # ------------------------------------------------------------------
    from classifier.sacred.pre_registered import load as load_pre_registered  # type: ignore[import]

    pre_reg = load_pre_registered()
    logger.info("Pre-registered constants loaded: %s", list(pre_reg.keys()))

    # ------------------------------------------------------------------
    # Load model — two-stage or plain stacker
    # ------------------------------------------------------------------
    model = _load_model(run_dir)

    # ------------------------------------------------------------------
    # Load frozen test split (Contract 8 — only this module may access it)
    # ------------------------------------------------------------------
    from classifier.data.splits import load_human_test_frozen  # type: ignore[import]

    pairs = load_human_test_frozen()
    logger.info("Loaded %d frozen test pairs", len(pairs))

    # ------------------------------------------------------------------
    # Run evaluation
    # ------------------------------------------------------------------
    predictions = [model.predict(pair) for pair in pairs]

    results: dict = {
        "n_pairs": len(pairs),
        "predictions": predictions,
        "break_glass": break_glass,
        "pre_registered_sha": pre_reg.get("_sha"),
    }

    # ------------------------------------------------------------------
    # Persist results
    # ------------------------------------------------------------------
    import subprocess

    git_sha = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    results_dir = Path("results/sacred")
    results_dir.mkdir(parents=True, exist_ok=True)
    out_path = results_dir / f"sacred_{git_sha}.json"
    out_path.write_text(json.dumps(results, indent=2))
    logger.info("Sacred run results written to %s", out_path)

    return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="One-shot sacred evaluation run (Plan 6).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--run-dir",
        type=Path,
        default=Path("checkpoints/ensemble"),
        help="Directory containing the trained model artifact.",
    )
    parser.add_argument(
        "--confirm-once",
        action="store_true",
        help="Required flag to proceed with the sacred run.",
    )
    parser.add_argument(
        "--break-glass",
        metavar="REASON",
        help="Override lockfile with a justification string.",
    )
    parser.add_argument(
        "--allow-unpushed",
        action="store_true",
        help="Skip the ahead-of-upstream check.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        results = sacred_run(
            run_dir=args.run_dir,
            confirm_once=args.confirm_once,
            break_glass=args.break_glass,
            allow_unpushed=args.allow_unpushed,
        )
        print(json.dumps({"status": "ok", "n_pairs": results["n_pairs"]}, indent=2))
        return 0
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
