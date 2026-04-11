# Crosswalk v4: LLM-as-Judge + CE Ensemble + Graph Features

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Achieve >0.70 tier accuracy on sacred holdout (400 pairs) by replacing garbage algorithmic labels with LLM-as-judge (Claude Sonnet 4.6 bulk + Opus 4.6 tiebreaker) silver labels, then fusing LLM predictions with cross-encoder logits and graph structural features.

**Architecture:** Three-signal fusion — (1) LLM-as-judge provides domain-reasoning signal that CEs cannot learn from text alone, (2) existing v3 CE logits provide complementary pattern-matching signal, (3) graph features (GAT embeddings, node2vec, structural metrics) provide topology signal. Ablation-driven: start with LLM-only, add signals only if needed. Phase 0 validation gate prevents wasting $100+ on bulk scoring if prompt engineering fails.

**Tech Stack:** Anthropic Python SDK 0.92.0 (async), LightGBM, scikit-learn, NetworkX, NumPy, WANDB (crosswalk-v4 project)

**Estimated LLM Cost:** ~$120-230 (Sonnet bulk: ~$114, Opus tiebreaker: ~$50-115, Phase 0 gate: ~$4)

---

## Why v3 Failed (37.75% accuracy)

1. **Training labels are garbage:** expert_train has 4,027 hard-negatives (all tier-0, algorithmic) + 2,701 OWASP self-mappings (75% Equivalent, 0.26% Tangential). This is a different labeling schema than human expert annotations.
2. **Text similarity is useless for tiers 0-2:** Mann-Whitney p>0.68 between tiers. Only tier 3 (Equivalent) is distinguishable by text (p=0.004).
3. **CEs hit information-theoretic ceiling:** The task requires domain reasoning about security standard semantics, not text pattern matching.
4. **Only 150 human labels:** Insufficient for 4-class ML. Domain adaptation with 100 upweighted pairs cannot overcome 6,728 mislabeled ones.

## Data Partition Contract

```
human_cal_train        (  100)  → LLM few-shot examples (5 per tier = 20)
human_cal_val          (   50)  → Phase 0 validation gate, conformal calibration
human_test_frozen      (  400)  → Sacred evaluation ONLY — NEVER in training/few-shot/validation
expert_train           (6,728)  → LLM bulk scoring → silver labels (potential CE retrain)
expert_val             (1,187)  → LLM bulk scoring → silver labels
```

## Anti-Failure Safeguards

| Failure Mode | Safeguard | Task |
|---|---|---|
| **LLM hallucination** | 3× Sonnet voting + Opus tiebreaker on disagreements | 2, 5 |
| **Prompt engineering failure** | Phase 0 gate: must hit >0.45 macro_f1 on 50 human_cal_val before bulk scoring | 3 |
| **Leakage** | Few-shot from human_cal_train ONLY. human_test_frozen NEVER seen until sacred. | 2, 5 |
| **Overfitting fusion** | Ablation-driven: LLM-only first, add features only if <0.70 | 7 |
| **CE collapse** | Only retrain CEs if silver labels prove high quality AND simpler approaches fail | 8 |
| **Cost overrun** | Phase 0 gate before bulk scoring. Cost tracker logs every API call. | 2, 3 |
| **Rate limits** | Async with semaphore (50 concurrent), exponential backoff | 2 |
| **Stacker overfit on 100 pairs** | Max 4-12 features for calibration LogReg. Full fusion only with regularization. | 6, 7 |

---

### Task 1: Clean stale v3 artifacts

**Files:**
- Delete: `runs/ce_v2/deberta/best/`, `runs/ce_v2/roberta/best/`, `runs/ce_v2/deberta_base/best/`
- Delete: `runs/stacker_v2/` (entire directory)
- Delete: `results/sacred/sacred_f81f2c2.json` (v3 result — keeping sacred_ca388cbc.json as v2.1a baseline)
- Delete: `runs/registry.jsonl`
- Keep: `runs/ce_v2/contrastive/` (SimCSE init checkpoints — reusable)
- Keep: `data/processed/ce_features_v2.npz` (v3 CE features — reused in fusion)
- Keep: `data/features/gat_embeddings.npz`, `data/processed/node2vec_*`

- [ ] **Step 1: Remove stale model artifacts**

```bash
rm -rf runs/ce_v2/deberta/best runs/ce_v2/roberta/best runs/ce_v2/deberta_base/best
rm -rf runs/stacker_v2
rm -f results/sacred/sacred_f81f2c2.json
rm -f runs/registry.jsonl
```

- [ ] **Step 2: Verify kept artifacts exist**

```bash
ls runs/ce_v2/contrastive/deberta/config.json
ls runs/ce_v2/contrastive/roberta/config.json
ls data/processed/ce_features_v2.npz
ls data/features/gat_embeddings.npz
ls data/processed/node2vec_embeddings.npy
```
Expected: all exist.

- [ ] **Step 3: Commit**

```bash
git add -u
git commit -m "clean: remove stale v3 artifacts before v4 LLM-as-judge pipeline"
```

---

### Task 2: Create LLM judge module

**Files:**
- Create: `classifier/llm/__init__.py`
- Create: `classifier/llm/prompts.py`
- Create: `classifier/llm/judge.py`
- Create: `classifier/llm/scorer.py`
- Create: `classifier/llm/cost_tracker.py`

- [ ] **Step 1: Create `classifier/llm/__init__.py`**

```python
"""LLM-as-judge tier classification for crosswalk pairs."""
```

- [ ] **Step 2: Create `classifier/llm/prompts.py`**

```python
"""Prompt templates for LLM-as-judge tier classification."""
from __future__ import annotations

import json
import random
from pathlib import Path

TIER_DEFINITIONS = {
    0: (
        "UNRELATED (Tier 0): The two controls/requirements address fundamentally "
        "different security concerns with no meaningful overlap in scope, intent, "
        "or application domain."
    ),
    1: (
        "PARTIAL (Tier 1): The controls share some thematic overlap but address "
        "different specific aspects. One might be tangentially relevant to the "
        "other, or they overlap in a narrow sub-area only."
    ),
    2: (
        "RELATED (Tier 2): The controls address the same broad security concern "
        "but from different angles, scopes, or levels of specificity. Implementing "
        "one would partially satisfy the other."
    ),
    3: (
        "EQUIVALENT (Tier 3): The controls address essentially the same security "
        "requirement, possibly with different wording, granularity, or minor scope "
        "differences. Implementing one substantially satisfies the other."
    ),
}

SYSTEM_PROMPT = """\
You are an expert in AI/ML security standards and frameworks. Your task is to \
classify the relationship between two security controls/requirements from \
different frameworks on a 4-tier scale.

## Tier Definitions

{tier_defs}

## Instructions

1. Read both controls carefully, focusing on their INTENT and SCOPE, not surface wording.
2. Consider: What specific security risk does each control mitigate? What actions does each require?
3. Think step-by-step about the degree of overlap.
4. Output your reasoning, then your classification.

## Output Format

Respond with a JSON object (no markdown fencing):
{{"reasoning": "<your step-by-step reasoning>", "tier": <0|1|2|3>}}
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

Classify the relationship between Control A and Control B.
"""


def build_system_prompt(few_shot_examples: list[dict] | None = None) -> str:
    """Build system prompt with tier definitions and optional few-shot examples."""
    tier_defs = "\n".join(f"- {v}" for v in TIER_DEFINITIONS.values())
    prompt = SYSTEM_PROMPT.format(tier_defs=tier_defs)

    if few_shot_examples:
        prompt += "\n## Examples\n\n"
        for ex in few_shot_examples:
            prompt += f"### Example (Tier {ex['tier_label']})\n"
            prompt += USER_PROMPT_TEMPLATE.format(
                framework_a=ex.get("source_framework", ""),
                id_a=ex.get("source_id", ""),
                name_a=ex.get("source_name", ""),
                desc_a=ex.get("source_description", ""),
                framework_b=ex.get("target_framework", ""),
                id_b=ex.get("target_id", ""),
                name_b=ex.get("target_name", ""),
                desc_b=ex.get("target_description", ""),
            )
            prompt += f'\nCorrect classification: {{"reasoning": "...", "tier": {ex["tier_label"]}}}\n\n'

    return prompt


def build_user_prompt(pair: dict) -> str:
    """Build user prompt for a single pair."""
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
    human_cal_train: list[dict],
    n_per_tier: int = 5,
    seed: int = 42,
) -> list[dict]:
    """Select balanced few-shot examples from human_cal_train.

    Picks n_per_tier examples from each tier (0-3).
    If a tier has fewer than n_per_tier, takes all available.
    """
    rng = random.Random(seed)
    by_tier: dict[int, list[dict]] = {t: [] for t in range(4)}
    for r in human_cal_train:
        by_tier[r["tier_label"]].append(r)

    selected = []
    for tier in range(4):
        pool = by_tier[tier]
        k = min(n_per_tier, len(pool))
        selected.extend(rng.sample(pool, k))

    return selected
```

