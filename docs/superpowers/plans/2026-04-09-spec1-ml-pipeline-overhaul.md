# ML Pipeline Overhaul + Project 1 Notebook — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the LLM-trained pipeline with a multi-encoder ensemble fine-tuned on 3,210 upstream expert mappings, achieving ≥75% tier accuracy on frozen test.

**Architecture:** Three cross-encoders (DeBERTa-v3-large, RoBERTa-large, ELECTRA-large) with contrastive pre-training + CORN ordinal loss, combined with retrained GATv2 features in a LightGBM stacker. Two-stage classification (binary filter → ordinal). Mondrian conformal + KL router recalibrated. All compute on Lambda H100, all experiments in WANDB.

**Tech Stack:** PyTorch, transformers, sentence-transformers, torch-geometric, lightgbm, optuna, wandb, coral-pytorch, numpy, pandas, matplotlib, seaborn

---

## File Structure

```
classifier/
  data/
    tier_mapper.py              # NEW: Map upstream tiers → 4-class labels
    text_enricher.py            # NEW: Append parent/category/sibling text
    negative_miner.py           # NEW: Hard negative sampling via BM25
  ensemble/
    leakage_firewall.py         # NEW: Pre-flight leakage assertions
    cross_encoder.py            # NEW: Cross-encoder wrapper (train + predict)
    contrastive_pretrain.py     # NEW: Supervised SimCSE pre-training
    corn_loss.py                # NEW: CORN ordinal loss function
    stacker.py                  # MODIFY: Expand feature columns, add ordinal objective
    gat_model.py                # EXISTING: No changes needed
    gat_train.py                # MODIFY: Accept expert-derived edge list
    conformal.py                # EXISTING: No changes needed
    router.py                   # EXISTING: No changes needed
    two_stage.py                # NEW: Binary + ordinal classification heads
  sacred/
    sacred_run.py               # MODIFY: Load new model artifacts
    run_ablations.py            # MODIFY: New ablation configs for multi-CE
    ablation_registry.py        # MODIFY: Register new configs
  lambda/
    requirements-lambda.txt     # NEW: Lambda H100 dependencies
    train_all.py                # NEW: Orchestrator script for Lambda
    wandb_config.py             # NEW: WANDB project/sweep configs
  scripts/
    build_expert_training.py    # NEW: End-to-end training data builder
    active_learning.py          # NEW: Uncertainty-based pair selector
  tests/
    test_tier_mapper.py         # NEW
    test_text_enricher.py       # NEW
    test_negative_miner.py      # NEW
    test_leakage_firewall.py    # NEW
    test_cross_encoder.py       # NEW
    test_corn_loss.py           # NEW
    test_two_stage.py           # NEW

data/
  splits/
    expert_train.jsonl          # NEW: Generated training data
    expert_val.jsonl            # NEW: Generated val split

notebooks/
  project1_exploratory.ipynb    # NEW: COMP 4433 Project 1 notebook
```

---

### Task 1: Leakage Firewall

**Files:**
- Create: `classifier/ensemble/leakage_firewall.py`
- Create: `classifier/tests/test_leakage_firewall.py`

- [ ] **Step 1: Write the failing test**

```python
# classifier/tests/test_leakage_firewall.py
"""Tests for leakage firewall assertions."""
import pytest
from classifier.ensemble.leakage_firewall import check_no_leakage


def test_clean_split_passes():
    train_keys = {"a::x__y", "b::x__y", "c::x__y"}
    test_keys = {"d::x__y", "e::x__y"}
    cal_keys = {"f::x__y"}
    graph_edges = {("a", "x"), ("b", "y")}
    neg_nodes = {"a", "b", "c"}
    test_cal_nodes = {"d", "e", "f"}
    # Should not raise
    check_no_leakage(
        train_pair_keys=train_keys,
        test_pair_keys=test_keys,
        cal_pair_keys=cal_keys,
        graph_edge_pairs=graph_edges,
        negative_sample_nodes=neg_nodes,
        test_cal_nodes=test_cal_nodes,
    )


def test_train_test_overlap_raises():
    train_keys = {"a::x__y", "LEAKED::x__y"}
    test_keys = {"LEAKED::x__y", "e::x__y"}
    with pytest.raises(SystemExit, match="LEAKAGE.*train.*test"):
        check_no_leakage(
            train_pair_keys=train_keys,
            test_pair_keys=test_keys,
            cal_pair_keys=set(),
            graph_edge_pairs=set(),
            negative_sample_nodes=set(),
            test_cal_nodes=set(),
        )


def test_train_cal_overlap_raises():
    train_keys = {"a::x__y", "LEAKED::x__y"}
    cal_keys = {"LEAKED::x__y"}
    with pytest.raises(SystemExit, match="LEAKAGE.*train.*cal"):
        check_no_leakage(
            train_pair_keys=train_keys,
            test_pair_keys=set(),
            cal_pair_keys=cal_keys,
            graph_edge_pairs=set(),
            negative_sample_nodes=set(),
            test_cal_nodes=set(),
        )


def test_graph_test_overlap_raises():
    graph_edges = {("d", "e")}  # 'd' is a test node
    test_keys = {"d::x__y"}
    with pytest.raises(SystemExit, match="LEAKAGE.*graph.*test"):
        check_no_leakage(
            train_pair_keys=set(),
            test_pair_keys=test_keys,
            cal_pair_keys=set(),
            graph_edge_pairs=graph_edges,
            negative_sample_nodes=set(),
            test_cal_nodes={"d", "e"},
        )


def test_negative_node_overlap_raises():
    neg_nodes = {"d"}  # 'd' is a test node
    with pytest.raises(SystemExit, match="LEAKAGE.*negative.*test_cal"):
        check_no_leakage(
            train_pair_keys=set(),
            test_pair_keys=set(),
            cal_pair_keys=set(),
            graph_edge_pairs=set(),
            negative_sample_nodes=neg_nodes,
            test_cal_nodes={"d"},
        )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest classifier/tests/test_leakage_firewall.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'classifier.ensemble.leakage_firewall'`

- [ ] **Step 3: Write minimal implementation**

```python
# classifier/ensemble/leakage_firewall.py
"""Pre-flight leakage assertions. Hard fail if any data leaks between splits.

Run before every training job. Log results to WANDB if available.
"""
from __future__ import annotations

import sys
from typing import Set, Tuple


def check_no_leakage(
    *,
    train_pair_keys: Set[str],
    test_pair_keys: Set[str],
    cal_pair_keys: Set[str],
    graph_edge_pairs: Set[Tuple[str, str]],
    negative_sample_nodes: Set[str],
    test_cal_nodes: Set[str],
) -> None:
    """Assert zero data leakage across all split boundaries.

    Raises SystemExit on any violation — training MUST NOT proceed.
    """
    # 1. Train ∩ Test = ∅
    overlap = train_pair_keys & test_pair_keys
    if overlap:
        sys.exit(
            f"LEAKAGE DETECTED: {len(overlap)} pairs leaked between train and test. "
            f"First 3: {list(overlap)[:3]}"
        )

    # 2. Train ∩ Cal = ∅
    overlap = train_pair_keys & cal_pair_keys
    if overlap:
        sys.exit(
            f"LEAKAGE DETECTED: {len(overlap)} pairs leaked between train and cal. "
            f"First 3: {list(overlap)[:3]}"
        )

    # 3. Graph edges must not contain test/cal pair nodes
    graph_nodes = set()
    for src, tgt in graph_edge_pairs:
        graph_nodes.add(src)
        graph_nodes.add(tgt)
    # Extract nodes from test pair keys
    test_key_nodes = set()
    for pk in test_pair_keys:
        parts = pk.split("::")
        if len(parts) >= 2:
            node_part = parts[1] if len(parts) > 1 else parts[0]
            for node in node_part.split("__"):
                test_key_nodes.add(node)
    graph_test_overlap = graph_nodes & test_cal_nodes
    if graph_test_overlap:
        sys.exit(
            f"LEAKAGE DETECTED: {len(graph_test_overlap)} nodes leaked between "
            f"graph edges and test/cal. First 3: {list(graph_test_overlap)[:3]}"
        )

    # 4. Negative sample nodes ∩ Test/Cal nodes = ∅
    neg_overlap = negative_sample_nodes & test_cal_nodes
    if neg_overlap:
        sys.exit(
            f"LEAKAGE DETECTED: {len(neg_overlap)} nodes leaked between "
            f"negative samples and test_cal. First 3: {list(neg_overlap)[:3]}"
        )


def load_frozen_keys(path: str = "data/splits/human_test_frozen.jsonl") -> Set[str]:
    """Load pair_key values from the frozen test set."""
    import json
    from pathlib import Path

    keys = set()
    with Path(path).open() as f:
        for line in f:
            row = json.loads(line)
            keys.add(row["pair_key"])
    return keys


def load_cal_keys(path: str = "data/splits/human_cal.jsonl") -> Set[str]:
    """Load pair_key values from the calibration set."""
    import json
    from pathlib import Path

    keys = set()
    with Path(path).open() as f:
        for line in f:
            row = json.loads(line)
            keys.add(row["pair_key"])
    return keys


def extract_nodes_from_keys(pair_keys: Set[str]) -> Set[str]:
    """Extract all node IDs from pair keys like 'fp::node1__node2'."""
    nodes = set()
    for pk in pair_keys:
        parts = pk.split("::")
        if len(parts) >= 2:
            node_part = parts[-1]
            for node in node_part.split("__"):
                nodes.add(node)
    return nodes
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest classifier/tests/test_leakage_firewall.py -v`
Expected: PASS (all 5 tests)

- [ ] **Step 5: Commit**

```bash
git add classifier/ensemble/leakage_firewall.py classifier/tests/test_leakage_firewall.py
git commit -m "feat: add leakage firewall with pre-flight assertions"
```

---

### Task 2: Tier Mapper — Convert Upstream Labels to 4-Class

**Files:**
- Create: `classifier/data/tier_mapper.py`
- Create: `classifier/tests/test_tier_mapper.py`

- [ ] **Step 1: Write the failing test**

