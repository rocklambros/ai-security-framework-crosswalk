"""Assemble v8 training data via disagreement mining on OpenCRE pairs.

Pipeline:
  1. Load all OpenCRE pairs
  2. Run contamination firewall (Rules 1-3)
  3. Run v7c inference on clean pairs (SetFit + CE + stacker)
  4. Identify disagreements (model pred ≠ expert signal)
  5. Generate calibrated soft labels
  6. Merge with existing expert_train data
  7. Write v8 training set
"""
from __future__ import annotations

import json
import time
from collections import Counter
from pathlib import Path

import numpy as np

from classifier.data.tier_mapper import TierLabel, map_opencre_tier
from classifier.data.contamination import check_cre_bridge_contamination

OPENCRE_PAIRS = Path("data/opencre/opencre_pairs.jsonl")
FROZEN_TEST = Path("data/splits/human_test_frozen.jsonl")
EXPERT_TRAIN = Path("data/splits/expert_train.jsonl")
V8_TRAIN_OUT = Path("data/splits/v8_train.jsonl")
V8_REPORT_OUT = Path("runs/v8_diagnosis/v8_data_assembly.json")

OPENCRE_WEIGHT = 0.3


def load_jsonl(path: Path) -> list[dict]:
    with open(path) as f:
        return [json.loads(line) for line in f]


def build_frozen_node_ids() -> set[str]:
    frozen = load_jsonl(FROZEN_TEST)
    ids = set()
    for row in frozen:
        ids.add(row["source_node_id"])
        ids.add(row["target_node_id"])
    return ids


def run_v7c_inference(pairs: list[dict]) -> np.ndarray:
    """Run v7c stacker inference on OpenCRE pairs.

    Returns shape (n_pairs, 4) probability matrix.
    Falls back to text-only baseline if full pipeline features unavailable.
    """
    try:
        import pickle
        model_path = Path("runs/v7c_sacred/logreg_model.pkl")
        if model_path.exists():
            with open(model_path, "rb") as f:
                bundle = pickle.load(f)
            model = bundle["model"]
            scaler = bundle.get("scaler")
            print(f"  Loaded v7c model from {model_path}")

            from classifier.sacred.v7c_sacred_run import build_features
            X, _ = build_features(pairs, "opencre", include_ce=True)
            if scaler:
                X = scaler.transform(X)
            proba = model.predict_proba(X)
            return proba
    except Exception as e:
        print(f"  v7c model unavailable ({e}), using text similarity fallback")

    try:
        from sentence_transformers import SentenceTransformer
        from sklearn.metrics.pairwise import cosine_similarity

        model = SentenceTransformer("BAAI/bge-large-en-v1.5")
        src_texts = [p.get("source_text", "") for p in pairs]
        tgt_texts = [p.get("target_text", "") for p in pairs]

        src_emb = model.encode(src_texts, batch_size=64, show_progress_bar=True)
        tgt_emb = model.encode(tgt_texts, batch_size=64, show_progress_bar=True)

        sims = np.array([
            cosine_similarity([s], [t])[0, 0]
            for s, t in zip(src_emb, tgt_emb)
        ])

        proba = np.zeros((len(pairs), 4))
        for i, sim in enumerate(sims):
            if sim > 0.8:
                proba[i] = [0.05, 0.10, 0.35, 0.50]
            elif sim > 0.6:
                proba[i] = [0.05, 0.15, 0.55, 0.25]
            elif sim > 0.4:
                proba[i] = [0.10, 0.40, 0.40, 0.10]
            else:
                proba[i] = [0.50, 0.30, 0.15, 0.05]
        return proba
    except Exception as e2:
        print(f"  SetFit fallback also failed ({e2}), using uniform priors")
        return np.full((len(pairs), 4), 0.25)


def identify_disagreements(
    pairs: list[dict],
    model_proba: np.ndarray,
) -> list[int]:
    """Find pairs where model prediction disagrees with OpenCRE expert signal."""
    disagreement_indices = []
    for i, pair in enumerate(pairs):
        expert_dist = map_opencre_tier(
            gap_penalty=pair.get("gap_penalty", 0),
            bridge_pair=(pair.get("fw_class_a") != pair.get("fw_class_b")
                        and "other" not in (pair.get("fw_class_a", ""), pair.get("fw_class_b", ""))),
        )
        expert_argmax = max(expert_dist, key=expert_dist.get)
        model_argmax = TierLabel(int(np.argmax(model_proba[i])))

        if model_argmax != expert_argmax:
            disagreement_indices.append(i)

    return disagreement_indices


