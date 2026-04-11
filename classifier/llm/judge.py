"""Core single-pair LLM judge with retry and exponential backoff."""
from __future__ import annotations

import asyncio
import json
import re
from dataclasses import dataclass

import anthropic

from classifier.llm.cost_tracker import CostTracker

_DEFAULT_MODEL = "claude-3-5-sonnet-20241022"
_TEMP_FIRST = 0.0
_TEMP_RETRY = 0.3

# Regex fallback: look for "tier": <digit>
_TIER_RE = re.compile(r'"tier"\s*:\s*([0-3])', re.IGNORECASE)
# Strip markdown code fences
_FENCE_RE = re.compile(r"```(?:json)?\s*([\s\S]*?)```", re.IGNORECASE)


@dataclass
class JudgeResult:
    """Result from a single LLM judge call."""

    tier: int
    reasoning: str
    model: str
    input_tokens: int
    output_tokens: int
    raw_response: str


def _parse_response(raw: str) -> tuple[int, str]:
    """Extract (tier, reasoning) from the model's raw text output.

    Handles:
      - Plain JSON
      - JSON wrapped in markdown fences
      - Fallback regex extraction of tier
    """
    text = raw.strip()

    # Strip markdown fences if present
    fence_match = _FENCE_RE.search(text)
    if fence_match:
        text = fence_match.group(1).strip()

    # Attempt full JSON parse
    try:
        data = json.loads(text)
        tier = int(data["tier"])
        if tier not in (0, 1, 2, 3):
            raise ValueError(f"Tier out of range: {tier}")
        return tier, str(data.get("reasoning", ""))
    except (json.JSONDecodeError, KeyError, ValueError):
        pass

    # Fallback: regex for tier value
    m = _TIER_RE.search(raw)
    if m:
        return int(m.group(1)), ""

    raise ValueError(f"Could not parse tier from response: {raw[:200]!r}")


async def judge_pair(
    client: anthropic.AsyncAnthropic,
    system_prompt: str,
    user_prompt: str,
    model: str = _DEFAULT_MODEL,
    cost_tracker: CostTracker | None = None,
    max_retries: int = 3,
) -> JudgeResult:
    """Call the Anthropic API to classify a single pair, with retry.

    Temperature is 0.0 on the first attempt and 0.3 on retries to
    encourage different output if parsing fails or an error occurs.
    """
    last_exc: Exception | None = None

    for attempt in range(max_retries):
        temperature = _TEMP_FIRST if attempt == 0 else _TEMP_RETRY
        wait = 2 ** attempt  # exponential backoff: 1s, 2s, 4s

        try:
            response = await client.messages.create(
                model=model,
                max_tokens=1024,
                temperature=temperature,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )

            raw = response.content[0].text
            tier, reasoning = _parse_response(raw)

            in_tok = response.usage.input_tokens
            out_tok = response.usage.output_tokens

            if cost_tracker is not None:
                cost_tracker.add(model, in_tok, out_tok)

            return JudgeResult(
                tier=tier,
                reasoning=reasoning,
                model=model,
                input_tokens=in_tok,
                output_tokens=out_tok,
                raw_response=raw,
            )

        except anthropic.RateLimitError as exc:
            last_exc = exc
            await asyncio.sleep(wait * 5)  # longer backoff for rate limits
        except anthropic.APIStatusError as exc:
            last_exc = exc
            if exc.status_code in (500, 529):
                await asyncio.sleep(wait)
            else:
                raise
        except (ValueError, IndexError) as exc:
            # Parse failure — retry with higher temperature
            last_exc = exc
            await asyncio.sleep(wait)

    raise RuntimeError(
        f"judge_pair failed after {max_retries} attempts"
    ) from last_exc
