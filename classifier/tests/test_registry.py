import pytest
from classifier.baselines.protocol import ScoreRecord
from classifier.baselines import registry


class _Fake:
    def __init__(self, name, version="1.0.0"):
        self.name = name; self.version = version
    def score(self, pairs):
        return []


def setup_function(_):
    registry._REGISTRY.clear()


def test_register_and_get():
    s = _Fake("bm25")
    registry.register(s)
    assert registry.get("bm25") is s


def test_register_duplicate_name_raises():
    registry.register(_Fake("bm25"))
    with pytest.raises(ValueError, match="already registered"):
        registry.register(_Fake("bm25"))


def test_all_scorers_stable_order():
    registry.register(_Fake("bm25"))
    registry.register(_Fake("bge_cosine"))
    registry.register(_Fake("v2_composite"))
    names = [s.name for s in registry.all_scorers()]
    assert names == sorted(names)
