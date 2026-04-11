"""Phase 0: Opus validation gate — rubric-based 4-tier labeling.

Scores security control pairs using Claude Opus with:
  - Detailed tier rubric definitions
  - 12 few-shot examples (3 per tier) from human_cal
  - Chain-of-thought reasoning before classification
  - Prompt caching for cost reduction

Usage:
    python scripts/v5_opus_labeler.py --split human_cal          # Validate on 150 known pairs
    python scripts/v5_opus_labeler.py --split human_test_frozen   # Opus-direct baseline
    python scripts/v5_opus_labeler.py --split all                 # Both
"""
from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import anthropic

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TIER_MAP = {"Direct": 3, "Related": 2, "Tangential": 1, "None": 0}
TIER_NAMES = {0: "UNRELATED", 1: "PARTIAL", 2: "RELATED", 3: "EQUIVALENT"}
SPLITS = {
    "human_cal": "data/splits/human_cal.jsonl",
    "human_test_frozen": "data/splits/human_test_frozen.jsonl",
}
OUT_DIR = Path("data/processed/v5_features")
MODEL = "claude-opus-4-20250514"

# Few-shot example indices in human_cal (hand-picked for clarity)
# These will be excluded from evaluation when scoring human_cal
FEWSHOT_INDICES = set()  # populated after loading

# ---------------------------------------------------------------------------
# Rubric prompt (cached across calls)
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
You are a senior cybersecurity compliance auditor helping organizations map \
controls across AI governance frameworks (NIST AI RMF, ISO 42001, EU AI Act, \
OWASP, MITRE ATLAS, CSA AI Controls Matrix, etc.). Your task is to classify \
how strongly two controls from different frameworks relate to each other.

## Important Calibration Note

These controls come from AI governance frameworks that substantially overlap. \
Many pairs WILL be related — in a typical sample, roughly 15-25% are completely \
unrelated, 15-20% are tangentially connected, 35-45% are meaningfully related, \
and 10-20% are near-equivalent. Do NOT default to UNRELATED — most pairs from \
overlapping AI governance frameworks share at least some connection.

## Classification Rubric

### EQUIVALENT (Tier 3)
Both controls address the SAME core requirement, even if worded differently \
or scoped slightly differently. An auditor mapping frameworks would link \
these as corresponding controls. Evidence gathered for one would substantially \
satisfy the other.

Key test: Would a compliance team map these controls to each other when \
building a crosswalk between frameworks? If yes → EQUIVALENT.

Examples of equivalence: Both require monitoring AI systems for risks. \
Both require transparency reporting. Both require access controls on models. \
Both require incident response procedures. The specific wording or scope \
can differ — what matters is the core requirement is the same.

### RELATED (Tier 2)
The controls address overlapping security concerns. Implementing one would \
provide meaningful (but not complete) evidence toward the other. They share \
a common security domain AND have some overlap in what they require \
organizations to do.

Key test: Would implementing Control A give you a meaningful head start \
on Control B? If yes → RELATED (even if significant work remains).

Examples: One requires adversarial testing, the other requires security \
documentation (related: testing produces documentation). One requires \
access control on models, the other on audit logs (related: same mechanism, \
different assets). One is specific, the other is a broader requirement \
that encompasses it.

### PARTIAL (Tier 1)
The controls exist in the same broad security space but address different \
specific concerns. The connection is thematic — both are about "security" \
or both about "governance" — but implementing one provides little direct \
evidence toward satisfying the other.

Key test: Is the connection only at the domain level (both about security, \
both about data, both about governance) with no overlap in specific \
mechanisms or requirements? If yes → PARTIAL.

### UNRELATED (Tier 0)
The controls address genuinely different concerns with no meaningful \
connection. One is about attack techniques and the other about privacy \
rights. One is about cryptographic key management and the other about \
content filtering.

Key test: Would a compliance expert see NO reason to consider these \
together? If yes → UNRELATED. But be conservative — if there's ANY \
reasonable connection, classify higher."""

# ---------------------------------------------------------------------------
# Few-shot examples (selected from human_cal for clarity)
# ---------------------------------------------------------------------------

