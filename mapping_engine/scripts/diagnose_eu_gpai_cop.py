"""S3: Forensic diagnosis of the aiuc_1__eu_gpai_cop MRR outlier.

aiuc_1__eu_gpai_cop scored MRR=0.1202 in both Session 7.5 (n=60) and
Session 7.6 S2 (n=60) — ~3x below the aggregate. Before sinking work
into target-side enrichment (S4) we want to confirm that missing/short
target descriptions are actually the root cause, rather than a
semantic-model mismatch on EU policy phrasing or distractor overlap.

Protocol:
  1. Run PairMapper on aiuc_1__eu_gpai_cop__expanded (leak-free masked
     composite scores already computed).
  2. Sample distractors via the S1 sampler.
  3. For each anchor, compute its reciprocal rank against its
     distractor pool (pessimistic tie-break, same as the metric module).
  4. Identify the 20 worst-ranked anchors (lowest RR, ties broken by
     positive composite ascending).
  5. For each, dump:
       - positive score
       - top-5 distractor scores
       - component breakdown at the positive cell: semantic, keyword,
         bridge, function_match, mitigation_lexical
       - target node description length (chars)
  6. Summary stats: median target description length across all 60
     anchors; fraction of worst-20 anchors with target description
     length < 200 chars.

Decision rule for S4: if >= 50% of worst-20 anchors have target
description length < 200 chars, enrichment is the right fix. Otherwise
mark S4–S7 as BLOCKED and investigate a different remediation.

Writes ``docs/diagnostics/eu_gpai_cop_forensics.md``.
"""

from __future__ import annotations

import statistics
from pathlib import Path

import numpy as np

from mapping_engine.calibration.distractor_sampler import sample_distractors
from mapping_engine.config import load_pair_config
from mapping_engine.engine.graph import load_graph
from mapping_engine.engine.mapper import PairMapper
from mapping_engine.engine.structural import compute_structural_features

REPO = Path(__file__).resolve().parents[2]
PAIR_NAME = "aiuc_1__eu_gpai_cop__expanded"
PAIR_YAML = REPO / f"mapping_engine/config/pairs/{PAIR_NAME}.yaml"
N_PER_ANCHOR = 20
RNG_SEED = 20260407


def _reciprocal_rank(pos: float, distractors: list[float]) -> float:
    """Pessimistic tie-break (same as discriminative_metric)."""
    better = sum(1 for d in distractors if d > pos)
    ties = sum(1 for d in distractors if d == pos)
    rank = better + ties + 1  # pessimistic: pos sits after all ties
    return 1.0 / rank


def _desc_len(G, node_id: str) -> int:
    d = G.nodes[node_id].get("description") or ""
    return len(d)