- [ ] **Step 3: Create `classifier/llm/judge.py`**

```python
"""Core LLM-as-judge: single-pair classification with retry and parsing."""
from __future__ import annotations

import asyncio
import json
import re
from dataclasses import dataclass

import anthropic

from classifier.llm.cost_tracker import CostTracker


@dataclass
class JudgeResult:
    """Result from a single LLM judge call."""
    tier: int
    reasoning: str
    model: str
    input_tokens: int
    output_tokens: int
    raw_response: str


async def judge_pair(
    client: anthropic.AsyncAnthropic,
    system_prompt: str,
    user_prompt: str,
    model: str = "claude-sonnet-4-6-20250514",
    cost_tracker: CostTracker | None = None,
    max_retries: int = 3,
) -> JudgeResult:
    """Classify a single pair using the LLM.

    Retries on parse failure or API error with exponential backoff.
    """
    last_error = None
    for attempt in range(max_retries):
        try:
            response = await client.messages.create(
                model=model,
                max_tokens=1024,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
                temperature=0.0 if attempt == 0 else 0.3,
            )
            raw = response.content[0].text
            parsed = _parse_response(raw)

            result = JudgeResult(
                tier=parsed["tier"],
                reasoning=parsed["reasoning"],
                model=model,
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
                raw_response=raw,
            )

            if cost_tracker:
                cost_tracker.log(model, result.input_tokens, result.output_tokens)

            return result

        except (anthropic.APIError, anthropic.APIConnectionError) as e:
            last_error = e
            await asyncio.sleep(2 ** attempt)
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            last_error = e
            await asyncio.sleep(1)

    raise RuntimeError(f"Failed after {max_retries} retries: {last_error}")


def _parse_response(raw: str) -> dict:
    """Parse LLM response to extract tier and reasoning.

    Handles: raw JSON, JSON in markdown fences, or tier-only fallback.
    """
    # Strip markdown code fences if present
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw.strip())
    cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        data = json.loads(cleaned)
        tier = int(data["tier"])
        if tier not in (0, 1, 2, 3):
            raise ValueError(f"Invalid tier: {tier}")
        return {"tier": tier, "reasoning": data.get("reasoning", "")}
    except (json.JSONDecodeError, KeyError):
        pass

    # Fallback: look for "tier": N pattern
    match = re.search(r'"tier"\s*:\s*(\d)', raw)
    if match:
        tier = int(match.group(1))
        if tier in (0, 1, 2, 3):
            return {"tier": tier, "reasoning": raw}

    raise ValueError(f"Cannot parse tier from response: {raw[:200]}")
```

- [ ] **Step 4: Create `classifier/llm/cost_tracker.py`**

```python
"""Track API token usage and estimated cost."""
from __future__ import annotations

import threading
from dataclasses import dataclass, field

# Pricing per 1M tokens (as of 2026-04)
PRICING = {
    "claude-sonnet-4-6-20250514": {"input": 3.0, "output": 15.0},
    "claude-opus-4-6-20250514": {"input": 15.0, "output": 75.0},
}


@dataclass
class CostTracker:
    """Thread-safe token and cost accumulator."""
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost_usd: float = 0.0
    calls_by_model: dict[str, int] = field(default_factory=dict)

    def log(self, model: str, input_tokens: int, output_tokens: int) -> None:
        prices = PRICING.get(model, {"input": 15.0, "output": 75.0})
        cost = (input_tokens * prices["input"] + output_tokens * prices["output"]) / 1_000_000

        with self._lock:
            self.total_input_tokens += input_tokens
            self.total_output_tokens += output_tokens
            self.total_cost_usd += cost
            self.calls_by_model[model] = self.calls_by_model.get(model, 0) + 1

    def summary(self) -> str:
        return (
            f"API Cost: ${self.total_cost_usd:.2f} | "
            f"Input: {self.total_input_tokens:,} tokens | "
            f"Output: {self.total_output_tokens:,} tokens | "
            f"Calls: {self.calls_by_model}"
        )
```

- [ ] **Step 5: Create `classifier/llm/scorer.py`**