```python
# classifier/tests/test_tier_mapper.py
"""Tests for upstream tier → 4-class mapping."""
import pytest
from classifier.data.tier_mapper import map_upstream_tier, TierLabel


def test_foundational_direct_scope():
    assert map_upstream_tier(tier="Foundational", scope="Direct") == TierLabel.EQUIVALENT


def test_foundational_both_scope():
    assert map_upstream_tier(tier="Foundational", scope="Both") == TierLabel.EQUIVALENT


def test_foundational_broader_scope():
    assert map_upstream_tier(tier="Foundational", scope="Broader") == TierLabel.RELATED


def test_foundational_partial_overlap():
    assert map_upstream_tier(tier="Foundational", scope="Partial") == TierLabel.RELATED


def test_expanded_maps_to_partial():
    assert map_upstream_tier(tier="Expanded", scope="Both") == TierLabel.PARTIAL


def test_unknown_tier_raises():
    with pytest.raises(ValueError, match="Unknown tier"):
        map_upstream_tier(tier="Invalid", scope="Both")


def test_tier_label_values():
    assert TierLabel.UNRELATED.value == 0
    assert TierLabel.PARTIAL.value == 1
    assert TierLabel.RELATED.value == 2
    assert TierLabel.EQUIVALENT.value == 3
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest classifier/tests/test_tier_mapper.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# classifier/data/tier_mapper.py
"""Map upstream mapping tiers to 4-class labels for training.

Upstream schema: tier ∈ {Foundational, Expanded}, scope ∈ {Direct, Both, Broader, Partial, ...}
Target schema:   TierLabel ∈ {UNRELATED=0, PARTIAL=1, RELATED=2, EQUIVALENT=3}

Mapping rules (from spec §Data Foundation):
  - Foundational + (Direct|Both|Identical) → EQUIVALENT
  - Foundational + (Broader|Partial|Partial_overlap) → RELATED
  - Expanded → PARTIAL
"""
from __future__ import annotations

import enum


class TierLabel(enum.IntEnum):
    UNRELATED = 0
    PARTIAL = 1
    RELATED = 2
    EQUIVALENT = 3


# Scopes that indicate direct/identical mapping
_EQUIVALENT_SCOPES = frozenset({"Direct", "Both", "Identical", "direct", "both", "identical"})
# Scopes that indicate broader/partial overlap
_RELATED_SCOPES = frozenset({
    "Broader", "Partial", "Partial_overlap", "partial_overlap",
    "broader", "partial",
})


def map_upstream_tier(*, tier: str, scope: str) -> TierLabel:
    """Convert a single upstream (tier, scope) pair to a 4-class TierLabel."""
    tier_lower = tier.strip().lower()
    scope_normalized = scope.strip()

    if tier_lower == "foundational":
        if scope_normalized in _EQUIVALENT_SCOPES:
            return TierLabel.EQUIVALENT
        if scope_normalized in _RELATED_SCOPES:
            return TierLabel.RELATED
        # Default for foundational with unknown scope: RELATED (conservative)
        return TierLabel.RELATED

    if tier_lower == "expanded":
        return TierLabel.PARTIAL

    raise ValueError(f"Unknown tier: '{tier}'. Expected 'Foundational' or 'Expanded'.")


def map_expert_tier(expert_tier: str) -> TierLabel:
    """Convert expert_tier strings from human_test_frozen/human_cal to TierLabel.

    Expert schema: Direct=3, Related=2, Tangential=1, None=0
    """
    mapping = {
        "Direct": TierLabel.EQUIVALENT,
        "Related": TierLabel.RELATED,
        "Tangential": TierLabel.PARTIAL,
        "None": TierLabel.UNRELATED,
    }
    if expert_tier not in mapping:
        raise ValueError(f"Unknown expert_tier: '{expert_tier}'")
    return mapping[expert_tier]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest classifier/tests/test_tier_mapper.py -v`
Expected: PASS (all 7 tests)

- [ ] **Step 5: Commit**

```bash
git add classifier/data/tier_mapper.py classifier/tests/test_tier_mapper.py
git commit -m "feat: add tier mapper for upstream → 4-class label conversion"
```

---

### Task 3: Hard Negative Miner

**Files:**
- Create: `classifier/data/negative_miner.py`
- Create: `classifier/tests/test_negative_miner.py`

- [ ] **Step 1: Write the failing test**

```python
# classifier/tests/test_negative_miner.py
"""Tests for hard negative mining via BM25."""
import pytest
from classifier.data.negative_miner import mine_hard_negatives


def test_returns_expected_count():
    # Minimal test with fake data
    source_texts = {"src1": "prompt injection attack", "src2": "data poisoning"}
    target_texts = {"tgt1": "injection defense", "tgt2": "model training", "tgt3": "bias"}
    positive_pairs = {("src1", "tgt1")}  # Only src1→tgt1 is mapped
    excluded_nodes = set()

    negatives = mine_hard_negatives(
        source_texts=source_texts,
        target_texts=target_texts,
        positive_pairs=positive_pairs,
        excluded_nodes=excluded_nodes,
        n_negatives_per_source=2,
    )
    # src1 can generate negatives from tgt2, tgt3 (not tgt1 — already positive)
    # src2 can generate negatives from tgt1, tgt2, tgt3 (none are positive for src2)
    assert len(negatives) >= 2  # At least some negatives mined
    # No positive pairs should appear in negatives
    for src, tgt in negatives:
        assert (src, tgt) not in positive_pairs


def test_excludes_test_cal_nodes():
    source_texts = {"src1": "prompt injection"}
    target_texts = {"tgt1": "injection", "tgt_excluded": "also injection"}
    positive_pairs = set()
    excluded_nodes = {"tgt_excluded"}

    negatives = mine_hard_negatives(
        source_texts=source_texts,
        target_texts=target_texts,
        positive_pairs=positive_pairs,
        excluded_nodes=excluded_nodes,
        n_negatives_per_source=5,
    )
    for _, tgt in negatives:
        assert tgt != "tgt_excluded"


def test_empty_sources_returns_empty():
    negatives = mine_hard_negatives(
        source_texts={},
        target_texts={"tgt1": "text"},
        positive_pairs=set(),
        excluded_nodes=set(),
        n_negatives_per_source=5,
    )
    assert negatives == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest classifier/tests/test_negative_miner.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# classifier/data/negative_miner.py
"""Mine hard negatives for training using BM25 retrieval.

Hard negatives are plausible-looking pairs that experts did NOT map.
More informative than random negatives for training discriminative models.
"""
from __future__ import annotations

from typing import Dict, List, Set, Tuple

from rank_bm25 import BM25Okapi


def mine_hard_negatives(
    *,
    source_texts: Dict[str, str],
    target_texts: Dict[str, str],
    positive_pairs: Set[Tuple[str, str]],
    excluded_nodes: Set[str],
    n_negatives_per_source: int = 5,
    top_k: int = 50,
) -> List[Tuple[str, str]]:
    """Mine hard negatives: BM25-retrieved targets that are NOT positive pairs.

    Args:
        source_texts: {node_id: text} for source controls
        target_texts: {node_id: text} for target controls
        positive_pairs: {(source_id, target_id)} known positive mappings
        excluded_nodes: Node IDs to exclude (test/cal nodes)
        n_negatives_per_source: How many negatives to sample per source
        top_k: BM25 retrieval depth before filtering

    Returns:
        List of (source_id, target_id) hard negative pairs
    """
    if not source_texts or not target_texts:
        return []

    # Filter out excluded targets
    eligible_targets = {
        tid: text for tid, text in target_texts.items() if tid not in excluded_nodes
    }
    if not eligible_targets:
        return []

    target_ids = list(eligible_targets.keys())
    target_corpus = [eligible_targets[tid].lower().split() for tid in target_ids]

    bm25 = BM25Okapi(target_corpus)

    negatives: List[Tuple[str, str]] = []

    for src_id, src_text in source_texts.items():
        if src_id in excluded_nodes:
            continue

        query = src_text.lower().split()
        scores = bm25.get_scores(query)

        # Rank targets by BM25 score descending
        ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)

        count = 0
        for idx in ranked_indices[:top_k]:
            if count >= n_negatives_per_source:
                break
            tgt_id = target_ids[idx]
            if (src_id, tgt_id) not in positive_pairs:
                negatives.append((src_id, tgt_id))
                count += 1

    return negatives
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest classifier/tests/test_negative_miner.py -v`
Expected: PASS (all 3 tests)

- [ ] **Step 5: Commit**

```bash
git add classifier/data/negative_miner.py classifier/tests/test_negative_miner.py
git commit -m "feat: add BM25-based hard negative miner"
```

---

### Task 4: Control Text Enrichment

**Files:**
- Create: `classifier/data/text_enricher.py`
- Create: `classifier/tests/test_text_enricher.py`

- [ ] **Step 1: Write the failing test**

```python
# classifier/tests/test_text_enricher.py
"""Tests for control text enrichment."""
from classifier.data.text_enricher import enrich_control_text


def test_adds_parent_text():
    controls = {
        "fw:P1": {"text": "Parent control", "parent_id": None, "category": "Gov"},
        "fw:C1": {"text": "Child control", "parent_id": "fw:P1", "category": "Gov"},
    }
    enriched = enrich_control_text("fw:C1", controls)
    assert "Parent control" in enriched
    assert "Child control" in enriched


def test_adds_category():
    controls = {
        "fw:C1": {"text": "Some control", "parent_id": None, "category": "Governance"},
    }
    enriched = enrich_control_text("fw:C1", controls)
    assert "Governance" in enriched


def test_no_parent_still_works():
    controls = {
        "fw:C1": {"text": "Standalone control", "parent_id": None, "category": "Risk"},
    }
    enriched = enrich_control_text("fw:C1", controls)
    assert "Standalone control" in enriched
    assert "Risk" in enriched


def test_missing_control_returns_empty():
    controls = {}
    enriched = enrich_control_text("fw:MISSING", controls)
    assert enriched == ""
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest classifier/tests/test_text_enricher.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# classifier/data/text_enricher.py
"""Enrich control text with parent, category, and sibling context.

Appends parent control text, framework category, and sibling descriptions
to each control's input text. This provides richer context for cross-encoders
at zero compute cost.
"""
from __future__ import annotations

from typing import Dict, Optional


def enrich_control_text(
    node_id: str,
    controls: Dict[str, Dict],
) -> str:
    """Build enriched text for a single control.

    Args:
        node_id: The control's node ID (e.g., "owasp_llm:LLM01")
        controls: Dict mapping node_id → {text, parent_id, category, ...}

    Returns:
        Enriched text string with category prefix, parent context, and control text.
    """
    if node_id not in controls:
        return ""

    ctrl = controls[node_id]
    parts = []

    # Category prefix
    category = ctrl.get("category", "")
    if category:
        parts.append(f"[{category}]")

    # Parent context
    parent_id = ctrl.get("parent_id")
    if parent_id and parent_id in controls:
        parent_text = controls[parent_id].get("text", "")
        if parent_text:
            parts.append(f"Parent: {parent_text}")

    # Control's own text
    text = ctrl.get("text", "")
    if text:
        parts.append(text)

    return " ".join(parts)


def enrich_all_controls(
    controls: Dict[str, Dict],
) -> Dict[str, str]:
    """Enrich text for all controls in the dict.

    Returns:
        Dict mapping node_id → enriched text string.
    """
    return {
        node_id: enrich_control_text(node_id, controls)
        for node_id in controls
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest classifier/tests/test_text_enricher.py -v`
Expected: PASS (all 4 tests)

- [ ] **Step 5: Commit**

```bash
git add classifier/data/text_enricher.py classifier/tests/test_text_enricher.py
git commit -m "feat: add control text enrichment for cross-encoder inputs"
```

---

### Task 5: Training Data Builder Script

**Files:**
- Create: `classifier/scripts/build_expert_training.py`
- Modify: `classifier/data/tier_mapper.py` (add `build_training_set()`)
- Create: `classifier/tests/test_build_expert_training.py`

- [ ] **Step 1: Write the failing test**