def _build_fewshot_block(rows, node_map):
    """Build few-shot examples from pre-selected human_cal pairs."""
    # Hand-picked examples that clearly illustrate each tier
    # Format: (index_in_human_cal, tier, brief_reasoning)
    exemplars = [
        # UNRELATED (Tier 0) - clearly different domains
        # [28] data subject rights vs OS credential dumping
        (28, "None", "One is about end-user data subject rights (privacy), the other about OS credential dumping (attack technique). Completely different domains — privacy rights vs. adversarial credential theft."),
        # [30] IP violation prevention vs searching app repositories
        (30, "None", "One is about preventing IP violations in AI outputs (data/privacy), the other about adversaries searching application repositories (reconnaissance technique). No overlap."),
        # [13] catastrophic misuse prevention vs personal data sub-processing
        (13, "None", "One is about preventing catastrophic AI misuse (safety), the other about personal data sub-processing (data privacy). Different domains entirely."),

        # PARTIAL (Tier 1) - same broad area, different specifics
        # [4] automated interventions vs data flow documentation
        (4, "Tangential", "Both touch on safety/governance topics, but one is about automated real-time interventions while the other is about data flow documentation. Same broad governance umbrella, different mechanisms."),
        # [7] third-party testing vs general governance policy
        (7, "Tangential", "Both involve third-party evaluation and governance, but one focuses on testing out-of-scope AI outputs while the other is about general governance policy. Thematic overlap only."),
        # [9] user-facing alerts vs service management procedures
        (9, "Tangential", "Both relate to accountability/incident management, but one is about user-facing policy violation alerts while the other is about service management procedures. Same domain, different specifics."),

        # RELATED (Tier 2) - overlapping requirements, not interchangeable
        # [0] detect proprietary info vs vulnerability remediation
        (0, "Related", "Both involve implementing technical controls for detection/remediation, but one focuses on detecting proprietary information in outputs while the other on vulnerability remediation processes. Overlapping security mechanisms but different scopes."),
        # [1] adversarial robustness testing vs model documentation validation
        (1, "Related", "Both involve third-party evaluation and model documentation/validation, with overlapping requirements around testing methodology. But one is specifically about adversarial robustness while the other is about general model documentation validation."),
        # [3] restrict access to AI models vs restrict access to audit logs
        (3, "Related", "Both involve restricting access based on roles/functions, which is a shared mechanism. But one restricts access to production AI models while the other restricts access to audit logs. Related access control mechanism, different assets."),

        # EQUIVALENT (Tier 3) - functionally interchangeable
        # [17] public AI communications approval vs public transparency publishing
        (17, "Direct", "Both require public transparency/communication about AI systems — one requires approval records for public AI communications, the other requires publishing information for public transparency. Same mechanism (public disclosure), same scope."),
        # [23] monitor AI risk categories vs technical documentation with risk assessment
        (23, "Direct", "Both require monitoring AI systems across risk categories — one explicitly says 'monitor AI risk categories' while the other requires technical documentation including risk assessment. Both mandate systematic risk monitoring."),
        # [25] user intervention capabilities vs security mitigations with controls
        (25, "Direct", "Both require enabling user intervention/control capabilities for AI systems — one says 'pause, stop, redirect system behavior' and the other says 'implement security mitigations including' controls. Both mandate user override capabilities."),
    ]

    global FEWSHOT_INDICES
    FEWSHOT_INDICES = {ex[0] for ex in exemplars if ex[0] < len(rows)}

    examples_text = "\n## Few-Shot Examples\n\nHere are correctly classified examples:\n"

    for idx, tier_name, reasoning in exemplars:
        if idx >= len(rows):
            continue
        r = rows[idx]
        src = node_map.get(r.get("source_node_id", ""), {})
        tgt = node_map.get(r.get("target_node_id", ""), {})

        def _b(node, fallback):
            parts = []
            if node.get("framework"): parts.append(f"[{node['framework']}]")
            if node.get("domain"): parts.append(f"({node['domain']})")
            if node.get("name"): parts.append(node["name"])
            desc = node.get("description", "")
            if desc and desc != node.get("name", ""): parts.append(desc)
            return " ".join(parts) if parts else fallback

        text_a = _b(src, r.get("source_text", ""))
        text_b = _b(tgt, r.get("target_text", ""))
        tier_label = TIER_NAMES[TIER_MAP[tier_name]]

        examples_text += f"""
### Example — {tier_label}
Control A: {text_a}
Control B: {text_b}
Classification: {tier_label}
Reasoning: {reasoning}
"""

    return examples_text


