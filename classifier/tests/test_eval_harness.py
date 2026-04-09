import json
from pathlib import Path
from classifier.baselines.eval_harness import evaluate_scorer, write_results
from classifier.baselines.protocol import NodePair, ScoreRecord


class _FakeScorer:
    name = "fake"
    version = "0.0.1"
    def score(self, pairs):
        return [ScoreRecord(
            pair_key=p.pair_key, scorer_name=self.name, scorer_version=self.version,
            score=0.5, tier_pred=None, tier_probs=None,
        ) for p in pairs]


def _make_pairs(n=3):
    return [NodePair(
        pair_key=f"src:S{i}__tgt:T{i}",
        source_node_id=f"src:S{i}", source_framework="src", source_text=f"source {i}",
        target_node_id=f"tgt:T{i}", target_framework="tgt", target_text=f"target {i}",
    ) for i in range(n)]


def test_evaluate_scorer_basic():
    pairs = _make_pairs()
    gold = {p.pair_key: "related" for p in pairs}
    result = evaluate_scorer(_FakeScorer(), pairs, gold)
    assert result["scorer_name"] == "fake"
    assert result["n_pairs"] == 3
    assert result["n_scored"] == 3
    assert len(result["records"]) == 3


def test_write_results_json(tmp_path):
    run_dir = tmp_path / "run_test"
    pairs = _make_pairs()
    gold = {p.pair_key: "related" for p in pairs}
    result = evaluate_scorer(_FakeScorer(), pairs, gold)
    write_results(run_dir, {"fake": result})
    path = run_dir / "results_llm_val.json"
    assert path.exists()
    data = json.loads(path.read_text())
    assert "timestamp" in data
    assert "fake" in data["scorers"]
