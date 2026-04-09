import json
from pathlib import Path
from classifier.labeling.client import LabelerClient


class _FakeMessages:
    def __init__(self):
        self.calls = 0

    def create(self, *, model, system, messages, max_tokens):
        self.calls += 1
        return type("R", (), {
            "content": [type("B", (), {"text": '{"relation":"related","confidence":0.7,"rationale":"ok"}'})()],
            "model": model,
        })()


class _FakeClient:
    def __init__(self):
        self.messages = _FakeMessages()


def test_client_caches_on_prompt_sha(tmp_path):
    cache = tmp_path / "cache"
    ledger = tmp_path / "ledger.jsonl"
    fake = _FakeClient()
    c = LabelerClient(
        anthropic_client=fake,
        cache_dir=cache,
        ledger_path=ledger,
        model="claude-sonnet-4-5-20251101",
    )
    out1 = c.label("sysprompt", "userprompt")
    out2 = c.label("sysprompt", "userprompt")
    assert out1 == out2
    assert fake.messages.calls == 1  # second hit served from cache
    ledger_rows = [json.loads(l) for l in ledger.read_text().splitlines() if l.strip()]
    assert len(ledger_rows) == 2  # one miss + one hit
    assert ledger_rows[0]["cache_hit"] is False
    assert ledger_rows[1]["cache_hit"] is True