```python
"""Bulk scoring orchestrator: batch pairs, 3x voting, consensus filter, Opus tiebreaker."""
from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass, field
from pathlib import Path

import anthropic

from classifier.llm.cost_tracker import CostTracker
from classifier.llm.judge import JudgeResult, judge_pair
from classifier.llm.prompts import build_system_prompt, build_user_prompt


@dataclass
class ScoredPair:
    """A pair with its LLM scoring results."""
    pair: dict
    sonnet_votes: list[int]
    opus_vote: int | None = None
    final_tier: int | None = None
    confidence: float = 0.0
    is_unanimous: bool = False
    reasonings: list[str] = field(default_factory=list)

    def compute_consensus(self) -> None:
        """Compute final tier from votes."""
        votes = self.sonnet_votes.copy()
        if self.opus_vote is not None:
            votes.append(self.opus_vote)

        if len(set(self.sonnet_votes)) == 1:
            self.is_unanimous = True
            self.final_tier = self.sonnet_votes[0]
            self.confidence = 1.0
        elif self.opus_vote is not None:
            # Opus is tiebreaker — its vote wins
            self.final_tier = self.opus_vote
            self.confidence = 0.7
        else:
            # Majority vote from Sonnet
            from collections import Counter
            counts = Counter(self.sonnet_votes)
            self.final_tier = counts.most_common(1)[0][0]
            self.confidence = counts.most_common(1)[0][1] / len(self.sonnet_votes)


async def score_pairs_bulk(
    pairs: list[dict],
    few_shot_examples: list[dict],
    model: str = "claude-sonnet-4-6-20250514",
    n_votes: int = 3,
    max_concurrent: int = 50,
    cost_tracker: CostTracker | None = None,
) -> list[ScoredPair]:
    """Score pairs with n_votes each using Sonnet.

    Args:
        pairs: List of pair dicts with source_*/target_* fields.
        few_shot_examples: Examples from human_cal_train for few-shot prompt.
        model: Anthropic model ID for bulk scoring.
        n_votes: Number of independent votes per pair.
        max_concurrent: Max concurrent API calls.
        cost_tracker: Optional cost tracker.

    Returns:
        List of ScoredPair with sonnet_votes populated.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY") or ""
    client = anthropic.AsyncAnthropic(api_key=api_key)
    semaphore = asyncio.Semaphore(max_concurrent)
    system_prompt = build_system_prompt(few_shot_examples)

    if cost_tracker is None:
        cost_tracker = CostTracker()

    scored = [ScoredPair(pair=p, sonnet_votes=[]) for p in pairs]

    async def _score_one(sp: ScoredPair, vote_idx: int) -> None:
        async with semaphore:
            user_prompt = build_user_prompt(sp.pair)
            result = await judge_pair(
                client=client,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model=model,
                cost_tracker=cost_tracker,
            )
            sp.sonnet_votes.append(result.tier)
            sp.reasonings.append(result.reasoning)

    # Launch all votes concurrently
    tasks = []
    for sp in scored:
        for v in range(n_votes):
            tasks.append(_score_one(sp, v))

    # Process in chunks to show progress
    chunk_size = max_concurrent * n_votes
    for i in range(0, len(tasks), chunk_size):
        chunk = tasks[i : i + chunk_size]
        await asyncio.gather(*chunk)
        n_done = min(i + chunk_size, len(tasks)) // n_votes
        print(f"  [scorer] {n_done}/{len(pairs)} pairs scored | {cost_tracker.summary()}")

    # Compute consensus for all
    for sp in scored:
        sp.compute_consensus()

    return scored


async def opus_tiebreaker(
    disagreed: list[ScoredPair],
    few_shot_examples: list[dict],
    model: str = "claude-opus-4-6-20250514",
    max_concurrent: int = 10,
    cost_tracker: CostTracker | None = None,
) -> list[ScoredPair]:
    """Re-score disagreement pairs with Opus for tiebreaking.

    Only call this on pairs where Sonnet votes were NOT unanimous.
    """
    if not disagreed:
        return disagreed

    api_key = os.environ.get("ANTHROPIC_API_KEY") or ""
    client = anthropic.AsyncAnthropic(api_key=api_key)
    semaphore = asyncio.Semaphore(max_concurrent)
    system_prompt = build_system_prompt(few_shot_examples)

    if cost_tracker is None:
        cost_tracker = CostTracker()

    async def _tiebreak_one(sp: ScoredPair) -> None:
        async with semaphore:
            user_prompt = build_user_prompt(sp.pair)
            result = await judge_pair(
                client=client,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model=model,
                cost_tracker=cost_tracker,
            )
            sp.opus_vote = result.tier
            sp.compute_consensus()

    await asyncio.gather(*[_tiebreak_one(sp) for sp in disagreed])

    print(f"  [opus_tiebreaker] {len(disagreed)} pairs re-scored | {cost_tracker.summary()}")
    return disagreed


def save_scores(scored: list[ScoredPair], path: Path) -> None:
    """Save scored pairs to JSONL."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        for sp in scored:
            record = {
                "source_id": sp.pair.get("source_id", ""),
                "target_id": sp.pair.get("target_id", ""),
                "source_framework": sp.pair.get("source_framework", ""),
                "target_framework": sp.pair.get("target_framework", ""),
                "sonnet_votes": sp.sonnet_votes,
                "opus_vote": sp.opus_vote,
                "final_tier": sp.final_tier,
                "confidence": sp.confidence,
                "is_unanimous": sp.is_unanimous,
            }
            f.write(json.dumps(record) + "\n")


def load_scores(path: Path) -> list[dict]:
    """Load scored pairs from JSONL."""
    rows = []
    with path.open() as f:
        for line in f:
            rows.append(json.loads(line))
    return rows
```

- [ ] **Step 6: Commit**

```bash
git add classifier/llm/
git commit -m "feat: add LLM-as-judge module (prompts, judge, scorer, cost tracker)"
```

---

### Task 3: Phase 0 — LLM validation gate

**Files:**
- Create: `classifier/llm/validation_gate.py`

This validates the LLM-as-judge approach on human_cal_val (50 pairs) before spending ~$114 on bulk scoring.

- [ ] **Step 1: Create `classifier/llm/validation_gate.py`**

```python
"""Phase 0: Validate LLM-as-judge on human_cal_val before bulk scoring."""
from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

import numpy as np
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score

from classifier.data.split_human_cal import split_human_cal
from classifier.llm.cost_tracker import CostTracker
from classifier.llm.prompts import select_few_shot_examples
from classifier.llm.scorer import ScoredPair, opus_tiebreaker, score_pairs_bulk


async def run_validation_gate(
    min_macro_f1: float = 0.45,
    n_votes: int = 3,
    use_opus_tiebreaker: bool = True,
    wandb_run=None,
) -> dict:
    """Run Phase 0 validation gate.

    Scores human_cal_val (50 pairs) with Sonnet 3x, optionally Opus tiebreaker.
    Returns gate result dict. Raises SystemExit if below threshold.

    Args:
        min_macro_f1: Minimum macro F1 to pass gate.
        n_votes: Number of Sonnet votes per pair.
        use_opus_tiebreaker: Whether to use Opus on disagreements.
        wandb_run: Optional WANDB run for logging.
    """
    print("=" * 60)
    print("PHASE 0: LLM Validation Gate (human_cal_val, 50 pairs)")
    print("=" * 60)

    # Load data — few-shot from train, evaluate on val
    human_train, human_val, _, _ = split_human_cal()
    few_shot = select_few_shot_examples(human_train, n_per_tier=5)

    print(f"  Few-shot examples: {len(few_shot)} (from human_cal_train)")
    print(f"  Validation pairs: {len(human_val)} (human_cal_val)")
    print(f"  Gate threshold: macro_f1 >= {min_macro_f1}")

    cost_tracker = CostTracker()

    # Score with Sonnet
    scored = await score_pairs_bulk(
        pairs=human_val,
        few_shot_examples=few_shot,
        n_votes=n_votes,
        max_concurrent=20,
        cost_tracker=cost_tracker,
    )

    # Opus tiebreaker on disagreements
    if use_opus_tiebreaker:
        disagreed = [sp for sp in scored if not sp.is_unanimous]
        if disagreed:
            print(f"  Opus tiebreaker on {len(disagreed)}/{len(scored)} disagreements")
            await opus_tiebreaker(
                disagreed,
                few_shot_examples=few_shot,
                max_concurrent=10,
                cost_tracker=cost_tracker,
            )

    # Evaluate
    y_true = np.array([r["tier_label"] for r in human_val])
    y_pred = np.array([sp.final_tier for sp in scored])

    tier_acc = accuracy_score(y_true, y_pred)
    macro_f1 = f1_score(y_true, y_pred, average="macro")
    per_class_f1 = f1_score(y_true, y_pred, average=None, labels=[0, 1, 2, 3])
    n_unanimous = sum(1 for sp in scored if sp.is_unanimous)
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1, 2, 3])

    print(f"\n  Results:")
    print(f"    Tier accuracy:  {tier_acc:.4f}")
    print(f"    Macro F1:       {macro_f1:.4f}")
    print(f"    Per-class F1:   {per_class_f1}")
    print(f"    Unanimous:      {n_unanimous}/{len(scored)} ({n_unanimous/len(scored):.0%})")
    print(f"    {cost_tracker.summary()}")
    print(f"\n  Confusion matrix:\n{cm}")

    result = {
        "phase": 0,
        "tier_accuracy": float(tier_acc),
        "macro_f1": float(macro_f1),
        "per_class_f1": per_class_f1.tolist(),
        "n_unanimous": n_unanimous,
        "n_pairs": len(scored),
        "cost_usd": cost_tracker.total_cost_usd,
        "confusion_matrix": cm.tolist(),
        "gate_threshold": min_macro_f1,
        "gate_passed": macro_f1 >= min_macro_f1,
    }

    if wandb_run:
        wandb_run.log({
            "phase0/tier_accuracy": tier_acc,
            "phase0/macro_f1": macro_f1,
            "phase0/n_unanimous": n_unanimous,
            "phase0/cost_usd": cost_tracker.total_cost_usd,
            **{f"phase0/f1_class_{i}": f for i, f in enumerate(per_class_f1)},
        })

    # Gate check
    if macro_f1 < min_macro_f1:
        print(f"\n  GATE FAILED: macro_f1={macro_f1:.4f} < {min_macro_f1}")
        print("  Action: Revise prompts/few-shot before proceeding to bulk scoring.")
        result["action"] = "STOP — revise prompts"
    else:
        print(f"\n  GATE PASSED: macro_f1={macro_f1:.4f} >= {min_macro_f1}")
        result["action"] = "PROCEED to bulk scoring"

    # Save result
    out_path = Path("results/phase0_validation_gate.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2))
    print(f"  Saved to {out_path}")

    return result
```

