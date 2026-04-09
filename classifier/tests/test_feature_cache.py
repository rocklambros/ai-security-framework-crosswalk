import pyarrow.parquet as pq
from classifier.baselines.feature_cache import build_feature_cache
from classifier.baselines.protocol import ScoreRecord


def test_feature_cache_shape(tmp_path):
    records = {
        "bm25": [
            ScoreRecord(pair_key="a__b", scorer_name="bm25", scorer_version="1.0",
                       score=0.5, tier_pred=None, tier_probs=None),
            ScoreRecord(pair_key="c__d", scorer_name="bm25", scorer_version="1.0",
                       score=0.3, tier_pred=None, tier_probs=None),
        ],
        "bge_cosine": [
            ScoreRecord(pair_key="a__b", scorer_name="bge_cosine", scorer_version="2.0",
                       score=0.8, tier_pred=None, tier_probs=None),
        ],
    }
    out = tmp_path / "features.parquet"
    build_feature_cache(records, out)
    tbl = pq.read_table(out)
    assert tbl.num_rows == 2
    assert "pair_key" in tbl.column_names
    assert "score_bm25" in tbl.column_names
    assert "score_bge_cosine" in tbl.column_names
