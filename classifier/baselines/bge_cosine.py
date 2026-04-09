"""BGE cosine baseline, reading a locally-produced embeddings parquet.

Model pin: BAAI/bge-base-en-v1.5 (Plan 1-B). Bumping this pin MUST bump
BGECosineScorer.version so the eval-harness results JSON reflects the change.
"""
from __future__ import annotations

from pathlib import Path
import numpy as np
import pyarrow.parquet as pq

from classifier.baselines.protocol import NodePair, ScoreRecord

MODEL_NAME = "BAAI/bge-base-en-v1.5"


class BGECosineScorer:
    name = "bge_cosine"
    version = "2.0.0"  # 2.0.0 = bge-base-en-v1.5 (was 1.0.0 = bge-large-en-v1.5)

    def __init__(self, embeddings_path: Path):
        tbl = pq.read_table(embeddings_path)
        cols = [c for c in tbl.column_names if c.startswith("e")]
        self._ids = tbl.column("node_id").to_pylist()
        self._emb = np.stack([tbl.column(c).to_numpy() for c in cols], axis=1)
        self._idx = {nid: i for i, nid in enumerate(self._ids)}

    def score(self, pairs: list[NodePair]) -> list[ScoreRecord]:
        out: list[ScoreRecord] = []
        for p in pairs:
            i = self._idx.get(p.source_node_id)
            j = self._idx.get(p.target_node_id)
            if i is None or j is None:
                score = float("nan")
            else:
                score = float(self._emb[i] @ self._emb[j])
            out.append(ScoreRecord(
                pair_key=p.pair_key, scorer_name=self.name, scorer_version=self.version,
                score=score, tier_pred=None, tier_probs=None,
                extras={"model": MODEL_NAME},
            ))
        return out