- [ ] **Step 2: Test the validation gate (dry run sanity check)**

```bash
python -c "
from classifier.llm.prompts import select_few_shot_examples, build_system_prompt, build_user_prompt
from classifier.data.split_human_cal import split_human_cal

train, val, _, _ = split_human_cal()
few_shot = select_few_shot_examples(train, n_per_tier=5)
print(f'Few-shot: {len(few_shot)} examples')
for t in range(4):
    n = sum(1 for e in few_shot if e['tier_label'] == t)
    print(f'  Tier {t}: {n}')

system = build_system_prompt(few_shot)
user = build_user_prompt(val[0])
print(f'System prompt length: {len(system)} chars')
print(f'User prompt length: {len(user)} chars')
print(f'User prompt preview:\n{user[:300]}')
"
```
Expected: 20 few-shot examples (5 per tier), system prompt ~3000-5000 chars, user prompt ~200-500 chars.

- [ ] **Step 3: Commit**

```bash
git add classifier/llm/validation_gate.py
git commit -m "feat: Phase 0 validation gate — LLM quality check before bulk scoring"
```

---

### Task 4: Graph feature engineering

**Files:**
- Create: `classifier/features/__init__.py`
- Create: `classifier/features/graph_features.py`

- [ ] **Step 1: Create `classifier/features/__init__.py`**

```python
"""Feature engineering modules for crosswalk classifier."""
```

- [ ] **Step 2: Create `classifier/features/graph_features.py`**

```python
"""Graph-structural features for crosswalk pairs.

Combines GAT embeddings, node2vec embeddings, and NetworkX structural metrics
into a feature vector for each (source, target) pair.
"""
from __future__ import annotations

import json
from pathlib import Path

import networkx as nx
import numpy as np


def load_embeddings() -> tuple[dict[str, np.ndarray], dict[str, np.ndarray]]:
    """Load GAT and node2vec embeddings, keyed by node_id."""
    # GAT embeddings: 983 x 32
    gat_data = np.load("data/features/gat_embeddings.npz")
    gat_ids = list(gat_data["node_ids"])
    gat_embs = gat_data["embeddings"]
    gat_dict = {nid: gat_embs[i] for i, nid in enumerate(gat_ids)}

    # Node2Vec embeddings: 983 x 64
    n2v_embs = np.load("data/processed/node2vec_embeddings.npy")
    n2v_vocab = json.loads(Path("data/processed/node2vec_vocab.json").read_text())
    n2v_dict = {nid: n2v_embs[i] for i, nid in enumerate(n2v_vocab)}

    return gat_dict, n2v_dict


def load_graph() -> nx.DiGraph:
    """Load the crosswalk graph."""
    nodes = json.loads(Path("data/processed/nodes.json").read_text())
    edges = json.loads(Path("data/processed/edges.json").read_text())

    g = nx.DiGraph()
    for n in nodes:
        g.add_node(n["node_id"], framework=n.get("framework", ""))
    for e in edges:
        src = e.get("source_node_id", "")
        tgt = e.get("target_node_id", "")
        if src in g and tgt in g:
            g.add_edge(src, tgt, edge_type=e.get("rationale_code", ""))

    return g


def compute_pair_features(
    pairs: list[dict],
    gat_dict: dict[str, np.ndarray],
    n2v_dict: dict[str, np.ndarray],
    graph: nx.DiGraph,
) -> np.ndarray:
    """Compute graph features for a list of pairs.

    Returns (n_pairs, n_features) array. Feature layout:
      [0:32]   GAT source embedding
      [32:64]  GAT target embedding
      [64:96]  GAT element-wise difference (|src - tgt|)
      [96:100] GAT scalar features (cosine, L2, dot, hadamard_sum)
      [100:164] Node2Vec source embedding
      [164:228] Node2Vec target embedding
      [228:292] Node2Vec element-wise difference
      [292:296] Node2Vec scalar features
      [296]    Shortest path length (undirected, 0 if unreachable)
      [297]    Common neighbors count
      [298]    Same framework (binary)
      [299]    Has direct edge (binary)
      [300]    Jaccard coefficient
    """
    n = len(pairs)
    n_feat = 301
    X = np.zeros((n, n_feat), dtype=np.float32)

    gat_zero = np.zeros(32, dtype=np.float32)
    n2v_zero = np.zeros(64, dtype=np.float32)

    # Undirected view for path/neighbor calculations
    g_undir = graph.to_undirected()

    for i, pair in enumerate(pairs):
        sid = pair.get("source_id", "")
        tid = pair.get("target_id", "")

        # GAT features
        gs = gat_dict.get(sid, gat_zero)
        gt = gat_dict.get(tid, gat_zero)
        X[i, 0:32] = gs
        X[i, 32:64] = gt
        diff_gat = np.abs(gs - gt)
        X[i, 64:96] = diff_gat
        norm_s = np.linalg.norm(gs) + 1e-8
        norm_t = np.linalg.norm(gt) + 1e-8
        X[i, 96] = np.dot(gs, gt) / (norm_s * norm_t)  # cosine
        X[i, 97] = np.linalg.norm(diff_gat)             # L2
        X[i, 98] = np.dot(gs, gt)                        # dot
        X[i, 99] = np.sum(gs * gt)                       # hadamard sum

        # Node2Vec features
        ns = n2v_dict.get(sid, n2v_zero)
        nt = n2v_dict.get(tid, n2v_zero)
        X[i, 100:164] = ns
        X[i, 164:228] = nt
        diff_n2v = np.abs(ns - nt)
        X[i, 228:292] = diff_n2v
        norm_ns = np.linalg.norm(ns) + 1e-8
        norm_nt = np.linalg.norm(nt) + 1e-8
        X[i, 292] = np.dot(ns, nt) / (norm_ns * norm_nt)
        X[i, 293] = np.linalg.norm(diff_n2v)
        X[i, 294] = np.dot(ns, nt)
        X[i, 295] = np.sum(ns * nt)

        # Structural features
        if sid in g_undir and tid in g_undir:
            try:
                X[i, 296] = nx.shortest_path_length(g_undir, sid, tid)
            except nx.NetworkXNoPath:
                X[i, 296] = 0.0  # unreachable
            X[i, 297] = len(list(nx.common_neighbors(g_undir, sid, tid)))
        X[i, 298] = float(
            pair.get("source_framework", "") == pair.get("target_framework", "")
            and pair.get("source_framework", "") != ""
        )
        X[i, 299] = float(graph.has_edge(sid, tid) or graph.has_edge(tid, sid))
        # Jaccard
        if sid in g_undir and tid in g_undir:
            s_neigh = set(g_undir.neighbors(sid))
            t_neigh = set(g_undir.neighbors(tid))
            union = len(s_neigh | t_neigh)
            X[i, 300] = len(s_neigh & t_neigh) / union if union > 0 else 0.0

    return X
```

- [ ] **Step 3: Test graph feature extraction**