def assemble_v8_training(max_opencre_pairs: int = 2000) -> dict:
    """Full v8 training data assembly pipeline."""
    t0 = time.time()

    print("Loading OpenCRE pairs...")
    opencre_pairs = load_jsonl(OPENCRE_PAIRS)
    print(f"  {len(opencre_pairs)} total OpenCRE pairs")

    print("Running contamination firewall...")
    frozen_ids = build_frozen_node_ids()
    contaminated_shas = set(check_cre_bridge_contamination(opencre_pairs, frozen_ids))
    clean_pairs = [p for p in opencre_pairs if p.get("provenance_sha") not in contaminated_shas]
    print(f"  {len(opencre_pairs) - len(clean_pairs)} contaminated, {len(clean_pairs)} clean")

    print("Running v7c inference on clean pairs...")
    model_proba = run_v7c_inference(clean_pairs)
    print(f"  Inference complete: shape {model_proba.shape}")

    print("Mining disagreements...")
    disagreement_idx = identify_disagreements(clean_pairs, model_proba)
    pct = len(disagreement_idx) / len(clean_pairs) * 100 if clean_pairs else 0
    print(f"  {len(disagreement_idx)} disagreements ({pct:.1f}%)")

    selected_idx = disagreement_idx[:max_opencre_pairs]
    selected_pairs = [clean_pairs[i] for i in selected_idx]

    print("Generating calibrated soft labels...")
    v8_rows = []
    label_dist = Counter()
    for pair in selected_pairs:
        is_bridge = (
            pair.get("fw_class_a") != pair.get("fw_class_b")
            and "other" not in (pair.get("fw_class_a", ""), pair.get("fw_class_b", ""))
        )
        expert_dist = map_opencre_tier(
            gap_penalty=pair.get("gap_penalty", 0),
            bridge_pair=is_bridge,
        )
        argmax_label = max(expert_dist, key=expert_dist.get)
        label_dist[TierLabel(argmax_label).name] += 1

        for label, prob in expert_dist.items():
            if prob < 0.05:
                continue
            v8_rows.append({
                "source_node_id": pair["source_node_id"],
                "target_node_id": pair["target_node_id"],
                "source_text": pair.get("source_text", ""),
                "target_text": pair.get("target_text", ""),
                "source_framework": pair.get("source_framework", ""),
                "target_framework": pair.get("target_framework", ""),
                "tier_label": int(label),
                "sample_weight": OPENCRE_WEIGHT * prob,
                "provenance": "opencre_disagreement",
                "provenance_sha": pair.get("provenance_sha", ""),
                "gap_penalty": pair.get("gap_penalty", -1),
                "cre_id": pair.get("cre_id", ""),
            })

    print("Merging with existing expert_train...")
    expert_rows = load_jsonl(EXPERT_TRAIN)
    print(f"  Existing expert_train: {len(expert_rows)} rows")
    print(f"  New OpenCRE rows: {len(v8_rows)} (from {len(selected_pairs)} pairs)")

    all_rows = expert_rows + v8_rows

    V8_TRAIN_OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(V8_TRAIN_OUT, "w") as f:
        for row in all_rows:
            f.write(json.dumps(row, ensure_ascii=True) + "\n")

    elapsed = time.time() - t0
    report = {
        "elapsed_seconds": elapsed,
        "opencre_total": len(opencre_pairs),
        "contaminated": len(opencre_pairs) - len(clean_pairs),
        "clean": len(clean_pairs),
        "disagreements": len(disagreement_idx),
        "selected": len(selected_pairs),
        "v8_rows_added": len(v8_rows),
        "expert_train_original": len(expert_rows),
        "v8_train_total": len(all_rows),
        "label_distribution": dict(label_dist),
        "output_path": str(V8_TRAIN_OUT),
    }

    V8_REPORT_OUT.parent.mkdir(parents=True, exist_ok=True)
    V8_REPORT_OUT.write_text(json.dumps(report, indent=2))
    print(f"\nv8 training data written to {V8_TRAIN_OUT}")
    print(f"Report: {V8_REPORT_OUT}")
    print(f"Total rows: {len(all_rows)} (expert: {len(expert_rows)}, opencre: {len(v8_rows)})")
    return report


if __name__ == "__main__":
    assemble_v8_training()
