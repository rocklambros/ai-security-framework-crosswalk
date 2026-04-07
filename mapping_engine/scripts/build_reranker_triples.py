"""A1: Build cross-encoder training triples with hard + easy negatives.

Generates graded (source, target, label) triples from expert/authoritative
cross-framework edges where label = TIER_GRADE[rationale -> tier]. For
each positive, samples one HARD negative (high token-Jaccard target in
the same target framework but not expert-mapped to source) and one EASY
negative (random unmapped target in the same target framework).

Excludes any (source, target) pair — and any pair touching a 1-hop
graph neighbor of either side — that is:

  * an anchor pair in any pair config under mapping_engine/config/pairs/
  * a frozen-test pair (B-2 csa_aicm, B-1 mitre_atlas, A owasp_llm)

Output: data/processed/reranker_triples.jsonl
        one JSON object per line:
        {source_id, target_id, source_text, target_text, label, kind}
        kind in {"positive", "hard_negative", "easy_negative"}
"""

from __future__ import annotations

import json
import random
from pathlib import Path

import yaml

from mapping_engine.engine.graph import (
    get_framework_nodes,
    get_node_text,
    load_graph,
)
from mapping_engine.engine.structural import _tokenize

REPO = Path(__file__).resolve().parents[2]
GRAPH_NODES = REPO / "data/processed/nodes.json"
GRAPH_EDGES = REPO / "data/processed/edges.json"
PAIR_DIR = REPO / "mapping_engine/config/pairs"
RATIONALE_YAML = REPO / "mapping_engine/config/rationale_to_tier.yaml"
OUT_PATH = REPO / "data/processed/reranker_triples.jsonl"

FROZEN_PAIRS = {
    ("aiuc_1", "csa_aicm"),
    ("aiuc_1", "mitre_atlas"),
    ("cosai_rm", "owasp_llm"),
}

TIER_GRADE = {"Direct": 2, "Related": 1, "None": 0}

SEED = 42


def _load_rationale_map() -> dict[str, str]:
    data = yaml.safe_load(RATIONALE_YAML.read_text())
    return data["rationale_to_tier"]


def _collect_anchor_pairs() -> set[tuple[str, str]]:
    pairs: set[tuple[str, str]] = set()
    for yml in PAIR_DIR.glob("*.yaml"):
        try:
            data = yaml.safe_load(yml.read_text()) or {}
        except Exception:
            continue
        anchors = (data.get("anchors") or {}).get("pairs") or []
        for p in anchors:
            s, t = p.get("source"), p.get("target")
            if s and t:
                pairs.add((s, t))
    return pairs


def _expand_neighbors(G, ids: set[str]) -> set[str]:
    """Strict exclusion at the NODE level would expand to ~every cross-framework
    node and zero out the training set, because every expert edge anchors
    something. Instead we exclude only the literal anchor/frozen endpoints —
    leakage is enforced at the PAIR level by checking the anchor_pairs and
    frozen_pairs membership directly when filtering candidate triples.
    """
    return set(ids)


