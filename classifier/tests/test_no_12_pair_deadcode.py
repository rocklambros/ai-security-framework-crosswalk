import re
from pathlib import Path

FORBIDDEN = [
    re.compile(r"FRAMEWORK_PAIRS\[:12\]"),
    re.compile(r"range\(\s*12\s*\).*pair", re.IGNORECASE),
    re.compile(r"assert\s+len\(\s*FRAMEWORK_PAIRS\s*\)\s*==\s*12"),
]

ROOT = Path(__file__).resolve().parents[2]
SCAN_DIRS = [ROOT / "classifier", ROOT / "mapping_engine"]


def test_no_12_pair_literals():
    hits: list[str] = []
    for d in SCAN_DIRS:
        if not d.exists():
            continue
        for py in d.rglob("*.py"):
            if py.name == "test_no_12_pair_deadcode.py":
                continue
            text = py.read_text(errors="ignore")
            for rx in FORBIDDEN:
                if rx.search(text):
                    hits.append(f"{py}: {rx.pattern}")
    assert not hits, "12-pair-era dead code found:\n" + "\n".join(hits)
