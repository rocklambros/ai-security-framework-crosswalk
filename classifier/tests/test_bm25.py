import json
from pathlib import Path
from classifier.baselines.bm25 import BM25Scorer
from classifier.baselines.protocol import NodePair


FIXTURE = Path(__file__).parent / "fixtures" / "pairs_5.jsonl"


def _load_pairs():
    return [NodePair(**json.loads(l)) for l in FIXTURE.read_text().splitlines()]


def test_bm25_runs_on_fixture():
    s = BM25Scorer()
    assert s.name == "bm25"
    assert s.version == "1.0.0"
    records = s.score(_load_pairs())
    assert len(records) == 5
    assert all(r.scorer_name == "bm25" for r in records)
    assert all(isinstance(r.score, float) for r in records)
    assert all(r.tier_pred is None for r in records)


def test_bm25_deterministic():
    s = BM25Scorer()
    pairs = _load_pairs()
    r1 = [r.score for r in s.score(pairs)]
    r2 = [r.score for r in s.score(pairs)]
    assert r1 == r2
