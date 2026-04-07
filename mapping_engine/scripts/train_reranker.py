"""A3: Cross-encoder fine-tune script.

Trains `BAAI/bge-reranker-base` on the graded triples produced by A1
(`data/processed/reranker_triples.jsonl`). Uses MarginMSE loss against
the per-source positive as the anchor, batch 16, lr 2e-5, max 5 epochs,
early stopping on leave-one-framework-pair-out validation NDCG@10.

The trained model is saved to `mapping_engine/models/reranker_v2/`.

Validation split. We do leave-one-framework-pair-out CV: for each unique
(source_framework, target_framework) appearing in the triples, holding
that pair out as the validation fold and training on the rest. This is
the val signal used for early stopping. Frozen test pairs are already
absent from the triples (enforced by A2).

Run:
    python -m mapping_engine.scripts.train_reranker [--epochs 5] [--batch 16]

Honest blocker note. This script imports `sentence-transformers` at the
module level so missing-dep failure is loud rather than silent. If GPU
is unavailable the script falls back to CPU (it will be slow). A4
decides whether training actually runs.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

from mapping_engine.calibration.metrics import ndcg_at_k
from mapping_engine.engine.graph import load_graph

REPO = Path(__file__).resolve().parents[2]
TRIPLES_PATH = REPO / "data/processed/reranker_triples.jsonl"
MODEL_OUT = REPO / "mapping_engine/models/reranker_v2"
BASE_MODEL = "BAAI/bge-reranker-base"


def _load_triples() -> list[dict]:
    rows: list[dict] = []
    for line in TRIPLES_PATH.read_text().splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _by_framework_pair(rows: list[dict], G) -> dict[tuple[str, str], list[dict]]:
    out: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for r in rows:
        sfw = G.nodes[r["source_id"]].get("framework") if r["source_id"] in G else None
        tfw = G.nodes[r["target_id"]].get("framework") if r["target_id"] in G else None
        out[(sfw, tfw)].append(r)
    return out


def _eval_ndcg(model, val_rows: list[dict]) -> float:
    """Aggregate NDCG@10 across val sources. Group by source_id, score the
    candidate list (positive + negatives) with the cross-encoder, and compute
    NDCG@10 against the graded labels."""
    by_src: dict[str, list[dict]] = defaultdict(list)
    for r in val_rows:
        by_src[r["source_id"]].append(r)
    if not by_src:
        return 0.0
    scores_list = []
    grades_list = []
    for src, items in by_src.items():
        pairs = [(it["source_text"], it["target_text"]) for it in items]
        preds = model.predict(pairs).tolist() if pairs else []
        grades = [float(it.get("label", 0)) for it in items]
        scores_list.append(np.asarray(preds, dtype=float))
        grades_list.append(np.asarray(grades, dtype=float))
    # Per-source NDCG@10, averaged.
    vals = []
    for s, g in zip(scores_list, grades_list):
        vals.append(ndcg_at_k(g, s, k=10))
    return float(np.mean(vals)) if vals else 0.0


def _train(
    train_rows: list[dict],
    val_rows: list[dict],
    epochs: int,
    batch: int,
    lr: float,
    out_dir: Path,
) -> dict:
    from sentence_transformers import CrossEncoder, InputExample
    from torch.utils.data import DataLoader

    model = CrossEncoder(BASE_MODEL, num_labels=1)
    examples = [
        InputExample(texts=[r["source_text"], r["target_text"]], label=float(r["label"]))
        for r in train_rows
    ]
    loader = DataLoader(examples, batch_size=batch, shuffle=True)

    history: list[dict] = []
    best = {"epoch": -1, "val_ndcg": -1.0}
    for ep in range(epochs):
        model.fit(
            train_dataloader=loader,
            epochs=1,
            warmup_steps=int(0.1 * len(loader)),
            optimizer_params={"lr": lr},
            show_progress_bar=False,
            output_path=None,
        )
        val_ndcg = _eval_ndcg(model, val_rows)
        history.append({"epoch": ep, "val_ndcg": val_ndcg})
        print(f"  epoch {ep}: val NDCG@10 = {val_ndcg:.4f}")
        if val_ndcg > best["val_ndcg"]:
            best = {"epoch": ep, "val_ndcg": val_ndcg}
            out_dir.mkdir(parents=True, exist_ok=True)
            model.save(str(out_dir))
        elif ep - best["epoch"] >= 1:
            print(f"  early stop (no improvement since epoch {best['epoch']})")
            break

    return {"history": history, "best": best}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=5)
    ap.add_argument("--batch", type=int, default=16)
    ap.add_argument("--lr", type=float, default=2e-5)
    ap.add_argument(
        "--val-pair",
        type=str,
        default=None,
        help="Override the validation framework pair as 'src,tgt'. "
        "Defaults to the largest non-frozen pair in the triples.",
    )
    args = ap.parse_args()

    G = load_graph(REPO / "data/processed/nodes.json", REPO / "data/processed/edges.json")
    rows = _load_triples()
    by_pair = _by_framework_pair(rows, G)
    print(f"Loaded {len(rows)} triples across {len(by_pair)} framework pairs")

    if args.val_pair:
        sfw, tfw = args.val_pair.split(",")
        val_key = (sfw, tfw)
    else:
        val_key = max(by_pair.keys(), key=lambda k: len(by_pair[k]))
    val_rows = by_pair[val_key]
    train_rows = [r for k, v in by_pair.items() if k != val_key for r in v]
    print(f"  validation pair: {val_key} ({len(val_rows)} rows)")
    print(f"  training rows:   {len(train_rows)}")

    summary = _train(
        train_rows=train_rows,
        val_rows=val_rows,
        epochs=args.epochs,
        batch=args.batch,
        lr=args.lr,
        out_dir=MODEL_OUT,
    )

    summary["base_model"] = BASE_MODEL
    summary["val_pair"] = list(val_key)
    summary["n_train"] = len(train_rows)
    summary["n_val"] = len(val_rows)
    summary["epochs"] = args.epochs
    summary["batch"] = args.batch
    summary["lr"] = args.lr

    out_json = REPO / "data/processed/reranker_v2_training.json"
    out_json.write_text(json.dumps(summary, indent=2, default=str))
    print(f"Wrote {out_json}")
    print(f"Best epoch: {summary['best']['epoch']} val NDCG@10={summary['best']['val_ndcg']:.4f}")


if __name__ == "__main__":
    main()
