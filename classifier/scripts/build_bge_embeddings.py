"""Encode all nodes with bge-base-en-v1.5 and cache to parquet.

Runs locally on GPU. Idempotent: refuses to overwrite unless --force.
"""
from __future__ import annotations

import argparse, json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
from sentence_transformers import SentenceTransformer

MODEL_NAME = "BAAI/bge-base-en-v1.5"
NODES_PATH = Path("data/processed/nodes.json")
OUT_PATH = Path("data/baselines/bge_cosine_embeddings.parquet")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    if OUT_PATH.exists() and not args.force:
        print(f"SKIP: {OUT_PATH} exists; pass --force to rewrite")
        return 0

    nodes = json.loads(NODES_PATH.read_text())
    ids = []
    texts = []
    for n in nodes:
        nid = n.get("node_id", "")
        text = n.get("description") or n.get("name") or ""
        ids.append(nid)
        texts.append(text)

    print(f"encoding {len(ids)} nodes with {MODEL_NAME}...")
    model = SentenceTransformer(MODEL_NAME)
    embs = model.encode(texts, batch_size=64, normalize_embeddings=True,
                        convert_to_numpy=True, show_progress_bar=True).astype(np.float32)

    dim = embs.shape[1]
    columns = {"node_id": ids}
    for i in range(dim):
        columns[f"e{i}"] = embs[:, i].tolist()

    tbl = pa.table(columns)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(tbl, OUT_PATH, compression="snappy", use_dictionary=False)

    print(f"wrote {OUT_PATH} ({len(ids)} rows, dim {dim})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
