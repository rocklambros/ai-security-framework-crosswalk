"""Smoke test: verify the Dash app creates without error."""
import pytest


def test_create_app_import():
    """App module is importable."""
    from app.dash_app.app import create_app
    assert callable(create_app)


def test_create_app_returns_dash_instance():
    """create_app() returns a Dash app with the expected layout."""
    from app.dash_app.app import create_app
    app = create_app()
    assert app.title == "AI Security Framework Crosswalk"
    assert app.layout is not None


def test_about_markdown():
    """about_panel_markdown returns a non-empty string."""
    from app.dash_app.app import about_panel_markdown
    md = about_panel_markdown()
    assert isinstance(md, str)
    assert "12 AI security" in md