def main() -> None:
    G = load_graph(
        REPO / "data/processed/nodes.json", REPO / "data/processed/edges.json"
    )
    cfg = load_pair_config(PAIR_NAME, validate_anchors_in=G)
    mapper = PairMapper(G, cfg, use_learned_weights=False)
    result = mapper.run()

    src_idx = {n: i for i, n in enumerate(result.source_nodes)}
    tgt_idx = {n: i for i, n in enumerate(result.target_nodes)}
    av = result.anchor_validation
    masked: dict = {}
    masked.update(av.get("training_anchors", {}))
    masked.update(av.get("holdout_anchors", {}))

    # Per-signal matrices from PairMapper's production path are stored on
    # the result for the UNMASKED graph, which is what distractor cells
    # use. Positive rows come from the masked dict's score, but for the
    # component breakdown we pull from the unmasked matrices (acceptable
    # approximation — the purpose here is diagnosis, not gating).
    sig = result.signal_matrices
    sem = sig.get("semantic", np.zeros_like(result.composite_scores))
    kw = sig.get("keyword", np.zeros_like(result.composite_scores))
    br = sig.get("bridge", np.zeros_like(result.composite_scores))
    fm = sig.get("function_match", np.zeros_like(result.composite_scores))

    # Compute mitigation_lexical on the production graph for the same cells.
    feats = compute_structural_features(
        G, result.source_nodes, result.target_nodes
    )
    ml = feats.get(
        "mitigation_lexical_match",
        np.zeros_like(result.composite_scores),
    )

    dsets = sample_distractors(
        PAIR_YAML, G, n_per_anchor=N_PER_ANCHOR, rng_seed=RNG_SEED
    )

    rows = []
    tgt_desc_lens: list[int] = []
    for ds in dsets:
        key = f"{ds.source}__{ds.positive}"
        rec = masked.get(key)
        if rec is None or ds.source not in src_idx:
            continue
        pos = float(rec.get("score", 0.0))
        if ds.positive not in tgt_idx:
            continue
        si = src_idx[ds.source]
        ti = tgt_idx[ds.positive]
        dists = []
        for d in ds.distractors:
            if d in tgt_idx:
                dists.append(float(result.composite_scores[si, tgt_idx[d]]))
        if not dists:
            continue
        rr = _reciprocal_rank(pos, dists)
        top_d = sorted(dists, reverse=True)[:5]
        tgt_dl = _desc_len(G, ds.positive)
        tgt_desc_lens.append(tgt_dl)
        rows.append(
            {
                "source": ds.source,
                "target": ds.positive,
                "rr": rr,
                "pos": pos,
                "top5_distractors": top_d,
                "semantic": float(sem[si, ti]),
                "keyword": float(kw[si, ti]),
                "bridge": float(br[si, ti]),
                "function_match": float(fm[si, ti]),
                "mitigation_lexical": float(ml[si, ti]),
                "tgt_desc_len": tgt_dl,
            }
        )

    # Sort ascending by RR, then by pos ascending; take worst 20.
    rows.sort(key=lambda r: (r["rr"], r["pos"]))
    worst = rows[:20]

    n = len(rows)
    short_desc_ct = sum(1 for r in worst if r["tgt_desc_len"] < 200)
    median_tgt_len = statistics.median(tgt_desc_lens) if tgt_desc_lens else 0
    median_worst_len = (
        statistics.median([r["tgt_desc_len"] for r in worst]) if worst else 0
    )

    lines: list[str] = []
    lines.append("# aiuc_1__eu_gpai_cop forensic diagnosis (S3)\n")
    lines.append(
        "Diagnosing why this pair scores MRR≈0.12 vs aggregate ≈0.34. "
        "Generated by `mapping_engine/scripts/diagnose_eu_gpai_cop.py`.\n"
    )
    lines.append("## Summary stats\n")
    lines.append(f"- n anchors scored: {n}")
    lines.append(f"- median target description length (all anchors): {median_tgt_len} chars")
    lines.append(f"- median target description length (worst 20): {median_worst_len} chars")
    lines.append(
        f"- fraction of worst-20 with target description < 200 chars: "
        f"{short_desc_ct}/{len(worst)} = {short_desc_ct/max(1,len(worst)):.2f}"
    )
    lines.append("")
    lines.append("## Decision for S4\n")
    threshold = 0.50
    frac = short_desc_ct / max(1, len(worst))
    if frac >= threshold:
        decision = (
            f"**PROCEED to S4 (enrichment).** {frac:.0%} of the worst-ranked "
            f"anchors have target descriptions shorter than 200 chars, "
            f"meeting the ≥50% threshold. Missing text is the leading "
            f"candidate for the outlier."
        )
    else:
        decision = (
            f"**BLOCK S4–S7.** Only {frac:.0%} of the worst-ranked anchors "
            f"have target descriptions shorter than 200 chars, below the "
            f"50% threshold. Enrichment is unlikely to be the fix; "
            f"investigate semantic-model mismatch on EU policy phrasing "
            f"or distractor-pool contamination instead."
        )
    lines.append(decision + "\n")

    lines.append("## Worst 20 anchors (sorted ascending by reciprocal rank)\n")
    lines.append(
        "| # | source | target | RR | pos | top-5 distractors | sem | kw | bridge | fn_m | mit_lex | tgt_len |"
    )
    lines.append(
        "|---:|---|---|---:|---:|---|---:|---:|---:|---:|---:|---:|"
    )
    for i, r in enumerate(worst, 1):
        top5 = ", ".join(f"{v:.3f}" for v in r["top5_distractors"])
        lines.append(
            f"| {i} | `{r['source'].split(':',1)[-1][:20]}` | `{r['target'].split(':',1)[-1][:20]}` "
            f"| {r['rr']:.3f} | {r['pos']:.3f} | {top5} "
            f"| {r['semantic']:.2f} | {r['keyword']:.2f} | {r['bridge']:.2f} "
            f"| {r['function_match']:.2f} | {r['mitigation_lexical']:.2f} | {r['tgt_desc_len']} |"
        )
    lines.append("")

    out = REPO / "docs/diagnostics/eu_gpai_cop_forensics.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines))
    print(f"Wrote {out}")
    print(
        f"n={n} median_tgt_len={median_tgt_len} worst20_short={short_desc_ct}/20 "
        f"frac={frac:.2f} → {'PROCEED' if frac >= threshold else 'BLOCK'}"
    )


if __name__ == "__main__":
    main()
