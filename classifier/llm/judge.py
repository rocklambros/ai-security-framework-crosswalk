"""Core single-pair LLM judge with retry and exponential backoff."""
from __future__ import annotations

import asyncio
import json
import re
from dataclasses import dataclass

import anthropic

from classifier.llm.cost_tracker import CostTracker

_DEFAULT_MODEL = "claude-sonnet-4-20250514"
_TEMP_FIRST = 0.0
_TEMP_RETRY = 0.3

# Regex fallbacks
_SCORE_RE = re.compile(r'"score"\s*:\s*(\d+(?:\.\d+)?)', re.IGNORECASE)
_TIER_RE = re.compile(r'"tier"\s*:\s*([0-3])', re.IGNORECASE)
_FENCE_RE = re.compile(r"```(?:json)?\s*([\s\S]*?)```", re.IGNORECASE)


@dataclass
class JudgeResult:
    """Result from a single LLM judge call."""

    score: float  # raw 0-10 score from LLM
    tier: int     # mapped tier 0-3
    reasoning: str
    model: str
    input_tokens: int
    output_tokens: int
    raw_response: str


def score_to_tier(score: float) -> int:
    """Map a 0-10 similarity score to a tier (0-3).

    Default boundaries (will be calibrated post-hoc):
      0-2.5  → Tier 0 (Unrelated)
      2.5-5  → Tier 1 (Partial)
      5-7.5  → Tier 2 (Related)
      7.5-10 → Tier 3 (Equivalent)
    """
    if score < 2.5:
        return 0
    elif score < 5.0:
        return 1
    elif score < 7.5:
        return 2
    else:
        return 3


def _parse_response(raw: str) -> tuple[float, str]:
    """Extract (score, reasoning) from the model's raw text output.

    The model outputs {"reasoning": "...", "score": N} where N is 0-10.
    Also handles legacy {"reasoning": "...", "tier": N} format.
    """
    text = raw.strip()

    # Strip markdown fences if present
    fence_match = _FENCE_RE.search(text)
    if fence_match:
        text = fence_match.group(1).strip()

    # Attempt full JSON parse
    try:
        data = json.loads(text)
        reasoning = str(data.get("reasoning", ""))

        # Prefer "score" field (0-10 scale)
        if "score" in data:
            score = float(data["score"])
            score = max(0.0, min(10.0, score))  # clamp
            return score, reasoning

        # Fallback: "tier" field (0-3 scale) → convert to score
        if "tier" in data:
            tier = int(data["tier"])
            if tier in (0, 1, 2, 3):
                score_map = {0: 1.0, 1: 4.0, 2: 7.0, 3: 9.0}
                return score_map[tier], reasoning

    except (json.JSONDecodeError, KeyError, ValueError):
        pass

    # Regex fallback: score
    m = _SCORE_RE.search(raw)
    if m:
        score = float(m.group(1))
        return max(0.0, min(10.0, score)), ""

    # Regex fallback: tier
    m = _TIER_RE.search(raw)
    if m:
        tier = int(m.group(1))
        score_map = {0: 1.0, 1: 4.0, 2: 7.0, 3: 9.0}
        return score_map.get(tier, 1.0), ""

    raise ValueError(f"Could not parse score from response: {raw[:200]!r}")


async def judge_pair(
    client: anthropic.AsyncAnthropic,
    system_prompt: str,
    user_prompt: str,
    model: str = _DEFAULT_MODEL,
    cost_tracker: CostTracker | None = None,
    max_retries: int = 5,
) -> JudgeResult:
    """Call the Anthropic API to score a single pair, with retry.

    Returns a JudgeResult with both a raw score (0-10) and mapped tier (0-3).
    """
    last_exc: Exception | None = None

    for attempt in range(max_retries):
        temperature = _TEMP_FIRST if attempt == 0 else _TEMP_RETRY
        wait = 2 ** attempt

        try:
            response = await client.messages.create(
                model=model,
                max_tokens=1024,
                temperature=temperature,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )

            raw = response.content[0].text
            score, reasoning = _parse_response(raw)

            in_tok = response.usage.input_tokens
            out_tok = response.usage.output_tokens

            if cost_tracker is not None:
                cost_tracker.add(model, in_tok, out_tok)

            return JudgeResult(
                score=score,
                tier=score_to_tier(score),
                reasoning=reasoning,
                model=model,
                input_tokens=in_tok,
                output_tokens=out_tok,
                raw_response=raw,
            )

        except anthropic.RateLimitError as exc:
            last_exc = exc
            await asyncio.sleep(wait * 20)  # aggressive backoff for rate limits
        except anthropic.APIStatusError as exc:
            last_exc = exc
            if exc.status_code in (500, 529):
                await asyncio.sleep(wait)
            else:
                raise
        except (ValueError, IndexError) as exc:
            last_exc = exc
            await asyncio.sleep(wait)

    raise RuntimeError(
        f"judge_pair failed after {max_retries} attempts"
    ) from last_exc
