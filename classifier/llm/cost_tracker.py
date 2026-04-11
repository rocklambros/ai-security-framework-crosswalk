"""Thread-safe token and cost accumulator for LLM API calls."""
from __future__ import annotations

import threading
from dataclasses import dataclass, field

# Cost in USD per 1M tokens: {model_key: (input_per_1m, output_per_1m)}
PRICING: dict[str, tuple[float, float]] = {
    # claude-3-5-sonnet-* family
    "claude-3-5-sonnet": (3.00, 15.00),
    "sonnet": (3.00, 15.00),
    # claude-3-opus-* family
    "claude-3-opus": (15.00, 75.00),
    "opus": (15.00, 75.00),
}

_FALLBACK_PRICING = (3.00, 15.00)  # Sonnet rates as safe default


def _get_rates(model: str) -> tuple[float, float]:
    """Return (input_per_1m, output_per_1m) for a model string."""
    model_lower = model.lower()
    for key, rates in PRICING.items():
        if key in model_lower:
            return rates
    return _FALLBACK_PRICING


@dataclass
class CostTracker:
    """Thread-safe accumulator for tokens used and cost incurred."""

    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)
    _input_tokens: int = field(default=0, repr=False)
    _output_tokens: int = field(default=0, repr=False)
    _total_cost_usd: float = field(default=0.0, repr=False)
    _call_count: int = field(default=0, repr=False)

    def add(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
    ) -> float:
        """Record token usage for one API call.

        Returns the cost (USD) for this specific call.
        """
        in_rate, out_rate = _get_rates(model)
        call_cost = (input_tokens * in_rate + output_tokens * out_rate) / 1_000_000.0
        with self._lock:
            self._input_tokens += input_tokens
            self._output_tokens += output_tokens
            self._total_cost_usd += call_cost
            self._call_count += 1
        return call_cost

    @property
    def input_tokens(self) -> int:
        with self._lock:
            return self._input_tokens

    @property
    def output_tokens(self) -> int:
        with self._lock:
            return self._output_tokens

    @property
    def total_tokens(self) -> int:
        with self._lock:
            return self._input_tokens + self._output_tokens

    @property
    def total_cost_usd(self) -> float:
        with self._lock:
            return self._total_cost_usd

    @property
    def call_count(self) -> int:
        with self._lock:
            return self._call_count

    def log(self) -> None:
        """Print a one-line running total."""
        with self._lock:
            print(
                f"[cost] calls={self._call_count} "
                f"in={self._input_tokens:,} out={self._output_tokens:,} "
                f"total_tokens={self._input_tokens + self._output_tokens:,} "
                f"cost=${self._total_cost_usd:.4f}"
            )

    def summary(self) -> dict[str, int | float]:
        """Return a dict snapshot of current totals."""
        with self._lock:
            return {
                "call_count": self._call_count,
                "input_tokens": self._input_tokens,
                "output_tokens": self._output_tokens,
                "total_tokens": self._input_tokens + self._output_tokens,
                "total_cost_usd": round(self._total_cost_usd, 6),
            }
