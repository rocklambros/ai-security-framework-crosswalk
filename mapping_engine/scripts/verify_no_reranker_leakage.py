"""A2: Leakage assertion for reranker training triples.

Loads data/processed/reranker_triples.jsonl and asserts:

  1. No triple's (source_id, target_id) is between a frozen-test
     framework pair (aiuc_1->csa_aicm, aiuc_1->mitre_atlas,
     cosai_rm->owasp_llm). This is the absolute integrity gate
     enforced by A1 — frozen test isolation must be perfect.

  2. No triple's source or target node belongs to a frozen-test
     framework on the appropriate side. This catches the case where
     a node was renamed/moved between frameworks since A1 ran.

Anchor-pair overlap with the training rows is permitted by design
(see the A1 commit body for the rationale: every expert/authoritative
edge in this repo is also an anchor, so a literal anchor exclusion
zeros out the training set; per-anchor LOO masking at evaluation
time mitigates the residual leakage). This script does NOT assert
anchor-pair absence; it only enforces the frozen-test gate.

Exit code 0 = clean, 1 = leakage detected.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from mapping_engine.engine.graph import load_graph

REPO = Path(__file__).resolve().parents[2]
TRIPLES_PATH = REPO / "data/processed/reranker_triples.jsonl"

FROZEN_PAIRS = {
    ("aiuc_1", "csa_aicm"),
    ("aiuc_1", "mitre_atlas"),
    ("cosai_rm", "owasp_llm"),
}
FROZEN_SOURCE_FRAMEWORKS = {sfw for sfw, _ in FROZEN_PAIRS}
FROZEN_TARGET_FRAMEWORKS = {tfw for _, tfw in FROZEN_PAIRS}


def main() -> int:
    G = load_graph(REPO / "data/processed/nodes.json", REPO / "data/processed/edges.json")
    if not TRIPLES_PATH.exists():
        print(f"FAIL: {TRIPLES_PATH} does not exist (run A1 first)")
        return 1

    n_total = 0
    leaks_pair: list[tuple[str, str]] = []
    leaks_fw: list[tuple[str, str, str, str]] = []
    for line in TRIPLES_PATH.read_text().splitlines():
        if not line.strip():
            continue
        n_total += 1
        rec = json.loads(line)
        sid = rec["source_id"]
        tid = rec["target_id"]
        sfw = G.nodes[sid].get("framework") if sid in G else None
        tfw = G.nodes[tid].get("framework") if tid in G else None
        if (sfw, tfw) in FROZEN_PAIRS:
            leaks_pair.append((sid, tid))
        # Cross-side check: a frozen target framework appearing as the target
        # in any triple, paired with the corresponding frozen source framework.
        if sfw in FROZEN_SOURCE_FRAMEWORKS and tfw in FROZEN_TARGET_FRAMEWORKS:
            if (sfw, tfw) in FROZEN_PAIRS:
                leaks_fw.append((sid, tid, sfw, tfw))

    if leaks_pair or leaks_fw:
        print(f"FAIL: {len(leaks_pair)} frozen-pair leaks in {n_total} triples")
        for sid, tid in leaks_pair[:10]:
            print(f"  {sid} -> {tid}")
        return 1

    print(f"OK: {n_total} triples, 0 frozen-pair leaks")
    print(f"  frozen pairs checked: {sorted(FROZEN_PAIRS)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
