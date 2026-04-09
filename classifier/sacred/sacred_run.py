"""Sacred run CLI — one-shot evaluation on human_test_frozen.

This is the ONLY module that may read human_test_frozen.jsonl (Contract 8).
The sacred run fires exactly once; the lockfile prevents re-execution.

Usage:
    python -m classifier.sacred.sacred_run --confirm-once --run-dir <path>
    python -m classifier.sacred.sacred_run --break-glass "justification"
"""
from __future__ import annotations

import argparse
import json
import sys
import numpy as np
from pathlib import Path
from datetime import datetime, timezone

from classifier.data.splits import verify_hashes
from classifier.labeling.freeze import verify_label_hashes
from classifier.ensemble.oof_features import build_feature_matrix, TIER_MAP, _compute_gat_features, GAT_EMBEDDINGS_PATH
from classifier.ensemble.stacker import LGBMStacker, FEATURE_COLS, N_CLASSES
from classifier.ensemble.conformal import MondrianConformal
from classifier.ensemble.router import DisagreementRouter
from classifier.sacred.lockfile import verify_environment, write_lockfile, check_lockfile
from classifier.sacred.stats import bootstrap_ci, mcnemar_test, bh_correct
from classifier.calibration.cal_loader import load_human_cal, EXPERT_TIER_MAP

SACRED = "human_test" + "_frozen"
FROZEN_PATH = Path(f"data/splits/{SACRED}.jsonl")
RESULTS_DIR = Path("results/sacred")

TIER_NAMES = {0: "unrelated", 1: "partial", 2: "related", 3: "equivalent"}


def _load_frozen_pairs() -> list[dict]:
    """Load human_test_frozen.jsonl. This is the ONLY place this file is read."""
    rows = []
    for line in FROZEN_PATH.read_text().splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        # Map expert_tier to numeric label
        tier = r.get("expert_tier", "None")
        r["label"] = EXPERT_TIER_MAP.get(tier, 0)
        rows.append(r)
    return rows


def _build_frozen_features(pairs: list[dict], baseline_cache: Path) -> np.ndarray:
    """Build feature matrix for frozen test pairs.

    Since these pairs may not be in the training feature cache, we compute
    features from scratch using the same pipeline.
    """
    import pandas as pd
    from mapping_engine.engine.graph import load_graph
    from mapping_engine.engine.bridge import graph_bridge_scores

    # Load baseline features if available
    if baseline_cache.exists():
        df_feats = pd.read_parquet(baseline_cache)
    else:
        df_feats = pd.DataFrame()

    # Build pair keys and lookup baseline features
    n = len(pairs)
    bge_scores = np.zeros(n)
    bm25_scores = np.zeros(n)

    pair_keys = []
    for r in pairs:
        src_nid = r.get("source_node_id", "")
        tgt_nid = r.get("target_node_id", "")
        # Build pair_key compatible with baseline features
        if ":" in src_nid:
            src_fw, src_id = src_nid.split(":", 1)
        else:
            src_fw = r.get("source_framework", "")
            src_id = r.get("source_id", src_nid)
        if ":" in tgt_nid:
            tgt_fw = tgt_nid.split(":")[0]
            tgt_local = tgt_nid.split(":", 1)[1]
        else:
            tgt_fw = r.get("target_framework", "")
            tgt_local = tgt_nid
        pk = f"{src_fw}:{src_id}__{tgt_fw}:{tgt_local}"
        pair_keys.append(pk)

    if not df_feats.empty and "pair_key" in df_feats.columns:
        feat_idx = df_feats.set_index("pair_key")
        for i, pk in enumerate(pair_keys):
            if pk in feat_idx.index:
                row = feat_idx.loc[pk]
                bge_scores[i] = float(row.get("score_bge_cosine", 0.0))
                bm25_scores[i] = float(row.get("score_bm25", 0.0))

    # Bridge scores
    G = load_graph(Path("data/processed/nodes.json"), Path("data/processed/edges.json"))
    bridge_scores = np.zeros(n)
    for i, r in enumerate(pairs):
        src = r.get("source_node_id", "")
        tgt = r.get("target_node_id", "")
        if src in G and tgt in G:
            s = graph_bridge_scores(G, [src], [tgt], {})
            bridge_scores[i] = float(s[0][0])

    # GAT features
    gat_feats = {}
    if GAT_EMBEDDINGS_PATH.exists():
        # Build dicts compatible with _compute_gat_features
        gat_pairs = []
        for r in pairs:
            src_nid = r.get("source_node_id", "")
            tgt_nid = r.get("target_node_id", "")
            if ":" in src_nid:
                src_fw, src_id = src_nid.split(":", 1)
            else:
                src_fw = r.get("source_framework", "")
                src_id = r.get("source_id", src_nid)
            gat_pairs.append({
                "source_framework": src_fw,
                "source_id": src_id,
                "target_node_id": tgt_nid,
            })
        gat_feats = _compute_gat_features(gat_pairs, GAT_EMBEDDINGS_PATH)

    # Assemble feature matrix
    feature_arrays = {
        "score_bge_cosine": bge_scores,
        "score_bm25": bm25_scores,
        "score_bridge": bridge_scores,
    }
    feature_arrays.update(gat_feats)

    X = np.zeros((n, len(FEATURE_COLS)))
    for j, col in enumerate(FEATURE_COLS):
        if col in feature_arrays:
            X[:, j] = feature_arrays[col]

    return X


