"""v5 Hierarchical Binary LLM Decomposition.

Scores security control pairs with 3 binary yes/no questions:
  Q1: "Do these controls address the same security domain?"
      No → Tier 0 (Unrelated), Yes → Q2
  Q2: "Would implementing control A provide evidence toward satisfying control B?"
      No → Tier 1 (Partial/Tangential), Yes → Q3
  Q3: "Are these controls functionally equivalent — interchangeable for audit purposes?"
      No → Tier 2 (Related), Yes → Tier 3 (Equivalent)

Binary questions are much easier for LLMs than ordinal scoring.
Each question also returns a confidence (0-1) for richer features.

Usage:
    python scripts/v5_hierarchical_llm.py [--split human_cal] [--concurrency 10]
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
SPLITS = {
    "human_cal": "data/splits/human_cal.jsonl",
    "human_test_frozen": "data/splits/human_test_frozen.jsonl",
}
OUT_DIR = Path("data/processed/v5_features")
MODEL = "claude-sonnet-4-20250514"

# ---------------------------------------------------------------------------
# Prompts — each is a binary yes/no question
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
You are a cybersecurity compliance expert evaluating relationships between \
security controls from different AI governance frameworks. Answer precisely \
in the JSON format requested. Be rigorous — "yes" means clearly yes, not \
"maybe" or "somewhat"."""

Q1_TEMPLATE = """\
Do these two security controls address the same security domain or concern?

Control A: {text_a}
Control B: {text_b}

Answer in JSON: {{"answer": "yes" or "no", "confidence": 0.0-1.0, "reasoning": "brief explanation"}}"""

Q2_TEMPLATE = """\
Given that these controls address overlapping security domains:

Control A: {text_a}
Control B: {text_b}

Would implementing Control A provide meaningful evidence toward satisfying \
Control B's requirements? (Not identical, but tangible overlap in what they \
require organizations to do.)

Answer in JSON: {{"answer": "yes" or "no", "confidence": 0.0-1.0, "reasoning": "brief explanation"}}"""

Q3_TEMPLATE = """\
Given that these controls have overlapping requirements:

Control A: {text_a}
Control B: {text_b}

Are these controls functionally equivalent — could evidence satisfying one \
be directly used to satisfy the other for audit/compliance purposes, with \
minimal additional work?

Answer in JSON: {{"answer": "yes" or "no", "confidence": 0.0-1.0, "reasoning": "brief explanation"}}"""

# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

_JSON_RE = re.compile(r"\{[^{}]*\}", re.DOTALL)


def _parse_binary(raw: str) -> dict:
    """Parse {"answer": "yes"/"no", "confidence": float, "reasoning": str}."""
    m = _JSON_RE.search(raw)
    if not m:
        raise ValueError(f"No JSON found in: {raw[:200]}")
    data = json.loads(m.group())
    answer = str(data.get("answer", "")).strip().lower()
    if answer not in ("yes", "no"):
        raise ValueError(f"Invalid answer: {answer}")
    conf = float(data.get("confidence", 0.5))
    return {
        "answer": answer,
        "yes": 1 if answer == "yes" else 0,
        "confidence": max(0.0, min(1.0, conf)),
        "reasoning": str(data.get("reasoning", "")),
    }


# ---------------------------------------------------------------------------
# Single-pair scoring
# ---------------------------------------------------------------------------

async def _ask_binary(
    client: anthropic.AsyncAnthropic,
    template: str,
    text_a: str,
    text_b: str,
    sem: asyncio.Semaphore,
    max_retries: int = 4,
) -> dict:
    """Ask one binary question with retry."""
    prompt = template.format(text_a=text_a, text_b=text_b)
    last_exc = None
    for attempt in range(max_retries):
        async with sem:
            try:
                resp = await client.messages.create(
                    model=MODEL,
                    max_tokens=256,
                    temperature=0.0 if attempt == 0 else 0.2,
                    system=SYSTEM_PROMPT,
                    messages=[{"role": "user", "content": prompt}],
                )
                raw = resp.content[0].text
                result = _parse_binary(raw)
                result["input_tokens"] = resp.usage.input_tokens
                result["output_tokens"] = resp.usage.output_tokens
                return result
            except anthropic.RateLimitError as e:
                last_exc = e
                await asyncio.sleep(2 ** attempt * 15)
            except (anthropic.APIStatusError, ValueError, json.JSONDecodeError) as e:
                last_exc = e
                await asyncio.sleep(2 ** attempt)
    raise RuntimeError(f"Binary question failed after {max_retries} retries") from last_exc


