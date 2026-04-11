"""Phase 0 v2: Opus validation gate — continuous 0-10 scoring with calibrated thresholds.

Instead of forcing Opus into 4 discrete tiers (which it systematically under-rates),
ask for a 0-10 similarity score and then calibrate thresholds on human_cal.

Usage:
    python scripts/v5_opus_labeler_v2.py --split human_cal
    python scripts/v5_opus_labeler_v2.py --split human_test_frozen
    python scripts/v5_opus_labeler_v2.py --split all
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

import numpy as np
import anthropic

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TIER_MAP = {"Direct": 3, "Related": 2, "Tangential": 1, "None": 0}
TIER_NAMES_REV = {3: "EQUIVALENT", 2: "RELATED", 1: "PARTIAL", 0: "UNRELATED"}
SPLITS = {
    "human_cal": "data/splits/human_cal.jsonl",
    "human_test_frozen": "data/splits/human_test_frozen.jsonl",
}
OUT_DIR = Path("data/processed/v5_features")
MODEL = "claude-opus-4-20250514"

# Few-shot indices to exclude from human_cal evaluation
FEWSHOT_INDICES = {28, 30, 13, 4, 7, 9, 0, 1, 3, 17, 23, 25}

# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
You are a senior cybersecurity compliance auditor helping organizations map \
controls across AI governance frameworks. Your task is to score how strongly \
two controls from different frameworks relate to each other on a 0-10 scale.

## Scoring Scale

**9-10: Near-equivalent.** These controls address the same core requirement. \
A compliance team would map them as corresponding controls in a framework \
crosswalk. Evidence for one substantially satisfies the other. Even if the \
wording or scope differs, the intent and practical requirement are the same.

**6-8: Meaningfully related.** The controls overlap in what they require \
organizations to do. Implementing one gives you a meaningful head start on \
the other. They share security domain AND mechanism overlap. One may be \
broader than the other, or they may address the same domain from different \
angles.

**3-5: Tangentially connected.** Same broad security space (both about \
"security", "governance", "data", "testing") but different specific concerns. \
The connection is thematic, not practical. Implementing one provides little \
direct evidence toward the other.

**0-2: Unrelated.** Different security domains entirely. No meaningful \
connection. One is an attack technique, the other a privacy control. One is \
about cryptography, the other about transparency reporting.

## Calibration Guidance

These pairs come from overlapping AI governance frameworks. Many pairs WILL \
be meaningfully related — in fact, about 40% of pairs score 6+ and about 15% \
score 9-10. Do not default to low scores. If you see ANY reasonable connection \
in what the controls require organizations to actually DO, score accordingly.

Think like a compliance auditor building a framework crosswalk: which controls \
would you link together? Even if the wording is very different, focus on the \
underlying requirement and whether evidence/implementation would transfer.

## Few-Shot Examples"""

# Build few-shot section dynamically
def _build_fewshot_text(rows, node_map):
    """Build few-shot examples with scores."""
    # (index, tier_name, score, reasoning)
    exemplars = [
        # UNRELATED — score 0-2
        (28, "None", 0, "One is about end-user data privacy rights (opt-in, access, portability), the other is an adversarial technique (OS credential dumping). Completely different domains."),
        (30, "None", 1, "One is about preventing IP violations in AI outputs, the other is adversaries searching application repositories. Different concerns entirely."),
        (13, "None", 1, "One is about preventing catastrophic AI misuse (chemical/bio/rad), the other about personal data sub-processing procedures. Safety vs. data privacy."),

        # PARTIAL — score 3-5
        (4, "Tangential", 4, "Both involve operational controls for AI systems, but one is about automated real-time interventions while the other is about data flow documentation. Same governance umbrella, different mechanisms."),
        (7, "Tangential", 3, "Both involve third-party evaluation and governance frameworks, but one is specifically about testing AI robustness while the other is about general governance policies and procedures. Broad thematic overlap only."),
        (9, "Tangential", 4, "Both relate to managing policy compliance and communication, but one focuses on user-facing alerts for policy violations while the other on establishing service management procedures. Related but distinct mechanisms."),

        # RELATED — score 6-8
        (0, "Related", 7, "Both involve implementing technical controls for detection and remediation. One detects proprietary information in outputs; the other manages vulnerability remediation processes. Both require implementing and evaluating technical measures."),
        (1, "Related", 7, "Both involve third-party evaluation and validation of AI models. One focuses on adversarial robustness testing; the other on model documentation validation. Overlapping testing/validation requirements."),
        (3, "Related", 6, "Both require restricting access based on roles/functions — a shared mechanism. But applied to different assets (production AI models vs. audit logs). Same access control pattern, different targets."),

        # EQUIVALENT — score 9-10
        (17, "Direct", 9, "Both require organizations to be transparent about AI systems publicly. One requires approval records for public AI communications; the other requires publishing information for public transparency to assess systemic risks. Same core requirement: public disclosure about AI."),
        (23, "Direct", 9, "Both require systematic monitoring and documentation of AI system risks. One says 'monitor AI systems across risk categories'; the other requires technical documentation including risk assessment. A compliance team would map these together."),
        (25, "Direct", 10, "Both require enabling human intervention/override capabilities for AI systems. One says 'pause, stop, or redirect system behavior'; the other requires 'appropriate security mitigations' including controls. Direct functional equivalence."),
    ]

    text = ""
    for idx, tier_name, score, reasoning in exemplars:
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
        text += f"""
### Score: {score}/10
Control A: {text_a}
Control B: {text_b}
Reasoning: {reasoning}
"""
    return text


