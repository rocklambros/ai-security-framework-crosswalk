"""Test that LICENSE file exists and contains Apache License text."""

from pathlib import Path


def test_license_exists_and_is_apache():
    """LICENSE must exist at repo root and contain Apache License text."""
    license_file = Path(__file__).resolve().parents[3] / "LICENSE"
    assert license_file.exists(), f"LICENSE not found at {license_file}"
    text = license_file.read_text()
    assert "Apache License" in text, (
        "LICENSE must contain 'Apache License'"
    )
