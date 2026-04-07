"""Phase A verification — score 550 SME labels with the production composite
score and report per-pair tier_acc, Cohen's kappa, and Direct-vs-rest AUROC.

Uses already-computed composite_score from the labeling sheets (production
pipeline output with reranker on for S7 pairs and off for S8 new pairs), so
no additional model load is required. Heavy model verification (BGE-rerankerv2,
deberta-NLI, Qwen LLM judge, embedding ensemble) is documented as deferred —
they would require multi-GB downloads beyond the unified-hardening budget.
"""
from __future__ import annotations
import json
from collections import Counter
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
SHEETS = REPO / "mapping_engine/output/labeling_sheets"
OUT = REPO / "docs/session9_verification.md"

TIERS = ["None", "Tangential", "Related", "Direct"]
TIER_IDX = {t: i for i, t in enumerate(TIERS)}


def tier_for_score(s: float) -> str:
    if s >= 0.45:
        return "Direct"
    if s >= 0.20:
        return "Related"
    if s >= 0.10:
        return "Tangential"
    return "None"


def cohen_kappa(y_true, y_pred):
    n = len(y_true)
    if n == 0:
        return 0.0
    labels = sorted(set(y_true) | set(y_pred))
    cm = {(a, b): 0 for a in labels for b in labels}
    for a, b in zip(y_true, y_pred):
        cm[(a, b)] += 1
    po = sum(cm[(l, l)] for l in labels) / n
    pe = sum(
        (sum(cm[(l, x)] for x in labels) / n)
        * (sum(cm[(x, l)] for x in labels) / n)
        for l in labels
    )
    return (po - pe) / (1 - pe) if (1 - pe) > 1e-9 else 0.0


def auroc(scores, labels):
    """Direct-vs-rest AUROC via Mann-Whitney."""
    pos = [s for s, l in zip(scores, labels) if l == 1]
    neg = [s for s, l in zip(scores, labels) if l == 0]
    if not pos or not neg:
        return float("nan")
    rank_sum = 0.0
    for p in pos:
        for n in neg:
            if p > n:
                rank_sum += 1
            elif p == n:
                rank_sum += 0.5
    return rank_sum / (len(pos) * len(neg))


def main() -> None:
    rows = []
    all_y, all_p = [], []
    for f in sorted(SHEETS.glob("*__candidates.yaml")):
        pair = f.stem.replace("__candidates", "")
        d = yaml.safe_load(f.read_text())
        cs = [c for c in d["candidates"] if c.get("expert_tier")]
        if not cs:
            continue
        y_true = [c["expert_tier"] for c in cs]
        scores = [float(c["composite_score"]) for c in cs]
        y_pred = [tier_for_score(s) for s in scores]
        # tier accuracy
        acc = sum(1 for a, b in zip(y_true, y_pred) if a == b) / len(cs)
        # Cohen kappa
        kappa = cohen_kappa(y_true, y_pred)
        # AUROC Direct vs rest
        bin_labels = [1 if t == "Direct" else 0 for t in y_true]
        roc = auroc(scores, bin_labels)
        # Direct precision/recall
        tp = sum(1 for a, b in zip(y_true, y_pred) if a == "Direct" and b == "Direct")
        fp = sum(1 for a, b in zip(y_true, y_pred) if a != "Direct" and b == "Direct")
        fn = sum(1 for a, b in zip(y_true, y_pred) if a == "Direct" and b != "Direct")
        prec = tp / (tp + fp) if (tp + fp) else float("nan")
        rec = tp / (tp + fn) if (tp + fn) else float("nan")
        rows.append((pair, len(cs), acc, kappa, roc, prec, rec))
        all_y.extend(y_true)
        all_p.extend(y_pred)

    overall_acc = sum(1 for a, b in zip(all_y, all_p) if a == b) / len(all_y)
    overall_kappa = cohen_kappa(all_y, all_p)

    md = ["# Session 9 — Phase A Verification\n"]
    md.append(
        "Per-pair verification of the production composite score against the "
        "550 SME labels (400 S7 + 150 S8). Pred tier uses unified thresholds "
        "Direct≥0.45, Related≥0.20, Tangential≥0.10.\n"
    )
    md.append(
        "| Pair | n | tier_acc | Cohen κ | AUROC(Direct) | P(Direct) | R(Direct) |"
    )
    md.append("|---|---:|---:|---:|---:|---:|---:|")
    for pair, n, acc, k, roc, p, r in rows:
        md.append(
            f"| {pair} | {n} | {acc:.3f} | {k:.3f} | {roc:.3f} | {p:.3f} | {r:.3f} |"
        )
    md.append(
        f"\n**Overall** (n={len(all_y)}): tier_acc={overall_acc:.3f}, "
        f"Cohen κ={overall_kappa:.3f}\n"
    )
    md.append("## Heavy verification — deferred\n")
    md.append(
        "BGE-reranker-v2-m3, deberta-v3-large-mnli, Qwen2.5-7B-Instruct LLM\n"
        "judge, and the BGE+stella+nomic embedding ensemble were planned as\n"
        "additional verification signals. They are documented as deferred for\n"
        "this iteration: each requires multi-GB GPU model downloads and a new\n"
        "wiring path through PairMapper.signal_matrices. Phase B (next) wires\n"
        "the slots at weight=0.0; the heavy models can be plugged in there\n"
        "without further code changes once the slots exist.\n"
    )
    OUT.write_text("\n".join(md) + "\n")
    print(f"[phase_a] wrote {OUT.relative_to(REPO)}")
    print(f"[phase_a] overall tier_acc={overall_acc:.3f} κ={overall_kappa:.3f}")
    # also dump JSON for downstream tools
    json_out = REPO / "mapping_engine/output/session9_phase_a.json"
    json_out.write_text(
        json.dumps(
            {
                "rows": [
                    {
                        "pair": pair,
                        "n": n,
                        "tier_acc": acc,
                        "kappa": k,
                        "auroc_direct": roc,
                        "p_direct": p,
                        "r_direct": r,
                    }
                    for pair, n, acc, k, roc, p, r in rows
                ],
                "overall": {
                    "n": len(all_y),
                    "tier_acc": overall_acc,
                    "kappa": overall_kappa,
                },
            },
            indent=2,
        )
    )
    print(f"[phase_a] wrote {json_out.relative_to(REPO)}")


if __name__ == "__main__":
    main()
