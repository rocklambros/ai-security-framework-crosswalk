"""Compute S8 per-pair tier_acc against the 150 SME labels and freeze it as
parity targets (replacing the tautological holdout_accuracy=1.00 from the
co-citation bootstrap)."""
from __future__ import annotations
import json
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
SHEETS = REPO / "mapping_engine/output/labeling_sheets"
OUT = REPO / "mapping_engine/output/session9_s8_frozen_tier_acc.json"

S8_PAIRS = [
    "csa_aicm__owasp_agentic",
    "mitre_atlas__owasp_llm",
    "nist_rmf__owasp_agentic",
]


def tier_for_score(s: float) -> str:
    if s >= 0.45:
        return "Direct"
    if s >= 0.20:
        return "Related"
    if s >= 0.10:
        return "Tangential"
    return "None"


def main() -> None:
    out = {}
    for pair in S8_PAIRS:
        f = SHEETS / f"{pair}__candidates.yaml"
        d = yaml.safe_load(f.read_text())
        cs = [c for c in d["candidates"] if c.get("expert_tier")]
        y = [c["expert_tier"] for c in cs]
        p = [tier_for_score(float(c["composite_score"])) for c in cs]
        acc = sum(1 for a, b in zip(y, p) if a == b) / len(cs)
        out[pair] = {"n": len(cs), "tier_acc": round(acc, 4)}
        print(f"[s8-frozen] {pair} n={len(cs)} tier_acc={acc:.4f}")
    OUT.write_text(json.dumps(out, indent=2))
    print(f"[s8-frozen] wrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