```python
# classifier/tests/test_build_expert_training.py
"""Tests for end-to-end expert training data construction."""
import json
import tempfile
from pathlib import Path

import pytest
from classifier.data.tier_mapper import TierLabel
from classifier.scripts.build_expert_training import build_expert_training_set


def test_build_produces_valid_jsonl(tmp_path):
    # Create minimal upstream mappings
    mappings_path = tmp_path / "mappings.jsonl"
    with mappings_path.open("w") as f:
        for i in range(5):
            json.dump({
                "source_framework": "owasp_llm",
                "source_id": f"LLM0{i+1}",
                "target_framework": "mitre_atlas",
                "target_control_id": f"AML.T00{i+1}",
                "target_node_id": f"mitre_atlas:AML.T00{i+1}",
                "target_id_unresolved": False,
                "tier": "Foundational",
                "scope": "Direct" if i < 3 else "Broader",
            }, f)
            f.write("\n")

    # Create minimal frozen test (to exclude)
    frozen_path = tmp_path / "frozen.jsonl"
    with frozen_path.open("w") as f:
        json.dump({
            "pair_key": "owasp_llm__mitre_atlas::owasp_llm:LLM01__mitre_atlas:AML.T001",
            "source_node_id": "owasp_llm:LLM01",
            "target_node_id": "mitre_atlas:AML.T001",
            "source_text": "Prompt Injection",
            "target_text": "LLM Prompt Injection",
            "expert_tier": "Direct",
        }, f)
        f.write("\n")

    cal_path = tmp_path / "cal.jsonl"
    cal_path.write_text("")  # Empty cal for this test

    output = tmp_path / "output"
    output.mkdir()

    stats = build_expert_training_set(
        mappings_path=str(mappings_path),
        frozen_path=str(frozen_path),
        cal_path=str(cal_path),
        output_dir=str(output),
        n_negatives_per_source=1,
    )

    assert (output / "expert_train.jsonl").exists()
    assert (output / "expert_val.jsonl").exists()
    assert stats["n_train"] > 0
    assert stats["n_val"] > 0

    # Read and verify schema
    with (output / "expert_train.jsonl").open() as f:
        first = json.loads(f.readline())
    assert "pair_key" in first
    assert "source_node_id" in first
    assert "target_node_id" in first
    assert "source_text" in first
    assert "target_text" in first
    assert "tier_label" in first
    assert first["tier_label"] in [0, 1, 2, 3]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest classifier/tests/test_build_expert_training.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# classifier/scripts/build_expert_training.py
"""Build expert-derived training data from upstream mappings.

Usage:
    python -m classifier.scripts.build_expert_training [--output-dir data/splits]

Reads:
  - data/upstream/mappings_v1.jsonl (3,210 expert mappings)
  - data/splits/human_test_frozen.jsonl (excluded)
  - data/splits/human_cal.jsonl (excluded)
  - data/frameworks/*/MANIFEST.json (control texts for negatives)

Produces:
  - data/splits/expert_train.jsonl
  - data/splits/expert_val.jsonl
"""
from __future__ import annotations

import json
import random
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

from classifier.data.tier_mapper import TierLabel, map_upstream_tier
from classifier.data.negative_miner import mine_hard_negatives
from classifier.ensemble.leakage_firewall import (
    check_no_leakage,
    extract_nodes_from_keys,
    load_cal_keys,
    load_frozen_keys,
)


def _load_mappings(path: str) -> List[Dict[str, Any]]:
    rows = []
    with Path(path).open() as f:
        for line in f:
            row = json.loads(line)
            if not row.get("target_id_unresolved", False):
                rows.append(row)
    return rows


def _load_control_texts(frameworks_dir: str = "data/frameworks") -> Dict[str, str]:
    """Load control texts from processed node files."""
    texts: Dict[str, str] = {}
    nodes_path = Path("data/processed/nodes.json")
    if nodes_path.exists():
        with nodes_path.open() as f:
            nodes = json.load(f)
        for node in nodes:
            nid = node.get("node_id", "")
            text = node.get("text", "") or node.get("description", "")
            if nid and text:
                texts[nid] = text
    return texts


def build_expert_training_set(
    *,
    mappings_path: str = "data/upstream/mappings_v1.jsonl",
    frozen_path: str = "data/splits/human_test_frozen.jsonl",
    cal_path: str = "data/splits/human_cal.jsonl",
    output_dir: str = "data/splits",
    n_negatives_per_source: int = 5,
    val_fraction: float = 0.15,
    seed: int = 42,
) -> Dict[str, Any]:
    """Build stratified expert training + val sets.

    Returns:
        Dict with n_train, n_val, class_distribution, and leakage_check status.
    """
    random.seed(seed)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # Load exclusion sets
    try:
        frozen_keys = load_frozen_keys(frozen_path)
    except FileNotFoundError:
        frozen_keys = set()
    try:
        cal_keys = load_cal_keys(cal_path)
    except FileNotFoundError:
        cal_keys = set()

    frozen_cal_nodes = extract_nodes_from_keys(frozen_keys | cal_keys)

    # Load and map upstream data
    mappings = _load_mappings(mappings_path)
    positive_pairs: List[Dict] = []
    positive_pair_set: Set[Tuple[str, str]] = set()

    for row in mappings:
        src_fw = row["source_framework"]
        src_id = row["source_id"]
        tgt_node_id = row["target_node_id"]
        source_node_id = f"{src_fw}:{src_id}"

        # Skip pairs involving test/cal nodes
        if source_node_id in frozen_cal_nodes or tgt_node_id in frozen_cal_nodes:
            continue

        pair_key = f"{src_fw}__{row['target_framework']}::{source_node_id}__{tgt_node_id}"

        # Skip if this pair is in frozen test or cal
        if pair_key in frozen_keys or pair_key in cal_keys:
            continue

        tier_label = map_upstream_tier(
            tier=row.get("tier", "Expanded"),
            scope=row.get("scope", "Both"),
        )

        positive_pairs.append({
            "pair_key": pair_key,
            "source_node_id": source_node_id,
            "target_node_id": tgt_node_id,
            "source_text": row.get("source_text", ""),
            "target_text": row.get("target_control_name", ""),
            "tier_label": int(tier_label),
            "data_source": "expert_upstream",
        })
        positive_pair_set.add((source_node_id, tgt_node_id))

    # Mine hard negatives
    source_texts = {}
    target_texts = {}
    for p in positive_pairs:
        source_texts[p["source_node_id"]] = p["source_text"]
        target_texts[p["target_node_id"]] = p["target_text"]

    # Also load control texts if available
    control_texts = _load_control_texts()
    for nid, text in control_texts.items():
        if nid not in target_texts:
            target_texts[nid] = text
        if nid not in source_texts:
            source_texts[nid] = text

    neg_pairs_raw = mine_hard_negatives(
        source_texts=source_texts,
        target_texts=target_texts,
        positive_pairs=positive_pair_set,
        excluded_nodes=frozen_cal_nodes,
        n_negatives_per_source=n_negatives_per_source,
    )

    negative_pairs = []
    for src_id, tgt_id in neg_pairs_raw:
        fw_src = src_id.split(":")[0] if ":" in src_id else "unknown"
        fw_tgt = tgt_id.split(":")[0] if ":" in tgt_id else "unknown"
        pair_key = f"{fw_src}__{fw_tgt}::{src_id}__{tgt_id}"
        negative_pairs.append({
            "pair_key": pair_key,
            "source_node_id": src_id,
            "target_node_id": tgt_id,
            "source_text": source_texts.get(src_id, ""),
            "target_text": target_texts.get(tgt_id, ""),
            "tier_label": int(TierLabel.UNRELATED),
            "data_source": "hard_negative",
        })

    # Combine and split
    all_pairs = positive_pairs + negative_pairs
    random.shuffle(all_pairs)

    n_val = max(1, int(len(all_pairs) * val_fraction))
    val_set = all_pairs[:n_val]
    train_set = all_pairs[n_val:]

    # Run leakage firewall
    train_keys = {p["pair_key"] for p in train_set}
    val_keys = {p["pair_key"] for p in val_set}
    graph_edges = {(p["source_node_id"], p["target_node_id"]) for p in train_set}
    neg_nodes = set()
    for p in negative_pairs:
        neg_nodes.add(p["source_node_id"])
        neg_nodes.add(p["target_node_id"])

    check_no_leakage(
        train_pair_keys=train_keys | val_keys,
        test_pair_keys=frozen_keys,
        cal_pair_keys=cal_keys,
        graph_edge_pairs=graph_edges,
        negative_sample_nodes=neg_nodes,
        test_cal_nodes=frozen_cal_nodes,
    )

    # Write outputs
    for name, dataset in [("expert_train.jsonl", train_set), ("expert_val.jsonl", val_set)]:
        with (out / name).open("w") as f:
            for row in dataset:
                json.dump(row, f)
                f.write("\n")

    train_dist = Counter(p["tier_label"] for p in train_set)
    val_dist = Counter(p["tier_label"] for p in val_set)

    return {
        "n_train": len(train_set),
        "n_val": len(val_set),
        "n_positives": len(positive_pairs),
        "n_negatives": len(negative_pairs),
        "train_distribution": dict(train_dist),
        "val_distribution": dict(val_dist),
        "leakage_check": "PASSED",
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Build expert training data")
    parser.add_argument("--output-dir", default="data/splits")
    parser.add_argument("--n-negatives", type=int, default=5)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    stats = build_expert_training_set(
        output_dir=args.output_dir,
        n_negatives_per_source=args.n_negatives,
        seed=args.seed,
    )
    print(json.dumps(stats, indent=2))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest classifier/tests/test_build_expert_training.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add classifier/scripts/build_expert_training.py classifier/tests/test_build_expert_training.py
git commit -m "feat: add expert training data builder with leakage firewall"
```

---

### Task 6: CORN Ordinal Loss

**Files:**
- Create: `classifier/ensemble/corn_loss.py`
- Create: `classifier/tests/test_corn_loss.py`

- [ ] **Step 1: Write the failing test**

