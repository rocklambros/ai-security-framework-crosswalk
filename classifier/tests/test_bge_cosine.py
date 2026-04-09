import pytest, json
from pathlib import Path
from classifier.baselines.bge_cosine import BGECosineScorer, MODEL_NAME
from classifier.baselines.protocol import NodePair
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq


FIXTURE = Path(__file__).parent / "fixtures" / "pairs_5.jsonl"


def test_model_pin_is_bge_base():
    assert MODEL_NAME == "BAAI/bge-base-en-v1.5"


def test_scorer_version_reflects_model_bump():
    assert BGECosineScorer.version == "2.0.0"


def test_bge_cosine_runs_on_fixture(tmp_path):
    pairs = [NodePair(**json.loads(l)) for l in FIXTURE.read_text().splitlines()]
    node_ids = sorted({p.source_node_id for p in pairs} | {p.target_node_id for p in pairs})
    dim = 8
    rng = np.random.default_rng(0)
    embs = rng.standard_normal((len(node_ids), dim)).astype("float32")
    embs /= np.linalg.norm(embs, axis=1, keepdims=True)
    tbl = pa.table({"node_id": node_ids, **{f"e{i}": embs[:, i] for i in range(dim)}})
    parquet_path = tmp_path / "bge_cosine_embeddings.parquet"
    pq.write_table(tbl, parquet_path)
    s = BGECosineScorer(embeddings_path=parquet_path)
    records = s.score(pairs)
    assert len(records) == 5
    assert all(-1.0 <= r.score <= 1.0 for r in records)