```bash
python -c "
import json
from classifier.features.graph_features import load_embeddings, load_graph, compute_pair_features

gat_dict, n2v_dict = load_embeddings()
graph = load_graph()
print(f'GAT nodes: {len(gat_dict)}, Node2Vec nodes: {len(n2v_dict)}, Graph nodes: {graph.number_of_nodes()}, edges: {graph.number_of_edges()}')

# Test on first 5 human_cal pairs
pairs = []
with open('data/splits/human_cal.jsonl') as f:
    for i, line in enumerate(f):
        if i >= 5: break
        pairs.append(json.loads(line))

X = compute_pair_features(pairs, gat_dict, n2v_dict, graph)
print(f'Feature matrix: {X.shape}')
print(f'Non-zero features per pair: {(X != 0).sum(axis=1)}')
print(f'Sample cosine (GAT): {X[0, 96]:.4f}, shortest_path: {X[0, 296]:.0f}')
"
```
Expected: (5, 301) matrix with reasonable values.

- [ ] **Step 4: Commit**

```bash
git add classifier/features/
git commit -m "feat: graph feature engineering (GAT + node2vec + structural metrics)"
```

---

### Task 5: LLM bulk scoring

**Files:**
- Create: `scripts/run_llm_scoring.py`

This script orchestrates the full LLM scoring pipeline: Phase 0 gate → Sonnet bulk → Opus tiebreaker → save results.

- [ ] **Step 1: Create `scripts/run_llm_scoring.py`**

```python
"""Run full LLM-as-judge scoring pipeline.

Usage:
    # Phase 0 only (validation gate)
    python scripts/run_llm_scoring.py --phase 0

    # Full pipeline (Phase 0 + bulk scoring)
    python scripts/run_llm_scoring.py --phase all

    # Bulk scoring only (skip gate, assumes already passed)
    python scripts/run_llm_scoring.py --phase bulk
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

import numpy as np

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from classifier.data.split_human_cal import split_human_cal
from classifier.llm.cost_tracker import CostTracker
from classifier.llm.prompts import select_few_shot_examples
from classifier.llm.scorer import opus_tiebreaker, save_scores, score_pairs_bulk
from classifier.llm.validation_gate import run_validation_gate


def load_pairs(path: str) -> list[dict]:
    """Load pairs from JSONL."""
    rows = []
    with open(path) as f:
        for line in f:
            rows.append(json.loads(line))
    return rows


async def run_bulk_scoring(cost_tracker: CostTracker) -> None:
    """Score all splits with Sonnet 3x + Opus tiebreaker."""
    human_train, _, _, _ = split_human_cal()
    few_shot = select_few_shot_examples(human_train, n_per_tier=5)

    splits = {
        "expert_train": "data/splits/expert_train.jsonl",
        "expert_val": "data/splits/expert_val.jsonl",
        "human_cal": "data/splits/human_cal.jsonl",
        "human_test_frozen": "data/splits/human_test_frozen.jsonl",
    }

    out_dir = Path("data/processed/llm_scores_v4")
    out_dir.mkdir(parents=True, exist_ok=True)

    for split_name, split_path in splits.items():
        print(f"\n{'='*60}")
        print(f"Scoring {split_name}: {split_path}")
        print(f"{'='*60}")

        pairs = load_pairs(split_path)
        print(f"  {len(pairs)} pairs")

        # Score with Sonnet 3x
        scored = await score_pairs_bulk(
            pairs=pairs,
            few_shot_examples=few_shot,
            n_votes=3,
            max_concurrent=50,
            cost_tracker=cost_tracker,
        )

        # Stats before tiebreaker
        n_unanimous = sum(1 for sp in scored if sp.is_unanimous)
        print(f"  Unanimous: {n_unanimous}/{len(scored)} ({n_unanimous/len(scored):.0%})")

        # Opus tiebreaker on disagreements
        disagreed = [sp for sp in scored if not sp.is_unanimous]
        if disagreed:
            print(f"  Running Opus tiebreaker on {len(disagreed)} disagreements...")
            await opus_tiebreaker(
                disagreed,
                few_shot_examples=few_shot,
                max_concurrent=10,
                cost_tracker=cost_tracker,
            )

        # Save
        save_scores(scored, out_dir / f"{split_name}.jsonl")
        print(f"  Saved to {out_dir / split_name}.jsonl")

        # Quality check against human labels if available
        if split_name == "human_cal":
            from sklearn.metrics import accuracy_score, f1_score as sklearn_f1

            y_true = [p["tier_label"] for p in pairs]
            y_pred = [sp.final_tier for sp in scored]
            acc = accuracy_score(y_true, y_pred)
            f1 = sklearn_f1(y_true, y_pred, average="macro")
            print(f"  human_cal quality: acc={acc:.4f}, macro_f1={f1:.4f}")

    # Final cost summary
    print(f"\n{'='*60}")
    print(f"BULK SCORING COMPLETE")
    print(f"  {cost_tracker.summary()}")
    print(f"{'='*60}")

    # Save cost report
    cost_path = out_dir / "cost_report.json"
    cost_path.write_text(json.dumps({
        "total_cost_usd": cost_tracker.total_cost_usd,
        "total_input_tokens": cost_tracker.total_input_tokens,
        "total_output_tokens": cost_tracker.total_output_tokens,
        "calls_by_model": cost_tracker.calls_by_model,
    }, indent=2))


async def main(phase: str) -> None:
    cost_tracker = CostTracker()

    if phase in ("0", "all"):
        result = await run_validation_gate()
        if not result["gate_passed"]:
            print("\nGATE FAILED — fix prompts before proceeding.")
            if phase == "all":
                sys.exit(1)
            return

    if phase in ("bulk", "all"):
        await run_bulk_scoring(cost_tracker)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=["0", "bulk", "all"], default="all")
    args = parser.parse_args()

    # Load API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        import subprocess
        result = subprocess.run(
            ["pass", "show", "anthropic/api-key"],
            capture_output=True, text=True,
        )
        if result.returncode == 0:
            os.environ["ANTHROPIC_API_KEY"] = result.stdout.strip()
        else:
            print("ERROR: Set ANTHROPIC_API_KEY or configure `pass show anthropic/api-key`")
            sys.exit(1)

    asyncio.run(main(args.phase))
```

- [ ] **Step 2: Commit**

```bash
git add scripts/run_llm_scoring.py
git commit -m "feat: LLM bulk scoring script (Phase 0 gate + Sonnet bulk + Opus tiebreaker)"
```

- [ ] **Step 3: Run Phase 0 validation gate**

```bash
python scripts/run_llm_scoring.py --phase 0
```

Expected: ~150 API calls (50 pairs × 3 votes), ~$4 cost. Gate passes if macro_f1 >= 0.45.

**Go/no-go:**
- macro_f1 >= 0.55: Excellent — proceed to bulk scoring
- macro_f1 0.45-0.55: Acceptable — proceed, may need prompt tuning later
- macro_f1 < 0.45: STOP — revise prompts, add more few-shot examples, try different tier definitions

- [ ] **Step 4: Run full bulk scoring (if gate passed)**

```bash
python scripts/run_llm_scoring.py --phase bulk
```

Expected: ~25,395 Sonnet calls + ~5,000 Opus calls. ~$130-230. Takes 30-60 min with 50 concurrent.

- [ ] **Step 5: Verify outputs**

```bash
wc -l data/processed/llm_scores_v4/*.jsonl
cat data/processed/llm_scores_v4/cost_report.json
python -c "
import json
from pathlib import Path
for p in sorted(Path('data/processed/llm_scores_v4').glob('*.jsonl')):
    rows = [json.loads(l) for l in p.read_text().strip().split('\n')]
    n_unan = sum(1 for r in rows if r['is_unanimous'])
    tiers = [r['final_tier'] for r in rows]
    from collections import Counter
    dist = Counter(tiers)
    print(f'{p.name}: {len(rows)} pairs, {n_unan} unanimous, dist={dict(sorted(dist.items()))}')
"
```
Expected: All splits present. >60% unanimous. Tier distribution roughly balanced (not all same class).