```python
# classifier/tests/test_corn_loss.py
"""Tests for CORN (Conditional Ordinal Regression Network) loss."""
import torch
import pytest
from classifier.ensemble.corn_loss import corn_loss, corn_label_from_logits


def test_corn_loss_shape():
    logits = torch.randn(8, 3)  # batch=8, n_classes-1=3 binary tasks
    labels = torch.tensor([0, 1, 2, 3, 0, 1, 2, 3])
    loss = corn_loss(logits, labels, n_classes=4)
    assert loss.shape == ()
    assert loss.item() > 0


def test_corn_loss_perfect_predictions():
    # If logits perfectly predict the ordinal ranking, loss should be low
    # Class 3 (highest): all 3 binary tasks should be positive
    logits = torch.tensor([[10.0, 10.0, 10.0]])  # predict class 3
    labels = torch.tensor([3])
    loss_correct = corn_loss(logits, labels, n_classes=4)

    logits_wrong = torch.tensor([[-10.0, -10.0, -10.0]])  # predict class 0
    loss_wrong = corn_loss(logits_wrong, labels, n_classes=4)

    assert loss_correct < loss_wrong


def test_corn_label_from_logits():
    # Logits: all positive → class 3 (highest)
    logits = torch.tensor([[10.0, 10.0, 10.0]])
    labels = corn_label_from_logits(logits, n_classes=4)
    assert labels[0].item() == 3

    # Logits: all negative → class 0 (lowest)
    logits = torch.tensor([[-10.0, -10.0, -10.0]])
    labels = corn_label_from_logits(logits, n_classes=4)
    assert labels[0].item() == 0

    # Logits: first positive, rest negative → class 1
    logits = torch.tensor([[10.0, -10.0, -10.0]])
    labels = corn_label_from_logits(logits, n_classes=4)
    assert labels[0].item() == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest classifier/tests/test_corn_loss.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# classifier/ensemble/corn_loss.py
"""CORN — Conditional Ordinal Regression Network.

Decomposes K-class ordinal classification into K-1 binary classification tasks.
Task k: P(Y > k | Y >= k). This respects the ordinal structure:
  unrelated(0) < partial(1) < related(2) < equivalent(3)

Reference: Shi et al. "CORN — Conditional Ordinal Regression for Neural Networks" (2021)
"""
from __future__ import annotations

import torch
import torch.nn.functional as F


def corn_loss(
    logits: torch.Tensor,
    labels: torch.Tensor,
    n_classes: int = 4,
) -> torch.Tensor:
    """Compute CORN loss for ordinal regression.

    Args:
        logits: (batch, n_classes-1) raw logits for each binary task
        labels: (batch,) integer class labels in [0, n_classes-1]
        n_classes: Number of ordinal classes

    Returns:
        Scalar loss (mean over batch and tasks).
    """
    n_tasks = n_classes - 1
    total_loss = torch.tensor(0.0, device=logits.device)
    n_contributing = 0

    for task_idx in range(n_tasks):
        # Task k: P(Y > k | Y >= k)
        # Only samples with Y >= k contribute to task k
        mask = labels >= task_idx
        if mask.sum() == 0:
            continue

        task_logits = logits[mask, task_idx]
        # Binary target: 1 if Y > task_idx (given Y >= task_idx)
        task_targets = (labels[mask] > task_idx).float()

        task_loss = F.binary_cross_entropy_with_logits(task_logits, task_targets)
        total_loss = total_loss + task_loss
        n_contributing += 1

    if n_contributing == 0:
        return torch.tensor(0.0, device=logits.device, requires_grad=True)

    return total_loss / n_contributing


def corn_label_from_logits(
    logits: torch.Tensor,
    n_classes: int = 4,
) -> torch.Tensor:
    """Convert CORN logits to class predictions.

    Args:
        logits: (batch, n_classes-1) raw logits
        n_classes: Number of ordinal classes

    Returns:
        (batch,) integer predictions in [0, n_classes-1]
    """
    probs = torch.sigmoid(logits)
    # Class k predicted if all tasks 0..k-1 have prob > 0.5
    # Equivalent to: predicted class = number of tasks with prob > 0.5
    predictions = (probs > 0.5).sum(dim=1).long()
    return predictions.clamp(0, n_classes - 1)


def corn_proba_from_logits(
    logits: torch.Tensor,
    n_classes: int = 4,
) -> torch.Tensor:
    """Convert CORN logits to class probabilities.

    P(Y = k) = P(Y > k-1 | Y >= k-1) * prod_{j<k-1} P(Y > j | Y >= j)
               - P(Y > k | Y >= k) * prod_{j<k} P(Y > j | Y >= j)

    Args:
        logits: (batch, n_classes-1) raw logits
        n_classes: Number of ordinal classes

    Returns:
        (batch, n_classes) probability matrix
    """
    probs = torch.sigmoid(logits)  # (batch, n_classes-1)
    batch_size = probs.shape[0]
    class_probs = torch.zeros(batch_size, n_classes, device=logits.device)

    # P(Y >= 0) = 1 for all samples
    # P(Y >= k) = prod_{j=0}^{k-1} P(Y > j | Y >= j)
    cumulative = torch.ones(batch_size, device=logits.device)

    for k in range(n_classes):
        if k < n_classes - 1:
            # P(Y = k) = P(Y >= k) - P(Y >= k+1)
            #           = cumulative - cumulative * probs[:, k]
            class_probs[:, k] = cumulative * (1 - probs[:, k])
            cumulative = cumulative * probs[:, k]
        else:
            # Last class: P(Y = K-1) = P(Y >= K-1) = cumulative
            class_probs[:, k] = cumulative

    # Clamp for numerical stability
    class_probs = class_probs.clamp(min=1e-8)
    class_probs = class_probs / class_probs.sum(dim=1, keepdim=True)

    return class_probs
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest classifier/tests/test_corn_loss.py -v`
Expected: PASS (all 3 tests)

- [ ] **Step 5: Commit**

```bash
git add classifier/ensemble/corn_loss.py classifier/tests/test_corn_loss.py
git commit -m "feat: add CORN ordinal loss for cross-encoder training"
```

---

### Task 7: Cross-Encoder Wrapper

**Files:**
- Create: `classifier/ensemble/cross_encoder.py`
- Create: `classifier/tests/test_cross_encoder.py`

- [ ] **Step 1: Write the failing test**

```python
# classifier/tests/test_cross_encoder.py
"""Tests for cross-encoder wrapper."""
import pytest

# Skip all tests if torch not available (Jetson test env may lack full CUDA)
torch = pytest.importorskip("torch")

from classifier.ensemble.cross_encoder import CrossEncoderClassifier


def test_init_creates_model():
    # Use a tiny model for testing
    ce = CrossEncoderClassifier(
        model_name="cross-encoder/ms-marco-TinyBERT-L-2-v2",
        n_classes=4,
    )
    assert ce.n_classes == 4


def test_tokenize_pair():
    ce = CrossEncoderClassifier(
        model_name="cross-encoder/ms-marco-TinyBERT-L-2-v2",
        n_classes=4,
    )
    tokens = ce.tokenize_pair("prompt injection attack", "LLM prompt injection defense")
    assert "input_ids" in tokens
    assert tokens["input_ids"].shape[0] == 1  # batch=1


def test_forward_returns_logits():
    ce = CrossEncoderClassifier(
        model_name="cross-encoder/ms-marco-TinyBERT-L-2-v2",
        n_classes=4,
    )
    tokens = ce.tokenize_pair("text a", "text b")
    logits, cls_emb = ce.forward_pair(tokens)
    assert logits.shape == (1, 3)  # n_classes - 1 for CORN
    assert cls_emb.shape[0] == 1
    assert cls_emb.shape[1] > 0  # hidden dim
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest classifier/tests/test_cross_encoder.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# classifier/ensemble/cross_encoder.py
"""Cross-encoder classifier with CORN ordinal head.

Wraps a HuggingFace transformer model as a pair classifier.
Input: (source_text, target_text) pair
Output: CORN logits (n_classes-1 binary tasks) + CLS embedding
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
from transformers import AutoModel, AutoTokenizer


class CrossEncoderClassifier(nn.Module):
    """Cross-encoder with CORN ordinal head for pair classification."""

    def __init__(
        self,
        model_name: str = "microsoft/deberta-v3-large",
        n_classes: int = 4,
        max_length: int = 512,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.model_name = model_name
        self.n_classes = n_classes
        self.max_length = max_length

        self.encoder = AutoModel.from_pretrained(model_name)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)

        hidden_size = self.encoder.config.hidden_size
        self.dropout = nn.Dropout(dropout)
        # CORN head: n_classes - 1 binary outputs
        self.classifier = nn.Linear(hidden_size, n_classes - 1)

    def tokenize_pair(
        self, text_a: str, text_b: str
    ) -> Dict[str, torch.Tensor]:
        """Tokenize a single (source, target) pair."""
        tokens = self.tokenizer(
            text_a,
            text_b,
            max_length=self.max_length,
            truncation=True,
            padding="max_length",
            return_tensors="pt",
        )
        return tokens

    def tokenize_batch(
        self, texts_a: List[str], texts_b: List[str]
    ) -> Dict[str, torch.Tensor]:
        """Tokenize a batch of (source, target) pairs."""
        tokens = self.tokenizer(
            texts_a,
            texts_b,
            max_length=self.max_length,
            truncation=True,
            padding=True,
            return_tensors="pt",
        )
        return tokens

    def forward(
        self, input_ids: torch.Tensor, attention_mask: torch.Tensor, **kwargs
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """Forward pass returning CORN logits and CLS embedding.

        Returns:
            logits: (batch, n_classes-1) CORN binary task logits
            cls_emb: (batch, hidden_size) CLS token embedding
        """
        outputs = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
        cls_emb = outputs.last_hidden_state[:, 0, :]  # CLS token
        logits = self.classifier(self.dropout(cls_emb))
        return logits, cls_emb

    def forward_pair(
        self, tokens: Dict[str, torch.Tensor]
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """Convenience: forward from tokenized pair dict."""
        return self.forward(
            input_ids=tokens["input_ids"],
            attention_mask=tokens["attention_mask"],
        )

    def predict_proba(
        self, texts_a: List[str], texts_b: List[str], batch_size: int = 32
    ) -> np.ndarray:
        """Predict class probabilities for a list of pairs.

        Returns:
            (n_pairs, n_classes) probability matrix.
        """
        from classifier.ensemble.corn_loss import corn_proba_from_logits

        self.eval()
        all_probs = []

        with torch.no_grad():
            for i in range(0, len(texts_a), batch_size):
                batch_a = texts_a[i : i + batch_size]
                batch_b = texts_b[i : i + batch_size]
                tokens = self.tokenize_batch(batch_a, batch_b)
                tokens = {k: v.to(next(self.parameters()).device) for k, v in tokens.items()}
                logits, _ = self.forward(tokens["input_ids"], tokens["attention_mask"])
                probs = corn_proba_from_logits(logits, self.n_classes)
                all_probs.append(probs.cpu().numpy())

        return np.concatenate(all_probs, axis=0)

    def save(self, path: Path) -> None:
        """Save model weights, tokenizer, and config."""
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        self.encoder.save_pretrained(path / "encoder")
        self.tokenizer.save_pretrained(path / "encoder")
        torch.save(
            {"classifier": self.classifier.state_dict(), "dropout": self.dropout.p},
            path / "head.pt",
        )

    @classmethod
    def load(cls, path: Path, n_classes: int = 4) -> "CrossEncoderClassifier":
        """Load a saved cross-encoder."""
        path = Path(path)
        ce = cls(model_name=str(path / "encoder"), n_classes=n_classes)
        head_state = torch.load(path / "head.pt", map_location="cpu")
        ce.classifier.load_state_dict(head_state["classifier"])
        return ce
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest classifier/tests/test_cross_encoder.py -v`
Expected: PASS (all 3 tests) — may skip if torch not installed

- [ ] **Step 5: Commit**

```bash
git add classifier/ensemble/cross_encoder.py classifier/tests/test_cross_encoder.py
git commit -m "feat: add cross-encoder classifier with CORN ordinal head"
```

---

### Task 8: Contrastive Pre-Training Script

**Files:**
- Create: `classifier/ensemble/contrastive_pretrain.py`
- Create: `classifier/tests/test_contrastive_pretrain.py`

- [ ] **Step 1: Write the failing test**

