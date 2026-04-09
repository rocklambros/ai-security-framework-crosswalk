"""Test that README.md documents the reproduce workflow."""

from pathlib import Path


def test_readme_contains_make_reproduce():
    """README.md must mention 'make reproduce' so users know the entry point."""
    readme = Path(__file__).resolve().parents[3] / "README.md"
    assert readme.exists(), f"README.md not found at {readme}"
    text = readme.read_text()
    assert "make reproduce" in text, (
        "README.md must contain 'make reproduce' instructions"
    )