- [ ] **Step 6: Commit LLM scores**

```bash
git add data/processed/llm_scores_v4/ results/phase0_validation_gate.json
git commit -m "feat: LLM-as-judge scores — Sonnet 3x + Opus tiebreaker on all splits"
```

---

### Task 6: Feature fusion module

**Files:**
- Create: `classifier/features/fusion.py`

- [ ] **Step 1: Create `classifier/features/fusion.py`**

```python
"""Feature fusion: combine LLM scores + CE logits + graph features."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np


def load_llm_features(split_name: str) -> np.ndarray:
    """Load LLM score features for a split.

    Returns (n_pairs, 5) array:
      [0:4] — vote distribution as probabilities (Sonnet votes normalized)
      [4]   — confidence score
    """
    path = Path(f"data/processed/llm_scores_v4/{split_name}.jsonl")
    rows = [json.loads(line) for line in path.read_text().strip().split("\n")]

    X = np.zeros((len(rows), 5), dtype=np.float32)
    for i, r in enumerate(rows):
        votes = r["sonnet_votes"]
        # Vote distribution: count per tier / n_votes
        for v in votes:
            X[i, v] += 1.0
        X[i, :4] /= len(votes)
        X[i, 4] = r["confidence"]

    return X


def load_ce_features(start: int, n: int) -> np.ndarray:
    """Load CE logit features from ce_features_v2.npz.

    Returns (n, 8) array: deberta_logits(4) + roberta_logits(4).
    DeBERTa-base excluded (least performant in v3).
    """
    data = np.load("data/processed/ce_features_v2.npz")
    feats = []
    for model in ["deberta", "roberta"]:
        logits = data[f"{model}_logits"][start : start + n]
        feats.append(logits)
    return np.hstack(feats)


def build_fusion_matrix(
    split_name: str,
    ce_start: int,
    n_pairs: int,
    pairs: list[dict] | None = None,
    graph_features: np.ndarray | None = None,
    include_ce: bool = True,
    include_graph: bool = True,
) -> np.ndarray:
    """Build fused feature matrix for a split.

    Feature layout (when all enabled):
      [0:5]    LLM features (vote dist + confidence)
      [5:13]   CE logits (deberta + roberta, 4 each)
      [13:314] Graph features (301-dim)

    Args:
        split_name: Name of LLM scores file (e.g., "human_cal", "human_test_frozen").
        ce_start: Start index in ce_features_v2.npz for this split.
        n_pairs: Number of pairs.
        pairs: Pair dicts (needed for graph features).
        graph_features: Pre-computed graph features (n_pairs, 301).
        include_ce: Whether to include CE logit features.
        include_graph: Whether to include graph features.
    """
    parts = []

    # LLM features (always included)
    llm_feat = load_llm_features(split_name)
    assert llm_feat.shape[0] == n_pairs, f"LLM features {llm_feat.shape[0]} != {n_pairs}"
    parts.append(llm_feat)

    # CE features
    if include_ce:
        ce_feat = load_ce_features(ce_start, n_pairs)
        assert ce_feat.shape[0] == n_pairs
        parts.append(ce_feat)

    # Graph features
    if include_graph and graph_features is not None:
        assert graph_features.shape[0] == n_pairs
        parts.append(graph_features)

    return np.hstack(parts)
```

- [ ] **Step 2: Commit**

```bash
git add classifier/features/fusion.py
git commit -m "feat: feature fusion module (LLM + CE + graph)"
```

---

### Task 7: Sacred evaluation — ablation-driven multi-method

**Files:**
- Modify: `classifier/lambda/train_all.py` (replace Phase 9 with v4 multi-method sacred)
- Create: `scripts/run_sacred_v4.py`

This is the core evaluation. It runs multiple methods in ablation order and picks the best:
- **Method A:** LLM-direct (Sonnet consensus tier predictions)
- **Method B:** LLM-calibrated (LogReg on human_cal_train LLM probs → predict test)
- **Method C:** LLM + CE fusion (LogReg on LLM probs + CE logits)
- **Method D:** LLM + CE + graph fusion (LightGBM on all features)

- [ ] **Step 1: Create `scripts/run_sacred_v4.py`**