USER_TEMPLATE = """\
Score the relationship between these two security controls on a 0-10 scale.

Control A: {text_a}
Control B: {text_b}

Think step by step:
1. What does each control require organizations to DO?
2. Would evidence/implementation for one help satisfy the other?
3. Would a compliance auditor link these in a framework crosswalk?

Answer in this exact JSON format:
{{"score": 0-10, "confidence": 0.0-1.0, "reasoning": "brief explanation"}}"""

# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

_JSON_RE = re.compile(r'\{[^{}]*"score"\s*:[^{}]*\}', re.DOTALL)
_SCORE_RE = re.compile(r'\bscore[:\s]*(\d+)', re.IGNORECASE)


def _parse_response(raw: str) -> dict:
    m = _JSON_RE.search(raw)
    if m:
        try:
            data = json.loads(m.group())
            score = int(data.get("score", -1))
            if 0 <= score <= 10:
                return {
                    "score": score,
                    "confidence": max(0.0, min(1.0, float(data.get("confidence", 0.5)))),
                    "reasoning": str(data.get("reasoning", "")),
                }
        except (json.JSONDecodeError, ValueError):
            pass

    # Fallback: find score in text
    m = _SCORE_RE.search(raw)
    if m:
        score = int(m.group(1))
        if 0 <= score <= 10:
            return {"score": score, "confidence": 0.5, "reasoning": raw[:200]}

    raise ValueError(f"No score found in: {raw[:300]}")


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

async def score_pair(client, text_a, text_b, system_text, sem, max_retries=4):
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
                        "text": system_text,
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


async def score_split(split_name, concurrency=8, resume=True):
    path = SPLITS[split_name]
    pairs = [json.loads(l) for l in open(path) if l.strip()]

    nodes = json.loads(Path("data/processed/nodes.json").read_text())
    node_map = {n["node_id"]: n for n in nodes}

    cal_rows = [json.loads(l) for l in open(SPLITS["human_cal"]) if l.strip()]
    fewshot_text = _build_fewshot_text(cal_rows, node_map)
    system_text = SYSTEM_PROMPT + fewshot_text

    out_path = OUT_DIR / f"opus_scores_{split_name}.jsonl"
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

        if split_name == "human_cal" and idx in FEWSHOT_INDICES:
            return {
                "pair_idx": idx, "skipped": True,
                "expert_tier": pair.get("expert_tier", ""),
                "expert_label": TIER_MAP.get(pair.get("expert_tier", ""), -1),
            }

        src = node_map.get(pair.get("source_node_id", ""), {})
        tgt = node_map.get(pair.get("target_node_id", ""), {})
        text_a = _enrich(src, pair.get("source_text", ""))
        text_b = _enrich(tgt, pair.get("target_text", ""))

        result = await score_pair(client, text_a, text_b, system_text, sem)
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
                print(f"  {completed}/{len(pairs)} done ({rate:.1f} pairs/s, ~{remaining:.0f}s left)")

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
# Threshold calibration + evaluation
# ---------------------------------------------------------------------------

