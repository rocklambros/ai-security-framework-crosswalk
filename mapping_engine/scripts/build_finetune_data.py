"""Build the contrastive fine-tuning dataset for the embedding model.

Inputs
------
* The 119 AIUC-1 → OWASP Agentic expert mappings (positive pairs)
* The base semantic model (BAAI/bge-large-en-v1.5) for hard-negative mining
* ``mapping_engine/config/synonyms.yaml`` for cheap text augmentation

Outputs
-------
* ``data/processed/finetune_train.json`` — list of triplets
  ``{"anchor": str, "positive": str, "negative": str}``
* ``data/processed/finetune_val.json`` — NIST validation cosine pairs
  ``{"sentence1": str, "sentence2": str, "score": float}``

Strategy
--------
Hard negatives: for each positive (A, B) we score every *non-mapped*
target node against A under the base model and pick the top-3 most
similar — those are the deceptive distractors the fine-tune should
push apart.

Augmentation: synonym substitution from ``synonyms.yaml``. For each
positive we create one augmented anchor where the first matching domain
term is replaced by a sibling synonym. This doubles the anchor count to
~238 without inventing new content.

Validation set: NIST RMF subcategories paired with the OWASP risks they
expert-map to (label 1.0) plus an equal number of random non-mapped
pairs (label 0.0). Used by the cosine evaluator during training.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

import numpy as np
import yaml

from mapping_engine.engine.graph import get_framework_nodes, get_node_text, load_graph
from mapping_engine.engine.semantic import _load_model, compute_embeddings

REPO = Path(__file__).resolve().parents[2]
TEST_DATA = Path.home() / "github_projects" / "AIUC_2_OWASP_Agentic_Top_10" / "tests" / "test_data.json"
SYNONYMS_PATH = REPO / "mapping_engine" / "config" / "synonyms.yaml"
NIST_PREFIX = {"GV": "GOVERN", "MP": "MAP", "MS": "MEASURE", "MG": "MANAGE"}


def _normalize_nist_id(short: str) -> str:
    pre, _, rest = short.partition(".")
    return f"{NIST_PREFIX.get(pre, pre)}-{rest}"


def _load_synonym_groups() -> list[list[str]]:
    raw = yaml.safe_load(SYNONYMS_PATH.read_text())
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        return raw.get("groups") or []
    return []


def _augment(text: str, groups: list[list[str]], rng: random.Random) -> str:
    low = text.lower()
    for group in groups:
        for term in group:
            if term.lower() in low:
                others = [t for t in group if t != term]
                if not others:
                    continue
                replacement = rng.choice(others)
                # case-insensitive replace, first occurrence only
                idx = low.find(term.lower())
                return text[:idx] + replacement + text[idx + len(term):]
    return text


def main() -> None:
    G = load_graph(REPO / "data/processed/nodes.json", REPO / "data/processed/edges.json")
    data = json.loads(TEST_DATA.read_text())

    aiuc_sources = sorted(get_framework_nodes(G, "aiuc_1", entry_types=["control"]))
    owasp_targets = sorted(get_framework_nodes(G, "owasp_agentic", entry_types=["risk"]))
    aiuc_lid = {G.nodes[n]["local_id"]: n for n in aiuc_sources}
    owasp_lid = {G.nodes[n]["local_id"]: n for n in owasp_targets}

    # Positive pairs ──────────────────────────────────────────────────────
    positives: list[tuple[str, str]] = []
    for tgt_local, src_dict in data["training"]["mappings"].items():
        tgt_node = owasp_lid.get(tgt_local)
        if not tgt_node:
            continue
        for src_local in src_dict.keys():
            src_node = aiuc_lid.get(src_local)
            if src_node:
                positives.append((src_node, tgt_node))
    print(f"Positive pairs: {len(positives)}")

    # Hard-negative mining ────────────────────────────────────────────────
    print("Loading base model for hard-negative mining...")
    model = _load_model("BAAI/bge-large-en-v1.5")
    src_emb = compute_embeddings(G, aiuc_sources, model)
    tgt_emb = compute_embeddings(G, owasp_targets, model)
    sims = src_emb @ tgt_emb.T
    src_idx = {n: i for i, n in enumerate(aiuc_sources)}
    tgt_idx = {n: j for j, n in enumerate(owasp_targets)}

    pos_set = set(positives)
    triplets: list[dict[str, str]] = []
    rng = random.Random(42)
    groups = _load_synonym_groups()
    for s, t in positives:
        i = src_idx[s]
        # rank target candidates by similarity to s, pick most similar that
        # is NOT t and NOT in any positive pair for s
        order = np.argsort(-sims[i])
        chosen_neg: str | None = None
        for j in order:
            cand = owasp_targets[j]
            if cand == t:
                continue
            if (s, cand) in pos_set:
                continue
            chosen_neg = cand
            break
        if chosen_neg is None:
            continue
        anchor = get_node_text(G, s)
        positive = get_node_text(G, t)
        negative = get_node_text(G, chosen_neg)
        triplets.append({"anchor": anchor, "positive": positive, "negative": negative})
        # augmented variant
        aug = _augment(anchor, groups, rng) if groups else anchor
        if aug != anchor:
            triplets.append({"anchor": aug, "positive": positive, "negative": negative})

    print(f"Triplets: {len(triplets)} (positives + augmented)")

    train_path = REPO / "data" / "processed" / "finetune_train.json"
    train_path.write_text(json.dumps(triplets, indent=2))
    print(f"Wrote {train_path}")

    # NIST validation cosine pairs ────────────────────────────────────────
    nist_sources = sorted(get_framework_nodes(G, "nist_rmf", entry_types=["subcategory"]))
    nist_lid = {G.nodes[n]["local_id"]: n for n in nist_sources}
    val_pairs: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for tgt_local, src_dict in data["validation"]["mappings"].items():
        tgt_node = owasp_lid.get(tgt_local)
        if not tgt_node:
            continue
        for src_local in src_dict.keys():
            src_node = nist_lid.get(_normalize_nist_id(src_local))
            if not src_node:
                continue
            key = (src_node, tgt_node)
            seen.add(key)
            val_pairs.append({
                "sentence1": get_node_text(G, src_node),
                "sentence2": get_node_text(G, tgt_node),
                "score": 1.0,
            })
    # equal-sized random negatives
    n_neg = len(val_pairs)
    rng2 = random.Random(7)
    while n_neg > 0:
        s = rng2.choice(nist_sources)
        t = rng2.choice(owasp_targets)
        if (s, t) in seen:
            continue
        seen.add((s, t))
        val_pairs.append({
            "sentence1": get_node_text(G, s),
            "sentence2": get_node_text(G, t),
            "score": 0.0,
        })
        n_neg -= 1

    val_path = REPO / "data" / "processed" / "finetune_val.json"
    val_path.write_text(json.dumps(val_pairs, indent=2))
    print(f"Wrote {val_path}: {len(val_pairs)} pairs")


if __name__ == "__main__":
    main()
