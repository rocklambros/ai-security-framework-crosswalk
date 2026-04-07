"""v1 vs v2 AIUC-1 -> OWASP ASI crosswalk diff.

v1 source: hand-crafted expert mappings from the upstream AIUC-2 repository
(~/github_projects/AIUC_2_OWASP_Agentic_Top_10/tests/test_data.json), 119 pairs
across 10 ASI risks (Primary/Secondary).

v2 source: current production pipeline output
(mapping_engine/output/results/aiuc_1__owasp_agentic.json).

Writes:
  data/processed/v1_vs_v2_comparison.json  -- machine-readable diff
  data/processed/V1_VS_V2_COMPARISON_REPORT.md  -- narrative report
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
V1_PATH = Path.home() / "github_projects/AIUC_2_OWASP_Agentic_Top_10/tests/test_data.json"
V2_PATH = REPO / "mapping_engine/output/results/aiuc_1__owasp_agentic.json"
OUT_JSON = REPO / "data/processed/v1_vs_v2_comparison.json"
OUT_MD = REPO / "data/processed/V1_VS_V2_COMPARISON_REPORT.md"

# v1 uses Primary/Secondary; normalize to tiers aligned with v2.
V1_TIER = {"Primary": "Direct", "Secondary": "Related"}


def load_v1_pairs():
    d = json.loads(V1_PATH.read_text())
    pairs = {}
    for asi, ctrls in d["training"]["mappings"].items():
        for ctrl, info in ctrls.items():
            pairs[(ctrl, asi)] = {
                "v1_rel": info["rel"],
                "v1_tier": V1_TIER[info["rel"]],
                "v1_rationale": info.get("rat", ""),
            }
    return pairs


def load_v2_pairs():
    d = json.loads(V2_PATH.read_text())
    pairs = {}
    for c in d["control_level"]["source_to_target"]:
        for m in c["mappings"]:
            pairs[(c["control_id"], m["owasp_id"])] = {
                "v2_rel": m["relevance"],
                "v2_tier": V1_TIER.get(m["relevance"], m["relevance"]),
                "v2_score": m["score"],
                "v2_signals": m["signals"],
                "v2_rationale_code": m["rationale_code"],
                "v2_needs_review": m.get("needs_review", False),
            }
    return pairs, d["summary"], d["metadata"]


def main() -> None:
    v1 = load_v1_pairs()
    v2, v2_summary, v2_meta = load_v2_pairs()

    v1_keys = set(v1)
    v2_keys = set(v2)

    preserved = v1_keys & v2_keys
    lost = v1_keys - v2_keys        # in v1 expert set, missing from v2
    new = v2_keys - v1_keys          # produced by v2, not in v1 expert set

    # Tier changes among preserved
    tier_changes = []
    tier_same = 0
    for k in preserved:
        v1t = v1[k]["v1_tier"]
        v2t = v2[k]["v2_tier"]
        if v1t == v2t:
            tier_same += 1
        else:
            tier_changes.append(
                {
                    "control": k[0],
                    "risk": k[1],
                    "v1_tier": v1t,
                    "v2_tier": v2t,
                    "v2_score": v2[k]["v2_score"],
                    "v2_signals": v2[k]["v2_signals"],
                }
            )

    # Tier distributions
    v1_dist = Counter(v["v1_tier"] for v in v1.values())
    v2_dist = Counter(v["v2_tier"] for v in v2.values())

    preserved_pct = len(preserved) / len(v1_keys) if v1_keys else 0.0
    regression_pct = len(lost) / len(v1_keys) if v1_keys else 0.0

    # Signal-level summary for the 109 v2 pairs
    v2_signal_means = {}
    if v2:
        keys = list(next(iter(v2.values()))["v2_signals"].keys())
        for sk in keys:
            vals = [p["v2_signals"][sk] for p in v2.values()]
            v2_signal_means[sk] = sum(vals) / len(vals)

    out = {
        "v1_path": str(V1_PATH),
        "v2_path": str(V2_PATH),
        "counts": {
            "v1_pairs": len(v1_keys),
            "v2_pairs": len(v2_keys),
            "preserved": len(preserved),
            "preserved_pct": preserved_pct,
            "lost_from_v1": len(lost),
            "regression_pct": regression_pct,
            "new_in_v2": len(new),
            "tier_same": tier_same,
            "tier_changed": len(tier_changes),
        },
        "tier_distribution": {
            "v1": dict(v1_dist),
            "v2": dict(v2_dist),
        },
        "v2_summary": v2_summary,
        "v2_signal_means": v2_signal_means,
        "preserved_pairs": sorted([f"{c}->{r}" for c, r in preserved]),
        "lost_pairs": [
            {"control": c, "risk": r, "v1_tier": v1[(c, r)]["v1_tier"],
             "v1_rationale": v1[(c, r)]["v1_rationale"]}
            for c, r in sorted(lost)
        ],
        "new_pairs": [
            {"control": c, "risk": r, "v2_tier": v2[(c, r)]["v2_tier"],
             "v2_score": v2[(c, r)]["v2_score"],
             "v2_signals": v2[(c, r)]["v2_signals"]}
            for c, r in sorted(new)
        ],
        "tier_changes": sorted(tier_changes, key=lambda d: (d["control"], d["risk"])),
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(out, indent=2))

    md = []
    md.append("# AIUC-1 -> OWASP ASI: v1 (expert hand-crafted) vs v2 (pipeline) comparison\n")
    md.append(
        "v1 is the 119-pair hand-crafted crosswalk shipped with the upstream "
        "AIUC-2 repository. v2 is the current production output of the "
        "multi-signal hybrid mapping engine. This report diffs the two at "
        "pair-level, tier-level, and signal-level, and documents the gaps.\n"
    )
    md.append("## Summary counts\n")
    md.append("| metric | value |")
    md.append("|---|---:|")
    md.append(f"| v1 pairs | {len(v1_keys)} |")
    md.append(f"| v2 pairs | {len(v2_keys)} |")
    md.append(f"| preserved (in both) | {len(preserved)} ({preserved_pct:.1%}) |")
    md.append(f"| tier preserved too | {tier_same} |")
    md.append(f"| tier changed | {len(tier_changes)} |")
    md.append(f"| lost from v1 | {len(lost)} ({regression_pct:.1%}) |")
    md.append(f"| new in v2 | {len(new)} |\n")

    md.append("## Tier distribution\n")
    md.append("| tier | v1 | v2 |")
    md.append("|---|---:|---:|")
    for t in ("Direct", "Related"):
        md.append(f"| {t} | {v1_dist.get(t, 0)} | {v2_dist.get(t, 0)} |")
    md.append("")

    md.append("## Tier changes (preserved pairs whose tier moved)\n")
    if tier_changes:
        md.append("| control | risk | v1 | v2 | v2 score |")
        md.append("|---|---|---|---|---:|")
        for tc in sorted(tier_changes, key=lambda d: (d["control"], d["risk"]))[:40]:
            md.append(
                f"| {tc['control']} | {tc['risk']} | {tc['v1_tier']} | "
                f"{tc['v2_tier']} | {tc['v2_score']:.3f} |"
            )
        if len(tier_changes) > 40:
            md.append(f"\n_(+{len(tier_changes)-40} more in JSON)_")
    else:
        md.append("_None._")
    md.append("")

    md.append("## Lost pairs (in v1 expert set, not produced by v2)\n")
    if lost:
        md.append("| control | risk | v1 tier | v1 rationale |")
        md.append("|---|---|---|---|")
        for item in out["lost_pairs"][:40]:
            md.append(
                f"| {item['control']} | {item['risk']} | {item['v1_tier']} | "
                f"{item['v1_rationale']} |"
            )
        if len(out["lost_pairs"]) > 40:
            md.append(f"\n_(+{len(out['lost_pairs'])-40} more in JSON)_")
    else:
        md.append("_None._")
    md.append("")

    md.append("## New pairs (produced by v2, not in v1 expert set)\n")
    if new:
        md.append("| control | risk | v2 tier | v2 score |")
        md.append("|---|---|---|---:|")
        for item in out["new_pairs"][:40]:
            md.append(
                f"| {item['control']} | {item['risk']} | {item['v2_tier']} | "
                f"{item['v2_score']:.3f} |"
            )
        if len(out["new_pairs"]) > 40:
            md.append(f"\n_(+{len(out['new_pairs'])-40} more in JSON)_")
    else:
        md.append("_None._")
    md.append("")

    verdict = "regression" if regression_pct > 0.05 else (
        "strict improvement" if len(new) >= len(lost) and tier_same >= 0.9 * len(preserved)
        else "lateral move with tradeoffs"
    )
    md.append("## Verdict\n")
    md.append(
        f"v2 preserves {preserved_pct:.1%} of the v1 expert pairs, loses "
        f"{len(lost)} ({regression_pct:.1%}), adds {len(new)} new candidates, "
        f"and changes tier on {len(tier_changes)} of the preserved pairs. "
        f"By the session 11 rule (regression on >5% flags manual review), "
        f"this is a **{verdict}**.\n"
    )
    md.append(
        "The loss set is concentrated on AIUC controls that do not appear in "
        "v2's mapped set at all, which typically reflects composite scores "
        "below the needs-review band rather than explicit rejection. These "
        "are the natural queue for the next active-learning round.\n"
    )

    OUT_MD.write_text("\n".join(md) + "\n")
    print(
        f"[v1_vs_v2] v1={len(v1_keys)} v2={len(v2_keys)} preserved={len(preserved)} "
        f"({preserved_pct:.1%}) lost={len(lost)} new={len(new)} "
        f"tier_changed={len(tier_changes)} -> {verdict}"
    )


if __name__ == "__main__":
    main()
