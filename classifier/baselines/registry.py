"""Module-level Scorer registry. Clear in tests via `_REGISTRY.clear()`."""
from __future__ import annotations

from classifier.baselines.protocol import Scorer


_REGISTRY: dict[str, Scorer] = {}


def register(scorer: Scorer) -> None:
    if scorer.name in _REGISTRY:
        raise ValueError(f"Scorer {scorer.name!r} already registered")
    _REGISTRY[scorer.name] = scorer


def get(name: str) -> Scorer:
    if name not in _REGISTRY:
        raise KeyError(f"no scorer named {name!r}; registered: {sorted(_REGISTRY)}")
    return _REGISTRY[name]


def all_scorers() -> list[Scorer]:
    return [_REGISTRY[k] for k in sorted(_REGISTRY)]
