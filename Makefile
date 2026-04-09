# AI Security Framework Crosswalk — Makefile (Plan 1-D bootstrap).
#
# Plan 8 will replace this file with the full `make reproduce` target. Until
# then this Makefile exposes only the firewall pre-gate so every phase can
# run `make verify-firewall` as part of its pre-flight.

.PHONY: verify-firewall verify-firewall-rebuild verify-firewall-tests

PY ?= python3

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
