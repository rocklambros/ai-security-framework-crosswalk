"""Contract 8: no Plan 5 code may reference human_test_frozen.

Walks every .py file under classifier/ensemble/ and classifier/scripts/
added by Plan 5 and asserts the literal string 'human_test_frozen' NEVER
appears (other than in test files that enforce the contract).
"""
from pathlib import Path

ENSEMBLE_DIR = Path("classifier/ensemble")
SCRIPTS_DIR = Path("classifier/scripts")

# Scripts added by Plan 5
PLAN5_SCRIPTS = {
    "train_stacker.py",
}


def test_no_human_test_frozen_in_ensemble():
    for py_file in ENSEMBLE_DIR.glob("**/*.py"):
        content = py_file.read_text()
        assert "human_test_frozen" not in content, (
            f"Contract 8: {py_file} references human_test_frozen"
        )


def test_no_human_test_frozen_in_plan5_scripts():
    for script_name in PLAN5_SCRIPTS:
        py_file = SCRIPTS_DIR / script_name
        if py_file.exists():
            content = py_file.read_text()
            assert "human_test_frozen" not in content, (
                f"Contract 8: {py_file} references human_test_frozen"
            )
