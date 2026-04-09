"""Scorer Protocol + NodePair + ScoreRecord dataclasses.

Contract 4: Plans 4-5 register learned models against this Protocol without
modifying this module. Every Scorer MUST expose name (stable identifier) and
version (bump on any algorithmic change) -- the eval harness refuses to overwrite
a results file with the same (name, version) pair.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class NodePair:
    pair_key: str
    source_node_id: str
    source_framework: str
    source_text: str
    target_node_id: str
    target_framework: str
    target_text: str


@dataclass
class ScoreRecord:
    pair_key: str
    scorer_name: str
    scorer_version: str
    score: float
    tier_pred: str | None
    tier_probs: dict[str, float] | None
    extras: dict = field(default_factory=dict)


@runtime_checkable
class Scorer(Protocol):
    name: str
    version: str

    def score(self, pairs: list[NodePair]) -> list[ScoreRecord]: ...
