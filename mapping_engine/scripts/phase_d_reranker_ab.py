"""Phase D — BGE-reranker-v2-m3 vs ms-marco-MiniLM A/B on the 550 SME labels.

For every SME-labeled candidate we re-score the (source_description,
target_description) pair with both cross-encoders on GPU, blend each into
the existing composite at the production blend weight (0.10), and report
per-pair tier_acc under both. Decision rule: ADOPT v2-m3 per pair where
its tier_acc is non-inferior (≥ baseline - 0.01); otherwise KEEP MiniLM.
"""
from __future__ import annotations
import json
from collections import defaultdict
from pathlib import Path

import torch
import yaml
from sentence_transformers import CrossEncoder

REPO = Path(__file__).resolve().parents[2]
SHEETS = REPO / "mapping_engine/output/labeling_sheets"
OUT_JSON = REPO / "mapping_engine/output/session9_phase_d.json"
OUT_MD = REPO / "docs/session9_phase_d.md"

BLEND_W = 0.10  # production blend weight from defaults.yaml


def tier_for_score(s: float) -> str:
    if s >= 0.45:
        return "Direct"
    if s >= 0.20:
        return "Related"
    if s >= 0.10:
        return "Tangential"
    return "None"


def load_pairs():
    items = []
    for f in sorted(SHEETS.glob("*__candidates.yaml")):
        pair = f.stem.replace("__candidates", "")
        d = yaml.safe_load(f.read_text())
        for c in d["candidates"]:
            if not c.get("expert_tier"):
                continue
            items.append(
                {
                    "pair": pair,
                    "src": (c.get("source_name") or "")
                    + ". "
                    + (c.get("source_description") or ""),
                    "tgt": (c.get("target_name") or "")
                    + ". "
                    + (c.get("target_description") or ""),
                    "composite": float(c["composite_score"]),
                    "expert_tier": c["expert_tier"],
                }
            )
    return items


def score_with(model_name, items):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[phase_d] loading {model_name} on {device}")
    m = CrossEncoder(model_name, device=device)
    pairs = [(it["src"], it["tgt"]) for it in items]
    print(f"[phase_d] scoring {len(pairs)} pairs ...")
    scores = m.predict(pairs, batch_size=64, show_progress_bar=False)
    return [float(s) for s in scores]


def normalize(scores):
    """min-max normalize to [0,1]."""
    lo, hi = min(scores), max(scores)
    if hi - lo < 1e-9:
        return [0.5 for _ in scores]
    return [(s - lo) / (hi - lo) for s in scores]


def per_pair_tier_acc(items, blended_scores):
    by_pair = defaultdict(lambda: [0, 0])
    for it, sc in zip(items, blended_scores):
        pred = tier_for_score(sc)
        by_pair[it["pair"]][1] += 1
        if pred == it["expert_tier"]:
            by_pair[it["pair"]][0] += 1
    return {p: hits / n for p, (hits, n) in by_pair.items()}


