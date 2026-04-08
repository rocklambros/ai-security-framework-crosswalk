import os
import pytest
from classifier import config

def test_repo_root_exists(repo_root):
    assert (repo_root / "mapping_engine").is_dir()
    assert config.REPO_ROOT == repo_root

def test_required_secrets_raises_when_missing(monkeypatch):
    for key in ("ANTHROPIC_API_KEY", "HF_TOKEN", "WANDB_API_KEY"):
        monkeypatch.delenv(key, raising=False)
    with pytest.raises(config.MissingSecretError) as excinfo:
        config.require_secrets(["ANTHROPIC_API_KEY"])
    assert "ANTHROPIC_API_KEY" in str(excinfo.value)

def test_required_secrets_ok(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    out = config.require_secrets(["ANTHROPIC_API_KEY"])
    assert out["ANTHROPIC_API_KEY"] == "sk-ant-test"
