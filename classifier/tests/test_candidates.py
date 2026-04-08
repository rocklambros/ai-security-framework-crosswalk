from classifier.data.candidates import FRAMEWORK_PAIRS, FRAMEWORKS


def test_framework_pairs_count():
    assert len(FRAMEWORK_PAIRS) == 26


def test_every_framework_in_at_least_two_pairs():
    """Feasibility: 12 fw x 2 = 24 appearances; 22 pairs x 2 sides = 44 slots. OK."""
    from collections import Counter
    appearances = Counter()
    for s, t in FRAMEWORK_PAIRS:
        appearances[s] += 1
        appearances[t] += 1
    for fw in FRAMEWORKS:
        assert appearances[fw] >= 2, f"{fw} appears in <2 pairs"


from classifier.data.candidates import load_nodes_by_framework


def test_load_nodes_has_all_9():
    by_fw = load_nodes_by_framework()
    for fw in ["aiuc_1", "csa_aicm", "mitre_atlas", "nist_rmf",
               "owasp_llm", "owasp_agentic", "owasp_ai_exchange",
               "eu_gpai_cop", "cosai_rm"]:
        assert fw in by_fw, f"{fw} missing"
        assert len(by_fw[fw]) > 0, f"{fw} empty"


def test_load_nodes_counts_match_known():
    by_fw = load_nodes_by_framework()
    expected = {
        "aiuc_1": 189, "csa_aicm": 261, "mitre_atlas": 218,
        "nist_rmf": 76, "owasp_llm": 10, "owasp_agentic": 10,
        "owasp_ai_exchange": 88, "eu_gpai_cop": 70, "cosai_rm": 61,
    }
    for fw, n in expected.items():
        assert len(by_fw[fw]) == n, f"{fw}: got {len(by_fw[fw])}, expected {n}"


from classifier.data.candidates import build_candidate_pool


def test_build_candidate_pool_one_pair(tmp_path):
    out = build_candidate_pool(
        pairs=[("aiuc_1", "owasp_agentic")],
        k=5,
        model_name="BAAI/bge-small-en-v1.5",
        cache_dir=tmp_path,
    )
    assert "aiuc_1__owasp_agentic" in out
    pool = out["aiuc_1__owasp_agentic"]
    assert len(pool) > 0
    first = pool[0]
    assert {"source_node_id", "candidates"} <= first.keys()
    assert len(first["candidates"]) <= 5
    assert first["candidates"][0]["rank"] == 1