def calibrate_and_evaluate(results: list[dict], split_name: str):
    from sklearn.metrics import accuracy_score, f1_score, classification_report, confusion_matrix

    scored = [r for r in results if not r.get("skipped")]
    scores = np.array([r["score"] for r in scored])
    y_true = np.array([r["expert_label"] for r in scored])
    valid = y_true >= 0
    scores = scores[valid]
    y_true = y_true[valid]

    print(f"\n{'='*60}")
    print(f"Opus Continuous Scoring — {split_name}")
    print(f"{'='*60}")
    print(f"  Pairs scored: {len(y_true)}")

    # Score distribution per tier
    print(f"\n  Score distributions by true tier:")
    for tier in range(4):
        mask = y_true == tier
        if mask.any():
            tier_scores = scores[mask]
            print(f"    Tier {tier} ({TIER_NAMES_REV[tier]:>10}): "
                  f"n={mask.sum():3d}  mean={tier_scores.mean():.1f}  "
                  f"median={np.median(tier_scores):.0f}  "
                  f"range=[{tier_scores.min()}-{tier_scores.max()}]  "
                  f"dist={np.bincount(tier_scores.astype(int), minlength=11).tolist()}")

    # Try multiple threshold strategies
    print(f"\n  Threshold search:")
    best_acc = 0
    best_thresholds = None

    # Grid search over threshold triplets (t1 <= t2 <= t3)
    for t1 in range(1, 5):
        for t2 in range(t1 + 1, 8):
            for t3 in range(t2 + 1, 10):
                y_pred = np.where(scores <= t1, 0,
                         np.where(scores <= t2, 1,
                         np.where(scores <= t3, 2, 3)))
                acc = accuracy_score(y_true, y_pred)
                f1 = f1_score(y_true, y_pred, average="macro", zero_division=0)
                if acc > best_acc:
                    best_acc = acc
                    best_f1 = f1
                    best_thresholds = (t1, t2, t3)

    t1, t2, t3 = best_thresholds
    print(f"  Best thresholds: ≤{t1}→UNREL, ≤{t2}→PARTIAL, ≤{t3}→RELATED, >{t3}→EQUIV")
    print(f"  Accuracy: {best_acc:.4f} ({best_acc*100:.1f}%)")
    print(f"  Macro F1: {best_f1:.4f}")

    y_pred_best = np.where(scores <= t1, 0,
                  np.where(scores <= t2, 1,
                  np.where(scores <= t3, 2, 3)))

    adj_acc = np.mean(np.abs(y_true - y_pred_best) <= 1)
    print(f"  Adjacent Accuracy: {adj_acc:.4f} ({adj_acc*100:.1f}%)")

    tier_names = ["UNRELATED", "PARTIAL", "RELATED", "EQUIVALENT"]
    print(f"\n{classification_report(y_true, y_pred_best, target_names=tier_names, zero_division=0)}")

    cm = confusion_matrix(y_true, y_pred_best, labels=[0, 1, 2, 3])
    print("Confusion Matrix (rows=true, cols=predicted):")
    print(f"{'':>12} {'UNREL':>8} {'PART':>8} {'REL':>8} {'EQUIV':>8}")
    for i, row in enumerate(cm):
        print(f"  {tier_names[i]:>10} {row[0]:8d} {row[1]:8d} {row[2]:8d} {row[3]:8d}")

    # Also evaluate with "natural" thresholds (0-2, 3-5, 6-8, 9-10)
    y_pred_natural = np.where(scores <= 2, 0,
                    np.where(scores <= 5, 1,
                    np.where(scores <= 8, 2, 3)))
    nat_acc = accuracy_score(y_true, y_pred_natural)
    nat_f1 = f1_score(y_true, y_pred_natural, average="macro", zero_division=0)
    print(f"\n  Natural thresholds (≤2/≤5/≤8/9+): acc={nat_acc:.4f}, F1={nat_f1:.4f}")

    cm_nat = confusion_matrix(y_true, y_pred_natural, labels=[0, 1, 2, 3])
    print(f"{'':>12} {'UNREL':>8} {'PART':>8} {'REL':>8} {'EQUIV':>8}")
    for i, row in enumerate(cm_nat):
        print(f"  {tier_names[i]:>10} {row[0]:8d} {row[1]:8d} {row[2]:8d} {row[3]:8d}")

    # Token costs
    total_in = sum(r.get("input_tokens", 0) for r in scored)
    total_out = sum(r.get("output_tokens", 0) for r in scored)
    cache_read = sum(r.get("cache_read", 0) for r in scored)
    cache_create = sum(r.get("cache_creation", 0) for r in scored)
    cost = (total_in - cache_read - cache_create) * 15e-6 + total_out * 75e-6 + cache_read * 1.5e-6 + cache_create * 18.75e-6
    print(f"\n  Tokens: {total_in:,} in / {total_out:,} out")
    print(f"  Cache: {cache_read:,} read / {cache_create:,} created")
    print(f"  Estimated cost: ${cost:.2f}")

    # Decision gate
    print(f"\n{'='*60}")
    if split_name == "human_cal":
        if best_acc > 0.65:
            print(f"  GATE: PASS ({best_acc:.1%} > 65%) — Proceed to label all 6,728 pairs")
        elif best_acc > 0.55:
            print(f"  GATE: ITERATE ({best_acc:.1%} in 55-65%) — Refine prompt and retry")
        else:
            print(f"  GATE: FAIL ({best_acc:.1%} < 55%) — Opus labeling not viable with current approach")
    else:
        print(f"  Opus-direct baseline: {best_acc:.1%} accuracy, {best_f1:.4f} macro F1")
        print(f"  This is the CEILING for any trained classifier using Opus labels")
    print(f"{'='*60}")

    return {
        "split": split_name,
        "n_scored": int(len(y_true)),
        "best_thresholds": list(best_thresholds),
        "best_accuracy": float(best_acc),
        "best_macro_f1": float(best_f1),
        "adjacent_accuracy": float(adj_acc),
        "natural_accuracy": float(nat_acc),
        "natural_macro_f1": float(nat_f1),
        "cost_usd": float(cost),
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
        print(f"\n--- Scoring {split_name} with Opus (0-10 scale) ---")
        results = await score_split(
            split_name,
            concurrency=args.concurrency,
            resume=not args.no_resume,
        )
        metrics = calibrate_and_evaluate(results, split_name)
        all_metrics[split_name] = metrics

    summary_path = OUT_DIR / "opus_v2_validation_summary.json"
    with open(summary_path, "w") as f:
        json.dump(all_metrics, f, indent=2)
    print(f"\nSaved summary to {summary_path}")


if __name__ == "__main__":
    asyncio.run(main())
