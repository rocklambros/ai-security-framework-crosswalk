"""Prompt templates for LLM-as-judge tier classification."""
from __future__ import annotations

import random
from typing import Any

TIER_DEFINITIONS: dict[int, str] = {
    0: (
        "UNRELATED — The two controls address completely different concerns. "
        "There is no meaningful overlap in scope, objective, or subject matter. "
        "Implementing one provides zero assurance toward the other."
    ),
    1: (
        "PARTIAL — The controls share a thematic or topical connection but diverge "
        "significantly in scope, depth, applicability, or required implementation. "
        "Partial compliance with one may provide limited, incidental evidence toward "
        "the other, but explicit mapping requires significant effort or assumptions."
    ),
    2: (
        "RELATED — The controls address the same security concern and overlap "
        "substantially in objective and typical implementation. Compliance with one "
        "provides meaningful, direct evidence toward the other, though some gaps or "
        "differences in scope, depth, or applicability remain."
    ),
    3: (
        "EQUIVALENT — The controls are functionally identical or near-identical in "
        "purpose, scope, and required implementation. Full compliance with one "
        "constitutes full or near-full compliance with the other. The mapping is "
        "direct and unambiguous."
    ),
}

_TIER_DEF_BLOCK = "\n".join(
    f"  Tier {t}: {desc}" for t, desc in TIER_DEFINITIONS.items()
)

SYSTEM_PROMPT = f"""\
You are a highly accurate AI security framework auditor. Your task is to assess \
the semantic relationship between two AI security controls and assign a tier score.

## Tier Definitions

{_TIER_DEF_BLOCK}

## Instructions

1. Read both controls carefully, paying attention to their names AND descriptions.
2. Reason step-by-step:
   - What is the core security concern of Control A?
   - What is the core security concern of Control B?
   - Where do they overlap? Where do they diverge?
   - Does compliance with one provide direct evidence toward the other?
3. Select the most appropriate tier (0, 1, 2, or 3).
4. Respond ONLY with a JSON object in exactly this format (no markdown, no extra text):
   {{"reasoning": "<your chain-of-thought reasoning>", "tier": <0|1|2|3>}}

{{few_shot_block}}\
"""

USER_PROMPT_TEMPLATE = """\
## Control A
Framework: {framework_a}
ID: {id_a}
Name: {name_a}
Description: {desc_a}

## Control B
Framework: {framework_b}
ID: {id_b}
Name: {name_b}
Description: {desc_b}

Assess the tier relationship between Control A and Control B.\
"""


def build_system_prompt(few_shot_examples: list[dict[str, Any]] | None = None) -> str:
    """Build the system prompt, optionally appending few-shot examples."""
    if not few_shot_examples:
        return SYSTEM_PROMPT.replace("{few_shot_block}", "")

    lines: list[str] = ["## Few-Shot Examples\n"]
    for i, ex in enumerate(few_shot_examples, 1):
        lines.append(f"### Example {i}")
        lines.append(
            USER_PROMPT_TEMPLATE.format(
                framework_a=ex.get("source_framework", ""),
                id_a=ex.get("source_id", ""),
                name_a=ex.get("source_name", ""),
                desc_a=ex.get("source_description", ""),
                framework_b=ex.get("target_framework", ""),
                id_b=ex.get("target_id", ""),
                name_b=ex.get("target_name", ""),
                desc_b=ex.get("target_description", ""),
            )
        )
        lines.append(
            f'Answer: {{"reasoning": "(example)", "tier": {ex["tier_label"]}}}\n'
        )

    few_shot_block = "\n".join(lines) + "\n"
    return SYSTEM_PROMPT.replace("{few_shot_block}", few_shot_block)


def build_user_prompt(pair: dict[str, Any]) -> str:
    """Build the user-turn prompt from a pair dict."""
    return USER_PROMPT_TEMPLATE.format(
        framework_a=pair.get("source_framework", ""),
        id_a=pair.get("source_id", ""),
        name_a=pair.get("source_name", ""),
        desc_a=pair.get("source_description", ""),
        framework_b=pair.get("target_framework", ""),
        id_b=pair.get("target_id", ""),
        name_b=pair.get("target_name", ""),
        desc_b=pair.get("target_description", ""),
    )


def select_few_shot_examples(
    human_cal_train: list[dict[str, Any]],
    n_per_tier: int = 5,
    seed: int = 42,
) -> list[dict[str, Any]]:
    """Select balanced few-shot examples from training data.

    Samples up to `n_per_tier` examples per tier (0-3). Tiers with fewer
    than `n_per_tier` examples return all available.
    """
    rng = random.Random(seed)
    selected: list[dict[str, Any]] = []
    for tier in range(4):
        pool = [r for r in human_cal_train if r["tier_label"] == tier]
        k = min(n_per_tier, len(pool))
        selected.extend(rng.sample(pool, k))
    # Sort by tier for readability
    selected.sort(key=lambda r: r["tier_label"])
    return selected
