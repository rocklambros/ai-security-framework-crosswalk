from classifier.baselines.per_pair_coverage import compute_per_pair_coverage
from classifier.data.candidates import FRAMEWORK_PAIRS


def _fake_records():
    return [
        {"framework_pair": "aiuc_1__owasp_agentic", "scorer_name": "bm25", "score": 0.5, "rank_of_gold": 1, "pair_key": "a"},
        {"framework_pair": "aiuc_1__owasp_agentic", "scorer_name": "bge_cosine", "score": 0.7, "rank_of_gold": 2, "pair_key": "a"},
        {"framework_pair": "owasp_dsgai__nist_800_53", "scorer_name": "bm25", "score": None, "rank_of_gold": None, "pair_key": "b"},
        {"framework_pair": "owasp_dsgai__nist_800_53", "scorer_name": "bge_cosine", "score": 0.3, "rank_of_gold": 5, "pair_key": "b"},
    ]


def test_compute_per_pair_coverage_shape():
    out = compute_per_pair_coverage(_fake_records(), framework_pairs=FRAMEWORK_PAIRS)
    assert set(out.keys()) == {f"{a}__{b}" for a, b in FRAMEWORK_PAIRS}
    row = out["aiuc_1__owasp_agentic"]
    assert row["n_rows"] == 1
    assert row["scorers"]["bm25"]["null_rate"] == 0.0
    assert row["scorers"]["bge_cosine"]["null_rate"] == 0.0


def test_all_26_pairs_present():
    out = compute_per_pair_coverage([], framework_pairs=FRAMEWORK_PAIRS)
    assert len(out) == 26