async def score_pair(
    client: anthropic.AsyncAnthropic,
    text_a: str,
    text_b: str,
    sem: asyncio.Semaphore,
) -> dict:
    """Score one pair through the 3-question hierarchy.

    Returns:
        dict with keys: tier, q1_yes, q1_conf, q2_yes, q2_conf, q3_yes, q3_conf,
                        total_input_tokens, total_output_tokens
    """
    total_in = 0
    total_out = 0

    # Q1: Same domain?
    q1 = await _ask_binary(client, Q1_TEMPLATE, text_a, text_b, sem)
    total_in += q1["input_tokens"]
    total_out += q1["output_tokens"]

    if q1["yes"] == 0:
        # Not same domain → Tier 0
        return {
            "tier": 0,
            "q1_yes": 0, "q1_conf": q1["confidence"],
            "q2_yes": 0, "q2_conf": 0.0,
            "q3_yes": 0, "q3_conf": 0.0,
            "q1_reasoning": q1["reasoning"],
            "q2_reasoning": "",
            "q3_reasoning": "",
            "total_input_tokens": total_in,
            "total_output_tokens": total_out,
        }

    # Q2: Evidence overlap?
    q2 = await _ask_binary(client, Q2_TEMPLATE, text_a, text_b, sem)
    total_in += q2["input_tokens"]
    total_out += q2["output_tokens"]

    if q2["yes"] == 0:
        # Same domain but no evidence overlap → Tier 1
        return {
            "tier": 1,
            "q1_yes": 1, "q1_conf": q1["confidence"],
            "q2_yes": 0, "q2_conf": q2["confidence"],
            "q3_yes": 0, "q3_conf": 0.0,
            "q1_reasoning": q1["reasoning"],
            "q2_reasoning": q2["reasoning"],
            "q3_reasoning": "",
            "total_input_tokens": total_in,
            "total_output_tokens": total_out,
        }

    # Q3: Functionally equivalent?
    q3 = await _ask_binary(client, Q3_TEMPLATE, text_a, text_b, sem)
    total_in += q3["input_tokens"]
    total_out += q3["output_tokens"]

    tier = 3 if q3["yes"] == 1 else 2

    return {
        "tier": tier,
        "q1_yes": 1, "q1_conf": q1["confidence"],
        "q2_yes": 1, "q2_conf": q2["confidence"],
        "q3_yes": q3["yes"], "q3_conf": q3["confidence"],
        "q1_reasoning": q1["reasoning"],
        "q2_reasoning": q2["reasoning"],
        "q3_reasoning": q3["reasoning"],
        "total_input_tokens": total_in,
        "total_output_tokens": total_out,
    }


# ---------------------------------------------------------------------------
# Batch scoring
# ---------------------------------------------------------------------------

async def score_split(
    split_name: str,
    concurrency: int = 10,
    resume: bool = True,
) -> list[dict]:
    """Score all pairs in a split file."""
    path = SPLITS[split_name]
    pairs = []
    with open(path) as f:
        for line in f:
            if line.strip():
                pairs.append(json.loads(line))

    # Load node metadata for enriched text
    nodes = json.loads(Path("data/processed/nodes.json").read_text())
    node_map = {n["node_id"]: n for n in nodes}

    # Resume support: load partial results
    out_path = OUT_DIR / f"hierarchical_{split_name}.jsonl"
    done = {}
    if resume and out_path.exists():
        with open(out_path) as f:
            for line in f:
                if line.strip():
                    rec = json.loads(line)
                    done[rec["pair_idx"]] = rec
        print(f"  Resuming: {len(done)} pairs already scored")

    client = anthropic.AsyncAnthropic()
    sem = asyncio.Semaphore(concurrency)

    async def _score_one(idx: int, pair: dict) -> dict:
        if idx in done:
            return done[idx]

        # Build enriched text
        src = node_map.get(pair.get("source_node_id", ""), {})
        tgt = node_map.get(pair.get("target_node_id", ""), {})

        def _build(node, fallback):
            parts = []
            if node.get("framework"):
                parts.append(f"[{node['framework']}]")
            if node.get("domain"):
                parts.append(f"({node['domain']})")
            if node.get("name"):
                parts.append(node["name"])
            desc = node.get("description", "")
            if desc and desc != node.get("name", ""):
                parts.append(desc)
            return " ".join(parts) if parts else fallback

        text_a = _build(src, pair.get("source_text", ""))
        text_b = _build(tgt, pair.get("target_text", ""))

        result = await score_pair(client, text_a, text_b, sem)
        result["pair_idx"] = idx
        result["expert_tier"] = pair.get("expert_tier", "")
        result["expert_label"] = TIER_MAP.get(pair.get("expert_tier", ""), -1)
        return result

    # Process with progress reporting
    tasks = [_score_one(i, p) for i, p in enumerate(pairs)]
    results = [None] * len(pairs)
    t0 = time.time()
    completed = len(done)

    # Write results incrementally
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
            if completed % 10 == 0:
                elapsed = time.time() - t0
                rate = (completed - len(done)) / max(elapsed, 0.01)
                remaining = (len(pairs) - completed) / max(rate, 0.01)
                total_in = sum(r["total_input_tokens"] for r in results if r)
                total_out = sum(r["total_output_tokens"] for r in results if r)
                print(
                    f"  {completed}/{len(pairs)} done "
                    f"({rate:.1f} pairs/s, ~{remaining:.0f}s left) "
                    f"tokens: {total_in:,}in/{total_out:,}out"
                )

    fh.close()

    # Reload in order
    ordered = []
    with open(out_path) as f:
        for line in f:
            if line.strip():
                ordered.append(json.loads(line))
    ordered.sort(key=lambda x: x["pair_idx"])
    # Rewrite sorted
    with open(out_path, "w") as f:
        for rec in ordered:
            f.write(json.dumps(rec) + "\n")

    return ordered


