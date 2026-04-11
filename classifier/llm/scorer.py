"""Bulk scoring orchestrator: Sonnet n-vote + Opus tiebreaker."""
from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import anthropic

from classifier.llm.cost_tracker import CostTracker
from classifier.llm.judge import JudgeResult, judge_pair
from classifier.llm.prompts import build_system_prompt, build_user_prompt

_DEFAULT_SONNET = "claude-3-5-sonnet-20241022"
_DEFAULT_OPUS = "claude-3-opus-20240229"


@dataclass
class ScoredPair:
    """Scoring result for a single crosswalk pair."""

    pair: dict[str, Any]
    sonnet_votes: list[int] = field(default_factory=list)
    opus_vote: int | None = None
    final_tier: int = -1
    confidence: float = 0.0
    is_unanimous: bool = False
    reasonings: list[str] = field(default_factory=list)

    def compute_consensus(self) -> None:
        """Compute final_tier, confidence, and is_unanimous from votes.

        Uses majority vote among sonnet_votes. If a tie exists, opus_vote
        breaks it. If opus_vote is unavailable on a tie, picks the lower tier.
        """
        if not self.sonnet_votes:
            self.final_tier = -1
            self.confidence = 0.0
            self.is_unanimous = False
            return

        n = len(self.sonnet_votes)
        counts: dict[int, int] = {}
        for v in self.sonnet_votes:
            counts[v] = counts.get(v, 0) + 1

        max_count = max(counts.values())
        self.is_unanimous = max_count == n
        self.confidence = max_count / n

        # Tiers with the highest vote count
        top_tiers = sorted(t for t, c in counts.items() if c == max_count)

        if len(top_tiers) == 1:
            self.final_tier = top_tiers[0]
        elif self.opus_vote is not None:
            # Opus breaks the tie
            self.final_tier = self.opus_vote
        else:
            # Default: lower (more conservative) tier
            self.final_tier = top_tiers[0]


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
        scored.sonnet_votes.append(r.tier)
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
    """Score all pairs with Sonnet using `n_votes` independent calls each.

    Uses an asyncio semaphore to cap concurrency at `max_concurrent` pairs
    (each pair itself fires `n_votes` parallel API calls).
    """
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
    """Re-score non-unanimous pairs with Opus for a single tiebreaking vote.

    Mutates each ScoredPair in-place (sets opus_vote, recomputes consensus).
    Returns the same list for convenience.
    """
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
        sp.opus_vote = result.tier
        sp.reasonings.append(f"[opus] {result.reasoning}")
        sp.compute_consensus()
        return sp

    updated = await asyncio.gather(*[_break_tie(sp) for sp in disagreed])
    return list(updated)


def save_scores(scored: list[ScoredPair], path: str | Path) -> None:
    """Save scored pairs to a JSONL file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        for sp in scored:
            record = {
                "source_id": sp.pair.get("source_id"),
                "target_id": sp.pair.get("target_id"),
                "sonnet_votes": sp.sonnet_votes,
                "opus_vote": sp.opus_vote,
                "final_tier": sp.final_tier,
                "confidence": sp.confidence,
                "is_unanimous": sp.is_unanimous,
            }
            f.write(json.dumps(record) + "\n")
    print(f"Saved {len(scored)} scored pairs → {path}")


def load_scores(path: str | Path) -> list[dict[str, Any]]:
    """Load scored pairs from a JSONL file produced by save_scores."""
    path = Path(path)
    records: list[dict[str, Any]] = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records