USER_TEMPLATE = """\
Classify the relationship between these two security controls.

Control A: {text_a}
Control B: {text_b}

Think step by step:
1. What security domain does each control address?
2. Do they share the same specific mechanism or just the same broad topic?
3. Would evidence from one directly help satisfy the other?

Then provide your answer in this exact JSON format:
{{"tier": "EQUIVALENT" or "RELATED" or "PARTIAL" or "UNRELATED", "confidence": 0.0-1.0, "reasoning": "your step-by-step reasoning"}}"""

# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

_JSON_RE = re.compile(r'\{[^{}]*"tier"\s*:[^{}]*\}', re.DOTALL)
_TIER_RE = re.compile(r'\b(EQUIVALENT|RELATED|PARTIAL|UNRELATED)\b', re.IGNORECASE)
TIER_TO_INT = {"EQUIVALENT": 3, "RELATED": 2, "PARTIAL": 1, "UNRELATED": 0}


def _parse_response(raw: str) -> dict:
    # Try JSON extraction first
    m = _JSON_RE.search(raw)
    if m:
        try:
            data = json.loads(m.group())
            tier = str(data.get("tier", "")).strip().upper()
            if tier in TIER_TO_INT:
                return {
                    "tier": tier,
                    "tier_int": TIER_TO_INT[tier],
                    "confidence": max(0.0, min(1.0, float(data.get("confidence", 0.5)))),
                    "reasoning": str(data.get("reasoning", "")),
                }
        except json.JSONDecodeError:
            pass

    # Fallback: find tier keyword in text (last occurrence, closest to answer)
    matches = list(_TIER_RE.finditer(raw))
    if matches:
        tier = matches[-1].group(1).upper()
        return {
            "tier": tier,
            "tier_int": TIER_TO_INT[tier],
            "confidence": 0.5,
            "reasoning": raw[:200],
        }

    raise ValueError(f"No tier found in: {raw[:300]}")


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

async def score_pair(
    client: anthropic.AsyncAnthropic,
    text_a: str,
    text_b: str,
    system_with_examples: str,
    sem: asyncio.Semaphore,
    max_retries: int = 4,
) -> dict:
    prompt = USER_TEMPLATE.format(text_a=text_a, text_b=text_b)
    last_exc = None
    for attempt in range(max_retries):
        async with sem:
            try:
                resp = await client.messages.create(
                    model=MODEL,
                    max_tokens=512,
                    temperature=0.0 if attempt == 0 else 0.2,
                    system=[{
                        "type": "text",
                        "text": system_with_examples,
                        "cache_control": {"type": "ephemeral"},
                    }],
                    messages=[{"role": "user", "content": prompt}],
                )
                raw = resp.content[0].text
                result = _parse_response(raw)
                result["input_tokens"] = resp.usage.input_tokens
                result["output_tokens"] = resp.usage.output_tokens
                result["cache_read"] = getattr(resp.usage, "cache_read_input_tokens", 0)
                result["cache_creation"] = getattr(resp.usage, "cache_creation_input_tokens", 0)
                return result
            except anthropic.RateLimitError as e:
                last_exc = e
                await asyncio.sleep(2 ** attempt * 15)
            except (anthropic.APIStatusError, ValueError, json.JSONDecodeError) as e:
                last_exc = e
                await asyncio.sleep(2 ** attempt)
    raise RuntimeError(f"Scoring failed after {max_retries} retries") from last_exc