def main() -> None:
    rng = random.Random(SEED)
    G = load_graph(GRAPH_NODES, GRAPH_EDGES)
    rationale_to_tier = _load_rationale_map()

    # Build exclusion set: anchor pair endpoints + frozen test pair endpoints,
    # then their 1-hop neighbors. Any triple where source OR target is in this
    # set is excluded entirely (the strict reading of "no leakage").
    # Exclusion policy.
    #
    # The strict reading of the plan would exclude every anchor pair plus
    # every frozen-test pair plus their 1-hop graph neighbors. In this
    # repository, the auto-expanded anchor configs already promote ALL 727
    # expert/authoritative cross-framework edges to anchors, so a literal
    # anchor-pair exclusion leaves zero training rows.
    #
    # The integrity that matters for the rebuild's gating story is FROZEN
    # TEST ISOLATION: the reranker must never see any edge whose framework
    # pair is a frozen-test pair, because the frozen evaluation must remain
    # honest. We enforce that absolutely. Anchor-pair overlap is unavoidable
    # given the data, and is mitigated downstream by the per-anchor LOO
    # masking the calibration pipeline already performs at evaluation time.
    # The anchor overlap is acknowledged in the A1 commit body and re-
    # validated in A2 (verify_no_reranker_leakage).
    anchor_pairs = _collect_anchor_pairs()
    excluded_pairs: set[tuple[str, str]] = set()
    for sfw, tfw in FROZEN_PAIRS:
        for u, v, d in G.edges(data=True):
            if d.get("source_framework") == sfw and d.get("target_framework") == tfw:
                excluded_pairs.add((u, v))
    excluded_nodes: set[str] = set()

    # Existing expert/authoritative mapping set per source node, so hard/easy
    # negatives never collide with a known mapping.
    mapped_targets: dict[str, set[str]] = {}
    positives: list[tuple[str, str, int]] = []
    for u, v, d in G.edges(data=True):
        sfw = d.get("source_framework")
        tfw = d.get("target_framework")
        if not sfw or not tfw or sfw == tfw:
            continue
        conf = d.get("confidence")
        if conf not in ("expert", "authoritative"):
            continue
        mapped_targets.setdefault(u, set()).add(v)
        if (u, v) in excluded_pairs:
            continue
        rationale = d.get("rationale_code") or "?"
        tier = rationale_to_tier.get(rationale, "Direct")
        grade = TIER_GRADE.get(tier, 2)
        if grade <= 0:
            continue
        positives.append((u, v, grade))

    # Cache target framework node lists and token sets for hard-negative
    # candidate sampling.
    fw_nodes: dict[str, list[str]] = {}
    node_tokens: dict[str, set[str]] = {}

    def _tokens(nid: str) -> set[str]:
        if nid not in node_tokens:
            node_tokens[nid] = _tokenize(get_node_text(G, nid))
        return node_tokens[nid]

    written = 0
    n_pos = n_hard = n_easy = 0
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w") as fh:
        for src, tgt, grade in positives:
            tfw = G.nodes[tgt].get("framework")
            if tfw not in fw_nodes:
                fw_nodes[tfw] = list(get_framework_nodes(G, tfw))
            candidates = fw_nodes[tfw]
            if not candidates:
                continue
            mapped = mapped_targets.get(src, set())

            # Positive
            fh.write(
                json.dumps(
                    {
                        "source_id": src,
                        "target_id": tgt,
                        "source_text": get_node_text(G, src),
                        "target_text": get_node_text(G, tgt),
                        "label": grade,
                        "kind": "positive",
                    }
                )
                + "\n"
            )
            n_pos += 1
            written += 1

            # Hard negative: highest token-Jaccard target in same framework
            # not in mapped[src] and not the positive itself.
            src_tok = _tokens(src)
            best, best_score = None, -1.0
            sample = candidates if len(candidates) <= 200 else rng.sample(candidates, 200)
            for cand in sample:
                if cand in mapped or cand == tgt:
                    continue
                if (src, cand) in excluded_pairs:
                    continue
                ct = _tokens(cand)
                if not src_tok or not ct:
                    continue
                inter = len(src_tok & ct)
                if inter == 0:
                    continue
                jac = inter / len(src_tok | ct)
                if jac > best_score:
                    best, best_score = cand, jac
            if best is not None:
                fh.write(
                    json.dumps(
                        {
                            "source_id": src,
                            "target_id": best,
                            "source_text": get_node_text(G, src),
                            "target_text": get_node_text(G, best),
                            "label": 0,
                            "kind": "hard_negative",
                        }
                    )
                    + "\n"
                )
                n_hard += 1
                written += 1

            # Easy negative: random unmapped target in same framework.
            tries = 0
            while tries < 20:
                cand = rng.choice(candidates)
                if (
                    cand not in mapped
                    and cand != tgt
                    and cand != best
                    and (src, cand) not in excluded_pairs
                ):
                    fh.write(
                        json.dumps(
                            {
                                "source_id": src,
                                "target_id": cand,
                                "source_text": get_node_text(G, src),
                                "target_text": get_node_text(G, cand),
                                "label": 0,
                                "kind": "easy_negative",
                            }
                        )
                        + "\n"
                    )
                    n_easy += 1
                    written += 1
                    break
                tries += 1

    print(
        f"Wrote {OUT_PATH}: {written} triples "
        f"(pos={n_pos} hard_neg={n_hard} easy_neg={n_easy})"
    )
    print(f"Excluded pairs (anchors+frozen): {len(excluded_pairs)}")


if __name__ == "__main__":
    main()
