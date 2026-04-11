"""Prompt templates for LLM-as-judge tier classification.

Pair dicts use these fields:
  source_node_id, target_node_id  — e.g. "aiuc_1:A004.3"
  source_text, target_text        — control text (name/description)
  tier_label                      — int 0-3 (added by split_human_cal)
  expert_tier                     — str "None"/"Tangential"/"Related"/"Direct"

Node enrichment (from nodes.json) adds: framework, name, description, domain.
"""
from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

TIER_DEFINITIONS: dict[int, str] = {
    0: (
        "UNRELATED — The controls address genuinely different security concerns "
        "with no meaningful connection. Example: an access control requirement vs. "
        "a data backup requirement."
    ),
    1: (
        "PARTIAL (Tangential) — The controls are in the same broad security domain "
        "but address different specific aspects. There is a thematic connection, but "
        "implementing one gives only indirect or incidental evidence toward the other. "
        "Example: a password policy vs. a session management requirement — both are "
        "authentication-adjacent but address different mechanisms."
    ),
    2: (
        "RELATED — The controls address overlapping security concerns and share "
        "meaningful functional overlap. Implementing one would partially satisfy or "
        "contribute direct evidence toward the other. They may differ in scope, "
        "specificity, or framing, but the core intent overlaps. Example: 'monitor "
        "AI model outputs for harmful content' vs. 'implement output filtering for "
        "AI systems' — same goal, different approach emphasis."
    ),
    3: (
        "EQUIVALENT (Direct) — The controls address the same requirement, even if "
        "worded differently or at different levels of specificity. Full compliance "
        "with one substantially satisfies the other. Example: 'maintain an AI model "
        "inventory' vs. 'catalog all AI/ML models in use' — same requirement, "
        "different phrasing."
    ),
}

_TIER_DEF_BLOCK = "\n".join(
    f"  Tier {t}: {desc}" for t, desc in TIER_DEFINITIONS.items()
)

SYSTEM_PROMPT = f"""\
You are an expert AI security framework auditor performing compliance crosswalk analysis. \
Your task is to assess how strongly two security controls/requirements relate to each other.

## Scoring Scale (0-10)

Rate the functional overlap between the two controls on a 0-10 scale:
- **0-1**: Completely unrelated. Different security domains, no connection.
- **2-3**: Same broad area (e.g., both "security") but different specific concerns.
- **4-5**: Tangential. Share a thematic connection. Implementing one gives indirect evidence toward the other.
- **6-7**: Related. Address overlapping concerns. Implementing one provides meaningful evidence toward the other, \
but gaps in scope or specificity remain.
- **8-9**: Strongly related. Address the same core requirement with minor differences in framing or scope.
- **10**: Functionally equivalent. Same requirement, different words.

## Instructions

1. Read both controls, paying attention to names, descriptions, AND security domains.
2. Think about what a compliance auditor would say:
   - Would these controls appear in the same section of an audit?
   - Would evidence for one control count toward the other?
   - Is one a subset/superset of the other?
3. Consider that different frameworks use very different terminology for the same concept. \
"Defensive prompting" and "Excessive Agency prevention" may be the same functional requirement \
expressed differently.
4. Respond ONLY with a JSON object (no markdown):
   {{"reasoning": "<your chain-of-thought reasoning>", "score": <0-10>}}

{{few_shot_block}}\
"""

USER_PROMPT_TEMPLATE = """\
## Control A
Framework: {framework_a}
ID: {id_a}
Name: {name_a}
Domain: {domain_a}
Description: {desc_a}

## Control B
Framework: {framework_b}
ID: {id_b}
Name: {name_b}
Domain: {domain_b}
Description: {desc_b}

Assess the tier relationship between Control A and Control B.\
"""

# Lazy-loaded node metadata cache
_NODE_MAP: dict[str, dict] | None = None


def _get_node_map() -> dict[str, dict]:
    """Load node metadata from nodes.json (cached)."""
    global _NODE_MAP
    if _NODE_MAP is None:
        nodes = json.loads(Path("data/processed/nodes.json").read_text())
        _NODE_MAP = {n["node_id"]: n for n in nodes}
    return _NODE_MAP


def _enrich_pair(pair: dict[str, Any]) -> dict[str, str]:
    """Extract prompt fields from a pair dict, enriching from nodes.json."""
    node_map = _get_node_map()
    src = node_map.get(pair.get("source_node_id", ""), {})
    tgt = node_map.get(pair.get("target_node_id", ""), {})

    return {
        "framework_a": src.get("framework", ""),
        "id_a": src.get("local_id", pair.get("source_node_id", "")),
        "name_a": src.get("name", ""),
        "domain_a": src.get("domain", "") or "",
        "desc_a": src.get("description", "") or pair.get("source_text", ""),
        "framework_b": tgt.get("framework", ""),
        "id_b": tgt.get("local_id", pair.get("target_node_id", "")),
        "name_b": tgt.get("name", ""),
        "domain_b": tgt.get("domain", "") or "",
        "desc_b": tgt.get("description", "") or pair.get("target_text", ""),
    }


def build_system_prompt(few_shot_examples: list[dict[str, Any]] | None = None) -> str:
    """Build the system prompt, optionally appending few-shot examples."""
    if not few_shot_examples:
        return SYSTEM_PROMPT.replace("{few_shot_block}", "")

    lines: list[str] = ["## Few-Shot Examples\n"]
    for i, ex in enumerate(few_shot_examples, 1):
        fields = _enrich_pair(ex)
        lines.append(f"### Example {i}")
        lines.append(USER_PROMPT_TEMPLATE.format(**fields))
        tier = ex["tier_label"]
        # Map tier to representative score: 0→1, 1→4, 2→7, 3→9
        score = {0: 1, 1: 4, 2: 7, 3: 9}[tier]
        reasoning = {
            0: "These controls address different security concerns with no meaningful functional overlap",
            1: "These controls share a thematic connection but address different specific security aspects",
            2: "These controls address overlapping security concerns — implementing one provides meaningful evidence toward the other",
            3: "These controls address the same functional requirement despite different wording or framing",
        }[tier]
        lines.append(
            f'Answer: {{"reasoning": "{reasoning}.", "score": {score}}}\n'
        )

    few_shot_block = "\n".join(lines) + "\n"
    return SYSTEM_PROMPT.replace("{few_shot_block}", few_shot_block)


def build_user_prompt(pair: dict[str, Any]) -> str:
    """Build the user-turn prompt from a pair dict."""
    fields = _enrich_pair(pair)
    return USER_PROMPT_TEMPLATE.format(**fields)


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
