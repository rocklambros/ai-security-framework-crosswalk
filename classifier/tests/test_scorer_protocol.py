from classifier.baselines.protocol import NodePair, ScoreRecord, Scorer


def test_nodepair_fields():
    p = NodePair(
        pair_key="aiuc-1:C-1.2__owasp-agentic:ASI-03",
        source_node_id="aiuc-1:C-1.2",
        source_framework="aiuc-1",
        source_text="source control text",
        target_node_id="owasp-agentic:ASI-03",
        target_framework="owasp-agentic",
        target_text="target control text",
    )
    assert p.pair_key.startswith("aiuc-1:")
    assert p.source_framework == "aiuc-1"


def test_score_record_fields():
    r = ScoreRecord(
        pair_key="a__b",
        scorer_name="bm25",
        scorer_version="1.0.0",
        score=0.42,
        tier_pred=None,
        tier_probs=None,
        extras={},
    )
    assert r.score == 0.42
    assert r.tier_pred is None


def test_scorer_protocol_structural():
    class Dummy:
        name = "dummy"
        version = "0.0.0"
        def score(self, pairs):
            return [ScoreRecord(pair_key=p.pair_key, scorer_name=self.name,
                                scorer_version=self.version, score=0.0,
                                tier_pred=None, tier_probs=None, extras={}) for p in pairs]
    d: Scorer = Dummy()
    assert d.name == "dummy"
    out = d.score([])
    assert out == []
