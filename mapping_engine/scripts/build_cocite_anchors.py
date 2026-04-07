"""Build co-citation transitive anchor candidates for a framework pair.

For a (source_fw, target_fw) pair with no direct expert edges, find hub
nodes in hub frameworks (default: aiuc_1, cosai_rm) that have
expert/authoritative edges to BOTH a source_fw node AND a target_fw
node. Each such co-citation emits a candidate (source, target) anchor
pair with a weak-supervision tier prior.

Tier prior rule (conservative):
  - Direct   iff multiplicity >= 3 AND all per-hop priors are Direct
  - Related  otherwise

Per-hop prior is derived from ``rationale_to_tier.yaml`` on each edge's
rationale_code (fallback "?" -> Direct per the existing table).

Outputs a JSON record list to
``data/processed/cocite_anchors/{source}__{target}.json`` with fields:
  source, target, expected_tier, multiplicity, confidence_weight, hubs

Usage::

    python -m mapping_engine.scripts.build_cocite_anchors \
        --source-fw csa_aicm --target-fw owasp_agentic --top-n 100
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
NODES = REPO / "data" / "processed" / "nodes.json"
EDGES = REPO / "data" / "processed" / "edges.json"
RATIONALE_TABLE = REPO / "mapping_engine" / "config" / "rationale_to_tier.yaml"
OUT_DIR = REPO / "data" / "processed" / "cocite_anchors"

DEFAULT_HUBS = ("aiuc_1", "cosai_rm")


def _load_rationale() -> tuple[dict[str, str], dict[str, float]]:
    t = yaml.safe_load(RATIONALE_TABLE.read_text())
    return t["rationale_to_tier"], t.get("confidence_weight", {})


def _per_hop_tier(rc: str | None, rc_to_tier: dict[str, str]) -> str:
    if rc is None:
        return rc_to_tier.get("?", "Direct")
    return rc_to_tier.get(rc, rc_to_tier.get("?", "Direct"))


def build_candidates(
    source_fw: str,
    target_fw: str,
    hubs: tuple[str, ...] = DEFAULT_HUBS,
    min_multiplicity: int = 1,
    top_n: int | None = None,
) -> list[dict]:
    nodes = json.loads(NODES.read_text())
    edges = json.loads(EDGES.read_text())
    fw = {n["node_id"]: n.get("framework") for n in nodes}
    rc_to_tier, rc_weight = _load_rationale()

    # hub_node -> list of (src_node, rc)
    hub_to_src: dict[str, list[tuple[str, str | None]]] = defaultdict(list)
    # hub_node -> list of (tgt_node, rc)
    hub_to_tgt: dict[str, list[tuple[str, str | None]]] = defaultdict(list)
    for e in edges:
        if e.get("confidence") not in ("expert", "authoritative"):
            continue
        s = e.get("source_node_id")
        t = e.get("target_node_id")
        sf, tf = fw.get(s), fw.get(t)
        rc = e.get("rationale_code")
        if sf in hubs and tf == source_fw:
            hub_to_src[s].append((t, rc))
        if sf in hubs and tf == target_fw:
            hub_to_tgt[s].append((t, rc))

    # (src, tgt) -> list of (hub, rc_s, rc_t)
    cocite: dict[tuple[str, str], list[tuple[str, str | None, str | None]]] = defaultdict(list)
    for hub in set(hub_to_src) & set(hub_to_tgt):
        for (sn, rcs) in hub_to_src[hub]:
            for (tn, rct) in hub_to_tgt[hub]:
                cocite[(sn, tn)].append((hub, rcs, rct))

    candidates: list[dict] = []
    for (sn, tn), obs in cocite.items():
        mult = len(obs)
        if mult < min_multiplicity:
            continue
        per_hop_all_direct = all(
            _per_hop_tier(rcs, rc_to_tier) == "Direct"
            and _per_hop_tier(rct, rc_to_tier) == "Direct"
            for (_h, rcs, rct) in obs
        )
        tier_prior = "Direct" if (mult >= 3 and per_hop_all_direct) else "Related"
        # confidence weight: sum of per-citation min(w_s, w_t)
        cw = 0.0
        for (_h, rcs, rct) in obs:
            ws = rc_weight.get(rcs or "?", 0.75)
            wt = rc_weight.get(rct or "?", 0.75)
            cw += float(min(ws, wt))
        candidates.append(
            {
                "source": sn,
                "target": tn,
                "expected_tier": tier_prior,
                "multiplicity": mult,
                "confidence_weight": round(cw, 4),
                "hubs": sorted({h for (h, _rs, _rt) in obs}),
            }
        )

    candidates.sort(key=lambda c: (-c["multiplicity"], -c["confidence_weight"]))
    if top_n is not None:
        candidates = candidates[:top_n]
    return candidates


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-fw", required=True)
    ap.add_argument("--target-fw", required=True)
    ap.add_argument("--hubs", nargs="*", default=list(DEFAULT_HUBS))
    ap.add_argument("--min-multiplicity", type=int, default=1)
    ap.add_argument("--top-n", type=int, default=80)
    args = ap.parse_args(argv)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    candidates = build_candidates(
        args.source_fw,
        args.target_fw,
        hubs=tuple(args.hubs),
        min_multiplicity=args.min_multiplicity,
        top_n=args.top_n,
    )
    out_path = OUT_DIR / f"{args.source_fw}__{args.target_fw}.json"
    out_path.write_text(json.dumps(candidates, indent=2))
    tier_counts: dict[str, int] = {}
    for c in candidates:
        tier_counts[c["expected_tier"]] = tier_counts.get(c["expected_tier"], 0) + 1
    print(
        f"[cocite] {args.source_fw} -> {args.target_fw}: "
        f"{len(candidates)} candidates, tiers={tier_counts}"
    )
    print(f"[cocite] wrote {out_path.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