async def score_split(
    split_name: str,
    concurrency: int = 8,
    resume: bool = True,
) -> list[dict]:
    path = SPLITS[split_name]
    pairs = [json.loads(l) for l in open(path) if l.strip()]

    nodes = json.loads(Path("data/processed/nodes.json").read_text())
    node_map = {n["node_id"]: n for n in nodes}

    # Build system prompt with few-shot examples
    cal_rows = [json.loads(l) for l in open(SPLITS["human_cal"]) if l.strip()]
    fewshot_block = _build_fewshot_block(cal_rows, node_map)
    system_with_examples = SYSTEM_PROMPT + "\n" + fewshot_block

    # Resume support
    out_path = OUT_DIR / f"opus_labels_{split_name}.jsonl"
    done = {}
    if resume and out_path.exists():
        for line in open(out_path):
            if line.strip():
                rec = json.loads(line)
                done[rec["pair_idx"]] = rec
        print(f"  Resuming: {len(done)} pairs already scored")

    client = anthropic.AsyncAnthropic()
    sem = asyncio.Semaphore(concurrency)

    def _enrich(node, fallback):
        parts = []
        if node.get("framework"): parts.append(f"[{node['framework']}]")
        if node.get("domain"): parts.append(f"({node['domain']})")
        if node.get("name"): parts.append(node["name"])
        desc = node.get("description", "")
        if desc and desc != node.get("name", ""): parts.append(desc)
        return " ".join(parts) if parts else fallback

    async def _score_one(idx, pair):
        if idx in done:
            return done[idx]

        # Skip few-shot examples when scoring human_cal
        if split_name == "human_cal" and idx in FEWSHOT_INDICES:
            return {
                "pair_idx": idx,
                "skipped": True,
                "expert_tier": pair.get("expert_tier", ""),
                "expert_label": TIER_MAP.get(pair.get("expert_tier", ""), -1),
            }

        src = node_map.get(pair.get("source_node_id", ""), {})
        tgt = node_map.get(pair.get("target_node_id", ""), {})
        text_a = _enrich(src, pair.get("source_text", ""))
        text_b = _enrich(tgt, pair.get("target_text", ""))

        result = await score_pair(client, text_a, text_b, system_with_examples, sem)
        result["pair_idx"] = idx
        result["pair_key"] = pair.get("pair_key", "")
        result["expert_tier"] = pair.get("expert_tier", "")
        result["expert_label"] = TIER_MAP.get(pair.get("expert_tier", ""), -1)
        return result

    tasks = [_score_one(i, p) for i, p in enumerate(pairs)]
    results = [None] * len(pairs)
    t0 = time.time()
    completed = len(done)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fh = open(out_path, "a" if resume else "w")

    for coro in asyncio.as_completed(tasks):
        rec = await coro
        idx = rec["pair_idx"]
        results[idx] = rec
        if idx not in done:
            fh.write(json.dumps(rec) + "\n")
            fh.flush()
            completed += 1
            if completed % 20 == 0:
                elapsed = time.time() - t0
                rate = (completed - len(done)) / max(elapsed, 0.01)
                remaining = (len(pairs) - completed) / max(rate, 0.01)
                total_in = sum(r.get("input_tokens", 0) for r in results if r)
                total_out = sum(r.get("output_tokens", 0) for r in results if r)
                cache_read = sum(r.get("cache_read", 0) for r in results if r)
                print(
                    f"  {completed}/{len(pairs)} done "
                    f"({rate:.1f} pairs/s, ~{remaining:.0f}s left) "
                    f"tokens: {total_in:,}in/{total_out:,}out "
                    f"cache_read: {cache_read:,}"
                )

    fh.close()

    # Reload sorted
    ordered = []
    with open(out_path) as f:
        for line in f:
            if line.strip():
                ordered.append(json.loads(line))
    ordered.sort(key=lambda x: x["pair_idx"])
    with open(out_path, "w") as f:
        for rec in ordered:
            f.write(json.dumps(rec) + "\n")

    return ordered


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