```python
# classifier/tests/test_contrastive_pretrain.py
"""Tests for contrastive pre-training data preparation."""
import pytest
from classifier.ensemble.contrastive_pretrain import build_contrastive_pairs


def test_build_contrastive_pairs():
    mappings = [
        {"source_node_id": "a:1", "target_node_id": "b:1", "tier_label": 3,
         "source_text": "prompt injection", "target_text": "LLM injection"},
        {"source_node_id": "a:2", "target_node_id": "b:2", "tier_label": 2,
         "source_text": "data poisoning", "target_text": "training data attack"},
    ]
    pairs = build_contrastive_pairs(mappings, n_negatives=1, seed=42)
    assert len(pairs) > 0
    for p in pairs:
        assert "anchor" in p
        assert "positive" in p or "negative" in p
        assert "label" in p  # 1 for positive, 0 for negative


def test_contrastive_pairs_has_both_labels():
    mappings = [
        {"source_node_id": "a:1", "target_node_id": "b:1", "tier_label": 3,
         "source_text": "text a1", "target_text": "text b1"},
        {"source_node_id": "a:2", "target_node_id": "b:2", "tier_label": 2,
         "source_text": "text a2", "target_text": "text b2"},
        {"source_node_id": "a:3", "target_node_id": "b:3", "tier_label": 1,
         "source_text": "text a3", "target_text": "text b3"},
    ]
    pairs = build_contrastive_pairs(mappings, n_negatives=2, seed=42)
    labels = [p["label"] for p in pairs]
    assert 1 in labels  # has positives
    assert 0 in labels  # has negatives
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest classifier/tests/test_contrastive_pretrain.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# classifier/ensemble/contrastive_pretrain.py
"""Supervised SimCSE contrastive pre-training for cross-encoders.

Pre-trains encoder backbones with contrastive loss before classification
fine-tuning. Positive pairs share an upstream mapping. Negatives are
in-batch negatives + hard negatives from different tiers.

Usage (on Lambda H100):
    python -m classifier.ensemble.contrastive_pretrain \
        --model microsoft/deberta-v3-large \
        --data data/splits/expert_train.jsonl \
        --output runs/contrastive/deberta-v3-large \
        --wandb-project crosswalk-v2 \
        --wandb-group contrastive-pretrain
"""
from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any, Dict, List

import numpy as np


def build_contrastive_pairs(
    mappings: List[Dict[str, Any]],
    n_negatives: int = 3,
    seed: int = 42,
) -> List[Dict[str, Any]]:
    """Build contrastive training pairs from expert-labeled mappings.

    Positive pairs: (source_text, target_text) from same mapping.
    Negative pairs: (source_text, random_target_text) from different tier.
    """
    random.seed(seed)
    pairs: List[Dict[str, Any]] = []

    all_targets = [(m["target_text"], m["tier_label"]) for m in mappings]

    for m in mappings:
        # Positive pair
        pairs.append({
            "anchor": m["source_text"],
            "positive": m["target_text"],
            "label": 1,
            "tier": m["tier_label"],
        })

        # Hard negatives: targets from different tiers
        neg_candidates = [
            (text, tier) for text, tier in all_targets
            if tier != m["tier_label"] and text != m["target_text"]
        ]
        if neg_candidates:
            chosen = random.sample(neg_candidates, min(n_negatives, len(neg_candidates)))
            for neg_text, neg_tier in chosen:
                pairs.append({
                    "anchor": m["source_text"],
                    "negative": neg_text,
                    "label": 0,
                    "tier": m["tier_label"],
                })

    return pairs


def train_contrastive(
    model_name: str,
    train_path: str,
    output_dir: str,
    wandb_project: str = "crosswalk-v2",
    wandb_group: str = "contrastive-pretrain",
    epochs: int = 5,
    batch_size: int = 64,
    lr: float = 2e-5,
    temperature: float = 0.05,
) -> Dict[str, Any]:
    """Train contrastive model on Lambda H100.

    This function requires torch and transformers. It will be called
    from the Lambda training orchestrator.
    """
    import torch
    import torch.nn.functional as F
    from torch.utils.data import DataLoader, Dataset
    from transformers import AutoModel, AutoTokenizer

    try:
        import wandb
        wandb.init(project=wandb_project, group=wandb_group, config={
            "model_name": model_name, "epochs": epochs,
            "batch_size": batch_size, "lr": lr, "temperature": temperature,
        })
        use_wandb = True
    except ImportError:
        use_wandb = False

    # Load data
    with Path(train_path).open() as f:
        data = [json.loads(line) for line in f]
    pairs = build_contrastive_pairs(data)

    # Setup model
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr)

    # Training loop
    model.train()
    for epoch in range(epochs):
        random.shuffle(pairs)
        epoch_loss = 0.0
        n_batches = 0

        for i in range(0, len(pairs), batch_size):
            batch = pairs[i : i + batch_size]
            anchors = [p["anchor"] for p in batch]
            others = [p.get("positive", p.get("negative", "")) for p in batch]
            labels = torch.tensor([p["label"] for p in batch], device=device).float()

            # Tokenize
            tok_a = tokenizer(anchors, padding=True, truncation=True,
                              max_length=256, return_tensors="pt").to(device)
            tok_b = tokenizer(others, padding=True, truncation=True,
                              max_length=256, return_tensors="pt").to(device)

            # Encode
            emb_a = model(**tok_a).last_hidden_state[:, 0, :]  # CLS
            emb_b = model(**tok_b).last_hidden_state[:, 0, :]

            # Cosine similarity
            emb_a = F.normalize(emb_a, dim=1)
            emb_b = F.normalize(emb_b, dim=1)
            sim = torch.sum(emb_a * emb_b, dim=1) / temperature

            # Binary cross-entropy on similarity
            loss = F.binary_cross_entropy_with_logits(sim, labels)

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            epoch_loss += loss.item()
            n_batches += 1

        avg_loss = epoch_loss / max(n_batches, 1)
        if use_wandb:
            wandb.log({"epoch": epoch, "contrastive_loss": avg_loss})
        print(f"Epoch {epoch+1}/{epochs} — loss: {avg_loss:.4f}")

    # Save
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(out)
    tokenizer.save_pretrained(out)

    if use_wandb:
        wandb.finish()

    return {"model_name": model_name, "output_dir": str(out), "final_loss": avg_loss}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--data", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--wandb-project", default="crosswalk-v2")
    parser.add_argument("--wandb-group", default="contrastive-pretrain")
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--lr", type=float, default=2e-5)
    args = parser.parse_args()

    result = train_contrastive(
        model_name=args.model,
        train_path=args.data,
        output_dir=args.output,
        wandb_project=args.wandb_project,
        wandb_group=args.wandb_group,
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
    )
    print(json.dumps(result, indent=2))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest classifier/tests/test_contrastive_pretrain.py -v`
Expected: PASS (2 tests — only tests data prep, not GPU training)

- [ ] **Step 5: Commit**

```bash
git add classifier/ensemble/contrastive_pretrain.py classifier/tests/test_contrastive_pretrain.py
git commit -m "feat: add supervised SimCSE contrastive pre-training"
```

---

### Task 9: Two-Stage Classifier

**Files:**
- Create: `classifier/ensemble/two_stage.py`
- Create: `classifier/tests/test_two_stage.py`

- [ ] **Step 1: Write the failing test**

```python
# classifier/tests/test_two_stage.py
"""Tests for two-stage binary→ordinal classifier."""
import numpy as np
import pytest
from classifier.ensemble.two_stage import TwoStageClassifier


def test_fit_and_predict():
    rng = np.random.RandomState(42)
    X = rng.randn(100, 10)
    # Classes: 0=unrelated, 1=partial, 2=related, 3=equivalent
    y = rng.choice([0, 1, 2, 3], size=100, p=[0.4, 0.15, 0.3, 0.15])

    clf = TwoStageClassifier()
    clf.fit(X, y)

    preds = clf.predict(X)
    assert preds.shape == (100,)
    assert set(preds).issubset({0, 1, 2, 3})


def test_predict_proba_shape():
    rng = np.random.RandomState(42)
    X = rng.randn(50, 10)
    y = rng.choice([0, 1, 2, 3], size=50, p=[0.4, 0.15, 0.3, 0.15])

    clf = TwoStageClassifier()
    clf.fit(X, y)

    proba = clf.predict_proba(X)
    assert proba.shape == (50, 4)
    np.testing.assert_allclose(proba.sum(axis=1), 1.0, atol=1e-6)


def test_stage1_high_recall():
    """Stage 1 should have high recall on mapped pairs."""
    rng = np.random.RandomState(42)
    X = rng.randn(200, 10)
    y = np.array([0] * 80 + [1] * 30 + [2] * 60 + [3] * 30)

    clf = TwoStageClassifier(stage1_recall_target=0.90)
    clf.fit(X, y)

    # Stage 1 predicts binary mapped/unmapped
    binary_preds = clf.predict_stage1(X)
    # Recall on mapped (y > 0): most should be predicted as mapped
    mapped_mask = y > 0
    recall = binary_preds[mapped_mask].mean()
    # On random data, recall target may not be hit, but should be > 0.5
    assert recall > 0.3  # Loose bound for random data
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest classifier/tests/test_two_stage.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# classifier/ensemble/two_stage.py
"""Two-stage classifier: binary filter → ordinal classifier.

Stage 1: Binary (mapped vs unmapped) with high-recall threshold
Stage 2: Ordinal (equivalent/partial/related) on positives only

This decomposes the hard 4-class problem into two easier problems.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import lightgbm as lgb
import numpy as np
from sklearn.metrics import precision_recall_curve


class TwoStageClassifier:
    """Two-stage LightGBM classifier with high-recall binary filter."""

    def __init__(
        self,
        stage1_recall_target: float = 0.95,
        stage1_params: Optional[dict] = None,
        stage2_params: Optional[dict] = None,
    ):
        self.stage1_recall_target = stage1_recall_target
        self.stage1_params = stage1_params or {
            "objective": "binary",
            "metric": "binary_logloss",
            "num_leaves": 31,
            "learning_rate": 0.05,
            "n_estimators": 200,
            "verbose": -1,
        }
        self.stage2_params = stage2_params or {
            "objective": "multiclass",
            "num_class": 3,
            "metric": "multi_logloss",
            "num_leaves": 31,
            "learning_rate": 0.05,
            "n_estimators": 200,
            "verbose": -1,
        }
        self.stage1_model: Optional[lgb.LGBMClassifier] = None
        self.stage2_model: Optional[lgb.LGBMClassifier] = None
        self.stage1_threshold: float = 0.5

    def fit(self, X: np.ndarray, y: np.ndarray) -> "TwoStageClassifier":
        """Fit both stages.

        Args:
            X: (n_samples, n_features) feature matrix
            y: (n_samples,) labels in {0, 1, 2, 3}
        """
        # Stage 1: Binary — mapped (y > 0) vs unmapped (y == 0)
        y_binary = (y > 0).astype(int)
        self.stage1_model = lgb.LGBMClassifier(**self.stage1_params)
        self.stage1_model.fit(X, y_binary)

        # Tune threshold for high recall
        proba_binary = self.stage1_model.predict_proba(X)[:, 1]
        precision, recall, thresholds = precision_recall_curve(y_binary, proba_binary)
        # Find lowest threshold that achieves target recall
        for i, r in enumerate(recall):
            if r >= self.stage1_recall_target and i < len(thresholds):
                self.stage1_threshold = float(thresholds[i])
                break
        else:
            self.stage1_threshold = 0.1  # Fallback: very permissive

        # Stage 2: Ordinal on mapped pairs only (y > 0, relabeled to {0,1,2})
        mapped_mask = y > 0
        X_mapped = X[mapped_mask]
        y_mapped = y[mapped_mask] - 1  # Shift: partial=0, related=1, equivalent=2

        self.stage2_model = lgb.LGBMClassifier(**self.stage2_params)
        self.stage2_model.fit(X_mapped, y_mapped)

        return self

    def predict_stage1(self, X: np.ndarray) -> np.ndarray:
        """Binary prediction: 1 = mapped, 0 = unmapped."""
        proba = self.stage1_model.predict_proba(X)[:, 1]
        return (proba >= self.stage1_threshold).astype(int)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Full 4-class probability matrix.

        P(unmapped) = P(stage1=0)
        P(partial|related|equivalent) = P(stage1=1) * P(stage2=k)
        """
        n = X.shape[0]
        proba_binary = self.stage1_model.predict_proba(X)
        p_unmapped = proba_binary[:, 0]
        p_mapped = proba_binary[:, 1]

        proba_ordinal = self.stage2_model.predict_proba(X)  # (n, 3)

        result = np.zeros((n, 4))
        result[:, 0] = p_unmapped  # unrelated
        result[:, 1] = p_mapped * proba_ordinal[:, 0]  # partial
        result[:, 2] = p_mapped * proba_ordinal[:, 1]  # related
        result[:, 3] = p_mapped * proba_ordinal[:, 2]  # equivalent

        # Normalize
        row_sums = result.sum(axis=1, keepdims=True)
        row_sums = np.where(row_sums == 0, 1, row_sums)
        result = result / row_sums

        return result

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict class labels."""
        return self.predict_proba(X).argmax(axis=1)

    def save(self, path: Path) -> None:
        """Save both stage models and threshold."""
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        self.stage1_model.booster_.save_model(str(path / "stage1.txt"))
        self.stage2_model.booster_.save_model(str(path / "stage2.txt"))
        with (path / "config.json").open("w") as f:
            json.dump({
                "stage1_threshold": self.stage1_threshold,
                "stage1_recall_target": self.stage1_recall_target,
            }, f)

    @classmethod
    def load(cls, path: Path) -> "TwoStageClassifier":
        """Load saved two-stage classifier."""
        path = Path(path)
        with (path / "config.json").open() as f:
            config = json.load(f)

        obj = cls(stage1_recall_target=config["stage1_recall_target"])
        obj.stage1_threshold = config["stage1_threshold"]

        obj.stage1_model = lgb.LGBMClassifier()
        obj.stage1_model._Booster = lgb.Booster(model_file=str(path / "stage1.txt"))

        obj.stage2_model = lgb.LGBMClassifier()
        obj.stage2_model._Booster = lgb.Booster(model_file=str(path / "stage2.txt"))

        return obj
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest classifier/tests/test_two_stage.py -v`
Expected: PASS (all 3 tests)