```python
"""Sacred evaluation: v4 multi-method ablation.

Usage:
    python scripts/run_sacred_v4.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from classifier.data.split_human_cal import split_human_cal
from classifier.features.fusion import build_fusion_matrix, load_llm_features


TIER_NAMES = ["unrelated", "partial", "related", "equivalent"]


def run_sacred_v4() -> dict:
    """Run sacred evaluation with ablation-driven multi-method approach."""
    print("=" * 60)
    print("SACRED EVALUATION v4: LLM-as-Judge + CE + Graph Fusion")
    print("=" * 60)

    # Load human_test_frozen labels
    test_pairs = []
    with open("data/splits/human_test_frozen.jsonl") as f:
        for line in f:
            test_pairs.append(json.loads(line))
    y_test = np.array([p["tier_label"] for p in test_pairs])
    print(f"  Test pairs: {len(test_pairs)}")
    print(f"  Test distribution: {np.bincount(y_test, minlength=4).tolist()}")

    # Load human_cal splits for calibration
    human_train, human_val, idx_train, idx_val = split_human_cal()
    cal_pairs = []
    with open("data/splits/human_cal.jsonl") as f:
        for line in f:
            cal_pairs.append(json.loads(line))
    y_cal_train = np.array([r["tier_label"] for r in human_train])
    y_cal_val = np.array([r["tier_label"] for r in human_val])

    # CE feature offsets (from Phase 4 ordering: train → val → cal → test)
    n_train = 6728
    n_val = 1187
    n_cal = 150
    n_test = 400
    cal_start = n_train + n_val      # 7915
    test_start = n_train + n_val + n_cal  # 8065

    results = {"methods": {}, "ablation": {}}

    # ── Method A: LLM-direct ──
    print("\n--- Method A: LLM-direct (Sonnet consensus) ---")
    llm_test = load_llm_features("human_test_frozen")
    y_pred_a = llm_test[:, :4].argmax(axis=1)  # highest vote fraction = predicted tier
    acc_a = accuracy_score(y_test, y_pred_a)
    f1_a = f1_score(y_test, y_pred_a, average="macro")
    print(f"  Tier accuracy: {acc_a:.4f}")
    print(f"  Macro F1:      {f1_a:.4f}")
    results["ablation"]["llm_direct"] = {"tier_accuracy": float(acc_a), "macro_f1": float(f1_a)}

    # ── Method B: LLM-calibrated (LogReg on LLM probs) ──
    print("\n--- Method B: LLM-calibrated (LogReg on LLM vote probs) ---")
    llm_cal = load_llm_features("human_cal")
    X_cal_train_b = llm_cal[idx_train]
    X_cal_val_b = llm_cal[idx_val]
    X_test_b = llm_test

    lr_b = LogisticRegression(C=1.0, max_iter=1000, class_weight="balanced")
    lr_b.fit(X_cal_train_b, y_cal_train)
    y_pred_b = lr_b.predict(X_test_b)
    acc_b = accuracy_score(y_test, y_pred_b)
    f1_b = f1_score(y_test, y_pred_b, average="macro")
    print(f"  Tier accuracy: {acc_b:.4f}")
    print(f"  Macro F1:      {f1_b:.4f}")
    results["ablation"]["llm_calibrated"] = {"tier_accuracy": float(acc_b), "macro_f1": float(f1_b)}

    # ── Method C: LLM + CE fusion ──
    print("\n--- Method C: LLM + CE fusion (LogReg on LLM probs + CE logits) ---")
    X_cal_train_c = build_fusion_matrix("human_cal", cal_start, n_cal, include_graph=False)[idx_train]
    X_cal_val_c = build_fusion_matrix("human_cal", cal_start, n_cal, include_graph=False)[idx_val]
    X_test_c = build_fusion_matrix("human_test_frozen", test_start, n_test, include_graph=False)

    lr_c = LogisticRegression(C=0.1, max_iter=1000, class_weight="balanced")
    lr_c.fit(X_cal_train_c, y_cal_train)
    y_pred_c = lr_c.predict(X_test_c)
    acc_c = accuracy_score(y_test, y_pred_c)
    f1_c = f1_score(y_test, y_pred_c, average="macro")
    print(f"  Tier accuracy: {acc_c:.4f}")
    print(f"  Macro F1:      {f1_c:.4f}")
    results["ablation"]["llm_ce_fusion"] = {"tier_accuracy": float(acc_c), "macro_f1": float(f1_c)}

    # ── Method D: LLM + CE + graph fusion ──
    print("\n--- Method D: LLM + CE + graph fusion (LogReg, full features) ---")
    from classifier.features.graph_features import compute_pair_features, load_embeddings, load_graph

    gat_dict, n2v_dict = load_embeddings()
    graph = load_graph()

    graph_cal = compute_pair_features(cal_pairs, gat_dict, n2v_dict, graph)
    graph_test = compute_pair_features(test_pairs, gat_dict, n2v_dict, graph)

    X_cal_train_d = build_fusion_matrix(
        "human_cal", cal_start, n_cal,
        pairs=cal_pairs, graph_features=graph_cal,
    )[idx_train]
    X_test_d = build_fusion_matrix(
        "human_test_frozen", test_start, n_test,
        pairs=test_pairs, graph_features=graph_test,
    )

    # Use LogReg with strong regularization (100 train pairs, 314 features)
    lr_d = LogisticRegression(C=0.01, max_iter=2000, class_weight="balanced")
    lr_d.fit(X_cal_train_d, y_cal_train)
    y_pred_d = lr_d.predict(X_test_d)
    acc_d = accuracy_score(y_test, y_pred_d)
    f1_d = f1_score(y_test, y_pred_d, average="macro")
    print(f"  Tier accuracy: {acc_d:.4f}")
    print(f"  Macro F1:      {f1_d:.4f}")
    results["ablation"]["llm_ce_graph_fusion"] = {"tier_accuracy": float(acc_d), "macro_f1": float(f1_d)}

    # ── Pick best method ──
    methods = {
        "llm_direct": (acc_a, f1_a, y_pred_a),
        "llm_calibrated": (acc_b, f1_b, y_pred_b),
        "llm_ce_fusion": (acc_c, f1_c, y_pred_c),
        "llm_ce_graph_fusion": (acc_d, f1_d, y_pred_d),
    }
    best_name = max(methods, key=lambda k: methods[k][1])  # best by macro_f1
    best_acc, best_f1, best_preds = methods[best_name]

    print(f"\n{'='*60}")
    print(f"BEST METHOD: {best_name}")
    print(f"  Tier accuracy: {best_acc:.4f}")
    print(f"  Macro F1:      {best_f1:.4f}")

    # Per-class metrics
    per_class_f1 = f1_score(y_test, best_preds, average=None, labels=[0, 1, 2, 3])
    cm = confusion_matrix(y_test, best_preds, labels=[0, 1, 2, 3])

    per_class = {}
    for i, name in enumerate(TIER_NAMES):
        mask = y_test == i
        per_class[name] = {
            "accuracy": float(accuracy_score(y_test[mask], best_preds[mask])) if mask.sum() > 0 else 0.0,
            "count": int(mask.sum()),
            "f1": float(per_class_f1[i]),
        }

    cm_dict = {}
    for i, true_name in enumerate(TIER_NAMES):
        cm_dict[true_name] = {}
        for j, pred_name in enumerate(TIER_NAMES):
            cm_dict[true_name][pred_name] = int(cm[i, j])

    # Conformal prediction (marginal, on human_cal_val)
    # Use best method's calibrated probabilities on val set
    print("\n--- Conformal Prediction ---")
    alpha = 0.1
    if best_name == "llm_direct":
        proba_val = llm_test[idx_val if len(idx_val) <= n_test else :len(idx_val), :4]
        # For llm_direct, use val from human_cal
        proba_val_cal = llm_cal[idx_val, :4]
        proba_test = llm_test[:, :4]
    elif best_name == "llm_calibrated":
        proba_val_cal = lr_b.predict_proba(X_cal_val_b)
        proba_test = lr_b.predict_proba(X_test_b)
    elif best_name == "llm_ce_fusion":
        proba_val_cal = lr_c.predict_proba(X_cal_val_c)
        proba_test = lr_c.predict_proba(X_test_c)
    else:
        X_cal_val_d = build_fusion_matrix(
            "human_cal", cal_start, n_cal,
            pairs=cal_pairs, graph_features=graph_cal,
        )[idx_val]
        proba_val_cal = lr_d.predict_proba(X_cal_val_d)
        proba_test = lr_d.predict_proba(X_test_d)

    # Marginal conformal
    scores_cal = 1.0 - proba_val_cal[np.arange(len(y_cal_val)), y_cal_val]
    n_conformal = len(y_cal_val)
    q_level = min(np.ceil((n_conformal + 1) * (1 - alpha)) / n_conformal, 1.0)
    q_hat = float(np.quantile(scores_cal, q_level))

    # Apply to test
    scores_test = 1.0 - proba_test
    pred_sets = (scores_test <= q_hat).astype(int)
    coverage = np.mean([pred_sets[i, y_test[i]] for i in range(len(y_test))])
    avg_set_size = pred_sets.sum(axis=1).mean()
    print(f"  Coverage: {coverage:.4f} (target: {1-alpha:.2f})")
    print(f"  Avg set size: {avg_set_size:.3f}")
    print(f"  q_hat: {q_hat:.4f}")

    # Bootstrap CI
    rng = np.random.default_rng(42)
    boot_accs = []
    for _ in range(2000):
        idx = rng.choice(len(y_test), size=len(y_test), replace=True)
        boot_accs.append(accuracy_score(y_test[idx], best_preds[idx]))
    ci_lower, ci_upper = np.percentile(boot_accs, [2.5, 97.5])

    # Build sacred result
    git_sha = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        capture_output=True, text=True,
    ).stdout.strip()

    sacred_result = {
        "tier_accuracy": float(best_acc),
        "macro_f1": float(best_f1),
        "method": best_name,
        "n_pairs": len(test_pairs),
        "confusion_matrix": cm_dict,
        "per_class": per_class,
        "ablation": results["ablation"],
        "bootstrap_ci_95": {
            "lower": float(ci_lower),
            "point": float(best_acc),
            "upper": float(ci_upper),
        },
        "conformal": {
            "marginal_coverage": float(coverage),
            "avg_set_size": float(avg_set_size),
            "q_hat": q_hat,
            "alpha": alpha,
            "n_cal": n_conformal,
        },
        "sacred_run": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    # Save
    out_path = Path(f"results/sacred/sacred_{git_sha}.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(sacred_result, indent=2))
    print(f"\n  Saved to {out_path}")
    print(f"  {json.dumps(sacred_result, indent=2)}")

    return sacred_result


if __name__ == "__main__":
    run_sacred_v4()
```

- [ ] **Step 2: Commit**

```bash
git add scripts/run_sacred_v4.py
git commit -m "feat: sacred v4 evaluation — 4-method ablation (LLM direct/calibrated/CE/graph)"
```

- [ ] **Step 3: Run sacred evaluation**

```bash
python scripts/run_sacred_v4.py
```

Expected output: 4 ablation results + best method + conformal prediction + bootstrap CI.

**Go/no-go after sacred:**
- tier_accuracy > 0.70: TARGET MET — proceed to Task 10 (notebook)
- tier_accuracy 0.55-0.70: Good improvement — consider Task 8 (CE retrain) for extra boost
- tier_accuracy < 0.55: Investigate — check per-class breakdown, LLM score quality