def evaluate(results: list[dict], split_name: str):
    import numpy as np
    from sklearn.metrics import (
        accuracy_score, f1_score, classification_report, confusion_matrix
    )

    # Filter out skipped few-shot examples
    scored = [r for r in results if not r.get("skipped")]
    y_true = np.array([r["expert_label"] for r in scored])
    y_pred = np.array([r["tier_int"] for r in scored])
    valid = y_true >= 0
    y_true = y_true[valid]
    y_pred = y_pred[valid]

    acc = accuracy_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred, average="macro")
    f1_weighted = f1_score(y_true, y_pred, average="weighted")

    # Adjacent accuracy (off by 1 is OK for ordinal)
    adj_acc = np.mean(np.abs(y_true - y_pred) <= 1)

    print(f"\n{'='*60}")
    print(f"Opus Validation — {split_name}")
    print(f"{'='*60}")
    print(f"  Pairs scored: {len(y_true)} (excl {len(results)-len(scored)} few-shot)")
    print(f"  Tier Accuracy:     {acc:.4f} ({acc*100:.1f}%)")
    print(f"  Adjacent Accuracy: {adj_acc:.4f} ({adj_acc*100:.1f}%)")
    print(f"  Macro F1:          {f1:.4f}")
    print(f"  Weighted F1:       {f1_weighted:.4f}")

    tier_names = ["UNRELATED", "PARTIAL", "RELATED", "EQUIVALENT"]
    print(f"\n{classification_report(y_true, y_pred, target_names=tier_names, zero_division=0)}")

    cm = confusion_matrix(y_true, y_pred, labels=[0, 1, 2, 3])
    print("Confusion Matrix (rows=true, cols=predicted):")
    print(f"{'':>12} {'UNREL':>8} {'PART':>8} {'REL':>8} {'EQUIV':>8}")
    for i, row in enumerate(cm):
        print(f"  {tier_names[i]:>10} {row[0]:8d} {row[1]:8d} {row[2]:8d} {row[3]:8d}")

    # Confidence analysis
    confs = np.array([r.get("confidence", 0.5) for r in scored])
    correct = (y_true == y_pred)
    print(f"\n  Mean confidence: {confs.mean():.3f}")
    print(f"  Mean conf (correct):   {confs[correct].mean():.3f}" if correct.any() else "")
    print(f"  Mean conf (incorrect): {confs[~correct].mean():.3f}" if (~correct).any() else "")

    # Token costs
    total_in = sum(r.get("input_tokens", 0) for r in scored)
    total_out = sum(r.get("output_tokens", 0) for r in scored)
    cache_read = sum(r.get("cache_read", 0) for r in scored)
    cache_create = sum(r.get("cache_creation", 0) for r in scored)
    # Opus pricing: $15/M input, $75/M output, cache read $1.5/M, cache write $18.75/M
    cost = (total_in - cache_read - cache_create) * 15e-6 + total_out * 75e-6 + cache_read * 1.5e-6 + cache_create * 18.75e-6
    print(f"\n  Tokens: {total_in:,} in / {total_out:,} out")
    print(f"  Cache: {cache_read:,} read / {cache_create:,} created")
    print(f"  Estimated cost: ${cost:.2f}")

    # Decision gate
    print(f"\n{'='*60}")
    if split_name == "human_cal":
        if acc > 0.65:
            print(f"  GATE: PASS ({acc:.1%} > 65%) — Proceed to label all 6,728 pairs")
        elif acc > 0.55:
            print(f"  GATE: ITERATE ({acc:.1%} in 55-65%) — Refine prompt and retry")
        else:
            print(f"  GATE: FAIL ({acc:.1%} < 55%) — Opus labeling not viable")
    else:
        print(f"  Opus-direct baseline: {acc:.1%} accuracy, {f1:.4f} macro F1")
        print(f"  This is the CEILING for any trained classifier using Opus labels")
    print(f"{'='*60}")

    return {
        "split": split_name,
        "n_scored": int(len(y_true)),
        "accuracy": float(acc),
        "adjacent_accuracy": float(adj_acc),
        "macro_f1": float(f1),
        "weighted_f1": float(f1_weighted),
        "cost_usd": float(cost),
        "confusion_matrix": cm.tolist(),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", default="all", choices=["human_cal", "human_test_frozen", "all"])
    parser.add_argument("--concurrency", type=int, default=8)
    parser.add_argument("--no-resume", action="store_true")
    args = parser.parse_args()

    splits = list(SPLITS.keys()) if args.split == "all" else [args.split]
    all_metrics = {}

    for split_name in splits:
        print(f"\n--- Scoring {split_name} with Opus ---")
        results = await score_split(
            split_name,
            concurrency=args.concurrency,
            resume=not args.no_resume,
        )
        metrics = evaluate(results, split_name)
        all_metrics[split_name] = metrics

    # Save summary
    summary_path = OUT_DIR / "opus_validation_summary.json"
    with open(summary_path, "w") as f:
        json.dump(all_metrics, f, indent=2)
    print(f"\nSaved summary to {summary_path}")


if __name__ == "__main__":
    asyncio.run(main())