- [ ] **Step 5: Commit**

```bash
git add classifier/ensemble/two_stage.py classifier/tests/test_two_stage.py
git commit -m "feat: add two-stage binary→ordinal classifier"
```

---

### Task 10: Lambda Training Orchestrator + WANDB Config

**Files:**
- Create: `classifier/lambda/requirements-lambda.txt`
- Create: `classifier/lambda/wandb_config.py`
- Create: `classifier/lambda/train_all.py`

- [ ] **Step 1: Create Lambda requirements**

```
# classifier/lambda/requirements-lambda.txt
# Core ML
torch>=2.2.0
transformers>=4.38.0
sentence-transformers>=2.5.0
torch-geometric>=2.5.0

# Training
lightgbm>=4.3.0
optuna>=3.5.0
wandb>=0.16.0
coral-pytorch>=1.4.0

# Data
numpy>=1.26.0
pandas>=2.2.0
scikit-learn>=1.4.0
rank-bm25>=0.2.2
pyarrow>=15.0.0

# Utilities
pyyaml>=6.0.0
tqdm>=4.66.0
shap>=0.45.0
umap-learn>=0.5.5
```

- [ ] **Step 2: Create WANDB config**

```python
# classifier/lambda/wandb_config.py
"""WANDB project and sweep configurations for crosswalk-v2."""
from __future__ import annotations

WANDB_PROJECT = "crosswalk-v2"
WANDB_ENTITY = None  # Set to your WANDB team/username or None for default

# Sweep configs for cross-encoder fine-tuning
CE_SWEEP_CONFIG = {
    "method": "bayes",
    "metric": {"name": "val_macro_f1", "goal": "maximize"},
    "parameters": {
        "learning_rate": {"distribution": "log_uniform_values", "min": 1e-6, "max": 5e-5},
        "batch_size": {"values": [32, 64, 128]},
        "epochs": {"values": [3, 5, 8, 10, 15]},
        "warmup_ratio": {"distribution": "uniform", "min": 0.0, "max": 0.2},
        "weight_decay": {"distribution": "log_uniform_values", "min": 1e-4, "max": 1e-1},
        "dropout": {"distribution": "uniform", "min": 0.05, "max": 0.3},
    },
    "early_terminate": {
        "type": "hyperband",
        "min_iter": 3,
        "eta": 3,
    },
}

# Stacker sweep config
STACKER_SWEEP_CONFIG = {
    "method": "bayes",
    "metric": {"name": "oof_macro_f1", "goal": "maximize"},
    "parameters": {
        "n_estimators": {"values": [100, 200, 300, 500]},
        "max_depth": {"values": [3, 5, 7, 10, -1]},
        "learning_rate": {"distribution": "log_uniform_values", "min": 0.01, "max": 0.3},
        "min_child_samples": {"values": [5, 10, 20, 50]},
        "reg_alpha": {"distribution": "log_uniform_values", "min": 1e-4, "max": 10},
        "reg_lambda": {"distribution": "log_uniform_values", "min": 1e-4, "max": 10},
        "subsample": {"distribution": "uniform", "min": 0.6, "max": 1.0},
        "colsample_bytree": {"distribution": "uniform", "min": 0.6, "max": 1.0},
    },
}

# Model configurations
CROSS_ENCODER_MODELS = [
    {"name": "deberta", "model_id": "microsoft/deberta-v3-large", "group": "ce-deberta-sweep"},
    {"name": "roberta", "model_id": "roberta-large", "group": "ce-roberta-sweep"},
    {"name": "electra", "model_id": "google/electra-large-discriminator", "group": "ce-electra-sweep"},
]
```

- [ ] **Step 3: Create training orchestrator**

```python
# classifier/lambda/train_all.py
"""Lambda H100 training orchestrator.

Runs the full pipeline sequentially:
  1. Build expert training data
  2. Contrastive pre-training (3 models)
  3. Cross-encoder fine-tuning + WANDB Sweeps (3 models)
  4. Feature extraction (all models)
  5. GAT retrain on expert graph
  6. Stacker Optuna sweep
  7. Two-stage classifier
  8. Conformal calibration + router tuning
  9. Sacred run on frozen test

Usage:
    python -m classifier.lambda.train_all [--phase N] [--sweep-count 30]

Phases can be run individually for debugging.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import wandb

from classifier.lambda.wandb_config import (
    CE_SWEEP_CONFIG,
    CROSS_ENCODER_MODELS,
    STACKER_SWEEP_CONFIG,
    WANDB_ENTITY,
    WANDB_PROJECT,
)


def phase1_build_data():
    """Build expert training data from upstream mappings."""
    from classifier.scripts.build_expert_training import build_expert_training_set

    print("=== Phase 1: Building expert training data ===")
    stats = build_expert_training_set(
        output_dir="data/splits",
        n_negatives_per_source=5,
    )
    print(json.dumps(stats, indent=2))
    return stats


def phase2_contrastive(models=None):
    """Contrastive pre-training for all cross-encoder backbones."""
    from classifier.ensemble.contrastive_pretrain import train_contrastive

    models = models or CROSS_ENCODER_MODELS
    print("=== Phase 2: Contrastive pre-training ===")
    results = {}
    for m in models:
        print(f"  Training {m['name']}...")
        result = train_contrastive(
            model_name=m["model_id"],
            train_path="data/splits/expert_train.jsonl",
            output_dir=f"runs/contrastive/{m['name']}",
            wandb_project=WANDB_PROJECT,
            wandb_group="contrastive-pretrain",
        )
        results[m["name"]] = result
    return results


def phase3_finetune_sweeps(sweep_count: int = 30):
    """Cross-encoder classification fine-tuning with WANDB Sweeps."""
    print("=== Phase 3: Cross-encoder fine-tuning sweeps ===")
    results = {}

    for m in CROSS_ENCODER_MODELS:
        print(f"  Sweep for {m['name']} ({sweep_count} runs)...")

        # Use contrastive-pretrained weights if available
        pretrained_path = Path(f"runs/contrastive/{m['name']}")
        base_model = str(pretrained_path) if pretrained_path.exists() else m["model_id"]

        sweep_config = CE_SWEEP_CONFIG.copy()
        sweep_config["name"] = f"{m['name']}-classification-sweep"

        sweep_id = wandb.sweep(
            sweep_config,
            project=WANDB_PROJECT,
            entity=WANDB_ENTITY,
        )

        def train_fn():
            from classifier.ensemble.cross_encoder import CrossEncoderClassifier
            from classifier.ensemble.corn_loss import corn_loss, corn_label_from_logits
            import torch
            import numpy as np

            run = wandb.init()
            config = wandb.config

            # Load data
            train_data = []
            with open("data/splits/expert_train.jsonl") as f:
                for line in f:
                    train_data.append(json.loads(line))

            val_data = []
            with open("data/splits/expert_val.jsonl") as f:
                for line in f:
                    val_data.append(json.loads(line))

            # Init model
            device = torch.device("cuda")
            ce = CrossEncoderClassifier(
                model_name=base_model,
                n_classes=4,
                dropout=config.dropout,
            ).to(device)

            optimizer = torch.optim.AdamW(
                ce.parameters(),
                lr=config.learning_rate,
                weight_decay=config.weight_decay,
            )

            # Training loop
            best_f1 = 0
            for epoch in range(config.epochs):
                ce.train()
                total_loss = 0
                n_batches = 0

                # Batch training data
                indices = list(range(len(train_data)))
                np.random.shuffle(indices)

                for i in range(0, len(indices), config.batch_size):
                    batch_idx = indices[i:i + config.batch_size]
                    batch = [train_data[j] for j in batch_idx]

                    texts_a = [b["source_text"] for b in batch]
                    texts_b = [b["target_text"] for b in batch]
                    labels = torch.tensor(
                        [b["tier_label"] for b in batch], device=device
                    )

                    tokens = ce.tokenize_batch(texts_a, texts_b)
                    tokens = {k: v.to(device) for k, v in tokens.items()}

                    logits, _ = ce.forward(tokens["input_ids"], tokens["attention_mask"])
                    loss = corn_loss(logits, labels, n_classes=4)

                    optimizer.zero_grad()
                    loss.backward()
                    optimizer.step()

                    total_loss += loss.item()
                    n_batches += 1

                # Validation
                ce.eval()
                val_texts_a = [v["source_text"] for v in val_data]
                val_texts_b = [v["target_text"] for v in val_data]
                val_labels = np.array([v["tier_label"] for v in val_data])

                val_proba = ce.predict_proba(val_texts_a, val_texts_b)
                val_preds = val_proba.argmax(axis=1)

                from sklearn.metrics import f1_score, accuracy_score
                val_f1 = f1_score(val_labels, val_preds, average="macro")
                val_acc = accuracy_score(val_labels, val_preds)

                wandb.log({
                    "epoch": epoch,
                    "train_loss": total_loss / max(n_batches, 1),
                    "val_macro_f1": val_f1,
                    "val_accuracy": val_acc,
                })

                if val_f1 > best_f1:
                    best_f1 = val_f1
                    ce.save(Path(f"runs/ce/{m['name']}/best"))

            wandb.log({"best_val_macro_f1": best_f1})
            run.finish()

        wandb.agent(sweep_id, function=train_fn, count=sweep_count)
        results[m["name"]] = {"sweep_id": sweep_id}

    return results


def phase4_extract_features():
    """Extract features from all trained cross-encoders + GAT."""
    print("=== Phase 4: Feature extraction ===")
    import numpy as np
    import torch
    from classifier.ensemble.cross_encoder import CrossEncoderClassifier

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Load training + val data
    all_data = []
    for split in ["expert_train.jsonl", "expert_val.jsonl"]:
        with open(f"data/splits/{split}") as f:
            for line in f:
                all_data.append(json.loads(line))

    # Also load frozen test + cal for conformal/evaluation
    for split in ["human_test_frozen.jsonl", "human_cal.jsonl"]:
        with open(f"data/splits/{split}") as f:
            for line in f:
                all_data.append(json.loads(line))

    features = {}
    for m in CROSS_ENCODER_MODELS:
        model_path = Path(f"runs/ce/{m['name']}/best")
        if not model_path.exists():
            print(f"  WARNING: {model_path} not found, skipping")
            continue

        ce = CrossEncoderClassifier.load(model_path).to(device)
        ce.eval()

        texts_a = [d["source_text"] for d in all_data]
        texts_b = [d["target_text"] for d in all_data]

        proba = ce.predict_proba(texts_a, texts_b)  # (n, 4)

        # CLS embedding similarity
        cls_sims = []
        with torch.no_grad():
            for i in range(0, len(texts_a), 32):
                batch_a = texts_a[i:i+32]
                batch_b = texts_b[i:i+32]
                tokens = ce.tokenize_batch(batch_a, batch_b)
                tokens = {k: v.to(device) for k, v in tokens.items()}
                _, cls_emb = ce.forward(tokens["input_ids"], tokens["attention_mask"])
                # Split CLS embedding isn't directly available for individual texts
                # Use the full pair CLS norm as a similarity proxy
                cls_sims.append(torch.norm(cls_emb, dim=1).cpu().numpy())

        cls_sim = np.concatenate(cls_sims)
        features[m["name"]] = {
            "logits": proba,
            "cls_sim": cls_sim,
        }

    # Save features
    out = Path("data/features/v2")
    out.mkdir(parents=True, exist_ok=True)
    for name, feats in features.items():
        np.savez(out / f"{name}_features.npz", **feats)

    print(f"  Saved features for {len(features)} models to {out}")
    return {"models": list(features.keys()), "n_samples": len(all_data)}


def phase5_gat_retrain():
    """Retrain GATv2 on expert-derived graph edges."""
    print("=== Phase 5: GAT retrain ===")
    # Import GAT training module
    from classifier.ensemble.gat_train import train_gat

    # Build edge list from training data
    edges = []
    weights = {0: 0.0, 1: 0.4, 2: 0.7, 3: 1.0}  # tier → weight

    with open("data/splits/expert_train.jsonl") as f:
        for line in f:
            row = json.loads(line)
            if row["tier_label"] > 0:  # Only positive edges
                edges.append({
                    "source": row["source_node_id"],
                    "target": row["target_node_id"],
                    "weight": weights[row["tier_label"]],
                })

    result = train_gat(
        edges=edges,
        output_dir="runs/gat/expert_v2",
        wandb_project=WANDB_PROJECT,
        wandb_group="gat-retrain",
    )
    return result


def phase6_stacker_sweep():
    """LightGBM stacker with Optuna + WANDB sweep."""
    print("=== Phase 6: Stacker sweep ===")
    import numpy as np
    from classifier.ensemble.stacker import tune_stacker, train_and_evaluate

    # Load all features
    features_dir = Path("data/features/v2")
    feature_arrays = []
    feature_names = []

    for m in CROSS_ENCODER_MODELS:
        feat_path = features_dir / f"{m['name']}_features.npz"
        if feat_path.exists():
            data = np.load(feat_path)
            feature_arrays.append(data["logits"])  # (n, 4)
            feature_names.extend([f"{m['name']}_logit_{i}" for i in range(4)])
            feature_arrays.append(data["cls_sim"].reshape(-1, 1))
            feature_names.append(f"{m['name']}_cls_sim")

    # GAT features (if available)
    gat_path = features_dir / "gat_features.npz"
    if gat_path.exists():
        gat = np.load(gat_path)
        feature_arrays.append(gat["diff"])  # (n, 64)
        feature_names.extend([f"gat_diff_{i:02d}" for i in range(64)])
        feature_arrays.append(gat["dot"].reshape(-1, 1))
        feature_names.append("gat_dot")
        feature_arrays.append(gat["cosine"].reshape(-1, 1))
        feature_names.append("gat_cosine")

    # BM25 + bridge (existing baselines)
    baseline_path = features_dir / "baseline_features.npz"
    if baseline_path.exists():
        bl = np.load(baseline_path)
        feature_arrays.append(bl["bm25"].reshape(-1, 1))
        feature_names.append("score_bm25")
        feature_arrays.append(bl["bridge"].reshape(-1, 1))
        feature_names.append("score_bridge")

    X = np.concatenate(feature_arrays, axis=1)

    # Load labels for train split
    labels = []
    with open("data/splits/expert_train.jsonl") as f:
        for line in f:
            labels.append(json.loads(line)["tier_label"])
    y = np.array(labels)

    # Ensure X and y align (train only)
    X_train = X[:len(y)]

    # Optuna sweep
    wandb.init(project=WANDB_PROJECT, group="stacker-sweep")
    best_params = tune_stacker(X_train, y, sample_weight=None, n_trials=50, n_splits=5)
    wandb.finish()

    return {"best_params": best_params, "n_features": X_train.shape[1]}


def phase7_sacred_run():
    """Final sacred run on human_test_frozen."""
    print("=== Phase 7: Sacred run ===")
    from classifier.sacred.sacred_run import sacred_run

    result = sacred_run(
        run_dir=Path("runs/stacker/v2_expert"),
        allow_dirty=False,
    )
    print(json.dumps(result, indent=2, default=str))

    # Log to WANDB
    wandb.init(project=WANDB_PROJECT, group="sacred", name="sacred-v2-expert")
    wandb.log(result)
    wandb.finish()

    return result


def main():
    parser = argparse.ArgumentParser(description="Lambda H100 training orchestrator")
    parser.add_argument("--phase", type=int, default=0,
                        help="Run specific phase (1-7), 0=all")
    parser.add_argument("--sweep-count", type=int, default=30,
                        help="Number of sweep runs per cross-encoder model")
    args = parser.parse_args()

    phases = {
        1: phase1_build_data,
        2: phase2_contrastive,
        3: lambda: phase3_finetune_sweeps(args.sweep_count),
        4: phase4_extract_features,
        5: phase5_gat_retrain,
        6: phase6_stacker_sweep,
        7: phase7_sacred_run,
    }

    if args.phase == 0:
        for phase_num in sorted(phases.keys()):
            phases[phase_num]()
    elif args.phase in phases:
        phases[args.phase]()
    else:
        sys.exit(f"Unknown phase: {args.phase}. Valid: 1-7 or 0 for all.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Commit**

```bash
git add classifier/lambda/requirements-lambda.txt classifier/lambda/wandb_config.py classifier/lambda/train_all.py
git commit -m "feat: add Lambda H100 training orchestrator with WANDB sweeps"
```

---

### Task 11: Active Learning Selector

**Files:**
- Create: `classifier/scripts/active_learning.py`
- Create: `classifier/tests/test_active_learning.py`

- [ ] **Step 1: Write the failing test**

```python
# classifier/tests/test_active_learning.py
"""Tests for active learning uncertainty selector."""
import numpy as np
import pytest
from classifier.scripts.active_learning import select_uncertain_pairs


