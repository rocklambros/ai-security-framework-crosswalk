"""Orchestrate Phase 0 gate + Sonnet bulk scoring + Opus tiebreaker.

Usage examples:
  python scripts/run_llm_scoring.py               # all: gate then bulk
  python scripts/run_llm_scoring.py --phase 0     # gate only
  python scripts/run_llm_scoring.py --phase bulk  # bulk only (skip gate)
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

SPLITS: dict[str, Path] = {
    "expert_train": Path("data/splits/expert_train.jsonl"),
    "expert_val": Path("data/splits/expert_val.jsonl"),
    "human_cal": Path("data/splits/human_cal.jsonl"),
    "human_test_frozen": Path("data/splits/human_test_frozen.jsonl"),
}

OUTPUT_DIR = Path("data/processed/llm_scores_v4")
COST_REPORT_PATH = OUTPUT_DIR / "cost_report.json"

# ---------------------------------------------------------------------------
# API key bootstrap
# ---------------------------------------------------------------------------


def _load_api_key() -> str:
    """Return the Anthropic API key from env or pass(1)."""
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if key:
        return key

    print("[auth] ANTHROPIC_API_KEY not set — trying 'pass show anthropic/api-key' …")
    result = subprocess.run(
        ["pass", "show", "anthropic/api-key"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"[auth] pass failed: {result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)

    key = result.stdout.strip().splitlines()[0]
    if not key:
        print("[auth] pass returned empty key", file=sys.stderr)
        sys.exit(1)

    os.environ["ANTHROPIC_API_KEY"] = key
    print("[auth] API key loaded from pass.")
    return key


# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    """Load a JSONL file into a list of dicts."""
    records: list[dict[str, Any]] = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


# ---------------------------------------------------------------------------
# Human-cal quality metrics
# ---------------------------------------------------------------------------


def _print_human_cal_quality(
    scored: list[Any],  # list[ScoredPair]
    records: list[dict[str, Any]],
) -> None:
    """Compare LLM predictions to human expert labels and print metrics."""
    from sklearn.metrics import (
        accuracy_score,
        classification_report,
        f1_score,
    )

    TIER_MAP = {"Direct": 3, "Related": 2, "Tangential": 1, "None": 0}

    y_true = []
    y_pred = []
    for sp, rec in zip(scored, records):
        expert_tier_str = rec.get("expert_tier", "")
        if expert_tier_str not in TIER_MAP:
            continue
        y_true.append(TIER_MAP[expert_tier_str])
        y_pred.append(sp.final_tier)

    if not y_true:
        print("  [human_cal] No expert labels found — skipping quality metrics.")
        return

    acc = accuracy_score(y_true, y_pred)
    macro_f1 = f1_score(y_true, y_pred, average="macro", zero_division=0)

    print("\n--- human_cal quality vs. expert labels ---")
    print(f"  n               : {len(y_true)}")
    print(f"  tier_accuracy   : {acc:.4f}")
    print(f"  macro_f1        : {macro_f1:.4f}")
    print(
        classification_report(
            y_true,
            y_pred,
            labels=[0, 1, 2, 3],
            target_names=["Tier0", "Tier1", "Tier2", "Tier3"],
            zero_division=0,
        )
    )


# ---------------------------------------------------------------------------
# Phase 0
# ---------------------------------------------------------------------------


async def _run_phase0() -> dict[str, Any]:
    from classifier.llm.validation_gate import run_validation_gate

    result = await run_validation_gate(
        min_macro_f1=0.45,
        n_votes=3,
        use_opus_tiebreaker=True,
        wandb_run=None,
    )
    return result


# ---------------------------------------------------------------------------
# Bulk scoring
# ---------------------------------------------------------------------------


async def _score_split(
    split_name: str,
    path: Path,
    few_shot_examples: list[dict[str, Any]],
    cost_tracker: Any,
) -> None:
    """Score one data split and save results."""
    from classifier.llm.scorer import (
        ScoredPair,
        opus_tiebreaker,
        save_scores,
        score_pairs_bulk,
    )

    print(f"\n{'=' * 60}")
    print(f"Scoring split: {split_name}  ({path})")
    print("=" * 60)

    records = _load_jsonl(path)
    print(f"  Loaded {len(records)} pairs.")

    # Sonnet 3-vote bulk scoring
    scored: list[ScoredPair] = await score_pairs_bulk(
        pairs=records,
        few_shot_examples=few_shot_examples,
        n_votes=3,
        max_concurrent=50,
        cost_tracker=cost_tracker,
    )

    # Opus tiebreaker on non-unanimous pairs
    disagreed = [sp for sp in scored if not sp.is_unanimous]
    if disagreed:
        print(f"\nOpus tiebreaker: {len(disagreed)} non-unanimous pairs …")
        await opus_tiebreaker(
            disagreed=disagreed,
            few_shot_examples=few_shot_examples,
            max_concurrent=10,
            cost_tracker=cost_tracker,
        )
    else:
        print("\nAll pairs unanimous — no Opus tiebreaker calls needed.")

    # Quality metrics for human_cal
    if split_name == "human_cal":
        _print_human_cal_quality(scored, records)

    # Save
    out_path = OUTPUT_DIR / f"{split_name}.jsonl"
    save_scores(scored, out_path)
    cost_tracker.log()


async def _run_bulk() -> None:
    from classifier.data.split_human_cal import split_human_cal
    from classifier.llm.cost_tracker import CostTracker
    from classifier.llm.prompts import select_few_shot_examples

    print("\n[bulk] Loading human_cal for few-shot examples …")
    train_records, _val, _idx_tr, _idx_val = split_human_cal()
    few_shot_examples = select_few_shot_examples(train_records, n_per_tier=5)
    print(f"[bulk] Selected {len(few_shot_examples)} few-shot examples.")

    cost_tracker = CostTracker()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for split_name, path in SPLITS.items():
        await _score_split(split_name, path, few_shot_examples, cost_tracker)

    # Save cost report
    report = cost_tracker.summary()
    with COST_REPORT_PATH.open("w") as f:
        json.dump(report, f, indent=2)
    print(f"\n[cost] Saved cost report → {COST_REPORT_PATH}")
    cost_tracker.log()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


async def _main(phase: str) -> None:
    _load_api_key()

    if phase in ("0", "all"):
        print("\n=== Phase 0: Validation Gate ===")
        gate_result = await _run_phase0()
        if not gate_result["gate_passed"]:
            print(
                "\n[gate] Gate FAILED. "
                "Investigate prompt quality before proceeding to bulk scoring.",
                file=sys.stderr,
            )
            if phase == "all":
                sys.exit(1)
            return

    if phase in ("bulk", "all"):
        print("\n=== Bulk Scoring ===")
        await _run_bulk()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="LLM scoring pipeline: Phase 0 gate + Sonnet bulk + Opus tiebreaker."
    )
    parser.add_argument(
        "--phase",
        choices=["0", "bulk", "all"],
        default="all",
        help=(
            "0 = Phase 0 gate only; "
            "bulk = bulk scoring only (skip gate); "
            "all = gate then bulk (default)"
        ),
    )
    args = parser.parse_args()
    asyncio.run(_main(args.phase))


if __name__ == "__main__":
    main()