def main() -> None:
    items = load_pairs()
    print(f"[phase_d] loaded {len(items)} labeled items")

    # Baseline = composite alone (production already includes ms-marco contribution
    # for S7 pairs and excludes it for the 3 S8 new pairs)
    baseline_acc = per_pair_tier_acc(items, [it["composite"] for it in items])

    minilm_raw = score_with("cross-encoder/ms-marco-MiniLM-L-6-v2", items)
    bge_raw = score_with("BAAI/bge-reranker-v2-m3", items)

    # Per-pair min-max normalize so blending is on a comparable scale
    items_by_pair = defaultdict(list)
    for i, it in enumerate(items):
        items_by_pair[it["pair"]].append(i)
    minilm_norm = [0.0] * len(items)
    bge_norm = [0.0] * len(items)
    for pair, idxs in items_by_pair.items():
        ml = normalize([minilm_raw[i] for i in idxs])
        bg = normalize([bge_raw[i] for i in idxs])
        for j, i in enumerate(idxs):
            minilm_norm[i] = ml[j]
            bge_norm[i] = bg[j]

    minilm_blend = [
        (1 - BLEND_W) * it["composite"] + BLEND_W * minilm_norm[i]
        for i, it in enumerate(items)
    ]
    bge_blend = [
        (1 - BLEND_W) * it["composite"] + BLEND_W * bge_norm[i]
        for i, it in enumerate(items)
    ]
    minilm_acc = per_pair_tier_acc(items, minilm_blend)
    bge_acc = per_pair_tier_acc(items, bge_blend)

    # Decision per pair
    decisions = {}
    for pair in baseline_acc:
        b = baseline_acc[pair]
        m = minilm_acc[pair]
        v2 = bge_acc[pair]
        # adopt v2-m3 if non-inferior to MiniLM (≥ MiniLM - 0.01)
        if v2 >= m - 0.01:
            decisions[pair] = "ADOPT_v2_m3"
        else:
            decisions[pair] = "KEEP_MiniLM"

    macro_baseline = sum(baseline_acc.values()) / len(baseline_acc)
    macro_minilm = sum(minilm_acc.values()) / len(minilm_acc)
    macro_bge = sum(bge_acc.values()) / len(bge_acc)
    n_adopt = sum(1 for v in decisions.values() if v == "ADOPT_v2_m3")

    out = {
        "blend_weight": BLEND_W,
        "n_items": len(items),
        "per_pair": {
            pair: {
                "baseline": baseline_acc[pair],
                "minilm_blend": minilm_acc[pair],
                "bge_v2_m3_blend": bge_acc[pair],
                "decision": decisions[pair],
            }
            for pair in baseline_acc
        },
        "macro": {
            "baseline": macro_baseline,
            "minilm": macro_minilm,
            "bge_v2_m3": macro_bge,
        },
        "adopt_count": n_adopt,
        "total_pairs": len(decisions),
    }
    OUT_JSON.write_text(json.dumps(out, indent=2))

    md = [
        "# Session 9 — Phase D BGE-reranker-v2-m3 vs ms-marco-MiniLM (per-pair A/B)\n",
        f"GPU scoring of {len(items)} SME-labeled candidates with both cross-"
        f"encoders, blended into the composite at production weight {BLEND_W}, "
        "evaluated by per-pair tier_acc.\n",
        "## Per-pair tier_acc\n",
        "| pair | baseline | MiniLM (blend) | BGE-v2-m3 (blend) | decision |",
        "|---|---:|---:|---:|---|",
    ]
    for pair in sorted(baseline_acc):
        md.append(
            f"| {pair} | {baseline_acc[pair]:.3f} | "
            f"{minilm_acc[pair]:.3f} | {bge_acc[pair]:.3f} | "
            f"{decisions[pair]} |"
        )
    md.append(
        f"\n**Macro**: baseline={macro_baseline:.3f} MiniLM={macro_minilm:.3f} "
        f"BGE-v2-m3={macro_bge:.3f}"
    )
    md.append(
        f"\n**Adoption**: {n_adopt}/{len(decisions)} pairs would switch to "
        f"BGE-reranker-v2-m3 under non-inferiority rule (v2 ≥ MiniLM − 0.01).\n"
    )
    md.append(
        "## Note on the labels\n"
        "The 550 SME labels are uncertainty-sampled — the active learner "
        "deliberately picked the cases where the production composite was "
        "least confident. tier_acc on this pool is correspondingly low and "
        "should not be read as overall mapper accuracy. What matters here "
        "is the *relative* per-pair comparison, which is what drives the "
        "per-pair toggle decision.\n"
    )
    OUT_MD.write_text("\n".join(md) + "\n")
    print(
        f"[phase_d] macro: baseline={macro_baseline:.3f} "
        f"minilm={macro_minilm:.3f} bge_v2={macro_bge:.3f} "
        f"adopt={n_adopt}/{len(decisions)}"
    )


if __name__ == "__main__":
    main()
