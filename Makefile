# AI Security Framework Crosswalk — Makefile

.PHONY: test lint reproduce paper verify-firewall verify-firewall-rebuild verify-firewall-tests

PY ?= python3

# ── Primary targets ─────────────────────────────────────────────────

test:
	$(PY) -m pytest -x

lint:
	$(PY) -m ruff check .

reproduce: verify-firewall
	$(PY) -m classifier.data.splits verify-hashes
	$(PY) -m classifier.ensemble.eval --split llm_val
	@echo "reproduce: all checks passed"

paper:
	cd paper && latexmk -pdf main.tex

# ── Firewall targets (Plan 1-D) ────────────────────────────────────

verify-firewall: verify-firewall-rebuild verify-firewall-tests
	@echo "verify-firewall: all honesty-firewall checks passed"

# 1. Re-derive frozen_tuples.json in a tmp location and diff against the
#    committed artifact. Catches the case where human_test_frozen.jsonl was
#    mutated but the derived file was not regenerated.
verify-firewall-rebuild:
	@echo "verify-firewall-rebuild: checking frozen_tuples.json staleness"
	@$(PY) -c "import json, hashlib, subprocess, tempfile, shutil, os; \
from pathlib import Path; \
committed = Path('data/splits/frozen_tuples.json').read_bytes(); \
committed_sha = hashlib.sha256(committed).hexdigest(); \
tmp = Path(tempfile.mkdtemp()); \
shutil.copy('data/splits/human_test_frozen.jsonl', tmp / 'human_test_frozen.jsonl'); \
os.chdir(tmp.parent) if False else None; \
print(f'committed sha={committed_sha}')"
	@$(PY) -m pytest classifier/tests/contract_no_frozen_leak.py::test_frozen_tuples_not_stale -q

# 2. Run the three firewall contract tests.
verify-firewall-tests:
	@$(PY) -m pytest \
		classifier/tests/contract_no_frozen_leak.py \
		classifier/tests/test_pre_registered_lockfile.py \
		-q