# ---------------------------------------------------------------------------
# Feature extraction
# ---------------------------------------------------------------------------

def extract_features(results: list[dict]) -> tuple:
    """Extract 6-dim feature vector from hierarchical results.

    Features per pair:
      [0] q1_yes (0/1)
      [1] q1_confidence (0-1)
      [2] q2_yes (0/1)
      [3] q2_confidence (0-1)
      [4] q3_yes (0/1)
      [5] q3_confidence (0-1)

    Returns (X, y_pred_tier, y_true)
    """
    import numpy as np
    X = []
    y_pred = []
    y_true = []
    for r in results:
        X.append([
            r["q1_yes"], r["q1_conf"],
            r["q2_yes"], r["q2_conf"],
            r["q3_yes"], r["q3_conf"],
        ])
        y_pred.append(r["tier"])
        y_true.append(r["expert_label"])
    return np.array(X, dtype=np.float32), np.array(y_pred), np.array(y_true)


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

def evaluate(results: list[dict], split_name: str):
    """Print classification metrics."""
    from sklearn.metrics import f1_score, accuracy_score, classification_report
    import numpy as np

    X, y_pred, y_true = extract_features(results)
    valid = y_true >= 0
    y_pred = y_pred[valid]
    y_true = y_true[valid]

    acc = accuracy_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred, average="macro")
    print(f"\n{'='*60}")
    print(f"Hierarchical Binary LLM — {split_name}")
    print(f"{'='*60}")
    print(f"  Tier Accuracy: {acc:.4f}")
    print(f"  Macro F1:      {f1:.4f}")
    print(f"\n{classification_report(y_true, y_pred, target_names=['Unrelated','Partial','Related','Equivalent'])}")

    # Token cost estimate
    total_in = sum(r["total_input_tokens"] for r in results)
    total_out = sum(r["total_output_tokens"] for r in results)
    # Sonnet 4 pricing: $3/M input, $15/M output
    cost = total_in * 3e-6 + total_out * 15e-6
    print(f"  Total tokens: {total_in:,} in / {total_out:,} out")
    print(f"  Estimated cost: ${cost:.2f}")

    return acc, f1


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", default="all", choices=["human_cal", "human_test_frozen", "all"])
    parser.add_argument("--concurrency", type=int, default=10)
    parser.add_argument("--no-resume", action="store_true")
    args = parser.parse_args()

    splits = list(SPLITS.keys()) if args.split == "all" else [args.split]

    for split_name in splits:
        print(f"\n--- Scoring {split_name} ---")
        results = await score_split(
            split_name,
            concurrency=args.concurrency,
            resume=not args.no_resume,
        )
        evaluate(results, split_name)

    # Save combined feature matrix
    import numpy as np
    all_results = []
    for split_name in ["human_cal", "human_test_frozen"]:
        path = OUT_DIR / f"hierarchical_{split_name}.jsonl"
        if path.exists():
            with open(path) as f:
                for line in f:
                    if line.strip():
                        all_results.append(json.loads(line))
    if all_results:
        X, _, _ = extract_features(all_results)
        np.savez(OUT_DIR / "hierarchical_features.npz", features=X)
        print(f"\nSaved hierarchical features: {X.shape}")


if __name__ == "__main__":
    asyncio.run(main())