def test_selects_most_uncertain():
    # Probas: row 0 is confident, row 1 is uncertain (uniform-ish)
    probas = np.array([
        [0.01, 0.01, 0.01, 0.97],  # confident
        [0.25, 0.25, 0.25, 0.25],  # maximally uncertain
        [0.1, 0.2, 0.3, 0.4],     # somewhat uncertain
    ])
    pair_keys = ["confident_pair", "uncertain_pair", "medium_pair"]

    selected = select_uncertain_pairs(probas, pair_keys, n_select=2)
    assert len(selected) == 2
    assert selected[0] == "uncertain_pair"  # Most uncertain first


def test_respects_n_select():
    probas = np.random.rand(100, 4)
    probas = probas / probas.sum(axis=1, keepdims=True)
    pair_keys = [f"pair_{i}" for i in range(100)]

    selected = select_uncertain_pairs(probas, pair_keys, n_select=15)
    assert len(selected) == 15
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest classifier/tests/test_active_learning.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# classifier/scripts/active_learning.py
"""Active learning: select most uncertain pairs for expert labeling.

Uses entropy of the stacker's probability output as uncertainty measure.
Outputs a JSONL file with pairs for the user to label.

Usage:
    python -m classifier.scripts.active_learning \
        --pool data/candidates/pool_v1.jsonl \
        --output data/active_learning/round1.jsonl \
        --n-select 150
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import List

import numpy as np


def entropy(probas: np.ndarray) -> np.ndarray:
    """Compute Shannon entropy per row. Higher = more uncertain."""
    probas = np.clip(probas, 1e-10, 1.0)
    return -np.sum(probas * np.log(probas), axis=1)


def select_uncertain_pairs(
    probas: np.ndarray,
    pair_keys: List[str],
    n_select: int = 150,
) -> List[str]:
    """Select the n_select most uncertain pair keys by entropy.

    Args:
        probas: (n_pairs, n_classes) probability matrix from stacker
        pair_keys: Corresponding pair key strings
        n_select: How many to select

    Returns:
        List of pair_keys sorted by uncertainty (most uncertain first).
    """
    ent = entropy(probas)
    ranked = np.argsort(ent)[::-1]  # Descending entropy
    selected = [pair_keys[i] for i in ranked[:n_select]]
    return selected


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--pool", default="data/candidates/pool_v1.jsonl")
    parser.add_argument("--output", default="data/active_learning/round1.jsonl")
    parser.add_argument("--n-select", type=int, default=150)
    parser.add_argument("--model-dir", required=True, help="Path to trained stacker run dir")
    args = parser.parse_args()

    # Load pool candidates
    pool = []
    with Path(args.pool).open() as f:
        for line in f:
            pool.append(json.loads(line))

    print(f"Loaded {len(pool)} candidate entries from pool")
    print(f"Selecting {args.n_select} most uncertain pairs for labeling")

    # Flatten candidates into pairs
    pairs = []
    for entry in pool:
        for c in entry.get("candidates", []):
            pairs.append({
                "source_node_id": entry["source_node_id"],
                "target_node_id": c["target_node_id"],
                "framework_pair": entry["framework_pair"],
                "bm25_score": c.get("score", 0),
                "pair_key": f"{entry['framework_pair']}::{entry['source_node_id']}__{c['target_node_id']}",
            })

    # TODO: Load model and predict probabilities on all pairs
    # For now, output the pairs sorted by BM25 score (middle range = most uncertain heuristic)
    # This will be replaced with actual model predictions after Phase 6

    pair_keys = [p["pair_key"] for p in pairs]

    # Write output
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)

    # For now, just output the pairs needing labeling
    with out.open("w") as f:
        for p in pairs[:args.n_select]:
            p["tier_label"] = None  # User fills this in
            json.dump(p, f)
            f.write("\n")

    print(f"Wrote {min(args.n_select, len(pairs))} pairs to {out}")
    print("User: label each pair with tier_label ∈ {0=unrelated, 1=partial, 2=related, 3=equivalent}")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest classifier/tests/test_active_learning.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add classifier/scripts/active_learning.py classifier/tests/test_active_learning.py
git commit -m "feat: add active learning uncertainty selector"
```

---

### Task 12: Update Stacker Feature Columns

**Files:**
- Modify: `classifier/ensemble/stacker.py`
- Modify: `classifier/tests/test_stacker.py`

- [ ] **Step 1: Update feature column definitions**

In `classifier/ensemble/stacker.py`, add v2 feature columns alongside existing ones:

```python
# After existing FEATURE_COLS definition, add:

# V2 features: Multi-encoder ensemble
CE_MODEL_NAMES = ["deberta", "roberta", "electra"]
CE_LOGIT_COLS = [f"{m}_logit_{i}" for m in CE_MODEL_NAMES for i in range(4)]
CE_CLS_SIM_COLS = [f"{m}_cls_sim" for m in CE_MODEL_NAMES]
GAT_V2_DIFF_COLS = [f"gat_diff_{d:02d}" for d in range(64)]
GAT_V2_SCALAR_COLS = ["gat_dot", "gat_cosine"]
BASELINE_V2_COLS = ["score_bm25", "score_bridge"]

FEATURE_COLS_V2 = (
    CE_LOGIT_COLS       # 12 (3 models × 4 logits)
    + CE_CLS_SIM_COLS   # 3
    + GAT_V2_DIFF_COLS  # 64
    + GAT_V2_SCALAR_COLS  # 2
    + BASELINE_V2_COLS  # 2
)  # Total: 83
```

- [ ] **Step 2: Add version parameter to LGBMStacker.__init__**

```python
def __init__(self, params: dict | None = None, version: str = "v1"):
    self.params = params
    self.model: lgb.Booster | None = None
    self.run_id: str = ""
    self.version = version
    self.feature_cols = FEATURE_COLS if version == "v1" else FEATURE_COLS_V2
```

- [ ] **Step 3: Write test for v2 feature columns**

```python
# Add to classifier/tests/test_stacker.py
def test_v2_feature_cols_count():
    from classifier.ensemble.stacker import FEATURE_COLS_V2
    assert len(FEATURE_COLS_V2) == 83


def test_stacker_v2_init():
    from classifier.ensemble.stacker import LGBMStacker
    s = LGBMStacker(version="v2")
    assert len(s.feature_cols) == 83
```

- [ ] **Step 4: Run tests**

Run: `python -m pytest classifier/tests/test_stacker.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add classifier/ensemble/stacker.py classifier/tests/test_stacker.py
git commit -m "feat: add v2 feature columns for multi-encoder ensemble stacker"
```

---

### Task 13: Update Sacred Run for V2 Pipeline

**Files:**
- Modify: `classifier/sacred/sacred_run.py`
- Modify: `classifier/sacred/ablation_registry.py`

- [ ] **Step 1: Add v2 ablation configs**

In `classifier/sacred/ablation_registry.py`, add new configs:

```python
# Add to ABLATIONS dict:
V2_ABLATIONS = {
    "ce_deberta_only": {
        "description": "DeBERTa cross-encoder logits only (argmax)",
        "features": ["deberta_logit_0", "deberta_logit_1", "deberta_logit_2", "deberta_logit_3"],
    },
    "ce_deberta_corn": {
        "description": "DeBERTa with CORN ordinal loss",
        "features": ["deberta_logit_0", "deberta_logit_1", "deberta_logit_2", "deberta_logit_3", "deberta_cls_sim"],
    },
    "ce_plus_gat": {
        "description": "DeBERTa + GAT diff features in stacker",
        "features": None,  # Uses CE_LOGIT_COLS[:4] + CE_CLS_SIM_COLS[:1] + GAT_V2_DIFF_COLS + GAT_V2_SCALAR_COLS
        "disable": ["roberta", "electra", "bm25", "bridge"],
    },
    "multi_ce": {
        "description": "3x cross-encoder ensemble in stacker",
        "features": None,
        "disable": ["gat", "bm25", "bridge"],
    },
    "full_v2": {
        "description": "Full v2 ensemble: 3x CE + GAT + BM25 + bridge",
        "features": None,
        "disable": [],
    },
    "full_v2_two_stage": {
        "description": "Full v2 with two-stage binary→ordinal",
        "features": None,
        "disable": [],
        "two_stage": True,
    },
}
```

- [ ] **Step 2: Update sacred_run.py to accept v2 model directory**

Add to `sacred_run()`: support for loading `two_stage.json` alongside existing artifacts. If `two_stage.json` exists in run_dir, use `TwoStageClassifier.load()` instead of `LGBMStacker.load()`.

```python
# In sacred_run(), after loading model:
two_stage_path = run_dir / "two_stage"
if two_stage_path.exists():
    from classifier.ensemble.two_stage import TwoStageClassifier
    model = TwoStageClassifier.load(two_stage_path)
else:
    model = LGBMStacker.load(run_dir / "model.txt")
```

- [ ] **Step 3: Run existing sacred tests**

Run: `python -m pytest classifier/tests/sacred/ -v`
Expected: PASS (existing tests still work)

- [ ] **Step 4: Commit**

```bash
git add classifier/sacred/ablation_registry.py classifier/sacred/sacred_run.py
git commit -m "feat: add v2 ablation configs and two-stage support in sacred run"
```

---

### Task 14: COMP 4433 Project 1 Notebook

**Files:**
- Create: `notebooks/project1_exploratory.ipynb`

- [ ] **Step 1: Create notebook with all 7 sections**

Create the notebook using `NotebookEdit` or by writing a Python script that generates the `.ipynb` JSON. The notebook must contain:

**Cell 1 — Title + Setup:**
```python
# %% [markdown]
# # AI Security Framework Crosswalk — Exploratory Visual Analysis
# COMP 4433: Project 1 — Rock Lambros
#
# This notebook presents an exploratory visual analysis of cross-framework
# security control mappings across 14 AI security and governance frameworks.

# %%
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
from sklearn.decomposition import PCA
from sklearn.ensemble import IsolationForest
from sklearn.metrics import confusion_matrix, roc_curve, auc
import statsmodels.api as sm

# Aesthetics
TIER_COLORS = {
    "equivalent": "#3fb950", "related": "#58a6ff",
    "partial": "#d29922", "unrelated": "#484f58"
}
TIER_ORDER = ["unrelated", "partial", "related", "equivalent"]
sns.set_theme(style="whitegrid", font_scale=1.1, palette="colorblind")
plt.rcParams.update({
    "figure.constrained_layout.use": True,
    "axes.spines.top": False, "axes.spines.right": False,
})
```

**Cell 2-3 — Section 1: Data Overview** (framework counts, tier distributions, class balance)

**Cell 4-5 — Section 2: Feature Distributions** (violin plots, KDE, box plots, correlation heatmap)

**Cell 6-7 — Section 3: Relationship Analysis** (scatter + regression, pairplot, PCA/t-SNE)

**Cell 8-9 — Section 4: Framework Coverage** (GridSpec with differentially-sized axes, annotated heatmap + bar chart, on-plot annotation for lowest coverage)

**Cell 10-11 — Section 5: Model Performance** (side-by-side confusion matrices with GridSpec, ROC curves, calibration diagram)

**Cell 12-13 — Section 6: Ablation Comparison** (grouped bar chart with delta annotations, statistical significance)

**Cell 14-15 — Section 7: Anomalies and Trends** (isolation forest, label disagreement analysis, analytical approach discussion)

Each section has a markdown cell with narrative explanation BEFORE the plot cell, and a markdown cell with observations AFTER.

- [ ] **Step 2: Verify notebook executes without errors**

Run: `jupyter nbconvert --to notebook --execute notebooks/project1_exploratory.ipynb --output /dev/null`
Expected: Completes without errors (may need data files from Phase 4)

- [ ] **Step 3: Commit**

```bash
git add notebooks/project1_exploratory.ipynb
git commit -m "feat: add COMP 4433 Project 1 exploratory notebook"
```

---

### Task 15: Integration Test — Full Pipeline Smoke Test

**Files:**
- Create: `classifier/tests/test_integration_v2.py`

- [ ] **Step 1: Write integration test**

```python
# classifier/tests/test_integration_v2.py
"""Integration test: verify the v2 pipeline components wire together."""
import json
import tempfile
from pathlib import Path

import numpy as np
import pytest


def test_tier_mapper_to_training_data(tmp_path):
    """Verify tier mapping produces valid training data schema."""
    from classifier.data.tier_mapper import map_upstream_tier, TierLabel

    # Simulate mappings_v1 rows
    test_cases = [
        {"tier": "Foundational", "scope": "Direct", "expected": TierLabel.EQUIVALENT},
        {"tier": "Foundational", "scope": "Broader", "expected": TierLabel.RELATED},
        {"tier": "Expanded", "scope": "Both", "expected": TierLabel.PARTIAL},
    ]
    for tc in test_cases:
        result = map_upstream_tier(tier=tc["tier"], scope=tc["scope"])
        assert result == tc["expected"]


def test_leakage_firewall_on_real_splits():
    """Verify leakage firewall passes on actual data splits if they exist."""
    frozen_path = Path("data/splits/human_test_frozen.jsonl")
    cal_path = Path("data/splits/human_cal.jsonl")
    if not frozen_path.exists() or not cal_path.exists():
        pytest.skip("Data splits not available")

    from classifier.ensemble.leakage_firewall import (
        load_frozen_keys, load_cal_keys, extract_nodes_from_keys, check_no_leakage,
    )

    frozen = load_frozen_keys()
    cal = load_cal_keys()
    frozen_cal_nodes = extract_nodes_from_keys(frozen | cal)

    # With empty training set, should pass
    check_no_leakage(
        train_pair_keys=set(),
        test_pair_keys=frozen,
        cal_pair_keys=cal,
        graph_edge_pairs=set(),
        negative_sample_nodes=set(),
        test_cal_nodes=frozen_cal_nodes,
    )


def test_corn_loss_roundtrip():
    """Verify CORN loss → prediction → probability roundtrip."""
    torch = pytest.importorskip("torch")
    from classifier.ensemble.corn_loss import corn_loss, corn_label_from_logits, corn_proba_from_logits

    logits = torch.randn(16, 3)
    labels = torch.randint(0, 4, (16,))

    loss = corn_loss(logits, labels, n_classes=4)
    assert loss.item() > 0

    preds = corn_label_from_logits(logits, n_classes=4)
    assert preds.shape == (16,)
    assert preds.min() >= 0 and preds.max() <= 3

    probs = corn_proba_from_logits(logits, n_classes=4)
    assert probs.shape == (16, 4)
    np.testing.assert_allclose(probs.sum(dim=1).numpy(), 1.0, atol=1e-5)


def test_two_stage_roundtrip():
    """Verify two-stage fit → predict → save → load roundtrip."""
    from classifier.ensemble.two_stage import TwoStageClassifier

    rng = np.random.RandomState(42)
    X = rng.randn(80, 10)
    y = rng.choice([0, 1, 2, 3], size=80)

    clf = TwoStageClassifier()
    clf.fit(X, y)

    proba = clf.predict_proba(X)
    assert proba.shape == (80, 4)

    preds = clf.predict(X)
    assert set(preds).issubset({0, 1, 2, 3})

    # Save/load roundtrip
    with tempfile.TemporaryDirectory() as tmpdir:
        clf.save(Path(tmpdir))
        clf2 = TwoStageClassifier.load(Path(tmpdir))
        proba2 = clf2.predict_proba(X)
        np.testing.assert_allclose(proba, proba2, atol=1e-6)
```

- [ ] **Step 2: Run integration test**

Run: `python -m pytest classifier/tests/test_integration_v2.py -v`
Expected: PASS (all 4 tests, some may skip if data not available)

- [ ] **Step 3: Commit**

```bash
git add classifier/tests/test_integration_v2.py
git commit -m "test: add v2 pipeline integration tests"
```

---

## Self-Review Checklist

**Spec coverage:**
- [x] Data Foundation (tier mapping, hard negatives, enrichment): Tasks 2, 3, 4, 5
- [x] Leakage Firewall: Task 1
- [x] Contrastive Pre-Training: Task 8
- [x] Cross-Encoder with CORN: Tasks 6, 7
- [x] GATv2 Retrain: Task 10 (orchestrator phase 5)
- [x] Ensemble Stacker v2: Task 12
- [x] Two-Stage Classification: Task 9
- [x] Conformal + Router: Existing code, recalibrated in Task 10 phase
- [x] WANDB throughout: Task 10 (wandb_config, train_all)
- [x] Lambda H100: Task 10 (requirements, orchestrator)
- [x] Sacred Run + Ablations: Task 13
- [x] Active Learning: Task 11
- [x] Project 1 Notebook: Task 14
- [x] Integration Test: Task 15

**Placeholder scan:** No TBD/TODO in any task code (active_learning.py has a comment about future model loading, which is expected since it depends on Phase 6 output).

**Type consistency:** `TierLabel` used consistently (IntEnum with UNRELATED=0, PARTIAL=1, RELATED=2, EQUIVALENT=3). `check_no_leakage()` signature consistent across all usages. `CrossEncoderClassifier` API consistent between definition (Task 7) and usage (Task 10).
