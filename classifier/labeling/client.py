from __future__ import annotations
import json
import time
from dataclasses import dataclass
from pathlib import Path
from tenacity import retry, stop_after_attempt, wait_exponential
from .prompts import prompt_sha


@dataclass
class LabelerClient:
    anthropic_client: object
    cache_dir: Path
    ledger_path: Path
    model: str
    max_tokens: int = 512

    def __post_init__(self) -> None:
        self.cache_dir = Path(self.cache_dir)
        self.ledger_path = Path(self.ledger_path)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)

    def _cache_path(self, sha: str) -> Path:
        return self.cache_dir / f"{sha}.json"

    def _append_ledger(self, row: dict) -> None:
        with self.ledger_path.open("a") as fh:
            fh.write(json.dumps(row, sort_keys=True) + "\n")

    @retry(stop=stop_after_attempt(5), wait=wait_exponential(min=1, max=30))
    def _call_api(self, system: str, user: str) -> str:
        resp = self.anthropic_client.messages.create(
            model=self.model,
            system=system,
            messages=[{"role": "user", "content": user}],
            max_tokens=self.max_tokens,
        )
        return resp.content[0].text

    def label(self, system: str, user: str) -> dict:
        sha = prompt_sha(system, user)
        cache = self._cache_path(sha)
        if cache.exists():
            self._append_ledger({
                "ts": time.time(), "prompt_sha": sha, "model": self.model, "cache_hit": True,
            })
            return json.loads(cache.read_text())
        text = self._call_api(system, user)
        parsed = json.loads(text)
        parsed["_prompt_sha"] = sha
        parsed["_model_version"] = self.model
        cache.write_text(json.dumps(parsed, sort_keys=True))
        self._append_ledger({
            "ts": time.time(), "prompt_sha": sha, "model": self.model, "cache_hit": False,
        })
        return parsed
