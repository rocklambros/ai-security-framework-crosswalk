"""BM25 baseline (rank_bm25). Row 1 of spec S1.3.

Score definition: for each pair, tokenize the source text as a query and
tokenize the target text as a 1-doc corpus; the BM25 score of the target
against the source is the scalar.
"""
from __future__ import annotations

import re
from classifier.baselines.protocol import NodePair, ScoreRecord
from rank_bm25 import BM25Okapi


_TOKEN_RE = re.compile(r"[A-Za-z0-9]+")


def _tokenize(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text)]


class BM25Scorer:
    name = "bm25"
    version = "1.0.0"

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b

    def score(self, pairs: list[NodePair]) -> list[ScoreRecord]:
        out: list[ScoreRecord] = []
        for p in pairs:
            query = _tokenize(p.source_text)
            corpus = [_tokenize(p.target_text)]
            bm25 = BM25Okapi(corpus, k1=self.k1, b=self.b)
            s = float(bm25.get_scores(query)[0])
            out.append(ScoreRecord(
                pair_key=p.pair_key, scorer_name=self.name, scorer_version=self.version,
                score=s, tier_pred=None, tier_probs=None,
                extras={"k1": self.k1, "b": self.b},
            ))
        return out
