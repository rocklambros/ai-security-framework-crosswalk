"""CLI: run all registered baselines on llm_val, write results JSON + feature cache."""
from __future__ import annotations

import argparse, json
from datetime import datetime, timezone
from pathlib import Path

from classifier.baselines import registry
from classifier.baselines.bm25 import BM25Scorer
from classifier.baselines.bge_cosine import BGECosineScorer
from classifier.baselines.eval_harness import load_llm_val_pairs, evaluate_scorer, write_results
from classifier.baselines.feature_cache import build_feature_cache
from classifier.baselines.protocol import ScoreRecord


EMBEDDINGS = Path("data/baselines/bge_cosine_embeddings.parquet")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-root", default="data/baselines")
    args = ap.parse_args()

    # Register scorers
    scorers = []
    bm25 = BM25Scorer()
    try:
        registry.register(bm25)
    except ValueError:
        pass
    scorers.append(bm25)

    if EMBEDDINGS.exists():
        bge = BGECosineScorer(embeddings_path=EMBEDDINGS)
        try:
            registry.register(bge)
        except ValueError:
            pass
        scorers.append(bge)
    else:
        print(f"WARNING: {EMBEDDINGS} not found, skipping bge_cosine")

    # Load llm_val
    pairs, gold = load_llm_val_pairs()
    print(f"loaded {len(pairs)} llm_val pairs")

    # Evaluate all scorers
    results = {}
    all_records: dict[str, list[ScoreRecord]] = {}
    for scorer in scorers:
        print(f"running {scorer.name} v{scorer.version}...")
        result = evaluate_scorer(scorer, pairs, gold)
        results[scorer.name] = result
        all_records[scorer.name] = [
            ScoreRecord(**r) for r in result["records"]
        ]
        print(f"  {scorer.name}: {result['n_scored']}/{result['n_pairs']} scored")

    # Write results
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    run_dir = Path(args.out_root) / f"run_{ts}"
    write_results(run_dir, results)
    print(f"wrote {run_dir}/results_llm_val.json")

    # Update latest symlink
    latest = Path(args.out_root) / "latest"
    if latest.is_symlink():
        latest.unlink()
    latest.symlink_to(run_dir.name)

    # Build feature cache
    features_path = Path("data/features/baseline_features.parquet")
    build_feature_cache(all_records, features_path)
    print(f"wrote {features_path} ({len(pairs)} pairs x {len(scorers)} scorers)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
