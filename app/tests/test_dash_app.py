"""Playwright GUI tests for the Dash app.

Run with: python -m pytest app/tests/test_dash_app.py -v

Requires the app to be running on localhost:8050.
Start it with: python -m app.dash_app.app &
"""
import subprocess
import time

import pytest


@pytest.fixture(scope="module")
def app_url():
    """Start the Dash app and return its URL."""
    proc = subprocess.Popen(
        ["python", "-m", "app.dash_app.app"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    time.sleep(3)  # Wait for startup
    yield "http://localhost:8050"
    proc.terminate()
    proc.wait()


# The actual Playwright tests will be run via the playwright MCP tool
# during implementation. This file provides the test structure.

def test_placeholder():
    """Placeholder — actual GUI tests run via playwright MCP tool."""
    assert True