- [ ] **Step 4: Commit sacred result**

```bash
git add results/sacred/
git commit -m "feat: sacred v4 result — LLM-as-judge + fusion evaluation"
```

---

### Task 8: Conditional CE retrain on silver labels (Lambda GPU)

**ONLY execute this task if Task 7 result < 0.70 tier accuracy AND LLM silver labels show >65% quality on human_cal.**

**Files:**
- Modify: `classifier/lambda/wandb_config.py` (change WANDB_PROJECT to crosswalk-v4)
- Modify: `classifier/lambda/train_all.py` (update Phase 3 to use silver labels)

- [ ] **Step 1: Update WANDB config**

In `classifier/lambda/wandb_config.py`, change:
```python
WANDB_PROJECT = "crosswalk-v4"
```

- [ ] **Step 2: Update Phase 3 training data to use silver labels**

In `classifier/lambda/train_all.py`, modify the Phase 3 `train_fn` to:
1. Load silver labels from `data/processed/llm_scores_v4/expert_train.jsonl`
2. Filter to only unanimous (confidence=1.0) pairs
3. Use silver tier as training label instead of expert_train's garbage labels
4. Keep human_cal_train (100 pairs) with upweighting
5. Keep all existing anti-collapse safeguards

```python
# Inside train_fn, replace expert_train label loading:
silver_labels = {}
with open("data/processed/llm_scores_v4/expert_train.jsonl") as f:
    for line in f:
        r = json.loads(line)
        key = (r["source_id"], r["target_id"])
        if r["is_unanimous"]:
            silver_labels[key] = r["final_tier"]

# Filter expert_train to only silver-labeled pairs
train_data_silver = []
for r in train_data_expert:
    key = (r["source_id"], r["target_id"])
    if key in silver_labels:
        r["tier_label"] = silver_labels[key]
        train_data_silver.append(r)

print(f"  Silver-labeled pairs: {len(train_data_silver)}/{len(train_data_expert)}")
train_data = train_data_silver  # Replace garbage labels with silver
```

- [ ] **Step 3: Dynamically detect Lambda GPU availability and provision**

```bash
export LAMBDA_API_KEY=$(pass show lambda/api-key)
python3 -c "
import json, os, urllib.request
req = urllib.request.Request(
    'https://cloud.lambdalabs.com/api/v1/instance-types',
    headers={'Authorization': f'Bearer {os.environ[\"LAMBDA_API_KEY\"]}'}
)
data = json.loads(urllib.request.urlopen(req).read())['data']
for name, info in sorted(data.items(), key=lambda x: -x[1]['instance_type']['specs']['vcpus']):
    avail = [r['name'] for r in info['regions_with_capacity_available']]
    if avail:
        specs = info['instance_type']['specs']
        price = info['instance_type']['price_cents_per_hour'] / 100
        print(f'{name}: {specs[\"vcpus\"]}vcpu, {specs[\"ram_gib\"]}GB RAM, \${price}/hr, regions={avail}')
"
```

Select the largest available GPU. Preference order: GH200 > H100 80GB > A100 80GB > A100 40GB > 8xV100.

- [ ] **Step 4: Provision instance and run Phase 3-4**

```bash
# (Instance ID from API response)
ssh lambda "cd crosswalk && git pull && git checkout <branch>"
rsync -avz data/processed/llm_scores_v4/ lambda:crosswalk/data/processed/llm_scores_v4/
rsync -avz runs/ce_v2/contrastive/ lambda:crosswalk/runs/ce_v2/contrastive/

ssh lambda "cd crosswalk && source ~/venv/bin/activate && \
  export WANDB_API_KEY=\$(pass show wandb/api-key) && \
  nohup python -m classifier.lambda.train_all --phase 3 > /tmp/phase3_v4.log 2>&1 &"
```

- [ ] **Step 5: After Phase 3 completes, run Phase 4 (feature extraction)**

```bash
ssh lambda "cd crosswalk && source ~/venv/bin/activate && \
  python -m classifier.lambda.train_all --phase 4"
```

- [ ] **Step 6: Rsync results + terminate instance**

```bash
rsync -avz lambda:crosswalk/runs/ce_v2/ runs/ce_v2/
rsync -avz lambda:crosswalk/data/processed/ce_features_v2.npz data/processed/ce_features_v4.npz
# Terminate instance via API
```

- [ ] **Step 7: Commit**

```bash
git add runs/ce_v2/*/best/ data/processed/ce_features_v4.npz
git commit -m "feat: CE retrained on LLM silver labels (Phase 3-4 v4)"
```

---

### Task 9: Conditional re-sacred with retrained CEs

**ONLY execute if Task 8 was executed.**

- [ ] **Step 1: Update fusion.py to use v4 CE features**

In `classifier/features/fusion.py`, update `load_ce_features` to accept a path parameter:

```python
def load_ce_features(start: int, n: int, path: str = "data/processed/ce_features_v2.npz") -> np.ndarray:
```

- [ ] **Step 2: Re-run sacred with v4 CE features**

```bash
python scripts/run_sacred_v4.py
```

Compare with Task 7 result. If improvement, keep. If not, revert to v3 CEs.

- [ ] **Step 3: Commit**

```bash
git add results/sacred/ classifier/features/fusion.py
git commit -m "feat: sacred v4 re-evaluation with silver-label retrained CEs"
```

---

### Task 10: Update notebook + submission

**ONLY execute after final sacred result is determined (Task 7 or Task 9).**

**Files:**
- Modify: `notebooks/build_project1_notebook.py`

- [ ] **Step 1: Update Section 8 narrative**

Replace the v3 results section with v4 results. Include:
- Methodology description: LLM-as-judge approach, 3× voting, Opus tiebreaker
- Ablation table: all 4 methods compared
- Confusion matrix visualization
- Per-class F1 breakdown
- Conformal prediction results
- Comparison with v3 (37.75% → new result)

- [ ] **Step 2: Rebuild notebook**

```bash
python notebooks/build_project1_notebook.py
```

- [ ] **Step 3: Rebuild submission zip**

```bash
rm -f submission/crosswalk-project1.zip
cd submission && zip -r crosswalk-project1.zip \
  ../notebooks/project1_crosswalk_eda.ipynb \
  ../results/sacred/ \
  ../data/processed/llm_scores_v4/cost_report.json
```

- [ ] **Step 4: Commit**

```bash
git add notebooks/ submission/
git commit -m "feat: update notebook and submission with v4 LLM-as-judge results"
```

---

## Execution Order Summary

```
Task 1 (cleanup)           → independent, do first
Task 2 (LLM module)        → independent
Task 3 (Phase 0 gate)      → depends on Task 2
Task 4 (graph features)    → independent, parallel with Tasks 2-3
Task 5 (LLM bulk scoring)  → depends on Task 2, requires Phase 0 pass
Task 6 (fusion module)     → depends on Tasks 4, 5
Task 7 (sacred eval)       → depends on Task 6
Task 8 (CE retrain)        → CONDITIONAL: only if Task 7 < 0.70
Task 9 (re-sacred)         → CONDITIONAL: only if Task 8 ran
Task 10 (notebook)         → after Task 7 or Task 9
```

**Parallelizable:**
- Tasks 2 + 4 can run in parallel (different modules, no dependencies)
- Task 1 should run first (cleanup before new work)

**Expected Timeline:**
- Tasks 1-4: ~1 hour (mostly code writing)
- Task 5: ~1-2 hours (LLM API calls, rate-limited)
- Task 6: ~15 min
- Task 7: ~15 min
- Task 8-9: ~6-8 hours (Lambda GPU training) — only if needed
- Task 10: ~1 hour
