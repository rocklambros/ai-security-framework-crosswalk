"""Bulk scoring orchestrator: Sonnet n-vote + Opus tiebreaker."""
from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import anthropic

from classifier.llm.cost_tracker import CostTracker
from classifier.llm.judge import JudgeResult, judge_pair, score_to_tier
from classifier.llm.prompts import build_system_prompt, build_user_prompt

_DEFAULT_SONNET = "claude-sonnet-4-20250514"
_DEFAULT_OPUS = "claude-opus-4-20250514"


@dataclass
class ScoredPair:
    """Scoring result for a single crosswalk pair."""

    pair: dict[str, Any]
    sonnet_scores: list[float] = field(default_factory=list)  # raw 0-10 scores
    sonnet_tiers: list[int] = field(default_factory=list)     # mapped tiers 0-3
    opus_score: float | None = None
    opus_tier: int | None = None
    final_score: float = -1.0      # mean of all scores
    final_tier: int = -1           # from final_score
    confidence: float = 0.0
    is_unanimous: bool = False
    reasonings: list[str] = field(default_factory=list)

    def compute_consensus(self) -> None:
        """Compute final_score/tier from raw scores.

        Uses mean of all scores (Sonnet + Opus if available), maps to tier.
        """
        if not self.sonnet_scores:
            return

        all_scores = list(self.sonnet_scores)
        if self.opus_score is not None:
            all_scores.append(self.opus_score)

        self.final_score = sum(all_scores) / len(all_scores)
        self.final_tier = score_to_tier(self.final_score)

        # Unanimity: all sonnet tiers agree
        self.is_unanimous = len(set(self.sonnet_tiers)) == 1
        # Confidence: 1 - normalized std dev of scores
        if len(all_scores) > 1:
            import statistics
            std = statistics.stdev(all_scores)
            self.confidence = max(0.0, 1.0 - std / 5.0)  # normalize by half-range
        else:
            self.confidence = 0.5


async def _score_one(
    semaphore: asyncio.Semaphore,
    client: anthropic.AsyncAnthropic,
    system_prompt: str,
    pair: dict[str, Any],
    model: str,
    n_votes: int,
    cost_tracker: CostTracker | None,
) -> ScoredPair:
    """Score a single pair with `n_votes` calls to `model`."""
    user_prompt = build_user_prompt(pair)
    scored = ScoredPair(pair=pair)

    async with semaphore:
        tasks = [
            judge_pair(client, system_prompt, user_prompt, model, cost_tracker)
            for _ in range(n_votes)
        ]
        results: list[JudgeResult] = await asyncio.gather(*tasks)

    for r in results:
        scored.sonnet_scores.append(r.score)
        scored.sonnet_tiers.append(r.tier)
        scored.reasonings.append(r.reasoning)

    scored.compute_consensus()
    return scored


async def score_pairs_bulk(
    pairs: list[dict[str, Any]],
    few_shot_examples: list[dict[str, Any]] | None = None,
    model: str = _DEFAULT_SONNET,
    n_votes: int = 3,
    max_concurrent: int = 50,
    cost_tracker: CostTracker | None = None,
) -> list[ScoredPair]:
    """Score all pairs with n_votes independent calls each."""
    system_prompt = build_system_prompt(few_shot_examples)
    semaphore = asyncio.Semaphore(max_concurrent)
    client = anthropic.AsyncAnthropic()

    total = len(pairs)
    print(f"Scoring {total} pairs × {n_votes} votes on {model} …")

    completed = 0

    async def _wrapped(pair: dict[str, Any]) -> ScoredPair:
        nonlocal completed
        result = await _score_one(
            semaphore, client, system_prompt, pair, model, n_votes, cost_tracker
        )
        completed += 1
        if completed % 10 == 0 or completed == total:
            print(f"  progress: {completed}/{total}")
            if cost_tracker is not None:
                cost_tracker.log()
        return result

    scored = await asyncio.gather(*[_wrapped(p) for p in pairs])
    return list(scored)


async def opus_tiebreaker(
    disagreed: list[ScoredPair],
    few_shot_examples: list[dict[str, Any]] | None = None,
    model: str = _DEFAULT_OPUS,
    max_concurrent: int = 10,
    cost_tracker: CostTracker | None = None,
) -> list[ScoredPair]:
    """Re-score non-unanimous pairs with Opus for tiebreaking."""
    if not disagreed:
        return disagreed

    system_prompt = build_system_prompt(few_shot_examples)
    semaphore = asyncio.Semaphore(max_concurrent)
    client = anthropic.AsyncAnthropic()

    total = len(disagreed)
    print(f"Opus tiebreaker: {total} pairs on {model} …")

    async def _break_tie(sp: ScoredPair) -> ScoredPair:
        user_prompt = build_user_prompt(sp.pair)
        async with semaphore:
            result = await judge_pair(
                client, system_prompt, user_prompt, model, cost_tracker
            )
        sp.opus_score = result.score
        sp.opus_tier = result.tier
        sp.reasonings.append(f"[opus] {result.reasoning}")
        sp.compute_consensus()
        return sp

    updated = await asyncio.gather(*[_break_tie(sp) for sp in disagreed])
    return list(updated)


def save_scores(scored: list[ScoredPair], path: str | Path) -> None:
    """Save scored pairs to JSONL."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        for sp in scored:
            record = {
                "source_id": sp.pair.get("source_node_id") or sp.pair.get("source_id"),
                "target_id": sp.pair.get("target_node_id") or sp.pair.get("target_id"),
                "sonnet_scores": sp.sonnet_scores,
                "sonnet_tiers": sp.sonnet_tiers,
                "opus_score": sp.opus_score,
                "opus_tier": sp.opus_tier,
                "final_score": sp.final_score,
                "final_tier": sp.final_tier,
                "confidence": sp.confidence,
                "is_unanimous": sp.is_unanimous,
            }
            f.write(json.dumps(record) + "\n")
    print(f"Saved {len(scored)} scored pairs → {path}")


def load_scores(path: str | Path) -> list[dict[str, Any]]:
    """Load scored pairs from JSONL."""
    path = Path(path)
    records: list[dict[str, Any]] = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records