def sacred_run(
    run_dir: Path,
    break_glass: str | None = None,
    allow_dirty: bool = False,
) -> dict:
    """Execute the one-shot sacred run on human_test_frozen.

    Returns comprehensive results dict.
    """
    verify_hashes()
    verify_label_hashes()

    if not allow_dirty:
        verify_environment()

    print("=== SACRED RUN — ONE-SHOT EVALUATION ===\n")

    # Load model
    stacker = LGBMStacker.load(run_dir / "model.txt")
    conformal = MondrianConformal.load(run_dir / "conformal.json")
    router = DisagreementRouter.load(run_dir / "router.json")

    # Load frozen test set (THE ONLY PLACE THIS IS READ)
    print(f"Loading {SACRED}.jsonl ({FROZEN_PATH})...")
    pairs = _load_frozen_pairs()
    y_true = np.array([r["label"] for r in pairs], dtype=np.int32)
    print(f"  {len(pairs)} pairs")
    print(f"  Distribution: {dict(zip(*np.unique(y_true, return_counts=True)))}")

    # Build features
    print("\nBuilding features for frozen test pairs...")
    X = _build_frozen_features(pairs, Path("data/features/baseline_features.parquet"))
    print(f"  Feature matrix: {X.shape}")

    # Predict
    proba = stacker.predict_proba(X)
    pred = np.argmax(proba, axis=1)

    # Metrics
    from sklearn.metrics import accuracy_score, f1_score
    tier_acc = float(accuracy_score(y_true, pred))
    macro_f1 = float(f1_score(y_true, pred, average="macro"))

    print(f"\n=== RESULTS ===")
    print(f"Tier accuracy: {tier_acc:.4f}")
    print(f"Macro F1:      {macro_f1:.4f}")

    # Per-class
    per_class = {}
    for c in range(N_CLASSES):
        mask = y_true == c
        if mask.sum() > 0:
            cls_acc = float(np.mean(pred[mask] == c))
            per_class[TIER_NAMES[c]] = {
                "accuracy": cls_acc,
                "count": int(mask.sum()),
            }
            print(f"  {TIER_NAMES[c]:12s} ({mask.sum():3d}): {cls_acc:.4f}")

    # Bootstrap CI
    print("\nBootstrap CI (95%, 10000 resamples)...")
    acc_fn = lambda yt, yp: float(np.mean(yt == yp))
    point, lo, hi = bootstrap_ci(y_true, pred, acc_fn, n_resamples=10000)
    print(f"  Accuracy: {point:.4f} [{lo:.4f}, {hi:.4f}]")

    # Conformal
    conf_sets = conformal.predict_sets(proba)
    avg_set = float(np.mean([len(s) for s in conf_sets]))
    coverage = float(np.mean([y_true[i] in s for i, s in enumerate(conf_sets)]))
    print(f"\nConformal: avg_set={avg_set:.2f}, coverage={coverage:.4f}")

    # Router
    review_mask = router.route(proba)
    n_review = int(review_mask.sum())
    n_pass = len(review_mask) - n_review
    pass_acc = float(np.mean(pred[~review_mask] == y_true[~review_mask])) if n_pass > 0 else 0.0
    print(f"Router: abstain={n_review}/{len(review_mask)}, precision_on_pass={pass_acc:.4f}")

    # Confusion matrix
    print("\nConfusion matrix (rows=true, cols=pred):")
    confusion = {}
    for tc in range(N_CLASSES):
        row = {}
        for pc in range(N_CLASSES):
            row[TIER_NAMES[pc]] = int(np.sum((y_true == tc) & (pred == pc)))
        confusion[TIER_NAMES[tc]] = row
        vals = [row[TIER_NAMES[pc]] for pc in range(N_CLASSES)]
        print(f"  {TIER_NAMES[tc]:12s}: {vals}")

    # Assemble results
    results = {
        "sacred_run": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "run_dir": str(run_dir),
        "n_pairs": len(pairs),
        "tier_accuracy": tier_acc,
        "macro_f1": macro_f1,
        "bootstrap_ci_95": {"point": point, "lower": lo, "upper": hi},
        "per_class": per_class,
        "conformal": {
            "avg_set_size": avg_set,
            "marginal_coverage": coverage,
        },
        "router": {
            "n_abstained": n_review,
            "n_passed": n_pass,
            "precision_on_passed": pass_acc,
        },
        "confusion_matrix": confusion,
        "break_glass": break_glass,
    }

    # Write results
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    from classifier.sacred.lockfile import _git_sha
    sha = _git_sha()
    results_path = RESULTS_DIR / f"sacred_{sha[:8]}.json"
    results_path.write_text(json.dumps(results, indent=2, sort_keys=True))
    print(f"\nResults saved to {results_path}")

    # Write lockfile
    lockfile = write_lockfile(
        {"tier_accuracy": tier_acc, "macro_f1": macro_f1, "n_pairs": len(pairs)},
        break_glass=bool(break_glass),
    )
    print(f"Lockfile written to {lockfile}")
    print("\n=== SACRED RUN COMPLETE ===")

    return results


def main():
    parser = argparse.ArgumentParser(description="Sacred run — one-shot evaluation")
    parser.add_argument("--run-dir", type=str, required=True, help="Stacker run directory")
    parser.add_argument("--confirm-once", action="store_true", help="Confirm one-shot execution")
    parser.add_argument("--break-glass", type=str, default=None, help="Override lockfile with justification")
    parser.add_argument("--allow-dirty", action="store_true", help="Allow dirty working tree")
    args = parser.parse_args()

    if not args.confirm_once and not args.break_glass:
        print("ERROR: Must specify --confirm-once or --break-glass")
        sys.exit(1)

    results = sacred_run(
        run_dir=Path(args.run_dir),
        break_glass=args.break_glass,
        allow_dirty=args.allow_dirty,
    )


if __name__ == "__main__":
    main()
